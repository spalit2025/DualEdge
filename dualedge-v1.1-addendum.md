# DualEdge V1.1 — PRD Addendum: Watchlist Monitor
## Daily Signal Scanner + Triggered Deep Analysis
**Version**: 1.1
**Last Updated**: 2026-02-07
**Depends On**: DualEdge V1 PRD (PRD.md)
**Status**: Ready for Implementation

---

## 1. Feature Overview

### 1.1 What Is the Watchlist Monitor?

The Watchlist Monitor is a two-tier extension to DualEdge that adds daily portfolio surveillance without burning LLM tokens on routine checks. It reuses the existing `data_utils.py` and `indicators.py` modules from V1 to compute signals across a user-defined watchlist, then flags only the stocks that need attention.

**Tier 1 — Daily Signal Scanner**: A pure Python script (no Claude, no LLM) that runs `data_utils` + `indicators` against every stock in the watchlist. It computes 18 trigger conditions per stock and flags any that fire. Output is a markdown dashboard. Runs in ~30-60 seconds for a 20-stock watchlist. Zero token cost.

**Tier 2 — Triggered Deep Dive**: When Tier 1 flags a stock, the user runs the existing DualEdge V1 two-agent analysis on that specific ticker. No changes to V1 — Tier 2 is exactly the current system.

### 1.2 Core Value Proposition

- **Signal, not noise**: Most stocks don't change their thesis day-to-day. The scanner surfaces only the ones that do.
- **Thesis-aware monitoring**: Checks the specific "change conditions" from prior DualEdge analyses — personalized, not generic.
- **Portfolio context**: Tracks P&L, cost basis, holding period, and concentration — connects technical signals to your actual positions.
- **Zero marginal token cost**: Tier 1 uses no LLM. Only Tier 2 (existing DualEdge) consumes tokens, and only when needed.
- **100% code reuse**: Built entirely on existing `data_utils.py`, `indicators.py`, and `sector_map.py`.

### 1.3 Success Criteria

| Criteria | Target |
|----------|--------|
| Scan 20 stocks in under 60 seconds | Pure computation, no LLM |
| Detect all 18 trigger conditions accurately | Verified against manual calculation for 3 test stocks |
| Track previous DualEdge change conditions | Load from watchlist.json, check against current data |
| Produce readable daily dashboard | Markdown output with clear flags and actionable summary |
| Integrate with V1 seamlessly | Triggered deep dive runs existing DualEdge with no modifications |
| Support both risk profiles | Risk-averse triggers are stricter than risk-neutral |

---

## 2. Architecture

### 2.1 System Flow

```
watchlist.json (user-maintained)
       │
       ▼
┌──────────────────────────────────────────────┐
│       TIER 1: Daily Signal Scanner           │
│       (scanner.py — pure Python)             │
│                                              │
│  For each ticker in watchlist:               │
│  1. Pull data via data_utils.py              │
│  2. Compute indicators via indicators.py     │
│  3. Evaluate 18 trigger conditions           │
│  4. Check prior DualEdge change conditions   │
│  5. Compute portfolio metrics (if holding)   │
│                                              │
│  Output: scans/{date}/daily_scan.md          │
└──────────┬───────────────────────────────────┘
           │
           │ flags triggered?
           │
     ┌─────┴─────┐
     │ NO        │ YES
     │ Done.     │ User runs DualEdge V1
     │ Check     │ on flagged ticker(s)
     │ tomorrow. │
     └───────────┘
```

### 2.2 New Files

| File | Type | Description |
|------|------|-------------|
| `watchlist.json` | Config | User's holdings, watchlist, risk profile, prior analysis conditions |
| `src/scanner.py` | Python module | Tier 1 scanner — pulls data, computes indicators, evaluates triggers |
| `src/portfolio.py` | Python module | Portfolio-level calculations (P&L, concentration, correlation) |
| `src/dashboard.py` | Python module | Formats scan results into markdown dashboard |
| `scans/{date}/daily_scan.md` | Output | Daily dashboard output |
| `scans/{date}/scan_data.json` | Output | Machine-readable scan results (for historical tracking) |

### 2.3 Updated File System Structure

```
DualEdge/
├── CLAUDE.md
├── PRD.md
├── watchlist.json                       # NEW — user watchlist + portfolio config
├── src/
│   ├── data_utils.py                    # Existing — no changes
│   ├── indicators.py                    # Existing — no changes
│   ├── sector_map.py                    # Existing — no changes
│   ├── scanner.py                       # NEW — Tier 1 signal scanner
│   ├── portfolio.py                     # NEW — portfolio-level calculations
│   ├── dashboard.py                     # NEW — markdown dashboard formatter
│   └── prompts/                         # Existing — no changes
├── templates/
│   └── daily_scan.md                    # NEW — dashboard output template
├── analysis/                            # Existing — DualEdge V1 output
│   └── {TICKER}/
├── scans/                               # NEW — daily scan output
│   └── {YYYY-MM-DD}/
│       ├── daily_scan.md
│       └── scan_data.json
```

---

## 3. Watchlist Configuration

### 3.1 watchlist.json Schema

