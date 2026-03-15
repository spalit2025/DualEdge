"""Data retrieval utilities for DualEdge stock analysis.

Provides functions to pull financial data from yfinance and SEC EDGAR.
All functions handle errors gracefully — returning None or empty structures
rather than raising exceptions — so agents can note data gaps in their analysis.
"""

import time
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import requests
import yfinance as yf

from src.sector_map import get_sector_etf

# SEC EDGAR configuration
EDGAR_HEADERS = {
    "User-Agent": "DualEdge/1.0 (your-email@example.com)",
    "Accept-Encoding": "gzip, deflate",
}
EDGAR_RATE_LIMIT_SECONDS = 0.12  # slightly above 100ms for safety


def _retry(func, retries: int = 3, delay: float = 2.0):
    """Retry a callable up to `retries` times with `delay` seconds between attempts."""
    last_err = None
    for attempt in range(retries):
        try:
            return func()
        except Exception as e:
            last_err = e
            if attempt < retries - 1:
                time.sleep(delay)
    raise last_err


# ---------------------------------------------------------------------------
# Ticker Validation
# ---------------------------------------------------------------------------

def validate_ticker(ticker: str) -> bool:
    """Check if a US equity ticker exists via yfinance.

    Args:
        ticker: Ticker symbol to validate (e.g., 'AAPL').

    Returns:
        True if the ticker is valid and has price data, False otherwise.
    """
    try:
        t = yf.Ticker(ticker)
        hist = t.history(period="5d")
        return len(hist) > 0
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Financial Statements
# ---------------------------------------------------------------------------

def get_financials(ticker: str) -> dict | None:
    """Pull income statement, balance sheet, and cash flow (annual + quarterly).

    Args:
        ticker: US equity ticker symbol.

    Returns:
        Dict with keys 'income_stmt', 'income_stmt_quarterly', 'balance_sheet',
        'balance_sheet_quarterly', 'cash_flow', 'cash_flow_quarterly'.
        Each value is a pandas DataFrame. Returns None if retrieval fails.
    """
    try:
        t = yf.Ticker(ticker)
        result = {
            "income_stmt": t.income_stmt,
            "income_stmt_quarterly": t.quarterly_income_stmt,
            "balance_sheet": t.balance_sheet,
            "balance_sheet_quarterly": t.quarterly_balance_sheet,
            "cash_flow": t.cashflow,
            "cash_flow_quarterly": t.quarterly_cashflow,
        }
        if result["income_stmt"] is None or result["income_stmt"].empty:
            print(f"Warning: No income statement data for {ticker}")
            return None
        return result
    except Exception as e:
        print(f"Error retrieving financials for {ticker}: {e}")
        return None


# ---------------------------------------------------------------------------
# Key Ratios
# ---------------------------------------------------------------------------

def get_key_ratios(ticker: str) -> dict | None:
    """Compute/pull key financial ratios for fundamental analysis.

    Retrieves: P/E, P/B, EV/EBITDA, debt-to-equity, ROE, ROA,
    FCF yield, and current ratio.

    Args:
        ticker: US equity ticker symbol.

    Returns:
        Flat dict of ratio name → value. Returns None if retrieval fails.
        Individual ratios may be None if the underlying data is unavailable.
    """
    try:
        t = yf.Ticker(ticker)
        info = t.info

        # Pull what yfinance provides directly
        pe = info.get("trailingPE")
        forward_pe = info.get("forwardPE")
        pb = info.get("priceToBook")
        ev_ebitda = info.get("enterpriseToEbitda")
        de = info.get("debtToEquity")
        roe = info.get("returnOnEquity")
        roa = info.get("returnOnAssets")
        current_ratio = info.get("currentRatio")

        # FCF yield = free cash flow / market cap
        fcf = info.get("freeCashflow")
        market_cap = info.get("marketCap")
        fcf_yield = None
        if fcf is not None and market_cap and market_cap > 0:
            fcf_yield = fcf / market_cap

        # Additional useful fields
        market_cap_val = info.get("marketCap")
        ev = info.get("enterpriseValue")
        trailing_eps = info.get("trailingEps")
        forward_eps = info.get("forwardEps")
        dividend_yield = info.get("dividendYield")
        peg_ratio = info.get("pegRatio")
        price = info.get("currentPrice") or info.get("regularMarketPrice")

        return {
            "trailing_pe": pe,
            "forward_pe": forward_pe,
            "pb": pb,
            "ev_ebitda": ev_ebitda,
            "debt_to_equity": de,
            "roe": roe,
            "roa": roa,
            "current_ratio": current_ratio,
            "fcf_yield": fcf_yield,
            "market_cap": market_cap_val,
            "enterprise_value": ev,
            "trailing_eps": trailing_eps,
            "forward_eps": forward_eps,
            "dividend_yield": dividend_yield,
            "peg_ratio": peg_ratio,
            "current_price": price,
            "free_cash_flow": fcf,
        }
    except Exception as e:
        print(f"Error retrieving key ratios for {ticker}: {e}")
        return None


