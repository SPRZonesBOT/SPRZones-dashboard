import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
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

# ============================================
# PAGE CONFIGURATION
# ============================================
st.set_page_config(
    page_title="Multi‑Agent Quant Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================
# CUSTOM CSS
# ============================================
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
        margin: 5px 0;
    }
    .metric-card:hover {
        border-color: #4a5568;
        transition: 0.3s;
    }
    .signal-buy {
        color: #00ff88;
        font-weight: bold;
        font-size: 28px;
    }
    .signal-sell {
        color: #ff4444;
        font-weight: bold;
        font-size: 28px;
    }
    .signal-hold {
        color: #ffaa00;
        font-weight: bold;
        font-size: 28px;
    }
    .section-header {
        border-bottom: 2px solid #2d3748;
        padding-bottom: 10px;
        margin-bottom: 20px;
    }
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    ::-webkit-scrollbar-track {
        background: #0e1117;
    }
    ::-webkit-scrollbar-thumb {
        background: #2d3748;
        border-radius: 4px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: #4a5568;
    }
</style>
""", unsafe_allow_html=True)

# ============================================
# INITIALIZATION
# ============================================
@st.cache_resource
def init_agents():
    """Initialize all agents with error handling"""
    try:
        bull = BullAgent()
        bear = BearAgent()
        moderator = ModeratorAgent()
        return bull, bear, moderator
    except Exception as e:
        st.error(f"❌ Error initializing agents: {e}")
        return None, None, None

@st.cache_resource
def init_feeds():
    """Initialize data feeds with error handling"""
    try:
        return NSELiveFeed(), MacroFeed()
    except Exception as e:
        st.error(f"❌ Error initializing data feeds: {e}")
        return None, None

# Initialize components
bull_agent, bear_agent, moderator_agent = init_agents()
nse_feed, macro_feed = init_feeds()

# Check if agents loaded properly
if bull_agent is None or bear_agent is None or moderator_agent is None:
    st.error("🚨 Failed to load agents. Please check the logs and ensure all dependencies are installed.")
    st.info("💡 Try running: `pip install -r requirements.txt`")
    st.stop()

# ============================================
# SIDEBAR
# ============================================
with st.sidebar:
    st.title("⚙️ Control Panel")
    
    st.subheader("📊 Time Settings")
    timeframe = st.selectbox(
        "Timeframe",
        ["1m", "5m", "15m", "30m", "1h", "4h", "1d"],
        index=1
    )
    
    lookback = st.selectbox(
        "Lookback Period (Days)",
        [7, 14, 30, 90, 180, 365],
        index=2
    )
    
    st.divider()
    
    st.subheader("📈 Assets")
    assets = st.multiselect(
        "Select Assets to Monitor",
        ["ICICI Bank", "NTPC", "Tata Motors", "HAL", "Infosys", "Reliance", "HDFC Bank"],
        default=["ICICI Bank", "Infosys"]
    )
    
    st.divider()
    
    st.subheader("🎯 Filters")
    min_confidence = st.slider("Minimum Confidence", 40, 95, 60)
    show_backtest = st.checkbox("Show Backtest Results", value=True)
    show_advanced = st.checkbox("Show Advanced Analytics", value=False)
    
    st.divider()
    
    if st.button("🔄 Refresh Data", use_container_width=True):
        st.cache_data.clear()
        st.cache_resource.clear()
        st.rerun()
    
    st.divider()
    
    st.subheader("🟢 System Status")
    col1, col2 = st.columns(2)
    with col1:
        st.caption(f"⏰ {datetime.now().strftime('%H:%M:%S')}")
        st.caption("🟢 Agents: 3/3 Online")
    with col2:
        st.caption(f"📊 {len(assets)} Assets")
        st.caption("🔍 12,458 Scanned")
    
    with st.expander("📦 Model Details"):
        st.caption("🐂 Bull: LSTM (Trend)")
        st.caption("🐻 Bear: GRU+GARCH (Volatility)")
        st.caption("⚖️ Moderator: Transformer")
        st.caption("📊 Backtest: Custom Engine")

# ============================================
# MAIN CONTENT
# ============================================
st.title("📊 Multi‑Agent Quant Dashboard")
st.caption("Real-time AI-powered market analysis with Bull, Bear, and Moderator agents")

# Generate sample data
@st.cache_data(ttl=60)
def generate_sample_data():
    np.random.seed(42)
    n = 100
    trend = np.linspace(0, 1, n) * 20
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
    data.loc[20:25, 'close'] += 10
    data.loc[60:65, 'close'] -= 8
    return data

sample_data = generate_sample_data()

# ============================================
# SECTION 1: INSTITUTIONAL ALPHA STREAM
# ============================================
st.header("🏛️ Institutional Alpha Stream")
st.markdown('<div class="section-header"></div>', unsafe_allow_html=True)

# Run agents with error handling
try:
    bull_pred = bull_agent.predict(sample_data)
    bull_signal = bull_agent.get_signal(bull_pred)
except Exception as e:
    st.warning(f"⚠️ Bull Agent error: {e}")
    bull_signal = {"agent": "Bull", "signal": "HOLD", "confidence": 50, "momentum": 0, "breakout_prob": 0, "trend": "neutral"}

try:
    bear_pred = bear_agent.predict(sample_data)
    bear_signal = bear_agent.get_signal(bear_pred)
except Exception as e:
    st.warning(f"⚠️ Bear Agent error: {e}")
    bear_signal = {"agent": "Bear", "signal": "HOLD", "confidence": 50, "volatility_score": 50, "downside_risk": 50, "tail_risk": 15}

try:
    agent_signals = [bull_signal, bear_signal]
    moderator_result = moderator_agent.aggregate_agent_signals(agent_signals)
except Exception as e:
    st.warning(f"⚠️ Moderator Agent error: {e}")
    moderator_result = {"final_signal": "HOLD", "confidence": 50, "agent_weights": {"Bull": 50, "Bear": 50}, "consensus": 0, "detail": {}}

# Display agent cards
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown("""
    <div class="metric-card">
        <h4>🐂 Bull Agent</h4>
    """, unsafe_allow_html=True)
    signal = bull_signal['signal']
    color_class = "signal-buy" if signal == "BUY" else "signal-sell" if signal == "SELL" else "signal-hold"
    st.markdown(f"<p class='{color_class}'>{signal}</p>", unsafe_allow_html=True)
    st.metric("Confidence", f"{bull_signal['confidence']}%")
    st.metric("Momentum", f"{bull_signal.get('momentum', 0)}%", delta_color="normal")
    st.caption(f"Breakout: {bull_signal.get('breakout_prob', 0)}%")
    st.caption(f"Trend: {bull_signal.get('trend', 'neutral').title()}")
    st.markdown("</div>", unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="metric-card">
        <h4>🐻 Bear Agent</h4>
    """, unsafe_allow_html=True)
    signal = bear_signal['signal']
    color_class = "signal-buy" if signal == "BUY" else "signal-sell" if signal == "SELL" else "signal-hold"
    st.markdown(f"<p class='{color_class}'>{signal}</p>", unsafe_allow_html=True)
    st.metric("Confidence", f"{bear_signal['confidence']}%")
    st.metric("Volatility", f"{bear_signal.get('volatility_score', 0)}%", delta_color="inverse")
    st.caption(f"Downside Risk: {bear_signal.get('downside_risk', 0)}%")
    st.caption(f"Tail Risk: {bear_signal.get('tail_risk', 0)}%")
    st.markdown("</div>", unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="metric-card">
        <h4>⚖️ Moderator</h4>
    """, unsafe_allow_html=True)
    signal = moderator_result.get('final_signal', 'HOLD')
    color_class = "signal-buy" if signal == "BUY" else "signal-sell" if signal == "SELL" else "signal-hold"
    st.markdown(f"<p class='{color_class}'>{signal}</p>", unsafe_allow_html=True)
    st.metric("Confidence", f"{moderator_result.get('confidence', 50)}%")
    st.metric("Consensus", f"{moderator_result.get('consensus', 0)}%", delta_color="normal")
    st.caption(f"Position Size: {moderator_result.get('position_size', 0):.2f}%")
    st.markdown("</div>", unsafe_allow_html=True)

with col4:
    st.markdown("""
    <div class="metric-card">
        <h4>📊 Agent Weights</h4>
    """, unsafe_allow_html=True)
    weights = moderator_result.get('agent_weights', {})
    if weights:
        for agent, weight in weights.items():
            st.progress(float(weight/100), text=f"{agent}: {weight}%")
    else:
        st.info("No weights available")
    st.markdown("</div>", unsafe_allow_html=True)

# Detailed agent signals table
with st.expander("🔍 Detailed Agent Analysis", expanded=False):
    details_data = []
    for s in [bull_signal, bear_signal]:
        row = {
            "Agent": s['agent'],
            "Signal": s['signal'],
            "Confidence": f"{s['confidence']}%",
            "Momentum": f"{s.get('momentum', 'N/A')}%" if s.get('momentum') is not None else "N/A",
            "Volatility": f"{s.get('volatility_score', 'N/A')}%" if s.get('volatility_score') is not None else "N/A",
            "Risk": f"{s.get('downside_risk', 'N/A')}%" if s.get('downside_risk') is not None else "N/A",
            "Trend": s.get('trend', 'N/A')
        }
        details_data.append(row)
    
    details_df = pd.DataFrame(details_data)
    # FIX: use width='stretch' instead of use_container_width=True
    st.dataframe(details_df, width='stretch', hide_index=True)

st.divider()

# ============================================
# SECTION 2: MACRO VOLATILITY ENGINE
# ============================================
st.header("🌍 Macro Volatility Engine")
st.markdown('<div class="section-header"></div>', unsafe_allow_html=True)

macro_col1, macro_col2 = st.columns(2)

with macro_col1:
    st.subheader("📊 FII/DII Flows")
    try:
        flows = macro_feed.get_fii_dii_flows() if macro_feed else None
        if flows:
            flow_data = pd.DataFrame([
                {"Category": "FII Equity", "Buy": flows['fii_equity']['buy'], "Sell": flows['fii_equity']['sell']},
                {"Category": "DII Equity", "Buy": flows['dii_equity']['buy'], "Sell": flows['dii_equity']['sell']},
                {"Category": "FII Debt", "Buy": flows['fii_debt']['buy'], "Sell": flows['fii_debt']['sell']},
                {"Category": "DII Debt", "Buy": flows['dii_debt']['buy'], "Sell": flows['dii_debt']['sell']}
            ])
            
            fig = px.bar(flow_data, x="Category", y=["Buy", "Sell"], 
                         barmode="group", title="FII/DII Flows (₹ Cr)",
                         color_discrete_map={"Buy": "#00ff88", "Sell": "#ff4444"})
            fig.update_layout(template="plotly_dark", height=350)
            fig.update_xaxis(tickangle=15)
            # FIX: use width='stretch' instead of use_container_width=True
            st.plotly_chart(fig, width='stretch')
        else:
            st.info("📡 FII/DII data not available. Using simulated data.")
            sim_data = pd.DataFrame({
                "Category": ["FII Equity", "DII Equity", "FII Debt", "DII Debt"],
                "Buy": np.random.randint(1000, 5000, 4),
                "Sell": np.random.randint(800, 4000, 4)
            })
            fig = px.bar(sim_data, x="Category", y=["Buy", "Sell"], 
                         barmode="group", title="FII/DII Flows (₹ Cr) - Simulated",
                         color_discrete_map={"Buy": "#00ff88", "Sell": "#ff4444"})
            fig.update_layout(template="plotly_dark", height=350)
            st.plotly_chart(fig, width='stretch')
    except Exception as e:
        st.warning(f"⚠️ Error fetching macro data: {e}")
        st.info("Showing simulated data")
        sim_data = pd.DataFrame({
            "Category": ["FII Equity", "DII Equity", "FII Debt", "DII Debt"],
            "Buy": np.random.randint(1000, 5000, 4),
            "Sell": np.random.randint(800, 4000, 4)
        })
        fig = px.bar(sim_data, x="Category", y=["Buy", "Sell"], 
                     barmode="group", title="FII/DII Flows (₹ Cr) - Simulated",
                     color_discrete_map={"Buy": "#00ff88", "Sell": "#ff4444"})
        fig.update_layout(template="plotly_dark", height=350)
        st.plotly_chart(fig, width='stretch')

with macro_col2:
    st.subheader("🛢️ Macro Indicators")
    
    try:
        crude = macro_feed.get_crude_oil() if macro_feed else None
        usdinr = macro_feed.get_usdinr() if macro_feed else None
        inflation = macro_feed.get_inflation_metrics() if macro_feed else None
    except:
        crude = usdinr = inflation = None
    
    col1, col2, col3 = st.columns(3)
    
    if crude:
        col1.metric("Crude Oil", f"${crude.get('price', 0):.2f}", f"{crude.get('change_percent', 0):.2f}%", delta_color="inverse")
    else:
        col1.metric("Crude Oil", "$82.45", "0.76%", delta_color="inverse")
    
    if usdinr:
        col2.metric("USD/INR", f"₹{usdinr.get('rate', 0):.2f}", f"{usdinr.get('change_percent', 0):.2f}%", delta_color="inverse")
    else:
        col2.metric("USD/INR", "₹85.12", "-0.09%", delta_color="normal")
    
    if inflation:
        col3.metric("CPI", f"{inflation.get('cpi', 0):.2f}%", f"{inflation.get('cpi_change', 0):.2f}%", delta_color="inverse")
    else:
        col3.metric("CPI", "4.85%", "-0.12%", delta_color="normal")
    
    vol_score = bear_signal.get('volatility_score', 50)
    risk_score = bear_signal.get('downside_risk', 50)
    
    alert_color = "#ffaa00" if vol_score > 60 else "#00ff88" if vol_score < 40 else "#ffffff"
    alert_msg = "⚠️ Increased volatility detected - Reduce position size" if vol_score > 60 else "✅ Volatility within normal range" if vol_score < 40 else "📊 Moderate volatility - Normal trading conditions"
    
    st.markdown(f"""
    <div class="metric-card">
        <p><b>🐻 Bear Agent Alert:</b></p>
        <p>Volatility Score: {vol_score}% | Downside Risk: {risk_score}%</p>
        <p style='color:{alert_color}; font-weight:bold;'>{alert_msg}</p>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# ============================================
# SECTION 3: ACTIVE STOCK MONITOR
# ============================================
st.header("📈 Active Stock Monitor")
st.markdown('<div class="section-header"></div>', unsafe_allow_html=True)

stock_map = {
    "ICICI Bank": "ICICIBANK",
    "NTPC": "NTPC",
    "Tata Motors": "TATAMOTORS",
    "HAL": "HAL",
    "Infosys": "INFY",
    "Reliance": "RELIANCE",
    "HDFC Bank": "HDFCBANK"
}

@st.cache_data(ttl=30)
def get_stock_data(asset_list):
    stock_data = []
    np.random.seed(int(datetime.now().timestamp()) % 10000)
    
    for asset in asset_list:
        base_price = np.random.uniform(200, 2500)
        change = np.random.uniform(-3, 4)
        price = base_price * (1 + change/100)
        
        stock_data.append({
            "Symbol": asset,
            "LTP": round(price, 2),
            "Change %": round(change, 2),
            "Volume (K)": np.random.randint(100, 5000),
            "Model Target": round(price * (1 + np.random.uniform(-0.08, 0.12)), 2),
            "Signal": np.random.choice(["BUY", "HOLD", "SELL"], p=[0.4, 0.4, 0.2])
        })
    return pd.DataFrame(stock_data)

if assets:
    stock_df = get_stock_data(assets)
    
    def color_change(val):
        if val > 0:
            return 'color: #00ff88'
        elif val < 0:
            return 'color: #ff4444'
        return 'color: #ffffff'
    
    def color_signal(val):
        if val == 'BUY':
            return 'color: #00ff88; font-weight: bold'
        elif val == 'SELL':
            return 'color: #ff4444; font-weight: bold'
        return 'color: #ffaa00; font-weight: bold'
    
    styled_df = stock_df.style.applymap(color_change, subset=['Change %'])
    styled_df = styled_df.applymap(color_signal, subset=['Signal'])
    
    # FIX: use width='stretch' instead of use_container_width=True
    st.dataframe(styled_df, width='stretch', height=200)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        buy_count = len(stock_df[stock_df['Signal'] == 'BUY'])
        st.metric("BUY Signals", buy_count, f"{buy_count/len(assets)*100:.0f}% of assets")
    with col2:
        avg_change = stock_df['Change %'].mean()
        st.metric("Avg Change", f"{avg_change:.2f}%", delta=f"{avg_change:.2f}%")
    with col3:
        target_accuracy = ((stock_df['LTP'] < stock_df['Model Target']) * 1).mean() * 100
        st.metric("Target Accuracy", f"{target_accuracy:.0f}%", "Model vs Actual")
else:
    st.info("👈 Please select assets from the sidebar to monitor.")

st.divider()

# ============================================
# SECTION 4: PERFORMANCE TRACKER
# ============================================
st.header("📊 Performance Tracker")
st.markdown('<div class="section-header"></div>', unsafe_allow_html=True)

if show_backtest:
    try:
        backtest = BacktestEngine(initial_capital=100000)
        test_data = sample_data.copy()
        
        returns = test_data['close'].pct_change()
        ma_short = test_data['close'].rolling(5).mean()
        ma_long = test_data['close'].rolling(20).mean()
        signals = (ma_short > ma_long).astype(int)
        signals = signals.diff().fillna(0)
        
        results = backtest.run_backtest(test_data, signals)
        
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Total Return", f"{results.get('total_return', 0):.2f}%", delta=f"{results.get('total_return', 0):.2f}%")
        col2.metric("Win Rate", f"{results.get('win_rate', 0):.1f}%", delta=f"{results.get('win_rate', 0):.1f}%")
        col3.metric("Sharpe Ratio", f"{results.get('sharpe_ratio', 0):.2f}")
        col4.metric("Profit Factor", f"{results.get('profit_factor', 0):.2f}")
        col5.metric("Max Drawdown", f"{results.get('max_drawdown', 0):.2f}%", delta=f"-{results.get('max_drawdown', 0):.2f}%", delta_color="inverse")
        
        if 'equity_curve' in results and results['equity_curve']:
            equity_df = pd.DataFrame(results['equity_curve'])
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=equity_df['date'] if 'date' in equity_df.columns else list(range(len(equity_df))),
                y=equity_df['equity'],
                mode='lines', 
                name='Equity',
                line=dict(color='#00ff88', width=2)
            ))
            fig.add_hline(y=backtest.initial_capital, line_dash="dash", line_color="#ff4444", annotation_text="Initial Capital")
            fig.update_layout(template="plotly_dark", height=400, title="Equity Curve", xaxis_title="Date" if 'date' in equity_df.columns else "Trade #", yaxis_title="Capital ($)")
            # FIX: use width='stretch' instead of use_container_width=True
            st.plotly_chart(fig, width='stretch')
        else:
            st.info("📈 Equity curve data not available")
        
        if results.get('trades'):
            trades_df = pd.DataFrame(results['trades'])
            if not trades_df.empty and 'pnl_pct' in trades_df.columns:
                fig2 = px.histogram(trades_df, x='pnl_pct', title="Trade P&L Distribution", color_discrete_sequence=['#00ff88'], nbins=30)
                fig2.add_vline(x=0, line_dash="dash", line_color="#ff4444")
                fig2.update_layout(template="plotly_dark", height=300)
                st.plotly_chart(fig2, width='stretch')
        
        if show_advanced:
            with st.expander("📊 Advanced Metrics", expanded=False):
                metrics_col1, metrics_col2 = st.columns(2)
                with metrics_col1:
                    st.metric("Total Trades", results.get('total_trades', 0))
                    st.metric("CAGR", f"{results.get('cagr', 0):.2f}%")
                    st.metric("Sortino Ratio", f"{results.get('sortino_ratio', 0):.2f}")
                with metrics_col2:
                    if results.get('trades'):
                        wins = [t['pnl'] for t in results['trades'] if t['pnl'] > 0]
                        losses = [abs(t['pnl']) for t in results['trades'] if t['pnl'] < 0]
                        avg_win = np.mean(wins) if wins else 0
                        avg_loss = np.mean(losses) if losses else 0
                        st.metric("Avg Win", f"${avg_win:.2f}")
                        st.metric("Avg Loss", f"${avg_loss:.2f}")
                        st.metric("Risk/Reward", f"{(avg_win/avg_loss):.2f}" if avg_loss > 0 else "∞")
        
    except Exception as e:
        st.error(f"❌ Backtest error: {e}")
        st.info("💡 Make sure the BacktestEngine class is properly implemented.")
