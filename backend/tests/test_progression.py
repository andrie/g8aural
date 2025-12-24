"""
Unit tests for chord progression generation and music theory module.
"""
import pytest
from app.music_theory.notes import Note, NoteName, Chord, ChordQuality
from app.music_theory.cadences import CadenceType, CadencePattern
from app.music_theory.progression import ChordProgressionGenerator


class TestNote:
    """Tests for Note class."""

    def test_note_creation(self):
        """Test creating a Note."""
        note = Note(NoteName.C, 4)
        assert note.name == NoteName.C
        assert note.octave == 4

    def test_midi_conversion_middle_c(self):
        """Test MIDI conversion for middle C."""
        note = Note(NoteName.C, 4)
        assert note.to_midi() == 60

    def test_midi_conversion_various_notes(self):
        """Test MIDI conversion for various notes."""
        assert Note(NoteName.A, 4).to_midi() == 69
        assert Note(NoteName.G, 4).to_midi() == 67
        assert Note(NoteName.E, 4).to_midi() == 64


class TestChord:
    """Tests for Chord class."""

    def test_chord_creation(self):
        """Test creating chords."""
        chord = Chord(1)  # I chord in C major
        assert chord.scale_degree == 1
        assert chord.quality == ChordQuality.MAJOR
        assert chord.root_note == NoteName.C

    def test_chord_qualities_c_major(self):
        """Test that chord qualities match C major scale."""
        assert Chord(1).quality == ChordQuality.MAJOR    # I
        assert Chord(2).quality == ChordQuality.MINOR    # ii
        assert Chord(3).quality == ChordQuality.MINOR    # iii
        assert Chord(4).quality == ChordQuality.MAJOR    # IV
        assert Chord(5).quality == ChordQuality.MAJOR    # V
        assert Chord(6).quality == ChordQuality.MINOR    # vi
        assert Chord(7).quality == ChordQuality.DIMINISHED  # vii°

    def test_chord_root_notes(self):
        """Test that chord root notes match scale degrees."""
        assert Chord(1).root_note == NoteName.C
        assert Chord(2).root_note == NoteName.D
        assert Chord(3).root_note == NoteName.E
        assert Chord(4).root_note == NoteName.F
        assert Chord(5).root_note == NoteName.G
        assert Chord(6).root_note == NoteName.A
        assert Chord(7).root_note == NoteName.B

    def test_major_chord_intervals(self):
        """Test major chord intervals."""
        chord = Chord(1)  # C major
        assert chord.get_intervals() == [0, 4, 7]

    def test_minor_chord_intervals(self):
        """Test minor chord intervals."""
        chord = Chord(2)  # D minor
        assert chord.get_intervals() == [0, 3, 7]

    def test_diminished_chord_intervals(self):
        """Test diminished chord intervals."""
        chord = Chord(7)  # B diminished
        assert chord.get_intervals() == [0, 3, 6]

    def test_chord_to_midi_c_major(self):
        """Test C major chord MIDI conversion."""
        chord = Chord(1)
        midi_notes = chord.to_midi_notes(base_octave=4)
        assert midi_notes == [60, 64, 67]  # C4, E4, G4

    def test_chord_to_midi_g_major(self):
        """Test G major chord MIDI conversion."""
        chord = Chord(5)
        midi_notes = chord.to_midi_notes(base_octave=4)
        assert midi_notes == [67, 71, 74]  # G4, B4, D5

    def test_chord_roman_numeral_major(self):
        """Test Roman numeral for major chords."""
        assert Chord(1).get_roman_numeral() == "I"
        assert Chord(4).get_roman_numeral() == "IV"
        assert Chord(5).get_roman_numeral() == "V"

    def test_chord_roman_numeral_minor(self):
        """Test Roman numeral for minor chords."""
        assert Chord(2).get_roman_numeral() == "ii"
        assert Chord(3).get_roman_numeral() == "iii"
        assert Chord(6).get_roman_numeral() == "vi"

    def test_chord_roman_numeral_diminished(self):
        """Test Roman numeral for diminished chord."""
        assert Chord(7).get_roman_numeral() == "vii°"


class TestCadencePattern:
    """Tests for CadencePattern class."""

    def test_perfect_cadence_chords(self):
        """Test perfect cadence returns V-I."""
        pen, final = CadencePattern.get_cadence_chords(CadenceType.PERFECT)
        assert pen == 5  # V
        assert final == 1  # I

    def test_plagal_cadence_chords(self):
        """Test plagal cadence returns IV-I."""
        pen, final = CadencePattern.get_cadence_chords(CadenceType.PLAGAL)
        assert pen == 4  # IV
        assert final == 1  # I

    def test_imperfect_cadence_chords(self):
        """Test imperfect cadence returns I-V."""
        pen, final = CadencePattern.get_cadence_chords(CadenceType.IMPERFECT)
        assert pen == 1  # I
        assert final == 5  # V

    def test_interrupted_cadence_chords(self):
        """Test interrupted cadence returns V-vi."""
        pen, final = CadencePattern.get_cadence_chords(CadenceType.INTERRUPTED)
        assert pen == 5  # V
        assert final == 6  # vi

    def test_approach_chords_not_empty(self):
        """Test that all cadence types have approach chords."""
        for cadence_type in CadenceType:
            approaches = CadencePattern.get_common_approach_chords(cadence_type)
            assert len(approaches) > 0
            assert all(1 <= deg <= 7 for deg in approaches)

    def test_display_names(self):
        """Test display names contain cadence type."""
        for cadence_type in CadenceType:
            name = CadencePattern.get_display_name(cadence_type)
            assert len(name) > 0
            assert "Cadence" in name