# ---------------------------------------------------------------------------
# OHLCV Data
# ---------------------------------------------------------------------------

def get_ohlcv_daily(ticker: str, months: int = 18) -> pd.DataFrame | None:
    """Pull daily OHLCV price data.

    Args:
        ticker: US equity ticker symbol.
        months: Number of months of history to retrieve (default 18).

    Returns:
        DataFrame with Date index, columns: Open, High, Low, Close, Volume.
        Returns None if retrieval fails.
    """
    try:
        end = datetime.now()
        start = end - timedelta(days=months * 30)
        df = _retry(lambda: yf.download(ticker, start=start.strftime("%Y-%m-%d"),
                                         end=end.strftime("%Y-%m-%d"),
                                         interval="1d", progress=False, auto_adjust=True))
        if df is None or df.empty:
            print(f"Warning: No daily OHLCV data for {ticker}")
            return None
        # Flatten MultiIndex columns if present (yfinance sometimes returns them)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        return df[["Open", "High", "Low", "Close", "Volume"]]
    except Exception as e:
        print(f"Error retrieving daily OHLCV for {ticker}: {e}")
        return None


def get_ohlcv_weekly(ticker: str, years: int = 3) -> pd.DataFrame | None:
    """Pull weekly OHLCV price data.

    Args:
        ticker: US equity ticker symbol.
        years: Number of years of history to retrieve (default 3).

    Returns:
        DataFrame with Date index, columns: Open, High, Low, Close, Volume.
        Returns None if retrieval fails.
    """
    try:
        end = datetime.now()
        start = end - timedelta(days=years * 365)
        df = _retry(lambda: yf.download(ticker, start=start.strftime("%Y-%m-%d"),
                                         end=end.strftime("%Y-%m-%d"),
                                         interval="1wk", progress=False, auto_adjust=True))
        if df is None or df.empty:
            print(f"Warning: No weekly OHLCV data for {ticker}")
            return None
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        return df[["Open", "High", "Low", "Close", "Volume"]]
    except Exception as e:
        print(f"Error retrieving weekly OHLCV for {ticker}: {e}")
        return None


# ---------------------------------------------------------------------------
# Benchmark Data
# ---------------------------------------------------------------------------

def get_benchmark_data(ticker: str, months: int = 18) -> tuple[pd.DataFrame | None, pd.DataFrame | None]:
    """Pull S&P 500 and relevant sector ETF daily data for relative strength.

    Args:
        ticker: Stock ticker (used to look up sector ETF).
        months: Number of months of history (default 18).

    Returns:
        Tuple of (spx_df, sector_etf_df). Either may be None on failure.
    """
    end = datetime.now()
    start = end - timedelta(days=months * 30)
    start_str = start.strftime("%Y-%m-%d")
    end_str = end.strftime("%Y-%m-%d")

    spx_df = None
    sector_df = None

    try:
        spx = _retry(lambda: yf.download("^GSPC", start=start_str, end=end_str,
                                          interval="1d", progress=False, auto_adjust=True))
        if spx is not None and not spx.empty:
            if isinstance(spx.columns, pd.MultiIndex):
                spx.columns = spx.columns.get_level_values(0)
            spx_df = spx[["Open", "High", "Low", "Close", "Volume"]]
    except Exception as e:
        print(f"Warning: Could not retrieve S&P 500 data: {e}")

    sector_etf = get_sector_etf(ticker)
    try:
        sec = _retry(lambda: yf.download(sector_etf, start=start_str, end=end_str,
                                          interval="1d", progress=False, auto_adjust=True))
        if sec is not None and not sec.empty:
            if isinstance(sec.columns, pd.MultiIndex):
                sec.columns = sec.columns.get_level_values(0)
            sector_df = sec[["Open", "High", "Low", "Close", "Volume"]]
    except Exception as e:
        print(f"Warning: Could not retrieve sector ETF ({sector_etf}) data: {e}")

    return spx_df, sector_df


