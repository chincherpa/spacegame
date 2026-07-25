"""
Tests für das Verkaufssystem im Shop.
"""
import pytest

import shop
from shop import SHOP_MATERIALIEN, VERKAUFSPREISE


class TestVerkaufbarkeit:
    def test_bekanntes_material_ist_verkaufbar(self):
        assert shop.ist_verkaufbar('Eisenbarren') is True

    def test_unbekanntes_material_ist_nicht_verkaufbar(self):
        assert shop.ist_verkaufbar('Warp-Antrieb') is False

    @pytest.mark.parametrize('material', sorted(shop.NICHT_VERKAUFBAR))
    def test_fortschrittsgegenstaende_sind_geschuetzt(self, material):
        assert shop.ist_verkaufbar(material) is False

    def test_preisliste_und_sperrliste_ueberschneiden_sich_nicht(self):
        assert not (set(VERKAUFSPREISE) & shop.NICHT_VERKAUFBAR)


class TestVerkaufspreis:
    def test_preis_skaliert_mit_menge(self):
        assert shop.verkaufspreis('Eisenbarren', 3) == VERKAUFSPREISE['Eisenbarren'] * 3

    def test_nicht_verkaufbares_material_kostet_nichts(self):
        assert shop.verkaufspreis('Mondbasen Bauplan', 5) == 0

    def test_negative_menge_ergibt_null(self):
        assert shop.verkaufspreis('Eisenbarren', -3) == 0

    @pytest.mark.parametrize('material', sorted(VERKAUFSPREISE))
    def test_alle_preise_sind_positiv(self, material):
        assert VERKAUFSPREISE[material] > 0

    @pytest.mark.parametrize('material', sorted(SHOP_MATERIALIEN))
    def test_verkauf_unter_einkauf(self, material):
        """Sonst liesse sich durch Kaufen und Verkaufen beliebig Geld drucken."""
        assert VERKAUFSPREISE[material] < SHOP_MATERIALIEN[material]['Kosten']


class TestVerkaufen:
    def test_erfolgreicher_verkauf(self):
        inventar = {'Eisenbarren': 10}
        erfolg, erloes, _ = shop.verkaufe(inventar, 'Eisenbarren', 4)
        assert erfolg is True
        assert erloes == VERKAUFSPREISE['Eisenbarren'] * 4
        assert inventar['Eisenbarren'] == 6

    def test_verkauf_des_gesamten_bestands(self):
        inventar = {'Gold': 2}
        erfolg, _, _ = shop.verkaufe(inventar, 'Gold', 2)
        assert erfolg is True
        assert inventar['Gold'] == 0

    def test_zu_wenig_bestand_aendert_nichts(self):
        inventar = {'Eisenbarren': 2}
        erfolg, erloes, meldung = shop.verkaufe(inventar, 'Eisenbarren', 5)
        assert erfolg is False
        assert erloes == 0
        assert inventar['Eisenbarren'] == 2
        assert 'Nicht genug' in meldung

    def test_gesperrtes_material_kann_nicht_verkauft_werden(self):
        inventar = {'Mondbasen Bauplan': 3}
        erfolg, _, _ = shop.verkaufe(inventar, 'Mondbasen Bauplan', 1)
        assert erfolg is False
        assert inventar['Mondbasen Bauplan'] == 3

    @pytest.mark.parametrize('menge', [0, -1])
    def test_ungueltige_menge(self, menge):
        inventar = {'Eisenbarren': 5}
        erfolg, _, _ = shop.verkaufe(inventar, 'Eisenbarren', menge)
        assert erfolg is False
        assert inventar['Eisenbarren'] == 5

    def test_material_ohne_bestand(self):
        erfolg, _, _ = shop.verkaufe({}, 'Eisenbarren', 1)
        assert erfolg is False


class TestVerkaufbareMaterialien:
    def test_nur_materialien_mit_bestand(self):
        inventar = {'Eisenbarren': 3, 'Gold': 0, 'Staub': 5}
        assert shop.verkaufbare_materialien(inventar) == ['Eisenbarren', 'Staub']

    def test_gesperrte_materialien_tauchen_nicht_auf(self):
        inventar = {'Mondbasen Bauplan': 2, 'Eisenbarren': 1}
        assert shop.verkaufbare_materialien(inventar) == ['Eisenbarren']

    def test_unbekannte_materialien_tauchen_nicht_auf(self):
        assert shop.verkaufbare_materialien({'Sternenstaub': 9}) == []

    def test_leeres_inventar(self):
        assert shop.verkaufbare_materialien({}) == []

    def test_ergebnis_ist_sortiert(self):
        inventar = {'Werkzeug': 1, 'Eisenbarren': 1, 'Gold': 1}
        materialien = shop.verkaufbare_materialien(inventar)
        assert materialien == sorted(materialien)


class TestPreisdatenKonsistenz:
    @pytest.mark.parametrize('material', sorted(VERKAUFSPREISE))
    def test_verkaufbare_materialien_existieren(self, material):
        from materials import MATERIALS
        assert material in MATERIALS, f'{material} ist in materials.py unbekannt'

    def test_teure_materialien_bringen_mehr(self):
        assert VERKAUFSPREISE['Gold'] > VERKAUFSPREISE['Eisenbarren']
        assert VERKAUFSPREISE['Seltene_Mineralien'] > VERKAUFSPREISE['Mondgestein']
