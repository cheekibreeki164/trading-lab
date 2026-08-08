def generate_daytrade_setup(price: float, atr: float, total_capital: float = 10000.0, leverage: float = 1.0, max_risk_pct: float = 0.02, rr_ratio: float = 2.0) -> dict:
    if not price or price <= 0:
        return {
            "Entry": 0, "Stop Loss": 0, "Target": 0, "Max Rupee Risk": 0, 
            "Shares to Buy": 0, "Total Position Value": 0, "Margin Required": 0, "Leverage": f"{leverage}x", "SL_Pct": 0
        }
        
    effective_capital = total_capital * leverage
    max_rupee_risk = round(total_capital * max_risk_pct, 2)
    
    shares_to_buy = int(effective_capital // price)
    if shares_to_buy == 0:
        shares_to_buy = 1
        
    total_trade_value = round(shares_to_buy * price, 2)
    margin_required = round(total_trade_value / leverage, 2)
    
    risk_per_share = max_rupee_risk / shares_to_buy
    stop_loss = round(price - risk_per_share, 2)
    target = round(price + (risk_per_share * rr_ratio), 2)
    
    sl_distance_pct = round(((price - stop_loss) / price) * 100, 2)

    return {
        "Entry": price,
        "Stop Loss": stop_loss,
        "Target": target,
        "Max Rupee Risk": max_rupee_risk,
        "Shares to Buy": shares_to_buy,
        "Total Position Value": total_trade_value,
        "Margin Required": margin_required,
        "Leverage": f"{int(leverage)}x",
        "SL_Pct": sl_distance_pct
    }