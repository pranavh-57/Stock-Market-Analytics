"""
alerts.py
Evaluates price thresholds and indicator-based alerts.
Returns a list of alert dicts that the Streamlit app renders.
"""

import pandas as pd


def check_alerts(
    df: pd.DataFrame,
    ticker: str,
    price_above: float = None,
    price_below: float = None,
    rsi_ob: float = 70.0,
    rsi_os: float = 30.0,
    check_cross: bool = True,
) -> list:
    """
    Returns a list of alert dicts:
      {"level": "success"|"warning"|"error", "message": str}
    """
    alerts = []
    if df.empty:
        return alerts

    last = df.iloc[-1]
    close = float(last["Close"])

    # ── Price alerts ──────────────────────────────────────────────────────────
    if price_above is not None and close > price_above:
        alerts.append({
            "level":   "success",
            "message": f"📈 {ticker}: Price ₹{close:,.2f} crossed ABOVE your target ₹{price_above:,.2f}",
        })
    if price_below is not None and close < price_below:
        alerts.append({
            "level":   "error",
            "message": f"📉 {ticker}: Price ₹{close:,.2f} dropped BELOW your alert ₹{price_below:,.2f}",
        })

    # ── RSI alerts ────────────────────────────────────────────────────────────
    if "RSI" in df.columns:
        rsi = float(last["RSI"])
        if rsi > rsi_ob:
            alerts.append({
                "level":   "warning",
                "message": f"⚠️ {ticker}: RSI = {rsi:.1f} — Overbought (>{rsi_ob:.0f}). Consider taking profits.",
            })
        elif rsi < rsi_os:
            alerts.append({
                "level":   "success",
                "message": f"🟢 {ticker}: RSI = {rsi:.1f} — Oversold (<{rsi_os:.0f}). Potential buying opportunity.",
            })

    # ── Golden / Death Cross alerts ───────────────────────────────────────────
    if check_cross and "SMA_50" in df.columns and "SMA_200" in df.columns and len(df) >= 6:
        sma50  = df["SMA_50"]
        sma200 = df["SMA_200"]

        # Check last 5 bars for a recent crossover
        recent = df.iloc[-5:]
        current_above = float(sma50.iloc[-1]) > float(sma200.iloc[-1])
        was_below_in_window = (recent["SMA_50"] < recent["SMA_200"]).any()
        was_above_in_window = (recent["SMA_50"] > recent["SMA_200"]).any()

        if current_above and was_below_in_window:
            alerts.append({
                "level":   "success",
                "message": f"🌟 {ticker}: GOLDEN CROSS detected — SMA50 crossed above SMA200. Bullish signal!",
            })
        elif not current_above and was_above_in_window:
            alerts.append({
                "level":   "error",
                "message": f"☠️ {ticker}: DEATH CROSS detected — SMA50 crossed below SMA200. Bearish signal!",
            })

    return alerts
