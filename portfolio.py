"""
portfolio.py
Simple portfolio tracker: current value, P&L, percentage return.
"""

import pandas as pd
import numpy as np


def compute_portfolio(holdings: list, price_map: dict) -> pd.DataFrame:
    """
    holdings  : [{"ticker": str, "qty": float, "buy_price": float}, ...]
    price_map : {ticker: current_price (float)}

    Returns a DataFrame with columns:
      Ticker | Qty | Buy Price | Invest | Current Price | Current Value | P&L | Return (%)
    """
    rows = []
    for h in holdings:
        ticker      = h["ticker"].upper().strip()
        qty         = h["qty"]
        buy_price   = h["buy_price"]
        cur_price   = price_map.get(ticker, None)

        invest      = qty * buy_price
        cur_value   = qty * cur_price if cur_price else None
        pnl         = (cur_value - invest) if cur_value is not None else None
        ret_pct     = (pnl / invest * 100) if (pnl is not None and invest != 0) else None

        rows.append({
            "Ticker":        ticker,
            "Qty":           qty,
            "Buy Price":     buy_price,
            "Investment":    round(invest, 2),
            "Current Price": round(cur_price, 2) if cur_price else "N/A",
            "Current Value": round(cur_value, 2) if cur_value else "N/A",
            "P&L":           round(pnl, 2) if pnl is not None else "N/A",
            "Return (%)":    round(ret_pct, 2) if ret_pct is not None else "N/A",
        })

    return pd.DataFrame(rows)


def portfolio_summary(df: pd.DataFrame) -> dict:
    """
    Aggregate portfolio stats from the DataFrame returned by compute_portfolio.
    Only rows where values are numeric are included.
    """
    numeric = df[df["Current Value"].apply(lambda x: isinstance(x, (int, float)))]

    total_invest = numeric["Investment"].sum()
    total_value  = numeric["Current Value"].sum()
    total_pnl    = total_value - total_invest
    total_ret    = (total_pnl / total_invest * 100) if total_invest else 0

    return {
        "total_investment": round(total_invest, 2),
        "total_value":      round(total_value, 2),
        "total_pnl":        round(total_pnl, 2),
        "total_return_pct": round(total_ret, 2),
        "num_positions":    len(df),
    }
