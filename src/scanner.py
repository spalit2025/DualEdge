"""Tier 1 Daily Signal Scanner for DualEdge Watchlist Monitor.

Pure Python scanner — no LLM calls. Pulls market data using existing
data_utils.py, computes indicators via indicators.py, evaluates 18 trigger
conditions, and outputs a markdown dashboard with flagged alerts.

Usage:
    python -m src.scanner
    python -m src.scanner --watchlist watchlist.json
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

# Ensure project root is on sys.path for standalone execution
_project_root = str(Path(__file__).resolve().parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

import numpy as np
import pandas as pd

from src.data_utils import (
    get_insider_transactions,
    get_key_ratios,
    get_ohlcv_daily,
    get_ohlcv_weekly,
    get_quarterly_eps,
    validate_ticker,
)
from src.indicators import compute_all_indicators
from src.portfolio import (
    compute_concentration,
    compute_correlation_matrix,
    compute_holding_metrics,
    compute_portfolio_metrics,
)
from src.sector_map import SECTOR_ETF_MAP, get_sector_etf

# Hardcoded sector P/E medians for D1 trigger (from V1.1 addendum)
SECTOR_PE_MEDIANS = {
    "Technology": 28,
    "Healthcare": 22,
    "Financial Services": 14,
    "Financials": 14,
    "Consumer Cyclical": 22,
    "Consumer Discretionary": 22,
    "Consumer Defensive": 20,
    "Consumer Staples": 20,
    "Industrials": 20,
    "Energy": 12,
    "Basic Materials": 16,
    "Materials": 16,
    "Utilities": 18,
    "Real Estate": 38,
    "Communication Services": 20,
}


# ---------------------------------------------------------------------------
# Watchlist Loading & Validation
# ---------------------------------------------------------------------------

def load_watchlist(path: str = "watchlist.json") -> dict:
    """Load and validate watchlist.json.

    Args:
        path: Path to watchlist.json.

    Returns:
        Parsed watchlist dict.

    Raises:
        FileNotFoundError: If watchlist.json doesn't exist.
        ValueError: If required fields are missing.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"watchlist.json not found at {path}. "
            "Create it with risk_profile, portfolio.holdings, and watchlist fields."
        )

    with open(path, "r") as f:
        data = json.load(f)

    # Validate required fields
    if "risk_profile" not in data:
        raise ValueError("watchlist.json must have 'risk_profile' field")
    if data["risk_profile"] not in ("risk-neutral", "risk-averse"):
        raise ValueError("risk_profile must be 'risk-neutral' or 'risk-averse'")
    if "portfolio" not in data or "holdings" not in data["portfolio"]:
        raise ValueError("watchlist.json must have portfolio.holdings array")
    if "watchlist" not in data:
        raise ValueError("watchlist.json must have 'watchlist' array")

    # Defaults for optional fields
    data.setdefault("previous_analyses", {})
    data["portfolio"].setdefault("cash_balance", 0)
    data.setdefault("scanner_config", {})
    data["scanner_config"].setdefault("lookback_daily_months", 18)
    data["scanner_config"].setdefault("lookback_weekly_years", 3)
    data["scanner_config"].setdefault("volume_spike_multiplier", 2.0)
    data["scanner_config"].setdefault("api_delay_seconds", 0.5)

    return data


# ---------------------------------------------------------------------------
# Prior Scan Loading
# ---------------------------------------------------------------------------

def load_prior_scan(scan_dir: str = "scans") -> dict | None:
    """Load the most recent scan_data.json from scans/ directory.

    Returns:
        Parsed scan data dict, or None if no prior scan exists.
    """
    scan_path = Path(scan_dir)
    if not scan_path.exists():
        return None

    # Find most recent date directory
    date_dirs = sorted(
        [d for d in scan_path.iterdir() if d.is_dir()],
        key=lambda d: d.name,
        reverse=True,
    )

    for d in date_dirs:
        json_path = d / "scan_data.json"
        if json_path.exists():
            try:
                with open(json_path, "r") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: Could not load prior scan from {json_path}: {e}")
                continue

    return None


# ---------------------------------------------------------------------------
# Data Pulling (Optimized)
# ---------------------------------------------------------------------------

def pull_all_data(all_tickers: list[str], config: dict) -> dict:
    """Pull market data for all tickers with optimized benchmark caching.

    Pulls S&P 500 once, each sector ETF once per sector.

    Args:
        all_tickers: Combined list of holding + watchlist tickers.
        config: scanner_config from watchlist.json.

    Returns:
        Dict keyed by ticker with sub-dicts containing:
        daily, weekly, spx, sector_df, sector_etf, sector_name,
        ratios, eps, insider.
    """
    delay = config.get("api_delay_seconds", 0.5)
    daily_months = config.get("lookback_daily_months", 18)
    weekly_years = config.get("lookback_weekly_years", 3)

    # Pull S&P 500 once
    print("  Pulling S&P 500 data...")
    spx_df = get_ohlcv_daily("^GSPC", months=daily_months)
    time.sleep(delay)

    # Determine sector for each ticker and cache sector ETF data
    sector_cache = {}  # etf_ticker -> DataFrame
    ticker_sectors = {}  # ticker -> sector_name
    ticker_sector_etfs = {}  # ticker -> etf_ticker

    for ticker in all_tickers:
        sector_etf = get_sector_etf(ticker)
        ticker_sector_etfs[ticker] = sector_etf
        # Get sector name from yfinance info (already called in get_sector_etf)
        try:
            import yfinance as yf
            info = yf.Ticker(ticker).info
            ticker_sectors[ticker] = info.get("sector", "Unknown")
        except Exception:
            ticker_sectors[ticker] = "Unknown"

        if sector_etf not in sector_cache:
            print(f"  Pulling sector ETF {sector_etf}...")
            sector_cache[sector_etf] = get_ohlcv_daily(sector_etf, months=daily_months)
            time.sleep(delay)

    # Pull per-ticker data
    data = {}
    for i, ticker in enumerate(all_tickers):
        print(f"  [{i+1}/{len(all_tickers)}] Pulling data for {ticker}...")

        daily = get_ohlcv_daily(ticker, months=daily_months)
        time.sleep(delay)
        weekly = get_ohlcv_weekly(ticker, years=weekly_years)
        time.sleep(delay)
        ratios = get_key_ratios(ticker)
        time.sleep(delay)
        eps = get_quarterly_eps(ticker)
        time.sleep(delay)
        insider = get_insider_transactions(ticker)
        time.sleep(delay)

        sector_etf = ticker_sector_etfs[ticker]
        sector_df = sector_cache.get(sector_etf)

        data[ticker] = {
            "daily": daily,
            "weekly": weekly,
            "spx": spx_df,
            "sector_df": sector_df,
            "sector_etf": sector_etf,
            "sector_name": ticker_sectors.get(ticker, "Unknown"),
            "ratios": ratios,
            "eps": eps,
            "insider": insider,
        }

    return data


