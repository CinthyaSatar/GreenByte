"""
Migration script to add Farm and related models to the database.
"""
import sys
import os

# Add the parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from greenbyte import db, createApp
from sqlalchemy import inspect

app = createApp()

def upgrade():
    with app.app_context():
        # Create the Farm model and related models
        from greenbyte.models import Farm, InventoryItem, InventoryTransaction, Sale, SaleItem, Purchase, PurchaseItem
        
        # Create all tables
        db.create_all()
        
        print("All farm-related tables created successfully.")

if __name__ == '__main__':
    upgrade()
