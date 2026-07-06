"""
Page 8 — Prédiction Coupe du Monde 2026

Affichage des résultats du modèle de Machine Learning entraîné sur les données historiques.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import pandas as pd
import plotly.express as px
from data_loader import add_flag_column

st.set_page_config(page_title="Prédiction 2026", layout="wide")

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

st.title("08 — Prédiction Coupe du Monde 2026 🤖")
st.markdown(
    "Voici les prédictions générées par notre modèle d'Intelligence Artificielle (**Random Forest**). "
    "L'algorithme a appris de toutes les Coupes du Monde précédentes (1930-2022) pour estimer les "
    "chances de chaque équipe d'atteindre le **Dernier Carré (Top 4)** en 2026."
)
st.divider()

# ─── Data ────────────────────────────────────────────────────────────────────
@st.cache_data
def load_predictions():
    pred_path = Path(__file__).parent.parent.parent / "data" / "processed" / "predictions_2026.csv"
    if not pred_path.exists():
        return pd.DataFrame()
    
    df = pd.read_csv(pred_path)
    # Renommer la colonne pour utiliser la fonction add_flag_column
    if "Équipe" in df.columns:
        df = df.rename(columns={"Équipe": "team"})
        df = add_flag_column(df)
        df = df.rename(columns={"team": "Équipe", "flag_team": "Nation"})
    return df

df_preds = load_predictions()

if df_preds.empty:
    st.error("Les données de prédiction n'ont pas été trouvées. Veuillez d'abord exécuter le Notebook ML.")
    st.stop()

# ─── KPIs ────────────────────────────────────────────────────────────────────
col1, col2, col3 = st.columns(3)

top_team = df_preds.iloc[0]
best_elo = df_preds.loc[df_preds["Score ELO actuel"].idxmax()]

col1.metric(
    label="🏆 Grand Favori (Top 4)", 
    value=f"{top_team['Nation']}", 
    delta=f"{top_team['Probabilité Top 4 (%)']}%",
    delta_color="normal"
)

col2.metric(
    label="⚡ Meilleur Score ELO Global", 
    value=f"{best_elo['Nation']}", 
    delta=f"ELO: {best_elo['Score ELO actuel']}",
    delta_color="off"
)

# Compter combien d'équipes de chaque confédération dans le Top 10
top10_confeds = df_preds.head(10)["Confédération"].value_counts()
dominant_confed = top10_confeds.index[0]
dominant_count = top10_confeds.iloc[0]

col3.metric(
    label="🌍 Confédération Dominante (Top 10)", 
    value=dominant_confed, 
    delta=f"{dominant_count}/10 équipes",
    delta_color="off"
)

st.divider()

# ─── Graphique Principal ──────────────────────────────────────────────────────
st.subheader("📊 Top 15 des Favoris")

top15 = df_preds.head(15).copy()
top15 = top15.sort_values(by="Probabilité Top 4 (%)", ascending=True)

fig = px.bar(
    top15,
    x="Probabilité Top 4 (%)",
    y="Nation",
    orientation="h",
    color="Probabilité Top 4 (%)",
    color_continuous_scale="magma",
    text="Probabilité Top 4 (%)",
    title="Probabilité d'atteindre les demi-finales (%)",
    template="plotly_dark",
    labels={"Nation": "Équipe", "Probabilité Top 4 (%)": "Probabilité (%)"}
)

fig.update_traces(textposition='outside')
fig.update_layout(
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    title_font_color="#e8eaf6",
    coloraxis_showscale=False,
    height=600
)

st.plotly_chart(fig, use_container_width=True)

# ─── Tableau de Données ───────────────────────────────────────────────────────
st.subheader("📋 Classement Complet des 48 Équipes")
st.markdown("Vous pouvez trier et filtrer le tableau ci-dessous :")

cols_to_display = ["Nation", "Confédération", "Score ELO actuel", "Probabilité Top 4 (%)"]
st.dataframe(
    df_preds[cols_to_display].set_index("Nation"),
    use_container_width=True,
    height=400
)
