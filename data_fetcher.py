from espn_api.baseball import League
import pandas as pd
from espn_config import LEAGUE_ID, YEAR, ESPN_S2, SWID

def get_league():
    return League(league_id=LEAGUE_ID, year=YEAR, espn_s2=ESPN_S2, swid=SWID)

def get_standings(league):
    rows = []
    for team in league.teams:
        rows.append({
            "Team": team.team_name,
            "Wins": team.wins,
            "Losses": team.losses,
            "Ties": team.ties,
            "Win %": round(team.wins / max(team.wins + team.losses + team.ties, 1), 3),
            "Standing": team.standing,
        })
    return pd.DataFrame(rows).sort_values("Standing")

def get_hitting_stats(league):
    stat_map = {
        "0": "AB", "1": "H", "2": "2B", "3": "3B", "4": "HR",
        "5": "RBI", "6": "R", "12": "BB", "23": "SB", "17": "AVG",
        "19": "OBP", "20": "SLG", "21": "OPS",
    }
    rows = []
    for team in league.teams:
        row = {"Team": team.team_name}
        for player in team.roster:
            if hasattr(player, "stats") and player.stats:
                stats = player.stats.get(YEAR, {}).get("total", {})
                for key, name in stat_map.items():
                    row[name] = row.get(name, 0) + (stats.get(key, 0) or 0)
        rows.append(row)
    return pd.DataFrame(rows).fillna(0)

def get_pitching_stats(league):
    stat_map = {
        "34": "IP", "48": "K", "37": "W", "39": "SV",
        "41": "ERA", "42": "WHIP", "45": "QS",
    }
    rows = []
    for team in league.teams:
        row = {"Team": team.team_name}
        for player in team.roster:
            if hasattr(player, "stats") and player.stats:
                stats = player.stats.get(YEAR, {}).get("total", {})
                for key, name in stat_map.items():
                    row[name] = row.get(name, 0) + (stats.get(key, 0) or 0)
        rows.append(row)
    return pd.DataFrame(rows).fillna(0)

def get_matchup_results(league):
    rows = []
    for week in range(1, league.current_week):
        try:
            box_scores = league.box_scores(week)
            for match in box_scores:
                if match.home_team and match.away_team:
                    rows.append({
                        "Week": week,
                        "Home Team": match.home_team.team_name,
                        "Home Score": round(match.home_score, 2),
                        "Away Team": match.away_team.team_name,
                        "Away Score": round(match.away_score, 2),
                        "Winner": match.home_team.team_name if match.home_score > match.away_score
                                  else match.away_team.team_name if match.away_score > match.home_score
                                  else "Tie",
                    })
        except Exception:
            pass
    return pd.DataFrame(rows)

def get_strength_of_schedule(league):
    SCORING_STATS = ['HR', 'RBI', 'R', 'SB', 'OBP', 'K', 'SV', 'QS']
    RATE_STATS = ['ERA', 'WHIP']  # lower is better, average differently
    ALL_STATS = SCORING_STATS + RATE_STATS

    # Track what each team faced from opponents
    opponent_stats = {t.team_name: {s: [] for s in ALL_STATS} for t in league.teams}
    opponent_wins = {t.team_name: [] for t in league.teams}

    for week in range(1, league.current_week):
        try:
            box_scores = league.box_scores(week)
            for match in box_scores:
                if not match.home_team or not match.away_team:
                    continue
                h = match.home_team.team_name
                a = match.away_team.team_name

                # Each team "faced" the other's stats
                for stat in ALL_STATS:
                    h_val = match.home_stats.get(stat, {}).get('value', 0) or 0
                    a_val = match.away_stats.get(stat, {}).get('value', 0) or 0
                    if isinstance(h_val, str): h_val = 0
                    if isinstance(a_val, str): a_val = 0
                    opponent_stats[a][stat].append(h_val)  # away faced home's stats
                    opponent_stats[h][stat].append(a_val)  # home faced away's stats

                # Track opponent win %
                h_winpct = match.home_team.wins / max(match.home_team.wins + match.home_team.losses + match.home_team.ties, 1)
                a_winpct = match.away_team.wins / max(match.away_team.wins + match.away_team.losses + match.away_team.ties, 1)
                opponent_wins[h].append(a_winpct)
                opponent_wins[a].append(h_winpct)
        except Exception:
            pass

    rows = []
    for team in league.teams:
        name = team.team_name
        opps = opponent_stats[name]
        row = {"Team": name}

        for stat in SCORING_STATS:
            vals = [v for v in opps[stat] if v != 0]
            row[f"{stat} Against (Avg)"] = round(sum(vals) / len(vals), 2) if vals else 0

        for stat in RATE_STATS:
            vals = [v for v in opps[stat] if v != 0]
            row[f"{stat} Against (Avg)"] = round(sum(vals) / len(vals), 3) if vals else 0

        wins_list = opponent_wins[name]
        row["SoS (Avg Opp Win%)"] = round(sum(wins_list) / len(wins_list), 3) if wins_list else 0
        row["Own Win%"] = round(team.wins / max(team.wins + team.losses + team.ties, 1), 3)
        row["Wins"] = team.wins
        row["Losses"] = team.losses
        rows.append(row)

    return pd.DataFrame(rows).sort_values("SoS (Avg Opp Win%)", ascending=False)
def get_weekly_scores(league):
    rows = []
    for week in range(1, league.current_week):
        try:
            box_scores = league.box_scores(week)
            for match in box_scores:
                for side, opp in [(match.home_team, match.away_team), (match.away_team, match.home_team)]:
                    if side and opp:
                        score = match.home_score if side == match.home_team else match.away_score
                        rows.append({"Week": week, "Team": side.team_name, "Score": round(score, 2)})
        except Exception:
            pass
    return pd.DataFrame(rows)

def get_roster_stats(league):
    """Return player stats for all teams."""
    rows = []
    for team in league.teams:
        for player in team.roster:
            proj = player.stats.get(0, {}).get('projected_breakdown', {})
            rows.append({
                "Team": team.team_name,
                "Player": player.name,
                "Position": player.position,
                "Pro Team": player.proTeam,
                "Status": player.injuryStatus,
                "% Owned": round(player.percent_owned, 1),
                "AB": proj.get('AB', 0),
                "AVG": proj.get('AVG', 0),
                "HR": proj.get('HR', 0),
                "RBI": proj.get('RBI', 0),
                "R": proj.get('R', 0),
                "SB": proj.get('SB', 0),
                "OBP": proj.get('OBP', 0),
                "SLG": proj.get('SLG', 0),
                "OPS": proj.get('OPS', 0),
                "K (pitcher)": proj.get('K', 0),
                "W": proj.get('W', 0),
                "SV": proj.get('SV', 0),
                "ERA": proj.get('ERA', 0),
                "WHIP": proj.get('WHIP', 0),
                "QS": proj.get('QS', 0),
            })
    return pd.DataFrame(rows).fillna(0)
