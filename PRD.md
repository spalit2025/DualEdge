# DualEdge — Product Requirements Document
## AI-Powered Dual-Agent Stock Analysis System
**Version**: 1.0
**Last Updated**: 2025-02-07
**Author**: Sandip
**Status**: Ready for Implementation

---

## 1. Product Overview

### 1.1 What Is DualEdge?

DualEdge is an AI-powered stock analysis system that uses two specialized analyst agents — a **Value Analyst** (fundamental analysis) and a **Technical Analyst** (quantitative/technical analysis) — to independently evaluate stocks, then debate their findings to produce a conviction-scored BUY or SELL recommendation.

Each agent applies 6 proven investment frameworks from established gurus (12 frameworks total). When agents disagree, a structured debate with an explicit tiebreaker protocol resolves the conflict, producing a transparent recommendation with full reasoning trail.

### 1.2 Core Value Proposition

- **Depth over breadth**: 12 named analytical frameworks (Graham, Buffett, Damodaran, Lynch, Piotroski, Weinstein, O'Neil, Wyckoff, etc.) applied systematically to every stock
- **Structured disagreement**: The fundamental vs. technical tension is the oldest debate in investing — DualEdge formalizes it into a productive, evidence-based decision process
- **Transparency**: Every recommendation includes the full analysis from both agents, the debate log, confidence scores, and explicit "what would change this call" conditions
- **Zero paid data dependencies**: Runs entirely on free APIs (yfinance + SEC EDGAR)

### 1.3 Target User

The primary user is the system builder (Sandip) — a finance professional using DualEdge for personal investment research and as a foundation for future AI-powered finance tools.

### 1.4 Success Criteria for V1

| Criteria | Target |
|----------|--------|
| Analyze a single stock end-to-end | Working for any US-listed equity |
| Both agents produce framework-based analysis | All 12 frameworks produce output |
| Debate mechanism resolves disagreements | Consensus or explicit split decision with tiebreaker |
| Output a structured stock analysis report | Markdown report with all sections populated |
| Support both risk profiles | Risk-Neutral and Risk-Averse produce different recommendations |
| Complete analysis within Max plan token budget | < 250K tokens per stock |

---

## 2. System Architecture

### 2.1 High-Level Architecture

```
USER INPUT: {ticker} + {risk_profile}
         │
         ▼
┌─────────────────────────────────────────────────┐
│              TEAM LEAD (CIO Agent)               │
│  • Receives user input                           │
│  • Spawns two teammates with full prompts         │
│  • Monitors task completion                       │
│  • Orchestrates debate when agents disagree       │
│  • Executes tiebreaker protocol if deadlocked     │
│  • Generates final consolidated report            │
└──────────┬────────────────────┬──────────────────┘
           │ spawn              │ spawn
  ┌────────▼────────┐ ┌────────▼──────────────┐
  │ TEAMMATE 1      │ │ TEAMMATE 2            │
  │ Value Analyst   │ │ Technical & Quant     │
  │                 │ │ Analyst               │
  │ 6 Frameworks:   │ │ 6 Frameworks:         │
  │ 1. Graham MoS   │ │ 1. Weinstein Staging  │
  │ 2. Buffett Moat │ │ 2. O'Neil CAN SLIM   │
  │ 3. Damodaran    │ │ 3. Relative Strength  │
  │ 4. Lynch PEG    │ │ 4. Volatility Regime  │
  │ 5. Piotroski F  │ │ 5. Wyckoff Volume     │
  │ 6. Insider/     │ │ 6. Mean Reversion     │
  │    Analyst      │ │                       │
  │                 │ │                       │
  │ Data Sources:   │ │ Data Sources:         │
  │ • SEC EDGAR     │ │ • yfinance OHLCV      │
  │ • yfinance      │ │ • S&P 500 benchmark   │
  │   financials    │ │ • Sector ETF          │
  └────────┬────────┘ └────────┬──────────────┘
           │ writes             │ writes
           ▼                    ▼
  fundamental_analysis.md  technical_analysis.md
           │                    │
           └────────┬───────────┘
                    ▼
  ┌─────────────────────────────────────────────┐
  │         DEBATE PHASE (Lead-Orchestrated)    │
  │                                             │
  │  AGREE? → Consensus report                  │
  │  DISAGREE? → Max 2 debate rounds            │
  │  STILL DISAGREE? → Tiebreaker protocol      │
  └─────────────────┬───────────────────────────┘
                    ▼
  ┌─────────────────────────────────────────────┐
  │  analysis/{ticker}/                         │
  │  ├── fundamental_analysis.md                │
  │  ├── technical_analysis.md                  │
  │  ├── debate_log.md                          │
  │  └── final_report.md                        │
  └─────────────────────────────────────────────┘
```

### 2.2 Component Inventory

| Component | Type | Description |
|-----------|------|-------------|
| `lead_agent` | Agent Teams Lead | Orchestrator — spawns teammates, runs debate, produces report |
| `value_analyst` | Agent Teams Teammate | Fundamental analysis using 6 guru frameworks |
| `technical_analyst` | Agent Teams Teammate | Technical/quantitative analysis using 6 guru frameworks |
| `data_utils.py` | Python module | Shared yfinance and SEC EDGAR data retrieval utilities |
| `indicators.py` | Python module | Technical indicator computation (MAs, RSI, Bollinger, OBV, etc.) |
| `report_template.md` | Template | Structured output format for final reports |

---

## 3. Functional Requirements

### 3.1 Input Requirements

#### FR-INPUT-01: Stock Ticker
- System accepts any valid US-listed equity ticker symbol (e.g., AAPL, TSLA, ZS)
- Validation: confirm ticker exists via yfinance before spawning agents
- Error handling: if invalid ticker, return clear error message without spawning agents

#### FR-INPUT-02: Risk Profile
- Two supported profiles: `risk-neutral` and `risk-averse`
- Default: `risk-neutral` if not specified
- Risk profile is passed to both agent prompts and modifies framework thresholds (see Section 4.5)

### 3.2 Value Analyst (Fundamental Agent) Requirements

#### FR-VA-01: Data Retrieval
The Value Analyst must retrieve the following data for the target stock:

| Data | Source | Required Fields |
|------|--------|----------------|
| Financial statements (annual + quarterly) | yfinance | Income statement, balance sheet, cash flow statement |
| Key ratios | yfinance / computed | P/E, P/B, EV/EBITDA, debt-to-equity, ROE, ROA, FCF yield, current ratio |
| 10-K filing (most recent) | SEC EDGAR API | Full text, with focus on: MD&A, Risk Factors, Financial Statements & Notes |
| Insider transactions | yfinance | `get_insider_transactions()` — last 12 months |
| Analyst estimates | yfinance | `analyst_price_targets` (low, mean, median, high, current), `recommendations` |

#### FR-VA-02: Framework Analysis
The Value Analyst must execute all 6 analytical frameworks in sequence:

**Framework 1 — Graham's Margin of Safety**
- Calculate Earnings Power Value (EPV): normalized earnings ÷ cost of capital (use 10-year Treasury yield + 5% equity risk premium)
- Compare EPV to current market capitalization
- Assess P/E relative to 5-year historical average and sector median
- Output: margin of safety percentage, verdict (adequate / insufficient / negative)

**Framework 2 — Buffett's Economic Moat**
- From 10-K MD&A and business description, evaluate:
  - Pricing power: evidence of ability to raise prices
  - Switching costs: customer lock-in mechanisms
  - Network effects: product value scales with user base
  - Cost advantages: structural cost advantages over competitors
- Output: moat rating (None / Narrow / Wide), supporting evidence from 10-K

**Framework 3 — Damodaran's Growth Reasonableness**
- Calculate implied growth rate from current P/E using simplified reverse DCF
- Compare to: actual reinvestment rate × return on invested capital (ROIC)
- Compare to: historical 3-year and 5-year revenue CAGR
- Output: market expectation assessment (reasonable / optimistic / pessimistic)

**Framework 4 — Lynch's PEG Check**
- Calculate PEG ratio: trailing P/E ÷ forward earnings growth rate (analyst consensus)
- If analyst estimate unavailable, use 3-year historical EPS CAGR
- Output: PEG value, assessment (undervalued <1.0 / fair 1.0-1.5 / overvalued >2.0)

**Framework 5 — Piotroski F-Score**
- Compute all 9 F-Score components:
  - Profitability (4 signals): positive ROA, positive operating cash flow, improving ROA, cash flow > net income
  - Leverage (3 signals): decreasing long-term debt/assets, increasing current ratio, no new equity issuance
  - Efficiency (2 signals): improving gross margin, improving asset turnover
- Output: score (0-9), trajectory (improving / stable / deteriorating)

**Framework 6 — Insider & Analyst Sentiment**
- Summarize net insider buying vs. selling over past 6 months
- Flag cluster insider purchases (3+ insiders buying within 30 days)
- Report: mean analyst price target vs. current price (% upside/downside)
- Report: distribution of analyst ratings (strong buy / buy / hold / sell / strong sell)
- Flag any rating changes in past 90 days
- Output: insider signal (bullish / neutral / bearish), analyst signal (bullish / neutral / bearish)

#### FR-VA-03: Recommendation Output
- Binary recommendation: BUY or SELL (no HOLD)
- Confidence score: 1-10 integer
- Key driver: one sentence explaining the primary reason
- Change condition: explicit statement of what evidence would flip the recommendation
- All output written to `analysis/{ticker}/fundamental_analysis.md`

#### FR-VA-04: Output Format
```markdown
## VALUE ANALYST REPORT: {TICKER}
**Risk Profile**: {risk_profile}

### SUMMARY
| Field | Value |
|-------|-------|
| RECOMMENDATION | BUY / SELL |
| CONFIDENCE | X / 10 |
| KEY DRIVER | [one sentence] |
| CHANGE CONDITION | [what would flip this call] |

### 1. Graham's Margin of Safety
[analysis...]

### 2. Buffett's Economic Moat
[analysis...]

### 3. Damodaran's Growth Reasonableness
[analysis...]

### 4. Lynch's PEG Check
[analysis...]

### 5. Piotroski F-Score
[analysis...]

### 6. Insider & Analyst Sentiment
[analysis...]

### DATA TABLES
[key financial metrics table]
[insider transaction summary table]
[analyst estimates table]
```

### 3.3 Technical & Quantitative Analyst Requirements

#### FR-TA-01: Data Retrieval
The Technical Analyst must retrieve the following data:

| Data | Source | Specification |
|------|--------|--------------|
| Daily OHLCV | yfinance | Past 18 months (12 months analysis + 6 months MA lookback) |
| Weekly OHLCV | yfinance | Past 3 years (for 30-week MA / Weinstein staging) |
| S&P 500 daily data | yfinance (`^GSPC`) | Same period as stock (for relative strength) |
| Sector ETF daily data | yfinance | Relevant sector ETF for the stock (for relative strength) |
| Quarterly EPS | yfinance | Last 4 quarters (for CAN SLIM earnings check) |

**Sector ETF Mapping** (for relative strength calculation):

| Sector | ETF |
|--------|-----|
| Technology | XLK |
| Healthcare | XLV |
| Financials | XLF |
| Consumer Discretionary | XLY |
| Consumer Staples | XLP |
| Industrials | XLI |
| Energy | XLE |
| Materials | XLB |
| Utilities | XLU |
| Real Estate | XLRE |
| Communication Services | XLC |

The agent should determine the stock's sector from yfinance's `info['sector']` and select the appropriate ETF.

#### FR-TA-02: Indicator Computation
The Technical Analyst must compute the following indicators via a Python script:

| Indicator | Formula / Method | Parameters |
|-----------|-----------------|------------|
| SMA (50, 150, 200-day) | Simple moving average of close prices | Windows: 50, 150, 200 |
| 30-week MA | Simple moving average of weekly close prices | Window: 30 weeks |
| Annualized Return | `R_ann = (1 + R_cum)^(252/n) - 1` | n = trading days in period |
| Annualized Volatility | `σ_ann = σ_daily × √252` | Daily std dev of log returns |
| RSI (14-day) | Wilder's smoothed RS method | Period: 14 |
| Bollinger Bands | 20-day SMA ± 2 × 20-day std dev | Period: 20, Width: 2σ |
| Bollinger Band Width | `(Upper - Lower) / Middle` | Derived |
| ATR (14-day) | Wilder's smoothed True Range | Period: 14 |
| OBV | Cumulative volume × sign of price change | Running total |
| OBV 20-day MA | SMA of OBV | Window: 20 |
| Relative Strength vs SPX | `stock_return / spx_return` | At 1m, 3m, 6m, 12m |
| Relative Strength vs Sector | `stock_return / sector_etf_return` | At 1m, 3m, 6m, 12m |
| Volume Ratio | `avg_vol_up_days / avg_vol_down_days` | Past 60 trading days |
| 52-week High/Low | Max/Min close over 252 trading days | Rolling |
| Distance from 52w High | `(current - 52w_high) / 52w_high` | Percentage |
| Price Z-score | `(price - 6mo_mean) / 6mo_std` | 6-month lookback |

All indicators must be computed programmatically (no manual calculation). The script should handle edge cases (insufficient data, missing values) gracefully.

#### FR-TA-03: Framework Analysis
The Technical Analyst must execute all 6 analytical frameworks:

**Framework 1 — Weinstein Stage Analysis**
- Determine 30-week MA slope (rising / flat / falling)
- Determine price position relative to 30-week MA (above / at / below)
- Assess volume pattern (expanding / contracting / mixed)
- Classify stage:
  - Stage 1 (Basing): flat 30w MA, price oscillating around it, low volume
  - Stage 2 (Advancing): rising 30w MA, price above it, expanding volume on advances
  - Stage 3 (Topping): flattening 30w MA, price crossing below, mixed volume
  - Stage 4 (Declining): falling 30w MA, price below it, volume on declines
- Output: stage classification, confidence in classification, implications

**Framework 2 — O'Neil CAN SLIM Quantitative**
- C (Current earnings): Is most recent quarterly EPS > prior year same quarter? Is acceleration present (sequential quarters accelerating)?
- A (Annual earnings): 3-year EPS CAGR > 25%?
- N (New highs): Is price within 5% of 52-week high?
- S (Supply/demand): Volume ratio (up days / down days) > 1.0?
- L (Leader): 6-month relative strength vs. S&P 500 in top quartile?
- Output: criteria met count (0-5), pass/fail per criterion

**Framework 3 — Relative Strength Analysis**
- RS vs. S&P 500 at 1m, 3m, 6m, 12m — tabulate
- RS trajectory: improving (accelerating outperformance) or deteriorating?
- RS vs. sector ETF — separate stock alpha from sector beta
- Output: RS scores, trajectory assessment, alpha vs. beta decomposition

**Framework 4 — Volatility Regime Assessment**
- Current annualized volatility vs. 12-month average volatility
- Bollinger Band Width: percentile relative to past 12 months (squeeze detection)
- ATR trend: increasing (last 20 days vs. prior 20 days) or decreasing?
- Volatility regime: low / normal / elevated / extreme
- Output: regime classification, implications for risk profile

**Framework 5 — Wyckoff Volume Analysis**
- OBV trend vs. price trend: confirming or diverging?
- Volume on up days vs. down days (60-day window)
- Identify accumulation (rising OBV, flat/rising price) or distribution (falling OBV, flat/falling price)
- Output: accumulation/distribution assessment, OBV divergence flag

**Framework 6 — Mean Reversion Check**
- RSI(14): overbought (>70), neutral (30-70), oversold (<30)
- Distance from 200-day MA: extended if >15% above or below
- Price Z-score: extreme if |Z| > 2.0
- Output: extension assessment, reversion probability signal

#### FR-TA-04: Recommendation Output
Same format as FR-VA-03:
- Binary recommendation: BUY or SELL
- Confidence score: 1-10
- Key driver: one sentence
- Change condition: what evidence would flip the call
- Written to `analysis/{ticker}/technical_analysis.md`

#### FR-TA-05: Output Format
```markdown
## TECHNICAL & QUANTITATIVE ANALYST REPORT: {TICKER}
**Risk Profile**: {risk_profile}

### SUMMARY
| Field | Value |
|-------|-------|
| RECOMMENDATION | BUY / SELL |
| CONFIDENCE | X / 10 |
| KEY DRIVER | [one sentence] |
| CHANGE CONDITION | [what would flip this call] |

### 1. Weinstein Stage Analysis
[analysis + stage classification...]

### 2. O'Neil CAN SLIM Quantitative
[analysis + criteria scorecard...]

### 3. Relative Strength Analysis
[analysis + RS tables...]

### 4. Volatility Regime Assessment
[analysis + regime classification...]

### 5. Wyckoff Volume Analysis
[analysis + accumulation/distribution assessment...]

### 6. Mean Reversion Check
[analysis + extension signals...]

### INDICATOR TABLE
[full computed indicator table with all values]
```

### 3.4 Team Lead (CIO Agent) Requirements

#### FR-LEAD-01: Initialization
- Validate ticker exists via yfinance (quick check: `yfinance.Ticker(ticker).info`)
- Create analysis directory: `analysis/{ticker}/`
- Spawn Value Analyst teammate with full system prompt (Section 4.1) and parameters
- Spawn Technical Analyst teammate with full system prompt (Section 4.2) and parameters
- Monitor both teammates until analysis files are written

#### FR-LEAD-02: Consensus Check
- Read both analysis files after teammates complete
- Extract RECOMMENDATION and CONFIDENCE from each
- Determine: AGREE or DISAGREE

#### FR-LEAD-03: Debate Protocol (when agents DISAGREE)

**Round 1:**
1. Message Value Analyst: "The Technical Analyst recommends {TA_recommendation} with confidence {TA_confidence}/10. Their key findings: {TA_summary}. Do you maintain your {VA_recommendation} position, or do you revise? Provide specific evidence for your stance."
2. Message Technical Analyst: "The Value Analyst recommends {VA_recommendation} with confidence {VA_confidence}/10. Their key findings: {VA_summary}. Do you maintain your {TA_recommendation} position, or do you revise? Provide specific evidence for your stance."
3. Check for convergence.

**Round 2 (if still disagreed):**
1. Extract each agent's CHANGE CONDITION from their analysis
2. Cross-reference: Does Agent A's analysis contain evidence that meets Agent B's change condition?
3. If yes: present that evidence to the relevant agent and ask for revised position
4. If no: proceed to tiebreaker

**Tiebreaker (if still deadlocked after 2 rounds):**
1. Compare confidence scores — higher confidence recommendation wins
2. Flag the report as `SPLIT DECISION`
3. Preserve both agents' perspectives in the final report
4. Note: "This recommendation is based on a split decision. The {winning_agent} had higher conviction ({score}/10 vs {score}/10). Review both analyses before acting."

#### FR-LEAD-04: Final Report Generation
Produce `analysis/{ticker}/final_report.md` with this structure:

```markdown
# DualEdge Stock Analysis: {TICKER}
**Date**: {date}
**Risk Profile**: {risk_profile}
**Decision**: {CONSENSUS / SPLIT DECISION}

---

## RECOMMENDATION
| Field | Value |
|-------|-------|
| RECOMMENDATION | BUY / SELL |
| CONFIDENCE | X / 10 |
| DECISION TYPE | Consensus / Split Decision |
| KEY DRIVER | [synthesis of both agents' primary signals] |

## AGREEMENTS
[Where both agents align — bullet points of shared conclusions]

## DISAGREEMENTS
[Where agents diverge — each agent's position with evidence]

## CHANGE CONDITIONS
[What specific new evidence would change this recommendation]

## RISK CONSIDERATIONS
[Risk factors specific to the selected risk profile]

---

## FUNDAMENTAL ANALYSIS SUMMARY
[Condensed summary of Value Analyst's 6 frameworks]

## TECHNICAL ANALYSIS SUMMARY
[Condensed summary of Technical Analyst's 6 frameworks]

## DEBATE LOG
[Full record of debate rounds, if any]

---

## APPENDIX: Full Agent Reports
- [fundamental_analysis.md](./fundamental_analysis.md)
- [technical_analysis.md](./technical_analysis.md)
```

#### FR-LEAD-05: Debate Logging
All debate exchanges must be written to `analysis/{ticker}/debate_log.md` including:
- Each agent's initial position
- Each round's exchanges (what was presented, how each agent responded)
- Tiebreaker outcome if triggered
- Final consensus statement

### 3.5 Risk Profile Behavior

Risk profile modifies framework thresholds and agent behavior:

| Framework | Risk-Neutral | Risk-Averse |
|-----------|-------------|-------------|
| Graham Margin of Safety | Accept 10-15% margin | Require 25%+ margin |
| PEG Ratio | Accept up to 2.0 | Require < 1.5 |
| Piotroski F-Score | Note score, no hard threshold | Require F-Score ≥ 6 for BUY |
| Insider Selling | Neutral unless extreme | Weight insider selling as bearish signal |
| Weinstein Staging | BUY in Stage 2 | Only BUY in early Stage 2 with volume confirmation |
| Volatility | Note but don't penalize | Flag if > 1.5x 12-month average; bias toward SELL |
| RSI Extremes | Note as context | Overbought (>70) = strong SELL signal |
| Extension from 200d MA | Note as context | >15% above = penalize BUY case |

### 3.6 File System Structure

```
DualEdge/                                # Project root
├── CLAUDE.md                            # Implementation guide
├── PRD.md                               # Product requirements
├── src/
│   ├── data_utils.py                    # yfinance + SEC EDGAR data retrieval
│   ├── indicators.py                    # Technical indicator computations
│   ├── sector_map.py                    # Sector → ETF mapping
│   └── prompts/
│       ├── value_analyst.md             # Value Analyst system prompt
│       ├── technical_analyst.md         # Technical Analyst system prompt
│       └── lead_agent.md               # Lead/CIO system prompt
├── templates/
│   ├── fundamental_report.md            # Output template
│   ├── technical_report.md              # Output template
│   └── final_report.md                  # Output template
│
├── analysis/                            # Runtime output (per-stock)
│   └── {TICKER}/
│       ├── fundamental_analysis.md
│       ├── technical_analysis.md
│       ├── debate_log.md
│       └── final_report.md
```

---

## 4. Agent System Prompts

### 4.1 Value Analyst System Prompt

```
You are "The Value Analyst" — a senior fundamental equity analyst who synthesizes
multiple investment frameworks to produce rigorous, evidence-based stock analysis.

For {TICKER}, conduct a layered fundamental analysis using these frameworks
sequentially. Your risk profile is: {RISK_PROFILE}.

STEP 1 — DATA GATHERING
Use the Python utilities in src/data_utils.py to pull:
- Annual/quarterly financials (income statement, balance sheet, cash flow)
- Key ratios: P/E, P/B, EV/EBITDA, debt-to-equity, ROE, ROA, FCF yield
- Insider transactions (last 12 months)
- Analyst price targets and recommendation trends
Use SEC EDGAR API to retrieve the most recent 10-K filing. Focus on:
  - MD&A (Management Discussion & Analysis)
  - Risk Factors
  - Financial Statements & Notes
If the 10-K is too large for context, prioritize MD&A and Risk Factors.

STEP 2 — MULTI-FRAMEWORK ANALYSIS

(A) Graham's Margin of Safety
- Calculate Earnings Power Value: normalized earnings / cost of capital
  (cost of capital = 10-year Treasury yield + 5% equity risk premium)
- Compare EPV to current market cap
- Assess P/E relative to 5-year historical average and sector median
- Verdict: margin of safety percentage and adequacy
- Risk-averse threshold: require 25%+ margin. Risk-neutral: 10-15% acceptable.

(B) Buffett's Economic Moat (from 10-K qualitative analysis)
- Evaluate pricing power: can the company raise prices without losing customers?
- Assess switching costs: how painful is it for customers to leave?
- Identify network effects: does the product get better with more users?
- Analyze cost advantages: structural cost benefits over competitors?
- Rate moat: None / Narrow / Wide

(C) Damodaran's Growth Reasonableness
- Calculate implied growth rate from current P/E using simplified reverse DCF
- Compare to actual reinvestment rate × ROIC
- Compare to historical 3-year and 5-year revenue CAGR
- Assess whether market expectations are reasonable, optimistic, or pessimistic

(D) Lynch's PEG Check
- Calculate PEG ratio: trailing P/E ÷ forward earnings growth rate (analyst consensus)
- If analyst estimate unavailable, use 3-year historical EPS CAGR
- Risk-averse: require PEG < 1.5. Risk-neutral: accept up to 2.0.
- Assessment: undervalued (<1.0) / fair (1.0-1.5) / overvalued (>2.0)

(E) Piotroski F-Score
- Compute all 9 components across Profitability (4), Leverage (3), Efficiency (2)
- Score 0-9 and note trajectory (improving / stable / deteriorating)
- Risk-averse: require F-Score ≥ 6 for BUY consideration

(F) Insider & Analyst Sentiment
- Summarize net insider buying vs. selling over past 6 months
- Flag cluster insider purchases (3+ insiders buying within 30 days)
- Report mean analyst price target vs. current price (% upside/downside)
- Report rating distribution and any changes in past 90 days
- Risk-averse: weight insider selling more heavily as bearish signal

STEP 3 — SYNTHESIS & RECOMMENDATION
- Note where the frameworks AGREE (high conviction signals)
- Note where they CONFLICT (explain the tension)
- Provide a final BUY or SELL recommendation with confidence level (1-10)
- State explicitly: "What specific evidence would change my recommendation?"

STEP 4 — OUTPUT
Write your complete analysis to:
analysis/{TICKER}/fundamental_analysis.md

Use the template format specified in the project requirements. Include the
SUMMARY table at the top with RECOMMENDATION, CONFIDENCE, KEY DRIVER,
and CHANGE CONDITION fields.
```

### 4.2 Technical & Quantitative Analyst System Prompt

```
You are "The Technical & Quantitative Analyst" — a senior market analyst who
combines classical technical analysis frameworks with quantitative rigor to
assess price trends, momentum, and risk.

For {TICKER}, conduct a multi-framework technical and quantitative analysis.
Your risk profile is: {RISK_PROFILE}.

STEP 1 — DATA GATHERING
Use the Python utilities in src/data_utils.py to pull:
- Daily OHLCV data for the past 18 months
- Weekly OHLCV data for the past 3 years
- S&P 500 (^GSPC) data for same periods
- Relevant sector ETF data (use sector_map.py to determine correct ETF)
- Quarterly EPS data for past 4 quarters

STEP 2 — COMPUTE ALL INDICATORS
Use src/indicators.py to calculate all technical indicators.
Verify the output includes: MAs (50/150/200-day, 30-week), RSI, Bollinger Bands,
ATR, OBV, Relative Strength ratios, Volume Ratio, 52-week high/low distances,
and Price Z-score.

STEP 3 — MULTI-FRAMEWORK ANALYSIS

(A) Weinstein Stage Analysis
- Classify current stage (1-4) based on 30-week MA slope, price position, volume
- Risk-averse: Only BUY in early Stage 2 with volume confirmation
- Risk-neutral: BUY in Stage 2, consider in late Stage 1 with confirmation

(B) O'Neil CAN SLIM Quantitative Screen
- Score 5 quantitative criteria: C, A, N, S, L (each pass/fail)
- Report count met and detail per criterion

(C) Relative Strength Analysis
- Tabulate RS vs. S&P 500 at 1m, 3m, 6m, 12m
- Assess RS trajectory: improving or deteriorating
- Separate stock alpha from sector beta using sector ETF comparison

(D) Volatility Regime Assessment
- Current vs. 12-month average annualized volatility
- Bollinger Band Width percentile (squeeze detection)
- ATR trend direction
- Risk-averse: flag if current vol > 1.5x 12-month average

(E) Wyckoff Volume Analysis
- OBV trend vs. price trend: confirming or diverging
- Volume on up days vs. down days
- Accumulation vs. distribution assessment

(F) Mean Reversion Check
- RSI(14): overbought/neutral/oversold
- Distance from 200-day MA
- Price Z-score: extreme if |Z| > 2.0
- Risk-averse: overbought (>70) = strong SELL signal; >15% above 200d MA = penalize BUY

STEP 4 — SYNTHESIS & RECOMMENDATION
- Note where the frameworks AGREE (high conviction signals)
- Note where they CONFLICT (explain the tension)
- Provide a final BUY or SELL recommendation with confidence level (1-10)
- State explicitly: "What specific evidence would change my recommendation?"

STEP 5 — OUTPUT
Write your complete analysis to:
analysis/{TICKER}/technical_analysis.md

Use the template format specified in the project requirements. Include the
SUMMARY table at the top and the full INDICATOR TABLE with all computed values.
```

### 4.3 Lead Agent (CIO) Prompt

```
You are the "Chief Investment Officer" — the lead agent coordinating DualEdge,
a dual-agent stock analysis system. Your role is to orchestrate two specialist
analysts and produce a final investment recommendation.

SETUP:
1. Validate the ticker {TICKER} exists using yfinance
2. Create directory: analysis/{TICKER}/
3. Spawn Teammate 1: "Value Analyst" with the system prompt from
   src/prompts/value_analyst.md
   Replace {TICKER} and {RISK_PROFILE} in the prompt.
4. Spawn Teammate 2: "Technical & Quantitative Analyst" with the system prompt from
   src/prompts/technical_analyst.md
   Replace {TICKER} and {RISK_PROFILE} in the prompt.

MONITORING:
- Wait for both teammates to complete their analysis
- Confirm both output files exist:
  analysis/{TICKER}/fundamental_analysis.md
  analysis/{TICKER}/technical_analysis.md

CONSENSUS CHECK:
- Read both files
- Extract RECOMMENDATION and CONFIDENCE from each SUMMARY table
- If both recommend the same (both BUY or both SELL): proceed to REPORT
- If they disagree: proceed to DEBATE

DEBATE PROTOCOL:
Round 1:
- Message Value Analyst with Technical Analyst's summary and recommendation.
  Ask: "Do you maintain your position or revise? Cite specific evidence."
- Message Technical Analyst with Value Analyst's summary and recommendation.
  Ask: "Do you maintain your position or revise? Cite specific evidence."
- Check for convergence.

Round 2 (if still disagreed):
- Extract each agent's CHANGE CONDITION
- Cross-reference: does one agent's analysis contain evidence matching the
  other's change condition?
- If yes: present that evidence and ask for revised position
- If no: proceed to tiebreaker

Tiebreaker:
- Higher confidence score wins
- Flag report as SPLIT DECISION
- Preserve both perspectives

REPORT:
Generate analysis/{TICKER}/final_report.md using the template
structure. Include all sections: recommendation summary, agreements,
disagreements, change conditions, risk considerations, both agent summaries,
and debate log.

Also generate analysis/{TICKER}/debate_log.md with the full
record of any debate exchanges.
```

---

## 5. Non-Functional Requirements

### 5.1 Performance
| Requirement | Target |
|------------|--------|
| Total token consumption per stock | < 250K tokens |
| Value Analyst analysis time | < 10 minutes |
| Technical Analyst analysis time | < 5 minutes |
| Debate resolution | < 5 minutes (max 2 rounds) |
| End-to-end per stock | < 20 minutes |

### 5.2 Reliability
| Requirement | Handling |
|------------|---------|
| yfinance API failure | Retry 3x with 2-second delay; fail gracefully with clear error |
| SEC EDGAR rate limit | 100ms delay between requests; retry with exponential backoff |
| 10-K too large for context | Truncate to MD&A + Risk Factors + Financial Statements |
| Teammate failure | Lead detects missing output file after timeout; reports error |
| Debate non-convergence | Hard limit: 2 rounds → tiebreaker → human escalation note |
| Invalid ticker | Validate before spawning agents; return error message |
| Missing data (e.g., no insider transactions) | Agent notes data unavailability; framework scored as N/A |

### 5.3 Data Freshness
| Data Type | Acceptable Staleness |
|-----------|---------------------|
| OHLCV price data | Same trading day (or most recent close) |
| Financial statements | Most recent filing (quarterly) |
| 10-K filing | Most recent annual (typically < 12 months old) |
| Insider transactions | Within past 30 days of SEC filing |
| Analyst estimates | Current consensus (yfinance real-time) |

### 5.4 Token Budget Breakdown
| Phase | Budget | Notes |
|-------|--------|-------|
| Lead setup + orchestration | 15K | Spawn, monitor, coordinate |
| Value Analyst | 120K | 10-K ingestion is primary cost driver |
| Technical Analyst | 40K | Mostly computation + interpretation |
| Debate (if triggered) | 30K | 2 rounds max |
| Report generation | 15K | Synthesis |
| **Buffer** | **30K** | Retries, error handling |
| **Total** | **250K** | Max plan allocation per analysis |

---

## 6. External Dependencies

### 6.1 APIs

| API | Auth | Rate Limit | Cost | Usage |
|-----|------|-----------|------|-------|
| **yfinance** | None | Unofficial; ~2000 req/hour reasonable | Free | Financials, OHLCV, insider data, analyst data |
| **SEC EDGAR** | User-Agent header with email | 10 req/sec | Free | 10-K/10-Q full text retrieval |

### 6.2 Python Packages

```
yfinance>=0.2.36
pandas>=2.0.0
numpy>=1.24.0
requests>=2.31.0
```

### 6.3 Claude Code Configuration

```json
{
  "env": {
    "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"
  }
}
```

---

## 7. Out of Scope for V1

| Feature | Reason | Target Version |
|---------|--------|---------------|
| Sentiment/news analysis agent | Simplification — absorbed key signals into Value Analyst | V1.1 |
| Multi-stock batch processing | Validate single-stock first | V1.1 |
| Automated backtesting pipeline | Focus on signal quality | V1.1 |
| MCP servers for data tools | Direct Python scripts sufficient for V1 | V1.1 |
| Portfolio construction / optimization | DualEdge is a stock analysis tool, not a portfolio manager | V2 |
| Confidence-weighted position sizing | Requires backtesting validation first | V2 |
| Web-based UI | CLI-first approach | V2 |
| Real-time / streaming analysis | Batch analysis per stock | V2 |
| Non-US equities | Focus on US-listed stocks with SEC filings | V2 |

---

## 8. Glossary

| Term | Definition |
|------|-----------|
| EPV | Earnings Power Value — normalized earnings divided by cost of capital |
| F-Score | Piotroski's 9-point financial health score |
| PEG | Price/Earnings to Growth ratio |
| ROIC | Return on Invested Capital |
| MoS | Margin of Safety — discount of market price vs. intrinsic value |
| OBV | On-Balance Volume — cumulative volume weighted by price direction |
| ATR | Average True Range — volatility measure |
| RS | Relative Strength — performance ratio vs. benchmark |
| CAN SLIM | O'Neil's growth + momentum stock selection criteria |
| Stage Analysis | Weinstein's 4-stage price cycle classification |
| OHLCV | Open, High, Low, Close, Volume — standard price data |
| 30w MA | 30-week moving average — key Weinstein indicator |
