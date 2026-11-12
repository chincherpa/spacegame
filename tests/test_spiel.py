"""
Tests gegen die echte Spiellogik in main.py (mit Fenster-Ersatz, siehe conftest).

Jeder Abschnitt sichert einen Befund aus docs/CODE_REVIEW.md ab.
"""
import json

import pytest

import saveslots


def ticks(spiel, anzahl):
    for _ in range(anzahl):
        spiel.verarbeite_tick()


def erforsche_alles(spiel):
    for eintrag in spiel.GAMESTATE['Forschung'].values():
        eintrag['erforscht'] = True


def entdecke(spiel, *planeten):
    for planet in planeten:
        spiel.GAMESTATE['Planeten'][planet]['entdeckt'] = True


def inventar(spiel):
    return spiel.GAMESTATE['Inventar']


# ---------------------------------------------------------------- Forschung

class TestForschung:
    def test_auswahl_waehrend_forschung_aendert_ergebnis_nicht(self, spiel):
        spiel.GAMESTATE['Forschung']['Eisenbarren']['erforscht'] = True
        spiel.iForschungspunkte = 10
        assert spiel.erforsche('Baumaterial')
        spiel.verarbeite_event('Erforsche Werkzeug', {})
        ticks(spiel, 3)
        assert spiel.GAMESTATE['Forschung']['Baumaterial']['erforscht']
        assert not spiel.GAMESTATE['Forschung']['Werkzeug']['erforscht']

    def test_abbruch_erstattet_kosten_der_laufenden_forschung(self, spiel):
        spiel.GAMESTATE['Forschung']['Eisenbarren']['erforscht'] = True
        spiel.iForschungspunkte = 10
        spiel.erforsche('Baumaterial')           # kostet 1
        spiel.verarbeite_event('Erforsche Werkzeug', {})   # kostet 2
        spiel.verarbeite_event('stop_research', {})
        assert spiel.iForschungspunkte == 10
        assert not spiel.bForschung_aktiv

    def test_voraussetzung_wird_geprueft(self, spiel):
        spiel.iForschungspunkte = 100
        assert not spiel.erforsche('Rakete')
        assert spiel.iForschungspunkte == 100

    def test_keine_zweite_forschung_parallel(self, spiel):
        spiel.iForschungspunkte = 100
        assert spiel.erforsche('Eisenbarren')
        spiel.GAMESTATE['Forschung']['Eisenbarren']['erforscht'] = True
        assert not spiel.erforsche('Baumaterial')

    def test_erforschte_technologie_ohne_punkte_zeigt_erforscht(self, spiel):
        spiel.GAMESTATE['Forschung']['Eisenbarren']['erforscht'] = True
        spiel.iForschungspunkte = 0
        spiel.zeige_Forschung('Eisenbarren')
        assert spiel.window['already_researched'].visible
        assert not spiel.window['comment'].visible
        assert not spiel.window['do_research'].visible

    def test_warteschlange_startet_sobald_punkte_reichen(self, spiel):
        spiel.iForschungspunkte = 5
        spiel.erforsche('Eisenbarren')
        spiel.verarbeite_event('Erforsche Werkzeug', {})
        spiel.verarbeite_event('queue_research', {})
        spiel.verarbeite_event('queue_research', {})   # doppelt zählt nicht
        assert spiel.forschungs_queue == ['Werkzeug']
        ticks(spiel, 3)
        assert spiel.GAMESTATE['Forschung']['Eisenbarren']['erforscht']
        assert not spiel.bForschung_aktiv              # 0 Punkte: wartet
        spiel.iForschungspunkte = 2
        ticks(spiel, 1)
        assert spiel.sLaufende_Forschung == 'Werkzeug'
        assert spiel.forschungs_queue == []


# ---------------------------------------------------------------- Werkstatt

