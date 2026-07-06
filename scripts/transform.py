import pandas as pd
import numpy as np


# =========================================================
# 1. DICTIONARIES & MAPPINGS
# =========================================================

COUNTRY_MAPPING = {
    "West Germany": "Germany",
    "FRG": "Germany",
    "East Germany": "Germany",
    "Soviet Union": "Russia",
    "Zaire": "DR Congo",
    "Yugoslavia": "Serbia",
    "Serbia and Montenegro": "Serbia",
    "Dutch East Indies": "Indonesia",
    "Czechoslovakia": "Czech Republic",
    "IR Iran": "Iran"
}


# =========================================================
# 2. CLEANING & STANDARDIZATION
# =========================================================

def standardize_country_names(df, columns):
    for col in columns:
        if col in df.columns:
            df[col] = df[col].replace(COUNTRY_MAPPING)
    return df


def normalize_strings(df, columns):
    for col in columns:
        if col in df.columns:
            df[col] = df[col].astype(str).str.lower().str.strip()
    return df


def clean_basic(df):
    if df is None:
        return None
    df = df.drop_duplicates()
    df = df.dropna(how="all")
    return df


def parse_dates(df, cols):
    if df is None:
        return None
    for col in cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")
    return df


# =========================================================
# 3. MATCH FEATURES (light only)
# =========================================================
def compute_match_features(df):
    if df is None:
        return None
    if {"home_score", "away_score"}.issubset(df.columns):
        df["goal_diff"] = df["home_score"] - df["away_score"]
        df["result"] = np.where(
            df["home_score"] > df["away_score"], "H",
            np.where(df["home_score"] < df["away_score"], "A", "D")
        )
    return df


# =========================================================
# 4. TEAM STATS (from matches only)
# =========================================================
def compute_team_stats(matches):
    if matches is None or matches.empty:
        return pd.DataFrame()

    home = matches.groupby("home_team").agg({
        "home_score": ["sum", "count"],
        "away_score": "sum"
    })

    away = matches.groupby("away_team").agg({
        "away_score": ["sum", "count"],
        "home_score": "sum"
    })

    home.columns = ["goals_scored_home", "home_games", "goals_conceded_home"]
    away.columns = ["goals_scored_away", "away_games", "goals_conceded_away"]

    df = home.join(away, how="outer").fillna(0)

    df["goals_scored"] = df["goals_scored_home"] + df["goals_scored_away"]
    df["goals_conceded"] = df["goals_conceded_home"] + df["goals_conceded_away"]
    df["games_played"] = df["home_games"] + df["away_games"]
    df["goal_diff"] = df["goals_scored"] - df["goals_conceded"]

    df["goals_per_game"] = np.where(df["games_played"] > 0, df["goals_scored"] / df["games_played"], 0)
    df["conceded_per_game"] = np.where(df["games_played"] > 0, df["goals_conceded"] / df["games_played"], 0)

    return df.reset_index().rename(columns={"home_team": "team"})


# =========================================================
# 5. WIN RATE (Corrected statistical formula)
# =========================================================
def compute_win_rate(matches):
    if matches is None or matches.empty:
        return pd.DataFrame()

    home_wins = matches[matches["home_score"] > matches["away_score"]].groupby("home_team").size()
    home_games = matches.groupby("home_team").size()

    away_wins = matches[matches["away_score"] > matches["home_score"]].groupby("away_team").size()
    away_games = matches.groupby("away_team").size()

    df_wins = pd.DataFrame({"home_wins": home_wins, "away_wins": away_wins}).fillna(0)
    df_games = pd.DataFrame({"home_games": home_games, "away_games": away_games}).fillna(0)

    df = df_wins.join(df_games, how="outer").fillna(0)
    
    df["total_wins"] = df["home_wins"] + df["away_wins"]
    df["total_games"] = df["home_games"] + df["away_games"]
    df["win_rate"] = np.where(df["total_games"] > 0, df["total_wins"] / df["total_games"], 0)

    return df[["win_rate", "total_wins", "total_games"]].reset_index().rename(columns={"index": "team"})


# =========================================================
# 6. TITLES & PHASE PERFORMANCE
# =========================================================
def compute_titles(worldcup):
    if worldcup is None or worldcup.empty or "winner" not in worldcup.columns:
        return pd.DataFrame(columns=["team", "titles"])
    
    titles = worldcup.groupby("winner").size().reset_index(name="titles")
    titles = titles.rename(columns={"winner": "team"})
    return titles


