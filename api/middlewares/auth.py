"""
Authentication middleware.
Handles user authentication and authorization for API endpoints.
"""

from fastapi import Request, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from typing import Optional, Dict, Any
import jwt
from datetime import datetime, timedelta

# This would be replaced with actual secret key in production
SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


async def verify_token(token: str) -> Dict[str, Any]:
    """
    Verify the JWT token and return the payload.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    Get the current user from the token.
    """
    payload = await verify_token(token)
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # Here you would typically fetch the user from the database
    return {"user_id": user_id}


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None):
    """
    Create a new JWT access token.
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


class AuthMiddleware:
    """
    Middleware for handling authentication.
    """
    async def __call__(self, request: Request, call_next):
        # Skip authentication for certain paths
        if request.url.path in ["/docs", "/redoc", "/openapi.json", "/token"]:
            return await call_next(request)

        # Get the Authorization header
        authorization = request.headers.get("Authorization")
        if not authorization:
            raise HTTPException(
                status_code=401,
                detail="Not authenticated",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Extract the token
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(
                status_code=401,
                detail="Invalid authentication scheme",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Verify the token
        try:
            payload = await verify_token(token)
            # Add the user to the request state
            request.state.user = payload
        except HTTPException:
            raise

        # Continue processing the request
        return await call_next(request)