class TestWerkstatt:
    def test_auswahl_waehrend_bau_aendert_ergebnis_nicht(self, spiel):
        erforsche_alles(spiel)
        assert spiel.baue('Baumaterial', 1)
        spiel.verarbeite_event('baue_Rakete', {})
        ticks(spiel, 2)
        assert inventar(spiel)['Baumaterial'] == 1
        assert spiel.GAMESTATE['Raumschiffe']['Erde']['Rakete']['Anzahl'] == 0

    def test_abbruch_erstattet_material_des_laufenden_baus(self, spiel):
        erforsche_alles(spiel)
        vorher = dict(inventar(spiel))
        spiel.baue('Baumaterial', 1)
        spiel.verarbeite_event('baue_Rakete', {})
        spiel.verarbeite_event('stop_bauen', {})
        assert inventar(spiel) == vorher

    def test_abbruch_liefert_fertige_stuecke(self, spiel):
        erforsche_alles(spiel)
        spiel.baue('Eisenbarren', 3)
        ticks(spiel, 3)                      # 1 Stück fertig (2 Zyklen), 2 offen
        spiel.stoppe_bauen()
        assert inventar(spiel)['Eisenbarren'] == 1
        assert inventar(spiel)['Roheisen'] == 9

    def test_unerforschtes_kann_nicht_gebaut_werden(self, spiel):
        assert not spiel.baue('Eisenbarren', 1)
        assert inventar(spiel)['Roheisen'] == 10

    def test_warteschlange_ueber_die_buttons(self, spiel):
        erforsche_alles(spiel)
        spiel.verarbeite_event('baue_Eisenbarren', {})
        spiel.window['anzahl_bauen'].update(value=2)
        spiel.verarbeite_event('do_bauen', {})
        assert spiel.window['queue_bauen'].visible
        spiel.window['anzahl_bauen'].update(value=3)
        spiel.verarbeite_event('queue_bauen', {})
        assert spiel.bau_queue == [{'name': 'Eisenbarren', 'anzahl': 3}]
        ticks(spiel, 4)                      # erster Auftrag fertig, zweiter startet
        assert inventar(spiel)['Eisenbarren'] == 2
        assert spiel.sLaufender_Bau == 'Eisenbarren' and spiel.iAnzahl_Bauen == 3
        ticks(spiel, 6)
        assert inventar(spiel)['Eisenbarren'] == 5
        assert not spiel.bBauen_aktiv

    def test_warteschlange_wartet_auf_material(self, spiel):
        erforsche_alles(spiel)
        spiel.bauauftrag_hinzufuegen('Werkzeug', 1)   # braucht Eisenbarren
        ticks(spiel, 2)
        assert not spiel.bBauen_aktiv and len(spiel.bau_queue) == 1
        assert 'wartet auf Eisenbarren' in spiel.window['bau_queue_anzeige'].get()
        inventar(spiel)['Eisenbarren'] = 1
        ticks(spiel, 1)
        assert spiel.sLaufender_Bau == 'Werkzeug'

    def test_weltraumstation_gewinnt_das_spiel(self, spiel):
        erforsche_alles(spiel)
        inventar(spiel).update({'Eisenbarren': 100, 'Werkzeug': 10, 'Mondbasen Bauplan': 1, 'Gold': 3})
        spiel.GAMESTATE['Raumschiffe']['Erde']['Mondlander']['Anzahl'] = 5
        assert spiel.baue('Weltraumstation', 1)
        ticks(spiel, 10)
        assert spiel.GAMESTATE['Spiel_gewonnen']
        assert spiel.GAMESTATE['Raumschiffe']['Erde']['Mondlander']['Anzahl'] == 0


# ---------------------------------------------------------------- Speichern

