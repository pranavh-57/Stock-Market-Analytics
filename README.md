# 📈 AI-Powered Stock Market Analytics Dashboard

> **Search any company by name. Analyse technicals. Get AI explanations. Track your portfolio.**
> Built with Python, Streamlit, Plotly, and Groq (Llama 3.3 70B).

![Python](https://img.shields.io/badge/Python-3.10+-blue?style=flat-square&logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-1.35+-red?style=flat-square&logo=streamlit)
![Plotly](https://img.shields.io/badge/Plotly-5.20+-purple?style=flat-square&logo=plotly)
![Groq](https://img.shields.io/badge/AI-Groq%20%7C%20Llama%203.3-orange?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

---

## What It Does

The project is a full-stack stock analysis dashboard that goes beyond just showing charts. It:

- Lets you **search companies by name** (type "Reliance" or "Tesla" — no ticker codes needed)
- Computes **7 technical indicators** and translates them into plain-English signals
- Uses **Groq's Llama 3.3 70B** to generate analyst-style narratives combining price movement, volume, indicators, live news, and historical pattern matching
- Tracks your **portfolio P&L** in real time
- Fires **price and indicator alerts** without needing an account
- Exports full datasets as **CSV** and generates **PDF reports**

---

## Features

### Smart Company Search
Type any company name — Indian or global. The app queries Yahoo Finance's autocomplete API and returns matching results with exchange and asset type. No need to know ticker symbols.

| You type | App finds |
|---|---|
| `Reliance` | Reliance Industries · RELIANCE.NS · NSE |
| `HDFC Bank` | HDFC Bank Ltd · HDFCBANK.NS · NSE |
| `Tesla` | Tesla Inc · TSLA · NASDAQ |
| `Bitcoin` | Bitcoin USD · BTC-USD · Crypto |

---

### Technical Analysis
Full indicator suite computed from scratch using pandas and numpy:

| Indicator | Details |
|---|---|
| SMA | 50-day and 200-day Simple Moving Average |
| EMA | 20-day Exponential Moving Average |
| RSI | 14-period Wilder RSI with overbought (>70) / oversold (<30) zones |
| MACD | 12/26/9 — line, signal line, and histogram |
| Bollinger Bands | 20-day SMA ± 2 standard deviations |
| Volatility | Rolling 20-day annualised volatility (%) |
| Returns | Daily %, cumulative, and normalised price |

---

### AI Analyst (Groq + Llama 3.3 70B)
The standout feature. Feeds 9 data inputs to the LLM and generates a structured analyst note:

1. **Price movement** — today's change and 52-week context
2. **Volume spike detection** — today vs 20-day average
3. **RSI + MACD + Bollinger Bands** — interpreted together, not in isolation
4. **Trend & cross signals** — Golden Cross / Death Cross detection
5. **Volatility level** — annualised risk classification
6. **Live news headlines** — fetched from yfinance (up to 6 headlines)
7. **Historical pattern matching** — finds past dates with similar RSI + daily return, shows 10-day forward outcomes

**Sample output:**

> **What Happened Today** — Infosys fell 2.3% on 1.9x average volume, suggesting active institutional selling rather than a thin-market drift...
>
> **What the Indicators Say** — RSI at 67 is approaching overbought territory as price touches the upper Bollinger Band. MACD histogram turned negative for the first time in 8 sessions, signalling fading momentum...
>
> **Historical Patterns** — 3 similar setups found (Sep 2023, Feb 2024, Jun 2024). Average 10-day outcome: −1.8%, with 2 of 3 seeing further weakness before recovery...
>
> **What to Watch Next**
> - Watch if price holds above ₹1,820 (BB Mid / 20-day SMA)
> - RSI crossing below 60 would confirm momentum shift
> - Watch for management commentary at upcoming earnings
>
> **Risk Note** — Elevated volatility at 38% annualised increases the chance of sharp intraday swings in either direction.

---

### Multi-Stock Comparison
Compare up to 5 stocks simultaneously on a normalised price chart (all start at 1.0) — making ₹ vs $ comparisons visually meaningful. Includes a return summary table with annualised volatility.

---

### Portfolio Tracker
Enter your holdings (stock, quantity, buy price) and instantly see:
- Current value per position
- Rupee P&L and percentage return
- Total portfolio value, total investment, overall return
- Allocation pie chart and per-stock returns bar chart

---

### Alerts System
Set price thresholds in the sidebar. The app automatically checks and fires:
- Price crossed above / below your target
- RSI overbought (>70) or oversold (<30)
- Golden Cross or Death Cross detected in the last 5 sessions

---

### Export
- **CSV** — full OHLCV dataset with all computed indicator columns
- **PDF** — formatted report with signals, metrics, summary, and recent price table

---

## Getting Started

### 1. Clone the repository
```bash
git clone https://github.com/your-username/stocklens.git
cd stocklens
```

### 2. Create a virtual environment
```bash
python -m venv .venv

# Activate it:
source .venv/bin/activate        # macOS / Linux
.venv\Scripts\activate           # Windows
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Set up your environment file
```bash
cp .env.example .env
```
Open `.env` and add your Groq API key:
```
GROQ_API_KEY=gsk_your_key_here
```
> Get a **free** Groq API key (no credit card) at [console.groq.com](https://console.groq.com)
> The AI Analyst tab works only with this key. All other features work without it.

### 5. Run the app
```bash
streamlit run app.py
```
Opens at **http://localhost:8501**

---

## Tech Stack

| Layer | Technology |
|---|---|
| UI Framework | Streamlit |
| Data Source | yfinance (Yahoo Finance) |
| Charts | Plotly |
| Data Processing | pandas, numpy |
| AI / LLM | Groq API · Llama 3.3 70B Versatile |
| PDF Generation | fpdf2 |
| Environment Config | python-dotenv |
| Search API | Yahoo Finance autocomplete (no key needed) |

---

## Dependencies

```
streamlit
yfinance
pandas
numpy
plotly
groq
fpdf2
requests
python-dotenv
matplotlib
```

---

## Privacy & Security

- Your `.env` file and Groq API key **never leave your machine** — `.gitignore` excludes it from git
- Your watchlist and portfolio data are stored only in **Streamlit session state** (in-memory, cleared on browser close)
- No user accounts, no cloud storage, no analytics tracking
- All data fetched directly from Yahoo Finance — no third-party intermediaries

---

## Disclaimer

This project is built for **educational and personal research purposes only**. It is not financial advice. Always do your own research before making investment decisions. Market data is sourced from Yahoo Finance via the yfinance library and may have delays or inaccuracies.

---

## Acknowledgements

- [yfinance](https://github.com/ranaroussi/yfinance) — Yahoo Finance data wrapper
- [Groq](https://groq.com) — Ultra-fast LLM inference
- [Streamlit](https://streamlit.io) — Python web app framework
- [Plotly](https://plotly.com) — Interactive charting library

---

## 📄 License

MIT License — free to use, modify, and distribute with attribution.
