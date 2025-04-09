from datetime import datetime, timedelta
import random
import os
import shutil
import requests
from PIL import Image
from io import BytesIO

from greenbyte import db
from run import app
from greenbyte.models import User, Post, PostImage, Garden, Plant
from greenbyte.utils.timezone import now_in_timezone

# Constants for generation
NUM_POSTS = 5  # Number of posts to generate
MAX_IMAGES_PER_POST = 3  # Maximum number of images per post

# List of garden/plant related images from Unsplash
post_images = [
    ("post_11.jpg", "https://images.unsplash.com/photo-1523348837708-15d4a09cfac2"),
    ("post_12.jpg", "https://images.unsplash.com/photo-1466692476868-aef1dfb1e735"),
    ("post_13.jpg", "https://images.unsplash.com/photo-1591857177580-dc82b9ac4e1e"),
    ("post_14.jpg", "https://images.unsplash.com/photo-1582131503261-fca1d1c0589f"),
    ("post_15.jpg", "https://images.unsplash.com/photo-1523348837708-15d4a09cfac2"),
]

# Post content templates
post_titles = [
    "Garden Update: Summer Edition",
    "Dealing with Garden Drought",
    "Organic Pest Control Methods",
    "My New Garden Layout",
    "Seasonal Planting Tips",
]

post_content_templates = [
    "I'm so excited about how my {garden_name} is doing this season! The {plant_name} are {status} and looking beautiful. I've been {action} regularly and it's really paying off.",
    "Just harvested my first {plant_name} from the {garden_name}! They're {description} and I can't wait to {use_case}.",
    "Added some new {plant_name} to my {garden_name} today. I'm hoping they'll {expected_outcome} by {timeframe}.",
    "Garden update: My {garden_name} is coming along nicely. The {plant_name} are {status}, and I've been {action} to keep everything healthy.",
    "Having some trouble with {pest} in my {garden_name}. Has anyone tried {solution}? I'm hoping to save my {plant_name} before it's too late.",
]

# Garden actions
garden_actions = [
    "watering", "fertilizing", "weeding", "pruning", "mulching", 
    "harvesting", "planting", "transplanting", "thinning", "staking"
]

# Plant descriptions
plant_descriptions = [
    "looking healthy", "growing fast", "producing well", "vibrant", 
    "lush", "thriving", "robust", "flourishing", "productive", "vigorous"
]

# Plant use cases
plant_use_cases = [
    "use them in a salad", "cook them for dinner", "share them with neighbors", 
    "make a sauce", "preserve them for winter", "use them in a recipe", 
    "add them to my compost", "dry them for later use", "make tea with them"
]

# Expected outcomes
expected_outcomes = [
    "be ready to harvest", "flower", "fruit", "mature", 
    "establish well", "fill out the space", "provide shade", 
    "attract pollinators", "repel pests", "improve soil health"
]

# Timeframes
timeframes = [
    "next month", "the end of summer", "fall", "next season", 
    "a few weeks", "the end of the year", "spring", "winter"
]

# Garden problems
garden_problems = [
    "aphids", "powdery mildew", "fungus gnats", "tomato blight", 
    "slugs", "cabbage worms", "root rot", "nutrient deficiency", 
    "overwatering", "underwatering"
]

# Solutions
solutions = [
    "neem oil spray", "companion planting", "diatomaceous earth", 
    "beneficial insects", "organic pesticides", "crop rotation", 
    "better drainage", "more consistent watering", "adding compost", 
    "using row covers"
]

# Categories
categories = ["Vegetables", "Herbs", "Flowers", "Fruits", "Indoor Plants", "Succulents"]

def download_image(url, filename):
    """Download an image from a URL and save it to the static/post_pics directory"""
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        # Create directory if it doesn't exist
        os.makedirs('greenbyte/static/post_pics', exist_ok=True)
        
        # Open the image and resize it
        img = Image.open(BytesIO(response.content))
        
        # Resize to a reasonable size for a blog post (max 1200px width)
        max_width = 1200
        if img.width > max_width:
            ratio = max_width / img.width
            new_height = int(img.height * ratio)
            img = img.resize((max_width, new_height), Image.LANCZOS)
        
        # Save the image
        img.save(f'greenbyte/static/post_pics/{filename}')
        return True
    except Exception as e:
        print(f"Error downloading image {url}: {e}")
        return False

