import os

files = {
    "engine/options_engine.py": '''import math

# Exact Lot Sizes for major NSE F&O Stocks & Indices
LOT_SIZES = {
    "NIFTY": 25,
    "BANKNIFTY": 15,
    "FINNIFTY": 25,
    "RELIANCE.NS": 250,
    "TCS.NS": 175,
    "HDFCBANK.NS": 550,
    "ICICIBANK.NS": 700,
    "SBIN.NS": 750,
    "BHARTIARTL.NS": 475,
    "TATAMOTORS.NS": 1425,
    "INFY.NS": 400,
    "HAL.NS": 300,
    "TATAINVEST.NS": 100,
}

DEFAULT_LOT_SIZE = 250  # Default FnO lot size fallback

def round_to_strike(price: float, step: float = 50.0) -> float:
    return round(price / step) * step

def generate_option_setup(symbol: str, spot_price: float, atr: float, capital: float, max_risk_pct: float, option_type: str = "CE", strike_mode: str = "ATM") -> dict:
    if not spot_price or spot_price <= 0:
        return {}
    
    # 1. Get exact Lot Size for the specific stock/index
    lot_size = LOT_SIZES.get(symbol, DEFAULT_LOT_SIZE)
    
    # 2. Determine Strike Step based on stock price magnitude
    if spot_price < 500:
        step = 10.0
    elif spot_price < 1500:
        step = 20.0
    elif spot_price < 5000:
        step = 50.0
    else:
        step = 100.0

    atm_strike = round_to_strike(spot_price, step)
    
    if strike_mode == "ITM":
        strike = atm_strike - step if option_type == "CE" else atm_strike + step
        delta = 0.65
        est_premium_pct = 0.035  # ~3.5% of spot price for ITM premium
    else:  # ATM
        strike = atm_strike
        delta = 0.50
        est_premium_pct = 0.020  # ~2.0% of spot price for ATM premium

    estimated_premium = round(spot_price * est_premium_pct, 2)
    cost_per_lot = estimated_premium * lot_size
    
    # 3. Capital Allocation for Options (deploy up to 100% account balance)
    lots_to_buy = int(capital // cost_per_lot) if cost_per_lot > 0 else 0
    
    if lots_to_buy < 1:
        lots_to_buy = 1  # Minimum 1 Lot if capital allows or forced minimum
        
    total_quantity = lots_to_buy * lot_size
    total_premium_required = round(total_quantity * estimated_premium, 2)
    
    # 4. Strictly cap risk at max_risk_pct of total account balance (e.g. 2% of ₹4,000 = ₹80)
    target_account_loss = capital * max_risk_pct
    
    # Calculate SL points per option unit
    premium_sl_drop = round(target_account_loss / total_quantity, 2) if total_quantity > 0 else 1.0
    option_sl_price = max(round(estimated_premium - premium_sl_drop, 2), 0.50)
    option_target_price = round(estimated_premium + (premium_sl_drop * 2.0), 2)
    
    actual_rupee_risk = round(premium_sl_drop * total_quantity, 2)
    actual_risk_pct = round((actual_rupee_risk / capital) * 100, 2)
    
    return {
        "Instrument": f"{int(strike)} {option_type}",
        "Strike": strike,
        "Option Type": option_type,
        "Est. Premium": estimated_premium,
        "Lot Size": lot_size,
        "Lots": lots_to_buy,
        "Total Qty": total_quantity,
        "Premium Required": total_premium_required,
        "Option SL": option_sl_price,
        "Option Target": option_target_price,
        "Risk Per Lot": round(premium_sl_drop * lot_size, 2),
        "Max Rupee Risk": actual_rupee_risk,
        "Risk Pct": actual_risk_pct
    }''',

    "app.py": '''import streamlit as st
import pandas as pd
import datetime
from engine.data_loader import load_stock_universe
from engine.market_data import fetch_batch_market_data
from engine.indicators import compute_indicators
from engine.analyzer import extract_latest_condition
from engine.scoring import score_market_condition
from engine.setup_generator import generate_trade_setup
from engine.options_engine import generate_option_setup
from components.charts import render_candlestick_chart

st.set_page_config(page_title="Medhansh TradingLab", layout="wide", page_icon="⚡")

# Sidebar - Mode Selection
market_mode = st.sidebar.selectbox("📈 Asset Class / Mode:", ["Equity Spot (Shares)", "NSE Options (CE/PE Buying)"])

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
else:
    leverage_multiplier = 1.0
    buying_power = capital
    option_strike_mode = st.sidebar.radio("Option Moneyness:", ["ATM (At-The-Money)", "ITM (In-The-Money)"])
    strike_type = "ITM" if "ITM" in option_strike_mode else "ATM"

max_risk_rupees = capital * max_risk_pct_input

st.sidebar.info(f"💰 **Buying / Capital Allocated:** ₹{buying_power:,.2f}")
st.sidebar.warning(f"🛑 **Max Rupee Loss Capped At:** ₹{max_risk_rupees:,.2f} ({max_risk_pct_input*100:.1f}%)")

st.sidebar.header("⚙️ Configuration & Filters")
universe = load_stock_universe()
min_score = st.sidebar.slider("Minimum Score Filter:", 0, 50, 30)

now_str = datetime.datetime.now().strftime("%H:%M:%S IST")
st.title(f"⚡ Medhansh TradingLab — {market_mode}")
st.caption(f"🟢 **SYSTEM ONLINE** | Last Update: `{now_str}` | Mode: `{market_mode}`")

@st.cache_data(ttl=20)
def run_pipeline(ticker_list, capital_input, leverage_input, risk_pct, period_lookback, mode):
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
                opt_type = "CE" if condition.get('Daily_Change', 0) >= 0 else "PE"
                setup = generate_option_setup(
                    symbol=ticker,
                    spot_price=condition.get('Price', 0),
                    atr=condition.get('ATR', 0),
                    capital=capital_input,
                    max_risk_pct=risk_pct,
                    option_type=opt_type,
                    strike_mode=strike_type
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

results, chart_dfs = run_pipeline(universe, capital, leverage_multiplier, max_risk_pct_input, default_period, market_mode)

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
            <h2 style="color: #00E676; margin: 0;">🎯 TOP FnO OPTION PICK: {winner_ticker} {winner_setup['Instrument']}</h2>
            <p style="font-size: 15px; color: #CCCCCC;"><b>Stock Spot Price:</b> ₹{winner_info['Price']} | <b>Lot Size:</b> {winner_setup['Lot Size']} Qty/Lot</p>
            <hr style="border-color: #333;">
            <div style="display: flex; justify-content: space-between; flex-wrap: wrap; gap: 10px;">
                <div><b>Est. Option Premium:</b> ₹{winner_setup['Est. Premium']}</div>
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
            st.markdown(f"### {'FnO Option Plan' if market_mode != 'Equity Spot (Shares)' else 'Equity Spot Plan'}")
            setup = stock_info['Setup']
            if market_mode == "Equity Spot (Shares)":
                st.write(f"**Entry:** ₹{setup['Entry']}")
                st.write(f"**Stop Loss:** ₹{setup['Stop Loss']} (-{setup['SL_Pct']}%)")
                st.write(f"**Target:** ₹{setup['Target']}")
                st.write(f"**Position:** {setup['Shares to Buy']} Shares")
                st.write(f"**Capital Needed:** ₹{setup['Margin Required']:,}")
            else:
                st.write(f"**Contract:** {setup['Instrument']}")
                st.write(f"**Est. Premium:** ₹{setup['Est. Premium']}")
                st.write(f"**Option SL:** ₹{setup['Option SL']}")
                st.write(f"**Option Target:** ₹{setup['Option Target']}")
                st.write(f"**Position:** {setup['Lots']} Lot ({setup['Total Qty']} Contracts)")
                st.write(f"**Capital Needed:** ₹{setup['Premium Required']:,}")
                st.write(f"**Max Rupee Risk:** ₹{setup['Max Rupee Risk']}")
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

print("✅ SUCCESS: FnO lot sizing and mode separation updated!")