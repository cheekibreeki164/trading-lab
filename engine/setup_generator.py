def generate_trade_setup(price: float, atr: float, risk_reward: float = 2.0) -> dict:
    if not price or not atr:
        return {"Entry": 0, "Stop Loss": 0, "Target": 0, "Risk Reward": "N/A"}
        
    stop_loss = round(price - (1.5 * atr), 2)
    risk = price - stop_loss
    target = round(price + (risk * risk_reward), 2)
    return {"Entry": price, "Stop Loss": stop_loss, "Target": target, "Risk Reward": f"{risk_reward}:1"}