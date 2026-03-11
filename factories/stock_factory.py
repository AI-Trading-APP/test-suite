"""Stock test data factory."""
import random
from datetime import datetime, timedelta


def create_stock_info(
    ticker: str = "TEST",
    short_name: str = "Test Corp",
    sector: str = "Technology",
    current_price: float = 150.00,
    market_cap: int = 1_000_000_000,
):
    """Create a realistic stock info dict."""
    return {
        "shortName": short_name,
        "symbol": ticker,
        "sector": sector,
        "industry": f"{sector} - General",
        "currentPrice": current_price,
        "previousClose": current_price * 0.998,
        "marketCap": market_cap,
        "trailingPE": round(random.uniform(10, 60), 1),
        "dividendYield": round(random.uniform(0, 0.04), 4),
        "beta": round(random.uniform(0.5, 2.0), 2),
        "fiftyTwoWeekHigh": round(current_price * 1.3, 2),
        "fiftyTwoWeekLow": round(current_price * 0.7, 2),
        "averageVolume": random.randint(1_000_000, 100_000_000),
        "regularMarketVolume": random.randint(500_000, 80_000_000),
        "profitMargins": round(random.uniform(0.05, 0.35), 3),
    }


def create_ohlcv_data(
    ticker: str = "TEST",
    days: int = 30,
    start_price: float = 150.00,
    volatility: float = 0.02,
    start_date: str = "2026-02-09",
):
    """Generate deterministic OHLCV data."""
    random.seed(hash(ticker))  # Deterministic per ticker
    data = []
    price = start_price
    current_date = datetime.strptime(start_date, "%Y-%m-%d")

    for i in range(days):
        daily_return = random.gauss(0.0005, volatility)
        price *= (1 + daily_return)

        open_price = round(price * (1 + random.gauss(0, 0.003)), 2)
        close_price = round(price, 2)
        high_price = round(max(open_price, close_price) * (1 + abs(random.gauss(0, 0.005))), 2)
        low_price = round(min(open_price, close_price) * (1 - abs(random.gauss(0, 0.005))), 2)
        volume = random.randint(20_000_000, 80_000_000)

        data.append({
            "date": current_date.strftime("%Y-%m-%d"),
            "open": open_price,
            "high": high_price,
            "low": low_price,
            "close": close_price,
            "volume": volume,
            "adj_close": close_price,
        })
        current_date += timedelta(days=1)
        # Skip weekends
        while current_date.weekday() >= 5:
            current_date += timedelta(days=1)

    return data
