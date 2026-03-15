"""Technical indicator computations for DualEdge stock analysis.

All functions take pandas DataFrames (from data_utils) and return dicts
of computed values. Edge cases (insufficient data, NaN) are handled
gracefully — functions return None for values that can't be computed.
"""

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Moving Averages
# ---------------------------------------------------------------------------

def compute_moving_averages(daily_df: pd.DataFrame, weekly_df: pd.DataFrame) -> dict:
    """Compute SMA 50, 150, 200 (daily) and 30-week (weekly).

    Args:
        daily_df: Daily OHLCV DataFrame with 'Close' column.
        weekly_df: Weekly OHLCV DataFrame with 'Close' column.

    Returns:
        Dict with current MA values and slope classifications
        (rising/flat/falling based on 10-period slope).
    """
    result = {}

    for window in [50, 150, 200]:
        key = f"sma_{window}"
        if len(daily_df) >= window:
            ma = daily_df["Close"].rolling(window=window).mean()
            current = ma.iloc[-1]
            # Slope: compare current MA to MA 10 days ago
            prev = ma.iloc[-11] if len(ma) >= 11 else ma.iloc[0]
            pct_change = (current - prev) / prev if prev != 0 else 0
            if pct_change > 0.005:
                slope = "rising"
            elif pct_change < -0.005:
                slope = "falling"
            else:
                slope = "flat"
            result[key] = {"value": round(float(current), 2), "slope": slope}
        else:
            result[key] = None

    # 30-week MA
    if len(weekly_df) >= 30:
        ma_30w = weekly_df["Close"].rolling(window=30).mean()
        current = ma_30w.iloc[-1]
        prev = ma_30w.iloc[-5] if len(ma_30w) >= 5 else ma_30w.iloc[0]
        pct_change = (current - prev) / prev if prev != 0 else 0
        if pct_change > 0.005:
            slope = "rising"
        elif pct_change < -0.005:
            slope = "falling"
        else:
            slope = "flat"
        result["sma_30w"] = {"value": round(float(current), 2), "slope": slope}
    else:
        result["sma_30w"] = None

    return result


# ---------------------------------------------------------------------------
# Annualized Return
# ---------------------------------------------------------------------------

def compute_annualized_return(daily_df: pd.DataFrame) -> dict:
    """Compute annualized return for multiple windows.

    Formula: R_ann = (1 + R_cum)^(252/n) - 1

    Args:
        daily_df: Daily OHLCV DataFrame with 'Close' column.

    Returns:
        Dict with annualized returns at 1m, 3m, 6m, 12m windows.
    """
    close = daily_df["Close"]
    result = {}
    windows = {"1m": 21, "3m": 63, "6m": 126, "12m": 252}

    for label, n in windows.items():
        if len(close) > n:
            r_cum = (close.iloc[-1] / close.iloc[-n - 1]) - 1
            r_ann = (1 + r_cum) ** (252 / n) - 1
            result[label] = round(float(r_ann), 4)
        else:
            result[label] = None

    return result


# ---------------------------------------------------------------------------
# Annualized Volatility
# ---------------------------------------------------------------------------

def compute_annualized_volatility(daily_df: pd.DataFrame) -> dict:
    """Compute annualized volatility for multiple windows.

    Formula: sigma_ann = sigma_daily * sqrt(252)

    Args:
        daily_df: Daily OHLCV DataFrame with 'Close' column.

    Returns:
        Dict with annualized volatility at 1m, 3m, 6m, 12m, plus
        12-month average for regime comparison.
    """
    log_returns = np.log(daily_df["Close"] / daily_df["Close"].shift(1)).dropna()
    result = {}
    windows = {"1m": 21, "3m": 63, "6m": 126, "12m": 252}

    for label, n in windows.items():
        if len(log_returns) >= n:
            daily_std = log_returns.iloc[-n:].std()
            result[label] = round(float(daily_std * np.sqrt(252)), 4)
        else:
            result[label] = None

    # 12-month average volatility (rolling 21-day vol, averaged over 252 days)
    if len(log_returns) >= 252:
        rolling_vol = log_returns.rolling(21).std() * np.sqrt(252)
        result["12m_average"] = round(float(rolling_vol.iloc[-252:].mean()), 4)
    else:
        result["12m_average"] = result.get("12m")

    return result


