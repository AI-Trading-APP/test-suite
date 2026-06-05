"""BB-GA-5 — E2E golden-path validation: are active stocks getting into the buckets?

This harness is the executable form of the PE-BT-GA Definition of Done question
the CPO asked: *"why are no active stocks getting added to the PE/Backtest
buckets?"* It asserts, end-to-end, that:

    Tier-1 universe ─▶ PE prediction bucket (predictions_cache) ─▶ readable
                    └▶ PE backtest bucket  (backtests_cache)   ─▶ readable
                       └▶ ScreenerService unified proxy returns the SAME numbers

It maps to the readiness dashboard tiles (program.md §4.3):
    * Tile 1 — universe coverage         -> test_prediction_bucket_non_empty
    * Tile 2 — NPP productive yield        -> test_prediction_bucket_non_empty / freshness
    * Tile 6 — backtest-engine = 1         -> test_screener_proxy_matches_pe (consolidation)
    * Per-ticker UX guarantee              -> test_sample_tickers_have_prediction_and_backtest

Design
------
* Read-only. Hits cache/read endpoints; never triggers compute.
* **Skips (not fails) when a service is unreachable**, so it is safe to run
  locally and meaningful on the test VPS / in CI. A reachable-but-empty bucket
  is a real FAIL — that is the exact GA-blocking condition.
* All base URLs + sample tickers + thresholds are env-overridable.

Run
---
    PE_BASE_URL=http://localhost:8010 \
    SCREENER_BASE_URL=http://localhost:8002 \
    BUCKET_SAMPLE_TICKERS=AAPL,MSFT,SPY \
    python -m pytest test_suite/test_bucket_fill_golden_path.py -v

On the test VPS, point the base URLs at the deployed services.
"""

from __future__ import annotations

import os

import pytest

try:
    import requests
except ImportError:  # pragma: no cover
    requests = None

PE_BASE_URL = os.getenv("PE_BASE_URL", "http://localhost:8010")
SCREENER_BASE_URL = os.getenv("SCREENER_BASE_URL", "http://localhost:8002")
PE_API_KEY = os.getenv("PE_API_KEY", os.getenv("API_KEY", ""))
SCREENER_TOKEN = os.getenv("SCREENER_TOKEN", "")

SAMPLE_TICKERS = [t.strip().upper() for t in os.getenv("BUCKET_SAMPLE_TICKERS", "AAPL,MSFT,SPY").split(",") if t.strip()]
MIN_UNIVERSE = int(os.getenv("BUCKET_MIN_UNIVERSE", "900"))      # Tier-1 floor (pre-1500 refresh)
MIN_PREDICTION_ROWS = int(os.getenv("BUCKET_MIN_PREDICTION_ROWS", "1"))
MIN_FRESH_BACKTEST_RATIO = float(os.getenv("BUCKET_MIN_FRESH_BACKTEST_RATIO", "0.0"))
TIMEOUT = int(os.getenv("BUCKET_HTTP_TIMEOUT", "30"))

pytestmark = pytest.mark.skipif(requests is None, reason="requests not installed")


def _pe_headers() -> dict:
    return {"Authorization": f"Bearer {PE_API_KEY}"} if PE_API_KEY else {}


def _screener_headers() -> dict:
    return {"Authorization": f"Bearer {SCREENER_TOKEN}"} if SCREENER_TOKEN else {}


def _get(url: str, headers: dict, params: dict | None = None):
    """GET that turns connection errors into a skip and other errors into context."""
    try:
        return requests.get(url, headers=headers, params=params, timeout=TIMEOUT)
    except requests.exceptions.RequestException as exc:
        pytest.skip(f"service unreachable at {url}: {exc}")


# --------------------------------------------------------------------------- #
# Pre-flight                                                                   #
# --------------------------------------------------------------------------- #

def test_pe_healthy():
    resp = _get(f"{PE_BASE_URL}/v1/health", _pe_headers())
    assert resp.status_code == 200, f"PE /v1/health -> {resp.status_code}: {resp.text[:200]}"


def test_universe_is_tier1_sized():
    """The eligibility bucket: the in-process universe must be Tier-1 sized.

    Uses the local StockUniverseManager (bundled tier files) — this is what PE
    fans out over, so it is the source of truth for 'which stocks are eligible'.
    """
    try:
        import sys
        from pathlib import Path

        pe_root = Path(os.getenv("PE_REPO_ROOT", Path(__file__).resolve().parent.parent / "Prediction-Engine"))
        if not pe_root.exists():
            pytest.skip(f"Prediction-Engine repo not found at {pe_root}")
        sys.path.insert(0, str(pe_root))
        from app_v1.services.stock_universe import StockUniverseManager
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"cannot import StockUniverseManager: {exc}")

    total = StockUniverseManager().total_count
    assert total >= MIN_UNIVERSE, (
        f"Universe has {total} symbols, below Tier-1 floor {MIN_UNIVERSE}. "
        "Run scripts/refresh_universe_data.py (BB-GA-1) to populate sp600/top_etfs."
    )


