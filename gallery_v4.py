import os
import requests
import time
from datetime import datetime
from PIL import Image, ImageChops
from io import BytesIO
import numpy as np
import cv2

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

        if "image" not in response.headers.get("Content-Type", ""):  # Validate image content
            print(f"Invalid image for buoy {buoy_id}")
            return None

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
    """Check if an image is mostly blank (e.g., white, black, or uniform colors)."""
    grayscale = image.convert("L")
    hist = grayscale.histogram()
    total_pixels = sum(hist)
    if hist[-1] > 0.95 * total_pixels or hist[0] > 0.95 * total_pixels:  # Mostly white or black
        return True
    if max(hist) > 0.95 * total_pixels:  # Uniform colors
        return True
    return False

def align_horizon(image):
    """Align the horizon line in an image using Hough Line Transform."""
    # Convert image to grayscale
    grayscale = np.array(image.convert("L"))

    # Apply Canny edge detection
    edges = cv2.Canny(grayscale, 50, 150)

    # Apply Hough Line Transform
    lines = cv2.HoughLines(edges, 1, np.pi / 180, 150)
    if lines is not None:
        angles = [np.rad2deg(theta) - 90 for rho, theta in lines[:, 0]]
        mean_angle = np.mean(angles)
    else:
        mean_angle = 0

    # Rotate the image to correct the horizon
    rotated_image = image.rotate(-mean_angle, resample=Image.BICUBIC, expand=True)
    return rotated_image

def process_and_split_image(image):
    """Split the image into 6 panels, align each panel's horizon, and recombine."""
    width, height = image.size
    if height < 6:  # Handle small images
        print("Image height is too small to split into 6 panels.")
        return image

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
                with Image.open(image_path) as img:
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
