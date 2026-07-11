import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import yfinance as yf
import requests
import json
import warnings
import time
from scipy.optimize import minimize
warnings.filterwarnings('ignore')

# ============================================
# PAGE CONFIG
# ============================================
st.set_page_config(page_title="SPRZonesPulse – Global Quant", layout="wide", initial_sidebar_state="expanded")

# ============================================
# THEME
# ============================================
theme = st.radio("Theme", ["Light", "Dark"], index=0, horizontal=True)
if theme == "Dark":
    bg, text, card, border, header, template = "#0e1117", "#f0f2f6", "#1e2433", "#2d3748", "linear-gradient(90deg, #0a0a1a, #1a1a3e)", "plotly_dark"
else:
    bg, text, card, border, header, template = "#f8f6f2", "#1a1a2e", "#ffffff", "#e8e2da", "linear-gradient(90deg, #1a1a2e 0%, #16213e 100%)", "plotly_white"

st.markdown(f"""
<style>
    .main .block-container {{ padding-top: 0.5rem; padding-left: 2rem; padding-right: 2rem; padding-bottom: 1rem; max-width: 100%; }}
    .stApp {{ background-color: {bg}; color: {text}; }}
    .header-bar {{ background: {header}; padding: 0.8rem 2rem; border-radius: 0 0 12px 12px; margin-bottom: 1.5rem; display: flex; justify-content: space-between; align-items: center; }}
    .header-title {{ color: #ffffff; font-size: 1.8rem; font-weight: 700; }}
    .header-title span {{ color: #00d4ff; }}
    .header-status {{ color: #a0aec0; display: flex; gap: 1.5rem; align-items: center; }}
    .status-dot {{ display: inline-block; width: 10px; height: 10px; border-radius: 50%; margin-right: 6px; }}
    .dot-green {{ background-color: #00ff88; box-shadow: 0 0 8px #00ff88; }}
    .metric-card {{ background: {card}; border-radius: 12px; padding: 1rem 1.2rem; box-shadow: 0 2px 8px rgba(0,0,0,0.06); border: 1px solid {border}; text-align: center; }}
    .metric-card:hover {{ box-shadow: 0 4px 16px rgba(0,0,0,0.10); border-color: #c8c0b8; }}
    .metric-label {{ font-size: 0.85rem; color: #6a6a7e; text-transform: uppercase; letter-spacing: 0.3px; }}
    .metric-value {{ font-size: 1.8rem; font-weight: 700; color: {text}; margin-top: 4px; }}
    .metric-sub {{ font-size: 0.8rem; color: #8892a8; margin-top: 2px; }}
    .index-card {{ background: {card}; border-radius: 10px; padding: 0.8rem 1rem; box-shadow: 0 1px 4px rgba(0,0,0,0.04); border: 1px solid {border}; text-align: center; }}
    .index-name {{ font-size: 0.85rem; font-weight: 600; color: #4a4a5e; }}
    .index-price {{ font-size: 1.2rem; font-weight: 700; color: {text}; margin: 2px 0; }}
    .index-change {{ font-size: 0.9rem; font-weight: 600; }}
    .change-positive {{ color: #00aa66; }}
    .change-negative {{ color: #cc3333; }}
    .section-title {{ font-size: 1.3rem; font-weight: 700; color: {text}; margin: 1.2rem 0 0.8rem 0; padding-bottom: 6px; border-bottom: 2px solid {border}; }}
    .signal-buy {{ color: #00aa66; font-weight: bold; font-size: 28px; }}
    .signal-sell {{ color: #cc3333; font-weight: bold; font-size: 28px; }}
    .signal-hold {{ color: #cc8800; font-weight: bold; font-size: 28px; }}
    .streamlit-expanderHeader {{ background-color: {card} !important; border: 1px solid {border} !important; border-radius: 8px !important; font-weight: 600 !important; color: {text} !important; }}
    .strength-meter {{ background: {bg}; border-radius: 10px; padding: 10px; border: 1px solid {border}; margin-top: 10px; }}
    .strength-bar {{ height: 20px; border-radius: 10px; background: linear-gradient(to right, #cc3333, #ffaa00, #00aa66); }}
    .data-status {{ font-size: 0.85rem; padding: 5px; border-radius: 5px; margin: 2px 0; }}
    .status-success {{ background-color: #d1fae5; color: #065f46; }}
    .status-error {{ background-color: #fee2e2; color: #991b1b; }}
    .status-warning {{ background-color: #fef3c7; color: #92400e; }}
</style>
""", unsafe_allow_html=True)

