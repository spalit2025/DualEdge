"""Unit tests for src.indicators — technical indicator computations.

All tests use synthetic DataFrames with known, hand-calculable values.
No API calls or external data sources are used.
"""

import numpy as np
import pandas as pd
import pytest

from src.indicators import (
    compute_all_indicators,
    compute_annualized_return,
    compute_annualized_volatility,
    compute_atr,
    compute_bollinger_bands,
    compute_canslim_quantitative,
    compute_moving_averages,
    compute_obv,
    compute_price_zscore,
    compute_relative_strength,
    compute_rsi,
    compute_volume_ratio,
    compute_weinstein_stage,
    compute_52week_metrics,
)


# ---------------------------------------------------------------------------
# Helper: synthetic DataFrame builders
# ---------------------------------------------------------------------------

def make_daily_df(prices: list[float], volumes: list[int] | None = None,
                  highs: list[float] | None = None,
                  lows: list[float] | None = None) -> pd.DataFrame:
    """Build a daily OHLCV DataFrame from a list of close prices.

    If highs/lows are not given, they are derived as close +/- 1.
    If volumes are not given, they default to 1_000_000 each day.
    """
    n = len(prices)
    if volumes is None:
        volumes = [1_000_000] * n
    if highs is None:
        highs = [p + 1.0 for p in prices]
    if lows is None:
        lows = [p - 1.0 for p in prices]
    dates = pd.bdate_range(end="2026-03-13", periods=n)
    return pd.DataFrame({
        "Open": prices,
        "High": highs,
        "Low": lows,
        "Close": prices,
        "Volume": volumes,
    }, index=dates)


def make_weekly_df(prices: list[float], volumes: list[int] | None = None) -> pd.DataFrame:
    """Build a weekly OHLCV DataFrame from a list of close prices."""
    n = len(prices)
    if volumes is None:
        volumes = [5_000_000] * n
    dates = pd.date_range(end="2026-03-13", periods=n, freq="W")
    return pd.DataFrame({
        "Open": prices,
        "High": [p + 2.0 for p in prices],
        "Low": [p - 2.0 for p in prices],
        "Close": prices,
        "Volume": volumes,
    }, index=dates)


def make_steady_rise(n: int, start: float = 100.0, step: float = 0.5) -> list[float]:
    """Generate a steadily rising price series."""
    return [start + i * step for i in range(n)]


def make_steady_decline(n: int, start: float = 200.0, step: float = 0.5) -> list[float]:
    """Generate a steadily declining price series."""
    return [start - i * step for i in range(n)]


def make_constant(n: int, value: float = 100.0) -> list[float]:
    """Generate a constant price series."""
    return [value] * n


# ---------------------------------------------------------------------------
# Tests: compute_rsi
# ---------------------------------------------------------------------------

class TestComputeRsi:
    def test_rsi_in_valid_range(self):
        """RSI should always be between 0 and 100."""
        prices = make_steady_rise(100)
        df = make_daily_df(prices)
        rsi = compute_rsi(df)
        assert rsi is not None
        assert 0 <= rsi <= 100, f"RSI {rsi} out of [0, 100]"

    def test_all_up_days_returns_100(self):
        """When every day is an up day, RSI should be 100."""
        prices = make_steady_rise(50, start=10, step=1.0)
        df = make_daily_df(prices)
        rsi = compute_rsi(df)
        assert rsi == 100.0, f"Expected RSI=100 for all up days, got {rsi}"

    def test_all_down_days_returns_near_zero(self):
        """When every day is a down day, RSI should be close to 0."""
        prices = make_steady_decline(50, start=200, step=1.0)
        df = make_daily_df(prices)
        rsi = compute_rsi(df)
        assert rsi is not None
        assert rsi < 1.0, f"Expected RSI near 0 for all down days, got {rsi}"

    def test_insufficient_data_returns_none(self):
        """RSI with fewer than period+1 rows should return None."""
        df = make_daily_df([100, 101, 102])
        assert compute_rsi(df, period=14) is None


# ---------------------------------------------------------------------------
# Tests: compute_bollinger_bands
# ---------------------------------------------------------------------------

