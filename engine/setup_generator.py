def generate_daytrade_setup(price: float, atr: float, total_capital: float = 10000.0, max_risk_pct: float = 0.02, rr_ratio: float = 2.0) -> dict:
    """
    Strict 2% Capital Risk Management & 2:1 Earn:Risk Ratio Calculator
    """
    if not price or not atr or price <= 0:
        return {"Entry": 0, "Stop Loss": 0, "Target": 0, "Max Risk (₹)": 0, "Shares to Buy": 0, "Risk:Reward": "2:1"}
        
    stop_loss = round(price - (1.2 * atr), 2)
    risk_per_share = round(price - stop_loss, 2)
    
    if risk_per_share <= 0:
        risk_per_share = round(price * 0.01, 2)
        stop_loss = round(price - risk_per_share, 2)

    target = round(price + (risk_per_share * rr_ratio), 2)
    max_rupee_risk = round(total_capital * max_risk_pct, 2)
    shares_to_buy = int(max_rupee_risk // risk_per_share)
    total_trade_value = round(shares_to_buy * price, 2)

    return {
        "Entry": price,
        "Stop Loss": stop_loss,
        "Target": target,
        "Risk Per Share": risk_per_share,
        "Max Rupee Risk": max_rupee_risk,
        "Shares to Buy": shares_to_buy,
        "Total Position Value": total_trade_value,
        "Risk:Reward": "2:1"
    }