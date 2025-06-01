import streamlit as st
import pandas as pd
import plotly.express as px
import time
from datetime import datetime
import sys
import os
import difflib
import yaml

# Add backend to path so we can import directly
sys.path.append('backend')
from contest_engine import ContestEngine
from agents.developer import Phi4Developer

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
        color: #ffffff;
    }
    
    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #262730;
    }
    
    /* Custom component cards */
    .metric-card {
        background-color: #2d2d2d;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #4fc3f7;
        margin-bottom: 1rem;
        color: #ffffff;
    }
    
    .metric-card h4 {
        color: #4fc3f7;
        margin-bottom: 0.5rem;
    }
    
    .metric-card h2 {
        margin: 0;
        color: #ffffff;
    }
    
    .problem-card {
        background-color: #2d2d2d;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #ffb74d;
        border: 1px solid #404040;
        color: #ffffff;
        margin-bottom: 1rem;
    }
    
    .problem-card h4 {
        color: #ffb74d;
        margin-bottom: 0.5rem;
    }
    
    .problem-card p {
        color: #ffffff;
        margin: 0.5rem 0;
    }
    
    .evaluation-log {
        background-color: #2d2d2d;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #404040;
        font-family: monospace;
        font-size: 0.9rem;
        max-height: 400px;
        overflow-y: auto;
        color: #ffffff;
        margin-bottom: 1rem;
    }
    
    .evaluation-log h5 {
        color: #4fc3f7;
        margin-bottom: 0.5rem;
    }
    
    .evaluation-log p {
        color: #ffffff;
        margin: 0.25rem 0;
    }
    
    /* Tab styling */
    div[data-testid="stTabs"] [role="tablist"] {
        background-color: #2d2d2d;
        border-radius: 8px;
        padding: 4px;
    }
    
    div[data-testid="stTabs"] button[role="tab"] {
        background: #404040;
        color: #ffffff;
        border: none;
        border-radius: 4px;
        padding: 8px 16px;
        margin: 0 2px;
    }
    
    div[data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
        background: #667eea;
        color: #ffffff;
    }
    
    /* Constitution diff styling */
    .constitution-panel {
        background-color: #2d2d2d;
        border: 1px solid #404040;
        border-radius: 0.5rem;
        padding: 1rem;
        font-family: 'Courier New', monospace;
        font-size: 14px;
        line-height: 1.4;
        overflow-y: auto;
        max-height: 500px;
        color: #ffffff;
    }
    
    .constitution-panel h4 {
        color: #4fc3f7;
        margin-bottom: 1rem;
        font-size: 16px;
        font-weight: 600;
        border-bottom: 1px solid #404040;
        padding-bottom: 0.5rem;
    }
    
    .diff-added {
        color: #ffffff;
        background-color: rgba(40, 167, 69, 0.3);
        border-left: 3px solid #28a745;
        padding-left: 8px;
    }
    
    .diff-removed {
        color: #ffffff;
        background-color: rgba(220, 53, 69, 0.3);
        border-left: 3px solid #dc3545;
        padding-left: 8px;
    }
    
    .diff-controls {
        background-color: #2d2d2d;
        border: 1px solid #404040;
        border-radius: 0.5rem;
        padding: 1rem;
        margin-bottom: 1rem;
        color: #ffffff;
    }
    
    .version-indicator {
        background-color: #404040;
        border: 1px solid #505050;
        border-radius: 4px;
        padding: 0.25rem 0.5rem;
        color: #ffffff;
        font-family: monospace;
        font-size: 12px;
    }
