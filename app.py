import streamlit as st
import pandas as pd
import datetime
from engine.data_loader import load_stock_universe
from engine.market_data import fetch_batch_market_data
from engine.options_engine import generate_option_setup
from components.charts import render_candlestick_chart, render_greeks_decay_chart

st.set_page_config(page_title="Medhansh BSM Trading Lab", layout="wide", page_icon="⚡")

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
now_str = datetime.datetime.now().strftime("%H:%M:%S IST")

st.title("⚡ Medhansh BSM Options & Spot Engine")
st.caption(f"🟢 **PURE BSM MODEL ACTIVE** | Direction: **{selected_option_type}** | Updated: `{now_str}`")

@st.cache_data(ttl=30)
def run_pipeline(ticker_list, cap, risk_pct, opt_type, strike_mode, dte_val):
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

results, chart_dfs = run_pipeline(
    universe, capital, max_risk_pct_input, selected_option_type, strike_type, dte_input
)

if results:
    df_all = pd.DataFrame.from_dict(results, orient='index')
    sorted_df = df_all.sort_values(by=['BSM Quant Score', '5D Trend Drift %'], ascending=[False, False if selected_option_type == "CE" else True])

    top_stock = sorted_df.index[0]
    top_setup = sorted_df.iloc[0]['Setup']

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
        selected_stock = st.selectbox("Choose Instrument:", sorted_df.index.tolist(), index=0)

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
    st.error("Market data could not be fetched. Please refresh.")