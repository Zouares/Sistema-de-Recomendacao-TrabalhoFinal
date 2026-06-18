import logging
from contextlib import asynccontextmanager

import pandas as pd
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import SessionLocal, create_all_tables
from app.recommender import recommender

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


def _seed_and_train() -> None:
    from app.database import ItemDB, RatingDB

    db = SessionLocal()
    try:
        item_count = db.query(ItemDB).count()
        rating_count = db.query(RatingDB).count()
    finally:
        db.close()

    if item_count == 0 or not recommender.is_trained:
        logger.info("Banco vazio. Carregando MovieLens e treinando SVD ...")
        try:
            ratings_df, movies_df = recommender.load_movielens_data()

            db = SessionLocal()
            try:
                existing_ids = {row[0] for row in db.query(ItemDB.id).all()}
                new_items = []
                for _, row in movies_df.iterrows():
                    mid = int(row["movieId"])
                    if mid not in existing_ids:
                        new_items.append(
                            ItemDB(
                                id=mid,
                                title=str(row["title"]),
                                genres=str(row["genres"]),
                            )
                        )
                if new_items:
                    db.bulk_save_objects(new_items)
                    db.commit()
                    logger.info("%d filmes inseridos.", len(new_items))
            finally:
                db.close()

            metrics = recommender.train(ratings_df)
            logger.info("Treino concluído — RMSE: %.4f | MAE: %.4f", metrics["rmse"], metrics["mae"])
        except Exception as exc:
            logger.error("Erro durante seed/treino: %s", exc)
    else:
        logger.info("Banco já populado (%d itens). Modelo carregado.", item_count)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Iniciando Sistema de Recomendação ...")
    create_all_tables()
    _seed_and_train()
    logger.info("API pronta. Acesse /docs para a documentação.")
    yield
    logger.info("Encerrando aplicação.")


app = FastAPI(
    title="Sistema de Recomendação de Filmes",
    description="API REST para recomendação de filmes usando Filtragem Colaborativa com SVD.",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.routers import items, recommendations, users

app.include_router(users.router, prefix="/users", tags=["Usuários"])
app.include_router(items.router, prefix="/items", tags=["Itens"])
app.include_router(recommendations.router, prefix="/recommendations", tags=["Recomendações"])


@app.get("/", tags=["Status"])
async def root() -> dict:
    return {
        "message": "API de Recomendação de Filmes online",
        "docs": "/docs",
        "version": "1.0.0",
        "model_trained": recommender.is_trained,
    }


@app.get("/health", tags=["Status"])
async def health_check() -> dict:
    return {
        "status": "healthy",
        "model_trained": recommender.is_trained,
        "items_in_model": len(recommender.item_ids),
    }
