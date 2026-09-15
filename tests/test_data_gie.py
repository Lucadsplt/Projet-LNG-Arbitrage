import pytest

from src.data_gie import GieFetchError, fetch_alsi, json_vers_dataframe

REPONSE_EXEMPLE = {
    "last_page": 1,
    "total": 2,
    "dataset": "EU",
    "gas_day": "2026-06-15",
    "data": [
        {
            "name": "France",
            "code": "fr",
            "gasDayStart": "2026-06-15",
            "inventory": "500.00",
            "sendOut": "300.5",
            "dtmi": "1000.00",
            "dtrs": "600.0",
        },
        {
            "name": "Belgium",
            "code": "be",
            "gasDayStart": "2026-06-14",
            "inventory": "200.00",
            "sendOut": "100.0",
            "dtmi": "400.00",
            "dtrs": "200.0",
        },
    ],
}


def test_json_vers_dataframe_colonnes_et_taux_remplissage():
    df = json_vers_dataframe(REPONSE_EXEMPLE)
    assert list(df.columns) == [
        "name", "code", "gasDayStart", "inventory", "sendOut", "dtmi", "dtrs", "taux_remplissage",
    ]
    # France : inventory 500 / dtmi 1000 = 0,5 de taux de remplissage
    ligne_france = df[df["code"] == "fr"].iloc[0]
    assert ligne_france["taux_remplissage"] == pytest.approx(0.5)


def test_json_vers_dataframe_trie_par_date_croissante():
    df = json_vers_dataframe(REPONSE_EXEMPLE)
    assert df["gasDayStart"].is_monotonic_increasing


def test_json_vers_dataframe_reponse_sans_donnees():
    df = json_vers_dataframe({"data": []})
    assert df.empty
    assert "taux_remplissage" in df.columns


def test_fetch_alsi_sans_cle_leve_erreur_claire(monkeypatch):
    monkeypatch.delenv("GIE_API_KEY", raising=False)
    with pytest.raises(GieFetchError, match="GIE_API_KEY"):
        fetch_alsi(api_key=None)