def compute_phase_performance(matches):
    if matches is None or matches.empty or "stage" not in matches.columns:
        return pd.DataFrame()
    
    home_stages = matches.groupby(["home_team", "stage"]).size().reset_index(name="count")
    home_stages = home_stages.rename(columns={"home_team": "team"})
    
    away_stages = matches.groupby(["away_team", "stage"]).size().reset_index(name="count")
    away_stages = away_stages.rename(columns={"away_team": "team"})
    
    all_stages = pd.concat([home_stages, away_stages]).groupby(["team", "stage"])["count"].sum().unstack(fill_value=0)
    return all_stages.reset_index()


# =========================================================
# 7. HOME ADVANTAGE (global indicator only)
# =========================================================
def compute_home_advantage(matches):
    if matches is None or matches.empty:
        return {}
    
    home_win_rate = (matches["home_score"] > matches["away_score"]).mean()
    away_win_rate = (matches["away_score"] > matches["home_score"]).mean()

    return {
        "home_win_rate": home_win_rate,
        "away_win_rate": away_win_rate,
        "home_advantage_index": home_win_rate - away_win_rate
    }


# =========================================================
# 8. MAIN PIPELINE
# =========================================================
def transform(datasets):

    # ---------------- MATCH DATA ----------------
    matches1 = datasets.get("matches", {}).get("matches_1930_2022")
    matches2 = datasets.get("compets", {}).get("wc_matches_historical")

    worldcup = datasets.get("matches", {}).get("world_cup")
    ranking = datasets.get("matches", {}).get("fifa_ranking_2022-10-06")

    h2h = datasets.get("compets", {}).get("wc_head_to_head")
    team_appearances = datasets.get("compets", {}).get("wc_team_appearances")
    team_stats_alltime = datasets.get("compets", {}).get("wc_team_alltime_stats")

    # ---------------- CLEAN ----------------
    matches1 = clean_basic(matches1)
    matches2 = clean_basic(matches2)
    worldcup = clean_basic(worldcup)

    # ---------------- STANDARDIZE COLUMNS ----------------
    for df in [matches1, matches2, worldcup, ranking, team_appearances, team_stats_alltime, h2h]:
        if df is not None:
            df.columns = df.columns.str.lower()
            
    if worldcup is not None:
        worldcup = worldcup.rename(columns={"host": "host_country", "champion": "winner"})

    # ---------------- STANDARDIZE TEXTS & COUNTRIES ----------------
    for df in [matches1, matches2, worldcup, ranking, team_appearances, team_stats_alltime, h2h]:
        if df is not None:
            df = standardize_country_names(df, ["home_team", "away_team", "team", "winner", "host_country"])
            df = normalize_strings(df, ["stadium", "stage", "city"])

    # ---------------- DATES ----------------
    matches1 = parse_dates(matches1, ["date"])
    matches2 = parse_dates(matches2, ["date"])

    # ---------------- FEATURES MATCH (LIGHT ONLY) ----------------
    matches1 = compute_match_features(matches1)
    matches2 = compute_match_features(matches2)

    # ---------------- UNIFIED MATCH HISTORY ----------------
    if matches1 is not None and matches2 is not None:
        all_matches = pd.concat([matches1, matches2], ignore_index=True)
        if {"date", "home_team", "away_team"}.issubset(all_matches.columns):
            all_matches = all_matches.drop_duplicates(subset=["date", "home_team", "away_team"])
        else:
            all_matches = all_matches.drop_duplicates()
    elif matches1 is not None:
        all_matches = matches1
    elif matches2 is not None:
        all_matches = matches2
    else:
        all_matches = pd.DataFrame()

    # ---------------- TEAM-LEVEL FEATURES ----------------
    team_stats = compute_team_stats(all_matches)
    win_rate = compute_win_rate(all_matches)
    titles = compute_titles(worldcup)
    phase_perf = compute_phase_performance(all_matches)

    # ---------------- GLOBAL INDICATOR ----------------
    home_adv = compute_home_advantage(all_matches)

    return {
        "matches": all_matches,
        "team_stats": team_stats,
        "win_rate": win_rate,
        "titles": titles,
        "phase_performance": phase_perf,
        "home_advantage": home_adv,
        "head_to_head": h2h,
        "team_appearances": team_appearances,
        "team_alltime_stats": team_stats_alltime,
        "worldcup": worldcup,
        "ranking": ranking
    }


if __name__ == "__main__":
    print("Clean ETL transformation pipeline ready")