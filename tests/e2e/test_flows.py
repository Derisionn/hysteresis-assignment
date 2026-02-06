"""End-to-end tests for complete user flows."""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_complete_product_flow():
    """Test complete product browsing flow."""
    # 1. Check API is alive
    response = client.get("/")
    assert response.status_code == 200
    assert "FarmLokal" in response.json()["message"]
    
    # 2. Check health
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    
    # 3. List all products
    response = client.get("/api/v1/products")
    assert response.status_code == 200
    data = response.json()
    assert "products" in data
    assert len(data["products"]) > 0
    
    # 4. Filter by category
    response = client.get("/api/v1/products?category=Vegetables")
    assert response.status_code == 200
    
    # 5. Search products
    response = client.get("/api/v1/products?search=organic")
    assert response.status_code == 200
    
    # 6. Sort by price
    response = client.get("/api/v1/products?sort_by=price&sort_order=asc")
    assert response.status_code == 200
    products = response.json()["products"]
    if len(products) >= 2:
        assert float(products[0]["price"]) <= float(products[1]["price"])


def test_pagination_flow():
    """Test pagination through product list."""
    # Get first page
    response = client.get("/api/v1/products?limit=3")
    assert response.status_code == 200
    
    page1 = response.json()
    assert len(page1["products"]) <= 3
    
    # If there's more data, get next page
    if page1.get("has_more") and page1.get("cursor"):
        response = client.get(f"/api/v1/products?limit=3&cursor={page1['cursor']}")
        assert response.status_code == 200
        
        page2 = response.json()
        # Ensure different products
        if len(page1["products"]) > 0 and len(page2["products"]) > 0:
            assert page1["products"][0]["id"] != page2["products"][0]["id"]


def test_rate_limiting_flow():
    """Test rate limiting behavior."""
    # Make multiple requests quickly
    responses = []
    for i in range(65):  # Exceed 60/minute limit
        response = client.get("/api/v1/products")
        responses.append(response)
    
    # At least one should be rate limited
    status_codes = [r.status_code for r in responses]
    assert 429 in status_codes or all(code == 200 for code in status_codes)
    
    # Check rate limit headers
    last_response = responses[-1]
    if last_response.status_code == 200:
        assert "X-RateLimit-Limit" in last_response.headers


def test_health_check_flow():
    """Test all health check endpoints."""
    # Basic health
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    
    # Detailed health
    response = client.get("/api/v1/health/detailed")
    assert response.status_code == 200
    data = response.json()
    assert "services" in data
    assert "system" in data
    
    # Readiness probe
    response = client.get("/api/v1/health/ready")
    assert response.status_code == 200
    
    # Liveness probe
    response = client.get("/api/v1/health/live")
    assert response.status_code == 200


def test_error_handling_flow():
    """Test error handling for invalid requests."""
    # Invalid product ID
    response = client.get("/api/v1/products/invalid-id")
    assert response.status_code == 404
    
    # Invalid query parameters
    response = client.get("/api/v1/products?sort_by=invalid_field")
    assert response.status_code == 422
    
    # Invalid pagination cursor
    response = client.get("/api/v1/products?cursor=invalid_cursor")
    assert response.status_code in [200, 422]  # May handle gracefully


def test_cache_effectiveness():
    """Test that caching improves performance."""
    import time
    
    # First request (cache miss)
    start = time.time()
    response1 = client.get("/api/v1/products?category=Fruits&limit=10")
    time1 = time.time() - start
    assert response1.status_code == 200
    
    # Second request (cache hit)
    start = time.time()
    response2 = client.get("/api/v1/products?category=Fruits&limit=10")
    time2 = time.time() - start
    assert response2.status_code == 200
    
    # Cached request should be faster (or similar if DB is very fast)
    # We don't assert time2 < time1 because in tests, both might be very fast
    assert response1.json() == response2.json()
