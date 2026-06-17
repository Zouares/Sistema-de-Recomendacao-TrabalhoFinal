from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import ItemDB, get_db
from app.models import ItemCreate, ItemResponse

router = APIRouter()


@router.post("/", response_model=ItemResponse, status_code=status.HTTP_201_CREATED)
def create_item(item_in: ItemCreate, db: Session = Depends(get_db)) -> ItemDB:
    new_item = ItemDB(title=item_in.title, genres=item_in.genres)
    db.add(new_item)
    db.commit()
    db.refresh(new_item)
    return new_item


@router.get("/", response_model=List[ItemResponse])
def list_items(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)) -> List[ItemDB]:
    return db.query(ItemDB).offset(skip).limit(limit).all()


@router.get("/{item_id}", response_model=ItemResponse)
def get_item(item_id: int, db: Session = Depends(get_db)) -> ItemDB:
    item = db.query(ItemDB).filter(ItemDB.id == item_id).first()
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item com ID {item_id} não encontrado.",
        )
    return item
