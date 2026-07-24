import requests
import json
from datetime import datetime

def fetch_macro():
    # Example static values (replace with API calls)
    return {
        "us_yield": "4.25%",
        "dxy": "105.3",
        "crude": "$82.5",
        "fii_dii": "FII +1200 Cr / DII +800 Cr",
        "fear_greed": "42 (Fear)"
    }

def fetch_news():
    # Example headlines (replace with NewsAPI, Bloomberg, Reuters feeds)
    return [
        {"source": "Bloomberg", "headline": "Fed hints at rate cuts", "sentiment": "Bullish"},
        {"source": "Reuters", "headline": "Crypto ETF inflows surge", "sentiment": "Bullish"},
        {"source": "CoinDesk", "headline": "Bitcoin whale transfers spike", "sentiment": "Neutral"}
    ]

def fetch_social():
    # Example social sentiment (replace with Twitter/Reddit APIs)
    return {
        "twitter_mentions": "12.4K (Bullish)",
        "reddit_sentiment": "65% Positive"
    }

def fetch_onchain():
    # Example on-chain metrics (replace with Glassnode/CryptoQuant APIs)
    return {
        "whale_inflows": "3.2K BTC",
        "stablecoin_activity": "USDT +450M minted",
        "exchange_reserves": "BTC reserves down 2%"
    }

def fetch_etf():
    # Example ETF flows (replace with World Gold Council/Bloomberg APIs)
    return {
        "gold_flows": "+$1.2B inflows",
        "btc_flows": "+$850M inflows"
    }

def fetch_confluence():
    # Example signals (replace with your agents logic)
    return [
        {"asset": "Gold (XAU/USD)", "signal": "🟢 Accumulate", "confidence": "74%", "bull": "Inflation hedge, central bank buying", "bear": "Fed tightening risk", "verdict": "Buy dips", "action": "Add"},
        {"asset": "Bitcoin (BTC/USD)", "signal": "🟢 Strong Buy", "confidence": "82%", "bull": "ETF inflows, whale accumulation", "bear": "SEC regulation risk", "verdict": "Accumulate", "action": "10% weight"},
        {"asset": "Ethereum (ETH/USD)", "signal": "🟡 Neutral", "confidence": "55%", "bull": "DeFi activity stable", "bear": "Gas fees + SEC risk", "verdict": "Hold", "action": "Wait"},
        {"asset": "Altcoins (SOL, ADA)", "signal": "🔴 Avoid", "confidence": "58%", "bull": "Low liquidity, hype cycles", "bear": "Pump/dump risk", "verdict": "Avoid", "action": "Exit"}
    ]

def update_signals():
    signals = {
        "macro": fetch_macro(),
        "news": fetch_news(),
        "social": fetch_social(),
        "onchain": fetch_onchain(),
        "etf": fetch_etf(),
        "confluence": fetch_confluence(),
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    with open("data/signals.json", "w") as f:
        json.dump(signals, f, indent=2)

if __name__ == "__main__":
    update_signals()
    print("signals.json updated successfully!")
