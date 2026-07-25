"""
Integration tests for moon missions.

These tests call the real MissionInstance class and the real
starte_mondmission()/beende_mondmission()/stoppe_mondmission() functions from
main.py through the `game` fixture.
"""
import pytest

MISSION = 'Erkundung und Probenentnahme'


@pytest.fixture
def ready(game):
    """A game state that can afford MISSION: credits, astronauts and tools."""
    from actions import ACTIONS
    mission = ACTIONS[MISSION]
    game.iCredits = mission['kosten'] * 10
    game.GAMESTATE['Astronauten']['Mond'] = mission.get('benötigt_astronauten', 0) + 5
    for key, value in mission.items():
        if key.startswith('benötigt_') and key != 'benötigt_astronauten':
            game.GAMESTATE['Inventar'][key.replace('benötigt_', '').title()] = value + 5
    return game


class TestMissionInstance:
    """Tests for the real MissionInstance progress class."""

    def test_creation_uses_duration_from_actions(self, game):
        from actions import ACTIONS
        mission = game.MissionInstance(MISSION)
        assert mission.name == MISSION
        assert mission.fortschritt == 0
        assert mission.aktiv is True
        assert mission.max_fortschritt == ACTIONS[MISSION]['dauer']

    def test_tick_advances_progress(self, game):
        mission = game.MissionInstance(MISSION)
        assert mission.tick() is False
        assert mission.fortschritt == 1

    def test_completion_reported_exactly_once(self, game):
        mission = game.MissionInstance(MISSION)
        results = [mission.tick() for _ in range(mission.max_fortschritt)]
        assert results[-1] is True
        assert results.count(True) == 1
        assert mission.aktiv is False

    def test_finished_mission_does_not_advance(self, game):
        mission = game.MissionInstance(MISSION)
        for _ in range(mission.max_fortschritt):
            mission.tick()
        fortschritt = mission.fortschritt
        assert mission.tick() is False
        assert mission.fortschritt == fortschritt

    @pytest.mark.parametrize('name', ['Erkundung und Probenentnahme'])
    def test_every_action_has_a_usable_duration(self, game, name):
        from actions import ACTIONS
        for mission_name, data in ACTIONS.items():
            assert data['dauer'] > 0, f"'{mission_name}' has non-positive dauer"


class TestStarteMondmission:
    """Tests for the preconditions enforced by starte_mondmission()."""

    def test_start_registers_the_mission(self, ready):
        ready.starte_mondmission(MISSION)
        assert [m.name for m in ready.missionen_aktiv] == [MISSION]

    def test_start_deducts_credits_and_resources(self, ready):
        from actions import ACTIONS
        mission = ACTIONS[MISSION]
        credits_before = ready.iCredits
        tools_before = ready.GAMESTATE['Inventar']['Werkzeug']

        ready.starte_mondmission(MISSION)

        assert ready.iCredits == credits_before - mission['kosten']
        assert ready.GAMESTATE['Inventar']['Werkzeug'] == (
            tools_before - mission['benötigt_werkzeug'])

    def test_start_refused_without_enough_credits(self, ready):
        from actions import ACTIONS
        ready.iCredits = ACTIONS[MISSION]['kosten'] - 1
        ready.starte_mondmission(MISSION)
        assert ready.missionen_aktiv == []

    def test_start_refused_without_astronauts_on_the_moon(self, ready):
        ready.GAMESTATE['Astronauten']['Mond'] = 0
        ready.starte_mondmission(MISSION)
        assert ready.missionen_aktiv == []

    def test_start_refused_without_required_material(self, ready):
        ready.GAMESTATE['Inventar']['Werkzeug'] = 0
        ready.starte_mondmission(MISSION)
        assert ready.missionen_aktiv == []

    def test_same_mission_cannot_run_twice(self, ready):
        ready.starte_mondmission(MISSION)
        ready.starte_mondmission(MISSION)
        assert len(ready.missionen_aktiv) == 1

    def test_completed_mission_cannot_restart(self, ready):
        from actions import ACTIONS
        ACTIONS[MISSION]['erforscht'] = True
        ready.starte_mondmission(MISSION)
        assert ready.missionen_aktiv == []

    def test_running_mission_binds_its_astronauts(self, ready):
        from actions import ACTIONS
        needed = ACTIONS[MISSION]['benötigt_astronauten']
        # Exactly enough astronauts for one run of this mission.
        ready.GAMESTATE['Astronauten']['Mond'] = needed
        ready.starte_mondmission(MISSION)
        assert len(ready.missionen_aktiv) == 1

        other = next((n for n in ACTIONS
                      if n != MISSION and ACTIONS[n].get('benötigt_astronauten', 0) > 0), None)
        if other is None:
            pytest.skip('no second astronaut-consuming mission defined')
        for key, value in ACTIONS[other].items():
            if key.startswith('benötigt_') and key != 'benötigt_astronauten':
                ready.GAMESTATE['Inventar'][key.replace('benötigt_', '').title()] = value + 5
        ready.iCredits = ACTIONS[other]['kosten'] * 5

        ready.starte_mondmission(other)
        assert len(ready.missionen_aktiv) == 1, 'astronauts were double-booked'


