"""
ai_analyst.py
Groq-powered AI analysis engine.

Pulls together:
  - Latest price movement & volume data
  - All technical indicator values (RSI, MACD, BB, Volatility)
  - Recent news headlines from yfinance
  - Historical context (similar past setups)

...and sends them to llama-3.3-70b-versatile on Groq to generate
a plain-English narrative that explains WHY the stock moved and
WHAT to watch for next — exactly like a human analyst would.
"""

import yfinance as yf
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False


# ── News fetcher ──────────────────────────────────────────────────────────────

@st.cache_data(ttl=600, show_spinner=False)
def fetch_recent_news(ticker: str, max_items: int = 6) -> list:
    """
    Fetch recent news headlines for a ticker via yfinance.
    Returns a list of dicts with 'title' and 'publisher'.
    """
    try:
        t = yf.Ticker(ticker)
        raw = t.news or []
        news = []
        for item in raw[:max_items]:
            content = item.get("content", {})
            title = (
                content.get("title")
                or item.get("title")
                or ""
            )
            provider = (
                content.get("provider", {}).get("displayName")
                or item.get("publisher")
                or "Unknown"
            )
            if title:
                news.append({"title": title, "publisher": provider})
        return news
    except Exception:
        return []


# ── Historical context builder ────────────────────────────────────────────────

def find_similar_past_setups(df: pd.DataFrame, lookback: int = 5) -> str:
    """
    Scan the last 2 years of data for setups where RSI and price change
    were in a similar range to today. Returns a short plain-text summary
    of what happened in the 10 days AFTER those setups.
    """
    if len(df) < 30 or "RSI" not in df.columns or "Daily_Return" not in df.columns:
        return "Insufficient historical data for pattern matching."

    last       = df.iloc[-1]
    cur_rsi    = float(last.get("RSI", 50))
    cur_ret    = float(last.get("Daily_Return", 0))

    # Define "similar" as RSI within ±8 and return within ±1.5%
    rsi_lo, rsi_hi = cur_rsi - 8,  cur_rsi + 8
    ret_lo, ret_hi = cur_ret - 1.5, cur_ret + 1.5

    # Only look at history up to 5 days before today (not recent)
    history = df.iloc[:-5]
    mask = (
        history["RSI"].between(rsi_lo, rsi_hi) &
        history["Daily_Return"].between(ret_lo, ret_hi)
    )
    similar = history[mask]

    if similar.empty:
        return "No closely matching historical setups found."

    # For each matched day, look at the 10-day forward return
    outcomes = []
    all_dates = df.index.tolist()

    for match_date in similar.index[-lookback:]:
        try:
            idx       = all_dates.index(match_date)
            fwd_end   = min(idx + 11, len(df) - 1)
            fwd_close = df["Close"].iloc[fwd_end]
            cur_close = df["Close"].iloc[idx]
            fwd_ret   = (fwd_close / cur_close - 1) * 100
            outcomes.append({
                "date":    match_date.strftime("%b %Y"),
                "fwd_ret": round(fwd_ret, 1),
            })
        except (ValueError, IndexError):
            continue

    if not outcomes:
        return "No closely matching historical setups found."

    pos = sum(1 for o in outcomes if o["fwd_ret"] > 0)
    neg = len(outcomes) - pos
    avg = np.mean([o["fwd_ret"] for o in outcomes])

    lines = [f"  • {o['date']}: {'+' if o['fwd_ret']>=0 else ''}{o['fwd_ret']}% over next 10 days"
             for o in outcomes]
    summary = (
        f"Found {len(outcomes)} similar past setup(s) (similar RSI + daily move):\n"
        + "\n".join(lines)
        + f"\nAverage 10-day outcome: {'+' if avg>=0 else ''}{avg:.1f}%  "
        f"({pos} positive, {neg} negative)"
    )
    return summary


# ── Prompt builder ────────────────────────────────────────────────────────────