# ---------------------------------------------------------------------------
# Insider Transactions
# ---------------------------------------------------------------------------

def get_insider_transactions(ticker: str) -> pd.DataFrame | None:
    """Pull insider transactions from yfinance.

    Args:
        ticker: US equity ticker symbol.

    Returns:
        DataFrame of insider transactions. Returns empty DataFrame if none found,
        None if retrieval fails entirely.
    """
    try:
        t = yf.Ticker(ticker)
        insider = t.insider_transactions
        if insider is None or (hasattr(insider, 'empty') and insider.empty):
            return pd.DataFrame()
        return insider
    except Exception as e:
        print(f"Error retrieving insider transactions for {ticker}: {e}")
        return None


# ---------------------------------------------------------------------------
# Analyst Data
# ---------------------------------------------------------------------------

def get_analyst_data(ticker: str) -> dict | None:
    """Pull analyst price targets and recommendation trends.

    Args:
        ticker: US equity ticker symbol.

    Returns:
        Dict with 'price_targets' (dict with low/mean/median/high/current)
        and 'recommendations' (DataFrame or summary). Returns None on failure.
    """
    try:
        t = yf.Ticker(ticker)
        info = t.info

        price_targets = {
            "low": info.get("targetLowPrice"),
            "mean": info.get("targetMeanPrice"),
            "median": info.get("targetMedianPrice"),
            "high": info.get("targetHighPrice"),
            "current_price": info.get("currentPrice") or info.get("regularMarketPrice"),
            "number_of_analysts": info.get("numberOfAnalystOpinions"),
            "recommendation_key": info.get("recommendationKey"),
            "recommendation_mean": info.get("recommendationMean"),
        }

        # Get recommendation trends
        recommendations = None
        try:
            recommendations = t.recommendations
        except Exception:
            pass

        return {
            "price_targets": price_targets,
            "recommendations": recommendations,
        }
    except Exception as e:
        print(f"Error retrieving analyst data for {ticker}: {e}")
        return None


# ---------------------------------------------------------------------------
# Quarterly EPS
# ---------------------------------------------------------------------------

def get_quarterly_eps(ticker: str) -> pd.DataFrame | None:
    """Pull quarterly EPS data for CAN SLIM analysis.

    Args:
        ticker: US equity ticker symbol.

    Returns:
        DataFrame with quarterly earnings data (EPS, date, surprise).
        Returns None if retrieval fails.
    """
    try:
        t = yf.Ticker(ticker)
        # yfinance provides earnings_dates and quarterly financials
        # Use quarterly income statement to derive EPS
        quarterly_income = t.quarterly_income_stmt
        if quarterly_income is None or quarterly_income.empty:
            print(f"Warning: No quarterly income data for {ticker}")
            return None

        # Extract basic EPS from Diluted EPS or compute from Net Income / Shares
        eps_data = {}
        for col in quarterly_income.columns:
            diluted_eps = None
            if "Diluted EPS" in quarterly_income.index:
                diluted_eps = quarterly_income.loc["Diluted EPS", col]
            elif "Basic EPS" in quarterly_income.index:
                diluted_eps = quarterly_income.loc["Basic EPS", col]
            if diluted_eps is not None:
                eps_data[col] = {"eps": diluted_eps}

        if not eps_data:
            print(f"Warning: Could not extract EPS data for {ticker}")
            return None

        df = pd.DataFrame.from_dict(eps_data, orient="index")
        df.index.name = "date"
        df = df.sort_index()
        return df
    except Exception as e:
        print(f"Error retrieving quarterly EPS for {ticker}: {e}")
        return None


# ---------------------------------------------------------------------------
# SEC EDGAR — 10-K Retrieval
# ---------------------------------------------------------------------------

def _edgar_get(url: str) -> requests.Response | None:
    """Make a rate-limited GET request to SEC EDGAR."""
    time.sleep(EDGAR_RATE_LIMIT_SECONDS)
    try:
        resp = requests.get(url, headers=EDGAR_HEADERS, timeout=30)
        resp.raise_for_status()
        return resp
    except requests.RequestException as e:
        print(f"EDGAR request failed ({url}): {e}")
        return None


