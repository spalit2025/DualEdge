# CLAUDE.md — DualEdge Implementation Guide

## Project Overview

DualEdge is a dual-agent stock analysis system built on Claude Code Agent Teams. Two specialist agents (Value Analyst + Technical Analyst) independently analyze a stock using 12 proven investment frameworks, then debate disagreements to produce a conviction-scored BUY/SELL recommendation.

**PRD Location**: `PRD.md` — refer to this for full requirements, agent prompts, and output specifications.

---

## Project Structure

```
DualEdge/                                  # Project root (you are here)
├── CLAUDE.md                              # This file
├── PRD.md                                 # Full product requirements
├── src/
│   ├── data_utils.py                      # Data retrieval (yfinance + SEC EDGAR)
│   ├── indicators.py                      # Technical indicator calculations
│   ├── sector_map.py                      # Sector → ETF ticker mapping
│   └── prompts/
│       ├── value_analyst.md               # Value Analyst system prompt template
│       ├── technical_analyst.md           # Technical Analyst system prompt template
│       └── lead_agent.md                 # Lead/CIO agent system prompt template
├── templates/
│   ├── fundamental_report.md              # Output template for Value Analyst
│   ├── technical_report.md                # Output template for Technical Analyst
│   └── final_report.md                   # Output template for final consolidated report
├── tests/
│   ├── test_data_utils.py                 # Test data retrieval functions
│   ├── test_indicators.py                # Test indicator calculations against known values
│   └── test_sector_map.py                # Test sector mapping
├── analysis/                              # Runtime output directory (created per-run)
│   └── {TICKER}/
│       ├── fundamental_analysis.md
│       ├── technical_analysis.md
│       ├── debate_log.md
│       └── final_report.md
└── requirements.txt                       # Python dependencies
```

---

## Implementation Phases

Build in this order. Each phase should be testable independently before moving to the next.

### Phase 1: Data Layer (`src/data_utils.py`)

Build the shared data retrieval module. Both agents depend on this.

**File: `src/data_utils.py`**

Functions to implement:

```python
def validate_ticker(ticker: str) -> bool:
    """Check if ticker exists via yfinance. Return True/False."""

def get_financials(ticker: str) -> dict:
    """Pull income statement, balance sheet, cash flow (annual + quarterly).
    Return as dict of DataFrames."""

def get_key_ratios(ticker: str) -> dict:
    """Compute/pull: P/E, P/B, EV/EBITDA, debt-to-equity, ROE, ROA,
    FCF yield, current ratio. Return as flat dict."""

def get_ohlcv_daily(ticker: str, months: int = 18) -> pd.DataFrame:
    """Pull daily OHLCV. Return DataFrame with Date index,
    columns: Open, High, Low, Close, Volume."""

def get_ohlcv_weekly(ticker: str, years: int = 3) -> pd.DataFrame:
    """Pull weekly OHLCV. Same format as daily."""

def get_benchmark_data(ticker: str, months: int = 18) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Pull S&P 500 (^GSPC) and relevant sector ETF daily data.
    Use sector_map to determine ETF. Return (spx_df, sector_df)."""

def get_insider_transactions(ticker: str) -> pd.DataFrame:
    """Pull insider transactions from yfinance. Include:
    date, insider_name, position, transaction_type, shares, value."""

def get_analyst_data(ticker: str) -> dict:
    """Pull analyst price targets (low, mean, median, high, current)
    and recommendations summary. Return as dict."""

def get_quarterly_eps(ticker: str) -> pd.DataFrame:
    """Pull last 4+ quarters of EPS data for CAN SLIM analysis."""

def get_10k_text(ticker: str, sections: list[str] = None) -> str:
    """Retrieve most recent 10-K from SEC EDGAR.
    
    Steps:
    1. Query EDGAR company search API for CIK:
       https://efts.sec.gov/LATEST/search-index?q={ticker}&dateRange=custom&startdt=...
       OR use: https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&company=&CIK={ticker}&type=10-K&dateb=&owner=include&count=5&search_text=&action=getcompany
    2. Get filing index page for most recent 10-K
    3. Retrieve the full filing text
    4. If sections specified, extract only those sections
       Default sections: ['MD&A', 'Risk Factors', 'Financial Statements']
    
    IMPORTANT: Set User-Agent header to a valid email address.
    Rate limit: max 10 requests/second to EDGAR.
    
    If 10-K text exceeds 150K characters, truncate to priority sections only.
    Return the text content as a string."""
```

