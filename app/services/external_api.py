"""External API client with reliability patterns."""

import httpx
from typing import Optional, Dict, Any
from app.config import settings
from app.core.circuit_breaker import CircuitBreaker, CircuitBreakerError
from app.core.retry import RetryStrategy, RetryError


class ExternalAPIClient:
    """
    Client for external API with circuit breaker and retry logic.
    """
    
    def __init__(self):
        """Initialize external API client."""
        self.base_url = settings.external_api_url
        self.timeout = settings.external_api_timeout
        
        # Circuit breaker configuration
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=5,
            recovery_timeout=60,
            expected_exception=Exception,
            name="external_api"
        )
        
        # Retry strategy configuration
        self.retry_strategy = RetryStrategy(
            max_attempts=3,
            base_delay=1.0,
            max_delay=10.0,
            exponential_base=2.0,
            jitter=True
        )
    
    async def get_product_enrichment(self, product_id: str) -> Optional[Dict[str, Any]]:
        """
        Get product enrichment data from external API.
        
        Args:
            product_id: Product ID
            
        Returns:
            Enrichment data or None if unavailable
        """
        try:
            # Use circuit breaker to protect against cascading failures
            result = self.circuit_breaker.call(
                self._fetch_with_retry,
                f"/products/{product_id}/enrichment"
            )
            return result
        except CircuitBreakerError as e:
            print(f"Circuit breaker open: {e}")
            return None
        except RetryError as e:
            print(f"All retry attempts failed: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error: {e}")
            return None
    
    async def get_recommendations(self, product_id: str, limit: int = 5) -> list:
        """
        Get product recommendations from external API.
        
        Args:
            product_id: Product ID
            limit: Number of recommendations
            
        Returns:
            List of recommended product IDs
        """
        try:
            result = self.circuit_breaker.call(
                self._fetch_with_retry,
                f"/products/{product_id}/recommendations",
                params={"limit": limit}
            )
            return result.get("recommendations", [])
        except (CircuitBreakerError, RetryError) as e:
            print(f"Failed to get recommendations: {e}")
            return []
        except Exception as e:
            print(f"Unexpected error: {e}")
            return []
    
    async def get_pricing_data(self, product_ids: list[str]) -> Dict[str, Any]:
        """
        Get pricing data for multiple products.
        
        Args:
            product_ids: List of product IDs
            
        Returns:
            Dictionary of product pricing data
        """
        try:
            result = self.circuit_breaker.call(
                self._fetch_with_retry,
                "/pricing/batch",
                method="POST",
                json={"product_ids": product_ids}
            )
            return result
        except (CircuitBreakerError, RetryError) as e:
            print(f"Failed to get pricing data: {e}")
            return {}
        except Exception as e:
            print(f"Unexpected error: {e}")
            return {}
    
    def _fetch_with_retry(
        self,
        endpoint: str,
        method: str = "GET",
        params: Optional[Dict] = None,
        json: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Fetch data with retry logic.
        
        Args:
            endpoint: API endpoint
            method: HTTP method
            params: Query parameters
            json: JSON body
            
        Returns:
            Response data
        """
        return self.retry_strategy.execute(
            self._make_request,
            endpoint,
            method,
            params,
            json,
            exceptions=(httpx.HTTPError, httpx.TimeoutException)
        )
    
    def _make_request(
        self,
        endpoint: str,
        method: str = "GET",
        params: Optional[Dict] = None,
        json: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Make HTTP request to external API.
        
        Args:
            endpoint: API endpoint
            method: HTTP method
            params: Query parameters
            json: JSON body
            
        Returns:
            Response data
        """
        url = f"{self.base_url}{endpoint}"
        
        with httpx.Client(timeout=self.timeout) as client:
            response = client.request(
                method=method,
                url=url,
                params=params,
                json=json
            )
            response.raise_for_status()
            return response.json()
    
    def get_circuit_state(self) -> dict:
        """Get circuit breaker state."""
        return self.circuit_breaker.get_state()
    
    def reset_circuit(self):
        """Reset circuit breaker."""
        self.circuit_breaker.reset()


# Global client instance
external_api_client = ExternalAPIClient()
