from engine.patterns import detect_chart_patterns
import pandas as pd

def score_market_condition(data: dict, df: pd.DataFrame = None) -> dict:
    if not data or 'Price' not in data or data['Price'] is None:
        return {"total": 0, "status": "NO DATA", "breakdown": {}, "pattern": "None"}
    
    scores = {}
    price = data['Price']
    
    scores['Trend_SMA20'] = 10 if price > data['SMA20'] else 2
    scores['Trend_SMA50'] = 8 if price > data['SMA50'] else 2
    scores['VWAP_Reclaim'] = 10 if price > data.get('VWAP', 0) else 2
    scores['RSI_Momentum'] = 10 if 55 <= data['RSI'] <= 70 else (5 if 40 <= data['RSI'] < 55 else 2)
    scores['RVOL_Surge'] = 10 if data['RVOL'] >= 1.5 else (6 if data['RVOL'] >= 1.1 else 2)
    scores['MACD_Bull'] = 7 if data.get('MACD_Bullish', False) else 2
    
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