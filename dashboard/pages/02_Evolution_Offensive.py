"""
Page 2 — Le football est-il devenu plus offensif ?

Evolution de la moyenne de buts par match par edition (1930-2022),
repartition des scores par decennie.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from data_loader import load_all, get_matches, get_worldcup

st.set_page_config(page_title="Evolution Offensive", layout="wide")

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
data     = load_all()
matches  = get_matches(data)
worldcup = get_worldcup(data)

st.title("02 — Le football est-il devenu plus offensif ?")
st.markdown("Evolution de la production de buts en Coupe du Monde de 1930 à 2022, par édition et par décennie.")
st.divider()

if matches.empty or not {"home_score", "away_score", "year"}.issubset(matches.columns):
    st.error("Données de matchs insuffisantes pour cette analyse.")
    st.stop()

# Nettoyage
df = matches.dropna(subset=["home_score", "away_score", "year"]).copy()
df["total_goals"] = df["home_score"] + df["away_score"]
df["year"] = df["year"].astype(int)

# ─── Par edition ─────────────────────────────────────────────────────────────
by_year = df.groupby("year").agg(
    goals_per_match=("total_goals", "mean"),
    total_goals=("total_goals", "sum"),
    nb_matches=("total_goals", "count"),
).reset_index()

# ─── Par decennie ────────────────────────────────────────────────────────────
df["decade"] = (df["year"] // 10 * 10).astype(int)
by_decade = df.groupby("decade").agg(
    goals_per_match=("total_goals", "mean"),
    home_goals=("home_score", "mean"),
    away_goals=("away_score", "mean"),
    nb_matches=("total_goals", "count"),
).reset_index()

# ─── KPIs ────────────────────────────────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)
col1.metric("Buts/match — 1930s", f"{by_decade[by_decade['decade']==1930]['goals_per_match'].values[0]:.2f}" if 1930 in by_decade['decade'].values else "N/A")
col2.metric("Buts/match — 1990s", f"{by_decade[by_decade['decade']==1990]['goals_per_match'].values[0]:.2f}" if 1990 in by_decade['decade'].values else "N/A")
col3.metric("Buts/match — 2010s", f"{by_decade[by_decade['decade']==2010]['goals_per_match'].values[0]:.2f}" if 2010 in by_decade['decade'].values else "N/A")
max_row = by_year.loc[by_year["goals_per_match"].idxmax()]
col4.metric("Edition la + offensive", f"{int(max_row['year'])} ({max_row['goals_per_match']:.2f} buts/match)")

st.divider()

# ─── Graphiques ──────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["Evolution par edition", "Buts par decennie", "Distribution des scores"])

# --- Tab 1 ---
with tab1:
    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(
        x=by_year["year"], y=by_year["goals_per_match"],
        mode="lines+markers",
        name="Buts/match",
        line=dict(color="#7c83f5", width=2.5),
        marker=dict(size=7, color="#7c83f5"),
        fill="tozeroy",
        fillcolor="rgba(124, 131, 245, 0.1)",
    ))
    # Moyenne globale
    global_mean = df["total_goals"].mean()
    fig1.add_hline(
        y=global_mean, line_dash="dash", line_color="#f72585",
        annotation_text=f"Moyenne globale: {global_mean:.2f}",
        annotation_position="top right",
    )
    fig1.update_layout(
        title="Evolution des buts par match par edition (1930–2022)",
        xaxis_title="Annee",
        yaxis_title="Buts par match",
        template="plotly_dark",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        title_font_color="#e8eaf6",
        hovermode="x unified",
    )
    st.plotly_chart(fig1, use_container_width=True)

    st.dataframe(
        by_year.rename(columns={
            "year": "Annee",
            "goals_per_match": "Buts/match",
            "total_goals": "Buts totaux",
            "nb_matches": "Matchs",
        }).assign(**{"Buts/match": by_year["goals_per_match"].round(2)}),
        use_container_width=True, hide_index=True,
    )

# --- Tab 2 ---
with tab2:
    fig2 = go.Figure()
    fig2.add_trace(go.Bar(
        name="Buts a domicile",
        x=by_decade["decade"].astype(str) + "s",
        y=by_decade["home_goals"].round(2),
        marker_color="#7c83f5",
    ))
    fig2.add_trace(go.Bar(
        name="Buts a l'exterieur",
        x=by_decade["decade"].astype(str) + "s",
        y=by_decade["away_goals"].round(2),
        marker_color="#f72585",
    ))
    fig2.update_layout(
        title="Buts a domicile vs a l'exterieur par decennie",
        xaxis_title="Decennie",
        yaxis_title="Moyenne de buts par match",
        barmode="stack",
        template="plotly_dark",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        title_font_color="#e8eaf6",
        legend=dict(orientation="h", y=-0.2),
    )
    st.plotly_chart(fig2, use_container_width=True)

# --- Tab 3 ---
with tab3:
    with st.sidebar:
        st.header("Filtres")
        decades_available = sorted(df["decade"].unique().tolist())
        selected_decades = st.multiselect(
            "Decennies a comparer",
            options=decades_available,
            default=decades_available,
            format_func=lambda x: f"{x}s",
        )

    df_filtered = df[df["decade"].isin(selected_decades)] if selected_decades else df

    fig3 = px.histogram(
        df_filtered,
        x="total_goals",
        color=df_filtered["decade"].astype(str) + "s",
        barmode="overlay",
        nbins=15,
        opacity=0.75,
        labels={"total_goals": "Buts par match", "color": "Decennie"},
        title="Distribution du nombre de buts par match selon la decennie",
        template="plotly_dark",
    )
    fig3.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        title_font_color="#e8eaf6",
    )
    st.plotly_chart(fig3, use_container_width=True)

    # Scores les plus frequents
    score_freq = df_filtered.groupby(["home_score", "away_score"]).size().reset_index(name="count")
    score_freq["score"] = score_freq["home_score"].astype(int).astype(str) + " - " + score_freq["away_score"].astype(int).astype(str)
    top_scores = score_freq.nlargest(10, "count")

    fig4 = px.bar(
        top_scores,
        x="score", y="count",
        color="count",
        color_continuous_scale="Blues",
        title="Top 10 des scores les plus frequents",
        labels={"score": "Score", "count": "Nombre de matchs"},
        template="plotly_dark",
    )
    fig4.update_layout(
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        coloraxis_showscale=False, title_font_color="#e8eaf6",
    )
    st.plotly_chart(fig4, use_container_width=True)
