from engine.patterns import detect_chart_patterns
import pandas as pd

def score_market_condition(data: dict, df: pd.DataFrame = None) -> dict:
    if not data or 'Price' not in data or data['Price'] is None:
        return {"total": 0, "status": "NO DATA", "breakdown": {}, "pattern": "None"}
    
    scores = {}
    
    # 1. Trend & VWAP Score (Max 10)
    if data['Price'] > data['SMA20'] and data['Price'] > data.get('VWAP', 0):
        scores['Trend'] = 10
    elif data['Price'] > data['SMA20']:
        scores['Trend'] = 6
    else:
        scores['Trend'] = 2
        
    # 2. Momentum Score (Max 10)
    if 55 <= data['RSI'] <= 70:
        scores['Momentum'] = 10
    elif 45 <= data['RSI'] < 55:
        scores['Momentum'] = 7
    else:
        scores['Momentum'] = 3
        
    # 3. Volume Score (Max 10)
    if data['RVOL'] >= 1.5:
        scores['Volume'] = 10
    elif data['RVOL'] >= 1.0:
        scores['Volume'] = 6
    else:
        scores['Volume'] = 2
        
    # 4. Volatility Risk Score (Max 10)
    atr_pct = (data['ATR'] / data['Price']) * 100
    if atr_pct <= 3.0:
        scores['Risk'] = 10
    elif atr_pct <= 5.0:
        scores['Risk'] = 6
    else:
        scores['Risk'] = 3
        
    # 5. MACD Confirmation (Max 10)
    scores['MACD'] = 10 if data.get('MACD_Bullish', False) else 4
    
    # Pattern Analysis Bonus
    pattern_info = detect_chart_patterns(df) if df is not None else {"Pattern": "N/A", "Pattern_Score": 0}
    
    total_score = sum(scores.values()) + pattern_info['Pattern_Score']
    total_score = min(total_score, 50) # Cap at 50
    
    if data.get('Preferred_Buy', False) or total_score >= 42:
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