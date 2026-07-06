"""
data_loader.py
Centralise le chargement et le cache des donnees pour le dashboard.
Toutes les pages importent depuis ce module.
"""
import sys
import os
from pathlib import Path

import pandas as pd
import streamlit as st

# Ajoute la racine du projet au path pour pouvoir importer scripts/
ROOT = Path(__file__).parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.extract import extract
from scripts.transform import transform


@st.cache_data(show_spinner="Chargement du pipeline ETL...")
def load_all() -> dict:
    """
    Execute le pipeline ETL et retourne le dictionnaire transforme.
    Mis en cache pour toute la session Streamlit.
    """
    raw = extract()
    return transform(raw)


def get_matches(data: dict) -> pd.DataFrame:
    df = data["matches"].copy()
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df["year"] = df["date"].dt.year
        df["decade"] = (df["year"] // 10 * 10).astype("Int64")
    return df


def get_team_alltime(data: dict) -> pd.DataFrame:
    df = data.get("team_alltime_stats", pd.DataFrame())
    if df is None:
        return pd.DataFrame()
    return df.copy()


def get_win_rate(data: dict) -> pd.DataFrame:
    df = data.get("win_rate", pd.DataFrame())
    if df is None:
        return pd.DataFrame()
    return df.copy()


def get_titles(data: dict) -> pd.DataFrame:
    df = data.get("titles", pd.DataFrame())
    if df is None:
        return pd.DataFrame()
    return df.copy()


def get_worldcup(data: dict) -> pd.DataFrame:
    df = data.get("worldcup", pd.DataFrame())
    if df is None:
        return pd.DataFrame()
    return df.copy()


def get_team_appearances(data: dict) -> pd.DataFrame:
    df = data.get("team_appearances", pd.DataFrame())
    if df is None:
        return pd.DataFrame()
    df = df.copy()
    if "wc_year" in df.columns:
        df["decade"] = (df["wc_year"] // 10 * 10).astype("Int64")
    return df


def get_ranking(data: dict) -> pd.DataFrame:
    df = data.get("ranking", pd.DataFrame())
    if df is None:
        return pd.DataFrame()
    return df.copy()


def get_phase_performance(data: dict) -> pd.DataFrame:
    df = data.get("phase_performance", pd.DataFrame())
    if df is None:
        return pd.DataFrame()
    return df.copy()


# Palette de couleurs coherente pour les confederations
CONF_COLORS = {
    "UEFA":     "#4361EE",
    "CONMEBOL": "#3A0CA3",
    "CONCACAF": "#7209B7",
    "CAF":      "#F72585",
    "AFC":      "#4CC9F0",
    "OFC":      "#80B918",
}

# Ordre des phases du tournoi (du plus facile au plus difficile)
# Les valeurs reelles dans team_appearances sont capitalisees
PHASE_ORDER = [
    "group stage",
    "round of 16",
    "quarter-finals",
    "semi-finals",
    "fourth place",
    "third place",
    "runner-up",
    "winner",
]

PHASE_SCORE = {phase: i for i, phase in enumerate(PHASE_ORDER)}


# ─── Flags ───────────────────────────────────────────────────────────────────

def _iso_to_flag(iso2: str) -> str:
    """Convertit un code ISO 3166-1 alpha-2 en emoji drapeau Unicode."""
    return "".join(chr(0x1F1E6 + ord(c) - ord("A")) for c in iso2.upper())


# Mapping complet : nom d'equipe → code ISO 3166-1 alpha-2
TEAM_ISO: dict[str, str] = {
    # Europe - UEFA
    "Albania": "AL", "Andorra": "AD", "Armenia": "AM", "Austria": "AT",
    "Azerbaijan": "AZ", "Belarus": "BY", "Belgium": "BE", "Bosnia and Herzegovina": "BA",
    "Bulgaria": "BG", "Croatia": "HR", "Cyprus": "CY", "Czech Republic": "CZ",
    "Czechoslovakia": "CZ", "Denmark": "DK", "England": "GB", "Estonia": "EE",
    "Faroe Islands": "FO", "Finland": "FI", "France": "FR", "Georgia": "GE",
    "Germany": "DE", "Germany DR": "DE", "FR Yugoslavia": "RS", "Gibraltar": "GI",
    "Greece": "GR", "Hungary": "HU", "Iceland": "IS", "Republic of Ireland": "IE",
    "Rep of Ireland": "IE", "Israel": "IL", "Italy": "IT", "Kazakhstan": "KZ",
    "Kosovo": "XK", "Latvia": "LV", "Liechtenstein": "LI", "Lithuania": "LT",
    "Luxembourg": "LU", "Malta": "MT", "Moldova": "MD", "Montenegro": "ME",
    "Netherlands": "NL", "North Macedonia": "MK", "Northern Ireland": "GB",
    "Norway": "NO", "Poland": "PL", "Portugal": "PT", "Romania": "RO",
    "Russia": "RU", "San Marino": "SM", "Scotland": "GB", "Serbia": "RS",
    "Slovakia": "SK", "Slovenia": "SI", "Spain": "ES", "Sweden": "SE",
    "Switzerland": "CH", "Turkey": "TR", "Türkiye": "TR", "Ukraine": "UA",
    "Wales": "GB",
    # Amérique du Sud - CONMEBOL
    "Argentina": "AR", "Bolivia": "BO", "Brazil": "BR", "Chile": "CL",
    "Colombia": "CO", "Ecuador": "EC", "Paraguay": "PY", "Peru": "PE",
    "Uruguay": "UY", "Venezuela": "VE",
    # Amérique du Nord / Centrale - CONCACAF
    "Canada": "CA", "Costa Rica": "CR", "Cuba": "CU", "El Salvador": "SV",
    "Guatemala": "GT", "Haiti": "HT", "Honduras": "HN", "Jamaica": "JM",
    "Mexico": "MX", "Panama": "PA", "Trinidad and Tobago": "TT",
    "United States": "US", "USA": "US",
    # Afrique - CAF
    "Algeria": "DZ", "Angola": "AO", "Cameroon": "CM", "Cape Verde": "CV",
    "Côte d'Ivoire": "CI", "Ivory Coast": "CI", "DR Congo": "CD",
    "Egypt": "EG", "Ethiopia": "ET", "Gabon": "GA", "Ghana": "GH",
    "Guinea": "GN", "Kenya": "KE", "Liberia": "LR", "Libya": "LY",
    "Madagascar": "MG", "Mali": "ML", "Morocco": "MA", "Mozambique": "MZ",
    "Nigeria": "NG", "Senegal": "SN", "Sierra Leone": "SL",
    "South Africa": "ZA", "Sudan": "SD", "Tanzania": "TZ", "Togo": "TG",
    "Tunisia": "TN", "Uganda": "UG", "Zambia": "ZM", "Zimbabwe": "ZW",
    # Asie - AFC
    "Afghanistan": "AF", "Australia": "AU", "Bahrain": "BH", "China": "CN",
    "China PR": "CN", "India": "IN", "Indonesia": "ID", "Iran": "IR",
    "Iraq": "IQ", "Japan": "JP", "Jordan": "JO", "Korea DPR": "KP",
    "Korea Republic": "KR", "South Korea": "KR", "Kuwait": "KW",
    "Malaysia": "MY", "Myanmar": "MM", "Oman": "OM", "Pakistan": "PK",
    "Palestine": "PS", "Philippines": "PH", "Qatar": "QA",
    "Saudi Arabia": "SA", "Singapore": "SG", "Syria": "SY",
    "Thailand": "TH", "United Arab Emirates": "AE", "Vietnam": "VN",
    "Yemen": "YE",
    # Océanie - OFC
    "Fiji": "FJ", "New Caledonia": "NC", "New Zealand": "NZ",
    "Papua New Guinea": "PG", "Solomon Islands": "SB", "Vanuatu": "VU",
}


def get_flag(team: str) -> str:
    """Retourne l'emoji drapeau pour un nom d'equipe. Retourne '' si inconnu."""
    iso = TEAM_ISO.get(team)
    if iso:
        return _iso_to_flag(iso)
    return ""


def with_flag(team: str) -> str:
    """Retourne 'emoji Nom' pour un nom d'equipe (ex: '🇧🇷 Brazil')."""
    flag = get_flag(team)
    return f"{flag} {team}" if flag else team


def add_flag_column(df: pd.DataFrame, team_col: str = "team") -> pd.DataFrame:
    """Ajoute une colonne 'flag_team' = emoji + nom. Retourne une copie."""
    df = df.copy()
    if team_col in df.columns:
        df["flag_team"] = df[team_col].apply(with_flag)
    return df

