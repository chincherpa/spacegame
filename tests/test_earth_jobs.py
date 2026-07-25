"""
Integration tests for Earth Jobs functionality.

These tests drive the real ERDE_JOBS table, the real ErdArbeit class and the
real starte_erde_job()/beende_erde_job() functions from main.py via the `game`
fixture. Nothing here re-implements game logic.
"""
import pytest


class TestErdeJobsStructure:
    """Tests for the ERDE_JOBS table shipped in main.py."""

    def test_erde_jobs_not_empty(self, game):
        assert len(game.ERDE_JOBS) > 0

    def test_all_jobs_have_required_keys(self, game):
        required = ['beschreibung', 'dauer', 'benötigt_arbeiter', 'belohnung']
        for job_name, job in game.ERDE_JOBS.items():
            for key in required:
                assert key in job, f"Missing '{key}' in job '{job_name}'"

    def test_all_jobs_have_positive_duration(self, game):
        for job_name, job in game.ERDE_JOBS.items():
            assert job['dauer'] > 0, f"Job '{job_name}' has non-positive dauer"

    def test_all_jobs_require_at_least_one_worker(self, game):
        for job_name, job in game.ERDE_JOBS.items():
            assert job['benötigt_arbeiter'] >= 1, f"Job '{job_name}' needs no worker"

    def test_all_jobs_grant_a_reward(self, game):
        for job_name, job in game.ERDE_JOBS.items():
            assert job['belohnung'], f"Job '{job_name}' has an empty reward"
            for res, amount in job['belohnung'].items():
                assert amount > 0, f"Job '{job_name}' rewards {amount} {res}"


class TestErdArbeit:
    """Tests for the real ErdArbeit progress class."""

    def test_starts_at_zero_and_active(self, game):
        job = game.ErdArbeit('Bergbau')
        assert job.name == 'Bergbau'
        assert job.fortschritt == 0
        assert job.aktiv is True
        assert job.max_fortschritt == game.ERDE_JOBS['Bergbau']['dauer']

    def test_tick_advances_progress(self, game):
        job = game.ErdArbeit('Laborarbeit')
        assert job.tick() is False
        assert job.fortschritt == 1

    def test_tick_returns_true_exactly_once_on_completion(self, game):
        job = game.ErdArbeit('Bergbau')
        results = [job.tick() for _ in range(game.ERDE_JOBS['Bergbau']['dauer'])]
        assert results[-1] is True
        assert results.count(True) == 1
        assert job.aktiv is False

    def test_finished_job_stops_progressing(self, game):
        job = game.ErdArbeit('Bergbau')
        for _ in range(job.max_fortschritt):
            job.tick()
        fortschritt = job.fortschritt
        assert job.tick() is False
        assert job.fortschritt == fortschritt


class TestStarteErdeJob:
    """Tests for worker accounting in starte_erde_job()."""

    def test_start_succeeds_and_registers_job(self, game):
        assert game.starte_erde_job('Laborarbeit') is True
        assert len(game.erde_jobs_aktiv) == 1
        assert game.erde_jobs_aktiv[0].name == 'Laborarbeit'

    def test_start_fails_without_free_workers(self, game):
        game.GAMESTATE['Arbeiter']['Erde'] = 1
        assert game.starte_erde_job('Bergbau') is False, 'Bergbau needs 2 workers'
        assert game.erde_jobs_aktiv == []

    def test_running_jobs_bind_their_workers(self, game):
        # Laborarbeit needs 1 worker; with exactly 1 worker a second job must fail.
        game.GAMESTATE['Arbeiter']['Erde'] = 1
        assert game.starte_erde_job('Laborarbeit') is True
        assert game.starte_erde_job('Wasseraufbereitung') is False
        assert len(game.erde_jobs_aktiv) == 1

    def test_workers_free_up_once_a_job_is_done(self, game):
        game.GAMESTATE['Arbeiter']['Erde'] = 1
        assert game.starte_erde_job('Laborarbeit') is True
        job = game.erde_jobs_aktiv[0]
        while job.tick() is False:
            pass
        # job.aktiv is now False, so its worker is no longer counted as busy
        assert game.starte_erde_job('Wasseraufbereitung') is True

    def test_parallel_jobs_within_worker_budget(self, game):
        game.GAMESTATE['Arbeiter']['Erde'] = 10
        assert game.starte_erde_job('Laborarbeit') is True
        assert game.starte_erde_job('Bergbau') is True
        assert game.starte_erde_job('Wasseraufbereitung') is True
        assert len(game.erde_jobs_aktiv) == 3


class TestBeendeErdeJob:
    """Tests that finishing a job actually pays out."""

    def test_material_reward_lands_in_inventory(self, game):
        before = game.GAMESTATE['Inventar'].get('Roheisen', 0)
        job = game.ErdArbeit('Bergbau')
        game.beende_erde_job(job)
        gain = game.ERDE_JOBS['Bergbau']['belohnung']['Roheisen']
        assert game.GAMESTATE['Inventar']['Roheisen'] == before + gain

    def test_research_reward_goes_to_research_points(self, game):
        before = game.iForschungspunkte
        job = game.ErdArbeit('Laborarbeit')
        game.beende_erde_job(job)
        gain = game.ERDE_JOBS['Laborarbeit']['belohnung']['Forschungspunkte']
        assert game.iForschungspunkte == before + gain

    def test_reward_for_material_not_yet_in_inventory(self, game):
        game.GAMESTATE['Inventar'].pop('Wasser', None)
        job = game.ErdArbeit('Wasseraufbereitung')
        game.beende_erde_job(job)
        gain = game.ERDE_JOBS['Wasseraufbereitung']['belohnung']['Wasser']
        assert game.GAMESTATE['Inventar']['Wasser'] == gain

    def test_completion_is_counted_in_statistics(self, game):
        before = game.GAMESTATE['Statistik'].get('jobs_abgeschlossen', 0)
        game.beende_erde_job(game.ErdArbeit('Bergbau'))
        assert game.GAMESTATE['Statistik']['jobs_abgeschlossen'] == before + 1

    @pytest.mark.parametrize('job_name', ['Laborarbeit', 'Bergbau',
                                          'Wasseraufbereitung', 'Staubsammlung'])
    def test_every_job_pays_its_declared_reward(self, game, job_name):
        belohnung = game.ERDE_JOBS[job_name]['belohnung']
        before_inv = dict(game.GAMESTATE['Inventar'])
        before_fp = game.iForschungspunkte

        game.beende_erde_job(game.ErdArbeit(job_name))

        for res, amount in belohnung.items():
            if res == 'Forschungspunkte':
                assert game.iForschungspunkte == before_fp + amount
            else:
                assert game.GAMESTATE['Inventar'][res] == before_inv.get(res, 0) + amount


class TestJobLifecycle:
    """A full start -> tick -> reward round trip through the real functions."""

    def test_full_cycle_pays_out_once(self, game):
        before = game.GAMESTATE['Inventar'].get('Staub', 0)
        assert game.starte_erde_job('Staubsammlung') is True

        job = game.erde_jobs_aktiv[0]
        completed = False
        for _ in range(job.max_fortschritt):
            if job.tick():
                game.beende_erde_job(job)
                completed = True
        assert completed, 'job never reported completion'

        gain = game.ERDE_JOBS['Staubsammlung']['belohnung']['Staub']
        assert game.GAMESTATE['Inventar']['Staub'] == before + gain