# ---------------------------------------------------------------------------
# RSI (Wilder's Smoothed)
# ---------------------------------------------------------------------------

def compute_rsi(daily_df: pd.DataFrame, period: int = 14) -> float | None:
    """Compute RSI using Wilder's smoothing method.

    Args:
        daily_df: Daily OHLCV DataFrame with 'Close' column.
        period: RSI period (default 14).

    Returns:
        Current RSI value (0-100), or None if insufficient data.
    """
    close = daily_df["Close"]
    if len(close) < period + 1:
        return None

    delta = close.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = (-delta).where(delta < 0, 0.0)

    # Wilder's smoothing: first average is simple, then exponential
    avg_gain = gain.iloc[1:period + 1].mean()
    avg_loss = loss.iloc[1:period + 1].mean()

    for i in range(period + 1, len(close)):
        avg_gain = (avg_gain * (period - 1) + gain.iloc[i]) / period
        avg_loss = (avg_loss * (period - 1) + loss.iloc[i]) / period

    if avg_loss == 0:
        return 100.0

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return round(float(rsi), 2)


# ---------------------------------------------------------------------------
# Bollinger Bands
# ---------------------------------------------------------------------------

def compute_bollinger_bands(daily_df: pd.DataFrame, period: int = 20,
                            num_std: float = 2.0) -> dict | None:
    """Compute Bollinger Bands and band width metrics.

    Args:
        daily_df: Daily OHLCV DataFrame with 'Close' column.
        period: Moving average period (default 20).
        num_std: Number of standard deviations (default 2.0).

    Returns:
        Dict with upper/middle/lower bands, current width, width percentile
        vs past 252 days. None if insufficient data.
    """
    close = daily_df["Close"]
    if len(close) < period:
        return None

    middle = close.rolling(window=period).mean()
    std = close.rolling(window=period).std()
    upper = middle + num_std * std
    lower = middle - num_std * std
    width = (upper - lower) / middle

    # Width percentile relative to past 252 days (or available data)
    lookback = min(252, len(width.dropna()))
    recent_width = width.dropna().iloc[-lookback:]
    current_width = width.iloc[-1]
    if len(recent_width) > 1:
        percentile = float((recent_width < current_width).sum() / len(recent_width) * 100)
    else:
        percentile = 50.0

    current_price = close.iloc[-1]
    return {
        "upper": round(float(upper.iloc[-1]), 2),
        "middle": round(float(middle.iloc[-1]), 2),
        "lower": round(float(lower.iloc[-1]), 2),
        "current_width": round(float(current_width), 4),
        "width_percentile": round(percentile, 1),
        "price_position": "above_upper" if current_price > upper.iloc[-1]
                          else "below_lower" if current_price < lower.iloc[-1]
                          else "within_bands",
    }


# ---------------------------------------------------------------------------
# ATR (Average True Range)
# ---------------------------------------------------------------------------

def compute_atr(daily_df: pd.DataFrame, period: int = 14) -> dict | None:
    """Compute Average True Range using Wilder's smoothing.

    Args:
        daily_df: Daily OHLCV DataFrame with High, Low, Close columns.
        period: ATR period (default 14).

    Returns:
        Dict with current ATR, ATR as % of price, and trend direction
        (last 20 days vs prior 20 days). None if insufficient data.
    """
    if len(daily_df) < period + 1:
        return None

    high = daily_df["High"]
    low = daily_df["Low"]
    close = daily_df["Close"]

    # True Range
    tr1 = high - low
    tr2 = (high - close.shift(1)).abs()
    tr3 = (low - close.shift(1)).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

    # Wilder's smoothing for ATR
    atr = tr.rolling(window=period).mean()
    # Refine with exponential smoothing after initial
    atr_series = [float(atr.iloc[period - 1])]
    for i in range(period, len(tr)):
        atr_val = (atr_series[-1] * (period - 1) + float(tr.iloc[i])) / period
        atr_series.append(atr_val)

    current_atr = atr_series[-1]
    current_price = float(close.iloc[-1])

    # Trend: compare last 20 days average ATR vs prior 20 days
    if len(atr_series) >= 40:
        recent_avg = np.mean(atr_series[-20:])
        prior_avg = np.mean(atr_series[-40:-20])
        trend = "increasing" if recent_avg > prior_avg * 1.05 else \
                "decreasing" if recent_avg < prior_avg * 0.95 else "stable"
    else:
        trend = "insufficient_data"

    return {
        "atr": round(current_atr, 2),
        "atr_pct": round(current_atr / current_price * 100, 2) if current_price > 0 else None,
        "trend": trend,
    }


