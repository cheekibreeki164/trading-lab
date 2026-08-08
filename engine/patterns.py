import pandas as pd

def detect_chart_patterns(df: pd.DataFrame) -> dict:
    if df.empty or len(df) < 20:
        return {"Pattern": "None", "Pattern_Score": 0}
    
    recent = df.tail(10)
    latest = df.iloc[-1]
    
    patterns_found = []
    bonus = 0
    
    if latest['Close'] > latest['VWAP'] and df.iloc[-2]['Close'] <= df.iloc[-2]['VWAP']:
        patterns_found.append("VWAP Reclaim 🔥")
        bonus += 5
        
    high_range = recent['High'].max()
    low_range = recent['Low'].min()
    price_spread = (high_range - low_range) / latest['Close'] * 100
    if price_spread <= 3.5 and latest['RVOL'] >= 1.2:
        patterns_found.append("Bull Flag Breakout 🚩")
        bonus += 5

    if latest['RVOL'] >= 2.0 and latest['Daily_Change_Pct'] > 1.5:
        patterns_found.append("Institutional Surge 🌊")
        bonus += 5

    pattern_name = " + ".join(patterns_found) if patterns_found else "Consolidation Range"
    return {"Pattern": pattern_name, "Pattern_Score": bonus}