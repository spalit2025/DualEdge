## VALUE ANALYST REPORT: NVDA
**Date**: 2026-02-07
**Risk Profile**: Risk-Neutral

### SUMMARY
| Field | Value |
|-------|-------|
| RECOMMENDATION | BUY |
| CONFIDENCE | 7 / 10 |
| KEY DRIVER | Dominant AI infrastructure moat with explosive earnings growth justifies premium valuation, and forward P/E of ~24x with 90%+ forward EPS growth provides a reasonable entry point for a risk-neutral investor. |
| CHANGE CONDITION | Recommendation flips to SELL if: (1) data center revenue growth decelerates below 30% YoY for two consecutive quarters, (2) gross margins compress below 65% indicating competitive erosion, (3) a credible GPU alternative gains >15% market share in AI training/inference, or (4) U.S.-China export restrictions materially escalate beyond current scope. |

---

### 1. Graham's Margin of Safety

- **Normalized Earnings**: To calculate Earnings Power Value, we normalize earnings across the cycle. Given the explosive trajectory, we use a blend: the trailing-twelve-month (TTM) net income from the most recent four quarters (Q1 FY2026 through Q3 FY2026 plus Q4 FY2025) is approximately $99.11B ($22.09B + $18.78B + $26.42B + $31.91B). However, Graham would insist on normalization. Averaging the last 3 fiscal years of net income (FY2023: $4.37B, FY2024: $29.76B, FY2025: $72.88B) gives $35.67B. Given the structural shift in AI spending, a more forward-looking normalized figure using the last 2 years gives $51.32B.
- **Earnings Power Value (EPV)**: $51.32B / 0.095 (cost of capital) = **$540.2B**
- **Current Market Cap**: **$4,514.2B**
- **Margin of Safety**: (EPV - Market Cap) / Market Cap = ($540.2B - $4,514.2B) / $4,514.2B = **-88.0%** (negative -- market cap vastly exceeds EPV)
- **Trailing P/E vs Sector**: Trailing P/E of 45.9x is well above the semiconductor sector median of ~20-25x.
- **Forward P/E**: 24.0x is more reasonable, reflecting consensus expectations for continued rapid earnings growth.
- **Verdict**: **Insufficient** under strict Graham criteria.

**Analysis**: A traditional Graham valuation framework, which anchors to historical or normalized earnings, fundamentally struggles with a company experiencing a paradigm shift in earnings. NVDA's EPV based on normalized past earnings is roughly $540B against a $4.5T market cap, yielding a deeply negative margin of safety. However, this is somewhat misleading because NVDA's earnings trajectory is not mean-reverting to historical levels -- it is structurally higher. The forward P/E of 24x against expected earnings of $7.71/share implies the market is pricing in a sustained high-earnings regime. Under strict Graham rules, this is a clear fail. For a risk-neutral investor, we note this finding but weigh it alongside growth-oriented frameworks below.

---

### 2. Buffett's Economic Moat

- **Pricing Power**: STRONG. NVDA's gross margins expanded from 57% (FY2023) to 72.8% (FY2024) to 75.0% (FY2025), and most recent quarters show gross margins of 73-76%. The company commands premium pricing for its data center GPUs (H100, Blackwell) with no meaningful discounting. The 10-K describes a full-stack platform (silicon + software) that creates value customers cannot replicate, enabling sustained premium pricing. Revenue more than doubled YoY in FY2025 with gross margin expansion, a hallmark of extraordinary pricing power.

- **Switching Costs**: VERY HIGH. The CUDA ecosystem, with over 5.9 million developers and 4,400+ supported applications, creates enormous switching costs. Enterprises have invested years of engineering effort building on CUDA, NVIDIA's software libraries (cuDNN, TensorRT, NeMo, NIM), and domain-specific SDKs. The 10-K explicitly describes the "large and growing number of developers and installed base across our platforms strengthens our ecosystem and increases the value of our platform to our customers." Migrating to an alternative accelerator would require rewriting and revalidating entire software stacks.

