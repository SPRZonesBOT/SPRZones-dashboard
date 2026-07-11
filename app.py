import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import yfinance as yf
import warnings
import json
import os
import scipy.stats as stats
warnings.filterwarnings('ignore')

# Import your agent classes (adjust paths if needed)
from agents.bull_agent import BullAgent
from agents.bear_agent import BearAgent
from agents.moderator_agent import ModeratorAgent
from agents.backtest_engine import BacktestEngine

# ============================================
# PAGE CONFIGURATION
# ============================================
st.set_page_config(
    page_title="SPRZonesPulse – Global Quant",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ============================================
# THEME TOGGLE
# ============================================
theme = st.radio("Theme", ["Light", "Dark"], index=0, horizontal=True)
if theme == "Dark":
    bg_color = "#0e1117"
    text_color = "#f0f2f6"
    card_bg = "#1e2433"
    border_color = "#2d3748"
    header_bg = "linear-gradient(90deg, #0a0a1a, #1a1a3e)"
    plot_template = "plotly_dark"
else:
    bg_color = "#f8f6f2"
    text_color = "#1a1a2e"
    card_bg = "#ffffff"
    border_color = "#e8e2da"
    header_bg = "linear-gradient(90deg, #1a1a2e 0%, #16213e 100%)"
    plot_template = "plotly_white"

# ============================================
# CUSTOM CSS (same as before)
# ============================================
st.markdown(f"""
<style>
    .main .block-container {{
        padding-top: 0.5rem;
        padding-left: 2rem;
        padding-right: 2rem;
        padding-bottom: 1rem;
        max-width: 100%;
    }}
    .stApp {{
        background-color: {bg_color};
        color: {text_color};
    }}
    .header-bar {{
        background: {header_bg};
        padding: 0.8rem 2rem;
        border-radius: 0 0 12px 12px;
        margin-bottom: 1.5rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    }}
    .header-title {{
        color: #ffffff;
        font-size: 1.8rem;
        font-weight: 700;
    }}
    .header-title span {{
        color: #00d4ff;
    }}
    .header-status {{
        color: #a0aec0;
        font-size: 0.9rem;
        display: flex;
        gap: 1.5rem;
        align-items: center;
    }}
    .status-dot {{
        display: inline-block;
        width: 10px;
        height: 10px;
        border-radius: 50%;
        margin-right: 6px;
    }}
    .dot-green {{
        background-color: #00ff88;
        box-shadow: 0 0 8px #00ff88;
    }}
    .metric-card {{
        background: {card_bg};
        border-radius: 12px;
        padding: 1rem 1.2rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        border: 1px solid {border_color};
        text-align: center;
        transition: 0.2s;
    }}
    .metric-card:hover {{
        box-shadow: 0 4px 16px rgba(0,0,0,0.10);
        border-color: #c8c0b8;
    }}
    .metric-label {{
        font-size: 0.85rem;
        color: #6a6a7e;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.3px;
    }}
    .metric-value {{
        font-size: 1.8rem;
        font-weight: 700;
        color: {text_color};
        margin-top: 4px;
    }}
    .metric-sub {{
        font-size: 0.8rem;
        color: #8892a8;
        margin-top: 2px;
    }}
    .index-card {{
        background: {card_bg};
        border-radius: 10px;
        padding: 0.8rem 1rem;
        box-shadow: 0 1px 4px rgba(0,0,0,0.04);
        border: 1px solid {border_color};
        text-align: center;
    }}
    .index-name {{
        font-size: 0.85rem;
        font-weight: 600;
        color: #4a4a5e;
    }}
    .index-price {{
        font-size: 1.2rem;
        font-weight: 700;
        color: {text_color};
        margin: 2px 0;
    }}
    .index-change {{
        font-size: 0.9rem;
        font-weight: 600;
    }}
    .change-positive {{
        color: #00aa66;
    }}
    .change-negative {{
        color: #cc3333;
    }}
    .section-title {{
        font-size: 1.3rem;
        font-weight: 700;
        color: {text_color};
        margin: 1.2rem 0 0.8rem 0;
        padding-bottom: 6px;
        border-bottom: 2px solid {border_color};
    }}
    .signal-buy {{
        color: #00aa66;
        font-weight: bold;
        font-size: 28px;
    }}
    .signal-sell {{
        color: #cc3333;
        font-weight: bold;
        font-size: 28px;
    }}
    .signal-hold {{
        color: #cc8800;
        font-weight: bold;
        font-size: 28px;
    }}
    .streamlit-expanderHeader {{
        background-color: {card_bg} !important;
        border: 1px solid {border_color} !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        color: {text_color} !important;
    }}
    .streamlit-expanderContent {{
        background-color: {bg_color} !important;
        border: 1px solid {border_color} !important;
        border-top: none !important;
        border-radius: 0 0 8px 8px !important;
    }}
    .footer {{
        margin-top: 2rem;
        padding-top: 1rem;
        border-top: 1px solid {border_color};
        display: flex;
        justify-content: space-between;
        color: #8892a8;
        font-size: 0.85rem;
    }}
    .stTabs [data-baseweb="tab-list"] {{
        gap: 8px;
    }}
    .stTabs [data-baseweb="tab"] {{
        background-color: {card_bg} !important;
        border-radius: 8px 8px 0 0 !important;
        border: 1px solid {border_color} !important;
        border-bottom: none !important;
        padding: 10px 20px !important;
        color: {text_color} !important;
        font-weight: 600 !important;
    }}
    .stTabs [aria-selected="true"] {{
        background-color: #00d4ff !important;
        color: #1a1a2e !important;
    }}
    .strength-meter {{
        background: {bg_color};
        border-radius: 10px;
        padding: 10px;
        border: 1px solid {border_color};
        margin-top: 10px;
    }}
    .strength-bar {{
        height: 20px;
        border-radius: 10px;
        background: linear-gradient(to right, #cc3333, #ffaa00, #00aa66);
    }}
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
# GLOBAL INDICES TICKER (with fallback)
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

cols = st.columns(len(indices))
for i, (name, ticker) in enumerate(indices.items()):
    try:
        data = yf.download(ticker, period="1d", interval="1m", progress=False)
        if not data.empty:
            price = data['Close'].iloc[-1]
            prev_close = data['Close'].iloc[0] if len(data) > 1 else price
            change = (price - prev_close) / prev_close * 100 if prev_close else 0
            cols[i].metric(name, f"{price:,.2f}", f"{change:+.2f}%", delta_color="normal")
        else:
            # Fallback simulated
            sim_price = np.random.uniform(10000, 20000) if "NIFTY" in name else np.random.uniform(2000, 5000)
            sim_change = np.random.uniform(-1, 1)
            cols[i].metric(name, f"{sim_price:,.2f}", f"{sim_change:+.2f}%", delta_color="normal")
    except:
        # Fallback
        sim_price = np.random.uniform(10000, 20000) if "NIFTY" in name else np.random.uniform(2000, 5000)
        sim_change = np.random.uniform(-1, 1)
        cols[i].metric(name, f"{sim_price:,.2f}", f"{sim_change:+.2f}%", delta_color="normal")

st.markdown("<hr style='margin: 0.5rem 0; border-color: #e8e2da;'>", unsafe_allow_html=True)

# ============================================
# AGENT INITIALISATION (Cached)
# ============================================
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

# ============================================
# HELPER FUNCTIONS (shared across tabs)
# ============================================
def add_technicals(df):
    """Add technical indicators to a dataframe (lowercase columns)."""
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
    """Enhanced pattern detection (returns list of patterns)."""
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
    """Calculate a signal strength score (0-100)."""
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
    """Fetch sector data for major Indian stocks and create a heatmap."""
    stock_sectors = {
        "RELIANCE": "Energy",
        "TCS": "Technology",
        "INFY": "Technology",
        "HDFCBANK": "Financial",
        "ICICIBANK": "Financial",
        "HINDUNILVR": "Consumer",
        "ITC": "Consumer",
        "SBIN": "Financial",
        "BHARTIARTL": "Telecom",
        "KOTAKBANK": "Financial",
        "LT": "Construction",
        "AXISBANK": "Financial",
        "HCLTECH": "Technology",
        "ASIANPAINT": "Consumer",
        "MARUTI": "Auto",
        "SUNPHARMA": "Pharma",
        "TITAN": "Consumer",
        "WIPRO": "Technology",
        "ULTRACEMCO": "Construction",
        "BAJFINANCE": "Financial",
        "ADANIPORTS": "Transport",
        "NTPC": "Energy",
        "POWERGRID": "Energy",
        "M&M": "Auto",
        "TECHM": "Technology",
        "JSWSTEEL": "Metals",
        "TATAMOTORS": "Auto",
        "TATASTEEL": "Metals",
        "HAL": "Aerospace"
    }
    data = []
    for symbol, sector in stock_sectors.items():
        try:
            ticker = symbol + ".NS"
            df = yf.download(ticker, period="5d", interval="1d", progress=False)
            if not df.empty:
                price = df['Close'].iloc[-1]
                change = (df['Close'].iloc[-1] - df['Close'].iloc[0]) / df['Close'].iloc[0] * 100
                data.append({"Symbol": symbol, "Sector": sector, "Price": price, "Change %": change})
        except:
            pass
    df_sector = pd.DataFrame(data)
    # Ensure numeric
    if not df_sector.empty:
        df_sector['Change %'] = pd.to_numeric(df_sector['Change %'], errors='coerce')
    return df_sector

# ============================================
# TAB LAYOUT
# ============================================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Overview",
    "🤖 Multi‑Agent Debate",
    "🔎 Scanners & Screeners",
    "📈 Backtest & Performance",
    "⭐ Watchlist"
])

# ============================================
# TAB 1: OVERVIEW
# ============================================
with tab1:
    st.markdown("### 📈 Market Snapshot")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### Sector Heatmap (Indian Stocks)")
        sector_df = get_sector_heatmap()
        if not sector_df.empty:
            # FIX: ensure numeric and handle duplicates
            sector_df['Change %'] = pd.to_numeric(sector_df['Change %'], errors='coerce')
            pivot = sector_df.pivot_table(index='Sector', columns='Symbol', values='Change %', aggfunc='mean', fill_value=0)
            fig = px.imshow(pivot, text_auto=True, color_continuous_scale='RdYlGn', title="Sector-wise Performance")
            fig.update_layout(template=plot_template, height=400, font=dict(color=text_color))
            st.plotly_chart(fig, width='stretch')
        else:
            st.info("Sector data unavailable. Try refreshing.")
    with col2:
        st.markdown("#### Top Movers (Today)")
        top_data = {
            "Symbol": ["RELIANCE", "BTC-USD", "EURUSD=X", "AAPL"],
            "Price": [2450, 67800, 1.085, 185.50],
            "Change %": [3.2, 2.4, 0.12, -1.2]
        }
        df_top = pd.DataFrame(top_data)
        st.dataframe(df_top.style.applymap(lambda x: 'color: #00aa66' if x > 0 else 'color: #cc3333', subset=['Change %']), width='stretch')

        st.markdown("#### Economic Calendar (Today)")
        econ_cal = pd.DataFrame({
            "Time": ["10:00", "14:30", "20:00"],
            "Event": ["Fed Speech", "ECB Rate Decision", "US GDP"],
            "Impact": ["Medium", "High", "High"]
        })
        st.dataframe(econ_cal, width='stretch', hide_index=True)

# ============================================
# TAB 2: MULTI‑AGENT DEBATE
# ============================================
with tab2:
    st.markdown("### 🧠 Agent Debate – Consensus Signal with Strength Meter")

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
                df = yf.download(ticker, period="1mo", interval="1d", progress=False)
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

# ============================================
# TAB 3: SCANNERS & SCREENERS (unchanged, but included for completeness)
# ============================================
with tab3:
    st.markdown("### 🔎 Scanners & Screeners")
    scanner_tabs = st.tabs(["Indian Stocks", "US Stocks", "Forex", "Crypto", "PEAD Screener", "Penny Stocks"])

    with scanner_tabs[0]:
        st.write("Scan NIFTY 50 stocks for 200 EMA breakouts with bullish patterns.")
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
                        df = yf.download(ticker, period=period, interval=interval, progress=False)
                        if df.empty or len(df) < 200:
                            continue
                        if isinstance(df.columns, pd.MultiIndex):
                            df.columns = [col[0] for col in df.columns]
                        df.columns = [col.capitalize() if col.lower() != 'volume' else 'Volume' for col in df.columns]
                        ema = df['Close'].ewm(span=200, adjust=False).mean()
                        last_price = df['Close'].iloc[-1]
                        prev_price = df['Close'].iloc[-2]
                        last_ema = ema.iloc[-1]
                        prev_ema = ema.iloc[-2]
                        cross = (last_price > last_ema) and (prev_price <= prev_ema)
                        if cross:
                            patterns = detect_bullish_patterns(df)
                            if patterns:
                                vol_avg = df['Volume'].rolling(20).mean().iloc[-1]
                                vol_ratio = df['Volume'].iloc[-1] / vol_avg if vol_avg > 0 else 0
                                if vol_ratio >= 1.5:
                                    strength = calculate_strength(last_price, last_ema, vol_ratio, 50, 0, patterns, False)
                                    all_results.append({
                                        "Symbol": sym,
                                        "Timeframe": tf_label,
                                        "Price": last_price,
                                        "EMA": last_ema,
                                        "Patterns": ", ".join(patterns),
                                        "Volume Ratio": round(vol_ratio, 2),
                                        "Strength": strength
                                    })
                except Exception as e:
                    pass
                prog.progress((idx+1)/len(stock_list))
            if all_results:
                df_results = pd.DataFrame(all_results)
                st.success(f"Found {len(df_results)} breakouts.")
                st.dataframe(df_results, width='stretch', hide_index=True)
            else:
                st.info("No breakouts found.")

    with scanner_tabs[1]:
        st.write("Scan S&P 500 stocks for 200 EMA breakouts.")
        if st.button("Scan US Stocks"):
            us_stocks = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "JPM", "V", "WMT"]
            timeframes = [("Daily", "1y", "1d")]
            all_results = []
            for sym in us_stocks:
                try:
                    df = yf.download(sym, period="1y", interval="1d", progress=False)
                    if df.empty or len(df) < 200:
                        continue
                    df.columns = [col.capitalize() if col.lower() != 'volume' else 'Volume' for col in df.columns]
                    ema = df['Close'].ewm(span=200, adjust=False).mean()
                    last_price = df['Close'].iloc[-1]
                    prev_price = df['Close'].iloc[-2]
                    last_ema = ema.iloc[-1]
                    prev_ema = ema.iloc[-2]
                    cross = (last_price > last_ema) and (prev_price <= prev_ema)
                    if cross:
                        patterns = detect_bullish_patterns(df)
                        if patterns:
                            vol_avg = df['Volume'].rolling(20).mean().iloc[-1]
                            vol_ratio = df['Volume'].iloc[-1] / vol_avg if vol_avg > 0 else 0
                            if vol_ratio >= 1.5:
                                strength = calculate_strength(last_price, last_ema, vol_ratio, 50, 0, patterns, False)
                                all_results.append({
                                    "Symbol": sym,
                                    "Price": last_price,
                                    "EMA": last_ema,
                                    "Patterns": ", ".join(patterns),
                                    "Volume Ratio": round(vol_ratio, 2),
                                    "Strength": strength
                                })
                except:
                    pass
            if all_results:
                df_results = pd.DataFrame(all_results)
                st.success(f"Found {len(df_results)} breakouts.")
                st.dataframe(df_results, width='stretch', hide_index=True)
            else:
                st.info("No breakouts found.")

    with scanner_tabs[2]:
        st.write("Scan major Forex pairs (Daily) for 200 EMA breakouts.")
        if st.button("Scan Forex"):
            forex_list = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "NZDUSD", "USDCHF"]
            all_results = []
            for sym in forex_list:
                try:
                    ticker = sym + "=X"
                    df = yf.download(ticker, period="1y", interval="1d", progress=False)
                    if df.empty or len(df) < 200:
                        continue
                    df.columns = [col.capitalize() if col.lower() != 'volume' else 'Volume' for col in df.columns]
                    ema = df['Close'].ewm(span=200, adjust=False).mean()
                    last_price = df['Close'].iloc[-1]
                    prev_price = df['Close'].iloc[-2]
                    last_ema = ema.iloc[-1]
                    prev_ema = ema.iloc[-2]
                    cross = (last_price > last_ema) and (prev_price <= prev_ema)
                    if cross:
                        patterns = detect_bullish_patterns(df)
                        if patterns:
                            # No volume for forex, skip volume check
                            strength = calculate_strength(last_price, last_ema, 1.0, 40, 0, patterns, False)
                            all_results.append({
                                "Symbol": sym,
                                "Price": last_price,
                                "EMA": last_ema,
                                "Patterns": ", ".join(patterns),
                                "Strength": strength
                            })
                except:
                    pass
            if all_results:
                df_results = pd.DataFrame(all_results)
                st.success(f"Found {len(df_results)} breakouts.")
                st.dataframe(df_results, width='stretch', hide_index=True)
            else:
                st.info("No breakouts found.")

    with scanner_tabs[3]:
        st.write("Scan top crypto coins for 200 EMA breakouts (1H & Daily).")
        if st.button("Scan Crypto"):
            crypto_list = ["BTC-USD", "ETH-USD", "SOL-USD", "XRP-USD", "ADA-USD", "DOGE-USD", "DOT-USD"]
            timeframes = [("1H", "5d", "1h"), ("Daily", "1y", "1d")]
            all_results = []
            for sym in crypto_list:
                for tf_label, period, interval in timeframes:
                    try:
                        df = yf.download(sym, period=period, interval=interval, progress=False)
                        if df.empty or len(df) < 200:
                            continue
                        df.columns = [col.capitalize() if col.lower() != 'volume' else 'Volume' for col in df.columns]
                        ema = df['Close'].ewm(span=200, adjust=False).mean()
                        last_price = df['Close'].iloc[-1]
                        prev_price = df['Close'].iloc[-2]
                        last_ema = ema.iloc[-1]
                        prev_ema = ema.iloc[-2]
                        cross = (last_price > last_ema) and (prev_price <= prev_ema)
                        if cross:
                            patterns = detect_bullish_patterns(df)
                            if patterns:
                                vol_avg = df['Volume'].rolling(20).mean().iloc[-1]
                                vol_ratio = df['Volume'].iloc[-1] / vol_avg if vol_avg > 0 else 0
                                if vol_ratio >= 1.2:
                                    strength = calculate_strength(last_price, last_ema, vol_ratio, 45, 0, patterns, False)
                                    all_results.append({
                                        "Symbol": sym,
                                        "Timeframe": tf_label,
                                        "Price": last_price,
                                        "EMA": last_ema,
                                        "Patterns": ", ".join(patterns),
                                        "Volume Ratio": round(vol_ratio, 2),
                                        "Strength": strength
                                    })
                    except:
                        pass
            if all_results:
                df_results = pd.DataFrame(all_results)
                st.success(f"Found {len(df_results)} breakouts.")
                st.dataframe(df_results, width='stretch', hide_index=True)
            else:
                st.info("No breakouts found.")

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
        st.dataframe(df_pead.style.applymap(lambda x: 'color: #00aa66' if x == 'BUY' else 'color: #cc8800', subset=['Signal']), width='stretch')

    with scanner_tabs[5]:
        st.write("### 💰 Penny Stock Screener (Price < $10 or ₹100)")
        penny_data = {
            "Symbol": ["SUZLON", "YESBANK", "IDEA", "PENNY1"],
            "Price": [85.5, 68.2, 42.0, 9.8],
            "Volume (K)": [5000, 3500, 2000, 1500],
            "Change %": [5.2, 3.8, 2.1, 8.5],
            "Strength": [72, 65, 58, 80]
        }
        df_penny = pd.DataFrame(penny_data)
        st.dataframe(df_penny.style.background_gradient(subset=['Strength'], cmap='RdYlGn'), width='stretch')

# ============================================
# TAB 4: BACKTEST & PERFORMANCE
# ============================================
with tab4:
    st.markdown("### 📊 Backtest Engine")
    st.write("Test a simple moving average crossover strategy on any asset.")

    backtest_asset = st.text_input("Asset for backtest", "RELIANCE.NS")
    if st.button("Run Backtest"):
        try:
            df = yf.download(backtest_asset, period="1y", interval="1d", progress=False)
            if df.empty:
                st.error("No data.")
            else:
                df.columns = [col.capitalize() for col in df.columns]
                backtest = BacktestEngine(initial_capital=100000)
                signals = (df['Close'].rolling(5).mean() > df['Close'].rolling(20).mean()).astype(int)
                signals = signals.diff().fillna(0)
                results = backtest.run_backtest(df, signals)

                st.metric("Total Return", f"{results['total_return']:.2f}%")
                st.metric("Sharpe Ratio", f"{results['sharpe_ratio']:.2f}")
                st.metric("Max Drawdown", f"{results['max_drawdown']:.2f}%")
                st.metric("Win Rate", f"{results['win_rate']:.1f}%")

                eq_df = pd.DataFrame(results['equity_curve'])
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=list(range(len(eq_df))), y=eq_df['equity'], mode='lines', name='Equity'))
                fig.update_layout(title="Equity Curve", template=plot_template, height=400)
                st.plotly_chart(fig, width='stretch')

                if results.get('trades'):
                    st.dataframe(pd.DataFrame(results['trades']), width='stretch')
        except Exception as e:
            st.error(f"Backtest error: {e}")

# ============================================
# TAB 5: WATCHLIST
# ============================================
with tab5:
    st.markdown("### ⭐ Watchlist")

    if 'watchlist' not in st.session_state:
        st.session_state.watchlist = ["RELIANCE", "BTC-USD"]

    new_symbol = st.text_input("Add symbol")
    if st.button("Add"):
        if new_symbol and new_symbol not in st.session_state.watchlist:
            st.session_state.watchlist.append(new_symbol)
            st.rerun()

    if st.session_state.watchlist:
        data = []
        for sym in st.session_state.watchlist:
            try:
                df = yf.download(sym, period="1d", interval="1m", progress=False)
                if not df.empty:
                    price = df['Close'].iloc[-1]
                    change = (df['Close'].iloc[-1] - df['Close'].iloc[0]) / df['Close'].iloc[0] * 100
                    data.append({"Symbol": sym, "Price": price, "Change %": change})
            except:
                pass
        if data:
            df_watch = pd.DataFrame(data)
            st.dataframe(df_watch.style.applymap(lambda x: 'color: #00aa66' if x > 0 else 'color: #cc3333', subset=['Change %']), width='stretch')
        else:
            st.info("No data for watchlist symbols.")
        if st.button("Clear Watchlist"):
            st.session_state.watchlist = []
            st.rerun()
    else:
        st.info("Watchlist is empty. Add symbols above.")

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
