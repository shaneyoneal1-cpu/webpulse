import os
import sys
import pytest
import pyotp
import tempfile

sys.path.insert(0, os.path.dirname(__file__))

# Use a temporary file for the test database
_test_db_fd, _test_db_path = tempfile.mkstemp(suffix=".db")
os.close(_test_db_fd)
TEST_DB_URL = f"sqlite:///{_test_db_path}"

# Set before any app imports
os.environ["DATABASE_URL"] = TEST_DB_URL

# Now import - database.py will use the test DB
import database
import config
from database import Base, SessionLocal, engine
from models import User, Website, CheckResult, SystemConfig
from auth import get_password_hash, verify_password
from monitor import generate_suggestions

# Need to import main for app, but suppress scheduler
config.CHECK_INTERVAL_SECONDS = 999999
from main import app
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def test_client():
    """Module-scoped TestClient so lifespan runs once."""
    with TestClient(app) as c:
        yield c


@pytest.fixture(autouse=True)
def reset_data(test_client):
    """Clear data before each test and seed admin."""
    db = SessionLocal()
    try:
        db.query(CheckResult).delete()
        db.query(Website).delete()
        db.query(SystemConfig).delete()
        db.query(User).delete()
        db.commit()

        admin = User(
            username="admin",
            hashed_password=get_password_hash("WebPulse@2026!"),
            is_main_admin=True,
            must_change_password=False,
            totp_secret=pyotp.random_base32(),
            totp_enabled=True,
            totp_verified=True,
            permissions={
                "view_websites": True,
                "manage_websites": True,
                "run_checks": True,
                "view_users": True,
                "manage_users": True,
                "view_settings": True,
                "manage_settings": True,
            },
        )
        db.add(admin)
        db.commit()
    finally:
        db.close()
    yield


def get_admin_token(client):
    db = SessionLocal()
    admin = db.query(User).filter(User.username == "admin").first()
    totp = pyotp.TOTP(admin.totp_secret)
    code = totp.now()
    db.close()

    res = client.post("/api/auth/login", json={
        "username": "admin",
        "password": "WebPulse@2026!",
        "totp_code": code,
    })
    assert res.status_code == 200, f"Login failed: {res.json()}"
    return res.json()["access_token"]


# ==================== AUTH TESTS ====================

