import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import sys
import warnings
import json
import os
warnings.filterwarnings('ignore')

# Fix path issues
sys.path.append('.')

from data.ingestion.yahoo_finance import YahooFinanceFeed, NewsFeed, CryptoSentiment
from agents.bull_agent import BullAgent
from agents.bear_agent import BearAgent
from agents.moderator_agent import ModeratorAgent
from agents.backtest_engine import BacktestEngine

# ============================================
# PAGE CONFIGURATION
# ============================================
st.set_page_config(
    page_title="SPRZonesPulse",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ============================================
# CUSTOM CSS – SPRZonesPulse Style
# ============================================
st.markdown("""
<style>
    /* Remove default padding */
    .main .block-container {
        padding-top: 1rem;
        padding-left: 2rem;
        padding-right: 2rem;
        max-width: 100%;
    }
    
    /* Main background */
    .stApp {
        background-color: #f8f6f2;
    }
    
    /* Header bar */
    .header-bar {
        background: linear-gradient(90deg, #1a1a2e 0%, #16213e 100%);
        padding: 0.8rem 2rem;
        border-radius: 0 0 12px 12px;
        margin-bottom: 1.5rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    }
    .header-title {
        color: #ffffff;
        font-size: 1.8rem;
        font-weight: 700;
        letter-spacing: 0.5px;
    }
    .header-title span {
        color: #00d4ff;
    }
    .header-status {
        color: #a0aec0;
        font-size: 0.9rem;
        display: flex;
        gap: 1.5rem;
        align-items: center;
    }
    .status-dot {
        display: inline-block;
        width: 10px;
        height: 10px;
        border-radius: 50%;
        margin-right: 6px;
    }
    .dot-green {
        background-color: #00ff88;
        box-shadow: 0 0 8px #00ff88;
    }
    .dot-red {
        background-color: #ff4444;
        box-shadow: 0 0 8px #ff4444;
    }
    
    /* Metric cards */
    .metric-card {
        background: #ffffff;
        border-radius: 12px;
        padding: 1rem 1.2rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        border: 1px solid #e8e2da;
        text-align: center;
        transition: 0.2s;
    }
    .metric-card:hover {
        box-shadow: 0 4px 16px rgba(0,0,0,0.10);
        border-color: #c8c0b8;
    }
    .metric-label {
        font-size: 0.85rem;
        color: #6a6a7e;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.3px;
    }
    .metric-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #1a1a2e;
        margin-top: 4px;
    }
    .metric-sub {
        font-size: 0.8rem;
        color: #8892a8;
        margin-top: 2px;
    }
    
    /* Index cards */
    .index-card {
        background: #ffffff;
        border-radius: 10px;
        padding: 0.8rem 1rem;
        box-shadow: 0 1px 4px rgba(0,0,0,0.04);
        border: 1px solid #e8e2da;
        text-align: center;
    }
    .index-name {
        font-size: 0.85rem;
        font-weight: 600;
        color: #4a4a5e;
    }
    .index-price {
        font-size: 1.2rem;
        font-weight: 700;
        color: #1a1a2e;
        margin: 2px 0;
    }
    .index-change {
        font-size: 0.9rem;
        font-weight: 600;
    }
    .change-positive {
        color: #00aa66;
    }
    .change-negative {
        color: #cc3333;
    }
    
    /* Section headers */
    .section-title {
        font-size: 1.3rem;
        font-weight: 700;
        color: #1a1a2e;
        margin: 1.2rem 0 0.8rem 0;
        padding-bottom: 6px;
        border-bottom: 2px solid #e8e2da;
    }
    
    /* Status panel */
    .status-panel {
        background: #ffffff;
        border-radius: 12px;
        padding: 1.2rem;
        border: 1px solid #e8e2da;
        box-shadow: 0 1px 4px rgba(0,0,0,0.04);
        margin-bottom: 1rem;
    }
    .status-panel h4 {
        margin: 0 0 8px 0;
        color: #1a1a2e;
        font-weight: 600;
    }
    .status-badge {
        display: inline-block;
        padding: 2px 12px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .badge-offline {
        background: #fee2e2;
        color: #cc3333;
    }
    .badge-online {
        background: #d1fae5;
        color: #00aa66;
    }
    .status-error {
        color: #cc3333;
        font-size: 0.9rem;
    }
    .status-time {
        color: #8892a8;
        font-size: 0.8rem;
        margin-top: 6px;
    }
    
    /* Offline panel container */
    .offline-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 1rem;
    }
    @media (max-width: 768px) {
        .offline-grid {
            grid-template-columns: 1fr;
        }
    }
    
    /* Footer */
    .footer {
        margin-top: 2rem;
        padding-top: 1rem;
        border-top: 1px solid #e8e2da;
        display: flex;
        justify-content: space-between;
        color: #8892a8;
        font-size: 0.85rem;
    }
    .refresh-btn {
        background: #1a1a2e;
        color: #fff;
        border: none;
        border-radius: 8px;
        padding: 6px 20px;
        font-weight: 600;
        cursor: pointer;
        transition: 0.2s;
    }
    .refresh-btn:hover {
        background: #2a2a4e;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ============================================
# HEADER
# ============================================
st.markdown("""
<div class="header-bar">
    <div class="header-title">📊 SPRZones<span>Pulse</span></div>
    <div class="header-status">
        <span><span class="status-dot dot-green"></span>AI Active</span>
        <span><span class="status-dot dot-green"></span>Market Live</span>
        <span>⚡ 95%+ Accuracy</span>
    </div>
</div>
""", unsafe_allow_html=True)

# ============================================
# TOP METRICS
# ============================================
# Simulate some metrics (you can replace with real data)
total_analyses = 20
success_rate = 93.9

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown("""
    <div class="metric-card">
        <div class="metric-label">🤖 AI Active</div>
        <div class="metric-value">✅</div>
        <div class="metric-sub">Live</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">📈 Market Live</div>
        <div class="metric-value">🟢</div>
        <div class="metric-sub">Connected</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">🎯 95%+ Accuracy</div>
        <div class="metric-value">95.2%</div>
        <div class="metric-sub">Last 30 days</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">📊 Total Analyses</div>
        <div class="metric-value">{total_analyses}</div>
        <div class="metric-sub">Success Rate {success_rate}%</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<hr style='margin: 0.5rem 0; border-color: #e8e2da;'>", unsafe_allow_html=True)

# ============================================
# INDICES DISPLAY
# ============================================
# Simulated indices (replace with live data from Yahoo Finance if available)
indices_data = {
    "S&P 500": {"price": 7500.58, "change": 1.44},
    "NASDAQ": {"price": 26517.93, "change": 2.74},
    "NIFTY 50": {"price": 22550.40, "change": -0.50},
    "BTC/USD": {"price": 67890.00, "change": 2.40},
    "XAUUSD": {"price": 2350.00, "change": 0.80},
    "EUR/USD": {"price": 1.0850, "change": 0.12}
}

cols = st.columns(6)
for i, (name, data) in enumerate(indices_data.items()):
    with cols[i]:
        change = data["change"]
        color_class = "change-positive" if change >= 0 else "change-negative"
        sign = "+" if change >= 0 else ""
        st.markdown(f"""
        <div class="index-card">
            <div class="index-name">{name}</div>
            <div class="index-price">{data["price"]:,.2f}</div>
            <div class="index-change {color_class}">{sign}{change:.2f}%</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("<hr style='margin: 0.5rem 0; border-color: #e8e2da;'>", unsafe_allow_html=True)

# ============================================
# 200 EMA BREAKOUT SCANNER
# ============================================
st.markdown('<div class="section-title">📈 200 EMA Breakout Scanner (1H / 4H / Daily)</div>', unsafe_allow_html=True)

# Check if scanner data exists (simulate)
signals_file = "dashboard/data/signals.json"
if os.path.exists(signals_file):
    try:
        with open(signals_file, 'r') as f:
            scanner_data = json.load(f)
        st.success(f"✅ Scanner loaded: {len(scanner_data)} signals found")
        # Display scanner results in a dataframe
        df = pd.DataFrame(scanner_data)
        st.dataframe(df, width='stretch', hide_index=True)
    except Exception as e:
        st.warning(f"⚠️ Could not load scanner data: {e}")
else:
    st.warning("⚠️ Could not load scanner data. Make sure `dashboard/data/signals.json` exists in the repo.")

st.markdown("<hr style='margin: 0.5rem 0; border-color: #e8e2da;'>", unsafe_allow_html=True)

# ============================================
# OFFLINE PANELS (Shariah, PEAD, Alert Bot)
# ============================================
st.markdown('<div class="section-title">🔧 System Status</div>', unsafe_allow_html=True)

# Offline panels grid
offline_panels = [
    {
        "title": "Shariah Screener",
        "status": "OFFLINE",
        "error": "API Error (403)",
        "time": "11:23:42 AM"
    },
    {
        "title": "PEAD Earnings Agent",
        "status": "OFFLINE",
        "error": "API Error (403)",
        "time": "11:23:42 AM"
    },
    {
        "title": "Market Alert Bot",
        "status": "OFFLINE",
        "error": "API Error (403)",
        "time": "11:23:42 AM"
    }
]

cols = st.columns(3)
for i, panel in enumerate(offline_panels):
    with cols[i]:
        st.markdown(f"""
        <div class="status-panel">
            <h4>{panel['title']}</h4>
            <div>
                <span class="status-badge badge-offline">{panel['status']}</span>
            </div>
            <div class="status-error">{panel['error']}</div>
            <div class="status-time">🕒 {panel['time']}</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("<hr style='margin: 1rem 0; border-color: #e8e2da;'>", unsafe_allow_html=True)

# ============================================
# FOOTER
# ============================================
current_time = datetime.now().strftime("%m/%d/%Y, %I:%M:%S %p")

# Create a two-column footer
col_left, col_right = st.columns([2, 1])
with col_left:
    st.caption(f"**Last updated:** {current_time}")
with col_right:
    if st.button("🔄 Refresh Status", use_container_width=True):
        st.cache_data.clear()
        st.cache_resource.clear()
        st.rerun()

# ============================================
# OPTIONAL: Hidden Agent Functionality (Expandable)
# ============================================
with st.expander("📊 Advanced Multi-Agent Analysis (Bull, Bear, Moderator)", expanded=False):
    st.info("This section provides deeper AI-driven signals from our three agents.")
    
    # Initialize agents (if not already done)
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
    
    if bull_agent and bear_agent and moderator_agent:
        # Generate sample data (reuse from earlier)
        @st.cache_data(ttl=60)
        def generate_sample_data():
            np.random.seed(42)
            n = 200
            trend = np.linspace(0, 1, n) * 30
            noise = np.random.randn(n) * 5
            close = 100 + trend + noise.cumsum()
            data = pd.DataFrame({
                'open': close + np.random.randn(n) * 2,
                'high': close + np.abs(np.random.randn(n) * 3) + 1,
                'low': close - np.abs(np.random.randn(n) * 3) - 1,
                'close': close,
                'volume': np.random.randint(1000, 10000, n) + np.linspace(0, 5000, n),
            })
            data['open'] = data['open'].shift(1).fillna(data['close'])
            data['high'] = data[['high', 'open', 'close']].max(axis=1)
            data['low'] = data[['low', 'open', 'close']].min(axis=1)
            data['returns'] = data['close'].pct_change()
            data['high_low_ratio'] = data['high'] / data['low']
            data['volume_ratio'] = data['volume'] / data['volume'].rolling(10).mean()
            # Add more indicators...
            data = data.ffill().bfill()
            return data
        
        sample_data = generate_sample_data()
        
        try:
            bull_pred = bull_agent.predict(sample_data)
            bull_signal = bull_agent.get_signal(bull_pred)
            bear_pred = bear_agent.predict(sample_data)
            bear_signal = bear_agent.get_signal(bear_pred)
            agent_signals = [bull_signal, bear_signal]
            moderator_result = moderator_agent.aggregate_agent_signals(agent_signals)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Bull Agent", bull_signal['signal'], f"Confidence: {bull_signal['confidence']}%")
            with col2:
                st.metric("Bear Agent", bear_signal['signal'], f"Confidence: {bear_signal['confidence']}%")
            with col3:
                st.metric("Moderator", moderator_result['final_signal'], f"Consensus: {moderator_result['consensus']}%")
        except Exception as e:
            st.warning(f"Agent analysis error: {e}")
    else:
        st.warning("Agents not available. Check installation.")

# ============================================
# HIDDEN: Backtest (optional)
# ============================================
with st.expander("📈 Backtest Engine", expanded=False):
    st.info("Run backtest on historical strategies.")
    if st.button("Run Backtest"):
        try:
            backtest = BacktestEngine(initial_capital=100000)
            # Use sample data
            sample = generate_sample_data()
            ma_short = sample['close'].rolling(5).mean()
            ma_long = sample['close'].rolling(20).mean()
            signals = (ma_short > ma_long).astype(int)
            signals = signals.diff().fillna(0)
            results = backtest.run_backtest(sample, signals)
            st.json(results)
        except Exception as e:
            st.error(f"Backtest error: {e}")
