# DualEdge Investment Techniques Guide

A deep dive into every analytical technique implemented in DualEdge -- the 12 guru frameworks used by the AI analyst agents, and the 18 scanner triggers that monitor your portfolio daily.

---

## The DualEdge Philosophy

The oldest debate in investing is fundamental value versus technical momentum. Value investors argue that a stock's price eventually converges to its intrinsic worth -- buy cheap, be patient, collect the spread. Technical analysts counter that price *is* information, that trends persist, and that volume reveals what smart money is doing before the narrative catches up. Both sides have produced legendary investors. Both sides have blind spots.

DualEdge does not pick a side. It formalizes this tension into a system. Two AI analyst agents -- a Value Analyst armed with six fundamental frameworks and a Technical Analyst armed with six quantitative frameworks -- independently analyze the same stock, then debate their findings when they disagree. A lead CIO agent orchestrates the debate and produces a final recommendation with full transparency into where the agents agreed, where they diverged, and what evidence would change the call. The productive friction between fundamental and technical perspectives is the system's core feature, not a bug to be resolved.

The scanner adds a third layer: an early warning system that runs daily with zero AI cost. It watches for the specific conditions that would challenge your existing investment thesis -- the "what would change my mind" conditions that each analyst explicitly states. When the scanner flags something, *that* is when you deploy the full dual-agent analysis. The result is a three-tier signal stack: scan daily, flag triggers, deep dive when needed, debate, decide.

---

## Part 1: Value Analyst Frameworks

The Value Analyst evaluates stocks through the lens of intrinsic worth, financial health, and business quality. Its six frameworks span nearly a century of fundamental analysis, from Benjamin Graham's Depression-era margin of safety to modern growth-adjusted valuation.

### Framework 1: Graham's Margin of Safety

#### The Guru and the Idea

Benjamin Graham, the father of value investing, developed the concept of intrinsic value and margin of safety in the 1930s and 1940s, codified in *Security Analysis* (1934) and *The Intelligent Investor* (1949). His core insight was deceptively simple: a stock has a calculable intrinsic value independent of its market price, and you should only buy when the market price is substantially below that value. The gap between intrinsic value and market price is the margin of safety -- your cushion against errors in estimation and unforeseen events.

#### How It Works

Graham's framework centers on Earnings Power Value (EPV): take the company's normalized earnings (smoothed across business cycles to avoid peak/trough distortions), divide by a cost of capital, and you get an estimate of what the business is worth as a going concern without any growth premium. The cost of capital is typically the 10-year Treasury yield plus an equity risk premium (DualEdge uses a 5% premium). Compare EPV to the current market capitalization. If EPV exceeds market cap, the stock trades below its earnings power -- a potential value opportunity. If market cap substantially exceeds EPV, the market is pricing in growth that may or may not materialize.

The P/E ratio provides a secondary check: compare the current P/E to the stock's 5-year historical average and its sector median to assess whether the market's valuation is high or low relative to its own history and peers.

#### How DualEdge Implements It

The Value Analyst pulls income statements (annual and quarterly) from yfinance to compute normalized earnings. Key ratios including trailing P/E, forward P/E, and EPS are retrieved from `get_key_ratios()`. The agent calculates EPV using a cost of capital derived from current Treasury yields plus a 5% equity risk premium, then compares it to the market cap pulled from yfinance's `info` dict.

Risk profile adjustment: risk-neutral investors accept a 10-15% margin of safety as adequate. Risk-averse investors require 25% or more -- a much stricter filter that eliminates stocks trading anywhere near fair value.

#### Practical Example

Consider a stock trading at $280 per share with a market cap of $4.3 trillion, trailing EPS of $7.50, and normalized earnings of roughly $115 billion. Using a cost of capital of 9.2% (4.2% Treasury yield + 5% equity risk premium), EPV = $115B / 0.092 = approximately $1.25 trillion. The market is pricing the stock at $4.3 trillion -- roughly 3.4x its earnings power. The margin of safety is deeply negative (-244%). Graham would say the market is paying an enormous premium for future growth. Whether that growth materializes is the key question, which is exactly what Damodaran's framework (Framework 3) addresses.

#### Strengths and Limitations

Graham's framework excels at identifying overvalued stocks and flagging situations where the market's growth expectations are unrealistic. It provides a reality check against momentum-driven exuberance. However, it systematically undervalues high-growth companies because it ignores growth entirely -- EPV assumes zero growth. A company reinvesting heavily in expansion will always look expensive through this lens. This is precisely where the Technical Analyst's CAN SLIM framework compensates: O'Neil's system explicitly values growth and momentum, providing a counterweight to Graham's inherent conservatism.

---

### Framework 2: Buffett's Economic Moat

#### The Guru and the Idea

Warren Buffett popularized the concept of economic moats in his Berkshire Hathaway shareholder letters, though the analytical framework was formalized by Morningstar's Pat Dorsey. Buffett's insight, rooted in his partnership with Charlie Munger, is that a company's durable competitive advantages matter more than its current financial metrics. A wide moat protects profits from competition the way a castle's moat protects against invaders. Companies with wide moats can sustain high returns on capital for decades; companies without them see profits competed away.

#### How It Works

Moat analysis is qualitative, drawn from reading the business description and management commentary. Four primary moat sources:

- **Pricing power**: Can the company raise prices without losing customers? Evidence includes consistent gross margin expansion, inflation pass-through, and premium brand positioning.
- **Switching costs**: How painful is it for a customer to leave? Enterprise software, financial platforms, and integrated systems create high switching costs.
- **Network effects**: Does the product become more valuable as more people use it? Social platforms, marketplaces, and payment networks exhibit network effects.
- **Cost advantages**: Does the company have structural cost advantages -- scale economies, proprietary processes, or resource access that competitors cannot replicate?

