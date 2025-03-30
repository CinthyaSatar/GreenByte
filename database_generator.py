from datetime import datetime, timedelta
from greenbyte import db
from run import app
from greenbyte.models import (
    User, Garden, Zone, Plant, PlantTracking, Post, PostImage, PostPlant,
    Harvest, Client, Order, OrderItem, Delivery, Payment, PlantAttribute,
    PlantDetail, PlantVariety, PlantStatus  # Added PlantStatus here
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
        # Disable autoflush temporarily
        with db.session.no_autoflush:
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
            used_emails = {'admin@example.com'}  # Track used emails
            for i in range(49):
                first_name = fake.first_name()
                last_name = fake.last_name()
                
                # Generate unique email
                while True:
                    email = f"{first_name.lower()}.{last_name.lower()}{random.randint(1,999)}@example.com"
                    if email not in used_emails:
                        used_emails.add(email)
                        break
                
                user = User(
                    username=f"{first_name.lower()}{last_name.lower()}{random.randint(1,999)}",
                    firstName=first_name,
                    lastName=last_name,
                    email=email,  # Use the unique email
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
                
                # Create timestamp in the correct timezone
                updated_at = current_time - timedelta(days=random.randint(0, 365))
                
                # Convert timezone to string
                timezone_str = str(get_current_timezone())
                
                garden = Garden(
                    name=fake.company() + " " + random.choice(["Garden", "Farm", "Greenhouse", "Nursery"]),
                    location=fake.address(),
                    owner_id=owner.id,
                    garden_type=random.choice(garden_types),
                    garden_size=garden_size,
                    timezone=timezone_str,
                    last_updated=updated_at
                )
                gardens.append(garden)
            
            # Add all gardens at once
            db.session.add_all(gardens)
            db.session.commit()

            # Now handle garden memberships separately
            for garden in gardens:
                # First, ensure the owner is a member with 'manager' role
                if garden.owner not in garden.members:
                    garden.add_member(garden.owner, role='manager')
                
                # Add 1-3 random members
                num_members = random.randint(1, 3)
                potential_members = [u for u in users if u != garden.owner and u not in garden.members]
                if potential_members:  # Only proceed if there are potential members available
                    members = random.sample(potential_members, min(num_members, len(potential_members)))
                    for member in members:
                        garden.add_member(member, role='member')
                
                # Commit after each garden's members are added
                db.session.commit()

            # Create zones (300)
            zones = []
            sunlight_types = ["Full Sun", "Partial Sun", "Partial Shade", "Full Shade"]
            soil_types = ["Loamy", "Sandy", "Clay", "Silt", "Peat", "Chalky"]
            watering_schedules = ["Daily", "Twice Daily", "Every Other Day", "Weekly"]
            temperature_ranges = ["55-65°F", "65-75°F", "75-85°F", "85-95°F"]
            ph_levels = ["5.5-6.0", "6.0-6.5", "6.5-7.0", "7.0-7.5"]
            organic_matter_levels = ["Low", "Medium", "High", "Very High"]
            
            # First create all zones with basic information
            for i in range(300):
                garden = random.choice(gardens)
                zone = Zone(
                    name=fake.word() + " Zone",
                    garden_id=garden.id
                )
                zones.append(zone)
            
            # Add all zones at once and commit to get IDs
            db.session.add_all(zones)
            db.session.commit()
            
            # Now set attributes for each zone
            for zone in zones:
                # Set growing conditions
                zone.set_growing_condition('sunlight', random.choice(sunlight_types))
                zone.set_growing_condition('watering', random.choice(watering_schedules))
                zone.set_growing_condition('temperature', random.choice(temperature_ranges))
                
                # Set soil information
                zone.set_soil_info('soil_type', random.choice(soil_types))
                zone.set_soil_info('ph_level', random.choice(ph_levels))
                zone.set_soil_info('organic_matter', random.choice(organic_matter_levels))
                
                # Commit after each zone's attributes are set
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
            for i in range(600):
                zone = random.choice(zones)
                plant_info = random.choice(plant_types)
                plant_type, varieties, is_recurring, harvest_freq = plant_info
                
                planting_date = current_time - timedelta(days=random.randint(30, 120))
                
                # First create or get a PlantDetail
                plant_detail = PlantDetail.query.filter_by(name=plant_type).first()
                if not plant_detail:
                    plant_detail = PlantDetail(
                        name=plant_type,
                        category="Vegetable",
                        description=fake.paragraph()
                    )
                    db.session.add(plant_detail)
                    db.session.commit()
                
                # Create the plant
                plant = Plant(
                    plant_detail_id=plant_detail.id,
                    zone_id=zone.id,
                    quantity=random.randint(5, 50),
                    planting_date=planting_date
                )
                plants.append(plant)
            
            # Add all plants at once
            db.session.add_all(plants)
            db.session.flush()  # Ensure all plants have IDs

            # Create initial tracking for each plant
            tracking_records = []
            for plant in plants:
                initial_tracking = PlantTracking(
                    plant_id=plant.id,
                    stage='Seedling',
                    date_logged=plant.planting_date,
                    notes='Initial plant stage'
                )
                tracking_records.append(initial_tracking)
            
            db.session.add_all(tracking_records)
            db.session.commit()

            # Now add additional growth stages
            additional_tracking = []
            plant_stages = ['Growing', 'Mature', 'Blooming', 'Fruiting', 'Ready', 'Harvesting', 'Regrowth']
            stage_notes = {
                'Growing': ['Healthy growth observed', 'New leaves forming', 'Plant developing well'],
                'Mature': ['Plant reached maturity', 'Full size achieved', 'Strong and healthy'],
                'Blooming': ['First flowers appearing', 'Multiple blooms visible', 'Peak flowering stage'],
                'Fruiting': ['Fruit set beginning', 'Developing fruit observed', 'Multiple fruits forming'],
                'Ready': ['Ready for harvest', 'Optimal harvest time', 'Peak ripeness achieved'],
                'Harvesting': ['First harvest complete', 'Ongoing harvests', 'Regular harvesting in progress'],
                'Regrowth': ['New growth after harvest', 'Plant recovering well', 'Secondary growth phase']
            }
            
            for plant in plants:
                num_updates = random.randint(2, 4)
                possible_stages = plant_stages[:random.randint(1, len(plant_stages))]
                
                for j in range(num_updates):
                    stage = possible_stages[min(j, len(possible_stages) - 1)]
                    days_after_planting = random.randint(5, 90)
                    stage_date = plant.planting_date + timedelta(days=days_after_planting)
                    
                    tracking = PlantTracking(
                        plant_id=plant.id,
                        stage=stage,
                        date_logged=stage_date,
                        notes=random.choice(stage_notes[stage])
                    )
                    additional_tracking.append(tracking)
            
            db.session.add_all(additional_tracking)
            db.session.commit()

            # Generate harvests for plants
            harvests = []
            for plant in plants:
                # Get the plant type info to determine if it's recurring
                plant_type = plant.plant_detail.name
                plant_info = next((info for info in plant_types if info[0] == plant_type), None)
                is_recurring = plant_info[2] if plant_info else False
                harvest_freq = plant_info[3] if plant_info else 14
                
                # Only generate harvests for plants that are mature enough
                if plant.status in ['Mature', 'Fruiting', 'Ready', 'Harvesting', 'Regrowth']:
                    # Generate between 1-5 harvests for recurring plants, 1 harvest for non-recurring
                    num_harvests = random.randint(1, 5) if is_recurring else 1
                    
                    last_harvest_date = None
                    current_tz = get_current_timezone()
                    
                    for harvest_num in range(num_harvests):
                        if last_harvest_date is None:
                            # First harvest happens after maturity (60-90 days after planting)
                            maturity_date = plant.planting_date.replace(tzinfo=current_tz) + timedelta(days=random.randint(60, 90))
                            harvest_date = maturity_date + timedelta(days=random.randint(1, 14))
                        else:
                            # Subsequent harvests follow the frequency pattern
                            harvest_date = last_harvest_date + timedelta(days=harvest_freq)
                        
                        # Only create harvest if it's not in the future
                        if harvest_date <= current_time:
                            completed_date = harvest_date + timedelta(hours=random.randint(1, 8))
                            
                            harvest = Harvest(
                                plant_id=plant.id,
                                date=harvest_date,
                                completed_date=completed_date,
                                amount_collected=round(random.uniform(0.1, 5.0), 2),
                                notes=f"Harvest #{harvest_num + 1}",
                                harvest_number=harvest_num + 1
                            )
                            harvests.append(harvest)
                            last_harvest_date = harvest_date
                            plant.total_harvests = harvest_num + 1
                    
                    # Set next harvest date if plant is still active and is recurring
                    if plant.status in ['Harvesting', 'Regrowth'] and is_recurring:
                        if last_harvest_date:
                            plant.next_harvest_date = last_harvest_date + timedelta(days=harvest_freq)
                        else:
                            plant.next_harvest_date = current_time + timedelta(days=random.randint(1, harvest_freq))
                
                # Add plant tracking entries
                tracking = PlantTracking(
                    plant_id=plant.id,
                    stage=plant.status,
                    date_logged=current_time - timedelta(days=random.randint(1, 30)),
                    notes=f"Plant reached {plant.status} stage"
                )
                db.session.add(tracking)

            # Commit all harvests and tracking entries
            db.session.add_all(harvests)
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
                    
                    # Format content with random plant names - using plant_detail.name instead of plant.name
                    content_template = random.choice(post_contents)
                    plant_names = [p.plant_detail.name for p in random.sample(plants, 2)]
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

def add_basic_plants():
    with app.app_context():  # Add this line to create application context
        basic_plants = [
            {"name": "Tomato", "description": "Various tomato varieties"},
            {"name": "Lettuce", "description": "Leafy greens"},
            {"name": "Pepper", "description": "Bell and chili peppers"},
            {"name": "Cucumber", "description": "Climbing vine vegetable"},
            {"name": "Carrot", "description": "Root vegetable"},
            {"name": "Basil", "description": "Aromatic herb"},
            {"name": "Strawberry", "description": "Sweet berries"},
            {"name": "Spinach", "description": "Nutrient-rich leafy green"}
        ]
        
        for plant_data in basic_plants:
            plant = PlantDetail.query.filter_by(name=plant_data["name"]).first()
            if not plant:
                plant = PlantDetail(
                    name=plant_data["name"],
                    description=plant_data["description"]
                )
                db.session.add(plant)
        
        db.session.commit()

def add_varieties():
    with app.app_context():
        # Dictionary of plant varieties
        plant_varieties = {
            "Tomato": ["Cherry", "Beefsteak", "Roma", "Grape", "San Marzano"],
            "Lettuce": ["Romaine", "Butterhead", "Iceberg", "Red Leaf"],
            "Pepper": ["Bell", "Jalapeño", "Habanero", "Thai Chili"],
            "Cucumber": ["English", "Persian", "Pickling", "Lemon"],
            "Carrot": ["Nantes", "Imperator", "Danvers", "Chantenay"],
            "Basil": ["Sweet", "Thai", "Purple", "Lemon"],
            "Strawberry": ["June-bearing", "Ever-bearing", "Day-neutral"],
            "Spinach": ["Savoy", "Flat-leaf", "Baby", "New Zealand"]
        }
        
        for plant_name, varieties in plant_varieties.items():
            plant_detail = PlantDetail.query.filter_by(name=plant_name).first()
            if plant_detail:
                for variety_name in varieties:
                    # Check if variety already exists
                    existing_variety = PlantVariety.query.filter_by(
                        plant_detail_id=plant_detail.id,
                        name=variety_name
                    ).first()
                    
                    if not existing_variety:
                        variety = PlantVariety(
                            plant_detail_id=plant_detail.id,
                            name=variety_name,
                            description=f"A {variety_name} variety of {plant_name}"
                        )
                        db.session.add(variety)
        
        db.session.commit()

if __name__ == "__main__":
    generate_database()
    add_basic_plants()
    add_varieties()  # Add this line to create varieties