class TestSpeichern:
    def test_autosave_schreibt_in_den_geladenen_slot(self, spiel):
        spiel.dump_gamestate(1)
        spiel.iCredits = 777
        spiel.dump_gamestate(2)
        spiel.dump_gamestate(1)              # Slot 1 mit 777 überschreiben ...
        spiel.iCredits = 5
        spiel.dump_gamestate(1)              # ... und dann mit 5
        assert spiel.lade_spielstand(2)
        assert spiel.aktiver_slot == 2 and spiel.iCredits == 777
        spiel.iCredits = 800
        spiel.dump_gamestate()               # Autosave/Beenden ohne Slot-Angabe
        assert saveslots.lade_slot(2)['Credits'] == 800
        assert saveslots.lade_slot(1)['Credits'] == 5

    def test_beenden_speichert_in_aktiven_slot(self, spiel):
        spiel.dump_gamestate(3)
        spiel.iCredits = 42
        assert spiel.verarbeite_event(None, None) is False
        assert saveslots.lade_slot(3)['Credits'] == 42
        assert saveslots.lade_slot(1) is None

    def test_beenden_fasst_das_geschlossene_fenster_nicht_an(self, spiel):
        """Nach dem Klick auf das X meldet FreeSimpleGUI jeden Zugriff als Fehler."""
        status = spiel.window['save_status']

        def verboten(*args, **kwargs):
            raise AssertionError('Fenster ist geschlossen')
        status.update = verboten
        assert spiel.verarbeite_event(None, None) is False
        assert saveslots.lade_slot(1) is not None

    def test_naechster_start_laedt_den_zuletzt_benutzten_slot(self, spiel):
        import sys
        spiel.iCredits = 321
        spiel.dump_gamestate(2)
        assert saveslots.gemerkter_slot() == 2
        sys.modules.pop('main')
        import main
        assert main.aktiver_slot == 2 and main.iCredits == 321

    def test_gemerkter_slot_ohne_spielstand_faellt_auf_slot_1(self, spiel):
        saveslots.merke_slot(3)
        assert saveslots.gemerkter_slot() == 1

    def test_laufende_forschung_und_bau_ueberleben_das_laden(self, spiel):
        erforsche_alles(spiel)
        spiel.GAMESTATE['Forschung']['Weltraumstation']['erforscht'] = False
        spiel.iForschungspunkte = 80
        spiel.erforsche('Weltraumstation')
        spiel.baue('Eisenbarren', 4)
        spiel.bauauftrag_hinzufuegen('Baumaterial', 2)
        spiel.starte_erde_job('Bergbau')
        ticks(spiel, 1)
        spiel.dump_gamestate(1)

        assert spiel.lade_spielstand(1)
        assert spiel.sLaufende_Forschung == 'Weltraumstation'
        assert spiel.iAktueller_Forschungsfortschritt == 1
        assert (spiel.sLaufender_Bau, spiel.iAnzahl_Bauen, spiel.iAktueller_Baufortschritt) == ('Eisenbarren', 4, 1)
        assert spiel.bau_queue == [{'name': 'Baumaterial', 'anzahl': 2}]
        assert [j.name for j in spiel.erde_jobs_aktiv] == ['Bergbau']
        assert spiel.window['progressbar_Bauen'].visible

        ticks(spiel, 7)
        assert inventar(spiel)['Eisenbarren'] == 4
        ticks(spiel, 42)
        assert spiel.GAMESTATE['Forschung']['Weltraumstation']['erforscht']

    def test_alter_spielstand_bekommt_aktuelle_rezepte(self, spiel):
        alt = spiel.neuer_spielstand()
        alt['Werkstatt']['Eisenbarren'] = {'beschreibung': 'alt', 'dauer': 99, 'material': {'Roheisen': 7, 'Staub': 1}}
        alt['Planeten']['Erde']['Entfernung']['Mond'] = 50
        del alt['Lager'], alt['BauQueue']
        saveslots.speichere_slot(2, alt)
        assert spiel.lade_spielstand(2)
        assert spiel.GAMESTATE['Werkstatt']['Eisenbarren']['material'] == {'Roheisen': 1}
        assert spiel.GAMESTATE['Planeten']['Erde']['Entfernung']['Mond'] == 1
        assert spiel.GAMESTATE['Lager'] == {'Mond': {}, 'Mars': {}}

    def test_beschaedigter_spielstand_wird_gesichert(self, spiel, tmp_path):
        (tmp_path / 'savefile.json').write_text('{kaputt', encoding='utf-8')
        gs = spiel.load_gamestate(1)
        assert gs['Ticks'] == 0
        assert (tmp_path / 'savefile.json.beschaedigt').read_text(encoding='utf-8') == '{kaputt'
        assert not (tmp_path / 'savefile.json').exists()

    def test_speichern_hinterlaesst_keine_temp_datei(self, spiel, tmp_path):
        spiel.dump_gamestate(1)
        assert sorted(p.name for p in tmp_path.iterdir()) == ['savefile.json']
        json.loads((tmp_path / 'savefile.json').read_text(encoding='utf-8'))

    def test_neues_spiel_setzt_alles_zurueck(self, spiel):
        erforsche_alles(spiel)
        entdecke(spiel, 'Mond', 'Mars')
        spiel.iCredits = 999
        spiel.baue('Eisenbarren', 2)
        spiel.dump_gamestate(2)
        spiel.verarbeite_event('Neues Spiel::neues_spiel', {})
        assert spiel.iCredits == 10 and spiel.iTicks == 0
        assert not spiel.bBauen_aktiv
        assert not spiel.GAMESTATE['Forschung']['Eisenbarren']['erforscht']
        assert not spiel.window['tab_Reisen'].visible
        assert saveslots.lade_slot(2)['Credits'] == 10
        assert spiel.DEFAULT_GAMESTATE['Credits'] == 10     # Vorlage unverändert

    def test_neues_spiel_fragt_nach(self, spiel):
        import sys
        sys.modules['FreeSimpleGUI'].antwort_ja_nein = 'No'
        spiel.iCredits = 999
        spiel.verarbeite_event('Neues Spiel::neues_spiel', {})
        assert spiel.iCredits == 999