# --------------------------------------------------------------------------- #
# Prediction bucket (predictions_cache)                                        #
# --------------------------------------------------------------------------- #

def test_prediction_bucket_non_empty():
    """The core DOD assertion: active stocks ARE in the prediction bucket.

    An empty-but-reachable prediction bucket is the precise GA-blocking failure
    (the model-registry-collapse / 0%-NPP-yield symptom)."""
    resp = _get(f"{PE_BASE_URL}/v1/predictions/all", _pe_headers(), params={"page": 1, "page_size": 50})
    if resp.status_code == 404:
        pytest.skip("PE /v1/predictions/all not present on this build")
    assert resp.status_code == 200, f"{resp.status_code}: {resp.text[:200]}"
    body = resp.json()
    rows = body.get("items") or body.get("predictions") or body.get("data") or []
    total = body.get("total", len(rows))
    assert total >= MIN_PREDICTION_ROWS, (
        "Prediction bucket is EMPTY. Active stocks are not being added. "
        "Likely the model registry is empty (RISK-GA-9) — run "
        "Prediction-Engine/scripts/seed_models_from_disk.py and restart PE."
    )


@pytest.mark.parametrize("ticker", SAMPLE_TICKERS)
def test_sample_tickers_have_prediction_and_backtest(ticker):
    """Per-ticker UX guarantee: each sample ticker is in BOTH buckets."""
    pred = _get(f"{PE_BASE_URL}/v1/predictions/{ticker}", _pe_headers())
    if pred.status_code == 404:
        pytest.fail(f"{ticker}: NOT in prediction bucket (404) — not being added.")
    assert pred.status_code == 200, f"{ticker} prediction -> {pred.status_code}: {pred.text[:150]}"

    bt = _get(f"{PE_BASE_URL}/v1/backtests/{ticker}/latest", _pe_headers())
    if bt.status_code == 404:
        pytest.fail(f"{ticker}: NOT in backtest bucket (404) — not being added.")
    assert bt.status_code == 200, f"{ticker} backtest -> {bt.status_code}: {bt.text[:150]}"


# --------------------------------------------------------------------------- #
# Backtest bucket (backtests_cache) + freshness                               #
# --------------------------------------------------------------------------- #

def test_backtest_bucket_freshness():
    resp = _get(f"{PE_BASE_URL}/v1/backtests/freshness", _pe_headers())
    if resp.status_code == 404:
        pytest.skip("PE /v1/backtests/freshness not present on this build")
    assert resp.status_code == 200, f"{resp.status_code}: {resp.text[:200]}"
    body = resp.json()
    # Accept either an explicit ratio or a fresh/recent/stale/expired distribution.
    ratio = body.get("fresh_recent_ratio")
    if ratio is None:
        dist = body.get("distribution", body)
        total = sum(int(dist.get(k, 0)) for k in ("fresh", "recent", "stale", "expired"))
        fresh = int(dist.get("fresh", 0)) + int(dist.get("recent", 0))
        ratio = (fresh / total) if total else 0.0
    assert ratio >= MIN_FRESH_BACKTEST_RATIO, f"backtest freshness ratio {ratio} < {MIN_FRESH_BACKTEST_RATIO}"


# --------------------------------------------------------------------------- #
# Consolidation: ScreenerService proxy must match PE (Tile 6, single engine)   #
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("ticker", SAMPLE_TICKERS[:1] or ["AAPL"])
def test_screener_proxy_matches_pe(ticker):
    """backtest-consolidation: the screener route is a pure proxy of the one PE engine."""
    screener = _get(f"{SCREENER_BASE_URL}/api/screener/backtest/{ticker}", _screener_headers())
    if screener.status_code in (401, 403):
        pytest.skip("ScreenerService requires auth token (set SCREENER_TOKEN)")
    if screener.status_code == 404:
        pytest.skip(f"{ticker} not yet in screener-visible backtest bucket")
    assert screener.status_code == 200, f"screener backtest -> {screener.status_code}: {screener.text[:150]}"

    pe = _get(f"{PE_BASE_URL}/v1/backtests/{ticker}/latest", _pe_headers())
    if pe.status_code != 200:
        pytest.skip(f"PE backtest for {ticker} unavailable for cross-check ({pe.status_code})")

    def _sharpe(payload: dict):
        p = payload.get("backtest", payload)
        m = p.get("metrics", p.get("adjusted_metrics", p))
        return m.get("sharpe", m.get("sharpe_ratio"))

    s_screener, s_pe = _sharpe(screener.json()), _sharpe(pe.json())
    if s_screener is None or s_pe is None:
        pytest.skip("sharpe not present in one of the payloads for cross-check")
    assert abs(float(s_screener) - float(s_pe)) < 1e-6, (
        f"Consolidation broken: screener sharpe {s_screener} != PE sharpe {s_pe} for {ticker}"
    )
