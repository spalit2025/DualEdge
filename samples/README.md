# Sample Analyses

These are real analyses produced by the DualEdge system, not manually written. They demonstrate the full output quality including framework-by-framework analysis, debate protocol, and final recommendations.

## What's Here

### [NVDA Risk-Averse: Consensus SELL](nvda-risk-averse-final-report.md)
Both agents independently reached SELL with 7/10 confidence. Demonstrates how risk-averse thresholds (25% margin of safety requirement, stricter RSI/volatility sensitivity) can flip a stock that's BUY under risk-neutral to SELL. Wide moat and 8/9 F-Score acknowledged, but 46x P/E with zero margin of safety fails risk-averse criteria.

### [AAPL Risk-Neutral: Split Decision BUY](aapl-split-decision-final-report.md)
The classic fundamental vs. technical disagreement. Value Analyst says SELL (overvalued at 3.5x EPV). Technical Analyst says BUY (confirmed Stage 2 advance). Two rounds of debate, neither agent budges, tiebreaker goes to Technical on higher confidence (7 vs 6).

### [AAPL Debate Log](aapl-debate-log.md)
The full debate transcript showing how the two agents engage with each other's evidence. This is the best demonstration of the adversarial analysis pattern -- watch the Value Analyst counter the technical trend with valuation math, and the Technical Analyst counter the valuation concern with price action.

## More Analyses

The complete set of analyses (6 stocks) is in the [`analysis/`](../analysis/) directory:
- **AAPL** -- Split Decision BUY (risk-neutral)
- **TSLA** -- Split Decision SELL (risk-neutral, 401x P/E)
- **NVDA** -- BUY risk-neutral, SELL risk-averse (same stock, opposite calls)
- **AMZN** -- Split Decision SELL
- **UBER** -- Split Decision SELL
- **HIMS** -- Split Decision SELL
