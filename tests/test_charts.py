import pandas as pd
import pytest

from src import charts, config


def test_grille_sensibilite_dimensions():
    grille = charts._grille_sensibilite(ttf_usd_mmbtu=10.129, cout_fob=6.68)
    assert len(grille) == len(config.SENSIBILITE_TAUX_FRET)
    assert all(len(ligne) == len(config.SENSIBILITE_ECARTS_JKM_TTF) for ligne in grille)


def test_grille_sensibilite_valeur_connue():
    # Reprend le cas deja verifie manuellement sur le classeur Excel du
    # Jalon 6 : taux de fret 70 000 $/jour, ecart JKM-TTF = 0 -> delta
    # attendu -0.749 $/MMBtu (l'Europe l'emporte, pas de spread pour
    # compenser le fret).
    grille = charts._grille_sensibilite(ttf_usd_mmbtu=10.128956623681127, cout_fob=6.68)
    indice_taux = config.SENSIBILITE_TAUX_FRET.index(70_000)
    indice_ecart = config.SENSIBILITE_ECARTS_JKM_TTF.index(0.0)
    assert grille[indice_taux][indice_ecart] == pytest.approx(-0.749, abs=0.001)


def test_graphe_comparaison_netback_gere_les_sources_indisponibles(tmp_path, monkeypatch):
    monkeypatch.setattr(charts.data_prices, "fetch_ttf",
                         lambda: pd.DataFrame(columns=["date", "ttf_eur_mwh"]))
    monkeypatch.setattr(charts.data_prices, "fetch_henry_hub",
                         lambda: pd.DataFrame(columns=["date", "henry_hub_usd_mmbtu"]))
    monkeypatch.setattr(charts.data_prices, "fetch_eur_usd",
                         lambda: pd.DataFrame(columns=["date", "eur_usd"]))

    chemin = charts.graphe_comparaison_netback(chemin_sortie=tmp_path / "netback.png")
    assert chemin.exists()


def test_graphe_series_prix_gere_les_donnees_vides(tmp_path, monkeypatch):
    monkeypatch.setattr(charts.data_prices, "fetch_ttf",
                         lambda: pd.DataFrame(columns=["date", "ttf_eur_mwh"]))
    monkeypatch.setattr(charts.data_prices, "fetch_henry_hub",
                         lambda: pd.DataFrame(columns=["date", "henry_hub_usd_mmbtu"]))

    chemin = charts.graphe_series_prix(chemin_sortie=tmp_path / "prix.png")
    assert chemin.exists()


def test_graphe_dashboard_gie_sans_cle_produit_un_placeholder(tmp_path, monkeypatch):
    monkeypatch.delenv("GIE_API_KEY", raising=False)
    chemin = charts.graphe_dashboard_gie(chemin_sortie=tmp_path / "gie.png")
    assert chemin.exists()


def test_generer_tous_les_graphes_continue_si_une_source_echoue(tmp_path, monkeypatch):
    monkeypatch.setattr(charts, "OUTPUT_DIR", tmp_path)
    monkeypatch.setattr(charts.data_prices, "fetch_ttf",
                         lambda: pd.DataFrame(columns=["date", "ttf_eur_mwh"]))
    monkeypatch.setattr(charts.data_prices, "fetch_henry_hub",
                         lambda: pd.DataFrame(columns=["date", "henry_hub_usd_mmbtu"]))
    monkeypatch.setattr(charts.data_prices, "fetch_eur_usd",
                         lambda: pd.DataFrame(columns=["date", "eur_usd"]))
    monkeypatch.delenv("GIE_API_KEY", raising=False)

    chemins = charts.generer_tous_les_graphes()
    assert len(chemins) == 4
    assert all(c.exists() for c in chemins)