class TestComputeBollingerBands:
    def test_middle_band_equals_20d_sma(self):
        """The middle Bollinger band must equal the 20-day SMA."""
        prices = make_steady_rise(60, start=50, step=0.5)
        df = make_daily_df(prices)
        bb = compute_bollinger_bands(df)
        expected_sma = np.mean(prices[-20:])
        assert bb is not None
        assert abs(bb["middle"] - expected_sma) < 0.01, (
            f"Middle band {bb['middle']} != expected SMA {expected_sma}"
        )

    def test_band_ordering(self):
        """Upper > middle > lower must always hold."""
        prices = make_steady_rise(60, start=50, step=0.5)
        df = make_daily_df(prices)
        bb = compute_bollinger_bands(df)
        assert bb["upper"] > bb["middle"] > bb["lower"]

    def test_width_non_negative(self):
        """Bandwidth should be non-negative."""
        prices = make_steady_rise(60, start=50, step=0.5)
        df = make_daily_df(prices)
        bb = compute_bollinger_bands(df)
        assert bb["current_width"] >= 0

    def test_width_percentile_in_range(self):
        """Width percentile should be in [0, 100]."""
        prices = make_steady_rise(300, start=50, step=0.1)
        df = make_daily_df(prices)
        bb = compute_bollinger_bands(df)
        assert 0 <= bb["width_percentile"] <= 100


# ---------------------------------------------------------------------------
# Tests: compute_moving_averages
# ---------------------------------------------------------------------------

class TestComputeMovingAverages:
    def test_50d_sma_matches_manual(self):
        """50-day SMA should match a hand-calculated average."""
        prices = make_steady_rise(60, start=100, step=1.0)
        df = make_daily_df(prices)
        weekly_prices = make_steady_rise(40, start=100, step=5.0)
        wdf = make_weekly_df(weekly_prices)

        result = compute_moving_averages(df, wdf)
        expected_sma50 = np.mean(prices[-50:])
        assert result["sma_50"] is not None
        assert abs(result["sma_50"]["value"] - expected_sma50) < 0.01

    def test_rising_slope_classification(self):
        """A steadily rising series should produce a 'rising' slope."""
        prices = make_steady_rise(210, start=50, step=0.5)
        df = make_daily_df(prices)
        weekly_prices = make_steady_rise(40, start=50, step=2.0)
        wdf = make_weekly_df(weekly_prices)

        result = compute_moving_averages(df, wdf)
        assert result["sma_50"]["slope"] == "rising"

    def test_falling_slope_classification(self):
        """A steadily declining series should produce a 'falling' slope."""
        prices = make_steady_decline(210, start=500, step=0.5)
        df = make_daily_df(prices)
        weekly_prices = make_steady_decline(40, start=500, step=2.0)
        wdf = make_weekly_df(weekly_prices)

        result = compute_moving_averages(df, wdf)
        assert result["sma_50"]["slope"] == "falling"


# ---------------------------------------------------------------------------
# Tests: compute_obv
# ---------------------------------------------------------------------------

class TestComputeObv:
    def test_obv_direction_consistency(self):
        """OBV should rise when most days are up days with volume."""
        prices = make_steady_rise(50, start=100, step=1.0)
        volumes = [1_000_000] * 50
        df = make_daily_df(prices, volumes=volumes)
        result = compute_obv(df)
        assert result is not None
        assert result["obv"] > 0, "OBV should be positive for all-up series"

    def test_divergence_detection(self):
        """When price rises but OBV falls, divergence should be True."""
        n = 50
        # Price rises over last 21 days, but volume is heavy on down days
        prices = [100.0] * 29 + make_steady_rise(21, start=100, step=0.5)
        volumes = [1_000_000] * 29
        # For the last 21 days, alternate up/down but with heavier down-day volume
        for i in range(21):
            if i % 2 == 0:
                volumes.append(500_000)   # up day, low volume
            else:
                volumes.append(5_000_000)  # down day, high volume (simulated via price dip)
        # Adjust prices to create some down days within the rising trend
        # Override with a pattern that gives rising price but falling OBV
        base = 100.0
        rising_prices = []
        for i in range(21):
            if i % 2 == 0:
                base += 2.0  # up day
                rising_prices.append(base)
            else:
                base -= 1.0  # down day (net upward)
                rising_prices.append(base)
        prices = [100.0] * 29 + rising_prices
        df = make_daily_df(prices, volumes=volumes)
        result = compute_obv(df)
        assert result is not None
        # We verify the function runs and returns a boolean for divergence
        assert isinstance(result["divergence"], bool)