</style>
""", unsafe_allow_html=True)

# Initialize contest engine (singleton)
@st.cache_resource
def get_contest_engine():
    return ContestEngine.get_instance()

def initialize_contest():
    """Initialize contest with fresh players."""
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
        
        alice = Phi4Developer("Alice")
        bob = Phi4Developer("Bob")
        
        # Register them
        engine.register_developer(alice)
        engine.register_developer(bob)
        
        # Start the contest (but don't run it)
        engine.start_contest()
        
        return True, "Contest initialized! Ready to step through problems."
    except Exception as e:
        return False, f"Error: {str(e)}"

def step_contest():
    """Run one contest round."""
    engine = get_contest_engine()
    
    try:
        # Check if contest is active
        if not engine.state.is_active:
            return False, "Contest not started. Click Step to initialize first."
        
        # Check if we have more problems
        if engine.state.current_problem_index >= len(engine.problems):
            return False, "Contest completed! All problems finished."
        
        # Run one round
        engine.run_contest_round()
        
        # Check if that was the last problem
        if engine.state.current_problem_index >= len(engine.problems):
            return True, "Contest completed! Final results available."
        else:
            current_prob = engine.state.current_problem_index + 1
            total_probs = len(engine.problems)
            return True, f"Round completed! Problem {current_prob-1} finished. Ready for problem {current_prob}/{total_probs}."
        
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
        
        if player_leaderboard:
            # Always create balance history - starting with round 0 at $0 for all players
            balance_history = []
            
            # Add starting point for all players at round 0
            for player in [p['name'] for p in player_leaderboard]:
                balance_history.append({
                    'round': 0,
                    'player': player,
                    'balance': 0
                })
            
            if transactions:
                # Build from transaction history - only problem-related transactions
                df_transactions = pd.DataFrame(transactions)
                df_transactions['timestamp'] = pd.to_datetime(df_transactions['timestamp'])
                
                for player in [p['name'] for p in player_leaderboard]:
                    player_txns = df_transactions[df_transactions['actor'] == player].copy()
                    
                    if not player_txns.empty:
                        player_txns = player_txns.sort_values('timestamp')
                        
                        running_balance = 0
                        for idx, (_, txn) in enumerate(player_txns.iterrows()):
                            reason = str(txn['reason'])
                            
                            # Only process transactions related to actual problems/submissions
                            if 'Problem' in reason or 'Submission' in reason or 'evaluation' in reason.lower():
                                running_balance += txn['delta']
                                
                                # Better round extraction logic
                                round_num = 0  # Default
                                
                                # Try multiple patterns to extract round number
                                if 'Problem' in reason:
                                    import re
                                    # Look for "Problem X" patterns
                                    match = re.search(r'Problem (\d+)', reason)
                                    if match:
                                        round_num = int(match.group(1))
                                    else:
                                        # Fallback: use transaction sequence
                                        round_num = idx + 1
                                elif 'Submission' in reason:
                                    # Extract from submission patterns
                                    import re
                                    match = re.search(r'(\d+)', reason)
                                    if match:
                                        round_num = int(match.group(1))
                                    else:
                                        round_num = idx + 1
                                else:
                                    # Use transaction sequence as fallback for evaluation transactions
                                    round_num = idx + 1
                                
                                # Only add if this is a valid problem round (> 0)
                                if round_num > 0:
                                    balance_history.append({
                                        'round': round_num,
                                        'player': player,
                                        'balance': running_balance
                                    })
            
            # Create the line plot
            df_history = pd.DataFrame(balance_history)
            
            fig_line = px.line(
                df_history,
                x='round',
                y='balance',
                color='player',
                title="💰 Player Balance Over Rounds",
                markers=True,
                color_discrete_map={'Alice': '#4fc3f7', 'Bob': '#ff9800'}
            )
            
            fig_line.update_layout(
                plot_bgcolor='#1e1e1e',
                paper_bgcolor='#1e1e1e',
                font=dict(color='white'),
                title_font=dict(color='white', size=16),
                xaxis=dict(
                    title="Round Number",
                    title_font=dict(color='white'),
                    tickfont=dict(color='white'),
                    gridcolor='#404040',
                    linecolor='white'
                ),
                yaxis=dict(
                    title="Balance ($)",
                    title_font=dict(color='white'),
                    tickfont=dict(color='white'),
                    gridcolor='#404040',
                    linecolor='white'
                ),
                height=400,
                hovermode='x unified',
                legend=dict(
                    font=dict(color='white'),
                    bgcolor='rgba(30,30,30,0.8)',
                    bordercolor='white'
                ),
                margin=dict(l=50, r=50, t=50, b=50)
            )
            
            # Update traces for better visibility
            fig_line.update_traces(
                line=dict(width=4),
                marker=dict(size=10, line=dict(color='white', width=2))
            )
            
            st.plotly_chart(fig_line, use_container_width=True)
            
            # Show current balances table
            st.subheader("📊 Current Balances")
            col1, col2 = st.columns(2)
            for i, entry in enumerate(player_leaderboard):
                with col1 if i % 2 == 0 else col2:
                    color = "green" if entry['balance'] >= 0 else "red"
                    st.markdown(f"**{entry['name']}**: <span style='color: {color}'>${entry['balance']:,}</span>", 
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
                # Ensure we have a valid range for the slider
                slider_max = max(1, max_version - 1)
                slider_min = min(1, slider_max - 1) if slider_max > 1 else 1
                
                if slider_max > slider_min:
                    comparison_start = st.slider(
                        "Compare versions:",
                        min_value=slider_min,
                        max_value=slider_max,
                        value=slider_max,
                        help=f"Comparing version {slider_max} → {max_version}"
                    )
                else:
                    # Fallback for edge case
                    comparison_start = 1
            
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

def display_player_personalities():
    """Display loaded player personalities."""
    st.subheader("🎭 Player Personalities")
    
    # Load and display personality files
    player_files = [f for f in os.listdir("players") if f.endswith('.yaml')]
    
    if not player_files:
        st.warning("No player personality files found in 'players' directory.")
        return
    
    for player_file in sorted(player_files):
        player_name = player_file[:-5].title()  # Remove .yaml and capitalize
        
        try:
            with open(f"players/{player_file}", 'r') as f:
                personality = yaml.safe_load(f)
            
            # Extract name from filename if not in YAML
            display_name = player_name
            
            with st.expander(f"🎯 {display_name} - Character Profile"):
                # Show the complete prompt
                if personality.get('prompt'):
                    st.markdown("**Complete Character Profile & Instructions:**")
                    st.markdown(personality['prompt'])
                else:
                    st.warning(f"No prompt found for {display_name}")
        
        except Exception as e:
            st.error(f"Error loading personality for {player_name}: {e}")

def display_player_history():
    """Display detailed history for a selected player."""
    engine = get_contest_engine()
    leaderboard = engine.bank.query_leaderboard()
    
    # First show player personalities
    display_player_personalities()
    
    st.markdown("---")
    st.subheader("📊 Individual Player History")
    
    # Get list of players (excluding PrincipleEvaluator)
    players = [entry['name'] for entry in leaderboard if entry['name'] != 'PrincipleEvaluator']
    
    if not players:
        st.info("No players registered yet. Initialize the contest first!")
        return
    
    # Player selection dropdown
    selected_player = st.selectbox(
        "🎯 Select Player",
        options=players,
        index=0,
        help="Choose a player to view their complete history"
    )
    
    if selected_player:
        st.subheader(f"📊 {selected_player}'s Complete History")
        
        # Get the developer object
        if selected_player not in engine.developers:
            st.error(f"Developer {selected_player} not found in engine.developers")
            return
        
        developer = engine.developers[selected_player]
        
        # Debug information
        st.write(f"🔍 **Debug Info for {selected_player}:**")
        st.write(f"  - Developer object found: {developer is not None}")
        st.write(f"  - Has submission_history: {hasattr(developer, 'submission_history')}")
        if hasattr(developer, 'submission_history'):
            st.write(f"  - Submission history length: {len(developer.submission_history)}")
        st.write(f"  - Has feedback_history: {hasattr(developer, 'feedback_history')}")
        if hasattr(developer, 'feedback_history'):
            st.write(f"  - Feedback history length: {len(developer.feedback_history)}")
        st.write(f"  - Total problems in engine.submissions: {len(engine.submissions)}")
        st.write(f"  - Problems with submissions: {list(engine.submissions.keys())}")
        for prob_id, subs in engine.submissions.items():
            if selected_player in subs:
                st.write(f"    - {prob_id}: Has submission ({len(subs[selected_player])} chars)")
        
        # Collect all player-related events
        events = []
        
        # 1. Get transaction history for this player
        transactions = engine.bank.query_transaction_history()
        player_transactions = [txn for txn in transactions if txn['actor'] == selected_player]
        
        for txn in player_transactions:
            events.append({
                'timestamp': pd.to_datetime(txn['timestamp']),
                'type': 'Transaction',
                'description': f"${txn['delta']:+} - {txn['reason']}",
                'details': {
                    'amount': txn['delta'],
                    'reason': txn['reason'],
                    'balance_after': None  # We'll calculate this
                }
            })
        
        # 2. Get submission history from the developer object (shows full responses)
        if hasattr(developer, 'submission_history'):
            for submission in developer.submission_history:
                submission_timestamp = submission.get('timestamp')
                if not submission_timestamp:
                    submission_timestamp = datetime.now().isoformat()
                
                # Convert string timestamp to datetime if needed
                if isinstance(submission_timestamp, str):
                    submission_timestamp = pd.to_datetime(submission_timestamp)
                
                events.append({
                    'timestamp': submission_timestamp,
                    'type': 'Submission',
                    'description': f"Submitted solution for {submission.get('problem_id', 'Unknown Problem')}",
                    'details': {
                        'problem_id': submission.get('problem_id'),
                        'full_response': submission.get('full_response'),
                        'extracted_code': submission.get('extracted_code'),
                        'submission_time': submission_timestamp
                    }
                })

        # 3. Get feedback history from the developer object
        if hasattr(developer, 'feedback_history'):
            for feedback in developer.feedback_history:
                feedback_timestamp = feedback.get('timestamp')
                if not feedback_timestamp:
                    # If no timestamp in feedback, try to infer from submission time or use current time
                    feedback_timestamp = datetime.now().isoformat()
                
                # Add the feedback event
                events.append({
                    'timestamp': pd.to_datetime(feedback_timestamp),
                    'type': 'Feedback',
                    'description': f"Received feedback for {feedback.get('problem_id', 'Unknown Problem')}",
                    'details': {
                        'problem_id': feedback.get('problem_id'),
                        'reward': feedback.get('reward'),
                        'bank_balance': feedback.get('bank_balance'),
                        'result': feedback.get('result'),
                        'constitution': feedback.get('constitution'),
                        'reasoning_transcript': feedback.get('reasoning_transcript'),
                        'full_feedback': feedback
                    }
                })
                
        # 4. Get any additional submissions from engine.submissions that might not have feedback yet
        for problem_id, problem_submissions in engine.submissions.items():
            if selected_player in problem_submissions:
                # Check if we already have this submission from submission_history
                has_submission_record = any(
                    submission.get('problem_id') == problem_id 
                    for submission in getattr(developer, 'submission_history', [])
                )
                
                if not has_submission_record:
                    # This is a submission without proper history record yet
                    submission_code = problem_submissions[selected_player]
                    submission_time = datetime.now()  # Fallback timestamp
                    
                    events.append({
                        'timestamp': submission_time,
                        'type': 'Submission',
                        'description': f"Submitted solution for {problem_id} (legacy record)",
                        'details': {
                            'problem_id': problem_id,
                            'full_response': submission_code,  # May just be extracted code
                            'extracted_code': submission_code,
                            'submission_time': submission_time
                        }
                    })
        
        # Sort events chronologically
        events.sort(key=lambda x: x['timestamp'])
        
        if not events:
            st.info(f"No history found for {selected_player}. They may not have participated in any rounds yet.")
            return
        
        # Display events in chronological order
        st.markdown(f"**Total Events:** {len(events)}")
        
        # Calculate running balance for transactions
        running_balance = 0
        for event in events:
            if event['type'] == 'Transaction':
                running_balance += event['details']['amount']
                event['details']['balance_after'] = running_balance
        
        # Display timeline
        for i, event in enumerate(events):
            # Create expandable sections for each event
            with st.expander(
                f"**{event['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}** - {event['type']}: {event['description']}",
                expanded=(i < 3)  # Expand first 3 events by default
            ):
                col1, col2 = st.columns([1, 3])
                
                with col1:
                    st.markdown(f"**Type:** {event['type']}")
                    st.markdown(f"**Time:** {event['timestamp'].strftime('%H:%M:%S')}")
                
                with col2:
                    if event['type'] == 'Transaction':
                        details = event['details']
                        color = "green" if details['amount'] >= 0 else "red"
                        st.markdown(f"**Amount:** <span style='color: {color}'>${details['amount']:+}</span>", unsafe_allow_html=True)
                        st.markdown(f"**Reason:** {details['reason']}")
                        st.markdown(f"**Balance After:** ${details['balance_after']:,}")
                    
                    elif event['type'] == 'Submission':
                        details = event['details']
                        st.markdown(f"**Problem:** {details['problem_id']}")
                        
                        # Show the full player response
                        if details['full_response']:
                            st.markdown("**Player's Complete Response:**")
                            st.text(details['full_response'])
                    
                    elif event['type'] == 'Feedback':
                        details = event['details']
                        st.markdown(f"**Problem:** {details['problem_id']}")
                        
                        # Show Principle Evaluator's reasoning transcript
                        reasoning_transcript = details['reasoning_transcript']
                        if reasoning_transcript and reasoning_transcript != 'No reasoning available':
                            st.markdown("**🧠 Principle Evaluator's Reasoning:**")
                            st.markdown(reasoning_transcript)
                        
                        # Show final reward
                        if details['reward'] is not None:
                            color = "green" if details['reward'] >= 0 else "red"
                            st.markdown(f"**💰 Final Reward: <span style='color: {color}'>${details['reward']:+}</span>**", unsafe_allow_html=True)
        
        # Summary statistics
        st.markdown("---")
        st.subheader("📈 Summary Statistics")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            transaction_count = len([e for e in events if e['type'] == 'Transaction'])
            st.metric("Transactions", transaction_count)
        
        with col2:
            submission_count = len([e for e in events if e['type'] == 'Submission'])
            st.metric("Submissions", submission_count)
        
        with col3:
            feedback_count = len([e for e in events if e['type'] == 'Feedback'])
            st.metric("Feedback Received", feedback_count)
        
        with col4:
            current_balance = running_balance
            color = "normal" if current_balance >= 0 else "inverse"
            st.metric("Current Balance", f"${current_balance:,}", delta=None)

def control_panel():
    """Contest control panel."""
    st.sidebar.header("🎮 Contest Controls")
    
    # Get contest status to determine button states
    engine = get_contest_engine()
    status = engine.get_contest_status()
    
    # Determine button states based on contest status
    if not status['is_active']:
        # Not initialized - show initialize button and disabled step button
        initialize_clicked = st.sidebar.button("🎭 Initialize Contest", type="primary", key="initialize_contest")
        st.sidebar.button("▶️ Step (Not Ready)", disabled=True, key="step_disabled")
        
        if initialize_clicked:
            with st.sidebar:
                with st.spinner("Initializing contest..."):
                    success, message = initialize_contest()
            
            if success:
                st.sidebar.success("Contest initialized successfully!")
            else:
                st.sidebar.error(message)
    
    else:
        # Contest is active - show reset button and step button
        reset_clicked = st.sidebar.button("🔄 Reset Contest", type="primary", key="reset_contest")
        
        if reset_clicked:
            with st.sidebar:
                with st.spinner("Resetting contest..."):
                    success, message = initialize_contest()
            
            if success:
                st.sidebar.success("Contest reset successfully!")
            else:
                st.sidebar.error(message)
        
        # Determine step button text and action
        if status['current_problem_index'] >= status['total_problems']:
            # Contest complete
            st.sidebar.button("🏁 Contest Complete", disabled=True, key="step_contest_complete")
        else:
            # Contest active - show step button
            current_prob = status['current_problem_index'] + 1
            total_probs = status['total_problems']
            step_button_text = f"▶️ Step (Problem {current_prob}/{total_probs})"
            
            step_clicked = st.sidebar.button(step_button_text, type="primary", key="step_contest_main")
            
            if step_clicked:
                with st.sidebar:
                    with st.spinner(f"Running problem {current_prob}..."):
                        success, message = step_contest()
                
                if success:
                    st.sidebar.success(message)
                else:
                    st.sidebar.error(message)
    
    # Apply custom styling to all primary buttons
    st.sidebar.markdown("""
    <style>
    /* Style all primary Streamlit buttons - including during global app processing */
    div[data-testid="stButton"] button[kind="primary"],
    div[data-testid="stButton"] button[kind="primary"]:enabled,
    div[data-testid="stButton"] button[kind="primary"]:disabled,
    div[data-testid="stButton"] button[kind="primary"][data-clicked="true"],
    div[data-testid="stButton"] button[kind="primary"]:active,
    div[data-testid="stButton"] button[kind="primary"]:focus,
    .stApp[data-test-script-state="running"] div[data-testid="stButton"] button[kind="primary"],
    .stApp[data-test-script-state="running"] div[data-testid="stButton"] button[kind="primary"]:enabled,
    .stApp[data-test-script-state="running"] div[data-testid="stButton"] button[kind="primary"]:disabled,
    body[data-test-script-state="running"] div[data-testid="stButton"] button[kind="primary"],
    [data-testid="stApp"][data-test-script-state="running"] div[data-testid="stButton"] button[kind="primary"] {
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
    
    /* Override any Streamlit processing states */
    div[data-testid="stButton"] button[kind="primary"].stButton > button,
    div[data-testid="stButton"] button[kind="primary"] > div,
    div[data-testid="stButton"] button[kind="primary"] span {
        background: transparent !important;
        color: white !important;
    }
    
    /* Force override any green processing states and global app processing */
    div[data-testid="stButton"] button[kind="primary"][style*="background"],
    div[data-testid="stButton"] button[kind="primary"][style*="green"],
    div[data-testid="stButton"] button[kind="primary"].st-emotion-cache-*,
    .stApp[data-test-script-state="running"] div[data-testid="stButton"] button[kind="primary"][style*="background"],
    .stApp[data-test-script-state="running"] div[data-testid="stButton"] button[kind="primary"][style*="green"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
    }
    
    /* Override global app processing styles */
    .stApp[data-test-script-state="running"] div[data-testid="stButton"] button[kind="primary"],
    body[data-test-script-state="running"] div[data-testid="stButton"] button[kind="primary"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        opacity: 1 !important;
    }
    
    div[data-testid="stButton"] button[kind="primary"]:hover,
    .stApp[data-test-script-state="running"] div[data-testid="stButton"] button[kind="primary"]:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4) !important;
        background: linear-gradient(135deg, #764ba2 0%, #667eea 100%) !important;
        outline: none !important;
        user-select: none !important;
    }
    
    div[data-testid="stButton"] button[kind="primary"]:active,
    div[data-testid="stButton"] button[kind="primary"][data-clicked="true"],
    .stApp[data-test-script-state="running"] div[data-testid="stButton"] button[kind="primary"]:active {
        transform: translateY(0) !important;
        box-shadow: 0 2px 10px rgba(102, 126, 234, 0.3) !important;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        outline: none !important;
        user-select: none !important;
    }
    
    div[data-testid="stButton"] button[kind="primary"]:focus,
    .stApp[data-test-script-state="running"] div[data-testid="stButton"] button[kind="primary"]:focus {
        outline: none !important;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3) !important;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        user-select: none !important;
    }
    
    div[data-testid="stButton"] button[kind="primary"]:focus:not(:focus-visible) {
        outline: none !important;
    }
    
    div[data-testid="stButton"] button[kind="primary"]:focus-visible,
    .stApp[data-test-script-state="running"] div[data-testid="stButton"] button[kind="primary"]:focus-visible {
        outline: none !important;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3) !important;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
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
    
    /* Override any dynamically generated Streamlit styles */
    div[data-testid="stButton"] button[kind="primary"][class*="st-"],
    .stApp[data-test-script-state="running"] div[data-testid="stButton"] button[kind="primary"][class*="st-"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
    }
    </style>
    """, unsafe_allow_html=True)

def main():
    """Main Streamlit application."""
    st.title("🎭 A Game of LLMs")
    st.markdown("Real-time monitoring of AI agents competing under evolving constitutional rules")
    
    # Control panel in sidebar
    control_panel()
    
    # Auto-refresh toggle
    auto_refresh = st.sidebar.checkbox("🔄 Auto-refresh (5s)", value=True)
    
    # Main dashboard
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Overview", "🤖 Principle Evaluator", "📜 Constitution", "💳 Transactions", "👥 Players"])
    
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
    
    with tab5:
        display_player_history()
    
    # Auto-refresh
    if auto_refresh:
        time.sleep(2)  # Faster refresh for better real-time feel
        st.rerun()

if __name__ == "__main__":
    main() 