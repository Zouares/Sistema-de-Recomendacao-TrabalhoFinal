from typing import Dict

import pytest
from fastapi.testclient import TestClient

from tests.conftest import client


class TestCreateUser:
    def test_create_user_success(self, client: TestClient) -> None:
        response = client.post("/users/", json={"username": "alice"})
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "alice"
        assert "id" in data
        assert "created_at" in data

    def test_create_user_duplicate_returns_409(self, client: TestClient) -> None:
        client.post("/users/", json={"username": "bob"})
        response = client.post("/users/", json={"username": "bob"})
        assert response.status_code == 409
        assert "já existe" in response.json()["detail"]

    def test_create_user_invalid_username(self, client: TestClient) -> None:
        response = client.post("/users/", json={"username": "usuário inválido!"})
        assert response.status_code == 422

    def test_create_user_short_username(self, client: TestClient) -> None:
        response = client.post("/users/", json={"username": "ab"})
        assert response.status_code == 422

    def test_username_is_normalized_to_lowercase(self, client: TestClient) -> None:
        response = client.post("/users/", json={"username": "Charlie"})
        assert response.status_code == 201
        assert response.json()["username"] == "charlie"


class TestGetUser:
    def test_get_existing_user(self, client: TestClient) -> None:
        create_resp = client.post("/users/", json={"username": "diana"})
        user_id = create_resp.json()["id"]
        response = client.get(f"/users/{user_id}")
        assert response.status_code == 200
        assert response.json()["id"] == user_id
        assert response.json()["username"] == "diana"

    def test_get_nonexistent_user_returns_404(self, client: TestClient) -> None:
        response = client.get("/users/999999")
        assert response.status_code == 404


class TestListUsers:
    def test_list_users_returns_list(self, client: TestClient) -> None:
        response = client.get("/users/")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_list_users_contains_created_users(self, client: TestClient) -> None:
        client.post("/users/", json={"username": "eve_list"})
        response = client.get("/users/")
        usernames = [u["username"] for u in response.json()]
        assert "eve_list" in usernames


class TestDeleteUser:
    def test_delete_existing_user(self, client: TestClient) -> None:
        create_resp = client.post("/users/", json={"username": "to_delete_user"})
        user_id = create_resp.json()["id"]
        del_response = client.delete(f"/users/{user_id}")
        assert del_response.status_code == 204
        get_response = client.get(f"/users/{user_id}")
        assert get_response.status_code == 404

    def test_delete_nonexistent_user_returns_404(self, client: TestClient) -> None:
        response = client.delete("/users/999999")
        assert response.status_code == 404
