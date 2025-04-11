"""
Migration script to add Farm and related models to the database.
"""
import sys
import os

# Add the parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from greenbyte import db, createApp
from sqlalchemy import inspect
from sqlalchemy.sql import text

app = createApp()

def upgrade():
    with app.app_context():
        inspector = db.inspect(db.engine)
        tables_to_create = [
            'farm_member',
            'farm',
            'inventory_item',
            'inventory_transaction',
            'sale',
            'sale_item',
            'purchase',
            'purchase_item'
        ]

        # Check which tables need to be created
        existing_tables = inspector.get_table_names()
        tables_to_create = [table for table in tables_to_create if table not in existing_tables]

        if not tables_to_create:
            print("All farm-related tables already exist.")
            return

        print(f"Creating tables: {', '.join(tables_to_create)}")

        # Add farm_id column to garden table if it doesn't exist
        garden_columns = [col['name'] for col in inspector.get_columns('garden')]
        if 'farm_id' not in garden_columns:
            print("Adding farm_id column to garden table...")
            db.engine.execute('''
                ALTER TABLE garden
                ADD COLUMN farm_id INTEGER,
                ADD FOREIGN KEY (farm_id) REFERENCES farm (id)
            ''')
            print("farm_id column added to garden table.")

        # Add access_level column to user table if it doesn't exist
        user_columns = [col['name'] for col in inspector.get_columns('user')]
        if 'access_level' not in user_columns:
            print("Adding access_level column to user table...")
            db.engine.execute('''
                ALTER TABLE user
                ADD COLUMN access_level VARCHAR(20) NOT NULL DEFAULT 'user'
            ''')
            print("access_level column added to user table.")

        # Create farm_member table
        if 'farm_member' in tables_to_create:
            print("Creating farm_member table...")
            db.engine.execute('''
                CREATE TABLE farm_member (
                    user_id INTEGER NOT NULL,
                    farm_id INTEGER NOT NULL,
                    role VARCHAR(20) NOT NULL DEFAULT 'gardener',
                    PRIMARY KEY (user_id, farm_id),
                    FOREIGN KEY (user_id) REFERENCES user (id) ON DELETE CASCADE,
                    FOREIGN KEY (farm_id) REFERENCES farm (id) ON DELETE CASCADE
                )
            ''')
            print("farm_member table created.")

        # Create farm table
        if 'farm' in tables_to_create:
            print("Creating farm table...")
            db.engine.execute('''
                CREATE TABLE farm (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR(100) NOT NULL,
                    location VARCHAR(200),
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    business_name VARCHAR(100),
                    tax_id VARCHAR(50),
                    phone VARCHAR(20),
                    email VARCHAR(120),
                    website VARCHAR(120),
                    owner_id INTEGER NOT NULL,
                    FOREIGN KEY (owner_id) REFERENCES user (id)
                )
            ''')
            print("farm table created.")

        # Create inventory_item table
        if 'inventory_item' in tables_to_create:
            print("Creating inventory_item table...")
            db.engine.execute('''
                CREATE TABLE inventory_item (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    farm_id INTEGER NOT NULL,
                    name VARCHAR(100) NOT NULL,
                    description TEXT,
                    category VARCHAR(50),
                    sku VARCHAR(50),
                    quantity FLOAT NOT NULL DEFAULT 0,
                    unit VARCHAR(20) NOT NULL DEFAULT 'unit',
                    price_per_unit FLOAT,
                    cost_per_unit FLOAT,
                    reorder_point FLOAT,
                    reorder_quantity FLOAT,
                    location VARCHAR(100),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    plant_id INTEGER,
                    harvest_id INTEGER,
                    FOREIGN KEY (farm_id) REFERENCES farm (id),
                    FOREIGN KEY (plant_id) REFERENCES plant (id),
                    FOREIGN KEY (harvest_id) REFERENCES harvest (id)
                )
            ''')
            print("inventory_item table created.")

        # Create inventory_transaction table
        if 'inventory_transaction' in tables_to_create:
            print("Creating inventory_transaction table...")
            db.engine.execute('''
                CREATE TABLE inventory_transaction (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    item_id INTEGER NOT NULL,
                    transaction_type VARCHAR(50) NOT NULL,
                    quantity_change FLOAT NOT NULL,
                    previous_quantity FLOAT NOT NULL,
                    new_quantity FLOAT NOT NULL,
                    transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    notes TEXT,
                    sale_id INTEGER,
                    purchase_id INTEGER,
                    FOREIGN KEY (item_id) REFERENCES inventory_item (id),
                    FOREIGN KEY (sale_id) REFERENCES sale (id),
                    FOREIGN KEY (purchase_id) REFERENCES purchase (id)
                )
            ''')
            print("inventory_transaction table created.")

        # Create sale table
        if 'sale' in tables_to_create:
            print("Creating sale table...")
            db.engine.execute('''
                CREATE TABLE sale (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    farm_id INTEGER NOT NULL,
                    customer_id INTEGER,
                    customer_name VARCHAR(100),
                    sale_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    total_amount FLOAT NOT NULL DEFAULT 0,
                    payment_method VARCHAR(50),
                    payment_status VARCHAR(50) DEFAULT 'pending',
                    notes TEXT,
                    created_by INTEGER NOT NULL,
                    FOREIGN KEY (farm_id) REFERENCES farm (id),
                    FOREIGN KEY (customer_id) REFERENCES client (id),
                    FOREIGN KEY (created_by) REFERENCES user (id)
                )
            ''')
            print("sale table created.")

        # Create sale_item table
        if 'sale_item' in tables_to_create:
            print("Creating sale_item table...")
            db.engine.execute('''
                CREATE TABLE sale_item (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sale_id INTEGER NOT NULL,
                    inventory_item_id INTEGER NOT NULL,
                    quantity FLOAT NOT NULL,
                    price_per_unit FLOAT NOT NULL,
                    total_price FLOAT NOT NULL,
                    FOREIGN KEY (sale_id) REFERENCES sale (id),
                    FOREIGN KEY (inventory_item_id) REFERENCES inventory_item (id)
                )
            ''')
            print("sale_item table created.")

        # Create purchase table
        if 'purchase' in tables_to_create:
            print("Creating purchase table...")
            db.engine.execute('''
                CREATE TABLE purchase (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    farm_id INTEGER NOT NULL,
                    supplier_name VARCHAR(100) NOT NULL,
                    purchase_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    total_amount FLOAT NOT NULL DEFAULT 0,
                    payment_method VARCHAR(50),
                    payment_status VARCHAR(50) DEFAULT 'pending',
                    notes TEXT,
                    created_by INTEGER NOT NULL,
                    FOREIGN KEY (farm_id) REFERENCES farm (id),
                    FOREIGN KEY (created_by) REFERENCES user (id)
                )
            ''')
            print("purchase table created.")

        # Create purchase_item table
        if 'purchase_item' in tables_to_create:
            print("Creating purchase_item table...")
            db.engine.execute('''
                CREATE TABLE purchase_item (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    purchase_id INTEGER NOT NULL,
                    inventory_item_id INTEGER NOT NULL,
                    quantity FLOAT NOT NULL,
                    price_per_unit FLOAT NOT NULL,
                    total_price FLOAT NOT NULL,
                    FOREIGN KEY (purchase_id) REFERENCES purchase (id),
                    FOREIGN KEY (inventory_item_id) REFERENCES inventory_item (id)
                )
            ''')
            print("purchase_item table created.")

        print("All farm-related tables created successfully.")

if __name__ == '__main__':
    upgrade()
