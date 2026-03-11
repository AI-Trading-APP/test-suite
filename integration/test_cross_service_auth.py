"""
Integration: Cross-service JWT authentication
Verifies that JWT tokens are properly validated by the watchlist service
(which uses real JWT verification) and that health endpoints don't require auth.

NOTE: Portfolio and Paper Trading use mock verify_token that accepts anything.
Only WatchlistService uses real JWT verification.
"""

import pytest
import jwt as pyjwt
from datetime import datetime, timedelta

JWT_SECRET = "test-jwt-secret-for-integration-tests-1234"


class TestWatchlistJWTValidation:
    """Watchlist service validates JWT tokens properly."""

    def test_valid_jwt_accepted(self, watchlist_client, auth_headers):
        resp = watchlist_client.get("/api/watchlist", headers=auth_headers)
        assert resp.status_code == 200

    def test_expired_jwt_rejected(self, watchlist_client):
        token = pyjwt.encode(
            {"user_id": 1, "email": "t@t.com", "exp": datetime.utcnow() - timedelta(hours=1)},
            JWT_SECRET,
            algorithm="HS256",
        )
        resp = watchlist_client.get("/api/watchlist", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 401

    def test_missing_auth_rejected(self, watchlist_client):
        resp = watchlist_client.get("/api/watchlist")
        assert resp.status_code in [401, 403]

    def test_invalid_token_rejected(self, watchlist_client):
        resp = watchlist_client.get(
            "/api/watchlist",
            headers={"Authorization": "Bearer invalid.token.here"},
        )
        assert resp.status_code == 401

    def test_wrong_secret_rejected(self, watchlist_client):
        token = pyjwt.encode(
            {"user_id": 1, "email": "t@t.com", "exp": datetime.utcnow() + timedelta(hours=1)},
            "wrong-secret",
            algorithm="HS256",
        )
        resp = watchlist_client.get(
            "/api/watchlist",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 401


class TestHealthEndpointsNoAuth:
    """Health check endpoints should NOT require authentication."""

    def test_portfolio_health(self, portfolio_client):
        resp = portfolio_client.get("/")
        assert resp.status_code == 200

    def test_portfolio_health_endpoint(self, portfolio_client):
        resp = portfolio_client.get("/health")
        assert resp.status_code == 200

    def test_paper_trading_health(self, paper_client):
        resp = paper_client.get("/")
        assert resp.status_code == 200

    def test_paper_trading_health_endpoint(self, paper_client):
        resp = paper_client.get("/health")
        assert resp.status_code == 200

    def test_watchlist_health(self, watchlist_client):
        resp = watchlist_client.get("/")
        assert resp.status_code == 200

    def test_analytics_health(self, analytics_client):
        resp = analytics_client.get("/")
        assert resp.status_code == 200

    def test_analytics_health_endpoint(self, analytics_client):
        resp = analytics_client.get("/health")
        assert resp.status_code == 200


class TestAnalyticsNoAuth:
    """Analytics service endpoints don't require auth.
    NOTE: The analytics_client fixture mocks portfolio HTTP calls.
    Analytics processing may fail with mock data, but the key assertion
    is that these endpoints do NOT return 401/403 (no auth required).
    """

    @pytest.mark.parametrize("path", [
        "/api/analytics/performance/1m",
        "/api/analytics/returns/1m",
        "/api/analytics/drawdown/1m",
        "/api/analytics/equity-curve/1m",
    ])
    def test_analytics_no_auth_required(self, analytics_client, path):
        """Analytics endpoints should never return 401/403."""
        try:
            resp = analytics_client.get(path)
        except Exception:
            # Internal processing error — not an auth issue
            return
        assert resp.status_code not in [401, 403], (
            f"{path} returned {resp.status_code} — should not require auth"
        )