class TestBeendeMondmission:
    """Tests that completing a mission pays the declared reward."""

    def test_rewards_are_paid_out(self, ready):
        from actions import ACTIONS
        belohnung = ACTIONS[MISSION]['belohnung']
        fp_before = ready.iForschungspunkte
        credits_before = ready.iCredits
        inv_before = dict(ready.GAMESTATE['Inventar'])

        ready.beende_mondmission(MISSION)

        for res, amount in belohnung.items():
            if res == 'Forschungspunkte':
                assert ready.iForschungspunkte == fp_before + amount
            elif res == 'Credits':
                assert ready.iCredits == credits_before + amount
            else:
                assert ready.GAMESTATE['Inventar'][res] == inv_before.get(res, 0) + amount

    def test_mission_is_marked_completed(self, ready):
        from actions import ACTIONS
        ready.beende_mondmission(MISSION)
        assert ACTIONS[MISSION]['erforscht'] is True
        assert ready.GAMESTATE['Mondmissionen'][MISSION]['erforscht'] is True

    def test_completion_is_counted_in_statistics(self, ready):
        before = ready.GAMESTATE['Statistik'].get('missionen_abgeschlossen', 0)
        ready.beende_mondmission(MISSION)
        assert ready.GAMESTATE['Statistik']['missionen_abgeschlossen'] == before + 1


class TestStoppeMondmission:
    """Tests that cancelling a mission refunds what it consumed."""

    def test_cancel_refunds_credits_and_material(self, ready):
        credits_before = ready.iCredits
        tools_before = ready.GAMESTATE['Inventar']['Werkzeug']

        ready.starte_mondmission(MISSION)
        ready.stoppe_mondmission(MISSION)

        assert ready.iCredits == credits_before
        assert ready.GAMESTATE['Inventar']['Werkzeug'] == tools_before
        assert ready.missionen_aktiv == []

    def test_cancelling_an_unknown_mission_is_a_no_op(self, ready):
        credits_before = ready.iCredits
        ready.stoppe_mondmission(MISSION)
        assert ready.iCredits == credits_before
        assert ready.missionen_aktiv == []


class TestMissionLifecycle:
    """Full start -> tick -> complete round trip through the real functions."""

    def test_full_cycle(self, ready):
        from actions import ACTIONS
        gestein_before = ready.GAMESTATE['Inventar'].get('Mondgestein', 0)

        ready.starte_mondmission(MISSION)
        mission = ready.missionen_aktiv[0]

        completed = False
        for _ in range(mission.max_fortschritt):
            if mission.tick():
                ready.beende_mondmission(mission.name)
                completed = True
        assert completed

        gain = ACTIONS[MISSION]['belohnung']['Mondgestein']
        assert ready.GAMESTATE['Inventar']['Mondgestein'] == gestein_before + gain
