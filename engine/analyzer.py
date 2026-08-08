import pandas as pd

def extract_latest_condition(df: pd.DataFrame, ticker: str) -> dict:
    if df.empty or len(df) < 15:
        return {}
    
    latest = df.iloc[-1]
    
    def safe_float(val):
        if hasattr(val, 'item'):
            return float(val.item())
        return float(val)

    close_price = safe_float(latest['Close'])
    sma20 = safe_float(latest['SMA20']) if pd.notna(latest['SMA20']) else close_price
    sma50 = safe_float(latest['SMA50']) if pd.notna(latest['SMA50']) else close_price
    vwap = safe_float(latest['VWAP']) if pd.notna(latest['VWAP']) else close_price
    rsi = safe_float(latest['RSI']) if pd.notna(latest['RSI']) else 50.0
    rvol = safe_float(latest['RVOL']) if pd.notna(latest['RVOL']) else 1.0
    atr = safe_float(latest['ATR']) if pd.notna(latest['ATR']) else close_price * 0.01
    macd = safe_float(latest['MACD']) if pd.notna(latest['MACD']) else 0.0
    macd_sig = safe_float(latest['MACD_Signal']) if pd.notna(latest['MACD_Signal']) else 0.0
    daily_change = safe_float(latest['Daily_Change_Pct']) if pd.notna(latest['Daily_Change_Pct']) else 0.0
    
    is_macd_bullish = macd > macd_sig
    is_trend_bullish = close_price > vwap and close_price > sma20
    is_momentum_hot = 50 <= rsi <= 75
    is_volume_breakout = rvol >= 1.1
    
    is_buy_candidate = is_trend_bullish and is_momentum_hot and is_volume_breakout and is_macd_bullish

    return {
        "Ticker": ticker,
        "Price": round(close_price, 2),
        "Daily_Change": round(daily_change, 2),
        "SMA20": round(sma20, 2),
        "SMA50": round(sma50, 2),
        "VWAP": round(vwap, 2),
        "RSI": round(rsi, 2),
        "ATR": round(atr, 2),
        "RVOL": round(rvol, 2),
        "MACD_Bullish": is_macd_bullish,
        "Preferred_Buy": is_buy_candidate
    }