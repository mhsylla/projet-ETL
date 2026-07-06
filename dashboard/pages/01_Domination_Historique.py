"""
Page 1 — Qui domine l'histoire de la Coupe du Monde ?

Classement des nations selon : titres, finales, demi-finales, participations,
taux de victoire.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from data_loader import load_all, get_team_alltime, get_win_rate, get_titles, add_flag_column, with_flag

st.set_page_config(page_title="Domination Historique", layout="wide")

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
data    = load_all()
alltime = get_team_alltime(data)
win_rate = get_win_rate(data)

# ─── Header ──────────────────────────────────────────────────────────────────
st.title("01 — Qui domine l'histoire de la Coupe du Monde ?")
st.markdown("Classement des nations selon leurs titres, finales, participations et taux de victoire sur toute l'histoire de la compétition.")
st.divider()

if alltime.empty:
    st.error("Données team_alltime_stats non disponibles.")
    st.stop()

# Merge win_rate si dispo
if not win_rate.empty and "win_rate" not in alltime.columns:
    alltime = alltime.merge(win_rate[["team", "win_rate"]], on="team", how="left")

# ─── Filtres sidebar ─────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Filtres")
    min_participations = st.slider("Participations minimum", 1, 20, 3)
    confederations = ["Toutes"] + sorted(alltime["confederation"].dropna().unique().tolist()) if "confederation" in alltime.columns else ["Toutes"]
    selected_conf = st.selectbox("Confederation", confederations)

df = alltime.copy()
if "total_wc_appearances" in df.columns:
    df = df[df["total_wc_appearances"] >= min_participations]
if selected_conf != "Toutes" and "confederation" in df.columns:
    df = df[df["confederation"] == selected_conf]

# ─── KPIs ────────────────────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)
c1.metric("Nations analysees", len(df))
if "titles" in df.columns:
    top_titles = df.loc[df["titles"].idxmax()]
    c2.metric("Plus de titres", f"{top_titles['team']} ({int(top_titles['titles'])})")
if "win_rate" in df.columns:
    top_wr = df.loc[df["win_rate"].idxmax()]
    c3.metric("Meilleur win rate", f"{top_wr['team']} ({top_wr['win_rate']:.1%})")
if "total_wc_appearances" in df.columns:
    top_app = df.loc[df["total_wc_appearances"].idxmax()]
    c4.metric("Plus de participations", f"{top_app['team']} ({int(top_app['total_wc_appearances'])})")

st.divider()

# ─── Visualisations ──────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs(["Titres & Finales", "Taux de Victoire", "Vue d'ensemble", "Tableau complet"])

# --- Tab 1 : Titres & Finales ---
with tab1:
    col_a, col_b = st.columns(2)

    with col_a:
        if "titles" in df.columns:
            top15_titles = df.nlargest(15, "titles")[["team", "titles", "finals_reached", "semis_reached"]].fillna(0)
            top15_titles = add_flag_column(top15_titles)
            fig = go.Figure()
            fig.add_trace(go.Bar(
                name="Titres", x=top15_titles["flag_team"], y=top15_titles["titles"],
                marker_color="#7c83f5", marker_line_width=0,
            ))
            fig.add_trace(go.Bar(
                name="Finales", x=top15_titles["flag_team"], y=top15_titles["finals_reached"],
                marker_color="#f72585", marker_line_width=0,
            ))
            fig.add_trace(go.Bar(
                name="Demi-finales", x=top15_titles["flag_team"], y=top15_titles["semis_reached"],
                marker_color="#4cc9f0", marker_line_width=0,
            ))
            fig.update_layout(
                title="Top 15 — Titres, Finales et Demi-finales",
                barmode="group", template="plotly_dark",
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                legend=dict(orientation="h", y=-0.2),
                title_font_color="#e8eaf6",
                margin=dict(t=50, b=10),
                xaxis=dict(tickfont=dict(size=13)),
            )
            st.plotly_chart(fig, use_container_width=True)

    with col_b:
        if "titles" in df.columns and "total_wc_appearances" in df.columns:
            top15 = df.nlargest(15, "titles")[["team", "titles", "total_wc_appearances", "confederation"]].fillna(0)
            fig2 = px.scatter(
                top15,
                x="total_wc_appearances", y="titles",
                size="titles", color="confederation",
                hover_name="team",
                labels={"total_wc_appearances": "Participations", "titles": "Titres"},
                title="Participations vs Titres (Top 15)",
                template="plotly_dark",
                size_max=50,
            )
            fig2.update_layout(
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                title_font_color="#e8eaf6",
            )
            st.plotly_chart(fig2, use_container_width=True)

# --- Tab 2 : Taux de victoire ---
with tab2:
    if "win_rate" in df.columns:
        top20_wr = df[df["total_matches"] >= 10].nlargest(20, "win_rate").copy()
        top20_wr = add_flag_column(top20_wr)
        top20_wr_sorted = top20_wr.sort_values("win_rate", ascending=True)
        fig3 = px.bar(
            top20_wr_sorted,
            x="win_rate", y="flag_team",
            orientation="h",
            color="win_rate",
            color_continuous_scale="Blues",
            labels={"win_rate": "Taux de victoire", "flag_team": "Nation"},
            title="Top 20 — Taux de victoire (min. 10 matchs)",
            template="plotly_dark",
            text=top20_wr_sorted["win_rate"].map(lambda x: f"{x:.1%}"),
        )
        fig3.update_layout(
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            coloraxis_showscale=False, title_font_color="#e8eaf6",
            yaxis=dict(tickfont=dict(size=13)),
        )
        fig3.update_traces(textposition="outside")
        st.plotly_chart(fig3, use_container_width=True)

# --- Tab 3 : Bubble chart global ---
with tab3:
    if {"win_rate", "titles", "total_wc_appearances", "confederation"}.issubset(df.columns):
        df_bubble = df[df["total_wc_appearances"] >= min_participations].copy()
        df_bubble["titles_disp"] = df_bubble["titles"].fillna(0)
        fig4 = px.scatter(
            df_bubble,
            x="total_wc_appearances",
            y="win_rate",
            size=df_bubble["titles_disp"].clip(lower=0.5),
            color="confederation",
            hover_name="team",
            hover_data={"titles": True, "total_wc_appearances": True, "win_rate": ":.1%"},
            labels={
                "total_wc_appearances": "Participations",
                "win_rate": "Taux de victoire",
                "confederation": "Confederation",
            },
            title="Vue d'ensemble — Toutes les nations (taille = titres)",
            template="plotly_dark",
            size_max=60,
        )
        fig4.update_layout(
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            title_font_color="#e8eaf6",
        )
        st.plotly_chart(fig4, use_container_width=True)

# --- Tab 4 : Tableau complet ---
with tab4:
    cols_to_show = [c for c in ["team", "confederation", "total_wc_appearances", "titles",
                                 "finals_reached", "semis_reached", "quarters_reached",
                                 "total_wins", "total_matches", "win_rate",
                                 "total_goals_scored", "best_finish"] if c in df.columns]
    display_df = df[cols_to_show].sort_values("titles", ascending=False).reset_index(drop=True)
    display_df = add_flag_column(display_df)

    if "win_rate" in display_df.columns:
        display_df["win_rate"] = display_df["win_rate"].map(lambda x: f"{x:.1%}" if pd.notna(x) else "N/A")

    # Reordonne pour mettre le drapeau en premier
    ordered_cols = ["flag_team"] + [c for c in display_df.columns if c not in ["flag_team", "team"]]
    display_df = display_df[ordered_cols].rename(columns={"flag_team": "Nation"})
    st.dataframe(display_df, use_container_width=True, hide_index=True)
