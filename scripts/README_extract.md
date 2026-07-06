#  Phase 1 — Extraction (`extract.py`)

## Rôle dans le Pipeline

La phase d'**Extraction** est la première étape du pipeline ETL. Son rôle est simple et ciblé : **lire les données brutes depuis le système de fichiers** et les retourner sous forme de DataFrames Python, sans aucune transformation.

> **Principe clé :** Cette phase ne modifie rien. Elle se contente de charger et de rendre les données disponibles pour l'étape suivante.

---

##  Sources de Données

L'extraction lit deux dossiers distincts situés dans `data/raw/` :

### `data/raw/matches/` — Données Matchs

| Fichier CSV | Contenu | Utilisation dans le pipeline |
|---|---|---|
| `matches_1930_2022.csv` | Historique complet de tous les matchs internationaux de 1930 à 2022 | Source principale des statistiques par équipe |
| `world_cup.csv` | Palmarès de chaque édition de la Coupe du Monde (vainqueur, hôte, année) | Calcul du nombre de titres par pays |
| `fifa_ranking_2022-10-06.csv` | Classement FIFA à la date du 6 octobre 2022 | Feature pour le modèle ML |
| `fifa_ranking_2026-06-08.csv` | Classement FIFA à la date du 8 juin 2026 | Feature pour le modèle ML |
| `schedule_2026.csv` | Calendrier officiel des matchs de la CdM 2026 | Données de prédiction |

### `data/raw/compets/` — Données Compétitions

| Fichier CSV | Contenu | Utilisation dans le pipeline |
|---|---|---|
| `wc_matches_historical.csv` | Matchs joués en Coupe du Monde avec phases du tournoi | Source principale des performances par phase |
| `wc_head_to_head.csv` | Statistiques de face-à-face entre équipes en CdM | Feature H2H pour le modèle |
| `wc_team_appearances.csv` | Nombre de participations de chaque équipe à la CdM | Indicateur d'expérience |
| `wc_team_alltime_stats.csv` | Statistiques cumulées all-time de chaque équipe en CdM | Consolidation des données |
| `wc_2026_groups.csv` | Groupes de la Coupe du Monde 2026 | Données de prédiction |
| `wc_2026_teams_snapshot.csv` | Snapshot des équipes qualifiées pour 2026 | Données de prédiction |
| `wc_2026_group_difficulty.csv` | Indice de difficulté par groupe | Feature pour le modèle |
| `wc_2026_qualifying_summary.csv` | Résumé des qualifications pour 2026 | Données de prédiction |
| `wc_coaches_2026.csv` | Coaches des équipes qualifiées pour 2026 | Données contextuelles |
| `wc_top_scorers_by_edition.csv` | Meilleurs buteurs par édition | Données contextuelles |
| `wc_tournaments.csv` | Informations générales sur chaque tournoi | Données contextuelles |
| `wc_prediction_features_2026.csv` | Features pré-calculées pour la prédiction 2026 | Données de prédiction |

---

##  Fonctionnement du Code

### `load_dataset(folder: str) -> dict`

```python
def load_dataset(folder: str) -> dict:
```

**Paramètre :** `folder` — nom du sous-dossier dans `data/raw/` (`"matches"` ou `"compets"`)

**Comportement :**
1. Construit le chemin complet vers le dossier
2. Vérifie que le dossier existe (lève `FileNotFoundError` sinon)
3. Parcourt **tous les fichiers `.csv`** du dossier avec `Path.glob("*.csv")`
4. Charge chaque fichier avec `pd.read_csv()` sans transformation
5. Retourne un dictionnaire `{nom_du_fichier: DataFrame}`

> Le nom de clé dans le dictionnaire est le **nom du fichier sans extension** (ex: `"matches_1930_2022"`, `"wc_head_to_head"`).

**Exemple de sortie :**
```python
{
  "matches_1930_2022": DataFrame(shape=(45000, 9)),
  "world_cup":         DataFrame(shape=(22, 5)),
  "fifa_ranking_2022-10-06": DataFrame(shape=(200, 4)),
  ...
}
```

---

### `extract() -> dict`

```python
def extract() -> dict:
```

**Fonction principale** appelée par `main.py`. Elle orchestre le chargement des deux dossiers et retourne un dictionnaire à deux niveaux :

```python
return {
    "compets": { ...tous les DataFrames du dossier compets... },
    "matches": { ...tous les DataFrames du dossier matches... }
}
```

---

##  Contrat de Sortie

La fonction `extract()` retourne un dictionnaire de la forme :

```python
{
    "matches": {
        "matches_1930_2022":       DataFrame,
        "world_cup":               DataFrame,
        "fifa_ranking_2022-10-06": DataFrame,
        "fifa_ranking_2026-06-08": DataFrame,
        "schedule_2026":           DataFrame,
    },
    "compets": {
        "wc_matches_historical":        DataFrame,
        "wc_head_to_head":             DataFrame,
        "wc_team_appearances":         DataFrame,
        "wc_team_alltime_stats":       DataFrame,
        "wc_2026_groups":              DataFrame,
        "wc_2026_teams_snapshot":      DataFrame,
        "wc_2026_group_difficulty":    DataFrame,
        "wc_2026_qualifying_summary":  DataFrame,
        "wc_coaches_2026":             DataFrame,
        "wc_top_scorers_by_edition":   DataFrame,
        "wc_tournaments":              DataFrame,
        "wc_prediction_features_2026": DataFrame,
    }
}
```

Ce dictionnaire est passé **tel quel** à la fonction `transform()`.

---

##  Dépendances

| Bibliothèque | Usage |
|---|---|
| `pandas` | Lecture des fichiers CSV avec `pd.read_csv()` |
| `pathlib.Path` | Manipulation des chemins de fichiers de manière cross-platform |

---

##  Exécution en Standalone

Il est possible de tester l'extraction seule :

```bash
python scripts/extract.py
```

Sortie attendue :
```
====== DATASET 1 (compets) ======
wc_matches_historical : (234, 12)
wc_head_to_head : (...)
...

====== DATASET 2 (matches) ======
matches_1930_2022 : (45000, 9)
world_cup : (22, 5)
...
```