# ===========================================================================
# TRIGGER EVALUATION — 18 triggers across 5 categories
# ===========================================================================

# ---------------------------------------------------------------------------
# Category A: Trend & Stage Triggers (A1-A4)
# ---------------------------------------------------------------------------

def _eval_a1_weinstein_stage_change(indicators: dict, prior_stock: dict | None) -> dict | None:
    """A1: Weinstein Stage Change — stage value changed from prior scan."""
    weinstein = indicators.get("weinstein_stage")
    if weinstein is None:
        return None

    current_stage = weinstein["stage"]

    if prior_stock is None:
        return None  # First scan — baseline only, no flag

    prior_stage = prior_stock.get("indicators", {}).get("weinstein_stage")
    if prior_stage is None:
        return None

    if current_stage != prior_stage:
        return {
            "id": "A1",
            "category": "Trend",
            "priority": "HIGH",
            "description": f"STAGE CHANGE: Stage {prior_stage} → Stage {current_stage} ({weinstein['stage_name']})",
            "details": {
                "old_stage": prior_stage,
                "new_stage": current_stage,
                "stage_name": weinstein["stage_name"],
                "confidence": weinstein["confidence"],
            },
        }
    return None


def _eval_a2_30w_ma_crossover(indicators: dict, daily_df: pd.DataFrame,
                               prior_stock: dict | None, risk_profile: str,
                               is_holding: bool) -> dict | None:
    """A2: Price vs 30-Week MA Crossover."""
    ma_data = indicators.get("moving_averages", {})
    sma_30w = ma_data.get("sma_30w")
    if sma_30w is None:
        return None

    current_close = float(daily_df["Close"].iloc[-1])
    ma_value = sma_30w["value"]
    currently_above = current_close > ma_value
    distance_pct = abs(current_close - ma_value) / ma_value * 100

    if prior_stock is None:
        # First scan: flag if within 2% of MA
        if distance_pct <= 2.0:
            return {
                "id": "A2",
                "category": "Trend",
                "priority": "INFO",
                "description": f"30W MA PROXIMITY: Price within {distance_pct:.1f}% of 30-week MA (${ma_value})",
                "details": {"distance_pct": round(distance_pct, 2), "ma_value": ma_value},
            }
        return None

    # State change detection
    prior_30w_above = prior_stock.get("indicators", {}).get("price_above_30w_ma")
    if prior_30w_above is None:
        return None

    if currently_above != prior_30w_above:
        direction = "ABOVE" if currently_above else "BELOW"
        priority = "HIGH"
        # Risk-averse upgrade: downward cross on holding → URGENT
        if risk_profile == "risk-averse" and not currently_above and is_holding:
            priority = "HIGHEST"
        return {
            "id": "A2",
            "category": "Trend",
            "priority": priority,
            "description": f"30W MA CROSS: Price crossed {direction} 30-week MA (${ma_value})",
            "details": {
                "direction": direction,
                "ma_value": ma_value,
                "current_close": round(current_close, 2),
            },
        }
    return None


def _eval_a3_200d_ma_crossover(indicators: dict, daily_df: pd.DataFrame,
                                prior_stock: dict | None) -> dict | None:
    """A3: Price vs 200-Day MA Crossover."""
    ma_data = indicators.get("moving_averages", {})
    sma_200 = ma_data.get("sma_200")
    if sma_200 is None:
        return None

    current_close = float(daily_df["Close"].iloc[-1])
    ma_value = sma_200["value"]
    currently_above = current_close > ma_value
    distance_pct = abs(current_close - ma_value) / ma_value * 100

    if prior_stock is None:
        # First scan: flag if within 2% of MA (same as A2)
        if distance_pct <= 2.0:
            return {
                "id": "A3",
                "category": "Trend",
                "priority": "INFO",
                "description": f"200D MA PROXIMITY: Price within {distance_pct:.1f}% of 200-day MA (${ma_value})",
                "details": {"distance_pct": round(distance_pct, 2), "ma_value": ma_value},
            }
        return None

    prior_200d_above = prior_stock.get("indicators", {}).get("price_above_200d_ma")
    if prior_200d_above is None:
        return None

    if currently_above != prior_200d_above:
        direction = "ABOVE" if currently_above else "BELOW"
        return {
            "id": "A3",
            "category": "Trend",
            "priority": "HIGH",
            "description": f"200D MA CROSS: Price crossed {direction} 200-day MA (${ma_value})",
            "details": {
                "direction": direction,
                "ma_value": ma_value,
                "current_close": round(current_close, 2),
            },
        }
    return None


def _classify_ma_alignment(indicators: dict) -> str | None:
    """Classify MA alignment as bullish/bearish/mixed."""
    ma = indicators.get("moving_averages", {})
    sma_50 = ma.get("sma_50")
    sma_150 = ma.get("sma_150")
    sma_200 = ma.get("sma_200")
    if not all([sma_50, sma_150, sma_200]):
        return None

    v50, v150, v200 = sma_50["value"], sma_150["value"], sma_200["value"]
    s50, s150, s200 = sma_50["slope"], sma_150["slope"], sma_200["slope"]

    if v50 > v150 > v200 and all(s == "rising" for s in [s50, s150, s200]):
        return "bullish"
    elif v50 < v150 < v200 and all(s == "falling" for s in [s50, s150, s200]):
        return "bearish"
    else:
        return "mixed"


def _eval_a4_ma_alignment_shift(indicators: dict,
                                 prior_stock: dict | None) -> dict | None:
    """A4: MA Alignment Shift — 50/150/200 order changed."""
    current_alignment = _classify_ma_alignment(indicators)
    if current_alignment is None:
        return None

    if prior_stock is None:
        return None  # First scan — baseline only

    prior_alignment = prior_stock.get("indicators", {}).get("ma_alignment")
    if prior_alignment is None:
        return None

    if current_alignment != prior_alignment:
        ma = indicators["moving_averages"]
        return {
            "id": "A4",
            "category": "Trend",
            "priority": "MEDIUM",
            "description": (
                f"MA ALIGNMENT: {prior_alignment} → {current_alignment} "
                f"(50d=${ma['sma_50']['value']}, 150d=${ma['sma_150']['value']}, "
                f"200d=${ma['sma_200']['value']})"
            ),
            "details": {
                "old_alignment": prior_alignment,
                "new_alignment": current_alignment,
            },
        }
    return None


# ---------------------------------------------------------------------------
# Category B: Momentum & Overbought/Oversold Triggers (B1-B5)
# ---------------------------------------------------------------------------

