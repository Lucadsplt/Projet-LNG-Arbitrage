"""
Calcul du netback : la valeur nette d'une cargaison de GNL, ramenee au
point de chargement, une fois retires tous les couts de transport.
"""

from . import config


def ttf_eur_mwh_to_usd_mmbtu(ttf_eur_per_mwh,
                              eur_usd_rate=config.EUR_USD_RATE,
                              mwh_to_mmbtu=config.MWH_TO_MMBTU):
    """
    Convertit un prix TTF cote en EUR/MWh vers des $/MMBtu, pour le rendre
    comparable au JKM (deja cote en $/MMBtu).

    1) EUR/MWh -> EUR/MMBtu : on divise par 3,412 (1 MWh = 3,412 MMBtu)
    2) EUR/MMBtu -> USD/MMBtu : on multiplie par le taux de change EUR/USD
    """
    prix_eur_par_mmbtu = ttf_eur_per_mwh / mwh_to_mmbtu
    return prix_eur_par_mmbtu * eur_usd_rate


def netback(prix_rendu, cout_fob, fret, jours_de_mer, frais_regaz,
            boil_off_rate=config.BOIL_OFF_RATE_PER_DAY):
    """
    Netback d'UNE destination, en $/MMBtu :

        netback = prix_rendu - cout_fob - fret - perte_boil_off - frais_regaz

    Tous les arguments doivent deja etre exprimes en $/MMBtu, sauf
    jours_de_mer qui sert uniquement a calculer la perte de boil-off.

    perte_boil_off = boil_off_rate * jours_de_mer * prix_rendu : le
    boil-off est une fraction de la cargaison qui ne sera jamais vendue,
    valorisee au prix de destination (c'est la valeur qu'on perd, pas un
    cout que l'on paie).
    """
    perte_boil_off = boil_off_rate * jours_de_mer * prix_rendu
    return prix_rendu - cout_fob - fret - perte_boil_off - frais_regaz


def compare_destinations(destinations):
    """
    destinations : dict {nom: dict(prix_rendu, cout_fob, fret,
                   jours_de_mer, frais_regaz)} - un jeu de parametres par
                   destination candidate.

    Renvoie (destination_recommandee, netbacks) ou netbacks est le dict
    {nom: valeur_netback} pour toutes les destinations evaluees.
    """
    netbacks = {name: netback(**params) for name, params in destinations.items()}
    recommandation = max(netbacks, key=netbacks.get)
    return recommandation, netbacks
