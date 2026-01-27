"""
Tests for main application (app.py).

Tests application initialization, imports, and basic structure.
"""

import pytest


@pytest.mark.unit
class TestAppImports:
    """Test that the application imports successfully."""

    def test_app_module_imports(self):
        """Main app.py module can be imported."""
        try:
            import app
            assert hasattr(app, 'app')  # App instance exists
            # Note: Shiny for Python doesn't export a separate 'server' function
            # The server logic is defined inline with @app.server decorator
        except ImportError as e:
            pytest.fail(f"Failed to import app module: {e}")

    def test_required_modules_import(self):
        """All required modules can be imported."""
        modules_to_test = [
            'src.config.app_config',
            'src.handlers.game_logic',
            'src.state.game_state',
            'src.ui.components',
            'src.music_theory.cadences',
            'src.music_theory.progression'
        ]

        for module_name in modules_to_test:
            try:
                __import__(module_name)
            except ImportError as e:
                pytest.fail(f"Failed to import {module_name}: {e}")


@pytest.mark.unit
class TestAppConfiguration:
    """Test application configuration."""

    def test_app_uses_grade_8_by_default(self):
        """Application initializes with Grade 8 configuration available."""
        from src.config.app_config import GENERATOR_CONFIG

        # Check that Grade 8 config exists and is valid
        assert 8 in GENERATOR_CONFIG, "Grade 8 configuration should exist"
        grade_8_config = GENERATOR_CONFIG[8]
        assert grade_8_config is not None
        assert grade_8_config.get('use_strict_cadence') is True, "Grade 8 should use strict cadence"

    def test_config_validation_passes(self):
        """Application configuration is valid."""
        from src.config.app_config import validate_config

        try:
            result = validate_config()
            assert result is True
        except ValueError as e:
            pytest.fail(f"Configuration validation failed: {e}")


@pytest.mark.unit
class TestStateObjects:
    """Test state object creation."""

    @pytest.mark.skip(reason="Requires Shiny reactive context")
    def test_progression_state_creation(self, progression_state):
        """ProgressionState can be created."""
        assert progression_state.progression() is None
        assert progression_state.note_names() is None
        assert progression_state.chord_symbols() is None
        assert progression_state.cadence_type() is None
        assert progression_state.key() is None

    @pytest.mark.skip(reason="Requires Shiny reactive context")
    def test_feedback_state_creation(self, feedback_state):
        """FeedbackState can be created."""
        assert feedback_state.message() == ""
        assert feedback_state.type() == "info"

    @pytest.mark.skip(reason="Requires Shiny reactive context")
    def test_game_flow_state_creation(self, game_flow_state):
        """GameFlowState can be created."""
        assert game_flow_state.has_played() is False
        assert game_flow_state.is_playing() is False
        assert game_flow_state.state() == "initial"
        assert game_flow_state.disabled_buttons() == []

    @pytest.mark.skip(reason="Requires Shiny reactive context")
    def test_grade_state_creation(self, grade_state):
        """GradeState can be created."""
        assert grade_state.level() == 6  # Default grade
        assert grade_state.restored() is False

    @pytest.mark.skip(reason="Requires Shiny reactive context")
    def test_progression_state_set_all(self, progression_state, sample_progression):
        """ProgressionState.set_all() works correctly."""
        prog, notes, symbols, cadence, key = sample_progression

        progression_state.set_all(prog, notes, symbols, cadence, key)

        assert progression_state.progression() == prog
        assert progression_state.note_names() == notes
        assert progression_state.chord_symbols() == symbols
        assert progression_state.cadence_type() == cadence
        assert progression_state.key() == key

    @pytest.mark.skip(reason="Requires Shiny reactive context")
    def test_feedback_state_set(self, feedback_state):
        """FeedbackState.set() works correctly."""
        feedback_state.set("Test message", "success")

        assert feedback_state.message() == "Test message"
        assert feedback_state.type() == "success"


@pytest.mark.integration
class TestAppIntegration:
    """Integration tests for the application."""

    def test_generator_creation(self, basic_generator):
        """ChordProgressionGenerator can be instantiated."""
        assert basic_generator is not None

    def test_generator_generates_progressions(self, basic_generator, all_cadence_types):
        """Generator can create progressions for all cadence types."""
        for cadence_type in all_cadence_types:
            progression = basic_generator.generate_progression(cadence_type)
            assert progression is not None
            assert len(progression) >= 3

    def test_full_workflow_simulation(self, basic_generator):
        """Simulate a complete game workflow (without reactive state)."""
        from src.music_theory.cadences import CadenceType
        from src.handlers.game_logic import validate_guess, generate_new_cadence_data

        # 1. Generate a cadence
        cadence_data = generate_new_cadence_data(
            basic_generator,
            grade_level=8,
            allowed_cadences=[CadenceType.PERFECT]
        )

        # 2. Verify cadence data structure
        assert 'cadence_type' in cadence_data
        assert 'progression' in cadence_data
        assert 'note_names' in cadence_data
        assert 'symbols' in cadence_data
        assert 'key' in cadence_data

        # 3. User makes a correct guess
        is_correct = validate_guess("perfect", cadence_data['cadence_type'])
        assert is_correct is True

        # 4. User makes an incorrect guess
        is_incorrect = validate_guess("plagal", cadence_data['cadence_type'])
        assert is_incorrect is False
