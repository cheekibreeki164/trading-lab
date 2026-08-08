def generate_trade_setup(price: float, atr: float, total_capital: float = 10000.0, leverage: float = 1.0, max_risk_pct: float = 0.02, trade_style: str = "Intraday") -> dict:
    if not price or price <= 0:
        return {
            "Entry": 0, "Stop Loss": 0, "Target": 0, "Max Rupee Risk": 0, 
            "Shares to Buy": 0, "Total Position Value": 0, "Margin Required": 0, "Leverage": f"{leverage}x", "SL_Pct": 0, "RR_Ratio": "1:2"
        }

    # Style Configurations
    if trade_style == "Intraday":
        sl_atr_mult = 1.0
        rr_ratio = 2.0
    elif trade_style == "Swing Trade":
        sl_atr_mult = 2.0
        rr_ratio = 2.5
    else:  # Long-Term
        sl_atr_mult = 3.0
        rr_ratio = 3.0

    effective_capital = total_capital * leverage
    max_rupee_risk = round(total_capital * max_risk_pct, 2)
    
    # Calculate Risk-based Position Sizing
    risk_per_share = atr * sl_atr_mult if atr > 0 else price * 0.02
    
    shares_by_risk = int(max_rupee_risk // risk_per_share) if risk_per_share > 0 else 1
    shares_by_capital = int(effective_capital // price)
    
    # Position size is constrained by whichever limit is stricter
    shares_to_buy = min(shares_by_risk, shares_by_capital)
    if shares_to_buy < 1:
        shares_to_buy = 1
        
    total_trade_value = round(shares_to_buy * price, 2)
    margin_required = round(total_trade_value / leverage, 2)
    
    stop_loss = round(price - risk_per_share, 2)
    target = round(price + (risk_per_share * rr_ratio), 2)
    
    sl_distance_pct = round(((price - stop_loss) / price) * 100, 2)

    return {
        "Entry": price,
        "Stop Loss": max(stop_loss, 0.1),
        "Target": target,
        "Max Rupee Risk": max_rupee_risk,
        "Shares to Buy": shares_to_buy,
        "Total Position Value": total_trade_value,
        "Margin Required": margin_required,
        "Leverage": f"{int(leverage)}x",
        "SL_Pct": sl_distance_pct,
        "RR_Ratio": f"1:{rr_ratio}"
    }