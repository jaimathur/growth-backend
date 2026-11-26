from datetime import date

from fastapi import APIRouter, HTTPException, Query, Response, status

from ...deps import DB, CurrentUser
from ...repositories import categories as categories_repo
from ...repositories import transactions as repo
from ...schemas.common import TransactionType
from ...schemas.transaction import TransactionIn, TransactionOut, TransactionPage, TransactionPatch

router = APIRouter(prefix="/transactions", tags=["transactions"])


def _check_category(db, user_id: int, category_id: int, type_: str) -> None:
    cat = categories_repo.get_visible(db, user_id, category_id)
    if cat is None:
        raise HTTPException(422, "Unknown category_id")
    if cat["type"] != type_:
        raise HTTPException(
            422,
            f"Category '{cat['name']}' is an {cat['type']} category and cannot be used for an {type_} transaction",
        )


def _get_or_404(db, user_id: int, txn_id: int) -> dict:
    row = repo.get(db, user_id, txn_id)
    if row is None:  # also what other users' ids look like: no existence leak
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Transaction not found")
    return row


@router.get("", response_model=TransactionPage)
def list_transactions(
    db: DB,
    user: CurrentUser,
    type: TransactionType | None = None,
    category_id: int | None = Query(None, gt=0),
    q: str | None = Query(None, max_length=100, description="Search in title and category name"),
    date_from: date | None = None,
    date_to: date | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(12, ge=1, le=100),
):
    if date_from and date_to and date_from > date_to:
        raise HTTPException(422, "date_from must not be after date_to")
    items, total = repo.search(
        db, user["id"], type_=type, category_id=category_id, q=(q or "").strip() or None,
        date_from=date_from, date_to=date_to, page=page, page_size=page_size,
    )
    return TransactionPage(items=items, total=total, page=page, page_size=page_size)


@router.post("", response_model=TransactionOut, status_code=status.HTTP_201_CREATED)
def create_transaction(body: TransactionIn, db: DB, user: CurrentUser):
    _check_category(db, user["id"], body.category_id, body.type)
    txn_id = repo.create(db, user["id"], body.model_dump())
    db.commit()
    return repo.get(db, user["id"], txn_id)


@router.get("/{txn_id}", response_model=TransactionOut)
def get_transaction(txn_id: int, db: DB, user: CurrentUser):
    return _get_or_404(db, user["id"], txn_id)


def _apply(db, user_id: int, txn_id: int, merged: dict) -> dict:
    _check_category(db, user_id, merged["category_id"], merged["type"])
    repo.update(db, user_id, txn_id, merged)
    db.commit()
    return repo.get(db, user_id, txn_id)


@router.put("/{txn_id}", response_model=TransactionOut)
def replace_transaction(txn_id: int, body: TransactionIn, db: DB, user: CurrentUser):
    _get_or_404(db, user["id"], txn_id)
    return _apply(db, user["id"], txn_id, body.model_dump())


@router.patch("/{txn_id}", response_model=TransactionOut)
def patch_transaction(txn_id: int, body: TransactionPatch, db: DB, user: CurrentUser):
    current = _get_or_404(db, user["id"], txn_id)
    changes = {k: getattr(body, k) for k in body.model_fields_set}
    if any(v is None for v in changes.values()):
        raise HTTPException(422, "Fields cannot be set to null")
    merged = {
        "title": current["title"], "amount": current["amount"], "type": current["type"],
        "category_id": current["category"]["id"], "payment_method": current["payment_method"],
        "date": current["date"],
    } | changes
    return _apply(db, user["id"], txn_id, merged)


@router.delete("/{txn_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transaction(txn_id: int, db: DB, user: CurrentUser):
    if not repo.delete(db, user["id"], txn_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Transaction not found")
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