# ---------------------------------------------------------------- Reisen

def bereite_flug_vor(spiel, typ='Mondlander'):
    erforsche_alles(spiel)
    entdecke(spiel, 'Mond', 'Mars')
    spiel.GAMESTATE['Raumschiffe']['Erde'][typ]['Anzahl'] = 1
    inventar(spiel).update({'Treibstoff': 20, 'Wasser': 30, 'Werkzeug': 5, 'Baumaterial': 5})


class TestReisen:
    def test_negative_astronauten_werden_abgelehnt(self, spiel):
        bereite_flug_vor(spiel)
        assert not spiel.starte_reise('Mondlander', 'Erde', 'Mond', -3, {})
        assert spiel.GAMESTATE['Astronauten'] == {'Erde': 10, 'Mond': 0, 'Mars': 0}

    def test_negative_fracht_wird_abgelehnt(self, spiel):
        bereite_flug_vor(spiel)
        assert not spiel.starte_reise('Mondlander', 'Erde', 'Mond', 1, {'Werkzeug': -2})
        assert inventar(spiel)['Werkzeug'] == 5

    def test_gleicher_start_und_zielplanet(self, spiel):
        bereite_flug_vor(spiel)
        assert not spiel.starte_reise('Mondlander', 'Erde', 'Erde', 1, {})

    def test_fracht_landet_im_lager_des_ziels(self, spiel):
        bereite_flug_vor(spiel)
        assert spiel.starte_reise('Mondlander', 'Erde', 'Mond', 2, {'Werkzeug': 2, 'Baumaterial': 1})
        assert inventar(spiel)['Werkzeug'] == 3
        assert inventar(spiel)['Treibstoff'] == 19 and inventar(spiel)['Wasser'] == 28
        ticks(spiel, 1)
        assert spiel.GAMESTATE['Lager']['Mond'] == {'Werkzeug': 2, 'Baumaterial': 1}
        assert spiel.GAMESTATE['Astronauten']['Mond'] == 2
        assert spiel.GAMESTATE['Raumschiffe']['Mond']['Mondlander']['Anzahl'] == 1
        assert spiel.aktive_reisen == []

    def test_rueckfracht_kommt_aus_dem_lager(self, spiel):
        bereite_flug_vor(spiel)
        spiel.starte_reise('Mondlander', 'Erde', 'Mond', 2, {'Werkzeug': 2, 'Treibstoff': 1, 'Wasser': 2})
        ticks(spiel, 1)
        assert not spiel.starte_reise('Mondlander', 'Mond', 'Erde', 0, {'Werkzeug': 3})
        assert spiel.starte_reise('Mondlander', 'Mond', 'Erde', 2, {'Werkzeug': 2})
        ticks(spiel, 1)
        assert spiel.GAMESTATE['Lager']['Mond'] == {'Werkzeug': 0, 'Treibstoff': 0, 'Wasser': 0}
        assert inventar(spiel)['Werkzeug'] == 5

    def test_rueckflug_verbraucht_treibstoff_aus_dem_lager_vor_ort(self, spiel):
        bereite_flug_vor(spiel)
        spiel.starte_reise('Mondlander', 'Erde', 'Mond', 0, {})
        ticks(spiel, 1)
        # Treibstoff auf der Erde hilft dem Schiff auf dem Mond nicht
        assert not spiel.starte_reise('Mondlander', 'Mond', 'Erde', 0, {})
        spiel.GAMESTATE['Lager']['Mond']['Treibstoff'] = 1
        erde_vorher = inventar(spiel)['Treibstoff']
        assert spiel.starte_reise('Mondlander', 'Mond', 'Erde', 0, {})
        assert spiel.GAMESTATE['Lager']['Mond']['Treibstoff'] == 0
        assert inventar(spiel)['Treibstoff'] == erde_vorher

    def test_ertrag_muss_zur_erde_geflogen_werden(self, spiel):
        bereite_flug_vor(spiel)
        spiel.starte_reise('Mondlander', 'Erde', 'Mond', 2, {'Werkzeug': 1, 'Treibstoff': 1})
        ticks(spiel, 1)
        spiel.starte_mining('Mond')
        ticks(spiel, 4)
        assert spiel.GAMESTATE['Lager']['Mond']['Mondgestein'] == 4
        assert inventar(spiel)['Mondgestein'] == 0
        assert spiel.starte_reise('Mondlander', 'Mond', 'Erde', 0, {'Mondgestein': 4})
        ticks(spiel, 1)
        assert inventar(spiel)['Mondgestein'] == 4
        assert spiel.GAMESTATE['Lager']['Mond']['Mondgestein'] == 0

    def test_reiseereignis_trifft_den_vorrat_am_ziel(self, spiel):
        bereite_flug_vor(spiel)
        spiel.starte_reise('Mondlander', 'Erde', 'Mond', 0, {'Treibstoff': 1})
        erde_vorher = dict(inventar(spiel))
        spiel.aktive_reisen[0].ereignis = {'name': 'Test', 'material': {'Staub': 3, 'Treibstoff': -1}}
        ticks(spiel, 1)
        assert spiel.GAMESTATE['Lager']['Mond'] == {'Treibstoff': 0, 'Staub': 3}
        assert inventar(spiel) == erde_vorher

    def test_gebundene_astronauten_koennen_nicht_abreisen(self, spiel):
        bereite_flug_vor(spiel)
        spiel.starte_reise('Mondlander', 'Erde', 'Mond', 2, {'Werkzeug': 1, 'Treibstoff': 1, 'Wasser': 2})
        ticks(spiel, 1)
        assert spiel.starte_mining('Mond')
        assert not spiel.starte_reise('Mondlander', 'Mond', 'Erde', 1, {})
        assert spiel.starte_reise('Mondlander', 'Mond', 'Erde', 0, {})

    def test_mondlander_erreicht_den_mars_nicht(self, spiel):
        bereite_flug_vor(spiel)
        assert not spiel.starte_reise('Mondlander', 'Erde', 'Mars', 1, {})

    def test_rueckflug_warnung(self, spiel):
        bereite_flug_vor(spiel)
        werte = {'reise_von_Erde': True, 'reise_zu_Mond': True, 'reise_raumschiff_Mondlander': True,
                 'reise_astronauten': 1}
        spiel.verarbeite_event('reise_astronauten', werte)
        assert 'Rückflug' in spiel.window['reise_info'].get()
        # Treibstoff als Fracht deckt den Rückflug ...
        spiel.verarbeite_event('fracht_Treibstoff', {**werte, 'fracht_Treibstoff': 1})
        assert 'Rückflug' not in spiel.window['reise_info'].get()
        # ... ebenso Treibstoff, der schon im Mond-Lager liegt
        spiel.GAMESTATE['Lager']['Mond']['Treibstoff'] = 1
        spiel.verarbeite_event('reise_astronauten', werte)
        assert 'Rückflug' not in spiel.window['reise_info'].get()

    def test_fracht_auswahl_folgt_dem_vorrat(self, spiel):
        bereite_flug_vor(spiel)
        spiel.verarbeite_event('reise_von_Erde', {'reise_von_Erde': True})
        assert spiel.window['fracht_Werkzeug'].kwargs['values'] == list(range(6))
        inventar(spiel)['Werkzeug'] = 8          # z.B. ein fertiger Bau
        ticks(spiel, 1)
        assert spiel.window['fracht_Werkzeug'].kwargs['values'] == list(range(9))
        spiel.GAMESTATE['Lager']['Mond']['Gold'] = 2
        spiel.verarbeite_event('reise_von_Mond', {'reise_von_Mond': True})
        assert spiel.window['fracht_Gold'].kwargs['values'] == [0, 1, 2]
        assert spiel.window['fracht_Werkzeug'].kwargs['values'] == [0]

    def test_reise_ueberlebt_speichern_und_laden(self, spiel):
        bereite_flug_vor(spiel, 'Rakete')
        spiel.starte_reise('Rakete', 'Erde', 'Mars', 2, {'Werkzeug': 3})
        ticks(spiel, 1)
        spiel.dump_gamestate(1)
        spiel.lade_spielstand(1)
        ticks(spiel, 2)
        assert spiel.GAMESTATE['Astronauten']['Mars'] == 2
        assert spiel.GAMESTATE['Lager']['Mars'] == {'Werkzeug': 3}

    def test_fortschritt_beruecksichtigt_verzoegerung(self, spiel):
        bereite_flug_vor(spiel)
        spiel.starte_reise('Mondlander', 'Erde', 'Mond', 0, {})
        reise = spiel.aktive_reisen[0]
        reise.end_tick += 3                  # Ereignis verzögert die Ankunft
        assert reise.fortschritt(reise.start_tick + 1) == 25