def _eval_b1_rsi_overbought(indicators: dict, risk_profile: str) -> dict | None:
    """B1: RSI Overbought — RSI > 75 (risk-neutral) or > 70 (risk-averse)."""
    rsi = indicators.get("rsi_14")
    if rsi is None:
        return None

    threshold = 70 if risk_profile == "risk-averse" else 75
    if rsi > threshold:
        return {
            "id": "B1",
            "category": "Momentum",
            "priority": "MEDIUM",
            "description": f"RSI OVERBOUGHT: RSI(14) = {rsi}",
            "details": {"rsi": rsi, "threshold": threshold},
        }
    return None


def _eval_b2_rsi_oversold(indicators: dict, risk_profile: str) -> dict | None:
    """B2: RSI Oversold — RSI < 25 (risk-neutral) or < 30 (risk-averse)."""
    rsi = indicators.get("rsi_14")
    if rsi is None:
        return None

    threshold = 30 if risk_profile == "risk-averse" else 25
    if rsi < threshold:
        return {
            "id": "B2",
            "category": "Momentum",
            "priority": "MEDIUM",
            "description": f"RSI OVERSOLD: RSI(14) = {rsi}",
            "details": {"rsi": rsi, "threshold": threshold},
        }
    return None


def _eval_b3_extended_from_200d(indicators: dict, daily_df: pd.DataFrame,
                                 risk_profile: str) -> dict | None:
    """B3: Extreme Extension from 200-Day MA."""
    ma = indicators.get("moving_averages", {})
    sma_200 = ma.get("sma_200")
    if sma_200 is None:
        return None

    current_close = float(daily_df["Close"].iloc[-1])
    ma_value = sma_200["value"]
    distance_pct = (current_close - ma_value) / ma_value * 100

    threshold = 15 if risk_profile == "risk-averse" else 20
    if abs(distance_pct) > threshold:
        direction = "above" if distance_pct > 0 else "below"
        return {
            "id": "B3",
            "category": "Momentum",
            "priority": "MEDIUM",
            "description": f"EXTENDED: {distance_pct:+.1f}% from 200d MA (${ma_value})",
            "details": {
                "distance_pct": round(distance_pct, 2),
                "direction": direction,
                "threshold": threshold,
                "ma_value": ma_value,
            },
        }
    return None


def _eval_b4_zscore_extreme(indicators: dict) -> dict | None:
    """B4: Price Z-Score Extreme — |Z| > 2.0."""
    zscore = indicators.get("price_zscore")
    if zscore is None:
        return None

    if abs(zscore) > 2.0:
        label = "OVERBOUGHT" if zscore > 0 else "OVERSOLD"
        return {
            "id": "B4",
            "category": "Momentum",
            "priority": "MEDIUM",
            "description": f"Z-SCORE EXTREME: Z = {zscore} ({label})",
            "details": {"zscore": zscore, "label": label},
        }
    return None


def _classify_rs_state(rs_data: dict) -> str:
    """Classify RS state as outperforming/underperforming/mixed."""
    rs_1m = rs_data.get("1m")
    rs_3m = rs_data.get("3m")
    rs_6m = rs_data.get("6m")
    trajectory = rs_data.get("trajectory", "stable")

    if rs_1m is None or rs_3m is None or rs_6m is None:
        return "insufficient_data"

    if rs_1m > 1.0 and rs_3m > 1.0 and rs_6m > 1.0:
        if trajectory == "improving":
            return "outperforming_improving"
        return "outperforming"
    elif rs_1m < 1.0 and rs_3m < 1.0 and rs_6m < 1.0:
        return "underperforming"
    else:
        return "mixed"


def _eval_b5_rs_shift(indicators: dict,
                       prior_stock: dict | None) -> list[dict]:
    """B5: Relative Strength Breakdown / Breakout vs SPX.

    Returns a list (0-2 triggers: state change and/or trajectory shift).
    """
    triggers = []
    rs_data = indicators.get("relative_strength_vs_spx", {})
    current_state = _classify_rs_state(rs_data)

    if current_state == "insufficient_data":
        return triggers

    if prior_stock is None:
        return triggers  # First scan — baseline only

    prior_rs_state = prior_stock.get("indicators", {}).get("rs_state_vs_spx")
    if prior_rs_state is None:
        return triggers

    # State change: outperforming -> underperforming or vice versa
    was_outperforming = prior_rs_state.startswith("outperforming")
    is_outperforming = current_state.startswith("outperforming")
    was_underperforming = prior_rs_state == "underperforming"
    is_underperforming = current_state == "underperforming"

    if was_outperforming and is_underperforming:
        triggers.append({
            "id": "B5",
            "category": "Momentum",
            "priority": "HIGH",
            "description": (
                f"RS BREAKDOWN: RS vs SPX "
                f"1m={rs_data.get('1m', 'N/A')}, "
                f"3m={rs_data.get('3m', 'N/A')}, "
                f"6m={rs_data.get('6m', 'N/A')}"
            ),
            "details": {"old_state": prior_rs_state, "new_state": current_state},
        })
    elif was_underperforming and is_outperforming:
        triggers.append({
            "id": "B5",
            "category": "Momentum",
            "priority": "HIGH",
            "description": (
                f"RS BREAKOUT: RS vs SPX "
                f"1m={rs_data.get('1m', 'N/A')}, "
                f"3m={rs_data.get('3m', 'N/A')}, "
                f"6m={rs_data.get('6m', 'N/A')}"
            ),
            "details": {"old_state": prior_rs_state, "new_state": current_state},
        })

    # Trajectory shift: outperforming but decelerating
    if is_outperforming and rs_data.get("trajectory") == "deteriorating":
        prior_trajectory = prior_stock.get("indicators", {}).get("rs_trajectory_vs_spx")
        if prior_trajectory and prior_trajectory != "deteriorating":
            triggers.append({
                "id": "B5",
                "category": "Momentum",
                "priority": "MEDIUM",
                "description": "RS DETERIORATING: Still above 1.0 but decelerating",
                "details": {"trajectory": "deteriorating", "state": current_state},
            })

    return triggers


# ---------------------------------------------------------------------------
# Category C: Volume & Accumulation/Distribution Triggers (C1-C4)
# ---------------------------------------------------------------------------

def _eval_c1_volume_spike(daily_df: pd.DataFrame,
                           volume_spike_multiplier: float,
                           is_holding: bool) -> list[dict]:
    """C1: Volume Spike — 2x+ avg volume on a down/up day."""
    triggers = []
    if daily_df is None or len(daily_df) < 21:
        return triggers

    today_volume = float(daily_df["Volume"].iloc[-1])
    avg_volume_20d = float(daily_df["Volume"].iloc[-21:-1].mean())

    if avg_volume_20d == 0:
        return triggers

    ratio = today_volume / avg_volume_20d

    if ratio < volume_spike_multiplier:
        return triggers

    today_close = float(daily_df["Close"].iloc[-1])
    yesterday_close = float(daily_df["Close"].iloc[-2])
    is_down_day = today_close < yesterday_close

    if is_down_day:
        triggers.append({
            "id": "C1",
            "category": "Volume",
            "priority": "HIGH",
            "description": f"VOLUME SPIKE: {ratio:.1f}x avg volume on DOWN day",
            "details": {
                "ratio": round(ratio, 2),
                "today_volume": int(today_volume),
                "avg_volume": int(avg_volume_20d),
                "day_type": "down",
            },
        })
    elif not is_holding:
        # Up-day volume spike on watchlist — potential breakout
        triggers.append({
            "id": "C1",
            "category": "Volume",
            "priority": "LOW",
            "description": f"VOLUME SPIKE: {ratio:.1f}x avg volume on UP day",
            "details": {
                "ratio": round(ratio, 2),
                "today_volume": int(today_volume),
                "avg_volume": int(avg_volume_20d),
                "day_type": "up",
            },
        })

    return triggers


