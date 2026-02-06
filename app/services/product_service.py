"""Product service with business logic and caching."""

import base64
import json
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from app.db.models.product import Product
from app.schemas.product import ProductCreate, ProductUpdate, ProductFilter, ProductResponse
from app.core.cache import cache_manager
from decimal import Decimal


class ProductService:
    """Product business logic service."""
    
    def __init__(self, db: Session):
        self.db = db
        self.cache = cache_manager
    
    def create_product(self, product_data: ProductCreate) -> Product:
        """
        Create a new product.
        
        Args:
            product_data: Product creation data
            
        Returns:
            Created product
        """
        product = Product(**product_data.model_dump())
        self.db.add(product)
        self.db.commit()
        self.db.refresh(product)
        
        # Invalidate product caches
        self.cache.invalidate_products()
        
        return product
    
    def get_product(self, product_id: str) -> Optional[Product]:
        """
        Get product by ID with caching.
        
        Args:
            product_id: Product UUID
            
        Returns:
            Product or None
        """
        # Try cache first
        cache_key = f"products:item:{product_id}"
        cached = self.cache.get(cache_key)
        
        if cached:
            # Reconstruct product from cache
            return self._dict_to_product(cached)
        
        # Query database
        product = self.db.query(Product).filter(Product.id == product_id).first()
        
        if product:
            # Cache the result
            self.cache.set(cache_key, self._product_to_dict(product))
        
        return product
    
    def update_product(self, product_id: str, product_data: ProductUpdate) -> Optional[Product]:
        """
        Update a product.
        
        Args:
            product_id: Product UUID
            product_data: Update data
            
        Returns:
            Updated product or None
        """
        product = self.db.query(Product).filter(Product.id == product_id).first()
        
        if not product:
            return None
        
        # Update fields
        update_data = product_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(product, field, value)
        
        self.db.commit()
        self.db.refresh(product)
        
        # Invalidate caches
        self.cache.delete(f"products:item:{product_id}")
        self.cache.invalidate_products()
        
        return product
    
    def delete_product(self, product_id: str) -> bool:
        """
        Delete a product.
        
        Args:
            product_id: Product UUID
            
        Returns:
            True if deleted, False if not found
        """
        product = self.db.query(Product).filter(Product.id == product_id).first()
        
        if not product:
            return False
        
        self.db.delete(product)
        self.db.commit()
        
        # Invalidate caches
        self.cache.delete(f"products:item:{product_id}")
        self.cache.invalidate_products()
        
        return True
    
    def list_products(self, filters: ProductFilter) -> Tuple[List[Product], bool, Optional[str]]:
        """
        List products with filtering, sorting, and cursor-based pagination.
        
        Args:
            filters: Filter parameters
            
        Returns:
            Tuple of (products, has_more, next_cursor)
        """
        # Generate cache key
        cache_key = self.cache._generate_key(
            "products:list",
            category=filters.category,
            min_price=str(filters.min_price) if filters.min_price else None,
            max_price=str(filters.max_price) if filters.max_price else None,
            availability=filters.availability,
            search=filters.search,
            sort_by=filters.sort_by,
            sort_order=filters.sort_order,
            limit=filters.limit,
            cursor=filters.cursor
        )
        
        # Try cache
        cached = self.cache.get(cache_key)
        if cached:
            products = [self._dict_to_product(p) for p in cached['products']]
            return products, cached['has_more'], cached['next_cursor']
        
        # Build query
        query = self.db.query(Product)
        
        # Apply filters
        if filters.category:
            query = query.filter(Product.category == filters.category)
        
        if filters.min_price is not None:
            query = query.filter(Product.price >= filters.min_price)
        
        if filters.max_price is not None:
            query = query.filter(Product.price <= filters.max_price)
        
        if filters.availability is not None:
            query = query.filter(Product.availability == filters.availability)
        
        if filters.search:
            search_term = f"%{filters.search}%"
            query = query.filter(
                or_(
                    Product.name.ilike(search_term),
                    Product.description.ilike(search_term)
                )
            )
        
        # Apply cursor pagination
        if filters.cursor:
            cursor_data = self._decode_cursor(filters.cursor)
            if cursor_data:
                query = self._apply_cursor(query, cursor_data, filters.sort_by, filters.sort_order)
        
        # Apply sorting
        sort_column = getattr(Product, filters.sort_by)
        if filters.sort_order == "desc":
            query = query.order_by(sort_column.desc(), Product.id.desc())
        else:
            query = query.order_by(sort_column.asc(), Product.id.asc())
        
        # Fetch limit + 1 to check if there are more results
        products = query.limit(filters.limit + 1).all()
        
        # Check if there are more results
        has_more = len(products) > filters.limit
        if has_more:
            products = products[:filters.limit]
        
        # Generate next cursor
        next_cursor = None
        if has_more and products:
            last_product = products[-1]
            next_cursor = self._encode_cursor(last_product, filters.sort_by)
        
        # Cache the result
        cache_data = {
            'products': [self._product_to_dict(p) for p in products],
            'has_more': has_more,
            'next_cursor': next_cursor
        }
        self.cache.set(cache_key, cache_data)
        
        return products, has_more, next_cursor
    
    def _encode_cursor(self, product: Product, sort_by: str) -> str:
        """Encode cursor for pagination."""
        cursor_data = {
            'id': str(product.id),
            'value': str(getattr(product, sort_by))
        }
        cursor_json = json.dumps(cursor_data)
        return base64.b64encode(cursor_json.encode()).decode()
    
    def _decode_cursor(self, cursor: str) -> Optional[dict]:
        """Decode cursor for pagination."""
        try:
            cursor_json = base64.b64decode(cursor.encode()).decode()
            return json.loads(cursor_json)
        except Exception:
            return None
    
    def _apply_cursor(self, query, cursor_data: dict, sort_by: str, sort_order: str):
        """Apply cursor to query."""
        sort_column = getattr(Product, sort_by)
        cursor_value = cursor_data['value']
        cursor_id = cursor_data['id']
        
        if sort_order == "desc":
            query = query.filter(
                or_(
                    sort_column < cursor_value,
                    and_(sort_column == cursor_value, Product.id < cursor_id)
                )
            )
        else:
            query = query.filter(
                or_(
                    sort_column > cursor_value,
                    and_(sort_column == cursor_value, Product.id > cursor_id)
                )
            )
        
        return query
    
    def _product_to_dict(self, product: Product) -> dict:
        """Convert product to dictionary for caching."""
        return {
            'id': str(product.id),
            'name': product.name,
            'description': product.description,
            'price': str(product.price),
            'category': product.category,
            'stock_quantity': product.stock_quantity,
            'availability': product.availability,
            'image_url': product.image_url,
            'created_at': product.created_at.isoformat(),
            'updated_at': product.updated_at.isoformat()
        }
    
    def _dict_to_product(self, data: dict) -> Product:
        """Convert dictionary to product object."""
        from datetime import datetime
        product = Product()
        product.id = data['id']
        product.name = data['name']
        product.description = data['description']
        product.price = Decimal(data['price'])
        product.category = data['category']
        product.stock_quantity = data['stock_quantity']
        product.availability = data['availability']
        product.image_url = data['image_url']
        product.created_at = datetime.fromisoformat(data['created_at'])
        product.updated_at = datetime.fromisoformat(data['updated_at'])
        return product