The output is a rating: None, Narrow, or Wide, with specific evidence cited from the 10-K filing.

#### How DualEdge Implements It

The Value Analyst ingests the most recent 10-K filing from SEC EDGAR via `get_10k_text()`, which retrieves the filing, strips HTML, and extracts key sections (MD&A, Risk Factors, Financial Statements). The agent reads the MD&A for evidence of competitive advantages and the Risk Factors for threats to those advantages. The 10-K is the primary source -- not third-party opinions -- because it contains management's own disclosure of their competitive position.

This is the most token-intensive framework because it requires processing large text documents. The 10-K retrieval is capped at 150,000 characters to manage context window usage.

#### Practical Example

A large tech platform might exhibit three moat sources: network effects (billions of users make the platform more valuable to advertisers), switching costs (businesses have built their advertising infrastructure on the platform's tools), and cost advantages (massive data centers at scale that smaller competitors cannot match). The Risk Factors section might disclose regulatory threats and competitive pressure from emerging platforms. The moat rating would be "Wide" based on three reinforcing moat sources, with a note that regulatory risk could narrow the moat over time.

#### Strengths and Limitations

Moat analysis captures what financial ratios miss: the *sustainability* of high returns. A company can have beautiful current financials but a crumbling competitive position. The weakness is subjectivity -- moat assessment is inherently qualitative, and the agent's interpretation of 10-K language may differ from a human analyst's. The Technical Analyst's Weinstein Stage Analysis provides an objective check: if a company truly has a wide moat, its stock should generally be in Stage 2 (Advancing), not Stage 4 (Declining).

---

### Framework 3: Damodaran's Growth Reasonableness

#### The Guru and the Idea

Aswath Damodaran, a finance professor at NYU Stern, is the foremost authority on valuation. His key contribution to practical investing is the concept of reverse-engineering: instead of projecting growth and discounting cash flows forward (which requires assumptions stacked on assumptions), start with the current stock price and solve backwards for the growth rate the market is implicitly pricing in. Then ask: is that implied growth rate achievable?

#### How It Works

A simplified reverse DCF starts with the current P/E multiple. Given a cost of equity and the current earnings, what annual growth rate would justify the current stock price? This implied growth rate is then compared to two reality checks:

1. **Reinvestment rate x ROIC**: A company's sustainable growth rate is how much it reinvests multiplied by the return it earns on those investments. If a company retains 60% of earnings and earns 20% ROIC, sustainable growth is approximately 12%.
2. **Historical revenue CAGR**: What has the company actually achieved over the past 3-5 years?

If the implied growth rate dramatically exceeds both the sustainable growth rate and the historical growth rate, the market may be too optimistic. If it falls below, the market may be pessimistic.

#### How DualEdge Implements It

The agent pulls financial statements from `get_financials()` to compute reinvestment rates and ROIC. Revenue CAGR is calculated from annual income statements. Key ratios (P/E, forward P/E, PEG) from `get_key_ratios()` provide the starting point for reverse DCF. The agent's output classifies the market's growth expectations as reasonable, optimistic, or pessimistic.

No risk-profile adjustment -- this framework assesses whether the market's expectations are realistic, which is profile-independent.

#### Practical Example

A semiconductor company trading at 26x forward earnings with an estimated cost of equity of 10.5%. The implied growth rate from the current price might be roughly 18% annually for the next 5 years. Historical 3-year revenue CAGR: 32%. Reinvestment rate x ROIC: approximately 22%. Both reality checks exceed the implied rate, suggesting the market's growth expectations are actually conservative relative to recent performance. Assessment: reasonable to slightly pessimistic.

#### Strengths and Limitations

Reverse DCF avoids the most common valuation mistake: anchoring on arbitrary growth projections. By starting from the price, it asks the right question ("what is the market expecting?") rather than the wrong one ("what do I think the company will earn?"). The limitation is that it depends on the accuracy of earnings estimates, which can be volatile for cyclical or rapidly changing businesses. The Technical Analyst's Relative Strength framework reveals whether the market is actually repricing the stock up or down, regardless of what the valuation math says it "should" do.

---

### Framework 4: Lynch's PEG Ratio

#### The Guru and the Idea

Peter Lynch ran the Magellan Fund at Fidelity from 1977 to 1990, compounding at 29.2% annually. His core investment philosophy was Growth At a Reasonable Price (GARP): don't pay any price for growth, but don't ignore growth either. The PEG ratio -- P/E divided by the earnings growth rate -- was his shorthand for whether you were getting a fair deal on a growth stock.

#### How It Works

PEG = Trailing P/E / Expected Annual EPS Growth Rate

A PEG of 1.0 means you're paying 1x for each unit of expected growth -- Lynch considered this fair value. Below 1.0 is attractive; above 2.0 is expensive. The elegance is in the simplicity: it normalizes valuation across growth rates. A stock at 50x earnings growing at 60% (PEG = 0.83) is cheaper than a stock at 15x earnings growing at 5% (PEG = 3.0).

If analyst growth estimates are unavailable, DualEdge falls back to the 3-year historical EPS CAGR.

#### How DualEdge Implements It

The PEG ratio is pulled directly from yfinance's `info` dict via `get_key_ratios()`. When yfinance's PEG is unavailable, the agent manually calculates it from the trailing P/E and either the forward EPS growth rate (from analyst consensus) or the historical EPS CAGR computed from quarterly income statements.

Risk profile adjustment: risk-neutral investors accept PEG up to 2.0. Risk-averse investors require PEG below 1.5 -- a tighter filter that demands more growth per unit of valuation.

#### Practical Example

A cloud software company with a trailing P/E of 45 and analyst-projected EPS growth of 30% has a PEG of 1.5. For a risk-neutral investor, this is acceptable -- you're paying a reasonable premium for above-average growth. For a risk-averse investor, this is borderline -- the growth needs to materialize exactly as projected to justify the valuation.

#### Strengths and Limitations

PEG is intuitive and widely applicable. Its weakness is that it treats all growth as equal -- 30% growth from a software company with 80% margins is very different from 30% growth from a retailer with 3% margins. It also relies on forward estimates, which can be wildly wrong. The Technical Analyst's CAN SLIM framework provides an independent check on whether the company is *actually* delivering the earnings growth that the PEG ratio assumes.

---

### Framework 5: Piotroski F-Score

#### The Guru and the Idea

Joseph Piotroski, a Stanford accounting professor, published his F-Score methodology in 2000. His insight was that simple binary accounting signals -- is profitability improving or declining? Is leverage going up or down? -- could separate genuine value stocks from value traps. The F-Score was designed specifically for stocks that *look* cheap on P/B or P/E: many of them are cheap for good reason (deteriorating fundamentals), and the F-Score helps identify which ones are improving.

#### How It Works

Nine binary signals, scored 0 or 1 each, producing a composite score from 0 to 9:

**Profitability (4 signals):**
1. Positive net income (ROA > 0)
2. Positive operating cash flow
3. ROA improving year-over-year
4. Cash flow from operations exceeds net income (earnings quality)

**Leverage & Liquidity (3 signals):**
5. Long-term debt / total assets decreased
6. Current ratio increased
7. No new equity issuance (no dilution)

**Operating Efficiency (2 signals):**
8. Gross margin improving
9. Asset turnover improving

Scores of 8-9 historically outperform; scores of 0-2 historically underperform.

#### How DualEdge Implements It

The Value Analyst computes all 9 signals from the annual and quarterly financial statements pulled via `get_financials()`. Income statement data provides profitability and margin metrics. Balance sheet data provides leverage and liquidity metrics. Cash flow statement data provides operating cash flow and capex for earnings quality assessment.

Risk profile adjustment: risk-neutral investors note the score as context. Risk-averse investors require an F-Score of 6 or higher to support a BUY recommendation -- a hard threshold that filters out stocks with weak financial health.

#### Practical Example

A retailer with a P/E of 8 (looks cheap) but an F-Score of 3: positive net income (1), negative operating cash flow (0), declining ROA (0), cash flow below net income (0), increased debt (0), lower current ratio (0), no new equity (1), declining gross margin (0), improving asset turnover (1). The low F-Score exposes this as a potential value trap -- the stock is cheap because the business is deteriorating. A risk-averse investor would screen this out immediately.

#### Strengths and Limitations

The F-Score is purely objective -- it's computed from financial statements with no subjective interpretation. It excels at distinguishing genuine value from value traps. The limitation is that it's backward-looking: it measures what has already happened in the financial statements, not what is about to happen. A company executing a strategic turnaround might have a low current F-Score but improving trajectory. The Technical Analyst's Weinstein framework can detect when the market is starting to price in a turnaround (Stage 1 to Stage 2 transition) before it shows up in the financials.

---

### Framework 6: Insider & Analyst Sentiment

#### The Guru and the Idea

This framework synthesizes two information asymmetry signals. Corporate insiders -- CEOs, CFOs, directors -- know more about their company's prospects than any external analyst. When multiple insiders buy stock with their own money (not exercising options), it's one of the strongest bullish signals in the market. Analyst price targets and recommendation changes reflect the consensus view of professional researchers, which tends to move stock prices when it shifts.

#### How It Works

**Insider signals**: Net insider buying vs. selling over the past 6 months, with special attention to cluster purchases (3+ insiders buying within 30 days -- a high-conviction signal). Individual insider sales are often routine (compensation, diversification) and less meaningful, but a pattern of heavy selling with zero purchases is notable.

**Analyst signals**: Mean analyst price target vs. current price (percentage upside/downside), distribution of ratings (strong buy through strong sell), and any rating changes in the past 90 days. A consensus shift (e.g., from "buy" to "hold" across multiple firms) is more meaningful than any single rating.

#### How DualEdge Implements It

Insider transactions are pulled via `get_insider_transactions()` from yfinance, which provides the transaction date, insider name, transaction type, share count, and value. The agent summarizes net buying vs. selling and identifies clusters.

Analyst data comes from `get_analyst_data()`, which retrieves price targets (low, mean, median, high), number of covering analysts, recommendation key (e.g., "buy"), and recommendation mean score from yfinance.

Risk profile adjustment: risk-neutral investors treat insider selling as neutral unless extreme. Risk-averse investors weight insider selling as a bearish signal, increasing sensitivity to distribution patterns.

#### Practical Example

A holding company shows 5 insider transactions in the past 90 days: all sales totaling $59 million, zero purchases. The analyst consensus is "buy" with a mean price target 8% above the current price, but two analysts downgraded in the past month. The insider signal is bearish (heavy selling, no buying); the analyst signal is neutral-to-cautious (target above price but downgrades emerging). A risk-averse investor would flag this as a concern and investigate whether the sales are routine compensation or reflect deteriorating insider confidence.

#### Strengths and Limitations

Insider buying is genuinely predictive -- executives rarely buy stock unless they expect it to appreciate. The limitation is that insider selling is noisy: executives sell for tax planning, diversification, and liquidity, not necessarily because they're bearish. The scanner's D3 trigger (Insider Activity Spike) filters for meaningful patterns: cluster buying (3+ insiders) and heavy selling ($10M+ with zero purchases), removing some of the noise. The Technical Analyst's volume analysis provides a complementary signal: institutional accumulation/distribution patterns in the trading volume.

---

## Part 2: Technical Analyst Frameworks

The Technical Analyst evaluates stocks through price action, volume behavior, and market-relative performance. Its six frameworks span from Stan Weinstein's stage analysis (1988) to modern statistical extension detection.

### Framework 1: Weinstein Stage Analysis

#### The Guru and the Idea

Stan Weinstein published *Secrets for Profiting in Bull and Bear Markets* in 1988. His central insight was that every stock moves through a four-stage cycle -- basing, advancing, topping, declining -- and the 30-week moving average is the key reference line that defines these stages. The genius of the framework is its simplicity: you buy in Stage 2 (advancing, price above a rising 30-week MA) and sell in Stage 4 (declining, price below a falling 30-week MA). You avoid Stage 1 (boring, flat) and Stage 3 (dangerous, topping).

#### How It Works

The stage is classified using three inputs:

| Input | Measurement |
|-------|-------------|
| 30-week MA slope | Rising (>1% change over 5 weeks), flat, or falling |
| Price vs. 30-week MA | Above (>3%), at (within 3%), or below (<-3%) |
| Volume pattern | Expanding (recent 8 weeks > prior 8 weeks by 15%+), contracting, or mixed |

**Stage 1 (Basing)**: Flat MA, price oscillating around it, often contracting volume. The stock is going nowhere while a new base forms.

**Stage 2 (Advancing)**: Rising MA, price above it, ideally with expanding volume on advances. This is where trends run.

**Stage 3 (Topping)**: Flattening MA, price crossing back below it, mixed volume signals. Distribution is occurring.

**Stage 4 (Declining)**: Falling MA, price below it, often with expanding volume on declines. The trend has turned bearish.

#### How DualEdge Implements It

`compute_weinstein_stage()` in `indicators.py` requires at least 35 weeks of weekly data. It computes the 30-week SMA, calculates the 5-week slope percentage change, compares the current price to the MA using a 3% threshold, and assesses the volume pattern by comparing average volume over the most recent 8 weeks to the prior 8 weeks. The output includes the stage (1-4), a confidence level (high, moderate, or low), and the underlying component assessments.

Confidence is "high" when stage and volume pattern align (e.g., Stage 2 with expanding volume). It drops to "moderate" or "low" when signals conflict (e.g., rising MA but price falling below it -- a possible late Stage 2 or early Stage 3).

Risk profile adjustment: risk-neutral investors can buy in Stage 2 at any point. Risk-averse investors should only buy in *early* Stage 2, confirmed by expanding volume.

#### Practical Example

In the February 7, 2026 scan, GOOG was classified as Stage 2 (Advancing): rising 30-week MA, price 20.4% above it, with the stock at $323. META, despite being a mega-cap peer, was classified as Stage 4 (Declining): falling 30-week MA, price 4.7% below it at $661. Two large-cap tech stocks in completely different structural positions -- Weinstein staging reveals this at a glance.

#### Strengths and Limitations

Weinstein staging provides a structural framework that keeps investors aligned with the primary trend. Its strength is regime identification: knowing whether you're in an advancing or declining stage changes how you interpret every other signal. The limitation is lag -- the 30-week MA is inherently slow, and by the time Stage 4 is confirmed, significant damage may have occurred. The Mean Reversion framework (Framework 6) provides faster signals through RSI and Z-scores that can detect potential turning points before the moving average confirms.

---

### Framework 2: O'Neil's CAN SLIM Quantitative

#### The Guru and the Idea

William O'Neil founded Investor's Business Daily and developed the CAN SLIM methodology, published in *How to Make Money in Stocks* (1988). O'Neil studied every major market winner from 1953 to 1993 and found that they shared common characteristics at the start of their runs: accelerating earnings, relative strength leadership, and proximity to new highs. CAN SLIM is a growth-momentum hybrid -- it demands both strong fundamentals and strong price action.

#### How It Works

DualEdge implements five of the seven CAN SLIM criteria quantitatively:

| Criterion | What It Measures | Pass Condition |
|-----------|-----------------|----------------|
| **C** (Current Earnings) | Most recent quarterly EPS vs. year-ago quarter | Year-over-year EPS growth positive |
| **A** (Annual Earnings) | Multi-year earnings growth rate | EPS CAGR > 25% |
| **N** (New Highs) | Proximity to 52-week high | Within 5% of 52-week high |
| **S** (Supply/Demand) | Volume on up days vs. down days | Volume ratio > 1.0 |
| **L** (Leader) | Relative strength vs. S&P 500 | 6-month RS > 1.0 |

The "I" (Institutional Sponsorship) and "M" (Market Direction) criteria require data not available from free APIs and are evaluated qualitatively by the agent.

Output: a score from 0 to 5 with pass/fail for each criterion.

#### How DualEdge Implements It

`compute_canslim_quantitative()` in `indicators.py` takes the stock's daily OHLCV, S&P 500 data, and quarterly EPS data. It calls several other indicator functions internally: `compute_52week_metrics()` for the N criterion, `compute_volume_ratio()` for S, and `compute_relative_strength()` for L. The C and A criteria are computed directly from the EPS DataFrame.

When quarterly EPS data is limited (fewer than 5 quarters), the function falls back to sequential quarter-over-quarter comparison for C and uses available data for A's CAGR calculation.

#### Practical Example

From the February 7, 2026 scan, AAPL scored 4/5 on CAN SLIM: passing C (current earnings growth), A (annual growth), N (near 52-week high), and L (6-month RS of 1.16 vs. S&P 500), failing only S (volume ratio below 1.0). TSM also scored 4/5. NFLX scored only 1/5 -- in Stage 4 Declining, far from its high, weak relative strength -- a clear non-leader despite its brand recognition.

#### Strengths and Limitations

CAN SLIM's strength is its multi-factor approach: it requires *both* earnings quality and price momentum, which filters out cheap-but-falling stocks (value traps) and expensive-but-growing stocks with deteriorating momentum. The limitation is that the criteria are designed for growth stocks near breakout points -- it's structurally biased against value stocks, defensive stocks, and turnaround situations. This is exactly where the Value Analyst's Graham and Piotroski frameworks fill the gap: they evaluate whether a low-scoring CAN SLIM stock is cheap for good reason or cheap because the business is deteriorating.

---

### Framework 3: Relative Strength Analysis

#### The Guru and the Idea

Relative strength measurement has roots in academic momentum research (Jegadeesh and Titman, 1993) and practical application by institutional investors. The core insight is simple but powerful: stocks that outperform the market tend to *continue* outperforming, and stocks that underperform tend to continue underperforming. This persistence of relative performance is one of the most robust anomalies in finance. Relative strength separates alpha (stock-specific outperformance) from beta (sector or market-driven movement).

#### How It Works

RS Ratio = (1 + stock return) / (1 + benchmark return) over a given period.

An RS ratio above 1.0 means the stock has outperformed its benchmark. Below 1.0 means underperformance. DualEdge computes RS at four timeframes -- 1 month, 3 months, 6 months, and 12 months -- against both the S&P 500 and the relevant sector ETF. Comparing the two reveals decomposition: outperformance vs. S&P 500 driven by sector tailwinds (high RS vs. S&P 500 but low RS vs. sector ETF) is different from genuine stock-specific alpha (high RS vs. both).

The trajectory assessment compares 3-month RS to 6-month RS: if 3m > 6m by more than 2%, relative strength is improving (accelerating outperformance). If 3m < 6m by more than 2%, it's deteriorating (decelerating or reversing).

#### How DualEdge Implements It

`compute_relative_strength()` in `indicators.py` calculates cumulative returns for both the stock and benchmark over each window, then divides. It's called twice by `compute_all_indicators()`: once with the S&P 500 as benchmark, once with the sector ETF. When the benchmark return is near zero (flat market), the function avoids division-by-zero by returning 1.0 plus the stock's raw return.

The trajectory is classified using only the 3m/6m comparison, not shortcut ratio comparisons that would introduce false positives. This is a deliberate design choice documented in the project's memory.

#### Practical Example

From the February 7, 2026 scan: MU had a 6-month RS vs. S&P 500 of 3.23 -- extreme outperformance, meaning MU returned more than 3x what the S&P 500 returned over 6 months. The trajectory arrow pointed down (deteriorating), suggesting the outperformance was decelerating. UBER, conversely, had a 6-month RS of 0.74 with an improving trajectory -- still underperforming but the trend was reversing. These trajectory arrows add crucial context: a high RS with deteriorating trajectory is a different signal than a high RS with improving trajectory.

#### Strengths and Limitations

Relative strength is objective and unemotional -- it measures what the market is actually doing, not what anyone thinks it should do. Its limitation is that momentum eventually reverses, and RS cannot tell you when. A stock with 12 months of strong RS can collapse abruptly. The Value Analyst's growth reasonableness check (Damodaran) provides a counterbalance: if RS is strong but the market's implied growth expectations are unrealistic, the momentum may be borrowed from the future.

---

### Framework 4: Volatility Regime Assessment

#### The Guru and the Idea

This framework synthesizes work from John Bollinger (Bollinger Bands, 1983), J. Welles Wilder (ATR, 1978), and modern volatility clustering research. The key insight is that volatility is *not* constant -- it moves in regimes. Low-volatility periods cluster together and tend to precede large moves (in either direction). High-volatility periods cluster together and eventually compress. Identifying the current regime helps calibrate position sizing and risk expectations.

#### How It Works

Three tools, each measuring a different aspect of volatility:

**Annualized Volatility**: Standard deviation of daily log returns, annualized by multiplying by sqrt(252). Computed at 1m, 3m, 6m, and 12m windows, plus a 12-month rolling average for regime comparison. Current volatility above 1.5x the 12-month average suggests an elevated regime.

**Bollinger Band Width**: The distance between the upper and lower Bollinger Bands, normalized by the middle band. The width percentile ranks the current width against the past 252 trading days. A percentile below 10 is a "squeeze" -- historically low volatility that often precedes an expansion (breakout or breakdown).

**ATR Trend**: Average True Range measures the typical daily price range (accounting for gaps). The trend compares the average ATR over the last 20 days to the prior 20 days. Increasing ATR during a decline is ominous; decreasing ATR during an advance suggests the move is running out of energy.

#### How DualEdge Implements It

`compute_annualized_volatility()` computes daily log returns and annualizes the standard deviation at each window. The 12-month average is a rolling 21-day volatility, averaged over 252 days -- a more stable measure than a single-window calculation.

`compute_bollinger_bands()` uses a 20-day SMA and 2 standard deviations. The width percentile calculation counts how many of the past 252 width values are below the current width.

`compute_atr()` uses Wilder's smoothing (exponential after the first simple average). The trend is classified as increasing (>5% higher), decreasing (>5% lower), or stable.

Risk profile adjustment: risk-neutral investors note volatility as context. Risk-averse investors penalize stocks in elevated volatility regimes (>1.5x 12-month average), biasing toward SELL.

#### Practical Example

From the February 7, 2026 scan, GOOG had a Bollinger Band width percentile of 2.0% -- an extreme squeeze, meaning its bands were tighter than 98% of the past year's readings. This doesn't predict direction, but it signals that a large move is imminent. Combined with its Stage 2 classification and strong RS, the expected breakout direction was upward. TSM showed a similar squeeze at 9.1%.

#### Strengths and Limitations

Volatility regime assessment helps with timing and position sizing, which pure valuation analysis ignores entirely. The Value Analyst can tell you a stock is cheap, but volatility analysis tells you whether now is the right moment to act or whether you should wait for the regime to clarify. The limitation is that volatility is direction-agnostic -- a squeeze can resolve up or down, and ATR doesn't tell you which.

---

### Framework 5: Wyckoff Volume Analysis

#### The Guru and the Idea

Richard Wyckoff, active in the early 1900s, developed one of the first systematic approaches to analyzing volume alongside price. His insight was that volume represents effort: price movement on high volume is "effortful" (driven by genuine buying or selling pressure), while price movement on low volume is "effortless" (likely to reverse). The relationship between price trends and volume trends reveals whether institutions are accumulating (building positions quietly) or distributing (selling into strength).

#### How It Works

**On-Balance Volume (OBV)**: A cumulative indicator that adds volume on up days and subtracts volume on down days. If price is rising and OBV is rising, the advance is supported by volume -- healthy. If price is rising but OBV is falling, the advance lacks volume support -- bearish divergence suggesting distribution. The inverse pattern (price falling, OBV rising) suggests accumulation despite price weakness -- potentially bullish.

**Volume Ratio**: The ratio of average volume on up days to average volume on down days over 60 trading days. A ratio above 1.0 means buyers are trading with more conviction than sellers. A ratio below 1.0 means sellers dominate.

#### How DualEdge Implements It

`compute_obv()` in `indicators.py` multiplies each day's volume by the sign of that day's price change and takes the cumulative sum. It computes a 20-day OBV moving average and classifies the 20-day OBV trend as rising (>2% change), falling (<-2% change), or flat. The price trend is classified the same way. Divergence is flagged when price and OBV trends move in opposite directions.

`compute_volume_ratio()` looks at the most recent 60+1 trading days, separates up days (close > prior close) from down days, and divides average up-day volume by average down-day volume.

#### Practical Example

In the February 7, 2026 scan, META showed a bearish OBV divergence: price trending up but OBV trending down. This suggests that while META's price was rising, volume was heavier on down days -- institutions may have been selling into the rally. IJR showed the same pattern. These divergence flags are among the scanner's most actionable volume signals -- the recommended actions listed both as requiring review.

#### Strengths and Limitations

Volume analysis reveals institutional behavior that price alone cannot show. The OBV divergence signal is particularly valuable because it often leads price by days or weeks -- distribution shows up in volume before the price breaks down. The limitation is that OBV is noisy on low-volume stocks and can generate false divergence signals. The Value Analyst's Insider Sentiment framework provides corroborating evidence: if OBV shows distribution *and* insiders are selling heavily, the convergence of signals is much more concerning than either alone.

---

### Framework 6: Mean Reversion

#### The Guru and the Idea

Mean reversion is the oldest statistical concept in finance, rooted in the work of Francis Galton (regression to the mean, 1886) and applied to stock analysis by practitioners across decades. The insight is that extreme deviations from a mean tend to reverse. A stock 40% above its 200-day moving average is not "strong" -- it is extended and statistically likely to pull back. A stock 40% below is not "weak" -- it is compressed and likely to bounce. This framework provides the counterweight to trend-following: trends are real, but extensions within trends are temporary.

#### How It Works

Three measurement tools:

**RSI (Relative Strength Index)**: Wilder's momentum oscillator, ranging from 0 to 100. RSI above 70 is overbought (momentum extended to the upside). RSI below 30 is oversold (extended to the downside). DualEdge uses 14-day RSI with Wilder's proprietary smoothing method, which is more stable than simple exponential moving averages.

**Distance from 200-Day MA**: The percentage gap between the current price and the 200-day simple moving average. Extreme extensions (>15-20% in either direction) tend to revert.

**Price Z-Score**: The current price expressed as standard deviations from its 6-month mean. A Z-score above +2.0 means the price is statistically unusual to the upside; below -2.0 is unusual to the downside.

#### How DualEdge Implements It

`compute_rsi()` implements Wilder's smoothing precisely: the first average gain and loss are simple arithmetic means over the initial period, then subsequent values use exponential smoothing with a factor of (period - 1) / period. This matches the original specification and produces values that align with professional charting platforms.

`compute_price_zscore()` uses a 126-trading-day lookback (approximately 6 months), computes the mean and standard deviation of closing prices, and returns (current - mean) / std.

Risk profile adjustment for scan triggers: risk-neutral RSI overbought threshold is 75, risk-averse is 70. Risk-neutral extension threshold from 200-day MA is 20%, risk-averse is 15%. In the full agent analysis, risk-averse investors treat RSI above 70 as a strong SELL signal and penalize the BUY case for any stock extended more than 15% above its 200-day MA.

#### Practical Example

From the February 7, 2026 scan: AMZN had a Z-score of -2.22 (deeply oversold) and RSI of 28.6 (nearing classic oversold at 30). UBER was similarly compressed at Z = -2.33. On the other end, IJR had Z = +2.59 (overbought territory). MU was 113.9% above its 200-day MA -- an extreme extension by any measure. These mean-reversion signals don't guarantee a reversal, but they flag that the current price is statistically unusual and worth monitoring for a potential change in direction.

#### Strengths and Limitations

Mean reversion provides timely signals -- RSI and Z-scores respond quickly to price changes, unlike lagging indicators such as 30-week moving averages. The danger is buying into a declining trend just because it "looks" oversold -- a stock at RSI 25 can go to RSI 15. Weinstein Stage Analysis provides critical context: an oversold RSI in Stage 2 (temporary pullback in an uptrend) is a very different signal than an oversold RSI in Stage 4 (potentially just the beginning of a larger decline).

---

## Part 3: Scanner Trigger Techniques

The scanner's 18 triggers translate the analytical principles from Parts 1 and 2 into automated daily surveillance. They don't replace the full agent analysis -- they tell you when to deploy it.

### Trend Triggers (A1-A4)

These detect structural changes in a stock's price trend. They are state-change triggers: they fire only when a value *transitions* from one state to another, not when it is simply at a level. This means they require a prior scan for comparison.

**A1: Weinstein Stage Change** -- Fires when the computed stage (1-4) changes between scans. A Stage 2 to Stage 3 transition on a held stock is a significant warning: the trend that supported your BUY thesis may be ending. A Stage 4 to Stage 1 transition on a watchlist stock signals a potential basing pattern worth monitoring. Priority: HIGH.

**A2: 30-Week MA Crossover** -- Fires when price crosses above or below the 30-week MA. The defining signal line in Weinstein's framework. For risk-averse investors, a downward cross on a held stock is elevated to HIGHEST priority. On first scan, stocks within 2% of the MA receive an informational proximity alert. Priority: HIGH (HIGHEST for risk-averse downward cross on holdings).

**A3: 200-Day MA Crossover** -- Same mechanism as A2 for the 200-day SMA. Institutional investors widely use this as a bull/bear dividing line. Priority: HIGH.

**A4: MA Alignment Shift** -- Fires when the ordering relationship among the 50, 150, and 200-day SMAs changes (e.g., bullish alignment where 50 > 150 > 200 with all rising shifts to mixed). This is a subtler signal than a crossover but indicates the trend's internal structure is deteriorating. Priority: MEDIUM.

### Momentum Triggers (B1-B5)

These detect overbought/oversold extremes and shifts in market-relative performance.

**B1: RSI Overbought** -- RSI(14) exceeds 75 (risk-neutral) or 70 (risk-averse). Indicates momentum is extended to the upside and a pullback is increasingly likely. Priority: MEDIUM.

**B2: RSI Oversold** -- RSI(14) drops below 25 (risk-neutral) or 30 (risk-averse). Indicates momentum is compressed and a bounce is increasingly likely -- but *only* in the right structural context (see Weinstein staging). Priority: MEDIUM.

**B3: Extended from 200-Day MA** -- Price more than 20% (risk-neutral) or 15% (risk-averse) from the 200-day MA in either direction. This fires frequently during strong trends and is most useful as a position-sizing signal: don't add to a position when it's this extended, even if the trend is intact. Priority: MEDIUM.

**B4: Z-Score Extreme** -- Price more than 2 standard deviations from its 6-month mean. A statistical outlier that historically tends to revert. Unlike RSI, Z-score has no risk-profile adjustment. Priority: MEDIUM.

**B5: RS Breakdown/Breakout** -- Fires when a stock's RS vs. S&P 500 transitions between outperforming and underperforming states. A stock that was outperforming across all timeframes (1m, 3m, 6m all above 1.0) and shifts to underperforming (all below 1.0) has experienced a fundamental change in market perception. Also flags trajectory deterioration: still outperforming but decelerating, suggesting the trend may be turning. State-change trigger, requires prior scan. Priority: HIGH for full state changes, MEDIUM for trajectory shifts.

### Volume Triggers (C1-C4)

These detect changes in institutional buying and selling pressure.

**C1: Volume Spike** -- Today's volume exceeds 2x the 20-day average. Down-day spikes on holdings (priority HIGH) signal potential institutional distribution. Up-day spikes on watchlist stocks (priority LOW) signal potential accumulation or breakout.

**C2: OBV Divergence** -- Price and On-Balance Volume trending in opposite directions over 20 days. Bearish divergence (price up, OBV down) is priority HIGH because it suggests the price advance lacks conviction. Bullish divergence (price down, OBV up) is priority MEDIUM because it suggests accumulation.

**C3: Volume Ratio Shift** -- 60-day volume ratio below 0.8 on a held stock (sellers dominating, priority MEDIUM) or above 1.3 on a watchlist stock (buyers dominating, priority MEDIUM). The asymmetry is deliberate: for holdings you want to know about selling pressure; for watchlist stocks you want to know about buying pressure.

**C4: Bollinger Squeeze** -- Band width below the 10th percentile over 252 days. Flags an impending large move. Purely informational -- does not predict direction. Priority: LOW.

### Valuation Triggers (D1-D3)

These apply fundamental valuation checks to the daily scan.

**D1: P/E Extreme** -- P/E above 50 and more than 2x the sector median (flagged as expensive), or P/E below 10 with positive earnings (flagged as potentially cheap). Sector medians are computed from peer stocks in the scan when possible, otherwise use hardcoded values. Priority: LOW.

**D2: Earnings Deterioration** -- Most recent quarterly EPS declined more than 25% year-over-year. This is a proxy for the CAN SLIM "C" criterion deteriorating. Annotates if the decline is consecutive quarters. Priority: MEDIUM.

**D3: Insider Activity Spike** -- Two patterns over 90 days: cluster buying (3+ distinct insiders purchasing within 30 days) signals informed bullishness, or heavy selling ($10M+ in sales with zero purchases) signals informed bearishness. Automatic and 10b5-1 plan transactions are filtered out. Priority: MEDIUM.

### Prior Analysis Triggers (E1-E2)

These close the loop between the scanner and the full DualEdge analysis system.

**E1: Change Condition Met** -- The explicit "what would change my mind" conditions from a prior DualEdge deep dive have been triggered. This supports 10 condition types including price thresholds, weekly closes, RS breakdowns, stage changes, RSI thresholds, and OBV divergence patterns. This is the highest-priority trigger in the entire system (HIGHEST) because it means your prior investment thesis -- the specific evidence you identified as thesis-changing -- has materialized.

**E2: Analysis Staleness** -- Last DualEdge deep dive was more than 30 days ago. A gentle reminder that your thesis may be based on outdated data, especially in fast-moving markets. Priority: LOW.

---

## Part 4: How They Work Together

### The Productive Tension

The Value Analyst and Technical Analyst are designed to disagree. Graham's margin of safety might flag a stock as overvalued while Weinstein's stage analysis shows it in a healthy Stage 2 advance. Lynch's PEG might call a stock cheap while mean reversion signals show it deeply overbought. These disagreements are not errors -- they are features. They force the debate mechanism to surface the key question: is this stock cheap-and-getting-cheaper (value trap) or expensive-and-getting-more-expensive (momentum winner)?

The debate protocol gives each agent the other's analysis and asks: does this evidence change your position? When it does, the system converges to a consensus recommendation with high confidence. When it doesn't, the lead agent executes a tiebreaker based on confidence scores and produces a "split decision" that preserves both perspectives. Either way, the user gets full transparency into the reasoning.

### The Scanner as Early Warning

The scanner doesn't replicate the agents' analysis -- it watches for the conditions that would make that analysis stale. A DualEdge deep dive might produce a BUY with two explicit change conditions: "SELL if price drops below $174" and "increase confidence if price breaks above $192.50 on volume." The scanner evaluates those conditions every day. When one fires, the E1 trigger generates the highest-priority alert: run the analysis again, because the market has handed you the specific evidence your prior thesis said would matter.

This two-tier design keeps LLM costs near zero on quiet days (the scanner is pure Python) and deploys the full analytical power only when the data demands it.

### The Risk Profile as Sensitivity Dial

The risk profile does not change the data or the frameworks -- it changes the thresholds. A risk-neutral investor sees RSI 72 and notes it as context. A risk-averse investor sees RSI 72 and flags it as overbought. The same stock, the same data, the same analytical frameworks, but different conclusions because the tolerance for risk is different. This applies across both the agent analysis and the scanner triggers, creating consistent behavior from daily monitoring through deep-dive recommendation.

---

## The Signal Stack

### All 30 Analytical Signals

| # | Signal | Source | Type | Category |
|---|--------|--------|------|----------|
| 1 | Graham's Margin of Safety | Value Analyst | Framework | Valuation |
| 2 | Buffett's Economic Moat | Value Analyst | Framework | Quality |
| 3 | Damodaran's Growth Reasonableness | Value Analyst | Framework | Valuation |
| 4 | Lynch's PEG Ratio | Value Analyst | Framework | Growth-Value |
| 5 | Piotroski F-Score | Value Analyst | Framework | Financial Health |
| 6 | Insider & Analyst Sentiment | Value Analyst | Framework | Information |
| 7 | Weinstein Stage Analysis | Technical Analyst | Framework | Trend |
| 8 | O'Neil's CAN SLIM | Technical Analyst | Framework | Growth-Momentum |
| 9 | Relative Strength Analysis | Technical Analyst | Framework | Momentum |
| 10 | Volatility Regime Assessment | Technical Analyst | Framework | Risk |
| 11 | Wyckoff Volume Analysis | Technical Analyst | Framework | Volume |
| 12 | Mean Reversion Check | Technical Analyst | Framework | Statistical |
| 13 | Weinstein Stage Change (A1) | Scanner | Trigger | Trend |
| 14 | 30-Week MA Crossover (A2) | Scanner | Trigger | Trend |
| 15 | 200-Day MA Crossover (A3) | Scanner | Trigger | Trend |
| 16 | MA Alignment Shift (A4) | Scanner | Trigger | Trend |
| 17 | RSI Overbought (B1) | Scanner | Trigger | Momentum |
| 18 | RSI Oversold (B2) | Scanner | Trigger | Momentum |
| 19 | Extended from 200d MA (B3) | Scanner | Trigger | Momentum |
| 20 | Z-Score Extreme (B4) | Scanner | Trigger | Momentum |
| 21 | RS Breakdown/Breakout (B5) | Scanner | Trigger | Momentum |
| 22 | Volume Spike (C1) | Scanner | Trigger | Volume |
| 23 | OBV Divergence (C2) | Scanner | Trigger | Volume |
| 24 | Volume Ratio Shift (C3) | Scanner | Trigger | Volume |
| 25 | Bollinger Squeeze (C4) | Scanner | Trigger | Volume |
| 26 | P/E Extreme (D1) | Scanner | Trigger | Valuation |
| 27 | Earnings Deterioration (D2) | Scanner | Trigger | Valuation |
| 28 | Insider Activity Spike (D3) | Scanner | Trigger | Information |
| 29 | Change Condition Met (E1) | Scanner | Trigger | Thesis |
| 30 | Analysis Staleness (E2) | Scanner | Trigger | Maintenance |

### The DualEdge Workflow

```
Daily: Run scanner (0 LLM tokens, ~2 minutes)
  |
  +--> No triggers? All quiet. Check again tomorrow.
  |
  +--> Triggers fired?
       |
       +--> E1 (Change Condition Met)? --> Run full DualEdge deep dive immediately.
       |
       +--> HIGH triggers (stage change, MA cross, RS shift, volume spike)?
       |    --> Review the stock. Consider a deep dive if multiple signals converge.
       |
       +--> MEDIUM triggers (RSI, extension, Z-score, earnings)?
       |    --> Monitor. Note the flag. Wait for escalation or convergence with other signals.
       |
       +--> LOW/INFO triggers (squeeze, P/E, staleness, proximity)?
            --> Informational. File away. These are early hints, not action items.

When a deep dive is warranted:
  1. Two AI agents independently analyze the stock using 12 frameworks
  2. If they agree: consensus recommendation with high confidence
  3. If they disagree: structured debate (max 2 rounds) + tiebreaker
  4. Output: BUY or SELL with confidence score and explicit change conditions
  5. Change conditions are added to watchlist.json
  6. Scanner monitors those conditions daily
  7. Loop continues
```

The system's power is in the loop: deep analysis produces explicit change conditions, the scanner monitors those conditions daily at zero cost, and when conditions are met, the system triggers a re-evaluation. Every recommendation has a built-in expiration mechanism -- not by time, but by evidence.