class TestChordProgressionGenerator:
    """Tests for ChordProgressionGenerator class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.generator = ChordProgressionGenerator(min_length=4, max_length=8)

    def test_generator_initialization(self):
        """Test generator can be initialized."""
        gen = ChordProgressionGenerator(4, 8)
        assert gen.min_length == 4
        assert gen.max_length == 8

    def test_generate_progression_length(self):
        """Test generated progressions are correct length."""
        for cadence_type in CadenceType:
            progression = self.generator.generate_progression(cadence_type)
            assert 4 <= len(progression) <= 8

    def test_generate_progression_starts_with_tonic(self):
        """Test progressions start with I chord."""
        for cadence_type in CadenceType:
            progression = self.generator.generate_progression(cadence_type)
            assert progression[0].scale_degree == 1

    def test_perfect_cadence_ends_correctly(self):
        """Test perfect cadence ends with V-I."""
        progression = self.generator.generate_progression(CadenceType.PERFECT)
        assert progression[-2].scale_degree == 5  # V
        assert progression[-1].scale_degree == 1  # I

    def test_plagal_cadence_ends_correctly(self):
        """Test plagal cadence ends with IV-I."""
        progression = self.generator.generate_progression(CadenceType.PLAGAL)
        assert progression[-2].scale_degree == 4  # IV
        assert progression[-1].scale_degree == 1  # I

    def test_imperfect_cadence_ends_correctly(self):
        """Test imperfect cadence ends with I-V."""
        progression = self.generator.generate_progression(CadenceType.IMPERFECT)
        assert progression[-2].scale_degree == 1  # I
        assert progression[-1].scale_degree == 5  # V

    def test_interrupted_cadence_ends_correctly(self):
        """Test interrupted cadence ends with V-vi."""
        progression = self.generator.generate_progression(CadenceType.INTERRUPTED)
        assert progression[-2].scale_degree == 5  # V
        assert progression[-1].scale_degree == 6  # vi

    def test_progression_to_midi_returns_correct_structure(self):
        """Test MIDI conversion returns correct data structure."""
        progression = self.generator.generate_progression(CadenceType.PERFECT)
        midi = self.generator.progression_to_midi(progression)

        assert len(midi) == len(progression)
        for chord_midi in midi:
            assert isinstance(chord_midi, list)
            assert len(chord_midi) == 3  # Three notes per chord
            assert all(isinstance(note, int) for note in chord_midi)
            assert all(0 <= note <= 127 for note in chord_midi)  # Valid MIDI range

    def test_progression_to_symbols_returns_correct_structure(self):
        """Test symbol conversion returns correct data structure."""
        progression = self.generator.generate_progression(CadenceType.PERFECT)
        symbols = self.generator.progression_to_symbols(progression)

        assert len(symbols) == len(progression)
        assert all(isinstance(symbol, str) for symbol in symbols)
        assert symbols[0] == "I"  # First chord should be tonic

    def test_multiple_generations_vary(self):
        """Test that multiple generations produce variety."""
        progressions = [
            self.generator.generate_progression(CadenceType.PERFECT)
            for _ in range(5)
        ]

        # Check that not all progressions are identical
        # Convert to tuples of scale degrees for comparison
        progression_tuples = [
            tuple(chord.scale_degree for chord in prog)
            for prog in progressions
        ]

        # Should have at least 2 different progressions out of 5
        assert len(set(progression_tuples)) >= 2

    def test_all_chords_are_valid_scale_degrees(self):
        """Test all generated chords use valid scale degrees (1-7)."""
        for cadence_type in CadenceType:
            progression = self.generator.generate_progression(cadence_type)
            for chord in progression:
                assert 1 <= chord.scale_degree <= 7

    def test_no_weak_progressions_used(self):
        """Test that weak progressions are avoided."""
        # Generate many progressions and check for weak progressions
        for cadence_type in CadenceType:
            for _ in range(10):
                progression = self.generator.generate_progression(cadence_type)
                degrees = [chord.scale_degree for chord in progression]

                # Check consecutive pairs
                for i in range(len(degrees) - 1):
                    pair = (degrees[i], degrees[i + 1])
                    # V → IV should be avoided (retrogression)
                    if pair == (5, 4):
                        pytest.fail(f"Found weak progression V→IV in {cadence_type}")


class TestIntegration:
    """Integration tests for the complete music theory system."""

    def test_complete_workflow(self):
        """Test complete workflow from generation to MIDI."""
        generator = ChordProgressionGenerator(4, 8)

        for cadence_type in CadenceType:
            # Generate progression
            progression = generator.generate_progression(cadence_type)

            # Convert to MIDI
            midi = generator.progression_to_midi(progression)

            # Convert to symbols
            symbols = generator.progression_to_symbols(progression)

            # Verify consistency
            assert len(progression) == len(midi) == len(symbols)

            # Verify MIDI notes are playable
            for chord_midi in midi:
                assert len(chord_midi) == 3
                assert all(36 <= note <= 84 for note in chord_midi)  # Piano range

    def test_cadence_pattern_integration(self):
        """Test that cadence patterns integrate correctly with generator."""
        generator = ChordProgressionGenerator(4, 8)

        for cadence_type in CadenceType:
            # Get expected cadence chords
            expected_pen, expected_final = CadencePattern.get_cadence_chords(cadence_type)

            # Generate progression
            progression = generator.generate_progression(cadence_type)

            # Verify cadence is correct
            assert progression[-2].scale_degree == expected_pen
            assert progression[-1].scale_degree == expected_final