# ---------------------------------------------------------------------------
# On-Balance Volume (OBV)
# ---------------------------------------------------------------------------

def compute_obv(daily_df: pd.DataFrame) -> dict | None:
    """Compute On-Balance Volume and related signals.

    Args:
        daily_df: Daily OHLCV DataFrame with Close and Volume columns.

    Returns:
        Dict with current OBV, 20-day OBV MA, OBV trend direction,
        and price-OBV divergence flag. None if insufficient data.
    """
    if len(daily_df) < 21:
        return None

    close = daily_df["Close"]
    volume = daily_df["Volume"]

    # OBV calculation
    direction = np.sign(close.diff())
    direction.iloc[0] = 0
    obv = (direction * volume).cumsum()

    obv_ma20 = obv.rolling(window=20).mean()

    current_obv = float(obv.iloc[-1])
    current_obv_ma = float(obv_ma20.iloc[-1])

    # OBV trend (20-day slope)
    obv_20_ago = float(obv.iloc[-21])
    obv_trend = "rising" if current_obv > obv_20_ago * 1.02 else \
                "falling" if current_obv < obv_20_ago * 0.98 else "flat"

    # Price trend (20-day)
    price_now = float(close.iloc[-1])
    price_20_ago = float(close.iloc[-21])
    price_trend = "rising" if price_now > price_20_ago * 1.02 else \
                  "falling" if price_now < price_20_ago * 0.98 else "flat"

    # Divergence: price and OBV moving in opposite directions
    divergence = False
    if (price_trend == "rising" and obv_trend == "falling") or \
       (price_trend == "falling" and obv_trend == "rising"):
        divergence = True

    return {
        "obv": round(current_obv),
        "obv_ma20": round(current_obv_ma),
        "obv_trend": obv_trend,
        "price_trend": price_trend,
        "divergence": divergence,
    }


# ---------------------------------------------------------------------------
# Relative Strength
# ---------------------------------------------------------------------------

def compute_relative_strength(daily_df: pd.DataFrame,
                               benchmark_df: pd.DataFrame) -> dict:
    """Compute relative strength ratios vs a benchmark at multiple windows.

    RS = stock_return / benchmark_return

    Args:
        daily_df: Stock daily OHLCV.
        benchmark_df: Benchmark daily OHLCV (S&P 500 or sector ETF).

    Returns:
        Dict with RS ratios at 1m, 3m, 6m, 12m and trajectory assessment.
    """
    stock_close = daily_df["Close"]
    bench_close = benchmark_df["Close"]
    windows = {"1m": 21, "3m": 63, "6m": 126, "12m": 252}
    result = {}

    for label, n in windows.items():
        if len(stock_close) > n and len(bench_close) > n:
            stock_ret = float(stock_close.iloc[-1] / stock_close.iloc[-n - 1]) - 1
            bench_ret = float(bench_close.iloc[-1] / bench_close.iloc[-n - 1]) - 1
            # Avoid division by zero; if benchmark flat, use raw return
            if abs(bench_ret) < 0.0001:
                rs = 1.0 + stock_ret
            else:
                rs = (1 + stock_ret) / (1 + bench_ret)
            result[label] = round(rs, 4)
        else:
            result[label] = None

    # Trajectory: is RS improving (3m > 6m) or deteriorating?
    rs_3m = result.get("3m")
    rs_6m = result.get("6m")
    if rs_3m is not None and rs_6m is not None:
        if rs_3m > rs_6m * 1.02:
            result["trajectory"] = "improving"
        elif rs_3m < rs_6m * 0.98:
            result["trajectory"] = "deteriorating"
        else:
            result["trajectory"] = "stable"
    else:
        result["trajectory"] = "insufficient_data"

    return result