def _eval_c2_obv_divergence(indicators: dict) -> dict | None:
    """C2: OBV Divergence — price/OBV trend mismatch."""
    obv_data = indicators.get("obv")
    if obv_data is None:
        return None

    if not obv_data.get("divergence", False):
        return None

    price_trend = obv_data.get("price_trend", "?")
    obv_trend = obv_data.get("obv_trend", "?")

    # Classify divergence type
    if price_trend == "rising" and obv_trend == "falling":
        div_type = "BEARISH"
        priority = "HIGH"
    elif price_trend == "falling" and obv_trend == "rising":
        div_type = "BULLISH"
        priority = "MEDIUM"
    else:
        div_type = "MIXED"
        priority = "LOW"

    return {
        "id": "C2",
        "category": "Volume",
        "priority": priority,
        "description": f"OBV DIVERGENCE ({div_type}): Price {price_trend} but OBV {obv_trend}",
        "details": {
            "divergence_type": div_type,
            "price_trend": price_trend,
            "obv_trend": obv_trend,
        },
    }


def _eval_c3_volume_ratio_shift(indicators: dict,
                                 is_holding: bool) -> dict | None:
    """C3: Volume Ratio Shift — sellers (<0.8) or buyers (>1.3) dominating."""
    vol_ratio = indicators.get("volume_ratio")
    if vol_ratio is None:
        return None

    if is_holding and vol_ratio < 0.8:
        return {
            "id": "C3",
            "category": "Volume",
            "priority": "MEDIUM",
            "description": f"VOLUME RATIO: {vol_ratio} (SELLERS dominating)",
            "details": {"volume_ratio": vol_ratio, "signal": "sellers"},
        }
    elif not is_holding and vol_ratio > 1.3:
        return {
            "id": "C3",
            "category": "Volume",
            "priority": "MEDIUM",
            "description": f"VOLUME RATIO: {vol_ratio} (BUYERS dominating)",
            "details": {"volume_ratio": vol_ratio, "signal": "buyers"},
        }
    return None


def _eval_c4_bollinger_squeeze(indicators: dict) -> dict | None:
    """C4: Bollinger Band Squeeze — width < 10th percentile."""
    bb = indicators.get("bollinger_bands")
    if bb is None:
        return None

    width_pctl = bb.get("width_percentile")
    if width_pctl is not None and width_pctl < 10:
        return {
            "id": "C4",
            "category": "Volume",
            "priority": "LOW",
            "description": f"BB SQUEEZE: Width percentile = {width_pctl}% (expansion imminent)",
            "details": {"width_percentile": width_pctl, "current_width": bb.get("current_width")},
        }
    return None


# ---------------------------------------------------------------------------
# Category D: Valuation & Fundamental Triggers (D1-D3)
# ---------------------------------------------------------------------------

def _get_sector_pe_median(sector: str, all_ratios: dict[str, dict]) -> float:
    """Get sector P/E median from peer stocks or hardcoded fallback.

    Args:
        sector: Sector name string.
        all_ratios: Dict of ticker -> ratios dict for all scanned stocks.

    Returns:
        Sector P/E median estimate.
    """
    # Collect P/E values from stocks in the same sector
    sector_pes = []
    for ticker, ratios in all_ratios.items():
        if ratios is None:
            continue
        pe = ratios.get("trailing_pe")
        if pe is not None and pe > 0:
            sector_pes.append(pe)

    if len(sector_pes) >= 2:
        return float(np.median(sector_pes))

    # Fallback to hardcoded
    return SECTOR_PE_MEDIANS.get(sector, 20)


def _eval_d1_pe_extreme(ratios: dict | None, sector: str,
                         sector_pe_median: float) -> dict | None:
    """D1: P/E Extreme — > 50 or < 10 vs sector median."""
    if ratios is None:
        return None

    pe = ratios.get("trailing_pe")
    if pe is None or pe <= 0:
        return None

    if pe > 50 and pe > 2 * sector_pe_median:
        return {
            "id": "D1",
            "category": "Valuation",
            "priority": "LOW",
            "description": f"P/E EXTREME: {pe:.1f}x (HIGH vs sector median {sector_pe_median:.0f}x)",
            "details": {"pe": pe, "sector_median": sector_pe_median, "signal": "high"},
        }
    elif pe < 10 and pe > 0:
        return {
            "id": "D1",
            "category": "Valuation",
            "priority": "LOW",
            "description": f"P/E EXTREME: {pe:.1f}x (LOW vs sector median {sector_pe_median:.0f}x)",
            "details": {"pe": pe, "sector_median": sector_pe_median, "signal": "low"},
        }
    return None


def _eval_d2_earnings_deterioration(eps_data: pd.DataFrame | None) -> dict | None:
    """D2: Earnings Deterioration — YoY EPS decline > 25%."""
    if eps_data is None or len(eps_data) < 5:
        return None

    try:
        current_eps = float(eps_data["eps"].iloc[-1])
        year_ago_eps = float(eps_data["eps"].iloc[-5])
    except (IndexError, KeyError, ValueError):
        return None

    if abs(year_ago_eps) < 0.001:
        return None

    yoy_change_pct = (current_eps - year_ago_eps) / abs(year_ago_eps) * 100

    if yoy_change_pct < -25:
        # Check for consecutive deterioration
        consecutive = False
        if len(eps_data) >= 6:
            try:
                prev_q_eps = float(eps_data["eps"].iloc[-2])
                prev_q_yago = float(eps_data["eps"].iloc[-6])
                if abs(prev_q_yago) > 0.001:
                    prev_change = (prev_q_eps - prev_q_yago) / abs(prev_q_yago) * 100
                    consecutive = prev_change < 0
            except (IndexError, ValueError):
                pass

        desc = f"EARNINGS DETERIORATION: Q EPS ${current_eps:.2f} vs ${year_ago_eps:.2f} ({yoy_change_pct:+.1f}% YoY)"
        if consecutive:
            desc += " [2 consecutive quarters of decline]"

        return {
            "id": "D2",
            "category": "Valuation",
            "priority": "MEDIUM",
            "description": desc,
            "details": {
                "current_eps": current_eps,
                "year_ago_eps": year_ago_eps,
                "yoy_change_pct": round(yoy_change_pct, 1),
                "consecutive": consecutive,
            },
        }
    return None


