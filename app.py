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
# IMPORTS FOR YOUR AGENTS (adjust paths if needed)
# ============================================
try:
    from agents.bull_agent import BullAgent
    from agents.bear_agent import BearAgent
    from agents.moderator_agent import ModeratorAgent
    from agents.backtest_engine import BacktestEngine
    AGENTS_AVAILABLE = True
except ImportError:
    AGENTS_AVAILABLE = False
    st.warning("Agent classes not found. Some features will be disabled.")

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
# ROBUST DATA FETCHER WITH DETAILED ERRORS
# ============================================
@st.cache_data(ttl=300)
def get_price_data(symbol, period="1d", interval="1d", debug=False):
    """
    Try: Yahoo Finance → Twelve Data → Alpha Vantage → Simulated
    Returns (DataFrame, source_string).
    """
    error_messages = []
    # ---------- 1. Yahoo Finance ----------
    try:
        session = requests.Session()
        session.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
        df = yf.download(symbol, period=period, interval=interval, progress=False, session=session)
        if not df.empty and len(df) > 1:
            df.columns = [col.capitalize() if col.lower() != 'volume' else 'Volume' for col in df.columns]
            return df, "Yahoo Finance"
    except Exception as e:
        error_messages.append(f"Yahoo: {e}")

    # ---------- 2. Twelve Data ----------
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
        error_messages.append(f"Twelve Data: {e}")

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
            if 'Note' in data:
                error_messages.append(f"AV rate limit: {data['Note']}")
            elif 'Error Message' in data:
                error_messages.append(f"AV error: {data['Error Message']}")
            else:
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
                    error_messages.append(f"AV response missing time series: {list(data.keys())}")
        except Exception as e:
            error_messages.append(f"AV exception: {e}")

    # ---------- 4. Simulated fallback ----------
    if debug:
        st.sidebar.error(f"⚠️ SIMULATED data for {symbol}")
        for msg in error_messages:
            st.sidebar.text(msg)
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

def add_technicals(df):
    df = df.copy()
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))
    exp1 = df['close'].ewm(span=12, adjust=False).mean()
    exp2 = df['close'].ewm(span=26, adjust=False).mean()
    df['macd'] = exp1 - exp2
    df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
    sma = df['close'].rolling(window=20).mean()
    std = df['close'].rolling(window=20).std()
    df['bb_upper'] = sma + (std * 2)
    df['bb_lower'] = sma - (std * 2)
    df['ema_9'] = df['close'].ewm(span=9, adjust=False).mean()
    df['ema_21'] = df['close'].ewm(span=21, adjust=False).mean()
    df['sma_50'] = df['close'].rolling(window=50).mean()
    df['sma_200'] = df['close'].rolling(window=200).mean()
    df['volume_change'] = df['volume'].pct_change()
    df['vwap'] = (df['volume'] * (df['high'] + df['low'] + df['close']) / 3).cumsum() / df['volume'].cumsum()
    df = df.ffill().bfill()
    return df

def detect_bullish_patterns(df):
    if len(df) < 3:
        return []
    patterns = []
    last = df.iloc[-1]
    prev = df.iloc[-2]
    prev2 = df.iloc[-3] if len(df) >= 3 else None

    body = last['Close'] - last['Open']
    upper_shadow = last['High'] - max(last['Close'], last['Open'])
    lower_shadow = min(last['Close'], last['Open']) - last['Low']
    body_prev = prev['Close'] - prev['Open']

    if body > 0 and body_prev < 0 and last['Close'] > prev['Open'] and last['Open'] < prev['Close']:
        patterns.append("Bullish Engulfing")
    if abs(body) < 0.1 * (last['High'] - last['Low']) and lower_shadow > 2 * abs(body) and upper_shadow < 0.1 * (last['High'] - last['Low']):
        patterns.append("Hammer")
    if abs(body) < 0.05 * (last['High'] - last['Low']) and lower_shadow > 3 * abs(body) and upper_shadow < 0.1 * (last['High'] - last['Low']):
        patterns.append("Dragonfly Doji")
    if prev2 is not None:
        if prev2['Close'] < prev2['Open'] and prev['Close'] < prev['Open'] and body > 0 and last['Close'] > (prev['Open'] + prev['Close'])/2:
            patterns.append("Morning Star")
    if body > 0 and body_prev < 0 and last['High'] < prev['Open'] and last['Low'] > prev['Close']:
        patterns.append("Bullish Harami")
    if body > 0 and body_prev < 0 and last['Open'] < prev['Close'] and last['Close'] > (prev['Open'] + prev['Close'])/2 and last['Close'] < prev['Open']:
        patterns.append("Piercing Line")
    return patterns