# ---------------------------------------------------------------------------
# Volume Ratio
# ---------------------------------------------------------------------------

def compute_volume_ratio(daily_df: pd.DataFrame, window: int = 60) -> float | None:
    """Compute ratio of average volume on up days vs down days.

    Up day = close > previous close.

    Args:
        daily_df: Daily OHLCV DataFrame.
        window: Lookback window in trading days (default 60).

    Returns:
        Volume ratio (>1.0 = more volume on up days). None if insufficient data.
    """
    if len(daily_df) < window + 1:
        return None

    recent = daily_df.iloc[-(window + 1):]
    price_change = recent["Close"].diff()
    volume = recent["Volume"]

    up_days = volume[price_change > 0]
    down_days = volume[price_change < 0]

    if len(down_days) == 0 or down_days.mean() == 0:
        return None

    ratio = float(up_days.mean() / down_days.mean())
    return round(ratio, 4)


# ---------------------------------------------------------------------------
# 52-Week Metrics
# ---------------------------------------------------------------------------

def compute_52week_metrics(daily_df: pd.DataFrame) -> dict | None:
    """Compute 52-week high, low, and distance from each.

    Args:
        daily_df: Daily OHLCV DataFrame with at least 252 rows.

    Returns:
        Dict with 52w high/low values and percentage distances.
        None if insufficient data.
    """
    lookback = min(252, len(daily_df))
    if lookback < 20:
        return None

    recent = daily_df.iloc[-lookback:]
    high_52w = float(recent["Close"].max())
    low_52w = float(recent["Close"].min())
    current = float(daily_df["Close"].iloc[-1])

    return {
        "high_52w": round(high_52w, 2),
        "low_52w": round(low_52w, 2),
        "current": round(current, 2),
        "dist_from_high_pct": round((current - high_52w) / high_52w * 100, 2),
        "dist_from_low_pct": round((current - low_52w) / low_52w * 100, 2),
    }


# ---------------------------------------------------------------------------
# Price Z-Score
# ---------------------------------------------------------------------------

def compute_price_zscore(daily_df: pd.DataFrame, lookback: int = 126) -> float | None:
    """Compute Z-score of current price relative to lookback distribution.

    Args:
        daily_df: Daily OHLCV DataFrame.
        lookback: Number of trading days for distribution (default 126 = ~6 months).

    Returns:
        Z-score float. None if insufficient data.
    """
    if len(daily_df) < lookback:
        return None

    close = daily_df["Close"].iloc[-lookback:]
    mean = float(close.mean())
    std = float(close.std())
    current = float(daily_df["Close"].iloc[-1])

    if std == 0:
        return 0.0

    z = (current - mean) / std
    return round(float(z), 2)


# ---------------------------------------------------------------------------
# Weinstein Stage Analysis
# ---------------------------------------------------------------------------

