"""Integration tests for product API."""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_list_products_without_auth():
    """Test listing products without authentication (should work)."""
    response = client.get("/api/v1/products")
    
    assert response.status_code == 200
    data = response.json()
    assert "products" in data
    assert "total" in data
    assert "has_more" in data


def test_list_products_with_filters():
    """Test listing products with category filter."""
    response = client.get("/api/v1/products?category=Vegetables&limit=5")
    
    assert response.status_code == 200
    data = response.json()
    assert data["page_size"] == 5


def test_list_products_with_price_range():
    """Test listing products with price range."""
    response = client.get("/api/v1/products?min_price=2.00&max_price=5.00")
    
    assert response.status_code == 200
    data = response.json()
    assert "products" in data


def test_list_products_with_search():
    """Test listing products with search term."""
    response = client.get("/api/v1/products?search=organic")
    
    assert response.status_code == 200
    data = response.json()
    assert "products" in data


def test_list_products_with_sorting():
    """Test listing products with sorting."""
    response = client.get("/api/v1/products?sort_by=price&sort_order=asc")
    
    assert response.status_code == 200
    data = response.json()
    assert "products" in data


def test_get_product_not_found():
    """Test getting non-existent product."""
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = client.get(f"/api/v1/products/{fake_id}")
    
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_create_product_without_auth():
    """Test creating product without authentication (should fail)."""
    product_data = {
        "name": "Test Product",
        "description": "Test description",
        "price": 9.99,
        "category": "Test",
        "stock_quantity": 10
    }
    
    response = client.post("/api/v1/products", json=product_data)
    
    assert response.status_code == 403  # Forbidden without auth


def test_update_product_without_auth():
    """Test updating product without authentication (should fail)."""
    fake_id = "00000000-0000-0000-0000-000000000000"
    update_data = {"name": "Updated Name"}
    
    response = client.put(f"/api/v1/products/{fake_id}", json=update_data)
    
    assert response.status_code == 403  # Forbidden without auth


def test_delete_product_without_auth():
    """Test deleting product without authentication (should fail)."""
    fake_id = "00000000-0000-0000-0000-000000000000"
    
    response = client.delete(f"/api/v1/products/{fake_id}")
    
    assert response.status_code == 403  # Forbidden without auth


def test_pagination_cursor():
    """Test cursor-based pagination."""
    # Get first page
    response1 = client.get("/api/v1/products?limit=3")
    assert response1.status_code == 200
    
    data1 = response1.json()
    
    # If there's a cursor, get next page
    if data1.get("cursor"):
        response2 = client.get(f"/api/v1/products?limit=3&cursor={data1['cursor']}")
        assert response2.status_code == 200
        
        data2 = response2.json()
        # Products should be different
        if len(data1["products"]) > 0 and len(data2["products"]) > 0:
            assert data1["products"][0]["id"] != data2["products"][0]["id"]
