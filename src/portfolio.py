"""Portfolio-level calculations for DualEdge Watchlist Monitor.

Computes per-holding metrics (P&L, daily change, holding period),
portfolio aggregates (total value, daily change), concentration analysis
(position weights, sector weights), and correlation risk.

All functions handle edge cases gracefully — zero-share holdings are
skipped for P&L/concentration but still tracked for indicator purposes.
"""

from datetime import datetime

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Per-Holding Metrics
# ---------------------------------------------------------------------------

def compute_holding_metrics(holding: dict, current_price: float,
                           yesterday_close: float) -> dict:
    """Compute per-holding metrics: market value, P&L, daily change, holding period.

    Args:
        holding: Dict from watchlist.json with keys:
            ticker, shares, cost_basis_per_share, entry_date.
        current_price: Latest close price from OHLCV data.
        yesterday_close: Prior day close price.

    Returns:
        Dict with ticker, shares, market_value, cost_basis, pnl_dollar,
        pnl_pct, daily_change_dollar, daily_change_pct, holding_days.
        P&L fields are None for zero-share holdings.
    """
    ticker = holding["ticker"]
    shares = holding.get("shares", 0)
    cost_basis_per_share = holding.get("cost_basis_per_share", 0)
    entry_date_str = holding.get("entry_date", "")

    # Holding period
    holding_days = None
    if entry_date_str:
        try:
            entry_date = datetime.strptime(entry_date_str, "%Y-%m-%d")
            holding_days = (datetime.now() - entry_date).days
        except ValueError:
            pass

    # Zero-share holdings: skip P&L, return marker values
    if shares == 0 or cost_basis_per_share == 0:
        return {
            "ticker": ticker,
            "shares": 0,
            "market_value": 0.0,
            "cost_basis": 0.0,
            "pnl_dollar": None,
            "pnl_pct": None,
            "daily_change_dollar": None,
            "daily_change_pct": None,
            "holding_days": holding_days,
            "current_price": current_price,
            "yesterday_close": yesterday_close,
            "is_zero_position": True,
        }

    market_value = shares * current_price
    cost_basis = shares * cost_basis_per_share
    pnl_dollar = market_value - cost_basis
    pnl_pct = (pnl_dollar / cost_basis * 100) if cost_basis != 0 else None

    daily_change_dollar = shares * (current_price - yesterday_close)
    daily_change_pct = ((current_price - yesterday_close) / yesterday_close * 100
                        if yesterday_close != 0 else None)

    return {
        "ticker": ticker,
        "shares": shares,
        "market_value": round(market_value, 2),
        "cost_basis": round(cost_basis, 2),
        "pnl_dollar": round(pnl_dollar, 2),
        "pnl_pct": round(pnl_pct, 2) if pnl_pct is not None else None,
        "daily_change_dollar": round(daily_change_dollar, 2),
        "daily_change_pct": round(daily_change_pct, 2) if daily_change_pct is not None else None,
        "holding_days": holding_days,
        "current_price": current_price,
        "yesterday_close": yesterday_close,
        "is_zero_position": False,
    }


# ---------------------------------------------------------------------------
# Portfolio-Level Metrics
# ---------------------------------------------------------------------------

def compute_portfolio_metrics(holdings_metrics: list[dict],
                              cash_balance: float) -> dict:
    """Compute portfolio-level aggregates.

    Only includes non-zero-position holdings in the calculations.

    Args:
        holdings_metrics: List of per-holding metric dicts from compute_holding_metrics.
        cash_balance: Available cash from watchlist.json.

    Returns:
        Dict with total_value, total_invested, total_pnl_dollar, total_pnl_pct,
        cash_allocation_pct, daily_change_dollar, daily_change_pct.
    """
    # Filter to real positions only
    real_holdings = [h for h in holdings_metrics if not h.get("is_zero_position", False)]

    if not real_holdings:
        return {
            "total_value": cash_balance,
            "total_invested": 0.0,
            "total_pnl_dollar": 0.0,
            "total_pnl_pct": None,
            "cash_allocation_pct": 100.0,
            "daily_change_dollar": 0.0,
            "daily_change_pct": None,
            "has_positions": False,
        }

    total_market_value = sum(h["market_value"] for h in real_holdings)
    total_invested = sum(h["cost_basis"] for h in real_holdings)
    total_pnl_dollar = sum(h["pnl_dollar"] for h in real_holdings)
    total_pnl_pct = (total_pnl_dollar / total_invested * 100) if total_invested != 0 else None

    total_portfolio_value = total_market_value + cash_balance
    cash_allocation_pct = (cash_balance / total_portfolio_value * 100
                           if total_portfolio_value != 0 else None)

    daily_change_dollar = sum(h["daily_change_dollar"] for h in real_holdings)
    # Daily change %: change relative to yesterday's portfolio value
    yesterday_value = total_portfolio_value - daily_change_dollar
    daily_change_pct = (daily_change_dollar / yesterday_value * 100
                        if yesterday_value != 0 else None)

    return {
        "total_value": round(total_portfolio_value, 2),
        "total_invested": round(total_invested, 2),
        "total_pnl_dollar": round(total_pnl_dollar, 2),
        "total_pnl_pct": round(total_pnl_pct, 2) if total_pnl_pct is not None else None,
        "cash_allocation_pct": round(cash_allocation_pct, 2) if cash_allocation_pct is not None else None,
        "daily_change_dollar": round(daily_change_dollar, 2),
        "daily_change_pct": round(daily_change_pct, 2) if daily_change_pct is not None else None,
        "has_positions": True,
    }