def _parse_insider_transaction_type(text: str) -> str:
    """Parse insider transaction text to classify as purchase/sale/automatic/unknown."""
    if not isinstance(text, str):
        return "unknown"
    text_lower = text.lower()
    if "purchase" in text_lower or "buy" in text_lower:
        return "purchase"
    elif "automatic" in text_lower or "plan" in text_lower or "10b5" in text_lower:
        return "automatic"
    elif "sale" in text_lower or "sell" in text_lower or "sold" in text_lower:
        return "sale"
    return "unknown"


def _eval_d3_insider_activity(insider_data: pd.DataFrame | None) -> dict | None:
    """D3: Insider Activity Spike — 3+ cluster buy or $10M+ selling (90 days).

    Filters out automatic/10b5-1 transactions based on Text field parsing.
    """
    if insider_data is None or (hasattr(insider_data, 'empty') and insider_data.empty):
        return None

    # Determine date column
    date_col = None
    for col in ["Start Date", "startDate", "Date", "date"]:
        if col in insider_data.columns:
            date_col = col
            break

    # Determine text column for transaction type parsing
    text_col = None
    for col in ["Text", "text", "Transaction", "transaction"]:
        if col in insider_data.columns:
            text_col = col
            break

    # Determine value column
    value_col = None
    for col in ["Value", "value", "Shares Value", "sharesValue"]:
        if col in insider_data.columns:
            value_col = col
            break

    if text_col is None:
        return None

    # Filter to last 90 days
    cutoff_90d = datetime.now() - timedelta(days=90)
    cutoff_30d = datetime.now() - timedelta(days=30)

    filtered = insider_data.copy()
    if date_col:
        try:
            filtered[date_col] = pd.to_datetime(filtered[date_col], errors="coerce")
            filtered = filtered[filtered[date_col] >= cutoff_90d]
        except Exception:
            pass  # If date parsing fails, use all rows

    if filtered.empty:
        return None

    # Classify each transaction
    filtered = filtered.copy()
    filtered["_txn_type"] = filtered[text_col].apply(_parse_insider_transaction_type)

    # Filter out automatic/10b5-1 plan transactions
    open_market = filtered[filtered["_txn_type"] != "automatic"]

    purchases = open_market[open_market["_txn_type"] == "purchase"]
    sales = open_market[open_market["_txn_type"].isin(["sale", "unknown"])]

    # Cluster buying: 3+ distinct insiders with purchases within 30 days
    if len(purchases) >= 3:
        # Count distinct insiders
        insider_col = None
        for col in ["Insider Trading", "insider", "Insider", "Name", "name"]:
            if col in purchases.columns:
                insider_col = col
                break
        if insider_col:
            if date_col:
                recent_purchases = purchases[purchases[date_col] >= cutoff_30d]
            else:
                recent_purchases = purchases
            distinct_buyers = recent_purchases[insider_col].nunique()
            if distinct_buyers >= 3:
                total_value = 0
                if value_col and value_col in purchases.columns:
                    total_value = purchases[value_col].abs().sum()
                return {
                    "id": "D3",
                    "category": "Valuation",
                    "priority": "MEDIUM",
                    "description": f"INSIDER CLUSTER BUY: {distinct_buyers} insiders bought in 30 days (${total_value:,.0f})",
                    "details": {
                        "type": "cluster_buy",
                        "distinct_insiders": int(distinct_buyers),
                        "total_value": float(total_value),
                    },
                }

    # Heavy selling: > $10M in 90 days with zero purchases
    if len(purchases) == 0 and value_col and value_col in sales.columns:
        total_selling = float(sales[value_col].abs().sum())
        if total_selling > 10_000_000:
            return {
                "id": "D3",
                "category": "Valuation",
                "priority": "MEDIUM",
                "description": f"INSIDER HEAVY SELLING: ${total_selling:,.0f} sold, $0 purchased (past 90 days)",
                "details": {
                    "type": "heavy_selling",
                    "total_selling": total_selling,
                    "purchase_count": 0,
                },
            }

    return None


# ---------------------------------------------------------------------------
# Category E: Prior DualEdge Change Condition Triggers (E1-E2)
# ---------------------------------------------------------------------------

def _eval_e1_change_condition_met(ticker: str, indicators: dict,
                                   daily_df: pd.DataFrame,
                                   weekly_df: pd.DataFrame | None,
                                   change_conditions: list,
                                   analysis_date: str) -> list[dict]:
    """E1: Evaluate prior DualEdge change conditions.

    Supports all condition types from Section 3.3 of the addendum.
    """
    triggers = []
    if not change_conditions:
        return triggers

    current_close = float(daily_df["Close"].iloc[-1])
    today_volume = float(daily_df["Volume"].iloc[-1])
    avg_volume_20d = float(daily_df["Volume"].iloc[-21:-1].mean()) if len(daily_df) >= 22 else 0

    for cond in change_conditions:
        ctype = cond.get("type", "")
        threshold = cond.get("threshold")
        description = cond.get("description", "")
        requires_volume = cond.get("requires_volume_confirmation", False)

        fired = False

        if ctype == "price_below":
            fired = current_close < threshold

        elif ctype == "price_above":
            if current_close > threshold:
                if requires_volume:
                    fired = avg_volume_20d > 0 and today_volume > avg_volume_20d
                else:
                    fired = True

        elif ctype == "weekly_close_below":
            if weekly_df is not None and len(weekly_df) >= 1:
                weekly_close = float(weekly_df["Close"].iloc[-1])
                if weekly_close < threshold:
                    if requires_volume:
                        weekly_vol = float(weekly_df["Volume"].iloc[-1])
                        avg_weekly_vol = float(weekly_df["Volume"].iloc[-21:-1].mean()) if len(weekly_df) >= 22 else 0
                        fired = avg_weekly_vol > 0 and weekly_vol > avg_weekly_vol
                    else:
                        fired = True

        elif ctype == "weekly_close_above":
            if weekly_df is not None and len(weekly_df) >= 1:
                weekly_close = float(weekly_df["Close"].iloc[-1])
                if weekly_close > threshold:
                    if requires_volume:
                        weekly_vol = float(weekly_df["Volume"].iloc[-1])
                        avg_weekly_vol = float(weekly_df["Volume"].iloc[-21:-1].mean()) if len(weekly_df) >= 22 else 0
                        fired = avg_weekly_vol > 0 and weekly_vol > avg_weekly_vol
                    else:
                        fired = True

        elif ctype == "rs_breakdown":
            rs_data = indicators.get("relative_strength_vs_spx", {})
            timeframes = cond.get("timeframes", ["1m", "3m", "6m"])
            all_below = True
            for tf in timeframes:
                rs_val = rs_data.get(tf)
                if rs_val is None or rs_val >= threshold:
                    all_below = False
                    break
            fired = all_below

        elif ctype == "rs_breakout":
            rs_data = indicators.get("relative_strength_vs_spx", {})
            timeframes = cond.get("timeframes", ["1m", "3m", "6m"])
            all_above = True
            for tf in timeframes:
                rs_val = rs_data.get(tf)
                if rs_val is None or rs_val <= threshold:
                    all_above = False
                    break
            fired = all_above

        elif ctype == "stage_change_to":
            target_stage = cond.get("target_stage")
            weinstein = indicators.get("weinstein_stage")
            if weinstein and target_stage is not None:
                fired = weinstein["stage"] == target_stage

        elif ctype == "rsi_above":
            rsi = indicators.get("rsi_14")
            if rsi is not None:
                fired = rsi > threshold

        elif ctype == "rsi_below":
            rsi = indicators.get("rsi_14")
            if rsi is not None:
                fired = rsi < threshold

        elif ctype == "obv_divergence":
            direction = cond.get("direction")
            obv = indicators.get("obv")
            if obv and obv.get("divergence"):
                if direction == "bearish":
                    fired = obv["price_trend"] == "rising" and obv["obv_trend"] == "falling"
                elif direction == "bullish":
                    fired = obv["price_trend"] == "falling" and obv["obv_trend"] == "rising"

        if fired:
            triggers.append({
                "id": "E1",
                "category": "Prior Analysis",
                "priority": "HIGHEST",
                "description": f'CHANGE CONDITION MET: "{description}" (from {analysis_date} analysis)',
                "details": {
                    "condition_type": ctype,
                    "threshold": threshold,
                    "description": description,
                    "analysis_date": analysis_date,
                },
            })

    return triggers


