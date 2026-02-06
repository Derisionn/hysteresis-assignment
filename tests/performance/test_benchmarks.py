"""Performance benchmark tests."""

import pytest
import time
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_product_list_performance():
    """Test product listing performance."""
    times = []
    
    for _ in range(10):
        start = time.time()
        response = client.get("/api/v1/products?limit=20")
        elapsed = time.time() - start
        times.append(elapsed)
        assert response.status_code == 200
    
    avg_time = sum(times) / len(times)
    max_time = max(times)
    
    print(f"\nProduct List Performance:")
    print(f"  Average: {avg_time*1000:.2f}ms")
    print(f"  Max: {max_time*1000:.2f}ms")
    
    # Should be reasonably fast (adjust threshold as needed)
    assert avg_time < 1.0, f"Average response time too slow: {avg_time*1000:.2f}ms"


def test_cached_vs_uncached_performance():
    """Compare cached vs uncached performance."""
    # Clear cache by using unique query
    import random
    unique_param = random.randint(1, 1000000)
    
    # First request (likely cache miss)
    start = time.time()
    response1 = client.get(f"/api/v1/products?limit=10&_cache_bust={unique_param}")
    time_uncached = time.time() - start
    assert response1.status_code == 200
    
    # Second request (cache hit)
    start = time.time()
    response2 = client.get(f"/api/v1/products?limit=10&_cache_bust={unique_param}")
    time_cached = time.time() - start
    assert response2.status_code == 200
    
    print(f"\nCache Performance:")
    print(f"  Uncached: {time_uncached*1000:.2f}ms")
    print(f"  Cached: {time_cached*1000:.2f}ms")
    print(f"  Speedup: {time_uncached/time_cached:.2f}x")


def test_concurrent_requests():
    """Test handling concurrent requests."""
    import concurrent.futures
    
    def make_request():
        response = client.get("/api/v1/products?limit=5")
        return response.status_code
    
    # Make 20 concurrent requests
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        start = time.time()
        futures = [executor.submit(make_request) for _ in range(20)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]
        elapsed = time.time() - start
    
    print(f"\nConcurrent Requests:")
    print(f"  Total time: {elapsed*1000:.2f}ms")
    print(f"  Requests: 20")
    print(f"  Throughput: {20/elapsed:.2f} req/s")
    
    # All should succeed
    assert all(status == 200 for status in results)
    
    # Should handle concurrency well
    assert elapsed < 5.0, f"Concurrent requests too slow: {elapsed:.2f}s"


def test_health_check_performance():
    """Test health check endpoint performance."""
    times = []
    
    for _ in range(20):
        start = time.time()
        response = client.get("/api/v1/health")
        elapsed = time.time() - start
        times.append(elapsed)
        assert response.status_code == 200
    
    avg_time = sum(times) / len(times)
    
    print(f"\nHealth Check Performance:")
    print(f"  Average: {avg_time*1000:.2f}ms")
    
    # Health checks should be very fast
    assert avg_time < 0.1, f"Health check too slow: {avg_time*1000:.2f}ms"


def test_filtering_performance():
    """Test performance with various filters."""
    filters = [
        "?category=Vegetables",
        "?min_price=2.00&max_price=5.00",
        "?search=organic",
        "?category=Fruits&sort_by=price&sort_order=asc",
    ]
    
    results = {}
    
    for filter_str in filters:
        times = []
        for _ in range(5):
            start = time.time()
            response = client.get(f"/api/v1/products{filter_str}")
            elapsed = time.time() - start
            times.append(elapsed)
            assert response.status_code == 200
        
        avg_time = sum(times) / len(times)
        results[filter_str] = avg_time
    
    print(f"\nFilter Performance:")
    for filter_str, avg_time in results.items():
        print(f"  {filter_str}: {avg_time*1000:.2f}ms")
    
    # All filters should be reasonably fast
    for filter_str, avg_time in results.items():
        assert avg_time < 1.0, f"Filter {filter_str} too slow: {avg_time*1000:.2f}ms"
