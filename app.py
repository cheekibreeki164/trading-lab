import streamlit as st
import pandas as pd
import datetime
from engine.data_loader import load_stock_universe
from engine.market_data import fetch_batch_market_data
from engine.indicators import compute_indicators
from engine.analyzer import extract_latest_condition
from engine.scoring import score_market_condition
from engine.setup_generator import generate_trade_setup
from engine.options_engine import generate_option_setup
from components.charts import render_candlestick_chart, render_greeks_decay_chart

st.set_page_config(page_title="Medhansh TradingLab", layout="wide", page_icon="⚡")

market_mode = st.sidebar.selectbox("📈 Asset Class / Mode:", ["Equity Spot (Shares)", "NSE Options Engine (BSM)"])

st.sidebar.header("🎯 Trading Strategy Profiles")
trade_style = st.sidebar.radio(
    "Select Horizon:",
    ["⚡ Intraday Breakdown", "📈 Swing Trade Setup", "🏦 Long-Term Breakout"],
    index=0
)

if "Intraday" in trade_style:
    default_period = "1mo"
    default_risk = 2.0
    default_lev = "5x (Intraday MIS Leverage)"
elif "Swing" in trade_style:
    default_period = "6mo"
    default_risk = 2.0
    default_lev = "1x (Cash Delivery)"
else:
    default_period = "2y"
    default_risk = 3.0
    default_lev = "1x (Cash Delivery)"

st.sidebar.header("🛡️ Capital & Risk Management")
capital = st.sidebar.number_input("Total Cash Balance (₹):", min_value=500.0, value=4000.0, step=500.0)
max_risk_pct_input = st.sidebar.slider("Max Balance Risk Per Trade (%):", 0.5, 5.0, default_risk, 0.5) / 100.0

if market_mode == "Equity Spot (Shares)":
    leverage_option = st.sidebar.radio("Leverage Mode:", ["1x (Cash Delivery)", "5x (Intraday MIS Leverage)"], index=1 if "5x" in default_lev else 0)
    leverage_multiplier = 5.0 if "5x" in leverage_option else 1.0
    buying_power = capital * leverage_multiplier
    selected_option_type = "CE"
    strike_type = "ATM"
    dte_input = 14
else:
    leverage_multiplier = 1.0
    buying_power = capital
    st.sidebar.header("📊 Options Strategy Specs")
    opt_selection_mode = st.sidebar.radio("Contract Selection Mode:", ["Auto-Select (Trend Based)", "Call Option (CE)", "Put Option (PE)"])
    option_strike_mode = st.sidebar.radio("Option Moneyness:", ["ATM (At-The-Money)", "ITM (In-The-Money)", "OTM (Out-Of-The-Money)"])
    
    if "ITM" in option_strike_mode:
        strike_type = "ITM"
    elif "OTM" in option_strike_mode:
        strike_type = "OTM"
    else:
        strike_type = "ATM"
        
    dte_input = st.sidebar.slider("Days to Expiry (DTE):", 1, 30, 14)
    selected_option_type = opt_selection_mode

max_risk_rupees = capital * max_risk_pct_input

st.sidebar.info(f"💰 **Buying / Capital Allocated:** ₹{buying_power:,.2f}")
st.sidebar.warning(f"🛑 **Max Rupee Loss Capped At:** ₹{max_risk_rupees:,.2f} ({max_risk_pct_input*100:.1f}%)")

st.sidebar.header("⚙️ Configuration & Filters")
universe = load_stock_universe()
min_score = st.sidebar.slider("Minimum Score Filter:", 0, 50, 30)

now_str = datetime.datetime.now().strftime("%H:%M:%S IST")
st.title(f"⚡ Medhansh TradingLab — {market_mode}")
st.caption(f"🟢 **BSM OPTIONS ENGINE + GREEKS VISUALIZER ACTIVE** | Last Update: `{now_str}`")

