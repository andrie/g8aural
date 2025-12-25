"""
Musical note and chord representations with MIDI conversion.
"""
from enum import Enum
from typing import List


class NoteName(Enum):
    """Musical note names."""
    C = 0
    D = 2
    E = 4
    F = 5
    G = 7
    A = 9
    B = 11


class ChordQuality(Enum):
    """Chord quality types."""
    MAJOR = "major"
    MINOR = "minor"
    DIMINISHED = "diminished"
    DOMINANT_SEVENTH = "dominant_seventh"
    MINOR_SEVENTH = "minor_seventh"
    HALF_DIMINISHED_SEVENTH = "half_diminished_seventh"


class Note:
    """Represents a musical note with pitch and octave."""

    def __init__(self, name: NoteName, octave: int):
        """
        Initialize a Note.

        Args:
            name: The note name (C, D, E, F, G, A, B)
            octave: The octave number (middle C is C4)
        """
        self.name = name
        self.octave = octave

    def to_midi(self) -> int:
        """
        Convert note to MIDI number.
        MIDI note 60 = C4 (middle C)

        Returns:
            MIDI note number (0-127)
        """
        return (self.octave + 1) * 12 + self.name.value

    def __repr__(self) -> str:
        return f"Note({self.name.name}{self.octave})"


class Chord:
    """Represents a musical chord."""

    # Scale degree to note name mapping for C major
    SCALE_DEGREES_C_MAJOR = {
        1: NoteName.C,  # I
        2: NoteName.D,  # ii
        3: NoteName.E,  # iii
        4: NoteName.F,  # IV
        5: NoteName.G,  # V
        6: NoteName.A,  # vi
        7: NoteName.B,  # vii°
    }

    # Scale degree to chord quality for C major
    CHORD_QUALITIES_C_MAJOR = {
        1: ChordQuality.MAJOR,    # I
        2: ChordQuality.MINOR,    # ii
        3: ChordQuality.MINOR,    # iii
        4: ChordQuality.MAJOR,    # IV
        5: ChordQuality.MAJOR,    # V
        6: ChordQuality.MINOR,    # vi
        7: ChordQuality.DIMINISHED,  # vii°
    }

    # Scale degree to chord quality for C major (seventh chords)
    CHORD_QUALITIES_C_MAJOR_SEVENTH = {
        1: ChordQuality.MAJOR,    # I (keep as triad)
        2: ChordQuality.MINOR_SEVENTH,    # ii7
        3: ChordQuality.MINOR,    # iii (keep as triad)
        4: ChordQuality.MAJOR,    # IV (keep as triad)
        5: ChordQuality.DOMINANT_SEVENTH,    # V7
        6: ChordQuality.MINOR_SEVENTH,    # vi7
        7: ChordQuality.HALF_DIMINISHED_SEVENTH,  # viiø7
    }

    def __init__(self, scale_degree: int, quality: ChordQuality = None, inversion: int = 0, use_seventh: bool = False):
        """
        Initialize a Chord in C major.

        Args:
            scale_degree: Roman numeral as integer (1-7 for I-vii)
            quality: Chord quality (auto-determined if None)
            inversion: 0 = root position, 1 = first inversion, 2 = second inversion
            use_seventh: If True, use seventh chord version where applicable
        """
        self.scale_degree = scale_degree
        self.use_seventh = use_seventh

        # Determine quality based on whether seventh is requested
        if quality is None:
            if use_seventh and scale_degree in [2, 5, 6, 7]:
                self.quality = self.CHORD_QUALITIES_C_MAJOR_SEVENTH[scale_degree]
            else:
                self.quality = self.CHORD_QUALITIES_C_MAJOR[scale_degree]
        else:
            self.quality = quality

        self.inversion = inversion
        self.root_note = self.SCALE_DEGREES_C_MAJOR[scale_degree]

    def get_intervals(self) -> List[int]:
        """
        Get intervals from root for this chord quality.

        Returns:
            List of semitone intervals from root (3 for triads, 4 for sevenths)
        """
        if self.quality == ChordQuality.MAJOR:
            return [0, 4, 7]  # Root, major 3rd, perfect 5th
        elif self.quality == ChordQuality.MINOR:
            return [0, 3, 7]  # Root, minor 3rd, perfect 5th
        elif self.quality == ChordQuality.DIMINISHED:
            return [0, 3, 6]  # Root, minor 3rd, diminished 5th
        elif self.quality == ChordQuality.DOMINANT_SEVENTH:
            return [0, 4, 7, 10]  # Major triad + minor 7th
        elif self.quality == ChordQuality.MINOR_SEVENTH:
            return [0, 3, 7, 10]  # Minor triad + minor 7th
        elif self.quality == ChordQuality.HALF_DIMINISHED_SEVENTH:
            return [0, 3, 6, 10]  # Diminished triad + minor 7th
        return [0, 4, 7]

    def is_seventh(self) -> bool:
        """
        Check if this is a seventh chord.

        Returns:
            True if this is a seventh chord (4 notes), False for triad (3 notes)
        """
        return len(self.get_intervals()) == 4

    def get_chord_tones(self, base_octave: int = 4) -> List[int]:
        """
        Get all chord tones as MIDI numbers without inversion applied.

        Args:
            base_octave: Base octave for the root note

        Returns:
            List of MIDI note numbers in root position
        """
        intervals = self.get_intervals()
        root_midi = (base_octave + 1) * 12 + self.root_note.value
        return [root_midi + interval for interval in intervals]

    def to_midi_notes(self, base_octave: int = 4) -> List[int]:
        """
        Convert chord to list of MIDI note numbers.

        Args:
            base_octave: Base octave for the root note

        Returns:
            List of MIDI note numbers for this chord
        """
        intervals = self.get_intervals()
        root_midi = (base_octave + 1) * 12 + self.root_note.value

        # Apply inversion
        if self.inversion == 0:
            # Root position
            midi_notes = [root_midi + interval for interval in intervals]
        elif self.inversion == 1:
            # First inversion: move root up an octave
            midi_notes = [root_midi + intervals[1], root_midi + intervals[2], root_midi + 12]
        elif self.inversion == 2:
            # Second inversion: move root and third up an octave
            midi_notes = [root_midi + intervals[2], root_midi + 12, root_midi + 12 + intervals[1]]
        else:
            midi_notes = [root_midi + interval for interval in intervals]

        return midi_notes

    def get_roman_numeral(self) -> str:
        """
        Get Roman numeral notation for this chord.

        Returns:
            Roman numeral string (e.g., "I", "ii", "V7", "viiø7")
        """
        numerals = ["", "I", "II", "III", "IV", "V", "VI", "VII"]
        numeral = numerals[self.scale_degree]

        # Use lowercase for minor chords
        if self.quality in [ChordQuality.MINOR, ChordQuality.MINOR_SEVENTH]:
            numeral = numeral.lower()
        elif self.quality in [ChordQuality.DIMINISHED, ChordQuality.HALF_DIMINISHED_SEVENTH]:
            numeral = numeral.lower()

        # Add seventh notation
        if self.quality == ChordQuality.DOMINANT_SEVENTH:
            numeral += "7"
        elif self.quality == ChordQuality.MINOR_SEVENTH:
            numeral += "7"
        elif self.quality == ChordQuality.HALF_DIMINISHED_SEVENTH:
            numeral += "ø7"
        elif self.quality == ChordQuality.DIMINISHED:
            numeral += "°"

        return numeral

    def __repr__(self) -> str:
        return f"Chord({self.get_roman_numeral()}, {self.root_note.name})"
