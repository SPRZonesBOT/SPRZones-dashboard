import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import requests
import json

class YahooFinanceFeed:
    """Real-time market data from Yahoo Finance"""
    
    def __init__(self):
        self.tickers = {
            'nifty': '^NSEI',
            'sensex': '^BSESN',
            'banknifty': '^NSEBANK',
            'btc': 'BTC-USD',
            'eth': 'ETH-USD',
            'sol': 'SOL-USD',
            'gold': 'GC=F',
            'silver': 'SI=F',
            'oil': 'CL=F',
            'usdinr': 'USDINR=X',
            'sp500': '^GSPC',
            'nasdaq': '^IXIC',
            'dow': '^DJI'
        }
        
        # Indian stocks mapping
        self.indian_stocks = {
            'RELIANCE': 'RELIANCE.NS',
            'TCS': 'TCS.NS',
            'INFY': 'INFY.NS',
            'HDFCBANK': 'HDFCBANK.NS',
            'ICICIBANK': 'ICICIBANK.NS',
            'HAL': 'HAL.NS',
            'NTPC': 'NTPC.NS',
            'TATAMOTORS': 'TATAMOTORS.NS'
        }
    
    def get_live_price(self, symbol: str) -> Dict:
        """Get live price for a symbol"""
        try:
            # Check if it's an Indian stock
            if symbol in self.indian_stocks:
                ticker = yf.Ticker(self.indian_stocks[symbol])
            else:
                ticker = yf.Ticker(symbol)
            
            info = ticker.info
            
            # Get current price
            price = info.get('regularMarketPrice', info.get('currentPrice', 0))
            previous_close = info.get('regularMarketPreviousClose', info.get('previousClose', price))
            
            change = price - previous_close if previous_close else 0
            change_percent = (change / previous_close * 100) if previous_close else 0
            
            return {
                'symbol': symbol,
                'price': price,
                'previous_close': previous_close,
                'change': change,
                'change_percent': change_percent,
                'volume': info.get('regularMarketVolume', info.get('volume', 0)),
                'high': info.get('regularMarketDayHigh', info.get('dayHigh', 0)),
                'low': info.get('regularMarketDayLow', info.get('dayLow', 0)),
                'timestamp': datetime.now().isoformat(),
                'source': 'Yahoo Finance'
            }
        except Exception as e:
            print(f"⚠️ Error fetching {symbol}: {e}")
            return None
    
    def get_historical_data(self, symbol: str, period: str = '1d', interval: str = '5m') -> pd.DataFrame:
        """Get historical data for a symbol"""
        try:
            # Check if it's an Indian stock
            if symbol in self.indian_stocks:
                ticker = yf.Ticker(self.indian_stocks[symbol])
            else:
                ticker = yf.Ticker(symbol)
            
            data = ticker.history(period=period, interval=interval)
            
            # Add technical indicators
            if not data.empty:
                data = self._add_technical_indicators(data)
            
            return data
        except Exception as e:
            print(f"⚠️ Error fetching historical data for {symbol}: {e}")
            return pd.DataFrame()
    
    def get_multiple_prices(self, symbols: List[str]) -> pd.DataFrame:
        """Get live prices for multiple symbols"""
        data = []
        for symbol in symbols:
            price_data = self.get_live_price(symbol)
            if price_data:
                data.append(price_data)
        return pd.DataFrame(data)
    
    def get_indices_data(self) -> Dict:
        """Get all major indices data"""
        indices = {}
        for name, symbol in self.tickers.items():
            price_data = self.get_live_price(symbol)
            if price_data:
                indices[name.upper()] = price_data
        return indices
    
    def _add_technical_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """Add technical indicators to historical data"""
        df = data.copy()
        
        # Returns
        df['returns'] = df['Close'].pct_change()
        
        # RSI
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # MACD
        exp1 = df['Close'].ewm(span=12, adjust=False).mean()
        exp2 = df['Close'].ewm(span=26, adjust=False).mean()
        df['macd'] = exp1 - exp2
        df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
        df['macd_histogram'] = df['macd'] - df['macd_signal']
        
        # Bollinger Bands
        sma = df['Close'].rolling(window=20).mean()
        std = df['Close'].rolling(window=20).std()
        df['bb_upper'] = sma + (std * 2)
        df['bb_middle'] = sma
        df['bb_lower'] = sma - (std * 2)
        df['bb_width'] = df['bb_upper'] - df['bb_lower']
        
        # EMAs
        df['ema_9'] = df['Close'].ewm(span=9, adjust=False).mean()
        df['ema_21'] = df['Close'].ewm(span=21, adjust=False).mean()
        df['ema_50'] = df['Close'].ewm(span=50, adjust=False).mean()
        
        # SMAs
        df['sma_20'] = df['Close'].rolling(window=20).mean()
        df['sma_50'] = df['Close'].rolling(window=50).mean()
        df['sma_200'] = df['Close'].rolling(window=200).mean()
        
        # ATR
        high_low = df['High'] - df['Low']
        high_close = np.abs(df['High'] - df['Close'].shift())
        low_close = np.abs(df['Low'] - df['Close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = np.max(ranges, axis=1)
        df['atr'] = true_range.rolling(14).mean()
        
        # Volume indicators
        df['volume_ma'] = df['Volume'].rolling(window=20).mean()
        df['volume_ratio'] = df['Volume'] / df['volume_ma']
        df['volume_change'] = df['Volume'].pct_change()
        
        # VWAP
        df['vwap'] = (df['Volume'] * (df['High'] + df['Low'] + df['Close']) / 3).cumsum() / df['Volume'].cumsum()
        
        # High/Low ratio
        df['high_low_ratio'] = df['High'] / df['Low']
        
        # Price momentum
        df['momentum'] = df['Close'] - df['Close'].shift(10)
        
        # Fill NaN values
        df = df.fillna(method='ffill').fillna(method='bfill')
        
        return df
    
    def get_option_chain(self, symbol: str) -> pd.DataFrame:
        """Get option chain data (for Indian stocks)"""
        try:
            if symbol in self.indian_stocks:
                ticker = yf.Ticker(self.indian_stocks[symbol])
            else:
                ticker = yf.Ticker(symbol)
            
            # Get option chain
            options = ticker.option_chain()
            
            # Combine calls and puts
            calls = options.calls
            puts = options.puts
            
            # Calculate PCR
            calls_oi = calls['openInterest'].sum()
            puts_oi = puts['openInterest'].sum()
            pcr = puts_oi / calls_oi if calls_oi > 0 else 0
            
            return {
                'calls': calls,
                'puts': puts,
                'pcr': pcr,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            print(f"⚠️ Error fetching option chain for {symbol}: {e}")
            return None


class NewsFeed:
    """Real-time news feed from multiple sources"""
    
    def __init__(self):
        self.news_sources = [
            'Bloomberg',
            'Reuters',
            'CNBC',
            'CoinDesk',
            'Economic Times'
        ]
    
    def get_market_news(self, limit: int = 10) -> List[Dict]:
        """Get latest market news"""
        # Simulated news data (replace with real API in production)
        news_items = [
            {
                'time': datetime.now().strftime('%H:%M'),
                'title': 'Fed signals rate cuts in 2025, markets rally',
                'source': 'Bloomberg',
                'impact': 'High',
                'sentiment': 'Bullish'
            },
            {
                'time': (datetime.now() - timedelta(minutes=15)).strftime('%H:%M'),
                'title': 'NVIDIA reports record earnings, beats estimates',
                'source': 'Reuters',
                'impact': 'High',
                'sentiment': 'Bullish'
            },
            {
                'time': (datetime.now() - timedelta(minutes=30)).strftime('%H:%M'),
                'title': 'Oil prices drop on weak demand concerns',
                'source': 'CNBC',
                'impact': 'Medium',
                'sentiment': 'Bearish'
            },
            {
                'time': (datetime.now() - timedelta(minutes=45)).strftime('%H:%M'),
                'title': 'Bitcoin ETFs see record inflows, BTC surges',
                'source': 'CoinDesk',
                'impact': 'High',
                'sentiment': 'Bullish'
            },
            {
                'time': (datetime.now() - timedelta(hours=1)).strftime('%H:%M'),
                'title': 'Tech sector leads market rally, Nasdaq up 2%',
                'source': 'CNBC',
                'impact': 'Medium',
                'sentiment': 'Bullish'
            }
        ]
        return news_items[:limit]
    
    def get_earnings_calendar(self) -> List[Dict]:
        """Get upcoming earnings announcements"""
        return [
            {'company': 'Reliance', 'date': '2026-07-15', 'time': 'After Market'},
            {'company': 'TCS', 'date': '2026-07-16', 'time': 'After Market'},
            {'company': 'Infosys', 'date': '2026-07-18', 'time': 'After Market'},
            {'company': 'HDFC Bank', 'date': '2026-07-20', 'time': 'After Market'}
        ]


class CryptoSentiment:
    """Cryptocurrency sentiment analysis"""
    
    def __init__(self):
        self.sentiment_sources = ['Twitter', 'Reddit', 'Telegram']
    
    def get_sentiment(self, symbol: str) -> Dict:
        """Get sentiment for a cryptocurrency"""
        # Simulated sentiment data
        sentiments = {
            'BTC': {'score': 0.72, 'bullish': 65, 'bearish': 20, 'neutral': 15},
            'ETH': {'score': 0.65, 'bullish': 58, 'bearish': 25, 'neutral': 17},
            'SOL': {'score': 0.48, 'bullish': 45, 'bearish': 35, 'neutral': 20}
        }
        return sentiments.get(symbol.upper(), {'score': 0.5, 'bullish': 50, 'bearish': 30, 'neutral': 20})
