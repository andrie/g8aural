"""
Chord progression generator with rule-based composition.
"""
import random
from typing import List

from .notes import Chord
from .cadences import CadenceType, CadencePattern
from .voice_leading import VoiceLeader


class ChordProgressionGenerator:
    """Generates musical chord progressions following music theory rules."""

    # Common chord progressions (scale degrees) that sound good
    STRONG_PROGRESSIONS = [
        (1, 4),   # I → IV
        (1, 5),   # I → V
        (1, 6),   # I → vi
        (2, 5),   # ii → V
        (4, 5),   # IV → V
        (4, 1),   # IV → I
        (5, 1),   # V → I
        (5, 6),   # V → vi
        (6, 4),   # vi → IV
        (6, 2),   # vi → ii
    ]

    # Progressions to avoid (weak voice leading)
    WEAK_PROGRESSIONS = [
        (5, 4),   # V → IV (retrogression)
        (1, 2),   # I → ii (weak)
        (3, 1),   # iii → I (uncommon)
    ]

    def __init__(self, min_length: int = 4, max_length: int = 8, use_voice_leading: bool = True, use_sevenths: bool = True):
        """
        Initialize the generator.

        Args:
            min_length: Minimum number of chords in progression
            max_length: Maximum number of chords in progression
            use_voice_leading: Apply automatic voice leading (default True)
            use_sevenths: Use 7th chords where appropriate (default True)
        """
        self.min_length = min_length
        self.max_length = max_length
        self.use_voice_leading = use_voice_leading
        self.use_sevenths = use_sevenths
        self.voice_leader = VoiceLeader() if use_voice_leading else None

    def generate_progression(self, cadence_type: CadenceType) -> List[Chord]:
        """
        Generate a chord progression ending with the specified cadence.

        Args:
            cadence_type: The target cadence type

        Returns:
            List of Chord objects forming a complete progression
        """
        # Determine total length
        total_length = random.randint(self.min_length, self.max_length)

        # Get the final two chords (the cadence)
        penultimate_degree, final_degree = CadencePattern.get_cadence_chords(cadence_type)

        # Calculate how many chords we need before the cadence
        intro_length = total_length - 2

        # Generate introduction chords
        intro_chords = self._generate_intro(intro_length, penultimate_degree, cadence_type)

        # Create the cadence chords
        # V chords often use 7th for stronger resolution
        penult_seventh = self.use_sevenths and penultimate_degree == 5

        cadence_chords = [
            Chord(penultimate_degree, use_seventh=penult_seventh),
            Chord(final_degree, use_seventh=False)  # Final chord usually triad
        ]

        # Combine and return
        progression = intro_chords + cadence_chords
        return progression

    def _generate_intro(self, length: int, target_degree: int, cadence_type: CadenceType) -> List[Chord]:
        """
        Generate introduction chords leading to the cadence.

        Args:
            length: Number of intro chords to generate
            target_degree: Scale degree we need to reach (first chord of cadence)
            cadence_type: Type of cadence for contextual choices

        Returns:
            List of Chord objects for the introduction
        """
        if length == 0:
            return []

        intro_chords = []

        # Always start with I (tonic) to establish key - use triad for stability
        current_degree = 1
        intro_chords.append(Chord(current_degree, use_seventh=False))

        # Generate middle chords
        for i in range(1, length):
            # On the last intro chord, we need to connect to the cadence
            if i == length - 1:
                next_degree = self._find_chord_leading_to(current_degree, target_degree)
            else:
                # Generate a good next chord
                next_degree = self._choose_next_chord(current_degree, cadence_type)

            # Use 7th chords for ii, V, vi, vii
            use_seventh = self.use_sevenths and next_degree in [2, 5, 6, 7]
            intro_chords.append(Chord(next_degree, use_seventh=use_seventh))
            current_degree = next_degree

        return intro_chords

    def _choose_next_chord(self, current_degree: int, cadence_type: CadenceType) -> int:
        """
        Choose a good next chord following music theory rules.

        Args:
            current_degree: Current scale degree
            cadence_type: Type of cadence (for context)

        Returns:
            Next scale degree
        """
        # Get common approach chords for this cadence type
        good_chords = CadencePattern.get_common_approach_chords(cadence_type)

        # Find valid next chords from current position
        valid_next = []
        for next_degree in good_chords:
            if next_degree != current_degree:  # Don't repeat the same chord
                progression = (current_degree, next_degree)
                # Check if it's a strong progression and not a weak one
                if progression in self.STRONG_PROGRESSIONS or self._is_allowed_progression(progression):
                    valid_next.append(next_degree)

        # If we have valid options, choose randomly
        if valid_next:
            return random.choice(valid_next)

        # Fallback: use any strong progression from current degree
        for from_deg, to_deg in self.STRONG_PROGRESSIONS:
            if from_deg == current_degree:
                valid_next.append(to_deg)

        if valid_next:
            return random.choice(valid_next)

        # Last resort: go to I or V
        return 1 if current_degree != 1 else 5

    def _find_chord_leading_to(self, current_degree: int, target_degree: int) -> int:
        """
        Find a chord that bridges from current to target degree.

        Args:
            current_degree: Current scale degree
            target_degree: Target scale degree to reach

        Returns:
            Bridge scale degree
        """
        # If direct progression is strong, use it
        if (current_degree, target_degree) in self.STRONG_PROGRESSIONS:
            return target_degree

        # Find intermediate chord
        for intermediate in [1, 4, 5, 6, 2]:
            if intermediate != current_degree and intermediate != target_degree:
                if ((current_degree, intermediate) in self.STRONG_PROGRESSIONS and
                    (intermediate, target_degree) in self.STRONG_PROGRESSIONS):
                    return intermediate

        # Fallback: return target directly
        return target_degree

    def _is_allowed_progression(self, progression: tuple) -> bool:
        """
        Check if a progression is allowed (not in weak progressions).

        Args:
            progression: Tuple of (from_degree, to_degree)

        Returns:
            True if allowed, False otherwise
        """
        return progression not in self.WEAK_PROGRESSIONS

    def progression_to_midi(self, progression: List[Chord]) -> List[List[int]]:
        """
        Convert a chord progression to MIDI note numbers.

        Args:
            progression: List of Chord objects

        Returns:
            List of lists, where each inner list contains MIDI notes for one chord
        """
        if self.use_voice_leading and self.voice_leader:
            # Apply voice leading algorithm
            return self.voice_leader.voice_progression(progression)
        else:
            # Original behavior: root position, no voice leading
            midi_progression = []
            for chord in progression:
                # Use octave 4 (middle C region) for a comfortable piano range
                midi_notes = chord.to_midi_notes(base_octave=4)
                midi_progression.append(midi_notes)
            return midi_progression

    def progression_to_symbols(self, progression: List[Chord]) -> List[str]:
        """
        Convert a chord progression to Roman numeral symbols.

        Args:
            progression: List of Chord objects

        Returns:
            List of Roman numeral strings
        """
        return [chord.get_roman_numeral() for chord in progression]
