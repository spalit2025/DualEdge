## VALUE ANALYST REPORT: NVDA
**Date**: 2026-02-07
**Risk Profile**: Risk-Averse

### SUMMARY
| Field | Value |
|-------|-------|
| RECOMMENDATION | SELL |
| CONFIDENCE | 7 / 10 |
| KEY DRIVER | Despite a wide economic moat and extraordinary earnings growth, the stock trades at a valuation that offers zero margin of safety; EPV analysis shows the market is pricing in perfection, and pervasive insider selling reinforces the risk-averse case to avoid. |
| CHANGE CONDITION | A sustained price decline to below $130 (bringing P/E closer to 30x trailing and delivering a meaningful margin of safety), OR clear evidence that forward earnings growth of 50%+ is sustainable for 3+ years beyond current consensus, would warrant upgrading to BUY. |

---

### 1. Graham's Margin of Safety

- **Normalized Earnings**: To compute Earnings Power Value (EPV), we normalize earnings across the last four fiscal years. FY2022 NI: $9.75B, FY2023: $4.37B, FY2024: $29.76B, FY2025: $72.88B. The simple average is ~$29.2B. However, the FY2023 trough was an aberration (crypto bust, inventory correction), and the recent trajectory is dramatically higher. Using a weighted normalization that gives more weight to recent years (1x/1x/2x/3x weighting): ($9.75 + $4.37 + $59.52 + $218.64) / 7 = ~$41.8B. Even using the most recent trailing twelve months (TTM) net income of approximately $99.1B (sum of last four quarters: $22.09 + $18.78 + $26.42 + $31.91 = $99.2B) as an aggressive "current earning power" figure, the EPV is still limited.
- **Earnings Power Value (EPV)**: Using normalized earnings of $41.8B / 0.095 cost of capital = **$440B**. Using TTM earnings of $99.2B / 0.095 = **$1,044B**. Even using the most generous interpretation (full TTM), EPV is ~$1.04T.
- **Current Market Cap**: **$4,514B**
- **Margin of Safety**: Using normalized EPV of $440B: market cap exceeds EPV by ~925% -- deeply negative margin of safety. Using aggressive TTM EPV of $1,044B: market cap exceeds EPV by ~333% -- still deeply negative.
- **P/E vs Historical Context**: Trailing P/E of 45.9x is elevated relative to the S&P 500 median (~20-22x) and even relative to large-cap tech peers. The forward P/E of 24.0x is more reasonable but embeds expectations for near-doubling of EPS.
- **Verdict**: **Negative / Insufficient**

The market is pricing NVDA not for its current or normalized earnings power, but for sustained hyper-growth far into the future. Under Graham's framework, there is no margin of safety whatsoever. The stock would need to trade at roughly $1,044B * 0.75 / 24.48B shares = ~$32 per share on normalized EPV (with 25% margin of safety) or ~$60 per share on TTM EPV. At $185.41, the market is pricing in enormous growth that has yet to be earned, which violates the core Graham principle of paying for demonstrated value, not speculative future value. For a risk-averse investor, this framework produces a clear SELL signal.

---

### 2. Buffett's Economic Moat

- **Pricing Power**: STRONG. NVIDIA commands gross margins of 75%+ (FY2025 gross margin: 97.86/130.50 = 75.0%, up from 72.7% in FY2024 and 56.9% in FY2023). This reflects extraordinary pricing power in the data center GPU market, where demand for AI training and inference hardware far exceeds supply. The Blackwell architecture launch further entrenches premium pricing through generational performance leaps. NVIDIA can and does price its products at significant premiums to competitors because customers derive outsized economic value from the performance advantage.

- **Switching Costs**: VERY HIGH. The CUDA software ecosystem, with 5.9 million+ developers, creates enormous switching costs. Enterprises that have built their AI workflows, trained models, and deployed inference pipelines on CUDA face massive retraining and re-engineering costs to move to alternative platforms (AMD ROCm, Intel oneAPI). The 10-K notes over 4,400 optimized applications and hundreds of domain-specific libraries, SDKs, and APIs. This deep software integration means switching is not just a hardware swap but a full-stack re-architecture.

