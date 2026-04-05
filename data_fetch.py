"""
data_fetch.py
Handles all data fetching, caching, and preprocessing using yfinance.
Supports NSE stocks (RELIANCE.NS, INFY.NS) and global stocks (AAPL).
"""

import yfinance as yf
import pandas as pd
import numpy as np
import streamlit as st
from datetime import datetime, timedelta


# ── Cache layer ──────────────────────────────────────────────────────────────

@st.cache_data(ttl=300, show_spinner=False)
def fetch_stock_data(
    ticker: str,
    start: str,
    end: str,
    interval: str = "1d",
) -> pd.DataFrame:
    """
    Fetch OHLCV data for a single ticker via yfinance.

    Returns a cleaned DataFrame with a DatetimeIndex, or an empty DataFrame
    if the download fails / returns no rows.
    """
    try:
        df = yf.download(
            ticker,
            start=start,
            end=end,
            interval=interval,
            auto_adjust=True,
            progress=False,
        )

        if df.empty:
            return pd.DataFrame()

        # Flatten multi-level columns that yfinance sometimes returns
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        df = _clean(df)
        return df

    except Exception as exc:
        st.error(f"[data_fetch] Error fetching {ticker}: {exc}")
        return pd.DataFrame()


@st.cache_data(ttl=300, show_spinner=False)
def fetch_multiple_stocks(
    tickers: list,
    start: str,
    end: str,
    interval: str = "1d",
) -> dict:
    """
    Fetch data for multiple tickers.

    Returns a dict  {ticker: DataFrame}.
    """
    result = {}
    for t in tickers:
        data = fetch_stock_data(t, start, end, interval)
        if not data.empty:
            result[t] = data
    return result


@st.cache_data(ttl=3600, show_spinner=False)
def get_company_info(ticker: str) -> dict:
    """
    Return basic company metadata (name, sector, market cap, etc.).
    Gracefully returns {} on failure.
    """
    try:
        info = yf.Ticker(ticker).info
        keys = [
            "longName", "shortName", "sector", "industry",
            "marketCap", "currency", "exchange", "website",
            "longBusinessSummary",
        ]
        return {k: info.get(k, "N/A") for k in keys}
    except Exception:
        return {}


# ── Internal helpers ─────────────────────────────────────────────────────────

def _clean(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalise column names, ensure DatetimeIndex, drop NaN rows.
    """
    # Standardise column names
    df.columns = [c.strip().title() for c in df.columns]

    # Ensure DatetimeIndex
    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index)

    # Drop rows where all OHLCV values are NaN
    df.dropna(subset=["Close"], inplace=True)

    # Fill remaining NaNs forward then backward
    df.ffill(inplace=True)
    df.bfill(inplace=True)

    # Ensure numeric types
    numeric_cols = ["Open", "High", "Low", "Close", "Volume"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df.sort_index(inplace=True)
    return df


def compute_returns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Append daily percentage returns and normalised price columns.
    """
    df = df.copy()
    df["Daily_Return"] = df["Close"].pct_change() * 100
    df["Cumulative_Return"] = (1 + df["Close"].pct_change()).cumprod() - 1
    first_close = df["Close"].iloc[0]
    df["Normalized"] = df["Close"] / first_close
    return df


def get_date_defaults() -> tuple:
    """Return sensible (start, end) defaults: 1 year back → today."""
    end = datetime.today()
    start = end - timedelta(days=365)
    return start.date(), end.date()