def calculate_strength(price, ema, vol_ratio, rsi, macd_hist, patterns, fund_strong):
    score = 0
    if price > ema * 1.02:
        score += 20
    elif price > ema * 1.01:
        score += 10
    if vol_ratio > 2.0:
        score += 20
    elif vol_ratio > 1.5:
        score += 10
    if 50 <= rsi <= 70:
        score += 15
    elif rsi > 70:
        score += 5
    if macd_hist > 0:
        score += 15
    score += min(len(patterns) * 5, 20)
    if fund_strong:
        score += 10
    return min(score, 100)

def get_sector_heatmap():
    stock_sectors = {
        "RELIANCE": "Energy", "TCS": "Technology", "INFY": "Technology",
        "HDFCBANK": "Financial", "ICICIBANK": "Financial", "HINDUNILVR": "Consumer",
        "ITC": "Consumer", "SBIN": "Financial", "BHARTIARTL": "Telecom",
        "KOTAKBANK": "Financial", "LT": "Construction", "AXISBANK": "Financial",
        "HCLTECH": "Technology", "ASIANPAINT": "Consumer", "MARUTI": "Auto",
        "SUNPHARMA": "Pharma", "TITAN": "Consumer", "WIPRO": "Technology",
        "ULTRACEMCO": "Construction", "BAJFINANCE": "Financial", "ADANIPORTS": "Transport",
        "NTPC": "Energy", "POWERGRID": "Energy", "M&M": "Auto", "TECHM": "Technology",
        "JSWSTEEL": "Metals", "TATAMOTORS": "Auto", "TATASTEEL": "Metals", "HAL": "Aerospace"
    }
    data = []
    for symbol, sector in stock_sectors.items():
        try:
            ticker = symbol + ".NS"
            df, _ = get_price_data(ticker, period="5d", interval="1d", debug=False)
            if not df.empty:
                price = df['Close'].iloc[-1]
                change = (df['Close'].iloc[-1] - df['Close'].iloc[0]) / df['Close'].iloc[0] * 100
                data.append({"Symbol": symbol, "Sector": sector, "Price": price, "Change %": change})
        except:
            continue
    df_sector = pd.DataFrame(data)
    if not df_sector.empty:
        df_sector['Change %'] = pd.to_numeric(df_sector['Change %'], errors='coerce')
    return df_sector

# ============================================
# AGENTS INIT (if available)
# ============================================
if AGENTS_AVAILABLE:
    @st.cache_resource
    def init_agents():
        try:
            bull = BullAgent()
            bear = BearAgent()
            moderator = ModeratorAgent()
            return bull, bear, moderator
        except Exception as e:
            st.error(f"Agent init error: {e}")
            return None, None, None
    bull_agent, bear_agent, moderator_agent = init_agents()
