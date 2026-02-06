"""Redis session management."""

import json
from typing import Optional, Any
from redis import Redis
from app.config import settings

# Redis client instance
redis_client = Redis.from_url(
    settings.redis_url,
    max_connections=settings.redis_max_connections,
    decode_responses=True
)


class SessionManager:
    """Manage user sessions in Redis."""
    
    def __init__(self):
        self.client = redis_client
        self.prefix = "session:"
    
    def create_session(self, user_id: str, data: dict, ttl: int = None) -> str:
        """
        Create a new session.
        
        Args:
            user_id: User identifier
            data: Session data to store
            ttl: Time to live in seconds (default: 7 days)
            
        Returns:
            Session key
        """
        if ttl is None:
            ttl = settings.refresh_token_expire_days * 24 * 60 * 60  # Convert days to seconds
        
        session_key = f"{self.prefix}{user_id}"
        self.client.setex(session_key, ttl, json.dumps(data))
        return session_key
    
    def get_session(self, user_id: str) -> Optional[dict]:
        """
        Get session data.
        
        Args:
            user_id: User identifier
            
        Returns:
            Session data or None if not found
        """
        session_key = f"{self.prefix}{user_id}"
        data = self.client.get(session_key)
        
        if data:
            return json.loads(data)
        return None
    
    def update_session(self, user_id: str, data: dict) -> bool:
        """
        Update existing session.
        
        Args:
            user_id: User identifier
            data: New session data
            
        Returns:
            True if updated, False if session doesn't exist
        """
        session_key = f"{self.prefix}{user_id}"
        
        # Get current TTL
        ttl = self.client.ttl(session_key)
        if ttl <= 0:
            return False
        
        # Update with same TTL
        self.client.setex(session_key, ttl, json.dumps(data))
        return True
    
    def delete_session(self, user_id: str) -> bool:
        """
        Delete a session.
        
        Args:
            user_id: User identifier
            
        Returns:
            True if deleted, False if not found
        """
        session_key = f"{self.prefix}{user_id}"
        return bool(self.client.delete(session_key))
    
    def extend_session(self, user_id: str, ttl: int = None) -> bool:
        """
        Extend session TTL.
        
        Args:
            user_id: User identifier
            ttl: New time to live in seconds
            
        Returns:
            True if extended, False if session doesn't exist
        """
        if ttl is None:
            ttl = settings.refresh_token_expire_days * 24 * 60 * 60
        
        session_key = f"{self.prefix}{user_id}"
        return bool(self.client.expire(session_key, ttl))


# Global session manager instance
session_manager = SessionManager()