- **Network Effects**: STRONG. NVIDIA's platform benefits from a virtuous cycle: more developers build on CUDA, which attracts more users, which attracts more developers. The Inception program supports thousands of AI startups. The 10-K states NVIDIA's "AI technology leadership is reinforced by our large and expanding ecosystem in a virtuous cycle." Every major CSP, server maker, and enterprise software vendor has optimized for NVIDIA's platform, creating a self-reinforcing ecosystem.

- **Cost Advantages**: MODERATE. NVIDIA's fabless model with TSMC provides access to leading-edge manufacturing without capital-intensive fabs. The company's massive R&D investment ($12.91B in FY2025, $58.2B cumulatively since inception) creates an IP moat that competitors cannot easily replicate. Scale advantages in software development are significant -- the same CUDA stack serves data center, gaming, professional visualization, and automotive markets.

- **Moat Rating**: **Wide**

**Analysis**: NVIDIA possesses one of the widest economic moats in the technology sector. The combination of the CUDA software ecosystem (switching costs), dominant market share in AI accelerators (~80%+ of AI training), a vertically integrated full-stack platform (hardware + networking + software), and a self-reinforcing developer ecosystem creates durable competitive advantages. The 10-K describes a company that has evolved from a GPU maker into a full-stack computing infrastructure provider, which deepens the moat. Potential moat threats include custom AI silicon from hyperscalers (Google TPU, Amazon Trainium, Microsoft Maia) and AMD's competitive offerings, but these have not materially eroded NVIDIA's dominance to date.

---

### 3. Damodaran's Growth Reasonableness

- **Implied Growth Rate from P/E**: The trailing P/E of 45.9x, against a cost of equity of ~9.5%, implies the market expects significant future earnings growth. Using a simplified reverse DCF approach: if a "no-growth" P/E is approximately 1/0.095 = 10.5x, then the premium of 45.9x - 10.5x = 35.4x reflects growth expectations. This implies an annualized earnings growth rate of approximately 35-40% over the next 5 years to justify current valuation, gradually declining to a terminal growth rate.

- **Reinvestment Rate x ROIC**: ROIC is extraordinarily high. With operating income of $81.45B on invested capital of $87.79B (FY2025), ROIC is approximately 92.8%. Reinvestment rate (capex + change in working capital - depreciation) / NOPAT is relatively low given the asset-light model. Even a modest reinvestment rate of 15-20% x 92.8% ROIC implies sustainable growth of 14-19% from reinvestment alone, before accounting for efficiency gains.

- **3-Year Revenue CAGR** (FY2022 to FY2025): ($130.50B / $26.91B)^(1/3) - 1 = **69.0%**
- **5-Year Revenue CAGR**: Not fully available from data, but the 3-year growth is extraordinary.
- **Forward EPS Growth Rate**: Forward EPS of $7.71 vs trailing EPS of $4.04 implies approximately **90.8% growth**, though this reflects the steep ramp from recent quarters.
- **TTM EPS Growth**: TTM diluted EPS is approximately $4.04 (based on trailing). The most recent four quarters sum to approximately $4.04 (per trailing_eps). Prior TTM was roughly $1.93 (based on FY2024 diluted EPS of $1.19 + ramp). This implies ~110%+ YoY EPS growth.

- **Assessment**: **Reasonable (at forward P/E), Optimistic (at trailing P/E)**

**Analysis**: The implied growth rate embedded in NVDA's trailing P/E of ~46x is demanding but not unreasonable given the company's demonstrated ability to grow revenue at 69% CAGR over 3 years and earnings at an even faster clip. The forward P/E of 24x is more instructive -- it implies a deceleration in growth is already expected, but the rate of deceleration is modest. NVIDIA's ROIC is extraordinarily high (>90%), meaning even modest reinvestment can sustain elevated growth. The key question is whether the AI infrastructure spending cycle is durable. Based on the 10-K disclosure of the Blackwell architecture ramp and continued data center buildout by CSPs, 30-40% revenue growth over the next 2-3 years appears achievable, which would justify the current forward P/E. The growth embedded in valuation is optimistic but supported by observable evidence.

---

### 4. Lynch's PEG Check

