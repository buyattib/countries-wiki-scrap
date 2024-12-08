import re
import time
import requests
from bs4 import BeautifulSoup
import unicodedata


def normalize(input_str):
    nfkd_form = unicodedata.normalize("NFKD", input_str)
    cleaned_str = "".join([c for c in nfkd_form if not unicodedata.combining(c)])
    return cleaned_str


BASE_URL = "https://en.wikipedia.org"
COUNTRY_LIST_PARTIAL_URL = "/wiki/List_of_ISO_3166_country_codes"


def get_country_list():
    country_list_url = BASE_URL + COUNTRY_LIST_PARTIAL_URL
    response = requests.get(country_list_url)

    if not response.ok:
        print("Error in country list response")
        return

    soup = BeautifulSoup(response.content, "html.parser")
    table = soup.find("table", class_="wikitable")

    rows = table.find_all("tr")[2:]

    country_list = []
    for row in rows:
        cols = row.find_all("td")

        if len(cols) < 4:
            continue

        name = cols[0].text.strip()
        official_name = cols[1].text.strip()
        sovereignity = cols[2].text.strip()
        alpha2 = cols[3].text.strip()
        alpha3 = cols[4].text.strip()

        # all the UN members have iso-2 (regions)
        if sovereignity.lower() != "un member":
            continue

        clean_name = normalize(re.sub(r"\[.*?\]", "", name).strip())
        clean_official_name = normalize(re.sub(r"\[.*?\]", "", official_name).strip())

        print(f"{clean_name} - {alpha2}")

        iso2_relative_url = cols[6].a["href"]
        regions = get_country_iso2_regions(BASE_URL + iso2_relative_url)

        country = {
            "english_name": clean_name,
            "official_name": clean_official_name,
            "alpha2": alpha2,
            "alpha3": alpha3,
            "regions": regions,
        }

        country_list.append(country)

        time.sleep(1)

    return country_list


def get_country_iso2_regions(url):
    response = requests.get(url)

    if not response.ok:
        print(f"Error getting iso-2")
        return

    soup = BeautifulSoup(response.content, "html.parser")

    title = soup.find("h2", id="Current_codes")
    if title is None:
        print("Country does not have iso-2 codes \n")
        return []

    regions = []
    for child in title.parent.parent.children:
        if child == "\n":
            continue

        tag = child.name
        class_ = None
        try:
            class_ = child.get("class")
        except:
            print("------ child has no class ------------")
            print(tag)
            print("\n")
            continue

        # section titles have this classes, need to break on section title after current codes to not get incorrect wikitable
        if tag == "div" and "mw-heading" in class_ and "mw-heading2" in class_:
            h2_id = child.h2.get("id")
            if h2_id != "Current_codes":
                break

        if tag == "table" and class_ and "wikitable" in class_:
            regions += parse_region_table(child)

    return regions


def parse_region_table(table):
    # all rows
    rows = table.find_all("tr")

    # check header rows
    header_rows_n = 0
    for row in rows:
        header_cols = row.find_all("th")
        header_cols_n = len(header_cols)
        is_header = header_cols_n > 0

        if is_header:
            header_rows_n += 1
            continue

    # handle multiple rows headers manually
    if header_rows_n != 1:
        print("Handle manually, more than one row in header")
        return []

    header_cols = rows[0].find_all("th")
    header_cols_names = [col.text for col in header_cols]

    # get the index of the column for the region name
    idx = None
    english_column = [
        i for i, name in enumerate(header_cols_names) if "name (en)" in name.lower()
    ]
    if len(english_column) == 1:
        idx = english_column[0]
    if not idx:
        idx = 1

    regions = []
    for row in rows[1:]:
        cols = row.find_all("td")

        name = cols[idx].text.strip()
        iso2_code = cols[0].text.strip()
        short_code = iso2_code.split("-")[-1]

        clean_name = normalize(re.sub(r"\[.*?\]", "", name).strip())

        region = {
            "name": clean_name,
            "iso2_code": iso2_code,
            "short_code": short_code,
        }

        regions.append(region)

    return regions


def get_not_un_countries():
    country_list_url = BASE_URL + COUNTRY_LIST_PARTIAL_URL
    response = requests.get(country_list_url)

    if not response.ok:
        print("Error in country list response")
        return

    soup = BeautifulSoup(response.content, "html.parser")
    table = soup.find("table", class_="wikitable")

    rows = table.find_all("tr")[2:]

    country_list = []
    for row in rows:
        cols = row.find_all("td")

        if len(cols) < 4:
            continue

        name = cols[0].text.strip()
        official_name = cols[1].text.strip()
        sovereignity = cols[2].text.strip()
        alpha2 = cols[3].text.strip()
        alpha3 = cols[4].text.strip()

        # all the UN members have iso-2 (regions)
        if sovereignity.lower() == "un member":
            continue

        clean_name = normalize(re.sub(r"\[.*?\]", "", name).strip())
        clean_official_name = normalize(re.sub(r"\[.*?\]", "", official_name).strip())

        print(f"{clean_name} - {alpha2}")

        country = {
            "english_name": clean_name,
            "official_name": clean_official_name,
            "alpha2": alpha2,
            "alpha3": alpha3,
            "sovereignity": sovereignity,
        }

        country_list.append(country)

        time.sleep(1)

    return country_list


country_list = get_country_list()
# country_list = get_not_un_countries()
