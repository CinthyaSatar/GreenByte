import requests
import os

# Create the directory if it doesn't exist
image_dir = "greenbyte/static/garden_images"
os.makedirs(image_dir, exist_ok=True)

# List of garden images from Unsplash
images = [
    ("garden_1.jpg", "https://images.unsplash.com/photo-1591857177580-dc82b9ac4e1e"),
    ("garden_2.jpg", "https://images.unsplash.com/photo-1590880449155-b54f958ce314"),
    ("garden_3.jpg", "https://images.unsplash.com/photo-1591857177580-dc82b9ac4e1e"),
    ("garden_4.jpg", "https://images.unsplash.com/photo-1558435186-d31d126391fa"),
    ("garden_5.jpg", "https://images.unsplash.com/photo-1585320806297-9794b3e4eeae"),
    ("garden_6.jpg", "https://images.unsplash.com/photo-1591857177580-dc82b9ac4e1e"),
    ("garden_7.jpg", "https://images.unsplash.com/photo-1416879595882-3373a0480b5b"),
    ("garden_8.jpg", "https://images.unsplash.com/photo-1584479898061-15742e14f50d"),
    ("garden_9.jpg", "https://images.unsplash.com/photo-1558693168-c370615b54e0"),
    ("garden_10.jpg", "https://images.unsplash.com/photo-1591857177580-dc82b9ac4e1e"),
]

# Download each image
for filename, url in images:
    response = requests.get(url)
    if response.status_code == 200:
        with open(os.path.join(image_dir, filename), 'wb') as f:
            f.write(response.content)
        print(f"Downloaded {filename}")
    else:
        print(f"Failed to download {filename}")