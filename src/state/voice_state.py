"""
Voice-specific state management dataclass for g8aural.

This module provides grouped reactive state objects for the voice singing feature,
enabling atomic updates and clearer state ownership.
"""
from dataclasses import dataclass
from typing import Optional, List, Tuple, Dict, Any
from shiny import reactive


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

    def get_target_melody(self) -> Optional[List[Tuple[int, float, float]]]:
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