# DualEdge Roadmap

## Content Pipeline

Three articles drawn from existing project documentation:

| # | Article | Source Material | Platform | Effort |
|---|---------|----------------|----------|--------|
| 1 | "Why I Built Two AI Analysts That Argue With Each Other" | PRD.md intro, debate protocol design, AAPL debate log | Substack / Medium | M |
| 2 | "12 Investment Frameworks, One AI System" | docs/investment-techniques-guide.md | Substack / Medium | S (80% written) |
| 3 | "Building a Zero-Cost Portfolio Scanner with 18 Trigger Conditions" | docs/scanner-explainer.md | Substack / Medium | S (80% written) |

Article 1 is the hook -- the adversarial AI thesis is the differentiator. Articles 2 and 3 are deep dives that demonstrate domain expertise and are already 80% written as project documentation.

---

## V1.2: Scanner Enhancements

| Feature | Description | Value |
|---------|-------------|-------|
| Auto-populate change conditions | Parse final_report.md after each DualEdge run and update watchlist.json automatically | Closes the manual loop between deep analysis and daily monitoring |
| Historical scan comparison | Dashboard comparing today's scan to 7/30/90 days ago -- trending triggers, resolved alerts | scan_data.json already supports this; needs visualization |
| Notifications | Email or Slack alerts on HIGHEST-priority triggers (change conditions met) | Reduces need to manually check the dashboard |
| Sector rotation view | Aggregate scanner data across sectors to identify rotation patterns | Portfolio-level insight beyond individual stock triggers |

---

## V2: Platform Evolution

| Feature | Description | Why It Matters |
|---------|-------------|----------------|
| Web dashboard | Streamlit or static HTML dashboard for scanner output | Makes results shareable, tweetable, monetizable |
| API-based orchestration | Replace Claude Code Agent Teams with Claude API SDK | Pip-installable, runs anywhere, no IDE dependency |
| International equities | Non-US markets, alternative data sources | Expands addressable market |
| Options chain analysis | Implied volatility, put/call ratios, unusual activity | Adds a dimension the current 12 frameworks miss |
| Custom framework plugins | Let users define their own analytical frameworks via config | Platform extensibility |

The API migration (row 2) is the most important -- it removes the Claude Code dependency and makes DualEdge a standalone Python package anyone can run.

---

## V3: Community & Monetization

| Path | Model | Effort |
|------|-------|--------|
| Weekly newsletter | Scanner output for 50 popular stocks, published weekly. Zero marginal cost per issue. | M -- template + automation |
| Open-source community | Accept framework contributions. "Add your own guru" via plugin system. | L -- needs plugin architecture |
| Premium tier | Custom watchlists, faster scanning, API access, priority support | L -- needs web infrastructure |
| Consulting / content | Use DualEdge analyses as the backbone for investment commentary | S -- leverages existing output |

The newsletter is the lowest-effort, highest-signal monetization path. The scanner already produces the content; it just needs formatting and distribution.
