import pytest

from src.routing import jours_de_mer, cout_fret_usd_mmbtu, comparer_routes


def test_jours_de_mer_par_route():
    assert jours_de_mer("europe") == 14
    assert jours_de_mer("asia_panama") == 27
    assert jours_de_mer("asia_cape") == 37


def test_cout_fret_europe_sans_peage():
    # 65 000 $/jour x 14 jours = 910 000 $ ; / 3 500 000 MMBtu = 0,26 $/MMBtu
    resultat = cout_fret_usd_mmbtu("europe", taux_affretement_usd_par_jour=65_000)
    assert resultat == pytest.approx(0.26, abs=0.001)


def test_cout_fret_asie_panama_avec_peage():
    # (65 000 x 27 + 900 000) / 3 500 000 = 0,759 $/MMBtu
    resultat = cout_fret_usd_mmbtu("asia_panama", taux_affretement_usd_par_jour=65_000)
    assert resultat == pytest.approx(0.759, abs=0.001)


def test_cap_peut_etre_moins_cher_que_panama_malgre_plus_de_jours():
    # Le peage de Panama (900 000 $, fixe) peut renverser la comparaison
    # malgre un trajet plus long (37 jours) via le Cap de Bonne-Esperance.
    fret_panama = cout_fret_usd_mmbtu("asia_panama", taux_affretement_usd_par_jour=65_000)
    fret_cape = cout_fret_usd_mmbtu("asia_cape", taux_affretement_usd_par_jour=65_000)
    assert fret_cape < fret_panama


def test_comparer_routes_bout_en_bout():
    # Reprend le scenario "Asie gagne" du Jalon 2, mais construit cette
    # fois le fret depuis un taux d'affretement plutot que de le saisir
    # directement.
    scenarios = {
        "europe": dict(
            prix_rendu=10.13, cout_fob=6.45, frais_regaz=0.40,
            taux_affretement_usd_par_jour=65_000,
        ),
        "asia_panama": dict(
            prix_rendu=11.50, cout_fob=6.45, frais_regaz=0.50,
            taux_affretement_usd_par_jour=65_000,
        ),
    }
    recommandation, netbacks = comparer_routes(scenarios)
    assert recommandation == "asia_panama"
    assert netbacks["asia_panama"] > netbacks["europe"]