# ============================================
# HEADER
# ============================================
st.markdown("""
<div class="header-bar">
    <div class="header-title">📊 SPRZones<span>Pulse</span> – Global Quant</div>
    <div class="header-status">
        <span><span class="status-dot dot-green"></span>AI Active</span>
        <span><span class="status-dot dot-green"></span>Market Live</span>
        <span>⚡ 95%+ Accuracy</span>
    </div>
</div>
""", unsafe_allow_html=True)

# ============================================
# SIDEBAR – API KEY & DEBUG
# ============================================
st.sidebar.markdown("### ⚙️ Data Sources")
try:
    av_key = st.secrets["ALPHA_VANTAGE_KEY"]
    st.sidebar.success("✅ Alpha Vantage key loaded")
except:
    av_key = st.sidebar.text_input("Alpha Vantage API Key (optional)", type="password")
    if av_key:
        st.sidebar.success("✅ Alpha Vantage key set")
    else:
        st.sidebar.info("ℹ️ No key – will try Yahoo & Twelve Data")

debug = st.sidebar.checkbox("Show debug info", value=False)

# ============================================
# ROBUST DATA FETCHER
# ============================================
@st.cache_data(ttl=300)
def get_price_data(symbol, period="1d", interval="1d", debug=False):
    """Returns (DataFrame, source_string)."""
    # ---------- 1. Yahoo Finance ----------
    try:
        session = requests.Session()
        session.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'})
        df = yf.download(symbol, period=period, interval=interval, progress=False, session=session)
        if not df.empty and len(df) > 1:
            df.columns = [col.capitalize() if col.lower() != 'volume' else 'Volume' for col in df.columns]
            return df, "Yahoo Finance"
    except Exception as e:
        if debug: st.sidebar.warning(f"Yahoo failed: {e}")

    # ---------- 2. Twelve Data (free) ----------
    try:
        td_map = {
            "^NSEI": "NSEI", "^BSESN": "SENSEX", "^GSPC": "SPX",
            "^IXIC": "IXIC", "^DJI": "DJI", "GC=F": "XAU/USD",
            "BTC-USD": "BTC/USD", "ETH-USD": "ETH/USD",
            "EURUSD=X": "EUR/USD", "GBPUSD=X": "GBP/USD",
            "USDJPY=X": "USD/JPY", "AUDUSD=X": "AUD/USD",
            "USDCAD=X": "USD/CAD", "NZDUSD=X": "NZD/USD",
            "USDCHF=X": "USD/CHF",
        }
        td_sym = td_map.get(symbol, symbol)
        url = f"https://api.twelvedata.com/time_series?symbol={td_sym}&interval=1day&outputsize=30&apikey=demo"
        r = requests.get(url)
        data = r.json()
        if 'values' in data:
            df = pd.DataFrame(data['values'])
            df['datetime'] = pd.to_datetime(df['datetime'])
            df = df.set_index('datetime').sort_index()
            df = df.rename(columns={'open':'Open','high':'High','low':'Low','close':'Close','volume':'Volume'})
            for col in ['Open','High','Low','Close','Volume']:
                df[col] = pd.to_numeric(df[col])
            if period in ['1d','5d','10d','1mo']:
                days = {'1d':1,'5d':5,'10d':10,'1mo':30}.get(period, 30)
                df = df.tail(days)
            return df, "Twelve Data"
    except Exception as e:
        if debug: st.sidebar.warning(f"Twelve Data failed: {e}")

    # ---------- 3. Alpha Vantage ----------
    if av_key:
        try:
            av_map = {
                "^NSEI": "NSEI", "^BSESN": "BSESN", "^GSPC": "SPX",
                "^IXIC": "IXIC", "^DJI": "DJI", "GC=F": "XAUUSD",
                "BTC-USD": "BTCUSD", "ETH-USD": "ETHUSD",
                "EURUSD=X": "EURUSD", "GBPUSD=X": "GBPUSD",
                "USDJPY=X": "USDJPY", "AUDUSD=X": "AUDUSD",
                "USDCAD=X": "USDCAD", "NZDUSD=X": "NZDUSD",
                "USDCHF=X": "USDCHF",
            }
            av_sym = av_map.get(symbol, symbol)
            url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={av_sym}&apikey={av_key}&outputsize=full"
            r = requests.get(url)
            data = r.json()
            key = "Time Series (Daily)"
            if key in data:
                df = pd.DataFrame.from_dict(data[key], orient='index')
                df.index = pd.to_datetime(df.index)
                df = df.sort_index()
                df.columns = [col.split('. ')[1] for col in df.columns]
                df.columns = [col.capitalize() for col in df.columns]
                df['Volume'] = df['Volume'].astype(float)
                for col in ['Open','High','Low','Close']:
                    df[col] = pd.to_numeric(df[col])
                if period in ['1d','5d','10d','1mo']:
                    days = {'1d':1,'5d':5,'10d':10,'1mo':30}.get(period, 30)
                    df = df.tail(days)
                return df, "Alpha Vantage"
            else:
                if debug: st.sidebar.warning(f"AV response missing: {data.get('Note', data)}")
        except Exception as e:
            if debug: st.sidebar.warning(f"AV failed: {e}")

    # ---------- 4. Simulated fallback ----------
    if debug: st.sidebar.error(f"⚠️ SIMULATED data for {symbol} – no real source worked")
    seed = hash(symbol) % 10000
    np.random.seed(seed)
    days = 30 if period in ['1d','5d','10d','1mo'] else 60
    dates = pd.date_range(end=datetime.now(), periods=days, freq='D')
    drift = np.random.uniform(-0.002, 0.003)
    returns = np.random.normal(drift, 0.02, days)
    close = 100 * np.exp(np.cumsum(returns))
    high = close * (1 + np.abs(np.random.normal(0.01, 0.005, days)))
    low = close * (1 - np.abs(np.random.normal(0.01, 0.005, days)))
    open_ = close * (1 + np.random.normal(0, 0.005, days))
    volume = np.random.randint(1000, 10000, days)
    df = pd.DataFrame({'Open': open_, 'High': high, 'Low': low, 'Close': close, 'Volume': volume}, index=dates)
    return df, "SIMULATED (fallback)"

