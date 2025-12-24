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

    def __init__(self, scale_degree: int, quality: ChordQuality = None, inversion: int = 0):
        """
        Initialize a Chord in C major.

        Args:
            scale_degree: Roman numeral as integer (1-7 for I-vii)
            quality: Chord quality (auto-determined if None)
            inversion: 0 = root position, 1 = first inversion, 2 = second inversion
        """
        self.scale_degree = scale_degree
        self.quality = quality or self.CHORD_QUALITIES_C_MAJOR[scale_degree]
        self.inversion = inversion
        self.root_note = self.SCALE_DEGREES_C_MAJOR[scale_degree]

    def get_intervals(self) -> List[int]:
        """
        Get intervals from root for this chord quality.

        Returns:
            List of semitone intervals from root
        """
        if self.quality == ChordQuality.MAJOR:
            return [0, 4, 7]  # Root, major 3rd, perfect 5th
        elif self.quality == ChordQuality.MINOR:
            return [0, 3, 7]  # Root, minor 3rd, perfect 5th
        elif self.quality == ChordQuality.DIMINISHED:
            return [0, 3, 6]  # Root, minor 3rd, diminished 5th
        return [0, 4, 7]

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
            Roman numeral string (e.g., "I", "ii", "V")
        """
        numerals = ["", "I", "II", "III", "IV", "V", "VI", "VII"]
        numeral = numerals[self.scale_degree]

        # Use lowercase for minor chords
        if self.quality == ChordQuality.MINOR:
            numeral = numeral.lower()
        elif self.quality == ChordQuality.DIMINISHED:
            numeral = numeral.lower() + "°"

        return numeral

    def __repr__(self) -> str:
        return f"Chord({self.get_roman_numeral()}, {self.root_note.name})"
