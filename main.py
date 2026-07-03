import yfinance as yf
import pandas as pd
import pandas_ta as ta
import json
import os
import time
from datetime import datetime

# ------------------- SCANNER LOGIC -------------------
def check_fundamentals(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        pe = info.get('trailingPE', 100)
        roe = info.get('returnOnEquity', 0)
        debt = info.get('debtToEquity', 999)
        margin = info.get('profitMargins', 0)
        growth = info.get('revenueGrowth', 0)
        if pe is None or roe is None: return False
        score = 0
        if pe < 30: score += 1
        if roe > 0.15: score += 1
        if debt < 1.5: score += 1
        if margin > 0.10: score += 1
        if growth > 0.10: score += 1
        return score >= 3
    except:
        return False

def scan_single_stock(ticker):
    try:
        timeframes = ['1h', '4h', '1d']
        results = {}
        final_signal = False
        for tf in timeframes:
            df = yf.download(ticker, period='max', interval=tf, progress=False)
            if len(df) < 250: continue
            df['EMA_200'] = ta.ema(df['Close'], length=200)
            prev_close = df['Close'].iloc[-2]; curr_close = df['Close'].iloc[-1]
            prev_ema = df['EMA_200'].iloc[-2]; curr_ema = df['EMA_200'].iloc[-1]
            ema_cross = (prev_close < prev_ema) and (curr_close > curr_ema)
            
            # Bullish Patterns
            engulf = ta.cdl_engulfing(df['Open'], df['High'], df['Low'], df['Close'])
            bull_engulf = False
            if engulf is not None and not engulf.empty:
                bull_engulf = engulf.iloc[-1] > 0 if len(engulf) > 0 else False
            
            hammer = ta.cdl_hammer(df['Open'], df['High'], df['Low'], df['Close'])
            bull_hammer = False
            if hammer is not None and not hammer.empty:
                bull_hammer = hammer.iloc[-1] > 0 if len(hammer) > 0 else False
            
            dragon = ta.cdl_dragonfly_doji(df['Open'], df['High'], df['Low'], df['Close'])
            bull_dragon = False
            if dragon is not None and not dragon.empty:
                bull_dragon = dragon.iloc[-1] > 0 if len(dragon) > 0 else False
            
            pattern_mila = bull_engulf or bull_hammer or bull_dragon
            tf_signal = ema_cross and pattern_mila
            results[tf] = {'Signal': tf_signal}
            if tf_signal: final_signal = True

        funda_strong = check_fundamentals(ticker)
        buy_decision = final_signal and funda_strong

        # Company Name fetch
        try:
            name = yf.Ticker(ticker).info.get('longName', ticker)[:30]
        except:
            name = ticker

        return {
            'Ticker': ticker,
            'Name': name,
            '1H_Signal': results.get('1h', {}).get('Signal', False),
            '4H_Signal': results.get('4h', {}).get('Signal', False),
            'Daily_Signal': results.get('1d', {}).get('Signal', False),
            'Fundamentals': funda_strong,
            'Final_Buy': buy_decision,
            'Scanned_At': datetime.now().strftime("%Y-%m-%d %H:%M")
        }
    except Exception as e:
        print(f"Error in {ticker}: {e}")
        return None

def run_full_scan():
    # 🔥 YAHAN APNE STOCKS KI LIST DAALO (Demo list)
    tickers = ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "ICICIBANK.NS", "INFY.NS", 
               "HINDUNILVR.NS", "ITC.NS", "SBIN.NS", "BHARTIARTL.NS", "KOTAKBANK.NS"]
    
    all_results = []
    print(f"🔄 Scanning {len(tickers)} stocks...")
    for i, t in enumerate(tickers):
        print(f"Scanning {i+1}/{len(tickers)}: {t}")
        data = scan_single_stock(t)
        if data: all_results.append(data)
        time.sleep(1)
    
    df = pd.DataFrame(all_results)
    return df

if __name__ == "__main__":
    print("🚀 Starting Stock Scan...")
    df = run_full_scan()
    
    # ✅ JSON save karo (Aapke existing 'data' folder mein)
    os.makedirs('data', exist_ok=True)  # Ensure folder exists
    records = df.to_dict(orient='records')
    with open('data/signals.json', 'w') as f:
        json.dump(records, f, indent=2, default=str)
    
    print(f"✅ JSON saved to data/signals.json with {len(records)} records")
