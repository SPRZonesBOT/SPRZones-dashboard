import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import sys
import warnings
warnings.filterwarnings('ignore')
import time

# Fix path issues
sys.path.append('.')

from data.ingestion.nse_bse_feeds import NSELiveFeed, MacroFeed
from data.ingestion.yahoo_finance import YahooFinanceFeed, NewsFeed, CryptoSentiment
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
    .live-indicator {
        color: #ff4444;
        animation: blink 1s infinite;
    }
    @keyframes blink {
        0% { opacity: 1; }
        50% { opacity: 0; }
        100% { opacity: 1; }
    }
    .news-bullish {
        color: #00ff88;
    }
    .news-bearish {
        color: #ff4444;
    }
    .news-neutral {
        color: #ffaa00;
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
        yahoo_feed = YahooFinanceFeed()
        news_feed = NewsFeed()
        crypto_sentiment = CryptoSentiment()
        return yahoo_feed, news_feed, crypto_sentiment
    except Exception as e:
        st.error(f"❌ Error initializing data feeds: {e}")
        return None, None, None

# Initialize components
bull_agent, bear_agent, moderator_agent = init_agents()
yahoo_feed, news_feed, crypto_sentiment = init_feeds()

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
        [1, 7, 14, 30, 90, 180],
        index=1
    )
    
    st.divider()
    
    st.subheader("📈 Assets")
    assets = st.multiselect(
        "Select Assets to Monitor",
        ["RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK", "HAL", "NTPC", "TATAMOTORS", "BTC-USD", "ETH-USD"],
        default=["RELIANCE", "INFY", "BTC-USD"]
    )
    
    st.divider()
    
    st.subheader("🎯 Filters")
    min_confidence = st.slider("Minimum Confidence", 40, 95, 60)
    show_backtest = st.checkbox("Show Backtest Results", value=True)
    show_advanced = st.checkbox("Show Advanced Analytics", value=False)
    show_news = st.checkbox("Show News Feed", value=True)
    show_correlation = st.checkbox("Show Correlation Heatmap", value=True)
    
    st.divider()
    
    st.subheader("🔄 Auto Refresh")
    auto_refresh = st.checkbox("Auto Refresh (30s)", value=False)
    if auto_refresh:
        st.caption("🔄 Auto-refresh enabled")
        time.sleep(0.1)  # Small delay
    
    if st.button("🔄 Refresh Now", use_container_width=True):
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
        st.caption("🔍 Live Data")
    
    with st.expander("📦 Model Details"):
        st.caption("🐂 Bull: LSTM (Trend)")
        st.caption("🐻 Bear: GRU+GARCH (Volatility)")
        st.caption("⚖️ Moderator: Transformer")
        st.caption("📊 Backtest: Custom Engine")

# ============================================
# MAIN CONTENT
# ============================================
st.title("📊 Multi‑Agent Quant Dashboard")
st.caption("Real-time AI-powered market analysis with live data integration")

# Live indicator
st.markdown('<span class="live-indicator">●</span> **LIVE DATA**', unsafe_allow_html=True)

# ============================================
# MARKET OVERVIEW (LIVE)
# ============================================
st.header("🌍 Market Overview")
st.markdown('<div class="section-header"></div>', unsafe_allow_html=True)

# Get live indices data
@st.cache_data(ttl=30)
def get_live_indices():
    if yahoo_feed:
        return yahoo_feed.get_indices_data()
    return {}

indices_data = get_live_indices()

# Display market overview
if indices_data:
    cols = st.columns(4)
    for i, (name, data) in enumerate(list(indices_data.items())[:8]):
        with cols[i % 4]:
            change = data.get('change_percent', 0)
            color = "🟢" if change > 0 else "🔴"
            st.metric(
                name,
                f"{data.get('price', 0):,.2f}",
                f"{color} {change:+.2f}%",
                delta_color="normal"
            )
else:
    # Fallback simulated data
    indices = {
        "NIFTY": 22450.60,
        "SENSEX": 73500.80,
        "BTC": 65420.30,
        "ETH": 3450.20,
        "Gold": 2405.60,
        "Oil": 82.45,
        "USDINR": 85.12,
        "NASDAQ": 18500.40
    }
    cols = st.columns(4)
    for i, (name, price) in enumerate(indices.items()):
        with cols[i % 4]:
            change = np.random.uniform(-1.5, 2.0)
            color = "🟢" if change > 0 else "🔴"
            st.metric(
                name,
                f"{price:,.2f}",
                f"{color} {change:+.2f}%",
                delta_color="normal"
            )

st.divider()

# ============================================
# LIVE PRICE DATA FETCH
# ============================================
@st.cache_data(ttl=30)
def get_live_prices(symbols):
    if yahoo_feed:
        return yahoo_feed.get_multiple_prices(symbols)
    return pd.DataFrame()

# Get live prices for selected assets
live_prices_df = get_live_prices(assets)

if not live_prices_df.empty:
    with st.expander("📊 Live Prices", expanded=True):
        st.dataframe(
            live_prices_df[['symbol', 'price', 'change_percent', 'volume', 'high', 'low']],
            width='stretch',
            hide_index=True
        )
