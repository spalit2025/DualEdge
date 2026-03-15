# DualEdge

**Two AI analysts. Twelve investment frameworks. One structured debate.**

DualEdge is a dual-agent stock analysis system where a Value Analyst and a Technical Analyst independently evaluate stocks using 12 proven investment frameworks, then debate their disagreements to produce a transparent, conviction-scored recommendation.

The oldest tension in investing is fundamental value versus technical momentum. DualEdge doesn't pick a side -- it formalizes this tension into a productive, evidence-based decision process.

---

## How It Works

```
USER INPUT: NVDA + risk-neutral
         |
         v
+--------------------------------------------------+
|              LEAD AGENT (CIO)                     |
|  Validates ticker, spawns two analyst agents      |
|  Orchestrates debate when agents disagree         |
|  Produces final consolidated report               |
+----------+------------------------+---------------+
           | spawn                  | spawn
  +--------v--------+     +--------v--------------+
  | VALUE ANALYST   |     | TECHNICAL ANALYST      |
  |                 |     |                        |
  | Graham MoS      |     | Weinstein Staging      |
  | Buffett Moat    |     | O'Neil CAN SLIM       |
  | Damodaran DCF   |     | Relative Strength      |
  | Lynch PEG       |     | Volatility Regime      |
  | Piotroski F     |     | Wyckoff Volume         |
  | Insider/Analyst |     | Mean Reversion         |
  +--------+--------+     +--------+--------------+
           |                        |
           v                        v
   fundamental_analysis.md   technical_analysis.md
           |                        |
           +----------+-------------+
                      v
           +---------------------+
           | DEBATE PHASE        |
           | AGREE? -> Consensus |
           | DISAGREE? -> Debate |
           | DEADLOCK? -> Tiebreak|
           +----------+----------+
                      v
              final_report.md
```

When both agents agree, you get a high-conviction consensus. When they disagree, the debate protocol forces each agent to engage with the other's evidence -- and the resulting split decision preserves both perspectives with full transparency.

---

## The 12 Frameworks

<table>
<tr>
<th>Value Analyst (Fundamental)</th>
<th>Technical Analyst (Quantitative)</th>
</tr>
<tr>
<td>

**Graham's Margin of Safety** -- Earnings Power Value vs. market cap. Is there a cushion against error?

**Buffett's Economic Moat** -- Pricing power, switching costs, network effects. Can the business defend its position?

**Damodaran's Growth Reasonableness** -- Reverse DCF to extract implied growth. Is the market's expectation realistic?

**Lynch's PEG Check** -- Price/Earnings to Growth. Are you overpaying for growth?

**Piotroski F-Score** -- 9-point financial health scorecard across profitability, leverage, and efficiency.

**Insider & Analyst Sentiment** -- Follow the money. What are insiders and analysts actually doing?

</td>
<td>

**Weinstein Stage Analysis** -- 4-stage price cycle classification using the 30-week moving average.

**O'Neil CAN SLIM** -- Growth + momentum screen. Current earnings, annual growth, new highs, supply/demand, leadership.

**Relative Strength Analysis** -- Performance vs. S&P 500 and sector at 1m, 3m, 6m, 12m. Leader or laggard?

**Volatility Regime Assessment** -- Current vs. historical volatility, Bollinger squeeze detection, ATR trends.

**Wyckoff Volume Analysis** -- On-Balance Volume, accumulation vs. distribution, price-volume divergence.

**Mean Reversion Check** -- RSI extremes, distance from 200-day MA, price Z-score. Is it overextended?

</td>
</tr>
</table>

---

## The Debate in Action

When agents disagree, the debate protocol runs up to two rounds, cross-referencing each agent's "change conditions" against the other's evidence. Here's a real excerpt from the AAPL analysis:

> **Initial positions:** Value Analyst recommends SELL (6/10) -- stock trades at 3.5x earnings power value. Technical Analyst recommends BUY (7/10) -- confirmed Stage 2 advance with strong relative strength.
>
> **Round 1:** The Value Analyst acknowledges the technical trend but counters: "at 285.9% premium to earnings power value, the stock is priced for 15-18% sustained growth that is 2-3x the historical 6.9% EPS CAGR. Strong trends can persist in overvalued stocks, but the fundamental risk/reward is unfavorable."
>
> The Technical Analyst holds: "the market has already processed this information and the price action reflects it. The 30-week MA at $252.44 provides a clear risk management level."
>
> **Round 2:** The CIO cross-references change conditions. Neither agent's evidence satisfies the other's conditions for changing their mind.
>
> **Tiebreaker:** Technical Analyst wins on higher confidence (7 vs 6). Final recommendation: **BUY -- SPLIT DECISION**. Both perspectives are preserved in the report.