def build_prompt(
    ticker:       str,
    company_name: str,
    df:           pd.DataFrame,
    insights:     dict,
    news:         list,
    historical_context: str,
) -> str:
    """
    Assembles the full data payload into a structured prompt for Groq.
    """
    last      = df.iloc[-1]
    prev      = df.iloc[-2] if len(df) > 1 else last

    close     = float(last["Close"])
    prev_close= float(prev["Close"])
    change    = close - prev_close
    change_pct= (change / prev_close) * 100 if prev_close else 0

    volume    = int(last.get("Volume", 0))
    avg_vol   = int(df["Volume"].rolling(20).mean().iloc[-1]) if "Volume" in df.columns else 0
    vol_ratio = volume / avg_vol if avg_vol > 0 else 1.0

    rsi       = float(last.get("RSI", 50))
    macd      = float(last.get("MACD", 0))
    macd_hist = float(last.get("MACD_Hist", 0))
    volatility= float(last.get("Volatility", 0))
    bb_upper  = float(last.get("BB_Upper", close))
    bb_lower  = float(last.get("BB_Lower", close))
    bb_mid    = float(last.get("BB_Mid", close))
    sma50     = float(last.get("SMA_50", close))
    sma200    = float(last.get("SMA_200", close))

    # Bollinger Band position
    bb_range = bb_upper - bb_lower
    bb_pos   = ((close - bb_lower) / bb_range * 100) if bb_range > 0 else 50

    # News headlines
    if news:
        news_block = "\n".join(
            f"  • [{n['publisher']}] {n['title']}" for n in news
        )
    else:
        news_block = "  No recent news headlines available."

    # 52-week high/low
    year_high = float(df["High"].tail(252).max()) if "High" in df.columns else close
    year_low  = float(df["Low"].tail(252).min())  if "Low"  in df.columns else close
    pct_from_high = ((close - year_high) / year_high) * 100
    pct_from_low  = ((close - year_low)  / year_low)  * 100

    trend_label = insights.get("trend",      ("Unknown",""))[0]
    cross_label = insights.get("cross",      ("Neutral",""))[0]
    rsi_label   = insights.get("rsi_signal", ("Neutral",""))[0]
    macd_label  = insights.get("macd_signal",("Neutral",""))[0]
    vol_label   = insights.get("volatility", ("Unknown",""))[0]

    today = datetime.today().strftime("%d %B %Y")

    prompt = f"""You are a senior equity research analyst writing a morning note for a retail investor in India. 
Your tone is clear, direct, and educational — like a knowledgeable friend, not a textbook.
Avoid generic disclaimers. Be specific to this stock's data.

=== STOCK DATA AS OF {today} ===

Company    : {company_name} ({ticker})
Price      : ₹{close:,.2f}  ({"+" if change >= 0 else ""}{change:,.2f} / {"+" if change_pct >= 0 else ""}{change_pct:.2f}% today)
52W High   : ₹{year_high:,.2f}  ({pct_from_high:+.1f}% from here)
52W Low    : ₹{year_low:,.2f}   ({pct_from_low:+.1f}% from here)

Volume     : {volume:,}  ({vol_ratio:.1f}x the 20-day average — {"SPIKE" if vol_ratio > 1.5 else "normal"})

--- Technical Indicators ---
RSI (14)          : {rsi:.1f}  → {rsi_label}
MACD              : {macd:.4f}  (histogram: {macd_hist:+.4f})  → {macd_label}
Bollinger Band    : Price at {bb_pos:.0f}% of band  (Lower: {bb_lower:.2f} | Mid: {bb_mid:.2f} | Upper: {bb_upper:.2f})
SMA 50 / SMA 200  : {sma50:.2f} / {sma200:.2f}  → {trend_label} trend  ({cross_label})
Ann. Volatility   : {volatility:.1f}%  → {vol_label}

--- Recent News Headlines ---
{news_block}

--- Historical Context (similar past setups) ---
{historical_context}

=== YOUR TASK ===

Write a focused analysis in EXACTLY this structure:

**What Happened Today**
2–3 sentences. Explain the price move and volume in plain English. 
Was the volume spike meaningful? Is the move technical or news-driven?

**What the Indicators Say**
3–4 sentences. Interpret RSI, MACD, Bollinger Bands, and the trend together as a unified picture.
Don't just repeat the numbers — explain what the combination means for this stock right now.

**Historical Patterns**
2–3 sentences. Reference the historical context data above.
What happened the last time this stock was in a similar setup?

**What to Watch Next**
2–3 bullet points. Specific price levels, indicator thresholds, or news catalysts to monitor.
Make these actionable — e.g., "Watch if price holds above ₹2,450 (BB Mid)" not "monitor the trend."

**Risk Note**
1 sentence. Honest assessment of the biggest risk in this stock right now.

Keep the entire response under 350 words. Be specific to {company_name}, not generic."""

    return prompt


# ── Main AI call ──────────────────────────────────────────────────────────────

def generate_ai_analysis(
    ticker:       str,
    company_name: str,
    df:           pd.DataFrame,
    insights:     dict,
    groq_api_key: str,
) -> str:
    """
    Orchestrates news fetch + historical context + Groq API call.
    Returns the AI-generated analysis as a markdown string.
    """
    if not GROQ_AVAILABLE:
        return "❌ `groq` package not installed. Run: `pip install groq`"

    if not groq_api_key or len(groq_api_key.strip()) < 10:
        return "⚠️ Please enter your Groq API key in the sidebar to enable AI Analysis."

    if df.empty or len(df) < 5:
        return "❌ Not enough price data to generate analysis."

    # Step 1 — fetch news
    news = fetch_recent_news(ticker)

    # Step 2 — build historical context
    hist_context = find_similar_past_setups(df)

    # Step 3 — build prompt
    prompt = build_prompt(ticker, company_name, df, insights, news, hist_context)

    # Step 4 — call Groq
    try:
        client = Groq(api_key=groq_api_key.strip())
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a senior equity research analyst. "
                        "You write clear, specific, data-driven stock analysis "
                        "for retail investors in India. "
                        "Always respond in markdown with the exact section headers provided. "
                        "Never use generic filler. Every sentence must reference the actual data given."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            temperature=0.4,        # lower = more factual, less hallucination
            max_tokens=700,
        )
        return response.choices[0].message.content

    except Exception as e:
        err = str(e)
        if "401" in err or "invalid_api_key" in err.lower():
            return "❌ Invalid Groq API key. Get yours free at https://console.groq.com"
        elif "429" in err or "rate_limit" in err.lower():
            return "⚠️ Groq rate limit hit. Wait a moment and try again."
        else:
            return f"❌ Groq API error: {err}"
