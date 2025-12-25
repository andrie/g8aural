"""
Chord progression generator using music21 and Bach corpus patterns.

This module generates chord progressions using music21's RomanNumeral analysis
combined with Markov chain models based on Bach chorale patterns.
"""
import random
from typing import List, Optional
from music21 import roman

from .cadences import CadenceType, CadencePattern
from .voice_leading import VoiceLeader
from .roman_numerals import ChordFactory
from .markov_model import MarkovChordSelector


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
                 keys: Optional[List[str]] = None):
        """
        Initialize the generator.

        Args:
            min_length: Minimum number of chords in progression
            max_length: Maximum number of chords in progression
            use_voice_leading: Apply automatic voice leading (default True)
            use_sevenths: Use 7th chords where appropriate (default True)
            use_corpus: Use Bach corpus patterns (default True)
            corpus_temperature: Randomness for Markov model (0.0=deterministic, 2.0=very random)
            key: Key for progressions (e.g., 'C', 'G', 'd' for D minor)
            keys: Optional list of keys to randomly choose from (e.g., ['C', 'c'] for C major and minor)
        """
        self.min_length = min_length
        self.max_length = max_length
        self.use_voice_leading = use_voice_leading
        self.use_sevenths = use_sevenths
        self.use_corpus = use_corpus
        self.key = key
        self.keys = keys  # List of keys to choose from
        self.corpus_temperature = corpus_temperature

        self.voice_leader = VoiceLeader() if use_voice_leading else None
        self.markov_selector = MarkovChordSelector() if use_corpus else None

    def generate_progression(self, cadence_type: CadenceType) -> List[roman.RomanNumeral]:
        """
        Generate a chord progression ending with specified cadence.

        Args:
            cadence_type: The target cadence type

        Returns:
            List of music21 RomanNumeral objects forming a complete progression

        Examples:
            >>> from .cadences import CadenceType
            >>> generator = ChordProgressionGenerator()
            >>> progression = generator.generate_progression(CadenceType.PERFECT)
            >>> len(progression) >= 4
            True
        """
        # Choose a random key if keys list is provided
        current_key = random.choice(self.keys) if self.keys else self.key

        # Determine total length
        total_length = random.randint(self.min_length, self.max_length)

        # Get the final two chords (the cadence)
        penultimate_degree, final_degree = CadencePattern.get_cadence_chords(cadence_type)

        # Calculate how many chords we need before the cadence
        intro_length = total_length - 2

        # Generate introduction chords (as scale degrees)
        intro_degrees = self._generate_intro(intro_length, penultimate_degree, cadence_type)

        # Combine intro + cadence
        all_degrees = intro_degrees + [penultimate_degree, final_degree]

        # Convert scale degrees to RomanNumeral objects
        progression = []
        for i, degree in enumerate(all_degrees):
            # Use sevenths on degrees 2, 5, 6, 7 (except first and last chord)
            use_seventh = (self.use_sevenths and
                          degree in [2, 5, 6, 7] and
                          i > 0 and
                          i < len(all_degrees) - 1)

            chord = ChordFactory.create_chord(degree, current_key, use_seventh)
            progression.append(chord)

        return progression

    def _generate_intro(self, length: int, target_degree: int,
                       cadence_type: CadenceType) -> List[int]:
        """
        Generate introduction chords leading to the cadence.

        Args:
            length: Number of intro chords to generate
            target_degree: Scale degree we need to reach (first chord of cadence)
            cadence_type: Type of cadence for contextual choices

        Returns:
            List of scale degrees for the introduction

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
        if self.use_voice_leading and self.voice_leader:
            # Apply voice leading algorithm
            return self.voice_leader.voice_progression(progression)
        else:
            # Simple root position fallback
            return [ChordFactory.get_midi_notes(chord) for chord in progression]

    def progression_to_symbols(self, progression: List[roman.RomanNumeral]) -> List[str]:
        """
        Convert a chord progression to Roman numeral symbols.

        Args:
            progression: List of music21 RomanNumeral objects

        Returns:
            List of Roman numeral strings

        Examples:
            >>> from music21 import roman
            >>> generator = ChordProgressionGenerator()
            >>> chords = [roman.RomanNumeral('I', 'C'), roman.RomanNumeral('V7', 'C')]
            >>> symbols = generator.progression_to_symbols(chords)
            >>> symbols
            ['I', 'V7']
        """
        return [ChordFactory.get_roman_numeral_string(chord) for chord in progression]

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
