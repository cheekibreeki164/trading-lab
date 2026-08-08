import yfinance as yf
import pandas as pd

def fetch_batch_market_data(tickers: list) -> dict:
    try:
        # Download 5-day history with 1-minute interval for live price updates
        data = yf.download(tickers, period="5d", interval="1m", group_by='ticker', threads=True, progress=False)
        stock_dfs = {}
        
        if len(tickers) == 1:
            ticker = tickers[0]
            df = data.dropna()
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            if not df.empty:
                stock_dfs[ticker] = df
        else:
            for ticker in tickers:
                try:
                    if ticker in data.columns.levels[0]:
                        df = data[ticker].dropna()
                        if not df.empty and len(df) >= 15:
                            stock_dfs[ticker] = df
                except Exception:
                    continue
                    
        return stock_dfs
    except Exception as e:
        print(f"Error fetching batch data: {e}")
        return {}