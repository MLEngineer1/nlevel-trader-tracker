import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# App Config
st.set_page_config(page_title="NLevel Trader Gamer", page_icon="🎮", layout="wide")

# Initialize Session State
if 'trades' not in st.session_state:
    st.session_state.trades = pd.DataFrame(columns=[
        "Date", "Pair", "Platform", "Profit", "Loss", "Level", "Lot Size", "Balance"
    ])
if 'current_level' not in st.session_state:
    st.session_state.current_level = 1
if 'current_balance' not in st.session_state:
    st.session_state.current_balance = 20.0  # Starting balance
if 'lot_size' not in st.session_state:
    st.session_state.lot_size = 0.03  # Starting lot size

# Constants
MAX_LEVEL = 40
LEVEL_UP_PROFIT_PCT = 0.30  # 30% profit needed to level up
MAX_LOSS_PCT = 0.30         # 30% max loss per level
BASE_BALANCE = 20.00        # Starting amount

# --- UI ---
st.title("🎮 NLevel Trader Gamer")
st.markdown("""
Track your trading progress across 40 levels with risk/reward mechanics.
- **Level Up Condition:** 30% profit from current level's starting balance
- **Max Loss Per Level:** 30% (if hit, reset to level 1)
- **Lot Size Growth:** +0.01 per level (starts at 0.03)
""")

# --- Input Form ---
with st.form("trade_form"):
    col1, col2 = st.columns(2)
    
    with col1:
        pair = st.selectbox("Trading Pair", ["XAU/USD", "EUR/USD", "BTC/USD", "ETH/USD", "Custom"])
        platform = st.selectbox("Platform", ["MetaTrader 4", "MetaTrader 5", "cTrader", "TradingView", "Other"])
    
    with col2:
        profit = st.number_input("Profit ($)", min_value=0.0, step=0.01)
        loss = st.number_input("Loss ($)", min_value=0.0, step=0.01)
        trade_date = st.date_input("Date")
        trade_time = st.time_input("Time")
    
    submitted = st.form_submit_button("Submit Trade")

# --- Process Trade ---
if submitted:
    if profit == 0 and loss == 0:
        st.error("❗ Enter either Profit or Loss")
    else:
        # Calculate new balance
        if profit > 0:
            st.session_state.current_balance += profit
        else:
            st.session_state.current_balance -= loss
        
        # Check for level up or reset
        level_start_balance = BASE_BALANCE * (1 + LEVEL_UP_PROFIT_PCT) ** (st.session_state.current_level - 1)
        next_level_requirement = level_start_balance * LEVEL_UP_PROFIT_PCT
        
        if st.session_state.current_balance >= level_start_balance + next_level_requirement:
            st.session_state.current_level += 1
            st.session_state.lot_size += 0.01
            st.balloons()
            st.success(f"🎉 LEVEL UP! Now at Level {st.session_state.current_level}")
        
        # Check for level reset (max loss)
        max_loss = level_start_balance * MAX_LOSS_PCT
        if loss > 0 and loss >= max_loss:
            st.session_state.current_level = 1
            st.session_state.current_balance = BASE_BALANCE
            st.session_state.lot_size = 0.03
            st.error("💥 MAX LOSS HIT! Reset to Level 1")
        
        # Record trade
        new_trade = {
            "Date": datetime.combine(trade_date, trade_time),
            "Pair": pair,
            "Platform": platform,
            "Profit": profit,
            "Loss": loss,
            "Level": st.session_state.current_level,
            "Lot Size": st.session_state.lot_size,
            "Balance": st.session_state.current_balance
        }
        st.session_state.trades = pd.concat([
            st.session_state.trades,
            pd.DataFrame([new_trade])
        ], ignore_index=True)

# --- Dashboard ---
st.divider()
col1, col2, col3 = st.columns(3)
col1.metric("Current Level", st.session_state.current_level)
col2.metric("Account Balance", f"${st.session_state.current_balance:.2f}")
col3.metric("Current Lot Size", st.session_state.lot_size)

# Progress to next level
if st.session_state.current_level < MAX_LEVEL:
    level_start_balance = BASE_BALANCE * (1 + LEVEL_UP_PROFIT_PCT) ** (st.session_state.current_level - 1)
    next_level_requirement = level_start_balance * LEVEL_UP_PROFIT_PCT
    progress = (st.session_state.current_balance - level_start_balance) / next_level_requirement
    st.progress(min(1.0, max(0.0, progress)))
    st.caption(f"⏳ {progress*100:.1f}% to Level {st.session_state.current_level + 1}")
else:
    st.success("🏆 CONGRATULATIONS! You've reached MAX LEVEL!")

# --- Analytics ---
st.divider()
st.subheader("📊 Trading Analytics")

tab1, tab2, tab3 = st.tabs(["Trade History", "Balance Growth", "Level Progression"])

with tab1:
    st.dataframe(st.session_state.trades.sort_values("Date", ascending=False))

with tab2:
    if not st.session_state.trades.empty:
        fig = px.line(
            st.session_state.trades,
            x="Date",
            y="Balance",
            title="Account Balance Over Time"
        )
        st.plotly_chart(fig, use_container_width=True)

with tab3:
    if not st.session_state.trades.empty:
        fig = px.bar(
            st.session_state.trades.groupby("Level").size().reset_index(name="Trades"),
            x="Level",
            y="Trades",
            title="Trades per Level"
        )
        st.plotly_chart(fig, use_container_width=True)

# --- How to Play ---
st.divider()
with st.expander("📖 Game Rules"):
    st.markdown("""
    ## **NLevel Trader Gamer Rules**
    
    - **Starting Balance:** $20
    - **Starting Lot Size:** 0.03
    - **Levels:** 40 total
    
    ### **Level Progression**
    - To advance to the next level, earn **30% profit** from your current level's starting balance.
    - Each level increases lot size by **+0.01**.
    
    ### **Risk Management**
    - Maximum loss per level: **30%** of level's starting balance.
    - If you hit max loss, you **reset to Level 1**.
    
    ### **Example**
    - **Level 1:** Start with $20, need $6 profit (30%) to reach Level 2.
    - **Level 2:** New starting balance = $26, need $7.8 profit to reach Level 3.
    - If you lose $6 (30% of $20) in Level 1 → Reset to Level 1.
    """)
