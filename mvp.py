import requests
from PIL import Image
from io import BytesIO

def fetch_buoy_image(station_id):
    url = f"https://www.ndbc.noaa.gov/buoycam.php?station={station_id}"
    response = requests.get(url)
    if response.status_code == 200:
        img = Image.open(BytesIO(response.content))
        return img
    else:
        print(f"Failed to retrieve image for station {station_id}.")
        return None

# Example usage
ids = [45007,45012,46002,46011,46012,46015,46025,46026,46027,46028,46042,46047,46053,46054,46059,46066,46069,46071,46072,46078,46085,46086,46087,46088,46089,51000,51001,51002,51003,51004,51101,46084]
import random
station_id = str(random.choice(ids))
# station_id = "46000"  # Replace with a valid station ID
image = fetch_buoy_image(station_id)
if image:
    image.show()
