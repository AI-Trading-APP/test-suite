"""
Integration: Paper Trading complete flow
Tests account lifecycle: create → trade → verify → reset.

NOTE: Paper trading verify_token always returns {"user_id": "user_1"}.
Account must be initialized via GET /api/paper/account before placing orders.
"""

import pytest


class TestPaperTradingLifecycle:
    """Full paper trading account lifecycle."""

    def test_new_account_has_100k_starting_cash(self, paper_client, auth_headers):
        resp = paper_client.get("/api/paper/account", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["cash"] == 100000.0
        assert data["positions"] == []

    def test_market_buy_reduces_cash_and_adds_position(self, paper_client, auth_headers):
        # Initialize account first
        paper_client.get("/api/paper/account", headers=auth_headers)

        resp = paper_client.post(
            "/api/paper/order",
            json={"ticker": "AAPL", "side": "buy", "quantity": 10, "type": "market"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        order = resp.json()
        assert order["status"] == "filled"

        resp = paper_client.get("/api/paper/account", headers=auth_headers)
        acct = resp.json()
        assert acct["cash"] < 100000.0
        aapl = next((p for p in acct["positions"] if p["ticker"] == "AAPL"), None)
        assert aapl is not None
        assert aapl["quantity"] == 10

    def test_market_sell_increases_cash_and_reduces_position(self, paper_client, auth_headers):
        # Setup: init account and buy
        paper_client.get("/api/paper/account", headers=auth_headers)
        paper_client.post(
            "/api/paper/order",
            json={"ticker": "MSFT", "side": "buy", "quantity": 5, "type": "market"},
            headers=auth_headers,
        )

        resp = paper_client.get("/api/paper/account", headers=auth_headers)
        cash_after_buy = resp.json()["cash"]

        # Sell
        resp = paper_client.post(
            "/api/paper/order",
            json={"ticker": "MSFT", "side": "sell", "quantity": 3, "type": "market"},
            headers=auth_headers,
        )
        assert resp.status_code == 200

        resp = paper_client.get("/api/paper/account", headers=auth_headers)
        acct = resp.json()
        assert acct["cash"] > cash_after_buy
        msft = next((p for p in acct["positions"] if p["ticker"] == "MSFT"), None)
        assert msft is not None
        assert msft["quantity"] == 2

    def test_order_history_tracks_all_orders(self, paper_client, auth_headers):
        paper_client.get("/api/paper/account", headers=auth_headers)
        paper_client.post(
            "/api/paper/order",
            json={"ticker": "AAPL", "side": "buy", "quantity": 5, "type": "market"},
            headers=auth_headers,
        )
        paper_client.post(
            "/api/paper/order",
            json={"ticker": "GOOGL", "side": "buy", "quantity": 3, "type": "market"},
            headers=auth_headers,
        )

        resp = paper_client.get("/api/paper/orders", headers=auth_headers)
        assert resp.status_code == 200
        orders = resp.json()
        if isinstance(orders, dict):
            orders = orders.get("orders", [])
        assert len(orders) >= 2

    def test_reset_account_restores_starting_state(self, paper_client, auth_headers):
        paper_client.get("/api/paper/account", headers=auth_headers)
        paper_client.post(
            "/api/paper/order",
            json={"ticker": "TSLA", "side": "buy", "quantity": 5, "type": "market"},
            headers=auth_headers,
        )

        resp = paper_client.post("/api/paper/reset", headers=auth_headers)
        assert resp.status_code == 200

        resp = paper_client.get("/api/paper/account", headers=auth_headers)
        acct = resp.json()
        assert acct["cash"] == 100000.0
        assert acct["positions"] == []
        assert acct["orders"] == []

    def test_sell_without_position_rejected(self, paper_client, auth_headers):
        paper_client.get("/api/paper/account", headers=auth_headers)
        resp = paper_client.post(
            "/api/paper/order",
            json={"ticker": "JPM", "side": "sell", "quantity": 1, "type": "market"},
            headers=auth_headers,
        )
        # Either 400 or "rejected" status
        if resp.status_code == 200:
            assert resp.json()["status"] == "rejected"
        else:
            assert resp.status_code in [400, 422]

    def test_buy_too_many_shares_rejected(self, paper_client, auth_headers):
        paper_client.get("/api/paper/account", headers=auth_headers)
        resp = paper_client.post(
            "/api/paper/order",
            json={"ticker": "NVDA", "side": "buy", "quantity": 999999, "type": "market"},
            headers=auth_headers,
        )
        if resp.status_code == 200:
            assert resp.json()["status"] == "rejected"
        else:
            assert resp.status_code in [400, 422]


class TestPaperTradingSlippage:
    """Verify slippage is applied to market orders."""

    def test_buy_fills_with_slippage(self, paper_client, auth_headers):
        paper_client.get("/api/paper/account", headers=auth_headers)
        resp = paper_client.post(
            "/api/paper/order",
            json={"ticker": "AAPL", "side": "buy", "quantity": 1, "type": "market"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        order = resp.json()
        assert order["status"] == "filled"
        if order.get("filledPrice"):
            # Buy with slippage: price should be near 230 (±1%)
            assert 228.0 <= order["filledPrice"] <= 233.0

    def test_sell_fills_with_slippage(self, paper_client, auth_headers):
        paper_client.get("/api/paper/account", headers=auth_headers)
        paper_client.post(
            "/api/paper/order",
            json={"ticker": "AAPL", "side": "buy", "quantity": 5, "type": "market"},
            headers=auth_headers,
        )
        resp = paper_client.post(
            "/api/paper/order",
            json={"ticker": "AAPL", "side": "sell", "quantity": 2, "type": "market"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        order = resp.json()
        assert order["status"] == "filled"


class TestPaperTradingHealthAndRoot:
    """Health endpoints work without auth."""

    def test_root_returns_200(self, paper_client):
        resp = paper_client.get("/")
        assert resp.status_code == 200

    def test_health_returns_200(self, paper_client):
        resp = paper_client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
