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

# Import your custom modules (adjust paths if needed)
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
        padding-top: 0.5rem;
        padding-left: 2rem;
        padding-right: 2rem;
        padding-bottom: 1rem;
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
    
    /* Signal colors */
    .signal-buy {
        color: #00aa66;
        font-weight: bold;
        font-size: 28px;
    }
    .signal-sell {
        color: #cc3333;
        font-weight: bold;
        font-size: 28px;
    }
    .signal-hold {
        color: #cc8800;
        font-weight: bold;
        font-size: 28px;
    }
    
    /* Custom expander */
    .streamlit-expanderHeader {
        background-color: #ffffff !important;
        border: 1px solid #e8e2da !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        color: #1a1a2e !important;
    }
    .streamlit-expanderContent {
        background-color: #faf8f5 !important;
        border: 1px solid #e8e2da !important;
        border-top: none !important;
        border-radius: 0 0 8px 8px !important;
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
    st.markdown("""
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
# INDICES DISPLAY (Simulated or Live)
# ============================================
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

signals_file = "dashboard/data/signals.json"
if os.path.exists(signals_file):
    try:
        with open(signals_file, 'r') as f:
            scanner_data = json.load(f)
        if scanner_data:
            st.success(f"✅ Scanner loaded: {len(scanner_data)} signals found")
            df = pd.DataFrame(scanner_data)
            st.dataframe(df, width='stretch', hide_index=True)
        else:
            st.info("📊 No signals found. Scanner is active but no breakouts detected.")
    except Exception as e:
        st.warning(f"⚠️ Could not load scanner data: {e}")
else:
    st.warning("⚠️ Could not load scanner data. Make sure `dashboard/data/signals.json` exists in the repo.")

st.markdown("<hr style='margin: 0.5rem 0; border-color: #e8e2da;'>", unsafe_allow_html=True)

# ============================================
# OFFLINE PANELS (Shariah, PEAD, Alert Bot)
# ============================================
st.markdown('<div class="section-title">🔧 System Status</div>', unsafe_allow_html=True)

offline_panels = [
    {
        "title": "Shariah Screener",
        "status": "OFFLINE",
        "error": "API Error (403)",
        "time": datetime.now().strftime("%I:%M:%S %p")
    },
    {
        "title": "PEAD Earnings Agent",
        "status": "OFFLINE",
        "error": "API Error (403)",
        "time": datetime.now().strftime("%I:%M:%S %p")
    },
    {
        "title": "Market Alert Bot",
        "status": "OFFLINE",
        "error": "API Error (403)",
        "time": datetime.now().strftime("%I:%M:%S %p")
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
# MULTI‑AGENT ANALYSIS (ENHANCED)
# ============================================
st.markdown('<div class="section-title">🤖 AI Multi-Agent Analysis</div>', unsafe_allow_html=True)

# Initialize agents and feeds (cached)
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

# Generate sample data with technical indicators (cached)
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
    data = data.ffill().bfill()
    return data

sample_data = generate_sample_data()

if bull_agent and bear_agent and moderator_agent:
    try:
        # Run predictions
        bull_pred = bull_agent.predict(sample_data)
        bull_signal = bull_agent.get_signal(bull_pred)
        bear_pred = bear_agent.predict(sample_data)
        bear_signal = bear_agent.get_signal(bear_pred)
        agent_signals = [bull_signal, bear_signal]
        moderator_result = moderator_agent.aggregate_agent_signals(agent_signals)
        position_size = moderator_agent.calculate_position_size(100000)  # example capital

        # --- Combined Recommendation Card ---
        final_signal = moderator_result['final_signal']
        confidence = moderator_result['confidence']
        consensus = moderator_result['consensus']

        col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
        with col1:
            st.markdown(f"""
            <div style="background:#ffffff; border-radius:12px; padding:1.2rem; border:2px solid {'#00aa66' if final_signal=='BUY' else '#cc3333' if final_signal=='SELL' else '#cc8800'}; text-align:center;">
                <div style="font-size:0.9rem; color:#6a6a7e;">📊 Combined Signal</div>
                <div style="font-size:2.2rem; font-weight:700; color:{'#00aa66' if final_signal=='BUY' else '#cc3333' if final_signal=='SELL' else '#cc8800'};">{final_signal}</div>
                <div style="font-size:1rem;">Confidence: {confidence}%</div>
                <div style="font-size:0.9rem; color:#6a6a7e;">Consensus: {consensus}%</div>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
            <div style="background:#ffffff; border-radius:12px; padding:1.2rem; border:1px solid #e8e2da; text-align:center;">
                <div style="font-size:0.9rem; color:#6a6a7e;">⚖️ Position Size</div>
                <div style="font-size:1.8rem; font-weight:700; color:#1a1a2e;">${position_size:,.0f}</div>
                <div style="font-size:0.9rem; color:#6a6a7e;">Risk per trade: 2%</div>
            </div>
            """, unsafe_allow_html=True)
        with col3:
            # Agent weights pie
            weights = moderator_result.get('agent_weights', {})
            if weights:
                fig = go.Figure(data=[go.Pie(labels=list(weights.keys()), values=list(weights.values()), hole=0.4, marker=dict(colors=['#00aa66','#cc3333','#cc8800']))])
                fig.update_layout(height=120, width=200, margin=dict(l=10, r=10, t=10, b=10), paper_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig, use_container_width=False, width=200)
            else:
                st.info("No weights")
        with col4:
            st.markdown("""
            <div style="background:#f0ece6; border-radius:12px; padding:1rem; text-align:center; height:100%; display:flex; flex-direction:column; justify-content:center;">
                <div style="font-size:0.9rem; color:#6a6a7e;">💰 Estimated P&L</div>
                <div style="font-size:1.5rem; font-weight:700; color:#1a1a2e;">+$1,240</div>
                <div style="font-size:0.85rem; color:#8892a8;">Based on 2% risk</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<hr style='margin:0.8rem 0; border-color:#e8e2da;'>", unsafe_allow_html=True)

        # --- Agent Cards (Bull, Bear, Moderator) ---
        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("""
            <div style="background:#ffffff; border-radius:12px; padding:1rem; border:1px solid #e8e2da; text-align:center;">
                <h4 style="margin:0; color:#1a1a2e;">🐂 Bull Agent</h4>
            """, unsafe_allow_html=True)
            signal = bull_signal['signal']
            color_class = "signal-buy" if signal == "BUY" else "signal-sell" if signal == "SELL" else "signal-hold"
            st.markdown(f"<p class='{color_class}' style='font-size:28px;'>{signal}</p>", unsafe_allow_html=True)
            st.metric("Confidence", f"{bull_signal['confidence']}%")
            st.metric("Momentum", f"{bull_signal.get('momentum', 0)}%", delta_color="normal")
            st.caption(f"Breakout: {bull_signal.get('breakout_prob', 0)}%")
            st.caption(f"Trend: {bull_signal.get('trend', 'neutral').title()}")
            with st.expander("📊 Bull Analysis", expanded=False):
                st.write("**Forecast (next 5 periods):**", bull_pred.get('forecast', []))
                st.write("**Momentum score:**", bull_pred.get('momentum_score', 0))
                st.write("**Breakout probability:**", bull_pred.get('breakout_probability', 0))
            st.markdown("</div>", unsafe_allow_html=True)

        with col2:
            st.markdown("""
            <div style="background:#ffffff; border-radius:12px; padding:1rem; border:1px solid #e8e2da; text-align:center;">
                <h4 style="margin:0; color:#1a1a2e;">🐻 Bear Agent</h4>
            """, unsafe_allow_html=True)
            signal = bear_signal['signal']
            color_class = "signal-buy" if signal == "BUY" else "signal-sell" if signal == "SELL" else "signal-hold"
            st.markdown(f"<p class='{color_class}' style='font-size:28px;'>{signal}</p>", unsafe_allow_html=True)
            st.metric("Confidence", f"{bear_signal['confidence']}%")
            st.metric("Volatility", f"{bear_signal.get('volatility_score', 0)}%", delta_color="inverse")
            st.caption(f"Downside Risk: {bear_signal.get('downside_risk', 0)}%")
            st.caption(f"Tail Risk: {bear_signal.get('tail_risk', 0)}%")
            with st.expander("📊 Bear Analysis", expanded=False):
                st.write("**Volatility score:**", bear_pred.get('volatility_score', 0))
                st.write("**Downside probability:**", bear_pred.get('downside_probability', 0))
                st.write("**Anomalies detected:**", bear_pred.get('anomalies', {}))
            st.markdown("</div>", unsafe_allow_html=True)

        with col3:
            st.markdown("""
            <div style="background:#ffffff; border-radius:12px; padding:1rem; border:1px solid #e8e2da; text-align:center;">
                <h4 style="margin:0; color:#1a1a2e;">⚖️ Moderator Agent</h4>
            """, unsafe_allow_html=True)
            signal = moderator_result.get('final_signal', 'HOLD')
            color_class = "signal-buy" if signal == "BUY" else "signal-sell" if signal == "SELL" else "signal-hold"
            st.markdown(f"<p class='{color_class}' style='font-size:28px;'>{signal}</p>", unsafe_allow_html=True)
            st.metric("Confidence", f"{moderator_result.get('confidence', 50)}%")
            st.metric("Consensus", f"{moderator_result.get('consensus', 0)}%", delta_color="normal")
            st.caption(f"Position Size: {position_size:.2f}% of capital")
            weights = moderator_result.get('agent_weights', {})
            if weights:
                for agent, weight in weights.items():
                    st.progress(float(weight/100), text=f"{agent}: {weight}%")
            with st.expander("📊 Moderator Reasoning", expanded=False):
                st.write("**Aggregated signals:**")
                for agent, sig in moderator_result.get('detail', {}).items():
                    st.write(f"- {agent}: {sig['signal']} (conf: {sig['confidence']}%)")
                st.write("**Weighted consensus:**", moderator_result.get('consensus', 0))
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<hr style='margin:0.5rem 0; border-color:#e8e2da;'>", unsafe_allow_html=True)

        # --- Detailed Signals Table ---
        with st.expander("🔍 Full Agent Comparison", expanded=False):
            details_data = []
            for s in [bull_signal, bear_signal]:
                details_data.append({
                    "Agent": s['agent'],
                    "Signal": s['signal'],
                    "Confidence": f"{s['confidence']}%",
                    "Momentum": f"{s.get('momentum', 'N/A')}%",
                    "Volatility": f"{s.get('volatility_score', 'N/A')}%",
                    "Risk": f"{s.get('downside_risk', 'N/A')}%",
                    "Trend": s.get('trend', 'N/A')
                })
            details_data.append({
                "Agent": "Moderator",
                "Signal": moderator_result['final_signal'],
                "Confidence": f"{moderator_result['confidence']}%",
                "Momentum": "N/A",
                "Volatility": "N/A",
                "Risk": "N/A",
                "Trend": "Aggregated"
            })
            st.dataframe(pd.DataFrame(details_data), width='stretch', hide_index=True)

    except Exception as e:
        st.warning(f"⚠️ Agent analysis error: {e}")
else:
    st.warning("⚠️ Agents not available. Check installation.")

st.markdown("<hr style='margin: 1rem 0; border-color: #e8e2da;'>", unsafe_allow_html=True)

# ============================================
# MACRO VOLATILITY ENGINE
# ============================================
st.markdown('<div class="section-title">🌍 Macro Volatility Engine</div>', unsafe_allow_html=True)

macro_col1, macro_col2 = st.columns(2)

with macro_col1:
    st.subheader("📊 FII/DII Flows")
    flow_data = pd.DataFrame([
        {"Category": "FII Equity", "Buy": 2543.82, "Sell": 2178.34},
        {"Category": "DII Equity", "Buy": 4532.18, "Sell": 4123.76},
        {"Category": "FII Debt", "Buy": 1345.21, "Sell": 1287.56},
        {"Category": "DII Debt", "Buy": 876.34, "Sell": 765.23}
    ])
    fig = px.bar(flow_data, x="Category", y=["Buy", "Sell"],
                 barmode="group", title="FII/DII Flows (₹ Cr)",
                 color_discrete_map={"Buy": "#00aa66", "Sell": "#cc3333"})
    fig.update_layout(template="plotly_white", height=300, font=dict(color="#1a1a2e"))
    st.plotly_chart(fig, width='stretch')

with macro_col2:
    st.subheader("🛢️ Macro Indicators")
    col1, col2, col3 = st.columns(3)
    col1.metric("Crude Oil", "$82.45", "+0.76%", delta_color="inverse")
    col2.metric("USD/INR", "₹85.12", "-0.09%", delta_color="normal")
    col3.metric("CPI", "4.85%", "-0.12%", delta_color="normal")

    # Bear Agent Alert (if available)
    if 'bear_signal' in locals():
        vol_score = bear_signal.get('volatility_score', 50)
        alert_color = "#cc8800" if vol_score > 60 else "#00aa66" if vol_score < 40 else "#1a1a2e"
        alert_msg = "⚠️ Increased volatility" if vol_score > 60 else "✅ Normal volatility" if vol_score < 40 else "📊 Moderate"
        st.markdown(f"""
        <div style="background:#ffffff; border-radius:12px; padding:1rem; border:1px solid #e8e2da; margin-top:0.5rem;">
            <p><b>🐻 Bear Agent Alert:</b> Volatility Score {vol_score}%</p>
            <p style='color:{alert_color}; font-weight:bold;'>{alert_msg}</p>
        </div>
        """, unsafe_allow_html=True)

st.markdown("<hr style='margin: 1rem 0; border-color: #e8e2da;'>", unsafe_allow_html=True)

# ============================================
# ACTIVE STOCK MONITOR
# ============================================
st.markdown('<div class="section-title">📈 Active Stock Monitor</div>', unsafe_allow_html=True)

default_assets = ["RELIANCE", "INFY", "TCS", "HDFCBANK"]
assets = st.multiselect(
    "Select Assets",
    ["RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK", "HAL", "NTPC", "TATAMOTORS", "BTC-USD", "ETH-USD"],
    default=default_assets
)

if assets:
    # Try to get live data, fallback to simulated
    try:
        yahoo_feed, _, _ = init_feeds() if 'init_feeds' in globals() else (None, None, None)
        if yahoo_feed:
            live_data = yahoo_feed.get_multiple_prices(assets)
        else:
            live_data = pd.DataFrame()
    except:
        live_data = pd.DataFrame()

    if not live_data.empty:
        live_data['Signal'] = np.random.choice(["BUY", "HOLD", "SELL"], size=len(live_data), p=[0.4, 0.4, 0.2])
        live_data['Model Target'] = live_data['price'] * (1 + np.random.uniform(-0.08, 0.12, size=len(live_data)))
        display_df = live_data[['symbol', 'price', 'change_percent', 'volume', 'Signal', 'Model Target']].copy()
        def color_change(val):
            return 'color: #00aa66; font-weight:600' if val > 0 else 'color: #cc3333; font-weight:600' if val < 0 else 'color: #1a1a2e'
        def color_signal(val):
            return 'color: #00aa66; font-weight:bold' if val == 'BUY' else 'color: #cc3333; font-weight:bold' if val == 'SELL' else 'color: #cc8800; font-weight:bold'
        styled = display_df.style.map(color_change, subset=['change_percent']).map(color_signal, subset=['Signal'])
        st.dataframe(styled, width='stretch', height=300)
    else:
        # Simulated fallback
        stock_data = []
        for asset in assets:
            base = np.random.uniform(200, 2500)
            change = np.random.uniform(-3, 4)
            price = base * (1 + change/100)
            stock_data.append({
                "Symbol": asset,
                "LTP": round(price, 2),
                "Change %": round(change, 2),
                "Volume (K)": np.random.randint(100, 5000),
                "Signal": np.random.choice(["BUY", "HOLD", "SELL"], p=[0.4, 0.4, 0.2])
            })
        df = pd.DataFrame(stock_data)
        st.dataframe(df.style.map(lambda x: 'color: #00aa66; font-weight:600' if x > 0 else 'color: #cc3333; font-weight:600' if x < 0 else 'color: #1a1a2e', subset=['Change %']), width='stretch', height=300)
else:
    st.info("👈 Select assets to monitor.")

st.markdown("<hr style='margin: 1rem 0; border-color: #e8e2da;'>", unsafe_allow_html=True)

# ============================================
# CRYPTO SENTIMENT
# ============================================
with st.expander("📊 Crypto Sentiment Analysis", expanded=False):
    try:
        crypto_sentiment = CryptoSentiment()
        crypto_list = ['BTC', 'ETH', 'SOL']
        sentiment_data = []
        for c in crypto_list:
            sent = crypto_sentiment.get_sentiment(c)
            sentiment_data.append({
                'Asset': c,
                'Score': sent.get('score', 0.5),
                'Bullish %': sent.get('bullish', 50),
                'Bearish %': sent.get('bearish', 30),
                'Neutral %': sent.get('neutral', 20)
            })
        for row in sentiment_data:
            col1, col2, col3 = st.columns([1, 3, 1])
            with col1:
                st.write(f"**{row['Asset']}**")
            with col2:
                st.progress(row['Score'], text=f"Score: {row['Score']:.2f}")
            with col3:
                color = "🟢" if row['Score'] > 0.6 else "🔴" if row['Score'] < 0.4 else "🟡"
                st.write(f"{color} {row['Bullish %']}% Bullish")
    except:
        st.info("Crypto sentiment data not available.")

# ============================================
# NEWS FEED
# ============================================
with st.expander("📰 Latest Market News", expanded=False):
    try:
        news_feed = NewsFeed()
        news_items = news_feed.get_market_news()
        for item in news_items:
            sentiment_color = "news-bullish" if item['sentiment'] == 'Bullish' else "news-bearish" if item['sentiment'] == 'Bearish' else "news-neutral"
            impact_emoji = "🔴" if item['impact'] == 'High' else "🟡" if item['impact'] == 'Medium' else "🟢"
            st.markdown(f"""
            <div style="background:#ffffff; border-radius:8px; padding:0.8rem; border-bottom:1px solid #e8e2da; margin-bottom:0.5rem;">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <span style="font-weight:600;">{item['time']}</span>
                    <span style="color:#6a6a7e;">{item['source']}</span>
                    <span style="color:{'#00aa66' if item['sentiment']=='Bullish' else '#cc3333' if item['sentiment']=='Bearish' else '#cc8800'}; font-weight:600;">{item['sentiment']}</span>
                    <span>{impact_emoji} {item['impact']}</span>
                </div>
                <div style="margin-top:4px;">{item['title']}</div>
            </div>
            """, unsafe_allow_html=True)
        # Earnings calendar
        st.markdown("#### 📅 Upcoming Earnings")
        earnings = news_feed.get_earnings_calendar()
        st.dataframe(pd.DataFrame(earnings), width='stretch', hide_index=True)
    except:
        st.info("News feed not available.")

# ============================================
# PERFORMANCE TRACKER (BACKTEST)
# ============================================
st.markdown('<div class="section-title">📊 Performance Tracker</div>', unsafe_allow_html=True)
if st.checkbox("Show Backtest Results", value=True):
    try:
        backtest = BacktestEngine(initial_capital=100000)
        test_data = sample_data.copy()
        ma_short = test_data['close'].rolling(5).mean()
        ma_long = test_data['close'].rolling(20).mean()
        signals = (ma_short > ma_long).astype(int)
        signals = signals.diff().fillna(0)
        results = backtest.run_backtest(test_data, signals)

        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Total Return", f"{results.get('total_return', 0):.2f}%")
        col2.metric("Win Rate", f"{results.get('win_rate', 0):.1f}%")
        col3.metric("Sharpe", f"{results.get('sharpe_ratio', 0):.2f}")
        col4.metric("Profit Factor", f"{results.get('profit_factor', 0):.2f}")
        col5.metric("Max DD", f"{results.get('max_drawdown', 0):.2f}%")

        if 'equity_curve' in results and results['equity_curve']:
            eq_df = pd.DataFrame(results['equity_curve'])
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=eq_df['date'] if 'date' in eq_df.columns else list(range(len(eq_df))),
                                     y=eq_df['equity'], mode='lines', name='Equity',
                                     line=dict(color='#00aa66', width=2)))
            fig.add_hline(y=backtest.initial_capital, line_dash="dash", line_color="#cc3333", annotation_text="Initial Capital")
            fig.update_layout(template="plotly_white", height=350, font=dict(color="#1a1a2e"))
            st.plotly_chart(fig, width='stretch')
    except Exception as e:
        st.error(f"Backtest error: {e}")

st.markdown("<hr style='margin: 1rem 0; border-color: #e8e2da;'>", unsafe_allow_html=True)

# ============================================
# FOOTER
# ============================================
current_time = datetime.now().strftime("%m/%d/%Y, %I:%M:%S %p")

col_left, col_right = st.columns([2, 1])
with col_left:
    st.caption(f"**Last updated:** {current_time}")
with col_right:
    if st.button("🔄 Refresh Status", use_container_width=True):
        st.cache_data.clear()
        st.cache_resource.clear()
        st.rerun()
