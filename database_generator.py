from greenbyte import db
from run import app
from greenbyte.models import (
    User, Garden, Zone, Plant, PlantTracking, Post, Harvest,
    Client, Order, OrderItem, Delivery, Payment
)
from datetime import datetime, timedelta, UTC
import random

def generate_sample_data():
    """Generate sample data for the application"""
    with app.app_context():
        # Clear existing data
        db.drop_all()
        db.session.commit()
        db.create_all()
        
        current_time = datetime.now(UTC)

        # Create sample users (50)
        users = []
        for i in range(50):
            user = User(
                username=f"gardener{i+1}",
                firstName=f"FirstName{i+1}",
                lastName=f"LastName{i+1}",
                email=f"user{i+1}@example.com",
                password="hashedpassword"  # In production, use proper password hashing
            )
            users.append(user)
        db.session.add_all(users)
        db.session.commit()

        # Create gardens (100) with owners and members
        gardens = []
        locations = ["California", "Oregon", "Washington", "Texas", "Florida", "New York", "Illinois"]
        
        for i in range(100):
            # Select an owner for the garden
            owner = random.choice(users)
            
            garden = Garden(
                name=f"Garden {i+1}",
                location=random.choice(locations),
                owner_id=owner.id
            )
            db.session.add(garden)
            db.session.commit()

            # Add owner as manager
            garden.add_member(owner, role='manager')

            # Add 2-5 additional members with different roles
            available_users = [u for u in users if u.id != owner.id]
            num_additional_members = random.randint(2, 5)
            selected_members = random.sample(available_users, num_additional_members)

            for member in selected_members:
                # Distribute roles: 15% commercial, 10% manager, 75% member
                role_chance = random.random()
                if role_chance < 0.15:
                    role = "commercial"
                elif role_chance < 0.25:
                    role = "manager"
                else:
                    role = "member"
                garden.add_member(member, role=role)

            gardens.append(garden)

        # Create zones (150)
        zones = []
        zone_names = ["Tomato Section", "Lettuce Section", "Pepper Greenhouse", "Herb Garden", 
                     "Root Vegetables", "Fruit Trees", "Berry Patch", "Cucumber Zone"]
        for i in range(150):
            garden = random.choice(gardens)
            zone = Zone(
                name=random.choice(zone_names),
                garden_id=garden.id,
                planting_date=current_time - timedelta(days=random.randint(1, 90))
            )
            zones.append(zone)
        db.session.add_all(zones)
        db.session.commit()

        # Create plants (300)
        plants = []
        plant_names = ["Tomato", "Cucumber", "Lettuce", "Pepper", "Carrot", "Basil", "Strawberry", "Blueberry"]
        for i in range(300):
            plant = Plant(
                name=random.choice(plant_names),
                zone_id=random.choice(zones).id,
                planting_date=current_time - timedelta(days=random.randint(1, 60))
            )
            plants.append(plant)
        db.session.add_all(plants)
        db.session.commit()

        # Create tracking entries (450)
        tracking_entries = []
        stages = ["Seeded", "Sprouted", "Growing", "Flowering", "Fruiting", "Ready for Harvest"]
        for i in range(450):
            tracking = PlantTracking(
                plant_id=random.choice(plants).id,
                date_logged=current_time - timedelta(days=random.randint(1, 45)),
                stage=random.choice(stages),
                notes=f"Plant tracking note {i+1}"
            )
            tracking_entries.append(tracking)
        db.session.add_all(tracking_entries)
        db.session.commit()

        # Create harvests (200)
        harvests = []
        for i in range(200):
            plant = random.choice(plants)
            harvest = Harvest(
                plant_id=plant.id,
                date=current_time - timedelta(days=random.randint(1, 30)),
                amount_collected=round(random.uniform(0.5, 10.0), 2),
                notes=f"Harvest note {i+1}"
            )
            harvests.append(harvest)
        db.session.add_all(harvests)
        db.session.commit()

        # Create posts (150)
        posts = []
        post_titles = [
            "Weekly Garden Update", "New Plants Added", "Harvest Report", 
            "Pest Management Success", "Weather Impact Report", "Growth Progress",
            "Composting Update", "Irrigation System Check", "Seasonal Planning"
        ]
        post_contents = [
            "Great progress in the garden this week!", 
            "Added some new varieties to our collection.", 
            "Successful harvest season continues.",
            "Natural pest control methods working well.",
            "Garden thriving despite weather challenges.",
            "Plants showing excellent growth rates."
        ]
        
        for i in range(150):
            author = random.choice(users)
            # Only create posts for gardens where the user is a member
            if author.gardens:
                garden = random.choice(author.gardens)
                post = Post(
                    title=f"{random.choice(post_titles)} #{i+1}",
                    content=f"{random.choice(post_contents)} Update #{i+1}",
                    user_id=author.id,
                    garden_id=garden.id,
                    date_posted=current_time - timedelta(days=random.randint(1, 90))
                )
                posts.append(post)
        
        db.session.add_all(posts)
        db.session.commit()

        # Create clients (100)
        clients = []
        for i in range(100):
            client = Client(
                name=f"Client {i+1}",
                email=f"client{i+1}@example.com",
                phone=f"555-{random.randint(1000,9999)}",
                address=f"{random.randint(100,999)} {random.choice(['Main', 'Market', 'Oak', 'Pine'])} St, {random.choice(locations)}"
            )
            clients.append(client)
        db.session.add_all(clients)
        db.session.commit()

        # Create orders (200) - Only for commercial/manager users
        orders = []
        order_statuses = ["pending", "processing", "completed", "cancelled"]
        recurring_frequencies = ["weekly", "monthly"]
        plant_prices = {plant.id: round(random.uniform(2.0, 15.0), 2) for plant in plants}  # Random prices for plants

        for i in range(200):
            # Get a random garden with its commercial members
            garden = random.choice(gardens)
            commercial_members = garden.get_commercial_members()
            
            if not commercial_members:
                continue  # Skip if no commercial members in this garden
            
            creator = random.choice(commercial_members)
            client = random.choice(clients)
            is_recurring = random.choice([True, False, False])  # 1/3 chance of recurring order
            
            try:
                order = Order(
                    client_id=client.id,
                    garden_id=garden.id,
                    created_by=creator.id,
                    date_placed=current_time - timedelta(days=random.randint(1, 90)),
                    status=random.choice(order_statuses),
                    recurring=is_recurring,
                    recurring_frequency=random.choice(recurring_frequencies) if is_recurring else None,
                    total_amount=0  # Will be calculated after adding items
                )
                
                # Add 1-5 order items
                num_items = random.randint(1, 5)
                garden_plants = [plant for plant in plants if plant.zone.garden_id == garden.id]
                
                if not garden_plants:
                    continue  # Skip if no plants in this garden
                
                # Create OrderItems
                for _ in range(num_items):
                    plant = random.choice(garden_plants)
                    quantity = random.randint(1, 10)
                    price = plant_prices[plant.id]
                    
                    order_item = OrderItem(
                        plant_id=plant.id,
                        quantity=quantity,
                        price_per_unit=price
                    )
                    order.order_items.append(order_item)
                
                # Calculate total and save
                db.session.add(order)
                db.session.flush()  # Get order ID
                order.calculate_total()
                
                # Add delivery for completed orders
                if order.status == "completed":
                    delivery = Delivery(
                        order_id=order.id,
                        delivery_date=order.date_placed + timedelta(days=random.randint(1, 7)),
                        status="delivered",
                        tracking_number=f"TRACK{random.randint(100000, 999999)}",
                        address=client.address  # Now this will work with the updated model
                    )
                    db.session.add(delivery)
                
                # Add payments
                payment_amount = order.total_amount
                if order.status == "completed":
                    payment_status = "completed"
                elif order.status == "cancelled":
                    payment_status = "refunded"
                else:
                    payment_status = "pending"
                
                payment = Payment(
                    order_id=order.id,
                    amount=payment_amount,
                    payment_method=random.choice(["credit_card", "bank_transfer", "cash"]),
                    status=payment_status,
                    payment_date=order.date_placed  # Changed from 'date' to 'payment_date'
                )
                db.session.add(payment)
                
                # Generate next order if recurring
                if is_recurring and order.status == "completed":
                    next_order = order.generate_next_order()
                    if next_order:
                        orders.append(next_order)
                
                orders.append(order)
                
            except ValueError as e:
                print(f"Skipping order creation due to: {e}")
                continue
        
        db.session.add_all(orders)
        db.session.commit()

        # Create order items (400)
        order_items = []
        for i in range(400):
            order = random.choice(orders)
            order_item = OrderItem(
                order_id=order.id,
                plant_id=random.choice(plants).id,
                quantity=random.randint(1, 10),
                price_per_unit=round(random.uniform(2.0, 15.0), 2)
            )
            order_items.append(order_item)
        db.session.add_all(order_items)
        db.session.commit()

        # Create deliveries (200)
        deliveries = []
        delivery_statuses = ["Pending", "Processing", "In Transit", "Delivered", "Failed"]
        for i in range(min(200, len(orders))):  # Use the smaller of 200 or number of orders
            order = random.choice(orders)  # Use random.choice instead of indexing
            delivery = Delivery(
                order_id=order.id,
                delivery_date=current_time + timedelta(days=random.randint(1, 14)),
                status=random.choice(delivery_statuses),
                tracking_number=f"TRACK{random.randint(100000,999999)}",
                address=order.client.address
            )
            deliveries.append(delivery)
        db.session.add_all(deliveries)
        db.session.commit()

        # Create payments (200)
        payments = []
        payment_methods = ["Credit Card", "PayPal", "Bank Transfer", "Cash"]
        payment_statuses = ["Pending", "Processing", "Completed", "Failed"]
        for i in range(min(200, len(orders))):  # Use the smaller of 200 or number of orders
            order = random.choice(orders)  # Use random.choice instead of indexing
            payment = Payment(
                order_id=order.id,
                amount=round(random.uniform(10.0, 200.0), 2),
                payment_date=current_time - timedelta(days=random.randint(1, 30)),
                payment_method=random.choice(payment_methods),
                status=random.choice(payment_statuses)
            )
            payments.append(payment)
        db.session.add_all(payments)
        db.session.commit()

        # Update order totals
        for order in orders:
            order.calculate_total()
        db.session.commit()

        # Print statistics
        print("\nSample data generated successfully!")
        print(f"Created {len(users)} users")
        print(f"Created {len(gardens)} gardens")
        print(f"Created {len(zones)} zones")
        print(f"Created {len(plants)} plants")
        print(f"Created {len(tracking_entries)} tracking entries")
        print(f"Created {len(harvests)} harvests")
        print(f"Created {len(posts)} posts")
        print(f"Created {len(clients)} clients")
        print(f"Created {len(orders)} orders")

        # Print role statistics
        print("\nRole Statistics:")
        role_counts = {"member": 0, "commercial": 0, "manager": 0}
        total_memberships = 0
        
        for garden in gardens:
            for member in garden.members:
                role = garden.get_member_role(member)
                if role:
                    role_counts[role] += 1
                    total_memberships += 1

        for role, count in role_counts.items():
            percentage = (count / total_memberships) * 100 if total_memberships > 0 else 0
            print(f"{role.capitalize()}: {count} ({percentage:.1f}%)")

if __name__ == "__main__":
    generate_sample_data()
