"""
app.py — Stock Market Analysis Dashboard
Run with:  streamlit run app.py
"""

# ── stdlib & third-party ──────────────────────────────────────────────────────
import os
import datetime
import pandas as pd
import streamlit as st
from dotenv import load_dotenv

# Load .env file if present (silently ignored if missing)
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

# ── Project modules ───────────────────────────────────────────────────────────
from data_fetch   import fetch_stock_data, fetch_multiple_stocks, get_company_info, compute_returns, get_date_defaults
from indicators   import compute_all_indicators, generate_insights
from visualization import (
    plot_price_chart, plot_rsi, plot_macd, plot_volume, plot_volatility,
    plot_comparison, plot_portfolio_pie, plot_portfolio_returns,
)
from portfolio    import compute_portfolio, portfolio_summary
from alerts       import check_alerts
from report       import df_to_csv_bytes, generate_pdf_report
from search       import search_companies, resolve_ticker
from ai_analyst   import generate_ai_analysis, fetch_recent_news


# ════════════════════════════════════════════════════════════════════════════
# PAGE CONFIG
# ════════════════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="StockLens · Analytics Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;700&family=IBM+Plex+Sans:wght@300;400;600;700&display=swap');

  /* Global */
  html, body, [class*="css"] {
    font-family: 'IBM Plex Sans', sans-serif;
    background-color: #0D1117;
    color: #E6EDF3;
  }

  /* Sidebar */
  section[data-testid="stSidebar"] {
    background: #161B22;
    border-right: 1px solid #21262D;
  }
  section[data-testid="stSidebar"] * { color: #E6EDF3 !important; }

  /* Main header */
  .dash-header {
    background: linear-gradient(135deg, #161B22 0%, #0D1117 50%, #1a1f2e 100%);
    border: 1px solid #21262D;
    border-radius: 12px;
    padding: 28px 36px;
    margin-bottom: 24px;
    position: relative;
    overflow: hidden;
  }
  .dash-header::before {
    content: '';
    position: absolute; top: 0; left: 0; right: 0; bottom: 0;
    background: radial-gradient(ellipse at top left, rgba(88,166,255,0.08) 0%, transparent 60%);
    pointer-events: none;
  }
  .dash-header h1 {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 2.1rem; font-weight: 700;
    background: linear-gradient(90deg, #58A6FF, #BC8CFF);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    margin: 0 0 4px 0;
  }
  .dash-header p { color: #8B949E; margin: 0; font-size: 0.95rem; }

  /* Metric card */
  .metric-card {
    background: #161B22;
    border: 1px solid #21262D;
    border-radius: 10px;
    padding: 18px 20px;
    text-align: center;
    transition: border-color .2s;
  }
  .metric-card:hover { border-color: #58A6FF; }
  .metric-label { font-size: 0.78rem; color: #8B949E; text-transform: uppercase; letter-spacing: .08em; margin-bottom: 6px; }
  .metric-value { font-family: 'IBM Plex Mono', monospace; font-size: 1.5rem; font-weight: 700; color: #E6EDF3; }
  .metric-value.up   { color: #00C897; }
  .metric-value.down { color: #FF4B4B; }

  /* Signal badge */
  .badge {
    display: inline-block;
    padding: 4px 12px; border-radius: 20px;
    font-size: 0.82rem; font-weight: 600;
    font-family: 'IBM Plex Mono', monospace;
    margin: 3px 4px;
  }
  .badge-green  { background: rgba(0,200,151,.15);  color: #00C897; border: 1px solid rgba(0,200,151,.3);  }
  .badge-red    { background: rgba(255,75,75,.15);   color: #FF4B4B; border: 1px solid rgba(255,75,75,.3);  }
  .badge-yellow { background: rgba(255,165,0,.15);   color: #FFA500; border: 1px solid rgba(255,165,0,.3);  }
  .badge-blue   { background: rgba(88,166,255,.15);  color: #58A6FF; border: 1px solid rgba(88,166,255,.3); }

  /* Section separator */
  .section-title {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.8rem; font-weight: 500;
    text-transform: uppercase; letter-spacing: .12em;
    color: #8B949E;
    border-bottom: 1px solid #21262D;
    padding-bottom: 8px; margin: 20px 0 14px 0;
  }

  /* Insights box */
  .insights-box {
    background: #161B22;
    border-left: 3px solid #58A6FF;
    border-radius: 0 8px 8px 0;
    padding: 16px 20px;
    margin: 12px 0;
    font-size: 0.9rem; line-height: 1.7;
  }

  /* Streamlit overrides */
  .stButton>button {
    background: #1F6FEB; color: #fff; border: none;
    border-radius: 6px; font-family: 'IBM Plex Mono', monospace;
    font-size: 0.85rem; padding: 8px 20px;
    transition: background .2s;
  }
  .stButton>button:hover { background: #388BFD; }

  div[data-testid="stDataFrame"] { border-radius: 8px; overflow: hidden; }

  /* Tab style */
  .stTabs [data-baseweb="tab"] {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.82rem; text-transform: uppercase; letter-spacing: .06em;
  }
  .stTabs [aria-selected="true"] { color: #58A6FF !important; }

  /* Alerts */
  .stAlert { border-radius: 8px !important; }
</style>
""", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ════════════════════════════════════════════════════════════════════════════

with st.sidebar:
    st.markdown("## 📈 Stock Analytics")
    st.markdown("---")

    # ── Smart Stock Search ────────────────────────────────────────────────────
    st.markdown("### 🔍 Search Stocks")
    st.caption("Type any company name — Indian or global")

    # ── Initialise watched list in session state ───────────────────────────────
    if "watchlist" not in st.session_state:
        st.session_state.watchlist = []

    # ── Live search box ───────────────────────────────────────────────────────
    search_query = st.text_input(
        "Search company",
        placeholder="e.g.  Reliance,  Tata Motors,  Tesla,  HDFC Bank…",
        key="search_box",
        label_visibility="collapsed",
    )

    # Show live search results as a dropdown when user types
    if search_query and len(search_query.strip()) >= 2:
        with st.spinner("Searching…"):
            results = search_companies(search_query, max_results=8)

        if results:
            st.markdown(
                "<div style='font-size:0.75rem;color:#8B949E;margin-bottom:4px;'>"
                f"Found {len(results)} results — select to add to watchlist:</div>",
                unsafe_allow_html=True,
            )
            # Show results as selectable cards
            for i, r in enumerate(results):
                exch_color = "#00C897" if "NSE" in r["exchange"] or "BSE" in r["exchange"] else "#58A6FF"
                if r["type"] == "Crypto":
                    exch_color = "#FFA500"

                col_info, col_btn = st.columns([4, 1])
                with col_info:
                    st.markdown(
                        f"<div style='background:#1c2128;border:1px solid #30363d;"
                        f"border-radius:8px;padding:8px 12px;margin:3px 0;'>"
                        f"<div style='font-size:0.88rem;font-weight:600;color:#E6EDF3;'>"
                        f"{r['name']}</div>"
                        f"<div style='font-size:0.75rem;margin-top:2px;'>"
                        f"<span style='color:{exch_color};font-family:monospace;font-weight:700;'>"
                        f"{r['ticker']}</span>"
                        f"<span style='color:#8B949E;margin-left:8px;'>{r['type']}</span>"
                        f"<span style='color:#8B949E;margin-left:6px;'>· {r['exchange']}</span>"
                        f"</div></div>",
                        unsafe_allow_html=True,
                    )
                with col_btn:
                    if st.button("➕", key=f"add_{i}_{r['ticker']}", help=f"Add {r['name']}"):
                        already = [w["ticker"] for w in st.session_state.watchlist]
                        if r["ticker"] not in already:
                            st.session_state.watchlist.append(
                                {"ticker": r["ticker"], "name": r["name"]}
                            )
                            st.success(f"Added {r['name']}")
                            st.rerun()
                        else:
                            st.info("Already in watchlist")
        else:
            st.warning("No results found. Try a shorter or different name.")

    st.markdown("---")

    # ── Watchlist manager ─────────────────────────────────────────────────────
    st.markdown("**📋 Your Watchlist**")
    if not st.session_state.watchlist:
        st.info("Search and add stocks above.")

    tickers_to_remove = []
    for i, item in enumerate(st.session_state.watchlist):
        wc1, wc2 = st.columns([5, 1])
        with wc1:
            st.markdown(
                f"<div style='padding:4px 0;font-size:0.85rem;'>"
                f"<span style='color:#58A6FF;font-family:monospace;font-weight:600;'>{item['ticker']}</span>"
                f"<span style='color:#8B949E;font-size:0.78rem;margin-left:6px;'>{item['name'][:22]}</span>"
                f"</div>",
                unsafe_allow_html=True,
            )
        with wc2:
            if st.button("✕", key=f"rm_{i}_{item['ticker']}", help="Remove"):
                tickers_to_remove.append(i)

    # Apply removals
    if tickers_to_remove:
        st.session_state.watchlist = [
            w for j, w in enumerate(st.session_state.watchlist)
            if j not in tickers_to_remove
        ]
        st.rerun()

    # ── Primary ticker for analysis ───────────────────────────────────────────
    watchlist_labels = [
        f"{w['ticker']} — {w['name'][:25]}"
        for w in st.session_state.watchlist
    ]
    if not watchlist_labels:
        watchlist_labels = ["—"]

    selected_label = st.selectbox(
        "Analyse stock",
        watchlist_labels,
        index=0,
        help="This stock will be shown in the Analysis tab",
    )
    primary_ticker = selected_label.split(" — ")[0].strip()
    tickers = [w["ticker"] for w in st.session_state.watchlist]

    # ── Date Range ────────────────────────────────────────────────────────────
    st.markdown("### Date Range")
    default_start, default_end = get_date_defaults()
    start_date = st.date_input("Start Date", value=default_start)
    end_date   = st.date_input("End Date",   value=default_end)
    interval   = st.selectbox("Interval", ["1d", "1wk"], format_func=lambda x: "Daily" if x == "1d" else "Weekly")

    # ── Indicator Toggles ─────────────────────────────────────────────────────
    st.markdown("### Indicators")
    show_sma = st.checkbox("SMA (50 / 200)", value=True)
    show_ema = st.checkbox("EMA (20)",       value=True)
    show_bb  = st.checkbox("Bollinger Bands",value=True)

    # ── Alert Thresholds ──────────────────────────────────────────────────────
    st.markdown("### Price Alerts")
    alert_above = st.number_input("Alert if price ABOVE (0 = off)", min_value=0.0, value=0.0, step=10.0)
    alert_below = st.number_input("Alert if price BELOW (0 = off)", min_value=0.0, value=0.0, step=10.0)

    st.markdown("---")
    run_btn = st.button("🔄  Refresh Data", use_container_width=True)
    st.markdown(
        "<div style='color:#8B949E;font-size:0.75rem;text-align:center;margin-top:8px;'>"
        "Data via yfinance · 5-min cache</div>",
        unsafe_allow_html=True,
    )


# ════════════════════════════════════════════════════════════════════════════
# HEADER
# ════════════════════════════════════════════════════════════════════════════

st.markdown("""
<div class="dash-header">
  <h1>📈 Stock Market Analytics Dashboard</h1>
  <p>Search any company by name · Technical analysis · Multi-stock comparison · Portfolio tracker · Alerts</p>
</div>
""", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════
# TABS
# ════════════════════════════════════════════════════════════════════════════

tab_analysis, tab_compare, tab_portfolio, tab_alerts, tab_export, tab_ai = st.tabs([
    "📊 Analysis",
    "🔀 Compare",
    "💼 Portfolio",
    "🔔 Alerts",
    "📥 Export",
    "🤖 AI Analyst",
])


# ════════════════════════════════════════════════════════════════════════════
# TAB 1 — ANALYSIS
# ════════════════════════════════════════════════════════════════════════════

with tab_analysis:
    start_str = start_date.strftime("%Y-%m-%d")
    end_str   = end_date.strftime("%Y-%m-%d")

    if not st.session_state.watchlist:
        st.info("👈 Use the **Search Stocks** panel in the sidebar to find and add stocks to your watchlist.")
        st.stop()

    with st.spinner(f"Fetching data for {primary_ticker}…"):
        raw_df = fetch_stock_data(primary_ticker, start_str, end_str, interval)

    if raw_df.empty:
        st.error(f"❌ No data returned for **{primary_ticker}**. Check the ticker symbol and date range.")
        st.stop()

    df = compute_all_indicators(compute_returns(raw_df.copy()))
    insights = generate_insights(df, primary_ticker)

    # ── Company Info ──────────────────────────────────────────────────────────
    with st.spinner("Loading company info…"):
        info = get_company_info(primary_ticker)
    company_name = info.get("longName") or info.get("shortName") or primary_ticker
    sector       = info.get("sector", "")
    currency     = info.get("currency", "")

    st.markdown(f"### {company_name}")
    if sector and sector != "N/A":
        st.markdown(f"<span class='badge badge-blue'>{sector}</span>", unsafe_allow_html=True)

    # ── Key Metrics ───────────────────────────────────────────────────────────
    st.markdown("<div class='section-title'>Key Metrics</div>", unsafe_allow_html=True)
    metrics = insights.get("metrics", {})
    m_cols = st.columns(6)
    metric_items = list(metrics.items())

    for i, col in enumerate(m_cols):
        if i < len(metric_items):
            k, v = metric_items[i]
            css_class = ""
            if "Return" in k:
                css_class = "up" if float(v) >= 0 else "down"
            with col:
                st.markdown(
                    f"<div class='metric-card'>"
                    f"<div class='metric-label'>{k}</div>"
                    f"<div class='metric-value {css_class}'>{v}</div>"
                    f"</div>",
                    unsafe_allow_html=True,
                )

    # ── Signal Badges ─────────────────────────────────────────────────────────
    st.markdown("<div class='section-title'>Signals</div>", unsafe_allow_html=True)

    def _color_class(color_hex: str) -> str:
        mapping = {"#00C897": "green", "#FF4B4B": "red", "#FFA500": "yellow", "#58A6FF": "blue"}
        return mapping.get(color_hex, "blue")

    badge_html = ""
    for key, label in [
        ("trend", "Trend"), ("cross", "Cross"), ("rsi_signal", "RSI"),
        ("macd_signal", "MACD"), ("volatility", "Volatility"),
    ]:
        val = insights.get(key, ("—", "#888"))
        text, color = val
        css = _color_class(color)
        badge_html += f"<span class='badge badge-{css}'>{label}: {text}</span>"
    st.markdown(badge_html, unsafe_allow_html=True)

    # ── Insights Box ──────────────────────────────────────────────────────────
    summary = insights.get("summary", "")
    if summary:
        st.markdown(f"<div class='insights-box'>{summary}</div>", unsafe_allow_html=True)

    # ── Price Chart ───────────────────────────────────────────────────────────
    st.markdown("<div class='section-title'>Price Chart</div>", unsafe_allow_html=True)
    st.plotly_chart(
        plot_price_chart(df, primary_ticker, show_sma=show_sma, show_ema=show_ema, show_bb=show_bb),
        use_container_width=True,
    )

    # ── Indicator Charts ──────────────────────────────────────────────────────
    st.markdown("<div class='section-title'>Indicators</div>", unsafe_allow_html=True)
    col_l, col_r = st.columns(2)
    with col_l:
        st.plotly_chart(plot_rsi(df, primary_ticker),  use_container_width=True)
        st.plotly_chart(plot_volume(df, primary_ticker), use_container_width=True)
    with col_r:
        st.plotly_chart(plot_macd(df, primary_ticker),       use_container_width=True)
        st.plotly_chart(plot_volatility(df, primary_ticker), use_container_width=True)

    # ── Raw Data ──────────────────────────────────────────────────────────────
    with st.expander("📋 View Raw Data"):
        display_cols = [c for c in ["Open","High","Low","Close","Volume","Daily_Return","RSI","MACD","Volatility"] if c in df.columns]
        st.dataframe(
            df[display_cols].tail(60).style.format({
                c: "{:.2f}" for c in display_cols if c != "Volume"
            }).background_gradient(subset=["Daily_Return"] if "Daily_Return" in display_cols else [], cmap="RdYlGn"),
            use_container_width=True,
        )


# ════════════════════════════════════════════════════════════════════════════
# TAB 2 — MULTI-STOCK COMPARISON
# ════════════════════════════════════════════════════════════════════════════

with tab_compare:
    st.markdown("### Multi-Stock Comparison")
    st.caption("Prices are normalised to 1.0 at the start date for fair comparison.")

    compare_tickers = tickers[:5]  # cap at 5

    with st.spinner("Loading comparison data…"):
        all_data = fetch_multiple_stocks(compare_tickers, start_str, end_str, interval)

    if len(all_data) < 1:
        st.warning("No data found. Check your ticker symbols.")
    else:
        # Normalise
        norm_stocks = {}
        for t, d in all_data.items():
            d2 = compute_returns(d.copy())
            norm_stocks[t] = d2

        st.plotly_chart(plot_comparison(norm_stocks), use_container_width=True)

        # ── Returns Summary Table ─────────────────────────────────────────────
        st.markdown("<div class='section-title'>Return Summary</div>", unsafe_allow_html=True)
        summary_rows = []
        for t, d in norm_stocks.items():
            if len(d) < 2:
                continue
            total_ret  = (d["Close"].iloc[-1] / d["Close"].iloc[0] - 1) * 100
            latest     = d["Close"].iloc[-1]
            vol        = d["Daily_Return"].std() * (252 ** 0.5) if "Daily_Return" in d.columns else None
            summary_rows.append({
                "Ticker":          t,
                "Latest Close":    round(float(latest), 2),
                "Total Return (%)":round(total_ret, 2),
                "Ann. Volatility (%)": round(float(vol), 2) if vol else "N/A",
            })

        if summary_rows:
            ret_df = pd.DataFrame(summary_rows).set_index("Ticker")
            st.dataframe(
                ret_df.style.background_gradient(subset=["Total Return (%)"], cmap="RdYlGn"),
                use_container_width=True,
            )


# ════════════════════════════════════════════════════════════════════════════
# TAB 3 — PORTFOLIO TRACKER
# ════════════════════════════════════════════════════════════════════════════

with tab_portfolio:
    st.markdown("### Portfolio Tracker")
    st.caption("Enter your holdings to calculate current value and P&L.")

    # ── Input Form ────────────────────────────────────────────────────────────
    if "portfolio_holdings" not in st.session_state:
        st.session_state.portfolio_holdings = [
            {"ticker": "", "qty": 1.0, "buy_price": 0.0},
        ]

    st.markdown("**Add / Edit Holdings**")
    num_rows = st.number_input("Number of positions", min_value=1, max_value=20, value=max(1, len(st.session_state.portfolio_holdings)))

    holdings = []
    for i in range(int(num_rows)):
        c1, c2, c3 = st.columns([2, 1, 1])
        prev = st.session_state.portfolio_holdings[i] if i < len(st.session_state.portfolio_holdings) else {}
        with c1:
            t = st.text_input(f"Ticker #{i+1}", value=prev.get("ticker",""), key=f"pt_{i}")
        with c2:
            q = st.number_input(f"Qty #{i+1}", value=float(prev.get("qty", 1)), min_value=0.0, key=f"pq_{i}")
        with c3:
            bp = st.number_input(f"Buy Price #{i+1}", value=float(prev.get("buy_price", 100.0)), min_value=0.0, key=f"pp_{i}")
        if t.strip():
            holdings.append({"ticker": t.strip().upper(), "qty": q, "buy_price": bp})

    st.session_state.portfolio_holdings = holdings

    if st.button("📊 Calculate Portfolio"):
        port_tickers = [h["ticker"] for h in holdings]
        with st.spinner("Fetching current prices…"):
            price_data = fetch_multiple_stocks(port_tickers, start_str, end_str, interval)

        price_map = {}
        for t, d in price_data.items():
            if not d.empty:
                price_map[t] = float(d["Close"].iloc[-1])

        df_port = compute_portfolio(holdings, price_map)
        summ    = portfolio_summary(df_port)

        # ── Summary Banner ────────────────────────────────────────────────────
        p_cols = st.columns(4)
        pnl_class = "up" if summ["total_pnl"] >= 0 else "down"
        ret_class  = "up" if summ["total_return_pct"] >= 0 else "down"

        banner_data = [
            ("Total Invested",   f"{summ['total_investment']:,.2f}", ""),
            ("Current Value",    f"{summ['total_value']:,.2f}", ""),
            ("Total P&L",        f"{'+' if summ['total_pnl']>=0 else ''}{summ['total_pnl']:,.2f}", pnl_class),
            ("Total Return",     f"{summ['total_return_pct']:+.2f}%", ret_class),
        ]
        for col, (lbl, val, css) in zip(p_cols, banner_data):
            with col:
                st.markdown(
                    f"<div class='metric-card'><div class='metric-label'>{lbl}</div>"
                    f"<div class='metric-value {css}'>{val}</div></div>",
                    unsafe_allow_html=True,
                )

        # ── Table ─────────────────────────────────────────────────────────────
        st.markdown("<div class='section-title'>Position Detail</div>", unsafe_allow_html=True)
        numeric_df = df_port.copy()
        st.dataframe(numeric_df, use_container_width=True)

        # ── Charts ────────────────────────────────────────────────────────────
        # Only rows with numeric Current Value
        pie_df = df_port[df_port["Current Value"].apply(lambda x: isinstance(x, (int, float)))].copy()
        ret_df = pie_df[pie_df["Return (%)"].apply(lambda x: isinstance(x, (int, float)))].copy()

        if not pie_df.empty:
            ch1, ch2 = st.columns(2)
            with ch1:
                st.plotly_chart(plot_portfolio_pie(pie_df),      use_container_width=True)
            with ch2:
                st.plotly_chart(plot_portfolio_returns(ret_df),  use_container_width=True)


# ════════════════════════════════════════════════════════════════════════════
# TAB 4 — ALERTS
# ════════════════════════════════════════════════════════════════════════════

with tab_alerts:
    st.markdown("### Active Alerts")
    st.caption("Alerts are evaluated against the latest data for each selected ticker.")

    any_alert = False
    for t in tickers:
        with st.spinner(f"Checking {t}…"):
            d = fetch_stock_data(t, start_str, end_str, interval)
        if d.empty:
            continue
        d = compute_all_indicators(d.copy())

        above = alert_above if alert_above > 0 else None
        below = alert_below if alert_below > 0 else None

        fired = check_alerts(d, t, price_above=above, price_below=below)
        for alert in fired:
            any_alert = True
            if alert["level"] == "success":
                st.success(alert["message"])
            elif alert["level"] == "warning":
                st.warning(alert["message"])
            else:
                st.error(alert["message"])

    if not any_alert:
        st.info("✅ No alerts triggered for the current settings.")

    st.markdown("---")
    st.markdown("**Configure alerts in the sidebar** (Price Above / Price Below) and here:")
    st.markdown("""
    | Alert Type | Condition | Visual |
    |---|---|---|
    | Golden Cross | SMA50 crosses above SMA200 | 🟢 Success |
    | Death Cross  | SMA50 crosses below SMA200 | 🔴 Error   |
    | RSI Overbought | RSI > 70               | 🟡 Warning |
    | RSI Oversold   | RSI < 30               | 🟢 Success |
    | Price Above    | Close > threshold      | 🟢 Success |
    | Price Below    | Close < threshold      | 🔴 Error   |
    """)


# ════════════════════════════════════════════════════════════════════════════
# TAB 5 — EXPORT
# ════════════════════════════════════════════════════════════════════════════

with tab_export:
    st.markdown("### Export Data & Reports")

    export_ticker = st.selectbox("Select ticker to export", tickers)
    with st.spinner(f"Loading {export_ticker} for export…"):
        exp_df  = fetch_stock_data(export_ticker, start_str, end_str, interval)

    if exp_df.empty:
        st.error("No data to export.")
    else:
        exp_df2     = compute_all_indicators(compute_returns(exp_df.copy()))
        exp_insights = generate_insights(exp_df2, export_ticker)

        col_csv, col_pdf = st.columns(2)

        with col_csv:
            st.markdown("#### 📄 CSV Export")
            st.caption("Full OHLCV + indicators dataset.")
            csv_bytes = df_to_csv_bytes(exp_df2)
            st.download_button(
                label="⬇️  Download CSV",
                data=csv_bytes,
                file_name=f"{export_ticker}_analysis.csv",
                mime="text/csv",
                use_container_width=True,
            )

        with col_pdf:
            st.markdown("#### 📑 PDF Report")
            st.caption("Summary PDF with metrics, signals & recent data.")
            if st.button("📄 Generate PDF Report", use_container_width=True):
                with st.spinner("Generating PDF…"):
                    pdf_bytes = generate_pdf_report(export_ticker, exp_insights, exp_df2)
                st.download_button(
                    label="⬇️  Download PDF",
                    data=pdf_bytes,
                    file_name=f"{export_ticker}_report.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )

        # ── Daily Summary ─────────────────────────────────────────────────────
        st.markdown("---")
        st.markdown("#### 🗒 Daily Plain-Language Summary")
        summary = exp_insights.get("summary", "No summary available.")
        st.markdown(f"<div class='insights-box'>{summary}</div>", unsafe_allow_html=True)

        # ── Preview Table ─────────────────────────────────────────────────────
        st.markdown("#### Preview (last 20 rows)")
        disp_cols = [c for c in ["Open","High","Low","Close","Volume","RSI","MACD","Volatility"] if c in exp_df2.columns]
        st.dataframe(exp_df2[disp_cols].tail(20), use_container_width=True)


# ════════════════════════════════════════════════════════════════════════════
# TAB 6 — AI ANALYST (Groq)
# ════════════════════════════════════════════════════════════════════════════

with tab_ai:
    st.markdown("### 🤖 AI-Powered Stock Analysis")
    st.markdown(
        "<div class='insights-box'>"
        "Powered by <b>Llama 3.3 70B</b> on Groq. "
        "The AI reads price movement, volume, RSI, MACD, Bollinger Bands, "
        "recent news headlines, and historical pattern context together — "
        "then writes a plain-English narrative explaining <i>why</i> the stock moved "
        "and <i>what to watch next</i>."
        "</div>",
        unsafe_allow_html=True,
    )

    ai_ticker = st.selectbox(
        "Select stock to analyse",
        [w["ticker"] for w in st.session_state.watchlist] if st.session_state.watchlist else [primary_ticker],
        key="ai_ticker_select",
    )

    col_btn, col_info = st.columns([2, 3])
    with col_btn:
        run_ai = st.button("⚡ Generate AI Analysis", use_container_width=True, type="primary")
    with col_info:
        st.markdown(
            "<div style='padding:8px 0;font-size:0.82rem;color:#8B949E;'>"
            "~3 second response · Uses Groq's free tier · "
            "Consumes ~700 tokens per analysis</div>",
            unsafe_allow_html=True,
        )

    if run_ai:
        if not GROQ_API_KEY:
            st.error("❌ Please enter your Groq API key in the sidebar first. Free at https://console.groq.com")
        else:
            # Load data + indicators for selected ticker
            with st.spinner(f"Loading data for {ai_ticker}…"):
                ai_raw = fetch_stock_data(ai_ticker, start_str, end_str, interval)

            if ai_raw.empty:
                st.error(f"No data found for {ai_ticker}")
            else:
                ai_df       = compute_all_indicators(compute_returns(ai_raw.copy()))
                ai_insights = generate_insights(ai_df, ai_ticker)
                ai_info     = get_company_info(ai_ticker)
                ai_name     = ai_info.get("longName") or ai_info.get("shortName") or ai_ticker

                # ── Data preview fed to AI ─────────────────────────────────────
                with st.expander("📋 Data being fed to the AI"):
                    last_row = ai_df.iloc[-1]
                    prev_row = ai_df.iloc[-2] if len(ai_df) > 1 else last_row

                    c1, c2, c3, c4 = st.columns(4)
                    change     = float(last_row["Close"]) - float(prev_row["Close"])
                    change_pct = change / float(prev_row["Close"]) * 100

                    c1.metric("Close",       f"₹{float(last_row['Close']):,.2f}", f"{change_pct:+.2f}%")
                    c2.metric("RSI",         f"{float(last_row.get('RSI', 0)):.1f}")
                    c3.metric("MACD Hist",   f"{float(last_row.get('MACD_Hist', 0)):+.4f}")
                    c4.metric("Volatility",  f"{float(last_row.get('Volatility', 0)):.1f}%")

                    # News preview
                    st.markdown("**Recent news headlines fetched:**")
                    news_prev = fetch_recent_news(ai_ticker)
                    if news_prev:
                        for n in news_prev:
                            st.markdown(f"- [{n['publisher']}] {n['title']}")
                    else:
                        st.caption("No recent news found via yfinance.")

                # ── Generate & stream analysis ─────────────────────────────────
                with st.spinner("🧠 Groq is analysing the data…"):
                    analysis = generate_ai_analysis(
                        ticker=ai_ticker,
                        company_name=ai_name,
                        df=ai_df,
                        insights=ai_insights,
                        groq_api_key=GROQ_API_KEY,
                    )

                # ── Render the analysis ────────────────────────────────────────
                st.markdown("---")
                st.markdown(
                    f"<div style='font-size:0.78rem;color:#8B949E;margin-bottom:12px;'>"
                    f"Analysis for <b style='color:#58A6FF;'>{ai_name} ({ai_ticker})</b> · "
                    f"Generated {__import__('datetime').datetime.now().strftime('%d %b %Y %H:%M')}"
                    f"</div>",
                    unsafe_allow_html=True,
                )

                # Render each section in a styled box
                sections = analysis.split("**")
                if len(sections) > 2:
                    st.markdown(
                        f"<div style='background:#161B22;border:1px solid #21262D;"
                        f"border-radius:12px;padding:24px 28px;line-height:1.8;'>"
                        f"{analysis}"
                        f"</div>",
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(analysis)

                # ── Save to session for re-display ─────────────────────────────
                if "ai_history" not in st.session_state:
                    st.session_state.ai_history = []
                st.session_state.ai_history.insert(0, {
                    "ticker":   ai_ticker,
                    "name":     ai_name,
                    "analysis": analysis,
                    "time":     __import__("datetime").datetime.now().strftime("%H:%M"),
                })
                st.session_state.ai_history = st.session_state.ai_history[:5]  # keep last 5

    # ── Previous analyses ──────────────────────────────────────────────────────
    if "ai_history" in st.session_state and st.session_state.ai_history:
        st.markdown("---")
        st.markdown("<div class='section-title'>Previous Analyses This Session</div>", unsafe_allow_html=True)
        for i, entry in enumerate(st.session_state.ai_history[1:], 1):
            with st.expander(f"[{entry['time']}] {entry['name']} ({entry['ticker']})"):
                st.markdown(entry["analysis"])

    # ── How it works ──────────────────────────────────────────────────────────
    with st.expander("🔍 How does this AI analysis work?"):
        st.markdown("""
**Data inputs fed to the AI (Llama 3.3 70B via Groq):**

1. **Price movement** — today's close, change %, 52-week high/low context
2. **Volume analysis** — today's volume vs 20-day average (detects unusual activity)
3. **RSI** — overbought/oversold classification with exact value
4. **MACD** — line, signal line, and histogram direction
5. **Bollinger Bands** — where price sits within the band (% position)
6. **SMA 50 / SMA 200** — trend classification and cross detection
7. **Annualised Volatility** — risk level assessment
8. **Recent news headlines** — fetched live from yfinance (up to 6 headlines)
9. **Historical pattern matching** — finds up to 5 past dates where RSI and daily return were in a similar range, and shows what happened in the 10 days after

The AI is instructed to write like a **senior equity analyst** — specific, data-driven, and actionable — not generic financial advice.
        """)
