"""Database seeding script for initial data."""

import sys
import os
from decimal import Decimal

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.db.base import SessionLocal
from app.db.models.product import Product
from app.db.models.user import User, UserRole
import uuid


def seed_products():
    """Seed database with sample products."""
    db = SessionLocal()
    
    try:
        # Check if products already exist
        existing = db.query(Product).first()
        if existing:
            print("Products already exist. Skipping seed.")
            return
        
        products = [
            # Vegetables
            Product(
                name="Organic Tomatoes",
                description="Fresh organic tomatoes from local farms",
                price=Decimal("3.99"),
                category="Vegetables",
                stock_quantity=150,
                availability=True,
                image_url="https://example.com/tomatoes.jpg"
            ),
            Product(
                name="Fresh Carrots",
                description="Crunchy orange carrots, perfect for salads",
                price=Decimal("2.49"),
                category="Vegetables",
                stock_quantity=200,
                availability=True,
                image_url="https://example.com/carrots.jpg"
            ),
            Product(
                name="Green Bell Peppers",
                description="Crisp green bell peppers",
                price=Decimal("4.99"),
                category="Vegetables",
                stock_quantity=80,
                availability=True,
                image_url="https://example.com/peppers.jpg"
            ),
            
            # Fruits
            Product(
                name="Red Apples",
                description="Sweet and crispy red apples",
                price=Decimal("5.99"),
                category="Fruits",
                stock_quantity=120,
                availability=True,
                image_url="https://example.com/apples.jpg"
            ),
            Product(
                name="Bananas",
                description="Fresh yellow bananas",
                price=Decimal("1.99"),
                category="Fruits",
                stock_quantity=300,
                availability=True,
                image_url="https://example.com/bananas.jpg"
            ),
            Product(
                name="Strawberries",
                description="Sweet organic strawberries",
                price=Decimal("6.99"),
                category="Fruits",
                stock_quantity=50,
                availability=True,
                image_url="https://example.com/strawberries.jpg"
            ),
            
            # Dairy
            Product(
                name="Organic Milk",
                description="Fresh organic whole milk",
                price=Decimal("4.49"),
                category="Dairy",
                stock_quantity=100,
                availability=True,
                image_url="https://example.com/milk.jpg"
            ),
            Product(
                name="Cheddar Cheese",
                description="Aged cheddar cheese block",
                price=Decimal("7.99"),
                category="Dairy",
                stock_quantity=60,
                availability=True,
                image_url="https://example.com/cheese.jpg"
            ),
            
            # Grains
            Product(
                name="Brown Rice",
                description="Organic brown rice, 2lb bag",
                price=Decimal("5.49"),
                category="Grains",
                stock_quantity=90,
                availability=True,
                image_url="https://example.com/rice.jpg"
            ),
            Product(
                name="Whole Wheat Bread",
                description="Fresh baked whole wheat bread",
                price=Decimal("3.99"),
                category="Grains",
                stock_quantity=40,
                availability=True,
                image_url="https://example.com/bread.jpg"
            ),
        ]
        
        db.bulk_save_objects(products)
        db.commit()
        
        print(f"✅ Successfully seeded {len(products)} products")
        
    except Exception as e:
        print(f"❌ Error seeding products: {e}")
        db.rollback()
    finally:
        db.close()


def seed_admin_user():
    """Create an admin user for testing."""
    db = SessionLocal()
    
    try:
        # Check if admin exists
        admin = db.query(User).filter(User.role == UserRole.ADMIN).first()
        if admin:
            print("Admin user already exists. Skipping.")
            return
        
        admin_user = User(
            email="admin@farmlokal.com",
            full_name="Admin User",
            oauth_provider="google",
            oauth_id="admin_oauth_id_12345",
            role=UserRole.ADMIN,
            is_active=True
        )
        
        db.add(admin_user)
        db.commit()
        
        print(f"✅ Successfully created admin user: {admin_user.email}")
        
    except Exception as e:
        print(f"❌ Error creating admin user: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    print("🌱 Seeding database...")
    seed_admin_user()
    seed_products()
    print("✅ Database seeding complete!")
