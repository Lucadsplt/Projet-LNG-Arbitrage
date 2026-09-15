# Note de décision — Arbitrage GNL Europe / Asie

**Contexte.** Une cargaison de GNL chargée au Golfe du Mexique (type Sabine
Pass, ~3,5 TBtu) doit être routée vers l'Europe (valorisée au TTF) ou
l'Asie (valorisée au JKM). Le modèle calcule le **netback** de chaque
destination — le prix de marché moins tous les coûts variables
d'acheminement — et recommande la route qui maximise la valeur nette.

## Hypothèses

| Catégorie | Paramètre | Valeur |
|---|---|---|
| Structurelle | Taille de cargaison | 3,5 TBtu |
| Structurelle | Boil-off | 0,1 %/jour |
| Structurelle | Coût FOB | 115 % Henry Hub + 3,00 $/MMBtu (tolling) |
| Structurelle | Routes | Europe 14j · Asie-Panama 27j (+ péage 900 k$) |
| Live (auto) | TTF, Henry Hub, EUR/USD | récupérés à chaque exécution (yfinance / EIA) |
| **Fragile (manuelle)** | **JKM** | 11,50 $/MMBtu — pas de source gratuite |
| **Fragile (manuelle)** | **Taux d'affrètement** | 65 000 $/jour — pas de source gratuite |

Le détail et le raisonnement économique de chaque hypothèse sont dans
[`README.md`](../README.md) et [`src/config.py`](../src/config.py).

## Résultat chiffré (données du jour de l'exécution)

Avec un TTF à **79,5 €/MWh** (soit ~26,9 $/MMBtu converti) et un Henry Hub
à **2,91 $/MMBtu** :

| | Europe | Asie (Panama) |
|---|---|---|
| Netback | **19,50 $/MMBtu** | 3,58 $/MMBtu |

**Recommandation : Europe**, avec un écart de ~15,9 $/MMBtu. La table de
sensibilité (`outputs/charts/sensitivity_heatmap.png`) montre que ce n'est
pas un cas limite : il faudrait un JKM très supérieur à sa valeur actuelle
pour inverser la décision, quel que soit le taux de fret retenu dans la
plage testée (30 000 à 150 000 $/jour).

## Limites

- **JKM et taux de fret sont des hypothèses figées, pas des flux live**
  (pas de source gratuite fiable). Le résultat ci-dessus l'illustre bien :
  le TTF a fortement monté depuis la dernière mise à jour manuelle du JKM,
  ce qui gonfle artificiellement l'écart en faveur de l'Europe. Dans la
  réalité, TTF et JKM sont partiellement corrélés — un vrai desk
  réajusterait les deux ensemble.
- **Aller simple, pas aller-retour** : le modèle ignore le coût de
  repositionnement du navire, ce qui sous-estime le coût réel côté
  armateur (choix assumé et documenté, cf. README).
- **Péage de Panama moyen**, alors qu'il varie fortement avec les
  enchères de créneau en période de congestion (ex. sécheresse 2023).
- **Pas de valeur d'option de déroutage** : un vrai trader peut changer
  la destination en cours de route si les prix bougent ; le modèle
  compare deux routes figées au moment du chargement.
- **Une cargaison isolée**, pas un portefeuille/une flotte.

## Ce que je ferais avec plus de données

1. **Brancher un flux JKM et fret payant** (Platts, Spark Commodities,
   Baltic Exchange) pour remplacer les hypothèses fixes par des séries
   réelles, et surtout **mesurer la corrélation TTF/JKM** plutôt que de
   les traiter comme deux variables indépendantes.
2. **Backtester le modèle sur 2022-2025** : combien de fois l'Asie
   l'aurait emporté sur l'Europe, et ce qu'une stratégie "toujours
   Europe" aurait laissé sur la table (chiffré en $/cargaison).
3. **Régaz et tolling fee par terminal/contrat réel** plutôt qu'une
   moyenne de marché.
4. **Élargir à un portefeuille de cargaisons** (plusieurs fenêtres de
   chargement, plusieurs navires) pour une vraie optimisation de
   routing, plutôt qu'une décision isolée cargaison par cargaison.