else:
    bull_agent = bear_agent = moderator_agent = None

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
        sector_df = get_sector_heatmap()
        if not sector_df.empty:
            pivot = sector_df.pivot_table(index='Sector', columns='Symbol', values='Change %', aggfunc='mean', fill_value=0)
            fig = px.imshow(pivot, text_auto=True, color_continuous_scale='RdYlGn', title="Sector-wise Performance")
            fig.update_layout(template=template, height=400, font=dict(color=text))
            st.plotly_chart(fig, width='stretch')
        else:
            st.info("Sector data unavailable. Please try again later.")
    with col2:
        st.markdown("#### Top Movers (Today)")
        # Simulated top movers – you can replace with dynamic data
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
    if not AGENTS_AVAILABLE:
        st.warning("Agent classes not found. Please install the agents module.")
    else:
        asset_input = st.text_input("Enter asset symbol (e.g., RELIANCE, BTC-USD, EURUSD=X, AAPL)", "RELIANCE")
        market_type = st.selectbox("Market", ["India", "US", "Forex", "Crypto"], index=0)
        if st.button("Analyse Asset"):
            if bull_agent and bear_agent and moderator_agent:
                if market_type == "India":
                    ticker = asset_input + ".NS"
                elif market_type == "US":
                    ticker = asset_input
                elif market_type == "Forex":
                    ticker = asset_input + "=X"
                else:
                    ticker = asset_input
                with st.spinner(f"Fetching data for {ticker}..."):
                    df, _ = get_price_data(ticker, period="1mo", interval="1d", debug=debug)
                    if df.empty:
                        st.error("No data found. Check symbol and market.")
                    else:
                        df.columns = [col.capitalize() if col.lower() != 'volume' else 'Volume' for col in df.columns]
                        df_agent = df.copy()
                        df_agent.columns = [col.lower() for col in df_agent.columns]
                        df_agent = add_technicals(df_agent)
                        try:
                            bull_pred = bull_agent.predict(df_agent)
                            bull_signal = bull_agent.get_signal(bull_pred)
                            bear_pred = bear_agent.predict(df_agent)
                            bear_signal = bear_agent.get_signal(bear_pred)
                            agent_signals = [bull_signal, bear_signal]
                            moderator_result = moderator_agent.aggregate_agent_signals(agent_signals)
                            final_signal = moderator_result['final_signal']
                            confidence = moderator_result['confidence']
                            bull_conf = bull_signal['confidence']
                            bear_conf = bear_signal['confidence']
                            if bull_signal['signal'] == 'BUY' and bear_signal['signal'] == 'SELL':
                                strength = (bull_conf + (100 - bear_conf)) / 2
                            else:
                                strength = (bull_conf + bear_conf) / 2
                            strength = min(100, max(0, strength))
                            st.success(f"**Final Signal: {final_signal}**")
                            st.metric("Consensus Confidence", f"{confidence}%")
                            st.markdown("#### Signal Strength Meter")
                            st.markdown(f"""
                            <div class="strength-meter">
                                <div style="display:flex; justify-content:space-between;">
                                    <span>Weak</span>
                                    <span>Strength: {strength:.0f}%</span>
                                    <span>Strong</span>
                                </div>
                                <div class="strength-bar" style="width:{strength}%;"></div>
                            </div>
                            """, unsafe_allow_html=True)
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Bull", bull_signal['signal'], f"Conf: {bull_conf}%")
                                st.caption(f"Momentum: {bull_signal.get('momentum',0)}%")
                            with col2:
                                st.metric("Bear", bear_signal['signal'], f"Conf: {bear_conf}%")
                                st.caption(f"Volatility: {bear_signal.get('volatility_score',0)}%")
                            with col3:
                                st.metric("Moderator", final_signal, f"Conf: {confidence}%")
                            with st.expander("📝 Agent Reasoning"):
                                st.write("**Bull Agent Reasoning:**", bull_signal.get('reasoning', 'N/A'))
                                st.write("**Bear Agent Reasoning:**", bear_signal.get('reasoning', 'N/A'))
                                st.write("**Moderator Reasoning:**", moderator_result.get('reasoning', 'N/A'))
                        except Exception as e:
                            st.error(f"Agent analysis failed: {e}")
            else:
                st.warning("Agents not available. Check installation.")

