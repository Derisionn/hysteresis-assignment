"""Health check endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db.base import get_db
from app.core.cache import cache_manager
from app.services.external_api import external_api_client
from datetime import datetime
import psutil
import os

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("")
async def health_check():
    """
    Basic health check endpoint.
    
    Returns:
        Simple health status
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }


@router.get("/detailed")
async def detailed_health_check(db: Session = Depends(get_db)):
    """
    Detailed health check with all service statuses.
    
    Returns:
        Comprehensive health information
    """
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {}
    }
    
    # Check database
    try:
        db.execute(text("SELECT 1"))
        health_status["services"]["database"] = {
            "status": "healthy",
            "message": "Database connection successful"
        }
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["services"]["database"] = {
            "status": "unhealthy",
            "message": f"Database error: {str(e)}"
        }
    
    # Check Redis cache
    try:
        cache_stats = cache_manager.get_stats()
        health_status["services"]["cache"] = {
            "status": "healthy",
            "message": "Redis connection successful",
            "stats": cache_stats
        }
    except Exception as e:
        health_status["status"] = "degraded"
        health_status["services"]["cache"] = {
            "status": "unhealthy",
            "message": f"Redis error: {str(e)}"
        }
    
    # Check external API circuit breaker
    circuit_state = external_api_client.get_circuit_state()
    health_status["services"]["external_api"] = {
        "status": "healthy" if circuit_state["state"] == "closed" else "degraded",
        "circuit_breaker": circuit_state
    }
    
    # System metrics
    health_status["system"] = {
        "cpu_percent": psutil.cpu_percent(interval=0.1),
        "memory_percent": psutil.virtual_memory().percent,
        "disk_percent": psutil.disk_usage('/').percent
    }
    
    return health_status


@router.get("/ready")
async def readiness_check(db: Session = Depends(get_db)):
    """
    Readiness probe for Kubernetes.
    
    Returns:
        Ready status if all critical services are available
    """
    try:
        # Check database
        db.execute(text("SELECT 1"))
        
        # Check Redis
        cache_manager.client.ping()
        
        return {
            "status": "ready",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "not_ready",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


@router.get("/live")
async def liveness_check():
    """
    Liveness probe for Kubernetes.
    
    Returns:
        Alive status if application is running
    """
    return {
        "status": "alive",
        "timestamp": datetime.now().isoformat()
    }