def _eval_e2_analysis_staleness(ticker: str,
                                 analysis_date: str) -> dict | None:
    """E2: Analysis Staleness — > 30 days since last DualEdge run."""
    try:
        last_date = datetime.strptime(analysis_date, "%Y-%m-%d")
    except (ValueError, TypeError):
        return None

    days_since = (datetime.now() - last_date).days
    if days_since > 30:
        return {
            "id": "E2",
            "category": "Prior Analysis",
            "priority": "LOW",
            "description": f"STALE ANALYSIS: Last DualEdge run was {days_since} days ago ({analysis_date})",
            "details": {"days_since": days_since, "analysis_date": analysis_date},
        }
    return None


# ===========================================================================
# Master Trigger Evaluator
# ===========================================================================

def evaluate_triggers(ticker: str, indicators: dict, daily_df: pd.DataFrame,
                      weekly_df: pd.DataFrame | None,
                      ratios: dict | None, eps_data: pd.DataFrame | None,
                      insider_data: pd.DataFrame | None,
                      prior_stock: dict | None,
                      change_conditions: list, analysis_date: str | None,
                      risk_profile: str, is_holding: bool,
                      volume_spike_multiplier: float,
                      sector: str, sector_pe_median: float) -> list[dict]:
    """Evaluate all 18 trigger conditions for a single stock.

    Args:
        ticker: Stock ticker.
        indicators: Output from compute_all_indicators().
        daily_df: Daily OHLCV DataFrame.
        weekly_df: Weekly OHLCV DataFrame.
        ratios: Output from get_key_ratios().
        eps_data: Output from get_quarterly_eps().
        insider_data: Output from get_insider_transactions().
        prior_stock: Previous scan data for this ticker (for state change detection).
        change_conditions: From watchlist.json previous_analyses.
        analysis_date: Date of previous analysis.
        risk_profile: "risk-neutral" or "risk-averse".
        is_holding: Whether this stock is in the portfolio (non-zero shares).
        volume_spike_multiplier: From scanner_config.
        sector: Sector name.
        sector_pe_median: Sector P/E median for D1.

    Returns:
        List of trigger dicts with id, category, priority, description, details.
    """
    fired = []

    # Category A: Trend
    t = _eval_a1_weinstein_stage_change(indicators, prior_stock)
    if t:
        fired.append(t)

    t = _eval_a2_30w_ma_crossover(indicators, daily_df, prior_stock, risk_profile, is_holding)
    if t:
        fired.append(t)

    t = _eval_a3_200d_ma_crossover(indicators, daily_df, prior_stock)
    if t:
        fired.append(t)

    t = _eval_a4_ma_alignment_shift(indicators, prior_stock)
    if t:
        fired.append(t)

    # Category B: Momentum
    t = _eval_b1_rsi_overbought(indicators, risk_profile)
    if t:
        fired.append(t)

    t = _eval_b2_rsi_oversold(indicators, risk_profile)
    if t:
        fired.append(t)

    t = _eval_b3_extended_from_200d(indicators, daily_df, risk_profile)
    if t:
        fired.append(t)

    t = _eval_b4_zscore_extreme(indicators)
    if t:
        fired.append(t)

    fired.extend(_eval_b5_rs_shift(indicators, prior_stock))

    # Category C: Volume
    fired.extend(_eval_c1_volume_spike(daily_df, volume_spike_multiplier, is_holding))

    t = _eval_c2_obv_divergence(indicators)
    if t:
        fired.append(t)

    t = _eval_c3_volume_ratio_shift(indicators, is_holding)
    if t:
        fired.append(t)

    t = _eval_c4_bollinger_squeeze(indicators)
    if t:
        fired.append(t)

    # Category D: Valuation
    t = _eval_d1_pe_extreme(ratios, sector, sector_pe_median)
    if t:
        fired.append(t)

    t = _eval_d2_earnings_deterioration(eps_data)
    if t:
        fired.append(t)

    t = _eval_d3_insider_activity(insider_data)
    if t:
        fired.append(t)

    # Category E: Prior Analysis
    if change_conditions and analysis_date:
        fired.extend(_eval_e1_change_condition_met(
            ticker, indicators, daily_df, weekly_df,
            change_conditions, analysis_date))

    if analysis_date:
        t = _eval_e2_analysis_staleness(ticker, analysis_date)
        if t:
            fired.append(t)

    return fired


# ===========================================================================
# Scan Result Building (per-stock indicator snapshot for scan_data.json)
# ===========================================================================

