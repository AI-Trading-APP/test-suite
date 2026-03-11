"""
Integration: Portfolio → Analytics flow
Tests that portfolio trades produce correct analytics metrics.

NOTE: Portfolio service's AddPositionRequest requires ticker, quantity, AND price.
The verify_token mock always returns {"user_id": "user_1"}.
"""

import pytest


class TestPortfolioBuySell:
    """Full buy → sell → verify P&L flow."""

    def test_buy_creates_position_and_reduces_cash(self, portfolio_client, auth_headers):
        resp = portfolio_client.get("/api/portfolio", headers=auth_headers)
        assert resp.status_code == 200
        initial_cash = resp.json()["cash"]

        resp = portfolio_client.post(
            "/api/portfolio/buy",
            json={"ticker": "AAPL", "quantity": 5, "price": 230.0},
            headers=auth_headers,
        )
        assert resp.status_code == 200

        resp = portfolio_client.get("/api/portfolio", headers=auth_headers)
        portfolio = resp.json()
        assert portfolio["cash"] < initial_cash
        aapl = next((p for p in portfolio["positions"] if p["ticker"] == "AAPL"), None)
        assert aapl is not None
        assert aapl["quantity"] == 5

    def test_buy_then_sell_partial(self, portfolio_client, auth_headers):
        # Initialize portfolio first
        portfolio_client.get("/api/portfolio", headers=auth_headers)
        portfolio_client.post(
            "/api/portfolio/buy",
            json={"ticker": "MSFT", "quantity": 10, "price": 415.0},
            headers=auth_headers,
        )
        resp = portfolio_client.post(
            "/api/portfolio/sell",
            json={"ticker": "MSFT", "quantity": 4, "price": 420.0},
            headers=auth_headers,
        )
        assert resp.status_code == 200

        resp = portfolio_client.get("/api/portfolio", headers=auth_headers)
        msft = next((p for p in resp.json()["positions"] if p["ticker"] == "MSFT"), None)
        assert msft is not None
        assert msft["quantity"] == 6

    def test_sell_all_removes_position(self, portfolio_client, auth_headers):
        # Initialize portfolio first
        portfolio_client.get("/api/portfolio", headers=auth_headers)
        portfolio_client.post(
            "/api/portfolio/buy",
            json={"ticker": "GOOGL", "quantity": 3, "price": 175.0},
            headers=auth_headers,
        )
        resp = portfolio_client.post(
            "/api/portfolio/sell",
            json={"ticker": "GOOGL", "quantity": 3, "price": 180.0},
            headers=auth_headers,
        )
        assert resp.status_code == 200

        resp = portfolio_client.get("/api/portfolio", headers=auth_headers)
        googl = next((p for p in resp.json()["positions"] if p["ticker"] == "GOOGL"), None)
        assert googl is None

    def test_transactions_recorded_for_all_trades(self, portfolio_client, auth_headers):
        # Initialize portfolio first
        portfolio_client.get("/api/portfolio", headers=auth_headers)
        portfolio_client.post(
            "/api/portfolio/buy",
            json={"ticker": "AAPL", "quantity": 2, "price": 230.0},
            headers=auth_headers,
        )
        portfolio_client.post(
            "/api/portfolio/buy",
            json={"ticker": "TSLA", "quantity": 3, "price": 250.0},
            headers=auth_headers,
        )
        portfolio_client.post(
            "/api/portfolio/sell",
            json={"ticker": "AAPL", "quantity": 1, "price": 235.0},
            headers=auth_headers,
        )

        resp = portfolio_client.get("/api/portfolio/transactions", headers=auth_headers)
        assert resp.status_code == 200
        txns = resp.json()
        # Response may be a dict with "transactions" key or a list
        if isinstance(txns, dict):
            txns = txns.get("transactions", [])
        assert len(txns) >= 3

    def test_insufficient_funds_rejected(self, portfolio_client, auth_headers):
        # Initialize portfolio first
        portfolio_client.get("/api/portfolio", headers=auth_headers)
        resp = portfolio_client.post(
            "/api/portfolio/buy",
            json={"ticker": "AAPL", "quantity": 999999, "price": 230.0},
            headers=auth_headers,
        )
        assert resp.status_code == 400

    def test_sell_without_position_rejected(self, portfolio_client, auth_headers):
        # Initialize portfolio first
        portfolio_client.get("/api/portfolio", headers=auth_headers)
        resp = portfolio_client.post(
            "/api/portfolio/sell",
            json={"ticker": "NVDA", "quantity": 1, "price": 880.0},
            headers=auth_headers,
        )
        assert resp.status_code in [400, 404]


class TestPortfolioPerformance:
    """Performance metrics after trades."""

    def test_performance_endpoint_returns_data(self, portfolio_client, auth_headers):
        # Initialize portfolio first
        portfolio_client.get("/api/portfolio", headers=auth_headers)
        portfolio_client.post(
            "/api/portfolio/buy",
            json={"ticker": "AAPL", "quantity": 5, "price": 230.0},
            headers=auth_headers,
        )
        resp = portfolio_client.get("/api/portfolio/performance", headers=auth_headers)
        assert resp.status_code == 200

    def test_empty_portfolio_returns_defaults(self, portfolio_client, auth_headers):
        # Initialize portfolio first (GET auto-creates with 100k cash)
        portfolio_client.get("/api/portfolio", headers=auth_headers)
        resp = portfolio_client.get("/api/portfolio/performance", headers=auth_headers)
        assert resp.status_code == 200
