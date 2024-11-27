import requests
from bs4 import BeautifulSoup
from pprint import pprint
from termcolor import colored
import re
from geopy.geocoders import Nominatim

url = "https://cad.chp.ca.gov/traffic.aspx?__EVENTTARGET=ddlComCenter&ddlComCenter=BCCC"

HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
}
PARAMS = {'ddlComCenter': 'BCCC'}
VIEWSTATE_PATTERN = re.compile(r'<input\s+type="hidden"\s+name="__VIEWSTATE"\s+id="__VIEWSTATE"\s+value="([^"]+)"\s*/?>')
LAT_LON_PATTERN = re.compile(r"(\d+\.\d+ -\d+\.\d+)")
BRACKETS_PATTERN = re.compile(r'\[.*?\]')

EXCLUDED_DETAILS = {'Unit At Scene', 'Unit Enroute', 'Unit Assigned'}

def scrape_table():
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    table = soup.find('table', id='gvIncidents')
    headers = [th.text.strip() for th in table.find_all('th')]
    first_row = table.find_all('tr')[1]
    cells = first_row.find_all('td')
    row_data = [cell.text.strip() for cell in cells]
    if "Location" in headers and row_data[headers.index("Location")] == "Media Log":
        return None
    return dict(zip(headers, row_data))

def get_viewstate(response_text):
    match = VIEWSTATE_PATTERN.search(response_text)
    return match.group(1) if match else None

def extract_traffic_info(response_text):
    matches = LAT_LON_PATTERN.findall(response_text)
    pattern = re.compile(r'<td[^>]*colspan="6"[^>]*>(.*?)</td>', re.DOTALL)
    matches_two = pattern.findall(response_text)
    details = []
    for match in matches_two:
        clean_detail = BRACKETS_PATTERN.sub('', match).strip()
        if not any(excluded_detail in clean_detail for excluded_detail in EXCLUDED_DETAILS):
            details.append(clean_detail)
    if matches:
        for match in matches:
            lat_str, lon_str = match.split()
            if len(lat_str.split('.')[-1]) == 6 and len(lon_str.split('.')[-1]) == 6:
                return {
                    "Latitude": float(lat_str),
                    "Longitude": float(lon_str),
                    "Details": details
                }
    return None

def get_location(lat, lon):
    geolocator = Nominatim(user_agent="GEOPY")
    location = geolocator.reverse((lat, lon), exactly_one=True)
    if location:
        return location.raw['address']
    else:
        return None

def get_coordinates():
    try:
        response = requests.get(url)
        response.raise_for_status()
        viewstate_value = get_viewstate(response.text)
        if not viewstate_value:
            print("No __VIEWSTATE found on the page.")
            return None
        data = {
            '__LASTFOCUS': '',
            '__EVENTTARGET': 'gvIncidents',
            '__EVENTARGUMENT': 'Select$0',
            '__VIEWSTATE': viewstate_value,
            '__VIEWSTATEGENERATOR': 'B13DF00D',
            'ddlComCenter': 'BCCC',
            'ddlSearches': 'Choose One',
            'ddlResources': 'Choose One',
        }
        response = requests.post(url, params=PARAMS, headers=HEADERS, data=data)
        response.raise_for_status()
        coordinates_data = extract_traffic_info(response.text)
        if coordinates_data:
            location_info = get_location(coordinates_data['Latitude'], coordinates_data['Longitude'])
            if location_info:
                coordinates_data['Neighborhood'] = location_info.get('neighbourhood', 'N/A')
                coordinates_data['City'] = location_info.get('city', 'N/A')
        return coordinates_data
    except requests.RequestException as e:
        print(f"Request failed: {e}")
        return None

def get_merged_data():
    table_data = scrape_table()
    if table_data is None:
        print("Skipping 'Media Log' entry.")
        return None
    if "Area" in table_data:
        del table_data["Area"]
    coordinates_data = get_coordinates()
    if coordinates_data:
        return {**table_data, **coordinates_data}
    return None

if __name__ == "__main__":
    merged_data = get_merged_data()
    if merged_data:
        pprint(merged_data)