This is the core value of DualEdge: the disagreement is the feature, not the bug. The debate log gives you full transparency into *why* the recommendation landed where it did.

---

## Risk Profiles Change Recommendations

The same stock can get opposite recommendations depending on risk profile:

| Stock | Risk-Neutral | Risk-Averse | Why |
|-------|-------------|-------------|-----|
| NVDA | **BUY** 6/10 (Consensus) | **SELL** 7/10 (Consensus) | PEG of 0.51 is acceptable risk-neutral; 46x trailing P/E with zero margin of safety fails risk-averse thresholds |
| AAPL | **BUY** 7/10 (Split Decision) | -- | Tiebreaker: technical momentum outweighs valuation stretch |
| TSLA | **SELL** 7/10 (Split Decision) | -- | 401x P/E with -47% net income YoY; stage upgrade insufficient |

Risk-averse mode requires 25%+ margin of safety (vs. 10-15%), PEG below 1.5 (vs. 2.0), Piotroski F-Score of 6+ for BUY consideration, and flags volatility above 1.5x the 12-month average as a SELL signal.

---

## Daily Watchlist Scanner

DualEdge includes a zero-cost daily scanner that monitors your portfolio and watchlist without using any LLM tokens. It evaluates **18 trigger conditions** across 5 categories:

| Category | Triggers | What They Detect |
|----------|----------|-----------------|
| **Trend** | Weinstein stage change, MA crossovers, MA alignment shift | Structural trend reversals |
| **Momentum** | RSI extremes, extension from 200d MA, Z-score, RS breakdown | Overbought/oversold conditions |
| **Volume** | Volume spikes, OBV divergence, volume ratio shift, Bollinger squeeze | Institutional activity |
| **Valuation** | P/E extreme, earnings deterioration, insider activity spike | Fundamental shifts |
| **Prior Analysis** | Change condition met, analysis staleness | Your thesis may need revision |

The scanner connects to your prior DualEdge analyses -- when the specific "what would change my mind" conditions are met, it flags the stock for a full re-analysis. This closes the loop between deep analysis and daily monitoring.

```
$ python -m src.scanner

DualEdge Daily Scan -- 2026-02-11
Stocks Scanned: 29 | Triggers Fired: 47

CRITICAL: NVDA -- STAGE CHANGE: Stage 3 -> Stage 2
WARNING:  GOOG -- EXTENDED: +32.1% from 200d MA
WARNING:  UBER -- EARNINGS DETERIORATION: Q EPS $0.14 vs $3.21 (-95.6% YoY)
INFO:     VTI  -- BB SQUEEZE: Width percentile = 7.5% (expansion imminent)
```

See [How the Scanner Works](docs/scanner-explainer.md) for the full technical breakdown.

---

## Quick Start

### Prerequisites

- Python 3.10+
- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) with Agent Teams enabled

### Setup

```bash
git clone https://github.com/spalit2025/DualEdge.git
cd DualEdge
pip install -r requirements.txt

# Configure your watchlist
cp watchlist.json.example watchlist.json
# Edit watchlist.json with your holdings and watchlist
```

### Run the Daily Scanner (no LLM tokens)

```bash
python -m src.scanner
# Output: scans/YYYY-MM-DD/daily_scan.md
```

### Run a Full DualEdge Analysis (requires Claude Code)

```bash
claude
> Run DualEdge analysis for AAPL with risk-neutral risk profile.
```

The lead agent reads prompts from `src/prompts/`, spawns two analyst teammates, orchestrates the debate, and writes the final report to `analysis/AAPL/`.

---

## What Makes DualEdge Different

