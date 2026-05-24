from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException, Security
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel

# MVP Configuration (Move to settings.py in production)
SECRET_KEY = "super-secret-enterprise-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

class TokenData(BaseModel):
    username: str
    role: str

# Mock Database of Enterprise Users
USERS_DB = {
    "admin": {"username": "admin", "password": "password123", "role": "ADMIN"},
    "aryan": {"username": "aryan", "password": "password123", "role": "USER"},
    "sitan": {"username": "sitan", "password": "password123", "role": "USER"}
}

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(token: str = Security(oauth2_scheme)) -> TokenData:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        role: str = payload.get("role")
        if username is None or role is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        return TokenData(username=username, role=role)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

def require_admin(current_user: TokenData = Depends(get_current_user)):
    """Dependency to enforce RBAC: Only ADMINs allowed."""
    if current_user.role != "ADMIN":
        raise HTTPException(status_code=403, detail="Not enough privileges. Admin required.")
    return current_user