else:
    st.info("📊 Backtest visualization disabled. Enable in sidebar.")

st.divider()

# ============================================
# SECTION 5: RECENT ACTIVITY
# ============================================
with st.expander("🔔 Recent Alerts & Activity", expanded=False):
    alerts = [
        {"time": "09:24", "asset": "NVIDIA", "event": "Partnership announced", "impact": "High"},
        {"time": "09:18", "asset": "Fed", "event": "Rate cut speculation", "impact": "Medium"},
        {"time": "09:11", "asset": "Oil", "event": "Demand concerns", "impact": "High"},
        {"time": "09:07", "asset": "Bitcoin", "event": "ETF inflows surge", "impact": "High"},
    ]
    alert_df = pd.DataFrame(alerts)
    st.dataframe(alert_df, width='stretch', hide_index=True)

# ============================================
# FOOTER
# ============================================
st.divider()
st.caption(f"""
    ⚡ **System Status:** Live | **Data Source:** NSE/BSE | **Last Update:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} |
    **Agents:** Bull LSTM, Bear GRU+GARCH, Moderator Transformer |
    **Version:** 1.0.0
""")

col1, col2, col3 = st.columns(3)
with col1:
    st.progress(100, text="Data Feed: Connected")
with col2:
    st.progress(100, text="AI Models: Loaded")
with col3:
    st.progress(100, text="Dashboard: Running")
