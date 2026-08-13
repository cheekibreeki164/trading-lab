def load_stock_universe():
    # Includes major indices (^NSEI for NIFTY 50, ^NSEBANK for BANK NIFTY) + liquid FnO stock universe
    return [
        "^NSEI",         # NIFTY 50 Index
        "^NSEBANK",      # BANK NIFTY Index
        "RELIANCE.NS",
        "TCS.NS",
        "HDFCBANK.NS",
        "ICICIBANK.NS",
        "SBIN.NS",
        "BHARTIARTL.NS",
        "TATAMOTORS.NS",
        "INFY.NS",
        "HAL.NS",
        "TATAINVEST.NS",
        "AXISBANK.NS",
        "LT.NS",
        "MARUTI.NS"
    ]