- **Network Effects**: MODERATE TO STRONG. NVIDIA benefits from a developer-ecosystem network effect: the more developers build on CUDA, the more optimized software exists, which attracts more customers, which attracts more developers. The Inception startup program (thousands of startups) and Deep Learning Institute create a virtuous cycle. Additionally, the data center networking business (InfiniBand, Ethernet) benefits from network effects as interconnected multi-node clusters must use compatible hardware.

- **Cost Advantages**: MODERATE. NVIDIA's fabless model and enormous scale (FY2025 revenue of $130.5B) provide significant cost leverage. R&D spending of $12.9B is large in absolute terms but represents only 9.9% of revenue, meaning the massive R&D investment is amortized across a huge revenue base. Competitors would need to invest comparable sums with far less revenue to support it. However, the reliance on TSMC for fabrication means NVIDIA does not have proprietary manufacturing cost advantages.

- **Moat Rating**: **Wide**

NVIDIA possesses one of the widest economic moats in the technology sector. The combination of CUDA ecosystem lock-in, generational architecture leadership, and extraordinary pricing power creates durable competitive advantages. The 10-K evidence is compelling: every major cloud provider and server maker offers NVIDIA platforms, the software stack is deeply embedded across industries, and the company has expanded from GPUs alone to a full-stack data center infrastructure offering (GPUs, CPUs, DPUs, networking, software). However, a wide moat does not guarantee a reasonable stock price. Buffett himself has noted he would not overpay even for the best business.

---

### 3. Damodaran's Growth Reasonableness

- **Implied Growth Rate (from P/E)**: The trailing P/E of 45.9x, against a cost of equity of approximately 9.5%, implies the market expects earnings growth of roughly 35-40% annually for the next 5-7 years before terminal growth normalizes. Using the forward P/E of 24.0x, the implied growth is more moderate but still expects forward EPS of $7.71 to continue growing at 20%+ annually.
- **Reinvestment Rate x ROIC**: ROE of 107.4% is extraordinary. Net income retention rate (after dividends and buybacks) is high. However, sustainable growth = reinvestment rate x ROIC is somewhat misleading here because NVDA's asset-light model means ROIC is extremely elevated and not indicative of the capital needed to sustain future growth. The company is now investing heavily in capex ($3.2B in FY2025, accelerating to ~$5.8B annualized in recent quarters), which will moderate returns.
- **3-Year Revenue CAGR** (FY2022 to FY2025): ($130.5B / $26.9B)^(1/3) - 1 = **69.1%**
- **5-Year Revenue CAGR**: Not fully available from data, but FY2022-FY2025 3-year CAGR of 69% is extraordinary and clearly unsustainable at this scale.
- **Historical EPS CAGR** (FY2022 to FY2025): ($2.94 / $0.385)^(1/3) - 1 = **96.7%**
- **Assessment**: **Optimistic**

The market's implied growth expectations are not unreasonable given the trailing 3-year performance, but they are optimistic when projected forward. NVDA is now a $130B+ annual revenue company. Maintaining even 30%+ growth requires generating $40B+ in incremental revenue annually -- an amount that exceeds the total annual revenue of most semiconductor companies. The law of large numbers will increasingly constrain growth. The 10-K itself acknowledges risks of customer concentration (CSPs represent a large share of data center revenue), export restrictions (China), and potential competitive threats. For a risk-averse investor, paying for optimistic growth expectations at this scale introduces meaningful downside risk if growth merely normalizes to 15-20%.

---

### 4. Lynch's PEG Check

