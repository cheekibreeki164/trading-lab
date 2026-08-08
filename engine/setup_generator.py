def generate_daytrade_setup(price: float, atr: float, total_capital: float = 10000.0, leverage: float = 1.0, max_risk_pct: float = 0.02, rr_ratio: float = 2.0) -> dict:
    """
    Calculates 1x or 5x Leveraged Intraday Trade Execution Parameters
    """
    if not price or not atr or price <= 0:
        return {
            "Entry": 0, "Stop Loss": 0, "Target": 0, "Max Rupee Risk": 0, 
            "Shares to Buy": 0, "Total Position Value": 0, "Margin Required": 0, "Leverage": f"{leverage}x"
        }
        
    effective_capital = total_capital * leverage
    stop_loss = round(price - (1.2 * atr), 2)
    risk_per_share = round(price - stop_loss, 2)
    
    if risk_per_share <= 0:
        risk_per_share = round(price * 0.01, 2)
        stop_loss = round(price - risk_per_share, 2)

    target = round(price + (risk_per_share * rr_ratio), 2)
    max_rupee_risk = round(total_capital * max_risk_pct, 2)
    
    # Calculate quantity based on risk limit vs purchasing power limit
    risk_based_qty = int(max_rupee_risk // risk_per_share) if risk_per_share > 0 else 0
    max_purchasing_qty = int(effective_capital // price)
    
    # Final shares to buy capped by available 5x capital
    shares_to_buy = min(risk_based_qty, max_purchasing_qty) if leverage > 1.0 else risk_based_qty
    if shares_to_buy == 0 and max_purchasing_qty > 0:
        shares_to_buy = 1
        
    total_trade_value = round(shares_to_buy * price, 2)
    margin_required = round(total_trade_value / leverage, 2)

    return {
        "Entry": price,
        "Stop Loss": stop_loss,
        "Target": target,
        "Risk Per Share": risk_per_share,
        "Max Rupee Risk": max_rupee_risk,
        "Shares to Buy": shares_to_buy,
        "Total Position Value": total_trade_value,
        "Margin Required": margin_required,
        "Leverage": f"{int(leverage)}x"
    }