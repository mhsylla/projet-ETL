"""
Page 4 — Cycles de domination

Visualise les periodes de domination de chaque nation en Coupe du Monde.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from data_loader import load_all, get_team_appearances, PHASE_ORDER, PHASE_SCORE

st.set_page_config(page_title="Cycles de Domination", layout="wide")

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

st.title("04 — Existe-t-il des cycles de domination ?")
st.markdown("Visualisation des periodes ou certaines nations dominent la Coupe du Monde avant de laisser place a de nouvelles generations.")
st.divider()

if appearances.empty or not {"team", "wc_year", "final_stage_reached"}.issubset(appearances.columns):
    st.error("Donnees insuffisantes pour cette analyse.")
    st.stop()

df = appearances.copy()

# Score numerique de la phase atteinte
df["phase_lower"] = df["final_stage_reached"].astype(str).str.lower().str.strip()
df["phase_score"] = df["phase_lower"].map(PHASE_SCORE)

# Remplir les phases inconnues avec 0
df["phase_score"] = df["phase_score"].fillna(0)

# ─── Sidebar ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Filtres")
    all_teams = sorted(df["team"].dropna().unique().tolist())

    # Top 15 par défaut = ceux avec le plus de participations
    top_teams_default = (
        df.groupby("team")["wc_year"].count()
        .nlargest(15).index.tolist()
    )
    selected_teams = st.multiselect(
        "Nations a afficher (heatmap)",
        options=all_teams,
        default=top_teams_default,
        max_selections=25,
    )

    year_range = st.slider(
        "Periode",
        int(df["wc_year"].min()), int(df["wc_year"].max()),
        (1950, int(df["wc_year"].max()))
    )

df_filtered = df[
    (df["team"].isin(selected_teams)) &
    (df["wc_year"] >= year_range[0]) &
    (df["wc_year"] <= year_range[1])
]

# ─── Tabs ────────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["Heatmap des performances", "Evolution du Win Rate", "Domination par decennie"])

# --- Tab 1 : Heatmap ---
with tab1:
    if not df_filtered.empty:
        pivot = df_filtered.pivot_table(
            index="team", columns="wc_year", values="phase_score", aggfunc="max"
        ).fillna(-1)

        # Labels pour le hover
        pivot_labels = df_filtered.pivot_table(
            index="team", columns="wc_year", values="final_stage_reached", aggfunc="first"
        ).fillna("Non qualifie")

        fig1 = go.Figure(data=go.Heatmap(
            z=pivot.values,
            x=pivot.columns.tolist(),
            y=pivot.index.tolist(),
            customdata=pivot_labels.values,
            hovertemplate="<b>%{y}</b><br>Annee: %{x}<br>Phase: %{customdata}<extra></extra>",
            colorscale=[
                [0.0, "#1a1d2e"],
                [0.2, "#3a0ca3"],
                [0.4, "#4361ee"],
                [0.6, "#4cc9f0"],
                [0.8, "#7c83f5"],
                [1.0, "#f72585"],
            ],
            zmin=-1, zmax=5,
            colorbar=dict(
                title="Phase",
                tickvals=[-1, 0, 1, 2, 3, 4, 5],
                ticktext=["Absent", "Groupes", "1/16", "1/4", "1/2", "3e place", "Finale"],
                tickfont=dict(color="#e8eaf6"),
            ),
        ))
        fig1.update_layout(
            title="Heatmap : Phase atteinte par nation et par edition",
            xaxis_title="Annee",
            yaxis_title="Nation",
            template="plotly_dark",
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            title_font_color="#e8eaf6",
            height=max(400, len(selected_teams) * 28),
            yaxis=dict(tickfont=dict(size=10)),
        )
        st.plotly_chart(fig1, use_container_width=True)

        st.caption(
            "Lecture : chaque cellule indique la phase la plus avancee atteinte par la nation cette annee-la. "
            "Les cellules sombres signifient que l'equipe n'etait pas qualifiee."
        )

# --- Tab 2 : Evolution win rate ---
with tab2:
    if "wins" in df.columns and "matches_played" in df.columns:
        df["win_rate_ed"] = df.apply(
            lambda r: r["wins"] / r["matches_played"] if r["matches_played"] > 0 else 0, axis=1
        )

        df_wr = df[
            (df["team"].isin(selected_teams)) &
            (df["wc_year"] >= year_range[0]) &
            (df["wc_year"] <= year_range[1])
        ]

        fig2 = px.line(
            df_wr, x="wc_year", y="win_rate_ed", color="team",
            markers=True,
            labels={"wc_year": "Annee", "win_rate_ed": "Taux de victoire", "team": "Nation"},
            title="Evolution du taux de victoire par nation",
            template="plotly_dark",
        )
        fig2.update_layout(
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            title_font_color="#e8eaf6", yaxis_tickformat=".0%",
        )
        st.plotly_chart(fig2, use_container_width=True)

# --- Tab 3 : Domination par decennie ---
with tab3:
    if "decade" in df.columns and "wins" in df.columns:
        # Top equipe par decennie (en nombre de victoires cumulees)
        decade_dom = df.groupby(["decade", "team"])["wins"].sum().reset_index()
        decade_dom = decade_dom.sort_values(["decade", "wins"], ascending=[True, False])
        decade_dom["rank"] = decade_dom.groupby("decade")["wins"].rank(ascending=False, method="first")
        top_per_decade = decade_dom[decade_dom["rank"] <= 5]

        fig3 = px.bar(
            top_per_decade,
            x="decade",
            y="wins",
            color="team",
            barmode="group",
            labels={"decade": "Decennie", "wins": "Victoires cumulees", "team": "Nation"},
            title="Top 5 nations par decennie (victoires cumulees)",
            template="plotly_dark",
        )
        fig3.update_layout(
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            title_font_color="#e8eaf6",
            xaxis=dict(tickvals=top_per_decade["decade"].unique(),
                       ticktext=[f"{d}s" for d in sorted(top_per_decade["decade"].unique())]),
        )
        st.plotly_chart(fig3, use_container_width=True)