```json
{
  "risk_profile": "risk-neutral",
  "portfolio": {
    "cash_balance": 25000.00,
    "holdings": [
      {
        "ticker": "NVDA",
        "shares": 100,
        "cost_basis_per_share": 142.50,
        "entry_date": "2024-09-15"
      },
      {
        "ticker": "AAPL",
        "shares": 50,
        "cost_basis_per_share": 195.00,
        "entry_date": "2024-06-01"
      },
      {
        "ticker": "UNH",
        "shares": 25,
        "cost_basis_per_share": 520.00,
        "entry_date": "2025-01-10"
      }
    ]
  },
  "watchlist": ["TSLA", "AMZN", "TSM", "PLTR", "MU", "NFLX", "VRT"],
  "previous_analyses": {
    "NVDA": {
      "date": "2026-02-07",
      "risk_profile": "risk-neutral",
      "recommendation": "BUY",
      "confidence": 6,
      "decision_type": "Consensus",
      "change_conditions": [
        {
          "type": "price_below",
          "description": "Price drops below $174 (spring thesis broken)",
          "threshold": 174.00
        },
        {
          "type": "price_above",
          "description": "Price above $192.50 on volume upgrades confidence",
          "threshold": 192.50,
          "requires_volume_confirmation": true
        }
      ]
    },
    "AAPL": {
      "date": "2026-02-07",
      "risk_profile": "risk-neutral",
      "recommendation": "BUY",
      "confidence": 7,
      "decision_type": "Split Decision",
      "change_conditions": [
        {
          "type": "weekly_close_below",
          "description": "Weekly close below 30-week MA ($252.44) on above-average volume",
          "threshold": 252.44,
          "requires_volume_confirmation": true
        },
        {
          "type": "rs_breakdown",
          "description": "RS vs SPX falls below 1.0 across all timeframes",
          "threshold": 1.0,
          "timeframes": ["1m", "3m", "6m", "12m"]
        }
      ]
    }
  },
  "scanner_config": {
    "lookback_daily_months": 18,
    "lookback_weekly_years": 3,
    "volume_spike_multiplier": 2.0,
    "max_concurrent_api_calls": 5,
    "api_delay_seconds": 0.5
  }
}
```

### 3.2 Field Definitions

| Field | Required | Description |
|-------|----------|-------------|
| `risk_profile` | Yes | `"risk-neutral"` or `"risk-averse"` — determines which trigger thresholds apply |
| `portfolio.cash_balance` | No | Available cash for new positions (used in concentration calculations) |
| `portfolio.holdings` | Yes | Array of current positions with cost basis and entry date |
| `watchlist` | Yes | Array of tickers to monitor (not currently held) |
| `previous_analyses` | No | Prior DualEdge analysis results with specific change conditions |
| `scanner_config` | No | Override default scanner parameters (all have sensible defaults) |

### 3.3 Change Condition Types

These are the supported types for `previous_analyses.{ticker}.change_conditions`:

| Type | Parameters | Trigger Logic |
|------|-----------|---------------|
| `price_below` | `threshold` | Current close < threshold |
| `price_above` | `threshold`, `requires_volume_confirmation` (optional) | Current close > threshold; if volume confirmation required, today's volume > 20-day average |
| `weekly_close_below` | `threshold`, `requires_volume_confirmation` (optional) | Most recent weekly close < threshold; volume check on weekly bar |
| `weekly_close_above` | `threshold`, `requires_volume_confirmation` (optional) | Most recent weekly close > threshold |
| `rs_breakdown` | `threshold`, `timeframes` | RS vs SPX < threshold across ALL specified timeframes |
| `rs_breakout` | `threshold`, `timeframes` | RS vs SPX > threshold across ALL specified timeframes |
| `stage_change_to` | `target_stage` | Weinstein stage classification equals target (e.g., 3 or 4) |
| `rsi_above` | `threshold` | RSI(14) > threshold |
| `rsi_below` | `threshold` | RSI(14) < threshold |
| `obv_divergence` | `direction` ("bearish" or "bullish") | OBV trend diverges from price trend in specified direction |

Users populate these by extracting change conditions from DualEdge final reports. Future versions could auto-populate from `final_report.md`.

---

## 4. Tier 1: Daily Signal Scanner — Functional Requirements

### 4.1 Data Retrieval (per stock)

The scanner pulls data using existing `data_utils.py` functions. No new data sources.

| Data | Function | Used For |
|------|----------|----------|
| Daily OHLCV (18 months) | `get_ohlcv_daily(ticker)` | All technical indicators |
| Weekly OHLCV (3 years) | `get_ohlcv_weekly(ticker)` | Weinstein staging, 30-week MA |
| S&P 500 daily | `get_ohlcv_daily("^GSPC")` | Relative strength calculations |
| Sector ETF daily | via `get_benchmark_data(ticker)` | Sector-relative strength |
| Current price/volume | From most recent row of daily OHLCV | All trigger evaluations |
| Quarterly EPS | `get_quarterly_eps(ticker)` | CAN SLIM C and A criteria |
| Key ratios | `get_key_ratios(ticker)` | Valuation triggers (P/E, PEG) |

**Optimization**: Pull S&P 500 data once and reuse across all tickers. Pull each sector ETF once per sector (not per stock).

**Rate limiting**: yfinance calls should be staggered with `scanner_config.api_delay_seconds` (default 0.5s) between tickers to avoid throttling. For a 20-stock watchlist: ~10 seconds for data retrieval.

### 4.2 Indicator Computation (per stock)

The scanner calls existing `indicators.py` functions. All indicators from V1 are computed.