**SEC EDGAR API Notes:**
- Base URL for full-text search: `https://efts.sec.gov/LATEST/search-index`
- Company filings: `https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={ticker}&type=10-K&dateb=&owner=include&count=1&search_text=&action=getcompany`
- EDGAR full-text filings API: `https://efts.sec.gov/LATEST/search-index?q=%22{ticker}%22&forms=10-K`
- Required header: `User-Agent: DualEdge/1.0 (your-email@example.com)`
- Respect 10 req/sec rate limit with `time.sleep(0.1)` between requests
- An alternative simpler approach: use the SEC EDGAR full-text search API at `https://efts.sec.gov/LATEST/search-index` or the newer EDGAR API at `https://data.sec.gov/submissions/CIK{cik_padded}.json` to find filings, then fetch the document

**Testing**: Test each function individually with a well-known stock (AAPL) before integration. Verify data completeness and handle missing fields gracefully (return None or empty).

---

### Phase 2: Technical Indicators (`src/indicators.py`)

Build the indicator computation module. Used by the Technical Analyst agent.

**File: `src/indicators.py`**

Functions to implement:

```python
def compute_all_indicators(daily_df: pd.DataFrame, weekly_df: pd.DataFrame,
                           spx_df: pd.DataFrame, sector_df: pd.DataFrame) -> dict:
    """Master function that calls all individual indicator functions.
    Returns a dict with all computed values organized by category."""

def compute_moving_averages(daily_df: pd.DataFrame, weekly_df: pd.DataFrame) -> dict:
    """Compute SMA 50, 150, 200 (daily) and 30-week (weekly).
    Return current values and slopes (rising/flat/falling)."""

def compute_annualized_return(daily_df: pd.DataFrame) -> dict:
    """R_ann = (1 + R_cum)^(252/n) - 1
    Compute for multiple windows: 1m, 3m, 6m, 12m."""

def compute_annualized_volatility(daily_df: pd.DataFrame) -> dict:
    """σ_ann = σ_daily × √252
    Compute for multiple windows: 1m, 3m, 6m, 12m.
    Also compute 12-month average for regime comparison."""

def compute_rsi(daily_df: pd.DataFrame, period: int = 14) -> float:
    """Wilder's smoothed RSI. Return current RSI value."""

def compute_bollinger_bands(daily_df: pd.DataFrame, period: int = 20,
                            num_std: float = 2.0) -> dict:
    """Return upper, middle, lower bands, current width,
    and width percentile vs. past 252 days."""

def compute_atr(daily_df: pd.DataFrame, period: int = 14) -> dict:
    """Wilder's ATR. Return current ATR, ATR trend
    (last 20 days vs prior 20 days: increasing/decreasing)."""

def compute_obv(daily_df: pd.DataFrame) -> dict:
    """On-Balance Volume. Return current OBV, 20-day OBV MA,
    OBV trend direction, price-OBV divergence flag."""

def compute_relative_strength(daily_df: pd.DataFrame,
                               benchmark_df: pd.DataFrame) -> dict:
    """RS ratio = stock_return / benchmark_return
    Compute at 1m, 3m, 6m, 12m. Return ratios and trajectory."""

def compute_volume_ratio(daily_df: pd.DataFrame, window: int = 60) -> float:
    """avg volume on up days / avg volume on down days over window.
    Up day = close > previous close."""

def compute_52week_metrics(daily_df: pd.DataFrame) -> dict:
    """52-week high, low, current distance from each (%)."""

def compute_price_zscore(daily_df: pd.DataFrame, lookback: int = 126) -> float:
    """Z-score of current price relative to 6-month distribution."""

def compute_weinstein_stage(weekly_df: pd.DataFrame) -> dict:
    """Classify Weinstein stage 1-4.
    Return: stage, confidence, 30w_ma_slope, price_vs_30w_ma, volume_pattern."""

def compute_canslim_quantitative(daily_df: pd.DataFrame, spx_df: pd.DataFrame,
                                  eps_data: pd.DataFrame) -> dict:
    """Score CAN SLIM criteria.
    C: Current quarterly EPS acceleration
    A: Annual EPS growth (3-year CAGR if available, else use available data)
    N: Within 5% of 52-week high
    S: Volume ratio > 1.0
    L: 6-month RS vs SPX in top quartile (> 1.0 threshold)
    Return: criteria dict with pass/fail + score out of 5."""
```

