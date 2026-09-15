"""
Hypothèses métier centralisées pour le modèle d'arbitrage GNL.

Toute constante utilisée dans un calcul (netback, fret, boil-off...) doit
venir de ce fichier et de nulle part ailleurs. C'est ce qui permet de
changer une hypothèse à un seul endroit et de la documenter clairement
pour un recruteur ou un jury.

Deux hypothèses sont volontairement les plus fragiles du modèle : le prix
JKM et le taux d'affrètement. Il n'existe pas de source gratuite fiable
pour ces deux données ; elles restent donc des valeurs assumées, à isoler
et à documenter (voir README).
"""

# --- Cargaison -------------------------------------------------------------

# Contenu énergétique d'un méthanier standard (160 000-174 000 m3), la
# taille la plus répandue de la flotte mondiale. C'est la base sur laquelle
# tous les coûts (fret, boil-off, tolling fee) sont ramenés.
CARGO_SIZE_TBTU = 3.5

# Part du volume chargé qui s'évapore chaque jour en mer (boil-off gas).
# Ordre de grandeur observé sur un méthanier moderne à cuves membrane.
BOIL_OFF_RATE_PER_DAY = 0.001  # 0,1 %/jour


# --- Coût FOB (Golfe du Mexique, type Sabine Pass) --------------------------

# Structure typique d'un contrat d'enlèvement (SPA) de GNL américain :
# feedgas indexé Henry Hub + une marge de liquéfaction (tolling fee) fixe.
# coût_FOB = FEEDGAS_HH_MULTIPLIER * Henry_Hub + LIQUEFACTION_TOLLING_FEE
FEEDGAS_HH_MULTIPLIER = 1.15

# Marge de liquéfaction payée au train de liquéfaction, indépendante du
# prix du gaz. Fourchette typique des contrats existants : 2,25-3,50
# $/MMBtu. On retient une valeur médiane, à documenter et à challenger.
LIQUEFACTION_TOLLING_FEE_USD_PER_MMBTU = 3.00


# --- Routes et durée de voyage -----------------------------------------------

# Durée US Gulf -> destination, en jours de mer. Ce sont des ordres de
# grandeur pour un méthanier à vitesse de croisière standard (~19,5 nœuds),
# pas un routage précis navire par navire.
ROUTE_DAYS = {
    "europe": 14,          # US Gulf -> Europe (nord-ouest), via l'Atlantique
    "asia_panama": 27,     # US Gulf -> Asie, via le canal de Panama
    "asia_cape": 37,       # US Gulf -> Asie, via le cap de Bonne-Espérance
}

# Péage du canal de Panama pour un méthanier de la taille standard
# CARGO_SIZE_TBTU. Le tarif réel dépend du gabarit du navire et des
# enchères de créneau (très volatile en période de congestion, ex. 2023).
# On retient un ordre de grandeur du tarif de base, à documenter.
PANAMA_TOLL_USD = 900_000


# --- Change et conversion d'unités -------------------------------------------

# Taux de change par défaut, utilisé tant qu'aucune donnée live n'est
# branchée (Jalon 4). À remplacer par un taux récupéré dynamiquement.
EUR_USD_RATE = 1.08

# 1 MWh = 3,412 MMBtu (conversion d'énergie). Sert à ramener le TTF,
# coté en EUR/MWh, vers des $/MMBtu comparables au JKM.
MWH_TO_MMBTU = 3.412


# --- Frais de regazéification (par destination) -----------------------------

# Tarif payé au terminal d'arrivée pour réinjecter le GNL dans le réseau,
# propre à chaque destination. Fourchette typique observée en Europe/Asie.
REGAS_FEE_USD_MMBTU = {
    "europe": 0.40,
    "asia": 0.50,
}


# --- Hypothèses de marché par défaut (fragiles, sans source gratuite) -------

# JKM et taux d'affrètement n'ont pas de source gratuite fiable (voir
# docstring plus haut) : ces valeurs par défaut servent de point de départ
# au classeur Excel (Jalon 6) et aux graphes (Jalon 8), tant que tu ne les
# as pas mises à jour toi-même depuis l'actualité.
JKM_USD_MMBTU_DEFAUT = 11.50
TAUX_AFFRETEMENT_USD_JOUR_DEFAUT = 65_000


# --- Table de sensibilité (Jalons 6 et 8) -----------------------------------

# Grille utilisée à la fois par le classeur Excel et par le graphe heatmap
# du Jalon 8 : mêmes valeurs, un seul endroit où les changer.
SENSIBILITE_ECARTS_JKM_TTF = [-1.0, -0.5, 0.0, 0.5, 1.0, 1.5, 2.0]
SENSIBILITE_TAUX_FRET = [30_000, 50_000, 70_000, 90_000, 110_000, 130_000, 150_000]
