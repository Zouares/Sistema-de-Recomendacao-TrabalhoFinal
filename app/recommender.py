import logging
import os
import pickle
import urllib.request
import zipfile
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

try:
    from surprise import SVD, Dataset, Reader, accuracy
    from surprise.model_selection import cross_validate
except ImportError as exc:
    raise ImportError(
        "scikit-surprise não encontrado. Instale com: pip install scikit-surprise"
    ) from exc

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
MOVIELENS_DIR = os.path.join(DATA_DIR, "ml-latest-small")
MODEL_PATH = os.path.join(DATA_DIR, "svd_model.pkl")
MOVIELENS_URL = "https://files.grouplens.org/datasets/movielens/ml-latest-small.zip"


class RecommenderSystem:
    def __init__(self) -> None:
        self.model: Optional[SVD] = None
        self.trainset = None
        self.item_ids: set = set()
        self.is_trained: bool = False
        self._try_load_model()

    def _try_load_model(self) -> None:
        if os.path.exists(MODEL_PATH):
            try:
                with open(MODEL_PATH, "rb") as f:
                    data = pickle.load(f)
                self.model = data["model"]
                self.trainset = data["trainset"]
                self.item_ids = data.get("item_ids", set())
                self.is_trained = True
                logger.info("Modelo SVD carregado de %s", MODEL_PATH)
            except Exception as exc:
                logger.warning("Falha ao carregar modelo salvo: %s", exc)
                self.model = None
                self.is_trained = False

    def load_movielens_data(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        ratings_path = os.path.join(MOVIELENS_DIR, "ratings.csv")
        movies_path = os.path.join(MOVIELENS_DIR, "movies.csv")

        if not (os.path.exists(ratings_path) and os.path.exists(movies_path)):
            logger.info("Baixando MovieLens de %s ...", MOVIELENS_URL)
            os.makedirs(DATA_DIR, exist_ok=True)
            zip_path = os.path.join(DATA_DIR, "ml-latest-small.zip")

            try:
                urllib.request.urlretrieve(MOVIELENS_URL, zip_path)
                with zipfile.ZipFile(zip_path, "r") as zf:
                    zf.extractall(DATA_DIR)
                os.remove(zip_path)
                logger.info("Download concluído em %s", DATA_DIR)
            except Exception as exc:
                logger.error("Erro ao baixar MovieLens: %s", exc)
                raise RuntimeError(f"Não foi possível baixar o dataset: {exc}") from exc

        ratings_df = pd.read_csv(ratings_path)[["userId", "movieId", "rating"]]
        movies_df = pd.read_csv(movies_path)[["movieId", "title", "genres"]]
        logger.info("Dataset: %d ratings, %d filmes", len(ratings_df), len(movies_df))
        return ratings_df, movies_df

    def train(self, ratings_df: pd.DataFrame) -> Dict[str, float]:
        if len(ratings_df) < 5:
            logger.warning("Poucos dados para treinar SVD. Pulando.")
            return {"rmse": 0.0, "mae": 0.0}

        df = ratings_df.copy()
        if "userId" in df.columns:
            df = df.rename(columns={"userId": "user_id", "movieId": "item_id"})
        elif "user_id" not in df.columns:
            df.columns = ["user_id", "item_id", "rating"]

        reader = Reader(rating_scale=(0.5, 5.0))
        data = Dataset.load_from_df(df[["user_id", "item_id", "rating"]], reader)

        logger.info("Iniciando cross-validation SVD ...")
        cv_results = cross_validate(
            SVD(n_factors=100, n_epochs=20, lr_all=0.005, reg_all=0.02, random_state=42),
            data,
            measures=["RMSE", "MAE"],
            cv=5,
            verbose=False,
        )
        avg_rmse = float(np.mean(cv_results["test_rmse"]))
        avg_mae = float(np.mean(cv_results["test_mae"]))
        logger.info("RMSE: %.4f | MAE: %.4f", avg_rmse, avg_mae)

        self.model = SVD(n_factors=100, n_epochs=20, lr_all=0.005, reg_all=0.02, random_state=42)
        full_trainset = data.build_full_trainset()
        self.model.fit(full_trainset)
        self.trainset = full_trainset
        self.item_ids = set(df["item_id"].unique())
        self.is_trained = True

        os.makedirs(DATA_DIR, exist_ok=True)
        with open(MODEL_PATH, "wb") as f:
            pickle.dump(
                {"model": self.model, "trainset": self.trainset, "item_ids": self.item_ids},
                f,
            )
        logger.info("Modelo salvo em %s", MODEL_PATH)
        return {"rmse": avg_rmse, "mae": avg_mae}

    def predict(self, user_id: int, item_id: int) -> float:
        if not self.is_trained or self.model is None:
            return 3.0
        prediction = self.model.predict(str(user_id), str(item_id))
        return round(float(prediction.est), 2)

    def get_recommendations(
        self,
        user_id: int,
        n: int = 10,
        rated_item_ids: Optional[List[int]] = None,
    ) -> List[Dict]:
        if not self.is_trained or self.model is None:
            return []

        already_rated = set(rated_item_ids or [])
        candidates = [iid for iid in self.item_ids if iid not in already_rated]

        if not candidates:
            return []

        predictions = [
            {"item_id": int(iid), "predicted_rating": self.predict(user_id, int(iid))}
            for iid in candidates
        ]
        predictions.sort(key=lambda x: x["predicted_rating"], reverse=True)
        return predictions[:n]


recommender = RecommenderSystem()
