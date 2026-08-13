def load_stock_universe():
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

def load_mcx_universe():
    return [
        "GC=F",   # Gold (MCX Benchmark)
        "SI=F",   # Silver (MCX Benchmark)
        "CL=F",   # Crude Oil (MCX Benchmark)
        "NG=F",   # Natural Gas (MCX Benchmark)
        "HG=F"    # Copper (MCX Benchmark)
    ]
