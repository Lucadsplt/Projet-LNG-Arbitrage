"""
Routing : jours de mer par route, et leur impact sur le fret et le
boil-off cumule. Fait le pont entre les hypotheses de config.py et le
calcul de netback du Jalon 2.
"""

from . import config
from .netback import compare_destinations

# 1 TBtu = 1 000 000 MMBtu : sert a ramener un cout total de voyage ($)
# en cout par MMBtu de cargaison, comparable au reste du netback.
CARGO_SIZE_MMBTU = config.CARGO_SIZE_TBTU * 1_000_000

# Seule la route Asie via Panama emprunte le canal ; le Cap de
# Bonne-Esperance et l'Atlantique vers l'Europe n'ont pas de peage.
ROUTES_AVEC_PEAGE_PANAMA = {"asia_panama"}


def jours_de_mer(route):
    """Duree de voyage (jours) pour une route de config.ROUTE_DAYS."""
    return config.ROUTE_DAYS[route]


def cout_fret_usd_mmbtu(route, taux_affretement_usd_par_jour):
    """
    Cout de fret total du voyage, ramene en $/MMBtu de cargaison :

        cout_fret_total = taux_affretement ($/jour) x jours_de_mer
                           + peage_Panama (uniquement si la route l'emprunte)
        cout_fret_par_mmbtu = cout_fret_total / taille_cargaison_MMBtu

    Le peage est un montant fixe par transit (pas par jour) : on l'ajoute
    donc une seule fois, apres le calcul taux x jours.
    """
    cout_total = taux_affretement_usd_par_jour * jours_de_mer(route)
    if route in ROUTES_AVEC_PEAGE_PANAMA:
        cout_total += config.PANAMA_TOLL_USD
    return cout_total / CARGO_SIZE_MMBTU


def construire_destination(route, prix_rendu, cout_fob, frais_regaz,
                            taux_affretement_usd_par_jour):
    """
    Assemble les parametres d'une destination, au format attendu par
    netback.netback(), a partir des hypotheses de routing (jours de mer,
    peage) et des donnees de marche (prix, cout FOB, frais de regaz).
    """
    return dict(
        prix_rendu=prix_rendu,
        cout_fob=cout_fob,
        fret=cout_fret_usd_mmbtu(route, taux_affretement_usd_par_jour),
        jours_de_mer=jours_de_mer(route),
        frais_regaz=frais_regaz,
    )


def comparer_routes(scenarios):
    """
    scenarios : dict {route: dict(prix_rendu, cout_fob, frais_regaz,
                taux_affretement_usd_par_jour)}

    Construit une destination complete par route via construire_destination(),
    puis delegue la decision a netback.compare_destinations() (Jalon 2).
    """
    destinations = {
        route: construire_destination(route, **params)
        for route, params in scenarios.items()
    }
    return compare_destinations(destinations)
