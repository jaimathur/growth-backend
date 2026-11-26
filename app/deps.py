from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pymysql.connections import Connection

from .db import get_db
from .repositories import users as users_repo
from .security import decode_access_token

DB = Annotated[Connection, Depends(get_db)]
_bearer = HTTPBearer(auto_error=False, description="JWT from POST /api/v1/auth/login")

_UNAUTH = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Not authenticated",
    headers={"WWW-Authenticate": "Bearer"},
)


def get_current_user(
    db: DB, creds: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)]
) -> dict:
    if creds is None:
        raise _UNAUTH
    try:
        claims = decode_access_token(creds.credentials)
        user_id = int(claims["sub"])
    except (jwt.PyJWTError, ValueError, KeyError):
        raise _UNAUTH
    user = users_repo.get_by_id(db, user_id)
    # Re-read from the DB on every request so deactivation / role changes apply immediately.
    if user is None or not user["is_active"]:
        raise _UNAUTH
    return user


CurrentUser = Annotated[dict, Depends(get_current_user)]


def require_role(*roles: str):
    """Dependency factory for role-protected routes, e.g. Depends(require_role('admin'))."""

    def checker(user: CurrentUser) -> dict:
        if user["role"] not in roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Insufficient permissions")
        return user

    return checker
