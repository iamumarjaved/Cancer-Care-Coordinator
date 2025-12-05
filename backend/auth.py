"""Authentication module for Clerk JWT validation."""

import logging
from typing import Optional
from datetime import datetime, timezone

import httpx
import jwt
from jwt import PyJWKClient
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

from config import settings

logger = logging.getLogger(__name__)

# HTTP Bearer token security scheme
security = HTTPBearer(auto_error=False)


class User(BaseModel):
    """Authenticated user model."""
    id: str
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None

    @property
    def full_name(self) -> str:
        parts = [p for p in [self.first_name, self.last_name] if p]
        return " ".join(parts) if parts else self.email or self.id


class ClerkJWKSClient:
    """Client for fetching and caching Clerk JWKS keys."""

    def __init__(self, jwks_url: str):
        self.jwks_url = jwks_url
        self._client: Optional[PyJWKClient] = None

    @property
    def client(self) -> PyJWKClient:
        if self._client is None:
            self._client = PyJWKClient(self.jwks_url)
        return self._client

    def get_signing_key(self, token: str):
        """Get the signing key for a token."""
        return self.client.get_signing_key_from_jwt(token)


# Global JWKS client instance (lazy loaded)
_jwks_client: Optional[ClerkJWKSClient] = None


def get_jwks_client() -> ClerkJWKSClient:
    """Get or create the JWKS client."""
    global _jwks_client
    if _jwks_client is None and settings.CLERK_JWKS_URL:
        _jwks_client = ClerkJWKSClient(settings.CLERK_JWKS_URL)
    return _jwks_client


def decode_clerk_token(token: str) -> dict:
    """Decode and validate a Clerk JWT token.

    Args:
        token: The JWT token string

    Returns:
        The decoded token payload

    Raises:
        HTTPException: If token validation fails
    """
    try:
        jwks_client = get_jwks_client()
        if not jwks_client:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Authentication not configured"
            )

        # Get the signing key from JWKS
        signing_key = jwks_client.get_signing_key(token)

        # Decode and validate the token
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            options={
                "verify_exp": True,
                "verify_iat": True,
                "verify_aud": False,  # Clerk doesn't always set audience
            }
        )

        return payload

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid token: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    except Exception as e:
        logger.error(f"Token validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token validation failed"
        )


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[User]:
    """Get the current authenticated user from the JWT token.

    This dependency returns None if auth is disabled or no token is provided.
    Use get_required_user for endpoints that require authentication.

    Args:
        credentials: The HTTP Authorization credentials

    Returns:
        The authenticated User or None if not authenticated
    """
    # If auth is disabled, return None (allow anonymous access)
    if not settings.AUTH_ENABLED:
        return None

    # If no credentials provided, return None
    if not credentials:
        return None

    # Decode the token
    payload = decode_clerk_token(credentials.credentials)

    # Extract user info from Clerk token
    # Clerk tokens include user info in different fields depending on session type
    user_id = payload.get("sub")  # Subject is always the user ID

    # Try to get user metadata from token
    user = User(
        id=user_id,
        email=payload.get("email"),
        first_name=payload.get("first_name"),
        last_name=payload.get("last_name"),
    )

    return user


async def get_required_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> User:
    """Get the current user, requiring authentication.

    Use this dependency for endpoints that require a logged-in user.

    Args:
        credentials: The HTTP Authorization credentials

    Returns:
        The authenticated User

    Raises:
        HTTPException: If not authenticated
    """
    # If auth is disabled, return a mock user
    if not settings.AUTH_ENABLED:
        return User(id="system", email="system@localhost", first_name="System")

    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"}
        )

    # Decode the token
    payload = decode_clerk_token(credentials.credentials)

    # Extract user info
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: missing user ID"
        )

    return User(
        id=user_id,
        email=payload.get("email"),
        first_name=payload.get("first_name"),
        last_name=payload.get("last_name"),
    )


# Convenience function to check if auth is enabled
def is_auth_enabled() -> bool:
    """Check if authentication is enabled."""
    return settings.AUTH_ENABLED and bool(settings.CLERK_JWKS_URL)