**Testing**: Write `test_indicators.py` with known calculation results. Use a stock with well-documented technical levels (e.g., AAPL or SPY) and verify:
- Moving averages match a reference source (e.g., Yahoo Finance chart)
- RSI is in valid range (0-100)
- Bollinger Bands: middle band = 20-day SMA
- OBV is monotonic relative to cumulative volume logic
- Relative strength ratios are reasonable (typically 0.5-2.0 range)

---

### Phase 3: Sector Mapping (`src/sector_map.py`)

**File: `src/sector_map.py`**

```python
SECTOR_ETF_MAP = {
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
    """Look up sector from yfinance info['sector'], map to ETF.
    Default to 'SPY' if sector not found or not in map."""
```

Simple module. Build it early because `data_utils.get_benchmark_data()` depends on it.

---

### Phase 4: Prompt Templates (`src/prompts/`)

Create three markdown files containing the full system prompts from the PRD (Section 4). These are templates with `{TICKER}` and `{RISK_PROFILE}` placeholders that the lead agent fills before spawning teammates.

**Files to create:**
1. `src/prompts/value_analyst.md` — copy from PRD Section 4.1
2. `src/prompts/technical_analyst.md` — copy from PRD Section 4.2
3. `src/prompts/lead_agent.md` — copy from PRD Section 4.3

The lead agent reads these files, replaces placeholders, and passes the result as the teammate's spawn prompt.

---

### Phase 5: Output Templates (`templates/`)

Create three markdown templates that define the output structure for each report type. Agents reference these when writing their analysis.

**Files to create:**
1. `templates/fundamental_report.md` — structure from PRD FR-VA-04
2. `templates/technical_report.md` — structure from PRD FR-TA-05
3. `templates/final_report.md` — structure from PRD FR-LEAD-04

---

### Phase 6: Integration Testing

Before wiring up Agent Teams, test the full data + computation pipeline as a standalone script:

```python
# test_integration.py — run this manually
ticker = "AAPL"

# Test data layer
assert validate_ticker(ticker)
financials = get_financials(ticker)
ratios = get_key_ratios(ticker)
daily = get_ohlcv_daily(ticker)
weekly = get_ohlcv_weekly(ticker)
spx, sector = get_benchmark_data(ticker)
insider = get_insider_transactions(ticker)
analyst = get_analyst_data(ticker)
eps = get_quarterly_eps(ticker)
# 10k = get_10k_text(ticker)  # Test separately (slower)

# Test indicator layer
indicators = compute_all_indicators(daily, weekly, spx, sector)

# Print summary to verify
print(f"Ratios: {ratios}")
print(f"Indicators: {indicators}")
print(f"Insider count: {len(insider)}")
print(f"Analyst targets: {analyst}")
```

Only proceed to Phase 7 once this runs cleanly.

---

### Phase 7: Agent Teams Orchestration

This is where everything comes together. The lead agent is the entry point.

**How to run DualEdge:**

1. Ensure Claude Code has Agent Teams enabled:
   ```json
   // settings.json
   { "env": { "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1" } }
   ```

2. Start a Claude Code session and give the instruction:
   ```
   Run DualEdge analysis for {TICKER} with {risk-neutral/risk-averse} risk profile.
   
   Read the lead agent prompt from src/prompts/lead_agent.md
   and follow it step by step. The PRD is at PRD.md for
   full specifications.
   ```

3. The lead agent:
   - Validates ticker
   - Creates `analysis/{TICKER}/`
   - Reads and fills prompt templates
   - Spawns two teammates
   - Waits for both to complete
   - Runs debate if needed
   - Generates final report

**Key orchestration details:**
- Teammates work in parallel — this is the primary benefit of Agent Teams
- Lead should NOT implement analysis itself — delegate only (use delegate mode `Shift+Tab` if needed)
- Each teammate has access to the full `src/` directory for Python utilities
- Teammates write output to `analysis/{TICKER}/`
- Lead reads output files to check consensus and orchestrate debate
- If a teammate errors, lead should report the error clearly rather than attempting the analysis itself

---

## Conventions

### Code Style
- Python 3.10+
- Type hints on all function signatures
- Docstrings on all public functions (Google style)
- Error handling: use try/except with specific exceptions, not bare except
- Data: use pandas DataFrames for tabular data, dicts for key-value results
- No classes needed for V1 — functional style with module-level functions

