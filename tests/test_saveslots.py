"""
Tests für saveslots: mehrere Speicherstände, Slot-Infos und Fehlerfälle.
"""
import copy
import json

import pytest

import config
import saveslots


@pytest.fixture
def slot_sandbox(tmp_path, monkeypatch):
    """Legt die Slot-Dateien in ein temporäres Verzeichnis."""
    monkeypatch.setattr(config, 'SAVEFILE', str(tmp_path / 'savefile.json'))
    return tmp_path


class TestSlotDatei:
    def test_slot1_nutzt_die_klassische_datei(self, slot_sandbox):
        assert saveslots.slot_datei(1) == config.SAVEFILE

    def test_weitere_slots_bekommen_suffix(self, slot_sandbox):
        assert saveslots.slot_datei(2).endswith('savefile_2.json')
        assert saveslots.slot_datei(3).endswith('savefile_3.json')

    def test_alle_slots_haben_unterschiedliche_dateien(self, slot_sandbox):
        dateien = {saveslots.slot_datei(s) for s in range(1, saveslots.SLOT_ANZAHL + 1)}
        assert len(dateien) == saveslots.SLOT_ANZAHL

    @pytest.mark.parametrize('slot', [0, -1, 99])
    def test_ungueltiger_slot_wirft(self, slot_sandbox, slot):
        with pytest.raises(ValueError):
            saveslots.slot_datei(slot)


class TestSpeichernUndLaden:
    def test_roundtrip(self, slot_sandbox, fresh_gamestate):
        gs = copy.deepcopy(fresh_gamestate)
        gs['Credits'] = 4711
        saveslots.speichere_slot(2, gs)
        assert saveslots.lade_slot(2)['Credits'] == 4711

    def test_slots_sind_unabhaengig(self, slot_sandbox, fresh_gamestate):
        a = copy.deepcopy(fresh_gamestate); a['Credits'] = 1
        b = copy.deepcopy(fresh_gamestate); b['Credits'] = 2
        saveslots.speichere_slot(1, a)
        saveslots.speichere_slot(2, b)
        assert saveslots.lade_slot(1)['Credits'] == 1
        assert saveslots.lade_slot(2)['Credits'] == 2

    def test_leerer_slot_liefert_none(self, slot_sandbox):
        assert saveslots.lade_slot(3) is None

    def test_umlaute_bleiben_erhalten(self, slot_sandbox, fresh_gamestate):
        gs = copy.deepcopy(fresh_gamestate)
        gs['Log'] = ['Raumsonde für Mondmission gestartet']
        saveslots.speichere_slot(1, gs)
        assert saveslots.lade_slot(1)['Log'] == ['Raumsonde für Mondmission gestartet']

    def test_beschaedigte_datei_liefert_none_statt_absturz(self, slot_sandbox):
        with open(saveslots.slot_datei(2), 'w') as fh:
            fh.write('{kein gueltiges json')
        assert saveslots.lade_slot(2) is None

    def test_liste_statt_dict_wird_abgelehnt(self, slot_sandbox):
        with open(saveslots.slot_datei(2), 'w') as fh:
            json.dump([1, 2, 3], fh)
        assert saveslots.lade_slot(2) is None


class TestSlotInfo:
    def test_leerer_slot(self, slot_sandbox):
        info = saveslots.slot_info(1)
        assert info['vorhanden'] is False
        assert info['beschaedigt'] is False

    def test_gefuellter_slot_zeigt_kennzahlen(self, slot_sandbox, fresh_gamestate):
        gs = copy.deepcopy(fresh_gamestate)
        gs.update({'Ticks': 42, 'Credits': 99, 'Forschungspunkte': 7})
        saveslots.speichere_slot(1, gs)
        info = saveslots.slot_info(1)
        assert (info['vorhanden'], info['ticks'], info['credits']) == (True, 42, 99)
        assert info['gespeichert']

    def test_beschaedigter_slot_wird_markiert(self, slot_sandbox):
        with open(saveslots.slot_datei(1), 'w') as fh:
            fh.write('kaputt')
        info = saveslots.slot_info(1)
        assert info['vorhanden'] is True
        assert info['beschaedigt'] is True

    @pytest.mark.parametrize('mutation,erwartet', [
        (lambda gs: None, 'Spielbeginn'),
        (lambda gs: gs['Forschung']['Eisenbarren'].update(erforscht=True), '1 Technologien erforscht'),
        (lambda gs: gs['Planeten']['Mond'].update(entdeckt=True), 'Mond entdeckt'),
        (lambda gs: gs['Planeten']['Mars'].update(entdeckt=True), 'Mars entdeckt'),
        (lambda gs: gs.update(Spiel_gewonnen=True), 'Gewonnen'),
    ])
    def test_fortschrittstext(self, slot_sandbox, fresh_gamestate, mutation, erwartet):
        gs = copy.deepcopy(fresh_gamestate)
        mutation(gs)
        saveslots.speichere_slot(1, gs)
        assert saveslots.slot_info(1)['fortschritt'] == erwartet

    def test_alle_slots_liefert_vollstaendige_liste(self, slot_sandbox):
        infos = saveslots.alle_slots()
        assert len(infos) == saveslots.SLOT_ANZAHL
        assert [i['slot'] for i in infos] == list(range(1, saveslots.SLOT_ANZAHL + 1))


class TestBeschriftungUndLoeschen:
    def test_beschriftung_leerer_slot(self, slot_sandbox):
        assert '(leer)' in saveslots.slot_beschriftung(saveslots.slot_info(2))

    def test_beschriftung_gefuellter_slot(self, slot_sandbox, fresh_gamestate):
        gs = copy.deepcopy(fresh_gamestate)
        gs['Ticks'] = 5
        saveslots.speichere_slot(1, gs)
        text = saveslots.slot_beschriftung(saveslots.slot_info(1))
        assert 'Slot 1' in text and 'Zyklus 5' in text

    def test_loeschen(self, slot_sandbox, fresh_gamestate):
        saveslots.speichere_slot(2, copy.deepcopy(fresh_gamestate))
        assert saveslots.loesche_slot(2) is True
        assert saveslots.lade_slot(2) is None

    def test_loeschen_eines_leeren_slots_ist_harmlos(self, slot_sandbox):
        assert saveslots.loesche_slot(3) is False
