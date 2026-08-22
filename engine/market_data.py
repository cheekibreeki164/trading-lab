import yfinance as yf
import pandas as pd
import requests
import io
import datetime

def fetch_google_finance_data(symbol: str) -> pd.DataFrame:
    """Direct Google Finance / NSE history scraper fallback"""
    clean_sym = symbol.replace(".NS", "").replace(".BO", "").upper()
    
    # Try fetching directly from Google Finance CSV endpoints
    urls = [
        f"https://query1.finance.yahoo.com/v7/finance/download/{clean_sym}.NS?period1=0&period2=9999999999&interval=1d&events=history",
        f"https://stooq.com/q/d/l/?s={clean_sym}.in&i=d"
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
    }

    for url in urls:
        try:
            resp = requests.get(url, headers=headers, timeout=5)
            if resp.status_code == 200 and len(resp.text) > 100:
                df = pd.read_csv(io.StringIO(resp.text))
                
                # Normalize column names
                df.columns = [c.capitalize() for c in df.columns]
                
                if 'Date' in df.columns:
                    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
                    df = df.dropna(subset=['Date']).set_index('Date').sort_index()
                
                # Ensure Close column exists and is numeric
                for col in ['Close', 'Open', 'High', 'Low']:
                    if col in df.columns:
                        df[col] = pd.to_numeric(df[col], errors='coerce')
                
                if 'Close' in df.columns and len(df.dropna(subset=['Close'])) >= 5:
                    return df.dropna(subset=['Close'])
        except Exception:
            continue
            
    return None

def search_and_fetch_stock(symbol: str, period: str = "3mo"):
    symbol = symbol.strip().upper()
    if not symbol:
        return None, None
    
    clean_symbol = symbol.replace(".NS", "").replace(".BO", "")
    ticker_ns = f"{clean_symbol}.NS"

    # Strategy 1: yfinance with session impersonation
    try:
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9'
        })
        
        t_obj = yf.Ticker(ticker_ns, session=session)
        df = t_obj.history(period=period, auto_adjust=True)
        if df is not None and not df.empty and 'Close' in df.columns and len(df) >= 5:
            return ticker_ns, df
    except Exception:
        pass

    # Strategy 2: Direct HTTP streaming endpoint fallback
    df_fallback = fetch_google_finance_data(clean_symbol)
    if df_fallback is not None and len(df_fallback) >= 5:
        # Slice last 90 days
        df_sliced = df_fallback.tail(90)
        return ticker_ns, df_sliced

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
