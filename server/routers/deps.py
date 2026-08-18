from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from server.db.session import get_db_session
from server.services import auth_service

# Shared auth dependency for all routers
bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db_session),
):
    """Decode JWT from Authorization header and return the matched user."""
    if not credentials:
        raise HTTPException(status_code=401, detail="缺少 Authorization Bearer token")

    token = credentials.credentials
    return auth_service.get_user_from_token(db, token)


def get_current_admin(current_user=Depends(get_current_user)):
    """Ensure the current user has admin role."""
    if getattr(current_user, "role", "") != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")
    return current_user
