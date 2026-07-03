# main.py (ya jahan bhi aapka scanner run ho raha hai)
import json
import os
import pandas as pd
from src.scanner import run_full_scan  # Maan lo aapka scanner function yahan hai

def save_signals_to_json(df):
    """DataFrame ko JSON mein convert karo aur dashboard folder mein save karo"""
    # Ensure folder exists
    os.makedirs('dashboard/data', exist_ok=True)
    
    # Convert DataFrame to list of dicts
    records = df.to_dict(orient='records')
    
    # Save as JSON
    with open('dashboard/data/signals.json', 'w') as f:
        json.dump(records, f, indent=2, default=str)  # default=str for datetime
    
    print(f"✅ JSON saved to dashboard/data/signals.json with {len(records)} records")

if __name__ == "__main__":
    print("🚀 Starting Stock Scan...")
    df_results = run_full_scan()  # Ye aapka existing function hai
    
    if not df_results.empty:
        save_signals_to_json(df_results)
        print("✅ Scan complete and JSON updated!")
    else:
        print("⚠️ No results, saving empty JSON")
        # Empty array save karo taaki dashboard crash na ho
        with open('dashboard/data/signals.json', 'w') as f:
            json.dump([], f)
