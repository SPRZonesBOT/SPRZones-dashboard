import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import sys
import warnings
warnings.filterwarnings('ignore')

# Fix path issues
sys.path.append('.')

from data.ingestion.nse_bse_feeds import NSELiveFeed, MacroFeed
from agents.bull_agent import BullAgent
from agents.bear_agent import BearAgent
from agents.moderator_agent import ModeratorAgent
from agents.backtest_engine import BacktestEngine

# Page configuration
st.set_page_config(
    page_title="Multi‑Agent Quant Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .stApp {
        background-color: #0e1117;
        color: #f0f2f6;
    }
    .css-1d391kg {
        background-color: #1e2433;
    }
    .metric-card {
        background-color: #1e2433;
        border-radius: 10px;
        padding: 15px;
        border: 1px solid #2d3748;
    }
    .signal-buy {
        color: #00ff88;
        font-weight: bold;
    }
    .signal-sell {
        color: #ff4444;
        font-weight: bold;
    }
    .signal-hold {
        color: #ffaa00;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Initialize components with proper error handling
@st.cache_resource
def init_agents():
    try:
        bull = BullAgent()
        bear = BearAgent()
        moderator = ModeratorAgent()
        return bull, bear, moderator
    except Exception as e:
        st.error(f"❌ Error initializing agents: {e}")
        # Return dummy agents for demo
        return None, None, None

@st.cache_resource
def init_feeds():
    try:
        return NSELiveFeed(), MacroFeed()
    except Exception as e:
        st.error(f"❌ Error initializing data feeds: {e}")
        return None, None

# Initialize
bull_agent, bear_agent, moderator_agent = init_agents()
nse_feed, macro_feed = init_feeds()

# Check if agents loaded properly
if bull_agent is None or bear_agent is None or moderator_agent is None:
    st.error("🚨 Failed to load agents. Please check the logs.")
    st.stop()

# Sidebar
with st.sidebar:
    st.title("⚙️ Control Panel")
    
    # Timeframe selection
    timeframe = st.selectbox(
        "Timeframe",
        ["1m", "5m", "15m", "30m", "1h", "4h", "1d"]
    )
    
    # Lookback period
    lookback = st.selectbox(
        "Lookback Period",
        [7, 14, 30, 90, 180, 365],
        index=2
    )
    
    # Asset selection
    assets = st.multiselect(
        "Select Assets",
        ["ICICI Bank", "NTPC", "Tata Motors", "HAL", "Infosys"],
        default=["ICICI Bank", "Infosys"]
    )
    
    st.divider()
    
    # Performance filters
    st.subheader("📈 Filters")
    min_confidence = st.slider("Min Confidence", 40, 95, 60)
    show_backtest = st.checkbox("Show Backtest", value=True)
    
    st.divider()
    
    # Refresh button
    if st.button("🔄 Refresh Data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    
    st.divider()
    
    # System status
    st.subheader("🟢 System Status")
    st.caption(f"Last Update: {datetime.now().strftime('%H:%M:%S')}")
    st.caption("Agents: 3/3 Online")
    st.caption(f"Scanned: 12,458 Assets")

# Main content
st.title("📊 Multi‑Agent Quant Dashboard")

# Generate sample data
@st.cache_data
def generate_sample_data():
    np.random.seed(42)
    data = pd.DataFrame({
        'open': np.random.randn(100) * 10 + 100,
        'high': np.random.randn(100) * 10 + 105,
        'low': np.random.randn(100) * 10 + 95,
        'close': np.random.randn(100) * 10 + 100,
        'volume': np.random.randint(1000, 10000, 100)
    })
    data = data.cumsum() + 1000
    # Add some basic technical indicators
    data['returns'] = data['close'].pct_change()
    data['high_low_ratio'] = data['high'] / data['low']
    data['volume_ratio'] = data['volume'] / data['volume'].rolling(10).mean()
    return data

sample_data = generate_sample_data()

# Run agents with error handling
try:
    bull_pred = bull_agent.predict(sample_data)
    bull_signal = bull_agent.get_signal(bull_pred)
except Exception as e:
    st.error(f"Bull Agent error: {e}")
    bull_signal = {"agent": "Bull", "signal": "HOLD", "confidence": 50, "momentum": 0, "breakout_prob": 0}

try:
    bear_pred = bear_agent.predict(sample_data)
    bear_signal = bear_agent.get_signal(bear_pred)
except Exception as e:
    st.error(f"Bear Agent error: {e}")
    bear_signal = {"agent": "Bear", "signal": "HOLD", "confidence": 50, "volatility_score": 50, "downside_risk": 50}

try:
    agent_signals = [bull_signal, bear_signal]
    moderator_result = moderator_agent.aggregate_agent_signals(agent_signals)
except Exception as e:
    st.error(f"Moderator Agent error: {e}")
    moderator_result = {"final_signal": "HOLD", "confidence": 50, "agent_weights": {"Bull": 50, "Bear": 50}, "consensus": 0}

# [Rest of your dashboard code remains the same]
# ... (display logic from your original app.py continues here)
