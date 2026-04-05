"""
search.py
Smart company name → ticker resolver.

Uses Yahoo Finance's internal autocomplete/search endpoint (no API key needed).
Supports:
  - Partial company name   : "reliance" → RELIANCE.NS
  - Full name              : "Infosys Limited" → INFY.NS
  - Partial ticker         : "AAPL" → Apple Inc.
  - Indian companies       : "HDFC", "Tata Motors", "Zomato"
  - US / Global companies  : "Tesla", "Samsung", "HSBC"

Results include company name, ticker, exchange, and asset type so the
Streamlit UI can show a dropdown like Moneycontrol does.
"""

import requests
import streamlit as st
from typing import List, Dict

# Yahoo Finance autocomplete endpoint (no key, no auth)
_YF_SEARCH_URL = "https://query2.finance.yahoo.com/v1/finance/search"

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
}

# Exchange display labels
_EXCHANGE_LABELS = {
    "NSE":    "🇮🇳 NSE",
    "BSE":    "🇮🇳 BSE",
    "NMS":    "🇺🇸 NASDAQ",
    "NGM":    "🇺🇸 NASDAQ",
    "NYQ":    "🇺🇸 NYSE",
    "LSE":    "🇬🇧 LSE",
    "FRA":    "🇩🇪 Frankfurt",
    "TYO":    "🇯🇵 Tokyo",
    "HKG":    "🇭🇰 HK",
    "TSX":    "🇨🇦 TSX",
    "ASX":    "🇦🇺 ASX",
    "SHH":    "🇨🇳 Shanghai",
    "CCC":    "🪙 Crypto",
}

_QUOTE_TYPE_LABELS = {
    "EQUITY":      "Stock",
    "ETF":         "ETF",
    "MUTUALFUND":  "Mutual Fund",
    "CRYPTOCURRENCY": "Crypto",
    "INDEX":       "Index",
    "FUTURE":      "Future",
    "OPTION":      "Option",
    "CURRENCY":    "Currency",
}


@st.cache_data(ttl=120, show_spinner=False)
def search_companies(query: str, max_results: int = 10) -> List[Dict]:
    """
    Search Yahoo Finance for companies matching `query`.

    Returns a list of dicts:
      {
        "ticker":    str,   # e.g. "RELIANCE.NS"
        "name":      str,   # e.g. "Reliance Industries Limited"
        "exchange":  str,   # e.g. "NSE"
        "type":      str,   # e.g. "Stock"
        "label":     str,   # display string for dropdown
      }
    """
    query = query.strip()
    if not query or len(query) < 1:
        return []

    try:
        params = {
            "q":            query,
            "quotesCount":  max_results,
            "newsCount":    0,
            "enableFuzzyQuery": True,
            "enableCb":     True,
            "lang":         "en-US",
            "region":       "IN",          # bias toward Indian results first
        }
        resp = requests.get(
            _YF_SEARCH_URL,
            params=params,
            headers=_HEADERS,
            timeout=6,
        )
        resp.raise_for_status()
        data = resp.json()

        quotes = data.get("quotes", [])
        results = []

        for q in quotes:
            ticker    = q.get("symbol", "")
            name      = q.get("longname") or q.get("shortname") or ticker
            exchange  = q.get("exchange", "")
            q_type    = q.get("quoteType", "EQUITY")

            # Skip indices and options for cleaner results
            if q_type in ("OPTION", "FUTURE", "CURRENCY"):
                continue

            exch_label = _EXCHANGE_LABELS.get(exchange, exchange)
            type_label = _QUOTE_TYPE_LABELS.get(q_type, q_type)

            label = f"{name}  ·  {ticker}  ·  {exch_label}  ·  {type_label}"

            results.append({
                "ticker":   ticker,
                "name":     name,
                "exchange": exchange,
                "type":     type_label,
                "label":    label,
            })

        return results[:max_results]

    except requests.exceptions.Timeout:
        return []
    except Exception:
        return []


def resolve_ticker(query: str) -> str:
    """
    Given a free-text company name or partial ticker, return the best-match
    ticker symbol. Returns the original query uppercased if no match found.
    """
    results = search_companies(query, max_results=3)
    if results:
        return results[0]["ticker"]
    return query.strip().upper()
