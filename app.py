import streamlit as st
import pandas as pd
import plotly.express as px
import time
from datetime import datetime
import sys
import os
import difflib

# Add backend to path so we can import directly
sys.path.append('backend')
from contest_engine import ContestEngine
from developers.starter_developer import Phi4Developer

# Page configuration
st.set_page_config(
    page_title="A Game of LLMs",
    page_icon="🎭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Simple styling - just basic dark background
st.markdown("""
<style>
    /* Basic dark background */
    .stApp {
        background-color: #1e1e1e;
    }
    
    /* Custom component cards */
    .metric-card {
        background-color: #2d2d2d;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #4fc3f7;
        margin-bottom: 1rem;
    }
    
    .metric-card h4 {
        color: #4fc3f7;
        margin-bottom: 0.5rem;
    }
    
    .metric-card h2 {
        margin: 0;
    }
    
    .winner-card {
        background-color: #1b5e20;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #4caf50;
        margin-bottom: 1rem;
    }
    
    .problem-card {
        background-color: #1e1e1e !important;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #ffb74d;
        border: 1px solid #404040;
        color: #ffffff !important;
        margin-bottom: 1rem;
    }
    
    .problem-card h4 {
        color: #ffb74d !important;
        margin-bottom: 0.5rem;
    }
    
    .problem-card p {
        color: #ffffff !important;
        margin: 0.5rem 0;
    }
    
    .problem-card pre {
        background-color: #0e1117 !important;
        color: #ffffff !important;
        border: 1px solid #404040 !important;
        padding: 1rem;
        border-radius: 0.25rem;
        overflow-x: auto;
    }
    
    .evaluation-log {
        background-color: #1e1e1e !important;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #404040;
        font-family: monospace;
        font-size: 0.9rem;
        max-height: 400px;
        overflow-y: auto;
        color: #ffffff !important;
        margin-bottom: 1rem;
    }
    
    .evaluation-log h5 {
        color: #4fc3f7 !important;
        margin-bottom: 0.5rem;
    }
    
    .evaluation-log p {
        color: #ffffff !important;
        margin: 0.25rem 0;
    }
    
    /* Code blocks */
    code {
        background-color: #1e1e1e !important;
        color: #4fc3f7 !important;
        padding: 0.2rem 0.4rem !important;
        border-radius: 0.25rem !important;
        border: 1px solid #404040 !important;
    }
    
    pre {
        background-color: #1e1e1e !important;
        color: #ffffff !important;
        border: 1px solid #404040 !important;
        padding: 1rem !important;
        border-radius: 0.5rem !important;
        overflow-x: auto !important;
    }
    
    /* Let Plotly handle its own styling */
    
    /* Spinner */
    .stSpinner {
        color: #4fc3f7 !important;
    }
    
    /* Columns */
    .element-container {
        color: #ffffff !important;
    }
    
    /* Success/Error/Info messages */
    .stSuccess {
        background-color: #1b5e20 !important;
        color: #ffffff !important;
        border: 1px solid #4caf50 !important;
    }
    
    .stError {
        background-color: #5d1a1a !important;
        color: #ffffff !important;
        border: 1px solid #f44336 !important;
    }
    
    .stInfo {
        background-color: #1e3a5f !important;
        color: #ffffff !important;
        border: 1px solid #2196f3 !important;
    }
    
    .stWarning {
        background-color: #5d4e1a !important;
        color: #ffffff !important;
        border: 1px solid #ff9800 !important;
    }
    
    /* Details/Summary elements */
    details {
        background-color: #1e1e1e !important;
        color: #ffffff !important;
        border: 1px solid #404040 !important;
        border-radius: 0.25rem !important;
        padding: 0.5rem !important;
        margin: 0.5rem 0 !important;
    }
    
    summary {
        color: #4fc3f7 !important;
        cursor: pointer !important;
        font-weight: bold !important;
    }
    
    summary:hover {
        color: #29b6f6 !important;
    }
    
    /* Additional comprehensive styling */
    
    /* Force all text elements to white */
    * {
        color: #ffffff !important;
    }
    
    /* Override any remaining light backgrounds */
    div[data-testid="stSidebar"] {
        background-color: #262730 !important;
    }
    
    div[data-testid="stSidebar"] * {
        color: #ffffff !important;
    }
    
    /* Main content wrapper */
    div[data-testid="stAppViewContainer"] {
        background-color: #0e1117 !important;
    }
    
    div[data-testid="stHeader"] {
        background-color: #0e1117 !important;
    }
    
    /* Metric containers */
    div[data-testid="metric-container"] {
        background-color: #1e1e1e !important;
        border: 1px solid #404040 !important;
        border-radius: 0.5rem !important;
        padding: 1rem !important;
    }
    
    div[data-testid="metric-container"] * {
        color: #ffffff !important;
    }
    
    /* Column containers */
    div[data-testid="column"] {
        background-color: transparent !important;
    }
    
    /* Plotly chart containers */
    div[data-testid="stPlotlyChart"] {
        background-color: #0e1117 !important;
    }
    
    /* DataFrame/table styling */
    div[data-testid="stDataFrame"] {
        background-color: #1e1e1e !important;
        border: 1px solid #404040 !important;
        border-radius: 0.5rem !important;
    }
    
    div[data-testid="stDataFrame"] * {
        color: #ffffff !important;
        background-color: #1e1e1e !important;
    }
    
    /* Table headers */
    th {
        background-color: #262730 !important;
        color: #4fc3f7 !important;
        border: 1px solid #404040 !important;
    }
    
    /* Table cells */
    td {
        background-color: #1e1e1e !important;
        color: #ffffff !important;
        border: 1px solid #404040 !important;
    }
    
    /* Form elements */
    .stForm {
        background-color: #1e1e1e !important;
        border: 1px solid #404040 !important;
        border-radius: 0.5rem !important;
        padding: 1rem !important;
    }
    
    .stForm * {
        color: #ffffff !important;
    }
    
    /* Radio buttons */
    .stRadio {
        color: #ffffff !important;
    }
    
    .stRadio > div {
        background-color: #1e1e1e !important;
        border: 1px solid #404040 !important;
        border-radius: 0.5rem !important;
        padding: 0.5rem !important;
    }
    
    /* Multiselect */
    .stMultiSelect {
        color: #ffffff !important;
    }
    
    .stMultiSelect > div > div {
        background-color: #1e1e1e !important;
        border: 1px solid #404040 !important;
        color: #ffffff !important;
    }
    
    /* Slider */
    .stSlider {
        color: #ffffff !important;
    }
    
    .stSlider > div > div > div {
        background-color: #4fc3f7 !important;
    }
    
    /* Number input */
    .stNumberInput > div > div > input {
        background-color: #1e1e1e !important;
        color: #ffffff !important;
        border: 1px solid #404040 !important;
    }
    
    /* Date input */
    .stDateInput > div > div > input {
        background-color: #1e1e1e !important;
        color: #ffffff !important;
        border: 1px solid #404040 !important;
    }
    
    /* Time input */
    .stTimeInput > div > div > input {
        background-color: #1e1e1e !important;
        color: #ffffff !important;
        border: 1px solid #404040 !important;
    }
    
    /* File uploader */
    .stFileUploader {
        background-color: #1e1e1e !important;
        border: 1px solid #404040 !important;
        border-radius: 0.5rem !important;
        color: #ffffff !important;
    }
    
    .stFileUploader * {
        color: #ffffff !important;
    }
    
    /* Progress bar */
    .stProgress > div > div {
        background-color: #4fc3f7 !important;
    }
    
    /* Balloons and other animations */
    .stBalloons {
        color: #4fc3f7 !important;
    }
    
    /* JSON display */
    .stJson {
        background-color: #1e1e1e !important;
        border: 1px solid #404040 !important;
        border-radius: 0.5rem !important;
        color: #ffffff !important;
    }
    
    /* Caption text */
    .caption {
        color: #b0b0b0 !important;
    }
    
    /* Subheader */
    .stSubheader {
        color: #ffffff !important;
    }
    
    /* Write content */
    .stWrite {
        color: #ffffff !important;
    }
    
    /* Container backgrounds */
    .element-container {
        background-color: transparent !important;
    }
    
    /* Block container */
    .block-container {
        background-color: #0e1117 !important;
        color: #ffffff !important;
    }
    
    /* Ensure all divs have proper text color */
    div {
        color: #ffffff !important;
    }
    
    /* Ensure all spans have proper text color */
    span {
        color: #ffffff !important;
    }
    
    /* Ensure all paragraphs have proper text color */
    p {
        color: #ffffff !important;
    }
    
    /* Labels */
    label {
        color: #ffffff !important;
    }
    
    /* Links */
    a {
        color: #4fc3f7 !important;
    }
    
    a:hover {
        color: #29b6f6 !important;
    }
    
    /* Tooltip */
    .stTooltipIcon {
        color: #4fc3f7 !important;
    }
    
    /* Popover */
    .stPopover {
        background-color: #1e1e1e !important;
        border: 1px solid #404040 !important;
        color: #ffffff !important;
    }
    
    /* Chat elements (if any) */
    .stChatMessage {
        background-color: #1e1e1e !important;
        border: 1px solid #404040 !important;
        color: #ffffff !important;
    }
    
    /* Plotly specific overrides */
    .plotly {
        background-color: #0e1117 !important;
    }
    
    .plotly .bg {
        fill: #0e1117 !important;
    }
    
    /* Override any matplotlib/seaborn plots */
    .matplotlib {
        background-color: #0e1117 !important;
    }
    
    /* Status indicators */
    .stStatus {
        background-color: #1e1e1e !important;
        border: 1px solid #404040 !important;
        color: #ffffff !important;
    }
    
    /* Ensure sidebar elements are properly styled */
    .css-1d391kg * {
        color: #ffffff !important;
    }
    
    /* Footer */
    .stApp > footer {
        background-color: #0e1117 !important;
        color: #ffffff !important;
    }
    
    /* Any remaining white backgrounds */
    [style*="background-color: white"], 
    [style*="background-color: #ffffff"],
    [style*="background-color: #fff"] {
        background-color: #1e1e1e !important;
    }
    
    /* Any remaining black text */
    [style*="color: black"],
    [style*="color: #000000"],
    [style*="color: #000"] {
        color: #ffffff !important;
    }
    
    /* AGGRESSIVE SIDEBAR FIXES */
    .css-1d391kg, 
    .css-1aumxhk,
    .css-17eq0hr,
    .css-1lcbmhc,
    .css-1y4p8pa,
    .css-12oz5g7,
    .css-1v3fvcr {
        background-color: #262730 !important;
    }
    
    /* Sidebar content wrapper */
    section[data-testid="stSidebar"] {
        background-color: #262730 !important;
    }
    
    section[data-testid="stSidebar"] > div {
        background-color: #262730 !important;
    }
    
    section[data-testid="stSidebar"] * {
        background-color: transparent !important;
        color: #ffffff !important;
    }
    
    /* AGGRESSIVE PLOT BACKGROUND FIXES */
    .js-plotly-plot,
    .plotly-graph-div,
    .svg-container,
    .plot-container {
        background-color: #0e1117 !important;
    }
    
    /* Plotly modebar */
    .modebar {
        background-color: #1e1e1e !important;
    }
    
    .modebar-btn {
        background-color: #1e1e1e !important;
        color: #ffffff !important;
    }
    
    /* Force plotly chart backgrounds */
    .js-plotly-plot .plotly .main-svg {
        background-color: #0e1117 !important;
    }
    
    /* AGGRESSIVE MAIN CONTENT FIXES */
    .main,
    .main > div,
    .block-container,
    .element-container,
    .stApp > div,
    .css-18e3th9,
    .css-1d391kg,
    .css-12oz5g7 {
        background-color: #0e1117 !important;
    }
    
    /* Header area */
    header[data-testid="stHeader"] {
        background-color: #0e1117 !important;
    }
    
    /* Toolbar */
    .css-14xtw13 {
        background-color: #0e1117 !important;
    }
    
    /* AGGRESSIVE TAB FIXES */
    .stTabs,
    .stTabs > div,
    .stTabs [role="tablist"],
    .stTabs [role="tab"],
    .stTabs [role="tabpanel"] {
        background-color: #0e1117 !important;
    }
    
    /* AGGRESSIVE METRIC FIXES */
    [data-testid="metric-container"],
    [data-testid="metric-container"] > div,
    .metric-container {
        background-color: #1e1e1e !important;
        border: 1px solid #404040 !important;
        border-radius: 0.5rem !important;
    }
    
    /* FORCE ALL BACKGROUNDS TO DARK */
    body,
    html,
    #root,
    .stApp,
    .main,
    .block-container,
    .element-container,
    .css-1d391kg,
    .css-18e3th9,
    .css-12oz5g7,
    .css-1aumxhk,
    .css-17eq0hr,
    .css-1lcbmhc,
    .css-1y4p8pa,
    .css-1v3fvcr,
    .css-14xtw13 {
        background: #0e1117 !important;
        background-color: #0e1117 !important;
    }
    
    /* FORCE SIDEBAR BACKGROUNDS */
    section[data-testid="stSidebar"],
    section[data-testid="stSidebar"] > div,
    section[data-testid="stSidebar"] * {
        background: #262730 !important;
        background-color: #262730 !important;
    }
    
    /* Override any SVG backgrounds in plots */
    svg {
        background-color: transparent !important;
    }
    
    /* Plotly paper background */
    .bg {
        fill: #0e1117 !important;
    }
    
    /* Chart paper */
    .paper {
        fill: #0e1117 !important;
    }
    
    /* FORCE ALL TEXT TO WHITE */
    body *,
    .stApp *,
    .main *,
    section[data-testid="stSidebar"] * {
        color: #ffffff !important;
    }
    
    /* Exception for buttons with dark backgrounds */
    .stButton > button * {
        color: #000000 !important;
    }
    
    /* PLOTLY SPECIFIC OVERRIDES */
    .plotly .modebar {
        background: rgba(30, 30, 30, 0.8) !important;
    }
    
    .plotly .modebar-btn path {
        fill: #ffffff !important;
    }
    
    /* Override any remaining white/light elements */
    [style*="background: white"],
    [style*="background: #fff"],
    [style*="background: #ffffff"],
    [style*="background-color: white"],
    [style*="background-color: #fff"],
    [style*="background-color: #ffffff"] {
        background: #1e1e1e !important;
        background-color: #1e1e1e !important;
    }
    
    /* Streamlit specific overrides */
    .css-1outpf7,
    .css-16huue1,
    .css-1inwz65,
    .css-12w0qpk {
        background-color: #0e1117 !important;
    }
    
    /* Column divs */
    .css-ocqkz7,
    .css-1r6slb0 {
        background-color: transparent !important;
    }
    
    /* Widget containers */
    .css-1cpxqw2,
    .css-16idsys {
        background-color: #1e1e1e !important;
        border: 1px solid #404040 !important;
        border-radius: 0.5rem !important;
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
        background-color: #1e1e1e !important;
        border-radius: 12px !important;
        padding: 4px !important;
        gap: 4px !important;
        border: 1px solid #404040 !important;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3) !important;
    }
    
    /* Individual tab buttons */
    div[data-testid="stTabs"] button[role="tab"] {
        background: linear-gradient(135deg, #404040 0%, #505050 100%) !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 8px 16px !important;
        color: #ffffff !important;
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
        background: linear-gradient(135deg, #505050 0%, #606060 100%) !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 2px 8px rgba(102, 126, 234, 0.2) !important;
    }
    
    /* Active/selected tab */
    div[data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: #ffffff !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4) !important;
        z-index: 2 !important;
        position: relative !important;
    }
    
    /* Active tab hover */
    div[data-testid="stTabs"] button[role="tab"][aria-selected="true"]:hover {
        background: linear-gradient(135deg, #764ba2 0%, #667eea 100%) !important;
        box-shadow: 0 6px 16px rgba(102, 126, 234, 0.5) !important;
    }
    
    /* Tab focus state */
    div[data-testid="stTabs"] button[role="tab"]:focus {
        outline: none !important;
        box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.3) !important;
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
        background-color: #1e1e1e !important;
        border: 1px solid #404040 !important;
        border-radius: 0.5rem !important;
        padding: 1rem !important;
        font-family: 'Courier New', monospace !important;
        font-size: 14px !important;
        line-height: 1.4 !important;
        overflow-y: auto !important;
        max-height: 500px !important;
        position: relative !important;
    }
    
    .constitution-panel h4 {
        color: #4fc3f7 !important;
        margin-bottom: 1rem !important;
        font-size: 16px !important;
        font-weight: 600 !important;
        border-bottom: 1px solid #404040 !important;
        padding-bottom: 0.5rem !important;
    }
    
    .constitution-panel .version-info {
        color: #b0b0b0 !important;
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
        color: #ffffff !important;
        background-color: transparent !important;
    }
    
    .diff-added {
        color: #ffffff !important;
        background-color: rgba(40, 167, 69, 0.3) !important;
        border-left: 3px solid #28a745 !important;
        padding-left: 8px !important;
    }
    
    .diff-removed {
        color: #ffffff !important;
        background-color: rgba(220, 53, 69, 0.3) !important;
        border-left: 3px solid #dc3545 !important;
        padding-left: 8px !important;
    }
    
    .diff-controls {
        background-color: #2d2d2d !important;
        border: 1px solid #404040 !important;
        border-radius: 0.5rem !important;
        padding: 1rem !important;
        margin-bottom: 1rem !important;
    }
    
    .diff-controls h4 {
        color: #4fc3f7 !important;
        margin-bottom: 1rem !important;
    }
    
    .slider-container {
        display: flex !important;
        align-items: center !important;
        gap: 1rem !important;
        margin: 0.5rem 0 !important;
    }
    
    .slider-label {
        color: #ffffff !important;
        font-weight: 600 !important;
        min-width: 100px !important;
    }
    
    .version-indicator {
        background-color: #404040 !important;
        border: 1px solid #505050 !important;
        border-radius: 4px !important;
        padding: 0.25rem 0.5rem !important;
        color: #ffffff !important;
        font-family: monospace !important;
        font-size: 12px !important;
    }
</style>
""", unsafe_allow_html=True)

# Initialize contest engine (singleton)
@st.cache_resource
def get_contest_engine():
    return ContestEngine.get_instance()

def reset_and_start_game():
    """Reset everything and start a fresh game."""
    engine = get_contest_engine()
    
    try:
        # Reset everything
        engine.state.is_active = False
        engine.state.start_time = None
        engine.state.current_problem_index = 0
        engine.state.participants = []
        
        # Clear developers and submissions
        engine.developers = {}
        engine.submissions = {}
        
        # Reset bank balances
        engine.bank._balances = {}
        engine.bank._transaction_history = []
        
        # Reset principle evaluator history
        engine.principle_evaluator.evaluation_history = []
        
        # Create fresh AI players
        alice = Phi4Developer("Alice")
        bob = Phi4Developer("Bob")
        
        # Register them
        engine.register_developer(alice)
        engine.register_developer(bob)
        
        # Start the contest
        engine.run_full_contest()
        
        return True, "Game completed successfully!"
    except Exception as e:
        return False, f"Error: {str(e)}"

def display_leaderboard():
    """Display the current leaderboard."""
    engine = get_contest_engine()
    leaderboard = engine.bank.query_leaderboard()
    transactions = engine.bank.query_transaction_history()
    
    # Debug information
    st.write(f"🔍 Debug: Found {len(leaderboard)} leaderboard entries, {len(transactions)} transactions")
    
    if leaderboard:
        # Filter out PrincipleEvaluator to show only players
        player_leaderboard = [entry for entry in leaderboard if entry['name'] != 'PrincipleEvaluator']
        
        if player_leaderboard and transactions:
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
            if player_leaderboard:
                df = pd.DataFrame(player_leaderboard)
                fig = px.bar(df, x="name", y="balance", title="💰 Current Player Balances")
                st.plotly_chart(fig, use_container_width=True)
        
        # Display as table
        if player_leaderboard:
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

def display_contest_status():
    """Display current contest status."""
    engine = get_contest_engine()
    status = engine.get_contest_status()
    
    # Debug info
    st.sidebar.write(f"🔍 **Debug Info:**")
    st.sidebar.write(f"Contest active: {status['is_active']}")
    st.sidebar.write(f"Problem: {status['current_problem_index'] + 1}/{status['total_problems']}")
    st.sidebar.write(f"Participants: {len(status['participants'])}")
    st.sidebar.write(f"Last update: {datetime.now().strftime('%H:%M:%S')}")
    
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

def display_principle_evaluator_output():
    """Display Principle Evaluator's recent evaluations and decisions."""
    engine = get_contest_engine()
    evaluations = engine.principle_evaluator.evaluation_history
    
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

def display_constitution():
    """Display current constitution and allow updates with side-by-side diff comparison."""
    engine = get_contest_engine()
    constitution_text = engine.constitution.query()
    history = engine.constitution.history
    
    st.subheader("📜 Contest Constitution")
    
    # Display current constitution
    st.markdown("""
    <div class="metric-card">
        <h4>Current Rules</h4>
        <pre>{}</pre>
    </div>
    """.format(constitution_text), unsafe_allow_html=True)
    
    # Constitution update form (for Principle Evaluator)
    with st.expander("🔧 Update Constitution (Principle Evaluator Only)"):
        new_constitution = st.text_area(
            "New Constitution Text",
            value=constitution_text,
            height=200
        )
        
        if st.button("Update Constitution"):
            try:
                engine.constitution.update(new_constitution, "PrincipleEvaluator")
                st.success("Constitution updated successfully!")
                st.rerun()
            except Exception as e:
                st.error(f"Failed to update constitution: {e}")
    
    # Constitution change comparison
    if history and len(history) >= 1:
        st.markdown("---")
        st.subheader("📊 Constitution Changes Comparison")
        
        # Create versions list (current + history)
        versions = []
        
        # Add current version
        versions.append({
            'timestamp': 'Current',
            'text': constitution_text,
            'updated_by': 'Current State',
            'version_num': len(history) + 1
        })
        
        # Add historical versions (newest first)
        for i, change in enumerate(reversed(history)):
            versions.append({
                'timestamp': change['timestamp'],
                'text': change['new_text'],
                'updated_by': change['updated_by'],
                'version_num': len(history) - i
            })
        
        # Comparison controls
        st.markdown("""
        <div class="diff-controls">
            <h4>🔍 Version Comparison</h4>
        </div>
        """, unsafe_allow_html=True)
        
        # Version selector
        max_version = len(versions)
        if max_version >= 2:
            col1, col2, col3 = st.columns([1, 2, 1])
            
            with col2:
                comparison_start = st.slider(
                    "Compare versions:",
                    min_value=1,
                    max_value=max_version - 1,
                    value=max_version - 1,
                    help=f"Comparing version {max_version - 1} → {max_version}"
                )
            
            # Get the two versions to compare
            left_version = versions[max_version - comparison_start]  # Earlier version
            right_version = versions[max_version - comparison_start - 1]  # Later version
            
            # Display version info
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"""
                <div class="version-indicator">
                    Version {left_version['version_num']} | {left_version['timestamp']} | {left_version['updated_by']}
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                <div class="version-indicator">
                    Version {right_version['version_num']} | {right_version['timestamp']} | {right_version['updated_by']}
                </div>
                """, unsafe_allow_html=True)
            
            # Generate diff
            left_lines = left_version['text'].splitlines()
            right_lines = right_version['text'].splitlines()
            
            diff = list(difflib.unified_diff(left_lines, right_lines, lineterm=''))
            
            # Create side-by-side comparison
            st.markdown('<div class="constitution-diff-container">', unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"""
                <div class="constitution-panel">
                    <h4>📄 Version {left_version['version_num']} (Before)</h4>
                    <div class="version-info">{left_version['timestamp']} by {left_version['updated_by']}</div>
                """, unsafe_allow_html=True)
                
                # Process lines for left panel
                left_content = ""
                for line in left_lines:
                    # Check if this line was removed in the diff
                    line_removed = any(d.startswith('-') and d[1:].strip() == line.strip() for d in diff)
                    
                    if line_removed:
                        left_content += f'<div class="diff-line diff-removed">{line}</div>'
                    else:
                        left_content += f'<div class="diff-line diff-unchanged">{line}</div>'
                
                st.markdown(left_content + "</div>", unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                <div class="constitution-panel">
                    <h4>📄 Version {right_version['version_num']} (After)</h4>
                    <div class="version-info">{right_version['timestamp']} by {right_version['updated_by']}</div>
                """, unsafe_allow_html=True)
                
                # Process lines for right panel
                right_content = ""
                for line in right_lines:
                    # Check if this line was added in the diff
                    line_added = any(d.startswith('+') and d[1:].strip() == line.strip() for d in diff)
                    
                    if line_added:
                        right_content += f'<div class="diff-line diff-added">{line}</div>'
                    else:
                        right_content += f'<div class="diff-line diff-unchanged">{line}</div>'
                
                st.markdown(right_content + "</div>", unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Show diff summary
            added_lines = len([d for d in diff if d.startswith('+')])
            removed_lines = len([d for d in diff if d.startswith('-')])
            
            if added_lines > 0 or removed_lines > 0:
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Lines Added", added_lines, delta=added_lines if added_lines > 0 else None)
                with col2:
                    st.metric("Lines Removed", removed_lines, delta=-removed_lines if removed_lines > 0 else None)
                with col3:
                    net_change = added_lines - removed_lines
                    st.metric("Net Change", f"+{net_change}" if net_change >= 0 else str(net_change))
        else:
            st.info("Need at least 2 versions to compare. Update the constitution to see comparisons!")
    
    # Constitution history (collapsed by default)
    if history:
        with st.expander("📚 Full Constitution History"):
            for i, change in enumerate(reversed(history)):
                version_num = len(history) - i + 1
                st.markdown(f"**Version {version_num}** - {change['timestamp']} - Updated by {change['updated_by']}")
                st.text("Previous text:")
                st.code(change['old_text'])
                st.text("New text:")
                st.code(change['new_text'])
                st.markdown("---")

def display_bank_transactions():
    """Display bank transaction history."""
    engine = get_contest_engine()
    transactions = engine.bank.query_transaction_history()
    
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
    
    # Custom styled start game button with onclick handler
    button_clicked = st.sidebar.button("🎭 Start Game", type="primary", key="start_game_main")
    
    # Apply custom styling to the actual Streamlit button
    st.sidebar.markdown("""
    <style>
    /* Style the actual Streamlit button */
    div[data-testid="stButton"] button[kind="primary"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 12px 24px !important;
        color: white !important;
        font-size: 16px !important;
        font-weight: 600 !important;
        cursor: pointer !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3) !important;
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
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4) !important;
        background: linear-gradient(135deg, #764ba2 0%, #667eea 100%) !important;
        outline: none !important;
        user-select: none !important;
    }
    
    div[data-testid="stButton"] button[kind="primary"]:active {
        transform: translateY(0) !important;
        box-shadow: 0 2px 10px rgba(102, 126, 234, 0.3) !important;
        outline: none !important;
        user-select: none !important;
    }
    
    div[data-testid="stButton"] button[kind="primary"]:focus {
        outline: none !important;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3) !important;
        user-select: none !important;
    }
    
    div[data-testid="stButton"] button[kind="primary"]:focus:not(:focus-visible) {
        outline: none !important;
    }
    
    div[data-testid="stButton"] button[kind="primary"]:focus-visible {
        outline: none !important;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3) !important;
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
                success, message = reset_and_start_game()
        
        if success:
            st.sidebar.success("Game completed! Check the results below.")
        else:
            st.sidebar.error(f"Failed to start game: {message}")

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
        display_contest_status()
        
        st.markdown("---")
        
        # Leaderboard
        display_leaderboard()
        
        st.markdown("---")
        
        # Principle Evaluator Output
        display_principle_evaluator_output()
    
    with tab2:
        display_principle_evaluator_output()
    
    with tab3:
        display_constitution()
    
    with tab4:
        display_bank_transactions()
    
    # Auto-refresh
    if auto_refresh:
        time.sleep(2)  # Faster refresh for better real-time feel
        st.rerun()

if __name__ == "__main__":
    main() 