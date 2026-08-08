import pandas as pd

def extract_latest_condition(df: pd.DataFrame, ticker: str) -> dict:
    if df.empty or len(df) < 10:
        return {}
    
    latest = df.iloc[-1]
    
    def safe_float(val):
        if hasattr(val, 'item'):
            return float(val.item())
        try:
            return float(val)
        except Exception:
            return 0.0

    close_price = safe_float(latest['Close'])
    sma20 = safe_float(latest.get('SMA20', close_price))
    sma50 = safe_float(latest.get('SMA50', close_price))
    sma200 = safe_float(latest.get('SMA200', close_price))
    vwap = safe_float(latest.get('VWAP', close_price))
    rsi = safe_float(latest.get('RSI', 50))
    rvol = safe_float(latest.get('RVOL', 1.0))
    atr = safe_float(latest.get('ATR', close_price * 0.02))
    macd = safe_float(latest.get('MACD', 0))
    macd_sig = safe_float(latest.get('MACD_Signal', 0))
    daily_change = safe_float(latest.get('Daily_Change_Pct', 0))
    
    is_macd_bullish = macd > macd_sig
    is_trend_bullish = close_price > sma20 > sma50 and close_price > vwap
    is_momentum_hot = 55 <= rsi <= 72
    is_volume_breakout = rvol >= 1.3
    
    is_buy_candidate = is_trend_bullish and is_momentum_hot and is_volume_breakout and is_macd_bullish

    return {
        "Ticker": ticker,
        "Price": round(close_price, 2),
        "Daily_Change": round(daily_change, 2),
        "SMA20": round(sma20, 2),
        "SMA50": round(sma50, 2),
        "SMA200": round(sma200, 2),
        "VWAP": round(vwap, 2),
        "RSI": round(rsi, 2),
        "ATR": round(atr, 2),
        "RVOL": round(rvol, 2),
        "MACD_Bullish": is_macd_bullish,
        "Preferred_Buy": is_buy_candidate
    }