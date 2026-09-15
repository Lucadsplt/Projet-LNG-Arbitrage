"""
Genere les graphiques de sortie du projet, dans outputs/charts/ :

- netback_comparison.png : Europe vs Asie, avec les prix de marche du jour
- price_series.png       : TTF et Henry Hub sur la periode recuperee (Jalon 4)
- sensitivity_heatmap.png : la meme table de sensibilite que le classeur
  Excel (Jalon 6), recalculee ici directement en Python
- gie_dashboard.png      : send-out et remplissage des terminaux GNL
  europeens (Jalon 5) - necessite GIE_API_KEY, sinon graphe "indisponible"

Chaque fonction est independante et n'echoue jamais bruyamment : une
source de donnees indisponible produit un graphe degrade plutot que de
faire planter tout le pipeline (meme logique que data_prices.py et
data_gie.py).
"""

import logging
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from . import config, data_gie, data_prices
from .netback import netback, ttf_eur_mwh_to_usd_mmbtu
from .routing import cout_fret_usd_mmbtu, jours_de_mer

logger = logging.getLogger(__name__)

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "outputs" / "charts"

COULEUR_EUROPE = "#1F4E78"
COULEUR_ASIE = "#C55A11"


def _derniere_valeur_ou_defaut(df, colonne, defaut):
    if df is None or df.empty:
        return defaut
    return float(df.iloc[-1][colonne])


def _cout_fob(henry_hub):
    return config.FEEDGAS_HH_MULTIPLIER * henry_hub + config.LIQUEFACTION_TOLLING_FEE_USD_PER_MMBTU


def _netback_europe(ttf_usd_mmbtu, cout_fob, taux_fret):
    return netback(
        prix_rendu=ttf_usd_mmbtu,
        cout_fob=cout_fob,
        fret=cout_fret_usd_mmbtu("europe", taux_fret),
        jours_de_mer=jours_de_mer("europe"),
        frais_regaz=config.REGAS_FEE_USD_MMBTU["europe"],
    )


def _netback_asie(jkm_usd_mmbtu, cout_fob, taux_fret):
    return netback(
        prix_rendu=jkm_usd_mmbtu,
        cout_fob=cout_fob,
        fret=cout_fret_usd_mmbtu("asia_panama", taux_fret),
        jours_de_mer=jours_de_mer("asia_panama"),
        frais_regaz=config.REGAS_FEE_USD_MMBTU["asia"],
    )


def _grille_sensibilite(ttf_usd_mmbtu, cout_fob):
    """
    Recalcule, en Python, exactement la meme grille que la feuille
    Sensibilite du classeur Excel (memes listes config.SENSIBILITE_*) :
    delta = netback(Asie) - netback(Europe), pour chaque combinaison
    (taux de fret, ecart JKM-TTF).
    """
    grille = []
    for taux_fret in config.SENSIBILITE_TAUX_FRET:
        ligne = []
        for ecart in config.SENSIBILITE_ECARTS_JKM_TTF:
            jkm = ttf_usd_mmbtu + ecart
            delta = _netback_asie(jkm, cout_fob, taux_fret) - _netback_europe(ttf_usd_mmbtu, cout_fob, taux_fret)
            ligne.append(delta)
        grille.append(ligne)
    return grille


def _valeurs_marche_du_jour():
    df_ttf = data_prices.fetch_ttf()
    df_hh = data_prices.fetch_henry_hub()
    df_fx = data_prices.fetch_eur_usd()

    ttf_eur_mwh = _derniere_valeur_ou_defaut(df_ttf, "ttf_eur_mwh", 32.0)
    henry_hub = _derniere_valeur_ou_defaut(df_hh, "henry_hub_usd_mmbtu", 3.20)
    eur_usd = _derniere_valeur_ou_defaut(df_fx, "eur_usd", config.EUR_USD_RATE)

    return {
        "ttf_usd_mmbtu": ttf_eur_mwh_to_usd_mmbtu(ttf_eur_mwh, eur_usd_rate=eur_usd),
        "henry_hub": henry_hub,
    }


