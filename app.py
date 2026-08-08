import streamlit as st
import pandas as pd
from engine.data_loader import load_stock_universe
from engine.market_data import fetch_batch_market_data
from engine.indicators import compute_indicators
from engine.analyzer import extract_latest_condition
from engine.scoring import score_market_condition
from engine.setup_generator import generate_trade_setup
from components.charts import render_candlestick_chart

st.set_page_config(page_title="Medhansh TradingLab", layout="wide", page_icon="👑")
st.title("👑 Medhansh TradingLab — Daily Winner Terminal")

st.sidebar.header("⚙️ Configuration & Filters")
universe = load_stock_universe()
st.sidebar.info(f"Market Universe: **{len(universe)}** Stocks")

min_score = st.sidebar.slider("Minimum TradingLab Score:", 0, 50, 30)
scan_button = st.sidebar.button("⚡ Lock In Today's Scan", type="primary")

@st.cache_data(ttl=43200)
def run_pipeline(ticker_list):
    results, chart_dfs = {}, {}
    batch_dfs = fetch_batch_market_data(ticker_list)
    
    for ticker, df in batch_dfs.items():
        try:
            df_ind = compute_indicators(df)
            condition = extract_latest_condition(df_ind, ticker)
            scores = score_market_condition(condition)
            setup = generate_trade_setup(condition.get('Price', 0), condition.get('ATR', 0))
            
            results[ticker] = {
                "Price": condition.get('Price'),
                "1D Change %": condition.get('Daily_Change', 0),
                "Score": scores['total'],
                "Status": scores['status'],
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

if scan_button or 'results' not in st.session_state:
    with st.spinner("Locking in daily market data to determine today's #1 winner..."):
        st.session_state.results, st.session_state.chart_dfs = run_pipeline(universe)

results, chart_dfs = st.session_state.results, st.session_state.chart_dfs

if results:
    df_all = pd.DataFrame.from_dict(results, orient='index')[['Price', '1D Change %', 'Score', 'Status', 'Preferred_Buy', 'RSI', 'RVOL', 'ATR']]
    
    sorted_df = df_all.sort_values(by=['Score', 'RVOL', '1D Change %'], ascending=[False, False, False])
    
    winner_ticker = sorted_df.index[0]
    winner_info = sorted_df.iloc[0]
    winner_setup = results[winner_ticker]['Setup']

    # BANNER: TOP WINNER OF THE DAY
    st.markdown(f"""
    <div style="background-color: #1E222D; padding: 20px; border-radius: 10px; border: 2px solid #00E676; margin-bottom: 20px;">
        <h2 style="color: #00E676; margin: 0;">🏆 OFFICIAL WINNER OF THE DAY: {winner_ticker}</h2>
        <p style="font-size: 16px; color: #CCCCCC;">Highest conviction stock selected based on maximum TradingLab Score, volume surge, and trend momentum.</p>
        <hr style="border-color: #333;">
        <div style="display: flex; justify-content: space-between; flex-wrap: wrap;">
            <div><b>Current Price:</b> ₹{winner_info['Price']} ({winner_info['1D Change %']}%)</div>
            <div><b>TradingLab Score:</b> {winner_info['Score']}/50</div>
            <div><b>RVOL:</b> {winner_info['RVOL']}x</div>
            <div><b>Target:</b> ₹{winner_setup['Target']}</div>
            <div><b>Stop Loss:</b> ₹{winner_setup['Stop Loss']}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["🔥 Top Buy Picks", "📊 Full Market Screener"])
    
    with tab1:
        st.subheader("🔥 High-Conviction Candidates")
        buy_picks = sorted_df[(sorted_df['Preferred_Buy'] == True) | (sorted_df['Score'] >= 40)]
        if not buy_picks.empty:
            st.dataframe(buy_picks[['Price', '1D Change %', 'Score', 'Status', 'RSI', 'RVOL', 'ATR']], use_container_width=True)
        else:
            st.info("No other stocks meet 100% of the strict breakout filters today.")

    with tab2:
        st.subheader("📊 All Stock Screener")
        st.dataframe(sorted_df[sorted_df['Score'] >= min_score][['Price', '1D Change %', 'Score', 'Status', 'RSI', 'RVOL', 'ATR']], use_container_width=True)

    st.markdown("---")
    
    all_available = sorted_df.index.tolist()
    selected_stock = st.selectbox("Inspect Chart & Plan for Any Stock:", all_available, index=0)
    if selected_stock:
        stock_info, df_stock = results[selected_stock], chart_dfs[selected_stock]
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"### {selected_stock}")
            st.metric("Price", f"₹{stock_info['Price']}", f"{stock_info['1D Change %']}%")
            st.metric("Score", f"{stock_info['Score']} / 50", delta=stock_info['Status'])
        with col2:
            st.markdown("### Metrics")
            st.write(f"**RSI (14):** {stock_info['RSI']}")
            st.write(f"**RVOL:** {stock_info['RVOL']}x")
            st.write(f"**ATR:** ₹{stock_info['ATR']}")
        with col3:
            st.markdown("### Plan")
            setup = stock_info['Setup']
            st.write(f"**Entry:** ₹{setup['Entry']}")
            st.write(f"**Stop Loss:** ₹{setup['Stop Loss']}")
            st.write(f"**Target:** ₹{setup['Target']}")
        st.markdown("---")
        st.plotly_chart(render_candlestick_chart(df_stock, selected_stock), use_container_width=True)