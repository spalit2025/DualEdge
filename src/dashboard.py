"""Markdown dashboard formatter for DualEdge Watchlist Monitor.

Generates the daily_scan.md dashboard from scan results, including
portfolio summary, triggered alerts, holdings detail, watchlist status,
and recommended actions.
"""

from datetime import datetime, timedelta


# Priority ordering for alert sorting
PRIORITY_ORDER = {"HIGHEST": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "INFO": 4}
PRIORITY_EMOJI = {
    "HIGHEST": "\U0001f534",  # red circle
    "HIGH": "\u26a0\ufe0f",   # warning
    "MEDIUM": "\u26a0\ufe0f", # warning
    "LOW": "\U0001f4a1",      # lightbulb
    "INFO": "\U0001f4a1",     # lightbulb
}
PRIORITY_LABEL = {
    "HIGHEST": "CRITICAL",
    "HIGH": "WARNING",
    "MEDIUM": "WARNING",
    "LOW": "INFORMATIONAL",
    "INFO": "INFORMATIONAL",
}


def generate_dashboard(scan_results: dict, risk_profile: str,
                       scan_duration: float) -> str:
    """Generate complete markdown dashboard from scan results.

    Args:
        scan_results: Full scan result dict from run_daily_scan().
        risk_profile: "risk-neutral" or "risk-averse".
        scan_duration: Time in seconds the scan took.

    Returns:
        Complete markdown string for daily_scan.md.
    """
    scan_date = scan_results["scan_date"]
    stocks_scanned = scan_results.get("stocks_scanned", 0)
    has_prior = scan_results.get("has_prior_scan", False)
    scan_time = datetime.now().strftime("%H:%M:%S")

    sections = []

    # Header
    sections.append(f"# DualEdge Daily Scan — {scan_date}")
    sections.append(f"**Risk Profile**: {risk_profile}")
    sections.append(
        f"**Scan Time**: {scan_time} | "
        f"**Stocks Scanned**: {stocks_scanned} | "
        f"**Prior Scan**: {'Yes' if has_prior else 'No (first run — baselines established)'}"
    )
    sections.append("")
    sections.append("---")
    sections.append("")

    # Portfolio summary
    sections.append(format_portfolio_summary(scan_results.get("portfolio_summary", {})))
    sections.append("")

    # Triggered alerts
    all_triggers = scan_results.get("all_triggers", [])
    sections.append(format_alerts(all_triggers))
    sections.append("")
    sections.append("---")
    sections.append("")

    # Holdings detail
    sections.append(format_holdings_table(scan_results))
    sections.append("")

    # Concentration
    sections.append(format_concentration(scan_results.get("concentration", {}),
                                          scan_results.get("correlation", {})))
    sections.append("")
    sections.append("---")
    sections.append("")

    # Watchlist
    sections.append(format_watchlist_table(scan_results))
    sections.append("")
    sections.append("---")
    sections.append("")

    # Recommended actions
    sections.append(format_recommended_actions(
        all_triggers, scan_results.get("concentration", {})))
    sections.append("")
    sections.append("---")
    sections.append("")

    # Footer
    tomorrow = (datetime.strptime(scan_date, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
    sections.append(
        f"*Scan computed in {scan_duration:.1f}s. No LLM tokens consumed.*  "
    )
    sections.append(f"*Next scan: {tomorrow}*")

    return "\n".join(sections)


def format_portfolio_summary(portfolio: dict) -> str:
    """Format the portfolio summary section."""
    lines = ["## PORTFOLIO SUMMARY"]

    if not portfolio.get("has_positions", False):
        lines.append("")
        lines.append("*No active positions (all holdings have 0 shares). "
                     "Update watchlist.json with your actual positions.*")
        return "\n".join(lines)

    total_value = portfolio.get("total_value", 0)
    daily_change = portfolio.get("daily_change_dollar", 0)
    daily_pct = portfolio.get("daily_change_pct")
    pnl = portfolio.get("total_pnl_dollar", 0)
    pnl_pct = portfolio.get("total_pnl_pct")
    cash = portfolio.get("cash_balance", 0)
    cash_pct = portfolio.get("cash_allocation_pct")

    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("|--------|-------|")
    lines.append(f"| Total Value | ${total_value:,.2f} |")
    lines.append(f"| Daily Change | ${daily_change:+,.2f} ({_fmt_pct(daily_pct)}) |")
    lines.append(f"| Unrealized P&L | ${pnl:+,.2f} ({_fmt_pct(pnl_pct)}) |")
    lines.append(f"| Cash | ${cash:,.2f} ({_fmt_pct(cash_pct)}) |")

    return "\n".join(lines)


def format_alerts(all_triggers: list[dict]) -> str:
    """Format triggered alerts, grouped by priority level."""
    lines = [f"## TRIGGERED ALERTS ({len(all_triggers)})"]

    if not all_triggers:
        lines.append("")
        lines.append("*No triggers fired. All stocks within normal parameters.*")
        return "\n".join(lines)

    # Sort by priority
    sorted_triggers = sorted(all_triggers, key=lambda t: PRIORITY_ORDER.get(t.get("priority", "LOW"), 3))

    # Group by priority label
    groups = {}
    for t in sorted_triggers:
        priority = t.get("priority", "LOW")
        label = PRIORITY_LABEL.get(priority, "INFORMATIONAL")
        emoji = PRIORITY_EMOJI.get(priority, "\U0001f4a1")
        key = f"{emoji} {label}"
        if key not in groups:
            groups[key] = []
        groups[key].append(t)

    for group_label, triggers in groups.items():
        lines.append("")
        lines.append(f"### {group_label}")
        for t in triggers:
            ticker = t.get("ticker", "?")
            desc = t.get("description", "")
            trigger_id = t.get("id", "")
            lines.append(f"- **{ticker}** [{trigger_id}]: {desc}")
            if t.get("priority") == "HIGHEST":
                lines.append(f"  → **Action: Run full DualEdge analysis on {ticker}**")

    return "\n".join(lines)


def format_holdings_table(scan_results: dict) -> str:
    """Format the holdings detail table with indicators and flags."""
    lines = ["## HOLDINGS DETAIL"]

    stocks = scan_results.get("stocks", {})
    holdings_detail = scan_results.get("holdings_detail", [])

    if not holdings_detail:
        lines.append("")
        lines.append("*No holdings configured.*")
        return "\n".join(lines)

    lines.append("")
    lines.append("| Ticker | Price | Daily Chg | P&L | Weight | Stage | RSI | vs 30w MA | RS vs SPX | Flags |")
    lines.append("|--------|-------|-----------|-----|--------|-------|-----|-----------|-----------|-------|")

    for hd in holdings_detail:
        ticker = hd["ticker"]
        stock = stocks.get(ticker, {})
        ind = stock.get("indicators", {})
        triggers = stock.get("triggers_fired", [])

        price = f"${hd['current_price']:,.2f}" if hd.get("current_price") else "N/A"
        daily_chg = _fmt_pct(hd.get("daily_change_pct")) if hd.get("daily_change_pct") is not None else "N/A"
        pnl = _fmt_pct(hd.get("pnl_pct")) if hd.get("pnl_pct") is not None else "N/A"
        weight = f"{stock.get('weight_pct', 0):.1f}%" if stock.get("weight_pct") else "—"

        stage = str(ind.get("weinstein_stage", "—"))
        rsi = f"{ind.get('rsi', 0):.1f}" if ind.get("rsi") is not None else "—"

        dist_30w = ind.get("distance_30w_ma_pct")
        if dist_30w is not None:
            if abs(dist_30w) < 1:
                vs_30w = "AT MA"
            else:
                vs_30w = f"{dist_30w:+.1f}%"
        else:
            vs_30w = "—"

        rs_6m = ind.get("rs_vs_spx_6m")
        rs_traj = ind.get("rs_trajectory_vs_spx", "")
        if rs_6m is not None:
            arrow = " ↑" if rs_traj == "improving" else " ↓" if rs_traj == "deteriorating" else ""
            rs_str = f"{rs_6m:.2f}{arrow}"
        else:
            rs_str = "—"

        flags = _format_flags(triggers)

        lines.append(f"| {ticker} | {price} | {daily_chg} | {pnl} | {weight} | {stage} | {rsi} | {vs_30w} | {rs_str} | {flags} |")

    return "\n".join(lines)


def format_concentration(concentration: dict, correlation: dict) -> str:
    """Format concentration and correlation warnings."""
    lines = []

    flags = concentration.get("concentration_flags", [])
    if flags:
        flag_strs = []
        for f in flags:
            flag_strs.append(f"\u26a0\ufe0f {f}")
        lines.append("**Concentration**: " + " | ".join(flag_strs))

    high_pairs = correlation.get("high_correlation_pairs", [])
    for pair in high_pairs:
        lines.append(
            f"\U0001f4a1 HIGH CORRELATION: {pair['ticker_a']} and {pair['ticker_b']} "
            f"(r={pair['correlation']}) — limited diversification benefit"
        )

    return "\n".join(lines) if lines else ""


def format_watchlist_table(scan_results: dict) -> str:
    """Format the watchlist table with indicators and flags."""
    lines = ["## WATCHLIST"]

    stocks = scan_results.get("stocks", {})
    holdings_tickers = {hd["ticker"] for hd in scan_results.get("holdings_detail", [])}

    watchlist_stocks = {t: s for t, s in stocks.items() if t not in holdings_tickers}

    # Also include zero-position holdings in watchlist view
    for hd in scan_results.get("holdings_detail", []):
        if hd.get("is_zero_position", False) and hd["ticker"] in stocks:
            watchlist_stocks[hd["ticker"]] = stocks[hd["ticker"]]

    if not watchlist_stocks:
        lines.append("")
        lines.append("*No watchlist stocks configured.*")
        return "\n".join(lines)

    lines.append("")
    lines.append("| Ticker | Price | Daily Chg | Stage | RSI | vs 30w MA | RS vs SPX | CAN SLIM | Flags |")
    lines.append("|--------|-------|-----------|-------|-----|-----------|-----------|----------|-------|")

    for ticker in sorted(watchlist_stocks.keys()):
        stock = watchlist_stocks[ticker]
        ind = stock.get("indicators", {})
        triggers = stock.get("triggers_fired", [])

        price = f"${stock.get('current_price', 0):,.2f}"
        daily_chg = _fmt_pct(stock.get("daily_change_pct"))

        stage = str(ind.get("weinstein_stage", "—"))
        rsi = f"{ind.get('rsi', 0):.1f}" if ind.get("rsi") is not None else "—"

        dist_30w = ind.get("distance_30w_ma_pct")
        if dist_30w is not None:
            if abs(dist_30w) < 1:
                vs_30w = "AT MA"
            else:
                vs_30w = f"{dist_30w:+.1f}%"
        else:
            vs_30w = "—"

        rs_6m = ind.get("rs_vs_spx_6m")
        rs_traj = ind.get("rs_trajectory_vs_spx", "")
        if rs_6m is not None:
            arrow = " ↑" if rs_traj == "improving" else " ↓" if rs_traj == "deteriorating" else ""
            rs_str = f"{rs_6m:.2f}{arrow}"
        else:
            rs_str = "—"

        canslim = ind.get("canslim_score")
        canslim_str = f"{canslim}/5" if canslim is not None else "—"

        flags = _format_flags(triggers)

        lines.append(f"| {ticker} | {price} | {daily_chg} | {stage} | {rsi} | {vs_30w} | {rs_str} | {canslim_str} | {flags} |")

    return "\n".join(lines)


def format_recommended_actions(all_triggers: list[dict],
                                concentration: dict) -> str:
    """Generate actionable recommendations based on triggers and concentration."""
    lines = ["## RECOMMENDED ACTIONS"]

    actions = []
    action_num = 1

    # HIGHEST priority: recommend deep dives
    deep_dive_tickers = set()
    for t in all_triggers:
        if t.get("priority") == "HIGHEST":
            ticker = t.get("ticker", "?")
            if ticker not in deep_dive_tickers:
                desc = t.get("description", "")
                actions.append(f"{action_num}. **Run DualEdge on {ticker}** — {desc}")
                action_num += 1
                deep_dive_tickers.add(ticker)

    # HIGH priority: review positions
    high_tickers = set()
    for t in all_triggers:
        if t.get("priority") == "HIGH" and t.get("ticker") not in deep_dive_tickers:
            ticker = t.get("ticker", "?")
            if ticker not in high_tickers:
                trigger_id = t.get("id", "")
                desc = t.get("description", "")
                actions.append(f"{action_num}. **Review {ticker}** — [{trigger_id}] {desc}")
                action_num += 1
                high_tickers.add(ticker)

    # MEDIUM priority: monitor
    medium_tickers = set()
    for t in all_triggers:
        if t.get("priority") == "MEDIUM":
            ticker = t.get("ticker", "?")
            if ticker not in deep_dive_tickers and ticker not in high_tickers and ticker not in medium_tickers:
                desc = t.get("description", "")
                actions.append(f"{action_num}. **Monitor {ticker}** — {desc}")
                action_num += 1
                medium_tickers.add(ticker)

    # Concentration warnings
    flags = concentration.get("concentration_flags", [])
    if flags:
        actions.append(f"{action_num}. **Address concentration risk** — " + "; ".join(flags))
        action_num += 1

    if not actions:
        lines.append("")
        lines.append("*No actions required. Portfolio within normal parameters.*")
    else:
        lines.append("")
        lines.extend(actions)

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fmt_pct(value) -> str:
    """Format a percentage value with sign."""
    if value is None:
        return "N/A"
    return f"{value:+.2f}%"


def _format_flags(triggers: list[dict]) -> str:
    """Format trigger list into compact flag string for table cells."""
    if not triggers:
        return "\u2705"  # green checkmark

    flag_parts = []
    for t in triggers:
        priority = t.get("priority", "LOW")
        trigger_id = t.get("id", "")
        emoji = PRIORITY_EMOJI.get(priority, "\U0001f4a1")

        # Short label based on trigger ID
        short_labels = {
            "A1": "STAGE",
            "A2": "30W MA",
            "A3": "200D MA",
            "A4": "MA ALIGN",
            "B1": "RSI \u2191",
            "B2": "RSI \u2193",
            "B3": "EXTENDED",
            "B4": "Z-SCORE",
            "B5": "RS",
            "C1": "VOL SPIKE",
            "C2": "OBV DIV",
            "C3": "VOL RATIO",
            "C4": "SQUEEZE",
            "D1": "P/E",
            "D2": "EPS",
            "D3": "INSIDER",
            "E1": "CHANGE COND",
            "E2": "STALE",
        }
        label = short_labels.get(trigger_id, trigger_id)
        flag_parts.append(f"{emoji} {label}")

    return " ".join(flag_parts)
