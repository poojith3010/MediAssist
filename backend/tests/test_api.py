from fastapi.testclient import TestClient
from uuid import uuid4

from app.main import app


def test_health() -> None:
    assert TestClient(app).get("/api/v1/health").json() == {"status": "ok"}


def test_authentication_and_owner_guard() -> None:
    client = TestClient(app)
    email = f"{uuid4().hex}@example.com"
    response = client.post("/api/v1/auth/register", json={"email": email, "password": "password123"})
    assert response.status_code == 201
    assert client.get("/api/v1/users/me").json()["email"] == email
    assert client.get("/api/v1/documents").status_code == 200
    other = TestClient(app)
    assert other.get("/api/v1/users/me").status_code == 401