### File Naming
- Python modules: `snake_case.py`
- Output files: `lowercase_with_underscores.md`
- Ticker references: always UPPERCASE (e.g., `AAPL`, not `aapl`)

### Error Handling Pattern
```python
def get_financials(ticker: str) -> dict | None:
    """Pull financials. Returns None if retrieval fails."""
    try:
        t = yf.Ticker(ticker)
        result = {
            "income_stmt": t.income_stmt,
            "balance_sheet": t.balance_sheet,
            "cash_flow": t.cashflow,
        }
        # Validate we got actual data
        if result["income_stmt"] is None or result["income_stmt"].empty:
            print(f"Warning: No income statement data for {ticker}")
            return None
        return result
    except Exception as e:
        print(f"Error retrieving financials for {ticker}: {e}")
        return None
```

Agents should handle None returns gracefully — note the data gap in their analysis and mark the affected framework as "N/A — insufficient data."

### SEC EDGAR Requests
Always include:
```python
HEADERS = {
    "User-Agent": "DualEdge/1.0 (contact-email@example.com)",
    "Accept-Encoding": "gzip, deflate",
}
# Rate limit
import time
time.sleep(0.1)  # 100ms between EDGAR requests
```

---

## Dependencies

```
# requirements.txt
yfinance>=0.2.36
pandas>=2.0.0
numpy>=1.24.0
requests>=2.31.0
```

Install with:
```bash
pip install -r requirements.txt --break-system-packages
```

---

## Key Constraints

1. **Agent Teams is experimental** — no session resumption. Each analysis is a fresh session. Don't assume state carries over.
2. **Token budget**: ~250K max per stock analysis. The Value Analyst's 10-K ingestion is the biggest consumer. Truncate 10-K to key sections if approaching limit.
3. **Two teammates max** per analysis run. Don't spawn additional agents.
4. **Binary output**: BUY or SELL only. No HOLD. This forces a position and makes the debate productive.
5. **Confidence scores**: 1-10 integer. Both agents must include this. It's the tiebreaker mechanism.
6. **Change conditions**: Both agents must state "what would change my mind." This drives the deadlock resolution protocol.
7. **Max 2 debate rounds** before tiebreaker. Don't let debate loop indefinitely.
8. **Free APIs only**: yfinance + SEC EDGAR. No paid data services.
9. **US equities only** for V1. Stocks must have SEC filings.

---

## Testing Checklist

Before considering V1 complete, verify:

- [ ] `validate_ticker()` correctly identifies valid and invalid tickers
- [ ] `get_financials()` returns populated DataFrames for a test stock
- [ ] `get_key_ratios()` returns reasonable values (P/E > 0, ROE between -1 and 1, etc.)
- [ ] `get_ohlcv_daily()` returns 18 months of data with no gaps > 3 days
- [ ] `get_benchmark_data()` returns matching date ranges for stock and benchmarks
- [ ] `get_insider_transactions()` returns data (or empty DataFrame if none)
- [ ] `get_analyst_data()` returns price targets and recommendations
- [ ] `get_10k_text()` retrieves readable 10-K text from EDGAR
- [ ] `compute_all_indicators()` returns all expected indicator values
- [ ] RSI is in range 0-100
- [ ] Bollinger middle band equals 20-day SMA
- [ ] OBV computation matches manual verification
- [ ] Weinstein stage classification produces valid stage (1-4)
- [ ] CAN SLIM score is 0-5
- [ ] Value Analyst produces complete `fundamental_analysis.md` with all 6 frameworks
- [ ] Technical Analyst produces complete `technical_analysis.md` with all 6 frameworks
- [ ] Both reports include SUMMARY table with RECOMMENDATION, CONFIDENCE, KEY DRIVER, CHANGE CONDITION
- [ ] Lead correctly identifies AGREE vs DISAGREE
- [ ] Debate protocol runs when agents disagree (test with a stock likely to cause disagreement)
- [ ] Tiebreaker activates when debate doesn't converge
- [ ] `final_report.md` contains all required sections
- [ ] `debate_log.md` is generated (even if empty when agents agree)
- [ ] Risk-neutral and risk-averse produce different outputs for the same stock
- [ ] Full pipeline completes within token budget (~250K)

---

## Quick Start for Implementation

If you're Claude Code starting implementation, do this:

1. `pip install yfinance pandas numpy requests --break-system-packages`
2. Build `src/sector_map.py` first (smallest, no dependencies)
3. Build `src/data_utils.py` next (test each function with AAPL)
4. Build `src/indicators.py` (test with AAPL daily/weekly data)
5. Create prompt templates in `src/prompts/` (copy from PRD Section 4)
6. Create output templates in `templates/` (copy from PRD Sections FR-VA-04, FR-TA-05, FR-LEAD-04)
7. Run integration test to verify data + indicators pipeline
8. Test each agent individually as a standalone Claude Code session (without Agent Teams) to verify prompt quality
9. Wire up Agent Teams for the full orchestrated run
10. Test end-to-end with AAPL (risk-neutral), then with a more volatile stock, then with risk-averse profile

---

## V1 Status: COMPLETE ✅

V1 has been built, tested, and validated across all scenarios:
- AAPL risk-neutral: Split Decision → BUY 7/10 (debate + tiebreaker validated)
- TSLA risk-neutral: Consensus SELL 7/10 (consensus path validated)
- NVDA risk-averse: Consensus SELL 7/10 (risk-averse thresholds validated)
- NVDA risk-neutral: Consensus BUY 6/10 (risk profile differentiation validated)

**V1 Architecture Lesson**: Background subagents cannot reliably run Bash commands (permission prompts have no user to approve them). The working pattern is: pre-compute all data in the main session, write to files, then have agents analyze pre-built files. This is actually better — data is pulled once (token-efficient) and agents focus on analysis.

---

# V1.1 — Watchlist Monitor

## V1.1 Overview

The Watchlist Monitor adds daily portfolio surveillance to DualEdge without burning LLM tokens on routine checks. It reuses the existing `data_utils.py` and `indicators.py` modules to scan a user-defined watchlist and flag only stocks that need attention.

**V1.1 Addendum**: `V1.1-ADDENDUM.md` — full specification with all 18 trigger conditions, portfolio calculations, dashboard format, and implementation details.

**Two-tier design:**
- **Tier 1 (Daily Scanner)**: Pure Python script. Computes indicators for all watchlist stocks, evaluates 18 trigger conditions, checks prior DualEdge change conditions. Zero LLM tokens. ~30-60 seconds for 20 stocks.
- **Tier 2 (Triggered Deep Dive)**: Existing DualEdge V1 system, triggered only when Tier 1 flags something. No changes to V1 needed.

## V1.1 Project Structure (New Files Only)

```
DualEdge/
├── watchlist.json                       # NEW — portfolio + watchlist config
├── V1.1-ADDENDUM.md                     # NEW — V1.1 requirements
├── src/
│   ├── data_utils.py                    # EXISTING — no changes
│   ├── indicators.py                    # EXISTING — no changes
│   ├── sector_map.py                    # EXISTING — no changes
│   ├── scanner.py                       # NEW — Tier 1 signal scanner
│   ├── portfolio.py                     # NEW — portfolio-level calculations
│   └── dashboard.py                     # NEW — markdown dashboard formatter
├── templates/
│   └── daily_scan.md                    # NEW — dashboard output template
├── scans/                               # NEW — daily scan output
│   └── {YYYY-MM-DD}/
│       ├── daily_scan.md
│       └── scan_data.json
```

## V1.1 Implementation Phases

Build in this order. Each phase depends on the one before it.

### Phase A: Portfolio Module (`src/portfolio.py`) — 2-3 hours

Functions to implement:

```python
def compute_holding_metrics(holding: dict, current_price: float,
                           yesterday_close: float) -> dict:
    """Per-holding: market value, P&L ($, %), daily change ($, %), holding period.
    Input 'holding' comes from watchlist.json (ticker, shares, cost_basis_per_share, entry_date)."""

def compute_portfolio_metrics(holdings_metrics: list[dict],
                              cash_balance: float) -> dict:
    """Portfolio aggregates: total value, total invested, total P&L ($, %),
    cash allocation %, daily change ($, %)."""

def compute_concentration(holdings_metrics: list[dict],
                          total_portfolio_value: float,
                          sector_map: dict) -> dict:
    """Position weights, sector weights, largest position, top-3 weight.
    Flag: single stock > 25%, sector > 40%, top-3 > 60%."""

def compute_correlation_matrix(tickers: list[str],
                               daily_data: dict[str, pd.DataFrame]) -> dict:
    """Pairwise Pearson correlation of 6-month daily returns.
    Only compute if < 15 holdings. Flag pairs with r > 0.85."""
```

