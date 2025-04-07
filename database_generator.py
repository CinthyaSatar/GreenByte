from datetime import datetime, timedelta
import random

from flask_bcrypt import Bcrypt
import faker

from greenbyte import db
from run import app
from greenbyte.models import (
    User, Garden, Zone, Plant, PlantTracking, PlantDetail, PlantVariety, PlantStage,
    CalendarEvent, CalendarEventInvitee
)
from greenbyte.utils.timezone import now_in_timezone

bcrypt = Bcrypt(app)
fake = faker.Faker()

# Constants for generation
NUM_USERS = 5
NUM_GARDENS = 3
MAX_MEMBERS_PER_GARDEN = 3
MAX_ZONES_PER_GARDEN = 4
MAX_PLANTS_PER_ZONE = 6
NUM_EVENTS_PER_USER = 5  # Number of calendar events to generate per user

def generate_database():
    with app.app_context():
        with db.session.no_autoflush:
            current_time = now_in_timezone()

            # Clear existing data
            db.drop_all()
            db.session.commit()
            db.create_all()

            # Create users
            users = []
            default_password = bcrypt.generate_password_hash('password').decode('utf-8')

            # Create main test user
            main_user = User(
                username='testuser',
                firstName='Test',
                lastName='User',
                email='test@example.com',
                password=default_password
            )
            db.session.add(main_user)
            users.append(main_user)

            # Create additional users
            for i in range(1, NUM_USERS):
                first_name = fake.first_name()
                last_name = fake.last_name()
                username = f"{first_name.lower()}{last_name.lower()}{random.randint(1, 99)}"

                user = User(
                    username=username,
                    firstName=first_name,
                    lastName=last_name,
                    email=f"{username}@example.com",
                    password=default_password
                )
                db.session.add(user)
                users.append(user)

            db.session.commit()
            print(f"Created {len(users)} users")

            # Create gardens
            gardens = []
            garden_names = [
                'My Test Garden', 'Community Garden', 'Rooftop Garden',
                'Indoor Garden', 'Vertical Garden', 'Container Garden'
            ]
            garden_locations = [
                'Backyard', 'Front Yard', 'Community Center', 'Rooftop',
                'Balcony', 'Window Sill', 'Patio', 'Greenhouse'
            ]

            # Ensure main user has a garden
            main_garden = Garden(
                name=garden_names[0],
                location=garden_locations[0],
                owner_id=main_user.id
            )
            db.session.add(main_garden)
            gardens.append(main_garden)

            # Add main user as a member of their own garden
            main_garden.members.append(main_user)

            # Create additional gardens with random owners
            for i in range(1, NUM_GARDENS):
                owner = random.choice(users)
                garden_name = garden_names[i % len(garden_names)]
                garden_location = random.choice(garden_locations)

                garden = Garden(
                    name=f"{owner.firstName}'s {garden_name}",
                    location=garden_location,
                    owner_id=owner.id
                )
                db.session.add(garden)
                gardens.append(garden)

                # Add owner as a member
                garden.members.append(owner)

                # Add random members to each garden
                potential_members = [u for u in users if u != owner]
                num_members = random.randint(1, min(MAX_MEMBERS_PER_GARDEN, len(potential_members)))
                garden_members = random.sample(potential_members, num_members)

                for member in garden_members:
                    garden.members.append(member)

            db.session.commit()
            print(f"Created {len(gardens)} gardens with members")

            # Create zones for each garden
            zones = []
            zone_names = [
                'Vegetable Patch', 'Herb Garden', 'Berry Patch', 'Flower Bed',
                'Greenhouse Area', 'Raised Beds', 'Container Section', 'Shade Garden',
                'Sunny Spot', 'Vertical Garden', 'Hydroponic Setup', 'Aquaponic System'
            ]

            for garden in gardens:
                # Determine how many zones for this garden
                num_zones = random.randint(1, min(MAX_ZONES_PER_GARDEN, len(zone_names)))
                garden_zone_names = random.sample(zone_names, num_zones)

                for name in garden_zone_names:
                    zone = Zone(
                        name=name,
                        garden_id=garden.id
                    )
                    db.session.add(zone)
                    zones.append(zone)

            db.session.commit()
            print(f"Created {len(zones)} zones across all gardens")

            # Plant data
            plant_details = [
                {
                    "name": "Tomato",
                    "scientific_name": "Solanum lycopersicum",
                    "category": "Vegetable",
                    "description": "A versatile fruit commonly used as a vegetable",
                    "attributes": {
                        "growing_info": {
                            "days_to_maturity": "60-80",
                            "spacing": "24-36 inches",
                            "sun_requirements": "Full sun"
                        }
                    },
                    "varieties": ["Roma", "Cherry", "Beefsteak", "San Marzano", "Brandywine", "Green Zebra", "Yellow Pear"]
                },
                {
                    "name": "Lettuce",
                    "scientific_name": "Lactuca sativa",
                    "category": "Vegetable",
                    "description": "A leafy green perfect for salads",
                    "attributes": {
                        "growing_info": {
                            "days_to_maturity": "30-60",
                            "spacing": "6-8 inches",
                            "sun_requirements": "Partial shade"
                        }
                    },
                    "varieties": ["Romaine", "Iceberg", "Butterhead", "Red Leaf", "Oak Leaf", "Arugula", "Mesclun Mix"]
                },
                {
                    "name": "Basil",
                    "scientific_name": "Ocimum basilicum",
                    "category": "Herb",
                    "description": "Aromatic herb essential in many cuisines",
                    "attributes": {
                        "growing_info": {
                            "days_to_maturity": "50-75",
                            "spacing": "12-18 inches",
                            "sun_requirements": "Full sun"
                        }
                    },
                    "varieties": ["Sweet Basil", "Thai Basil", "Purple Basil", "Genovese", "Lemon Basil", "Cinnamon Basil"]
                },
                {
                    "name": "Strawberry",
                    "scientific_name": "Fragaria × ananassa",
                    "category": "Fruit",
                    "description": "Sweet berries perfect for home gardens",
                    "attributes": {
                        "growing_info": {
                            "days_to_maturity": "90-120",
                            "spacing": "12-18 inches",
                            "sun_requirements": "Full sun"
                        }
                    },
                    "varieties": ["June-bearing", "Everbearing", "Day-neutral", "Alpine", "Seascape", "Chandler"]
                },
                {
                    "name": "Pepper",
                    "scientific_name": "Capsicum annuum",
                    "category": "Vegetable",
                    "description": "Versatile vegetables ranging from sweet to spicy",
                    "attributes": {
                        "growing_info": {
                            "days_to_maturity": "60-90",
                            "spacing": "18-24 inches",
                            "sun_requirements": "Full sun"
                        }
                    },
                    "varieties": ["Bell", "Jalapeño", "Habanero", "Cayenne", "Poblano", "Sweet Banana", "Serrano"]
                },
                {
                    "name": "Cucumber",
                    "scientific_name": "Cucumis sativus",
                    "category": "Vegetable",
                    "description": "Refreshing vegetable perfect for salads and pickling",
                    "attributes": {
                        "growing_info": {
                            "days_to_maturity": "50-70",
                            "spacing": "36-60 inches",
                            "sun_requirements": "Full sun"
                        }
                    },
                    "varieties": ["Slicing", "Pickling", "English", "Lemon", "Armenian", "Persian"]
                },
                {
                    "name": "Mint",
                    "scientific_name": "Mentha",
                    "category": "Herb",
                    "description": "Aromatic herb used in teas, desserts, and savory dishes",
                    "attributes": {
                        "growing_info": {
                            "days_to_maturity": "60-90",
                            "spacing": "18-24 inches",
                            "sun_requirements": "Partial shade"
                        }
                    },
                    "varieties": ["Peppermint", "Spearmint", "Chocolate Mint", "Apple Mint", "Moroccan Mint"]
                },
                {
                    "name": "Blueberry",
                    "scientific_name": "Vaccinium",
                    "category": "Fruit",
                    "description": "Antioxidant-rich berries that grow on bushes",
                    "attributes": {
                        "growing_info": {
                            "days_to_maturity": "730-1095",  # 2-3 years
                            "spacing": "4-6 feet",
                            "sun_requirements": "Full sun to partial shade"
                        }
                    },
                    "varieties": ["Highbush", "Lowbush", "Rabbiteye", "Duke", "Bluecrop", "Patriot"]
                }
            ]

            # Create plant details and varieties
            plant_detail_objects = {}
            for plant in plant_details:
                plant_detail = PlantDetail(
                    name=plant["name"],
                    scientific_name=plant["scientific_name"],
                    category=plant["category"],
                    description=plant["description"]
                )
                db.session.add(plant_detail)
                db.session.flush()

                # Add attributes
                for category, attributes in plant["attributes"].items():
                    for name, value in attributes.items():
                        plant_detail.set_attribute(name, value, category)

                # Create varieties
                for variety_name in plant["varieties"]:
                    variety = PlantVariety(
                        name=variety_name,
                        plant_detail_id=plant_detail.id,
                        description=f"A popular {plant['name'].lower()} variety"
                    )
                    db.session.add(variety)

                plant_detail_objects[plant["name"]] = plant_detail

            db.session.commit()

            # Add plants to appropriate zones
            for zone in zones:
                # Select plants based on zone type
                suitable_plants = []
                if "Vegetable" in zone.name:
                    suitable_plants = [p for p in plant_details if p["category"] == "Vegetable"]
                elif "Herb" in zone.name:
                    suitable_plants = [p for p in plant_details if p["category"] == "Herb"]
                elif "Berry" in zone.name or "Fruit" in zone.name:
                    suitable_plants = [p for p in plant_details if p["category"] == "Fruit"]
                elif "Flower" in zone.name:
                    # Use any plant type for flower beds
                    suitable_plants = plant_details
                else:
                    # For other zones, use any plant type
                    suitable_plants = plant_details

                # Add plants to each zone
                num_plants = random.randint(1, min(MAX_PLANTS_PER_ZONE, len(suitable_plants) * 2))
                for _ in range(num_plants):
                    if suitable_plants:
                        plant_info = random.choice(suitable_plants)
                        plant_detail = plant_detail_objects[plant_info["name"]]
                        variety = random.choice(plant_detail.varieties)

                        # Create a random planting date between 7 and 120 days ago
                        days_ago = random.randint(7, 120)
                        planting_date = current_time - timedelta(days=days_ago)

                        plant = Plant(
                            plant_detail_id=plant_detail.id,
                            variety_id=variety.id,
                            zone_id=zone.id,
                            quantity=random.randint(1, 15),
                            planting_date=planting_date
                        )
                        db.session.add(plant)
                        db.session.flush()

                        # Determine appropriate plant stage based on age
                        stage = PlantStage.SEEDLING.value
                        if days_ago > 90:
                            stage_options = [PlantStage.MATURE.value, PlantStage.HARVESTING.value, PlantStage.FRUITING.value]
                            stage = random.choice(stage_options)
                        elif days_ago > 60:
                            stage_options = [PlantStage.GROWING.value, PlantStage.FLOWERING.value]
                            stage = random.choice(stage_options)
                        elif days_ago > 30:
                            stage = PlantStage.GROWING.value

                        # Add initial tracking entry at planting time
                        initial_tracking = PlantTracking(
                            plant_id=plant.id,
                            stage=PlantStage.SEEDLING.value,
                            notes=f"Initial planting of {plant_detail.name} ({variety.name})",
                            date_logged=planting_date
                        )
                        db.session.add(initial_tracking)

                        # Add current status tracking entry if plant has progressed beyond seedling
                        if stage != PlantStage.SEEDLING.value:
                            status_date = current_time - timedelta(days=random.randint(1, min(7, days_ago - 1)))
                            current_tracking = PlantTracking(
                                plant_id=plant.id,
                                stage=stage,
                                notes=f"Updated status to {stage}",
                                date_logged=status_date
                            )
                            db.session.add(current_tracking)

            # Generate calendar events
            events = []
            event_titles = [
                "Water Plants", "Fertilize Garden", "Harvest Vegetables", "Plant Seeds",
                "Prune Trees", "Check Soil pH", "Apply Compost", "Weed Garden",
                "Inspect for Pests", "Transplant Seedlings", "Garden Planning", "Crop Rotation",
                "Greenhouse Maintenance", "Tool Maintenance", "Garden Meeting", "Seed Starting",
                "Mulching", "Irrigation Check", "Garden Cleanup", "Soil Testing"
            ]

            event_locations = [
                "Main Garden", "Greenhouse", "Community Center", "Backyard", "Front Yard",
                "Garden Shed", "Nursery", "Local Farm", "Garden Store", "Online Meeting"
            ]

            calendar_types = ["work", "community", "school", "personal"]

            # Generate events for each user
            for user in users:
                # Get gardens this user is a member of
                user_gardens = user.gardens

                # Get plants from these gardens
                user_plants = []
                for garden in user_gardens:
                    for zone in garden.zones:
                        user_plants.extend(zone.plants)

                # Generate random events
                for _ in range(NUM_EVENTS_PER_USER):
                    # Random date within 30 days before or after current date
                    days_offset = random.randint(-30, 30)
                    event_date = current_time + timedelta(days=days_offset)

                    # Random time
                    hour = random.randint(8, 20)  # Between 8 AM and 8 PM
                    minute = random.choice([0, 15, 30, 45])
                    event_date = event_date.replace(hour=hour, minute=minute)

                    # Random duration between 30 minutes and 3 hours
                    duration_minutes = random.choice([30, 60, 90, 120, 180])
                    end_date = event_date + timedelta(minutes=duration_minutes)

                    # Randomly decide if it's an all-day event
                    all_day = random.random() < 0.2  # 20% chance of being all-day
                    if all_day:
                        event_date = event_date.replace(hour=0, minute=0)
                        end_date = event_date.replace(hour=23, minute=59)

                    # Randomly select a garden and plant (if available)
                    garden = random.choice(user_gardens) if user_gardens else None
                    plant = random.choice(user_plants) if user_plants and random.random() < 0.3 else None

                    # Create event
                    title = random.choice(event_titles)
                    if plant:
                        title = f"{title} - {plant.plant_detail.name}"

                    event = CalendarEvent(
                        title=title,
                        description=fake.paragraph(),
                        location=random.choice(event_locations) if random.random() < 0.7 else None,
                        start_datetime=event_date,
                        end_datetime=end_date,
                        all_day=all_day,
                        repeat_type=random.choice([None, 'daily', 'weekly', 'monthly']) if random.random() < 0.3 else None,
                        calendar_type=random.choice(calendar_types),
                        is_private=random.random() < 0.1,  # 10% chance of being private
                        alert_before_minutes=random.choice([0, 5, 10, 15, 30, 60]) if random.random() < 0.7 else None,
                        user_id=user.id,
                        garden_id=garden.id if garden else None,
                        plant_id=plant.id if plant else None
                    )

                    db.session.add(event)
                    events.append(event)

                    # Add invitees for some events
                    if random.random() < 0.4:  # 40% chance of having invitees
                        # Get potential invitees (other users)
                        potential_invitees = [u for u in users if u != user]
                        num_invitees = random.randint(1, min(3, len(potential_invitees)))
                        invitees = random.sample(potential_invitees, num_invitees)

                        # We need to commit the event first to get a valid ID
                        db.session.flush()

                        for invitee in invitees:
                            event_invitee = CalendarEventInvitee(
                                event_id=event.id,
                                user_id=invitee.id,
                                status=random.choice(['pending', 'accepted', 'declined'])
                            )
                            db.session.add(event_invitee)

            db.session.commit()
            print(f"Created {len(events)} calendar events")
            print("Database generated successfully with plant data and calendar events!")

if __name__ == "__main__":
    generate_database()  # Add this line to create varieties
