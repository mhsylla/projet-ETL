"""
Page 7 — Quels facteurs expliquent le mieux les succes ?

Analyse de l'influence de l'experience, l'efficacite offensive, la solidite
defensive et les performances recentes.
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
from data_loader import load_all, get_team_alltime, get_win_rate, get_ranking, add_flag_column, with_flag

st.set_page_config(page_title="Facteurs de Succes", layout="wide")

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
win_r   = get_win_rate(data)
ranking = get_ranking(data)

st.title("07 — Quels facteurs expliquent le mieux les succes ?")
st.markdown(
    "Analyse de l'influence de l'experience, de l'efficacite offensive, de la solidite "
    "defensive et du classement FIFA sur les titres remportes."
)
st.divider()

if alltime.empty:
    st.error("Donnees alltime non disponibles.")
    st.stop()

# Merge
df = alltime.copy()
if not win_r.empty and "win_rate" not in df.columns:
    df = df.merge(win_r[["team", "win_rate"]], on="team", how="left")

# Calcul goals/match
if "total_goals_scored" in df.columns and "total_matches" in df.columns:
    df["goals_per_match"] = df.apply(
        lambda r: r["total_goals_scored"] / r["total_matches"] if r["total_matches"] > 0 else 0, axis=1
    )
if "total_goals_conceded" in df.columns and "total_matches" in df.columns:
    df["conceded_per_match"] = df.apply(
        lambda r: r["total_goals_conceded"] / r["total_matches"] if r["total_matches"] > 0 else 0, axis=1
    )

# Merge ranking
if not ranking.empty and "rank" in ranking.columns:
    df = df.merge(ranking[["team", "rank"]], on="team", how="left")
    df = df.rename(columns={"rank": "fifa_ranking"})

# Filtre min matchs
df_full = df[df["total_matches"] >= 5].copy()

# ─── Sidebar ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Filtres")
    min_matches = st.slider("Matchs minimum joues", 5, 50, 10)
    df_full = df[df["total_matches"] >= min_matches].copy()

    if "confederation" in df_full.columns:
        confs = ["Toutes"] + sorted(df_full["confederation"].dropna().unique().tolist())
        selected_conf = st.selectbox("Confederation", confs)
        if selected_conf != "Toutes":
            df_full = df_full[df_full["confederation"] == selected_conf]

# ─── KPIs ────────────────────────────────────────────────────────────────────
numeric_cols = ["titles", "win_rate", "goals_per_match", "conceded_per_match",
                "total_wc_appearances", "fifa_ranking"]
numeric_cols = [c for c in numeric_cols if c in df_full.columns]

c1, c2, c3, c4 = st.columns(4)
if "goals_per_match" in df_full.columns:
    best_attack = df_full.loc[df_full["goals_per_match"].idxmax()]
    c1.metric("Meilleure attaque", f"{best_attack['team']} ({best_attack['goals_per_match']:.2f} buts/m)")
if "conceded_per_match" in df_full.columns:
    best_def = df_full.loc[df_full["conceded_per_match"].idxmin()]
    c2.metric("Meilleure defense", f"{best_def['team']} ({best_def['conceded_per_match']:.2f} enc./m)")
if "total_wc_appearances" in df_full.columns:
    most_exp = df_full.loc[df_full["total_wc_appearances"].idxmax()]
    c3.metric("Plus grande experience", f"{most_exp['team']} ({int(most_exp['total_wc_appearances'])} CdM)")
if "win_rate" in df_full.columns:
    best_wr = df_full.loc[df_full["win_rate"].idxmax()]
    c4.metric("Meilleur win rate", f"{best_wr['team']} ({best_wr['win_rate']:.1%})")

st.divider()

# ─── Tabs ────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "Correlations", "Experience vs Succes",
    "Attaque vs Defense", "Top 10 par indicateur"
])

# --- Tab 1 : Heatmap de correlation ---
with tab1:
    num_df = df_full[numeric_cols].dropna()

    if len(num_df) > 3:
        corr_matrix = num_df.corr()

        readable_labels = {
            "titles": "Titres",
            "win_rate": "Win Rate",
            "goals_per_match": "Buts/match",
            "conceded_per_match": "Enc./match",
            "total_wc_appearances": "Participations",
            "fifa_ranking": "Rang FIFA",
        }
        corr_matrix.columns = [readable_labels.get(c, c) for c in corr_matrix.columns]
        corr_matrix.index   = [readable_labels.get(c, c) for c in corr_matrix.index]

        fig1 = go.Figure(data=go.Heatmap(
            z=corr_matrix.values,
            x=corr_matrix.columns.tolist(),
            y=corr_matrix.index.tolist(),
            colorscale="RdBu",
            zmid=0, zmin=-1, zmax=1,
            text=corr_matrix.values.round(2),
            texttemplate="%{text}",
            hovertemplate="%{y} / %{x}: %{z:.2f}<extra></extra>",
        ))
        fig1.update_layout(
            title="Matrice de correlation entre les indicateurs",
            template="plotly_dark",
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            title_font_color="#e8eaf6",
            height=450,
        )
        st.plotly_chart(fig1, use_container_width=True)
        st.caption(
            "Lecture : une valeur proche de +1 indique une forte correlation positive, "
            "proche de -1 une forte correlation negative, proche de 0 = pas de correlation."
        )

# --- Tab 2 : Experience vs Succes ---
with tab2:
    col_a, col_b = st.columns(2)

    with col_a:
        if {"total_wc_appearances", "titles"}.issubset(df_full.columns):
            fig2 = px.scatter(
                df_full,
                x="total_wc_appearances", y="titles",
                hover_name="team",
                color="confederation" if "confederation" in df_full.columns else None,
                labels={"total_wc_appearances": "Participations en CdM", "titles": "Titres"},
                title="Experience (participations) vs Titres",
                template="plotly_dark",
            )
            # Ligne de tendance manuelle
            _x = df_full["total_wc_appearances"].dropna()
            _y = df_full["titles"].dropna()
            if len(_x) == len(_y) and len(_x) > 2:
                _z = np.polyfit(_x, _y, 1)
                _p = np.poly1d(_z)
                fig2.add_trace(go.Scatter(
                    x=sorted(_x), y=_p(sorted(_x)),
                    mode="lines", name="Tendance",
                    line=dict(color="#f72585", dash="dash", width=1.5),
                ))
            fig2.update_layout(
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                title_font_color="#e8eaf6",
            )
            st.plotly_chart(fig2, use_container_width=True)

    with col_b:
        if {"total_wc_appearances", "win_rate"}.issubset(df_full.columns):
            fig3 = px.scatter(
                df_full,
                x="total_wc_appearances", y="win_rate",
                hover_name="team",
                color="titles" if "titles" in df_full.columns else None,
                color_continuous_scale="Blues",
                labels={"total_wc_appearances": "Participations", "win_rate": "Win Rate"},
                title="Experience vs Win Rate",
                template="plotly_dark",
            )
            # Ligne de tendance manuelle
            _x = df_full["total_wc_appearances"].dropna()
            _y = df_full.loc[_x.index, "win_rate"].dropna()
            if len(_x) == len(_y) and len(_x) > 2:
                _z = np.polyfit(_x, _y, 1)
                _p = np.poly1d(_z)
                fig3.add_trace(go.Scatter(
                    x=sorted(_x), y=_p(sorted(_x)),
                    mode="lines", name="Tendance",
                    line=dict(color="#f72585", dash="dash", width=1.5),
                ))
            fig3.update_layout(
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                title_font_color="#e8eaf6", yaxis_tickformat=".0%",
            )
            st.plotly_chart(fig3, use_container_width=True)

# --- Tab 3 : Attaque vs Defense ---
with tab3:
    if {"goals_per_match", "conceded_per_match"}.issubset(df_full.columns):
        fig4 = px.scatter(
            df_full,
            x="conceded_per_match", y="goals_per_match",
            hover_name="team",
            size="titles" if "titles" in df_full.columns else None,
            color="win_rate" if "win_rate" in df_full.columns else None,
            color_continuous_scale="Viridis",
            labels={
                "conceded_per_match": "Buts encaisses / match (defense)",
                "goals_per_match": "Buts marques / match (attaque)",
                "win_rate": "Win Rate",
            },
            title="Profil offensif / defensif (taille = titres, couleur = win rate)",
            template="plotly_dark",
            size_max=40,
        )
        # Lignes de references (moyenne)
        fig4.add_hline(
            y=df_full["goals_per_match"].mean(), line_dash="dash",
            line_color="rgba(255,255,255,0.3)",
            annotation_text="Moy. attaque",
        )
        fig4.add_vline(
            x=df_full["conceded_per_match"].mean(), line_dash="dash",
            line_color="rgba(255,255,255,0.3)",
            annotation_text="Moy. defense",
        )
        fig4.update_layout(
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            title_font_color="#e8eaf6",
        )
        st.plotly_chart(fig4, use_container_width=True)
        st.caption(
            "Quadrant ideal : haut-gauche (beaucoup de buts marques, peu encaisses). "
            "Les equipes titrées (grosses bulles) y sont concentrées."
        )

# --- Tab 4 : Classements ---
with tab4:
    indicator = st.selectbox(
        "Indicateur",
        options=[c for c in ["titles", "win_rate", "goals_per_match", "conceded_per_match",
                              "total_wc_appearances", "total_wins"] if c in df_full.columns],
        format_func=lambda x: {
            "titles": "Titres",
            "win_rate": "Taux de victoire",
            "goals_per_match": "Buts marques / match",
            "conceded_per_match": "Buts encaisses / match (moins = mieux)",
            "total_wc_appearances": "Participations en CdM",
            "total_wins": "Victoires totales",
        }.get(x, x)
    )

    ascending = indicator == "conceded_per_match"
    top10 = df_full.nsmallest(10, indicator) if ascending else df_full.nlargest(10, indicator)
    top10 = top10.sort_values(indicator, ascending=ascending).copy()
    top10 = add_flag_column(top10)

    fig5 = px.bar(
        top10,
        x=indicator, y="flag_team",
        orientation="h",
        color=indicator,
        color_continuous_scale="Blues" if not ascending else "Reds_r",
        labels={"flag_team": "Nation", indicator: indicator},
        title=f"Top 10 — {indicator}",
        template="plotly_dark",
    )
    fig5.update_layout(
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        coloraxis_showscale=False, title_font_color="#e8eaf6",
        yaxis=dict(tickfont=dict(size=13)),
    )
    if indicator == "win_rate":
        fig5.update_layout(xaxis_tickformat=".0%")
    st.plotly_chart(fig5, use_container_width=True)
