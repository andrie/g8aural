"""
Game state management dataclasses for g8aural cadence training.

This module provides grouped reactive state objects that replace flat reactive values,
enabling atomic updates and clearer state ownership.
"""
from dataclasses import dataclass
from typing import Optional, List
from shiny import reactive


@dataclass
class ProgressionState:
    """Groups all data about the current progression."""

    progression: reactive.Value  # MIDI notes (4-voice SATB)
    note_names: reactive.Value   # Note names for display
    chord_symbols: reactive.Value  # Roman numerals
    cadence_type: reactive.Value  # Correct answer
    key: reactive.Value  # Key of the progression

    @staticmethod
    def create():
        """Factory function to create initialized state."""
        return ProgressionState(
            progression=reactive.Value(None),
            note_names=reactive.Value(None),
            chord_symbols=reactive.Value(None),
            cadence_type=reactive.Value(None),
            key=reactive.Value(None)
        )

    def set_all(self, progression, note_names, chord_symbols, cadence_type, key):
        """Atomic update of all progression data."""
        self.progression.set(progression)
        self.note_names.set(note_names)
        self.chord_symbols.set(chord_symbols)
        self.cadence_type.set(cadence_type)
        self.key.set(key)

    def clear(self):
        """Reset all to None."""
        self.set_all(None, None, None, None, None)


@dataclass
class FeedbackState:
    """Groups feedback-related state."""

    message: reactive.Value  # Feedback message text
    type: reactive.Value  # "info", "error", "success"

    @staticmethod
    def create():
        """Factory function to create initialized state."""
        return FeedbackState(
            message=reactive.Value(""),
            type=reactive.Value("info")
        )

    def set(self, message: str, feedback_type: str = "info"):
        """Atomic update of feedback message and type."""
        self.message.set(message)
        self.type.set(feedback_type)


@dataclass
class GameFlowState:
    """Groups game flow state."""

    state: reactive.Value  # "initial", "ready", "guessing", "correct", "hint_shown"
    has_played: reactive.Value  # Has user heard the cadence?
    is_playing: reactive.Value  # Is audio currently playing?
    disabled_buttons: reactive.Value  # Buttons disabled due to wrong answers

    @staticmethod
    def create():
        """Factory function to create initialized state."""
        return GameFlowState(
            state=reactive.Value("initial"),
            has_played=reactive.Value(False),
            is_playing=reactive.Value(False),
            disabled_buttons=reactive.Value([])
        )


@dataclass
class GradeState:
    """Groups grade-related state."""

    level: reactive.Value  # Current grade level (6, 7, or 8)
    restored: reactive.Value  # Whether grade restoration from localStorage is complete

    @staticmethod
    def create(default_level: int = 6):
        """Factory function to create initialized state."""
        return GradeState(
            level=reactive.Value(default_level),
            restored=reactive.Value(False)
        )


@dataclass
class VoiceState:
    """Groups voice singing tab state."""

    soprano_melody: reactive.Value  # [(midi, start, duration), ...]
    bass_melody: reactive.Value     # [(midi, start, duration), ...]
    target_key: reactive.Value      # 'C', 'G', 'd', etc.
    target_voice: reactive.Value    # Which voice user should sing ('soprano', 'bass', etc.)
    recorded_pitch: reactive.Value  # [{time: float, freq: float|null}, ...]
    grading_result: reactive.Value  # {mae_cents: float, detected_voice: str, feedback: str}
    is_recording: reactive.Value    # Recording status

    @staticmethod
    def create():
        """Factory function to create initialized state."""
        return VoiceState(
            soprano_melody=reactive.Value(None),
            bass_melody=reactive.Value(None),
            target_key=reactive.Value(None),
            target_voice=reactive.Value('bass'),  # Default to bass
            recorded_pitch=reactive.Value(None),
            grading_result=reactive.Value(None),
            is_recording=reactive.Value(False)
        )

    def get_target_melody(self):
        """Get the melody the user should sing."""
        target = self.target_voice()
        if target == 'soprano':
            return self.soprano_melody()
        elif target == 'bass':
            return self.bass_melody()
        return None

    def set_melodies(self, soprano, bass, key):
        """Atomic update of melody data."""
        self.soprano_melody.set(soprano)
        self.bass_melody.set(bass)
        self.target_key.set(key)

    def clear(self):
        """Reset all to None/False."""
        self.soprano_melody.set(None)
        self.bass_melody.set(None)
        self.target_key.set(None)
        self.target_voice.set('bass')  # Reset to default
        self.recorded_pitch.set(None)
        self.grading_result.set(None)
        self.is_recording.set(False)
