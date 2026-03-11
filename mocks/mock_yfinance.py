"""Mock yfinance module backed by golden test data."""
import json
import pandas as pd
from pathlib import Path
from datetime import datetime

GOLDEN_DIR = Path(__file__).parent.parent / "golden"

def _load_stocks():
    with open(GOLDEN_DIR / "stocks.json") as f:
        data = json.load(f)
    return {s["ticker"]: s for s in data}

def _load_snapshots(ticker):
    path = GOLDEN_DIR / "market_snapshots" / f"{ticker}.json"
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return []

_STOCKS = None
def _get_stocks():
    global _STOCKS
    if _STOCKS is None:
        _STOCKS = _load_stocks()
    return _STOCKS

class MockTicker:
    """Drop-in replacement for yfinance.Ticker."""
    def __init__(self, ticker):
        self.ticker = ticker.upper()
        stocks = _get_stocks()
        self._data = stocks.get(self.ticker)

    @property
    def info(self):
        if self._data is None:
            return {}
        return self._data.get("info", {})

    def history(self, period=None, start=None, end=None, interval="1d"):
        snapshots = _load_snapshots(self.ticker)
        if not snapshots:
            return pd.DataFrame(columns=["Open", "High", "Low", "Close", "Volume"])
        df = pd.DataFrame(snapshots)
        df["Date"] = pd.to_datetime(df["date"])
        df = df.set_index("Date")
        df = df.rename(columns={
            "open": "Open", "high": "High", "low": "Low",
            "close": "Close", "volume": "Volume", "adj_close": "Adj Close"
        })
        if start:
            df = df[df.index >= pd.to_datetime(start)]
        if end:
            df = df[df.index <= pd.to_datetime(end)]
        if period:
            period_map = {"1d": 1, "5d": 5, "1mo": 30, "3mo": 90, "6mo": 180, "1y": 365}
            days = period_map.get(period, 30)
            df = df.tail(days)
        return df

    @property
    def fast_info(self):
        info = self.info
        return {
            "lastPrice": info.get("currentPrice", 0),
            "marketCap": info.get("marketCap", 0),
        }


class MockDownload:
    """Drop-in for yfinance.download()."""
    def __call__(self, tickers, start=None, end=None, **kwargs):
        if isinstance(tickers, str):
            tickers = [tickers]
        frames = {}
        for t in tickers:
            ticker = MockTicker(t)
            df = ticker.history(start=start, end=end)
            frames[t] = df
        if len(frames) == 1:
            return list(frames.values())[0]
        return pd.concat(frames, axis=1)


# Module-level replacements
Ticker = MockTicker
download = MockDownload()
