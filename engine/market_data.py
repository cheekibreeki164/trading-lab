import yfinance as yf
import pandas as pd

def fetch_batch_market_data(tickers: list, period: str = "6mo") -> dict:
    try:
        data = yf.download(tickers, period=period, group_by='ticker', threads=True, progress=False)
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