def generate_posts():
    """Generate random posts with and without images"""
    with app.app_context():
        # Get all users
        users = User.query.all()
        if not users:
            print("No users found in the database. Please run database_generator.py first.")
            return
        
        # Get all gardens
        gardens = Garden.query.all()
        if not gardens:
            print("No gardens found in the database. Please run database_generator.py first.")
            return
        
        # Get all plants
        plants = Plant.query.all()
        if not plants:
            print("No plants found in the database. Please run database_generator.py first.")
            return
        
        # Download images if they don't exist
        for filename, url in post_images:
            if not os.path.exists(f'greenbyte/static/post_pics/{filename}'):
                print(f"Downloading image {filename}...")
                download_image(url, filename)
        
        # Generate posts
        for i in range(NUM_POSTS):
            # Select a random user
            user = random.choice(users)
            
            # Select a random garden (optionally)
            garden = random.choice(gardens) if random.random() < 0.7 else None
            
            # Select a random title
            title = post_titles[i % len(post_titles)]
            
            # Generate content
            template = random.choice(post_content_templates)
            
            # Replace placeholders with random values
            content = template.format(
                garden_name=garden.name if garden else "my garden",
                plant_name=random.choice(plants).plant_detail.name if plants else "plants",
                status=random.choice(plant_descriptions),
                action=random.choice(garden_actions),
                description=random.choice(plant_descriptions),
                use_case=random.choice(plant_use_cases),
                expected_outcome=random.choice(expected_outcomes),
                timeframe=random.choice(timeframes),
                pest=random.choice(garden_problems),
                solution=random.choice(solutions),
            )
            
            # Add some more paragraphs to make the content longer
            content += "\n\n" + random.choice(post_content_templates).format(
                garden_name=garden.name if garden else "my garden",
                plant_name=random.choice(plants).plant_detail.name if plants else "plants",
                status=random.choice(plant_descriptions),
                action=random.choice(garden_actions),
                description=random.choice(plant_descriptions),
                use_case=random.choice(plant_use_cases),
                expected_outcome=random.choice(expected_outcomes),
                timeframe=random.choice(timeframes),
                pest=random.choice(garden_problems),
                solution=random.choice(solutions),
            )
            
            # Create a random date within the last 30 days
            days_ago = random.randint(0, 30)
            date_posted = now_in_timezone() - timedelta(days=days_ago)
            
            # Calculate read time (roughly 1 minute per 200 words)
            word_count = len(content.split())
            read_time = max(1, word_count // 200)
            
            # Create the post
            post = Post(
                title=title,
                content=content,
                date_posted=date_posted,
                read_time=read_time,
                category=random.choice(categories),
                user_id=user.id,
                garden_id=garden.id if garden else None,
                garden_type=f"{random.choice(['Indoor', 'Outdoor', 'Balcony', 'Rooftop', 'Community'])} Garden" if garden else None,
                garden_size=random.randint(10, 1000) if garden else None,
                plant_count=random.randint(1, 50) if garden else None,
                start_date=date_posted - timedelta(days=random.randint(30, 365)) if garden else None,
                sunlight=random.choice(['Full Sun', 'Partial Shade', 'Full Shade']) if garden else None,
                watering=random.choice(['Daily', 'Weekly', 'Bi-weekly']) if garden else None,
                zone=f"Zone {random.randint(1, 13)}" if garden else None,
            )
            
            db.session.add(post)
            db.session.flush()  # Get the post ID
            
            # For this batch, alternate between posts with and without images
            if i % 2 == 0:
                # Add 1-3 random images
                num_images = random.randint(1, min(MAX_IMAGES_PER_POST, len(post_images)))
                selected_images = random.sample(post_images, num_images)
                
                for j, (filename, _) in enumerate(selected_images):
                    # Create a post image
                    post_image = PostImage(
                        post_id=post.id,
                        image_file=filename,
                        caption=f"Image {j+1} for {post.title}",
                        order=j
                    )
                    db.session.add(post_image)
            
        # Commit all changes
        db.session.commit()
        print(f"Generated {NUM_POSTS} posts (some with images, some without)")

if __name__ == "__main__":
    generate_posts()
