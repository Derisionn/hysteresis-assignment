"""OAuth 2.0 Google client integration."""

from typing import Optional, Dict, Any
from authlib.integrations.starlette_client import OAuth
from starlette.config import Config
from app.config import settings

# OAuth configuration
config = Config(environ={
    "GOOGLE_CLIENT_ID": settings.google_client_id,
    "GOOGLE_CLIENT_SECRET": settings.google_client_secret,
})

# Initialize OAuth
oauth = OAuth(config)

# Register Google OAuth provider
oauth.register(
    name='google',
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile'
    }
)


class GoogleOAuthClient:
    """Google OAuth 2.0 client."""
    
    def __init__(self):
        self.client = oauth.google
        self.redirect_uri = settings.google_redirect_uri
    
    async def get_authorization_url(self, request) -> tuple[str, str]:
        """
        Generate OAuth authorization URL.
        
        Args:
            request: Starlette request object
            
        Returns:
            Tuple of (authorization_url, state)
        """
        redirect_uri = self.redirect_uri
        return await self.client.authorize_redirect(request, redirect_uri)
    
    async def get_user_info(self, request) -> Optional[Dict[str, Any]]:
        """
        Get user information from OAuth callback.
        
        Args:
            request: Starlette request object with OAuth callback data
            
        Returns:
            User information dictionary or None if failed
        """
        try:
            token = await self.client.authorize_access_token(request)
            user_info = token.get('userinfo')
            
            if user_info:
                return {
                    'oauth_id': user_info.get('sub'),
                    'email': user_info.get('email'),
                    'full_name': user_info.get('name'),
                    'picture': user_info.get('picture'),
                    'email_verified': user_info.get('email_verified', False),
                }
            return None
        except Exception as e:
            print(f"OAuth error: {e}")
            return None


# Global OAuth client instance
google_oauth_client = GoogleOAuthClient()
