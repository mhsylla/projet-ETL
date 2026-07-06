"""
Page 6 — Quels continents progressent le plus ?

Compare les performances des confederations (UEFA, CONMEBOL, CAF, AFC, CONCACAF)
au fil des editions.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from data_loader import load_all, get_team_appearances, get_team_alltime, CONF_COLORS, PHASE_SCORE

st.set_page_config(page_title="Performances par Continent", layout="wide")

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
alltime     = get_team_alltime(data)

st.title("06 — Quels continents progressent le plus ?")
st.markdown("Comparaison des performances de l'Europe, l'Amérique du Sud, l'Afrique, l'Asie et la CONCACAF au fil des éditions.")
st.divider()

if appearances.empty or "confederation" not in appearances.columns:
    st.error("Donnees insuffisantes pour cette analyse.")
    st.stop()

df = appearances.copy()
df["phase_lower"] = df["final_stage_reached"].astype(str).str.lower().str.strip()
df["phase_score"] = df["phase_lower"].map(PHASE_SCORE).fillna(0)

if "wins" in df.columns and "matches_played" in df.columns:
    df["win_rate"] = df.apply(
        lambda r: r["wins"] / r["matches_played"] if r["matches_played"] > 0 else 0, axis=1
    )

confs = sorted(df["confederation"].dropna().unique().tolist())

# ─── Sidebar ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Filtres")
    selected_confs = st.multiselect("Confederations", confs, default=confs)
    if "wc_year" in df.columns:
        year_range = st.slider(
            "Periode",
            int(df["wc_year"].min()), int(df["wc_year"].max()),
            (1950, int(df["wc_year"].max())),
        )
    else:
        year_range = (1950, 2022)

df_f = df[
    df["confederation"].isin(selected_confs) &
    (df["wc_year"] >= year_range[0]) &
    (df["wc_year"] <= year_range[1])
]

# ─── KPIs ────────────────────────────────────────────────────────────────────
cols = st.columns(len(selected_confs) if selected_confs else 1)
for i, conf in enumerate(selected_confs):
    conf_df = df_f[df_f["confederation"] == conf]
    total_part = len(conf_df)
    cols[i].metric(conf, f"{total_part} participations")

st.divider()

# ─── Tabs ────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "Titres par confederation",
    "Win rate par decade",
    "Phases atteintes",
    "Participations par edition",
])

# --- Tab 1 : Titres par confederation ---
with tab1:
    col_a, col_b = st.columns(2)

    with col_a:
        if not alltime.empty and "confederation" in alltime.columns and "titles" in alltime.columns:
            titles_by_conf = alltime.groupby("confederation")["titles"].sum().reset_index()
            titles_by_conf = titles_by_conf[titles_by_conf["confederation"].isin(selected_confs)]
            titles_by_conf = titles_by_conf.sort_values("titles", ascending=False)

            color_map = {c: CONF_COLORS.get(c, "#888888") for c in titles_by_conf["confederation"]}

            fig1 = px.pie(
                titles_by_conf,
                names="confederation",
                values="titles",
                color="confederation",
                color_discrete_map=color_map,
                title="Repartition des titres par confederation",
                template="plotly_dark",
                hole=0.45,
            )
            fig1.update_layout(
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                title_font_color="#e8eaf6",
            )
            st.plotly_chart(fig1, use_container_width=True)

    with col_b:
        if not alltime.empty and {"confederation", "finals_reached", "semis_reached"}.issubset(alltime.columns):
            phases_conf = alltime[alltime["confederation"].isin(selected_confs)].groupby("confederation").agg(
                Finales=("finals_reached", "sum"),
                Demi_finales=("semis_reached", "sum"),
                Quarts=("quarters_reached", "sum") if "quarters_reached" in alltime.columns else ("finals_reached", "count"),
            ).reset_index()

            fig2 = go.Figure()
            metrics_map = {"Finales": "#f72585", "Demi_finales": "#7c83f5", "Quarts": "#4cc9f0"}
            for metric, color in metrics_map.items():
                if metric in phases_conf.columns:
                    fig2.add_trace(go.Bar(
                        name=metric.replace("_", " "),
                        x=phases_conf["confederation"],
                        y=phases_conf[metric],
                        marker_color=color,
                    ))
            fig2.update_layout(
                title="Finales, demi-finales, quarts par confederation",
                barmode="group", template="plotly_dark",
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                title_font_color="#e8eaf6",
            )
            st.plotly_chart(fig2, use_container_width=True)

# --- Tab 2 : Win rate par décennie ---
with tab2:
    if "decade" in df_f.columns and "win_rate" in df_f.columns:
        wr_decade = df_f.groupby(["decade", "confederation"])["win_rate"].mean().reset_index()
        wr_decade["decade_label"] = wr_decade["decade"].astype(str) + "s"

        fig3 = px.line(
            wr_decade,
            x="decade_label", y="win_rate",
            color="confederation",
            markers=True,
            color_discrete_map={c: CONF_COLORS.get(c, "#888888") for c in wr_decade["confederation"].unique()},
            labels={"decade_label": "Decennie", "win_rate": "Win rate moyen", "confederation": "Confederation"},
            title="Evolution du win rate moyen par confederation",
            template="plotly_dark",
        )
        fig3.update_layout(
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            title_font_color="#e8eaf6", yaxis_tickformat=".0%",
        )
        st.plotly_chart(fig3, use_container_width=True)

# --- Tab 3 : Phases atteintes ---
with tab3:
    if "decade" in df_f.columns:
        phase_conf = df_f.groupby(["confederation", "phase_lower"]).size().reset_index(name="count")

        fig4 = px.bar(
            phase_conf,
            x="phase_lower", y="count",
            color="confederation",
            barmode="stack",
            color_discrete_map={c: CONF_COLORS.get(c, "#888888") for c in phase_conf["confederation"].unique()},
            labels={"phase_lower": "Phase", "count": "Nb de participations", "confederation": "Confederation"},
            title="Repartition des phases atteintes par confederation",
            template="plotly_dark",
        )
        fig4.update_layout(
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            title_font_color="#e8eaf6",
            xaxis=dict(categoryorder="array", categoryarray=[
                "group stage", "round of 16", "quarter-finals", "semi-finals", "third place", "final",
            ]),
        )
        st.plotly_chart(fig4, use_container_width=True)

# --- Tab 4 : Participations par edition ---
with tab4:
    part_by_edition = df_f.groupby(["wc_year", "confederation"]).size().reset_index(name="participations")

    fig5 = px.bar(
        part_by_edition,
        x="wc_year", y="participations",
        color="confederation",
        barmode="stack",
        color_discrete_map={c: CONF_COLORS.get(c, "#888888") for c in part_by_edition["confederation"].unique()},
        labels={"wc_year": "Edition", "participations": "Equipes qualifiees", "confederation": "Confederation"},
        title="Nombre d'equipes qualifiees par confederation et par edition",
        template="plotly_dark",
    )
    fig5.update_layout(
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        title_font_color="#e8eaf6",
    )
    st.plotly_chart(fig5, use_container_width=True)
