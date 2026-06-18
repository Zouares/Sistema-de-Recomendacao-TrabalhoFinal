import logging
from typing import List

import pandas as pd
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import ItemDB, RatingDB, UserDB, get_db
from app.models import (
    RatingCreate,
    RatingHistory,
    RatingResponse,
    RecommendationList,
    RecommendationResponse,
)
from app.recommender import recommender

logger = logging.getLogger(__name__)
router = APIRouter()


def _retrain_model(db_session_factory) -> None:
    logger.info("Iniciando re-treino do modelo ...")
    db = db_session_factory()
    try:
        rows = db.query(RatingDB).all()
        if len(rows) < 5:
            logger.info("Poucos ratings para re-treinar (%d).", len(rows))
            return

        ratings_data = [
            {"user_id": r.user_id, "item_id": r.item_id, "rating": r.rating}
            for r in rows
        ]
        df = pd.DataFrame(ratings_data)
        metrics = recommender.train(df)
        logger.info("Re-treino concluído — RMSE: %.4f | MAE: %.4f", metrics["rmse"], metrics["mae"])
    except Exception as exc:
        logger.error("Erro no re-treino: %s", exc)
    finally:
        db.close()


@router.get("/{user_id}", response_model=RecommendationList)
def get_recommendations(
    user_id: int,
    n: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
) -> RecommendationList:
    user = db.query(UserDB).filter(UserDB.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Usuário com ID {user_id} não encontrado.",
        )

    if not recommender.is_trained:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Modelo ainda não treinado. Tente novamente em instantes.",
        )

    rated_ids = [
        row[0]
        for row in db.query(RatingDB.item_id).filter(RatingDB.user_id == user_id).all()
    ]

    raw_recs = recommender.get_recommendations(user_id=user_id, n=n, rated_item_ids=rated_ids)

    recommendations: List[RecommendationResponse] = []
    for rec in raw_recs:
        item = db.query(ItemDB).filter(ItemDB.id == rec["item_id"]).first()
        if item:
            recommendations.append(
                RecommendationResponse(
                    item_id=item.id,
                    title=item.title,
                    predicted_rating=rec["predicted_rating"],
                    genres=item.genres,
                )
            )

    return RecommendationList(
        user_id=user_id,
        recommendations=recommendations,
        total=len(recommendations),
    )


@router.post("/rate", response_model=RatingResponse, status_code=status.HTTP_201_CREATED)
def rate_item(
    rating_in: RatingCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> RatingDB:
    user = db.query(UserDB).filter(UserDB.id == rating_in.user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Usuário com ID {rating_in.user_id} não encontrado.",
        )

    item = db.query(ItemDB).filter(ItemDB.id == rating_in.item_id).first()
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item com ID {rating_in.item_id} não encontrado.",
        )

    existing = (
        db.query(RatingDB)
        .filter(RatingDB.user_id == rating_in.user_id, RatingDB.item_id == rating_in.item_id)
        .first()
    )
    if existing:
        existing.rating = rating_in.rating
        db.commit()
        db.refresh(existing)
        saved_rating = existing
    else:
        new_rating = RatingDB(
            user_id=rating_in.user_id,
            item_id=rating_in.item_id,
            rating=rating_in.rating,
        )
        db.add(new_rating)
        db.commit()
        db.refresh(new_rating)
        saved_rating = new_rating

    from app.database import SessionLocal
    background_tasks.add_task(_retrain_model, SessionLocal)

    return saved_rating


@router.get("/{user_id}/history", response_model=RatingHistory)
def get_user_history(user_id: int, db: Session = Depends(get_db)) -> RatingHistory:
    user = db.query(UserDB).filter(UserDB.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Usuário com ID {user_id} não encontrado.",
        )

    ratings = db.query(RatingDB).filter(RatingDB.user_id == user_id).all()

    return RatingHistory(
        user_id=user_id,
        username=user.username,
        ratings=[
            RatingResponse(
                id=r.id,
                user_id=r.user_id,
                item_id=r.item_id,
                rating=r.rating,
                timestamp=r.timestamp,
            )
            for r in ratings
        ],
        total=len(ratings),
    )
