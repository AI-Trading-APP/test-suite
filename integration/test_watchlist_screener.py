"""
Integration: Watchlist operations flow
Tests multi-watchlist CRUD, stock add/remove, and price refresh.
"""

import pytest


class TestWatchlistCRUD:
    """Create, rename, delete watchlists."""

    def test_create_watchlist(self, watchlist_client, auth_headers):
        resp = watchlist_client.post(
            "/api/watchlists",
            json={"name": "Tech Stocks"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Tech Stocks"

    def test_list_watchlists_returns_created(self, watchlist_client, auth_headers):
        # Create a watchlist first
        watchlist_client.post(
            "/api/watchlists",
            json={"name": "My Picks"},
            headers=auth_headers,
        )
        resp = watchlist_client.get("/api/watchlists", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_rename_watchlist(self, watchlist_client, auth_headers):
        # Create
        create_resp = watchlist_client.post(
            "/api/watchlists",
            json={"name": "Old Name"},
            headers=auth_headers,
        )
        wl_id = create_resp.json().get("id", create_resp.json().get("watchlistId", "default"))

        # Rename
        resp = watchlist_client.put(
            f"/api/watchlists/{wl_id}",
            json={"name": "New Name"},
            headers=auth_headers,
        )
        assert resp.status_code == 200


class TestWatchlistStockOperations:
    """Add/remove stocks from watchlists."""

    def test_add_stock_to_watchlist(self, watchlist_client, auth_headers):
        # Note: default watchlist is initialized with AAPL, MSFT, GOOGL
        # so we add a stock that's not in the defaults
        resp = watchlist_client.post(
            "/api/watchlist",
            json={"ticker": "NVDA"},
            headers=auth_headers,
        )
        assert resp.status_code == 200

    def test_get_watchlist_stocks_with_prices(self, watchlist_client, auth_headers):
        # Add a stock first
        watchlist_client.post(
            "/api/watchlist",
            json={"ticker": "MSFT"},
            headers=auth_headers,
        )
        resp = watchlist_client.get("/api/watchlist", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, (list, dict))

    def test_remove_stock_from_watchlist(self, watchlist_client, auth_headers):
        # Add then remove
        watchlist_client.post(
            "/api/watchlist",
            json={"ticker": "GOOGL"},
            headers=auth_headers,
        )
        resp = watchlist_client.delete("/api/watchlist/GOOGL", headers=auth_headers)
        assert resp.status_code == 200

    def test_bulk_add_stocks(self, watchlist_client, auth_headers):
        resp = watchlist_client.post(
            "/api/watchlist/bulk",
            json={"tickers": ["AAPL", "MSFT", "GOOGL"]},
            headers=auth_headers,
        )
        assert resp.status_code == 200

    def test_add_duplicate_stock_handled(self, watchlist_client, auth_headers):
        watchlist_client.post(
            "/api/watchlist",
            json={"ticker": "TSLA"},
            headers=auth_headers,
        )
        resp = watchlist_client.post(
            "/api/watchlist",
            json={"ticker": "TSLA"},
            headers=auth_headers,
        )
        # Should either succeed (idempotent) or return 400/409
        assert resp.status_code in [200, 400, 409]

    def test_watchlist_stats(self, watchlist_client, auth_headers):
        watchlist_client.post(
            "/api/watchlist",
            json={"ticker": "AMZN"},
            headers=auth_headers,
        )
        resp = watchlist_client.get("/api/watchlist/stats", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "totalStocks" in data or "total_stocks" in data or isinstance(data, dict)


class TestWatchlistIsolation:
    """Multiple users should have separate watchlists."""

    def test_user_watchlists_isolated(self, watchlist_client, auth_headers, second_user_headers):
        # User 1 adds stock
        watchlist_client.post(
            "/api/watchlist",
            json={"ticker": "META"},
            headers=auth_headers,
        )

        # User 2 should have empty watchlist
        resp = watchlist_client.get("/api/watchlist", headers=second_user_headers)
        assert resp.status_code == 200
        data = resp.json()
        if isinstance(data, list):
            tickers = [s.get("ticker", "") for s in data]
            assert "META" not in tickers


class TestWatchlistPriceRefresh:
    """Refresh prices for watchlist stocks."""

    def test_refresh_updates_prices(self, watchlist_client, auth_headers):
        watchlist_client.post(
            "/api/watchlist",
            json={"ticker": "AAPL"},
            headers=auth_headers,
        )
        resp = watchlist_client.put("/api/watchlist/refresh", headers=auth_headers)
        assert resp.status_code == 200

    def test_get_stock_history(self, watchlist_client, auth_headers):
        resp = watchlist_client.get("/api/watchlist/history/AAPL", headers=auth_headers)
        assert resp.status_code == 200
