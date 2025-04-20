import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import math

# App Config
st.set_page_config(page_title="NLevel Trader Gamer", page_icon="🎮", layout="wide")

# Initialize Session State
if 'trades' not in st.session_state:
    st.session_state.trades = pd.DataFrame(columns=[
        "Date", "Pair", "Platform", "Profit", "Loss", "Level", "Lot Size", "Balance"
    ])
if 'current_balance' not in st.session_state:
    st.session_state.current_balance = 20.0  # Starting balance

# Constants
MAX_LEVEL = 40
LEVEL_GROWTH_RATE = 1.30  # 30% growth per level
BASE_BALANCE = 20.00       # Starting amount
BASE_LOT_SIZE = 0.03       # Starting lot size
MAX_LOSS_PCT = 0.30        # 30% max loss per level

# Helper Functions
def calculate_current_level(balance):
    """Calculate level based on exponential growth from base balance"""
    if balance < BASE_BALANCE:
        return 1
    try:
        level = math.floor(math.log(balance / BASE_BALANCE) / math.log(LEVEL_GROWTH_RATE)) + 1
    except ValueError:
        level = 1
    return min(level, MAX_LEVEL)

def get_level_requirements(level):
    """Calculate level requirements for a given level"""
    if level < 1:
        level = 1
    starting_balance = BASE_BALANCE * (LEVEL_GROWTH_RATE ** (level - 1))
    
    level_up_requirement = starting_balance * (LEVEL_GROWTH_RATE - 1)
    target_balance = starting_balance * LEVEL_GROWTH_RATE
    lot_size = BASE_LOT_SIZE + (0.01 * (level - 1))
    risk_limit = starting_balance * MAX_LOSS_PCT
    
    return {
        "starting_balance": starting_balance,
        "level_up_requirement": level_up_requirement,
        "target_balance": target_balance,
        "lot_size": lot_size,
        "risk_limit": risk_limit
    }

# --- UI ---
st.title("🎮 NLevel Trader Gamer")
st.markdown("""
Track your trading progress across 40 levels with exponential growth.
- **Level Progression:** Each level requires 30% growth from previous level's starting balance
- **Risk Management:** Automatically adjusts level based on current balance
- **Lot Size Growth:** +0.01 per level (starts at 0.03)
""")

# --- Input Form ---
with st.form("trade_form"):
    col1, col2 = st.columns(2)
    
    with col1:
        pair = st.selectbox("Trading Pair", ["XAU/USD", "SOL/USD", "BTC/USD", "ETH/USD", "US100"])
        platform = st.selectbox("Platform", ["HFM", "FBS", "BYBIT", "WEEX", "MEXC"])
    
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
        # Get current state before trade
        old_level = calculate_current_level(st.session_state.current_balance)
        old_balance = st.session_state.current_balance
        
        # Apply trade result
        if profit > 0:
            st.session_state.current_balance += profit
        else:
            st.session_state.current_balance -= loss
        
        # Calculate new level
        new_level = calculate_current_level(st.session_state.current_balance)
        level_reqs = get_level_requirements(new_level)
        
        # Check for level changes
        if new_level > old_level:
            st.balloons()
            st.success(f"🎉 LEVEL UP! Now at Level {new_level}")
        elif new_level < old_level:
            st.warning(f"⚠️ Level decreased to {new_level} due to losses")
        
        # Check for catastrophic loss (below level 1 threshold)
        if st.session_state.current_balance < BASE_BALANCE * 0.7:  # More than 30% loss from base
            st.session_state.current_balance = BASE_BALANCE
            st.error("💥 CATASTROPHIC LOSS! Reset to Level 1 with $20")
        
        # Record trade
        new_trade = {
            "Date": datetime.combine(trade_date, trade_time),
            "Pair": pair,
            "Platform": platform,
            "Profit": profit,
            "Loss": loss,
            "Level": new_level,
            "Lot Size": level_reqs["lot_size"],
            "Balance": st.session_state.current_balance
        }
        st.session_state.trades = pd.concat([
            st.session_state.trades,
            pd.DataFrame([new_trade])
        ], ignore_index=True)

# --- Dashboard ---
st.divider()
current_level = calculate_current_level(st.session_state.current_balance)
level_reqs = get_level_requirements(current_level)

col1, col2, col3 = st.columns(3)
col1.metric("Current Level", current_level)
col2.metric("Account Balance", f"${st.session_state.current_balance:.2f}")
col3.metric("Current Lot Size", f"{level_reqs['lot_size']:.2f}")

# Progress to next level
if current_level < MAX_LEVEL:
    progress = (st.session_state.current_balance - level_reqs['starting_balance']) / level_reqs['level_up_requirement']
    st.progress(min(1.0, max(0.0, progress)))
    st.caption(f"⏳ {progress*100:.1f}% to Level {current_level + 1} (Need ${level_reqs['target_balance']:.2f})")
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
            title="Account Balance Over Time",
            markers=True
        )
        # Add level target lines
        for level in range(1, min(current_level + 3, MAX_LEVEL + 1)):
            reqs = get_level_requirements(level)
            fig.add_hline(y=reqs['starting_balance'], line_dash="dot", 
                         annotation_text=f"Level {level}", line_color="green")
        st.plotly_chart(fig, use_container_width=True)

with tab3:
    if not st.session_state.trades.empty:
        # Prepare level history data
        level_history = st.session_state.trades.groupby('Level').last().reset_index()
        fig = px.line(level_history, x="Level", y="Balance", 
                     title="Balance at Each Level Reached",
                     markers=True)
        st.plotly_chart(fig, use_container_width=True)

# --- Level Requirements Table ---
st.divider()
st.subheader("📋 Level Requirements Reference")

# Generate table for next 5 levels or until max level
display_levels = range(current_level, min(current_level + 5, MAX_LEVEL + 1))
level_data = []
for level in display_levels:
    reqs = get_level_requirements(level)
    level_data.append({
        "Level": level,
        "Minimum Balance": f"${reqs['starting_balance']:.2f}",
        "Target Balance": f"${reqs['target_balance']:.2f}",
        "Lot Size": reqs['lot_size'],
        "Max Allowed Loss": f"${reqs['risk_limit']:.2f}"
    })

st.table(pd.DataFrame(level_data))
