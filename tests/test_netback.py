import pytest

from src.netback import netback, compare_destinations, ttf_eur_mwh_to_usd_mmbtu


def test_netback_manual_calculation():
    # Chiffres ronds, verifiables a la main :
    # perte_boil_off = 0.001 * 10 jours * 10 $/MMBtu = 0.10
    # netback = 10 - 6 - 0.5 - 0.10 - 0.3 = 3.10
    resultat = netback(
        prix_rendu=10,
        cout_fob=6,
        fret=0.5,
        jours_de_mer=10,
        frais_regaz=0.3,
        boil_off_rate=0.001,
    )
    assert resultat == pytest.approx(3.10)


def test_ttf_conversion_eur_mwh_vers_usd_mmbtu():
    # 32 EUR/MWh / 3,412 = 9,3788 EUR/MMBtu ; x 1,08 = 10,129 $/MMBtu
    resultat = ttf_eur_mwh_to_usd_mmbtu(32, eur_usd_rate=1.08, mwh_to_mmbtu=3.412)
    assert resultat == pytest.approx(10.129, abs=0.01)


def test_compare_destinations_asie_gagne_si_spread_suffisant():
    # TTF converti ~10,13 $/MMBtu vs JKM 11,50 $/MMBtu : l'ecart de prix
    # (1,37 $/MMBtu) couvre largement le surcout de transport vers l'Asie.
    destinations = {
        "europe": dict(
            prix_rendu=10.13, cout_fob=6.45, fret=0.26,
            jours_de_mer=14, frais_regaz=0.40,
        ),
        "asia_panama": dict(
            prix_rendu=11.50, cout_fob=6.45, fret=0.76,
            jours_de_mer=27, frais_regaz=0.50,
        ),
    }
    recommandation, netbacks = compare_destinations(destinations)
    assert recommandation == "asia_panama"
    assert netbacks["asia_panama"] > netbacks["europe"]


def test_compare_destinations_europe_gagne_si_spread_insuffisant():
    # Meme cas, mais JKM ne depasse plus TTF que de 0,17 $/MMBtu : ca ne
    # suffit plus a couvrir le surcout de transport vers l'Asie.
    destinations = {
        "europe": dict(
            prix_rendu=10.13, cout_fob=6.45, fret=0.26,
            jours_de_mer=14, frais_regaz=0.40,
        ),
        "asia_panama": dict(
            prix_rendu=10.30, cout_fob=6.45, fret=0.76,
            jours_de_mer=27, frais_regaz=0.50,
        ),
    }
    recommandation, netbacks = compare_destinations(destinations)
    assert recommandation == "europe"
    assert netbacks["europe"] > netbacks["asia_panama"]