def _get_cik(ticker: str) -> str | None:
    """Resolve ticker to CIK (Central Index Key) via EDGAR company tickers JSON."""
    url = "https://www.sec.gov/files/company_tickers.json"
    resp = _edgar_get(url)
    if resp is None:
        return None
    try:
        data = resp.json()
        ticker_upper = ticker.upper()
        for entry in data.values():
            if entry.get("ticker", "").upper() == ticker_upper:
                return str(entry["cik_str"]).zfill(10)
        print(f"Warning: CIK not found for {ticker}")
        return None
    except Exception as e:
        print(f"Error parsing CIK lookup response: {e}")
        return None


def _get_latest_10k_url(cik: str) -> str | None:
    """Find the most recent 10-K filing URL from EDGAR submissions API."""
    url = f"https://data.sec.gov/submissions/CIK{cik}.json"
    resp = _edgar_get(url)
    if resp is None:
        return None
    try:
        data = resp.json()
        recent = data.get("filings", {}).get("recent", {})
        forms = recent.get("form", [])
        accession_numbers = recent.get("accessionNumber", [])
        primary_docs = recent.get("primaryDocument", [])

        for i, form in enumerate(forms):
            if form in ("10-K", "10-K/A"):
                accession = accession_numbers[i].replace("-", "")
                doc = primary_docs[i]
                filing_url = f"https://www.sec.gov/Archives/edgar/data/{cik.lstrip('0')}/{accession}/{doc}"
                return filing_url

        print(f"Warning: No 10-K found for CIK {cik}")
        return None
    except Exception as e:
        print(f"Error parsing EDGAR submissions: {e}")
        return None


def _extract_10k_sections(text: str, sections: list[str] | None = None) -> str:
    """Extract key sections from 10-K HTML/text.

    Looks for common section headers in 10-K filings and extracts content.
    This is a best-effort extraction — 10-K formats vary significantly.
    """
    import re

    if sections is None:
        sections = ["MD&A", "Risk Factors", "Financial Statements"]

    # Remove HTML tags and entities for cleaner text
    clean = re.sub(r"<[^>]+>", " ", text)
    clean = re.sub(r"&#?\w+;", " ", clean)  # handles &amp; &#8217; &#x2019; etc.
    clean = re.sub(r"\s+", " ", clean)

    # Common section header patterns in 10-K filings
    section_patterns = {
        "MD&A": [
            r"(?i)item\s*7[\.\s]*management.s\s*discussion\s*and\s*analysis",
            r"(?i)management.s\s*discussion\s*and\s*analysis",
        ],
        "Risk Factors": [
            r"(?i)item\s*1a[\.\s]*risk\s*factors",
            r"(?i)risk\s*factors",
        ],
        "Financial Statements": [
            r"(?i)item\s*8[\.\s]*financial\s*statements",
            r"(?i)consolidated\s*statements\s*of\s*(?:income|operations)",
        ],
    }

    # Try to extract each requested section
    extracted_parts = []
    for section_name in sections:
        patterns = section_patterns.get(section_name, [])
        for pattern in patterns:
            match = re.search(pattern, clean)
            if match:
                start = match.start()
                # Extract up to ~30K chars from the section start
                chunk = clean[start:start + 30000]
                extracted_parts.append(f"\n\n--- {section_name} ---\n{chunk}")
                break

    if extracted_parts:
        return "\n".join(extracted_parts)

    # Fallback: return truncated full text
    return clean[:80000]


def get_10k_text(ticker: str, sections: list[str] | None = None) -> str | None:
    """Retrieve the most recent 10-K filing text from SEC EDGAR.

    Steps:
    1. Resolve ticker to CIK
    2. Find most recent 10-K filing URL
    3. Fetch and extract key sections

    Args:
        ticker: US equity ticker symbol.
        sections: Sections to extract. Defaults to MD&A, Risk Factors,
                  Financial Statements.

    Returns:
        Extracted 10-K text as a string. Returns None if retrieval fails.
        Text is truncated to 150K characters max.
    """
    cik = _get_cik(ticker)
    if cik is None:
        return None

    filing_url = _get_latest_10k_url(cik)
    if filing_url is None:
        return None

    print(f"Fetching 10-K from: {filing_url}")
    resp = _edgar_get(filing_url)
    if resp is None:
        return None

    raw_text = resp.text
    extracted = _extract_10k_sections(raw_text, sections)

    # Hard cap at 150K characters per CLAUDE.md spec
    if len(extracted) > 150000:
        extracted = extracted[:150000] + "\n\n[TRUNCATED — 10-K text exceeded 150K character limit]"

    return extracted
