import os

files = {
    "engine/data_loader.py": '''def load_stock_universe():
    # Includes major indices (^NSEI for NIFTY 50, ^NSEBANK for BANK NIFTY) + liquid FnO stock universe
    return [
        "^NSEI",         # NIFTY 50 Index
        "^NSEBANK",      # BANK NIFTY Index
        "RELIANCE.NS",
        "TCS.NS",
        "HDFCBANK.NS",
        "ICICIBANK.NS",
        "SBIN.NS",
        "BHARTIARTL.NS",
        "TATAMOTORS.NS",
        "INFY.NS",
        "HAL.NS",
        "TATAINVEST.NS",
        "AXISBANK.NS",
        "LT.NS",
        "MARUTI.NS"
    ]''',

    "engine/options_engine.py": '''import math

LOT_SIZES = {
    "^NSEI": 25,          # NIFTY 50
    "^NSEBANK": 15,       # BANKNIFTY
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
    "AXISBANK.NS": 625,
    "LT.NS": 300,
    "MARUTI.NS": 100
}

DEFAULT_LOT_SIZE = 250

def round_to_strike(price: float, step: float = 50.0) -> float:
    return round(price / step) * step

def analyze_option_trend(spot_price: float, rsi: float, rvol: float, daily_change: float) -> dict:
    """Analyzes overall trend and directional bias for Options (CE vs PE dominance)."""
    if daily_change > 0.5 and rsi > 55:
        bias = "BULLISH CE"
        signal = "BUY CALL (CE)"
        strength = "STRONG UPWARD MOMENTUM"
        color = "#00E676"
    elif daily_change < -0.5 and rsi < 45:
        bias = "BEARISH PE"
        signal = "BUY PUT (PE)"
        strength = "STRONG DOWNWARD MOMENTUM"
        color = "#FF5252"
    else:
        bias = "SIDEWAYS / NEUTRAL"
        signal = "WAIT / NO CLEAR TREND"
        strength = "CONSOLIDATION"
        color = "#FFB300"

    return {
        "Bias": bias,
        "Signal": signal,
        "Strength": strength,
        "Color": color
    }

def generate_option_setup(symbol: str, spot_price: float, atr: float, capital: float, max_risk_pct: float, option_type: str = "CE", strike_mode: str = "ATM") -> dict:
    if not spot_price or spot_price <= 0:
        return {}
    
    lot_size = LOT_SIZES.get(symbol, DEFAULT_LOT_SIZE)
    
    # Dynamic Strike Steps
    if symbol in ["^NSEI", "NIFTY"]:
        step = 50.0
    elif symbol in ["^NSEBANK", "BANKNIFTY"]:
        step = 100.0
    elif spot_price < 500:
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
        est_premium_pct = 0.018 if "NSE" in symbol or symbol in ["NIFTY", "BANKNIFTY"] else 0.035
    else:  # ATM
        strike = atm_strike
        delta = 0.50
        est_premium_pct = 0.012 if "NSE" in symbol or symbol in ["NIFTY", "BANKNIFTY"] else 0.020

    estimated_premium = round(spot_price * est_premium_pct, 2)
    cost_per_lot = estimated_premium * lot_size
    
    lots_to_buy = int(capital // cost_per_lot) if cost_per_lot > 0 else 0
    if lots_to_buy < 1:
        lots_to_buy = 1  # Forced 1 lot min view
        
    total_quantity = lots_to_buy * lot_size
    total_premium_required = round(total_quantity * estimated_premium, 2)
    
    target_account_loss = capital * max_risk_pct
    premium_sl_drop = round(target_account_loss / total_quantity, 2) if total_quantity > 0 else 1.0
    option_sl_price = max(round(estimated_premium - premium_sl_drop, 2), 0.50)
    option_target_price = round(estimated_premium + (premium_sl_drop * 2.0), 2)
    
    actual_rupee_risk = round(premium_sl_drop * total_quantity, 2)
    actual_risk_pct = round((actual_rupee_risk / capital) * 100, 2)
    
    display_symbol = "NIFTY" if symbol == "^NSEI" else ("BANKNIFTY" if symbol == "^NSEBANK" else symbol.replace(".NS", ""))

    return {
        "Instrument": f"{display_symbol} {int(strike)} {option_type}",
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
from engine.options_engine import generate_option_setup, analyze_option_trend
from components.charts import render_candlestick_chart

st.set_page_config(page_title="Medhansh TradingLab", layout="wide", page_icon="⚡")

market_mode = st.sidebar.selectbox("📈 Asset Class / Mode:", ["NSE Options (CE/PE Buying)", "Equity Spot (Shares)"])

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
min_score = st.sidebar.slider("Minimum Score Filter:", 0, 50, 25)

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
            
            trend_info = analyze_option_trend(
                condition.get('Price', 0), 
                condition.get('RSI', 50), 
                condition.get('RVOL', 1.0), 
                condition.get('Daily_Change', 0)
            )

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
            
            clean_name = "NIFTY 50" if ticker == "^NSEI" else ("BANK NIFTY" if ticker == "^NSEBANK" else ticker)

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
                "OptionTrend": trend_info,
                "Setup": setup
            }
            chart_dfs[clean_name] = df_ind
        except Exception:
            continue

    return results, chart_dfs

results, chart_dfs = run_pipeline(universe, capital, leverage_multiplier, max_risk_pct_input, default_period, market_mode)

if results:
    # Option Index Trend Header Cards
    if "NIFTY 50" in results or "BANK NIFTY" in results:
        st.subheader("📊 Major Index Option Trends")
        idx_col1, idx_col2 = st.columns(2)
        
        if "NIFTY 50" in results:
            n_res = results["NIFTY 50"]
            n_trend = n_res['OptionTrend']
            with idx_col1:
                st.markdown(f"""
                <div style="background-color: #1A1D24; padding: 15px; border-radius: 8px; border-left: 5px solid {n_trend['Color']};">
                    <h3 style="margin: 0; color: #FFFFFF;">NIFTY 50 Options Trend</h3>
                    <p style="font-size: 20px; font-weight: bold; color: {n_trend['Color']}; margin: 5px 0;">{n_trend['Signal']} ({n_res['1D Change %']}%)</p>
                    <p style="margin: 0; color: #AAA;">Spot: <b>₹{n_res['Price']:,}</b> | RSI: <b>{n_res['RSI']}</b> | Trend: <b>{n_trend['Strength']}</b></p>
                </div>
                """, unsafe_allow_html=True)

        if "BANK NIFTY" in results:
            b_res = results["BANK NIFTY"]
            b_trend = b_res['OptionTrend']
            with idx_col2:
                st.markdown(f"""
                <div style="background-color: #1A1D24; padding: 15px; border-radius: 8px; border-left: 5px solid {b_trend['Color']};">
                    <h3 style="margin: 0; color: #FFFFFF;">BANK NIFTY Options Trend</h3>
                    <p style="font-size: 20px; font-weight: bold; color: {b_trend['Color']}; margin: 5px 0;">{b_trend['Signal']} ({b_res['1D Change %']}%)</p>
                    <p style="margin: 0; color: #AAA;">Spot: <b>₹{b_res['Price']:,}</b> | RSI: <b>{b_res['RSI']}</b> | Trend: <b>{b_trend['Strength']}</b></p>
                </div>
                """, unsafe_allow_html=True)

    st.markdown("---")

    df_all = pd.DataFrame.from_dict(results, orient='index')[['Price', '1D Change %', 'Score', 'Status', 'Pattern', 'Preferred_Buy', 'RSI', 'RVOL']]
    sorted_df = df_all.sort_values(by=['Score', 'RVOL', '1D Change %'], ascending=[False, False, False])
    
    winner_ticker = sorted_df.index[0]
    winner_setup = results[winner_ticker]['Setup']

    if market_mode != "Equity Spot (Shares)":
        st.markdown(f"""
        <div style="background-color: #1E222D; padding: 20px; border-radius: 10px; border: 2px solid #00E676; margin-bottom: 20px;">
            <h2 style="color: #00E676; margin: 0;">🎯 TOP RECOMMENDED OPTION TRADE: {winner_setup['Instrument']}</h2>
            <p style="font-size: 15px; color: #CCCCCC;"><b>Underlying Spot:</b> ₹{results[winner_ticker]['Price']} | <b>Lot Size:</b> {winner_setup['Lot Size']} Qty/Lot</p>
            <hr style="border-color: #333;">
            <div style="display: flex; justify-content: space-between; flex-wrap: wrap; gap: 10px;">
                <div><b>Est. Premium:</b> ₹{winner_setup['Est. Premium']}</div>
                <div><b>Premium Stop Loss:</b> <span style="color:#FF5252;">₹{winner_setup['Option SL']}</span></div>
                <div><b>Premium Target:</b> <span style="color:#00E676;">₹{winner_setup['Option Target']}</span></div>
                <div><b>Position Size:</b> <span style="color:#00E676; font-size:18px;"><b>{winner_setup['Lots']} Lot ({winner_setup['Total Qty']} Qty)</b></span></div>
                <div><b>Capital Allocated:</b> ₹{winner_setup['Premium Required']:,}</div>
                <div><b>Max Rupee Risk:</b> ₹{winner_setup['Max Rupee Risk']} ({winner_setup['Risk Pct']}%)</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.subheader("📊 Complete Market & Index Options Screener")
    st.dataframe(sorted_df[sorted_df['Score'] >= min_score], use_container_width=True)

    st.markdown("---")
    
    selected_stock = st.selectbox("Inspect Setup & Chart for Any Index / Stock:", sorted_df.index.tolist(), index=0)
    if selected_stock:
        stock_info, df_stock = results[selected_stock], chart_dfs[selected_stock]
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"### {selected_stock}")
            st.metric("Spot Price", f"₹{stock_info['Price']}", f"{stock_info['1D Change %']}%")
            st.metric("Algo Score", f"{stock_info['Score']} / 50", delta=stock_info['Status'])
        with col2:
            st.markdown("### Technical Trend")
            st.write(f"**Option Signal:** {stock_info['OptionTrend']['Signal']}")
            st.write(f"**Pattern:** {stock_info['Pattern']}")
            st.write(f"**RSI (14):** {stock_info['RSI']}")
            st.write(f"**RVOL:** {stock_info['RVOL']}x")
        with col3:
            st.markdown("### Trade Execution Plan")
            setup = stock_info['Setup']
            if market_mode == "Equity Spot (Shares)":
                st.write(f"**Entry:** ₹{setup['Entry']}")
                st.write(f"**Stop Loss:** ₹{setup['Stop Loss']}")
                st.write(f"**Target:** ₹{setup['Target']}")
                st.write(f"**Shares:** {setup['Shares to Buy']}")
            else:
                st.write(f"**Contract:** {setup['Instrument']}")
                st.write(f"**Est. Premium:** ₹{setup['Est. Premium']}")
                st.write(f"**Option SL:** ₹{setup['Option SL']}")
                st.write(f"**Option Target:** ₹{setup['Option Target']}")
                st.write(f"**Lots:** {setup['Lots']} Lot ({setup['Total Qty']} Contracts)")
                st.write(f"**Capital Needed:** ₹{setup['Premium Required']:,}")
        st.markdown("---")
        st.plotly_chart(render_candlestick_chart(df_stock, selected_stock), use_container_width=True)
else:
    st.error("Failed to load market data.")'''
}

for path, content in files.items():
    folder = os.path.dirname(path)
    if folder:
        os.makedirs(folder, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

print("✅ SUCCESS: NIFTY/BANKNIFTY Option trend analysis & index support added!")