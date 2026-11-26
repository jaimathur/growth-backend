from fastapi import APIRouter, HTTPException, status
from pymysql.err import IntegrityError

from ...config import get_settings
from ...deps import DB, CurrentUser
from ...repositories import users as users_repo
from ...schemas.auth import LoginIn, RegisterIn, TokenOut, UserOut
from ...security import create_access_token, hash_password, needs_rehash, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


def _token_response(user: dict) -> TokenOut:
    token, ttl = create_access_token(user["id"], user["role"])
    return TokenOut(access_token=token, expires_in=ttl, user=UserOut.model_validate(user))


@router.post("/register", response_model=TokenOut, status_code=status.HTTP_201_CREATED)
def register(body: RegisterIn, db: DB):
    if not get_settings().allow_registration:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Registration is disabled")
    try:
        # Public sign-up always creates the least-privileged 'user' role.
        user_id = users_repo.create(
            db, email=body.email, full_name=body.full_name, password_hash=hash_password(body.password)
        )
        db.commit()
    except IntegrityError as e:
        db.rollback()
        if e.args and e.args[0] == 1062:
            raise HTTPException(status.HTTP_409_CONFLICT, "An account with this email already exists")
        raise
    return _token_response(users_repo.get_by_id(db, user_id))


@router.post("/login", response_model=TokenOut)
def login(body: LoginIn, db: DB):
    user = users_repo.get_by_email(db, body.email)
    ok = verify_password(body.password, user["password_hash"] if user else None)
    if not user or not ok:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, "Invalid email or password", headers={"WWW-Authenticate": "Bearer"}
        )
    if not user["is_active"]:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "This account is disabled")
    new_hash = hash_password(body.password) if needs_rehash(user["password_hash"]) else None
    users_repo.record_login(db, user["id"], new_hash)
    db.commit()
    return _token_response(user)


@router.get("/me", response_model=UserOut)
def me(user: CurrentUser):
    return user
