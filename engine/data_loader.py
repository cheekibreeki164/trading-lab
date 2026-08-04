import pandas as pd
import os

def load_stock_universe(file_path: str = "data/stocks.csv") -> list:
    if not os.path.exists(file_path):
        return ["RELIANCE.NS", "SBIN.NS", "HAL.NS", "TATAMOTORS.NS"]
    df = pd.read_csv(file_path)
    if "Ticker" in df.columns:
        return df["Ticker"].dropna().unique().tolist()
    return []