def _build_stock_snapshot(ticker: str, indicators: dict, daily_df: pd.DataFrame,
                          ratios: dict | None) -> dict:
    """Build the indicator snapshot stored in scan_data.json for state change detection."""
    snapshot = {}

    # Weinstein stage
    weinstein = indicators.get("weinstein_stage")
    if weinstein:
        snapshot["weinstein_stage"] = weinstein["stage"]

    # Price vs key MAs (for crossover detection)
    ma = indicators.get("moving_averages", {})
    current_close = float(daily_df["Close"].iloc[-1])

    sma_30w = ma.get("sma_30w")
    if sma_30w:
        snapshot["price_above_30w_ma"] = current_close > sma_30w["value"]

    sma_200 = ma.get("sma_200")
    if sma_200:
        snapshot["price_above_200d_ma"] = current_close > sma_200["value"]

    # MA alignment
    snapshot["ma_alignment"] = _classify_ma_alignment(indicators)

    # RS state vs SPX (for B5)
    rs_spx = indicators.get("relative_strength_vs_spx", {})
    snapshot["rs_state_vs_spx"] = _classify_rs_state(rs_spx)
    snapshot["rs_trajectory_vs_spx"] = rs_spx.get("trajectory")

    # RSI
    snapshot["rsi"] = indicators.get("rsi_14")

    # Volume ratio
    snapshot["volume_ratio"] = indicators.get("volume_ratio")

    # Bollinger width percentile
    bb = indicators.get("bollinger_bands")
    if bb:
        snapshot["bollinger_width_percentile"] = bb.get("width_percentile")

    # CAN SLIM score
    canslim = indicators.get("canslim")
    if canslim:
        snapshot["canslim_score"] = canslim["score"]

    # Price Z-score
    snapshot["price_zscore"] = indicators.get("price_zscore")

    # Annualized volatility
    vol = indicators.get("annualized_volatility", {})
    snapshot["annualized_volatility"] = vol.get("6m")

    # ATR trend
    atr = indicators.get("atr")
    if atr:
        snapshot["atr_trend"] = atr.get("trend")

    # 52-week metrics
    w52 = indicators.get("week_52_metrics")
    if w52:
        snapshot["dist_from_52w_high_pct"] = w52.get("dist_from_high_pct")

    # RS vs SPX individual timeframes
    for tf in ["1m", "3m", "6m", "12m"]:
        snapshot[f"rs_vs_spx_{tf}"] = rs_spx.get(tf)

    # Distance from 30w MA and 200d MA
    if sma_30w:
        snapshot["distance_30w_ma_pct"] = round(
            (current_close - sma_30w["value"]) / sma_30w["value"] * 100, 2)
    if sma_200:
        snapshot["distance_200d_ma_pct"] = round(
            (current_close - sma_200["value"]) / sma_200["value"] * 100, 2)

    return snapshot


# ===========================================================================
# Main Scanner Entry Point
# ===========================================================================

def save_scan_results(results: dict, dashboard_md: str,
                      scan_dir: str = "scans") -> str:
    """Save scan_data.json and daily_scan.md to scans/{date}/ directory.

    Returns:
        Path to the output directory.
    """
    date_str = results["scan_date"]
    output_dir = Path(scan_dir) / date_str
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save JSON
    json_path = output_dir / "scan_data.json"
    with open(json_path, "w") as f:
        json.dump(results, f, indent=2, default=str)

    # Save dashboard markdown
    md_path = output_dir / "daily_scan.md"
    with open(md_path, "w") as f:
        f.write(dashboard_md)

    return str(output_dir)