- **Trailing P/E**: 45.89
- **Forward Earnings Growth Rate**: Using the forward EPS of $7.71 vs trailing EPS of $4.04, the implied 1-year forward growth rate is approximately 90.8%. For a more conservative PEG calculation, we can use analyst consensus forward growth. The trailing-to-forward P/E compression (45.9x to 24.0x) implies the market expects ~91% earnings growth.
- **PEG Ratio**: 45.89 / 90.8 = **0.51**
- **Alternative PEG (using 3-year normalized growth)**: If we assume earnings growth normalizes to ~35% annualized over the next 3 years (consistent with Damodaran analysis above), PEG = 45.89 / 35 = **1.31**
- **Assessment**: **Undervalued** on near-term PEG (0.51); **Fair value** on normalized PEG (1.31)

**Analysis**: Lynch's PEG framework is highly favorable for NVDA. Even using a conservative normalized growth rate of 35%, the PEG of 1.31 falls well within the risk-neutral acceptable threshold of 2.0 and within Lynch's "fairly valued" range of 1.0-1.5. On a near-term basis, with ~91% forward earnings growth, the PEG of 0.51 would classify NVDA as a strong buy under this framework. The critical assumption is whether growth can sustain at elevated levels. Given the Blackwell product cycle, expanding data center TAM, and enterprise AI adoption, a normalized 35% earnings CAGR over 3 years is defensible.

---

### 5. Piotroski F-Score

**Profitability (4 signals)**:
| Signal | Pass/Fail |
|--------|-----------|
| Positive ROA (ROA = 53.5%) | PASS |
| Positive Operating Cash Flow (OCF = $64.09B) | PASS |
| Improving ROA YoY (FY2025 ROA ~65.3% vs FY2024 ROA ~45.3%) | PASS |
| Cash Flow > Net Income (OCF $64.09B > NI $72.88B) | FAIL |

Note on CFO vs NI: Operating cash flow of $64.09B is less than net income of $72.88B, largely due to working capital absorption (receivables growth of $13.06B) from the massive revenue ramp. This is a technical fail but not a fundamental concern -- it reflects hypergrowth, not earnings quality issues.

**Leverage (3 signals)**:
| Signal | Pass/Fail |
|--------|-----------|
| Decreasing Long-term Debt/Assets (FY2025: $8.46B/$111.60B = 7.6% vs FY2024: $8.46B/$65.73B = 12.9%) | PASS |
| Increasing Current Ratio (FY2025: 4.47 vs FY2024: 4.17) | PASS |
| No New Equity Issuance (shares outstanding decreased from 24.64B to 24.48B due to buybacks) | PASS |

**Efficiency (2 signals)**:
| Signal | Pass/Fail |
|--------|-----------|
| Improving Gross Margin (FY2025: 75.0% vs FY2024: 72.7%) | PASS |
| Improving Asset Turnover (FY2025: $130.50B/$111.60B = 1.17 vs FY2024: $60.92B/$65.73B = 0.93) | PASS |

- **F-Score**: **8 / 9**
- **Trajectory**: **Improving**

**Analysis**: NVDA scores an exceptional 8 out of 9 on the Piotroski F-Score, failing only on the CFO > NI signal, which is a consequence of working capital absorption during a period of hypergrowth rather than an earnings quality concern. All profitability, leverage, and efficiency signals are strongly positive. The balance sheet is strengthening (debt/assets declining, current ratio expanding, share count decreasing via buybacks). Gross margins and asset turnover are both improving. This is a textbook high-quality financial profile. An F-Score of 8 far exceeds the risk-neutral threshold of 5.

---

### 6. Insider & Analyst Sentiment

**Insider Activity (Past 6 Months)**:
| Metric | Value |
|--------|-------|
| Net Insider Buying/Selling | Overwhelmingly net selling |
| Aggregate Sales (approx.) | ~$1.2B+ in open-market sales over 6 months |
| Cluster Purchases (3+ in 30 days) | No -- zero insider purchases observed |
| CEO (Jensen Huang) Activity | Systematic selling of 225,000 shares approximately every 3-5 business days under a 10b5-1 plan |
| CFO (Colette Kress) Activity | Regular periodic sales of ~47,640-66,670 shares |
| Director Activity | Large sales by Stevens, Seawell, Coxe, Jones |
| Stock Gifts | Multiple large stock gifts by Huang, Kress, Stevens, Seawell, Coxe (estate/tax planning) |
| Insider Signal | **Bearish** (high volume of sales, no purchases) |

