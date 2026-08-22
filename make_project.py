import os

files = {
    "engine/market_data.py": '''import yfinance as yf
import pandas as pd
import pandas_datareader as pdr
import requests
import datetime

# Fix Yahoo Finance User-Agent blocking
yf.set_tz_cache_location("/tmp/yf_cache")

def get_session():
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    })
    return session

def search_and_fetch_stock(symbol: str, period: str = "3mo"):
    symbol = symbol.strip().upper()
    if not symbol:
        return None, None
    
    clean_symbol = symbol.replace(".NS", "").replace(".BO", "")
    ticker_ns = f"{clean_symbol}.NS"

    # Strategy 1: yfinance with custom session
    try:
        session = get_session()
        ticker_obj = yf.Ticker(ticker_ns, session=session)
        df = ticker_obj.history(period=period, auto_adjust=True)
        if df is not None and not df.empty and 'Close' in df.columns and len(df) >= 5:
            return ticker_ns, df
    except Exception:
        pass

    # Strategy 2: Stooq Data Reader (High Reliability Backup)
    try:
        # Stooq uses .IN suffix for Indian stocks
        stooq_symbol = f"{clean_symbol}.IN"
        end = datetime.datetime.now()
        start = end - datetime.timedelta(days=90)
        df_stooq = pdr.get_data_stooq(stooq_symbol, start=start, end=end)
        
        if df_stooq is not None and not df_stooq.empty:
            df_stooq = df_stooq.sort_index()
            # Stooq columns are capitalized (Open, High, Low, Close, Volume)
            if 'Close' in df_stooq.columns and len(df_stooq) >= 5:
                return ticker_ns, df_stooq
    except Exception:
        pass

    # Strategy 3: yf.download fallback
    try:
        df_dl = yf.download(ticker_ns, period=period, progress=False, auto_adjust=True)
        if df_dl is not None and not df_dl.empty:
            if isinstance(df_dl.columns, pd.MultiIndex):
                df_dl.columns = df_dl.columns.get_level_values(0)
            if 'Close' in df_dl.columns and len(df_dl) >= 5:
                return ticker_ns, df_dl
    except Exception:
        pass

    return ticker_ns, None

def fetch_batch_market_data(tickers: list, period: str = "3mo") -> dict:
    data_dict = {}
    if not tickers:
        return data_dict

    for t in tickers:
        sym, df = search_and_fetch_stock(t, period=period)
        if df is not None and not df.empty:
            data_dict[t] = df

    return data_dict
''',

    "requirements.txt": '''streamlit
pandas
numpy
yfinance
pandas-datareader
requests
plotly
'''
}

for path, content in files.items():
    folder = os.path.dirname(path)
    if folder:
        os.makedirs(folder, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

print("✅ MULTI-SOURCE MARKET DATA ENGINE DEPLOYED!")