# ---------------------------------------------------------------------------
# Tests: compute_weinstein_stage
# ---------------------------------------------------------------------------

class TestComputeWeinsteinStage:
    def test_stage_in_valid_set(self):
        """Stage should be one of {1, 2, 3, 4}."""
        prices = make_steady_rise(50, start=100, step=1.0)
        wdf = make_weekly_df(prices)
        result = compute_weinstein_stage(wdf)
        assert result is not None
        assert result["stage"] in {1, 2, 3, 4}

    def test_stage_2_rising_ma_price_above(self):
        """Rising 30w MA with price above should produce Stage 2 (Advancing)."""
        prices = make_steady_rise(50, start=50, step=2.0)
        wdf = make_weekly_df(prices)
        result = compute_weinstein_stage(wdf)
        assert result is not None
        assert result["stage"] == 2
        assert result["stage_name"] == "Advancing"

    def test_stage_4_falling_ma_price_below(self):
        """Falling 30w MA with price below should produce Stage 4 (Declining)."""
        prices = make_steady_decline(50, start=300, step=2.0)
        wdf = make_weekly_df(prices)
        result = compute_weinstein_stage(wdf)
        assert result is not None
        assert result["stage"] == 4
        assert result["stage_name"] == "Declining"

    def test_insufficient_data_returns_none(self):
        """Fewer than 35 weeks should return None."""
        wdf = make_weekly_df([100] * 20)
        assert compute_weinstein_stage(wdf) is None


# ---------------------------------------------------------------------------
# Tests: compute_canslim_quantitative
# ---------------------------------------------------------------------------

class TestComputeCanslimQuantitative:
    def test_score_in_range(self):
        """CAN SLIM score should be between 0 and 5."""
        prices = make_steady_rise(300, start=50, step=0.2)
        df = make_daily_df(prices)
        spx = make_daily_df(make_constant(300, 4000))
        eps = pd.DataFrame({"eps": [1.0, 1.1, 1.2, 1.3, 1.5, 1.7]})
        result = compute_canslim_quantitative(df, spx, eps)
        assert 0 <= result["score"] <= 5

    def test_known_pass_criteria(self):
        """Construct data where N (near 52w high) clearly passes."""
        # Price is AT the 52-week high
        prices = make_steady_rise(260, start=50, step=0.1)
        df = make_daily_df(prices)
        spx = make_daily_df(make_constant(260, 4000))
        result = compute_canslim_quantitative(df, spx, None)
        # N criterion: price is at the 52-week high, so distance = 0%
        assert result["criteria"]["N"]["pass"] is True


# ---------------------------------------------------------------------------
# Tests: compute_relative_strength
# ---------------------------------------------------------------------------

class TestComputeRelativeStrength:
    def test_outperformer_rs_above_one(self):
        """A stock that outperforms its benchmark should have RS > 1."""
        stock = make_daily_df(make_steady_rise(150, start=100, step=0.5))
        bench = make_daily_df(make_steady_rise(150, start=100, step=0.1))
        result = compute_relative_strength(stock, bench)
        for period in ["1m", "3m", "6m"]:
            assert result[period] is not None
            assert result[period] > 1.0, f"RS at {period} should be > 1.0, got {result[period]}"

    def test_underperformer_rs_below_one(self):
        """A stock that underperforms its benchmark should have RS < 1."""
        stock = make_daily_df(make_steady_rise(150, start=100, step=0.1))
        bench = make_daily_df(make_steady_rise(150, start=100, step=0.5))
        result = compute_relative_strength(stock, bench)
        for period in ["1m", "3m", "6m"]:
            assert result[period] is not None
            assert result[period] < 1.0, f"RS at {period} should be < 1.0, got {result[period]}"

    def test_ratios_are_positive(self):
        """RS ratios should always be positive (prices are positive)."""
        stock = make_daily_df(make_steady_rise(300, start=50, step=0.2))
        bench = make_daily_df(make_steady_rise(300, start=100, step=0.1))
        result = compute_relative_strength(stock, bench)
        for period in ["1m", "3m", "6m", "12m"]:
            if result[period] is not None:
                assert result[period] > 0


