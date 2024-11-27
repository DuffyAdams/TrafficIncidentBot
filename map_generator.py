import requests
import datetime
import pytz
from dotenv import load_dotenv
import os

load_dotenv()

MAPBOX_BASE_URL = "https://api.mapbox.com/styles/v1/mapbox/"

def generate_mapbox_url(lon, lat, access_token, zoom=16, bearing=0, pitch=60, size='500x500@2x', dark_mode=False):
    style = "traffic-night-v2" if dark_mode else "traffic-day-v2"
    url = f"{MAPBOX_BASE_URL}{style}/static/pin-s+ff4242({lon},{lat})/{lon},{lat},{zoom},{bearing},{pitch}/{size}?access_token={access_token}"
    return url

def is_after_sunset(lon, lat):
    local_timezone = pytz.timezone('America/Los_Angeles')
    now = datetime.datetime.now(local_timezone)
    sunset = datetime.datetime(now.year, now.month, now.day, 19, 0, 0, tzinfo=local_timezone)
    return now > sunset

def save_map_image(lon, lat, access_token, filename='map.png'):
    dark_mode = is_after_sunset(lon, lat)
    url = generate_mapbox_url(lon, lat, access_token, dark_mode=dark_mode)
    response = requests.get(url)
    response.raise_for_status()
    with open(filename, 'wb') as file:
        file.write(response.content)
    print(f"Map image saved as {filename}")

if __name__ == "__main__":
    lon = -117.242060
    lat = 32.940853
    access_token = os.getenv("MAP_ACCESS_TOKEN")
    filename = 'map.png'
    save_map_image(lon, lat, access_token, filename)
