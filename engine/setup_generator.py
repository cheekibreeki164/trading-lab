def generate_daytrade_setup(price: float, atr: float, total_capital: float = 10000.0, leverage: float = 1.0, stop_loss_pct: float = 0.02, rr_ratio: float = 2.0) -> dict:
    """
    Direct % Stop Loss & Max Purchasing Power Sizer
    """
    if not price or price <= 0:
        return {
            "Entry": 0, "Stop Loss": 0, "Target": 0, "Max Rupee Risk": 0, 
            "Shares to Buy": 0, "Total Position Value": 0, "Margin Required": 0, "Leverage": f"{leverage}x"
        }
        
    effective_capital = total_capital * leverage
    
    # 2% Price Drop Stop Loss
    stop_loss = round(price * (1 - stop_loss_pct), 2)
    target = round(price * (1 + (stop_loss_pct * rr_ratio)), 2)
    
    # Buy maximum shares possible with available margin/buying power
    shares_to_buy = int(effective_capital // price)
    if shares_to_buy == 0:
        shares_to_buy = 1
        
    total_trade_value = round(shares_to_buy * price, 2)
    margin_required = round(total_trade_value / leverage, 2)
    
    # Rupee risk if 2% stop loss hits on full leveraged position
    max_rupee_risk = round(shares_to_buy * (price - stop_loss), 2)

    return {
        "Entry": price,
        "Stop Loss": stop_loss,
        "Target": target,
        "Max Rupee Risk": max_rupee_risk,
        "Shares to Buy": shares_to_buy,
        "Total Position Value": total_trade_value,
        "Margin Required": margin_required,
        "Leverage": f"{int(leverage)}x"
    }