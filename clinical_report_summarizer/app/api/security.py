import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, List

import jwt
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import PyJWTError
from keycloak import KeycloakOpenID
from pydantic import BaseModel

from app.core.config import settings

logger = logging.getLogger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


class KeycloakAuth:
    """Keycloak authentication handler"""
    
    def __init__(self):
        self.keycloak_openid = KeycloakOpenID(
            server_url=settings.KEYCLOAK_SERVER_URL,
            client_id=settings.KEYCLOAK_CLIENT_ID,
            realm_name=settings.KEYCLOAK_REALM,
            client_secret_key=settings.KEYCLOAK_CLIENT_SECRET
        )
    
    async def get_user_roles(self, token: str) -> List[str]:
        """Get user roles from the token"""
        try:
            # Decode the JWT token to get the roles
            options = {"verify_signature": True, "verify_aud": False, "exp": True}
            token_info = self.keycloak_openid.decode_token(token, options=options)
            
            # Extract roles from token
            realm_access = token_info.get("realm_access", {})
            roles = realm_access.get("roles", [])
            
            return roles
            
        except Exception as e:
            logger.error(f"Error getting user roles: {e}")
            return []
    
    async def verify_token(self, token: str) -> Dict:
        """Verify the token with Keycloak"""
        try:
            # Get the public key for token verification
            KEYCLOAK_PUBLIC_KEY = "-----BEGIN PUBLIC KEY-----\n" + \
                                self.keycloak_openid.public_key() + \
                                "\n-----END PUBLIC KEY-----"
            
            # Decode and verify the token
            options = {"verify_signature": True, "verify_aud": False, "exp": True}
            return self.keycloak_openid.decode_token(
                token,
                key=KEYCLOAK_PUBLIC_KEY,
                options=options
            )
            
        except Exception as e:
            logger.error(f"Token verification failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )


# Create a global instance
keycloak_auth = KeycloakAuth()


class TokenPayload(BaseModel):
    """JWT token payload model"""
    sub: str  # subject (user id)
    exp: int  # expiration time
    iat: Optional[int] = None  # issued at
    roles: List[str] = []
    preferred_username: Optional[str] = None
    email: Optional[str] = None


async def get_current_user(token: str = Depends(oauth2_scheme)) -> TokenPayload:
    """Dependency to get the current authenticated user"""
    try:
        # Verify the token with Keycloak
        payload = await keycloak_auth.verify_token(token)
        
        # Extract user info from token
        token_data = TokenPayload(
            sub=payload.get("sub"),
            exp=payload.get("exp"),
            iat=payload.get("iat"),
            preferred_username=payload.get("preferred_username"),
            email=payload.get("email")
        )
        
        # Get user roles
        token_data.roles = await keycloak_auth.get_user_roles(token)
        
        return token_data
        
    except PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def requires_role(required_roles: List[str]):
    """Dependency to check if user has required roles"""
    async def role_checker(
        current_user: TokenPayload = Depends(get_current_user),
    ) -> TokenPayload:
        for role in required_roles:
            if role in current_user.roles:
                return current_user
        
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Insufficient permissions. Required roles: {required_roles}"
        )
    
    return role_checker


# Role-based security dependencies
requires_admin = requires_role(["admin"])
requires_doctor = requires_role(["doctor", "admin"])
requires_nurse = requires_role(["nurse", "doctor", "admin"])
requires_radiologist = requires_role(["radiologist", "doctor", "admin"])
requires_lab_technician = requires_role(["lab_technician", "doctor", "admin"])