| Indicator | Function | Output |
|-----------|----------|--------|
| SMA 50, 150, 200-day | `compute_moving_averages()` | Current values + slopes |
| 30-week MA | `compute_moving_averages()` | Current value + slope (rising/flat/falling) |
| RSI(14) | `compute_rsi()` | Current value (0-100) |
| Bollinger Bands | `compute_bollinger_bands()` | Upper, middle, lower, width, width percentile |
| ATR(14) | `compute_atr()` | Current value, trend (increasing/decreasing) |
| OBV | `compute_obv()` | Current OBV, 20d MA, trend, divergence flag |
| RS vs S&P 500 | `compute_relative_strength()` | Ratios at 1m, 3m, 6m, 12m + trajectory |
| RS vs Sector ETF | `compute_relative_strength()` | Ratios at 1m, 3m, 6m, 12m + trajectory |
| Volume Ratio | `compute_volume_ratio()` | Up-day vol / down-day vol (60-day window) |
| 52-week High/Low | `compute_52week_metrics()` | High, low, distance from each |
| Price Z-score | `compute_price_zscore()` | Z-score (6-month lookback) |
| Weinstein Stage | `compute_weinstein_stage()` | Stage (1-4), confidence |
| CAN SLIM Score | `compute_canslim_quantitative()` | Score (0-5), per-criterion pass/fail |
| Annualized Volatility | `compute_annualized_volatility()` | Current vs 12-month average |
| Annualized Return | `compute_annualized_return()` | At 1m, 3m, 6m, 12m |

### 4.3 Trigger Conditions — Complete Specification

The scanner evaluates **18 trigger conditions** per stock. Each trigger has a specific computation, threshold, and flag behavior. Triggers are grouped into four categories.

#### Category A: Trend & Stage Triggers (4 triggers)

**A1 — Weinstein Stage Change**
- Computation: Compare current `compute_weinstein_stage()` result to the previous scan's stage classification (stored in `scan_data.json`)
- Trigger: Stage value changed from prior scan
- Flag: `⚠️ STAGE CHANGE: Stage {old} → Stage {new}`
- Priority: HIGH — stage transitions are the most important structural signals
- Special case: If no prior scan exists (first run), compute stage but don't flag as "change" — just record as baseline
- Notes: Stage 2→3 and Stage 3→4 transitions on holdings are urgent sell signals. Stage 4→1 and Stage 1→2 on watchlist are potential buy signals.

**A2 — Price vs 30-Week MA Crossover**
- Computation: `current_close` vs `30_week_ma` (from `compute_moving_averages()`)
- Previous state: Price was above/below 30w MA on prior scan
- Trigger: Crossover detected — price was above, now below (or vice versa)
- Flag: `⚠️ 30W MA CROSS: Price crossed {BELOW/ABOVE} 30-week MA (${ma_value})`
- Risk-averse modifier: If risk-averse AND cross is downward on a holding → upgrade to `🔴 URGENT`
- Notes: For first scan, compare current close to 30w MA directly; flag if within 2% (near MA)

**A3 — Price vs 200-Day MA Crossover**
- Computation: `current_close` vs `sma_200` (from `compute_moving_averages()`)
- Previous state: Price was above/below 200d MA on prior scan
- Trigger: Crossover detected
- Flag: `⚠️ 200D MA CROSS: Price crossed {BELOW/ABOVE} 200-day MA (${ma_value})`
- Notes: 200d MA crossover is a widely followed institutional signal. Combined with volume, it's highly significant.

**A4 — MA Alignment Shift**
- Computation: Check ordering of 50d, 150d, 200d SMAs
- Bullish alignment: 50d > 150d > 200d AND all three slopes positive
- Bearish alignment: 50d < 150d < 200d AND all three slopes negative
- Previous state: Prior scan's alignment classification
- Trigger: Alignment changed (e.g., bullish → mixed, mixed → bearish)
- Flag: `⚠️ MA ALIGNMENT: {old} → {new} (50d=${v}, 150d=${v}, 200d=${v})`

#### Category B: Momentum & Overbought/Oversold Triggers (5 triggers)

**B1 — RSI Overbought**
- Computation: `compute_rsi(daily_df, period=14)`
- Risk-neutral threshold: RSI > 75
- Risk-averse threshold: RSI > 70
- Trigger: RSI crosses above threshold
- Flag: `⚠️ RSI OVERBOUGHT: RSI(14) = {value}`
- Notes: On holdings, this is a potential profit-taking signal. On watchlist, avoid new entry.

**B2 — RSI Oversold**
- Computation: `compute_rsi(daily_df, period=14)`
- Risk-neutral threshold: RSI < 25
- Risk-averse threshold: RSI < 30
- Trigger: RSI crosses below threshold
- Flag: `⚠️ RSI OVERSOLD: RSI(14) = {value}`
- Notes: On watchlist, this is a potential entry signal (mean reversion). On holdings, monitor for further deterioration.

**B3 — Extreme Extension from 200-Day MA**
- Computation: `distance_pct = (current_close - sma_200) / sma_200 * 100`
- Risk-neutral threshold: |distance| > 20%
- Risk-averse threshold: |distance| > 15%
- Trigger: Distance exceeds threshold (either direction)
- Flag: `⚠️ EXTENDED: {distance_pct}% from 200d MA (${sma_200})`
- Directional note: If positive (above MA), flag as mean reversion risk. If negative (below MA), flag as potential oversold opportunity.

**B4 — Price Z-Score Extreme**
- Computation: `compute_price_zscore(daily_df, lookback=126)` (6-month)
- Threshold: |Z| > 2.0 (same for both risk profiles)
- Trigger: Z-score exceeds ±2.0
- Flag: `⚠️ Z-SCORE EXTREME: Z = {value} ({OVERBOUGHT/OVERSOLD})`
- Notes: Z > 2.0 means price is 2 standard deviations above 6-month mean. Combined with RSI overbought, very high mean-reversion probability.

