"""
Chord progression generator using music21 and Bach corpus patterns.

This module generates chord progressions using music21's RomanNumeral analysis
combined with Markov chain models based on Bach chorale patterns.
"""
import logging
import random
from typing import List, Optional, Dict, Tuple
from music21 import roman

from .cadences import CadenceType, CadencePattern
from .voice_leading import VoiceLeader
from .roman_numerals import ChordFactory
from .markov_model import MarkovChordSelector

logger = logging.getLogger(__name__)


class ChordProgressionGenerator:
    """Generates chord progressions using music21 and Bach corpus patterns."""

    # Fallback strong progressions (used when corpus is unavailable)
    STRONG_PROGRESSIONS = {
        1: [2, 4, 5, 6],  # Added ii for more variety
        2: [5, 4],  # ii can go to V or IV
        3: [4, 6],
        4: [5, 1, 2],  # IV can go back to ii
        5: [1, 6],
        6: [4, 2, 5],  # vi can also go to V
        7: [1, 3]  # vii can go to iii as well as I
    }

    def __init__(self,
                 min_length: int = 4,
                 max_length: int = 8,
                 use_voice_leading: bool = True,
                 use_sevenths: bool = True,
                 use_corpus: bool = True,
                 corpus_temperature: float = 0.8,
                 key: str = 'C',
                 keys: Optional[List[str]] = None,
                 use_strict_cadence: bool = True):
        """
        Initialize the generator.

        Args:
            min_length: Minimum total progression length (default 4) when use_strict_cadence=True
            max_length: Maximum total progression length (default 8) when use_strict_cadence=True
            use_voice_leading: Apply automatic voice leading (default True)
            use_sevenths: Use 7th chords where appropriate (default True)
            use_corpus: Use Bach corpus patterns (default True)
            corpus_temperature: Randomness for Markov model (0.0=deterministic, 2.0=very random)
            key: Key for progressions (e.g., 'C', 'G', 'd' for D minor)
            keys: Optional list of keys to randomly choose from (e.g., ['C', 'c'] for C major and minor)
            use_strict_cadence: If True, generates 1-5 lead-in chords + strict 3-chord Grade 8 cadence (4-8 total).
                                If False, generates pure 3-chord cadence only (for simpler grade levels).
        """
        self.min_length = min_length
        self.max_length = max_length
        self.use_voice_leading = use_voice_leading
        self.use_sevenths = use_sevenths
        self.use_corpus = use_corpus
        self.key = key
        self.keys = keys  # List of keys to choose from
        self.corpus_temperature = corpus_temperature
        self.use_strict_cadence = use_strict_cadence

        self.voice_leader = VoiceLeader() if use_voice_leading else None
        self.markov_selector = MarkovChordSelector() if use_corpus else None

        # Cache for last generated voicing (to avoid re-voicing with wrong constraints)
        self._last_progression = None
        self._last_voiced_midi = None
        self._last_voiced_names = None

    def generate_progression(self, cadence_type: CadenceType, max_retries: int = 10) -> List[roman.RomanNumeral]:
        """
        Generate a cadence progression with retry logic.

        Hybrid Mode (use_strict_cadence=True, default for Grade 8):
            - Generates 1-5 lead-in chords (including starting tonic) using Bach corpus patterns
            - Appends strict 3-chord Grade 8 cadence with inversion constraints
            - Total length: 4-8 chords (min_length to max_length)
            - Voice leading applied to entire progression
            - Inversion constraints only on final 3 chords

        Pure 3-Chord Mode (use_strict_cadence=False, for Grades 6-7):
            - Generates only the 3-chord cadence pattern
            - Follows GRADE_8_INVERSION_RULES for inversions
            - Total length: 3 chords

        If voice leading cannot satisfy inversion constraints, it retries with different
        chord selections.

        Args:
            cadence_type: The target cadence type
            max_retries: Maximum number of attempts to generate valid progression (default 10)

        Returns:
            List of music21 RomanNumeral objects (4-8 chords in hybrid mode, 3 in pure mode)

        Raises:
            RuntimeError: If unable to generate valid progression after max_retries

        Examples:
            >>> from .cadences import CadenceType
            >>> generator = ChordProgressionGenerator(use_strict_cadence=True)
            >>> progression = generator.generate_progression(CadenceType.PERFECT)
            >>> 4 <= len(progression) <= 8  # Total: 4-8 chords (1-5 lead-in + 3 cadence)
            True
        """
        retry_count = 0
        for attempt in range(max_retries):
            try:
                progression = self._generate_single_attempt(cadence_type)

                # Validate that we got a valid progression
                expected_min_length = self.min_length if self.use_strict_cadence else 3
                if progression and len(progression) >= expected_min_length:
                    if retry_count > 0:
                        logger.info(
                            f"Successfully generated {cadence_type.value} cadence after {retry_count + 1} attempt(s)"
                        )
                    return progression

            except Exception as e:
                # Log the failure and retry
                retry_count += 1
                logger.info(
                    f"Attempt {attempt + 1}/{max_retries} failed for {cadence_type.value} cadence: {e}"
                )
                continue

        # If all retries failed, raise an error with warning
        logger.warning(
            f"Exhausted all {max_retries} attempts to generate {cadence_type.value} cadence. "
            "Voice leading constraints may be too restrictive."
        )
        raise RuntimeError(
            f"Failed to generate valid {cadence_type.value} cadence after {max_retries} attempts. "
            "Voice leading constraints may be too restrictive."
        )

    def _generate_single_attempt(self, cadence_type: CadenceType) -> List[roman.RomanNumeral]:
        """
        Generate a single attempt at a cadence progression.

        Hybrid Mode: Creates lead-in chords + 3-chord cadence with inversion constraints.
        Pure Mode: Creates only the 3-chord cadence with inversion constraints.

        Args:
            cadence_type: The target cadence type

        Returns:
            List of music21 RomanNumeral objects

        Raises:
            ValueError: If voice leading fails to satisfy inversion constraints
        """
        # Choose a random key if keys list is provided
        current_key = random.choice(self.keys) if self.keys else self.key

        # Get the three scale degrees for this cadence
        antepenultimate_degree, penultimate_degree, final_degree = CadencePattern.get_cadence_chords(cadence_type)

        if self.use_strict_cadence:
            # HYBRID MODE: Generate lead-in chords + strict 3-chord cadence
            # 1. Calculate total progression length (4-8 chords) and derive lead-in length (1-5)
            total_length = random.randint(self.min_length, self.max_length)  # 4-8 total chords
            intro_length = total_length - 3  # Lead-in: 1-5 chords (total - 3-chord cadence)
            intro_degrees = self._generate_intro(intro_length, antepenultimate_degree, cadence_type)

            # 2. Build the strict 3-chord cadence
            first_degree = self._select_antepenultimate(cadence_type, antepenultimate_degree)
            cadence_degrees = [first_degree, penultimate_degree, final_degree]

            # 3. Combine intro + cadence
            all_degrees = intro_degrees + cadence_degrees

            # 4. Convert all scale degrees to RomanNumeral objects
            progression = []
            for i, degree in enumerate(all_degrees):
                # Use sevenths on penultimate chord (second-to-last) if it's degree 5
                is_penultimate = (i == len(all_degrees) - 2)
                use_seventh = (self.use_sevenths and degree == 5 and is_penultimate)

                chord = ChordFactory.create_chord(degree, current_key, use_seventh)
                progression.append(chord)

            # 5. Apply voice leading with inversion constraints ONLY on final 3 chords
            if self.use_voice_leading and self.voice_leader:
                # Create constraints: None for lead-in, specific constraints for final 3 chords
                cadence_constraints = self._generate_inversion_constraints(cadence_type)
                full_constraints = [None] * len(intro_degrees) + cadence_constraints

                logger.debug(
                    f"Hybrid mode: {len(intro_degrees)} lead-in chords + 3 cadence chords. "
                    f"Constraints on final 3: {cadence_constraints}"
                )

                # Get the voiced progression
                voiced_midi = self.voice_leader.voice_progression(progression, full_constraints)
                logger.debug(f"Voiced progression: {[len(v) for v in voiced_midi]} voices per chord")

                # Verify that the final 3 chords match constraints
                actual_inversions = self.progression_to_inversions(progression, voiced_midi)
                final_3_inversions = actual_inversions[-3:]
                logger.debug(f"Final 3 chord inversions: {final_3_inversions}")

                # Check if cadence constraints are satisfied
                for i, (expected, actual) in enumerate(zip(cadence_constraints, final_3_inversions)):
                    chord_idx = len(progression) - 3 + i
                    if actual not in expected:
                        logger.warning(
                            f"Cadence chord {i+1}/3 (position {chord_idx}): expected inversions {expected}, got {actual}. "
                            f"Chord: {ChordFactory.get_roman_numeral_string(progression[chord_idx])}"
                        )
                        raise ValueError(f"Voice leading produced inversion {actual}, expected one of {expected}")

                logger.debug(f"All cadence inversion constraints satisfied!")

                # Cache the voicing for later use
                self._last_progression = progression
                self._last_voiced_midi = voiced_midi
                # Generate note names from the voiced MIDI (preserving correct spellings)
                self._last_voiced_names = self._midi_to_note_names(progression, voiced_midi)

        else:
            # PURE 3-CHORD MODE: Generate only the 3-chord cadence
            first_degree = self._select_antepenultimate(cadence_type, antepenultimate_degree)
            degrees = [first_degree, penultimate_degree, final_degree]

            # Convert scale degrees to RomanNumeral objects
            progression = []
            for i, degree in enumerate(degrees):
                # Use sevenths on penultimate chord (middle chord) if it's degree 5
                use_seventh = (self.use_sevenths and degree == 5 and i == 1)

                chord = ChordFactory.create_chord(degree, current_key, use_seventh)
                progression.append(chord)

            # Apply voice leading with inversion constraints
            if self.use_voice_leading and self.voice_leader:
                inversion_constraints = self._generate_inversion_constraints(cadence_type)
                logger.debug(f"Pure 3-chord mode. Inversion constraints: {inversion_constraints}")

                # Get the voiced progression
                voiced_midi = self.voice_leader.voice_progression(progression, inversion_constraints)
                logger.debug(f"Voiced progression: {voiced_midi}")

                # Verify that the inversions match constraints
                actual_inversions = self.progression_to_inversions(progression, voiced_midi)
                logger.debug(f"Actual inversions: {actual_inversions}")

                # Check if constraints are satisfied
                for i, (expected, actual) in enumerate(zip(inversion_constraints, actual_inversions)):
                    if actual not in expected:
                        logger.warning(
                            f"Chord {i+1}/3: expected inversions {expected}, got {actual}. "
                            f"Chord: {ChordFactory.get_roman_numeral_string(progression[i])}"
                        )
                        raise ValueError(f"Voice leading produced inversion {actual}, expected one of {expected}")

                logger.debug(f"All inversion constraints satisfied!")

                # Cache the voicing for later use
                self._last_progression = progression
                self._last_voiced_midi = voiced_midi
                # Generate note names from the voiced MIDI (preserving correct spellings)
                self._last_voiced_names = self._midi_to_note_names(progression, voiced_midi)

        return progression

    def _midi_to_note_names(self, progression: List[roman.RomanNumeral],
                           midi_voicings: List[List[int]]) -> List[List[str]]:
        """
        Convert MIDI voicings to note names with correct enharmonic spelling.

        Args:
            progression: List of RomanNumeral objects
            midi_voicings: List of MIDI note lists

        Returns:
            List of note name lists
        """
        from music21 import pitch

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
                    temp_pitch = pitch.Pitch(midi=midi_num)
                    note_name = temp_pitch.name

                # Combine name and octave
                note_names.append(f"{note_name}{octave}")

            result.append(note_names)

        return result

    def _select_antepenultimate(self, cadence_type: CadenceType, default_degree: int) -> int:
        """
        Select the antepenultimate (first) chord for the cadence.

        For most cadences, this uses the default degree from CadencePattern.
        This method allows for variation in future enhancements.

        Args:
            cadence_type: The type of cadence
            default_degree: The default scale degree from CadencePattern

        Returns:
            Scale degree for the first chord

        Examples:
            >>> generator = ChordProgressionGenerator()
            >>> degree = generator._select_antepenultimate(CadenceType.PERFECT, 1)
            >>> degree
            1
        """
        # For now, use the default degree
        # Future enhancement: could randomly select from common approach chords
        # e.g., for Perfect cadence (I-V-I), could start with I, IV, or vi
        return default_degree

    def _generate_inversion_constraints(self, cadence_type: CadenceType) -> List[List[int]]:
        """
        Get inversion constraints for the cadence from GRADE_8_INVERSION_RULES.

        Args:
            cadence_type: The type of cadence

        Returns:
            List of 3 lists, each containing allowed inversion numbers for that chord.
            Inversions: 0=root, 1=first, 2=second, 3=third (for 7th chords)

        Examples:
            >>> generator = ChordProgressionGenerator()
            >>> constraints = generator._generate_inversion_constraints(CadenceType.PERFECT)
            >>> constraints
            [[2], [0, 1, 2], [0]]
        """
        return CadencePattern.get_allowed_inversions(cadence_type)

    def progression_to_inversions(self, progression: List[roman.RomanNumeral],
                                  voiced_midi: Optional[List[List[int]]] = None) -> List[int]:
        """
        Detect the inversions of each chord in a voiced progression.

        Args:
            progression: List of music21 RomanNumeral objects
            voiced_midi: Optional voiced MIDI notes. If not provided, will voice the progression.

        Returns:
            List of inversion numbers (0-3) for each chord

        Examples:
            >>> from music21 import roman
            >>> generator = ChordProgressionGenerator()
            >>> chords = [roman.RomanNumeral('I', 'C'), roman.RomanNumeral('V', 'C')]
            >>> inversions = generator.progression_to_inversions(chords)
            >>> all(inv in [0, 1, 2, 3] for inv in inversions)
            True
        """
        # Get voiced progression if not provided
        if voiced_midi is None:
            if self.use_voice_leading and self.voice_leader:
                voiced_midi = self.voice_leader.voice_progression(progression)
            else:
                # Without voice leading, use ChordFactory's default
                voiced_midi = [ChordFactory.get_midi_notes(chord) for chord in progression]

        # Detect inversion for each chord
        inversions = []
        for chord, voicing in zip(progression, voiced_midi):
            # Use the voice leader's inversion detection method
            if self.voice_leader:
                inversion = self.voice_leader._detect_voicing_inversion(chord, voicing)
            else:
                # Fallback: use ChordFactory's detect_inversion
                inversion = ChordFactory.detect_inversion(chord)

            inversions.append(inversion)

        return inversions

    def _generate_intro(self, length: int, target_degree: int,
                       cadence_type: CadenceType) -> List[int]:
        """
        Generate introduction chords leading to the cadence.

        Args:
            length: Number of intro chords to generate (1-5 in hybrid mode)
            target_degree: Scale degree we need to reach (first chord of cadence)
            cadence_type: Type of cadence for contextual choices

        Returns:
            List of scale degrees for the introduction (always starts with tonic)

        Examples:
            >>> generator = ChordProgressionGenerator()
            >>> intro = generator._generate_intro(3, 5, CadenceType.PERFECT)
            >>> len(intro) == 3
            True
            >>> intro[0] == 1  # Always starts with tonic
            True
        """
        if length == 0:
            return []

        # Always start with I (tonic)
        intro = [1]
        current = 1

        # Generate middle chords
        for i in range(1, length):
            # Check for excessive repetition (3+ consecutive same chords)
            consecutive_count = 1
            for j in range(len(intro) - 1, -1, -1):
                if intro[j] == current:
                    consecutive_count += 1
                else:
                    break

            # If we've repeated the same chord 2+ times, force a different choice
            force_different = consecutive_count >= 2

            if self.use_corpus and self.markov_selector:
                # Use Bach corpus patterns
                next_degree = self.markov_selector.get_next_chord(
                    current, cadence_type, self.corpus_temperature
                )

                # If forcing different and got same chord, try again or use fallback
                if force_different and next_degree == current:
                    # Try one more time with higher temperature (more random)
                    next_degree = self.markov_selector.get_next_chord(
                        current, cadence_type, min(self.corpus_temperature * 1.5, 2.0)
                    )

                if next_degree is None or (force_different and next_degree == current):
                    # Corpus had no good option, use rule fallback
                    exclude = current if force_different else None
                    next_degree = self._choose_next_chord_rules(current, target_degree, exclude)
            else:
                # Rule-based selection
                exclude = current if force_different else None
                next_degree = self._choose_next_chord_rules(current, target_degree, exclude)

            intro.append(next_degree)
            current = next_degree

        return intro

    def _choose_next_chord_rules(self, current: int, target_degree: int,
                                  exclude: Optional[int] = None) -> int:
        """
        Fallback rule-based chord selection.

        Args:
            current: Current scale degree
            target_degree: Target scale degree (for context)
            exclude: Optional scale degree to exclude (to prevent repetition)

        Returns:
            Next scale degree

        Examples:
            >>> generator = ChordProgressionGenerator()
            >>> next_chord = generator._choose_next_chord_rules(1, 5)
            >>> next_chord in [2, 4, 5, 6]
            True
        """
        valid = self.STRONG_PROGRESSIONS.get(current, [1, 5])

        # Exclude the specified chord if requested
        if exclude is not None and exclude in valid:
            valid = [deg for deg in valid if deg != exclude]
            if not valid:  # If no valid options left, use any strong progression
                valid = [2, 4, 5, 6]  # Common pre-dominant and dominant chords

        # Prefer chords that lead toward the target
        if target_degree in valid:
            # 70% chance to go directly to target if it's a strong progression
            if random.random() < 0.7:
                return target_degree

        return random.choice(valid)

    def progression_to_midi(self, progression: List[roman.RomanNumeral]) -> List[List[int]]:
        """
        Convert a chord progression to MIDI note numbers.

        Args:
            progression: List of music21 RomanNumeral objects

        Returns:
            List of lists, where each inner list contains MIDI notes for one chord

        Examples:
            >>> from music21 import roman
            >>> generator = ChordProgressionGenerator()
            >>> chords = [roman.RomanNumeral('I', 'C'), roman.RomanNumeral('V', 'C')]
            >>> midi = generator.progression_to_midi(chords)
            >>> len(midi) == 2
            True
            >>> all(isinstance(chord, list) for chord in midi)
            True
        """
        # Use cached voicing if available and matches the progression
        if (self._last_progression is not None and
            self._last_voiced_midi is not None and
            progression is self._last_progression):
            return self._last_voiced_midi

        # Otherwise, voice without constraints (old behavior for backwards compatibility)
        if self.use_voice_leading and self.voice_leader:
            # Apply voice leading algorithm
            return self.voice_leader.voice_progression(progression)
        else:
            # Simple root position fallback
            return [ChordFactory.get_midi_notes(chord) for chord in progression]

    def progression_to_symbols(self, progression: List[roman.RomanNumeral],
                               include_inversions: bool = True) -> List[str]:
        """
        Convert a chord progression to Roman numeral symbols with inversion labels.

        Args:
            progression: List of music21 RomanNumeral objects
            include_inversions: If True, add inversion labels (e.g., "Ic", "V7", "I6")

        Returns:
            List of Roman numeral strings with inversion labels

        Examples:
            >>> from music21 import roman
            >>> generator = ChordProgressionGenerator()
            >>> chords = [roman.RomanNumeral('I', 'C'), roman.RomanNumeral('V7', 'C')]
            >>> symbols = generator.progression_to_symbols(chords)
            >>> symbols
            ['I', 'V7']
        """
        if not include_inversions:
            return [ChordFactory.get_roman_numeral_string(chord) for chord in progression]

        # Get the voiced MIDI progression to detect actual inversions
        midi_voicings = self.progression_to_midi(progression)
        inversions = self.progression_to_inversions(progression, midi_voicings)

        # Build symbols with inversion labels
        symbols = []
        for chord, inversion in zip(progression, inversions):
            base_symbol = ChordFactory.get_roman_numeral_string(chord)
            symbol_with_inversion = self._add_inversion_label(base_symbol, inversion)
            symbols.append(symbol_with_inversion)

        return symbols

    def _add_inversion_label(self, base_symbol: str, inversion: int) -> str:
        """
        Add inversion label to a Roman numeral symbol.

        Args:
            base_symbol: Base Roman numeral (e.g., "I", "V7", "vi")
            inversion: Inversion number (0=root, 1=first, 2=second, 3=third)

        Returns:
            Symbol with inversion label (e.g., "I", "I6", "Ic", "V7", "V65")

        Examples:
            >>> generator = ChordProgressionGenerator()
            >>> generator._add_inversion_label("I", 0)
            'I'
            >>> generator._add_inversion_label("I", 1)
            'I6'
            >>> generator._add_inversion_label("I", 2)
            'Ic'
            >>> generator._add_inversion_label("V7", 1)
            'V65'
        """
        if inversion == 0:
            # Root position - no label needed
            return base_symbol

        # Check if this is a seventh chord
        is_seventh = '7' in base_symbol

        if is_seventh:
            # Seventh chord inversions use figured bass notation
            # Root position: V7, First: V65, Second: V43, Third: V42
            inversions_map = {
                1: '65',  # First inversion
                2: '43',  # Second inversion
                3: '42'   # Third inversion (or just '2')
            }
            # Remove the '7' and add the figured bass
            base_without_7 = base_symbol.replace('7', '')
            return f"{base_without_7}{inversions_map.get(inversion, '7')}"
        else:
            # Triad inversions
            # Root position: I, First: I6, Second: Ic (or I64)
            inversions_map = {
                1: '6',   # First inversion
                2: 'c'    # Second inversion (cadential 6/4)
            }
            suffix = inversions_map.get(inversion, '')
            return f"{base_symbol}{suffix}"

    def progression_to_note_names(self, progression: List[roman.RomanNumeral]) -> List[List[str]]:
        """
        Convert a chord progression to note names with correct enharmonic spelling.

        Args:
            progression: List of music21 RomanNumeral objects

        Returns:
            List of lists, where each inner list contains note names (e.g., "C4", "Eb4", "G4")

        Examples:
            >>> from music21 import roman
            >>> generator = ChordProgressionGenerator()
            >>> chords = [roman.RomanNumeral('i', 'c')]
            >>> names = generator.progression_to_note_names(chords)
            >>> names[0]
            ['C4', 'Eb4', 'G4']  # Correct spelling, not D#4
        """
        # Use cached note names if available and matches the progression
        if (self._last_progression is not None and
            self._last_voiced_names is not None and
            progression is self._last_progression):
            return self._last_voiced_names

        # Otherwise, voice without constraints (old behavior for backwards compatibility)
        if self.use_voice_leading and self.voice_leader:
            # Get the voiced progression with correct spellings
            return self.voice_leader.voice_progression_with_names(progression)
        else:
            # Simple fallback: extract pitches directly from RomanNumeral
            result = []
            for chord in progression:
                note_names = [p.nameWithOctave for p in chord.pitches]
                result.append(note_names)
            return result

    def extract_voices(self, progression: List[roman.RomanNumeral],
                      voices: Optional[List[str]] = None,
                      note_duration: float = 1.0) -> Dict[str, List[Tuple[int, float, float]]]:
        """
        Extract individual melodic voices from a 4-voice SATB progression.

        Args:
            progression: List of music21 RomanNumeral objects (voiced progression)
            voices: List of voice names to extract (default: ['soprano', 'bass'])
                    Options: 'soprano' (top), 'alto', 'tenor', 'bass' (bottom)
            note_duration: Duration of each note in seconds (default: 1.0)

        Returns:
            Dictionary mapping voice names to melody lists.
            Each melody is a list of (midi_note, start_time, duration) tuples.

        Examples:
            >>> generator = ChordProgressionGenerator()
            >>> progression = generator.generate_progression(CadenceType.PERFECT)
            >>> melodies = generator.extract_voices(progression, voices=['soprano', 'bass'])
            >>> 'soprano' in melodies and 'bass' in melodies
            True
            >>> len(melodies['soprano']) == len(progression)
            True
        """
        if voices is None:
            voices = ['soprano', 'bass']

        # Get voiced progression (may be 3-voice or 4-voice SATB)
        voiced_midi = self.progression_to_midi(progression)

        # Voice index mapping (SATB order: bass=0, tenor=1, alto=2, soprano=3)
        voice_indices = {
            'bass': 0,      # Lowest voice
            'tenor': 1,
            'alto': 2,
            'soprano': 3    # Highest voice
        }

        # Extract melodies
        melodies = {}
        for voice_name in voices:
            if voice_name not in voice_indices:
                logger.warning(f"Unknown voice name: {voice_name}. Skipping.")
                continue

            voice_idx = voice_indices[voice_name]
            melody = []

            for i, chord_voicing in enumerate(voiced_midi):
                # Handle soprano for non-4-voice progressions: use highest note (top voice)
                if voice_name == 'soprano' and voice_idx >= len(chord_voicing):
                    # For triads (3 voices) or other non-SATB progressions,
                    # soprano is the top voice (last element)
                    actual_idx = len(chord_voicing) - 1
                else:
                    actual_idx = voice_idx

                if actual_idx >= len(chord_voicing):
                    logger.warning(
                        f"Voice index {actual_idx} out of range for chord {i} "
                        f"(has {len(chord_voicing)} voices). Skipping."
                    )
                    continue

                # Extract the MIDI note for this voice
                midi_note = chord_voicing[actual_idx]
                start_time = i * note_duration
                duration = note_duration

                melody.append((midi_note, start_time, duration))

            melodies[voice_name] = melody

        return melodies
