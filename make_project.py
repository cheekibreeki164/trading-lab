import os

files = {
    "engine/market_data.py": '''import yfinance as yf
import pandas as pd
import requests
import io
import datetime

def fetch_google_finance_data(symbol: str) -> pd.DataFrame:
    """Direct Google Finance / NSE history scraper fallback"""
    clean_sym = symbol.replace(".NS", "").replace(".BO", "").upper()
    
    # Try fetching directly from Google Finance CSV endpoints
    urls = [
        f"https://query1.finance.yahoo.com/v7/finance/download/{clean_sym}.NS?period1=0&period2=9999999999&interval=1d&events=history",
        f"https://stooq.com/q/d/l/?s={clean_sym}.in&i=d"
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
    }

    for url in urls:
        try:
            resp = requests.get(url, headers=headers, timeout=5)
            if resp.status_code == 200 and len(resp.text) > 100:
                df = pd.read_csv(io.StringIO(resp.text))
                
                # Normalize column names
                df.columns = [c.capitalize() for c in df.columns]
                
                if 'Date' in df.columns:
                    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
                    df = df.dropna(subset=['Date']).set_index('Date').sort_index()
                
                # Ensure Close column exists and is numeric
                for col in ['Close', 'Open', 'High', 'Low']:
                    if col in df.columns:
                        df[col] = pd.to_numeric(df[col], errors='coerce')
                
                if 'Close' in df.columns and len(df.dropna(subset=['Close'])) >= 5:
                    return df.dropna(subset=['Close'])
        except Exception:
            continue
            
    return None

def search_and_fetch_stock(symbol: str, period: str = "3mo"):
    symbol = symbol.strip().upper()
    if not symbol:
        return None, None
    
    clean_symbol = symbol.replace(".NS", "").replace(".BO", "")
    ticker_ns = f"{clean_symbol}.NS"

    # Strategy 1: yfinance with session impersonation
    try:
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9'
        })
        
        t_obj = yf.Ticker(ticker_ns, session=session)
        df = t_obj.history(period=period, auto_adjust=True)
        if df is not None and not df.empty and 'Close' in df.columns and len(df) >= 5:
            return ticker_ns, df
    except Exception:
        pass

    # Strategy 2: Direct HTTP streaming endpoint fallback
    df_fallback = fetch_google_finance_data(clean_symbol)
    if df_fallback is not None and len(df_fallback) >= 5:
        # Slice last 90 days
        df_sliced = df_fallback.tail(90)
        return ticker_ns, df_sliced

    return ticker_ns, None

def fetch_batch_market_data(tickers: list, period: str = "3mo") -> dict:
    data_dict = {}
    if not tickers:
        return data_dict

    for t in tickers:
        sym, df = search_and_fetch_stock(t, period=period)
        if df is not None and not df.empty:
            data_dict[t] = df

    return data_dict
''',

    "app.py": '''import streamlit as st
import pandas as pd
import datetime
from engine.data_loader import load_stock_universe
from engine.market_data import fetch_batch_market_data, search_and_fetch_stock
from engine.options_engine import generate_option_setup
from components.charts import render_candlestick_chart, render_greeks_decay_chart

st.set_page_config(page_title="Medhansh BSM Trading Lab", layout="wide", page_icon="⚡")

st.sidebar.header("🔍 Search Any Stock (NSE/BSE)")
search_input = st.sidebar.text_input("Enter Stock Symbol (e.g. ZOMATO, TATASTEEL, ITC):", "").strip().upper()

st.sidebar.header("🎯 Option Contract Config")
opt_type_input = st.sidebar.radio("Option Strategy:", ["Call Option (CE)", "Put Option (PE)"])
selected_option_type = "CE" if "Call" in opt_type_input else "PE"

moneyness_input = st.sidebar.radio("Moneyness:", ["ATM (At-The-Money)", "ITM (In-The-Money)", "OTM (Out-Of-The-Money)"])
if "ITM" in moneyness_input:
    strike_type = "ITM"
elif "OTM" in moneyness_input:
    strike_type = "OTM"
else:
    strike_type = "ATM"

dte_input = st.sidebar.slider("Days to Expiry (DTE):", 1, 30, 14)

st.sidebar.header("🛡️ Account Capital & Risk")
capital = st.sidebar.number_input("Capital (₹):", min_value=1000.0, value=50000.0, step=5000.0)
max_risk_pct_input = st.sidebar.slider("Max Account Risk per Trade (%):", 0.5, 5.0, 2.0, 0.5) / 100.0

universe = load_stock_universe()

# Process dynamic custom stock search
custom_ticker = None
custom_df_found = None

if search_input:
    formatted_sym, custom_df_found = search_and_fetch_stock(search_input)
    if custom_df_found is not None:
        custom_ticker = formatted_sym
        if custom_ticker not in universe:
            universe.insert(0, custom_ticker)
        st.sidebar.success(f"Loaded **{custom_ticker}** successfully!")
    else:
        st.sidebar.error(f"Could not fetch data for '{search_input}'. Check ticker symbol.")

now_str = datetime.datetime.now().strftime("%H:%M:%S IST")

st.title("⚡ Medhansh BSM Options & Spot Engine")
st.caption(f"🟢 **PURE BSM MODEL ACTIVE** | Direction: **{selected_option_type}** | Updated: `{now_str}`")

# Un-cached execution when searching to prevent returning stale failed results
def run_pipeline_direct(ticker_list, cap, risk_pct, opt_type, strike_mode, dte_val, custom_sym, custom_df):
    results, chart_dfs = {}, {}
    
    # If custom searched stock is active, attach its df directly
    if custom_sym and custom_df is not None:
        chart_dfs[custom_sym] = custom_df

    batch_dfs = fetch_batch_market_data([t for t in ticker_list if t != custom_sym], period="3mo")
    batch_dfs.update(chart_dfs)

    for ticker, df in batch_dfs.items():
        try:
            if df is None or len(df) < 5:
                continue
            
            spot_price = float(df['Close'].iloc[-1])
            prev_close = float(df['Close'].iloc[-2]) if len(df) > 1 else spot_price
            day_change = round(((spot_price - prev_close) / prev_close) * 100, 2)

            setup = generate_option_setup(
                symbol=ticker,
                spot_price=spot_price,
                capital=cap,
                max_risk_pct=risk_pct,
                df_history=df,
                option_type=opt_type,
                strike_mode=strike_mode,
                days_to_expiry=dte_val
            )

            results[ticker] = {
                "Spot Price": spot_price,
                "1D Change %": day_change,
                "5D Trend Drift %": setup["Drift %"],
                "BSM Quant Score": setup["BSM Score"],
                "Instrument": setup["Instrument"],
                "BSM Premium": setup["BSM Premium"],
                "Delta": setup["BSM Delta"],
                "Gamma": setup["BSM Gamma"],
                "Theta": setup["BSM Theta"],
                "Vega": setup["BSM Vega"],
                "Volatility %": setup["Ann. Volatility"],
                "Lots": setup["Lots"],
                "Total Qty": setup["Total Qty"],
                "Capital Required": setup["Premium Required"],
                "Option SL": setup["Option SL"],
                "Option Target": setup["Option Target"],
                "Max Rupee Risk": setup["Max Rupee Risk"],
                "Setup": setup
            }
            chart_dfs[ticker] = df
        except Exception:
            continue

    return results, chart_dfs

results, chart_dfs = run_pipeline_direct(
    universe, capital, max_risk_pct_input, selected_option_type, strike_type, dte_input, custom_ticker, custom_df_found
)

if results:
    df_all = pd.DataFrame.from_dict(results, orient='index')
    sorted_df = df_all.sort_values(by=['BSM Quant Score', '5D Trend Drift %'], ascending=[False, False if selected_option_type == "CE" else True])

    top_stock = custom_ticker if custom_ticker and custom_ticker in sorted_df.index else sorted_df.index[0]
    top_setup = sorted_df.loc[top_stock]['Setup']

    color = "#00E676" if selected_option_type == "CE" else "#FF5252"

    st.markdown(f"""
    <div style="background-color: #1E222D; padding: 18px; border-radius: 8px; border: 2px solid {color}; margin-bottom: 20px;">
        <h2 style="color: {color}; margin: 0;">🏆 TOP BSM {selected_option_type} OPPORTUNITY: {top_stock} — {top_setup['Instrument']}</h2>
        <p style="font-size: 14px; color: #BBB;">Spot: <b>₹{top_setup['Strike']}</b> | Drift: <b>{top_setup['Drift %']}%</b> | Volatility: <b>{top_setup['Ann. Volatility']}%</b> | Quant Score: <b>{top_setup['BSM Score']}/100</b></p>
        <hr style="border-color: #333;">
        <div style="display: flex; justify-content: space-between; flex-wrap: wrap; gap: 10px; font-size: 15px;">
            <div><b>Theoretical Premium:</b> ₹{top_setup['BSM Premium']}</div>
            <div><b>Stop Loss:</b> <span style="color:#FF5252;">₹{top_setup['Option SL']}</span></div>
            <div><b>Target:</b> <span style="color:#00E676;">₹{top_setup['Option Target']}</span></div>
            <div><b>Sizing:</b> <span style="color:{color}; font-weight:bold;">{top_setup['Lots']} Lot ({top_setup['Total Qty']} Qty)</span></div>
            <div><b>Margin Required:</b> ₹{top_setup['Premium Required']:,}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    tab_equity, tab_options, tab_detail = st.tabs([
        "📈 Equity Spot Rankings", 
        "🎯 Options Engine", 
        "⚡ Contract Deep-Dive"
    ])

    with tab_equity:
        st.subheader(f"📈 Equity Spot Rankings ({selected_option_type} Direction-Aware)")
        st.dataframe(
            sorted_df[['Spot Price', '1D Change %', '5D Trend Drift %', 'Volatility %', 'BSM Quant Score', 'Capital Required', 'Max Rupee Risk']], 
            use_container_width=True
        )

    with tab_options:
        st.subheader(f"🎯 BSM Options Valuation ({selected_option_type})")
        st.dataframe(
            sorted_df[['Instrument', 'Spot Price', 'BSM Premium', 'Delta', 'Gamma', 'Theta', 'Vega', 'Volatility %', 'Lots', 'Total Qty', 'Capital Required', 'Option SL', 'Option Target']], 
            use_container_width=True
        )

    with tab_detail:
        st.subheader("⚡ Contract Deep-Dive & Greeks Visualizer")
        
        default_index = sorted_df.index.tolist().index(top_stock) if top_stock in sorted_df.index else 0
        selected_stock = st.selectbox("Choose Instrument:", sorted_df.index.tolist(), index=default_index)

        if selected_stock:
            info = results[selected_stock]
            setup = info['Setup']
            df_chart = chart_dfs[selected_stock]

            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric("Spot Price", f"₹{info['Spot Price']}", f"{info['1D Change %']}%")
                st.metric("BSM Quant Score", f"{info['BSM Quant Score']} / 100")
            with c2:
                st.write(f"**Contract:** {setup['Instrument']}")
                st.write(f"**BSM Premium:** ₹{setup['BSM Premium']}")
                st.write(f"**Stop Loss:** ₹{setup['Option SL']}")
                st.write(f"**Target:** ₹{setup['Option Target']}")
            with c3:
                st.write(f"**Delta (Δ):** {setup['BSM Delta']}")
                st.write(f"**Gamma (γ):** {setup['BSM Gamma']}")
                st.write(f"**Theta (θ):** ₹{setup['BSM Theta']} / day")
                st.write(f"**Vega (ν):** ₹{setup['BSM Vega']} / % vol")

            st.markdown("---")
            ct1, ct2 = st.tabs(["📉 Price Candlesticks", "⚡ Greeks & Premium Decay"])
            with ct1:
                st.plotly_chart(render_candlestick_chart(df_chart, selected_stock), use_container_width=True)
            with ct2:
                st.plotly_chart(render_greeks_decay_chart(setup['Decay Curve'], selected_stock, setup['Instrument']), use_container_width=True)
else:
    st.error("Market data could not be fetched. Please refresh.")'''
}

for path, content in files.items():
    folder = os.path.dirname(path)
    if folder:
        os.makedirs(folder, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

print("✅ CACHE REMOVED & DIRECT STREAMING ENGINE LOADED!")