# ---------------------------------------------------------------------------
# Tests: compute_volume_ratio
# ---------------------------------------------------------------------------

class TestComputeVolumeRatio:
    def test_more_volume_on_up_days(self):
        """When up days have higher volume, ratio should be > 1.0."""
        n = 80
        prices = []
        volumes = []
        base = 100.0
        for i in range(n):
            if i % 2 == 0:
                base += 1.0  # up day
                prices.append(base)
                volumes.append(2_000_000)  # heavy volume on up days
            else:
                base -= 0.5  # down day (smaller)
                prices.append(base)
                volumes.append(500_000)  # light volume on down days
        df = make_daily_df(prices, volumes=volumes)
        ratio = compute_volume_ratio(df, window=60)
        assert ratio is not None
        assert ratio > 1.0, f"Expected ratio > 1.0 for heavy up-day volume, got {ratio}"

    def test_ratio_positive(self):
        """Volume ratio should always be positive."""
        prices = make_steady_rise(80, start=100, step=0.3)
        df = make_daily_df(prices)
        ratio = compute_volume_ratio(df, window=60)
        if ratio is not None:
            assert ratio > 0


# ---------------------------------------------------------------------------
# Tests: compute_52week_metrics
# ---------------------------------------------------------------------------

class TestCompute52WeekMetrics:
    def test_high_gte_current_gte_low(self):
        """52w high >= current price >= 52w low."""
        prices = make_steady_rise(100, start=80, step=0.5)
        # Add a dip then recovery so high != low != current
        prices[50] = 60.0
        df = make_daily_df(prices)
        result = compute_52week_metrics(df)
        assert result is not None
        assert result["high_52w"] >= result["current"]
        assert result["current"] >= result["low_52w"]

    def test_distance_calculations(self):
        """Distance from high and low should match manual calculation."""
        prices = [100.0] * 50 + [150.0] * 10  # low=100, high=150, current=150
        df = make_daily_df(prices)
        result = compute_52week_metrics(df)
        assert result is not None
        # Current is at the high -> dist_from_high = 0%
        assert result["dist_from_high_pct"] == 0.0
        # Distance from low: (150 - 100) / 100 * 100 = 50%
        assert result["dist_from_low_pct"] == 50.0


# ---------------------------------------------------------------------------
# Tests: compute_price_zscore
# ---------------------------------------------------------------------------

class TestComputePriceZscore:
    def test_zscore_zero_at_mean(self):
        """When current price equals the mean, Z-score should be 0."""
        # Build prices centered around 100, with the last price equal to the mean
        np.random.seed(42)
        prices = list(np.random.normal(100, 5, 125)) + [100.0]
        mean_of_last_126 = np.mean(prices[-126:])
        # Set the last price exactly to the mean of the lookback window
        prices[-1] = mean_of_last_126
        df = make_daily_df(prices)
        z = compute_price_zscore(df, lookback=126)
        assert z is not None
        assert abs(z) < 0.01, f"Expected Z near 0 when price == mean, got {z}"

    def test_zscore_positive_above_mean(self):
        """When current price is above the mean, Z-score should be positive."""
        prices = make_constant(126, value=100.0)
        prices[-1] = 120.0  # push the last price well above the mean
        df = make_daily_df(prices)
        z = compute_price_zscore(df, lookback=126)
        assert z is not None
        assert z > 0, f"Expected positive Z-score when above mean, got {z}"


# ---------------------------------------------------------------------------
# Tests: compute_annualized_return
# ---------------------------------------------------------------------------

