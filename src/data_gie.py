"""
Send-out et stocks des terminaux GNL europeens, via l'API GIE ALSI
(Aggregated LNG Storage Inventory, https://alsi.gie.eu).

Cette donnee sert uniquement au dashboard (Jalon 8) : elle donne le
contexte physique du marche europeen (terminaux pleins ou non, send-out
eleve ou non), mais n'entre dans AUCUN calcul de netback des Jalons 2-3.
"""

import logging
import os

import pandas as pd
import requests
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

BASE_URL = "https://alsi.gie.eu/api"

COLONNES_UTILES = ["name", "code", "gasDayStart", "inventory", "sendOut", "dtmi", "dtrs"]


class GieFetchError(Exception):
    """Levee quand l'API GIE ALSI ne repond pas, refuse la cle, ou renvoie une erreur."""


def fetch_alsi(type_="eu", country=None, date=None, from_=None, to=None,
                size=300, api_key=None):
    """
    Interroge l'API GIE ALSI et renvoie la reponse JSON brute (dict).

    - type_="eu" (par defaut) : agrege l'ensemble des pays europeens.
      Ignore si `country` est fourni.
    - country="fr" : filtre sur un pays precis (code ISO 2 lettres).
    - date / from_ / to : filtres sur le "gas day" (format YYYY-MM-DD).
    - size : nombre de lignes par page (30 par defaut, 300 max cote API).

    Leve GieFetchError si la cle API est absente, si la requete echoue
    (reseau, timeout), ou si l'API repond avec un champ "error".
    """
    api_key = api_key or os.getenv("GIE_API_KEY")
    if not api_key:
        raise GieFetchError(
            "GIE_API_KEY absente du .env : inscription gratuite sur "
            "https://alsi.gie.eu (menu API) pour obtenir une cle."
        )

    params = {"size": size}
    if country:
        params["country"] = country
    else:
        params["type"] = type_
    if date:
        params["date"] = date
    if from_:
        params["from"] = from_
    if to:
        params["to"] = to

    try:
        reponse = requests.get(
            BASE_URL,
            params=params,
            headers={"x-key": api_key},
            timeout=15,
        )
        reponse.raise_for_status()
    except requests.exceptions.RequestException as erreur:
        raise GieFetchError(f"Echec de l'appel a l'API GIE ALSI : {erreur}") from erreur

    donnees = reponse.json()
    if donnees.get("error"):
        raise GieFetchError(f"L'API GIE ALSI a renvoye une erreur : {donnees.get('message')}")

    return donnees


def json_vers_dataframe(reponse_json):
    """
    Extrait la liste "data" de la reponse JSON ALSI et la met en forme
    pour le dashboard.

    Champs conserves (documentation GIE, section ALSI - Facility Report) :
    - name, code       : identifiant du pays/terminal
    - gasDayStart      : date du jour gazier
    - inventory        : stock de GNL en fin de journee (10^3 m3 LNG)
    - sendOut          : gaz reinjecte dans le reseau ce jour-la (GWh/j)
    - dtmi             : capacite maximale de stockage (10^3 m3 LNG)
    - dtrs              : capacite maximale de send-out (GWh/j)

    On ajoute une colonne calculee "taux_remplissage" = inventory / dtmi,
    plus parlante pour un graphe que le volume brut en m3.
    """
    lignes = reponse_json.get("data", [])
    colonnes_sortie = COLONNES_UTILES + ["taux_remplissage"]

    if not lignes:
        return pd.DataFrame(columns=colonnes_sortie)

    df = pd.json_normalize(lignes)
    colonnes_presentes = [c for c in COLONNES_UTILES if c in df.columns]
    df = df[colonnes_presentes].copy()

    for colonne in ("inventory", "sendOut", "dtmi", "dtrs"):
        if colonne in df.columns:
            df[colonne] = pd.to_numeric(df[colonne], errors="coerce")

    if "inventory" in df.columns and "dtmi" in df.columns:
        df["taux_remplissage"] = df["inventory"] / df["dtmi"]
    else:
        df["taux_remplissage"] = pd.NA

    if "gasDayStart" in df.columns:
        df["gasDayStart"] = pd.to_datetime(df["gasDayStart"])
        df = df.sort_values("gasDayStart").reset_index(drop=True)

    return df


def fetch_alsi_dataframe(**kwargs):
    """Combine fetch_alsi() et json_vers_dataframe() en un seul appel."""
    return json_vers_dataframe(fetch_alsi(**kwargs))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    df = fetch_alsi_dataframe(type_="eu", size=30)
    print(df)