def graphe_comparaison_netback(chemin_sortie=None):
    """
    Barres Europe vs Asie (Panama) au netback du jour. Prix TTF/Henry Hub
    recuperes en direct ; JKM et taux de fret restent les hypotheses par
    defaut de config.py (pas de source gratuite - voir README).
    """
    chemin_sortie = chemin_sortie or OUTPUT_DIR / "netback_comparison.png"
    chemin_sortie = Path(chemin_sortie)

    marche = _valeurs_marche_du_jour()
    cout_fob = _cout_fob(marche["henry_hub"])
    taux_fret = config.TAUX_AFFRETEMENT_USD_JOUR_DEFAUT

    nb_europe = _netback_europe(marche["ttf_usd_mmbtu"], cout_fob, taux_fret)
    nb_asie = _netback_asie(config.JKM_USD_MMBTU_DEFAUT, cout_fob, taux_fret)

    fig, ax = plt.subplots(figsize=(6, 5))
    destinations = ["Europe", "Asie (Panama)"]
    valeurs = [nb_europe, nb_asie]
    barres = ax.bar(destinations, valeurs, color=[COULEUR_EUROPE, COULEUR_ASIE])
    ax.bar_label(barres, fmt="%.2f $/MMBtu")
    ax.axhline(0, color="black", linewidth=0.8)
    ax.set_ylabel("Netback ($/MMBtu)")
    gagnant = destinations[0] if nb_europe > nb_asie else destinations[1]
    ax.set_title(f"Netback par destination - recommandation : {gagnant}")
    fig.tight_layout()

    chemin_sortie.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(chemin_sortie, dpi=150)
    plt.close(fig)
    return chemin_sortie


def graphe_series_prix(chemin_sortie=None):
    """TTF (EUR/MWh) et Henry Hub ($/MMBtu) sur la periode recuperee (Jalon 4)."""
    chemin_sortie = chemin_sortie or OUTPUT_DIR / "price_series.png"
    chemin_sortie = Path(chemin_sortie)

    df_ttf = data_prices.fetch_ttf()
    df_hh = data_prices.fetch_henry_hub()

    fig, ax1 = plt.subplots(figsize=(8, 5))
    if not df_ttf.empty:
        ax1.plot(df_ttf["date"], df_ttf["ttf_eur_mwh"], color=COULEUR_EUROPE, label="TTF (EUR/MWh)")
    ax1.set_ylabel("TTF (EUR/MWh)", color=COULEUR_EUROPE)
    ax1.tick_params(axis="y", labelcolor=COULEUR_EUROPE)

    ax2 = ax1.twinx()
    if not df_hh.empty:
        ax2.plot(df_hh["date"], df_hh["henry_hub_usd_mmbtu"], color=COULEUR_ASIE, label="Henry Hub ($/MMBtu)")
    ax2.set_ylabel("Henry Hub ($/MMBtu)", color=COULEUR_ASIE)
    ax2.tick_params(axis="y", labelcolor=COULEUR_ASIE)

    ax1.set_title("TTF (Europe) et Henry Hub (US) - prix de marche")
    fig.autofmt_xdate()
    fig.tight_layout()

    chemin_sortie.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(chemin_sortie, dpi=150)
    plt.close(fig)
    return chemin_sortie


