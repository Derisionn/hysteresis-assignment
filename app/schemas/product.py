"""Product Pydantic schemas."""

from typing import Optional
from pydantic import BaseModel, Field, condecimal
from datetime import datetime
from decimal import Decimal


class ProductBase(BaseModel):
    """Base product schema."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    price: condecimal(gt=0, decimal_places=2)
    category: str = Field(..., min_length=1, max_length=100)
    stock_quantity: int = Field(default=0, ge=0)
    availability: bool = True
    image_url: Optional[str] = Field(None, max_length=500)


class ProductCreate(ProductBase):
    """Schema for creating a product."""
    pass


class ProductUpdate(BaseModel):
    """Schema for updating a product."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    price: Optional[condecimal(gt=0, decimal_places=2)] = None
    category: Optional[str] = Field(None, min_length=1, max_length=100)
    stock_quantity: Optional[int] = Field(None, ge=0)
    availability: Optional[bool] = None
    image_url: Optional[str] = Field(None, max_length=500)


class ProductResponse(ProductBase):
    """Schema for product response."""
    id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ProductListResponse(BaseModel):
    """Schema for paginated product list."""
    products: list[ProductResponse]
    total: int
    page_size: int
    cursor: Optional[str] = None
    has_more: bool


class ProductFilter(BaseModel):
    """Schema for product filtering."""
    category: Optional[str] = None
    min_price: Optional[Decimal] = Field(None, ge=0)
    max_price: Optional[Decimal] = Field(None, ge=0)
    availability: Optional[bool] = None
    search: Optional[str] = None
    sort_by: str = Field(default="created_at", pattern="^(name|price|created_at)$")
    sort_order: str = Field(default="desc", pattern="^(asc|desc)$")
    limit: int = Field(default=20, ge=1, le=100)
    cursor: Optional[str] = None