**Context**: The insider selling pattern is consistent with pre-programmed 10b5-1 trading plans, which are common for executives of mega-cap companies. CEO Jensen Huang has been selling 225,000 shares on a near-weekly cadence, which is a programmatic pattern rather than a discretionary bearish signal. Several directors (Stevens, Seawell, Coxe) have made very large sales ($50M-$240M blocks), which could reflect portfolio diversification rather than negative conviction. No insider has made a single open-market purchase in the data set, which is notable but not unusual for a stock that has appreciated dramatically.

**Analyst Consensus**:
| Metric | Value |
|--------|-------|
| Mean Price Target | $253.62 |
| Median Price Target | $250.00 |
| Low Target | $140.00 |
| High Target | $352.00 |
| Current Price | $185.41 |
| Upside to Mean Target | +36.8% |
| Number of Analysts | 58 |
| Strong Buy / Buy / Hold / Sell / Strong Sell | 12 / 47 / 3 / 1 / 0 |
| Recommendation Key | Strong Buy (mean score: 1.35) |
| Analyst Signal | **Bullish** |

**Analysis**: Insider and analyst signals are divergent. Insiders are net sellers with no purchases, but the pattern is predominantly systematic 10b5-1 plan sales rather than discretionary panic selling. For a company whose stock has appreciated ~5x in 2 years, this level of insider selling is expected and does not necessarily indicate negative fundamental conviction. The analyst consensus is overwhelmingly bullish: 59 out of 63 ratings are Buy or Strong Buy, with a mean price target implying 36.8% upside. Only 1 analyst has a Sell rating, and even the low target of $140 represents only ~24% downside. As a risk-neutral investor, the strong analyst consensus and structural explanation for insider selling result in a **net Neutral-to-Bullish** composite signal.

---

### SYNTHESIS & FINAL RECOMMENDATION

| Framework | Signal | Weight |
|-----------|--------|--------|
| Graham Margin of Safety | FAIL (negative MoS) | Negative |
| Buffett Economic Moat | Wide moat | Strong Positive |
| Damodaran Growth Reasonableness | Reasonable at forward P/E | Positive |
| Lynch PEG | 0.51-1.31 (favorable) | Positive |
| Piotroski F-Score | 8/9 (excellent) | Strong Positive |
| Insider & Analyst Sentiment | Mixed insiders / Strong analyst buy | Neutral-to-Positive |

**Scoring Summary**: Of the six frameworks, four produce positive signals (Moat, Growth, PEG, F-Score), one produces a negative signal (Graham MoS), and one is mixed (Sentiment). The Graham failure is the most significant headwind, but it is substantially mitigated by the fact that NVDA is not a value stock -- it is a high-growth compounder in the early-to-mid stages of a secular AI infrastructure buildout. The Graham framework is not well-suited to evaluate companies experiencing a structural earnings step-change.

**Key Risk Factors from 10-K**:
1. Customer concentration: A significant portion of data center revenue comes from a handful of hyperscale CSPs.
2. Export controls: U.S. government restrictions on sales to China have already impacted revenue and could tighten further.
3. Supply chain: Dependence on TSMC for leading-edge manufacturing creates single-source risk.
4. Competition: Custom silicon from hyperscalers (Google TPU, Amazon Trainium, Microsoft Maia) and AMD's MI-series GPUs could erode market share over time.
5. Cyclicality: AI infrastructure spending could prove more cyclical than currently assumed if ROI on AI deployments disappoints.

**Bull Case**: AI is a generational computing platform shift comparable to the internet. NVDA is the dominant infrastructure provider with a wide, deepening moat. The Blackwell architecture extends performance leadership. Enterprise AI adoption is still in early innings. Forward P/E of 24x is reasonable for 35%+ earnings growth.

**Bear Case**: Valuation assumes sustained hypergrowth that could disappoint if AI spending normalizes. Insider selling, while systematic, is voluminous. Custom silicon alternatives could commoditize GPU compute over 3-5 years. The trailing P/E of 46x leaves no room for execution missteps.

