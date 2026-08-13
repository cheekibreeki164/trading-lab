import math

LOT_SIZES = {
    "NIFTY": 25,
    "BANKNIFTY": 15,
    "FINNIFTY": 25,
    "RELIANCE.NS": 250,
    "TCS.NS": 175,
    "HDFCBANK.NS": 550,
    "ICICIBANK.NS": 700,
    "SBIN.NS": 750,
    "BHARTIARTL.NS": 475,
    "TATAMOTORS.NS": 1425,
    "INFY.NS": 400,
    "HAL.NS": 300,
    "TATAINVEST.NS": 100,
}

DEFAULT_LOT_SIZE = 500  # Fallback for stock options without exact spec

def round_to_strike(price: float, step: float = 50.0) -> float:
    return round(price / step) * step

def generate_option_setup(spot_price: float, atr: float, capital: float, max_risk_pct: float, option_type: str = "CE", strike_mode: str = "ATM") -> dict:
    if not spot_price or spot_price <= 0:
        return {}
    
    # 1. Determine Strike Step based on stock price magnitude
    if spot_price < 500:
        step = 10.0
    elif spot_price < 1500:
        step = 20.0
    elif spot_price < 5000:
        step = 50.0
    else:
        step = 100.0

    atm_strike = round_to_strike(spot_price, step)
    
    if strike_mode == "ITM":
        strike = atm_strike - step if option_type == "CE" else atm_strike + step
        delta = 0.65
        est_premium_pct = 0.035  # ~3.5% of spot price
    else:  # ATM
        strike = atm_strike
        delta = 0.50
        est_premium_pct = 0.025  # ~2.5% of spot price

    estimated_premium = round(spot_price * est_premium_pct, 2)
    lot_size = DEFAULT_LOT_SIZE
    
    # 2. Capital Allocation & Lot Sizing
    cost_per_lot = estimated_premium * lot_size
    lots_to_buy = int(capital // cost_per_lot) if cost_per_lot > 0 else 0
    
    if lots_to_buy < 1:
        lots_to_buy = 1  # Minimum 1 Lot
        
    total_quantity = lots_to_buy * lot_size
    total_premium_required = round(total_quantity * estimated_premium, 2)
    
    # 3. Delta-adjusted Stop Loss
    target_account_loss = capital * max_risk_pct
    spot_sl_distance = (target_account_loss / (total_quantity * delta)) if total_quantity > 0 else (spot_price * 0.01)
    
    premium_sl_drop = round(spot_sl_distance * delta, 2)
    option_sl_price = max(round(estimated_premium - premium_sl_drop, 2), 0.5)
    option_target_price = round(estimated_premium + (premium_sl_drop * 2.0), 2)
    
    return {
        "Instrument": f"{strike} {option_type}",
        "Strike": strike,
        "Option Type": option_type,
        "Est. Premium": estimated_premium,
        "Lot Size": lot_size,
        "Lots": lots_to_buy,
        "Total Qty": total_quantity,
        "Premium Required": total_premium_required,
        "Option SL": option_sl_price,
        "Option Target": option_target_price,
        "Risk Per Lot": round(premium_sl_drop * lot_size, 2),
        "Max Rupee Risk": round(premium_sl_drop * total_quantity, 2),
        "Risk Pct": round(((premium_sl_drop * total_quantity) / capital) * 100, 2)
    }