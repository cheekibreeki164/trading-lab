import yfinance as yf
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

                if df is not None and not df.empty and 'Close' in df.columns:
                    df = df.dropna(subset=['Close'])
                    if len(df) >= 5:
                        data_dict[t] = df
            except Exception:
                continue
    except Exception:
        pass

    return data_dict
