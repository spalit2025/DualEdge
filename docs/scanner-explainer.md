# How scanner.py Works

A technical explainer for the DualEdge Daily Signal Scanner.

---

## 1. What the Scanner Does

The DualEdge scanner is a daily surveillance tool that monitors a portfolio and watchlist of stocks for changes that demand attention. It pulls live market data, computes 14 technical indicators for every stock, evaluates 18 trigger conditions, calculates portfolio-level risk metrics, and outputs a markdown dashboard with prioritized alerts. The entire process runs in under two minutes for a 25-stock universe.

The scanner's core design principle is **zero LLM tokens**. It is pure Python computation, reusing the same `data_utils.py` and `indicators.py` modules that power the full DualEdge dual-agent analysis. This makes it cheap to run daily. When the scanner flags something worth investigating, *that* is when you deploy the full DualEdge deep dive (which does consume LLM tokens through two AI analyst agents). The scanner is Tier 1; the agents are Tier 2.

---

## 2. Inputs

### watchlist.json

The scanner's configuration file. It defines everything the scanner needs to know about what to monitor and how.

**Schema:**

| Field | Type | Description |
|-------|------|-------------|
| `risk_profile` | `"risk-neutral"` or `"risk-averse"` | Controls trigger thresholds for RSI, extension, and MA crossover sensitivity |
| `portfolio.holdings` | Array of objects | Each holding has `ticker`, `shares`, `cost_basis_per_share`, `entry_date` |
| `portfolio.cash_balance` | Number | Cash position for portfolio value calculation |
| `watchlist` | Array of strings | Ticker symbols to monitor (not currently held) |
| `previous_analyses` | Object | Keyed by ticker, contains `date`, `recommendation`, `confidence`, `change_conditions` from prior DualEdge runs |
| `scanner_config` | Object | Tuning knobs: `lookback_daily_months` (default 18), `lookback_weekly_years` (default 3), `volume_spike_multiplier` (default 2.0), `api_delay_seconds` (default 0.5) |

The `previous_analyses` section is what connects the scanner to the full DualEdge system. When a DualEdge deep dive produces a recommendation with explicit change conditions (e.g., "this BUY becomes a SELL if price drops below $174"), those conditions are stored here and the scanner evaluates them on every run.

Zero-share holdings are a supported pattern. They appear in the holdings array but are treated like watchlist stocks for trigger evaluation purposes (e.g., volume spike on an up day is flagged as a potential entry, not a concern).

### Prior Scan Data (scan_data.json)

Every scan saves a `scan_data.json` file in `scans/{YYYY-MM-DD}/`. This file contains a per-stock snapshot of indicator values at scan time: Weinstein stage, price position relative to key moving averages, MA alignment classification, relative strength state, RSI, volume ratio, and more.

On the next run, the scanner loads the most recent `scan_data.json` and compares current values against the prior snapshot. This is how state-change triggers work -- they fire only when a value *transitions* (e.g., price crosses below the 30-week MA), not when a value is simply at a level. Without a prior scan, state-change triggers cannot fire; the first run establishes baselines only.

---

## 3. Data Flow

Here is the step-by-step execution path through `run_daily_scan()`:

### Step 1: Load and Validate watchlist.json

The scanner reads `watchlist.json`, validates required fields (`risk_profile`, `portfolio.holdings`, `watchlist`), and applies defaults for optional fields like `scanner_config` and `previous_analyses`.

### Step 2: Build the Ticker Universe

Holdings tickers and watchlist tickers are combined into a single deduplicated list using insertion-order deduplication (`dict.fromkeys()`). This ensures each ticker is processed exactly once, even if it appears in both lists. A holding/watchlist map tracks which category each ticker belongs to, since some triggers behave differently for holdings vs. watchlist stocks.

### Step 3: Load Prior Scan

The scanner checks the `scans/` directory for the most recent `scan_data.json`. It sorts date directories in reverse chronological order and loads the first valid JSON file it finds. If no prior scan exists, the `prior_stocks` dict is empty and all state-change triggers are suppressed.

### Step 4: Pull S&P 500 Data (Once)

The S&P 500 (`^GSPC`) is the universal benchmark. Its daily OHLCV is pulled once and shared across all stock evaluations for relative strength calculations.

