"""
Recuperation et nettoyage des prix TTF (Europe) et Henry Hub (US) : la
donnee de marche qui alimente prix_rendu (TTF) et cout_fob (Henry Hub)
dans le netback des Jalons 2-3.
"""

import logging
import os
from pathlib import Path

import pandas as pd
import requests
import yfinance as yf
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "prices"

TICKERS = {
    "ttf": "TTF=F",
    "henry_hub": "NG=F",
    "eur_usd": "EURUSD=X",
}


class PriceFetchError(Exception):
    """Levee quand aucune source de prix n'a pu etre recuperee du tout."""


def _nettoyer_serie_yfinance(df_brut, nom_colonne):
    """
    yfinance renvoie un DataFrame Open/High/Low/Close/Volume indexe par
    date (parfois avec des colonnes multi-niveaux selon la version). On
    ne garde que la cloture (Close), qu'on renomme, et on retire les
    lignes sans valeur (jours feries, donnee manquante).
    """
    if df_brut is None or df_brut.empty:
        return pd.DataFrame(columns=["date", nom_colonne])

    cloture = df_brut["Close"]
    if isinstance(cloture, pd.DataFrame):
        cloture = cloture.iloc[:, 0]
    cloture = cloture.dropna()

    df_propre = cloture.reset_index()
    df_propre.columns = ["date", nom_colonne]
    return df_propre


def fetch_ttf(period="3mo", interval="1d"):
    """
    TTF (Title Transfer Facility), prix spot europeen de reference du gaz,
    cote en EUR/MWh. Source : contrat future front-month via Yahoo
    Finance (pas d'API officielle gratuite pour le TTF).

    Renvoie un DataFrame (date, ttf_eur_mwh) ; DataFrame vide si l'API
    ne repond pas, jamais d'exception.
    """
    try:
        df_brut = yf.download(TICKERS["ttf"], period=period, interval=interval, progress=False)
    except Exception as erreur:
        logger.warning("Echec de recuperation TTF via yfinance : %s", erreur)
        return pd.DataFrame(columns=["date", "ttf_eur_mwh"])
    return _nettoyer_serie_yfinance(df_brut, "ttf_eur_mwh")


def fetch_henry_hub_yfinance(period="3mo", interval="1d"):
    """
    Henry Hub via Yahoo Finance (ticker NG=F), cote en $/MMBtu. Source
    rapide et gratuite, mais non officielle - sert de repli si l'API EIA
    n'est pas disponible.
    """
    try:
        df_brut = yf.download(TICKERS["henry_hub"], period=period, interval=interval, progress=False)
    except Exception as erreur:
        logger.warning("Echec de recuperation Henry Hub via yfinance : %s", erreur)
        return pd.DataFrame(columns=["date", "henry_hub_usd_mmbtu"])
    return _nettoyer_serie_yfinance(df_brut, "henry_hub_usd_mmbtu")


def fetch_eur_usd(period="1mo", interval="1d"):
    """
    Taux de change EUR/USD via Yahoo Finance (ticker EURUSD=X). Sert a
    convertir le TTF (cote en EUR/MWh) en $/MMBtu comparable au JKM -
    c'est la 3e donnee "de marche, live et gratuite" du modele, avec le
    TTF et le Henry Hub (voir README, "Fraicheur des hypotheses").
    """
    try:
        df_brut = yf.download(TICKERS["eur_usd"], period=period, interval=interval, progress=False)
    except Exception as erreur:
        logger.warning("Echec de recuperation EUR/USD via yfinance : %s", erreur)
        return pd.DataFrame(columns=["date", "eur_usd"])
    return _nettoyer_serie_yfinance(df_brut, "eur_usd")


def fetch_henry_hub_eia(api_key=None):
    """
    Henry Hub via l'API officielle EIA (Energy Information Administration,
    agence federale americaine) - serie "Henry Hub Natural Gas Spot
    Price". C'est LA source de reference pour ce prix, mais elle demande
    une cle API gratuite (voir .env.example) ; sans cle, on bascule sur
    yfinance.
    """
    api_key = api_key or os.getenv("EIA_API_KEY")
    if not api_key:
        logger.info("EIA_API_KEY absente du .env : bascule sur yfinance pour Henry Hub.")
        return pd.DataFrame(columns=["date", "henry_hub_usd_mmbtu"])

    url = "https://api.eia.gov/v2/natural-gas/pri/fut/data/"
    params = {
        "api_key": api_key,
        "frequency": "daily",
        "data[0]": "value",
        "facets[series][]": "RNGWHHD",  # Henry Hub Natural Gas Spot Price
        "sort[0][column]": "period",
        "sort[0][direction]": "desc",
    }

    try:
        reponse = requests.get(url, params=params, timeout=10)
        reponse.raise_for_status()
    except requests.exceptions.RequestException as erreur:
        logger.warning("Echec de recuperation Henry Hub via l'API EIA : %s", erreur)
        return pd.DataFrame(columns=["date", "henry_hub_usd_mmbtu"])

    lignes = reponse.json().get("response", {}).get("data", [])
    if not lignes:
        return pd.DataFrame(columns=["date", "henry_hub_usd_mmbtu"])

    df = pd.DataFrame(lignes)[["period", "value"]]
    df.columns = ["date", "henry_hub_usd_mmbtu"]
    df["date"] = pd.to_datetime(df["date"])
    df["henry_hub_usd_mmbtu"] = pd.to_numeric(df["henry_hub_usd_mmbtu"], errors="coerce")
    return df.dropna().sort_values("date").reset_index(drop=True)


def fetch_henry_hub(api_key=None):
    """
    Henry Hub : tente d'abord la source officielle EIA, puis se rabat sur
    yfinance si la cle API est absente ou si l'appel echoue.
    """
    df = fetch_henry_hub_eia(api_key=api_key)
    if df.empty:
        df = fetch_henry_hub_yfinance()
    return df


def save_csv(df, nom_fichier):
    """Sauvegarde un DataFrame de prix dans data/prices/, cree le dossier si besoin."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    chemin = DATA_DIR / nom_fichier
    df.to_csv(chemin, index=False)
    return chemin


def update_price_data():
    """
    Recupere TTF et Henry Hub et sauvegarde chacun en CSV independamment :
    si une source echoue, l'autre est quand meme sauvegardee (best effort,
    pas de tout-ou-rien). Leve PriceFetchError seulement si les DEUX
    sources ont echoue.

    Renvoie {source: (dataframe, chemin_ou_None)}.
    """
    resultats = {}

    df_ttf = fetch_ttf()
    resultats["ttf"] = (df_ttf, save_csv(df_ttf, "ttf.csv") if not df_ttf.empty else None)

    df_hh = fetch_henry_hub()
    resultats["henry_hub"] = (df_hh, save_csv(df_hh, "henry_hub.csv") if not df_hh.empty else None)

    if df_ttf.empty and df_hh.empty:
        raise PriceFetchError("Aucune source de prix n'a pu etre recuperee (TTF et Henry Hub).")

    return resultats


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    for source, (df, chemin) in update_price_data().items():
        statut = f"sauvegarde -> {chemin}" if chemin else "ECHEC (aucune donnee)"
        print(f"{source}: {len(df)} lignes, {statut}")
