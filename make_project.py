import os

files = {
    "engine/market_data.py": '''import yfinance as yf
import pandas as pd

def fetch_batch_market_data(tickers: list, period: str = "3mo") -> dict:
    data_dict = {}
    if not tickers:
        return data_dict

    try:
        df_batch = yf.download(tickers, period=period, group_by='ticker', progress=False, auto_adjust=True)
        
        for t in tickers:
            try:
                if len(tickers) == 1:
                    df = df_batch.copy()
                else:
                    df = df_batch[t].copy() if t in df_batch else None

                if df is not None and not df.empty:
                    # Clean multi-index columns if present
                    if isinstance(df.columns, pd.MultiIndex):
                        df.columns = df.columns.get_level_values(0)
                    
                    if 'Close' in df.columns:
                        df = df.dropna(subset=['Close'])
                        if len(df) >= 5:
                            data_dict[t] = df
            except Exception:
                continue
    except Exception:
        pass

    return data_dict

def search_and_fetch_stock(symbol: str, period: str = "3mo"):
    symbol = symbol.strip().upper()
    if not symbol:
        return None, None
    
    # Format symbol for Indian market (NSE default)
    if not symbol.endswith('.NS') and not symbol.endswith('.BO'):
        ticker_symbol = f"{symbol}.NS"
    else:
        ticker_symbol = symbol

    # Method 1: yf.Ticker().history() (Most reliable for single tickers)
    try:
        t_obj = yf.Ticker(ticker_symbol)
        df = t_obj.history(period=period, auto_adjust=True)
        if df is not None and not df.empty and 'Close' in df.columns:
            df = df.dropna(subset=['Close'])
            if len(df) >= 5:
                return ticker_symbol, df
    except Exception:
        pass

    # Method 2: yf.download fallback
    try:
        df = yf.download(ticker_symbol, period=period, progress=False, auto_adjust=True)
        if df is not None and not df.empty:
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            if 'Close' in df.columns:
                df = df.dropna(subset=['Close'])
                if len(df) >= 5:
                    return ticker_symbol, df
    except Exception:
        pass
        
    return ticker_symbol, None
'''
}

for path, content in files.items():
    folder = os.path.dirname(path)
    if folder:
        os.makedirs(folder, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

print("✅ MARKET DATA SEARCH ENGINE FIXED!")