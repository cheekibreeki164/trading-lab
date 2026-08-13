import streamlit as st
import pandas as pd
import datetime
from engine.data_loader import load_stock_universe, load_mcx_universe
from engine.market_data import fetch_batch_market_data
from engine.indicators import compute_indicators
from engine.analyzer import extract_latest_condition
from engine.scoring import score_market_condition
from engine.setup_generator import generate_trade_setup
from engine.options_engine import generate_option_setup, analyze_option_trend
from engine.mcx_engine import analyze_mcx_trend, generate_mcx_setup, MCX_NAMES
from components.charts import render_candlestick_chart

st.set_page_config(page_title="Medhansh TradingLab", layout="wide", page_icon="⚡")

market_mode = st.sidebar.selectbox("📈 Asset Class / Mode:", ["NSE Options (CE/PE Buying)", "Equity Spot (Shares)", "MCX Commodities"])

st.sidebar.header("🎯 Trading Strategy Profiles")
trade_style = st.sidebar.radio(
    "Select Horizon:",
    ["⚡ Intraday Breakdown", "📈 Swing Trade Setup", "🏦 Long-Term Breakout"],
    index=0
)

default_period = "1mo" if "Intraday" in trade_style else ("6mo" if "Swing" in trade_style else "2y")
default_risk = 2.0

st.sidebar.header("🛡️ Capital & Risk Management")
capital = st.sidebar.number_input("Total Cash Balance (₹):", min_value=500.0, value=4000.0, step=500.0)
max_risk_pct_input = st.sidebar.slider("Max Balance Risk Per Trade (%):", 0.5, 5.0, default_risk, 0.5) / 100.0

if market_mode == "Equity Spot (Shares)":
    leverage_option = st.sidebar.radio("Leverage Mode:", ["1x (Cash Delivery)", "5x (Intraday MIS Leverage)"], index=1)
    leverage_multiplier = 5.0 if "5x" in leverage_option else 1.0
    buying_power = capital * leverage_multiplier
elif market_mode == "MCX Commodities":
    leverage_multiplier = 1.0
    buying_power = capital
else:
    leverage_multiplier = 1.0
    buying_power = capital
    option_strike_mode = st.sidebar.radio("Option Moneyness:", ["ATM (At-The-Money)", "ITM (In-The-Money)"])
    strike_type = "ITM" if "ITM" in option_strike_mode else "ATM"

max_risk_rupees = capital * max_risk_pct_input

st.sidebar.info(f"💰 **Capital Allocated:** ₹{buying_power:,.2f}")
st.sidebar.warning(f"🛑 **Max Risk Capped At:** ₹{max_risk_rupees:,.2f} ({max_risk_pct_input*100:.1f}%)")

st.sidebar.header("⚙️ Configuration & Filters")
if market_mode == "MCX Commodities":
    universe = load_mcx_universe()
else:
    universe = load_stock_universe()

min_score = st.sidebar.slider("Minimum Score Filter:", 0, 50, 20 if market_mode == "MCX Commodities" else 25)

now_str = datetime.datetime.now().strftime("%H:%M:%S IST")
st.title(f"⚡ Medhansh TradingLab — {market_mode}")
st.caption(f"🟢 **SYSTEM ONLINE** | Last Update: `{now_str}`")

