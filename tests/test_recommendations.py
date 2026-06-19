from typing import Dict
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from tests.conftest import client


def _create_test_user(client: TestClient, username: str) -> Dict:
    resp = client.post("/users/", json={"username": username})
    return resp.json()


def _create_test_item(client: TestClient, title: str, genres: str = "Drama") -> Dict:
    resp = client.post("/items/", json={"title": title, "genres": genres})
    return resp.json()


class TestGetRecommendations:
    def test_recommendations_for_nonexistent_user_returns_404(self, client: TestClient) -> None:
        response = client.get("/recommendations/999999")
        assert response.status_code == 404

    def test_recommendations_with_mock_model(self, client: TestClient) -> None:
        user = _create_test_user(client, "rec_user_alpha")
        item = _create_test_item(client, "Mock Movie Alpha", "Action")
        user_id = user["id"]
        item_id = item["id"]

        mock_recs = [{"item_id": item_id, "predicted_rating": 4.5}]

        with patch("app.routers.recommendations.recommender") as mock_rec:
            mock_rec.is_trained = True
            mock_rec.get_recommendations.return_value = mock_recs
            response = client.get(f"/recommendations/{user_id}?n=5")

        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == user_id
        assert isinstance(data["recommendations"], list)

    def test_recommendations_model_not_trained_returns_503(self, client: TestClient) -> None:
        user = _create_test_user(client, "rec_user_beta")
        with patch("app.routers.recommendations.recommender") as mock_rec:
            mock_rec.is_trained = False
            response = client.get(f"/recommendations/{user['id']}")
        assert response.status_code == 503

    def test_recommendations_response_structure(self, client: TestClient) -> None:
        user = _create_test_user(client, "rec_user_gamma")
        item = _create_test_item(client, "Structural Test Movie", "Comedy")

        mock_recs = [{"item_id": item["id"], "predicted_rating": 3.8}]

        with patch("app.routers.recommendations.recommender") as mock_rec:
            mock_rec.is_trained = True
            mock_rec.get_recommendations.return_value = mock_recs
            response = client.get(f"/recommendations/{user['id']}")

        assert response.status_code == 200
        data = response.json()
        assert "user_id" in data
        assert "recommendations" in data
        assert "total" in data


class TestRateItem:
    def test_rate_item_success(self, client: TestClient) -> None:
        user = _create_test_user(client, "rater_delta")
        item = _create_test_item(client, "Rateable Movie Delta")
        response = client.post(
            "/recommendations/rate",
            json={"user_id": user["id"], "item_id": item["id"], "rating": 4.0},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["rating"] == 4.0

    def test_rate_item_invalid_rating_too_high(self, client: TestClient) -> None:
        user = _create_test_user(client, "rater_epsilon")
        item = _create_test_item(client, "Invalid Rate Movie Epsilon")
        response = client.post(
            "/recommendations/rate",
            json={"user_id": user["id"], "item_id": item["id"], "rating": 6.0},
        )
        assert response.status_code == 422

    def test_rate_item_invalid_rating_too_low(self, client: TestClient) -> None:
        user = _create_test_user(client, "rater_zeta")
        item = _create_test_item(client, "Invalid Rate Movie Zeta")
        response = client.post(
            "/recommendations/rate",
            json={"user_id": user["id"], "item_id": item["id"], "rating": 0.0},
        )
        assert response.status_code == 422

    def test_rate_nonexistent_user_returns_404(self, client: TestClient) -> None:
        item = _create_test_item(client, "Movie for Missing User")
        response = client.post(
            "/recommendations/rate",
            json={"user_id": 999999, "item_id": item["id"], "rating": 3.0},
        )
        assert response.status_code == 404

    def test_rate_nonexistent_item_returns_404(self, client: TestClient) -> None:
        user = _create_test_user(client, "rater_eta")
        response = client.post(
            "/recommendations/rate",
            json={"user_id": user["id"], "item_id": 999999, "rating": 3.0},
        )
        assert response.status_code == 404

    def test_rate_update_existing_rating(self, client: TestClient) -> None:
        user = _create_test_user(client, "rater_theta")
        item = _create_test_item(client, "Update Rating Movie Theta")
        client.post(
            "/recommendations/rate",
            json={"user_id": user["id"], "item_id": item["id"], "rating": 2.0},
        )
        response = client.post(
            "/recommendations/rate",
            json={"user_id": user["id"], "item_id": item["id"], "rating": 5.0},
        )
        assert response.status_code == 201
        assert response.json()["rating"] == 5.0


class TestUserHistory:
    def test_history_empty_for_new_user(self, client: TestClient) -> None:
        user = _create_test_user(client, "history_user_iota")
        response = client.get(f"/recommendations/{user['id']}/history")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["ratings"] == []

    def test_history_shows_submitted_ratings(self, client: TestClient) -> None:
        user = _create_test_user(client, "history_user_kappa")
        item1 = _create_test_item(client, "History Movie 1")
        item2 = _create_test_item(client, "History Movie 2")

        client.post(
            "/recommendations/rate",
            json={"user_id": user["id"], "item_id": item1["id"], "rating": 4.5},
        )
        client.post(
            "/recommendations/rate",
            json={"user_id": user["id"], "item_id": item2["id"], "rating": 3.0},
        )

        response = client.get(f"/recommendations/{user['id']}/history")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert data["username"] == "history_user_kappa"

    def test_history_for_nonexistent_user_returns_404(self, client: TestClient) -> None:
        response = client.get("/recommendations/999999/history")
        assert response.status_code == 404