**FINAL RECOMMENDATION: BUY**
**CONFIDENCE: 7 / 10**

The risk-neutral recommendation is BUY at a confidence level of 7/10. The wide economic moat, exceptional financial quality (F-Score 8/9), favorable PEG ratio, and strong analyst consensus outweigh the Graham valuation concern. The forward P/E of 24x paired with ~91% near-term earnings growth and a normalized PEG of 1.31 offers an attractive risk-reward profile for a risk-neutral investor willing to accept that traditional value metrics do not adequately capture NVDA's structural growth trajectory. The confidence is capped at 7 (not higher) due to: (1) the sheer magnitude of the negative Graham margin of safety, (2) the heavy insider selling, and (3) the concentration risk in AI infrastructure spending.

---

### DATA TABLES

**Key Financial Metrics**:
| Metric | Value |
|--------|-------|
| Trailing P/E | 45.89 |
| Forward P/E | 24.04 |
| P/B | 37.90 |
| EV/EBITDA | 39.54 |
| Debt-to-Equity | 9.10% |
| ROE | 107.4% |
| ROA | 53.5% |
| FCF Yield | 1.18% |
| Current Ratio | 4.47 |
| Market Cap | $4,514.2B |
| Enterprise Value | $4,455.7B |
| Trailing EPS | $4.04 |
| Forward EPS | $7.71 |
| Dividend Yield | 0.02% |
| Free Cash Flow (FY2025) | $60.85B |

**Revenue & Earnings Trajectory**:
| Fiscal Year | Revenue | Net Income | Diluted EPS | Gross Margin |
|-------------|---------|------------|-------------|--------------|
| FY2022 (Jan 2022) | $26.91B | $9.75B | $0.39 | 64.9% |
| FY2023 (Jan 2023) | $26.97B | $4.37B | $0.17 | 56.9% |
| FY2024 (Jan 2024) | $60.92B | $29.76B | $1.19 | 72.7% |
| FY2025 (Jan 2025) | $130.50B | $72.88B | $2.94 | 75.0% |

**Quarterly EPS Trend**:
| Quarter | Diluted EPS |
|---------|-------------|
| Q3 FY2025 (Oct 2024) | $0.78 |
| Q4 FY2025 (Jan 2025) | $0.89 |
| Q1 FY2026 (Apr 2025) | $0.76 |
| Q2 FY2026 (Jul 2025) | $1.08 |
| Q3 FY2026 (Oct 2025) | $1.30 |

**Significant Insider Transactions (Last 6 Months)**:
| Date | Insider | Position | Transaction | Shares | Est. Value |
|------|---------|----------|-------------|--------|------------|
| 2026-01-21 | Ajay Puri | Officer | Sale | 200,000 | $36.0M |
| 2026-01-13 | Colette Kress | CFO | Sale | 47,640 | $8.8M |
| 2026-01-07 | Ajay Puri | Officer | Sale | 200,000 | $37.6M |
| 2026-01-02 | Donald Robertson | Officer | Sale | 80,000 | $15.2M |
| 2025-12-19 | Mark Stevens | Director | Sale | 222,500 | $40.1M |
| 2025-12-15 | Harvey Jones | Director | Sale | 250,000 | $44.3M |
| 2025-12-12 | Debora Shoquist | Officer | Sale | 229,840 | $41.4M |
| 2025-12-05 | Mark Stevens | Director | Sale | 350,000 | $63.6M |
| 2025-10-29 | Jensen Huang | CEO | Sale | 25,000 | $5.2M |
| 2025-10-28 | Jensen Huang | CEO | Sale | 125,000 | $23.6M |

**Analyst Estimates**:
| Metric | Value |
|--------|-------|
| Number of Analysts | 58 |
| Mean Price Target | $253.62 |
| Median Price Target | $250.00 |
| Low Target | $140.00 |
| High Target | $352.00 |
| Strong Buy | 12 |
| Buy | 47 |
| Hold | 3 |
| Sell | 1 |
| Strong Sell | 0 |
| Consensus | Strong Buy |

---

*This report was generated by The Value Analyst on 2026-02-07. It represents a point-in-time assessment based on available data and should not be construed as personalized investment advice. All investments carry risk, including the potential loss of principal.*