| Feature | DualEdge | Generic AI Stock Analysis | Paid Services |
|---------|----------|--------------------------|---------------|
| Adversarial agents | Two specialists that debate | Single agent, single perspective | N/A |
| Named frameworks | 12 established methodologies | "Analyze this stock" | Proprietary black box |
| Transparent reasoning | Full debate log with evidence | Summary only | Recommendation only |
| Change conditions | Explicit "what would flip this" | None | None |
| Risk profile sensitivity | Same stock, different recommendations | One-size-fits-all | Limited |
| Cost | Free (yfinance + SEC EDGAR) | API costs | $50-500/mo |
| Daily monitoring | 18-trigger scanner, zero LLM cost | None | Alerts (generic) |

---

## Sample Analyses

See the `analysis/` directory for complete reports:

- **[NVDA Risk-Neutral](analysis/NVDA/final_report_rn.md)** -- Consensus BUY 6/10. PEG favorable, wide moat, but technical signals ambiguous.
- **[NVDA Risk-Averse](analysis/NVDA/final_report.md)** -- Consensus SELL 7/10. Same stock, opposite recommendation. Zero margin of safety at 46x P/E.
- **[AAPL](analysis/AAPL/final_report.md)** -- Split Decision BUY 7/10. Full debate: Value says overpriced, Technical says trend is strong.
- **[TSLA](analysis/TSLA/final_report.md)** -- Split Decision SELL 7/10. 401x P/E, -47% net income. Stage upgrade insufficient.

Each analysis includes the full fundamental report, technical report, debate log, and final consolidated recommendation.

---

## Project Structure

```
DualEdge/
├── src/
│   ├── data_utils.py          # yfinance + SEC EDGAR data retrieval
│   ├── indicators.py          # 14 technical indicator computations
│   ├── scanner.py             # Daily watchlist scanner (18 triggers)
│   ├── portfolio.py           # P&L, concentration, correlation
│   ├── dashboard.py           # Markdown dashboard formatter
│   ├── sector_map.py          # Sector -> ETF mapping
│   └── prompts/               # Agent system prompts
│       ├── value_analyst.md
│       ├── technical_analyst.md
│       └── lead_agent.md
├── analysis/                  # Stock analysis outputs
│   ├── AAPL/                  # Full analysis with debate
│   ├── NVDA/                  # Risk-neutral + risk-averse
│   ├── TSLA/                  # Split decision example
│   └── .../
├── samples/                   # Curated showcase analyses
├── docs/
│   ├── investment-techniques-guide.md  # Deep dive into all 12 frameworks
│   └── scanner-explainer.md            # Technical breakdown of the scanner
├── templates/                 # Report output templates
├── tests/                     # 52 unit tests (indicators + portfolio)
├── PRD.md                     # Full product requirements
├── watchlist.json.example     # Sample watchlist configuration
└── requirements.txt           # Python dependencies (4 packages)
```

---

## Documentation

- **[Sample Analyses](samples/)** -- Curated showcase: consensus SELL, split decision BUY, and a full debate log
- **[Product Requirements (PRD.md)](PRD.md)** -- Full specification including agent prompts, framework definitions, debate protocol, and token budget
- **[Investment Techniques Guide](docs/investment-techniques-guide.md)** -- Deep dive into every analytical framework and scanner trigger
- **[Scanner Technical Breakdown](docs/scanner-explainer.md)** -- How the 18-trigger scanner works, step by step
- **[V1.1 Addendum](dualedge-v1.1-addendum.md)** -- Watchlist monitor specification with all trigger formulas

---

## Beyond Finance

The dual-agent debate architecture is generalizable. Any domain where confirmation bias is dangerous and multiple valid perspectives exist can benefit from structured adversarial analysis:

- **Code review**: Security analyst vs. performance engineer, debating tradeoffs
- **Medical diagnosis**: Specialist vs. generalist, with explicit "what would change my assessment" conditions
- **Policy analysis**: Economic impact vs. social impact, with transparent disagreement logging

DualEdge is a reference implementation of this pattern. The debate protocol, tiebreaker mechanism, and change-condition tracking are all reusable primitives.

---

## Built With

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) Agent Teams for multi-agent orchestration
- [yfinance](https://github.com/ranaroussi/yfinance) for market data
- [SEC EDGAR](https://www.sec.gov/edgar) for 10-K filing retrieval
- Python 3.10+ with pandas, numpy, requests

## License

[MIT](LICENSE)
