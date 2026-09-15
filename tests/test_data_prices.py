import pandas as pd

import src.data_prices as data_prices
from src.data_prices import _nettoyer_serie_yfinance, fetch_henry_hub, fetch_henry_hub_eia


def test_nettoyer_serie_yfinance_colonnes_simples():
    df_brut = pd.DataFrame(
        {
            "Open": [1.0, 2.0, 3.0],
            "Close": [1.1, None, 3.3],
        },
        index=pd.to_datetime(["2026-01-01", "2026-01-02", "2026-01-03"]),
    )
    resultat = _nettoyer_serie_yfinance(df_brut, "prix")
    assert list(resultat.columns) == ["date", "prix"]
    assert len(resultat) == 2  # la ligne avec Close manquant est retiree
    assert resultat["prix"].tolist() == [1.1, 3.3]


def test_nettoyer_serie_yfinance_colonnes_multi_index():
    # yfinance renvoie parfois des colonnes a deux niveaux (Close, ticker)
    colonnes = pd.MultiIndex.from_product([["Close", "Open"], ["TTF=F"]])
    df_brut = pd.DataFrame(
        [[10.0, 9.0], [11.0, 9.5]],
        columns=colonnes,
        index=pd.to_datetime(["2026-01-01", "2026-01-02"]),
    )
    resultat = _nettoyer_serie_yfinance(df_brut, "ttf_eur_mwh")
    assert list(resultat.columns) == ["date", "ttf_eur_mwh"]
    assert resultat["ttf_eur_mwh"].tolist() == [10.0, 11.0]


def test_nettoyer_serie_yfinance_dataframe_vide():
    resultat = _nettoyer_serie_yfinance(pd.DataFrame(), "prix")
    assert resultat.empty
    assert list(resultat.columns) == ["date", "prix"]


def test_fetch_henry_hub_eia_sans_cle_renvoie_dataframe_vide(monkeypatch):
    monkeypatch.delenv("EIA_API_KEY", raising=False)
    resultat = fetch_henry_hub_eia(api_key=None)
    assert resultat.empty


def test_fetch_eur_usd_en_echec_renvoie_dataframe_vide(monkeypatch):
    def yf_download_qui_echoue(*args, **kwargs):
        raise RuntimeError("pas de reseau")

    monkeypatch.setattr(data_prices.yf, "download", yf_download_qui_echoue)
    resultat = data_prices.fetch_eur_usd()
    assert resultat.empty
    assert list(resultat.columns) == ["date", "eur_usd"]


def test_fetch_henry_hub_bascule_sur_yfinance_si_eia_indisponible(monkeypatch):
    # EIA sans cle -> DataFrame vide -> fetch_henry_hub() doit basculer
    # sur le fallback yfinance. On remplace ce fallback par une fonction
    # factice pour que le test reste hors-ligne et deterministe.
    monkeypatch.delenv("EIA_API_KEY", raising=False)
    faux_df = pd.DataFrame({"date": ["2026-01-01"], "henry_hub_usd_mmbtu": [3.0]})
    monkeypatch.setattr(data_prices, "fetch_henry_hub_yfinance", lambda *a, **k: faux_df)

    resultat = fetch_henry_hub()
    assert resultat.equals(faux_df)