def test_health(test_client):
    res = test_client.get("/api/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


def test_login_invalid_credentials(test_client):
    res = test_client.post("/api/auth/login", json={"username": "admin", "password": "wrong"})
    assert res.status_code == 401


def test_login_success_with_totp(test_client):
    token = get_admin_token(test_client)
    assert token is not None and len(token) > 20


def test_login_totp_required(test_client):
    res = test_client.post("/api/auth/login", json={
        "username": "admin",
        "password": "WebPulse@2026!",
    })
    assert res.status_code == 200
    data = res.json()
    assert data["totp_required"] is True


def test_get_me(test_client):
    token = get_admin_token(test_client)
    res = test_client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert res.json()["username"] == "admin"
    assert res.json()["is_main_admin"] is True


def test_change_password(test_client):
    token = get_admin_token(test_client)
    res = test_client.post("/api/auth/change-password", json={
        "current_password": "WebPulse@2026!",
        "new_password": "NewPassword123!",
    }, headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200


def test_forced_password_change(test_client):
    db = SessionLocal()
    user = User(
        username="newuser",
        hashed_password=get_password_hash("TempPass123!"),
        is_main_admin=False,
        must_change_password=True,
        permissions={"view_websites": True},
    )
    db.add(user)
    db.commit()
    db.close()

    res = test_client.post("/api/auth/login", json={
        "username": "newuser",
        "password": "TempPass123!",
    })
    assert res.status_code == 200
    data = res.json()
    assert data["must_change_password"] is True


def test_totp_setup_required_for_new_user(test_client):
    """User without TOTP gets totp_setup_required."""
    db = SessionLocal()
    user = User(
        username="nototp",
        hashed_password=get_password_hash("NoTotp123!"),
        is_main_admin=False,
        must_change_password=False,
        totp_enabled=False,
        totp_verified=False,
        permissions={"view_websites": True},
    )
    db.add(user)
    db.commit()
    db.close()

    res = test_client.post("/api/auth/login", json={
        "username": "nototp",
        "password": "NoTotp123!",
    })
    assert res.status_code == 200
    data = res.json()
    assert data["totp_setup_required"] is True


# ==================== WEBSITE TESTS ====================

def test_add_website(test_client):
    token = get_admin_token(test_client)
    res = test_client.post("/api/websites", json={
        "name": "Google",
        "url": "https://www.google.com",
    }, headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert res.json()["name"] == "Google"


def test_list_websites(test_client):
    token = get_admin_token(test_client)
    test_client.post("/api/websites", json={
        "name": "GitHub",
        "url": "https://github.com",
    }, headers={"Authorization": f"Bearer {token}"})

    res = test_client.get("/api/websites", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert len(res.json()) >= 1


def test_delete_website(test_client):
    token = get_admin_token(test_client)
    res = test_client.post("/api/websites", json={
        "name": "Test",
        "url": "https://test.com",
    }, headers={"Authorization": f"Bearer {token}"})
    site_id = res.json()["id"]

    res = test_client.delete(f"/api/websites/{site_id}", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200


def test_max_websites(test_client):
    token = get_admin_token(test_client)
    for i in range(10):
        res = test_client.post("/api/websites", json={
            "name": f"Site {i}",
            "url": f"https://site{i}.com",
        }, headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 200

    res = test_client.post("/api/websites", json={
        "name": "Site 11",
        "url": "https://site11.com",
    }, headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 400


def test_check_website_live(test_client):
    token = get_admin_token(test_client)
    res = test_client.post("/api/websites", json={
        "name": "httpbin",
        "url": "https://httpbin.org/get",
    }, headers={"Authorization": f"Bearer {token}"})
    site_id = res.json()["id"]

    res = test_client.post(f"/api/websites/{site_id}/check", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.json()
    assert "is_up" in data
    assert "latency_ms" in data
    assert "suggestions" in data
    assert isinstance(data["suggestions"], list)


def test_dashboard(test_client):
    token = get_admin_token(test_client)
    res = test_client.get("/api/websites/dashboard", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert "total_websites" in res.json()


def test_weekly_roundup(test_client):
    token = get_admin_token(test_client)
    res = test_client.get("/api/websites/weekly-roundup", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.json()
    assert "tip" in data
    assert len(data["tip"]) > 0


def test_website_history(test_client):
    token = get_admin_token(test_client)
    res = test_client.post("/api/websites", json={
        "name": "HistTest",
        "url": "https://example.com",
    }, headers={"Authorization": f"Bearer {token}"})
    site_id = res.json()["id"]

    test_client.post(f"/api/websites/{site_id}/check", headers={"Authorization": f"Bearer {token}"})

    res = test_client.get(f"/api/websites/{site_id}/history", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.json()
    assert len(data) >= 1


# ==================== ADMIN TESTS ====================

def test_create_subadmin(test_client):
    token = get_admin_token(test_client)
    res = test_client.post("/api/admin/users", json={
        "username": "subadmin1",
        "password": "SubPass123!",
        "permissions": {
            "view_websites": True,
            "manage_websites": False,
            "run_checks": True,
        },
    }, headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.json()
    assert data["username"] == "subadmin1"
    assert data["is_main_admin"] is False


def test_duplicate_username(test_client):
    token = get_admin_token(test_client)
    test_client.post("/api/admin/users", json={
        "username": "dup",
        "password": "DupPass123!",
    }, headers={"Authorization": f"Bearer {token}"})

    res = test_client.post("/api/admin/users", json={
        "username": "dup",
        "password": "DupPass123!",
    }, headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 400


def test_update_user_permissions(test_client):
    token = get_admin_token(test_client)
    res = test_client.post("/api/admin/users", json={
        "username": "editor",
        "password": "EditPass123!",
        "permissions": {"view_websites": True},
    }, headers={"Authorization": f"Bearer {token}"})
    user_id = res.json()["id"]

    res = test_client.put(f"/api/admin/users/{user_id}", json={
        "permissions": {
            "view_websites": True,
            "manage_websites": True,
            "run_checks": True,
        },
    }, headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert res.json()["permissions"]["manage_websites"] is True


def test_delete_subadmin(test_client):
    token = get_admin_token(test_client)
    res = test_client.post("/api/admin/users", json={
        "username": "todelete",
        "password": "DelPass123!",
    }, headers={"Authorization": f"Bearer {token}"})
    user_id = res.json()["id"]

    res = test_client.delete(f"/api/admin/users/{user_id}", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200


def test_cannot_delete_main_admin(test_client):
    token = get_admin_token(test_client)
    db = SessionLocal()
    admin = db.query(User).filter(User.username == "admin").first()
    admin_id = admin.id
    db.close()

    res = test_client.delete(f"/api/admin/users/{admin_id}", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 400


def test_list_permissions(test_client):
    token = get_admin_token(test_client)
    res = test_client.get("/api/admin/permissions", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.json()
    assert "view_websites" in data


def test_permission_enforcement(test_client):
    token = get_admin_token(test_client)
    res = test_client.post("/api/admin/users", json={
        "username": "readonly",
        "password": "ReadOnly123!",
        "permissions": {"view_websites": True},
    }, headers={"Authorization": f"Bearer {token}"})
    user_id = res.json()["id"]

    db = SessionLocal()
    user = db.query(User).filter(User.id == user_id).first()
    user.must_change_password = False
    secret = pyotp.random_base32()
    user.totp_secret = secret
    user.totp_enabled = True
    user.totp_verified = True
    db.commit()
    db.close()

    totp = pyotp.TOTP(secret)
    res = test_client.post("/api/auth/login", json={
        "username": "readonly",
        "password": "ReadOnly123!",
        "totp_code": totp.now(),
    })
    sub_token = res.json()["access_token"]

    res = test_client.post("/api/websites", json={
        "name": "Forbidden",
        "url": "https://forbidden.com",
    }, headers={"Authorization": f"Bearer {sub_token}"})
    assert res.status_code == 403


# ==================== MONITOR TESTS ====================

def test_suggestions_high_latency():
    s = generate_suggestions({"latency_ms": 1200, "ttfb_ms": 200, "page_load_time_ms": 500, "page_size_kb": 100})
    assert any(sg["type"] == "latency" for sg in s)


def test_suggestions_slow_ttfb():
    s = generate_suggestions({"latency_ms": 100, "ttfb_ms": 2000, "page_load_time_ms": 500, "page_size_kb": 100})
    assert any(sg["type"] == "ttfb" for sg in s)


def test_suggestions_large_page():
    s = generate_suggestions({"latency_ms": 100, "ttfb_ms": 200, "page_load_time_ms": 500, "page_size_kb": 6000})
    assert any(sg["type"] == "page_size" and sg["severity"] == "high" for sg in s)


def test_suggestions_good_performance():
    s = generate_suggestions({"latency_ms": 50, "ttfb_ms": 100, "page_load_time_ms": 800, "page_size_kb": 200})
    assert any(sg["type"] == "performance" for sg in s)


def test_suggestions_slow_page_load():
    s = generate_suggestions({"latency_ms": 100, "ttfb_ms": 200, "page_load_time_ms": 6000, "page_size_kb": 100})
    assert any(sg["type"] == "page_speed" for sg in s)


def test_url_validation(test_client):
    token = get_admin_token(test_client)
    res = test_client.post("/api/websites", json={
        "name": "Bad",
        "url": "not-a-url",
    }, headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 422


def test_unauthorized_access(test_client):
    res = test_client.get("/api/websites", headers={"Authorization": "Bearer invalid-token"})
    assert res.status_code == 401


def test_password_hash_utils():
    hashed = get_password_hash("test123")
    assert verify_password("test123", hashed)
    assert not verify_password("wrong", hashed)
