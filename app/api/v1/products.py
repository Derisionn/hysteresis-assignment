"""Product API endpoints."""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.db.base import get_db
from app.dependencies import get_current_user, require_admin
from app.schemas.auth import CurrentUser
from app.schemas.product import (
    ProductCreate,
    ProductUpdate,
    ProductResponse,
    ProductListResponse,
    ProductFilter
)
from app.services.product_service import ProductService
from decimal import Decimal

router = APIRouter(prefix="/products", tags=["Products"])


@router.get("", response_model=ProductListResponse)
async def list_products(
    category: Optional[str] = Query(None, description="Filter by category"),
    min_price: Optional[Decimal] = Query(None, ge=0, description="Minimum price"),
    max_price: Optional[Decimal] = Query(None, ge=0, description="Maximum price"),
    availability: Optional[bool] = Query(None, description="Filter by availability"),
    search: Optional[str] = Query(None, description="Search in name and description"),
    sort_by: str = Query("created_at", regex="^(name|price|created_at)$", description="Sort field"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="Sort order"),
    limit: int = Query(20, ge=1, le=100, description="Page size"),
    cursor: Optional[str] = Query(None, description="Pagination cursor"),
    db: Session = Depends(get_db)
):
    """
    List products with filtering, sorting, and cursor-based pagination.
    
    - **category**: Filter by product category
    - **min_price**: Minimum price filter
    - **max_price**: Maximum price filter
    - **availability**: Filter by availability status
    - **search**: Search term for name and description
    - **sort_by**: Field to sort by (name, price, created_at)
    - **sort_order**: Sort order (asc, desc)
    - **limit**: Number of results per page (1-100)
    - **cursor**: Cursor for next page
    
    Returns paginated product list with cursor for next page.
    """
    filters = ProductFilter(
        category=category,
        min_price=min_price,
        max_price=max_price,
        availability=availability,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
        limit=limit,
        cursor=cursor
    )
    
    service = ProductService(db)
    products, has_more, next_cursor = service.list_products(filters)
    
    return ProductListResponse(
        products=[ProductResponse.model_validate(p) for p in products],
        total=len(products),
        page_size=limit,
        cursor=next_cursor,
        has_more=has_more
    )


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: str,
    db: Session = Depends(get_db)
):
    """
    Get product by ID.
    
    - **product_id**: Product UUID
    
    Returns product details.
    """
    service = ProductService(db)
    product = service.get_product(product_id)
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    return ProductResponse.model_validate(product)


@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    product_data: ProductCreate,
    current_user: CurrentUser = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Create a new product (Admin only).
    
    - **name**: Product name (required)
    - **description**: Product description
    - **price**: Product price (required, > 0)
    - **category**: Product category (required)
    - **stock_quantity**: Stock quantity (default: 0)
    - **availability**: Availability status (default: true)
    - **image_url**: Product image URL
    
    Returns created product.
    """
    service = ProductService(db)
    product = service.create_product(product_data)
    
    return ProductResponse.model_validate(product)


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: str,
    product_data: ProductUpdate,
    current_user: CurrentUser = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Update a product (Admin only).
    
    - **product_id**: Product UUID
    - All fields are optional
    
    Returns updated product.
    """
    service = ProductService(db)
    product = service.update_product(product_id, product_data)
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    return ProductResponse.model_validate(product)


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: str,
    current_user: CurrentUser = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Delete a product (Admin only).
    
    - **product_id**: Product UUID
    
    Returns 204 No Content on success.
    """
    service = ProductService(db)
    deleted = service.delete_product(product_id)
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
