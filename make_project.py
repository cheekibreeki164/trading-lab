import os

files = {
    "engine/setup_generator.py": '''def generate_trade_setup(price: float, atr: float, total_capital: float = 10000.0, leverage: float = 1.0, max_risk_pct: float = 0.02) -> dict:
    if not price or price <= 0:
        return {
            "Entry": 0, "Stop Loss": 0, "Target": 0, "Max Rupee Risk": 0, 
            "Actual Rupee Risk": 0, "Actual Account Risk Pct": 0, "Shares to Buy": 0, 
            "Total Position Value": 0, "Margin Required": 0, "Leverage": f"{leverage}x", "SL_Pct": 0
        }

    effective_capital = total_capital * leverage
    target_rupee_risk = total_capital * max_risk_pct
    
    # Dynamic ATR risk per share (1.5x ATR)
    risk_per_share = (atr * 1.5) if (atr and atr > 0) else (price * 0.015)
    
    # Calculate shares based on risk budget
    shares_by_risk = int(target_rupee_risk // risk_per_share) if risk_per_share > 0 else 1
    # Calculate maximum shares allowed by total buying power
    shares_by_capital = int(effective_capital // price)
    
    # Size position to target risk while staying within buying power limits
    shares_to_buy = min(shares_by_risk, shares_by_capital)
    if shares_to_buy < 1:
        shares_to_buy = 1
        
    total_trade_value = round(shares_to_buy * price, 2)
    margin_required = round(total_trade_value / leverage, 2)
    
    stop_loss = round(price - risk_per_share, 2)
    target = round(price + (risk_per_share * 2.0), 2)
    
    sl_distance_pct = round(((price - stop_loss) / price) * 100, 2)
    
    actual_rupee_risk = round(shares_to_buy * risk_per_share, 2)
    actual_risk_pct = round((actual_rupee_risk / total_capital) * 100, 2)

    return {
        "Entry": price,
        "Stop Loss": max(stop_loss, 0.1),
        "Target": target,
        "Max Rupee Risk": actual_rupee_risk,
        "Target Rupee Risk": round(target_rupee_risk, 2),
        "Actual Account Risk Pct": actual_risk_pct,
        "Shares to Buy": shares_to_buy,
        "Total Position Value": total_trade_value,
        "Margin Required": margin_required,
        "Leverage": f"{int(leverage)}x",
        "SL_Pct": sl_distance_pct
    }''',

    "app.py": '''import streamlit as st
import pandas as pd
import datetime
from streamlit_autorefresh import st_autorefresh
from engine.data_loader import load_stock_universe
from engine.market_data import fetch_batch_market_data
from engine.indicators import compute_indicators
from engine.analyzer import extract_latest_condition
from engine.scoring import score_market_condition
from engine.setup_generator import generate_trade_setup
from components.charts import render_candlestick_chart

st.set_page_config(page_title="Medhansh TradingLab", layout="wide", page_icon="⚡")

st.sidebar.header("🎯 Trading Strategy Profiles")
trade_style = st.sidebar.radio(
    "Select Horizon:",
    ["⚡ Intraday Breakdown", "📈 Swing Trade Setup", "🏦 Long-Term Breakout"],
    index=0
)

if "Intraday" in trade_style:
    default_period = "1mo"
    default_risk = 1.5
    default_lev = "5x (Intraday MIS Leverage)"
elif "Swing" in trade_style:
    default_period = "6mo"
    default_risk = 2.5
    default_lev = "1x (Cash Delivery)"
else:
    default_period = "2y"
    default_risk = 3.5
    default_lev = "1x (Cash Delivery)"

st.sidebar.header("🛡️ Capital & Risk Management")
capital = st.sidebar.number_input("Total Cash Balance (₹):", min_value=500.0, value=4000.0, step=500.0)
max_risk_pct_input = st.sidebar.slider("Max Balance Risk Per Trade (%):", 0.5, 5.0, default_risk, 0.5) / 100.0

leverage_option = st.sidebar.radio(
    "Leverage Mode:", 
    ["1x (Cash Delivery)", "5x (Intraday MIS Leverage)"], 
    index=0 if "1x" in default_lev else 1
)
leverage_multiplier = 5.0 if "5x" in leverage_option else 1.0

buying_power = capital * leverage_multiplier
max_risk_rupees = capital * max_risk_pct_input

st.sidebar.info(f"💰 **Purchasing Power:** ₹{buying_power:,.2f}")
st.sidebar.warning(f"🛑 **Target Max Loss Capped At:** ₹{max_risk_rupees:,.2f} ({max_risk_pct_input*100:.1f}%)")

st.sidebar.header("⏱️ Live Refresh Engine")
enable_autorefresh = st.sidebar.checkbox("Enable Auto-Refresh", value=True)
refresh_seconds = st.sidebar.slider("Refresh Interval (Seconds):", 15, 120, 30, 15)

if enable_autorefresh:
    count = st_autorefresh(interval=refresh_seconds * 1000, key="auto_refresh")

st.sidebar.header("⚙️ Configuration & Filters")
universe = load_stock_universe()
min_score = st.sidebar.slider("Minimum Score Filter:", 0, 50, 30)

now_str = datetime.datetime.now().strftime("%H:%M:%S IST")
st.title(f"⚡ Medhansh TradingLab — {trade_style}")
st.caption(f"🟢 **SYSTEM ONLINE** | Last Update: `{now_str}` | Auto Refresh: `{refresh_seconds}s` | Fetch Period: `{default_period}`")

@st.cache_data(ttl=20)
def run_pipeline(ticker_list, capital_input, leverage_input, risk_pct, period_lookback):
    results, chart_dfs = {}, {}
    batch_dfs = fetch_batch_market_data(ticker_list, period=period_lookback)
    
    for ticker, df in batch_dfs.items():
        try:
            df_ind = compute_indicators(df)
            condition = extract_latest_condition(df_ind, ticker)
            scores = score_market_condition(condition, df_ind)
            setup = generate_trade_setup(
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
results, chart_dfs = run_pipeline(universe, capital, leverage_multiplier, max_risk_pct_input, default_period)

if results:
    df_all = pd.DataFrame.from_dict(results, orient='index')[['Price', '1D Change %', 'Score', 'Status', 'Pattern', 'Preferred_Buy', 'RSI', 'RVOL', 'ATR']]
    sorted_df = df_all.sort_values(by=['Score', 'RVOL', '1D Change %'], ascending=[False, False, False])
    
    winner_ticker = sorted_df.index[0]
    winner_info = sorted_df.iloc[0]
    winner_setup = results[winner_ticker]['Setup']

    st.markdown(f"""
    <div style="background-color: #1E222D; padding: 20px; border-radius: 10px; border: 2px solid #00E676; margin-bottom: 20px;">
        <h2 style="color: #00E676; margin: 0;">🏆 TOP ALGO PICK: {winner_ticker} ({winner_setup['Leverage']} Mode)</h2>
        <p style="font-size: 15px; color: #CCCCCC;"><b>Pattern Detected:</b> {winner_info['Pattern']} | <b>Score:</b> {winner_info['Score']}/50 | <b>Risk-Reward Ratio:</b> 1:2.0</p>
        <hr style="border-color: #333;">
        <div style="display: flex; justify-content: space-between; flex-wrap: wrap; gap: 10px;">
            <div><b>Entry Price:</b> ₹{winner_setup['Entry']}</div>
            <div><b>Stop Loss ({winner_setup['SL_Pct']}% Drop):</b> <span style="color:#FF5252;">₹{winner_setup['Stop Loss']}</span></div>
            <div><b>Target Price:</b> <span style="color:#00E676;">₹{winner_setup['Target']}</span></div>
            <div><b>Position Size:</b> {winner_setup['Shares to Buy']} Shares</div>
            <div><b>Capital Allocated:</b> ₹{winner_setup['Margin Required']:,}</div>
            <div><b>Actual Rupee Risk:</b> ₹{winner_setup['Max Rupee Risk']} ({winner_setup['Actual Account Risk Pct']}%)</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["🔥 Preferred Buy Candidates", "📊 Full Screener"])
    
    with tab1:
        st.subheader("🔥 Top High-Conviction Breakouts")
        buy_picks = sorted_df[(sorted_df['Preferred_Buy'] == True) | (sorted_df['Score'] >= 40)]
        if not buy_picks.empty:
            st.dataframe(buy_picks[['Price', '1D Change %', 'Score', 'Status', 'Pattern', 'RSI', 'RVOL']], use_container_width=True)
        else:
            st.info("No stocks currently meet strict 4-indicator breakout alignment.")

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
            st.metric("Price", f"₹{stock_info['Price']}", f"{stock_info['1D Change %']}%")
            st.metric("Algo Score", f"{stock_info['Score']} / 50", delta=stock_info['Status'])
        with col2:
            st.markdown("### Technical Summary")
            st.write(f"**Pattern:** {stock_info['Pattern']}")
            st.write(f"**RSI (14):** {stock_info['RSI']}")
            st.write(f"**RVOL:** {stock_info['RVOL']}x")
            st.write(f"**14-Day ATR:** ₹{stock_info['ATR']}")
        with col3:
            st.markdown("### Execution Plan")
            setup = stock_info['Setup']
            st.write(f"**Entry:** ₹{setup['Entry']}")
            st.write(f"**Stop Loss:** ₹{setup['Stop Loss']} (-{setup['SL_Pct']}%)")
            st.write(f"**Target (1:2 R:R):** ₹{setup['Target']}")
            st.write(f"**Quantity:** {setup['Shares to Buy']} Shares")
            st.write(f"**Capital Needed:** ₹{setup['Margin Required']:,}")
            st.write(f"**Actual Risk:** ₹{setup['Max Rupee Risk']} ({setup['Actual Account Risk Pct']}% of capital)")
        st.markdown("---")
        st.plotly_chart(render_candlestick_chart(df_stock, selected_stock), use_container_width=True)
else:
    st.error("Failed to load market data. Please refresh or check connection.")'''
}

for path, content in files.items():
    folder = os.path.dirname(path)
    if folder:
        os.makedirs(folder, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

print("✅ SUCCESS: KeyError resolved!")