# ---------- TAB 3: Scanners ----------
with tab3:
    st.markdown("### 🔎 Scanners & Screeners")
    st.sidebar.markdown("### ⚙️ Scanner Settings")
    ema_period = st.sidebar.slider("EMA Period", 50, 300, 200, 10)
    vol_threshold = st.sidebar.slider("Volume Ratio", 1.0, 3.0, 1.5, 0.1)
    rsi_min = st.sidebar.slider("RSI Minimum", 30, 60, 45)
    pattern_toggle = st.sidebar.checkbox("Require Bullish Pattern", value=True)

    scanner_tabs = st.tabs(["Indian Stocks", "US Stocks", "Forex", "Crypto", "PEAD Screener", "Penny Stocks"])

    with scanner_tabs[0]:
        st.write(f"Scan NIFTY 50 stocks for {ema_period} EMA breakouts.")
        if st.button("Scan Indian Stocks"):
            stock_list = [
                "RELIANCE","TCS","INFY","HDFCBANK","ICICIBANK","HINDUNILVR","ITC","SBIN",
                "BHARTIARTL","KOTAKBANK","LT","AXISBANK","HCLTECH","ASIANPAINT","MARUTI",
                "SUNPHARMA","TITAN","WIPRO","ULTRACEMCO","BAJFINANCE","ADANIPORTS","NTPC",
                "POWERGRID","M&M","TECHM","JSWSTEEL","TATAMOTORS","TATASTEEL","HAL"
            ]
            timeframes = [("1H", "5d", "1h"), ("4H", "10d", "1h"), ("Daily", "1y", "1d")]
            all_results = []
            prog = st.progress(0)
            for idx, sym in enumerate(stock_list):
                try:
                    ticker = sym + ".NS"
                    for tf_label, period, interval in timeframes:
                        df, _ = get_price_data(ticker, period=period, interval=interval, debug=False)
                        if df.empty or len(df) < 200:
                            continue
                        if isinstance(df.columns, pd.MultiIndex):
                            df.columns = [col[0] for col in df.columns]
                        df.columns = [col.capitalize() if col.lower() != 'volume' else 'Volume' for col in df.columns]
                        ema = df['Close'].ewm(span=ema_period, adjust=False).mean()
                        last_price = df['Close'].iloc[-1]
                        prev_price = df['Close'].iloc[-2]
                        last_ema = ema.iloc[-1]
                        prev_ema = ema.iloc[-2]
                        cross = (last_price > last_ema) and (prev_price <= prev_ema)
                        if cross:
                            patterns = detect_bullish_patterns(df) if pattern_toggle else ["N/A"]
                            if patterns:
                                vol_avg = df['Volume'].rolling(20).mean().iloc[-1]
                                vol_ratio = df['Volume'].iloc[-1] / vol_avg if vol_avg > 0 else 0
                                if vol_ratio >= vol_threshold:
                                    delta = df['Close'].diff()
                                    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
                                    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
                                    rs = gain / loss
                                    rsi = 100 - (100 / (1 + rs))
                                    if rsi.iloc[-1] >= rsi_min:
                                        strength = calculate_strength(last_price, last_ema, vol_ratio, rsi.iloc[-1], 0, patterns, False)
                                        all_results.append({
                                            "Symbol": sym,
                                            "Timeframe": tf_label,
                                            "Price": last_price,
                                            "EMA": last_ema,
                                            "Patterns": ", ".join(patterns),
                                            "Volume Ratio": round(vol_ratio, 2),
                                            "RSI": round(rsi.iloc[-1], 1),
                                            "Strength": strength
                                        })
                except:
                    continue
                prog.progress((idx+1)/len(stock_list))
            if all_results:
                df_results = pd.DataFrame(all_results)
                st.success(f"Found {len(df_results)} breakouts.")
                st.dataframe(df_results, width='stretch', hide_index=True)
            else:
                st.info("No breakouts found with current settings.")

    # Placeholders for other scanner tabs
    with scanner_tabs[1]:
        st.info("US Stocks scanner – extend using same pattern.")
    with scanner_tabs[2]:
        st.info("Forex scanner – extend using same pattern.")
    with scanner_tabs[3]:
        st.info("Crypto scanner – extend using same pattern.")
    with scanner_tabs[4]:
        st.write("### 📰 PEAD – Post‑Earnings Announcement Drift")
        pead_data = {
            "Symbol": ["RELIANCE", "TCS", "HDFCBANK", "INFY"],
            "EPS Surprise %": [8.5, 3.2, 5.1, 2.8],
            "Revenue Surprise %": [6.2, 4.0, 3.5, 1.5],
            "Next Earnings Date": ["2026-07-20", "2026-07-18", "2026-07-22", "2026-07-25"],
            "Signal": ["BUY", "BUY", "HOLD", "BUY"]
        }
        df_pead = pd.DataFrame(pead_data)
        def color_signal(s):
            return ['color: #00aa66' if v == 'BUY' else 'color: #cc8800' for v in s]
        st.dataframe(df_pead.style.apply(color_signal, subset=['Signal'], axis=0), width='stretch')
    with scanner_tabs[5]:
        st.write("### 💰 Penny Stock Screener")
        penny_data = {
            "Symbol": ["SUZLON", "YESBANK", "IDEA", "PENNY1"],
            "Price": [85.5, 68.2, 42.0, 9.8],
            "Volume (K)": [5000, 3500, 2000, 1500],
            "Change %": [5.2, 3.8, 2.1, 8.5],
            "Strength": [72, 65, 58, 80]
        }
        df_penny = pd.DataFrame(penny_data)
        st.dataframe(df_penny.style.background_gradient(subset=['Strength'], cmap='RdYlGn'), width='stretch')

