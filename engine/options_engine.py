import math
import numpy as np

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

def norm_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))

def norm_pdf(x: float) -> float:
    return math.exp(-0.5 * x * x) / math.sqrt(2.0 * math.pi)

def black_scholes_merton(S: float, K: float, T: float, r: float, sigma: float, option_type: str = "CE") -> dict:
    if S <= 0 or K <= 0 or T <= 0 or sigma <= 0:
        return {"premium": 0.0, "delta": 0.5, "gamma": 0.0, "theta": 0.0, "vega": 0.0}

    d1 = (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
    d2 = d1 - sigma * math.sqrt(T)

    pdf_d1 = norm_pdf(d1)

    if option_type == "CE":
        premium = S * norm_cdf(d1) - K * math.exp(-r * T) * norm_cdf(d2)
        delta = norm_cdf(d1)
        theta = (- (S * pdf_d1 * sigma) / (2 * math.sqrt(T)) - r * K * math.exp(-r * T) * norm_cdf(d2)) / 365.0
    else:  # PE
        premium = K * math.exp(-r * T) * norm_cdf(-d2) - S * norm_cdf(-d1)
        delta = norm_cdf(d1) - 1.0
        theta = (- (S * pdf_d1 * sigma) / (2 * math.sqrt(T)) + r * K * math.exp(-r * T) * norm_cdf(-d2)) / 365.0

    gamma = pdf_d1 / (S * sigma * math.sqrt(T))
    vega = (S * pdf_d1 * math.sqrt(T)) / 100.0

    return {
        "premium": max(round(premium, 2), 0.5),
        "delta": round(delta, 4),
        "gamma": round(gamma, 6),
        "theta": round(theta, 2),
        "vega": round(vega, 2)
    }

def compute_greeks_decay_curve(S: float, K: float, sigma: float, option_type: str = "CE", r: float = 0.07, max_dte: int = 30) -> dict:
    dtes = list(range(max_dte, 0, -1))
    premiums, deltas, thetas = [], [], []

    for dte in dtes:
        T = dte / 365.0
        res = black_scholes_merton(S=S, K=K, T=T, r=r, sigma=sigma, option_type=option_type)
        premiums.append(res["premium"])
        deltas.append(abs(res["delta"]))
        thetas.append(res["theta"])

    return {
        "DTE": dtes,
        "Premium": premiums,
        "Delta": deltas,
        "Theta": thetas
    }

def round_to_strike(price: float, step: float = 50.0) -> float:
    return round(price / step) * step

def compute_historical_volatility(df, window: int = 30) -> float:
    if df is None or len(df) < 5:
        return 0.25
    
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
    elif strike_mode == "OTM":
        strike = atm_strike + step if option_type == "CE" else atm_strike - step
    else:
        strike = atm_strike

    sigma = compute_historical_volatility(df_history)
    T = max(days_to_expiry, 1) / 365.0
    
    bsm_res = black_scholes_merton(S=spot_price, K=strike, T=T, r=risk_free_rate, sigma=sigma, option_type=option_type)
    bsm_premium = bsm_res["premium"]
    bsm_delta = abs(bsm_res["delta"])
    
    cost_per_lot = bsm_premium * lot_size
    lots_to_buy = int(capital // cost_per_lot) if cost_per_lot > 0 else 0
    if lots_to_buy < 1:
        lots_to_buy = 1
        
    total_quantity = lots_to_buy * lot_size
    total_premium_required = round(total_quantity * bsm_premium, 2)
    
    target_account_loss = capital * max_risk_pct
    premium_sl_drop = round(target_account_loss / total_quantity, 2) if total_quantity > 0 else 1.0
    
    option_sl_price = max(round(bsm_premium - premium_sl_drop, 2), 0.50)
    option_target_price = round(bsm_premium + (premium_sl_drop * 2.0), 2)
    
    actual_rupee_risk = round(premium_sl_drop * total_quantity, 2)
    actual_risk_pct = round((actual_rupee_risk / capital) * 100, 2)

    decay_curve = compute_greeks_decay_curve(S=spot_price, K=strike, sigma=sigma, option_type=option_type, r=risk_free_rate)
    
    return {
        "Instrument": f"{int(strike)} {option_type}",
        "Strike": strike,
        "Option Type": option_type,
        "BSM Premium": bsm_premium,
        "BSM Delta": bsm_delta,
        "BSM Gamma": bsm_res["gamma"],
        "BSM Theta": bsm_res["theta"],
        "BSM Vega": bsm_res["vega"],
        "Ann. Volatility": round(sigma * 100, 2),
        "Lot Size": lot_size,
        "Lots": lots_to_buy,
        "Total Qty": total_quantity,
        "Premium Required": total_premium_required,
        "Option SL": option_sl_price,
        "Option Target": option_target_price,
        "Max Rupee Risk": actual_rupee_risk,
        "Risk Pct": actual_risk_pct,
        "Decay Curve": decay_curve
    }