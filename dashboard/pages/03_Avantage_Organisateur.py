"""
Page 3 — Quel est l'impact du pays organisateur ?

Compare les performances des equipes hotes vs visiteuses.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from data_loader import load_all, get_team_appearances, get_worldcup, add_flag_column, with_flag

st.set_page_config(page_title="Avantage Organisateur", layout="wide")

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
worldcup    = get_worldcup(data)

st.title("03 — Quel est l'impact du pays organisateur ?")
st.markdown("Les équipes jouant chez elles obtiennent-elles de meilleurs résultats ? Analyse historique de l'effet du pays hôte.")
st.divider()

if appearances.empty or "host_nation" not in appearances.columns:
    st.error("Donnees team_appearances avec colonne host_nation non disponibles.")
    st.stop()

df = appearances.copy()

# Nettoyage host_nation
df["is_host"] = df["host_nation"].astype(str).str.strip().str.lower().isin(["true", "yes", "1", "oui"])

# Phase score (calcul simplifie via wins/draws/losses)
if "wins" in df.columns and "matches_played" in df.columns:
    df["win_rate"] = df.apply(
        lambda r: r["wins"] / r["matches_played"] if r["matches_played"] > 0 else 0, axis=1
    )

# ─── KPIs globaux ────────────────────────────────────────────────────────────
host_df    = df[df["is_host"]]
visitor_df = df[~df["is_host"]]

col1, col2, col3, col4 = st.columns(4)
col1.metric("Editions avec hote participant", len(host_df))

if "win_rate" in df.columns:
    host_wr    = host_df["win_rate"].mean()
    visitor_wr = visitor_df["win_rate"].mean()
    delta = host_wr - visitor_wr
    col2.metric("Win rate — Hotes",    f"{host_wr:.1%}")
    col3.metric("Win rate — Visiteurs", f"{visitor_wr:.1%}")
    col4.metric("Avantage hote",       f"+{delta:.1%}" if delta > 0 else f"{delta:.1%}",
                delta=f"{delta:.1%}", delta_color="normal")

st.divider()

# ─── Tabs ────────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["Hote vs Visiteur", "Performances des hotes", "Par edition"])

# --- Tab 1 : Comparaison globale ---
with tab1:
    col_a, col_b = st.columns(2)

    with col_a:
        if "win_rate" in df.columns:
            compare = pd.DataFrame({
                "Statut": ["Pays hote", "Pays visiteur"],
                "Win Rate": [host_df["win_rate"].mean(), visitor_df["win_rate"].mean()],
            })
            fig1 = px.bar(
                compare, x="Statut", y="Win Rate",
                color="Statut",
                color_discrete_sequence=["#7c83f5", "#f72585"],
                title="Taux de victoire : Hote vs Visiteur",
                template="plotly_dark",
                text=compare["Win Rate"].map(lambda x: f"{x:.1%}"),
            )
            fig1.update_layout(
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                showlegend=False, title_font_color="#e8eaf6",
                yaxis_tickformat=".0%",
            )
            fig1.update_traces(textposition="outside")
            st.plotly_chart(fig1, use_container_width=True)

    with col_b:
        if all(c in df.columns for c in ["wins", "draws", "losses"]):
            host_agg = host_df[["wins", "draws", "losses"]].mean()
            visit_agg = visitor_df[["wins", "draws", "losses"]].mean()

            fig2 = go.Figure()
            metrics = ["Victoires", "Nuls", "Defaites"]
            colors_h = ["#7c83f5", "#4cc9f0", "#f72585"]

            fig2.add_trace(go.Bar(
                name="Hote", x=metrics,
                y=[host_agg["wins"], host_agg["draws"], host_agg["losses"]],
                marker_color="#7c83f5",
            ))
            fig2.add_trace(go.Bar(
                name="Visiteur", x=metrics,
                y=[visit_agg["wins"], visit_agg["draws"], visit_agg["losses"]],
                marker_color="#f72585",
            ))
            fig2.update_layout(
                title="V/N/D moyens par equipe (par participation)",
                barmode="group", template="plotly_dark",
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                title_font_color="#e8eaf6",
            )
            st.plotly_chart(fig2, use_container_width=True)

# --- Tab 2 : Tableau des performances des hotes ---
with tab2:
    if not host_df.empty:
        cols = [c for c in ["team", "wc_year", "wins", "draws", "losses",
                             "goals_scored", "goals_conceded", "final_stage_reached",
                             "win_rate"] if c in host_df.columns]
        display = host_df[cols].sort_values("wc_year", ascending=False).reset_index(drop=True)
        display = add_flag_column(display)

        if "win_rate" in display.columns:
            display["win_rate"] = display["win_rate"].map(lambda x: f"{x:.1%}")

        display = display.rename(columns={
            "flag_team": "Pays hote", "wc_year": "Annee",
            "wins": "Victoires", "draws": "Nuls", "losses": "Defaites",
            "goals_scored": "Buts marques", "goals_conceded": "Buts encaisses",
            "final_stage_reached": "Phase atteinte", "win_rate": "Win rate",
        })
        ordered = ["Pays hote"] + [c for c in display.columns if c not in ["Pays hote", "team"]]
        st.dataframe(display[ordered], use_container_width=True, hide_index=True)

        # Bar chart phase atteinte par hote
        if "Phase atteinte" in display.columns:
            phase_counts = display["Phase atteinte"].value_counts().reset_index()
            phase_counts.columns = ["Phase", "Nombre"]
            fig3 = px.bar(
                phase_counts, x="Phase", y="Nombre",
                color="Nombre", color_continuous_scale="Blues",
                title="Phases atteintes par les pays hotes",
                template="plotly_dark",
            )
            fig3.update_layout(
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                coloraxis_showscale=False, title_font_color="#e8eaf6",
            )
            st.plotly_chart(fig3, use_container_width=True)

# --- Tab 3 : Evolution par edition ---
with tab3:
    if "wc_year" in df.columns and "win_rate" in df.columns:
        yearly = df.groupby(["wc_year", "is_host"])["win_rate"].mean().reset_index()
        yearly["Statut"] = yearly["is_host"].map({True: "Hote", False: "Visiteur"})

        fig4 = px.line(
            yearly, x="wc_year", y="win_rate", color="Statut",
            color_discrete_map={"Hote": "#7c83f5", "Visiteur": "#f72585"},
            markers=True,
            labels={"wc_year": "Annee", "win_rate": "Taux de victoire moyen"},
            title="Evolution du win rate : Hote vs Visiteur par edition",
            template="plotly_dark",
        )
        fig4.update_layout(
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            title_font_color="#e8eaf6", yaxis_tickformat=".0%",
        )
        st.plotly_chart(fig4, use_container_width=True)
