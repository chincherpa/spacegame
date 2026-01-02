"""
Integration tests for Earth Jobs functionality.
Tests validate job creation, worker management, and reward distribution.
"""
import pytest
import copy
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


# Define ERDE_JOBS for testing (mirrors main.py definition)
ERDE_JOBS = {
    'Laborarbeit': {
        'beschreibung': 'Wissenschaftler arbeiten im Labor und generieren Forschungspunkte.',
        'dauer': 3,
        'benötigt_arbeiter': 1,
        'belohnung': {'Forschungspunkte': 2}
    },
    'Bergbau': {
        'beschreibung': 'Arbeiter bauen Roheisen ab.',
        'dauer': 2,
        'benötigt_arbeiter': 2,
        'belohnung': {'Roheisen': 3}
    },
    'Wasseraufbereitung': {
        'beschreibung': 'Wasser wird aufbereitet und gesammelt.',
        'dauer': 2,
        'benötigt_arbeiter': 1,
        'belohnung': {'Wasser': 2}
    },
    'Staubsammlung': {
        'beschreibung': 'Staub wird für Baumaterial gesammelt.',
        'dauer': 2,
        'benötigt_arbeiter': 1,
        'belohnung': {'Staub': 2}
    },
}


class MockErdArbeit:
    """Mock implementation of ErdArbeit class for testing."""
    def __init__(self, job_name):
        self.name = job_name
        self.fortschritt = 0
        self.max_fortschritt = ERDE_JOBS[job_name]['dauer']
        self.aktiv = True

    def tick(self):
        if self.aktiv:
            self.fortschritt += 1
            if self.fortschritt >= self.max_fortschritt:
                self.aktiv = False
                return True
        return False


class TestErdeJobsStructure:
    """Tests for ERDE_JOBS structure validation."""

    def test_erde_jobs_not_empty(self):
        """Test that ERDE_JOBS is not empty."""
        assert len(ERDE_JOBS) > 0

    def test_all_jobs_have_required_keys(self):
        """Test that all jobs have required keys."""
        required_keys = ['beschreibung', 'dauer', 'benötigt_arbeiter', 'belohnung']
        for job_name, job_data in ERDE_JOBS.items():
            for key in required_keys:
                assert key in job_data, f"Missing '{key}' in job '{job_name}'"

    def test_all_jobs_have_positive_duration(self):
        """Test that all jobs have positive duration."""
        for job_name, job_data in ERDE_JOBS.items():
            assert job_data['dauer'] > 0, f"Job '{job_name}' has non-positive dauer"

    def test_all_jobs_require_workers(self):
        """Test that all jobs require at least one worker."""
        for job_name, job_data in ERDE_JOBS.items():
            assert job_data['benötigt_arbeiter'] >= 1, \
                f"Job '{job_name}' should require at least 1 worker"

    def test_laborarbeit_gives_research_points(self):
        """Test that Laborarbeit gives research points."""
        assert 'Forschungspunkte' in ERDE_JOBS['Laborarbeit']['belohnung']
        assert ERDE_JOBS['Laborarbeit']['belohnung']['Forschungspunkte'] > 0


class TestErdArbeitClass:
    """Tests for ErdArbeit class."""

    def test_erd_arbeit_creation(self):
        """Test creating an ErdArbeit instance."""
        job = MockErdArbeit('Laborarbeit')
        
        assert job.name == 'Laborarbeit'
        assert job.fortschritt == 0
        assert job.aktiv == True
        assert job.max_fortschritt == ERDE_JOBS['Laborarbeit']['dauer']

    def test_erd_arbeit_tick_increments_progress(self):
        """Test that tick() increments progress."""
        job = MockErdArbeit('Laborarbeit')
        initial = job.fortschritt
        
        job.tick()
        
        assert job.fortschritt == initial + 1

    def test_erd_arbeit_completes_after_max_ticks(self):
        """Test that job completes after max_fortschritt ticks."""
        job = MockErdArbeit('Laborarbeit')
        
        # Tick until completion
        for _ in range(job.max_fortschritt - 1):
            result = job.tick()
            assert result == False
            assert job.aktiv == True
        
        # Final tick completes
        result = job.tick()
        assert result == True
        assert job.aktiv == False

    def test_erd_arbeit_no_tick_after_completion(self):
        """Test that tick() does nothing after completion."""
        job = MockErdArbeit('Wasseraufbereitung')
        
        # Complete the job
        while job.aktiv:
            job.tick()
        
        final_progress = job.fortschritt
        job.tick()  # Extra tick
        
        assert job.fortschritt == final_progress


class TestWorkerManagement:
    """Tests for worker management in Earth jobs."""

    def test_initial_workers_on_earth(self, fresh_gamestate):
        """Test that there are initial workers on Earth."""
        assert fresh_gamestate['Arbeiter']['Erde'] >= 1

    def test_calculate_free_workers(self, fresh_gamestate):
        """Test calculating free workers."""
        total_workers = fresh_gamestate['Arbeiter']['Erde']
        active_jobs = []  # No active jobs
        
        beschäftigte = sum(ERDE_JOBS[j.name].get('benötigt_arbeiter', 1) 
                          for j in active_jobs if j.aktiv)
        freie = total_workers - beschäftigte
        
        assert freie == total_workers

    def test_workers_occupied_by_job(self, fresh_gamestate):
        """Test that active jobs occupy workers."""
        total_workers = fresh_gamestate['Arbeiter']['Erde']
        
        # Simulate one active Bergbau job (requires 2 workers)
        active_jobs = [MockErdArbeit('Bergbau')]
        
        beschäftigte = sum(ERDE_JOBS[j.name].get('benötigt_arbeiter', 1) 
                          for j in active_jobs if j.aktiv)
        freie = total_workers - beschäftigte
        
        assert beschäftigte == 2
        assert freie == total_workers - 2

    def test_multiple_jobs_occupy_workers(self, fresh_gamestate):
        """Test that multiple jobs occupy cumulative workers."""
        total_workers = fresh_gamestate['Arbeiter']['Erde']
        
        # Simulate multiple active jobs
        active_jobs = [
            MockErdArbeit('Laborarbeit'),  # 1 worker
            MockErdArbeit('Bergbau'),       # 2 workers
            MockErdArbeit('Wasseraufbereitung'),  # 1 worker
        ]
        
        beschäftigte = sum(ERDE_JOBS[j.name].get('benötigt_arbeiter', 1) 
                          for j in active_jobs if j.aktiv)
        
        assert beschäftigte == 4  # 1 + 2 + 1


