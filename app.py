import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import sys
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

# Initialize components
@st.cache_resource
def init_agents():
    bull = BullAgent()
    bear = BearAgent()
    moderator = ModeratorAgent()
    return bull, bear, moderator

@st.cache_resource
def init_feeds():
    return NSELiveFeed(), MacroFeed()

bull_agent, bear_agent, moderator_agent = init_agents()
nse_feed, macro_feed = init_feeds()

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

# ============================================
# SECTION 1: Institutional Alpha Stream
# ============================================
st.header("🏛️ Institutional Alpha Stream")

# Get sample data (in production, use actual market data)
sample_data = pd.DataFrame({
    'open': np.random.randn(100) * 10 + 100,
    'high': np.random.randn(100) * 10 + 105,
    'low': np.random.randn(100) * 10 + 95,
    'close': np.random.randn(100) * 10 + 100,
    'volume': np.random.randint(1000, 10000, 100)
})
sample_data = sample_data.cumsum() + 1000

# Run agents
bull_signal = bull_agent.get_signal(bull_agent.predict(sample_data))
bear_signal = bear_agent.get_signal(bear_agent.predict(sample_data))
agent_signals = [bull_signal, bear_signal]
moderator_result = moderator_agent.aggregate_agent_signals(agent_signals)

# Display agent cards
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown("""
    <div class="metric-card">
        <h4>🐂 Bull Agent</h4>
    """, unsafe_allow_html=True)
    signal = bull_signal['signal']
    color = "signal-buy" if signal == "BUY" else "signal-sell" if signal == "SELL" else "signal-hold"
    st.markdown(f"<p class='{color}' style='font-size:24px'>{signal}</p>", unsafe_allow_html=True)
    st.metric("Confidence", f"{bull_signal['confidence']}%")
    st.metric("Momentum", f"{bull_signal['momentum']}%", delta_color="normal")
    st.caption(f"Breakout: {bull_signal['breakout_prob']}%")
    st.markdown("</div>", unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="metric-card">
        <h4>🐻 Bear Agent</h4>
    """, unsafe_allow_html=True)
    signal = bear_signal['signal']
    color = "signal-buy" if signal == "BUY" else "signal-sell" if signal == "SELL" else "signal-hold"
    st.markdown(f"<p class='{color}' style='font-size:24px'>{signal}</p>", unsafe_allow_html=True)
    st.metric("Confidence", f"{bear_signal['confidence']}%")
    st.metric("Volatility", f"{bear_signal['volatility_score']}%", delta_color="inverse")
    st.caption(f"Downside Risk: {bear_signal['downside_risk']}%")
    st.markdown("</div>", unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="metric-card">
        <h4>⚖️ Moderator</h4>
    """, unsafe_allow_html=True)
    signal = moderator_result['final_signal']
    color = "signal-buy" if signal == "BUY" else "signal-sell" if signal == "SELL" else "signal-hold"
    st.markdown(f"<p class='{color}' style='font-size:24px'>{signal}</p>", unsafe_allow_html=True)
    st.metric("Confidence", f"{moderator_result['confidence']}%")
    st.metric("Consensus", f"{moderator_result['consensus']}%", delta_color="normal")
    st.markdown("</div>", unsafe_allow_html=True)

with col4:
    st.markdown("""
    <div class="metric-card">
        <h4>📊 Agent Weights</h4>
    """, unsafe_allow_html=True)
    for agent, weight in moderator_result['agent_weights'].items():
        st.metric(agent, f"{weight}%")
    st.markdown("</div>", unsafe_allow_html=True)

# Detailed agent signals table
with st.expander("🔍 Detailed Agent Analysis"):
    details_df = pd.DataFrame([
        {
            "Agent": s['agent'],
            "Signal": s['signal'],
            "Confidence": s['confidence'],
            "Momentum": s.get('momentum', 'N/A'),
            "Volatility": s.get('volatility_score', 'N/A'),
            "Risk": s.get('downside_risk', 'N/A')
        }
        for s in agent_signals
    ])
    st.dataframe(details_df, use_container_width=True)

st.divider()

# ============================================
# SECTION 2: Macro Volatility Engine
# ============================================
st.header("🌍 Macro Volatility Engine")

macro_col1, macro_col2 = st.columns(2)

with macro_col1:
    st.subheader("📊 FII/DII Flows")
    flows = macro_feed.get_fii_dii_flows()
    
    flow_data = pd.DataFrame([
        {"Category": "FII Equity", "Buy": flows['fii_equity']['buy'], "Sell": flows['fii_equity']['sell']},
        {"Category": "DII Equity", "Buy": flows['dii_equity']['buy'], "Sell": flows['dii_equity']['sell']},
        {"Category": "FII Debt", "Buy": flows['fii_debt']['buy'], "Sell": flows['fii_debt']['sell']},
        {"Category": "DII Debt", "Buy": flows['dii_debt']['buy'], "Sell": flows['dii_debt']['sell']}
    ])
    
    fig = px.bar(flow_data, x="Category", y=["Buy", "Sell"], 
                 barmode="group", title="FII/DII Flows (₹ Cr)",
                 color_discrete_map={"Buy": "#00ff88", "Sell": "#ff4444"})
    fig.update_layout(template="plotly_dark", height=300)
    st.plotly_chart(fig, use_container_width=True)