- **Trailing P/E**: 45.89
- **Forward Earnings Growth Rate**: Forward EPS of $7.71 vs trailing EPS of $4.04 implies ~91% forward growth. However, using a more conservative approach based on consensus and the trajectory of quarterly EPS (Q4 FY2025: $0.89, Q1 FY2026: $0.76, Q2 FY2026: $1.08, Q3 FY2026: $1.30), the annualized run-rate is ~$4.04 trailing and forward consensus is ~$7.71, suggesting ~91% growth. Using a more moderate long-term sustainable growth estimate of 30-40% (which is already aggressive for a company of this size), the PEG calculation changes materially.
- **PEG Ratio (using 91% forward growth)**: 45.89 / 91 = **0.50** -- appears undervalued
- **PEG Ratio (using 40% sustainable growth)**: 45.89 / 40 = **1.15** -- fair value
- **PEG Ratio (using 25% normalized growth)**: 45.89 / 25 = **1.84** -- overvalued
- **Assessment**: The PEG ratio is highly sensitive to the growth assumption used. At the current explosive growth rate, PEG appears favorable. However, Lynch's PEG framework was designed for steady-state growers, not hyperbolic growth phases. For a risk-averse investor, the appropriate growth rate to use is the one sustainable over the next 3-5 years. If growth decelerates to 25-30% (still exceptional), the PEG exceeds the 1.5 risk-averse threshold.

**Risk-Averse Assessment**: **MARGINAL TO OVERVALUED**. The PEG is favorable only if near-term hyper-growth persists. Using prudent growth assumptions, PEG exceeds the 1.5 threshold, producing a cautionary signal. This framework provides no clear buy signal for a risk-averse investor.

---

### 5. Piotroski F-Score

**Profitability (4 signals)**:
| Signal | Pass/Fail | Detail |
|--------|-----------|--------|
| Positive ROA | PASS | ROA = 53.5% -- strongly positive |
| Positive Operating Cash Flow | PASS | OCF = $64.1B -- strongly positive |
| Improving ROA (YoY) | PASS | FY2025 ROA: 72.88/111.6 = 65.3% vs FY2024: 29.76/65.7 = 45.3% -- improved |
| Cash Flow > Net Income | FAIL | OCF $64.1B < Net Income $72.9B (due to large working capital build) |

**Leverage (3 signals)**:
| Signal | Pass/Fail | Detail |
|--------|-----------|--------|
| Decreasing Long-term Debt/Assets | PASS | FY2025: 8.46/111.6 = 7.6% vs FY2024: 8.46/65.7 = 12.9% -- improved |
| Increasing Current Ratio | PASS | FY2025: 4.47 vs FY2024: 44.35/10.63 = 4.17 -- improved |
| No New Equity Issuance | PASS | Shares outstanding decreased from 24.64B to 24.48B -- net buyback, no dilutive issuance |

**Efficiency (2 signals)**:
| Signal | Pass/Fail | Detail |
|--------|-----------|--------|
| Improving Gross Margin | PASS | FY2025: 75.0% vs FY2024: 72.7% -- improved |
| Improving Asset Turnover | PASS | FY2025: 130.5/111.6 = 1.17x vs FY2024: 60.9/65.7 = 0.93x -- improved |

- **F-Score**: **8 / 9**
- **Trajectory**: **Improving** -- virtually every financial quality metric has strengthened dramatically

The F-Score of 8 out of 9 is excellent and well above the risk-averse threshold of 6. The only miss is operating cash flow trailing net income, which is attributable to rapid growth in accounts receivable and inventory (working capital investment to support revenue scaling). This is a growth-phase artifact, not a quality concern. The Piotroski analysis confirms that NVDA is a financially healthy, operationally excellent business. This is the one framework that provides an unambiguous positive signal.

---

### 6. Insider & Analyst Sentiment

**Insider Activity (Past 6 Months)**:
| Metric | Value |
|--------|-------|
| Net Insider Buying/Selling | **Overwhelmingly net selling** -- zero insider purchases identified across the entire dataset. Every transaction with a dollar value is a sale. |
| Cluster Selling (3+ in 30 days) | **Yes** -- CEO Jensen Huang has been selling 225,000 shares approximately every 3-5 business days on a systematic 10b5-1 plan since mid-2024. CFO Colette Kress sells ~47,640-66,670 shares monthly. Director Mark Stevens has sold millions of shares. Director Tench Coxe sold 1,000,000 shares at $142.80 in June 2025. Director A. Brooke Seawell sold hundreds of thousands of shares in July 2025. |
| Total Insider Sales Value (est. last 6 months) | **$1.5B+** in aggregate insider sales |
| Insider Signal | **Bearish** |

