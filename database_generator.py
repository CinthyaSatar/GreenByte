from datetime import datetime, timedelta
from greenbyte import db
from run import app
from greenbyte.models import (
    User, Garden, Zone, Plant, PlantTracking, Post, PostImage, PostPlant,
    Harvest, Client, Order, OrderItem, Delivery, Payment
)
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import random
from flask_bcrypt import Bcrypt
import faker
from greenbyte.utils.timezone import now_in_timezone, get_current_timezone

bcrypt = Bcrypt(app)
fake = faker.Faker()

def generate_database():
    with app.app_context():
        # Get current time in configured timezone
        current_time = now_in_timezone()
        
        # Clear existing data
        db.drop_all()
        db.session.commit()
        db.create_all()
        
        # Sample profile and garden images
        profile_images = [f"profile_{i}.jpg" for i in range(1, 11)]
        garden_images = [f"garden_{i}.jpg" for i in range(1, 11)]
        post_images = [f"post_{i}.jpg" for i in range(1, 21)]  # Make sure this matches the number of images downloaded

        # Create sample users (50)
        users = []
        hashed_password = bcrypt.generate_password_hash('password123').decode('utf-8')
        
        # Create one admin user
        admin = User(
            username="admin",
            firstName="Admin",
            lastName="User",
            email="admin@example.com",
            password=hashed_password,
            location="San Francisco, CA",
            bio="Garden enthusiast and sustainability advocate. Managing multiple urban farming projects.",
            image_file="default.jpg"  # Set default profile picture
        )
        users.append(admin)

        # Create regular users
        for i in range(49):
            first_name = fake.first_name()
            last_name = fake.last_name()
            user = User(
                username=f"{first_name.lower()}{last_name.lower()}{random.randint(1,999)}",
                firstName=first_name,
                lastName=last_name,
                email=f"{first_name.lower()}.{last_name.lower()}@example.com",
                password=hashed_password,
                location=fake.city() + ", " + fake.state_abbr(),
                bio=fake.paragraph(nb_sentences=3),
                image_file="default.jpg"  # Set default profile picture
            )
            users.append(user)
        db.session.add_all(users)
        db.session.commit()

        # Create gardens (100)
        gardens = []
        garden_types = [
            "Backyard Garden",
            "Community Garden",
            "Commercial Farm",
            "Urban Garden",
            "Greenhouse",
            "Rooftop Garden",
            "Indoor Garden"
        ]
        
        for i in range(100):
            owner = random.choice(users)
            garden_size = round(random.uniform(100, 1000), 2)
            
            # Create timestamps in the correct timezone
            created_at = current_time - timedelta(days=random.randint(30, 365))
            updated_at = created_at + timedelta(days=random.randint(0, 30))
            
            # Convert timezone to string
            timezone_str = str(get_current_timezone())  # This will convert ZoneInfo to string like 'America/Montreal'
            
            garden = Garden(
                name=fake.company() + " " + random.choice(["Garden", "Farm", "Greenhouse", "Nursery"]),
                location=fake.address(),
                owner_id=owner.id,
                garden_type=random.choice(garden_types),
                garden_size=garden_size,
                created_at=created_at,
                updated_at=updated_at,
                last_updated=updated_at,
                timezone=timezone_str  # Use the string version
            )
            gardens.append(garden)
            
            # Add owner as a member
            garden.members.append(owner)
            
            # Add 1-3 random members
            num_members = random.randint(1, 3)
            potential_members = [u for u in users if u != owner]
            members = random.sample(potential_members, num_members)
            for member in members:
                garden.members.append(member)
        
        # Add all gardens at once and commit
        db.session.add_all(gardens)
        db.session.commit()

        # Create zones (300)
        zones = []
        sunlight_types = ["Full Sun", "Partial Sun", "Partial Shade", "Full Shade"]
        soil_types = ["Loamy", "Sandy", "Clay", "Silt", "Peat", "Chalky"]
        watering_schedules = ["Daily", "Twice Daily", "Every Other Day", "Weekly"]
        temperature_ranges = ["55-65°F", "65-75°F", "75-85°F", "85-95°F"]
        ph_levels = ["5.5-6.0", "6.0-6.5", "6.5-7.0", "7.0-7.5"]
        organic_matter_levels = ["Low", "Medium", "High", "Very High"]
        
        for i in range(300):
            # Get a random garden that's already in the database
            garden = random.choice(gardens)
            
            zone = Zone(
                name=fake.word() + " Zone",
                garden_id=garden.id,  # This will now have a valid ID
                sunlight=random.choice(sunlight_types),
                soil_type=random.choice(soil_types),
                watering=random.choice(watering_schedules),
                temperature=random.choice(temperature_ranges),
                ph_level=random.choice(ph_levels),
                organic_matter=random.choice(organic_matter_levels)
            )
            zones.append(zone)
        
        # Add all zones at once
        db.session.add_all(zones)
        db.session.commit()

        # Updated plant types with recurring harvest information
        plant_types = [
            ("Tomato", ["Cherry", "Beefsteak", "Roma", "Grape"], True, 14),
            ("Pepper", ["Bell", "Jalapeño", "Habanero", "Sweet"], True, 14),
            ("Lettuce", ["Romaine", "Butterhead", "Iceberg"], True, 7),
            ("Basil", ["Sweet", "Thai", "Purple"], True, 10),
            ("Mint", ["Spearmint", "Peppermint"], True, 14),
            ("Carrot", ["Nantes", "Imperator", "Danvers"], False, None),
            ("Potato", ["Russet", "Yukon Gold", "Red"], False, None),
            ("Cucumber", ["English", "Persian", "Pickling"], True, 7),
            ("Kale", ["Curly", "Dinosaur", "Red Russian"], True, 10),
            ("Spinach", ["Savoy", "Flat-leaf", "Baby"], True, 7),
        ]

        # Create plants (600)
        plants = []
        plant_statuses = ['Seedling', 'Growing', 'Mature', 'Blooming', 'Fruiting', 'Ready', 'Harvesting', 'Regrowth']
        
        for i in range(600):
            zone = random.choice(zones)
            plant_info = random.choice(plant_types)
            plant_type, varieties, is_recurring, harvest_freq = plant_info
            
            planting_date = current_time - timedelta(days=random.randint(30, 120))
            maturity_date = planting_date + timedelta(days=random.randint(60, 120))
            
            plant = Plant(
                name=plant_type,
                variety=random.choice(varieties),
                zone_id=zone.id,
                quantity=random.randint(5, 50),  # Added random quantity between 5 and 50
                planting_date=planting_date,
                maturity_date=maturity_date,
                flowering_date=planting_date + timedelta(days=random.randint(20, 40)),
                fruiting_date=planting_date + timedelta(days=random.randint(40, 80)),
                status=random.choice(plant_statuses),
                is_recurring_harvest=is_recurring,
                harvest_frequency_days=harvest_freq,
                total_harvests=0
            )
            
            plants.append(plant)

        # First commit all plants to get their IDs
        db.session.add_all(plants)
        db.session.commit()

        # Now create harvests and tracking entries
        for plant in plants:
            # Generate some harvest records for mature plants
            if plant.status in ['Harvesting', 'Regrowth'] and plant.is_recurring_harvest:
                num_harvests = random.randint(1, 5)
                plant.total_harvests = num_harvests
                
                for h in range(num_harvests):
                    harvest_date = plant.planting_date + timedelta(days=(60 + (h * plant.harvest_frequency_days)))
                    harvest = Harvest(
                        plant_id=plant.id,
                        date=harvest_date,
                        completed_date=harvest_date + timedelta(days=random.randint(1, 3)),
                        amount_collected=round(random.uniform(0.5, 5.0), 2),
                        notes=f"Harvest #{h+1}",
                        harvest_number=h+1
                    )
                    db.session.add(harvest)
                
                # Set next harvest date if plant is still active
                if plant.status != 'Completed':
                    plant.next_harvest_date = current_time + timedelta(days=random.randint(1, plant.harvest_frequency_days))
            
            # Add plant tracking entries
            tracking = PlantTracking(
                plant_id=plant.id,
                stage=plant.status,
                date_logged=current_time - timedelta(days=random.randint(1, 30)),
                notes=f"Plant reached {plant.status} stage"
            )
            db.session.add(tracking)

        # Commit all harvests and tracking entries
        db.session.commit()

        # Create sample posts (150)
        posts = []
        post_titles = [
            "My Garden Journey", "Growing Success", "Garden Update", 
            "Harvest Time", "Planting Season", "Garden Tips"
        ]
        post_contents = [
            "Today I'm excited to share my progress with {plants}...",
            "Finally harvested my {plants} and they turned out great!",
            "Started growing some new {plants} in the garden...",
            "Here's what I learned about growing {plants}..."
        ]
        categories = ["Vegetables", "Herbs", "Flowers", "Fruits", "Maintenance", "Planning"]
        
        for i in range(150):
            author = random.choice(users)
            if author.gardens:
                garden = random.choice(author.gardens)
                
                # Format content with random plant names
                content_template = random.choice(post_contents)
                plant_names = [p.name for p in random.sample(plants, 2)]
                content = content_template.format(plants=", ".join(plant_names))
                
                post = Post(
                    title=f"{random.choice(post_titles)} #{i+1}",
                    content=content,
                    user_id=author.id,
                    garden_id=garden.id,
                    date_posted=current_time - timedelta(days=random.randint(1, 90)),
                    read_time=random.randint(2, 10),
                    category=random.choice(categories)
                )
                db.session.add(post)
                db.session.flush()  # This ensures post.id is available
                
                # Add 1-3 images to the post
                num_images = random.randint(1, 3)
                for j in range(num_images):
                    post_image = PostImage(
                        post_id=post.id,
                        image_file=random.choice(post_images),
                        caption=f"Garden photo #{j+1}",
                        order=j
                    )
                    db.session.add(post_image)
                
                posts.append(post)
                
                if len(posts) % 10 == 0:  # Commit every 10 posts
                    db.session.commit()

        print("Sample data generated successfully!")

if __name__ == "__main__":
    generate_database()
