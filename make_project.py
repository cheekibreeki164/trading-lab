import os

files = {
    "engine/setup_generator.py": '''def generate_trade_setup(price: float, atr: float, total_capital: float = 10000.0, leverage: float = 1.0, max_risk_pct: float = 0.02) -> dict:
    if not price or price <= 0:
        return {
            "Entry": 0, "Stop Loss": 0, "Target": 0, "Max Rupee Risk": 0, 
            "Target Rupee Risk": 0, "Actual Account Risk Pct": 0, "Shares to Buy": 0, 
            "Total Position Value": 0, "Margin Required": 0, "Leverage": f"{leverage}x", "SL_Pct": 0
        }

    # Total buying power using 100% capital with leverage
    buying_power = total_capital * leverage
    
    # 1. Buy 100% capacity based on buying power
    shares_to_buy = int(buying_power // price)
    if shares_to_buy < 1:
        shares_to_buy = 1
        
    total_trade_value = round(shares_to_buy * price, 2)
    margin_required = round(total_trade_value / leverage, 2)
    
    # 2. Set total risk budget (e.g. 2% of total_capital = ₹80)
    target_rupee_risk = total_capital * max_risk_pct
    
    # 3. Calculate Stop Loss distance per share to match ₹ risk strictly
    risk_per_share = target_rupee_risk / shares_to_buy
    
    stop_loss = round(price - risk_per_share, 2)
    target = round(price + (risk_per_share * 2.0), 2)
    
    sl_distance_pct = round(((price - stop_loss) / price) * 100, 2)
    
    actual_rupee_risk = round(shares_to_buy * risk_per_share, 2)
    actual_risk_pct = round((actual_rupee_risk / total_capital) * 100, 2)

    return {
        "Entry": price,
        "Stop Loss": max(stop_loss, 0.1),
        "Target": target,
        "Max Rupee Risk": actual_rupee_risk,
        "Target Rupee Risk": round(target_rupee_risk, 2),
        "Actual Account Risk Pct": actual_risk_pct,
        "Shares to Buy": shares_to_buy,
        "Total Position Value": total_trade_value,
        "Margin Required": margin_required,
        "Leverage": f"{int(leverage)}x",
        "SL_Pct": sl_distance_pct
    }'''
}

for path, content in files.items():
    folder = os.path.dirname(path)
    if folder:
        os.makedirs(folder, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

print("✅ SUCCESS: 100% Capital allocation logic updated!")