**Analyst Consensus**:
| Metric | Value |
|--------|-------|
| Mean Price Target | $253.62 |
| Current Price | $185.41 |
| Upside/Downside | +36.8% upside to mean target |
| Strong Buy / Buy / Hold / Sell / Strong Sell | 12 / 47 / 3 / 1 / 0 |
| Number of Analysts | 58 |
| Recommendation | Strong Buy (1.35 mean score) |
| Analyst Signal | **Bullish** |

The insider and analyst signals are diametrically opposed. Analysts are overwhelmingly bullish with a mean price target 37% above the current price. However, insiders -- who have the deepest understanding of the business -- are selling relentlessly and at scale. CEO Jensen Huang has sold approximately 225,000 shares every few trading days for over a year. While these are 10b5-1 pre-planned dispositions, the sheer volume and consistency are notable.

For a risk-averse investor, insider selling should be weighted more heavily than analyst optimism. Analysts have well-documented herding tendencies and rarely issue sell ratings on mega-cap momentum stocks. Insider selling of this magnitude, while not necessarily signaling belief in overvaluation (it can reflect diversification, tax planning, or philanthropy), provides no offsetting positive signal. The absence of ANY insider buying in the dataset is significant.

**Net Signal for Risk-Averse Investor**: **Bearish** -- the pervasive insider selling outweighs Wall Street optimism.

---

### SYNTHESIS & FINAL RECOMMENDATION

**Framework Scorecard:**

| Framework | Signal | Weight (Risk-Averse) |
|-----------|--------|---------------------|
| Graham Margin of Safety | SELL -- deeply negative MoS | High |
| Buffett Economic Moat | POSITIVE -- Wide moat | Medium |
| Damodaran Growth Reasonableness | CAUTIOUS -- Optimistic pricing | High |
| Lynch PEG | NEUTRAL to CAUTIOUS -- marginal at sustainable rates | Medium |
| Piotroski F-Score | POSITIVE -- 8/9, excellent quality | Medium |
| Insider & Analyst Sentiment | BEARISH -- massive insider selling | High |

**The Tension**: NVDA is an outstanding business (wide moat, 8/9 F-Score, extraordinary financial performance) trading at a price that embeds unrealistic expectations for a risk-averse investor. The quality of the business is undeniable. The price paid for that quality is the problem.

**Risk-Averse Decision**: The Graham framework (highest weight) and insider sentiment (high weight) both signal SELL. The Damodaran growth test (high weight) shows the market is pricing optimistic expectations at a scale where deceleration is mathematically likely. Only the F-Score and moat analysis are positive, but these speak to business quality, not valuation attractiveness.

**Final Verdict**: **SELL** with **Confidence 7/10**

The confidence is not higher because the wide moat and extraordinary operational execution create a real possibility that the company exceeds even the market's aggressive expectations, which would make the current price look reasonable in hindsight. AI infrastructure spending may have a longer runway than historical technology investment cycles. However, a risk-averse mandate requires prioritizing downside protection over upside participation. At $185.41, the risk-reward is asymmetric to the downside for a value-oriented, risk-averse investor.

**What would change the recommendation**:
1. Price decline to ~$120-130, creating a forward P/E below 18x and a more reasonable margin of safety against plausible earnings scenarios
2. Two consecutive quarters of revenue growth acceleration (not deceleration) above 50% YoY, demonstrating the growth runway is extending rather than compressing
3. Meaningful insider buying -- even one significant open-market purchase by the CEO or CFO
4. Evidence of a durable structural shift in the competitive landscape (e.g., a major hyperscaler publicly committing to NVIDIA-exclusive AI infrastructure for 5+ years)

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
| Market Cap | $4,514B |
| Enterprise Value | $4,456B |
| Free Cash Flow | $53.3B |
| Trailing EPS | $4.04 |
| Forward EPS | $7.71 |

**Revenue & Earnings Growth (Annual)**:
| Fiscal Year | Revenue ($B) | Net Income ($B) | Diluted EPS | YoY Rev Growth |
|-------------|-------------|----------------|-------------|----------------|
| FY2022 (Jan 2022) | 26.91 | 9.75 | $0.385 | -- |
| FY2023 (Jan 2023) | 26.97 | 4.37 | $0.174 | +0.2% |
| FY2024 (Jan 2024) | 60.92 | 29.76 | $1.19 | +125.8% |
| FY2025 (Jan 2025) | 130.50 | 72.88 | $2.94 | +114.2% |