### Step 5: Determine Sectors and Pull Sector ETFs (Once Per Sector)

For each ticker, the scanner looks up its sector via `yfinance` and maps it to the corresponding sector ETF using `sector_map.py`. Sector ETF data is cached -- if three stocks are all in Technology, `XLK` is pulled once and reused for all three.

### Step 6: Pull Per-Ticker Data

For each ticker, five API calls are made with a configurable delay between them (default 0.5 seconds):

1. **Daily OHLCV** -- 18 months of daily price and volume data
2. **Weekly OHLCV** -- 3 years of weekly data (for 30-week MA / Weinstein staging)
3. **Key ratios** -- P/E, P/B, EV/EBITDA, ROE, FCF yield, etc. from yfinance
4. **Quarterly EPS** -- Last 4+ quarters for CAN SLIM and earnings deterioration checks
5. **Insider transactions** -- Recent insider buys and sells

### Step 7: Compute All Indicators

For each ticker, `compute_all_indicators()` from `indicators.py` runs 14 computations:

- Moving averages (50, 150, 200-day SMAs + 30-week SMA with slope classification)
- Annualized return (1m, 3m, 6m, 12m windows)
- Annualized volatility (1m, 3m, 6m, 12m + 12-month rolling average)
- RSI (14-day, Wilder's smoothing)
- Bollinger Bands (20-day, 2 standard deviations, with width percentile)
- ATR (14-day, with trend direction)
- OBV (with 20-day MA and price-OBV divergence detection)
- Relative Strength vs. S&P 500 (1m, 3m, 6m, 12m ratios + trajectory)
- Relative Strength vs. Sector ETF (same timeframes)
- Volume Ratio (up-day volume / down-day volume over 60 days)
- 52-Week Metrics (high, low, distance from each)
- Price Z-Score (current price vs. 6-month distribution)
- Weinstein Stage (1-4 classification with confidence)
- CAN SLIM Quantitative (5-criteria pass/fail scorecard)

### Step 8: Evaluate All 18 Triggers

Each stock is evaluated against all 18 trigger conditions. The trigger evaluator receives the computed indicators, raw data, prior scan data, risk profile, and holding status. Triggers return structured dicts with an ID, category, priority level, human-readable description, and detail payload. Triggers that don't fire return `None` and are skipped.

### Step 9: Compute Portfolio Metrics

For holdings with non-zero share counts:

- **Per-holding**: market value, cost basis, P&L (dollar and percent), daily change, holding period in days
- **Portfolio aggregate**: total value (market value + cash), total invested, total P&L, daily change, cash allocation percentage
- **Concentration**: position weights, sector weights, three concentration flags
- **Correlation**: pairwise Pearson correlation of 6-month daily returns (only if fewer than 15 holdings), flagging pairs with r > 0.85

### Step 10: Generate Dashboard

The `dashboard.py` module formats all results into a markdown document with six sections: Portfolio Summary, Triggered Alerts, Holdings Detail, Concentration, Watchlist, and Recommended Actions. Alerts are sorted by priority and grouped by severity level.

### Step 11: Save Results

Two files are written to `scans/{YYYY-MM-DD}/`:

- **`daily_scan.md`** -- the human-readable dashboard
- **`scan_data.json`** -- the full machine-readable results, including per-stock indicator snapshots for next-run state change detection

### Data Flow Diagram

```
watchlist.json          Prior scan_data.json
     |                         |
     v                         v
  Load & Validate         Load Prior Scan
     |                         |
     v                         |
  Build Ticker Universe        |
     |                         |
     v                         |
  Pull S&P 500 (once)         |
     |                         |
     v                         |
  Pull Sector ETFs (once/sector)
     |                         |
     v                         |
  For each ticker:             |
  +--Pull daily/weekly OHLCV   |
  +--Pull ratios, EPS, insider |
  +--Compute 14 indicators     |
  +--Evaluate 18 triggers <----+
  +--Build indicator snapshot
     |
     v
  Compute Portfolio Metrics
  (P&L, concentration, correlation)
     |
     v
  Generate Dashboard (dashboard.py)
     |
     v
  Save to scans/{date}/
  +--daily_scan.md
  +--scan_data.json (for next run)
```

### Optimization Strategy

The scanner minimizes API calls through three techniques:

1. **S&P 500 pulled once** -- shared across all relative strength calculations
2. **Sector ETFs cached** -- if multiple stocks share a sector, the ETF data is pulled once
3. **Rate limiting** -- 0.5-second delay between per-ticker API calls prevents yfinance throttling

For a 25-stock universe, this means roughly 5 API calls per stock (daily, weekly, ratios, EPS, insider) plus ~5 benchmark pulls, totaling ~130 calls with ~65 seconds of rate-limit delay. Actual execution time is typically 60-120 seconds.

---

## 4. The 18 Trigger Conditions

### Category A: Trend Triggers

Structural trend changes that affect the investment thesis. These are the most significant signals because they indicate a shift in the stock's primary direction.

**A1 -- Weinstein Stage Change**
Detects when a stock transitions from one Weinstein stage to another (e.g., Stage 2 Advancing to Stage 3 Topping). This is a structural regime change -- the stock's relationship to its 30-week moving average has fundamentally shifted. Requires a prior scan for comparison; does not fire on first run. Priority: HIGH. Applies to both holdings and watchlist.

**A2 -- 30-Week MA Crossover**
Detects when price crosses above or below the 30-week moving average. In Weinstein's framework, this is the key signal line -- crossing below often precedes extended declines. On first run without a prior scan, flags stocks within 2% of the 30-week MA as an informational proximity alert. For risk-averse profiles, a downward cross on a held stock is elevated to HIGHEST priority. Applies to both.

**A3 -- 200-Day MA Crossover**
Same logic as A2 but for the 200-day SMA, the institutional signal level. Widely watched by fund managers as a bull/bear market dividing line. First-run behavior identical to A2 (2% proximity alert). Priority: HIGH. Applies to both.

**A4 -- MA Alignment Shift**
Monitors the ordering of the 50, 150, and 200-day SMAs. Bullish alignment means 50 > 150 > 200 with all rising. Bearish means the reverse. A shift from bullish to mixed (or mixed to bearish) signals structural deterioration. Requires prior scan. Priority: MEDIUM. Applies to both.

### Category B: Momentum Triggers

Overbought/oversold conditions and relative performance shifts. These flag when a stock's momentum is at an extreme that historically tends to revert.

**B1 -- RSI Overbought**
Fires when the 14-day RSI exceeds the overbought threshold. Risk-neutral threshold: RSI > 75. Risk-averse threshold: RSI > 70. The lower risk-averse threshold reflects a preference for earlier warnings. Priority: MEDIUM. Applies to both.

**B2 -- RSI Oversold**
Fires when RSI drops below the oversold threshold. Risk-neutral: RSI < 25. Risk-averse: RSI < 30. Priority: MEDIUM. Applies to both.

**B3 -- Extended from 200-Day MA**
Flags stocks whose price has moved an extreme distance from the 200-day MA. Risk-neutral threshold: |distance| > 20%. Risk-averse: |distance| > 15%. A stock 35% above its 200-day MA is historically stretched and vulnerable to a pullback. Priority: MEDIUM. Applies to both.

**B4 -- Price Z-Score Extreme**
Fires when the current price is more than 2 standard deviations from its 6-month mean (|Z| > 2.0). No risk-profile adjustment. This is a statistical measure of how unusual the current price is relative to recent history. Priority: MEDIUM. Applies to both.

**B5 -- RS Breakdown/Breakout**
Detects when a stock's relative strength vs. the S&P 500 shifts from outperforming (all RS ratios > 1.0) to underperforming (all < 1.0), or vice versa. Also flags trajectory deterioration (still outperforming but decelerating). Requires prior scan. RS state is classified using the `trajectory` field from `compute_relative_strength()`, not shortcut ratio comparisons. Priority: HIGH for full state changes, MEDIUM for trajectory shifts. Applies to both.

### Category C: Volume Triggers

Institutional activity and supply/demand signals. Volume is the only indicator that is independent of price -- it reveals what large players are doing.

**C1 -- Volume Spike**
Fires when today's volume exceeds 2x the 20-day average volume (configurable via `volume_spike_multiplier`). For holdings, only flags down-day volume spikes (potential distribution). For watchlist stocks, also flags up-day spikes (potential breakout entry). The asymmetry reflects different concerns: you want to know when institutions are dumping a stock you hold, and when they're accumulating one you're watching. Priority: HIGH for down-day spikes, LOW for up-day spikes.

**C2 -- OBV Divergence**
Detects when On-Balance Volume and price are trending in opposite directions over 20 days. Bearish divergence (price rising, OBV falling) suggests the advance lacks volume support and may fail. Bullish divergence (price falling, OBV rising) suggests accumulation despite price weakness. Priority: HIGH for bearish, MEDIUM for bullish.

**C3 -- Volume Ratio Shift**
Monitors the 60-day ratio of average volume on up days vs. down days. For holdings, flags when sellers dominate (ratio < 0.8). For watchlist stocks, flags when buyers dominate (ratio > 1.3). Again, asymmetric by category -- different concerns depending on whether you own it. Priority: MEDIUM. Holding-only for selling signal, watchlist-only for buying signal.

**C4 -- Bollinger Squeeze**
Fires when Bollinger Band width falls below its 10th percentile over the past 252 days. A squeeze indicates unusually low volatility, which historically precedes a large price move (direction unknown). Priority: LOW. Applies to both.

### Category D: Valuation Triggers

Fundamental valuation extremes and earnings deterioration. These complement the technical signals with business-level data.

**D1 -- P/E Extreme**
Flags P/E ratios above 50 (and more than 2x the sector median) or below 10 (with positive earnings). The sector median is computed from peer stocks in the scan when at least two peers share a sector; otherwise falls back to hardcoded sector medians (e.g., Technology: 28, Energy: 12, Real Estate: 38). Priority: LOW. Applies to both.

**D2 -- Earnings Deterioration**
Fires when the most recent quarterly EPS declined more than 25% year-over-year. Also checks for consecutive quarters of decline and annotates accordingly. Requires at least 5 quarters of EPS data. Priority: MEDIUM. Applies to both.

**D3 -- Insider Activity Spike**
Two sub-conditions, evaluated over a 90-day window:
- **Cluster buying**: 3 or more distinct insiders purchasing within 30 days (bullish signal)
- **Heavy selling**: Over $10 million in insider sales with zero purchases (bearish signal)

Automatic/10b5-1 plan transactions are filtered out by parsing the transaction text field for keywords like "Automatic", "Plan", or "10b5". Unknown transaction types are conservatively included. Priority: MEDIUM. Applies to both.

### Category E: Prior Analysis Triggers

Thesis-aware monitoring that connects the scanner to previous DualEdge deep dives. These are the highest-priority triggers because they indicate your prior investment thesis may need revision.

**E1 -- Change Condition Met**
Evaluates the explicit change conditions stored in `watchlist.json` from previous DualEdge runs. Supports 10 condition types:

| Condition Type | What It Checks |
|---------------|----------------|
| `price_below` | Current price < threshold |
| `price_above` | Current price > threshold (optionally requires above-average volume) |
| `weekly_close_below` | Weekly close < threshold (optionally requires above-average weekly volume) |
| `weekly_close_above` | Weekly close > threshold |
| `rs_breakdown` | RS vs SPX below threshold across specified timeframes |
| `rs_breakout` | RS vs SPX above threshold across specified timeframes |
| `stage_change_to` | Weinstein stage matches target stage |
| `rsi_above` | RSI exceeds threshold |
| `rsi_below` | RSI drops below threshold |
| `obv_divergence` | OBV divergence in specified direction (bearish or bullish) |

Priority: HIGHEST. This is the only trigger level that generates an automatic "Run full DualEdge analysis" recommendation.

**E2 -- Analysis Staleness**
Fires when the last DualEdge deep dive for a stock was more than 30 days ago. A reminder that the thesis may be based on outdated data. Priority: LOW.

---

## 5. Portfolio Analytics

### Per-Holding Metrics

For each holding with non-zero shares, the scanner computes:

- **Market value**: shares x current price
- **Cost basis**: shares x cost_basis_per_share
- **P&L**: dollar and percentage, unrealized
- **Daily change**: dollar and percentage, based on today's close vs. yesterday's close
- **Holding period**: days since entry_date

Zero-share holdings are flagged as `is_zero_position` and excluded from P&L and portfolio-level calculations but still receive full indicator computation and trigger evaluation.

### Portfolio-Level Metrics

- **Total value**: sum of all market values + cash balance
- **Total invested**: sum of all cost bases
- **Total P&L**: aggregate unrealized gain/loss (dollar and percentage)
- **Daily change**: portfolio-level daily move (dollar and percentage), computed relative to yesterday's portfolio value
- **Cash allocation**: cash as a percentage of total portfolio value

### Concentration Analysis

Three flags, each with a specific threshold:

| Flag | Threshold | Why It Matters |
|------|-----------|---------------|
| Single stock concentration | Any position > 25% of portfolio | Idiosyncratic risk -- one stock's bad earnings report disproportionately impacts the whole portfolio |
| Sector concentration | Any sector > 40% of portfolio | Sector rotation risk -- an entire industry can fall out of favor simultaneously |
| Top-heavy portfolio | Top 3 positions > 60% of portfolio | Diversification failure -- the portfolio's performance is driven by just a few names |

Position and sector weights are computed from market values relative to total portfolio value (including cash). In the real scan output from February 7, 2026, all three flags fired: GOOG at 51.2%, Communication Services at 64.0%, and top 3 at 73.3%.

### Correlation Matrix

For portfolios with fewer than 15 holdings (above that, the computation becomes unwieldy), the scanner computes pairwise Pearson correlation of 6-month daily returns. Pairs with r > 0.85 are flagged -- holding two highly correlated stocks provides limited diversification benefit. The matrix requires at least 20 overlapping trading days and at least 2 holdings to compute.

---

## 6. Dashboard Output

The daily scan produces a markdown file (`daily_scan.md`) with six sections:

### Header

Displays the scan date, risk profile, number of stocks scanned, scan time, and whether a prior scan was available for state change detection.

### Portfolio Summary

A table showing total value, daily change (dollar and percent), unrealized P&L (dollar and percent), and cash position. If no holdings have non-zero shares, displays a message prompting the user to update `watchlist.json`.

### Triggered Alerts

All fired triggers, sorted by priority and grouped into three severity levels:

| Priority Level | Label | Triggers |
|---------------|-------|----------|
| HIGHEST, HIGH | CRITICAL / WARNING | Stage changes, MA crossovers, RS shifts, volume spikes on down days, bearish OBV divergence, insider selling, change conditions met |
| MEDIUM | WARNING | RSI extremes, extension from 200d MA, Z-score extremes, earnings deterioration, volume ratio shifts, insider cluster buys |
| LOW, INFO | INFORMATIONAL | Bollinger squeeze, P/E extremes, analysis staleness, MA proximity alerts |

HIGHEST-priority triggers include an action line: "Run full DualEdge analysis on {TICKER}."

### Holdings Detail

A table for each holding showing: price, daily change, P&L, portfolio weight, Weinstein stage, RSI, distance from 30-week MA, relative strength vs. S&P 500 (with trajectory arrow), and a compact flag column summarizing any fired triggers. Clean stocks show a green checkmark.

Below the table, concentration warnings and high-correlation pairs are listed.

### Watchlist

Same table format but for non-held stocks and zero-position holdings, adding a CAN SLIM score column (X/5) instead of P&L and weight.

### Recommended Actions

A numbered, prioritized action list generated algorithmically:

1. **HIGHEST priority** generates: "Run DualEdge on {TICKER}" -- a change condition from a prior analysis has been met, warranting a full re-evaluation
2. **HIGH priority** generates: "Review {TICKER}" -- a significant technical signal requires attention
3. **MEDIUM priority** generates: "Monitor {TICKER}" -- watch for escalation but no immediate action needed
4. **Concentration flags** generate: "Address concentration risk" -- portfolio-level structural issues

Each action is deduplicated by ticker -- if a stock fires multiple triggers, only the highest-priority trigger is surfaced in the action list.

### Footer

Displays scan duration and confirms zero LLM tokens were consumed. Shows the next expected scan date.

In the February 7, 2026 scan, 36 triggers fired across 26 stocks, generating 19 recommended actions. The scan completed in 116.2 seconds.

---

## 7. State Change Detection

### How the Baseline Works

Every scan saves a per-stock indicator snapshot in `scan_data.json`. The snapshot includes:

- `weinstein_stage` -- integer 1-4
- `price_above_30w_ma` -- boolean
- `price_above_200d_ma` -- boolean
- `ma_alignment` -- "bullish", "bearish", or "mixed"
- `rs_state_vs_spx` -- "outperforming", "outperforming_improving", "underperforming", or "mixed"
- `rs_trajectory_vs_spx` -- "improving", "deteriorating", or "stable"
- Plus: RSI, volume ratio, Bollinger width percentile, CAN SLIM score, price Z-score, annualized volatility, ATR trend, distance from 52-week high, RS values at each timeframe, and distance from key MAs

### First Run Behavior

On the first run (no prior `scan_data.json` found):

- State-change triggers (A1, A2, A3, A4, B5) **do not fire**. They require a "before" state to compare against.
- Exception: A2 and A3 generate INFO-level proximity alerts if the stock is within 2% of the 30-week or 200-day MA. This flags stocks that are near a potential crossover.
- All non-state-change triggers (B1-B4, C1-C4, D1-D3, E1-E2) evaluate normally.
- The snapshot is saved, establishing the baseline for the next run.

### Subsequent Run Behavior

On every subsequent run:

1. The scanner loads the most recent `scan_data.json`
2. For each stock, it retrieves the prior snapshot from `prior_stocks[ticker]`
3. State-change triggers compare current values against prior values:
   - A1: `indicators.weinstein_stage.stage` vs. `prior.indicators.weinstein_stage`
   - A2: `current_close > sma_30w.value` vs. `prior.indicators.price_above_30w_ma`
   - A3: `current_close > sma_200.value` vs. `prior.indicators.price_above_200d_ma`
   - A4: `_classify_ma_alignment()` vs. `prior.indicators.ma_alignment`
   - B5: `_classify_rs_state()` vs. `prior.indicators.rs_state_vs_spx`
4. A new snapshot is saved, becoming the baseline for the next run

The date directory naming (`scans/2026-02-07/`) means running the scanner twice in one day overwrites the same files. Running on consecutive days creates separate directories, and the scanner always loads the most recent.

---

## 8. How to Use It

### Running the Scanner

From the project root:

```bash
python -m src.scanner
```

Or with a custom watchlist path:

```bash
python -m src.scanner --watchlist /path/to/watchlist.json
```

The scanner prints progress to stdout as it runs: which tickers are being pulled, how many triggers fired per stock, and the final summary.

### Reading the Output

Open `scans/{today's date}/daily_scan.md` in any markdown viewer.

**What to look at first:**

1. **Triggered Alerts section** -- scan the CRITICAL/WARNING groups. These are the stocks that need attention today.
2. **Recommended Actions** -- the numbered list at the bottom tells you exactly what to do, in priority order.
3. **Holdings Detail table** -- check the Flags column for any held stock. Green checkmarks mean all quiet.

**What the flags mean in context:**

- A held stock with a red stage change or MA crossover: your thesis may be breaking down. Consider a DualEdge re-evaluation.
- A watchlist stock with RSI oversold + Bollinger squeeze: potential entry setup forming. Worth watching for a breakout.
- Multiple insider-selling flags across your holdings: likely noise (routine executive compensation), but the dollar amounts tell you if it's meaningful.

### When to Run a Full DualEdge Deep Dive

- **Always run one** when an E1 (Change Condition Met) trigger fires -- by definition, the condition that would change your prior thesis has been met.
- **Strongly consider** running one when a held stock fires A1 (stage change) or A2 (30-week MA crossover below), especially if your prior analysis was a BUY.
- **Optional but useful** when a watchlist stock fires multiple complementary signals (e.g., RSI oversold + bullish OBV divergence + price near 52-week low) -- these are the setups the full analysis is designed to evaluate.
- **Not necessary** for single LOW/INFO triggers like Bollinger squeeze or P/E extreme in isolation. Note them and wait for confirming signals.

### Updating watchlist.json After a DualEdge Run

After completing a DualEdge deep dive, manually add the results to the `previous_analyses` section of `watchlist.json`:

```json
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
  }
}
```

The `change_conditions` array supports 10 condition types (see E1 trigger documentation above). The `description` field is free-text and appears in the dashboard when the condition fires, so make it specific enough to remind you of the original thesis.

This is currently a manual step. The user updates `watchlist.json` after each deep dive with the recommendation, confidence score, and -- most importantly -- the change conditions from both analysts' reports. This is what closes the loop between Tier 2 (deep analysis) and Tier 1 (daily monitoring).
