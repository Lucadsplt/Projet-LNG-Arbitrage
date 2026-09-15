# Modèle d'arbitrage et de routing de cargaisons GNL

**[Tableau de bord interactif](https://lucadsplt.github.io/Projet-LNG-Arbitrage/dashboard.html)** &middot; [page du projet](https://lucadsplt.github.io/Projet-LNG-Arbitrage/)

Simulation de la décision qu'un desk GNL prend chaque jour : une cargaison
chargée au Golfe du Mexique (type Sabine Pass) doit-elle partir vers
l'Europe (prix TTF) ou vers l'Asie (prix JKM), une fois déduits tous les
coûts de transport ? Le modèle calcule le **netback** de chaque
destination et recommande la route qui maximise la valeur nette de la
cargaison.

Contexte complet du projet (pourquoi ce projet, raisonnement économique
détaillé de chaque formule) : voir [`docs/Projet_GNL_Contexte_et_Explications.docx`](docs/Projet_GNL_Contexte_et_Explications.docx).

## Arborescence du repo

```
Projet-GNL/
├── src/
│   ├── config.py             # hypothèses métier centralisées (Jalon 1)
│   ├── netback.py            # calcul du netback + comparaison Europe/Asie (Jalon 2)
│   ├── routing.py            # jours de voyage, fret, boil-off par route (Jalon 3)
│   ├── data_prices.py        # récupération TTF / Henry Hub (Jalon 4)
│   ├── data_gie.py           # send-out et stocks terminaux GNL (GIE ALSI) (Jalon 5)
│   ├── build_excel_model.py  # génère excel/modele_arbitrage.xlsx (Jalon 6)
│   ├── update_excel.py       # pont Python -> Excel (Jalon 7)
│   └── charts.py             # graphes de sortie (Jalon 8)
├── tests/                 # un fichier de test par module de src/ (29 tests)
├── excel/
│   └── modele_arbitrage.xlsx  # classeur de décision avec table de sensibilité (Jalon 6)
├── data/
│   └── prices/             # CSV de prix (TTF, Henry Hub) (Jalon 4)
├── outputs/
│   ├── charts/              # graphes générés (Jalon 8)
│   └── note.md               # note d'une page (Jalon 8)
├── docs/
│   └── Projet_GNL_Contexte_et_Explications.docx  # cahier des charges / contexte
├── run_pipeline.py        # point d'entrée unique (Jalon 8)
├── requirements.txt
├── .env.example
└── .gitignore
```

## Lancer le projet en une commande

```bash
pip install -r requirements.txt
cp .env.example .env   # optionnel : cles EIA / GIE, voir plus bas
python run_pipeline.py
```

Ça enchaîne : récupération des derniers prix (TTF, Henry Hub) →
mise à jour du classeur `excel/modele_arbitrage.xlsx` → régénération des
4 graphes dans `outputs/charts/`. Le `.env` est optionnel : sans clé
`GIE_API_KEY`, tout le reste fonctionne quand même — seul le graphe
`gie_dashboard.png` devient un visuel "donnée indisponible" explicite
plutôt qu'un échec silencieux. Sans clé `EIA_API_KEY`, le Henry Hub
bascule automatiquement sur yfinance (voir Jalon 4).

La note de synthèse est dans [`outputs/note.md`](outputs/note.md).

## Tableau de bord (snapshot)

**En ligne :** https://lucadsplt.github.io/Projet-LNG-Arbitrage/dashboard.html (servi par GitHub Pages depuis `docs/dashboard.html`, lien public, sans compte requis).

Code source : [`outputs/dashboard.html`](outputs/dashboard.html) — une page autonome (HTML/CSS/JS, sans dépendance) qui reprend les résultats de ce snapshot dans une mise en page façon BI : recommandation, netback détaillé par étape (waterfall), historique TTF/Henry Hub, et la table de sensibilité avec un point mobile. Les curseurs JKM et taux de fret sont interactifs — ils réimplémentent en JavaScript les mêmes formules que `src/netback.py` et `src/routing.py`, pour recalculer sans recharger. **Ce n'est pas un composant du pipeline** : c'est un instantané figé sur les données du jour où il a été généré, à régénérer manuellement si les données changent significativement (les deux copies, `outputs/` et `docs/`, doivent alors être remises à jour ensemble).

## Statut des jalons

- [x] Jalon 1 — squelette du repo + `src/config.py` (hypothèses métier)
- [x] Jalon 2 — calcul du netback + tests
- [x] Jalon 3 — routing (jours de voyage, fret, boil-off par route)
- [x] Jalon 4 — prix TTF / Henry Hub
- [x] Jalon 5 — donnée physique GIE ALSI
- [x] Jalon 6 — modèle Excel
- [x] Jalon 7 — pont Python -> Excel
- [x] Jalon 8 — graphes + note d'une page

## Hypothèses métier (Jalon 1)

Toutes les hypothèses sont centralisées dans [`src/config.py`](src/config.py) —
c'est la source de vérité, à ne jamais dupliquer ailleurs dans le code.

| Hypothèse | Valeur par défaut | Pourquoi |
|---|---|---|
| Taille de cargaison | 3,5 TBtu | Contenu énergétique d'un méthanier standard (160-174 000 m³) |
| Boil-off | 0,1 %/jour | Ordre de grandeur observé sur un méthanier moderne |
| Feedgas | 115 % du Henry Hub | Structure typique d'un contrat d'enlèvement américain (type Sabine Pass) |
| Tolling fee de liquéfaction | 3,00 $/MMBtu | Fourchette typique des contrats existants (2,25-3,50 $/MMBtu) |
| Route Europe | 14 jours | US Gulf -> Europe, via l'Atlantique |
| Route Asie (Panama) | 27 jours | US Gulf -> Asie, via le canal de Panama |
| Route Asie (Cap) | 37 jours | US Gulf -> Asie, via le cap de Bonne-Espérance |
| Péage Panama | 900 000 $ | Ordre de grandeur du tarif de base pour un méthanier standard |
| Taux EUR/USD | 1,08 | Valeur par défaut, remplacée par une donnée live au Jalon 4 |
| Conversion €/MWh -> $/MMBtu | ÷ 3,412 puis × EUR/USD | 1 MWh = 3,412 MMBtu (conversion d'énergie) |

**Hypothèses les plus fragiles, assumées et documentées** : le prix **JKM**
(pas de source gratuite fiable) et le **taux d'affrètement** (fret,
$/jour). Ces deux paramètres seront isolés clairement et feront l'objet de
la table de sensibilité au Jalon 6.

## Fraîcheur des hypothèses : trois catégories, trois traitements

Pour que le modèle (et le classeur Excel du Jalon 6) ne devienne pas
obsolète en quelques semaines, chaque hypothèse est classée dans une de
ces trois catégories, qui déterminent comment elle est tenue à jour :

| Catégorie | Exemples | Mode de mise à jour |
|---|---|---|
| **Données de marché live, gratuites** | TTF, Henry Hub, EUR/USD | Automatique : `data_prices.py` (Jalon 4) va chercher le dernier prix, `update_excel.py` (Jalon 7) le réinjecte dans le classeur qui se recalcule seul. |
| **Hypothèses structurelles, stables sur des mois/années** | Tolling fee, multiplicateur feedgas, boil-off, taille cargaison, jours de route | Révisées ponctuellement dans `config.py` (ex. si un nouveau contrat de liquéfaction est annoncé), pas de flux temps réel nécessaire. |
| **Paramètres de marché volatils, sans source gratuite** | JKM, taux d'affrètement ($/jour) | Pas d'automatisation possible (données Platts/Baltic Exchange payantes) : ce sont des **cellules d'entrée modifiables directement dans le classeur Excel** (Jalon 6), pas des constantes cachées dans le code. |
