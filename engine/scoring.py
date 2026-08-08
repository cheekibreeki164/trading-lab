from engine.patterns import detect_chart_patterns
import pandas as pd

def score_market_condition(data: dict, df: pd.DataFrame = None, trade_style: str = "Intraday") -> dict:
    if not data or 'Price' not in data or data['Price'] is None:
        return {"total": 0, "status": "NO DATA", "breakdown": {}, "pattern": "None"}
    
    scores = {}
    price = data['Price']
    
    if trade_style == "Intraday":
        # Intraday prioritizes RVOL, VWAP, and short-term volatility/momentum
        scores['VWAP_Reclaim'] = 12 if price > data.get('VWAP', 0) else 3
        scores['RVOL_Surge'] = 12 if data['RVOL'] >= 1.5 else (8 if data['RVOL'] >= 1.1 else 2)
        scores['RSI_Momentum'] = 10 if 55 <= data['RSI'] <= 75 else 4
        scores['Short_Trend'] = 10 if price > data['SMA20'] else 3
        scores['MACD_Bull'] = 6 if data.get('MACD_Bullish', False) else 2
        
    elif trade_style == "Swing Trade":
        # Swing prioritizes 20/50 SMA trend, MACD alignment, and sustainable RSI
        scores['Trend_20_50'] = 15 if price > data['SMA20'] > data['SMA50'] else (8 if price > data['SMA20'] else 2)
        scores['MACD_Structure'] = 12 if data.get('MACD_Bullish', False) else 3
        scores['RSI_Health'] = 10 if 50 <= data['RSI'] <= 68 else 4
        scores['Volume_Support'] = 8 if data['RVOL'] >= 1.1 else 3
        scores['ATR_Risk'] = 5 if (data['ATR']/price)*100 <= 4.0 else 2

    else:  # Long-Term
        # Long-term prioritizes 200 SMA alignment, lower ATR volatility, and valuation safety
        scores['Trend_200SMA'] = 18 if price > data.get('SMA200', price) else 2
        scores['Trend_50SMA'] = 12 if price > data['SMA50'] else 4
        scores['Low_Volatility'] = 10 if (data['ATR']/price)*100 <= 3.0 else 4
        scores['RSI_Value'] = 10 if 40 <= data['RSI'] <= 62 else 3

    pattern_info = detect_chart_patterns(df) if df is not None else {"Pattern": "N/A", "Pattern_Score": 0}
    
    total_score = sum(scores.values()) + pattern_info['Pattern_Score']
    total_score = min(total_score, 50)
    
    if total_score >= 42:
        status = "MUST BUY 🔥"
    elif total_score >= 32:
        status = "WATCH 👁️"
    else:
        status = "WEAK ❌"
        
    return {
        "total": total_score, 
        "status": status, 
        "breakdown": scores, 
        "pattern": pattern_info['Pattern']
    }