def compute_weinstein_stage(weekly_df: pd.DataFrame) -> dict | None:
    """Classify Weinstein stage (1-4) based on 30-week MA behavior.

    Stage 1 (Basing): flat 30w MA, price oscillating around it
    Stage 2 (Advancing): rising 30w MA, price above it
    Stage 3 (Topping): flattening 30w MA, price crossing below
    Stage 4 (Declining): falling 30w MA, price below it

    Args:
        weekly_df: Weekly OHLCV DataFrame.

    Returns:
        Dict with stage, confidence, component assessments.
        None if insufficient data.
    """
    if len(weekly_df) < 35:
        return None

    close = weekly_df["Close"]
    ma_30w = close.rolling(window=30).mean()
    volume = weekly_df["Volume"]

    current_price = float(close.iloc[-1])
    current_ma = float(ma_30w.iloc[-1])
    ma_5_weeks_ago = float(ma_30w.iloc[-6]) if len(ma_30w) >= 6 else current_ma

    # MA slope
    pct_change = (current_ma - ma_5_weeks_ago) / ma_5_weeks_ago if ma_5_weeks_ago != 0 else 0
    if pct_change > 0.01:
        ma_slope = "rising"
    elif pct_change < -0.01:
        ma_slope = "falling"
    else:
        ma_slope = "flat"

    # Price vs MA
    price_vs_ma = current_price / current_ma if current_ma != 0 else 1.0
    if price_vs_ma > 1.03:
        price_position = "above"
    elif price_vs_ma < 0.97:
        price_position = "below"
    else:
        price_position = "at"

    # Volume pattern (recent 8 weeks vs prior 8 weeks)
    if len(volume) >= 16:
        recent_vol = volume.iloc[-8:].mean()
        prior_vol = volume.iloc[-16:-8].mean()
        vol_ratio = recent_vol / prior_vol if prior_vol > 0 else 1.0
        if vol_ratio > 1.15:
            volume_pattern = "expanding"
        elif vol_ratio < 0.85:
            volume_pattern = "contracting"
        else:
            volume_pattern = "mixed"
    else:
        volume_pattern = "insufficient_data"

    # Stage classification
    if ma_slope == "rising" and price_position == "above":
        stage = 2
        confidence = "high" if volume_pattern == "expanding" else "moderate"
    elif ma_slope == "falling" and price_position == "below":
        stage = 4
        confidence = "high" if volume_pattern == "expanding" else "moderate"
    elif ma_slope == "flat" and price_position in ("at", "above"):
        stage = 1
        confidence = "moderate" if volume_pattern == "contracting" else "low"
    elif (ma_slope == "flat" or ma_slope == "falling") and price_position in ("at", "below"):
        # Distinguish stage 3 (topping) from stage 4 (declining)
        if ma_slope == "flat":
            stage = 3
            confidence = "moderate"
        else:
            stage = 4
            confidence = "moderate"
    elif ma_slope == "rising" and price_position in ("at", "below"):
        # Possible late stage 2 or early stage 3
        stage = 3
        confidence = "low"
    else:
        stage = 1
        confidence = "low"

    stage_names = {1: "Basing", 2: "Advancing", 3: "Topping", 4: "Declining"}

    return {
        "stage": stage,
        "stage_name": stage_names[stage],
        "confidence": confidence,
        "ma_30w_slope": ma_slope,
        "price_vs_30w_ma": price_position,
        "price_to_ma_ratio": round(price_vs_ma, 4),
        "volume_pattern": volume_pattern,
    }


# ---------------------------------------------------------------------------
# CAN SLIM Quantitative
# ---------------------------------------------------------------------------

