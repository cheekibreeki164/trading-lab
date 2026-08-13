import math

LOT_SIZES = {
    "^NSEI": 25,          # NIFTY 50
    "^NSEBANK": 15,       # BANKNIFTY
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
    "AXISBANK.NS": 625,
    "LT.NS": 300,
    "MARUTI.NS": 100
}

DEFAULT_LOT_SIZE = 250

def round_to_strike(price: float, step: float = 50.0) -> float:
    return round(price / step) * step

def analyze_option_trend(spot_price: float, rsi: float, rvol: float, daily_change: float) -> dict:
    """Analyzes overall trend and directional bias for Options (CE vs PE dominance)."""
    if daily_change > 0.5 and rsi > 55:
        bias = "BULLISH CE"
        signal = "BUY CALL (CE)"
        strength = "STRONG UPWARD MOMENTUM"
        color = "#00E676"
    elif daily_change < -0.5 and rsi < 45:
        bias = "BEARISH PE"
        signal = "BUY PUT (PE)"
        strength = "STRONG DOWNWARD MOMENTUM"
        color = "#FF5252"
    else:
        bias = "SIDEWAYS / NEUTRAL"
        signal = "WAIT / NO CLEAR TREND"
        strength = "CONSOLIDATION"
        color = "#FFB300"

    return {
        "Bias": bias,
        "Signal": signal,
        "Strength": strength,
        "Color": color
    }

def generate_option_setup(symbol: str, spot_price: float, atr: float, capital: float, max_risk_pct: float, option_type: str = "CE", strike_mode: str = "ATM") -> dict:
    if not spot_price or spot_price <= 0:
        return {}
    
    lot_size = LOT_SIZES.get(symbol, DEFAULT_LOT_SIZE)
    
    # Dynamic Strike Steps
    if symbol in ["^NSEI", "NIFTY"]:
        step = 50.0
    elif symbol in ["^NSEBANK", "BANKNIFTY"]:
        step = 100.0
    elif spot_price < 500:
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
        est_premium_pct = 0.018 if "NSE" in symbol or symbol in ["NIFTY", "BANKNIFTY"] else 0.035
    else:  # ATM
        strike = atm_strike
        delta = 0.50
        est_premium_pct = 0.012 if "NSE" in symbol or symbol in ["NIFTY", "BANKNIFTY"] else 0.020

    estimated_premium = round(spot_price * est_premium_pct, 2)
    cost_per_lot = estimated_premium * lot_size
    
    lots_to_buy = int(capital // cost_per_lot) if cost_per_lot > 0 else 0
    if lots_to_buy < 1:
        lots_to_buy = 1  # Forced 1 lot min view
        
    total_quantity = lots_to_buy * lot_size
    total_premium_required = round(total_quantity * estimated_premium, 2)
    
    target_account_loss = capital * max_risk_pct
    premium_sl_drop = round(target_account_loss / total_quantity, 2) if total_quantity > 0 else 1.0
    option_sl_price = max(round(estimated_premium - premium_sl_drop, 2), 0.50)
    option_target_price = round(estimated_premium + (premium_sl_drop * 2.0), 2)
    
    actual_rupee_risk = round(premium_sl_drop * total_quantity, 2)
    actual_risk_pct = round((actual_rupee_risk / capital) * 100, 2)
    
    display_symbol = "NIFTY" if symbol == "^NSEI" else ("BANKNIFTY" if symbol == "^NSEBANK" else symbol.replace(".NS", ""))

    return {
        "Instrument": f"{display_symbol} {int(strike)} {option_type}",
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