"""
Voice leading algorithm using music21 with 1-step lookahead optimization.

This module provides professional-grade voice leading using music21's
VoiceLeadingQuartet to validate transitions and a lookahead algorithm
to prevent "painting into corners".
"""

import logging
from typing import List, Optional, Tuple
from itertools import product
from music21 import roman, pitch, voiceLeading
from .roman_numerals import ChordFactory

logger = logging.getLogger(__name__)


class VoiceLeader:
    """Voice leading with music21 validation and lookahead optimization."""

    # Voice ranges optimized for treble clef notation (MIDI note numbers)
    VOICE_RANGES = {
        'bass': (55, 67),      # G3 to G4 (bottom of treble clef)
        'tenor': (60, 72),     # C4 (middle C) to C5
        'alto': (64, 76),      # E4 to E5
        'soprano': (67, 79),   # G4 to G5
    }

    def __init__(self):
        """Initialize voice leader."""
        pass

    def voice_progression(self, chords: List[roman.RomanNumeral],
                         inversion_constraints: Optional[List[List[int]]] = None) -> List[List[int]]:
        """
        Voice chord progression with 1-step lookahead.

        Algorithm:
        1. Generate candidate voicings for each chord
        2. For each transition, evaluate:
           - Voice motion distance
           - music21.voiceLeading.VoiceLeadingQuartet violations
           - If lookahead available, consider next transition too
        3. Use dynamic programming to find optimal path

        Args:
            chords: List of music21 RomanNumeral objects
            inversion_constraints: Optional list of allowed inversions per chord.
                Each element is a list of allowed inversion numbers (0-3).
                Example: [[0, 1], [2], [0]] means chord 0 can be root or first inversion,
                chord 1 must be second inversion, chord 2 must be root position.

        Returns:
            List of MIDI note lists (4 voices per chord)

        Examples:
            >>> from music21 import roman
            >>> from .voice_leading import VoiceLeader
            >>> vl = VoiceLeader()
            >>> chords = [roman.RomanNumeral('I', 'C'), roman.RomanNumeral('V', 'C')]
            >>> voicings = vl.voice_progression(chords)
            >>> len(voicings) == 2
            True
        """
        if not chords:
            return []

        # Generate candidate voicings for all chords
        all_candidates = []
        for i, chord in enumerate(chords):
            # Get inversion constraint for this chord if specified
            allowed_inversions = None
            if inversion_constraints and i < len(inversion_constraints):
                allowed_inversions = inversion_constraints[i]

            candidates = self._generate_candidates(chord, allowed_inversions)
            all_candidates.append(candidates)

        # Dynamic programming with lookahead
        voiced_progression = []
        prev_voicing = None

        for i, chord in enumerate(chords):
            candidates_current = all_candidates[i]

            if i == 0:
                # First chord: pick best initial voicing (close position, good spacing)
                best_voicing = self._choose_initial_voicing(candidates_current)
            else:
                # Has previous chord
                if i < len(chords) - 1:
                    # Has next chord: use lookahead
                    candidates_next = all_candidates[i + 1]
                    best_voicing = self._voice_with_lookahead(
                        candidates_current,
                        candidates_next,
                        prev_voicing,
                        chords[i - 1],
                        chord,
                        chords[i + 1]
                    )
                else:
                    # Last chord: no lookahead
                    best_voicing = self._find_best_voicing(
                        candidates_current,
                        prev_voicing,
                        chords[i - 1],
                        chord
                    )

            voiced_progression.append(best_voicing)
            prev_voicing = best_voicing

        return voiced_progression

    def voice_progression_with_names(self, progression: List[roman.RomanNumeral]) -> List[List[str]]:
        """
        Voice a progression and return note names with correct enharmonic spelling.

        This method voices the progression using the voice leading algorithm, then
        extracts the correctly-spelled note names from the original RomanNumeral objects.

        Args:
            progression: List of music21 RomanNumeral objects

        Returns:
            List of lists containing note names (e.g., ["C4", "Eb4", "G4", "C5"])

        Examples:
            >>> from music21 import roman
            >>> vl = VoiceLeader()
            >>> chords = [roman.RomanNumeral('i', 'c'), roman.RomanNumeral('V7', 'c')]
            >>> names = vl.voice_progression_with_names(chords)
            >>> names[0]
            ['C4', 'Eb4', 'G4', 'C5']  # Correct spelling preserved
        """
        from music21 import pitch

        # Get MIDI voicings
        midi_voicings = self.voice_progression(progression)

        # For each chord, map MIDI numbers to correctly-spelled names
        result = []
        for chord, midi_voicing in zip(progression, midi_voicings):
            # Get all available pitches from the original chord
            available_pitches = {}
            for p in chord.pitches:
                # Store by pitch class (MIDI % 12) for lookup
                pitch_class = p.midi % 12
                if pitch_class not in available_pitches:
                    available_pitches[pitch_class] = p.name  # e.g., "E-", "C"

            # Build note names for this voicing
            note_names = []
            for midi_num in midi_voicing:
                pitch_class = midi_num % 12
                octave = midi_num // 12 - 1

                # Get correct spelling from the chord
                if pitch_class in available_pitches:
                    note_name = available_pitches[pitch_class]
                else:
                    # Fallback: create pitch object and use its spelling
                    # This happens for added notes (like 7ths)
                    temp_pitch = pitch.Pitch(midi=midi_num)
                    note_name = temp_pitch.name

                # Combine name and octave
                note_names.append(f"{note_name}{octave}")

            result.append(note_names)

        return result

    def _generate_candidates(self, chord: roman.RomanNumeral,
                            allowed_inversions: Optional[List[int]] = None) -> List[List[int]]:
        """
        Generate valid voicings within voice ranges.

        Args:
            chord: music21 RomanNumeral object
            allowed_inversions: Optional list of allowed inversion numbers (0-3).
                If None, all inversions are allowed. If specified, only voicings
                with bass notes that produce the allowed inversions will be generated.

        Returns:
            List of candidate voicings (each is a list of 4 MIDI notes for SATB)

        Examples:
            >>> chord = roman.RomanNumeral('I', 'C')
            >>> vl = VoiceLeader()
            >>> candidates = vl._generate_candidates(chord)
            >>> len(candidates) > 0
            True
        """
        # Get all available pitches across octaves
        chord_tones = ChordFactory.get_chord_tones(chord, octave_range=(3, 6))

        # Determine number of unique pitch classes
        pitches = chord.pitches
        num_pitch_classes = len(pitches)

        candidates = []

        if num_pitch_classes == 3:
            # Triad: pick 4 notes, doubling one pitch class
            # Common practice: double root or fifth
            for bass in chord_tones:
                if not (self.VOICE_RANGES['bass'][0] <= bass <= self.VOICE_RANGES['bass'][1]):
                    continue

                for tenor in chord_tones:
                    if not (self.VOICE_RANGES['tenor'][0] <= tenor <= self.VOICE_RANGES['tenor'][1]):
                        continue
                    if tenor < bass:
                        continue

                    for alto in chord_tones:
                        if not (self.VOICE_RANGES['alto'][0] <= alto <= self.VOICE_RANGES['alto'][1]):
                            continue
                        if alto < tenor:
                            continue

                        for soprano in chord_tones:
                            if not (self.VOICE_RANGES['soprano'][0] <= soprano <= self.VOICE_RANGES['soprano'][1]):
                                continue
                            if soprano < alto:
                                continue

                            voicing = [bass, tenor, alto, soprano]

                            # Check that we have all 3 pitch classes (mod 12)
                            pitch_classes = set(n % 12 for n in voicing)
                            required_pcs = set(p.midi % 12 for p in pitches)

                            if pitch_classes == required_pcs and self._is_valid_voicing(voicing):
                                candidates.append(voicing)

        elif num_pitch_classes == 4:
            # Seventh chord: use all 4 pitch classes, one each
            for bass in chord_tones:
                if not (self.VOICE_RANGES['bass'][0] <= bass <= self.VOICE_RANGES['bass'][1]):
                    continue

                for tenor in chord_tones:
                    if not (self.VOICE_RANGES['tenor'][0] <= tenor <= self.VOICE_RANGES['tenor'][1]):
                        continue
                    if tenor < bass:
                        continue

                    for alto in chord_tones:
                        if not (self.VOICE_RANGES['alto'][0] <= alto <= self.VOICE_RANGES['alto'][1]):
                            continue
                        if alto < tenor:
                            continue

                        for soprano in chord_tones:
                            if not (self.VOICE_RANGES['soprano'][0] <= soprano <= self.VOICE_RANGES['soprano'][1]):
                                continue
                            if soprano < alto:
                                continue

                            voicing = [bass, tenor, alto, soprano]

                            # Check that we have all 4 pitch classes
                            pitch_classes = set(n % 12 for n in voicing)
                            required_pcs = set(p.midi % 12 for p in pitches)

                            if pitch_classes == required_pcs and self._is_valid_voicing(voicing):
                                candidates.append(voicing)

        # Filter by allowed inversions if specified
        if allowed_inversions is not None:
            filtered_candidates = []
            for voicing in candidates:
                inversion = self._detect_voicing_inversion(chord, voicing)
                if inversion in allowed_inversions:
                    filtered_candidates.append(voicing)

            # Graceful constraint relaxation if no candidates match
            if not filtered_candidates:
                logger.info(f"No candidates match exact inversion constraints {allowed_inversions}, "
                           "trying adjacent inversions")
                # Try allowing adjacent inversions (e.g., if [0] requested, try [0, 1])
                relaxed_inversions = set(allowed_inversions)
                for inv in allowed_inversions:
                    if inv > 0:
                        relaxed_inversions.add(inv - 1)
                    if inv < 3:
                        relaxed_inversions.add(inv + 1)

                for voicing in candidates:
                    inversion = self._detect_voicing_inversion(chord, voicing)
                    if inversion in relaxed_inversions:
                        filtered_candidates.append(voicing)

                # If still no candidates, fall back to any inversion
                if not filtered_candidates:
                    logger.warning(f"No candidates match relaxed inversions {relaxed_inversions}, "
                                  "using any available inversion")
                    filtered_candidates = candidates
                else:
                    logger.info(f"Found {len(filtered_candidates)} candidates with relaxed inversions")

            candidates = filtered_candidates

        # Limit candidates to avoid excessive computation
        return candidates[:200]

    def _detect_voicing_inversion(self, chord: roman.RomanNumeral, voicing: List[int]) -> int:
        """
        Detect the inversion of a voicing based on which chord tone is in the bass.

        Args:
            chord: music21 RomanNumeral object
            voicing: List of 4 MIDI notes [bass, tenor, alto, soprano]

        Returns:
            Inversion number: 0=root position, 1=first inversion (3rd in bass),
            2=second inversion (5th in bass), 3=third inversion (7th in bass)

        Examples:
            >>> from music21 import roman
            >>> vl = VoiceLeader()
            >>> chord = roman.RomanNumeral('I', 'C')
            >>> vl._detect_voicing_inversion(chord, [60, 64, 67, 72])  # C in bass
            0
            >>> vl._detect_voicing_inversion(chord, [64, 67, 72, 76])  # E in bass
            1
        """
        if not voicing:
            return 0

        bass_midi = voicing[0]
        bass_pitch_class = bass_midi % 12

        # Get the chord's pitches ordered by their role (root, third, fifth, seventh)
        chord_pitches = chord.pitches
        chord_pitch_classes = [p.midi % 12 for p in chord_pitches]

        # Find which chord member is in the bass
        # The inversion corresponds to the position of the bass note in the chord structure
        try:
            # Get the root of the chord
            root_pc = chord.root().midi % 12

            # Calculate interval from root to bass note (mod 12)
            interval_from_root = (bass_pitch_class - root_pc) % 12

            # Map interval to inversion
            # Root (0 semitones) = root position (0)
            # Third (3-4 semitones) = first inversion (1)
            # Fifth (7 semitones) = second inversion (2)
            # Seventh (10-11 semitones) = third inversion (3)

            if interval_from_root == 0:
                return 0  # Root position
            elif interval_from_root in [3, 4]:
                return 1  # First inversion (third in bass)
            elif interval_from_root == 7:
                return 2  # Second inversion (fifth in bass)
            elif interval_from_root in [10, 11]:
                return 3  # Third inversion (seventh in bass)
            else:
                # Fallback: check against chord members in order
                if len(chord_pitch_classes) > 0 and bass_pitch_class == chord_pitch_classes[0]:
                    return 0
                elif len(chord_pitch_classes) > 1 and bass_pitch_class == chord_pitch_classes[1]:
                    return 1
                elif len(chord_pitch_classes) > 2 and bass_pitch_class == chord_pitch_classes[2]:
                    return 2
                elif len(chord_pitch_classes) > 3 and bass_pitch_class == chord_pitch_classes[3]:
                    return 3
                else:
                    return 0

        except Exception:
            # If something goes wrong, default to root position
            return 0

    def _is_valid_voicing(self, voicing: List[int]) -> bool:
        """
        Check if voicing is valid (reasonable spacing, no voice crossing, no duplicate pitches).

        Args:
            voicing: List of 4 MIDI notes [bass, tenor, alto, soprano]

        Returns:
            True if valid

        Examples:
            >>> vl = VoiceLeader()
            >>> vl._is_valid_voicing([60, 64, 67, 72])
            True
            >>> vl._is_valid_voicing([60, 60, 64, 67])  # Duplicate MIDI note
            False
        """
        if len(voicing) != 4:
            return False

        # CRITICAL: All 4 MIDI notes must be unique (no duplicate pitches in same octave)
        if len(set(voicing)) != 4:
            return False

        # Check spacing between upper voices (no more than an octave)
        for i in range(1, len(voicing) - 1):
            if voicing[i + 1] - voicing[i] > 12:
                return False

        # Bass to tenor can be wider (up to 1.5 octaves)
        if voicing[1] - voicing[0] > 18:
            return False

        # Check no voice crossing
        for i in range(len(voicing) - 1):
            if voicing[i] > voicing[i + 1]:
                return False

        return True

    def _choose_initial_voicing(self, candidates: List[List[int]]) -> List[int]:
        """
        Choose best initial voicing (favor close position, good spacing).

        Args:
            candidates: List of candidate voicings

        Returns:
            Best initial voicing

        Examples:
            >>> vl = VoiceLeader()
            >>> candidates = [[60, 64, 67, 72], [60, 67, 72, 76]]
            >>> voicing = vl._choose_initial_voicing(candidates)
            >>> voicing in candidates
            True
        """
        if not candidates:
            # Fallback: create a basic C major chord
            return [60, 64, 67, 72]

        # Score each candidate
        best_voicing = candidates[0]
        best_score = float('inf')

        for voicing in candidates:
            # Prefer close position (smaller total span)
            span = voicing[-1] - voicing[0]

            # Prefer voicings with reasonable spacing
            spacing_penalty = 0
            for i in range(len(voicing) - 1):
                interval = voicing[i + 1] - voicing[i]
                if interval > 12:
                    spacing_penalty += (interval - 12)

            score = span + spacing_penalty

            if score < best_score:
                best_score = score
                best_voicing = voicing

        return best_voicing

    def _find_best_voicing(self, candidates: List[List[int]],
                          prev_voicing: List[int],
                          prev_chord: roman.RomanNumeral,
                          current_chord: roman.RomanNumeral) -> List[int]:
        """
        Find best voicing that minimizes cost from previous voicing.

        Args:
            candidates: List of candidate voicings for current chord
            prev_voicing: Previous chord's voicing
            prev_chord: Previous RomanNumeral
            current_chord: Current RomanNumeral

        Returns:
            Best voicing for current chord

        Examples:
            >>> from music21 import roman
            >>> vl = VoiceLeader()
            >>> prev_chord = roman.RomanNumeral('I', 'C')
            >>> curr_chord = roman.RomanNumeral('V', 'C')
            >>> candidates = [[67, 71, 74, 79]]
            >>> prev_voicing = [60, 64, 67, 72]
            >>> best = vl._find_best_voicing(candidates, prev_voicing, prev_chord, curr_chord)
            >>> best in candidates
            True
        """
        if not candidates:
            return prev_voicing

        best_voicing = candidates[0]
        best_cost = float('inf')

        for candidate in candidates:
            cost = self._evaluate_transition(
                prev_voicing,
                candidate,
                prev_chord,
                current_chord
            )

            if cost < best_cost:
                best_cost = cost
                best_voicing = candidate

        return best_voicing

    def _voice_with_lookahead(self, candidates_current: List[List[int]],
                              candidates_next: List[List[int]],
                              prev_voicing: List[int],
                              prev_chord: roman.RomanNumeral,
                              chord_current: roman.RomanNumeral,
                              chord_next: roman.RomanNumeral) -> List[int]:
        """
        Choose voicing considering both current and next transition.

        For each candidate_current:
            cost1 = transition(prev → candidate_current)
            For each candidate_next:
                cost2 = transition(candidate_current → candidate_next)
            total_cost = cost1 + 0.5 * min(cost2)  # Discount future

        Return candidate_current with minimum total_cost

        Args:
            candidates_current: Candidates for current chord
            candidates_next: Candidates for next chord
            prev_voicing: Previous chord's voicing
            prev_chord: Previous RomanNumeral
            chord_current: Current RomanNumeral
            chord_next: Next RomanNumeral

        Returns:
            Best voicing for current chord considering lookahead

        Examples:
            >>> from music21 import roman
            >>> vl = VoiceLeader()
            >>> prev_chord = roman.RomanNumeral('I', 'C')
            >>> curr_chord = roman.RomanNumeral('IV', 'C')
            >>> next_chord = roman.RomanNumeral('V', 'C')
            >>> candidates_curr = [[65, 69, 72, 77]]
            >>> candidates_next = [[67, 71, 74, 79]]
            >>> prev_voicing = [60, 64, 67, 72]
            >>> best = vl._voice_with_lookahead(
            ...     candidates_curr, candidates_next, prev_voicing,
            ...     prev_chord, curr_chord, next_chord
            ... )
            >>> best in candidates_curr
            True
        """
        if not candidates_current:
            return prev_voicing

        best_voicing = candidates_current[0]
        best_total_cost = float('inf')

        for candidate_current in candidates_current:
            # Cost from previous to current
            cost1 = self._evaluate_transition(
                prev_voicing,
                candidate_current,
                prev_chord,
                chord_current
            )

            # Find minimum cost to next chord
            min_cost2 = float('inf')
            for candidate_next in candidates_next[:50]:  # Sample for performance
                cost2 = self._evaluate_transition(
                    candidate_current,
                    candidate_next,
                    chord_current,
                    chord_next
                )
                if cost2 < min_cost2:
                    min_cost2 = cost2

            # Total cost with discounted future
            total_cost = cost1 + 0.5 * min_cost2

            if total_cost < best_total_cost:
                best_total_cost = total_cost
                best_voicing = candidate_current

        return best_voicing

    def _evaluate_transition(self, voicing1: List[int],
                            voicing2: List[int],
                            chord1: roman.RomanNumeral,
                            chord2: roman.RomanNumeral) -> float:
        """
        Score a voice leading transition.

        Uses music21.voiceLeading.VoiceLeadingQuartet:
        - Check parallelFifth(), parallelOctave()
        - Check voiceCrossing()
        - Measure total voice motion

        Args:
            voicing1: First voicing (4 MIDI notes)
            voicing2: Second voicing (4 MIDI notes)
            chord1: First RomanNumeral
            chord2: Second RomanNumeral

        Returns:
            Cost (lower is better)

        Examples:
            >>> from music21 import roman
            >>> vl = VoiceLeader()
            >>> chord1 = roman.RomanNumeral('I', 'C')
            >>> chord2 = roman.RomanNumeral('V', 'C')
            >>> cost = vl._evaluate_transition([60, 64, 67, 72], [67, 71, 74, 79], chord1, chord2)
            >>> cost >= 0
            True
        """
        # Base cost: total voice motion
        motion = sum(abs(v2 - v1) for v1, v2 in zip(voicing1, voicing2))

        penalty = 0.0

        # Create voice leading quartet for music21 analysis
        try:
            # Convert MIDI numbers to pitch objects
            v1_pitches = [pitch.Pitch(midi=m) for m in voicing1]
            v2_pitches = [pitch.Pitch(midi=m) for m in voicing2]

            # Check each pair of voices for parallel motion
            for i in range(len(voicing1)):
                for j in range(i + 1, len(voicing1)):
                    vlq = voiceLeading.VoiceLeadingQuartet(
                        v1_pitches[i], v1_pitches[j],
                        v2_pitches[i], v2_pitches[j]
                    )

                    # Parallel fifths
                    if vlq.parallelFifth():
                        penalty += 100.0

                    # Parallel octaves
                    if vlq.parallelOctave():
                        penalty += 100.0

                    # Voice crossing (penalize but not as heavily)
                    if vlq.voiceCrossing():
                        penalty += 20.0

        except Exception:
            # If music21 analysis fails, fall back to simple checks
            pass

        # Penalize large leaps (more than a perfect 5th = 7 semitones)
        for v1, v2 in zip(voicing1, voicing2):
            leap = abs(v2 - v1)
            if leap > 7:
                penalty += (leap - 7) * 3.0

        return motion + penalty
