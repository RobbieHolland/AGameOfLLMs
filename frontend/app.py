import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time
import json
from datetime import datetime
import asyncio
import threading
import difflib

# Direct imports instead of API calls
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from backend.contest_engine import ContestEngine
from backend.models import api_response

# Configuration
API_BASE_URL = "http://localhost:8000"

# Page configuration
st.set_page_config(
    page_title="A Game of LLMs",
    page_icon="🎭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .metric-card {
        background-color: #ffffff;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
        border: 1px solid #e0e0e0;
        color: #333333;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        transition: box-shadow 0.3s ease;
    }
    
    .metric-card:hover {
        box-shadow: 0 4px 8px rgba(0,0,0,0.15);
    }
    
    .metric-card h4 {
        color: #1f77b4;
        margin-bottom: 0.5rem;
    }
    .metric-card h2 {
        color: #333333;
        margin: 0;
    }
    .winner-card {
        background-color: #d4edda;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #28a745;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .problem-card {
        background-color: #ffffff;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #ffc107;
        border: 1px solid #e0e0e0;
        color: #333333;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        transition: box-shadow 0.3s ease;
    }
    
    .problem-card:hover {
        box-shadow: 0 4px 8px rgba(0,0,0,0.15);
    }
    
    .problem-card h4 {
        color: #ffc107;
        margin-bottom: 0.5rem;
    }
    .problem-card p {
        color: #333333;
        margin: 0.5rem 0;
    }
    .evaluation-log {
        background-color: #ffffff;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #e0e0e0;
        font-family: monospace;
        font-size: 0.9rem;
        max-height: 400px;
        overflow-y: auto;
        color: #333333;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .evaluation-log h5 {
        color: #1f77b4;
        margin-bottom: 0.5rem;
    }
    .evaluation-log p {
        color: #333333;
        margin: 0.25rem 0;
    }
    
    /* Disable any highlighting on the button container */
    div[data-testid="stButton"] {
        user-select: none !important;
        -webkit-user-select: none !important;
        -moz-user-select: none !important;
        -ms-user-select: none !important;
    }
    
    /* TAB STYLING TO MATCH BUTTON */
    /* Tab container */
    div[data-testid="stTabs"] {
        margin-top: 1rem;
    }
    
    /* Tab list container */
    div[data-testid="stTabs"] [role="tablist"] {
        background-color: #f8f9fa !important;
        border-radius: 12px !important;
        padding: 4px !important;
        gap: 4px !important;
        border: 1px solid #e0e0e0 !important;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1) !important;
    }
    
    /* Individual tab buttons */
    div[data-testid="stTabs"] button[role="tab"] {
        background: linear-gradient(135deg, #e9ecef 0%, #f8f9fa 100%) !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 8px 16px !important;
        color: #495057 !important;
        font-size: 14px !important;
        font-weight: 600 !important;
        cursor: pointer !important;
        transition: all 0.3s ease !important;
        margin: 0 !important;
        outline: none !important;
        user-select: none !important;
        -webkit-user-select: none !important;
        -moz-user-select: none !important;
        -ms-user-select: none !important;
        text-shadow: none !important;
        min-height: 36px !important;
        flex: 1 !important;
        text-align: center !important;
    }
    
    /* Hover state for inactive tabs */
    div[data-testid="stTabs"] button[role="tab"]:hover:not([aria-selected="true"]) {
        background: linear-gradient(135deg, #dee2e6 0%, #e9ecef 100%) !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 2px 8px rgba(31, 119, 180, 0.2) !important;
        color: #333333 !important;
    }
    
    /* Active/selected tab */
    div[data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
        background: linear-gradient(135deg, #1f77b4 0%, #17a2b8 100%) !important;
        color: #ffffff !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 12px rgba(31, 119, 180, 0.4) !important;
        z-index: 2 !important;
        position: relative !important;
    }
    
    /* Active tab hover */
    div[data-testid="stTabs"] button[role="tab"][aria-selected="true"]:hover {
        background: linear-gradient(135deg, #17a2b8 0%, #1f77b4 100%) !important;
        box-shadow: 0 6px 16px rgba(31, 119, 180, 0.5) !important;
    }
    
    /* Tab focus state */
    div[data-testid="stTabs"] button[role="tab"]:focus {
        outline: none !important;
        box-shadow: 0 0 0 2px rgba(31, 119, 180, 0.3) !important;
    }
    
    /* Tab content area */
    div[data-testid="stTabs"] [role="tabpanel"] {
        background-color: transparent !important;
        padding: 1rem 0 !important;
        border: none !important;
    }
    
    /* Remove default tab styling */
    div[data-testid="stTabs"] button[role="tab"] * {
        color: inherit !important;
        user-select: none !important;
        pointer-events: none !important;
    }
    
    /* Ensure tab text is not selectable */
    div[data-testid="stTabs"] button[role="tab"]::selection,
    div[data-testid="stTabs"] button[role="tab"] *::selection {
        background: transparent !important;
    }
    
    div[data-testid="stTabs"] button[role="tab"]::-moz-selection,
    div[data-testid="stTabs"] button[role="tab"] *::-moz-selection {
        background: transparent !important;
    }
    
    /* CONSTITUTION DIFF STYLING */
    .constitution-diff-container {
        display: flex;
        gap: 1rem;
        margin: 1rem 0;
    }
    
    .constitution-panel {
        flex: 1;
        background-color: #ffffff !important;
        border: 1px solid #e0e0e0 !important;
        border-radius: 0.5rem !important;
        padding: 1rem !important;
        font-family: 'Courier New', monospace !important;
        font-size: 14px !important;
        line-height: 1.4 !important;
        overflow-y: auto !important;
        max-height: 500px !important;
        position: relative !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1) !important;
    }
    
    .constitution-panel h4 {
        color: #1f77b4 !important;
        margin-bottom: 1rem !important;
        font-size: 16px !important;
        font-weight: 600 !important;
        border-bottom: 1px solid #e0e0e0 !important;
        padding-bottom: 0.5rem !important;
    }
    
    .constitution-panel .version-info {
        color: #6c757d !important;
        font-size: 12px !important;
        margin-bottom: 1rem !important;
        font-style: italic !important;
    }
    
    .diff-line {
        padding: 2px 4px !important;
        margin: 1px 0 !important;
        border-radius: 2px !important;
        white-space: pre-wrap !important;
        word-break: break-word !important;
    }
    
    .diff-unchanged {
        color: #333333 !important;
        background-color: transparent !important;
    }
    
    .diff-added {
        color: #333333 !important;
        background-color: rgba(40, 167, 69, 0.2) !important;
        border-left: 3px solid #28a745 !important;
        padding-left: 8px !important;
    }
    
    .diff-removed {
        color: #333333 !important;
        background-color: rgba(220, 53, 69, 0.2) !important;
        border-left: 3px solid #dc3545 !important;
        padding-left: 8px !important;
    }
    
    .diff-controls {
        background-color: #f8f9fa !important;
        border: 1px solid #e0e0e0 !important;
        border-radius: 0.5rem !important;
        padding: 1rem !important;
        margin-bottom: 1rem !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1) !important;
    }
    
    .diff-controls h4 {
        color: #1f77b4 !important;
        margin-bottom: 1rem !important;
    }
    
    .slider-container {
        display: flex !important;
        align-items: center !important;
        gap: 1rem !important;
        margin: 0.5rem 0 !important;
    }
    
    .slider-label {
        color: #333333 !important;
        font-weight: 600 !important;
        min-width: 100px !important;
    }
    
    .version-indicator {
        background-color: #e9ecef !important;
        border: 1px solid #dee2e6 !important;
        border-radius: 4px !important;
        padding: 0.25rem 0.5rem !important;
        color: #333333 !important;
        font-family: monospace !important;
        font-size: 12px !important;
    }
</style>
""", unsafe_allow_html=True)


def fetch_api_data(endpoint: str):
    """Fetch data from API endpoint."""
    try:
        response = requests.get(f"{API_BASE_URL}{endpoint}", timeout=5)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"API Error: {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        st.error(f"Connection Error: {e}")
        return None


def post_api_data(endpoint: str, data: dict):
    """Post data to API endpoint."""
    try:
        response = requests.post(f"{API_BASE_URL}{endpoint}", json=data, timeout=5)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"API Error: {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        st.error(f"Connection Error: {e}")
        return None


def display_leaderboard():
    """Display the current leaderboard."""
    leaderboard_data = fetch_api_data("/leaderboard")
    transactions_data = fetch_api_data("/bank/transactions")
    
    if leaderboard_data and leaderboard_data.get("success"):
        leaderboard = leaderboard_data["data"]
        
        if leaderboard:
            # Filter out PrincipleEvaluator to show only players
            player_leaderboard = [entry for entry in leaderboard if entry['name'] != 'PrincipleEvaluator']
            
            if player_leaderboard and transactions_data and transactions_data.get("success"):
                # Get transaction history to build balance over time
                transactions = transactions_data["data"]["transactions"]
                
                if transactions:
                    # Create balance history for line plot
                    df_transactions = pd.DataFrame(transactions)
                    df_transactions['timestamp'] = pd.to_datetime(df_transactions['timestamp'])
                    
                    # Filter for players only
                    player_transactions = df_transactions[
                        df_transactions['actor'].isin([p['name'] for p in player_leaderboard])
                    ].copy()
                    
                    if not player_transactions.empty:
                        # Calculate running balance for each player per round
                        balance_history = []
                        for player in [p['name'] for p in player_leaderboard]:
                            player_txns = player_transactions[player_transactions['actor'] == player].copy()
                            player_txns = player_txns.sort_values('timestamp')
                            
                            # Extract problem/round number from reason field
                            player_txns['round'] = player_txns['reason'].str.extract(r'Problem (\d+)').fillna('0').astype(int)
                            
                            # Group by round and sum deltas for each round
                            round_balances = player_txns.groupby('round')['delta'].sum().cumsum()
                            
                            for round_num, balance in round_balances.items():
                                if round_num > 0:  # Skip initial registration (round 0)
                                    balance_history.append({
                                        'round': f"Problem {round_num}",
                                        'round_num': round_num,
                                        'player': player,
                                        'balance': balance
                                    })
                        
                        if balance_history:
                            df_history = pd.DataFrame(balance_history)
                            
                            # Create line plot by round
                            fig = px.line(
                                df_history,
                                x='round_num',
                                y='balance',
                                color='player',
                                title="💰 Player Balance Per Round",
                                markers=True
                            )
                            fig.update_layout(
                                xaxis_title="Problem Number",
                                yaxis_title="Balance ($)",
                                height=400,
                                hovermode='x unified'
                            )
                            # Update x-axis to show problem numbers
                            fig.update_xaxes(tickmode='linear', tick0=1, dtick=1)
                            st.plotly_chart(fig, use_container_width=True)
                        else:
                            # Fallback to current balances as bar chart
                            df = pd.DataFrame(player_leaderboard)
                            fig = px.bar(df, x="name", y="balance", title="💰 Current Player Balances")
                            st.plotly_chart(fig, use_container_width=True)
                    else:
                        # No player transactions yet, show current balances
                        df = pd.DataFrame(player_leaderboard)
                        fig = px.bar(df, x="name", y="balance", title="💰 Current Player Balances")
                        st.plotly_chart(fig, use_container_width=True)
                else:
                    # No transactions yet, show current balances
                    df = pd.DataFrame(player_leaderboard)
                    fig = px.bar(df, x="name", y="balance", title="💰 Current Player Balances")
                    st.plotly_chart(fig, use_container_width=True)
                
                # Display as table
                st.subheader("📊 Player Leaderboard")
                for i, entry in enumerate(player_leaderboard):
                    col1, col2, col3 = st.columns([1, 3, 2])
                    with col1:
                        if i == 0:
                            st.markdown("🥇")
                        elif i == 1:
                            st.markdown("🥈")
                        elif i == 2:
                            st.markdown("🥉")
                        else:
                            st.markdown(f"{i+1}.")
                    with col2:
                        st.markdown(f"**{entry['name']}**")
                    with col3:
                        color = "green" if entry['balance'] >= 0 else "red"
                        st.markdown(f"<span style='color: {color}'>${entry['balance']:,}</span>", 
                                  unsafe_allow_html=True)
            else:
                st.info("No players registered yet")
        else:
            st.info("No participants yet")
    else:
        st.error("Failed to fetch leaderboard data")


def display_contest_status():
    """Display current contest status."""
    status_data = fetch_api_data("/status")
    
    if status_data and status_data.get("success"):
        status = status_data["data"]
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown("""
            <div class="metric-card">
                <h4>Contest Status</h4>
                <h2>{}</h2>
            </div>
            """.format("🟢 Active" if status["is_active"] else "🔴 Inactive"), 
            unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div class="metric-card">
                <h4>Current Problem</h4>
                <h2>{}/{}</h2>
            </div>
            """.format(status["current_problem_index"] + 1, status["total_problems"]), 
            unsafe_allow_html=True)
        
        with col3:
            st.markdown("""
            <div class="metric-card">
                <h4>Participants</h4>
                <h2>{}</h2>
            </div>
            """.format(len(status["participants"])), 
            unsafe_allow_html=True)
        
        with col4:
            start_time = status.get("start_time")
            if start_time:
                start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                elapsed = datetime.now() - start_dt.replace(tzinfo=None)
                elapsed_str = str(elapsed).split('.')[0]  # Remove microseconds
            else:
                elapsed_str = "Not started"
            
            st.markdown("""
            <div class="metric-card">
                <h4>Elapsed Time</h4>
                <h2>{}</h2>
            </div>
            """.format(elapsed_str), 
            unsafe_allow_html=True)
        
        # Current problem details
        if status.get("current_problem"):
            problem = status["current_problem"]
            st.markdown("""
            <div class="problem-card">
                <h4>📝 Current Problem: {}</h4>
                <p><strong>Description:</strong> {}</p>
                <details>
                    <summary>View Problem Code</summary>
                    <pre>{}</pre>
                </details>
            </div>
            """.format(
                problem["id"], 
                problem.get("description", "No description available"),
                problem["stub_code"]
            ), unsafe_allow_html=True)
        
        return status
    else:
        st.error("Failed to fetch contest status")
        return None


def display_principle_evaluator_output():
    """Display Principle Evaluator's recent evaluations and decisions."""
    evaluations_data = fetch_api_data("/principle/evaluations")
    
    if evaluations_data and evaluations_data.get("success"):
        evaluations = evaluations_data["data"]["evaluations"]
        
        st.subheader("🤖 Principle Evaluator Output")
        
        if evaluations:
            # Show latest evaluation
            latest = evaluations[-1]
            
            st.markdown(f"""
            <div class="evaluation-log">
                <h5>Latest Evaluation - Problem {latest['problem_id']}</h5>
                <p><strong>Timestamp:</strong> {latest['timestamp']}</p>
            """, unsafe_allow_html=True)
            
            # Display evaluation log
            for log_entry in latest.get('log', []):
                st.markdown(f"<p>• {log_entry}</p>", unsafe_allow_html=True)
            
            st.markdown("</div>", unsafe_allow_html=True)
            
            # Show evaluation history
            if len(evaluations) > 1:
                with st.expander("📜 Evaluation History"):
                    for eval_data in reversed(evaluations[:-1]):
                        st.markdown(f"**Problem {eval_data['problem_id']}** - {eval_data['timestamp']}")
                        for log_entry in eval_data.get('log', []):
                            st.text(f"  • {log_entry}")
                        st.markdown("---")
        else:
            st.info("No evaluations yet")
    else:
        st.error("Failed to fetch Principle Evaluator data")


def display_constitution():
    """Display current constitution and allow updates."""
    constitution_data = fetch_api_data("/constitution")
    
    if constitution_data and constitution_data.get("success"):
        data = constitution_data["data"]
        
        st.subheader("📜 Contest Constitution")
        
        # Display current constitution
        st.markdown("""
        <div class="metric-card">
            <h4>Current Rules</h4>
            <pre>{}</pre>
        </div>
        """.format(data["text"]), unsafe_allow_html=True)
        
        # Constitution update form (for Principle Evaluator)
        with st.expander("🔧 Update Constitution (Principle Evaluator Only)"):
            new_constitution = st.text_area(
                "New Constitution Text",
                value=data["text"],
                height=200
            )
        
        # Constitution history
        if data.get("history"):
            with st.expander("📚 Constitution History"):
                for change in reversed(data["history"]):
                    st.markdown(f"**{change['timestamp']}** - Updated by {change['updated_by']}")
                    st.text("Old text:")
                    st.code(change['old_text'])
                    st.text("New text:")
                    st.code(change['new_text'])
                    st.markdown("---")


def display_bank_transactions():
    """Display bank transaction history."""
    transactions_data = fetch_api_data("/bank/transactions")
    
    if transactions_data and transactions_data.get("success"):
        transactions = transactions_data["data"]["transactions"]
        
        if transactions:
            st.subheader("💳 Recent Bank Transactions")
            
            # Convert to DataFrame for better display
            df = pd.DataFrame(transactions)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.sort_values('timestamp', ascending=False)
            
            # Show recent transactions
            recent_transactions = df.head(10)
            
            for _, transaction in recent_transactions.iterrows():
                col1, col2, col3, col4 = st.columns([2, 2, 1, 2])
                
                with col1:
                    st.text(transaction['actor'])
                with col2:
                    st.text(transaction['timestamp'].strftime('%H:%M:%S'))
                with col3:
                    color = "green" if transaction['delta'] >= 0 else "red"
                    st.markdown(f"<span style='color: {color}'>{transaction['delta']:+}</span>", 
                              unsafe_allow_html=True)
                with col4:
                    st.text(transaction.get('reason', ''))
        else:
            st.info("No transactions yet")


def control_panel():
    """Contest control panel."""
    st.sidebar.header("🎮 Contest Controls")
    
    # Custom styled start game button
    button_clicked = st.sidebar.button("🎭 Start Game", type="primary", key="start_game_main")
    
    # Apply custom styling to the actual Streamlit button
    st.sidebar.markdown("""
    <style>
    /* Style the actual Streamlit button */
    div[data-testid="stButton"] button[kind="primary"] {
        background: linear-gradient(135deg, #1f77b4 0%, #17a2b8 100%) !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 12px 24px !important;
        color: white !important;
        font-size: 16px !important;
        font-weight: 600 !important;
        cursor: pointer !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 15px rgba(31, 119, 180, 0.3) !important;
        width: 100% !important;
        margin-bottom: 1rem !important;
        height: auto !important;
        min-height: 48px !important;
        outline: none !important;
        text-decoration: none !important;
        user-select: none !important;
        -webkit-user-select: none !important;
        -moz-user-select: none !important;
        -ms-user-select: none !important;
        -webkit-tap-highlight-color: transparent !important;
        -webkit-appearance: none !important;
        -moz-appearance: none !important;
        appearance: none !important;
        text-shadow: none !important;
        box-sizing: border-box !important;
        font-family: inherit !important;
    }
    
    div[data-testid="stButton"] button[kind="primary"]:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(31, 119, 180, 0.4) !important;
        background: linear-gradient(135deg, #17a2b8 0%, #1f77b4 100%) !important;
        outline: none !important;
        user-select: none !important;
    }
    
    div[data-testid="stButton"] button[kind="primary"]:active {
        transform: translateY(0) !important;
        box-shadow: 0 2px 10px rgba(31, 119, 180, 0.3) !important;
        outline: none !important;
        user-select: none !important;
    }
    
    div[data-testid="stButton"] button[kind="primary"]:focus {
        outline: none !important;
        box-shadow: 0 4px 15px rgba(31, 119, 180, 0.3) !important;
        user-select: none !important;
    }
    
    div[data-testid="stButton"] button[kind="primary"]:focus:not(:focus-visible) {
        outline: none !important;
    }
    
    div[data-testid="stButton"] button[kind="primary"]:focus-visible {
        outline: none !important;
        box-shadow: 0 4px 15px rgba(31, 119, 180, 0.3) !important;
    }
    
    /* Remove any text selection on button text */
    div[data-testid="stButton"] button[kind="primary"] *,
    div[data-testid="stButton"] button[kind="primary"]::selection,
    div[data-testid="stButton"] button[kind="primary"] *::selection {
        user-select: none !important;
        -webkit-user-select: none !important;
        -moz-user-select: none !important;
        -ms-user-select: none !important;
        pointer-events: none !important;
        background: transparent !important;
        color: inherit !important;
        text-shadow: none !important;
    }
    
    /* Completely disable selection */
    div[data-testid="stButton"] button[kind="primary"]::selection {
        background: transparent !important;
    }
    
    div[data-testid="stButton"] button[kind="primary"]::-moz-selection {
        background: transparent !important;
    }
    
    /* Disable any highlighting on the button container */
    div[data-testid="stButton"] {
        user-select: none !important;
        -webkit-user-select: none !important;
        -moz-user-select: none !important;
        -ms-user-select: none !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    if button_clicked:
        with st.sidebar:
            with st.spinner("Starting fresh game..."):
                result = post_api_data("/contest/run", {})
        
        if result and result.get("success"):
            st.sidebar.success("Game started fresh! Alice & Bob are competing...")
        else:
            st.sidebar.error(f"Failed to start game: {result}")


def main():
    """Main Streamlit application."""
    st.title("🎭 A Game of LLMs")
    st.markdown("Real-time monitoring of AI agents competing under evolving constitutional rules")
    
    # Control panel in sidebar
    control_panel()
    
    # Auto-refresh toggle
    auto_refresh = st.sidebar.checkbox("🔄 Auto-refresh (5s)", value=True)
    
    # Main dashboard
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "🤖 Principle Evaluator", "📜 Constitution", "💳 Transactions"])
    
    with tab1:
        # Contest status
        status = display_contest_status()
        
        st.markdown("---")
        
        # Leaderboard
        display_leaderboard()
    
    with tab2:
        display_principle_evaluator_output()
    
    with tab3:
        display_constitution()
    
    with tab4:
        display_bank_transactions()
    
    # Auto-refresh
    if auto_refresh:
        time.sleep(5)
        st.rerun()


if __name__ == "__main__":
    main() 