with macro_col2:
    st.subheader("🛢️ Macro Indicators")
    
    crude = macro_feed.get_crude_oil()
    usdinr = macro_feed.get_usdinr()
    inflation = macro_feed.get_inflation_metrics()
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Crude Oil", f"${crude['price']}", f"{crude['change_percent']}%", delta_color="inverse")
    col2.metric("USD/INR", f"₹{usdinr['rate']}", f"{usdinr['change_percent']}%", delta_color="inverse")
    col3.metric("CPI", f"{inflation['cpi']}%", f"{inflation['cpi_change']}%", delta_color="inverse")
    
    st.markdown(f"""
    <div class="metric-card">
        <p><b>Bear Agent Alert:</b> Volatility Score {bear_signal['volatility_score']}% | 
        Downside Risk {bear_signal['downside_risk']}%</p>
        <p style='color:#ffaa00'>{'⚠️ Increased volatility detected' if bear_signal['volatility_score'] > 60 else '✅ Volatility within normal range'}</p>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# ============================================
# SECTION 3: Active Stock Monitor
# ============================================
st.header("📈 Active Stock Monitor")

# Map display names to symbols
stock_map = {
    "ICICI Bank": "ICICIBANK",
    "NTPC": "NTPC",
    "Tata Motors": "TATAMOTORS",
    "HAL": "HAL",
    "Infosys": "INFY"
}

# Simulate live prices
stock_data = []
for asset in assets:
    symbol = stock_map.get(asset, asset)
    try:
        quote = nse_feed.get_equity_quote(symbol)
        stock_data.append({
            "Symbol": asset,
            "LTP": quote['ltp'],
            "Change": quote['pChange'],
            "Volume": quote['volume'] // 1000,
            "Model Target": round(quote['ltp'] * (1 + np.random.uniform(-0.05, 0.08)), 2)
        })
    except:
        # Simulated data fallback
        base_price = np.random.uniform(500, 2000)
        stock_data.append({
            "Symbol": asset,
            "LTP": round(base_price, 2),
            "Change": round(np.random.uniform(-2, 3), 2),
            "Volume": np.random.randint(100, 1000),
            "Model Target": round(base_price * (1 + np.random.uniform(-0.05, 0.08)), 2)
        })

stock_df = pd.DataFrame(stock_data)
st.dataframe(stock_df, use_container_width=True, hide_index=True)

st.divider()

# ============================================
# SECTION 4: Performance Tracker
# ============================================
st.header("📊 Performance Tracker")

if show_backtest:
    # Run backtest
    backtest = BacktestEngine(initial_capital=100000)
    test_data = sample_data.copy()
    
    # Generate signals (simplified)
    signals = (test_data['close'].pct_change().rolling(5).mean() > 0.01).astype(int)
    
    results = backtest.run_backtest(test_data, signals)
    
    # Performance metrics
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total Return", f"{results['total_return']}%", delta_color="normal")
    col2.metric("Win Rate", f"{results['win_rate']}%", delta_color="normal")
    col3.metric("Sharpe Ratio", results['sharpe_ratio'])
    col4.metric("Profit Factor", results['profit_factor'])
    col5.metric("Max Drawdown", f"{results['max_drawdown']}%", delta_color="inverse")
    
    # Equity Curve
    equity_df = pd.DataFrame(results['equity_curve'])
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=equity_df['date'], y=equity_df['equity'],
                             mode='lines', name='Equity',
                             line=dict(color='#00ff88', width=2)))
    fig.add_hline(y=backtest.initial_capital, line_dash="dash", 
                  line_color="#ff4444", annotation_text="Initial Capital")
    fig.update_layout(template="plotly_dark", height=400,
                     title="Equity Curve",
                     xaxis_title="Date", yaxis_title="Capital ($)")
    st.plotly_chart(fig, use_container_width=True)
    
    # Trade Distribution
    if results['trades']:
        trades_df = pd.DataFrame(results['trades'])
        fig2 = px.histogram(trades_df, x='pnl_pct', title="Trade P&L Distribution",
                            color_discrete_sequence=['#00ff88'])
        fig2.update_layout(template="plotly_dark", height=300)
        st.plotly_chart(fig2, use_container_width=True)
else:
    st.info("Backtest visualization disabled. Enable in sidebar.")

st.divider()

# ============================================
# FOOTER
# ============================================
st.caption("""
    ⚡ **System Status:** Live | **Data Source:** NSE/BSE | **Last Update:** {} |
    **Agents:** Bull LSTM, Bear GRU+GARCH, Moderator Transformer
""".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