**Testing**: Create a sample `watchlist.json` with 3-5 holdings. Verify P&L calculations against manual math. Verify concentration flags fire at correct thresholds.

### Phase B: Scanner Core (`src/scanner.py`) — 4-5 hours

This is the most complex phase. The scanner evaluates 18 trigger conditions across 5 categories.

```python
def run_daily_scan(watchlist_path: str = "watchlist.json") -> dict:
    """Main entry point.
    1. Load watchlist.json
    2. Pull S&P 500 data once (shared benchmark)
    3. For each ticker: pull data, compute indicators, evaluate triggers
    4. Compute portfolio metrics + concentration
    5. Load prior scan for state change detection
    6. Generate dashboard + save scan_data.json
    Returns: dict of scan results."""

def evaluate_triggers(ticker: str, indicators: dict, ratios: dict,
                      eps_data, insider_data, prior_scan: dict | None,
                      change_conditions: list, risk_profile: str,
                      is_holding: bool) -> list[dict]:
    """Evaluate all 18 triggers for one stock. Returns list of fired triggers."""

def load_prior_scan(scan_dir: str = "scans") -> dict | None:
    """Load most recent scan_data.json for state change comparison."""

def save_scan_results(results: dict, scan_dir: str = "scans") -> str:
    """Save scan_data.json and daily_scan.md to scans/{date}/."""
```

**The 18 triggers** (full specs in V1.1-ADDENDUM.md Sections 4.3-4.4):

| ID | Trigger | Category | What It Detects |
|----|---------|----------|----------------|
| A1 | Weinstein Stage Change | Trend | Stage transition (e.g., 2→3) |
| A2 | 30-Week MA Crossover | Trend | Price crossing the key Weinstein level |
| A3 | 200-Day MA Crossover | Trend | Price crossing institutional signal level |
| A4 | MA Alignment Shift | Trend | 50/150/200 MA order changed |
| B1 | RSI Overbought | Momentum | RSI > 75 (risk-neutral) or > 70 (risk-averse) |
| B2 | RSI Oversold | Momentum | RSI < 25 (risk-neutral) or < 30 (risk-averse) |
| B3 | Extended from 200d MA | Momentum | \|distance\| > 20% (RN) or > 15% (RA) |
| B4 | Price Z-Score Extreme | Momentum | \|Z\| > 2.0 |
| B5 | RS Breakdown/Breakout | Momentum | RS vs SPX state changed |
| C1 | Volume Spike | Volume | 2x+ avg volume on down day |
| C2 | OBV Divergence | Volume | Price/OBV trend mismatch |
| C3 | Volume Ratio Shift | Volume | Sellers dominating (<0.8) or buyers (>1.3) |
| C4 | Bollinger Squeeze | Volume | Band width < 10th percentile |
| D1 | P/E Extreme | Valuation | > 50 or < 10 vs sector median |
| D2 | Earnings Deterioration | Valuation | YoY EPS decline > 25% |
| D3 | Insider Activity Spike | Valuation | 3+ cluster buy or $10M+ selling |
| E1 | Change Condition Met | Prior Analysis | DualEdge change condition triggered |
| E2 | Analysis Staleness | Prior Analysis | Last analysis > 30 days old |

**Critical implementation notes for triggers:**
- State-change triggers (A1, A2, A3, A4, B5) require a prior scan for comparison. On first run, compute baselines only — don't flag as "changed."
- Risk-profile-adjusted triggers (B1, B2, B3) use different thresholds per `watchlist.json` risk_profile.
- E1 triggers load change conditions from `watchlist.json` previous_analyses and evaluate using the type-specific logic in V1.1-ADDENDUM.md Section 3.3.
- D3 (insider activity) should filter out automatic/10b5-1 transactions where detectable (transaction code "A").

**Testing**: Test each trigger category independently. Use known data — for example, TSLA should fire A1 (Stage 3), B5 (RS breakdown), D2 (earnings deterioration). AAPL should fire B1 (RSI near 70). Create a synthetic prior scan to test state change detection.

### Phase C: Dashboard Formatter (`src/dashboard.py`) — 2-3 hours

