"""
Enhanced voice leading with improved musicality and voice ranges.

This module extends the base VoiceLeader class with:
- Extended voice ranges for better coverage of bass clef
- Improved voice motion rules favoring contrary motion
- Common tone retention and proper voice resolution
- Better spacing algorithms for more musical voicings
- Special handling for cadential patterns
"""

import logging
from typing import List, Optional, Dict, Tuple
from music21 import roman, pitch, voiceLeading

from .voice_leading import VoiceLeader

logger = logging.getLogger(__name__)


class EnhancedVoiceLeader(VoiceLeader):
    """Enhanced voice leading with improved musicality."""

    # Extended voice ranges with wider bass range (MIDI note numbers)
    VOICE_RANGES = {
        'bass': (40, 60),      # E2 to C4 (wider range for proper bass)
        'tenor': (48, 69),     # C3 to A4
        'alto': (55, 74),      # G3 to D5
        'soprano': (60, 81),   # C4 to A5
    }

    def _evaluate_transition(self, voicing1: List[int],
                            voicing2: List[int],
                            chord1: roman.RomanNumeral,
                            chord2: roman.RomanNumeral) -> float:
        """
        Score a voice leading transition with enhanced musicality rules.

        Adds rewards for:
        - Contrary motion between soprano and bass
        - Common tone retention
        - Stepwise motion
        - Leading tone resolution

        Args:
            voicing1: First voicing (4 MIDI notes)
            voicing2: Second voicing (4 MIDI notes)
            chord1: First RomanNumeral
            chord2: Second RomanNumeral

        Returns:
            Cost (lower is better)
        """
        # Base cost: total voice motion
        motion = sum(abs(v2 - v1) for v1, v2 in zip(voicing1, voicing2))

        penalty = 0.0
        reward = 0.0

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

                    # Parallel fifths (prohibited)
                    if vlq.parallelFifth():
                        penalty += 100.0

                    # Parallel octaves (prohibited)
                    if vlq.parallelOctave():
                        penalty += 100.0

                    # Voice crossing (penalize but not as heavily)
                    if vlq.voiceCrossing():
                        penalty += 20.0

            # NEW: Reward contrary motion between outer voices
            bass_direction = 1 if voicing2[0] > voicing1[0] else -1 if voicing2[0] < voicing1[0] else 0
            soprano_direction = 1 if voicing2[-1] > voicing1[-1] else -1 if voicing2[-1] < voicing1[-1] else 0

            # Strongly prefer contrary motion between outer voices
            if bass_direction != 0 and soprano_direction != 0:
                if bass_direction != soprano_direction:
                    # True contrary motion (one up, one down)
                    reward += 15.0  # Increased reward for contrary motion
                else:
                    # Both voices moving in same direction (parallel)
                    # Penalize parallel motion between outer voices, especially for strong chord changes
                    # Strong chord changes are those where both voices move significantly
                    bass_leap = abs(voicing2[0] - voicing1[0])
                    soprano_leap = abs(voicing2[-1] - voicing1[-1])
                    if bass_leap > 2 and soprano_leap > 2:  # Both moving more than a whole step
                        penalty += 10.0  # Penalize parallel motion on strong chord changes

            # NEW: Reward common tone retention
            for v1, v2 in zip(voicing1, voicing2):
                if v1 == v2:  # Common tone retained
                    reward += 3.0

            # NEW: Reward stepwise motion in all voices
            for v1, v2 in zip(voicing1, voicing2):
                step = abs(v2 - v1)
                if step == 1 or step == 2:  # Semitone or whole tone
                    reward += 1.5

            # NEW: Check for proper leading tone resolution
            # Get key context for identifying leading tone
            key = chord1.key
            if key is None:
                key = chord2.key

            if key is not None:
                scale = key.getScale()
                leading_tone = scale.pitchFromDegree(7).midi % 12
                tonic = scale.pitchFromDegree(1).midi % 12

                # Check if any voice has the leading tone in the first chord
                for i, note in enumerate(voicing1):
                    if note % 12 == leading_tone:
                        # Found leading tone - check if it resolves to tonic
                        next_note = voicing2[i]
                        if next_note % 12 == tonic:
                            # Properly resolved leading tone
                            reward += 4.0
                        elif abs((next_note % 12) - tonic) > 2:
                            # Leading tone doesn't resolve properly
                            penalty += 5.0

        except Exception as e:
            # If music21 analysis fails, fall back to simple checks
            logger.debug(f"Music21 analysis failed in voice leading: {e}")
            pass

        # Penalize large leaps (more than a perfect 5th = 7 semitones)
        for i, (v1, v2) in enumerate(zip(voicing1, voicing2)):
            leap = abs(v2 - v1)
            if leap > 7:
                # Penalize large leaps more in inner voices
                if i == 1 or i == 2:  # Tenor or alto
                    penalty += (leap - 7) * 4.0
                else:  # Bass or soprano
                    penalty += (leap - 7) * 3.0

            # Specially penalize tritone leaps (augmented 4th/diminished 5th)
            if leap == 6:  # Tritone in semitones
                penalty += 5.0

        return motion + penalty - reward  # Lower score is better

    def _choose_initial_voicing(self, candidates: List[List[int]]) -> List[int]:
        """
        Choose best initial voicing with preference for open position.

        Args:
            candidates: List of candidate voicings

        Returns:
            Best initial voicing
        """
        if not candidates:
            # Fallback: create a basic C major chord in open position
            return [48, 64, 60, 72]  # C3, E4, G4, C5

        # Score each candidate
        best_voicing = candidates[0]
        best_score = float('inf')

        for voicing in candidates:
            # Prefer voicings with reasonable spacing
            spacing_penalty = 0
            spans = []

            for i in range(len(voicing) - 1):
                interval = voicing[i + 1] - voicing[i]
                spans.append(interval)
                if interval > 12:
                    spacing_penalty += (interval - 12)
                elif interval < 3:
                    spacing_penalty += (3 - interval) * 2  # Penalize very close voices

            # Calculate variance - prefer even spacing between voices
            if len(spans) > 0:
                mean_span = sum(spans) / len(spans)
                variance = sum((s - mean_span) ** 2 for s in spans) / len(spans)

                # Prefer open position (lower variance, more even spacing)
                score = spacing_penalty + variance * 0.5

                if score < best_score:
                    best_score = score
                    best_voicing = voicing

        return best_voicing

    def _voice_with_lookahead(self, candidates_current: List[List[int]],
                             candidates_next: List[List[int]],
                             prev_voicing: List[int],
                             prev_chord: roman.RomanNumeral,
                             chord_current: roman.RomanNumeral,
                             chord_next: roman.RomanNumeral) -> List[int]:
        """
        Choose voicing considering both current and next transition,
        with special handling for cadential patterns.

        Args:
            candidates_current: Candidates for current chord
            candidates_next: Candidates for next chord
            prev_voicing: Previous chord's voicing
            prev_chord: Previous RomanNumeral
            chord_current: Current RomanNumeral
            chord_next: Next RomanNumeral

        Returns:
            Best voicing for current chord considering lookahead
        """
        if not candidates_current:
            return prev_voicing

        best_voicing = candidates_current[0]
        best_total_cost = float('inf')

        # Special case handling for cadential patterns
        is_cadential_64 = False
        try:
            # Check if this is a cadential 6/4 chord based on its figure
            is_cadential_64 = (chord_current.figure in ['I64', 'i64'] and
                              chord_next.figure in ['V', 'V7', 'v', 'v7'])

            # Also check for first inversion chords that should be realized as cadential 6/4
            if not is_cadential_64 and chord_current.figure in ['I', 'i']:
                inversion = self._detect_voicing_inversion(chord_current, candidates_current[0])
                is_cadential_64 = (inversion == 2 and
                                  chord_next.figure in ['V', 'V7', 'v', 'v7'])
        except Exception:
            pass

        for candidate_current in candidates_current:
            # Cost from previous to current
            cost1 = self._evaluate_transition(
                prev_voicing,
                candidate_current,
                prev_chord,
                chord_current
            )

            # Apply special bonus for cadential 6/4 voicings
            if is_cadential_64:
                try:
                    # In cadential 6/4, the bass should be scale degree 5 (dominant)
                    key = chord_current.key
                    if key:
                        # Get the dominant pitch class in this key
                        dominant_pc = key.pitchFromDegree(5).pitchClass

                        # Check if the bass note is the dominant
                        bass_pc = candidate_current[0] % 12
                        if bass_pc == dominant_pc:
                            cost1 -= 20.0  # Big bonus for correct cadential 6/4 bass
                        else:
                            cost1 += 50.0  # Heavy penalty for wrong bass in cadential 6/4

                    # Also verify proper doubling (root doubled in I64)
                    root_pc = chord_current.root().midi % 12
                    root_count = sum(1 for n in candidate_current if n % 12 == root_pc)
                    if root_count >= 2:  # Root should be doubled in cadential 6/4
                        cost1 -= 10.0  # Bonus for correct doubling
                except Exception as e:
                    pass

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

    def _is_valid_voicing(self, voicing: List[int]) -> bool:
        """
        Check if voicing is valid with enhanced spacing rules.

        Args:
            voicing: List of 4 MIDI notes [bass, tenor, alto, soprano]

        Returns:
            True if valid
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

        # Bass to tenor can be wider (up to 2 octaves for extended bass range)
        if voicing[1] - voicing[0] > 24:
            return False

        # Check no voice crossing
        for i in range(len(voicing) - 1):
            if voicing[i] > voicing[i + 1]:
                return False

        return True

    def _generate_candidates(self, chord: roman.RomanNumeral,
                            allowed_inversions: Optional[List[int]] = None) -> List[List[int]]:
        """
        Generate valid voicings within voice ranges.

        Special handling for cadential 6/4 chords to ensure they're properly voiced.

        Args:
            chord: music21 RomanNumeral object
            allowed_inversions: Optional list of allowed inversion numbers (0-3).
                If None, all inversions are allowed. If specified, only voicings
                with bass notes that produce the allowed inversions will be generated.

        Returns:
            List of candidate voicings (each is a list of 4 MIDI notes for SATB)
        """
        # Special handling for cadential 6/4 chords
        is_cadential_64 = chord.figure in ['I64', 'i64'] or (
            chord.figure in ['I', 'i'] and allowed_inversions and 2 in allowed_inversions and len(allowed_inversions) == 1
        )

        if is_cadential_64:
            # For cadential 6/4, explicitly force dominant in bass
            try:
                # Get the key context
                key_context = chord.key
                if key_context:
                    # Get the dominant scale degree (5)
                    dominant_pitch = key_context.pitchFromDegree(5)
                    # Get the dominant's pitch class and find all octaves in bass range
                    dominant_pc = dominant_pitch.pitchClass

                    # Create modified chord with second inversion
                    # This ensures the candidates have the right bass note
                    chord2 = roman.RomanNumeral(chord.figure, key_context)
                    chord2.inversion(2)  # Force second inversion

                    # Generate candidates using the parent method
                    candidates = super()._generate_candidates(chord2, [2])

                    # Filter to keep only candidates with dominant in bass
                    filtered_candidates = []
                    for candidate in candidates:
                        if candidate[0] % 12 == dominant_pc:
                            filtered_candidates.append(candidate)

                    if filtered_candidates:
                        return filtered_candidates
            except Exception as e:
                # Fall back to regular candidate generation if special handling fails
                pass

        # Regular candidate generation from parent
        return super()._generate_candidates(chord, allowed_inversions)