# ---------------------------------------------------------------- Missionen und Mining

def astronauten_auf(spiel, planet, anzahl, **lager):
    entdecke(spiel, 'Mond', 'Mars')
    spiel.GAMESTATE['Astronauten'][planet] = anzahl
    spiel.GAMESTATE['Lager'][planet].update(lager)


class TestMining:
    def test_expedition_bindet_astronauten(self, spiel):
        astronauten_auf(spiel, 'Mond', 2, Werkzeug=5)
        assert spiel.starte_mining('Mond')
        assert not spiel.starte_mining('Mond')
        assert spiel.GAMESTATE['Lager']['Mond']['Werkzeug'] == 4

    def test_hoechstens_so_viele_expeditionen_wie_slots(self, spiel):
        astronauten_auf(spiel, 'Mond', 100, Werkzeug=100)
        for _ in range(spiel.MINING_SLOTS):
            assert spiel.starte_mining('Mond')
        assert not spiel.starte_mining('Mond')
        assert len(spiel.mining_aktiv) == spiel.MINING_SLOTS

    def test_material_muss_im_lager_des_planeten_liegen(self, spiel):
        astronauten_auf(spiel, 'Mond', 2)
        inventar(spiel)['Werkzeug'] = 10     # auf der Erde hilft es nicht
        assert not spiel.starte_mining('Mond')

    def test_ertrag_und_abbruch(self, spiel):
        astronauten_auf(spiel, 'Mars', 2, Werkzeug=2, Baumaterial=2)
        spiel.starte_mining('Mars')
        spiel.verarbeite_event('mining_slot_0_stop', {})
        assert spiel.GAMESTATE['Lager']['Mars'] == {'Werkzeug': 2, 'Baumaterial': 2}
        spiel.verarbeite_event('mining_starte_Mars', {})
        ticks(spiel, 6)
        mars = spiel.GAMESTATE['Lager']['Mars']
        assert mars['Gold'] == 1 and mars['Roheisen'] == 8
        assert inventar(spiel)['Gold'] == 0 and inventar(spiel)['Roheisen'] == 10
        assert spiel.mining_aktiv == []

    def test_erfahrung_und_modul_wirken(self, spiel):
        astronauten_auf(spiel, 'Mond', 2, Werkzeug=1)
        inventar(spiel).update({'Astronaut_Erfahrung': 5, 'Mondstation_Modul': 1})
        assert spiel.mining_belohnung('Mond')['Mondgestein'] == 7     # 4 + max. 3
        assert spiel.mining_dauer('Mond') == 3
        assert spiel.mining_dauer('Mars') == 6
        spiel.starte_mining('Mond')
        ticks(spiel, 3)
        assert spiel.GAMESTATE['Lager']['Mond']['Mondgestein'] == 7


