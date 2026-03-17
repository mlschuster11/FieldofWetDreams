cat > ~/Downloads/dashboard.py << 'EOF'
import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="ESPN Fantasy Baseball Dashboard", page_icon="⚾", layout="wide")

from espn_config import PASSWORD

def check_password():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if not st.session_state.authenticated:
        st.title("⚾ ESPN Fantasy Baseball Dashboard")
        pwd = st.text_input("Enter league password:", type="password")
        if st.button("Login"):
            if pwd == PASSWORD:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Incorrect password")
        st.stop()

check_password()

from data_fetcher import (
    get_league, get_standings, get_hitting_stats, get_pitching_stats,
    get_matchup_results, get_strength_of_schedule, get_weekly_scores,
)

st.title("⚾ ESPN Fantasy Baseball Dashboard")

@st.cache_resource(ttl=3600, show_spinner="Fetching league data from ESPN...")
def load_all_data():
    league = get_league()
    return {
        "league": league,
        "standings": get_standings(league),
        "hitting": get_hitting_stats(league),
        "pitching": get_pitching_stats(league),
        "matchups": get_matchup_results(league),
        "sos": get_strength_of_schedule(league),
        "weekly_scores": get_weekly_scores(league),
    }

try:
    data = load_all_data()
except Exception as e:
    st.error(f"❌ Could not connect to ESPN API. Check your credentials in espn_config.py.\n\nError: {e}")
    st.stop()

league = data["league"]
st.success(f"✅ Connected to **{league.settings.name}** — Week {league.current_week - 1} complete")

tabs = st.tabs(["🏆 Standings", "🏏 Hitting", "⚡ Pitching", "🤝 Head-to-Head", "📅 Weekly Scores", "💪 Strength of Schedule"])

with tabs[0]:
    st.subheader("League Standings")
    df = data["standings"]
    st.dataframe(df, use_container_width=True, hide_index=True)
    col1, col2 = st.columns(2)
    with col1:
        fig = px.bar(df, x="Team", y=["Wins", "Losses"], barmode="group", title="Wins vs Losses")
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        fig2 = px.bar(df, x="Team", y="Win %", title="Win % by Team",
                      color="Win %", color_continuous_scale="RdYlGn")
        fig2.update_layout(xaxis_tickangle