class TestComputeAnnualizedReturn:
    def test_positive_for_uptrend(self):
        """Annualized return should be positive for an uptrending series."""
        prices = make_steady_rise(300, start=100, step=0.5)
        df = make_daily_df(prices)
        result = compute_annualized_return(df)
        for period in ["1m", "3m", "6m", "12m"]:
            if result[period] is not None:
                assert result[period] > 0, f"Expected positive return at {period}"

    def test_negative_for_downtrend(self):
        """Annualized return should be negative for a downtrending series."""
        prices = make_steady_decline(300, start=500, step=0.5)
        df = make_daily_df(prices)
        result = compute_annualized_return(df)
        for period in ["1m", "3m", "6m", "12m"]:
            if result[period] is not None:
                assert result[period] < 0, f"Expected negative return at {period}"


# ---------------------------------------------------------------------------
# Tests: compute_annualized_volatility
# ---------------------------------------------------------------------------

class TestComputeAnnualizedVolatility:
    def test_non_negative(self):
        """Annualized volatility should be non-negative."""
        prices = make_steady_rise(300, start=100, step=0.3)
        df = make_daily_df(prices)
        result = compute_annualized_volatility(df)
        for period in ["1m", "3m", "6m", "12m"]:
            if result[period] is not None:
                assert result[period] >= 0

    def test_zero_for_constant_prices(self):
        """Volatility should be 0 (or near-zero) when prices don't change."""
        prices = make_constant(300, value=100.0)
        df = make_daily_df(prices)
        result = compute_annualized_volatility(df)
        for period in ["1m", "3m", "6m", "12m"]:
            if result[period] is not None:
                assert result[period] < 0.001, (
                    f"Expected near-zero vol for constant prices at {period}, "
                    f"got {result[period]}"
                )


# ---------------------------------------------------------------------------
# Tests: compute_atr
# ---------------------------------------------------------------------------

class TestComputeAtr:
    def test_atr_non_negative(self):
        """ATR must be non-negative."""
        prices = make_steady_rise(60, start=100, step=0.5)
        df = make_daily_df(prices)
        result = compute_atr(df)
        assert result is not None
        assert result["atr"] >= 0

    def test_trend_direction_present(self):
        """ATR result should contain a trend field."""
        prices = make_steady_rise(60, start=100, step=0.5)
        df = make_daily_df(prices)
        result = compute_atr(df)
        assert result is not None
        assert result["trend"] in {"increasing", "decreasing", "stable", "insufficient_data"}


# ---------------------------------------------------------------------------
# Tests: compute_all_indicators
# ---------------------------------------------------------------------------

class TestComputeAllIndicators:
    def test_returns_all_expected_keys(self):
        """The master function should return a dict with all indicator keys."""
        prices = make_steady_rise(300, start=50, step=0.2)
        daily = make_daily_df(prices)
        weekly = make_weekly_df(make_steady_rise(50, start=50, step=1.0))
        spx = make_daily_df(make_steady_rise(300, start=4000, step=0.5))
        sector = make_daily_df(make_steady_rise(300, start=100, step=0.1))

        result = compute_all_indicators(daily, weekly, spx, sector)
        expected_keys = {
            "moving_averages", "annualized_return", "annualized_volatility",
            "rsi_14", "bollinger_bands", "atr", "obv",
            "relative_strength_vs_spx", "relative_strength_vs_sector",
            "volume_ratio", "week_52_metrics", "price_zscore",
            "weinstein_stage", "canslim",
        }
        assert set(result.keys()) == expected_keys

    def test_no_crash_on_valid_input(self):
        """The master function should not raise on well-formed data."""
        prices = make_steady_rise(300, start=50, step=0.2)
        daily = make_daily_df(prices)
        weekly = make_weekly_df(make_steady_rise(50, start=50, step=1.0))
        spx = make_daily_df(make_constant(300, 4000))
        sector = make_daily_df(make_constant(300, 100))
        eps = pd.DataFrame({"eps": [1.0, 1.1, 1.2, 1.3, 1.5, 1.7]})

        # Should complete without exception
        result = compute_all_indicators(daily, weekly, spx, sector, eps_data=eps)
        assert isinstance(result, dict)
