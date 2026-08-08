import streamlit as st
import pandas as pd
import datetime
from streamlit_autorefresh import st_autorefresh
from engine.data_loader import load_stock_universe
from engine.market_data import fetch_batch_market_data
from engine.indicators import compute_indicators
from engine.analyzer import extract_latest_condition
from engine.scoring import score_market_condition
from engine.setup_generator import generate_daytrade_setup
from components.charts import render_candlestick_chart

st.set_page_config(page_title="Medhansh TradingLab — Realtime Terminal", layout="wide", page_icon="⚡")

# Sidebar - Live Settings
st.sidebar.header("⏱️ Real-Time Stream Control")
refresh_interval = st.sidebar.slider("Auto-Refresh Interval (Seconds):", min_value=5, max_value=60, value=10, step=5)

# Trigger auto-refresh loop
count = st_autorefresh(interval=refresh_interval * 1000, key="realtime_ticker")

st.sidebar.header("🛡️ Capital & Risk Management")
capital = st.sidebar.number_input("Total Cash Balance (₹):", min_value=500.0, value=4000.0, step=500.0)
max_risk_pct_input = st.sidebar.slider("Max Balance Risk Per Trade (%):", 1.0, 5.0, 2.0, 0.5) / 100.0

leverage_option = st.sidebar.radio("Leverage Mode:", ["1x (Cash)", "5x (Intraday MIS Leverage)"], index=1)
leverage_multiplier = 5.0 if "5x" in leverage_option else 1.0

buying_power = capital * leverage_multiplier
max_risk_rupees = capital * max_risk_pct_input

st.sidebar.info(f"💰 **Purchasing Power ({leverage_option}):** ₹{buying_power:,.2f}")
st.sidebar.warning(f"🛑 **Max Account Loss Capped At:** ₹{max_risk_rupees:,.2f} ({max_risk_pct_input*100:.1f}%)")

st.sidebar.header("⚙️ Configuration & Filters")
universe = load_stock_universe()
min_score = st.sidebar.slider("Minimum Score:", 0, 50, 30)

# Streamlit App Header
now_str = datetime.datetime.now().strftime("%H:%M:%S IST")
st.title("⚡ Medhansh TradingLab — Live Algo Terminal")
st.caption(f"🟢 **LIVE MARKET TICKING** | Last Algo Update: `{now_str}` | Cycle Refresh Count: `{count}`")

@st.cache_data(ttl=5)
def run_realtime_pipeline(ticker_list, capital_input, leverage_input, risk_pct):
    results, chart_dfs = {}, {}
    batch_dfs = fetch_batch_market_data(ticker_list)
    
    for ticker, df in batch_dfs.items():
        try:
            df_ind = compute_indicators(df)
            condition = extract_latest_condition(df_ind, ticker)
            scores = score_market_condition(condition, df_ind)
            setup = generate_daytrade_setup(
                condition.get('Price', 0), 
                condition.get('ATR', 0), 
                total_capital=capital_input, 
                leverage=leverage_input,
                max_risk_pct=risk_pct
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

# Execute pipeline
results, chart_dfs = run_realtime_pipeline(universe, capital, leverage_multiplier, max_risk_pct_input)

if results:
    df_all = pd.DataFrame.from_dict(results, orient='index')[['Price', '1D Change %', 'Score', 'Status', 'Pattern', 'Preferred_Buy', 'RSI', 'RVOL', 'ATR']]
    sorted_df = df_all.sort_values(by=['Score', 'RVOL', '1D Change %'], ascending=[False, False, False])
    
    winner_ticker = sorted_df.index[0]
    winner_info = sorted_df.iloc[0]
    winner_setup = results[winner_ticker]['Setup']

    st.markdown(f"""
    <div style="background-color: #1E222D; padding: 20px; border-radius: 10px; border: 2px solid #00E676; margin-bottom: 20px;">
        <h2 style="color: #00E676; margin: 0;">🏆 #1 INTRADAY ALGO WINNER: {winner_ticker} ({winner_setup['Leverage']} Mode)</h2>
        <p style="font-size: 15px; color: #CCCCCC;"><b>Pattern Detected:</b> {winner_info['Pattern']} | <b>Score:</b> {winner_info['Score']}/50</p>
        <hr style="border-color: #333;">
        <div style="display: flex; justify-content: space-between; flex-wrap: wrap; gap: 10px;">
            <div><b>Live Entry Price:</b> ₹{winner_setup['Entry']}</div>
            <div><b>Dynamic Stop Loss ({winner_setup['SL_Pct']}%):</b> <span style="color:#FF5252;">₹{winner_setup['Stop Loss']}</span></div>
            <div><b>Target (2:1 Ratio):</b> <span style="color:#00E676;">₹{winner_setup['Target']}</span></div>
            <div><b>Leveraged Shares:</b> {winner_setup['Shares to Buy']}</div>
            <div><b>Margin Used:</b> ₹{winner_setup['Margin Required']:,}</div>
            <div><b>Max Loss Cap:</b> ₹{winner_setup['Max Rupee Risk']}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["🔥 Top Real-Time Picks", "📊 Live Algo Screener"])
    
    with tab1:
        st.subheader("🔥 High-Conviction Breakout Candidates")
        buy_picks = sorted_df[(sorted_df['Preferred_Buy'] == True) | (sorted_df['Score'] >= 40)]
        if not buy_picks.empty:
            st.dataframe(buy_picks[['Price', '1D Change %', 'Score', 'Status', 'Pattern', 'RSI', 'RVOL']], use_container_width=True)
        else:
            st.info("No stocks currently meet 100% of high-conviction breakout filters.")

    with tab2:
        st.subheader("📊 Live Stock Screener")
        st.dataframe(sorted_df[sorted_df['Score'] >= min_score][['Price', '1D Change %', 'Score', 'Status', 'Pattern', 'RSI', 'RVOL']], use_container_width=True)

    st.markdown("---")
    
    all_available = sorted_df.index.tolist()
    selected_stock = st.selectbox("Inspect Real-Time Execution & Chart:", all_available, index=0)
    if selected_stock:
        stock_info, df_stock = results[selected_stock], chart_dfs[selected_stock]
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"### {selected_stock}")
            st.metric("Live Price", f"₹{stock_info['Price']}", f"{stock_info['1D Change %']}%")
            st.metric("Algo Score", f"{stock_info['Score']} / 50", delta=stock_info['Status'])
        with col2:
            st.markdown("### Metrics & Pattern")
            st.write(f"**Pattern:** {stock_info['Pattern']}")
            st.write(f"**RSI (14):** {stock_info['RSI']}")
            st.write(f"**RVOL:** {stock_info['RVOL']}x")
        with col3:
            st.markdown(f"### Trade Plan ({leverage_multiplier}x Leverage)")
            setup = stock_info['Setup']
            st.write(f"**Entry:** ₹{setup['Entry']}")
            st.write(f"**Stop Loss:** ₹{setup['Stop Loss']} ({setup['SL_Pct']}% Drop)")
            st.write(f"**Target:** ₹{setup['Target']}")
            st.write(f"**Leveraged Shares:** {setup['Shares to Buy']}")
            st.write(f"**Margin Used:** ₹{setup['Margin Required']:,}")
            st.write(f"**Max Loss Capped At:** ₹{setup['Max Rupee Risk']}")
        st.markdown("---")
        st.plotly_chart(render_candlestick_chart(df_stock, selected_stock), use_container_width=True)