**B5 — Relative Strength Breakdown / Breakout**
- Computation: `compute_relative_strength(daily_df, spx_df)` at 1m, 3m, 6m, 12m
- Breakdown trigger: RS < 1.0 at ALL of 1m, 3m, 6m (not 12m — that's lagging)
- Breakout trigger: RS > 1.0 at ALL of 1m, 3m, 6m AND RS improving (3m > 6m)
- Previous state: Prior scan's RS classification
- Trigger: State changed (was outperforming, now underperforming, or vice versa)
- Flag: `⚠️ RS {BREAKDOWN/BREAKOUT}: RS vs SPX 1m={v}, 3m={v}, 6m={v}`
- RS trajectory: Also flag if trajectory shifted from "improving" to "deteriorating" (even if still > 1.0): `⚠️ RS DETERIORATING: Still above 1.0 but decelerating`

#### Category C: Volume & Accumulation/Distribution Triggers (4 triggers)

**C1 — Volume Spike**
- Computation: Compare today's volume to 20-day average volume
- Formula: `volume_ratio = today_volume / sma_20_volume`
- Threshold: `volume_ratio > scanner_config.volume_spike_multiplier` (default 2.0x)
- Trigger: Volume spike on a DOWN day (close < prior close) — this is the concerning signal
- Flag: `⚠️ VOLUME SPIKE: {ratio}x avg volume on DOWN day`
- Also flag (lower priority): Volume spike on UP day for watchlist stocks (potential breakout)
- Flag: `💡 VOLUME SPIKE: {ratio}x avg volume on UP day`

**C2 — OBV Divergence**
- Computation: `compute_obv(daily_df)` — extract `divergence_flag` and `divergence_type`
- Bearish divergence: Price making higher highs, OBV making lower highs (or flat)
- Bullish divergence: Price making lower lows, OBV making higher lows (or flat)
- Trigger: Divergence detected (from `compute_obv` output)
- Flag: `⚠️ OBV DIVERGENCE ({BEARISH/BULLISH}): Price {direction} but OBV {direction}`
- Priority: HIGH for bearish divergence on holdings (distribution signal)

**C3 — Volume Ratio Shift**
- Computation: `compute_volume_ratio(daily_df, window=60)`
- Formula: `avg_volume_up_days / avg_volume_down_days`
- Trigger for holdings: Volume ratio drops below 0.8 (sellers dominating)
- Trigger for watchlist: Volume ratio rises above 1.3 (buyers dominating, potential entry)
- Flag: `⚠️ VOLUME RATIO: {value} ({SELLERS/BUYERS} dominating)`

**C4 — Bollinger Band Squeeze**
- Computation: `compute_bollinger_bands(daily_df)` — extract `width_percentile`
- Trigger: `width_percentile < 10` (Bollinger Bands are in bottom 10% of 12-month range)
- Flag: `💡 BB SQUEEZE: Width percentile = {value}% (expansion imminent)`
- Notes: Squeeze signals imminent volatility expansion but not direction. Combined with other signals (stage, OBV) to infer likely direction.

#### Category D: Valuation & Fundamental Triggers (3 triggers)

These use `get_key_ratios()` — lighter than full fundamental analysis but catch major valuation shifts.

**D1 — P/E Extreme**
- Computation: `get_key_ratios(ticker)["trailing_pe"]`
- Trigger (overvalued): P/E > 50 AND P/E > 2x sector median (flag as expensive)
- Trigger (undervalued): P/E < 10 AND P/E > 0 (flag as potentially cheap; exclude negative P/E)
- Sector median: Compute median P/E across all holdings + watchlist in same sector; if only one stock in sector, use hardcoded sector median estimates:

| Sector | Typical P/E Range | Median Estimate |
|--------|------------------|----------------|
| Technology | 20-35 | 28 |
| Healthcare | 18-30 | 22 |
| Financials | 10-18 | 14 |
| Consumer Discretionary | 18-30 | 22 |
| Consumer Staples | 18-25 | 20 |
| Industrials | 16-24 | 20 |
| Energy | 8-16 | 12 |
| Materials | 12-20 | 16 |
| Utilities | 14-22 | 18 |
| Real Estate | 30-50 | 38 |
| Communication Services | 16-25 | 20 |

- Flag: `⚠️ P/E EXTREME: {value}x ({HIGH/LOW} vs sector median {median}x)`

**D2 — Earnings Deterioration**
- Computation: `get_quarterly_eps(ticker)` — compare most recent quarter to same quarter prior year
- YoY EPS change: `(eps_current_q - eps_same_q_last_year) / abs(eps_same_q_last_year) * 100`
- Trigger: YoY EPS decline > 25% (significant deterioration)
- Also trigger: Two consecutive quarters of YoY EPS decline (trend confirmation)
- Flag: `⚠️ EARNINGS DETERIORATION: Q EPS ${current} vs ${prior_year} ({change}% YoY)`
- Notes: This catches the CAN SLIM "C" criterion failure at the scanner level.

**D3 — Insider Activity Spike**
- Computation: `get_insider_transactions(ticker)` — analyze last 90 days
- Cluster buying trigger: 3+ distinct insiders with open-market purchases within 30 days
- Heavy selling trigger: Total insider sales > $10M in past 90 days with zero purchases
- Flag (buying): `💡 INSIDER CLUSTER BUY: {count} insiders bought in {days} days (${total})`
- Flag (selling): `⚠️ INSIDER HEAVY SELLING: ${total} sold, $0 purchased (past 90 days)`
- Notes: Filter out automatic/10b5-1 plan transactions where detectable (transaction code "S" = open market sale, "P" = open market purchase; "A" = automatic/plan — exclude A from analysis)

#### Category E: Prior DualEdge Change Condition Triggers (2 triggers)

**E1 — Change Condition Met**
- Computation: Load `previous_analyses.{ticker}.change_conditions` from watchlist.json
- For each change condition, evaluate using the type-specific logic defined in Section 3.3
- Trigger: Any change condition evaluates to TRUE
- Flag: `🔴 CHANGE CONDITION MET: "{description}" (from {date} analysis)`
- Priority: HIGHEST — this means a prior DualEdge analysis explicitly identified this as the trigger for re-evaluation
- Action: Recommend full DualEdge re-analysis

**E2 — Analysis Staleness**
- Computation: Compare `previous_analyses.{ticker}.date` to current date
- Trigger: Prior analysis is older than 30 days
- Flag: `💡 STALE ANALYSIS: Last DualEdge run was {days} days ago ({date})`
- Notes: Not urgent, but helps maintain freshness of the recommendation base.

### 4.4 Trigger Summary Table

| ID | Trigger | Category | Threshold (Risk-Neutral) | Threshold (Risk-Averse) | Priority |
|----|---------|----------|-------------------------|------------------------|----------|
| A1 | Weinstein Stage Change | Trend | Stage value changed | Same | HIGH |
| A2 | 30-Week MA Crossover | Trend | Price crosses MA | Same + URGENT if holding | HIGH |
| A3 | 200-Day MA Crossover | Trend | Price crosses MA | Same | HIGH |
| A4 | MA Alignment Shift | Trend | 50/150/200 order changed | Same | MEDIUM |
| B1 | RSI Overbought | Momentum | RSI > 75 | RSI > 70 | MEDIUM |
| B2 | RSI Oversold | Momentum | RSI < 25 | RSI < 30 | MEDIUM |
| B3 | Extended from 200d MA | Momentum | \|dist\| > 20% | \|dist\| > 15% | MEDIUM |
| B4 | Price Z-Score Extreme | Momentum | \|Z\| > 2.0 | Same | MEDIUM |
| B5 | RS Breakdown/Breakout | Momentum | RS state changed | Same | HIGH |
| C1 | Volume Spike | Volume | 2x avg on down day | Same | HIGH |
| C2 | OBV Divergence | Volume | Divergence detected | Same | HIGH |
| C3 | Volume Ratio Shift | Volume | < 0.8 or > 1.3 | Same | MEDIUM |
| C4 | Bollinger Band Squeeze | Volume | Width < 10th pctl | Same | LOW |
| D1 | P/E Extreme | Valuation | > 50 or < 10 | Same | LOW |
| D2 | Earnings Deterioration | Valuation | YoY EPS decline > 25% | Same | MEDIUM |
| D3 | Insider Activity Spike | Valuation | 3+ cluster buy or $10M+ selling | Same | MEDIUM |
| E1 | Change Condition Met | Prior Analysis | Condition evaluates TRUE | Same | HIGHEST |
| E2 | Analysis Staleness | Prior Analysis | > 30 days | Same | LOW |

### 4.5 Risk-Profile-Adjusted Thresholds Summary

All threshold differences between risk profiles in one place:

| Trigger | Risk-Neutral | Risk-Averse | Why |
|---------|-------------|-------------|-----|
| B1 RSI Overbought | > 75 | > 70 | Risk-averse cuts earlier at standard overbought level |
| B2 RSI Oversold | < 25 | < 30 | Risk-averse flags at standard oversold level |
| B3 Extension from 200d MA | > 20% | > 15% | Risk-averse flags extension sooner |
| A2 30w MA Cross (holding) | ⚠️ flag | 🔴 URGENT | Risk-averse treats any MA cross on a holding as urgent |

All other triggers use identical thresholds. The risk profile mainly affects urgency classification, not whether a trigger fires.

---

## 5. Portfolio-Level Calculations

### 5.1 Per-Holding Metrics (`portfolio.py`)

Computed for each stock in `portfolio.holdings`:

| Metric | Formula | Notes |
|--------|---------|-------|
| Current Market Value | `shares × current_close` | From latest OHLCV |
| Total Cost Basis | `shares × cost_basis_per_share` | From watchlist.json |
| Unrealized P&L ($) | `current_value - total_cost_basis` | |
| Unrealized P&L (%) | `(current_value - total_cost_basis) / total_cost_basis × 100` | |
| Holding Period (days) | `current_date - entry_date` | From watchlist.json |
| Daily Change ($) | `shares × (today_close - yesterday_close)` | |
| Daily Change (%) | `(today_close - yesterday_close) / yesterday_close × 100` | |

### 5.2 Portfolio-Level Metrics

| Metric | Formula | Notes |
|--------|---------|-------|
| Total Portfolio Value | `sum(all holding market values) + cash_balance` | |
| Total Invested | `sum(all holding cost bases)` | |
| Total Unrealized P&L ($) | `sum(all holding P&L)` | |
| Total Unrealized P&L (%) | `total_unrealized_pnl / total_invested × 100` | |
| Cash Allocation (%) | `cash_balance / total_portfolio_value × 100` | |
| Daily Portfolio Change ($) | `sum(all holding daily changes)` | |
| Daily Portfolio Change (%) | `daily_change / (total_portfolio_value - daily_change) × 100` | |

### 5.3 Concentration Analysis

| Metric | Formula | Notes |
|--------|---------|-------|
| Position Weight (%) | `holding_value / total_portfolio_value × 100` | Per holding |
| Largest Position | `max(position_weights)` | Flag if > 25% |
| Sector Concentration | Group holdings by sector, sum weights | Flag if any sector > 40% |
| Top 3 Concentration | Sum of 3 largest position weights | Flag if > 60% |

**Concentration flags:**
- `⚠️ CONCENTRATION: {ticker} is {weight}% of portfolio (>25%)` — single stock risk
- `⚠️ SECTOR CONCENTRATION: {sector} is {weight}% of portfolio (>40%)` — sector risk
- `⚠️ TOP-HEAVY: Top 3 positions = {weight}% of portfolio (>60%)` — diversification risk

### 5.4 Correlation Risk (Optional — Compute if < 15 Holdings)

- Pull 6-month daily returns for all holdings
- Compute pairwise Pearson correlation matrix
- Flag any pair with correlation > 0.85: `💡 HIGH CORRELATION: {A} and {B} (r={value}) — limited diversification benefit`
- Note: This uses numpy — no new dependencies required.

```python
import numpy as np
# returns_matrix: DataFrame with columns = tickers, rows = daily returns
corr_matrix = returns_matrix.corr()
for i in range(len(tickers)):
    for j in range(i+1, len(tickers)):
        if corr_matrix.iloc[i, j] > 0.85:
            flag(f"HIGH CORRELATION: {tickers[i]} and {tickers[j]}")
```

---

## 6. Dashboard Output Format

### 6.1 Daily Scan Dashboard (`scans/{date}/daily_scan.md`)

```markdown
# DualEdge Daily Scan — {YYYY-MM-DD}
**Risk Profile**: {risk_profile}
**Scan Time**: {HH:MM:SS} | **Stocks Scanned**: {count}

---

## PORTFOLIO SUMMARY
| Metric | Value |
|--------|-------|
| Total Value | ${total_value} |
| Daily Change | ${daily_change} ({daily_change_pct}%) |
| Unrealized P&L | ${total_pnl} ({total_pnl_pct}%) |
| Cash | ${cash} ({cash_pct}%) |

## TRIGGERED ALERTS ({count})
{alerts sorted by priority: 🔴 HIGHEST → ⚠️ HIGH → ⚠️ MEDIUM → 💡 LOW}

### 🔴 CRITICAL
- **NVDA**: CHANGE CONDITION MET — "Price drops below $174" (from 2026-02-07 analysis)
  → **Action: Run full DualEdge analysis on NVDA**

### ⚠️ WARNING
- **AAPL**: RSI OVERBOUGHT — RSI(14) = 72.3
- **PLTR**: EXTENDED — 22.1% above 200d MA ($48.32)
- **TSLA**: VOLUME SPIKE — 2.4x avg volume on DOWN day

### 💡 INFORMATIONAL
- **MU**: BB SQUEEZE — Width percentile = 8% (expansion imminent)
- **UNH**: STALE ANALYSIS — Last DualEdge run was 35 days ago (2026-01-03)

---

## HOLDINGS DETAIL
| Ticker | Price | Daily Δ | P&L | Weight | Stage | RSI | vs 30w MA | RS vs SPX | Flags |
|--------|-------|---------|-----|--------|-------|-----|-----------|-----------|-------|
| NVDA | $168.50 | -2.1% | +18.2% | 32.1% | 3 | 48.2 | AT MA | 0.94 ↓ | 🔴 CHANGE COND |
| AAPL | $280.15 | +0.4% | +43.7% | 26.8% | 2 | 72.3 | +10.9% | 1.07 | ⚠️ RSI |
| UNH | $562.30 | +0.8% | +8.1% | 26.8% | 2 | 55.3 | +6.1% | 1.12 ↑ | ✅ |

**Concentration**: NVDA 32.1% (>25% ⚠️) | Top 3 = 85.7% (>60% ⚠️) | Tech 58.9% (>40% ⚠️)

## WATCHLIST
| Ticker | Price | Daily Δ | Stage | RSI | vs 30w MA | RS vs SPX | CAN SLIM | Flags |
|--------|-------|---------|-------|-----|-----------|-----------|----------|-------|
| TSLA | $398.20 | -3.2% | 3 | 39.1 | -2.1% | 0.88 ↓ | 2/5 | ⚠️ VOL SPIKE |
| AMZN | $228.40 | +1.1% | 2 | 62.1 | +8.3% | 1.15 ↑ | 3/5 | ✅ |
| TSM | $198.70 | +0.5% | 2 | 58.7 | +5.4% | 1.08 | 3/5 | ✅ |
| PLTR | $82.60 | +2.4% | 2 | 74.1 | +18.2% | 1.31 ↑ | 4/5 | ⚠️ EXTENDED |
| MU | $97.30 | -0.3% | 1 | 44.2 | -1.2% | 0.92 ↓ | 1/5 | 💡 SQUEEZE |
| NFLX | $1012 | +0.7% | 2 | 61.8 | +7.4% | 1.22 ↑ | 4/5 | ✅ |
| VRT | $142.80 | +1.8% | 2 | 66.3 | +12.1% | 1.18 ↑ | 3/5 | ✅ |

## RECOMMENDED ACTIONS
1. **Run DualEdge on NVDA** — change condition triggered (price below $174 threshold)
2. **Review AAPL position** — RSI approaching overbought; consider profit-taking rules
3. **Monitor PLTR** — extended but strong; wait for pullback or breakout for entry
4. **Address concentration risk** — portfolio is top-heavy and tech-concentrated

---
*Scan computed in {seconds}s using {api_calls} API calls. No LLM tokens consumed.*
*Next scan: {tomorrow_date}*
```

### 6.2 Machine-Readable Output (`scans/{date}/scan_data.json`)

```json
{
  "scan_date": "2026-02-08",
  "risk_profile": "risk-neutral",
  "scan_duration_seconds": 34.2,
  "portfolio_summary": {
    "total_value": 52430.00,
    "daily_change_pct": -0.31,
    "unrealized_pnl_pct": 24.8,
    "cash_pct": 47.6
  },
  "stocks": {
    "NVDA": {
      "current_price": 168.50,
      "daily_change_pct": -2.1,
      "is_holding": true,
      "pnl_pct": 18.2,
      "weight_pct": 32.1,
      "indicators": {
        "weinstein_stage": 3,
        "rsi": 48.2,
        "distance_30w_ma_pct": 0.3,
        "rs_vs_spx_6m": 0.94,
        "rs_trajectory": "deteriorating",
        "obv_trend": "falling",
        "volume_ratio": 0.88,
        "canslim_score": 2,
        "price_zscore": -0.4,
        "annualized_volatility": 0.52,
        "bollinger_width_percentile": 45,
        "atr_trend": "increasing"
      },
      "triggers_fired": [
        {
          "id": "E1",
          "priority": "HIGHEST",
          "description": "CHANGE CONDITION MET: Price drops below $174 (from 2026-02-07 analysis)"
        }
      ]
    }
  },
  "concentration": {
    "largest_position": {"ticker": "NVDA", "weight": 32.1},
    "top_3_weight": 85.7,
    "sector_weights": {"Technology": 58.9, "Healthcare": 26.8}
  },
  "triggered_stocks": ["NVDA", "AAPL", "PLTR", "TSLA", "MU", "UNH"],
  "recommended_deep_dives": ["NVDA"]
}
```

This JSON is saved for historical comparison. Subsequent scans can diff against it to detect state changes (e.g., stage transitions, RS crossovers).

---

## 7. Implementation Specification

### 7.1 `src/scanner.py` — Main Entry Point

```python
def run_daily_scan(watchlist_path: str = "watchlist.json") -> dict:
    """Main scanner entry point.

    Steps:
    1. Load watchlist.json
    2. Pull S&P 500 data once (shared benchmark)
    3. For each ticker (holdings + watchlist):
       a. Pull data via data_utils
       b. Compute all indicators via indicators.py
       c. Compute portfolio metrics (if holding)
       d. Evaluate all 18 trigger conditions
       e. Check prior DualEdge change conditions
    4. Compute portfolio-level metrics
    5. Compute concentration analysis
    6. Compute correlation matrix (if < 15 holdings)
    7. Load prior scan from scan_data.json (if exists) for state change detection
    8. Generate dashboard via dashboard.py
    9. Save scan_data.json for next run's comparison

    Returns: dict of scan results (same structure as scan_data.json)
    """

def evaluate_triggers(ticker: str, indicators: dict, ratios: dict,
                      eps_data, insider_data, prior_scan: dict | None,
                      change_conditions: list, risk_profile: str,
                      is_holding: bool) -> list[dict]:
    """Evaluate all 18 trigger conditions for a single stock.

    Args:
        ticker: Stock ticker
        indicators: Output from compute_all_indicators()
        ratios: Output from get_key_ratios()
        eps_data: Output from get_quarterly_eps()
        insider_data: Output from get_insider_transactions()
        prior_scan: Previous scan data for this ticker (for state change detection)
        change_conditions: From watchlist.json previous_analyses
        risk_profile: "risk-neutral" or "risk-averse"
        is_holding: Whether this stock is in the portfolio

    Returns: List of trigger dicts with id, priority, description, category
    """

def load_prior_scan(scan_dir: str = "scans") -> dict | None:
    """Load the most recent scan_data.json from scans/ directory.
    Returns None if no prior scan exists."""

def save_scan_results(results: dict, scan_dir: str = "scans") -> str:
    """Save scan_data.json and daily_scan.md to scans/{date}/ directory.
    Returns path to the output directory."""
```

### 7.2 `src/portfolio.py` — Portfolio Calculations

```python
def compute_holding_metrics(holding: dict, current_price: float,
                           yesterday_close: float) -> dict:
    """Compute per-holding metrics: market value, P&L, daily change, holding period.

    Args:
        holding: Dict from watchlist.json (ticker, shares, cost_basis_per_share, entry_date)
        current_price: Latest close price
        yesterday_close: Prior day close price

    Returns: Dict with market_value, cost_basis, pnl_dollar, pnl_pct,
             daily_change_dollar, daily_change_pct, holding_days
    """

def compute_portfolio_metrics(holdings_metrics: list[dict],
                              cash_balance: float) -> dict:
    """Compute portfolio-level aggregates: total value, total P&L, daily change.

    Returns: Dict with total_value, total_invested, total_pnl_dollar,
             total_pnl_pct, cash_allocation_pct, daily_change_dollar, daily_change_pct
    """

def compute_concentration(holdings_metrics: list[dict],
                          total_portfolio_value: float,
                          sector_map: dict) -> dict:
    """Compute position weights, sector concentration, top-3 concentration.

    Args:
        holdings_metrics: List of per-holding metrics (includes ticker, market_value)
        total_portfolio_value: From compute_portfolio_metrics
        sector_map: Dict of ticker → sector (looked up from yfinance)

    Returns: Dict with position_weights, sector_weights, largest_position,
             top_3_weight, concentration_flags (list of warning strings)
    """

def compute_correlation_matrix(tickers: list[str],
                               daily_data: dict[str, pd.DataFrame]) -> dict:
    """Compute pairwise correlation of daily returns.

    Args:
        tickers: List of holding tickers
        daily_data: Dict of ticker → daily OHLCV DataFrame (already pulled)

    Returns: Dict with correlation_matrix (as nested dict), high_correlation_pairs
             (list of tuples where r > 0.85)
    """
```

### 7.3 `src/dashboard.py` — Output Formatting

```python
def generate_dashboard(scan_results: dict, risk_profile: str,
                       scan_duration: float) -> str:
    """Generate markdown dashboard from scan results.

    Returns: Complete markdown string for daily_scan.md
    """

def format_holdings_table(holdings: list[dict]) -> str:
    """Format holdings section of dashboard with indicators and flags."""

def format_watchlist_table(watchlist: list[dict]) -> str:
    """Format watchlist section of dashboard."""

def format_alerts(triggers: list[dict]) -> str:
    """Format triggered alerts section, grouped by priority."""

def format_recommended_actions(triggers: list[dict],
                                concentration: dict) -> str:
    """Generate actionable recommendations based on triggers and concentration."""

def format_portfolio_summary(portfolio_metrics: dict) -> str:
    """Format the portfolio summary box at top of dashboard."""
```

---

## 8. Execution

### 8.1 Running the Scanner

From the DualEdge project root:

```bash
# Run daily scan
python src/scanner.py

# Or with explicit watchlist path
python src/scanner.py --watchlist watchlist.json

# Output location
cat scans/2026-02-08/daily_scan.md
```

### 8.2 Following Up on Triggers

When the scanner recommends a deep dive:

```bash
# Start Claude Code and run full DualEdge analysis
claude
> Run DualEdge analysis for NVDA with risk-neutral risk profile.
```

This runs the existing V1 system with no modifications.

### 8.3 Updating watchlist.json After a DualEdge Run

After running a full DualEdge analysis, manually update `previous_analyses` in `watchlist.json` with the new recommendation and change conditions from the `final_report.md`. Future versions could automate this.

---

## 9. Non-Functional Requirements

### 9.1 Performance

| Requirement | Target |
|------------|--------|
| 20-stock scan | < 60 seconds |
| Per-stock data pull | < 2 seconds (yfinance) |
| Per-stock indicator computation | < 0.5 seconds |
| Per-stock trigger evaluation | < 0.1 seconds |
| Dashboard generation | < 1 second |
| Token cost | Zero (pure Python) |

### 9.2 Reliability

| Scenario | Handling |
|----------|---------|
| yfinance timeout on one ticker | Log warning, skip ticker, continue with rest |
| Missing quarterly EPS data | Skip D2 (Earnings Deterioration) for that ticker, note in dashboard |
| No prior scan exists | Skip state-change triggers (A1, A2, A3, A4, B5), compute baselines only |
| watchlist.json missing or malformed | Exit with clear error message and schema example |
| Insider data unavailable | Skip D3 for that ticker, note in dashboard |
| Weekend/holiday (market closed) | Use most recent trading day's data; note data date in dashboard |

### 9.3 Data Freshness

Scanner should be run after market close (4:00 PM ET) for complete daily data. If run during market hours, note that data is intraday and may change by close.

---

## 10. Implementation Phases

### Phase A: Portfolio Module (`src/portfolio.py`) — 2-3 hours
- Implement all per-holding and portfolio-level calculations
- Implement concentration analysis
- Implement correlation matrix
- Test with sample watchlist.json

### Phase B: Scanner Core (`src/scanner.py`) — 4-5 hours
- Implement watchlist.json loader with validation
- Implement all 18 trigger conditions (most complex phase)
- Implement prior scan loading and state change detection
- Test each trigger category independently with known data

### Phase C: Dashboard Formatter (`src/dashboard.py`) — 2-3 hours
- Implement markdown template generation
- Implement all table formatters
- Implement alert grouping and priority sorting
- Implement recommended actions logic

### Phase D: Integration Testing — 1-2 hours
- Run full scan against real watchlist with 5-10 stocks
- Verify all trigger conditions produce correct flags
- Verify dashboard renders cleanly
- Run scan twice to verify state change detection works
- Test with both risk profiles

**Total estimated effort**: 9-13 hours

---

## 11. Dependencies

No new Python packages required. V1.1 uses only:
- `yfinance` (existing)
- `pandas` (existing)
- `numpy` (existing)
- `requests` (existing)
- `json` (standard library)
- `datetime` (standard library)
- `os` / `pathlib` (standard library)

---

## 12. Out of Scope for V1.1

| Feature | Reason | Target Version |
|---------|--------|---------------|
| Auto-populate change conditions from final_report.md | Requires NLP parsing; manual is fine for V1.1 | V1.2 |
| Email/Slack notifications on triggers | Keep it simple — check dashboard manually | V1.2 |
| Historical scan comparison dashboard | scan_data.json supports it; just not built yet | V1.2 |
| Intraday scanning | Focus on end-of-day signals | V2 |
| Options chain analysis | Separate product concern | V2 |
| News/sentiment triggers | Would require paid API or web scraping | V2 |
| Automated DualEdge triggering | Keep human in the loop for V1.1 | V2 |
| Portfolio optimization / rebalancing suggestions | DualEdge is analysis, not portfolio management | V2 |
| Multi-portfolio support | Single portfolio sufficient for personal use | V2 |
