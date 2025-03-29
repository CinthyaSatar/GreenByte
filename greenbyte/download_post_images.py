import requests
import os

# Create the directory if it doesn't exist
image_dir = "greenbyte/static/post_pics"
os.makedirs(image_dir, exist_ok=True)

# List of garden/plant related images from Unsplash
post_images = [
    ("post_1.jpg", "https://images.unsplash.com/photo-1466692476868-aef1dfb1e735"),
    ("post_2.jpg", "https://images.unsplash.com/photo-1523348837708-15d4a09cfac2"),
    ("post_3.jpg", "https://images.unsplash.com/photo-1591857177580-dc82b9ac4e1e"),
    ("post_4.jpg", "https://images.unsplash.com/photo-1582131503261-fca1d1c0589f"),
    ("post_5.jpg", "https://images.unsplash.com/photo-1589876568181-a28611e7294b"),
    ("post_6.jpg", "https://images.unsplash.com/photo-1592150621744-aca64f48394a"),
    ("post_7.jpg", "https://images.unsplash.com/photo-1592150621744-aca64f48394a"),
    ("post_8.jpg", "https://images.unsplash.com/photo-1591857177580-dc82b9ac4e1e"),
    ("post_9.jpg", "https://images.unsplash.com/photo-1523348837708-15d4a09cfac2"),
    ("post_10.jpg", "https://images.unsplash.com/photo-1466692476868-aef1dfb1e735"),
    ("post_11.jpg", "https://images.unsplash.com/photo-1582131503261-fca1d1c0589f"),
    ("post_12.jpg", "https://images.unsplash.com/photo-1589876568181-a28611e7294b"),
    ("post_13.jpg", "https://images.unsplash.com/photo-1592150621744-aca64f48394a"),
    ("post_14.jpg", "https://images.unsplash.com/photo-1466692476868-aef1dfb1e735"),
    ("post_15.jpg", "https://images.unsplash.com/photo-1523348837708-15d4a09cfac2"),
    ("post_16.jpg", "https://images.unsplash.com/photo-1591857177580-dc82b9ac4e1e"),
    ("post_17.jpg", "https://images.unsplash.com/photo-1582131503261-fca1d1c0589f"),
    ("post_18.jpg", "https://images.unsplash.com/photo-1589876568181-a28611e7294b"),
    ("post_19.jpg", "https://images.unsplash.com/photo-1592150621744-aca64f48394a"),
    ("post_20.jpg", "https://images.unsplash.com/photo-1466692476868-aef1dfb1e735"),
]

# Download each image
for filename, url in post_images:
    response = requests.get(url)
    if response.status_code == 200:
        with open(os.path.join(image_dir, filename), 'wb') as f:
            f.write(response.content)
        print(f"Downloaded {filename}")
    else:
        print(f"Failed to download {filename}")

print("Post images download completed!")