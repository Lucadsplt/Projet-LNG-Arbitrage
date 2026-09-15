"""
Point d'entree unique du projet : recupere les dernieres donnees,
met a jour le classeur Excel, et regenere les graphes.

    python run_pipeline.py
"""

import logging

from src.charts import generer_tous_les_graphes
from src.data_prices import update_price_data
from src.update_excel import mettre_a_jour_classeur


def main():
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    print("1/3 - Recuperation des prix (TTF, Henry Hub)...")
    update_price_data()

    print("2/3 - Mise a jour du classeur Excel (excel/modele_arbitrage.xlsx)...")
    mettre_a_jour_classeur()

    print("3/3 - Generation des graphes (outputs/charts/)...")
    for chemin in generer_tous_les_graphes():
        print(f"  - {chemin}")

    print("Termine.")


if __name__ == "__main__":
    main()