@st.cache_data(ttl=20)
def run_pipeline(ticker_list, capital_input, leverage_input, risk_pct, period_lookback, mode, opt_mode, strike_mode_val, dte_val):
    results, chart_dfs = {}, {}
    batch_dfs = fetch_batch_market_data(ticker_list, period=period_lookback)
    
    for ticker, df in batch_dfs.items():
        try:
            df_ind = compute_indicators(df)
            condition = extract_latest_condition(df_ind, ticker)
            scores = score_market_condition(condition, df_ind)
            
            if mode == "Equity Spot (Shares)":
                setup = generate_trade_setup(
                    condition.get('Price', 0), 
                    condition.get('ATR', 0), 
                    total_capital=capital_input, 
                    leverage=leverage_input,
                    max_risk_pct=risk_pct
                )
            else:
                if "Call" in opt_mode:
                    opt_type = "CE"
                elif "Put" in opt_mode:
                    opt_type = "PE"
                else:
                    opt_type = "CE" if condition.get('Daily_Change', 0) >= 0 else "PE"
                    
                setup = generate_option_setup(
                    symbol=ticker,
                    spot_price=condition.get('Price', 0),
                    atr=condition.get('ATR', 0),
                    capital=capital_input,
                    max_risk_pct=risk_pct,
                    df_history=df_ind,
                    option_type=opt_type,
                    strike_mode=strike_mode_val,
                    days_to_expiry=dte_val
                )
            
            results[ticker] = {
                "Price": condition.get('Price'),
                "1D Change %": condition.get('Daily_Change', 0),
                "Score": scores['total'],
                "Status": scores['status'],
                "Pattern": scores['pattern'],
                "Preferred_Buy": condition.get('Preferred_Buy', False),
                "RSI": condition.get('RSI'),
                "RVOL": condition.get('RVOL'),
                "ATR": condition.get('ATR'),
                "Setup": setup,
                "Breakdown": scores['breakdown']
            }
            chart_dfs[ticker] = df_ind
        except Exception:
            continue

    return results, chart_dfs

results, chart_dfs = run_pipeline(
    universe, capital, leverage_multiplier, max_risk_pct_input, default_period, market_mode, selected_option_type, strike_type, dte_input
)

