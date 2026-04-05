"""
report.py
Export helpers: CSV download bytes and a lightweight PDF summary
using the fpdf2 library (no LaTeX required).
"""

import io
import pandas as pd


# ── CSV ───────────────────────────────────────────────────────────────────────

def df_to_csv_bytes(df: pd.DataFrame) -> bytes:
    """Return a UTF-8 encoded CSV byte-string suitable for st.download_button."""
    return df.to_csv(index=True).encode("utf-8")


# ── PDF ───────────────────────────────────────────────────────────────────────

def generate_pdf_report(
    ticker: str,
    insights: dict,
    df: pd.DataFrame,
) -> bytes:
    """
    Build a simple PDF report and return it as bytes.
    Falls back to a plain-text byte string if fpdf2 is unavailable.
    """
    try:
        from fpdf import FPDF
    except ImportError:
        # Fallback: return plain-text
        return _plain_text_report(ticker, insights, df)

    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # ── Header ────────────────────────────────────────────────────────────────
    pdf.set_fill_color(13, 17, 23)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 20)
    pdf.cell(0, 14, f"Stock Analysis Report: {ticker}", ln=True, align="C", fill=True)
    pdf.ln(4)

    pdf.set_text_color(30, 30, 30)
    pdf.set_font("Helvetica", "", 10)
    from datetime import datetime
    pdf.cell(0, 6, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=True, align="C")
    pdf.ln(8)

    # ── Trend section ─────────────────────────────────────────────────────────
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_fill_color(220, 230, 255)
    pdf.cell(0, 9, "Trend & Signal Summary", ln=True, fill=True)
    pdf.ln(3)

    pdf.set_font("Helvetica", "", 11)
    if insights:
        for label, key in [
            ("Trend",           "trend"),
            ("Cross Signal",    "cross"),
            ("RSI Signal",      "rsi_signal"),
            ("MACD Signal",     "macd_signal"),
            ("Volatility",      "volatility"),
        ]:
            val = insights.get(key, ("N/A", ""))
            text = val[0] if isinstance(val, tuple) else str(val)
            pdf.cell(60, 7, f"{label}:", border=0)
            pdf.cell(0, 7, text, ln=True)
    pdf.ln(6)

    # ── Key Metrics ───────────────────────────────────────────────────────────
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_fill_color(220, 230, 255)
    pdf.cell(0, 9, "Key Metrics", ln=True, fill=True)
    pdf.ln(3)
    pdf.set_font("Helvetica", "", 11)
    if insights and "metrics" in insights:
        for k, v in insights["metrics"].items():
            pdf.cell(80, 7, f"{k}:", border=0)
            pdf.cell(0, 7, str(v), ln=True)
    pdf.ln(6)

    # ── Plain-language summary ────────────────────────────────────────────────
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_fill_color(220, 230, 255)
    pdf.cell(0, 9, "Daily Summary", ln=True, fill=True)
    pdf.ln(3)
    pdf.set_font("Helvetica", "", 10)
    summary_raw = insights.get("summary", "") if insights else ""
    # Strip markdown bold markers
    summary_clean = summary_raw.replace("**", "")
    pdf.multi_cell(0, 6, summary_clean)
    pdf.ln(6)

    # ── Recent OHLCV table ────────────────────────────────────────────────────
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_fill_color(220, 230, 255)
    pdf.cell(0, 9, "Recent Price Data (last 10 rows)", ln=True, fill=True)
    pdf.ln(3)

    cols = ["Open", "High", "Low", "Close", "Volume"]
    cols = [c for c in cols if c in df.columns]
    recent = df[cols].tail(10).reset_index()

    pdf.set_font("Helvetica", "B", 9)
    col_widths = [28] + [25] * len(cols)
    headers = ["Date"] + cols
    for i, h in enumerate(headers):
        pdf.cell(col_widths[i], 7, h, border=1, align="C")
    pdf.ln()

    pdf.set_font("Helvetica", "", 9)
    for _, row in recent.iterrows():
        date_str = str(row.iloc[0])[:10]
        pdf.cell(col_widths[0], 6, date_str, border=1, align="C")
        for j, c in enumerate(cols):
            val = row[c]
            txt = f"{val:,.0f}" if c == "Volume" else f"{val:.2f}"
            pdf.cell(col_widths[j + 1], 6, txt, border=1, align="R")
        pdf.ln()

    return bytes(pdf.output())


def _plain_text_report(ticker, insights, df) -> bytes:
    """Fallback plain-text report when fpdf2 is not installed."""
    lines = [
        f"Stock Analysis Report: {ticker}",
        "=" * 50,
        "",
    ]
    if insights:
        for key in ["trend", "cross", "rsi_signal", "macd_signal", "volatility"]:
            val = insights.get(key, ("N/A",))
            lines.append(f"{key.upper()}: {val[0] if isinstance(val, tuple) else val}")
        lines.append("")
        lines.append("SUMMARY:")
        lines.append(insights.get("summary", "").replace("**", ""))
    return "\n".join(lines).encode("utf-8")