def graphe_heatmap_sensibilite(chemin_sortie=None):
    """Heatmap Python de la meme table de sensibilite que le classeur Excel."""
    chemin_sortie = chemin_sortie or OUTPUT_DIR / "sensitivity_heatmap.png"
    chemin_sortie = Path(chemin_sortie)

    marche = _valeurs_marche_du_jour()
    cout_fob = _cout_fob(marche["henry_hub"])
    grille = np.array(_grille_sensibilite(marche["ttf_usd_mmbtu"], cout_fob))

    fig, ax = plt.subplots(figsize=(7, 5))
    lim = max(abs(grille.min()), abs(grille.max())) or 1.0
    im = ax.imshow(grille, cmap="RdYlGn", vmin=-lim, vmax=lim, aspect="auto")

    ax.set_xticks(range(len(config.SENSIBILITE_ECARTS_JKM_TTF)))
    ax.set_xticklabels([f"{e:+.2f}" for e in config.SENSIBILITE_ECARTS_JKM_TTF])
    ax.set_yticks(range(len(config.SENSIBILITE_TAUX_FRET)))
    ax.set_yticklabels([f"{t:,.0f}" for t in config.SENSIBILITE_TAUX_FRET])
    ax.set_xlabel("Ecart JKM - TTF ($/MMBtu)")
    ax.set_ylabel("Taux d'affretement ($/jour)")
    ax.set_title("Sensibilite : netback Asie - Europe ($/MMBtu)")

    for i in range(grille.shape[0]):
        for j in range(grille.shape[1]):
            ax.text(j, i, f"{grille[i, j]:.2f}", ha="center", va="center", fontsize=8)

    fig.colorbar(im, ax=ax, label="$/MMBtu")
    fig.tight_layout()

    chemin_sortie.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(chemin_sortie, dpi=150)
    plt.close(fig)
    return chemin_sortie


def graphe_dashboard_gie(chemin_sortie=None):
    """
    Send-out et taux de remplissage des terminaux GNL europeens (Jalon 5).
    Sans GIE_API_KEY, produit un graphe "indisponible" explicite plutot
    que de faire planter generer_tous_les_graphes().
    """
    chemin_sortie = chemin_sortie or OUTPUT_DIR / "gie_dashboard.png"
    chemin_sortie = Path(chemin_sortie)
    chemin_sortie.parent.mkdir(parents=True, exist_ok=True)

    try:
        df = data_gie.fetch_alsi_dataframe(type_="eu", size=90)
    except data_gie.GieFetchError as erreur:
        logger.warning("Dashboard GIE non genere : %s", erreur)
        fig, ax = plt.subplots(figsize=(7, 4))
        ax.text(0.5, 0.5, f"Donnee GIE ALSI indisponible :\n{erreur}",
                ha="center", va="center", wrap=True, fontsize=10)
        ax.axis("off")
        fig.savefig(chemin_sortie, dpi=150)
        plt.close(fig)
        return chemin_sortie

    fig, ax1 = plt.subplots(figsize=(8, 5))
    ax1.plot(df["gasDayStart"], df["sendOut"], color=COULEUR_EUROPE, label="Send-out (GWh/j)")
    ax1.set_ylabel("Send-out (GWh/j)", color=COULEUR_EUROPE)
    ax1.tick_params(axis="y", labelcolor=COULEUR_EUROPE)

    ax2 = ax1.twinx()
    ax2.plot(df["gasDayStart"], df["taux_remplissage"] * 100, color=COULEUR_ASIE, label="Remplissage (%)")
    ax2.set_ylabel("Taux de remplissage (%)", color=COULEUR_ASIE)
    ax2.tick_params(axis="y", labelcolor=COULEUR_ASIE)

    ax1.set_title("Terminaux GNL europeens : send-out et remplissage (GIE ALSI)")
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(chemin_sortie, dpi=150)
    plt.close(fig)
    return chemin_sortie


def generer_tous_les_graphes():
    """Genere les 4 graphes ; une source en echec ne bloque pas les autres."""
    fonctions = [
        graphe_comparaison_netback,
        graphe_series_prix,
        graphe_heatmap_sensibilite,
        graphe_dashboard_gie,
    ]
    chemins = []
    for fonction in fonctions:
        try:
            chemins.append(fonction())
        except Exception as erreur:
            logger.error("Echec de generation de %s : %s", fonction.__name__, erreur)
    return chemins


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    for chemin in generer_tous_les_graphes():
        print(f"Genere : {chemin}")