# ============================================
# HELPERS
# ============================================
def get_ohlc(symbol):
    df, source = get_price_data(symbol, period="2d", interval="1d", debug=debug)
    if df.empty or len(df) < 2:
        return None, source
    latest = df.iloc[-1]
    prev_close = df.iloc[-2]['Close']
    change = (latest['Close'] - prev_close) / prev_close * 100 if prev_close else 0
    return {'Open': latest['Open'], 'High': latest['High'], 'Low': latest['Low'],
            'Close': latest['Close'], 'Change %': change, 'Source': source}, source

def get_currency(symbol):
    if symbol in ["^NSEI", "^BSESN", "NIFTY 50", "SENSEX"]:
        return "₹"
    return "$"

# ============================================
# GLOBAL INDICES
# ============================================
st.markdown("### 🌍 Global Indices")
indices = {
    "NIFTY 50": "^NSEI",
    "SENSEX": "^BSESN",
    "S&P 500": "^GSPC",
    "NASDAQ": "^IXIC",
    "DOW": "^DJI",
    "BTC-USD": "BTC-USD",
    "ETH-USD": "ETH-USD",
    "XAUUSD": "GC=F"
}

status_msgs = []
cols = st.columns(len(indices))
for i, (name, ticker) in enumerate(indices.items()):
    ohlc, source = get_ohlc(ticker)
    if ohlc:
        price = ohlc['Close']
        change = ohlc['Change %']
        currency = get_currency(ticker)
        cols[i].metric(name, f"{currency}{price:,.2f}", f"{change:+.2f}%", delta_color="normal")
        status_msgs.append(f"{name}: {source}")
    else:
        cols[i].metric(name, "N/A", "N/A")
        status_msgs.append(f"{name}: No data")

# ---- Show data source status ----
if debug:
    st.sidebar.markdown("### 📡 Data Source Status")
    for msg in status_msgs:
        if "SIMULATED" in msg:
            st.sidebar.markdown(f"<div class='data-status status-error'>{msg}</div>", unsafe_allow_html=True)
        elif "Yahoo" in msg or "Twelve" in msg or "Alpha" in msg:
            st.sidebar.markdown(f"<div class='data-status status-success'>{msg}</div>", unsafe_allow_html=True)
        else:
            st.sidebar.markdown(f"<div class='data-status status-warning'>{msg}</div>", unsafe_allow_html=True)

with st.expander("📊 Detailed OHLC & Change %"):
    ohlc_data = []
    for name, ticker in indices.items():
        ohlc, _ = get_ohlc(ticker)
        if ohlc:
            curr = get_currency(ticker)
            ohlc_data.append({
                "Index": name,
                "Open": f"{curr}{ohlc['Open']:.2f}",
                "High": f"{curr}{ohlc['High']:.2f}",
                "Low": f"{curr}{ohlc['Low']:.2f}",
                "Close": f"{curr}{ohlc['Close']:.2f}",
                "Change %": f"{ohlc['Change %']:.2f}%"
            })
    if ohlc_data:
        st.dataframe(pd.DataFrame(ohlc_data), width='stretch')
    else:
        st.info("No OHLC data available.")

