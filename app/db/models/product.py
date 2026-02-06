"""Product database model."""

import uuid
from datetime import datetime
from decimal import Decimal
from sqlalchemy import Column, String, Text, Numeric, Integer, Boolean, DateTime, Index
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base


class Product(Base):
    """Product model for farm products."""
    
    __tablename__ = "products"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    price = Column(Numeric(10, 2), nullable=False)
    category = Column(String(100), nullable=False, index=True)
    stock_quantity = Column(Integer, default=0, nullable=False)
    availability = Column(Boolean, default=True, nullable=False, index=True)
    image_url = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Composite index for efficient querying
    __table_args__ = (
        Index('idx_category_price_created', 'category', 'price', 'created_at'),
        Index('idx_availability_category', 'availability', 'category'),
    )
    
    def __repr__(self):
        return f"<Product {self.name}>"
