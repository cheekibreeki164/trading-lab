# MCX Lot sizes and contract specifications
MCX_LOT_SIZES = {
    "GC=F": 100,      # Gold Regular (100 grams / oz conversion proxy)
    "SI=F": 30,       # Silver Regular (30 kg)
    "CL=F": 100,      # Crude Oil (100 barrels)
    "NG=F": 1250,     # Natural Gas (1250 mmBtu)
    "HG=F": 2500      # Copper (2500 kg)
}

MCX_NAMES = {
    "GC=F": "GOLD (MCX Futures)",
    "SI=F": "SILVER (MCX Futures)",
    "CL=F": "CRUDE OIL (MCX Futures)",
    "NG=F": "NATURAL GAS (MCX Futures)",
    "HG=F": "COPPER (MCX Futures)"
}

def analyze_mcx_trend(price: float, rsi: float, rvol: float, daily_change: float) -> dict:
    if daily_change > 0.5 and rsi > 55:
        bias = "BULLISH"
        signal = "BUY FUTURES / CE"
        strength = "STRONG UPWARD MOMENTUM"
        color = "#00E676"
    elif daily_change < -0.5 and rsi < 45:
        bias = "BEARISH"
        signal = "SELL FUTURES / BUY PE"
        strength = "STRONG DOWNWARD MOMENTUM"
        color = "#FF5252"
    else:
        bias = "SIDEWAYS"
        signal = "WAIT / NO CLEAR TREND"
        strength = "CONSOLIDATION"
        color = "#FFB300"

    return {
        "Bias": bias,
        "Signal": signal,
        "Strength": strength,
        "Color": color
    }

def generate_mcx_setup(symbol: str, price: float, atr: float, capital: float, max_risk_pct: float) -> dict:
    if not price or price <= 0:
        return {}

    lot_size = MCX_LOT_SIZES.get(symbol, 100)
    display_name = MCX_NAMES.get(symbol, symbol)

    # Calculate ATR-based Stop Loss and Target
    sl_distance = round(atr * 1.5, 2) if atr > 0 else round(price * 0.01, 2)
    sl_price = round(price - sl_distance, 2)
    target_price = round(price + (sl_distance * 2.0), 2)

    risk_per_unit = sl_distance
    risk_per_lot = round(risk_per_unit * lot_size, 2)

    target_rupee_risk = capital * max_risk_pct
    lots_to_trade = int(target_rupee_risk // risk_per_lot) if risk_per_lot > 0 else 0
    if lots_to_trade < 1:
        lots_to_trade = 1

    total_qty = lots_to_trade * lot_size
    actual_rupee_risk = round(risk_per_unit * total_qty, 2)
    actual_risk_pct = round((actual_rupee_risk / capital) * 100, 2)

    return {
        "Instrument": display_name,
        "Entry Price": price,
        "Stop Loss": sl_price,
        "Target": target_price,
        "Lot Size": lot_size,
        "Lots": lots_to_trade,
        "Total Qty": total_qty,
        "Risk Per Lot": risk_per_lot,
        "Max Rupee Risk": actual_rupee_risk,
        "Risk Pct": actual_risk_pct
    }
