import math

# Exact Lot Sizes for major NSE F&O Stocks & Indices
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

DEFAULT_LOT_SIZE = 250  # Default FnO lot size fallback

def round_to_strike(price: float, step: float = 50.0) -> float:
    return round(price / step) * step

def generate_option_setup(symbol: str, spot_price: float, atr: float, capital: float, max_risk_pct: float, option_type: str = "CE", strike_mode: str = "ATM") -> dict:
    if not spot_price or spot_price <= 0:
        return {}
    
    # 1. Get exact Lot Size for the specific stock/index
    lot_size = LOT_SIZES.get(symbol, DEFAULT_LOT_SIZE)
    
    # 2. Determine Strike Step based on stock price magnitude
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
        est_premium_pct = 0.035  # ~3.5% of spot price for ITM premium
    else:  # ATM
        strike = atm_strike
        delta = 0.50
        est_premium_pct = 0.020  # ~2.0% of spot price for ATM premium

    estimated_premium = round(spot_price * est_premium_pct, 2)
    cost_per_lot = estimated_premium * lot_size
    
    # 3. Capital Allocation for Options (deploy up to 100% account balance)
    lots_to_buy = int(capital // cost_per_lot) if cost_per_lot > 0 else 0
    
    if lots_to_buy < 1:
        lots_to_buy = 1  # Minimum 1 Lot if capital allows or forced minimum
        
    total_quantity = lots_to_buy * lot_size
    total_premium_required = round(total_quantity * estimated_premium, 2)
    
    # 4. Strictly cap risk at max_risk_pct of total account balance (e.g. 2% of ₹4,000 = ₹80)
    target_account_loss = capital * max_risk_pct
    
    # Calculate SL points per option unit
    premium_sl_drop = round(target_account_loss / total_quantity, 2) if total_quantity > 0 else 1.0
    option_sl_price = max(round(estimated_premium - premium_sl_drop, 2), 0.50)
    option_target_price = round(estimated_premium + (premium_sl_drop * 2.0), 2)
    
    actual_rupee_risk = round(premium_sl_drop * total_quantity, 2)
    actual_risk_pct = round((actual_rupee_risk / capital) * 100, 2)
    
    return {
        "Instrument": f"{int(strike)} {option_type}",
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
        "Max Rupee Risk": actual_rupee_risk,
        "Risk Pct": actual_risk_pct
    }