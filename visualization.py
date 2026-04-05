"""
visualization.py
All Plotly chart builders for the dashboard.
Charts are interactive: zoom, hover, legend toggle.
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ── Shared colour palette ─────────────────────────────────────────────────────
PALETTE = {
    "bg":        "#0D1117",
    "paper":     "#161B22",
    "grid":      "#21262D",
    "text":      "#E6EDF3",
    "subtext":   "#8B949E",
    "green":     "#00C897",
    "red":       "#FF4B4B",
    "yellow":    "#FFA500",
    "blue":      "#58A6FF",
    "purple":    "#BC8CFF",
    "candle_up": "#00C897",
    "candle_dn": "#FF4B4B",
}

_LAYOUT_BASE = dict(
    paper_bgcolor=PALETTE["paper"],
    plot_bgcolor=PALETTE["bg"],
    font=dict(family="'IBM Plex Mono', monospace", size=12, color=PALETTE["text"]),
    legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor=PALETTE["grid"], borderwidth=1),
    margin=dict(l=60, r=20, t=50, b=40),
    xaxis=dict(
        gridcolor=PALETTE["grid"],
        zerolinecolor=PALETTE["grid"],
        showspikes=True,
        spikecolor=PALETTE["subtext"],
        spikethickness=1,
    ),
    yaxis=dict(
        gridcolor=PALETTE["grid"],
        zerolinecolor=PALETTE["grid"],
        showspikes=True,
        spikecolor=PALETTE["subtext"],
        spikethickness=1,
    ),
    hovermode="x unified",
)


def _apply_base_layout(fig, title: str = "") -> go.Figure:
    fig.update_layout(**_LAYOUT_BASE, title=dict(text=title, font=dict(size=16)))
    return fig


# ── 1. Candlestick + Overlays ─────────────────────────────────────────────────

def plot_price_chart(
    df: pd.DataFrame,
    ticker: str,
    show_sma: bool = True,
    show_ema: bool = True,
    show_bb: bool = True,
) -> go.Figure:
    """Candlestick chart with optional SMA, EMA, Bollinger Band overlays."""
    fig = go.Figure()

    # Candlesticks
    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df["Open"], high=df["High"], low=df["Low"], close=df["Close"],
        name="OHLC",
        increasing_line_color=PALETTE["candle_up"],
        decreasing_line_color=PALETTE["candle_dn"],
        increasing_fillcolor=PALETTE["candle_up"],
        decreasing_fillcolor=PALETTE["candle_dn"],
    ))

    # Bollinger Bands (filled channel)
    if show_bb and "BB_Upper" in df.columns:
        fig.add_trace(go.Scatter(
            x=df.index, y=df["BB_Upper"],
            name="BB Upper", line=dict(color=PALETTE["purple"], width=1, dash="dot"),
            opacity=0.7,
        ))
        fig.add_trace(go.Scatter(
            x=df.index, y=df["BB_Lower"],
            name="BB Lower", line=dict(color=PALETTE["purple"], width=1, dash="dot"),
            fill="tonexty",
            fillcolor="rgba(188,140,255,0.07)",
            opacity=0.7,
        ))
        fig.add_trace(go.Scatter(
            x=df.index, y=df["BB_Mid"],
            name="BB Mid", line=dict(color=PALETTE["purple"], width=1),
            opacity=0.5,
        ))

    # SMA 50 & 200
    if show_sma:
        if "SMA_50" in df.columns:
            fig.add_trace(go.Scatter(
                x=df.index, y=df["SMA_50"],
                name="SMA 50", line=dict(color=PALETTE["yellow"], width=1.5),
            ))
        if "SMA_200" in df.columns:
            fig.add_trace(go.Scatter(
                x=df.index, y=df["SMA_200"],
                name="SMA 200", line=dict(color=PALETTE["red"], width=1.5),
            ))

    # EMA 20
    if show_ema and "EMA_20" in df.columns:
        fig.add_trace(go.Scatter(
            x=df.index, y=df["EMA_20"],
            name="EMA 20", line=dict(color=PALETTE["blue"], width=1.5),
        ))

    _apply_base_layout(fig, f"{ticker} — Price Chart")
    fig.update_xaxes(rangeslider_visible=False)
    fig.update_layout(height=520)
    return fig


# ── 2. RSI ────────────────────────────────────────────────────────────────────

def plot_rsi(df: pd.DataFrame, ticker: str) -> go.Figure:
    fig = go.Figure()
    if "RSI" not in df.columns:
        return fig

    # Colour the RSI line by zone
    rsi = df["RSI"]
    fig.add_trace(go.Scatter(
        x=df.index, y=rsi,
        name="RSI",
        line=dict(color=PALETTE["blue"], width=2),
    ))

    # Overbought / Oversold bands
    fig.add_hrect(y0=70, y1=100, fillcolor=PALETTE["red"],    opacity=0.07, line_width=0)
    fig.add_hrect(y0=0,  y1=30,  fillcolor=PALETTE["green"],  opacity=0.07, line_width=0)
    fig.add_hline(y=70, line_dash="dash", line_color=PALETTE["red"],   line_width=1,
                  annotation_text="Overbought 70", annotation_position="top left",
                  annotation_font_color=PALETTE["red"])
    fig.add_hline(y=30, line_dash="dash", line_color=PALETTE["green"], line_width=1,
                  annotation_text="Oversold 30", annotation_position="bottom left",
                  annotation_font_color=PALETTE["green"])
    fig.add_hline(y=50, line_dash="dot",  line_color=PALETTE["subtext"], line_width=1)

    _apply_base_layout(fig, f"{ticker} — RSI (14)")
    fig.update_yaxes(range=[0, 100])
    fig.update_layout(height=280)
    return fig


# ── 3. MACD ───────────────────────────────────────────────────────────────────

def plot_macd(df: pd.DataFrame, ticker: str) -> go.Figure:
    if "MACD" not in df.columns:
        return go.Figure()

    colors = [PALETTE["green"] if v >= 0 else PALETTE["red"] for v in df["MACD_Hist"]]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df.index, y=df["MACD_Hist"],
        name="Histogram", marker_color=colors, opacity=0.7,
    ))
    fig.add_trace(go.Scatter(
        x=df.index, y=df["MACD"],
        name="MACD", line=dict(color=PALETTE["blue"], width=2),
    ))
    fig.add_trace(go.Scatter(
        x=df.index, y=df["MACD_Signal"],
        name="Signal", line=dict(color=PALETTE["yellow"], width=1.5, dash="dash"),
    ))
    fig.add_hline(y=0, line_color=PALETTE["subtext"], line_width=1)

    _apply_base_layout(fig, f"{ticker} — MACD (12/26/9)")
    fig.update_layout(height=280)
    return fig


# ── 4. Volume ─────────────────────────────────────────────────────────────────

def plot_volume(df: pd.DataFrame, ticker: str) -> go.Figure:
    if "Volume" not in df.columns:
        return go.Figure()

    vol_colors = []
    for i, (idx, row) in enumerate(df.iterrows()):
        if i == 0:
            vol_colors.append(PALETTE["blue"])
        else:
            prev_close = df["Close"].iloc[i - 1]
            vol_colors.append(PALETTE["green"] if row["Close"] >= prev_close else PALETTE["red"])

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df.index, y=df["Volume"],
        name="Volume", marker_color=vol_colors, opacity=0.8,
    ))
    # 20-day MA of volume
    fig.add_trace(go.Scatter(
        x=df.index,
        y=df["Volume"].rolling(20).mean(),
        name="Vol MA 20", line=dict(color=PALETTE["yellow"], width=1.5),
    ))

    _apply_base_layout(fig, f"{ticker} — Volume")
    fig.update_layout(height=230)
    return fig


# ── 5. Volatility ─────────────────────────────────────────────────────────────

def plot_volatility(df: pd.DataFrame, ticker: str) -> go.Figure:
    if "Volatility" not in df.columns:
        return go.Figure()

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df.index, y=df["Volatility"],
        name="Annualised Vol (%)",
        line=dict(color=PALETTE["purple"], width=2),
        fill="tozeroy",
        fillcolor="rgba(188,140,255,0.12)",
    ))

    _apply_base_layout(fig, f"{ticker} — Rolling 20-Day Volatility (%)")
    fig.update_layout(height=240)
    return fig


# ── 6. Multi-Stock Comparison ─────────────────────────────────────────────────

def plot_comparison(stocks: dict) -> go.Figure:
    """
    Normalised price comparison for multiple tickers.
    `stocks` = {ticker: DataFrame (must contain 'Normalized' column)}
    """
    colors = [
        PALETTE["blue"], PALETTE["green"], PALETTE["yellow"],
        PALETTE["purple"], PALETTE["red"],
    ]
    fig = go.Figure()
    for i, (ticker, df) in enumerate(stocks.items()):
        if "Normalized" not in df.columns:
            df["Normalized"] = df["Close"] / df["Close"].iloc[0]
        fig.add_trace(go.Scatter(
            x=df.index, y=df["Normalized"],
            name=ticker,
            line=dict(color=colors[i % len(colors)], width=2),
        ))

    fig.add_hline(y=1, line_dash="dot", line_color=PALETTE["subtext"], line_width=1)
    _apply_base_layout(fig, "Normalised Price Comparison")
    fig.update_yaxes(tickformat=".2%")
    fig.update_layout(height=420)
    return fig


# ── 7. Portfolio Allocation Pie ───────────────────────────────────────────────

def plot_portfolio_pie(df_port: pd.DataFrame) -> go.Figure:
    colors = [
        PALETTE["blue"], PALETTE["green"], PALETTE["yellow"],
        PALETTE["purple"], PALETTE["red"],
        "#FF9F43", "#48DBFB", "#FF6B81",
    ]
    fig = go.Figure(go.Pie(
        labels=df_port["Ticker"],
        values=df_port["Current Value"],
        hole=0.45,
        marker=dict(colors=colors[:len(df_port)], line=dict(color=PALETTE["bg"], width=2)),
        textinfo="label+percent",
        hovertemplate="%{label}<br>Value: %{value:,.2f}<br>Share: %{percent}<extra></extra>",
    ))
    _apply_base_layout(fig, "Portfolio Allocation")
    fig.update_layout(height=380)
    return fig


# ── 8. Returns Bar (portfolio) ────────────────────────────────────────────────

def plot_portfolio_returns(df_port: pd.DataFrame) -> go.Figure:
    colors = [PALETTE["green"] if v >= 0 else PALETTE["red"] for v in df_port["Return (%)"]]
    fig = go.Figure(go.Bar(
        x=df_port["Ticker"],
        y=df_port["Return (%)"],
        marker_color=colors,
        text=df_port["Return (%)"].apply(lambda x: f"{x:+.2f}%"),
        textposition="outside",
    ))
    fig.add_hline(y=0, line_color=PALETTE["subtext"], line_width=1)
    _apply_base_layout(fig, "Portfolio Return per Stock (%)")
    fig.update_layout(height=320, yaxis_ticksuffix="%")
    return fig
