import os
import requests
import time
from datetime import datetime
from PIL import Image
from io import BytesIO

# Buoy IDs
buoy_ids = [
    45007, 45012, 46002, 46011, 46012, 46015, 46025, 46026, 46027, 46028,
    46042, 46047, 46053, 46054, 46059, 46066, 46069, 46071, 46072, 46078,
    46085, 46086, 46087, 46088, 46089, 51000, 51001, 51002, 51003, 51004,
    51101, 46084
]

# Output directory
output_dir = "./buoy_images"
os.makedirs(output_dir, exist_ok=True)

# Base URL for NOAA BuoyCAM images
base_url = "https://www.ndbc.noaa.gov/buoycam.php?station={}"

def fetch_buoy_image(buoy_id):
    """Fetch the latest image for a given buoy ID."""
    try:
        url = base_url.format(buoy_id)
        response = requests.get(url)
        response.raise_for_status()

        # Save the image locally
        image_path = os.path.join(output_dir, f"{buoy_id}.jpg")
        with open(image_path, "wb") as f:
            f.write(response.content)
        print(f"Image saved for buoy {buoy_id}: {image_path}")
        return image_path
    except requests.RequestException as e:
        print(f"Failed to fetch image for buoy {buoy_id}: {e}")
        return None

def create_gallery():
    """Fetch images for all buoys and create a gallery."""
    images = []
    for buoy_id in buoy_ids:
        image_path = fetch_buoy_image(buoy_id)
        if image_path:
            try:
                images.append(Image.open(image_path))
            except Exception as e:
                print(f"Error loading image for buoy {buoy_id}: {e}")

    # Combine images into a single gallery
    if images:
        gallery_width = max(img.width for img in images)
        gallery_height = sum(img.height for img in images)
        gallery = Image.new("RGB", (gallery_width, gallery_height))

        y_offset = 0
        for img in images:
            gallery.paste(img, (0, y_offset))
            y_offset += img.height

        # Save the gallery
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        gallery_path = os.path.join(output_dir, f"gallery_{timestamp}.jpg")
        gallery.save(gallery_path)
        print(f"Gallery created: {gallery_path}")
    else:
        print("No images available for gallery.")

if __name__ == "__main__":
    schedule_interval = 3600/4  # Fetch images every 15 minutes
    while True:
        print("Updating gallery...")
        create_gallery()
        print(f"Waiting for {schedule_interval} seconds...")
        time.sleep(schedule_interval)
