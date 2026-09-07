import os
import pandas as pd
from dotenv import load_dotenv
from fredapi import Fred
import yfinance as yf

# Unlock the vault
load_dotenv()
API_KEY = os.getenv("FRED_API_KEY")

def get_macro_data():
    """Route 1: Pulls aggregate economic data from FRED (Macro)"""
    print("Fetching Macro Data (FRED)...")
    fred = Fred(api_key=API_KEY)
    
    # Using 2018 to present for a tighter dataset
    price_series = fred.get_series('CPIAUCSL', observation_start='2018-01-01')
    quantity_series = fred.get_series('GDPC1', observation_start='2018-01-01')
    
    df_macro = pd.DataFrame({
        'Price': price_series,
        'Quantity': quantity_series
    })
    
    return df_macro.dropna()

def get_micro_data(ticker="AAPL"):
    """Route 2: Pulls firm-level market data from Yahoo Finance (Micro)"""
    print(f"Fetching Micro Data for {ticker} (yfinance)...")
    
    # Connect to the specific company's data
    stock = yf.Ticker(ticker)
    
    # Pull the last 5 years of historical trading data
    hist = stock.history(period="5y")
    
    # For a micro market, we use Close Price as P, and Trading Volume as Q
    df_micro = pd.DataFrame({
        'Price': hist['Close'],
        'Quantity': hist['Volume']
    })
    
    return df_micro.dropna()

# --- Execution Block ---
# This tells Python to run these functions when we test the script
if __name__ == "__main__":
    # 1. Test Macro
    macro_df = get_macro_data()
    print("\n✅ --- MACROECONOMIC DATA (Whole Economy) ---")
    print(macro_df.head())
    print(f"Total Macro Rows: {len(macro_df)}")
    
    # 2. Test Micro (We are using Apple 'AAPL' as the default)
    micro_df = get_micro_data("AAPL")
    print("\n✅ --- MICROECONOMIC DATA (Single Firm: AAPL) ---")
    print(micro_df.head())
    print(f"Total Micro Rows: {len(micro_df)}")
    
    print("\n🚀 Both pipelines are fully operational!")