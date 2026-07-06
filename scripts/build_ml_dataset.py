import pandas as pd
import numpy as np
from pathlib import Path

def build_ml_dataset():
    """
    Construit le jeu de données pour le Machine Learning.
    Calcule les variables historiques cumulées (avant le tournoi) pour éviter le data leakage,
    et encode les cibles du tournoi.
    """
    print("\n===================================")
    print(" CONSTRUCTION DU DATASET ML")
    print("===================================")
    
    # 1. Charger les données d'apparitions historiques
    # Le fichier source brut contient l'historique par équipe et par année.
    raw_path = Path("data/raw/compets/wc_team_appearances.csv")
    if not raw_path.exists():
        print(f"Erreur : fichier {raw_path} introuvable.")
        return
        
    df = pd.read_csv(raw_path)
    
    # S'assurer du bon format et trier chronologiquement
    df["wc_year"] = pd.to_numeric(df["wc_year"], errors="coerce")
    df = df.dropna(subset=["wc_year"]).sort_values(by=["team", "wc_year"])
    
    # 2. Initialisation des listes pour les nouvelles colonnes
    ml_data = []
    
    # Variables de suivi par équipe
    history = {}
    
    for _, row in df.iterrows():
        team = row["team"]
        year = int(row["wc_year"])
        
        # Initialiser l'historique de l'équipe si c'est sa première apparition
        if team not in history:
            history[team] = {
                "participations": 0,
                "matches_played": 0,
                "wins": 0,
                "goals_scored": 0,
                "goals_conceded": 0,
                "titles": 0,
                "consecutive": 0,
                "last_year": 0
            }
            
        t_hist = history[team]
        
        # Feature Engineering (avant le tournoi actuel)
        wc_appearances = t_hist["participations"]
        is_debut = 1 if wc_appearances == 0 else 0
        
        # Calcul de la série d'apparitions consécutives
        # Si last_year est l'édition précédente (à 4 ans d'écart, sauf WW2)
        consecutive = t_hist["consecutive"]
        
        # Win rate historique
        if t_hist["matches_played"] > 0:
            win_rate_before = t_hist["wins"] / t_hist["matches_played"]
            gf_per_match_before = t_hist["goals_scored"] / t_hist["matches_played"]
            ga_per_match_before = t_hist["goals_conceded"] / t_hist["matches_played"]
        else:
            win_rate_before = 0.0
            gf_per_match_before = 0.0
            ga_per_match_before = 0.0
            
        # Variables statiques de la ligne
        host = 1 if str(row.get("host_nation", "")).lower() == "yes" else 0
        elo = pd.to_numeric(row.get("elo_rating_approx", np.nan), errors="coerce")
        
        # 3. Encodage des cibles (Targets)
        stage = str(row.get("final_stage_reached", "")).lower()
        target_champion = 1 if stage == "winner" else 0
        target_top4 = 1 if stage in ["winner", "runner-up", "third place", "fourth place", "semi-finals"] else 0
        target_top8 = 1 if stage in ["quarter-finals"] or target_top4 == 1 else 0
        
        # Ajouter la ligne au jeu de données ML
        ml_data.append({
            "team": team,
            "confederation": row.get("confederation", "Unknown"),
            "wc_year": year,
            "wc_appearances": wc_appearances,
            "wc_titles": t_hist["titles"],
            "elo_rating": elo,
            "host_nation": host,
            "consecutive_wc_appearances": consecutive,
            "is_debut": is_debut,
            "win_rate_before": round(win_rate_before, 3),
            "goals_scored_per_match_before": round(gf_per_match_before, 3),
            "goals_conceded_per_match_before": round(ga_per_match_before, 3),
            "target_champion": target_champion,
            "target_top4": target_top4,
            "target_top8": target_top8
        })
        
        # 4. Mise à jour de l'historique de l'équipe (APRES avoir enregistré la ligne)
        t_hist["participations"] += 1
        t_hist["matches_played"] += pd.to_numeric(row.get("matches_played", 0), errors="coerce")
        t_hist["wins"] += pd.to_numeric(row.get("wins", 0), errors="coerce")
        t_hist["goals_scored"] += pd.to_numeric(row.get("goals_scored", 0), errors="coerce")
        t_hist["goals_conceded"] += pd.to_numeric(row.get("goals_conceded", 0), errors="coerce")
        if target_champion == 1:
            t_hist["titles"] += 1
            
        if year - t_hist["last_year"] <= 4 or (year == 1950 and t_hist["last_year"] == 1938):
            t_hist["consecutive"] += 1
        else:
            t_hist["consecutive"] = 1 # reset to 1 for next time
            
        t_hist["last_year"] = year

    # 5. Conversion en DataFrame
    ml_df = pd.DataFrame(ml_data)
    
    # 6. Sauvegarde
    out_dir = Path("data/processed")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "ml_dataset_historical.csv"
    
    ml_df.to_csv(out_path, index=False)
    print(f"✅ Dataset ML généré avec succès : {out_path} ({len(ml_df)} lignes, {len(ml_df.columns)} features)")
    print("   -> Ce jeu de données est prêt pour entraîner un algorithme de Machine Learning sans fuite de données.")

if __name__ == "__main__":
    build_ml_dataset()