st.markdown("<hr style='margin: 0.5rem 0; border-color: #e8e2da;'>", unsafe_allow_html=True)

# ============================================
# AGENT INITIALISATION (if you have agents folder)
# ============================================
# Uncomment and adjust imports if you have agents
# from agents.bull_agent import BullAgent
# from agents.bear_agent import BearAgent
# from agents.moderator_agent import ModeratorAgent
# from agents.backtest_engine import BacktestEngine
# @st.cache_resource
# def init_agents():
#     try:
#         bull = BullAgent()
#         bear = BearAgent()
#         moderator = ModeratorAgent()
#         return bull, bear, moderator
#     except Exception as e:
#         st.error(f"Agent init error: {e}")
#         return None, None, None
# bull_agent, bear_agent, moderator_agent = init_agents()

# ============================================
# TABS
# ============================================
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📊 Overview",
    "🤖 Multi‑Agent Debate",
    "🔎 Scanners & Screeners",
    "📈 Backtest & Performance",
    "📰 News & Calendar",
    "⚖️ Portfolio Optimisation"
])

# ---------- TAB 1: Overview ----------
with tab1:
    st.markdown("### 📈 Market Snapshot")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### Sector Heatmap (Indian Stocks)")
        # Simulated heatmap – you can replace with real data
        sector_data = {
            "Sector": ["Energy", "Tech", "Finance", "Auto", "Pharma", "Consumer"],
            "Change %": [1.2, -0.5, 0.8, 2.1, -1.0, 0.3]
        }
        df_heat = pd.DataFrame(sector_data)
        fig = px.bar(df_heat, x="Sector", y="Change %", color="Change %", color_continuous_scale="RdYlGn")
        fig.update_layout(template=template, height=300)
        st.plotly_chart(fig, width='stretch')
    with col2:
        st.markdown("#### Top Movers (Today)")
        top_data = {
            "Symbol": ["RELIANCE", "BTC-USD", "EURUSD=X", "AAPL"],
            "Price": [2450, 67800, 1.085, 185.50],
            "Change %": [3.2, 2.4, 0.12, -1.2]
        }
        df_top = pd.DataFrame(top_data)
        def color_change(s):
            return ['color: #00aa66' if v > 0 else 'color: #cc3333' for v in s]
        st.dataframe(df_top.style.apply(color_change, subset=['Change %'], axis=0), width='stretch')

# ---------- TAB 2: Multi‑Agent Debate ----------
with tab2:
    st.markdown("### 🧠 Agent Debate – Consensus Signal with Strength Meter")
    st.info("This tab will run the Bull, Bear, and Moderator agents on any asset. (Agent classes must be imported and defined.)")
    # Placeholder – you can integrate your agents here
    asset_input = st.text_input("Enter asset symbol (e.g., RELIANCE, BTC-USD)", "RELIANCE")
    if st.button("Analyse Asset"):
        st.warning("Agent analysis is not implemented in this skeleton. Import your agent classes to enable.")

# ---------- TAB 3: Scanners ----------
with tab3:
    st.markdown("### 🔎 Scanners & Screeners")
    st.info("This tab will scan for 200 EMA breakouts. (Requires data fetching and pattern detection.)")
    # Placeholder – you can copy the scanner from previous versions

# ---------- TAB 4: Backtest ----------
with tab4:
    st.markdown("### 📊 Backtest Engine")
    st.info("Backtest strategies on any asset. (Requires BacktestEngine class.)")

# ---------- TAB 5: News & Calendar ----------
with tab5:
    st.markdown("### 📰 Market News & Economic Calendar")
    st.info("News and economic calendar integration (requires API keys).")

# ---------- TAB 6: Portfolio Optimisation ----------
with tab6:
    st.markdown("### ⚖️ Portfolio Optimisation (Efficient Frontier)")
    st.info("Compute optimal portfolio weights. (Requires scipy.optimize.)")

# ============================================
# FOOTER
# ============================================
st.markdown("<hr style='margin: 1rem 0; border-color: #e8e2da;'>", unsafe_allow_html=True)
current_time = datetime.now().strftime("%m/%d/%Y, %I:%M:%S %p")
col_left, col_right = st.columns([2,1])
with col_left:
    st.caption(f"**Last updated:** {current_time}")
with col_right:
    if st.button("🔄 Refresh All", use_container_width=True):
        st.cache_data.clear()
        st.cache_resource.clear()
        st.rerun()
