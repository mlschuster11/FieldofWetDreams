import streamlit as st
import pandas as pd
import plotly.express as px
import sys
sys.path.insert(0, '/mount/src/fieldofwetdreams')

st.set_page_config(page_title="ESPN Fantasy Baseball Dashboard", page_icon="⚾", layout="wide")

def check_password():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if not st.session_state.authenticated:
        st.title("⚾ ESPN Fantasy Baseball Dashboard")
        pwd = st.text_input("Enter league password:", type="password")
        if st.button("Login"):
            from espn_config import PASSWORD
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
    get_roster_stats, get_projected_totals,
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
	"rosters": get_roster_stats(league),
        "projected": get_projected_totals(league),


    }

try:
    data = load_all_data()
except Exception as e:
    st.error(f"❌ Could not connect to ESPN API. Check your credentials in espn_config.py.\n\nError: {e}")
    st.stop()

league = data["league"]
st.success(f"✅ Connected to **{league.settings.name}** — Week {league.current_week - 1} complete")

tabs = st.tabs(["🏆 Standings", "🏏 Hitting", "⚡ Pitching", "🤝 Head-to-Head", "📅 Weekly Scores", "💪 Strength of Schedule", "👤 Rosters", "📊 Projected Totals"])

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
        fig2.update_layout(xaxis_tickangle=-30)
        st.plotly_chart(fig2, use_container_width=True)

with tabs[1]:
    st.subheader("Team Hitting Statistics")
    df = data["hitting"]
    st.dataframe(df, use_container_width=True, hide_index=True)
    hit_cols = [c for c in ["HR", "RBI", "R", "SB", "AVG", "OPS"] if c in df.columns]
    selected = st.selectbox("Visualize stat:", hit_cols)
    fig = px.bar(df.sort_values(selected, ascending=False), x="Team", y=selected, color=selected, color_continuous_scale="Blues")
    st.plotly_chart(fig, use_container_width=True)

with tabs[2]:
    st.subheader("Team Pitching Statistics")
    df = data["pitching"]
    st.dataframe(df, use_container_width=True, hide_index=True)
    pitch_cols = [c for c in ["ERA", "WHIP", "K", "W", "SV", "QS"] if c in df.columns]
    selected_p = st.selectbox("Visualize stat:", pitch_cols)
    ascending = selected_p in ["ERA", "WHIP"]
    fig = px.bar(df.sort_values(selected_p, ascending=ascending), x="Team", y=selected_p, color=selected_p,
                 color_continuous_scale="RdYlGn_r" if ascending else "RdYlGn")
    st.plotly_chart(fig, use_container_width=True)

with tabs[3]:
    st.subheader("Head-to-Head Matchup Results")
    df = data["matchups"]
    if df.empty:
        st.info("No completed matchups found yet.")
    else:
        weeks = sorted(df["Week"].unique())
        selected_week = st.selectbox("Filter by week:", ["All"] + [str(w) for w in weeks])
        display_df = df if selected_week == "All" else df[df["Week"] == int(selected_week)]
        st.dataframe(display_df, use_container_width=True, hide_index=True)

with tabs[4]:
    st.subheader("Weekly Score Trends")
    df = data["weekly_scores"]
    if df.empty:
        st.info("No weekly score data available yet.")
    else:
        teams_all = sorted(df["Team"].unique())
        selected_teams = st.multiselect("Show teams:", teams_all, default=teams_all)
        fig = px.line(df[df["Team"].isin(selected_teams)], x="Week", y="Score", color="Team", markers=True)
        st.plotly_chart(fig, use_container_width=True)

with tabs[5]:
    st.subheader("Strength of Schedule")
    st.caption("Stats shown are averages of what each team faced from opponents across all matchups.")
    df = data["sos"]
    st.dataframe(df, use_container_width=True, hide_index=True)

    st.subheader("Opponent Stats Faced")
    against_cols = [c for c in df.columns if "Against" in c]
    selected_sos = st.selectbox("Visualize stat faced:", against_cols)
    fig = px.bar(df.sort_values(selected_sos, ascending=False), x="Team", y=selected_sos,
                 title=f"Avg {selected_sos} by Team",
                 color=selected_sos, color_continuous_scale="Reds")
    fig.update_layout(xaxis_tickangle=-30)
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Overall Strength of Schedule")
    fig2 = px.scatter(df, x="SoS (Avg Opp Win%)", y="Own Win%", text="Team",
                      color="Own Win%", color_continuous_scale="RdYlGn")
    fig2.update_traces(textposition="top center")
    st.plotly_chart(fig2, use_container_width=True)
with tabs[6]:
    st.subheader("Rosters & Player Stats (Projected)")
    df = data["rosters"]

    teams_list = ["All"] + sorted(df["Team"].unique())
    selected_team = st.selectbox("Filter by team:", teams_list)
    positions = ["All"] + sorted(df["Position"].unique())
    selected_pos = st.selectbox("Filter by position:", positions)

    filtered = df.copy()
    if selected_team != "All":
        filtered = filtered[filtered["Team"] == selected_team]
    if selected_pos != "All":
        filtered = filtered[filtered["Position"] == selected_pos]

    st.dataframe(filtered, use_container_width=True, hide_index=True)

    st.subheader("Top Players by Stat")
    stat_cols = ["HR", "RBI", "R", "SB", "OPS", "ERA", "WHIP", "K (pitcher)", "SV", "QS"]
    selected_stat = st.selectbox("Rank players by:", stat_cols)
    ascending = selected_stat in ["ERA", "WHIP"]
    top_df = df[df[selected_stat] > 0].sort_values(selected_stat, ascending=ascending).head(20)
    fig = px.bar(top_df, x="Player", y=selected_stat, color="Team",
                 title=f"Top 20 Players by {selected_stat}")
    fig.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig, use_container_width=True)
with tabs[7]:
    st.subheader("Projected Season Totals by Team")
    st.caption("Based on ESPN projected stats for all rostered players.")
    df = data["projected"]
    st.dataframe(df, use_container_width=True, hide_index=True)

    stat_cols = ["HR", "RBI", "R", "SB", "K (pitcher)", "W", "SV", "QS"]
    selected_stat = st.selectbox("Visualize projected stat:", stat_cols, key="proj_stat")
    fig = px.bar(df.sort_values(selected_stat, ascending=False),
                 x="Team", y=selected_stat,
                 title=f"Projected {selected_stat} by Team",
                 color=selected_stat, color_continuous_scale="Blues")
    fig.update_layout(xaxis_tickangle=-30)
    st.plotly_chart(fig, use_container_width=True)
