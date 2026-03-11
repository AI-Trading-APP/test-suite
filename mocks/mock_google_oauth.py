"""Mock Google OAuth for authentication testing."""
import json
from pathlib import Path

GOLDEN_DIR = Path(__file__).parent.parent / "golden"


def _load_users():
    with open(GOLDEN_DIR / "users.json") as f:
        return json.load(f)


class MockIdToken:
    """Mock for google.oauth2.id_token."""

    @staticmethod
    def verify_oauth2_token(token: str, request, audience: str = None) -> dict:
        """Return golden user data based on token value."""
        users = _load_users()
        google_user = next((u for u in users if u.get("auth_provider") == "google"), users[0])
        return {
            "iss": "accounts.google.com",
            "sub": google_user.get("google_id", "google-sub-12345"),
            "email": google_user["email"],
            "email_verified": True,
            "name": google_user["name"],
            "picture": "https://lh3.googleusercontent.com/test-avatar",
            "aud": audience or "test-google-client-id",
        }


class MockGoogleRequest:
    """Mock for google.auth.transport.requests.Request."""
    def __init__(self):
        pass
    def __call__(self):
        return self
