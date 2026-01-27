"""
Pytest configuration and shared fixtures for g8aural tests.

This module provides common fixtures used across multiple test files.
"""

import pytest
from src.music_theory.progression import ChordProgressionGenerator
from src.music_theory.cadences import CadenceType
from src.state.game_state import ProgressionState, FeedbackState, GameFlowState, GradeState


@pytest.fixture
def basic_generator():
    """
    Create a basic generator for testing (no corpus, predictable).

    Returns:
        ChordProgressionGenerator: Generator configured for testing
    """
    return ChordProgressionGenerator(
        min_length=3,
        max_length=3,
        use_voice_leading=True,
        use_sevenths=True,
        use_corpus=False,  # Disable corpus for predictable testing
        keys=['C'],
        use_strict_cadence=False
    )


@pytest.fixture
def hybrid_generator():
    """
    Create a hybrid mode generator (Grade 8 style: 4-8 chords).

    Returns:
        ChordProgressionGenerator: Generator configured for Grade 8
    """
    return ChordProgressionGenerator(
        min_length=4,
        max_length=8,
        use_voice_leading=True,
        use_sevenths=True,
        use_corpus=True,
        corpus_temperature=0.8,
        keys=['C'],
        use_strict_cadence=True
    )


@pytest.fixture
def multi_key_generator():
    """
    Create a generator with multiple keys.

    Returns:
        ChordProgressionGenerator: Generator configured for multiple keys
    """
    return ChordProgressionGenerator(
        min_length=3,
        max_length=3,
        use_voice_leading=True,
        use_sevenths=True,
        use_corpus=False,
        keys=['C', 'G', 'D', 'a', 'd'],
        use_strict_cadence=False
    )


@pytest.fixture
def all_cadence_types():
    """
    Provide all cadence types for iteration.

    Returns:
        list[CadenceType]: All cadence types
    """
    return list(CadenceType)


@pytest.fixture
def progression_state():
    """
    Create a fresh ProgressionState instance.

    Returns:
        ProgressionState: New progression state object
    """
    return ProgressionState.create()


@pytest.fixture
def feedback_state():
    """
    Create a fresh FeedbackState instance.

    Returns:
        FeedbackState: New feedback state object
    """
    return FeedbackState.create()


@pytest.fixture
def game_flow_state():
    """
    Create a fresh GameFlowState instance.

    Returns:
        GameFlowState: New game flow state object
    """
    return GameFlowState.create()


@pytest.fixture
def grade_state():
    """
    Create a fresh GradeState instance.

    Returns:
        GradeState: New grade state object
    """
    return GradeState.create()


@pytest.fixture
def sample_progression():
    """
    Provide a sample progression for testing (C major perfect cadence).

    Returns:
        tuple: (progression, note_names, chord_symbols, cadence_type, key)
    """
    progression = [
        [60, 64, 67, 72],  # C major (I)
        [67, 71, 74, 79],  # G major (V)
        [60, 64, 67, 72]   # C major (I)
    ]
    note_names = [
        ["C4", "E4", "G4", "C5"],
        ["G4", "B4", "D5", "G5"],
        ["C4", "E4", "G4", "C5"]
    ]
    chord_symbols = ["I", "V", "I"]
    cadence_type = "perfect"
    key = "C"

    return (progression, note_names, chord_symbols, cadence_type, key)


# Test utilities

def assert_valid_midi_notes(progression: list) -> None:
    """
    Assert that a progression contains valid MIDI notes.

    Args:
        progression: List of chords (each chord is a list of MIDI note numbers)

    Raises:
        AssertionError: If validation fails
    """
    assert isinstance(progression, list), "Progression must be a list"
    assert len(progression) > 0, "Progression must not be empty"

    for i, chord in enumerate(progression):
        assert isinstance(chord, list), f"Chord {i} must be a list"
        assert len(chord) == 4, f"Chord {i} must have exactly 4 notes (SATB)"

        for j, note in enumerate(chord):
            assert isinstance(note, int), f"Chord {i}, note {j} must be an integer"
            assert 0 <= note <= 127, f"Chord {i}, note {j} must be valid MIDI (0-127)"


def assert_valid_note_names(note_names: list) -> None:
    """
    Assert that note names are in valid format.

    Args:
        note_names: List of chords (each chord is a list of note name strings)

    Raises:
        AssertionError: If validation fails
    """
    assert isinstance(note_names, list), "Note names must be a list"
    assert len(note_names) > 0, "Note names must not be empty"

    for i, chord in enumerate(note_names):
        assert isinstance(chord, list), f"Chord {i} note names must be a list"
        assert len(chord) == 4, f"Chord {i} must have exactly 4 note names"

        for j, name in enumerate(chord):
            assert isinstance(name, str), f"Chord {i}, note {j} name must be a string"
            assert len(name) >= 2, f"Chord {i}, note {j} name '{name}' too short"


def assert_valid_chord_symbols(symbols: list) -> None:
    """
    Assert that chord symbols are valid.

    Args:
        symbols: List of chord symbol strings

    Raises:
        AssertionError: If validation fails
    """
    assert isinstance(symbols, list), "Chord symbols must be a list"
    assert len(symbols) > 0, "Chord symbols must not be empty"

    for i, symbol in enumerate(symbols):
        assert isinstance(symbol, str), f"Symbol {i} must be a string"
        assert len(symbol) > 0, f"Symbol {i} must not be empty"
