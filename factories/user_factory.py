"""User test data factory."""
import uuid
import jwt
from datetime import datetime, timezone, timedelta


def create_user(
    name: str = "Test User",
    email: str = None,
    password: str = "TestPass@123",
    auth_provider: str = "email",
    user_id: str = None,
):
    """Create a test user dict."""
    return {
        "id": user_id or str(uuid.uuid4()),
        "name": name,
        "email": email or f"test-{uuid.uuid4().hex[:8]}@test.ktrading.tech",
        "password": password,
        "auth_provider": auth_provider,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


def create_auth_headers(
    user_id: str = "user-pro-001",
    email: str = "pro@test.ktrading.tech",
    secret: str = "test-jwt-secret-key-for-testing",
    expires_hours: int = 24,
):
    """Create JWT Authorization headers for authenticated requests."""
    payload = {
        "user_id": user_id,
        "email": email,
        "exp": datetime.now(timezone.utc) + timedelta(hours=expires_hours),
        "iat": datetime.now(timezone.utc),
    }
    token = jwt.encode(payload, secret, algorithm="HS256")
    return {"Authorization": f"Bearer {token}"}


def create_expired_auth_headers(user_id: str = "user-pro-001", email: str = "pro@test.ktrading.tech", secret: str = "test-jwt-secret-key-for-testing"):
    """Create expired JWT headers for auth failure testing."""
    payload = {
        "user_id": user_id,
        "email": email,
        "exp": datetime.now(timezone.utc) - timedelta(hours=1),
        "iat": datetime.now(timezone.utc) - timedelta(hours=25),
    }
    token = jwt.encode(payload, secret, algorithm="HS256")
    return {"Authorization": f"Bearer {token}"}
