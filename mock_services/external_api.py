"""Mock external API service for testing integrations."""

import random
import time
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI(title="Mock External API", version="1.0.0")


class PriceUpdate(BaseModel):
    """Price update model."""
    product_id: str
    new_price: float
    supplier: str


class InventoryItem(BaseModel):
    """Inventory item model."""
    product_id: str
    quantity: int
    location: str


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Mock External API", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get("/api/prices")
async def get_prices(category: Optional[str] = None):
    """Get product prices from external supplier."""
    # Simulate occasional failures
    if random.random() < 0.1:  # 10% failure rate
        raise HTTPException(status_code=500, detail="External API error")
    
    # Simulate network delay
    time.sleep(random.uniform(0.1, 0.5))
    
    prices = [
        {"product_id": str(i), "price": round(random.uniform(10, 100), 2), "supplier": "SupplierA"}
        for i in range(10)
    ]
    
    return {"prices": prices, "timestamp": time.time()}


@app.get("/api/inventory")
async def get_inventory():
    """Get inventory levels from external warehouse."""
    # Simulate occasional timeout
    if random.random() < 0.05:  # 5% timeout rate
        time.sleep(10)  # Simulate timeout
    
    inventory = [
        {"product_id": str(i), "quantity": random.randint(0, 100), "location": "Warehouse-A"}
        for i in range(10)
    ]
    
    return {"inventory": inventory, "timestamp": time.time()}


@app.post("/api/orders")
async def create_order(order: dict):
    """Create order in external system."""
    # Simulate rate limiting
    if random.random() < 0.15:  # 15% rate limit
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    
    return {
        "order_id": f"ORD-{random.randint(1000, 9999)}",
        "status": "created",
        "timestamp": time.time()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
