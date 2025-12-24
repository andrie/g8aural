"""
Voice leading algorithm for smooth chord progressions.
"""
from typing import List, Tuple
from itertools import combinations

from .notes import Chord


class VoiceLeader:
    """
    Implements automatic voice leading for chord progressions.
    Uses greedy algorithm to minimize voice movement between consecutive chords.
    """

    # SATB voice ranges (MIDI note numbers)
    VOICE_RANGES = {
        'bass': (40, 60),      # E2 to C4
        'tenor': (48, 67),     # C3 to G4
        'alto': (55, 72),      # G3 to C5
        'soprano': (60, 79),   # C4 to G5
    }

    # Preferred initial spacing (intervals above bass)
    INITIAL_SPACING = {
        3: [0, 7, 12],         # Triad: root, 5th, octave (3-voice)
        4: [0, 7, 12, 16],     # Seventh: root, 5th, octave, 10th (4-voice)
    }

    def __init__(self):
        """Initialize voice leader."""
        self.previous_voicing = None

    def voice_progression(self, chords: List[Chord]) -> List[List[int]]:
        """
        Apply voice leading to a chord progression.

        Args:
            chords: List of Chord objects

        Returns:
            List of MIDI note lists (one per chord) with optimal voice leading
        """
        if not chords:
            return []

        voiced_progression = []

        for i, chord in enumerate(chords):
            if i == 0:
                # First chord: use good initial voicing
                voicing = self._get_initial_voicing(chord)
            else:
                # Subsequent chords: optimize for smooth voice leading
                voicing = self._find_best_voicing(chord, self.previous_voicing)

            voiced_progression.append(voicing)
            self.previous_voicing = voicing

        # Reset for next progression
        self.previous_voicing = None

        return voiced_progression

    def _get_initial_voicing(self, chord: Chord) -> List[int]:
        """
        Get initial voicing for first chord in progression.
        Uses root position with good spacing.

        Args:
            chord: The chord to voice

        Returns:
            List of MIDI note numbers
        """
        chord_tones = chord.get_chord_tones(base_octave=3)  # Start from low octave
        num_voices = len(chord_tones)

        # Get preferred spacing
        spacing = self.INITIAL_SPACING.get(num_voices, [0, 7, 12])

        # Bass note (root) in bass range
        bass_note = chord_tones[0]

        # Build voicing with spacing
        voicing = []
        for i, interval in enumerate(spacing[:num_voices]):
            # For 7th chords, adjust the 4th note to use the actual 7th
            if i == 3 and num_voices == 4:
                # Use the actual 7th from chord tones (10 semitones)
                note = bass_note + 19  # Roughly two octaves up for the 7th
            else:
                note = bass_note + interval
            voicing.append(note)

        # Ensure all notes are in reasonable ranges
        voicing = self._adjust_to_ranges(voicing, chord_tones)

        return voicing

    def _find_best_voicing(self, chord: Chord, prev_voicing: List[int]) -> List[int]:
        """
        Find best voicing for chord that minimizes movement from previous voicing.

        Args:
            chord: The chord to voice
            prev_voicing: MIDI notes from previous chord

        Returns:
            List of MIDI note numbers with optimal voice leading
        """
        # Get all chord tones in multiple octaves
        chord_tones = self._get_chord_tones_multi_octave(chord)

        # Determine number of voices based on chord type
        num_voices = len(chord.get_intervals())  # 3 for triads, 4 for sevenths
        best_voicing = None
        best_distance = float('inf')

        # Generate candidate voicings
        candidates = self._generate_candidate_voicings(chord_tones, num_voices, chord)

        for candidate in candidates:
            # Calculate total voice movement (handle different voice counts)
            if len(prev_voicing) == num_voices:
                # Same number of voices - direct comparison
                distance = self._calculate_voice_distance(prev_voicing, candidate)
                penalty = self._calculate_penalties(prev_voicing, candidate)
            else:
                # Different voice counts - use simplified distance metric
                # Compare closest voices only
                distance = self._calculate_adaptive_distance(prev_voicing, candidate)
                penalty = 0.0  # Don't apply strict voice leading rules when voice count changes

            total_cost = distance + penalty

            if total_cost < best_distance:
                best_distance = total_cost
                best_voicing = candidate

        return best_voicing if best_voicing else self._get_initial_voicing(chord)

    def _get_chord_tones_multi_octave(self, chord: Chord, octave_range: int = 4) -> List[int]:
        """
        Get chord tones across multiple octaves.

        Args:
            chord: The chord
            octave_range: Number of octaves to span

        Returns:
            List of MIDI notes spanning multiple octaves
        """
        intervals = chord.get_intervals()
        base_midi = 36  # Start from C2

        tones = []
        for octave in range(octave_range):
            for interval in intervals:
                note = base_midi + (octave * 12) + interval
                if note <= 84:  # Don't go above C6
                    tones.append(note)

        return sorted(set(tones))

    def _generate_candidate_voicings(self, chord_tones: List[int], num_voices: int, chord: Chord) -> List[List[int]]:
        """
        Generate candidate voicings from available chord tones.

        Args:
            chord_tones: Available MIDI notes
            num_voices: Number of voices needed
            chord: The chord object

        Returns:
            List of possible voicings
        """
        candidates = []
        intervals = chord.get_intervals()
        num_chord_tones = len(intervals)

        # For voicings, we need to ensure we use one of each chord tone
        # Generate voicings by selecting one instance of each interval class
        if num_voices == 3 and num_chord_tones == 3:
            # Triads: select one of each note (root, 3rd, 5th)
            for combo in combinations(chord_tones, 3):
                voicing = sorted(list(combo))
                # Check that we have all three different chord tones (modulo 12)
                pitch_classes = set((note % 12) for note in voicing)
                chord_pitch_classes = set((interval % 12) for interval in intervals)
                # We need to check against the actual pitch classes of the chord
                root_pc = chord_tones[0] % 12
                required_pcs = set((root_pc + interval) % 12 for interval in intervals)
                if pitch_classes == required_pcs and self._is_valid_voicing(voicing):
                    candidates.append(voicing)

        elif num_voices == 4 and num_chord_tones == 4:
            # 7th chords: select one of each note (root, 3rd, 5th, 7th)
            for combo in combinations(chord_tones, 4):
                voicing = sorted(list(combo))
                # Check that we have all four different chord tones
                pitch_classes = set((note % 12) for note in voicing)
                root_pc = chord_tones[0] % 12
                required_pcs = set((root_pc + interval) % 12 for interval in intervals)
                if pitch_classes == required_pcs and self._is_valid_voicing(voicing):
                    candidates.append(voicing)

        # If no candidates found, generate simpler voicings
        if not candidates:
            for combo in combinations(chord_tones, num_voices):
                voicing = sorted(list(combo))
                if self._is_valid_voicing(voicing):
                    candidates.append(voicing)

        return candidates[:100]  # Limit to avoid excessive computation

    def _is_valid_voicing(self, voicing: List[int]) -> bool:
        """
        Check if voicing is valid (reasonable spacing, within ranges).

        Args:
            voicing: List of MIDI notes

        Returns:
            True if valid
        """
        if not voicing or len(voicing) < 3:
            return False

        # Check voice ranges - get ranges for the number of voices we have
        range_keys = ['bass', 'tenor', 'alto', 'soprano'][:len(voicing)]
        ranges = [self.VOICE_RANGES[key] for key in range_keys]

        for note, (min_note, max_note) in zip(voicing, ranges):
            if note < min_note or note > max_note:
                return False

        # Check spacing (no voice should be more than 12 semitones apart except bass)
        for i in range(1, len(voicing) - 1):
            if voicing[i+1] - voicing[i] > 12:
                return False

        # Bass to tenor can be wider
        if len(voicing) > 1 and voicing[1] - voicing[0] > 15:
            return False

        return True

    def _calculate_voice_distance(self, voicing1: List[int], voicing2: List[int]) -> float:
        """
        Calculate total movement between two voicings.

        Args:
            voicing1: First voicing
            voicing2: Second voicing

        Returns:
            Total semitone distance (sum of absolute differences)
        """
        if len(voicing1) != len(voicing2):
            return float('inf')

        return sum(abs(n1 - n2) for n1, n2 in zip(voicing1, voicing2))

    def _calculate_adaptive_distance(self, voicing1: List[int], voicing2: List[int]) -> float:
        """
        Calculate distance between voicings with different voice counts.
        Matches closest voices and adds penalty for extra/missing voices.

        Args:
            voicing1: First voicing
            voicing2: Second voicing

        Returns:
            Adaptive distance metric
        """
        # Match common voices (take minimum count)
        min_voices = min(len(voicing1), len(voicing2))

        # Compare bottom voices (most important for stability)
        distance = sum(abs(voicing1[i] - voicing2[i]) for i in range(min_voices))

        # Add penalty for voice count difference
        voice_diff = abs(len(voicing1) - len(voicing2))
        distance += voice_diff * 5  # Moderate penalty for changing voice count

        return distance

    def _calculate_penalties(self, prev_voicing: List[int], curr_voicing: List[int]) -> float:
        """
        Calculate penalties for voice leading violations.

        Args:
            prev_voicing: Previous chord voicing
            curr_voicing: Current chord voicing

        Returns:
            Penalty score (higher is worse)
        """
        penalty = 0.0

        if len(prev_voicing) != len(curr_voicing):
            return float('inf')

        # Check for parallel fifths and octaves
        for i in range(len(prev_voicing)):
            for j in range(i + 1, len(prev_voicing)):
                interval1 = prev_voicing[j] - prev_voicing[i]
                interval2 = curr_voicing[j] - curr_voicing[i]

                # Parallel perfect fifth (7 semitones)
                if abs(interval1 % 12) == 7 and abs(interval2 % 12) == 7:
                    # Check if moving in same direction with same interval
                    motion1 = curr_voicing[i] - prev_voicing[i]
                    motion2 = curr_voicing[j] - prev_voicing[j]
                    if motion1 == motion2 and motion1 != 0:
                        penalty += 50.0  # Heavy penalty

                # Parallel octave
                if interval1 % 12 == 0 and interval2 % 12 == 0:
                    motion1 = curr_voicing[i] - prev_voicing[i]
                    motion2 = curr_voicing[j] - prev_voicing[j]
                    if motion1 == motion2 and motion1 != 0:
                        penalty += 50.0  # Heavy penalty

        # Penalize large leaps (more than a 5th)
        for i in range(len(prev_voicing)):
            leap = abs(curr_voicing[i] - prev_voicing[i])
            if leap > 7:  # Larger than perfect 5th
                penalty += (leap - 7) * 2.0

        return penalty

    def _adjust_to_ranges(self, voicing: List[int], chord_tones: List[int]) -> List[int]:
        """
        Adjust voicing to fit within voice ranges.

        Args:
            voicing: Initial voicing
            chord_tones: Available chord tones

        Returns:
            Adjusted voicing within ranges
        """
        adjusted = []
        range_keys = ['bass', 'tenor', 'alto', 'soprano'][:len(voicing)]
        ranges = [self.VOICE_RANGES[key] for key in range_keys]

        for note, (min_note, max_note) in zip(voicing, ranges):
            # Shift note into range if needed
            while note < min_note:
                note += 12
            while note > max_note:
                note -= 12
            adjusted.append(note)

        return adjusted