def run_daily_scan(watchlist_path: str = "watchlist.json") -> dict:
    """Main scanner entry point.

    Steps:
    1. Load watchlist.json
    2. Pull S&P 500 data once (shared benchmark)
    3. For each ticker (holdings + watchlist): pull data, compute indicators,
       evaluate all 18 triggers
    4. Compute portfolio metrics + concentration
    5. Load prior scan for state change detection
    6. Generate dashboard + save scan_data.json

    Returns:
        Dict of scan results (same structure as scan_data.json).
    """
    start_time = time.time()

    # 1. Load watchlist
    print("Loading watchlist...")
    watchlist_data = load_watchlist(watchlist_path)
    risk_profile = watchlist_data["risk_profile"]
    config = watchlist_data["scanner_config"]
    holdings = watchlist_data["portfolio"]["holdings"]
    watchlist_tickers = watchlist_data["watchlist"]
    cash_balance = watchlist_data["portfolio"]["cash_balance"]
    previous_analyses = watchlist_data.get("previous_analyses", {})

    # Build ticker lists
    holding_tickers = [h["ticker"] for h in holdings]
    all_tickers = list(dict.fromkeys(holding_tickers + watchlist_tickers))  # deduplicated, ordered
    is_holding_map = {t: True for t in holding_tickers}
    # Zero-share holdings are treated like watchlist for trigger purposes
    for h in holdings:
        if h.get("shares", 0) == 0:
            is_holding_map[h["ticker"]] = False

    print(f"Risk profile: {risk_profile}")
    print(f"Holdings: {holding_tickers}")
    print(f"Watchlist: {watchlist_tickers}")
    print(f"Total tickers: {len(all_tickers)}")
    print()

    # 2. Load prior scan
    print("Loading prior scan...")
    prior_scan = load_prior_scan()
    prior_stocks = prior_scan.get("stocks", {}) if prior_scan else {}
    has_prior = prior_scan is not None
    print(f"  Prior scan: {'Found (' + prior_scan.get('scan_date', '?') + ')' if has_prior else 'None (first run)'}")
    print()

    # 3. Pull all data
    print("Pulling market data...")
    all_data = pull_all_data(all_tickers, config)
    print()

    # 4. Compute indicators and evaluate triggers for each stock
    print("Computing indicators and evaluating triggers...")
    stock_results = {}
    all_triggers = []
    holdings_metrics_list = []
    sector_pe_cache = {}  # sector -> list of P/Es for median calculation
    all_ratios_by_sector = {}  # sector -> {ticker: ratios}

    # First pass: collect sector P/E data
    for ticker in all_tickers:
        td = all_data[ticker]
        sector = td["sector_name"]
        if sector not in all_ratios_by_sector:
            all_ratios_by_sector[sector] = {}
        if td["ratios"]:
            all_ratios_by_sector[sector][ticker] = td["ratios"]

    # Compute sector medians
    for sector, ratios_map in all_ratios_by_sector.items():
        sector_pe_cache[sector] = _get_sector_pe_median(sector, ratios_map)

    # Second pass: compute indicators + triggers
    for ticker in all_tickers:
        td = all_data[ticker]
        daily = td["daily"]
        weekly = td["weekly"]
        spx = td["spx"]
        sector_df = td["sector_df"]

        if daily is None:
            print(f"  ⚠️ {ticker}: No daily data — skipping")
            continue

        # Compute indicators
        eps = td["eps"]
        indicators = compute_all_indicators(
            daily, weekly if weekly is not None else pd.DataFrame(),
            spx if spx is not None else pd.DataFrame(),
            sector_df if sector_df is not None else pd.DataFrame(),
            eps_data=eps,
        )

        # Holding metrics (for portfolio calculations)
        is_holding = is_holding_map.get(ticker, False)
        holding_match = next((h for h in holdings if h["ticker"] == ticker), None)

        if holding_match:
            current_price = float(daily["Close"].iloc[-1])
            yesterday_close = float(daily["Close"].iloc[-2]) if len(daily) >= 2 else current_price
            hm = compute_holding_metrics(holding_match, current_price, yesterday_close)
            holdings_metrics_list.append(hm)

        # Prior stock data for state change detection
        prior_stock = prior_stocks.get(ticker)

        # Change conditions from previous analyses
        prev_analysis = previous_analyses.get(ticker, {})
        change_conditions = prev_analysis.get("change_conditions", [])
        analysis_date = prev_analysis.get("date")

        # Sector P/E median
        sector = td["sector_name"]
        sector_pe_med = sector_pe_cache.get(sector, 20)

        # Evaluate all 18 triggers
        triggers = evaluate_triggers(
            ticker=ticker,
            indicators=indicators,
            daily_df=daily,
            weekly_df=weekly,
            ratios=td["ratios"],
            eps_data=eps,
            insider_data=td["insider"],
            prior_stock=prior_stock,
            change_conditions=change_conditions,
            analysis_date=analysis_date,
            risk_profile=risk_profile,
            is_holding=is_holding,
            volume_spike_multiplier=config["volume_spike_multiplier"],
            sector=sector,
            sector_pe_median=sector_pe_med,
        )

        # Build indicator snapshot
        snapshot = _build_stock_snapshot(ticker, indicators, daily, td["ratios"])

        current_price = float(daily["Close"].iloc[-1])
        yesterday_close = float(daily["Close"].iloc[-2]) if len(daily) >= 2 else current_price
        daily_change_pct = ((current_price - yesterday_close) / yesterday_close * 100
                            if yesterday_close != 0 else 0)

        stock_result = {
            "current_price": round(current_price, 2),
            "daily_change_pct": round(daily_change_pct, 2),
            "is_holding": is_holding,
            "indicators": snapshot,
            "triggers_fired": triggers,
        }

        # Add holding-specific fields
        if holding_match and not hm.get("is_zero_position", True):
            stock_result["pnl_pct"] = hm.get("pnl_pct")
            stock_result["weight_pct"] = None  # Computed after portfolio metrics

        stock_results[ticker] = stock_result
        all_triggers.extend([(ticker, t) for t in triggers])

        trigger_count = len(triggers)
        if trigger_count > 0:
            print(f"  {ticker}: {trigger_count} trigger(s) fired")
        else:
            print(f"  {ticker}: ✅ no triggers")

    print()

    # 5. Portfolio metrics
    print("Computing portfolio metrics...")
    sector_map_for_conc = {t: all_data[t]["sector_name"] for t in all_tickers if t in all_data}
    portfolio_metrics = compute_portfolio_metrics(holdings_metrics_list, cash_balance)
    total_value = portfolio_metrics["total_value"]

    concentration = compute_concentration(
        holdings_metrics_list, total_value, sector_map_for_conc)

    # Set weight_pct on stock results
    for ticker, weight in concentration.get("position_weights", {}).items():
        if ticker in stock_results:
            stock_results[ticker]["weight_pct"] = weight

    # Correlation
    real_holding_tickers = [h["ticker"] for h in holdings
                            if h.get("shares", 0) > 0 and h["ticker"] in all_data]
    daily_data_for_corr = {t: all_data[t]["daily"] for t in real_holding_tickers
                           if all_data[t]["daily"] is not None}
    correlation = compute_correlation_matrix(real_holding_tickers, daily_data_for_corr)

    # 6. Build results
    scan_duration = time.time() - start_time
    scan_date = datetime.now().strftime("%Y-%m-%d")

    triggered_stocks = [ticker for ticker, stock in stock_results.items()
                        if stock["triggers_fired"]]
    recommended_deep_dives = [ticker for ticker, stock in stock_results.items()
                              if any(t["priority"] == "HIGHEST" for t in stock["triggers_fired"])]

    results = {
        "scan_date": scan_date,
        "risk_profile": risk_profile,
        "scan_duration_seconds": round(scan_duration, 1),
        "stocks_scanned": len(stock_results),
        "has_prior_scan": has_prior,
        "portfolio_summary": {
            "total_value": portfolio_metrics["total_value"],
            "total_invested": portfolio_metrics["total_invested"],
            "total_pnl_dollar": portfolio_metrics["total_pnl_dollar"],
            "total_pnl_pct": portfolio_metrics["total_pnl_pct"],
            "daily_change_dollar": portfolio_metrics["daily_change_dollar"],
            "daily_change_pct": portfolio_metrics["daily_change_pct"],
            "cash_balance": cash_balance,
            "cash_allocation_pct": portfolio_metrics["cash_allocation_pct"],
            "has_positions": portfolio_metrics["has_positions"],
        },
        "stocks": stock_results,
        "concentration": {
            "position_weights": concentration["position_weights"],
            "sector_weights": concentration["sector_weights"],
            "largest_position": concentration["largest_position"],
            "top_3_weight": concentration["top_3_weight"],
            "concentration_flags": concentration["concentration_flags"],
        },
        "correlation": {
            "high_correlation_pairs": correlation["high_correlation_pairs"],
            "skipped": correlation.get("skipped", False),
        },
        "triggered_stocks": triggered_stocks,
        "recommended_deep_dives": recommended_deep_dives,
        "all_triggers": [
            {"ticker": ticker, **trigger}
            for ticker, trigger in all_triggers
        ],
        "holdings_detail": [
            {
                "ticker": hm["ticker"],
                "shares": hm["shares"],
                "current_price": hm["current_price"],
                "market_value": hm["market_value"],
                "cost_basis": hm["cost_basis"],
                "pnl_dollar": hm["pnl_dollar"],
                "pnl_pct": hm["pnl_pct"],
                "daily_change_dollar": hm["daily_change_dollar"],
                "daily_change_pct": hm["daily_change_pct"],
                "holding_days": hm["holding_days"],
                "is_zero_position": hm.get("is_zero_position", False),
            }
            for hm in holdings_metrics_list
        ],
    }

    # 7. Generate dashboard
    from src.dashboard import generate_dashboard
    dashboard_md = generate_dashboard(results, risk_profile, scan_duration)

    # 8. Save results
    print("Saving results...")
    output_dir = save_scan_results(results, dashboard_md)
    print(f"  Output: {output_dir}/")
    print(f"  Dashboard: {output_dir}/daily_scan.md")
    print(f"  Data: {output_dir}/scan_data.json")
    print()
    print(f"Scan complete in {scan_duration:.1f}s — "
          f"{len(triggered_stocks)} stocks with triggers, "
          f"{len(recommended_deep_dives)} recommended for deep dive")

    return results


# ===========================================================================
# CLI Entry Point
# ===========================================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="DualEdge Daily Signal Scanner")
    parser.add_argument("--watchlist", default="watchlist.json",
                        help="Path to watchlist.json (default: watchlist.json)")
    args = parser.parse_args()
    run_daily_scan(args.watchlist)