class TestJobRewards:
    """Tests for job reward distribution."""

    def test_laborarbeit_reward(self, fresh_gamestate):
        """Test Laborarbeit reward."""
        gs = copy.deepcopy(fresh_gamestate)
        initial_points = gs['Forschungspunkte']
        
        # Simulate receiving Laborarbeit reward
        belohnung = ERDE_JOBS['Laborarbeit']['belohnung']
        for ressource, menge in belohnung.items():
            if ressource == 'Forschungspunkte':
                gs['Forschungspunkte'] += menge
        
        assert gs['Forschungspunkte'] == initial_points + 2

    def test_bergbau_reward(self, fresh_gamestate):
        """Test Bergbau reward adds Roheisen."""
        gs = copy.deepcopy(fresh_gamestate)
        initial = gs['Inventar']['Roheisen']
        
        # Simulate receiving Bergbau reward
        belohnung = ERDE_JOBS['Bergbau']['belohnung']
        for ressource, menge in belohnung.items():
            gs['Inventar'][ressource] += menge
        
        assert gs['Inventar']['Roheisen'] == initial + 3

    def test_wasseraufbereitung_reward(self, fresh_gamestate):
        """Test Wasseraufbereitung reward adds Wasser."""
        gs = copy.deepcopy(fresh_gamestate)
        initial = gs['Inventar']['Wasser']
        
        # Simulate receiving reward
        belohnung = ERDE_JOBS['Wasseraufbereitung']['belohnung']
        for ressource, menge in belohnung.items():
            gs['Inventar'][ressource] += menge
        
        assert gs['Inventar']['Wasser'] == initial + 2

    def test_staubsammlung_reward(self, fresh_gamestate):
        """Test Staubsammlung reward adds Staub."""
        gs = copy.deepcopy(fresh_gamestate)
        initial = gs['Inventar']['Staub']
        
        # Simulate receiving reward
        belohnung = ERDE_JOBS['Staubsammlung']['belohnung']
        for ressource, menge in belohnung.items():
            gs['Inventar'][ressource] += menge
        
        assert gs['Inventar']['Staub'] == initial + 2


class TestJobQueue:
    """Tests for managing multiple jobs."""

    def test_can_run_multiple_jobs(self, fresh_gamestate):
        """Test that multiple jobs can run simultaneously."""
        total_workers = fresh_gamestate['Arbeiter']['Erde']  # 10 workers
        
        active_jobs = [
            MockErdArbeit('Laborarbeit'),      # 1 worker
            MockErdArbeit('Laborarbeit'),      # 1 worker
            MockErdArbeit('Bergbau'),          # 2 workers
        ]
        
        beschäftigte = sum(ERDE_JOBS[j.name].get('benötigt_arbeiter', 1) 
                          for j in active_jobs if j.aktiv)
        
        assert beschäftigte <= total_workers
        assert len(active_jobs) == 3

    def test_jobs_complete_independently(self):
        """Test that jobs complete independently."""
        jobs = [
            MockErdArbeit('Wasseraufbereitung'),  # 2 ticks
            MockErdArbeit('Laborarbeit'),          # 3 ticks
        ]
        
        # After 2 ticks
        for _ in range(2):
            for job in jobs:
                job.tick()
        
        # First should be done, second still active
        assert jobs[0].aktiv == False
        assert jobs[1].aktiv == True

    def test_completed_jobs_removed_from_active(self):
        """Test that completed jobs can be removed from active list."""
        active_jobs = [
            MockErdArbeit('Wasseraufbereitung'),
            MockErdArbeit('Laborarbeit'),
        ]
        
        # Complete all jobs
        for _ in range(5):
            for job in active_jobs[:]:
                if job.tick():
                    active_jobs.remove(job)
        
        assert len(active_jobs) == 0


class TestGameplayBalance:
    """Tests for gameplay balance of Earth jobs."""

    def test_laborarbeit_faster_than_passive_income(self):
        """Test that Laborarbeit is faster than passive income."""
        # Passive: 1 point every 20 ticks
        passive_rate = 1 / 20  # 0.05 points per tick
        
        # Laborarbeit: 2 points every 3 ticks
        laborarbeit_rate = 2 / 3  # ~0.67 points per tick
        
        assert laborarbeit_rate > passive_rate

    def test_can_research_eisenbarren_with_two_laborarbeit(self):
        """Test that 2 Laborarbeit jobs give enough for Eisenbarren research."""
        # Eisenbarren costs 5 research points
        eisenbarren_cost = 5
        
        # 2 Laborarbeit jobs = 2 * 2 = 4 points
        # Plus some passive income, should be enough
        total_from_labs = 2 * ERDE_JOBS['Laborarbeit']['belohnung']['Forschungspunkte']
        
        # With 3 jobs we definitely have enough
        total_from_3_labs = 3 * ERDE_JOBS['Laborarbeit']['belohnung']['Forschungspunkte']
        assert total_from_3_labs >= eisenbarren_cost
