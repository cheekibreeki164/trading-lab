import pandas as pd

def extract_latest_condition(df: pd.DataFrame, ticker: str) -> dict:
    if df.empty or len(df) < 50:
        return {}
    
    latest = df.iloc[-1]
    
    def safe_float(val):
        if hasattr(val, 'item'):
            return float(val.item())
        return float(val)

    close_price = safe_float(latest['Close'])
    sma20 = safe_float(latest['SMA20'])
    sma50 = safe_float(latest['SMA50'])
    rsi = safe_float(latest['RSI'])
    rvol = safe_float(latest['RVOL'])
    atr = safe_float(latest['ATR'])
    macd = safe_float(latest['MACD'])
    macd_sig = safe_float(latest['MACD_Signal'])
    daily_change = safe_float(latest['Daily_Change_Pct'])
    
    is_macd_bullish = macd > macd_sig
    is_trend_bullish = close_price > sma20 > sma50
    is_momentum_hot = 55 <= rsi <= 72
    is_volume_breakout = rvol >= 1.3
    
    is_buy_candidate = is_trend_bullish and is_momentum_hot and is_volume_breakout and is_macd_bullish

    return {
        "Ticker": ticker,
        "Price": round(close_price, 2),
        "Daily_Change": round(daily_change, 2),
        "SMA20": round(sma20, 2),
        "SMA50": round(sma50, 2),
        "RSI": round(rsi, 2),
        "ATR": round(atr, 2),
        "RVOL": round(rvol, 2),
        "MACD_Bullish": is_macd_bullish,
        "Preferred_Buy": is_buy_candidate
    }