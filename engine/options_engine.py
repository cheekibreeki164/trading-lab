import math
import numpy as np
from scipy.stats import norm

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

DEFAULT_LOT_SIZE = 250

def black_scholes_merton(S: float, K: float, T: float, r: float, sigma: float, option_type: str = "CE") -> dict:
    """
    Calculates theoretical Option Premium and Delta using Black-Scholes-Merton model.
    S: Spot Price
    K: Strike Price
    T: Time to Expiry (in years, e.g., 15/365)
    r: Risk-free rate (e.g., 0.07 for 7%)
    sigma: Volatility (annualized, e.g., 0.25 for 25%)
    """
    if S <= 0 or K <= 0 or T <= 0 or sigma <= 0:
        return {"premium": 0.0, "delta": 0.5, "d1": 0, "d2": 0}

    d1 = (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
    d2 = d1 - sigma * math.sqrt(T)

    if option_type == "CE":
        premium = S * norm.cdf(d1) - K * math.exp(-r * T) * norm.cdf(d2)
        delta = norm.cdf(d1)
    else:  # PE
        premium = K * math.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)
        delta = norm.cdf(d1) - 1.0

    return {
        "premium": max(round(premium, 2), 0.5),
        "delta": round(delta, 4),
        "d1": round(d1, 4),
        "d2": round(d2, 4)
    }

def round_to_strike(price: float, step: float = 50.0) -> float:
    return round(price / step) * step

def compute_historical_volatility(df, window: int = 30) -> float:
    """Computes 30-day annualized historical volatility from close prices."""
    if df is None or len(df) < 5:
        return 0.25  # Fallback default volatility (25%)
    
    log_returns = np.log(df['Close'] / df['Close'].shift(1)).dropna()
    daily_std = log_returns.tail(window).std()
    
    if np.isnan(daily_std) or daily_std <= 0:
        return 0.25
        
    annualized_vol = daily_std * np.sqrt(252)
    return float(annualized_vol)

def generate_option_setup(
    symbol: str, 
    spot_price: float, 
    atr: float, 
    capital: float, 
    max_risk_pct: float, 
    df_history = None,
    option_type: str = "CE", 
    strike_mode: str = "ATM",
    days_to_expiry: int = 15,
    risk_free_rate: float = 0.07
) -> dict:
    if not spot_price or spot_price <= 0:
        return {}
    
    lot_size = LOT_SIZES.get(symbol, DEFAULT_LOT_SIZE)
    
    # 1. Determine Strike Step based on stock price
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
    else:  # ATM
        strike = atm_strike

    # 2. Compute Volatility & Time to Expiry
    sigma = compute_historical_volatility(df_history)
    T = max(days_to_expiry, 1) / 365.0
    
    # 3. Apply Black-Scholes-Merton Engine
    bsm_res = black_scholes_merton(S=spot_price, K=strike, T=T, r=risk_free_rate, sigma=sigma, option_type=option_type)
    bsm_premium = bsm_res["premium"]
    bsm_delta = abs(bsm_res["delta"])
    
    # 4. Lot sizing based on BSM calculated premium
    cost_per_lot = bsm_premium * lot_size
    lots_to_buy = int(capital // cost_per_lot) if cost_per_lot > 0 else 0
    if lots_to_buy < 1:
        lots_to_buy = 1
        
    total_quantity = lots_to_buy * lot_size
    total_premium_required = round(total_quantity * bsm_premium, 2)
    
    # 5. Delta-Adjusted Account Risk Sizing (2% max account risk)
    target_account_loss = capital * max_risk_pct
    
    # Premium drop required to hit exact rupee loss
    premium_sl_drop = round(target_account_loss / total_quantity, 2) if total_quantity > 0 else 1.0
    
    option_sl_price = max(round(bsm_premium - premium_sl_drop, 2), 0.50)
    option_target_price = round(bsm_premium + (premium_sl_drop * 2.0), 2)
    
    actual_rupee_risk = round(premium_sl_drop * total_quantity, 2)
    actual_risk_pct = round((actual_rupee_risk / capital) * 100, 2)
    
    return {
        "Instrument": f"{int(strike)} {option_type}",
        "Strike": strike,
        "Option Type": option_type,
        "BSM Premium": bsm_premium,
        "BSM Delta": bsm_delta,
        "Ann. Volatility": round(sigma * 100, 2),
        "Lot Size": lot_size,
        "Lots": lots_to_buy,
        "Total Qty": total_quantity,
        "Premium Required": total_premium_required,
        "Option SL": option_sl_price,
        "Option Target": option_target_price,
        "Max Rupee Risk": actual_rupee_risk,
        "Risk Pct": actual_risk_pct
    }