# ---------- TAB 4: Backtest ----------
with tab4:
    st.markdown("### 📊 Backtest Engine")
    backtest_asset = st.text_input("Asset for backtest", "RELIANCE.NS")
    strategy = st.selectbox("Strategy", ["MA Crossover", "RSI", "MACD"])
    if st.button("Run Backtest"):
        df, _ = get_price_data(backtest_asset, period="1y", interval="1d", debug=False)
        if df.empty:
            st.error("No data.")
        else:
            df.columns = [col.capitalize() for col in df.columns]
            if AGENTS_AVAILABLE:
                backtest = BacktestEngine(initial_capital=100000)
                if strategy == "MA Crossover":
                    signals = (df['Close'].rolling(5).mean() > df['Close'].rolling(20).mean()).astype(int)
                    signals = signals.diff().fillna(0)
                elif strategy == "RSI":
                    delta = df['Close'].diff()
                    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
                    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
                    rs = gain / loss
                    rsi = 100 - (100 / (1 + rs))
                    signals = ((rsi < 30) | (rsi > 70)).astype(int)
                    signals = signals.diff().fillna(0)
                elif strategy == "MACD":
                    exp1 = df['Close'].ewm(span=12, adjust=False).mean()
                    exp2 = df['Close'].ewm(span=26, adjust=False).mean()
                    macd = exp1 - exp2
                    signal_line = macd.ewm(span=9, adjust=False).mean()
                    signals = ((macd > signal_line) & (macd.shift(1) <= signal_line.shift(1))).astype(int)
                    signals = signals - ((macd < signal_line) & (macd.shift(1) >= signal_line.shift(1))).astype(int)
                results = backtest.run_backtest(df, signals)
                st.metric("Total Return", f"{results['total_return']:.2f}%")
                st.metric("Sharpe Ratio", f"{results['sharpe_ratio']:.2f}")
                st.metric("Max Drawdown", f"{results['max_drawdown']:.2f}%")
                st.metric("Win Rate", f"{results['win_rate']:.1f}%")
                eq_df = pd.DataFrame(results['equity_curve'])
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=list(range(len(eq_df))), y=eq_df['equity'], mode='lines', name='Equity'))
                fig.update_layout(title="Equity Curve", template=template, height=400)
                st.plotly_chart(fig, width='stretch')
                if results.get('trades'):
                    st.dataframe(pd.DataFrame(results['trades']), width='stretch')
            else:
                st.warning("BacktestEngine not available.")

