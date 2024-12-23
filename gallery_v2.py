import os
import requests
import time
from datetime import datetime
from PIL import Image, ImageChops
from io import BytesIO
import numpy as np

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

def is_blank_image(image):
    """Check if an image is mostly blank (e.g., white)."""
    grayscale = image.convert("L")
    hist = grayscale.histogram()
    # If the histogram indicates most pixels are white, consider it blank
    return hist[-1] > 0.95 * sum(hist)

def align_horizon(image):
    """Align the horizon line in an image."""
    # Convert image to grayscale for edge detection
    grayscale = image.convert("L")
    edges = np.array(grayscale)

    # Detect edges (Sobel filter approximation)
    sobel_x = np.abs(np.diff(edges, axis=1))
    sobel_y = np.abs(np.diff(edges, axis=0))
    edge_strength = sobel_x[:-1, :] + sobel_y[:, :-1]

    # Find the horizon line: the line with the least variation in edge strength
    horizon_y = np.argmin(edge_strength.mean(axis=1))

    # Align the image by rotating to level the horizon
    width, height = image.size
    rotation_angle = (horizon_y - height // 2) * 0.1  # Estimate angle correction
    aligned_image = image.rotate(rotation_angle, resample=Image.BICUBIC, expand=True)
    return aligned_image

def process_and_split_image(image):
    """Split the image into 6 panels, align each panel's horizon, and recombine."""
    width, height = image.size
    panel_height = height // 6
    aligned_panels = []

    for i in range(6):
        panel = image.crop((0, i * panel_height, width, (i + 1) * panel_height))
        aligned_panel = align_horizon(panel)
        aligned_panels.append(aligned_panel)

    # Combine aligned panels back into a single image
    combined_height = sum(panel.height for panel in aligned_panels)
    combined_image = Image.new("RGB", (width, combined_height))
    y_offset = 0
    for panel in aligned_panels:
        combined_image.paste(panel, (0, y_offset))
        y_offset += panel.height

    # Trim excess from top and bottom
    trim_top = max(0, aligned_panels[0].height - panel_height)
    trim_bottom = max(0, aligned_panels[-1].height - panel_height)
    trimmed_image = combined_image.crop((0, trim_top, width, combined_height - trim_bottom))

    return trimmed_image

def create_gallery():
    """Fetch images for all buoys and create a gallery."""
    images = []
    for buoy_id in buoy_ids:
        image_path = fetch_buoy_image(buoy_id)
        if image_path:
            try:
                img = Image.open(image_path)
                if is_blank_image(img):
                    print(f"Skipping blank image for buoy {buoy_id}")
                    continue
                processed_img = process_and_split_image(img)
                images.append(processed_img)
            except Exception as e:
                print(f"Error processing image for buoy {buoy_id}: {e}")

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
    schedule_interval = 3600  # Fetch images every hour
    while True:
        print("Updating gallery...")
        create_gallery()
        print(f"Waiting for {schedule_interval} seconds...")
        time.sleep(schedule_interval)
