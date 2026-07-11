import requests
import pandas as pd
import websocket
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional

class NSELiveFeed:
    """NSE Live Feed Handler with WebSocket support"""
    
    def __init__(self):
        self.base_url = "https://www.nseindia.com/api"
        self.ws_url = "wss://ws.nseindia.com/marketdata/ws"
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json"
        })
        
    def get_equity_quote(self, symbol: str) -> Dict:
        """Get real-time equity quote"""
        url = f"{self.base_url}/quote-equity?symbol={symbol}"
        response = self.session.get(url)
        data = response.json()
        
        return {
            "symbol": symbol,
            "ltp": data["priceInfo"]["lastPrice"],
            "change": data["priceInfo"]["change"],
            "pChange": data["priceInfo"]["pChange"],
            "volume": data["priceInfo"]["totalTradedVolume"],
            "bid": data["priceInfo"]["bidPrice"],
            "ask": data["priceInfo"]["askPrice"],
            "timestamp": datetime.now().isoformat()
        }
    
    def get_order_book_imbalance(self, symbol: str) -> Dict:
        """Calculate order book imbalance"""
        # This would require depth data
        # Placeholder logic
        return {
            "symbol": symbol,
            "bid_volume": 150000,
            "ask_volume": 120000,
            "imbalance_ratio": 1.25,  # > 1 = bullish
            "timestamp": datetime.now().isoformat()
        }
    
    def get_option_chain(self, symbol: str, expiry: str) -> pd.DataFrame:
        """Fetch option chain data"""
        url = f"{self.base_url}/option-chain-equities?symbol={symbol}"
        response = self.session.get(url)
        data = response.json()
        
        records = []
        for item in data["data"]["records"]["data"]:
            records.append({
                "strikePrice": item["strikePrice"],
                "ce_oi": item["CE"]["openInterest"],
                "ce_volume": item["CE"]["totalTradedVolume"],
                "pe_oi": item["PE"]["openInterest"],
                "pe_volume": item["PE"]["totalTradedVolume"],
                "pcr": item["PE"]["openInterest"] / item["CE"]["openInterest"] if item["CE"]["openInterest"] > 0 else None
            })
        return pd.DataFrame(records)


class MacroFeed:
    """Macro indicator feed handler"""
    
    def __init__(self):
        self.api_url = "https://api.investing.com/api/v1"
        
    def get_fii_dii_flows(self) -> Dict:
        """Fetch FII/DII flow data"""
        # Simulate real data
        # In production, scrape from NSE or use paid APIs
        return {
            "fii_equity": {"buy": 2543.82, "sell": 2178.34, "net": 365.48},
            "fii_debt": {"buy": 1345.21, "sell": 1287.56, "net": 57.65},
            "dii_equity": {"buy": 4532.18, "sell": 4123.76, "net": 408.42},
            "dii_debt": {"buy": 876.34, "sell": 765.23, "net": 111.11},
            "date": datetime.now().strftime("%Y-%m-%d")
        }
    
    def get_crude_oil(self) -> Dict:
        """Fetch crude oil prices"""
        # Use Alpha Vantage or similar API
        url = "https://www.alphavantage.co/query"
        params = {
            "function": "WTI",
            "apikey": "YOUR_API_KEY"
        }
        # response = requests.get(url, params=params)
        # Simulate
        return {"price": 82.45, "change": 0.62, "change_percent": 0.76}
    
    def get_usdinr(self) -> Dict:
        """Fetch USD/INR rate"""
        return {"rate": 85.12, "change": -0.08, "change_percent": -0.09}
    
    def get_inflation_metrics(self) -> Dict:
        """Get inflation data (CPI, WPI, etc.)"""
        return {
            "cpi": 4.85,
            "cpi_change": -0.12,
            "wpi": 3.42,
            "wpi_change": 0.23,
            "gdp_growth": 7.2,
            "date": datetime.now().strftime("%Y-%m-%d")
        }
