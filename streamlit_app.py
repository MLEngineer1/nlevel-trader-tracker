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
    level = math.floor(math.log(balance / BASE_BALANCE) / math.log(LEVEL_GROWTH_RATE)) + 1
    return min(level, MAX_LEVEL)

def get_level_requirements(level):
    """Calculate level requirements for a given level"""
    if level == 1:
        starting_balance = BASE_BALANCE
    else:
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
- **Risk Management:** 30% max loss per level (reset if hit)
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
        current_level = calculate_current_level(st.session_state.current_balance)
        level_reqs = get_level_requirements(current_level)
        
        if profit > 0:
            st.session_state.current_balance += profit
        else:
            st.session_state.current_balance -= loss
        
        # Check for level up
        new_level = calculate_current_level(st.session_state.current_balance)
        if new_level > current_level:
            st.balloons()
            st.success(f"🎉 LEVEL UP! Now at Level {new_level}")
        
        # Check for level reset (max loss)
        if loss > 0 and loss >= level_reqs["risk_limit"]:
            st.session_state.current_balance = BASE_BALANCE
            st.error("💥 MAX LOSS HIT! Reset to Level 1")
        
        # Record trade
        new_level = calculate_current_level(st.session_state.current_balance)
        level_reqs = get_level_requirements(new_level)
        
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

# Level Requirements Table
with st.expander("📊 Current Level Details"):
    level_data = {
        "Metric": ["Starting Balance", "Level Up Requirement", "Target Balance", "Risk Limit"],
        "Value": [
            f"${level_reqs['starting_balance']:.2f}",
            f"${level_reqs['level_up_requirement']:.2f}",
            f"${level_reqs['target_balance']:.2f}",
            f"${level_reqs['risk_limit']:.2f} (Max Loss)"
        ]
    }
    st.table(pd.DataFrame(level_data))

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
                         annotation_text=f"Level {level} Start", line_color="green")
            fig.add_hline(y=reqs['target_balance'], line_dash="dot", 
                         annotation_text=f"Level {level} Target", line_color="blue")
        st.plotly_chart(fig, use_container_width=True)

with tab3:
    if not st.session_state.trades.empty:
        # Prepare level progression data
        level_chart_data = []
        for level in range(1, min(current_level + 1, MAX_LEVEL + 1)):
            reqs = get_level_requirements(level)
            level_chart_data.append({
                "Level": level,
                "Starting Balance": reqs['starting_balance'],
                "Target Balance": reqs['target_balance'],
                "Lot Size": reqs['lot_size']
            })
        
        df_levels = pd.DataFrame(level_chart_data)
        fig = px.bar(df_levels, x="Level", y=["Starting Balance", "Target Balance"],
                     title="Level Progression Requirements", barmode="group")
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
    - Each level requires **30% growth** from the previous level's starting balance
    - Formula: `Target = Starting Balance × 1.3`
    - Example:
      - Level 1: $20 → Need $26 (30% of $20)
      - Level 2: $26 → Need $33.80 (30% of $26)
      - And so on...
    
    ### **Risk Management**
    - Maximum loss per level: **30%** of level's starting balance
    - If you hit max loss, you **reset to Level 1** with $20
    
    ### **Lot Size Growth**
    - Increases by **+0.01** per level
    - Level 1: 0.03
    - Level 2: 0.04
    - ...
    - Level 40: 0.42
    """)
