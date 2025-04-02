from datetime import datetime, timedelta
from greenbyte import db
from run import app
from greenbyte.models import (
    User, Garden, Zone, Plant, PlantTracking, PlantDetail, PlantVariety, 
    PlantStatus, user_garden
)
from datetime import datetime, timedelta
import random
from flask_bcrypt import Bcrypt
import faker
from greenbyte.utils.timezone import now_in_timezone

bcrypt = Bcrypt(app)
fake = faker.Faker()

def generate_database():
    with app.app_context():
        with db.session.no_autoflush:
            current_time = now_in_timezone()
            
            # Clear existing data
            db.drop_all()
            db.session.commit()
            db.create_all()

            # Create test user
            hashed_password = bcrypt.generate_password_hash('password').decode('utf-8')
            user = User(
                username='testuser',
                firstName='Test',
                lastName='User',
                email='test@example.com',
                password=hashed_password
            )
            db.session.add(user)
            db.session.commit()

            # Create garden
            garden = Garden(
                name='My Test Garden',
                location='Backyard',
                owner_id=user.id
            )
            db.session.add(garden)
            db.session.commit()

            # Create zones
            zones = []
            zone_names = ['Vegetable Patch', 'Herb Garden', 'Berry Patch']
            for name in zone_names:
                zone = Zone(
                    name=name,
                    garden_id=garden.id
                )
                db.session.add(zone)
                zones.append(zone)
            db.session.commit()

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
                    "varieties": ["Roma", "Cherry", "Beefsteak", "San Marzano"]
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
                    "varieties": ["Romaine", "Iceberg", "Butterhead", "Red Leaf"]
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
                    "varieties": ["Sweet Basil", "Thai Basil", "Purple Basil", "Genovese"]
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
                    "varieties": ["June-bearing", "Everbearing", "Day-neutral", "Alpine"]
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
                elif "Berry" in zone.name:
                    suitable_plants = [p for p in plant_details if p["category"] == "Fruit"]
                
                # Add 2-4 plants per zone
                num_plants = random.randint(2, 4)
                for _ in range(num_plants):
                    if suitable_plants:
                        plant_info = random.choice(suitable_plants)
                        plant_detail = plant_detail_objects[plant_info["name"]]
                        variety = random.choice(plant_detail.varieties)
                        
                        planting_date = current_time - timedelta(days=random.randint(1, 90))
                        
                        plant = Plant(
                            plant_detail_id=plant_detail.id,
                            variety_id=variety.id,
                            zone_id=zone.id,
                            quantity=random.randint(1, 10),
                            planting_date=planting_date
                        )
                        db.session.add(plant)
                        db.session.flush()

                        # Add initial tracking entry
                        tracking = PlantTracking(
                            plant_id=plant.id,
                            stage='Seedling',
                            notes=f"Initial planting of {plant_detail.name} ({variety.name})",
                            date_logged=planting_date
                        )
                        db.session.add(tracking)

            db.session.commit()
            print("Database generated successfully with plant data!")

if __name__ == "__main__":
    generate_database()  # Add this line to create varieties
