"""Kiểm thử endpoint hệ thống + xác thực (không phụ thuộc LLM/DB)."""
from fastapi.testclient import TestClient

import main

client = TestClient(main.app)


def auth_headers() -> dict:
    """Đăng nhập tài khoản mặc định và trả về header Bearer."""
    r = client.post("/auth/login", json={"username": "admin", "password": "admin123"})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


# ---------- Public endpoints ----------
def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_system_status_shape():
    r = client.get("/system-status")
    assert r.status_code == 200
    body = r.json()
    assert set(body.keys()) == {"mysql", "vector_db", "llm"}
    for comp in body.values():
        assert "healthy" in comp


# ---------- Auth ----------
def test_login_success():
    r = client.post("/auth/login", json={"username": "admin", "password": "admin123"})
    assert r.status_code == 200
    assert r.json()["access_token"]


def test_login_wrong_password():
    r = client.post("/auth/login", json={"username": "admin", "password": "sai"})
    assert r.status_code == 401


def test_protected_requires_token():
    # Không có token -> 401
    r = client.post("/chat", json={"question": "test"})
    assert r.status_code == 401


def test_me_endpoint():
    r = client.get("/auth/me", headers=auth_headers())
    assert r.status_code == 200
    assert r.json()["username"] == "admin"


# ---------- Protected endpoints (kèm token) ----------
def test_chat_validation_error():
    r = client.post("/chat", json={"question": ""}, headers=auth_headers())
    assert r.status_code == 422


def test_history_graceful_when_db_down():
    r = client.post("/history", json={"session_id": "test-x", "limit": 5}, headers=auth_headers())
    assert r.status_code == 200
    assert r.json()["count"] == 0


def test_stats_shape():
    r = client.get("/stats", headers=auth_headers())
    assert r.status_code == 200
    body = r.json()
    for key in ("total_queries", "success_rate", "feedback_up", "top_questions", "by_day"):
        assert key in body


def test_feedback_invalid_rating():
    r = client.post("/feedback", json={"rating": "maybe"}, headers=auth_headers())
    assert r.status_code == 422


def test_feedback_valid_rating():
    r = client.post("/feedback", json={"rating": "up", "question": "q", "answer": "a"}, headers=auth_headers())
    assert r.status_code == 200
