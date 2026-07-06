#  Phase 2 — Transformation (`transform.py`)

## Rôle dans le Pipeline

La phase de **Transformation** est le cœur analytique du pipeline. Elle reçoit les données brutes issues de l'extraction et les convertit en **indicateurs prédictifs exploitables** pour le Machine Learning.

Elle réalise trois types d'opérations :
1. **Nettoyage** — suppression des doublons, valeurs manquantes, standardisation des formats
2. **Harmonisation** — unification des noms de pays historiques, normalisation des textes
3. **Feature Engineering** — calcul de nouveaux indicateurs statistiques par équipe

---

##  Architecture du Script

Le script est organisé en **8 sections** numérotées :

```
1. DICTIONARIES & MAPPINGS     → Table de correspondance des noms de pays
2. CLEANING & STANDARDIZATION  → Fonctions de nettoyage de base
3. MATCH FEATURES              → Calcul de variables par match
4. TEAM STATS                  → Statistiques offensives/défensives par équipe
5. WIN RATE                    → Taux de victoire corrigé statistiquement
6. TITLES & PHASE PERFORMANCE  → Titres remportés et performances par phase
7. HOME ADVANTAGE              → Indicateur global d'avantage à domicile
8. MAIN PIPELINE               → Fonction orchestratrice transform()
```

---

##  Section 1 — Dictionnaire de Correspondance des Pays

```python
COUNTRY_MAPPING = {
    "West Germany":          "Germany",
    "FRG":                   "Germany",
    "East Germany":          "Germany",
    "Soviet Union":          "Russia",
    "Zaire":                 "DR Congo",
    "Yugoslavia":            "Serbia",
    "Serbia and Montenegro": "Serbia",
    "Dutch East Indies":     "Indonesia",
    "Czechoslovakia":        "Czech Republic",
    "IR Iran":               "Iran"
}
```

**Problème résolu :** Les données historiques (1930–2022) utilisent des noms de nations qui n'existent plus aujourd'hui. Sans harmonisation, l'Allemagne de l'Ouest (`West Germany`) et l'Allemagne actuelle (`Germany`) seraient considérées comme deux équipes distinctes, **divisant artificiellement leurs statistiques**.

Ce dictionnaire fusionne ces entités historiques vers leur équivalent moderne, permettant un calcul cohérent sur toute la période.

---

##  Section 2 — Nettoyage & Standardisation

### `standardize_country_names(df, columns)`
Applique le `COUNTRY_MAPPING` sur les colonnes spécifiées (`home_team`, `away_team`, `team`, `winner`, `host_country`).

### `normalize_strings(df, columns)`
Convertit les valeurs textuelles (`stadium`, `stage`, `city`) en **minuscules sans espaces superflus** pour éviter les doublons liés à la casse (`"Wembley"` vs `"wembley"`).

### `clean_basic(df)`
- Supprime les lignes entièrement dupliquées (`.drop_duplicates()`)
- Supprime les lignes entièrement vides (`.dropna(how="all")`)

### `parse_dates(df, cols)`
Convertit les colonnes de dates en `datetime` pandas avec `errors="coerce"` (les valeurs non parsables deviennent `NaT` plutôt que de lever une erreur).

---

##  Section 3 — Features par Match

### `compute_match_features(df)`

Ajoute deux colonnes à chaque DataFrame de matchs :

| Colonne | Calcul | Description |
|---|---|---|
| `goal_diff` | `home_score - away_score` | Différence de buts du match (positif = victoire domicile) |
| `result` | Comparaison des scores | `"H"` (Home win), `"A"` (Away win), `"D"` (Draw) |

---

##  Section 4 — Statistiques par Équipe

### `compute_team_stats(matches) -> DataFrame`

Calcule des statistiques **offensives et défensives** pour chaque pays sur l'ensemble de l'historique, en agrégeant les performances à domicile ET à l'extérieur.

**Méthode :**
- Agrégation séparée des matchs `home` et `away`
- Jointure externe (`outer join`) pour inclure toutes les équipes
- Combinaison des totaux

**Colonnes produites :**

| Colonne | Description |
|---|---|
| `team` | Nom de l'équipe |
| `goals_scored` | Total de buts marqués (domicile + extérieur) |
| `goals_conceded` | Total de buts encaissés (domicile + extérieur) |
| `games_played` | Total de matchs joués |
| `goal_diff` | Différence de buts globale |
| `goals_per_game` | Moyenne de buts marqués par match |
| `conceded_per_game` | Moyenne de buts encaissés par match |

---

##  Section 5 — Taux de Victoire (Corrigé)

### `compute_win_rate(matches) -> DataFrame`

**Problème du biais statistique corrigé :** Une erreur classique consiste à calculer le taux de victoire en faisant la moyenne des victoires à domicile séparément de celles à l'extérieur, puis en faisant la moyenne des deux moyennes. Cette approche biaise le résultat si une équipe a joué un nombre inégal de matchs à domicile et à l'extérieur.

