from fastapi import APIRouter, HTTPException, Query, Response, status
from pymysql.err import IntegrityError

from ...deps import DB, CurrentUser
from ...repositories import categories as repo
from ...schemas.category import CategoryIn, CategoryOut, CategoryUpdate
from ...schemas.common import TransactionType

router = APIRouter(prefix="/categories", tags=["categories"])

_DUP = "You already have a category with this name and type"


def _owned_or_404(db, user, category_id: int) -> dict:
    """System categories are visible but immutable; other users' categories don't exist for you."""
    cat = repo.get_visible(db, user["id"], category_id)
    if cat is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Category not found")
    if cat["is_system"]:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "System categories cannot be modified")
    return cat


@router.get("", response_model=list[CategoryOut])
def list_categories(db: DB, user: CurrentUser, type: TransactionType | None = Query(None)):
    return repo.list_visible(db, user["id"], type)


@router.post("", response_model=CategoryOut, status_code=status.HTTP_201_CREATED)
def create_category(body: CategoryIn, db: DB, user: CurrentUser):
    try:
        cid = repo.create(db, user["id"], body.name, body.type, body.icon)
        db.commit()
    except IntegrityError as e:
        db.rollback()
        if e.args[0] == 1062:
            raise HTTPException(status.HTTP_409_CONFLICT, _DUP)
        raise
    return repo.get_owned(db, user["id"], cid)


@router.patch("/{category_id}", response_model=CategoryOut)
def update_category(category_id: int, body: CategoryUpdate, db: DB, user: CurrentUser):
    _owned_or_404(db, user, category_id)
    fields = body.model_dump(exclude_unset=True, exclude_none=True)
    try:
        repo.update(db, user["id"], category_id, fields)
        db.commit()
    except IntegrityError as e:
        db.rollback()
        if e.args[0] == 1062:
            raise HTTPException(status.HTTP_409_CONFLICT, _DUP)
        raise
    return repo.get_owned(db, user["id"], category_id)


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(category_id: int, db: DB, user: CurrentUser):
    _owned_or_404(db, user, category_id)
    try:
        repo.delete(db, user["id"], category_id)
        db.commit()
    except IntegrityError as e:
        db.rollback()
        if e.args[0] in (1451, 1217):  # row is referenced by a foreign key
            raise HTTPException(status.HTTP_409_CONFLICT, "Category is used by transactions; reassign or delete them first")
        raise
    return Response(status_code=status.HTTP_204_NO_CONTENT)