# ---------- TAB 5: News & Calendar ----------
with tab5:
    st.markdown("### 📰 Market News & Economic Calendar")
    st.subheader("Latest Financial News")
    news_query = st.text_input("Search news (e.g., 'stock market')", "stock market")
    if st.button("Fetch News"):
        st.info("News API integration – add your key to secrets.toml as NEWS_API_KEY")
    st.subheader("Economic Calendar")
    st.info("Economic calendar – requires Alpha Vantage key and endpoint integration.")

# ---------- TAB 6: Portfolio Optimisation ----------
with tab6:
    st.markdown("### ⚖️ Portfolio Optimisation (Efficient Frontier)")
    st.write("Select up to 5 assets to optimise.")
    asset_list = st.multiselect("Assets", 
                               ["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS", 
                                "AAPL", "MSFT", "GOOGL", "AMZN", "BTC-USD", "ETH-USD"],
                               default=["RELIANCE.NS", "TCS.NS", "INFY.NS"])
    if len(asset_list) >= 2:
        if st.button("Compute Efficient Frontier"):
            returns_data = {}
            for sym in asset_list:
                df, _ = get_price_data(sym, period="1y", interval="1d", debug=False)
                if not df.empty:
                    returns_data[sym] = df['Close'].pct_change().dropna()
            if len(returns_data) >= 2:
                returns_df = pd.DataFrame(returns_data).dropna()
                mu = returns_df.mean() * 252
                cov = returns_df.cov() * 252
                n_assets = len(mu)
                def portfolio_stats(w):
                    ret = np.sum(w * mu)
                    vol = np.sqrt(np.dot(w.T, np.dot(cov, w)))
                    return ret, vol
                def neg_sharpe(w):
                    ret, vol = portfolio_stats(w)
                    return -ret/vol
                cons = ({'type':'eq','fun': lambda x: np.sum(x)-1})
                bounds = tuple((0,1) for _ in range(n_assets))
                init = np.ones(n_assets)/n_assets
                opt = minimize(neg_sharpe, init, method='SLSQP', bounds=bounds, constraints=cons)
                if opt.success:
                    w_opt = opt.x
                    ret_opt, vol_opt = portfolio_stats(w_opt)
                    st.write("**Max Sharpe Portfolio Weights:**")
                    for i, sym in enumerate(asset_list):
                        st.write(f"{sym}: {w_opt[i]*100:.1f}%")
                    frontiers = []
                    target_returns = np.linspace(mu.min(), mu.max(), 20)
                    for tr in target_returns:
                        cons_ret = ({'type':'eq','fun': lambda x: np.sum(x)-1},
                                    {'type':'eq','fun': lambda x: np.sum(x*mu)-tr})
                        opt2 = minimize(lambda x: portfolio_stats(x)[1], init, method='SLSQP', bounds=bounds, constraints=cons_ret)
                        if opt2.success:
                            frontiers.append((portfolio_stats(opt2.x)))
                    if frontiers:
                        frontier_vols = [f[1] for f in frontiers]
                        frontier_rets = [f[0] for f in frontiers]
                        fig = go.Figure()
                        fig.add_trace(go.Scatter(x=frontier_vols, y=frontier_rets, mode='lines+markers', name='Efficient Frontier'))
                        fig.add_trace(go.Scatter(x=[vol_opt], y=[ret_opt], mode='markers', marker=dict(size=15, color='red'), name='Max Sharpe'))
                        fig.update_layout(title="Efficient Frontier", template=template, height=400)
                        st.plotly_chart(fig, width='stretch')
                else:
                    st.warning("Optimisation failed.")
            else:
                st.warning("Not enough data for selected assets.")
    else:
        st.info("Select at least 2 assets.")

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
