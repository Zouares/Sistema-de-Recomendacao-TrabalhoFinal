import pytest
from fastapi.testclient import TestClient

from tests.conftest import client


class TestCreateItem:
    def test_create_item_success(self, client: TestClient) -> None:
        response = client.post(
            "/items/",
            json={"title": "Inception (2010)", "genres": "Action|Sci-Fi|Thriller"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Inception (2010)"
        assert data["genres"] == "Action|Sci-Fi|Thriller"
        assert "id" in data

    def test_create_item_with_default_genres(self, client: TestClient) -> None:
        response = client.post("/items/", json={"title": "Unnamed Movie"})
        assert response.status_code == 201
        assert response.json()["genres"] == "Unknown"

    def test_create_item_empty_title_returns_422(self, client: TestClient) -> None:
        response = client.post("/items/", json={"title": "", "genres": "Drama"})
        assert response.status_code == 422

    def test_create_multiple_items(self, client: TestClient) -> None:
        movies = [
            {"title": "The Matrix (1999)", "genres": "Action|Sci-Fi"},
            {"title": "Interstellar (2014)", "genres": "Adventure|Drama|Sci-Fi"},
            {"title": "The Dark Knight (2008)", "genres": "Action|Crime|Drama"},
        ]
        ids = []
        for movie in movies:
            resp = client.post("/items/", json=movie)
            assert resp.status_code == 201
            ids.append(resp.json()["id"])
        assert len(set(ids)) == 3


class TestGetItem:
    def test_get_existing_item(self, client: TestClient) -> None:
        create_resp = client.post(
            "/items/",
            json={"title": "Pulp Fiction (1994)", "genres": "Crime|Drama"},
        )
        item_id = create_resp.json()["id"]
        response = client.get(f"/items/{item_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == item_id
        assert data["title"] == "Pulp Fiction (1994)"

    def test_get_nonexistent_item_returns_404(self, client: TestClient) -> None:
        response = client.get("/items/999999")
        assert response.status_code == 404
        assert "não encontrado" in response.json()["detail"]


class TestListItems:
    def test_list_items_returns_list(self, client: TestClient) -> None:
        response = client.get("/items/")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_list_items_pagination_skip(self, client: TestClient) -> None:
        all_items = client.get("/items/?skip=0&limit=100").json()
        skipped_items = client.get("/items/?skip=1&limit=100").json()
        if len(all_items) > 1:
            assert len(skipped_items) == len(all_items) - 1

    def test_list_items_pagination_limit(self, client: TestClient) -> None:
        for i in range(3):
            client.post("/items/", json={"title": f"Pagination Movie {i}"})
        response = client.get("/items/?limit=2")
        assert response.status_code == 200
        assert len(response.json()) <= 2

    def test_list_items_all_have_required_fields(self, client: TestClient) -> None:
        response = client.get("/items/?limit=10")
        for item in response.json():
            assert "id" in item
            assert "title" in item
            assert "genres" in item