def compute_canslim_quantitative(daily_df: pd.DataFrame, spx_df: pd.DataFrame,
                                  eps_data: pd.DataFrame | None) -> dict:
    """Score O'Neil's CAN SLIM quantitative criteria.

    C: Current quarterly EPS > year-ago quarter, with acceleration
    A: Annual EPS growth (3-year CAGR > 25%)
    N: Price within 5% of 52-week high
    S: Volume ratio (up/down days) > 1.0
    L: 6-month RS vs SPX > 1.0 (top quartile proxy)

    Args:
        daily_df: Stock daily OHLCV.
        spx_df: S&P 500 daily OHLCV.
        eps_data: Quarterly EPS DataFrame from get_quarterly_eps().

    Returns:
        Dict with pass/fail per criterion and total score (0-5).
    """
    criteria = {}

    # C — Current quarterly EPS acceleration
    c_pass = False
    c_detail = "N/A — insufficient EPS data"
    if eps_data is not None and len(eps_data) >= 5:
        # Compare most recent quarter to same quarter last year
        recent_eps = float(eps_data["eps"].iloc[-1])
        year_ago_eps = float(eps_data["eps"].iloc[-5]) if len(eps_data) >= 5 else None
        if year_ago_eps is not None and year_ago_eps > 0:
            growth = (recent_eps - year_ago_eps) / abs(year_ago_eps)
            c_pass = growth > 0
            c_detail = f"EPS growth YoY: {growth:.1%}"
        elif year_ago_eps is not None:
            c_pass = recent_eps > year_ago_eps
            c_detail = f"EPS: {recent_eps:.2f} vs year-ago {year_ago_eps:.2f}"
    elif eps_data is not None and len(eps_data) >= 2:
        recent = float(eps_data["eps"].iloc[-1])
        prev = float(eps_data["eps"].iloc[-2])
        c_pass = recent > prev
        c_detail = f"Sequential EPS: {recent:.2f} vs {prev:.2f} (limited data)"
    criteria["C"] = {"pass": c_pass, "detail": c_detail}

    # A — Annual earnings growth
    a_pass = False
    a_detail = "N/A — insufficient annual EPS data"
    if eps_data is not None and len(eps_data) >= 4:
        # Use available EPS data to estimate annual growth
        eps_values = eps_data["eps"].values
        oldest = float(eps_values[0])
        newest = float(eps_values[-1])
        n_years = len(eps_values) / 4
        if oldest > 0 and newest > 0 and n_years > 0:
            cagr = (newest / oldest) ** (1 / n_years) - 1
            a_pass = cagr > 0.25
            a_detail = f"EPS CAGR: {cagr:.1%} (threshold: 25%)"
        else:
            a_detail = f"Cannot compute CAGR (oldest EPS: {oldest:.2f})"
    criteria["A"] = {"pass": a_pass, "detail": a_detail}

    # N — New highs (within 5% of 52-week high)
    metrics_52w = compute_52week_metrics(daily_df)
    if metrics_52w:
        dist = abs(metrics_52w["dist_from_high_pct"])
        n_pass = dist <= 5.0
        n_detail = f"Distance from 52w high: {metrics_52w['dist_from_high_pct']:.1f}%"
    else:
        n_pass = False
        n_detail = "N/A — insufficient price data"
    criteria["N"] = {"pass": n_pass, "detail": n_detail}

    # S — Supply/demand (volume ratio > 1.0)
    vol_ratio = compute_volume_ratio(daily_df)
    if vol_ratio is not None:
        s_pass = vol_ratio > 1.0
        s_detail = f"Volume ratio (up/down): {vol_ratio:.2f}"
    else:
        s_pass = False
        s_detail = "N/A — insufficient volume data"
    criteria["S"] = {"pass": s_pass, "detail": s_detail}

    # L — Leader (6-month RS vs SPX > 1.0)
    rs = compute_relative_strength(daily_df, spx_df)
    rs_6m = rs.get("6m")
    if rs_6m is not None:
        l_pass = rs_6m > 1.0
        l_detail = f"6-month RS vs SPX: {rs_6m:.4f}"
    else:
        l_pass = False
        l_detail = "N/A — insufficient data for RS calculation"
    criteria["L"] = {"pass": l_pass, "detail": l_detail}

    score = sum(1 for c in criteria.values() if c["pass"])
    return {"criteria": criteria, "score": score, "max_score": 5}


# ---------------------------------------------------------------------------
# Master Function
# ---------------------------------------------------------------------------

def compute_all_indicators(daily_df: pd.DataFrame, weekly_df: pd.DataFrame,
                           spx_df: pd.DataFrame, sector_df: pd.DataFrame,
                           eps_data: pd.DataFrame | None = None) -> dict:
    """Compute all technical indicators for a stock.

    This is the single entry point agents call. It orchestrates every
    individual indicator function and returns a structured dict.

    Args:
        daily_df: Stock daily OHLCV (18 months).
        weekly_df: Stock weekly OHLCV (3 years).
        spx_df: S&P 500 daily OHLCV.
        sector_df: Sector ETF daily OHLCV.
        eps_data: Quarterly EPS DataFrame (optional, for CAN SLIM).

    Returns:
        Dict organized by category with all computed indicator values.
    """
    return {
        "moving_averages": compute_moving_averages(daily_df, weekly_df),
        "annualized_return": compute_annualized_return(daily_df),
        "annualized_volatility": compute_annualized_volatility(daily_df),
        "rsi_14": compute_rsi(daily_df),
        "bollinger_bands": compute_bollinger_bands(daily_df),
        "atr": compute_atr(daily_df),
        "obv": compute_obv(daily_df),
        "relative_strength_vs_spx": compute_relative_strength(daily_df, spx_df),
        "relative_strength_vs_sector": compute_relative_strength(daily_df, sector_df),
        "volume_ratio": compute_volume_ratio(daily_df),
        "week_52_metrics": compute_52week_metrics(daily_df),
        "price_zscore": compute_price_zscore(daily_df),
        "weinstein_stage": compute_weinstein_stage(weekly_df),
        "canslim": compute_canslim_quantitative(daily_df, spx_df, eps_data),
    }
