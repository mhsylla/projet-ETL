import sqlite3
import pandas as pd
from pathlib import Path

DB_PATH = Path("data/datawarehouse.db")

def create_dimensions(transformed_data):
    """Crée les tables de dimensions à partir des données transformées."""
    
    # 1. Dimension: Équipes (dim_team)
    teams = set()
    if not transformed_data["matches"].empty:
        teams.update(transformed_data["matches"]["home_team"].dropna().unique())
        teams.update(transformed_data["matches"]["away_team"].dropna().unique())
    
    dim_team = pd.DataFrame({"team_name": list(teams)})
    dim_team["team_id"] = dim_team.index + 1
    
    stats = transformed_data.get("team_stats", pd.DataFrame())
    win_rate = transformed_data.get("win_rate", pd.DataFrame())
    titles = transformed_data.get("titles", pd.DataFrame())
    
    if not stats.empty:
        dim_team = dim_team.merge(stats[["team", "games_played"]], left_on="team_name", right_on="team", how="left").drop(columns=["team"])
    if not win_rate.empty:
        dim_team = dim_team.merge(win_rate[["team", "win_rate"]], left_on="team_name", right_on="team", how="left").drop(columns=["team"])
    if not titles.empty:
        dim_team = dim_team.merge(titles[["team", "titles"]], left_on="team_name", right_on="team", how="left").drop(columns=["team"])
        dim_team["titles"] = dim_team["titles"].fillna(0).astype(int)
    
    # 2. Dimension: Éditions (dim_edition)
    worldcup = transformed_data.get("worldcup", pd.DataFrame())
    if not worldcup.empty:
        # Avoid KeyError if some columns don't exist
        cols = [c for c in ["year", "host_country", "winner", "teams"] if c in worldcup.columns]
        dim_edition = worldcup[cols].copy()
        if "year" in dim_edition.columns:
            dim_edition = dim_edition.rename(columns={"year": "edition_year"})
    else:
        dim_edition = pd.DataFrame(columns=["edition_year", "host_country", "winner", "teams"])
    
    # 3. Dimension: Stades (dim_stadium)
    matches = transformed_data["matches"]
    dim_stadium = pd.DataFrame()
    if not matches.empty and "stadium" in matches.columns:
        cols_stadium = ["stadium", "city"] if "city" in matches.columns else ["stadium"]
        dim_stadium = matches[cols_stadium].drop_duplicates().dropna(subset=["stadium"])
        dim_stadium = dim_stadium.reset_index(drop=True)
        dim_stadium["stadium_id"] = dim_stadium.index + 1
    else:
         dim_stadium = pd.DataFrame(columns=["stadium_id", "stadium", "city"])
        
    return {
        "dim_team": dim_team,
        "dim_edition": dim_edition,
        "dim_stadium": dim_stadium
    }


def create_facts(transformed_data, dimensions):
    """Crée les tables de faits en utilisant les IDs des dimensions."""
    
    matches = transformed_data["matches"].copy()
    dim_team = dimensions["dim_team"]
    dim_stadium = dimensions["dim_stadium"]
    
    facts = {}
    team_map = dim_team.set_index("team_name")["team_id"].to_dict()
    
    # 1. Table de faits: Matchs (fact_matches)
    if not matches.empty:
        fact_matches = matches.copy()
        
        fact_matches["home_team_id"] = fact_matches["home_team"].map(team_map)
        fact_matches["away_team_id"] = fact_matches["away_team"].map(team_map)
        
        if "stadium" in fact_matches.columns and not dim_stadium.empty:
            stadium_map = dim_stadium.set_index("stadium")["stadium_id"].to_dict()
            fact_matches["stadium_id"] = fact_matches["stadium"].map(stadium_map)
            
        cols_to_keep = ["date", "home_team_id", "away_team_id", "stadium_id", "home_score", "away_score", "goal_diff", "stage", "result"]
        cols_to_keep = [c for c in cols_to_keep if c in fact_matches.columns]
        facts["fact_matches"] = fact_matches[cols_to_keep]
    
    # 2. Table de faits: Performances des équipes (fact_team_performance)
    team_stats = transformed_data.get("team_stats", pd.DataFrame())
    if not team_stats.empty:
        fact_team_perf = team_stats.copy()
        fact_team_perf["team_id"] = fact_team_perf["team"].map(team_map)
        fact_team_perf = fact_team_perf.drop(columns=["team"])
        facts["fact_team_performance"] = fact_team_perf
        
    # 3. Table de faits: Performances par phase (fact_phase_performance)
    phase_perf = transformed_data.get("phase_performance", pd.DataFrame())
    if not phase_perf.empty:
        fact_phase = phase_perf.copy()
        fact_phase["team_id"] = fact_phase["team"].map(team_map)
        fact_phase = fact_phase.drop(columns=["team"])
        facts["fact_phase_performance"] = fact_phase
        
    # 4. Table de faits: Head to head (fact_head_to_head)
    h2h = transformed_data.get("head_to_head", pd.DataFrame())
    if not h2h.empty:
        facts["fact_head_to_head"] = h2h

    return facts


def load_to_sqlite(db_path, dimensions, facts):
    """Charge les dataframes dans la base SQLite."""
    
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    
    for name, df in dimensions.items():
        df.to_sql(name, conn, if_exists="replace", index=False)
        print(f"✅ Dimension chargée : {name} ({len(df)} lignes)")
        
    for name, df in facts.items():
        df.to_sql(name, conn, if_exists="replace", index=False)
        print(f"✅ Fait chargé : {name} ({len(df)} lignes)")
        
    conn.close()
    print(f"\n🚀 Data Warehouse généré avec succès dans : {db_path}")


def load(transformed_data):
    """Fonction principale du processus de Load."""
    print("Mise en place du Schéma en Étoile...")
    dimensions = create_dimensions(transformed_data)
    facts = create_facts(transformed_data, dimensions)
    load_to_sqlite(DB_PATH, dimensions, facts)

if __name__ == "__main__":
    print("Script de chargement prêt.")
