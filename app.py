import streamlit as st
import pandas as pd
from engine.data_loader import load_stock_universe
from engine.market_data import fetch_batch_market_data
from engine.indicators import compute_indicators
from engine.analyzer import extract_latest_condition
from engine.scoring import score_market_condition
from engine.setup_generator import generate_trade_setup
from components.charts import render_candlestick_chart

st.set_page_config(page_title="Medhansh TradingLab", layout="wide", page_icon="🚀")
st.title("🚀 Medhansh TradingLab — Indian Market Terminal")

st.sidebar.header("⚙️ Configuration & Filters")
universe = load_stock_universe()
st.sidebar.info(f"Market Universe: **{len(universe)}** Stocks")

min_score = st.sidebar.slider("Minimum TradingLab Score:", 0, 50, 30)
scan_button = st.sidebar.button("⚡ Run Full Market Scan", type="primary")

@st.cache_data(ttl=600)
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
    with st.spinner("Analyzing top Indian stocks for high-conviction buy setups..."):
        st.session_state.results, st.session_state.chart_dfs = run_pipeline(universe)

results, chart_dfs = st.session_state.results, st.session_state.chart_dfs

if results:
    df_all = pd.DataFrame.from_dict(results, orient='index')[['Price', 'Score', 'Status', 'Preferred_Buy', 'RSI', 'RVOL', 'ATR']].sort_values(by="Score", ascending=False)
    
    # Navigation Tabs
    tab1, tab2 = st.tabs(["🔥 Preferred Stocks to Buy", "📊 Full Market Screener"])
    
    with tab1:
        st.subheader("🔥 Top High-Conviction Buy Candidates")
        st.write("These stocks meet **all strict quantitative buy criteria**: Bullish Trend (Price > SMA20 > SMA50), MACD Crossover, Hot RSI Momentum (55-72), and Volume Surge (RVOL >= 1.3x).")
        
        buy_picks = df_all[(df_all['Preferred_Buy'] == True) | (df_all['Score'] >= 40)]
        
        if not buy_picks.empty:
            st.dataframe(buy_picks[['Price', 'Score', 'Status', 'RSI', 'RVOL', 'ATR']], use_container_width=True)
        else:
            st.warning("No stocks currently meet 100% of the strict breakout criteria. Check back near market close or adjust score filters.")

    with tab2:
        st.subheader("📊 All Stock Universe Screener")
        filtered_df = df_all[df_all['Score'] >= min_score]
        st.dataframe(filtered_df[['Price', 'Score', 'Status', 'RSI', 'RVOL', 'ATR']], use_container_width=True)

    st.markdown("---")
    
    # Stock Detail Viewer
    all_available = df_all.index.tolist()
    if all_available:
        selected_stock = st.selectbox("Select Stock to View Detailed Analysis & Setup:", all_available)
        if selected_stock:
            stock_info, df_stock = results[selected_stock], chart_dfs[selected_stock]
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown(f"### {selected_stock}")
                st.metric("Current Price", f"₹{stock_info['Price']}")
                st.metric("TradingLab Score", f"{stock_info['Score']} / 50", delta=stock_info['Status'])
            with col2:
                st.markdown("### Technical Metrics")
                st.write(f"**RSI (14):** {stock_info['RSI']}")
                st.write(f"**Relative Volume (RVOL):** {stock_info['RVOL']}x")
                st.write(f"**ATR (14):** ₹{stock_info['ATR']}")
                st.write(f"**Preferred Buy Status:** {'✅ YES' if stock_info['Preferred_Buy'] else '❌ NO'}")
            with col3:
                st.markdown("### Automated Trade Plan")
                setup = stock_info['Setup']
                st.write(f"**Suggested Entry:** ₹{setup['Entry']}")
                st.write(f"**Stop Loss:** ₹{setup['Stop Loss']}")
                st.write(f"**Target:** ₹{setup['Target']}")
                st.write(f"**Risk/Reward Ratio:** {setup['Risk Reward']}")
                
            st.markdown("---")
            st.markdown("### Technical Chart (Price, RSI & MACD)")
            fig = render_candlestick_chart(df_stock, selected_stock)
            st.plotly_chart(fig, use_container_width=True)