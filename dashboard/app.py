"""
app.py — Page d'accueil du Dashboard EDA
Coupe du Monde 2026 — Analyse Exploratoire
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent))

import streamlit as st
from data_loader import load_all, get_matches, get_team_alltime, get_win_rate, add_flag_column, with_flag

# ─── Configuration de la page ───────────────────────────────────────────────
st.set_page_config(
    page_title="World Cup EDA Dashboard",
    page_icon="assets/logo.png" if Path("dashboard/assets/logo.png").exists() else "⚽",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── CSS Global ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Fond principal */
    .stApp { background-color: #0f1117; }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a1d2e 0%, #0f1117 100%);
        border-right: 1px solid #2d2f3e;
    }

    /* Titres */
    h1, h2, h3 { color: #e8eaf6 !important; }
    p, li { color: #b0b3c1; }

    /* Metric cards */
    [data-testid="metric-container"] {
        background: linear-gradient(135deg, #1e2132 0%, #252840 100%);
        border: 1px solid #3d3f5c;
        border-radius: 12px;
        padding: 1rem;
    }
    [data-testid="metric-container"] label { color: #8b8fa8 !important; font-size: 0.8rem; }
    [data-testid="metric-container"] [data-testid="stMetricValue"] {
        color: #7c83f5 !important;
        font-size: 2rem !important;
        font-weight: 700 !important;
    }

    /* Divider */
    hr { border-color: #2d2f3e !important; }

    /* Badge style */
    .badge {
        display: inline-block;
        background: linear-gradient(135deg, #4361EE, #7209B7);
        color: white;
        padding: 3px 10px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        margin: 2px;
    }
</style>
""", unsafe_allow_html=True)

# ─── Chargement des données ──────────────────────────────────────────────────
data = load_all()
matches = get_matches(data)
alltime = get_team_alltime(data)
win_rate = get_win_rate(data)

# ─── Header ─────────────────────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center; padding: 2rem 0 1rem 0;">
    <h1 style="font-size: 2.8rem; background: linear-gradient(135deg, #7c83f5, #f72585);
               -webkit-background-clip: text; -webkit-text-fill-color: transparent;
               font-weight: 800; letter-spacing: -1px;">
        Coupe du Monde — Analyse Exploratoire
    </h1>
    <p style="color: #8b8fa8; font-size: 1.1rem; margin-top: -0.5rem;">
        De l'histoire du football (1930 – 2022) à la prédiction des favoris 2026
    </p>
</div>
""", unsafe_allow_html=True)

st.divider()

# ─── KPI Cards ───────────────────────────────────────────────────────────────
col1, col2, col3, col4, col5 = st.columns(5)

total_matches   = len(matches)
total_teams     = matches["home_team"].nunique() if "home_team" in matches.columns else 0
total_editions  = matches["year"].nunique() if "year" in matches.columns else 0
avg_goals       = round((matches["home_score"].fillna(0) + matches["away_score"].fillna(0)).mean(), 2) if {"home_score","away_score"}.issubset(matches.columns) else 0
most_titles     = alltime.loc[alltime["titles"].idxmax(), "team"] if not alltime.empty and "titles" in alltime.columns else "N/A"

col1.metric("Matchs analysés",   f"{total_matches:,}")
col2.metric("Nations",           f"{total_teams}")
col3.metric("Editions",          f"{total_editions}")
col4.metric("Buts / match moy.", f"{avg_goals}")
col5.metric("Nation la + titrée", most_titles)

st.divider()

# ─── Description du projet ───────────────────────────────────────────────────
st.subheader("A propos de ce dashboard")

col_left, col_right = st.columns([3, 2])

with col_left:
    st.markdown("""
Ce dashboard constitue la **Phase 2** du projet ETL dédié à la Coupe du Monde 2026.
Il répond aux 7 questions analytiques définies dans le storytelling du projet,
en s'appuyant sur le **Data Warehouse** construit lors de la Phase 1.

**Pipeline de données :**
1. **Extraction** — 18 fichiers CSV issus de deux sources complémentaires
2. **Transformation** — Harmonisation, nettoyage, feature engineering
3. **Chargement** — Data Warehouse SQLite en schéma étoile

**Sources de données :**
- Historique complet des matchs internationaux (1930–2022)
- Données Coupe du Monde : éditions, équipes, classements FIFA
    """)

with col_right:
    st.markdown("**7 questions analytiques :**")
    questions = [
        ("01", "Domination historique"),
        ("02", "Evolution offensive du football"),
        ("03", "Impact du pays organisateur"),
        ("04", "Cycles de domination"),
        ("05", "Upsets et surprises"),
        ("06", "Performances par continent"),
        ("07", "Facteurs de succes"),
    ]
    for num, question in questions:
        st.markdown(
            f'<span class="badge">{num}</span> {question}',
            unsafe_allow_html=True
        )

st.divider()

# ─── Apercu rapide ───────────────────────────────────────────────────────────
st.subheader("Apercu rapide — Top 10 nations")

if not alltime.empty:
    import plotly.express as px

    top10_raw = alltime.nlargest(10, "titles")[["team", "titles", "total_wc_appearances", "win_rate", "finals_reached"]]
    top10_raw = add_flag_column(top10_raw)
    top10 = top10_raw.rename(columns={
        "flag_team": "Nation",
        "titles": "Titres",
        "total_wc_appearances": "Participations",
        "win_rate": "Win Rate",
        "finals_reached": "Finales",
    })
    top10["Win Rate"] = (top10["Win Rate"] * 100).round(1).astype(str) + "%"

    fig = px.bar(
        top10,
        x="Nation",
        y="Titres",
        color="Titres",
        color_continuous_scale="Blues",
        template="plotly_dark",
        title="Top 10 nations — Titres remportes",
    )
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        coloraxis_showscale=False,
        margin=dict(t=40, b=0),
        title_font_color="#e8eaf6",
        xaxis=dict(tickfont=dict(size=14)),
    )
    fig.update_traces(marker_line_width=0)
    st.plotly_chart(fig, use_container_width=True)

    display_cols = [c for c in ["Nation", "Titres", "Participations", "Win Rate", "Finales"] if c in top10.columns]
    st.dataframe(
        top10[display_cols],
        use_container_width=True,
        hide_index=True,
    )

# ─── Footer ──────────────────────────────────────────────────────────────────
st.divider()
st.markdown(
    "<p style='text-align:center; color:#3d3f5c; font-size:0.8rem;'>"
    "Projet ETL — Coupe du Monde 2026 | Données : 1930–2022 | Streamlit + Plotly"
    "</p>",
    unsafe_allow_html=True,
)