@st.cache_data(ttl=20)
def run_pipeline(ticker_list, capital_input, leverage_input, risk_pct, period_lookback, mode):
    results, chart_dfs = {}, {}
    batch_dfs = fetch_batch_market_data(ticker_list, period=period_lookback)
    
    for ticker, df in batch_dfs.items():
        try:
            df_ind = compute_indicators(df)
            condition = extract_latest_condition(df_ind, ticker)
            scores = score_market_condition(condition, df_ind)
            
            clean_name = MCX_NAMES.get(ticker, ("NIFTY 50" if ticker == "^NSEI" else ("BANK NIFTY" if ticker == "^NSEBANK" else ticker)))

            if mode == "MCX Commodities":
                trend_info = analyze_mcx_trend(
                    condition.get('Price', 0),
                    condition.get('RSI', 50),
                    condition.get('RVOL', 1.0),
                    condition.get('Daily_Change', 0)
                )
                setup = generate_mcx_setup(
                    symbol=ticker,
                    price=condition.get('Price', 0),
                    atr=condition.get('ATR', 0),
                    capital=capital_input,
                    max_risk_pct=risk_pct
                )
            elif mode == "Equity Spot (Shares)":
                trend_info = analyze_option_trend(
                    condition.get('Price', 0), condition.get('RSI', 50), condition.get('RVOL', 1.0), condition.get('Daily_Change', 0)
                )
                setup = generate_trade_setup(
                    condition.get('Price', 0), condition.get('ATR', 0), total_capital=capital_input, leverage=leverage_input, max_risk_pct=risk_pct
                )
            else:
                trend_info = analyze_option_trend(
                    condition.get('Price', 0), condition.get('RSI', 50), condition.get('RVOL', 1.0), condition.get('Daily_Change', 0)
                )
                opt_type = "CE" if condition.get('Daily_Change', 0) >= 0 else "PE"
                setup = generate_option_setup(
                    symbol=ticker, spot_price=condition.get('Price', 0), atr=condition.get('ATR', 0), capital=capital_input, max_risk_pct=risk_pct, option_type=opt_type, strike_mode=strike_type
                )

            results[clean_name] = {
                "RawTicker": ticker,
                "Price": condition.get('Price'),
                "1D Change %": condition.get('Daily_Change', 0),
                "Score": scores['total'],
                "Status": scores['status'],
                "Pattern": scores['pattern'],
                "Preferred_Buy": condition.get('Preferred_Buy', False),
                "RSI": condition.get('RSI'),
                "RVOL": condition.get('RVOL'),
                "ATR": condition.get('ATR'),
                "TrendInfo": trend_info,
                "Setup": setup
            }
            chart_dfs[clean_name] = df_ind
        except Exception:
            continue

    return results, chart_dfs

results, chart_dfs = run_pipeline(universe, capital, leverage_multiplier, max_risk_pct_input, default_period, market_mode)

if results:
    df_all = pd.DataFrame.from_dict(results, orient='index')[['Price', '1D Change %', 'Score', 'Status', 'Pattern', 'Preferred_Buy', 'RSI', 'RVOL']]
    sorted_df = df_all.sort_values(by=['Score', 'RVOL', '1D Change %'], ascending=[False, False, False])
    
    winner_name = sorted_df.index[0]
    winner_setup = results[winner_name]['Setup']

    st.markdown(f"""
    <div style="background-color: #1E222D; padding: 20px; border-radius: 10px; border: 2px solid #00E676; margin-bottom: 20px;">
        <h2 style="color: #00E676; margin: 0;">🎯 TOP RECOMMENDED TRADE: {winner_name}</h2>
        <p style="font-size: 15px; color: #CCCCCC;"><b>Current Price / Spot:</b> {results[winner_name]['Price']} | <b>Signal:</b> {results[winner_name]['TrendInfo']['Signal']}</p>
        <hr style="border-color: #333;">
        <div style="display: flex; justify-content: space-between; flex-wrap: wrap; gap: 10px;">
            <div><b>Target:</b> <span style="color:#00E676;">{winner_setup.get('Target', 'N/A')}</span></div>
            <div><b>Stop Loss:</b> <span style="color:#FF5252;">{winner_setup.get('Stop Loss', winner_setup.get('Option SL', 'N/A'))}</span></div>
            <div><b>Position Size:</b> <span style="color:#00E676;"><b>{winner_setup.get('Lots', winner_setup.get('Shares to Buy', 'N/A'))} Lots / Qty</b></span></div>
            <div><b>Max Risk:</b> ₹{winner_setup.get('Max Rupee Risk', 'N/A')} ({winner_setup.get('Risk Pct', 'N/A')}%)</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.subheader(f"📊 {market_mode} Market Dashboard")
    st.dataframe(sorted_df[sorted_df['Score'] >= min_score], use_container_width=True)

    st.markdown("---")
    
    selected_asset = st.selectbox("Inspect Asset & Technical Chart:", sorted_df.index.tolist(), index=0)
    if selected_asset:
        asset_info, df_asset = results[selected_asset], chart_dfs[selected_asset]
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"### {selected_asset}")
            st.metric("Price", f"{asset_info['Price']}", f"{asset_info['1D Change %']}%")
            st.metric("Algo Score", f"{asset_info['Score']} / 50", delta=asset_info['Status'])
        with col2:
            st.markdown("### Technical Indicators")
            st.write(f"**Signal:** {asset_info['TrendInfo']['Signal']}")
            st.write(f"**Pattern:** {asset_info['Pattern']}")
            st.write(f"**RSI (14):** {asset_info['RSI']}")
            st.write(f"**RVOL:** {asset_info['RVOL']}x")
        with col3:
            st.markdown("### Trade Plan")
            setup = asset_info['Setup']
            for k, v in setup.items():
                st.write(f"**{k}:** {v}")
        st.markdown("---")
        st.plotly_chart(render_candlestick_chart(df_asset, selected_asset), use_container_width=True)
else:
    st.error("Failed to load market data.")