"""Unit tests for src.portfolio — portfolio-level calculations.

All tests use synthetic holdings dicts and DataFrames with known,
hand-calculable values. No API calls or external data sources.
"""

import numpy as np
import pandas as pd
import pytest

from src.portfolio import (
    compute_concentration,
    compute_correlation_matrix,
    compute_holding_metrics,
    compute_portfolio_metrics,
)


# ---------------------------------------------------------------------------
# Helper: synthetic data builders
# ---------------------------------------------------------------------------

def make_holding(ticker: str, shares: int, cost_basis: float,
                 entry_date: str = "2025-06-01") -> dict:
    """Build a holding dict matching watchlist.json format."""
    return {
        "ticker": ticker,
        "shares": shares,
        "cost_basis_per_share": cost_basis,
        "entry_date": entry_date,
    }


def make_holding_metrics(ticker: str, market_value: float, cost_basis: float,
                         pnl_dollar: float, pnl_pct: float,
                         daily_change_dollar: float, daily_change_pct: float,
                         shares: int = 10, is_zero: bool = False) -> dict:
    """Build a holding metrics dict as returned by compute_holding_metrics."""
    return {
        "ticker": ticker,
        "shares": shares,
        "market_value": market_value,
        "cost_basis": cost_basis,
        "pnl_dollar": pnl_dollar,
        "pnl_pct": pnl_pct,
        "daily_change_dollar": daily_change_dollar,
        "daily_change_pct": daily_change_pct,
        "holding_days": 100,
        "current_price": market_value / shares if shares > 0 else 0,
        "yesterday_close": (market_value - daily_change_dollar) / shares if shares > 0 else 0,
        "is_zero_position": is_zero,
    }


def make_daily_df_for_corr(prices: list[float]) -> pd.DataFrame:
    """Build a minimal daily OHLCV DataFrame for correlation tests."""
    n = len(prices)
    dates = pd.bdate_range(end="2026-03-13", periods=n)
    return pd.DataFrame({
        "Open": prices,
        "High": [p + 1.0 for p in prices],
        "Low": [p - 1.0 for p in prices],
        "Close": prices,
        "Volume": [1_000_000] * n,
    }, index=dates)


# ---------------------------------------------------------------------------
# Tests: compute_holding_metrics
# ---------------------------------------------------------------------------

class TestComputeHoldingMetrics:
    def test_basic_pnl_math(self):
        """Bought 10 shares at $100, now at $150 = $500 profit, 50% gain."""
        holding = make_holding("AAPL", shares=10, cost_basis=100.0)
        result = compute_holding_metrics(holding, current_price=150.0,
                                          yesterday_close=148.0)

        assert result["market_value"] == 1500.0
        assert result["cost_basis"] == 1000.0
        assert result["pnl_dollar"] == 500.0
        assert result["pnl_pct"] == 50.0
        assert result["is_zero_position"] is False

    def test_daily_change(self):
        """Daily change: 10 shares * ($150 - $148) = $20."""
        holding = make_holding("AAPL", shares=10, cost_basis=100.0)
        result = compute_holding_metrics(holding, current_price=150.0,
                                          yesterday_close=148.0)

        assert result["daily_change_dollar"] == 20.0
        # (150 - 148) / 148 * 100 = 1.35%
        expected_daily_pct = round((150.0 - 148.0) / 148.0 * 100, 2)
        assert result["daily_change_pct"] == expected_daily_pct

    def test_loss_scenario(self):
        """Bought 5 shares at $200, now at $180 = -$100 loss, -10%."""
        holding = make_holding("TSLA", shares=5, cost_basis=200.0)
        result = compute_holding_metrics(holding, current_price=180.0,
                                          yesterday_close=182.0)

        assert result["pnl_dollar"] == -100.0
        assert result["pnl_pct"] == -10.0

    def test_zero_share_handling(self):
        """Zero-share holdings should return None for P&L fields."""
        holding = make_holding("MSFT", shares=0, cost_basis=300.0)
        result = compute_holding_metrics(holding, current_price=350.0,
                                          yesterday_close=348.0)

        assert result["is_zero_position"] is True
        assert result["pnl_dollar"] is None
        assert result["pnl_pct"] is None
        assert result["daily_change_dollar"] is None
        assert result["market_value"] == 0.0


# ---------------------------------------------------------------------------
# Tests: compute_portfolio_metrics
# ---------------------------------------------------------------------------