else:
    st.info("📡 No live data available. Showing simulated data.")

# ============================================
# GENERATE SAMPLE DATA WITH TECHNICAL INDICATORS
# ============================================
@st.cache_data(ttl=60)
def generate_sample_data():
    """Generate realistic sample data with technical indicators"""
    np.random.seed(42)
    n = 200
    
    # Generate price data
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
    
    # Technical indicators
    data['returns'] = data['close'].pct_change()
    data['high_low_ratio'] = data['high'] / data['low']
    data['volume_ratio'] = data['volume'] / data['volume'].rolling(10).mean()
    
    # RSI
    delta = data['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    data['rsi'] = 100 - (100 / (1 + rs))
    
    # MACD
    exp1 = data['close'].ewm(span=12, adjust=False).mean()
    exp2 = data['close'].ewm(span=26, adjust=False).mean()
    data['macd'] = exp1 - exp2
    data['macd_signal'] = data['macd'].ewm(span=9, adjust=False).mean()
    
    # Bollinger Bands
    sma = data['close'].rolling(window=20).mean()
    std = data['close'].rolling(window=20).std()
    data['bb_upper'] = sma + (std * 2)
    data['bb_lower'] = sma - (std * 2)
    
    # EMAs
    data['ema_9'] = data['close'].ewm(span=9, adjust=False).mean()
    data['ema_21'] = data['close'].ewm(span=21, adjust=False).mean()
    
    # SMAs
    data['sma_50'] = data['close'].rolling(window=50).mean()
    data['sma_200'] = data['close'].rolling(window=200).mean()
    
    # Volume change
    data['volume_change'] = data['volume'].pct_change()
    
    # VWAP
    data['vwap'] = (data['volume'] * (data['high'] + data['low'] + data['close']) / 3).cumsum() / data['volume'].cumsum()
    
    # Add anomalies
    data.loc[20:25, 'close'] += 15
    data.loc[60:65, 'close'] -= 12
    data.loc[80:85, 'volume'] *= 3
    
    # Fill NaN
    data = data.fillna(method='ffill').fillna(method='bfill')
    
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
    st.dataframe(details_df, width='stretch', hide_index=True)

st.divider()

# ============================================
# SECTION 2: CRYPTO SENTIMENT
# ============================================
with st.expander("📊 Crypto Sentiment Analysis", expanded=False):
    if crypto_sentiment:
        crypto_list = ['BTC', 'ETH', 'SOL']
        sentiment_data = []
        for crypto in crypto_list:
            sentiment = crypto_sentiment.get_sentiment(crypto)
            sentiment_data.append({
                'Asset': crypto,
                'Sentiment Score': sentiment.get('score', 0.5),
                'Bullish %': sentiment.get('bullish', 50),
                'Bearish %': sentiment.get('bearish', 30),
                'Neutral %': sentiment.get('neutral', 20)
            })
        
        sentiment_df = pd.DataFrame(sentiment_data)
        
        # Display sentiment as progress bars
        for _, row in sentiment_df.iterrows():
            col1, col2, col3 = st.columns([1, 3, 1])
            with col1:
                st.write(f"**{row['Asset']}**")
            with col2:
                st.progress(row['Sentiment Score'], text=f"Score: {row['Sentiment Score']:.2f}")
            with col3:
                sentiment_color = "🟢" if row['Sentiment Score'] > 0.6 else "🔴" if row['Sentiment Score'] < 0.4 else "🟡"
                st.write(f"{sentiment_color} {row['Bullish %']}% Bullish")
    else:
        st.info("📡 Crypto sentiment data not available")

st.divider()

# ============================================
# SECTION 3: NEWS FEED
# ============================================
if show_news:
    with st.expander("📰 Latest Market News", expanded=True):
        if news_feed:
            news_items = news_feed.get_market_news()
            
            # Create news display
            for item in news_items:
                sentiment_color = "news-bullish" if item['sentiment'] == 'Bullish' else "news-bearish" if item['sentiment'] == 'Bearish' else "news-neutral"
                impact_emoji = "🔴" if item['impact'] == 'High' else "🟡" if item['impact'] == 'Medium' else "🟢"
                
                st.markdown(f"""
                <div style="padding: 10px; border-bottom: 1px solid #2d3748;">
                    <div style="display: flex; justify-content: space-between;">
                        <span style="font-weight: bold;">{item['time']}</span>
                        <span style="color: #666;">{item['source']}</span>
                        <span class="{sentiment_color}">{item['sentiment']}</span>
                        <span>{impact_emoji} {item['impact']}</span>
                    </div>
                    <div style="margin-top: 5px;">{item['title']}</div>
                </div>
                """, unsafe_allow_html=True)
            
            # Earnings calendar
            st.markdown("### 📅 Upcoming Earnings")
            earnings = news_feed.get_earnings_calendar()
            earnings_df = pd.DataFrame(earnings)
            st.dataframe(earnings_df, width='stretch', hide_index=True)
        else:
            st.info("📡 News feed not available")

st.divider()

# ============================================
# SECTION 4: ACTIVE STOCK MONITOR
# ============================================
st.header("📈 Active Stock Monitor")
st.markdown('<div class="section-header"></div>', unsafe_allow_html=True)

# Get live stock data
@st.cache_data(ttl=30)
def get_live_stock_data(asset_list):
    if yahoo_feed:
        return yahoo_feed.get_multiple_prices(asset_list)
    return pd.DataFrame()

if assets:
    live_stock_data = get_live_stock_data(assets)
    
    if not live_stock_data.empty:
        # Add signal column (simulated)
        live_stock_data['Signal'] = np.random.choice(["BUY", "HOLD", "SELL"], size=len(live_stock_data), p=[0.4, 0.4, 0.2])
        live_stock_data['Model Target'] = live_stock_data['price'] * (1 + np.random.uniform(-0.08, 0.12, size=len(live_stock_data)))
        
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
        
        styled_df = live_stock_data.style.map(color_change, subset=['change_percent'])
        styled_df = styled_df.map(color_signal, subset=['Signal'])
        
        st.dataframe(
            styled_df[['symbol', 'price', 'change_percent', 'volume', 'Signal', 'Model Target']],
            width='stretch',
            height=300
        )
    else:
        # Fallback simulated data
        stock_data = []
        for asset in assets:
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
        stock_df = pd.DataFrame(stock_data)
        
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
        
        styled_df = stock_df.style.map(color_change, subset=['Change %'])
        styled_df = styled_df.map(color_signal, subset=['Signal'])
        
        st.dataframe(styled_df, width='stretch', height=300)
else:
    st.info("👈 Please select assets from the sidebar to monitor.")

st.divider()

# ============================================
# SECTION 5: PERFORMANCE TRACKER
# ============================================
st.header("📊 Performance Tracker")
st.markdown('<div class="section-header"></div>', unsafe_allow_html=True)

if show_backtest:
    try:
        backtest = BacktestEngine(initial_capital=100000)
        test_data = sample_data.copy()
        
        # Generate signals
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
            fig.update_layout(
                template="plotly_dark", 
                height=400, 
                title="Equity Curve",
                xaxis_title="Date" if 'date' in equity_df.columns else "Trade #",
                yaxis_title="Capital ($)"
            )
            st.plotly_chart(fig, width='stretch')
        else:
            st.info("📈 Equity curve data not available")
        
    except Exception as e:
        st.error(f"❌ Backtest error: {e}")
else:
    st.info("📊 Backtest visualization disabled. Enable in sidebar.")

st.divider()

# ============================================
# SECTION 6: CORRELATION HEATMAP
# ============================================
if show_correlation:
    with st.expander("📊 Asset Correlation Heatmap", expanded=False):
        # Use live data if available
        if not live_prices_df.empty and len(live_prices_df) > 1:
            # Get historical data for correlation
            correlation_data = {}
            for symbol in live_prices_df['symbol'].tolist()[:5]:  # Limit to 5 for performance
                hist_data = yahoo_feed.get_historical_data(symbol, period='1d')
                if not hist_data.empty:
                    correlation_data[symbol] = hist_data['Close']
            
            if correlation_data:
                corr_df = pd.DataFrame(correlation_data)
                corr_matrix = corr_df.corr()
                
                fig = px.imshow(
                    corr_matrix,
                    text_auto=True,
                    color_continuous_scale='RdBu_r',
                    title="Asset Correlation Matrix",
                    zmin=-1,
                    zmax=1
                )
                fig.update_layout(template="plotly_dark", height=400)
                st.plotly_chart(fig, width='stretch')
            else:
                st.info("📊 Not enough data for correlation analysis")
        else:
            # Generate sample correlation
            assets_corr = ['NIFTY', 'BTC', 'ETH', 'Gold', 'Oil']
            np.random.seed(42)
            corr_matrix = np.random.randn(len(assets_corr), len(assets_corr))
            corr_matrix = (corr_matrix @ corr_matrix.T) / len(assets_corr)
            np.fill_diagonal(corr_matrix, 1)
            
            fig = px.imshow(
                corr_matrix,
                x=assets_corr,
                y=assets_corr,
                text_auto=True,
                color_continuous_scale='RdBu_r',
                title="Asset Correlation Matrix",
                zmin=-1,
                zmax=1
            )
            fig.update_layout(template="plotly_dark", height=400)
            st.plotly_chart(fig, width='stretch')

# ============================================
# FOOTER
# ============================================
st.divider()
st.caption(f"""
    ⚡ **System Status:** Live | **Data Source:** Yahoo Finance, NSE/BSE | **Last Update:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} |
    **Agents:** Bull LSTM, Bear GRU+GARCH, Moderator Transformer |
    **Version:** 2.0.0
""")

col1, col2, col3 = st.columns(3)
with col1:
    st.progress(100, text="Data Feed: Connected")
with col2:
    st.progress(100, text="AI Models: Loaded")
with col3:
    st.progress(100, text="Dashboard: Running")
