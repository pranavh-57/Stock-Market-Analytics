"""
indicators.py
Calculates all technical indicators:
  Moving Averages (SMA, EMA), RSI, MACD, Bollinger Bands, Volatility.
Also contains the lightweight 'analysis engine' that converts indicators
into human-readable insights and colour-coded signals.
"""

import pandas as pd
import numpy as np


# ── Moving Averages ───────────────────────────────────────────────────────────

def add_moving_averages(df: pd.DataFrame) -> pd.DataFrame:
    """SMA 50, SMA 200, EMA 20."""
    df = df.copy()
    df["SMA_50"]  = df["Close"].rolling(window=50, min_periods=1).mean()
    df["SMA_200"] = df["Close"].rolling(window=200, min_periods=1).mean()
    df["EMA_20"]  = df["Close"].ewm(span=20, adjust=False).mean()
    return df


# ── RSI ──────────────────────────────────────────────────────────────────────

def add_rsi(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    """14-period Wilder RSI."""
    df = df.copy()
    delta = df["Close"].diff()
    gain  = delta.clip(lower=0)
    loss  = (-delta).clip(lower=0)

    avg_gain = gain.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()

    rs = avg_gain / avg_loss.replace(0, np.nan)
    df["RSI"] = 100 - (100 / (1 + rs))
    return df


# ── MACD ─────────────────────────────────────────────────────────────────────

def add_macd(
    df: pd.DataFrame,
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
) -> pd.DataFrame:
    """Standard MACD: line, signal line, and histogram."""
    df = df.copy()
    ema_fast   = df["Close"].ewm(span=fast,   adjust=False).mean()
    ema_slow   = df["Close"].ewm(span=slow,   adjust=False).mean()
    df["MACD"]        = ema_fast - ema_slow
    df["MACD_Signal"] = df["MACD"].ewm(span=signal, adjust=False).mean()
    df["MACD_Hist"]   = df["MACD"] - df["MACD_Signal"]
    return df


# ── Bollinger Bands ───────────────────────────────────────────────────────────

def add_bollinger_bands(df: pd.DataFrame, window: int = 20, num_std: float = 2.0) -> pd.DataFrame:
    """20-day SMA ± 2 standard deviations."""
    df = df.copy()
    sma = df["Close"].rolling(window=window, min_periods=1).mean()
    std = df["Close"].rolling(window=window, min_periods=1).std()
    df["BB_Mid"]   = sma
    df["BB_Upper"] = sma + num_std * std
    df["BB_Lower"] = sma - num_std * std
    df["BB_Width"] = (df["BB_Upper"] - df["BB_Lower"]) / df["BB_Mid"]
    return df


# ── Volatility ────────────────────────────────────────────────────────────────

def add_volatility(df: pd.DataFrame, window: int = 20) -> pd.DataFrame:
    """Annualised rolling volatility (standard deviation of log returns × √252)."""
    df = df.copy()
    log_ret = np.log(df["Close"] / df["Close"].shift(1))
    df["Volatility"] = log_ret.rolling(window=window, min_periods=1).std() * np.sqrt(252) * 100
    df["Daily_Return"] = df["Close"].pct_change() * 100
    return df


# ── Master function ───────────────────────────────────────────────────────────

def compute_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Apply all indicators in sequence."""
    df = add_moving_averages(df)
    df = add_rsi(df)
    df = add_macd(df)
    df = add_bollinger_bands(df)
    df = add_volatility(df)
    return df


# ── Analysis Engine ───────────────────────────────────────────────────────────

def generate_insights(df: pd.DataFrame, ticker: str = "") -> dict:
    """
    Converts the latest indicator values into a structured insight dict:
      {
        'trend':        ('Bullish' | 'Bearish' | 'Sideways', color),
        'cross':        ('Golden Cross' | 'Death Cross' | 'Neutral', color),
        'rsi_signal':   ('Overbought' | 'Oversold' | 'Neutral', color),
        'macd_signal':  ('Bullish' | 'Bearish', color),
        'volatility':   ('High' | 'Moderate' | 'Low', color),
        'summary':      str,
        'metrics':      dict,
      }
    """
    if df.empty or len(df) < 5:
        return {}

    last = df.iloc[-1]

    # ── Trend via SMA cross ───────────────────────────────────────────────────
    if "SMA_50" in df.columns and "SMA_200" in df.columns:
        if last["SMA_50"] > last["SMA_200"] * 1.002:
            trend, trend_color = "Bullish",  "#00C897"
        elif last["SMA_50"] < last["SMA_200"] * 0.998:
            trend, trend_color = "Bearish",  "#FF4B4B"
        else:
            trend, trend_color = "Sideways", "#FFA500"
    else:
        trend, trend_color = "Unknown", "#888888"

    # ── Golden / Death Cross (recent crossover within 5 bars) ────────────────
    cross_label, cross_color = "Neutral", "#888888"
    if "SMA_50" in df.columns and "SMA_200" in df.columns and len(df) >= 6:
        prev = df.iloc[-6:-1]
        current_above = last["SMA_50"] > last["SMA_200"]
        prev_above_any = (prev["SMA_50"] > prev["SMA_200"]).any()
        prev_below_any = (prev["SMA_50"] < prev["SMA_200"]).any()
        if current_above and prev_below_any:
            cross_label, cross_color = "Golden Cross 🌟", "#00C897"
        elif not current_above and prev_above_any:
            cross_label, cross_color = "Death Cross ☠️", "#FF4B4B"

    # ── RSI Signal ────────────────────────────────────────────────────────────
    rsi_val = last.get("RSI", 50)
    if rsi_val > 70:
        rsi_label, rsi_color = f"Overbought ({rsi_val:.1f})", "#FF4B4B"
    elif rsi_val < 30:
        rsi_label, rsi_color = f"Oversold ({rsi_val:.1f})",   "#00C897"
    else:
        rsi_label, rsi_color = f"Neutral ({rsi_val:.1f})",    "#FFA500"

    # ── MACD Signal ───────────────────────────────────────────────────────────
    macd_hist = last.get("MACD_Hist", 0)
    if macd_hist > 0:
        macd_label, macd_color = "Bullish Momentum", "#00C897"
    else:
        macd_label, macd_color = "Bearish Momentum", "#FF4B4B"

    # ── Volatility Level ──────────────────────────────────────────────────────
    vol = last.get("Volatility", 0)
    if vol > 40:
        vol_label, vol_color = f"High ({vol:.1f}%)",     "#FF4B4B"
    elif vol > 20:
        vol_label, vol_color = f"Moderate ({vol:.1f}%)", "#FFA500"
    else:
        vol_label, vol_color = f"Low ({vol:.1f}%)",      "#00C897"

    # ── Plain-language summary ────────────────────────────────────────────────
    name = ticker or "This stock"
    summary = (
        f"**{name}** is currently showing a **{trend}** trend. "
        f"RSI is {rsi_label.lower()}, indicating "
        f"{'selling pressure' if rsi_val > 70 else 'buying opportunity' if rsi_val < 30 else 'balanced momentum'}. "
        f"MACD signals {macd_label.lower()}. Annualised volatility is {vol_label.lower()}, "
        f"suggesting {'elevated' if vol > 40 else 'moderate' if vol > 20 else 'low'} risk."
    )

    # ── Key metrics ───────────────────────────────────────────────────────────
    metrics = {
        "Latest Close":      round(float(last["Close"]), 2),
        "Daily Return (%)":  round(float(last.get("Daily_Return", 0)), 2),
        "RSI":               round(float(rsi_val), 1),
        "MACD":              round(float(last.get("MACD", 0)), 4),
        "Volatility (%)":    round(float(vol), 2),
        "BB Width":          round(float(last.get("BB_Width", 0)), 4),
    }

    return {
        "trend":       (trend, trend_color),
        "cross":       (cross_label, cross_color),
        "rsi_signal":  (rsi_label, rsi_color),
        "macd_signal": (macd_label, macd_color),
        "volatility":  (vol_label, vol_color),
        "summary":     summary,
        "metrics":     metrics,
    }
