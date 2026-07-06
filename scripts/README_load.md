#  Phase 3 — Chargement (`load.py`)

## Rôle dans le Pipeline

La phase de **Chargement** est l'étape finale du pipeline ETL. Elle prend le dictionnaire d'indicateurs produit par `transform.py` et le **structure dans un Data Warehouse** SQLite local, organisé selon un **Schéma en Étoile** (_Star Schema_).

> **Objectif :** Transformer un dictionnaire Python en une base de données relationnelle interrogeable via SQL, optimisée pour les requêtes analytiques et le Machine Learning.

---

##  Concept : Le Schéma en Étoile

Le **Schéma en Étoile** est le standard de l'architecture des Data Warehouses analytiques. Il sépare les données en deux types de tables :

- **Tables de Dimensions** : référentiels décrivant **qui**, **quoi**, **où** (équipes, éditions, stades)
- **Tables de Faits** : mesures numériques et métriques liées aux dimensions via des clés étrangères

```
              ┌──────────────────┐
              │   dim_edition    │
              │  22 éditions CdM │
              └────────┬─────────┘
                       │
┌─────────────┐  ┌─────▼──────────┐  ┌─────────────────────┐
│ dim_stadium │──  fact_matches  │◀──│      dim_team       │
│  (stades)   │  │  (1015 matchs) │  │  (83 équipes)       │
└─────────────┘  └────────┬───────┘  │  + stats globales   │
                          │          └──────────┬──────────┘
                          │                     │
               ┌──────────▼──────┐  ┌──────────▼──────────┐
               │fact_team_perf   │  │ fact_phase_perf      │
               │(stats offens./  │  │(présences par phase  │
               │ défens.)        │  │ du tournoi)          │
               └─────────────────┘  └──────────────────────┘
```

---

##  Architecture du Script

Le script est composé de **4 fonctions** :

| Fonction | Rôle |
|---|---|
| `create_dimensions(transformed_data)` | Construit les 3 tables de dimensions |
| `create_facts(transformed_data, dimensions)` | Construit les 4 tables de faits avec les IDs |
| `load_to_sqlite(db_path, dimensions, facts)` | Persiste toutes les tables dans SQLite |
| `load(transformed_data)` | Fonction principale appelée par `main.py` |

---

##  Section 1 — Tables de Dimensions

### `create_dimensions(transformed_data) -> dict`

#### `dim_team` — Table des Équipes

La dimension centrale du Data Warehouse. Chaque ligne représente une **équipe nationale** avec ses indicateurs de performance globaux.

**Construction :**
1. Extrait toutes les équipes uniques depuis `home_team` et `away_team` dans `fact_matches`
2. Fusionne avec `team_stats` (stats offensives/défensives)
3. Fusionne avec `win_rate` (taux de victoire)
4. Fusionne avec `titles` (nombre de titres)

**Colonnes :**

| Colonne | Type | Description |
|---|---|---|
| `team_id` | `int` | Clé primaire auto-incrémentée |
| `team_name` | `str` | Nom de l'équipe (ex: `"France"`, `"Brazil"`) |
| `games_played` | `int` | Nombre total de matchs joués en CdM |
| `win_rate` | `float` | Taux de victoire global (0.0 à 1.0) |
| `titles` | `int` | Nombre de Coupes du Monde remportées (0 par défaut) |

**Exemple :**

| team_id | team_name | games_played | win_rate | titles |
|---|---|---|---|---|
| 1 | Brazil | 109 | 0.674 | 5 |
| 2 | Germany | 106 | 0.613 | 4 |
| 3 | France | 66 | 0.545 | 2 |

---

#### `dim_edition` — Table des Éditions

Chaque ligne représente une **édition de la Coupe du Monde**.

**Source :** `worldcup` DataFrame (issu du fichier `world_cup.csv`)

**Colonnes :**

| Colonne | Type | Description |
|---|---|---|
| `edition_year` | `int` | Année de l'édition (ex: `1998`, `2022`) |
| `host_country` | `str` | Pays organisateur |
| `winner` | `str` | Équipe championne |
| `teams` | `int` | Nombre d'équipes participantes |

> Si le fichier `world_cup.csv` n'existe pas, une table vide est créée pour ne pas bloquer le pipeline.

---

#### `dim_stadium` — Table des Stades

Chaque ligne représente un **stade unique** ayant accueilli des matchs.

**Source :** Colonnes `stadium` et `city` du DataFrame `matches` unifié

**Construction :** Déduplication sur la colonne `stadium` + réinitialisation de l'index

**Colonnes :**

| Colonne | Type | Description |
|---|---|---|
| `stadium_id` | `int` | Clé primaire auto-incrémentée |
| `stadium` | `str` | Nom du stade (normalisé en minuscules) |
| `city` | `str` | Ville du stade (si disponible) |

---

##  Section 2 — Tables de Faits

### `create_facts(transformed_data, dimensions) -> dict`

#### `fact_matches` — Faits des Matchs

La table de faits principale. Chaque ligne représente un **match individuel** de l'historique.

Les noms d'équipes (`home_team`, `away_team`) sont remplacés par leurs **IDs de dimension** (`home_team_id`, `away_team_id`) via un dictionnaire de correspondance.

**Colonnes :**