```python
def generate_dashboard(scan_results: dict, risk_profile: str,
                       scan_duration: float) -> str:
    """Main entry: returns complete markdown string for daily_scan.md."""

def format_portfolio_summary(portfolio_metrics: dict) -> str:
    """Portfolio value, daily change, P&L, cash allocation."""

def format_alerts(triggers: list[dict]) -> str:
    """Alerts grouped by priority: 🔴 CRITICAL → ⚠️ WARNING → 💡 INFO."""

def format_holdings_table(holdings: list[dict]) -> str:
    """Holdings with price, P&L, weight, indicators, flags."""

def format_watchlist_table(watchlist: list[dict]) -> str:
    """Watchlist with price, indicators, CAN SLIM, flags."""

def format_recommended_actions(triggers: list[dict],
                                concentration: dict) -> str:
    """Actionable recommendations based on triggers and concentration."""
```

**Testing**: Generate a dashboard with mock data. Verify markdown renders correctly. Verify alerts are sorted by priority. Verify tables are aligned.

### Phase D: Integration Testing — 1-2 hours

- Run full scan with real watchlist (5-10 stocks)
- Verify all 18 trigger conditions produce correct flags for known stocks
- Verify dashboard renders cleanly in a markdown viewer
- Run scan twice in sequence to verify state change detection works (second run should detect any changes from first)
- Test with both risk-neutral and risk-averse to confirm threshold differences
- Verify `scan_data.json` is saved correctly and loadable

## V1.1 Key Constraints

1. **No LLM tokens in Tier 1.** The scanner is pure Python. If you find yourself calling Claude API, you're overcomplicating it.
2. **Reuse existing modules only.** `data_utils.py` and `indicators.py` are not modified. If a new computation is needed, add it to `portfolio.py` or `scanner.py`.
3. **No new Python packages.** Everything runs on yfinance + pandas + numpy + requests.
4. **Rate limit yfinance.** Stagger API calls with 0.5s delay between tickers. Pull S&P 500 and sector ETFs only once each.
5. **watchlist.json is user-maintained.** After a DualEdge run, the user manually updates `previous_analyses`. Auto-population is V1.2.
6. **State change detection requires a prior scan.** First run establishes baselines only. Triggers A1/A2/A3/A4/B5 don't fire on first run.

## V1.1 Testing Checklist

Before considering V1.1 complete, verify:

- [ ] `watchlist.json` loads and validates correctly (handles missing optional fields)
- [ ] `compute_holding_metrics()` produces correct P&L for known positions
- [ ] `compute_portfolio_metrics()` aggregates correctly
- [ ] `compute_concentration()` flags single stock > 25%, sector > 40%, top-3 > 60%
- [ ] `compute_correlation_matrix()` produces valid correlation values (-1 to 1)
- [ ] Scanner pulls data for all watchlist stocks without errors
- [ ] S&P 500 data is pulled once and reused (not per-ticker)
- [ ] Sector ETFs are pulled once per sector (not per-stock)
- [ ] All 18 trigger conditions are evaluated per stock
- [ ] Risk-neutral and risk-averse produce different trigger thresholds for B1, B2, B3
- [ ] State change triggers (A1-A4, B5) don't fire on first run (no prior scan)
- [ ] State change triggers fire correctly on second run when data changes
- [ ] E1 (change condition met) correctly evaluates each condition type
- [ ] E2 (staleness) correctly calculates days since last analysis
- [ ] D3 (insider) filters out 10b5-1 plan transactions
- [ ] Dashboard markdown renders cleanly
- [ ] Alerts sorted by priority (🔴 → ⚠️ → 💡)
- [ ] Holdings table shows all required columns
- [ ] Watchlist table shows all required columns
- [ ] Recommended actions are generated for triggered stocks
- [ ] `scan_data.json` saves and loads correctly
- [ ] Full 20-stock scan completes in < 60 seconds
- [ ] Scanner runs as standalone script: `python src/scanner.py`

## V1.1 Quick Start

If you're Claude Code starting V1.1 implementation:

1. Read `V1.1-ADDENDUM.md` completely — it has the full trigger specifications with formulas
2. Verify existing V1 modules work: `python -c "from src.data_utils import validate_ticker; print(validate_ticker('AAPL'))"`
3. Create `watchlist.json` with Sandip's actual holdings and watchlist
4. Build `src/portfolio.py` (test with sample holdings)
5. Build `src/scanner.py` — implement trigger evaluation one category at a time (A, then B, then C, then D, then E)
6. Build `src/dashboard.py` (test with mock scan results first, then real data)
7. Run integration test: full scan with real watchlist
8. Run scan twice to verify state change detection
9. Test with both risk profiles