if results:
    df_all = pd.DataFrame.from_dict(results, orient='index')[['Price', '1D Change %', 'Score', 'Status', 'Pattern', 'Preferred_Buy', 'RSI', 'RVOL', 'ATR']]
    sorted_df = df_all.sort_values(by=['Score', 'RVOL', '1D Change %'], ascending=[False, False, False])
    
    winner_ticker = sorted_df.index[0]
    winner_info = sorted_df.iloc[0]
    winner_setup = results[winner_ticker]['Setup']

    if market_mode == "Equity Spot (Shares)":
        st.markdown(f"""
        <div style="background-color: #1E222D; padding: 20px; border-radius: 10px; border: 2px solid #00E676; margin-bottom: 20px;">
            <h2 style="color: #00E676; margin: 0;">🏆 TOP SPOT PICK: {winner_ticker} ({winner_setup['Leverage']} Mode)</h2>
            <p style="font-size: 15px; color: #CCCCCC;"><b>Pattern:</b> {winner_info['Pattern']} | <b>Score:</b> {winner_info['Score']}/50</p>
            <hr style="border-color: #333;">
            <div style="display: flex; justify-content: space-between; flex-wrap: wrap; gap: 10px;">
                <div><b>Entry Price:</b> ₹{winner_setup['Entry']}</div>
                <div><b>Stop Loss ({winner_setup['SL_Pct']}% Drop):</b> <span style="color:#FF5252;">₹{winner_setup['Stop Loss']}</span></div>
                <div><b>Target Price:</b> <span style="color:#00E676;">₹{winner_setup['Target']}</span></div>
                <div><b>Shares to Buy:</b> <span style="color:#00E676; font-size:18px;"><b>{winner_setup['Shares to Buy']} Shares</b></span></div>
                <div><b>Margin Required:</b> ₹{winner_setup['Margin Required']:,}</div>
                <div><b>Max Loss Risk:</b> ₹{winner_setup['Max Rupee Risk']}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style="background-color: #1E222D; padding: 20px; border-radius: 10px; border: 2px solid #00E676; margin-bottom: 20px;">
            <h2 style="color: #00E676; margin: 0;">🎯 BSM OPTION PICK: {winner_ticker} {winner_setup['Instrument']}</h2>
            <p style="font-size: 15px; color: #CCCCCC;"><b>Spot Price:</b> ₹{winner_info['Price']} | <b>Vol:</b> {winner_setup['Ann. Volatility']}% | <b>Delta:</b> {winner_setup['BSM Delta']} | <b>Gamma:</b> {winner_setup['BSM Gamma']} | <b>Theta:</b> ₹{winner_setup['BSM Theta']}/day | <b>Vega:</b> ₹{winner_setup['BSM Vega']}</p>
            <hr style="border-color: #333;">
            <div style="display: flex; justify-content: space-between; flex-wrap: wrap; gap: 10px;">
                <div><b>BSM Option Premium:</b> ₹{winner_setup['BSM Premium']}</div>
                <div><b>Premium Stop Loss:</b> <span style="color:#FF5252;">₹{winner_setup['Option SL']}</span></div>
                <div><b>Premium Target:</b> <span style="color:#00E676;">₹{winner_setup['Option Target']}</span></div>
                <div><b>Lots to Buy:</b> <span style="color:#00E676; font-size:18px;"><b>{winner_setup['Lots']} Lot ({winner_setup['Total Qty']} Qty)</b></span></div>
                <div><b>Capital Allocated:</b> ₹{winner_setup['Premium Required']:,}</div>
                <div><b>Max Rupee Risk:</b> ₹{winner_setup['Max Rupee Risk']} ({winner_setup['Risk Pct']}%)</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["🔥 Preferred Breakout Picks", "📊 Full Universe Screener"])
    
    with tab1:
        st.subheader("🔥 High-Conviction Setups")
        buy_picks = sorted_df[(sorted_df['Preferred_Buy'] == True) | (sorted_df['Score'] >= 40)]
        if not buy_picks.empty:
            st.dataframe(buy_picks[['Price', '1D Change %', 'Score', 'Status', 'Pattern', 'RSI', 'RVOL']], use_container_width=True)
        else:
            st.info("No stocks currently meet strict breakout criteria.")

    with tab2:
        st.subheader("📊 Stock Universe Screener")
        st.dataframe(sorted_df[sorted_df['Score'] >= min_score][['Price', '1D Change %', 'Score', 'Status', 'Pattern', 'RSI', 'RVOL']], use_container_width=True)

    st.markdown("---")
    
    all_available = sorted_df.index.tolist()
    selected_stock = st.selectbox("Inspect Setup & Technical Chart for Any Stock:", all_available, index=0)
    if selected_stock:
        stock_info, df_stock = results[selected_stock], chart_dfs[selected_stock]
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"### {selected_stock}")
            st.metric("Spot Price", f"₹{stock_info['Price']}", f"{stock_info['1D Change %']}%")
            st.metric("Algo Score", f"{stock_info['Score']} / 50", delta=stock_info['Status'])
        with col2:
            st.markdown("### Technical Indicators")
            st.write(f"**Pattern:** {stock_info['Pattern']}")
            st.write(f"**RSI (14):** {stock_info['RSI']}")
            st.write(f"**RVOL:** {stock_info['RVOL']}x")
            st.write(f"**14-Day ATR:** ₹{stock_info['ATR']}")
        with col3:
            st.markdown(f"### {'BSM Option Model Output' if market_mode != 'Equity Spot (Shares)' else 'Equity Spot Plan'}")
            setup = stock_info['Setup']
            if market_mode == "Equity Spot (Shares)":
                st.write(f"**Entry:** ₹{setup['Entry']}")
                st.write(f"**Stop Loss:** ₹{setup['Stop Loss']} (-{setup['SL_Pct']}%)")
                st.write(f"**Target:** ₹{setup['Target']}")
                st.write(f"**Position:** {setup['Shares to Buy']} Shares")
                st.write(f"**Capital Needed:** ₹{setup['Margin Required']:,}")
            else:
                st.write(f"**Contract:** {setup['Instrument']}")
                st.write(f"**BSM Est. Premium:** ₹{setup['BSM Premium']}")
                st.write(f"**Delta:** {setup['BSM Delta']}")
                st.write(f"**Gamma:** {setup['BSM Gamma']}")
                st.write(f"**Theta:** ₹{setup['BSM Theta']} / day")
                st.write(f"**Vega:** ₹{setup['BSM Vega']} per 1% vol")
                st.write(f"**Ann. Volatility:** {setup['Ann. Volatility']}%")
                st.write(f"**Option SL:** ₹{setup['Option SL']}")
                st.write(f"**Option Target:** ₹{setup['Option Target']}")
                st.write(f"**Position:** {setup['Lots']} Lot ({setup['Total Qty']} Contracts)")
                st.write(f"**Capital Needed:** ₹{setup['Premium Required']:,}")
                st.write(f"**Max Rupee Risk:** ₹{setup['Max Rupee Risk']}")
        
        st.markdown("---")
        
        if market_mode != "Equity Spot (Shares)":
            chart_tab1, chart_tab2 = st.tabs(["📉 Price Candlestick Chart", "⚡ Interactive Greeks Decay Simulator"])
            with chart_tab1:
                st.plotly_chart(render_candlestick_chart(df_stock, selected_stock), use_container_width=True)
            with chart_tab2:
                st.subheader(f"⚡ Black-Scholes Greeks Decay Profile: {selected_stock} {setup['Instrument']}")
                st.caption("Visualizing theoretical option price decay, Delta sensitivity, and non-linear Theta loss as Expiry approaches (30 DTE → 1 DTE).")
                st.plotly_chart(render_greeks_decay_chart(setup['Decay Curve'], selected_stock, setup['Instrument']), use_container_width=True)
        else:
            st.plotly_chart(render_candlestick_chart(df_stock, selected_stock), use_container_width=True)
else:
    st.error("Failed to load market data. Please refresh or check connection.")