class TestMondmissionen:
    ERKUNDUNG = 'Erkundung und Probenentnahme'
    GEOLOGIE = 'Geologische Untersuchungen'

    def test_mission_laeuft_durch(self, spiel):
        astronauten_auf(spiel, 'Mond', 2, Werkzeug=1)
        spiel.iCredits = 100
        spiel.verarbeite_event(f'mondmission_{self.ERKUNDUNG}', {})
        assert spiel.window['do_mondmission'].visible
        spiel.verarbeite_event('do_mondmission', {})
        assert spiel.iCredits == 40
        assert spiel.GAMESTATE['Lager']['Mond']['Werkzeug'] == 0
        ticks(spiel, 3)
        assert spiel.mission_abgeschlossen(self.ERKUNDUNG)
        assert spiel.GAMESTATE['Lager']['Mond']['Mondgestein'] == 5
        assert inventar(spiel)['Mondgestein'] == 0
        assert spiel.iCredits == 40 + 140 + 100     # Belohnung + Erfolg 'Fussabdruck'
        assert not spiel.starte_mondmission(self.ERKUNDUNG)   # nur einmal

    def test_abbruch_erstattet(self, spiel):
        astronauten_auf(spiel, 'Mond', 2, Werkzeug=1)
        spiel.iCredits = 100
        spiel.starte_mondmission(self.ERKUNDUNG)
        spiel.verarbeite_event('slot_0_stop', {})
        assert spiel.iCredits == 100
        assert spiel.GAMESTATE['Lager']['Mond']['Werkzeug'] == 1
        assert spiel.missionen_aktiv == []

    def test_voraussetzung(self, spiel):
        astronauten_auf(spiel, 'Mond', 4, Werkzeug=5)
        spiel.iCredits = 1000
        assert not spiel.starte_mondmission(self.GEOLOGIE)
        spiel.GAMESTATE['Mondmissionen'][self.ERKUNDUNG]['erforscht'] = True
        assert spiel.starte_mondmission(self.GEOLOGIE)

    def test_missionen_und_mining_teilen_sich_die_astronauten(self, spiel):
        astronauten_auf(spiel, 'Mond', 3, Werkzeug=5)
        spiel.iCredits = 1000
        assert spiel.starte_mondmission(self.ERKUNDUNG)       # bindet 2
        assert not spiel.starte_mining('Mond')                # braucht 2, frei ist 1
        assert spiel.freie_astronauten('Mond') == 1

    def test_upgrades_wirken_sofort_und_liegen_nicht_im_lager(self, spiel):
        astronauten_auf(spiel, 'Mond', 1)
        spiel.iCredits = 100
        assert spiel.starte_mondmission('Navigation und Anpassung an die geringere Schwerkraft')
        ticks(spiel, 2)
        assert inventar(spiel)['Astronaut_Erfahrung'] == 1
        assert 'Astronaut_Erfahrung' not in spiel.GAMESTATE['Lager']['Mond']

    def test_abschluss_ueberlebt_neuen_spielstand(self, spiel):
        """Der Abschluss steht im Spielstand, nicht in den Moduldaten."""
        astronauten_auf(spiel, 'Mond', 2, Werkzeug=1)
        spiel.iCredits = 100
        spiel.starte_mondmission(self.ERKUNDUNG)
        ticks(spiel, 3)
        spiel.neues_spiel()
        assert not spiel.mission_abgeschlossen(self.ERKUNDUNG)

    def test_kommunikations_upgrade_bringt_forschungspunkte(self, spiel):
        import config
        inventar(spiel)['Kommunikations_Upgrade'] = 1
        vorher = spiel.iForschungspunkte
        ticks(spiel, config.SCIENCE_POINTS_EXTRA_TICKS)
        assert spiel.iForschungspunkte == vorher + config.SCIENCE_POINTS_EXTRA + config.COMM_UPGRADE_SCIENCE_POINTS


