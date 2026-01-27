"""
Tests for game logic functions (handlers/game_logic.py).

Tests the business logic functions that handle game state, validation,
and progression generation.
"""

import pytest
from src.music_theory.cadences import CadenceType
from src.handlers.game_logic import (
    validate_guess,
    get_feedback_message,
    generate_new_cadence_data
)


@pytest.mark.unit
class TestValidateGuess:
    """Test the validate_guess() function."""

    def test_correct_guess(self):
        """Exact match returns True."""
        assert validate_guess("perfect", "perfect") is True
        assert validate_guess("plagal", "plagal") is True
        assert validate_guess("imperfect", "imperfect") is True
        assert validate_guess("interrupted", "interrupted") is True

    def test_incorrect_guess(self):
        """Non-matching guess returns False."""
        assert validate_guess("perfect", "plagal") is False
        assert validate_guess("imperfect", "interrupted") is False
        assert validate_guess("plagal", "perfect") is False

    def test_case_insensitive(self):
        """Guess is case-insensitive."""
        assert validate_guess("PERFECT", "perfect") is True
        assert validate_guess("Perfect", "perfect") is True
        assert validate_guess("pErFeCt", "perfect") is True

    def test_whitespace_handling(self):
        """Leading/trailing whitespace is ignored."""
        assert validate_guess("  perfect  ", "perfect") is True
        assert validate_guess("\tperfect\n", "perfect") is True
        assert validate_guess(" plagal ", "plagal") is True

    def test_empty_strings(self):
        """Empty guess never matches."""
        assert validate_guess("", "perfect") is False
        assert validate_guess("  ", "perfect") is False

    def test_invalid_input(self):
        """Invalid cadence type never matches."""
        assert validate_guess("invalid", "perfect") is False
        assert validate_guess("dominant", "perfect") is False


@pytest.mark.unit
class TestGetFeedbackMessage:
    """Test the get_feedback_message() function."""

    def test_correct_answer_message(self):
        """Correct answer returns success message."""
        msg, msg_type = get_feedback_message(is_correct=True)
        assert msg == "Correct! Well done!"
        assert msg_type == "success"

    def test_incorrect_first_attempt_message(self):
        """Incorrect first attempt returns encouraging error."""
        msg, msg_type = get_feedback_message(is_correct=False, is_first_attempt=True)
        assert msg == "Not quite. Try again!"
        assert msg_type == "error"

    def test_incorrect_retry_message(self):
        """Incorrect retry returns keep trying message."""
        msg, msg_type = get_feedback_message(is_correct=False, is_first_attempt=False)
        assert msg == "Keep trying!"
        assert msg_type == "error"

    def test_message_always_returns_tuple(self):
        """Function always returns (str, str) tuple."""
        result = get_feedback_message(True)
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], str)
        assert isinstance(result[1], str)


