import streamlit as st
import pandas as pd
import datetime
from engine.data_loader import load_stock_universe
from engine.market_data import fetch_batch_market_data
from engine.options_engine import generate_option_setup
from components.charts import render_candlestick_chart, render_greeks_decay_chart

st.set_page_config(page_title="Medhansh BSM Options Lab", layout="wide", page_icon="⚡")

st.sidebar.header("🎯 BSM Options Parameters")
opt_type_input = st.sidebar.radio("Option Type Preference:", ["Call Option (CE)", "Put Option (PE)"])
selected_option_type = "CE" if "Call" in opt_type_input else "PE"

moneyness_input = st.sidebar.radio("Option Moneyness:", ["ATM (At-The-Money)", "ITM (In-The-Money)", "OTM (Out-Of-The-Money)"])
if "ITM" in moneyness_input:
    strike_type = "ITM"
elif "OTM" in moneyness_input:
    strike_type = "OTM"
else:
    strike_type = "ATM"

dte_input = st.sidebar.slider("Days to Expiry (DTE):", 1, 30, 14)

st.sidebar.header("🛡️ Capital & Risk Settings")
capital = st.sidebar.number_input("Total Trading Capital (₹):", min_value=500.0, value=50000.0, step=1000.0)
max_risk_pct_input = st.sidebar.slider("Max Capital Risk Per Trade (%):", 0.5, 5.0, 2.0, 0.5) / 100.0

universe = load_stock_universe()
now_str = datetime.datetime.now().strftime("%H:%M:%S IST")

st.title("⚡ Medhansh BSM Pricing & Options Engine")
st.caption(f"🟢 **PURE BLACK-SCHOLES-MERTON (BSM) QUANT MODEL ACTIVE** | Last Update: `{now_str}`")

@st.cache_data(ttl=30)
def run_bsm_pipeline(ticker_list, cap, risk_pct, opt_type, strike_mode, dte_val):
    results, chart_dfs = {}, {}
    batch_dfs = fetch_batch_market_data(ticker_list, period="3mo")

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
                "BSM Score": setup["BSM Score"],
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

results, chart_dfs = run_bsm_pipeline(
    universe, capital, max_risk_pct_input, selected_option_type, strike_type, dte_input
)

if results:
    df_all = pd.DataFrame.from_dict(results, orient='index')
    sorted_df = df_all.sort_values(by=['BSM Score', 'Volatility %'], ascending=[False, False])

    winner_ticker = sorted_df.index[0]
    winner_setup = sorted_df.iloc[0]['Setup']

    st.markdown(f"""
    <div style="background-color: #1E222D; padding: 20px; border-radius: 10px; border: 2px solid #00E676; margin-bottom: 20px;">
        <h2 style="color: #00E676; margin: 0;">🏆 TOP QUANT PICK (BSM): {winner_ticker} — {winner_setup['Instrument']}</h2>
        <p style="font-size: 15px; color: #CCCCCC;"><b>Spot Price:</b> ₹{winner_setup['Strike']} | <b>Ann. Volatility:</b> {winner_setup['Ann. Volatility']}% | <b>Delta:</b> {winner_setup['BSM Delta']} | <b>BSM Score:</b> {winner_setup['BSM Score']}/100</p>
        <hr style="border-color: #333;">
        <div style="display: flex; justify-content: space-between; flex-wrap: wrap; gap: 10px;">
            <div><b>Theoretical BSM Premium:</b> ₹{winner_setup['BSM Premium']}</div>
            <div><b>Option SL:</b> <span style="color:#FF5252;">₹{winner_setup['Option SL']}</span></div>
            <div><b>Option Target:</b> <span style="color:#00E676;">₹{winner_setup['Option Target']}</span></div>
            <div><b>Position Size:</b> <span style="color:#00E676; font-size:18px;"><b>{winner_setup['Lots']} Lot ({winner_setup['Total Qty']} Contracts)</b></span></div>
            <div><b>Capital Required:</b> ₹{winner_setup['Premium Required']:,}</div>
            <div><b>Max Risk:</b> ₹{winner_setup['Max Rupee Risk']}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    tab_equity, tab_options, tab_detail = st.tabs([
        "📈 Equity Spot Ranking", 
        "🎯 BSM Options Engine", 
        "⚡ Contract Deep-Dive & Greeks"
    ])

    with tab_equity:
        st.subheader("📈 Equity Spot Rankings (Driven by BSM Volatility & Dynamic Metrics)")
        st.dataframe(
            sorted_df[['Spot Price', '1D Change %', 'Volatility %', 'BSM Score', 'Capital Required', 'Max Rupee Risk']], 
            use_container_width=True
        )

    with tab_options:
        st.subheader("🎯 BSM Options Chain & Premium Valuation Engine")
        st.dataframe(
            sorted_df[['Instrument', 'Spot Price', 'BSM Premium', 'Delta', 'Gamma', 'Theta', 'Vega', 'Volatility %', 'Lots', 'Total Qty', 'Capital Required', 'Option SL', 'Option Target']], 
            use_container_width=True
        )

    with tab_detail:
        st.subheader("⚡ Individual Contract Deep-Dive & Visual Greeks Simulator")
        selected_stock = st.selectbox("Select Instrument to Inspect:", sorted_df.index.tolist(), index=0)

        if selected_stock:
            stock_info = results[selected_stock]
            setup = stock_info['Setup']
            df_stock = chart_dfs[selected_stock]

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Spot Price", f"₹{stock_info['Spot Price']}", f"{stock_info['1D Change %']}%")
                st.metric("BSM Quant Score", f"{stock_info['BSM Score']} / 100")
            with col2:
                st.write(f"**Contract:** {setup['Instrument']}")
                st.write(f"**BSM Premium:** ₹{setup['BSM Premium']}")
                st.write(f"**Option SL:** ₹{setup['Option SL']}")
                st.write(f"**Option Target:** ₹{setup['Option Target']}")
            with col3:
                st.write(f"**Delta (Δ):** {setup['BSM Delta']}")
                st.write(f"**Gamma (γ):** {setup['BSM Gamma']}")
                st.write(f"**Theta (θ):** ₹{setup['BSM Theta']} / day")
                st.write(f"**Vega (ν):** ₹{setup['BSM Vega']} / % vol")

            st.markdown("---")
            chart_tab1, chart_tab2 = st.tabs(["📉 Price Candlestick", "⚡ Greeks Decay Profile"])
            with chart_tab1:
                st.plotly_chart(render_candlestick_chart(df_stock, selected_stock), use_container_width=True)
            with chart_tab2:
                st.plotly_chart(render_greeks_decay_chart(setup['Decay Curve'], selected_stock, setup['Instrument']), use_container_width=True)
else:
    st.error("Failed to load market data. Please refresh.")