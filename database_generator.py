from datetime import timedelta
import random

from flask_bcrypt import Bcrypt
import faker

from greenbyte import db
from run import app
from greenbyte.models import (
    User, Garden, Zone, Plant, PlantTracking, PlantDetail, PlantVariety, PlantStage
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

            db.session.commit()
            print("Database generated successfully with plant data!")

if __name__ == "__main__":
    generate_database()  # Add this line to create varieties