| Colonne | Type | Description |
|---|---|---|
| `date` | `datetime` | Date du match |
| `home_team_id` | `int` | Clé étrangère → `dim_team.team_id` |
| `away_team_id` | `int` | Clé étrangère → `dim_team.team_id` |
| `stadium_id` | `int` | Clé étrangère → `dim_stadium.stadium_id` |
| `home_score` | `int` | Buts marqués par l'équipe à domicile |
| `away_score` | `int` | Buts marqués par l'équipe à l'extérieur |
| `goal_diff` | `int` | Différence de buts (`home_score - away_score`) |
| `stage` | `str` | Phase du tournoi (normalisée en minuscules) |
| `result` | `str` | Résultat : `"H"`, `"A"` ou `"D"` |

---

#### `fact_team_performance` — Performances Globales par Équipe

Reprend les statistiques offensives/défensives calculées par `compute_team_stats()`, enrichies de la clé de dimension.

**Colonnes :**

| Colonne | Type | Description |
|---|---|---|
| `team_id` | `int` | Clé étrangère → `dim_team.team_id` |
| `goals_scored` | `int` | Total buts marqués |
| `goals_conceded` | `int` | Total buts encaissés |
| `games_played` | `int` | Nombre total de matchs |
| `goal_diff` | `int` | Différence de buts globale |
| `goals_per_game` | `float` | Moyenne buts marqués / match |
| `conceded_per_game` | `float` | Moyenne buts encaissés / match |

---

#### `fact_phase_performance` — Performances par Phase du Tournoi

Reprend le tableau produit par `compute_phase_performance()`. Chaque ligne représente une **équipe** avec le nombre de matchs joués dans **chaque phase** sous forme de colonnes pivotées.

**Colonnes :**

| Colonne | Type | Description |
|---|---|---|
| `team_id` | `int` | Clé étrangère → `dim_team.team_id` |
| `group stage` | `int` | Matchs joués en phase de groupes |
| `quarter-finals` | `int` | Matchs joués en quarts de finale |
| `semi-finals` | `int` | Matchs joués en demi-finales |
| `final` | `int` | Matchs joués en finale |
| *(autres phases...)* | `int` | Toutes les phases présentes dans les données |

---

#### `fact_head_to_head` — Face-à-Face entre Équipes

Charge directement les données brutes de `wc_head_to_head.csv`, sans transformation. Contient les statistiques historiques de confrontations directes entre paires d'équipes en Coupe du Monde.

---

##  Section 3 — Persistance SQLite

### `load_to_sqlite(db_path, dimensions, facts)`

**Comportement :**
1. Crée le répertoire `data/` si inexistant (`mkdir(parents=True, exist_ok=True)`)
2. Ouvre une connexion SQLite vers `data/datawarehouse.db`
3. Écrit chaque dimension avec `df.to_sql(name, conn, if_exists="replace")`
4. Écrit chaque table de faits de la même manière
5. Ferme la connexion
6. Affiche un résumé avec le nombre de lignes chargées par table

> La politique `if_exists="replace"` garantit que chaque exécution du pipeline **recrée proprement** le Data Warehouse en supprimant les données précédentes.

---

##  Sortie Finale

À la fin du pipeline, la base `data/datawarehouse.db` contient **7 tables** :

| Table | Type | Description |
|---|---|---|
| `dim_team` | Dimension | Référentiel des équipes avec métriques |
| `dim_edition` | Dimension | Référentiel des éditions de la CdM |
| `dim_stadium` | Dimension | Référentiel des stades |
| `fact_matches` | Fait | Historique de tous les matchs |
| `fact_team_performance` | Fait | Stats offensives/défensives par équipe |
| `fact_phase_performance` | Fait | Présences par phase du tournoi |
| `fact_head_to_head` | Fait | Face-à-face historiques |

---

##  Interroger le Data Warehouse

La base peut être requêtée directement en Python ou via un outil SQL :

```python
import sqlite3
import pandas as pd

conn = sqlite3.connect("data/datawarehouse.db")

# Top 10 équipes par taux de victoire
query = """
    SELECT team_name, win_rate, titles, games_played
    FROM dim_team
    WHERE games_played > 10
    ORDER BY win_rate DESC
    LIMIT 10
"""
df = pd.read_sql(query, conn)
print(df)
conn.close()
```

**Exemple de jointure :**

```python
# Matchs de finale avec les noms d'équipes
query = """
    SELECT
        fm.date,
        ht.team_name AS home_team,
        at.team_name AS away_team,
        fm.home_score,
        fm.away_score,
        fm.stage
    FROM fact_matches fm
    JOIN dim_team ht ON fm.home_team_id = ht.team_id
    JOIN dim_team at ON fm.away_team_id = at.team_id
    WHERE fm.stage = 'final'
    ORDER BY fm.date
"""
finals = pd.read_sql(query, conn)
```

---

##  Dépendances

| Bibliothèque | Usage |
|---|---|
| `sqlite3` | Connexion et écriture dans la base SQLite (stdlib Python) |
| `pandas` | Manipulation des DataFrames et écriture avec `.to_sql()` |
| `pathlib.Path` | Gestion du chemin vers la base de données |

---

##  Exécution en Standalone

```bash
python scripts/load.py
```

> En standalone, le script affiche uniquement `"Script de chargement prêt."`. Pour une exécution complète, utiliser `main.py`.