# ---------------------------------------------------------------------------
# Concentration Analysis
# ---------------------------------------------------------------------------

def compute_concentration(holdings_metrics: list[dict],
                          total_portfolio_value: float,
                          sector_map: dict) -> dict:
    """Compute position weights, sector concentration, and top-3 weight.

    Only includes non-zero-position holdings.

    Args:
        holdings_metrics: List of per-holding metric dicts.
        total_portfolio_value: From compute_portfolio_metrics.
        sector_map: Dict of ticker -> sector string (looked up from yfinance).

    Returns:
        Dict with position_weights, sector_weights, largest_position,
        top_3_weight, concentration_flags (list of warning strings).
    """
    real_holdings = [h for h in holdings_metrics if not h.get("is_zero_position", False)]

    if not real_holdings or total_portfolio_value <= 0:
        return {
            "position_weights": {},
            "sector_weights": {},
            "largest_position": None,
            "top_3_weight": 0.0,
            "concentration_flags": [],
        }

    # Position weights
    position_weights = {}
    for h in real_holdings:
        weight = h["market_value"] / total_portfolio_value * 100
        position_weights[h["ticker"]] = round(weight, 2)

    # Sector weights
    sector_weights = {}
    for h in real_holdings:
        ticker = h["ticker"]
        sector = sector_map.get(ticker, "Unknown")
        weight = position_weights.get(ticker, 0)
        sector_weights[sector] = sector_weights.get(sector, 0) + weight
    sector_weights = {k: round(v, 2) for k, v in sector_weights.items()}

    # Largest position
    sorted_weights = sorted(position_weights.items(), key=lambda x: x[1], reverse=True)
    largest_position = {"ticker": sorted_weights[0][0], "weight": sorted_weights[0][1]}

    # Top 3 weight
    top_3_weight = sum(w for _, w in sorted_weights[:3])

    # Concentration flags
    flags = []
    for ticker, weight in position_weights.items():
        if weight > 25:
            flags.append(f"CONCENTRATION: {ticker} is {weight}% of portfolio (>25%)")

    for sector, weight in sector_weights.items():
        if weight > 40:
            flags.append(f"SECTOR CONCENTRATION: {sector} is {weight}% of portfolio (>40%)")

    if top_3_weight > 60:
        flags.append(f"TOP-HEAVY: Top 3 positions = {round(top_3_weight, 1)}% of portfolio (>60%)")

    return {
        "position_weights": position_weights,
        "sector_weights": sector_weights,
        "largest_position": largest_position,
        "top_3_weight": round(top_3_weight, 2),
        "concentration_flags": flags,
    }


# ---------------------------------------------------------------------------
# Correlation Matrix
# ---------------------------------------------------------------------------

def compute_correlation_matrix(tickers: list[str],
                               daily_data: dict[str, pd.DataFrame]) -> dict:
    """Compute pairwise Pearson correlation of 6-month daily returns.

    Only computed if < 15 holdings. Flags pairs with r > 0.85.

    Args:
        tickers: List of holding tickers (non-zero positions only).
        daily_data: Dict of ticker -> daily OHLCV DataFrame (already pulled).

    Returns:
        Dict with correlation_matrix (nested dict), high_correlation_pairs
        (list of dicts with ticker_a, ticker_b, correlation).
        Returns empty results if > 14 tickers or insufficient data.
    """
    if len(tickers) > 14 or len(tickers) < 2:
        return {
            "correlation_matrix": {},
            "high_correlation_pairs": [],
            "skipped": len(tickers) > 14,
        }

    # Build returns DataFrame: last 126 trading days (~6 months)
    returns_dict = {}
    for ticker in tickers:
        df = daily_data.get(ticker)
        if df is None or len(df) < 30:
            continue
        close = df["Close"].iloc[-126:] if len(df) >= 126 else df["Close"]
        daily_returns = close.pct_change().dropna()
        returns_dict[ticker] = daily_returns

    if len(returns_dict) < 2:
        return {
            "correlation_matrix": {},
            "high_correlation_pairs": [],
            "skipped": False,
        }

    # Align on common dates
    returns_df = pd.DataFrame(returns_dict)
    returns_df = returns_df.dropna()

    if len(returns_df) < 20:
        return {
            "correlation_matrix": {},
            "high_correlation_pairs": [],
            "skipped": False,
        }

    corr_matrix = returns_df.corr()

    # Convert to nested dict for JSON serialization
    corr_dict = {}
    for t in corr_matrix.columns:
        corr_dict[t] = {t2: round(float(corr_matrix.loc[t, t2]), 4)
                        for t2 in corr_matrix.columns}

    # Find high correlation pairs
    high_pairs = []
    tickers_in_matrix = list(corr_matrix.columns)
    for i in range(len(tickers_in_matrix)):
        for j in range(i + 1, len(tickers_in_matrix)):
            r = float(corr_matrix.iloc[i, j])
            if r > 0.85:
                high_pairs.append({
                    "ticker_a": tickers_in_matrix[i],
                    "ticker_b": tickers_in_matrix[j],
                    "correlation": round(r, 4),
                })

    return {
        "correlation_matrix": corr_dict,
        "high_correlation_pairs": high_pairs,
        "skipped": False,
    }