class TestComputePortfolioMetrics:
    def test_total_value_equals_holdings_plus_cash(self):
        """Total portfolio value = sum(market_values) + cash."""
        h1 = make_holding_metrics("AAPL", market_value=5000, cost_basis=4000,
                                   pnl_dollar=1000, pnl_pct=25.0,
                                   daily_change_dollar=50, daily_change_pct=1.0)
        h2 = make_holding_metrics("GOOG", market_value=3000, cost_basis=2500,
                                   pnl_dollar=500, pnl_pct=20.0,
                                   daily_change_dollar=30, daily_change_pct=1.0)
        cash = 2000.0
        result = compute_portfolio_metrics([h1, h2], cash)

        assert result["total_value"] == 10000.0  # 5000 + 3000 + 2000
        assert result["total_invested"] == 6500.0  # 4000 + 2500
        assert result["total_pnl_dollar"] == 1500.0  # 1000 + 500
        assert result["has_positions"] is True

    def test_pnl_percentages(self):
        """Total P&L % = total_pnl / total_invested * 100."""
        h1 = make_holding_metrics("AAPL", market_value=6000, cost_basis=5000,
                                   pnl_dollar=1000, pnl_pct=20.0,
                                   daily_change_dollar=100, daily_change_pct=1.7)
        result = compute_portfolio_metrics([h1], cash_balance=0.0)

        # P&L % = 1000 / 5000 * 100 = 20%
        assert result["total_pnl_pct"] == 20.0

    def test_zero_position_exclusion(self):
        """Zero-position holdings should not affect aggregates."""
        real = make_holding_metrics("AAPL", market_value=5000, cost_basis=4000,
                                     pnl_dollar=1000, pnl_pct=25.0,
                                     daily_change_dollar=50, daily_change_pct=1.0)
        zero = make_holding_metrics("MSFT", market_value=0, cost_basis=0,
                                     pnl_dollar=None, pnl_pct=None,
                                     daily_change_dollar=None, daily_change_pct=None,
                                     shares=0, is_zero=True)
        result = compute_portfolio_metrics([real, zero], cash_balance=1000.0)

        assert result["total_value"] == 6000.0  # 5000 + 1000 cash
        assert result["total_invested"] == 4000.0

    def test_no_positions_returns_cash_only(self):
        """With no real holdings, total value should equal cash."""
        result = compute_portfolio_metrics([], cash_balance=5000.0)
        assert result["total_value"] == 5000.0
        assert result["cash_allocation_pct"] == 100.0
        assert result["has_positions"] is False


# ---------------------------------------------------------------------------
# Tests: compute_concentration
# ---------------------------------------------------------------------------

class TestComputeConcentration:
    def test_single_stock_over_25_pct_flag(self):
        """A single stock > 25% of portfolio should trigger a flag."""
        # AAPL is 3000 / 10000 = 30%
        h1 = make_holding_metrics("AAPL", market_value=3000, cost_basis=2500,
                                   pnl_dollar=500, pnl_pct=20.0,
                                   daily_change_dollar=30, daily_change_pct=1.0)
        h2 = make_holding_metrics("GOOG", market_value=2000, cost_basis=1800,
                                   pnl_dollar=200, pnl_pct=11.1,
                                   daily_change_dollar=20, daily_change_pct=1.0)
        h3 = make_holding_metrics("MSFT", market_value=2000, cost_basis=1900,
                                   pnl_dollar=100, pnl_pct=5.3,
                                   daily_change_dollar=10, daily_change_pct=0.5)
        sector_map = {"AAPL": "Technology", "GOOG": "Technology", "MSFT": "Technology"}
        result = compute_concentration([h1, h2, h3], total_portfolio_value=10000.0,
                                        sector_map=sector_map)

        assert result["position_weights"]["AAPL"] == 30.0
        concentration_flags = result["concentration_flags"]
        assert any("AAPL" in f and ">25%" in f for f in concentration_flags), (
            f"Expected AAPL concentration flag, got: {concentration_flags}"
        )

    def test_sector_over_40_pct_flag(self):
        """A sector > 40% of portfolio should trigger a sector flag."""
        h1 = make_holding_metrics("AAPL", market_value=3000, cost_basis=2500,
                                   pnl_dollar=500, pnl_pct=20.0,
                                   daily_change_dollar=30, daily_change_pct=1.0)
        h2 = make_holding_metrics("MSFT", market_value=2500, cost_basis=2000,
                                   pnl_dollar=500, pnl_pct=25.0,
                                   daily_change_dollar=25, daily_change_pct=1.0)
        h3 = make_holding_metrics("XOM", market_value=1500, cost_basis=1400,
                                   pnl_dollar=100, pnl_pct=7.1,
                                   daily_change_dollar=10, daily_change_pct=0.7)
        sector_map = {"AAPL": "Technology", "MSFT": "Technology", "XOM": "Energy"}
        # Tech = 3000+2500 = 5500 / 10000 = 55%
        result = compute_concentration([h1, h2, h3], total_portfolio_value=10000.0,
                                        sector_map=sector_map)

        assert any("SECTOR CONCENTRATION" in f and ">40%" in f
                    for f in result["concentration_flags"]), (
            f"Expected sector concentration flag, got: {result['concentration_flags']}"
        )

    def test_top3_over_60_pct_flag(self):
        """Top-3 positions > 60% of portfolio should trigger a flag."""
        h1 = make_holding_metrics("A", market_value=2500, cost_basis=2000,
                                   pnl_dollar=500, pnl_pct=25.0,
                                   daily_change_dollar=25, daily_change_pct=1.0)
        h2 = make_holding_metrics("B", market_value=2500, cost_basis=2000,
                                   pnl_dollar=500, pnl_pct=25.0,
                                   daily_change_dollar=25, daily_change_pct=1.0)
        h3 = make_holding_metrics("C", market_value=2500, cost_basis=2000,
                                   pnl_dollar=500, pnl_pct=25.0,
                                   daily_change_dollar=25, daily_change_pct=1.0)
        h4 = make_holding_metrics("D", market_value=2500, cost_basis=2000,
                                   pnl_dollar=500, pnl_pct=25.0,
                                   daily_change_dollar=25, daily_change_pct=1.0)
        sector_map = {"A": "S1", "B": "S2", "C": "S3", "D": "S4"}
        # top-3 = 75%
        result = compute_concentration([h1, h2, h3, h4],
                                        total_portfolio_value=10000.0,
                                        sector_map=sector_map)

        assert any("TOP-HEAVY" in f and ">60%" in f
                    for f in result["concentration_flags"]), (
            f"Expected top-heavy flag, got: {result['concentration_flags']}"
        )

    def test_no_flags_when_diversified(self):
        """No concentration flags when portfolio is well-diversified."""
        holdings = [
            make_holding_metrics(f"T{i}", market_value=1000, cost_basis=900,
                                  pnl_dollar=100, pnl_pct=11.1,
                                  daily_change_dollar=5, daily_change_pct=0.5)
            for i in range(10)
        ]
        sector_map = {f"T{i}": f"Sector{i}" for i in range(10)}
        # Each position = 1000 / 15000 = 6.67%, each sector = 6.67%, top-3 = 20%
        result = compute_concentration(holdings, total_portfolio_value=15000.0,
                                        sector_map=sector_map)

        assert result["concentration_flags"] == [], (
            f"Expected no flags, got: {result['concentration_flags']}"
        )


