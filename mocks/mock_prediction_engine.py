"""Mock Prediction Engine HTTP responses."""
import json
from pathlib import Path

GOLDEN_DIR = Path(__file__).parent.parent / "golden"


def _load_predictions():
    with open(GOLDEN_DIR / "predictions.json") as f:
        return json.load(f)


def get_prediction_response(ticker: str, horizon: int = 7):
    """Return a mock prediction response matching the Prediction Engine API format."""
    predictions = _load_predictions()
    match = next(
        (p for p in predictions if p["ticker"] == ticker.upper() and p["horizon"] == horizon),
        None
    )
    if match is None:
        return {"error": f"No prediction available for {ticker} at horizon {horizon}"}, 404

    return {
        "ticker": match["ticker"],
        "horizon": match["horizon"],
        "prediction_date": match["prediction_date"],
        "predicted_return": match["predicted_return"],
        "direction": match["direction"],
        "confidence": match["confidence"],
        "models": match["models"],
    }, 200


def get_health_response():
    return {"status": "ok", "version": "1.0.0"}, 200


def get_backtest_response(ticker: str):
    """Return mock backtest results."""
    with open(GOLDEN_DIR / "backtest_results.json") as f:
        backtests = json.load(f)
    matches = [b for b in backtests if b["ticker"] == ticker.upper()]
    if not matches:
        return {"error": f"No backtest for {ticker}"}, 404
    return matches[0], 200