@pytest.mark.integration
@pytest.mark.music_theory
class TestGenerateNewCadenceData:
    """Test the generate_new_cadence_data() function."""

    def test_generates_valid_cadence_data(self, basic_generator, all_cadence_types):
        """Generated data contains all required fields."""
        cadence_data = generate_new_cadence_data(
            basic_generator,
            grade_level=8,
            allowed_cadences=all_cadence_types
        )

        # Check required keys
        assert 'cadence_type' in cadence_data
        assert 'progression' in cadence_data
        assert 'note_names' in cadence_data
        assert 'symbols' in cadence_data
        assert 'key' in cadence_data

    def test_cadence_type_is_from_allowed_list(self, basic_generator):
        """Generated cadence type is from allowed list."""
        allowed = [CadenceType.PERFECT, CadenceType.IMPERFECT]

        for _ in range(10):  # Test multiple times due to randomness
            cadence_data = generate_new_cadence_data(
                basic_generator,
                grade_level=6,
                allowed_cadences=allowed
            )

            cadence_type = cadence_data['cadence_type']
            assert cadence_type in ['perfect', 'imperfect']

    def test_progression_has_midi_notes(self, basic_generator, all_cadence_types):
        """Generated progression contains valid MIDI notes."""
        cadence_data = generate_new_cadence_data(
            basic_generator,
            grade_level=8,
            allowed_cadences=all_cadence_types
        )

        progression = cadence_data['progression']
        assert isinstance(progression, list)
        assert len(progression) > 0

        # Each chord should be a list of MIDI notes
        for chord in progression:
            assert isinstance(chord, list)
            for note in chord:
                assert isinstance(note, int)
                assert 0 <= note <= 127

    def test_note_names_match_progression_length(self, basic_generator, all_cadence_types):
        """Note names list matches progression length."""
        cadence_data = generate_new_cadence_data(
            basic_generator,
            grade_level=8,
            allowed_cadences=all_cadence_types
        )

        progression = cadence_data['progression']
        note_names = cadence_data['note_names']

        assert len(note_names) == len(progression)

    def test_symbols_match_progression_length(self, basic_generator, all_cadence_types):
        """Chord symbols list matches progression length."""
        cadence_data = generate_new_cadence_data(
            basic_generator,
            grade_level=8,
            allowed_cadences=all_cadence_types
        )

        progression = cadence_data['progression']
        symbols = cadence_data['symbols']

        assert len(symbols) == len(progression)

    def test_key_is_valid_string(self, basic_generator, all_cadence_types):
        """Generated key is a non-empty string."""
        cadence_data = generate_new_cadence_data(
            basic_generator,
            grade_level=8,
            allowed_cadences=all_cadence_types
        )

        key = cadence_data['key']
        assert isinstance(key, str)
        assert len(key) > 0

    def test_grade_6_generates_two_cadence_types(self, basic_generator):
        """Grade 6 only generates Perfect and Imperfect cadences."""
        from src.config.app_config import CADENCE_TYPES_BY_GRADE

        grade_6_cadences = CADENCE_TYPES_BY_GRADE[6]
        generated_types = set()

        # Generate multiple cadences to see both types
        for _ in range(20):
            cadence_data = generate_new_cadence_data(
                basic_generator,
                grade_level=6,
                allowed_cadences=grade_6_cadences
            )
            generated_types.add(cadence_data['cadence_type'])

        # Should only see perfect and imperfect
        assert generated_types.issubset({'perfect', 'imperfect'})

    def test_grade_8_can_generate_all_types(self, basic_generator):
        """Grade 8 can generate all four cadence types."""
        from src.config.app_config import CADENCE_TYPES_BY_GRADE

        grade_8_cadences = CADENCE_TYPES_BY_GRADE[8]
        generated_types = set()

        # Generate many cadences to see all types
        for _ in range(50):
            cadence_data = generate_new_cadence_data(
                basic_generator,
                grade_level=8,
                allowed_cadences=grade_8_cadences
            )
            generated_types.add(cadence_data['cadence_type'])

        # With 50 attempts, we should see most if not all types
        # (Though with random selection, we can't guarantee all 4)
        assert len(generated_types) >= 2  # At least some variety

    def test_hybrid_mode_generates_longer_progressions(self, hybrid_generator):
        """Hybrid mode (Grade 8) generates 4-8 chord progressions."""
        from src.config.app_config import CADENCE_TYPES_BY_GRADE

        grade_8_cadences = CADENCE_TYPES_BY_GRADE[8]

        for _ in range(10):
            cadence_data = generate_new_cadence_data(
                hybrid_generator,
                grade_level=8,
                allowed_cadences=grade_8_cadences
            )

            progression = cadence_data['progression']
            assert 4 <= len(progression) <= 8, \
                f"Expected 4-8 chords in hybrid mode, got {len(progression)}"

    def test_pure_mode_generates_three_chords(self, basic_generator):
        """Pure mode (Grades 6-7) generates exactly 3 chords."""
        from src.config.app_config import CADENCE_TYPES_BY_GRADE

        grade_6_cadences = CADENCE_TYPES_BY_GRADE[6]

        for _ in range(10):
            cadence_data = generate_new_cadence_data(
                basic_generator,
                grade_level=6,
                allowed_cadences=grade_6_cadences
            )

            progression = cadence_data['progression']
            assert len(progression) == 3, \
                f"Expected exactly 3 chords in pure mode, got {len(progression)}"

    def test_multiple_keys_generates_variety(self, multi_key_generator):
        """Generator with multiple keys produces variety."""
        from src.config.app_config import CADENCE_TYPES_BY_GRADE

        grade_8_cadences = CADENCE_TYPES_BY_GRADE[8]
        generated_keys = set()

        # Generate many progressions
        for _ in range(30):
            cadence_data = generate_new_cadence_data(
                multi_key_generator,
                grade_level=8,
                allowed_cadences=grade_8_cadences
            )
            generated_keys.add(cadence_data['key'])

        # Should see multiple different keys
        assert len(generated_keys) >= 2, "Expected variety in key selection"
