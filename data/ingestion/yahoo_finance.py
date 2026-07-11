import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

class YahooFinanceFeed:
    """Real-time market data from Yahoo Finance"""
    
    def __init__(self):
        self.tickers = {
            'nifty': '^NSEI',
            'sensex': '^BSESN',
            'btc': 'BTC-USD',
            'eth': 'ETH-USD',
            'gold': 'GC=F',
            'oil': 'CL=F',
            'usdinr': 'USDINR=X'
        }
    
    def get_live_price(self, symbol: str) -> dict:
        """Get live price for a symbol"""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            return {
                'symbol': symbol,
                'price': info.get('regularMarketPrice', 0),
                'change': info.get('regularMarketChange', 0),
                'change_percent': info.get('regularMarketChangePercent', 0),
                'volume': info.get('regularMarketVolume', 0),
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            print(f"Error fetching {symbol}: {e}")
            return None
    
    def get_historical_data(self, symbol: str, period: str = '1d') -> pd.DataFrame:
        """Get historical data for a symbol"""
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period=period)
            return data
        except Exception as e:
            print(f"Error fetching historical data for {symbol}: {e}")
            return pd.DataFrame()
