from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from app.core.config import settings

security = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(
            token,
            settings.SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            options={"verify_aud": False}
        )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

def require_role(*roles):
    allowed_roles = [r.value if hasattr(r, "value") else str(r) for r in roles]
    def role_checker(user: dict = Depends(get_current_user)):
        # Inspect user_metadata, app_metadata, or direct role claim
        user_role = (
            user.get("user_metadata", {}).get("role")
            or user.get("app_metadata", {}).get("role")
            or user.get("role", "customer")
        )
        user_role_val = user_role.value if hasattr(user_role, "value") else str(user_role)
        if user_role_val not in allowed_roles:
            raise HTTPException(status_code=403, detail="Not enough permissions")
        return user
    return role_checker

def require_roles(*roles):
    return require_role(*roles)


