"""Authentication endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.core.oauth import google_oauth_client
from app.core.security import create_access_token, create_refresh_token, verify_token
from app.core.session import session_manager
from app.db.base import get_db
from app.db.models.user import User, UserRole
from app.dependencies import get_current_user
from app.schemas.auth import TokenResponse, RefreshTokenRequest, UserResponse, CurrentUser
from app.config import settings

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.get("/login/google")
async def login_google(request: Request):
    """
    Initiate Google OAuth login flow.
    
    Returns:
        Redirect to Google OAuth consent page
    """
    return await google_oauth_client.get_authorization_url(request)


@router.get("/callback/google")
async def callback_google(request: Request, db: Session = Depends(get_db)):
    """
    Handle Google OAuth callback.
    
    Args:
        request: Request object with OAuth callback data
        db: Database session
        
    Returns:
        JWT tokens for authenticated user
    """
    # Get user info from Google
    user_info = await google_oauth_client.get_user_info(request)
    
    if not user_info:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to get user information from Google"
        )
    
    # Check if user exists
    user = db.query(User).filter(
        User.oauth_provider == "google",
        User.oauth_id == user_info['oauth_id']
    ).first()
    
    # Create new user if doesn't exist
    if not user:
        user = User(
            email=user_info['email'],
            full_name=user_info.get('full_name'),
            oauth_provider="google",
            oauth_id=user_info['oauth_id'],
            role=UserRole.USER,
            is_active=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    
    # Generate tokens
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    # Store session in Redis
    session_manager.create_session(
        user_id=str(user.id),
        data={
            "email": user.email,
            "role": user.role.value,
            "refresh_token": refresh_token
        }
    )
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_access_token(
    request: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """
    Refresh access token using refresh token.
    
    Args:
        request: Refresh token request
        db: Database session
        
    Returns:
        New access token
    """
    # Verify refresh token
    payload = verify_token(request.refresh_token, token_type="refresh")
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )
    
    user_id = payload.get("sub")
    
    # Verify session exists
    session_data = session_manager.get_session(user_id)
    if not session_data or session_data.get("refresh_token") != request.refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid session"
        )
    
    # Verify user exists and is active
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    # Generate new access token
    access_token = create_access_token(data={"sub": str(user.id)})
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=request.refresh_token,
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60
    )


@router.post("/logout")
async def logout(current_user: CurrentUser = Depends(get_current_user)):
    """
    Logout current user by invalidating session.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Success message
    """
    session_manager.delete_session(current_user.id)
    return {"message": "Successfully logged out"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current user information.
    
    Args:
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        User information
    """
    user = db.query(User).filter(User.id == current_user.id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse(
        id=str(user.id),
        email=user.email,
        full_name=user.full_name,
        role=user.role.value,
        is_active=user.is_active,
        created_at=user.created_at
    )
