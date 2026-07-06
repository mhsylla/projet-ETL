"""
Page 5 — Les surprises deviennent-elles plus frequentes ?

Compare classement FIFA et performance en tournoi pour detecter les upsets.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from data_loader import load_all, get_team_appearances, PHASE_SCORE, add_flag_column, with_flag

st.set_page_config(page_title="Upsets et Surprises", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #0f1117; }
    [data-testid="stSidebar"] { background: linear-gradient(180deg, #1a1d2e 0%, #0f1117 100%); }
    h1, h2, h3 { color: #e8eaf6 !important; }
    p, li { color: #b0b3c1; }
    [data-testid="metric-container"] {
        background: linear-gradient(135deg, #1e2132 0%, #252840 100%);
        border: 1px solid #3d3f5c; border-radius: 12px; padding: 1rem;
    }
    [data-testid="metric-container"] label { color: #8b8fa8 !important; }
    [data-testid="metric-container"] [data-testid="stMetricValue"] {
        color: #7c83f5 !important; font-weight: 700 !important;
    }
</style>
""", unsafe_allow_html=True)

# ─── Data ────────────────────────────────────────────────────────────────────
data        = load_all()
appearances = get_team_appearances(data)

st.title("05 — Les surprises deviennent-elles plus frequentes ?")
st.markdown(
    "Comparaison entre le score ELO avant le tournoi et la phase effectivement atteinte. "
    "Un 'upset' se produit quand une equipe avec un faible ELO depasse les attentes."
)
st.divider()

if appearances.empty or "elo_rating_approx" not in appearances.columns:
    st.warning("La colonne `elo_rating_approx` est necessaire pour cette analyse.")
    st.dataframe(appearances.head())
    st.stop()

df = appearances.copy()
df["phase_lower"]  = df["final_stage_reached"].astype(str).str.lower().str.strip()
df["phase_score"]  = df["phase_lower"].map(PHASE_SCORE).fillna(0)
df["elo_rating"] = pd.to_numeric(df["elo_rating_approx"], errors="coerce")

df_valid = df.dropna(subset=["elo_rating", "phase_score"])

# ─── KPIs ────────────────────────────────────────────────────────────────────
corr = df_valid[["elo_rating", "phase_score"]].corr().loc["elo_rating", "phase_score"]

# Upsets = equipes avec ELO < 1750 ayant atteint les quarts ou plus (phase_score >= 3)
upsets = df_valid[(df_valid["elo_rating"] < 1750) & (df_valid["phase_score"] >= 2)]

col1, col2, col3, col4 = st.columns(4)
col1.metric("Correlation ELO/Performance", f"{corr:.2f}",
            help="Proche de 1 = le score ELO predit bien la performance (score plus haut = meilleure equipe)")
col2.metric("Upsets detectes", len(upsets),
            help="Equipes avec ELO < 1750 ayant atteint les quarts de finale ou plus")
col3.metric("Top ELO (>1950) → finale", len(df_valid[(df_valid["elo_rating"] >= 1950) & (df_valid["phase_score"] >= 4)]))
col4.metric("Scores ELO analyses", len(df_valid))

st.divider()

# ─── Sidebar ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Filtres")
    if "wc_year" in df_valid.columns:
        years_clean = df_valid["wc_year"].dropna()
        if not years_clean.empty:
            year_min = int(years_clean.min())
            year_max = int(years_clean.max())
            year_range = st.slider(
                "Periode",
                year_min, year_max,
                (year_min, year_max)
            )
            df_valid = df_valid[
                (df_valid["wc_year"] >= year_range[0]) &
                (df_valid["wc_year"] <= year_range[1])
            ]

    min_elo = st.slider("Score ELO min affiche", 1400, 2100, 1400)
    df_valid = df_valid[df_valid["elo_rating"] >= min_elo]

# ─── Tabs ────────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["Score ELO vs Performance", "Upsets par edition", "Surprises notables"])

# --- Tab 1 : Scatter ---
with tab1:
    fig1 = px.scatter(
        df_valid,
        x="elo_rating",
        y="phase_score",
        color="confederation" if "confederation" in df_valid.columns else None,
        size_max=10,
        hover_name="team",
        hover_data={"wc_year": True, "final_stage_reached": True, "elo_rating": True},
        labels={
            "elo_rating": "Score ELO pre-tournoi",
            "phase_score": "Phase atteinte (0=Groupes, 5=Finale)",
            "confederation": "Confederation",
        },
        title="Score ELO vs Phase atteinte en Coupe du Monde",
        template="plotly_dark",
    )

    # Ligne de tendance
    if len(df_valid) > 5:
        z = np.polyfit(df_valid["elo_rating"], df_valid["phase_score"], 1)
        p = np.poly1d(z)
        x_line = np.linspace(df_valid["elo_rating"].min(), df_valid["elo_rating"].max(), 100)
        fig1.add_trace(go.Scatter(
            x=x_line, y=p(x_line),
            mode="lines", name="Tendance",
            line=dict(color="#f72585", dash="dash", width=2),
        ))

    fig1.update_layout(
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        title_font_color="#e8eaf6",
        yaxis=dict(
            tickvals=list(range(6)),
            ticktext=["Groupes", "1/16", "1/4", "1/2", "3e place", "Finale"],
        ),
    )
    st.plotly_chart(fig1, use_container_width=True)
    st.caption(
        f"Correlation de Pearson entre score ELO et phase atteinte : **{corr:.2f}**. "
        "Une valeur positive indique que les equipes avec un meilleur score tendent a aller plus loin."
    )

# --- Tab 2 : Upsets par edition ---
with tab2:
    if "wc_year" in df.columns:
        upset_threshold_elo = st.slider("Upset = Score ELO inferieur a :", 1500, 1900, 1750)
        upset_threshold_phase = st.selectbox(
            "Et ayant atteint au minimum :",
            options=["round of 16", "quarter-finals", "semi-finals", "final"],
            index=1,
        )
        phase_min_score = PHASE_SCORE.get(upset_threshold_phase, 2)

        upsets_custom = df[
            (df["elo_rating"] < upset_threshold_elo) &
            (df["phase_score"] >= phase_min_score)
        ]

        by_edition = upsets_custom.groupby("wc_year").size().reset_index(name="upsets")

        fig2 = px.bar(
            by_edition, x="wc_year", y="upsets",
            color="upsets",
            color_continuous_scale="Reds",
            labels={"wc_year": "Edition", "upsets": "Nombre d'upsets"},
            title=f"Upsets par edition (ELO < {upset_threshold_elo} + {upset_threshold_phase})",
            template="plotly_dark",
        )
        fig2.update_layout(
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            coloraxis_showscale=False, title_font_color="#e8eaf6",
        )
        st.plotly_chart(fig2, use_container_width=True)

# --- Tab 3 : Top upsets ---
with tab3:
    upsets_all = df_valid[(df_valid["elo_rating"] < 1800) & (df_valid["phase_score"] >= 2)].copy()
    upsets_all = upsets_all.sort_values("phase_score", ascending=False)
    upsets_all = add_flag_column(upsets_all)

    cols = [c for c in ["flag_team", "wc_year", "elo_rating", "final_stage_reached", "confederation"] if c in upsets_all.columns]
    display = upsets_all[cols].rename(columns={
        "flag_team": "Nation", "wc_year": "Annee", "elo_rating": "Score ELO",
        "final_stage_reached": "Phase atteinte", "confederation": "Confederation",
    }).reset_index(drop=True)

    st.dataframe(display, use_container_width=True, hide_index=True)
    st.caption(f"{len(display)} surprises detectees sur toute l'histoire de la Coupe du Monde.")