**Quarterly EPS Trajectory**:
| Quarter | Diluted EPS |
|---------|-------------|
| Q3 FY2025 (Oct 2024) | $0.78 |
| Q4 FY2025 (Jan 2025) | $0.89 |
| Q1 FY2026 (Apr 2025) | $0.76 |
| Q2 FY2026 (Jul 2025) | $1.08 |
| Q3 FY2026 (Oct 2025) | $1.30 |

**Most Recent Quarterly Revenue ($B)**:
| Quarter | Revenue | QoQ Growth |
|---------|---------|------------|
| Q4 FY2025 (Jan 2025) | $39.33 | -- |
| Q1 FY2026 (Apr 2025) | $44.06 | +12.0% |
| Q2 FY2026 (Jul 2025) | $46.74 | +6.1% |
| Q3 FY2026 (Oct 2025) | $57.01 | +22.0% |

**Significant Insider Transactions (Last 6 Months)**:
| Date | Insider | Position | Transaction | Shares | Value ($M) |
|------|---------|----------|-------------|--------|------------|
| 2026-01-21 | Ajay K. Puri | Officer | Sale | 200,000 | $36.0 |
| 2026-01-13 | Colette M. Kress | CFO | Sale | 47,640 | $8.8 |
| 2026-01-07 | Ajay K. Puri | Officer | Sale | 200,000 | $37.6 |
| 2026-01-02 | Donald F. Robertson Jr | Officer | Sale | 80,000 | $15.2 |
| 2025-12-19 | Mark A. Stevens | Director | Sale | 222,500 | $40.1 |
| 2025-12-15 | Harvey C. Jones Jr. | Director | Sale | 250,000 | $44.3 |
| 2025-12-12 | Debora C. Shoquist | Officer | Sale | 229,840 | $41.4 |
| 2025-12-05 | Mark A. Stevens | Director | Sale | 350,000 | $63.6 |
| 2025-11-03 | Colette M. Kress | CFO | Sale | 47,640 | $9.9 |
| 2025-10-29 | Jensen Huang | CEO | Sale | 25,000 | $5.2 |
| 2025-10-28 | Jensen Huang | CEO | Sale | 125,000 | $23.6 |
| 2025-10-23 | Jensen Huang | CEO | Sale | 225,000 | $40.7 |
| 2025-10-20 | Jensen Huang | CEO | Sale | 225,000 | $41.1 |
| 2025-10-15 | Jensen Huang | CEO | Sale | 225,000 | $41.3 |
| 2025-10-10 | Jensen Huang | CEO | Sale | 225,000 | $42.9 |
| 2025-10-07 | Jensen Huang | CEO | Sale | 225,000 | $42.1 |
| 2025-10-02 | Jensen Huang | CEO | Sale | 225,000 | $42.1 |
| 2025-09-29 | Jensen Huang | CEO | Sale | 225,000 | $40.2 |
| 2025-09-24 | Jensen Huang | CEO | Sale | 225,000 | $40.2 |
| 2025-09-19 | Mark A. Stevens | Director | Sale | 350,000 | $61.7 |

*Note: Zero insider purchases were identified across the entire dataset. All monetary transactions are sales.*

**Analyst Price Target Distribution**:
| Metric | Value |
|--------|-------|
| Number of Analysts | 58 |
| Low Target | $140.00 |
| Mean Target | $253.62 |
| Median Target | $250.00 |
| High Target | $352.00 |
| Current Price | $185.41 |
| Implied Upside to Mean | +36.8% |
| Consensus Rating | Strong Buy (1.35) |

**Recommendation Breakdown**:
| Rating | Count |
|--------|-------|
| Strong Buy | 12 |
| Buy | 47 |
| Hold | 3 |
| Sell | 1 |
| Strong Sell | 0 |

---

*Disclaimer: This analysis is for informational and educational purposes only and does not constitute investment advice. Past performance is not indicative of future results. Investors should conduct their own due diligence and consult a qualified financial advisor before making investment decisions.*
