"""
Unit tests for the ACTIONS data structure.
Tests validate structure and consistency of action definitions.
"""
import pytest


class TestActionsStructure:
    """Tests for ACTIONS structure validation."""

    def test_actions_is_not_empty(self, test_actions):
        """Test that ACTIONS dictionary is not empty."""
        assert len(test_actions) > 0, "ACTIONS should not be empty"

    def test_all_actions_have_required_keys(self, test_actions):
        """Test that all actions have required keys."""
        required_keys = ['dauer', 'kosten', 'belohnung']
        for action_name, action_data in test_actions.items():
            for key in required_keys:
                assert key in action_data, f"Missing '{key}' in action '{action_name}'"

    def test_all_actions_have_beschreibung(self, test_actions):
        """Test that all actions have a description (case-insensitive)."""
        for action_name, action_data in test_actions.items():
            has_desc = 'beschreibung' in action_data or 'Beschreibung' in action_data
            assert has_desc, f"Missing beschreibung in action '{action_name}'"

    def test_action_dauer_is_positive(self, test_actions):
        """Test that all actions have positive duration."""
        for action_name, action_data in test_actions.items():
            assert action_data['dauer'] > 0, f"Action '{action_name}' has non-positive dauer"

    def test_action_kosten_is_non_negative(self, test_actions):
        """Test that all actions have non-negative cost."""
        for action_name, action_data in test_actions.items():
            assert action_data['kosten'] >= 0, f"Action '{action_name}' has negative kosten"


class TestActionsBelohnung:
    """Tests for action rewards (Belohnung)."""

    def test_belohnung_is_dict(self, test_actions):
        """Test that belohnung is always a dictionary."""
        for action_name, action_data in test_actions.items():
            assert isinstance(action_data['belohnung'], dict), \
                f"belohnung in action '{action_name}' should be a dict"

    def test_belohnung_values_are_positive(self, test_actions):
        """Test that all reward values are positive."""
        for action_name, action_data in test_actions.items():
            for reward_name, reward_value in action_data['belohnung'].items():
                assert reward_value > 0, \
                    f"Reward '{reward_name}' in action '{action_name}' should be positive"

    def test_common_reward_types(self, test_actions):
        """Test that actions have expected reward types."""
        common_rewards = ['Forschungspunkte', 'Credits']
        for action_name, action_data in test_actions.items():
            belohnung_keys = action_data['belohnung'].keys()
            # At least one common reward should be present
            has_common = any(reward in belohnung_keys for reward in common_rewards)
            assert has_common, f"Action '{action_name}' should have Forschungspunkte or Credits"


class TestActionsAnforderungen:
    """Tests for action requirements (benötigt_* keys)."""

    def test_benoetigt_astronauten_is_positive(self, test_actions):
        """Test that astronaut requirements are positive when present."""
        for action_name, action_data in test_actions.items():
            if 'benötigt_astronauten' in action_data:
                assert action_data['benötigt_astronauten'] > 0, \
                    f"benötigt_astronauten in '{action_name}' should be positive"

    def test_benoetigt_werkzeug_is_positive(self, test_actions):
        """Test that tool requirements are positive when present."""
        for action_name, action_data in test_actions.items():
            if 'benötigt_werkzeug' in action_data:
                assert action_data['benötigt_werkzeug'] > 0, \
                    f"benötigt_werkzeug in '{action_name}' should be positive"

    def test_benoetigt_baumaterial_is_positive(self, test_actions):
        """Test that building material requirements are positive when present."""
        for action_name, action_data in test_actions.items():
            if 'benötigt_baumaterial' in action_data:
                assert action_data['benötigt_baumaterial'] > 0, \
                    f"benötigt_baumaterial in '{action_name}' should be positive"


class TestSpecificActions:
    """Tests for specific important actions."""

    def test_erkundung_exists(self, test_actions):
        """Test that exploration action exists."""
        assert 'Erkundung' in test_actions or 'Erkundung und Probenentnahme' in test_actions

    def test_mondbasen_design_exists(self, test_actions):
        """Test that moon base design action exists."""
        assert 'Mondbasen-Design' in test_actions

    def test_mondbasen_design_gives_bauplan(self, test_actions):
        """Test that Mondbasen-Design gives Mondbasen Bauplan as reward."""
        if 'Mondbasen-Design' in test_actions:
            belohnung = test_actions['Mondbasen-Design']['belohnung']
            assert 'Mondbasen Bauplan' in belohnung, \
                "Mondbasen-Design should give Mondbasen Bauplan as reward"

    def test_action_names_are_unique(self, test_actions):
        """Test that action names are unique (implicit in dict)."""
        # This is implicitly tested by the dict structure, but we verify
        action_names = list(test_actions.keys())
        assert len(action_names) == len(set(action_names)), "Action names should be unique"