**Formule corrigée :**
```
win_rate = total_wins / total_games
```

où `total_wins = home_wins + away_wins` et `total_games = home_games + away_games`.

**Colonnes produites :**

| Colonne | Description |
|---|---|
| `team` | Nom de l'équipe |
| `win_rate` | Taux de victoire global (0.0 à 1.0) |
| `total_wins` | Nombre total de victoires |
| `total_games` | Nombre total de matchs joués |

---

##  Section 6 — Titres & Performances par Phase

### `compute_titles(worldcup) -> DataFrame`

Compte le nombre de **Coupes du Monde remportées** par chaque équipe depuis 1930, en s'appuyant sur la colonne `winner` du fichier `world_cup.csv`.

| Colonne | Description |
|---|---|
| `team` | Nom de l'équipe |
| `titles` | Nombre de titres mondiaux remportés |

### `compute_phase_performance(matches) -> DataFrame`

Calcule combien de fois chaque équipe a joué à chaque **phase du tournoi** (Groupes, Huitièmes, Quarts, Demi-finales, Finale...).

**Méthode :** Comptage des apparitions en `home_team` + `away_team` pour chaque couple `(équipe, phase)`, puis pivot en colonnes.

**Exemple de sortie :**

| team | group stage | quarter-finals | semi-finals | final |
|---|---|---|---|---|
| Brazil | 18 | 7 | 5 | 3 |
| Germany | 20 | 8 | 6 | 4 |
| France | 12 | 4 | 3 | 2 |

> Cet indicateur est particulièrement précieux pour évaluer la **régularité d'une équipe dans les phases éliminatoires**.

---

##  Section 7 — Avantage à Domicile

### `compute_home_advantage(matches) -> dict`

Calcule un indicateur **global** (non par équipe) de l'avantage à domicile sur toute l'histoire de la compétition.

**Valeurs retournées :**

| Clé | Description |
|---|---|
| `home_win_rate` | Proportion de matchs gagnés par l'équipe à domicile |
| `away_win_rate` | Proportion de matchs gagnés par l'équipe à l'extérieur |
| `home_advantage_index` | Différence entre les deux (`home_win_rate - away_win_rate`) |

> Un `home_advantage_index` positif et élevé confirme empiriquement que jouer sur son sol est un avantage statistique.

---

##  Section 8 — Pipeline Principal

### `transform(datasets: dict) -> dict`

Fonction **orchestratrice** principale appelée par `main.py`. Elle enchaîne toutes les étapes dans l'ordre :

```
1. Extraction des DataFrames depuis le dictionnaire d'entrée
2. Nettoyage de base (doublons, valeurs vides)
3. Normalisation des noms de colonnes en minuscules
4. Renommage des colonnes du fichier worldcup (host → host_country, champion → winner)
5. Standardisation des noms de pays (COUNTRY_MAPPING)
6. Normalisation des textes (stades, phases, villes)
7. Parsing des dates
8. Calcul des features par match (goal_diff, result)
9. Fusion des deux sources de matchs en un historique unifié
10. Déduplication sur (date, home_team, away_team)
11. Calcul de tous les indicateurs par équipe
```

**Paramètre :** `datasets` — le dictionnaire retourné par `extract()`

---

##  Contrat de Sortie

La fonction `transform()` retourne un dictionnaire contenant **11 éléments** :

| Clé | Type | Description |
|---|---|---|
| `matches` | `DataFrame` | Historique unifié de tous les matchs (~1015 lignes, nettoyé et enrichi) |
| `team_stats` | `DataFrame` | Stats offensives/défensives par équipe (83 équipes) |
| `win_rate` | `DataFrame` | Taux de victoire global par équipe |
| `titles` | `DataFrame` | Nombre de titres mondiaux par équipe |
| `phase_performance` | `DataFrame` | Nombre de matchs par phase du tournoi par équipe |
| `home_advantage` | `dict` | Indicateurs globaux d'avantage à domicile |
| `head_to_head` | `DataFrame` | Données de face-à-face entre équipes (brut) |
| `team_appearances` | `DataFrame` | Nombre de participations à la CdM par équipe (brut) |
| `team_alltime_stats` | `DataFrame` | Statistiques all-time par équipe (brut) |
| `worldcup` | `DataFrame` | Palmarès des Coupes du Monde nettoyé |
| `ranking` | `DataFrame` | Classement FIFA (brut) |

---

##  Dépendances

| Bibliothèque | Usage |
|---|---|
| `pandas` | Manipulation et agrégation des DataFrames |
| `numpy` | Calculs vectorisés (`np.where`, divisions avec protection div/0) |

---

##  Exécution en Standalone

```bash
python scripts/transform.py
```

> En standalone, le script affiche uniquement `"Clean ETL transformation pipeline ready"`. Pour tester avec des données réelles, utiliser `main.py`.
