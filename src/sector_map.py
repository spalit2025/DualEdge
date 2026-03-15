"""Sector-to-ETF mapping for relative strength analysis.

Maps yfinance sector names to their corresponding SPDR sector ETFs.
yfinance uses different naming conventions than the official GICS sectors,
so we include both variants.
"""

import yfinance as yf

SECTOR_ETF_MAP: dict[str, str] = {
    "Technology": "XLK",
    "Healthcare": "XLV",
    "Financial Services": "XLF",
    "Financials": "XLF",
    "Consumer Cyclical": "XLY",
    "Consumer Discretionary": "XLY",
    "Consumer Defensive": "XLP",
    "Consumer Staples": "XLP",
    "Industrials": "XLI",
    "Energy": "XLE",
    "Basic Materials": "XLB",
    "Materials": "XLB",
    "Utilities": "XLU",
    "Real Estate": "XLRE",
    "Communication Services": "XLC",
}


def get_sector_etf(ticker: str) -> str:
    """Look up a stock's sector from yfinance and map to sector ETF ticker.

    Args:
        ticker: US equity ticker symbol (e.g., 'AAPL').

    Returns:
        Sector ETF ticker (e.g., 'XLK'). Defaults to 'SPY' if sector
        is unavailable or not in the mapping.
    """
    try:
        info = yf.Ticker(ticker).info
        sector = info.get("sector", "")
        return SECTOR_ETF_MAP.get(sector, "SPY")
    except Exception as e:
        print(f"Warning: Could not determine sector for {ticker}: {e}")
        return "SPY"