# ---------------------------------------------------------------- Shop und UI

class TestShopUndUI:
    def test_shop_zeigt_die_schiffsdaten_der_spiellogik(self, spiel):
        for typ in spiel.RAUMSCHIFF_TYPEN:
            kapazitaet = spiel.get_raumschiff_kapazitaet(typ)
            text = spiel.SHOP_ITEMS[typ]['beschreibung']
            assert f"Sitzplätze: {kapazitaet['astronauten']}" in text
            assert f"Frachtplätze: {kapazitaet['fracht']}" in text
            assert f"Reichweite: {kapazitaet['reichweite']}" in text

    def test_kaufen_und_verkaufen(self, spiel):
        spiel.iCredits = 100
        spiel.verarbeite_event('shop_Roheisen', {})
        spiel.window['shop_anzahl'].update(value=4)
        spiel.verarbeite_event('do_kaufen', {})
        assert spiel.iCredits == 80 and inventar(spiel)['Roheisen'] == 14
        spiel.window['verkauf_material'].update(value='Roheisen')
        spiel.window['verkauf_menge'].update(value=4)
        spiel.verarbeite_event('do_verkaufen', {})
        assert spiel.iCredits == 88 and inventar(spiel)['Roheisen'] == 10

    def test_raumschiff_nur_nach_forschung_kaufbar(self, spiel):
        spiel.iCredits = 1000
        spiel.kaufe_shop_artikel('Mondlander')
        assert spiel.iCredits == 1000
        erforsche_alles(spiel)
        spiel.kaufe_shop_artikel('Mondlander')
        assert spiel.GAMESTATE['Raumschiffe']['Erde']['Mondlander']['Anzahl'] == 1

    def test_jeder_button_wird_ohne_fehler_verarbeitet(self, spiel):
        """Jeder Button im Layout hat einen Handler, der auch im Leerlauf nicht abstürzt."""
        buttons = [k for k, e in spiel.window.elemente.items() if e.typ == 'Button']
        assert len(buttons) > 40
        for key in buttons:
            assert spiel.verarbeite_event(key, {}) is True, key

    def test_jeder_tab_laesst_sich_oeffnen(self, spiel):
        tabs = [k for k, e in spiel.window.elemente.items() if e.typ == 'Tab' and k.startswith('tab_')]
        for tab in tabs:
            spiel.verarbeite_event('TabGroup_Main', {'TabGroup_Main': tab})

    def test_menue_eintraege(self, spiel):
        for eintrag in ('Slot 2::save_slot_2', 'Slot 2::load_slot_2', 'Spielstände anzeigen::slot_uebersicht',
                        'Kurzanleitung::hilfe_allgemein', 'Hilfe zum aktuellen Tab::hilfe_tab',
                        'Erfolge und Statistik::erfolge_anzeigen', 'hotkey_speichern', 'hotkey_hilfe'):
            assert spiel.verarbeite_event(eintrag, {}) is True
        assert spiel.aktiver_slot == 2

    def test_erd_jobs_binden_arbeiter(self, spiel):
        for _ in range(5):
            assert spiel.starte_erde_job('Bergbau')
        assert not spiel.starte_erde_job('Laborarbeit')
        ticks(spiel, 2)
        assert inventar(spiel)['Roheisen'] == 25
        assert spiel.erde_jobs_aktiv == []

    def test_erd_jobs_wiederholen_sich_auf_wunsch(self, spiel):
        spiel.verarbeite_event('erde_jobs_wiederholen', {'erde_jobs_wiederholen': True})
        assert spiel.starte_erde_job('Bergbau')
        ticks(spiel, 6)
        assert inventar(spiel)['Roheisen'] == 10 + 3 * 3
        assert [j.name for j in spiel.erde_jobs_aktiv] == ['Bergbau']
        # Einstellung wird gespeichert
        spiel.dump_gamestate(1)
        spiel.lade_spielstand(1)
        assert spiel.window['erde_jobs_wiederholen'].get() is True
        # Haken entfernen: der laufende Job läuft aus
        spiel.verarbeite_event('erde_jobs_wiederholen', {'erde_jobs_wiederholen': False})
        ticks(spiel, 2)
        assert spiel.erde_jobs_aktiv == []

    def test_raumsonde_entdeckt_mond_dann_mars(self, spiel):
        inventar(spiel)['Raumsonde'] = 2
        spiel.verarbeite_event('starte_raumsonde', {})
        ticks(spiel, 8)
        assert spiel.GAMESTATE['Planeten']['Mond']['entdeckt']
        assert spiel.window['tab_Reisen'].visible
        spiel.verarbeite_event('starte_raumsonde', {})
        ticks(spiel, 8)
        assert spiel.GAMESTATE['Planeten']['Mars']['entdeckt']
