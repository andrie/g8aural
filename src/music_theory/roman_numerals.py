"""
Wrapper for music21's RomanNumeral functionality.

Provides a simplified interface for creating and working with chords
in the context of the chord progression generator.
"""

from typing import List, Optional
from music21 import roman, note, pitch


class ChordFactory:
    """Creates chords using music21 with simplified interface."""

    # Map scale degree numbers to Roman numeral figures in major keys
    MAJOR_SCALE_DEGREES = {
        1: 'I',
        2: 'ii',
        3: 'iii',
        4: 'IV',
        5: 'V',
        6: 'vi',
        7: 'viio'  # Diminished seventh
    }

    # Map scale degree numbers to Roman numeral figures in minor keys
    MINOR_SCALE_DEGREES = {
        1: 'i',
        2: 'iio',  # Diminished
        3: 'III',
        4: 'iv',
        5: 'V',    # Usually major in minor keys
        6: 'VI',
        7: 'viio'
    }

    @staticmethod
    def create_chord(scale_degree: int, key: str = 'C',
                     use_seventh: bool = False) -> roman.RomanNumeral:
        """
        Create a chord from scale degree.

        Args:
            scale_degree: 1-7 (I-vii)
            key: Key name (e.g., 'C', 'G', 'd' for D minor)
            use_seventh: Add seventh to chord

        Returns:
            music21 RomanNumeral object

        Examples:
            >>> chord = ChordFactory.create_chord(5, 'C', use_seventh=True)
            >>> chord.figure
            'V7'
        """
        # Determine if key is major or minor
        is_minor = key.islower()

        # Get Roman numeral figure
        scale_map = ChordFactory.MINOR_SCALE_DEGREES if is_minor else ChordFactory.MAJOR_SCALE_DEGREES
        figure = scale_map.get(scale_degree, 'I')

        # Add seventh if requested
        if use_seventh:
            # Remove 'o' suffix if present for diminished chords
            if figure.endswith('o'):
                figure = figure[:-1] + '7'  # Will be interpreted as diminished seventh
            else:
                figure = figure + '7'

        # Create RomanNumeral object
        # Ensure key is in the right case for music21
        if is_minor:
            key = key.lower()
        else:
            key = key.upper()

        rn = roman.RomanNumeral(figure, key)
        return rn

    @staticmethod
    def get_midi_notes(chord: roman.RomanNumeral,
                       voicing: Optional[List[int]] = None) -> List[int]:
        """
        Extract MIDI numbers from voiced chord.

        Args:
            chord: music21 RomanNumeral object
            voicing: Optional specific MIDI pitches to use

        Returns:
            List of MIDI note numbers

        Examples:
            >>> chord = ChordFactory.create_chord(1, 'C')
            >>> ChordFactory.get_midi_notes(chord)
            [60, 64, 67]
        """
        if voicing is not None:
            return voicing

        # Default: root position in middle octave
        pitches = chord.pitches
        midi_notes = [p.midi for p in pitches]

        # Ensure notes are in reasonable range (C4-C6)
        # Transpose if needed
        while max(midi_notes) > 84:  # Above C6
            midi_notes = [n - 12 for n in midi_notes]
        while min(midi_notes) < 48:  # Below C3
            midi_notes = [n + 12 for n in midi_notes]

        return sorted(midi_notes)

    @staticmethod
    def get_chord_tones(chord: roman.RomanNumeral,
                        octave_range: tuple = (3, 6)) -> List[int]:
        """
        Get all available MIDI pitches across octaves.

        Args:
            chord: music21 RomanNumeral object
            octave_range: Tuple of (min_octave, max_octave)

        Returns:
            List of all MIDI note numbers for this chord across the octave range

        Examples:
            >>> chord = ChordFactory.create_chord(1, 'C')
            >>> tones = ChordFactory.get_chord_tones(chord, (4, 5))
            >>> tones
            [60, 64, 67, 72, 76, 79]  # C, E, G in octaves 4 and 5
        """
        base_pitches = chord.pitches
        all_midi = []

        for octave in range(octave_range[0], octave_range[1] + 1):
            for p in base_pitches:
                # Create new pitch at specific octave
                new_pitch = pitch.Pitch(p.name)
                new_pitch.octave = octave
                all_midi.append(new_pitch.midi)

        return sorted(list(set(all_midi)))

    @staticmethod
    def get_roman_numeral_string(chord: roman.RomanNumeral) -> str:
        """
        Get Roman numeral string representation of chord.

        Args:
            chord: music21 RomanNumeral object

        Returns:
            String like "I", "V7", "vi", etc.

        Examples:
            >>> chord = ChordFactory.create_chord(5, 'C', use_seventh=True)
            >>> ChordFactory.get_roman_numeral_string(chord)
            'V7'
        """
        return chord.figure

    @staticmethod
    def get_scale_degree(chord: roman.RomanNumeral) -> int:
        """
        Get scale degree number from RomanNumeral.

        Args:
            chord: music21 RomanNumeral object

        Returns:
            Scale degree (1-7)

        Examples:
            >>> chord = ChordFactory.create_chord(5, 'C')
            >>> ChordFactory.get_scale_degree(chord)
            5
        """
        return chord.scaleDegree

    @staticmethod
    def detect_inversion(chord: roman.RomanNumeral) -> int:
        """
        Detect the inversion of a chord.

        Args:
            chord: music21 RomanNumeral object

        Returns:
            Inversion number: 0=root position, 1=first inversion (6),
            2=second inversion (6/4), 3=third inversion (for 7th chords)

        Examples:
            >>> chord = ChordFactory.create_chord(1, 'C')
            >>> ChordFactory.detect_inversion(chord)
            0
        """
        return chord.inversion()

    @staticmethod
    def get_inversion_label(chord: roman.RomanNumeral) -> str:
        """
        Get human-readable inversion label.

        Args:
            chord: music21 RomanNumeral object

        Returns:
            Inversion label: "root position", "first inversion", "second inversion",
            or "third inversion"

        Examples:
            >>> chord = ChordFactory.create_chord(1, 'C')
            >>> ChordFactory.get_inversion_label(chord)
            'root position'
        """
        inversion = chord.inversion()
        labels = {
            0: 'root position',
            1: 'first inversion',
            2: 'second inversion',
            3: 'third inversion'
        }
        return labels.get(inversion, f'inversion {inversion}')