# ---------------------------------------------------------------------------
# Tests: compute_correlation_matrix
# ---------------------------------------------------------------------------

class TestComputeCorrelationMatrix:
    def test_perfectly_correlated_returns(self):
        """Identical return series should produce r = 1.0."""
        np.random.seed(0)
        base_prices = np.cumsum(np.random.randn(130)) + 200
        base_prices = np.maximum(base_prices, 10)  # keep positive
        # Two tickers with identical price series
        df_a = make_daily_df_for_corr(base_prices.tolist())
        df_b = make_daily_df_for_corr(base_prices.tolist())
        result = compute_correlation_matrix(
            ["A", "B"], {"A": df_a, "B": df_b}
        )
        assert result["correlation_matrix"]["A"]["B"] == 1.0
        assert len(result["high_correlation_pairs"]) >= 1

    def test_high_correlation_pairs_flagged(self):
        """Pairs with r > 0.85 should appear in high_correlation_pairs."""
        np.random.seed(1)
        base = np.cumsum(np.random.randn(130)) + 200
        base = np.maximum(base, 10)
        # Small noise so correlation is high but not exactly 1
        noise = np.random.randn(130) * 0.3
        prices_a = base.tolist()
        prices_b = (base + noise).tolist()
        df_a = make_daily_df_for_corr(prices_a)
        df_b = make_daily_df_for_corr(prices_b)
        result = compute_correlation_matrix(
            ["X", "Y"], {"X": df_a, "Y": df_b}
        )
        # Should be flagged as highly correlated
        pairs = result["high_correlation_pairs"]
        assert len(pairs) >= 1
        assert pairs[0]["correlation"] > 0.85

    def test_fewer_than_two_tickers(self):
        """With < 2 tickers, should return empty results gracefully."""
        result = compute_correlation_matrix(
            ["SOLO"], {"SOLO": make_daily_df_for_corr([100] * 130)}
        )
        assert result["correlation_matrix"] == {}
        assert result["high_correlation_pairs"] == []

    def test_too_many_tickers_skipped(self):
        """With > 14 tickers, computation should be skipped."""
        tickers = [f"T{i}" for i in range(15)]
        data = {t: make_daily_df_for_corr([100 + i] * 130)
                for i, t in enumerate(tickers)}
        result = compute_correlation_matrix(tickers, data)
        assert result["skipped"] is True
        assert result["correlation_matrix"] == {}
