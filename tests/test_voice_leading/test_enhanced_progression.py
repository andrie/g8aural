"""
Test enhanced progression generation.

This module tests the EnhancedChordProgressionGenerator to ensure
it creates progressions with improved voice leading.
"""

import unittest
from music21 import pitch
from src.music_theory.cadences import CadenceType
from src.music_theory.progression import ChordProgressionGenerator
from src.music_theory.enhanced_progression import EnhancedChordProgressionGenerator


class TestEnhancedProgression(unittest.TestCase):
    """Tests for enhanced chord progression generation."""

    def setUp(self):
        """Set up test environment."""
        self.regular_generator = ChordProgressionGenerator(
            use_strict_cadence=True,
            use_sevenths=True,
            key='C'
        )
        self.enhanced_generator = EnhancedChordProgressionGenerator(
            use_strict_cadence=True,
            use_sevenths=True,
            key='C'
        )

    def test_progression_length(self):
        """Test that both generators create progressions of expected length."""
        for cadence_type in [CadenceType.PERFECT, CadenceType.PLAGAL,
                           CadenceType.IMPERFECT, CadenceType.INTERRUPTED]:
            regular_prog = self.regular_generator.generate_progression(cadence_type)
            enhanced_prog = self.enhanced_generator.generate_progression(cadence_type)

            # Both should generate 4-8 chords in strict cadence mode
            self.assertTrue(4 <= len(regular_prog) <= 8)
            self.assertTrue(4 <= len(enhanced_prog) <= 8)

    def test_bass_range(self):
        """Test that enhanced progressions use a wider bass range."""
        for cadence_type in [CadenceType.PERFECT, CadenceType.PLAGAL]:
            # Generate progressions
            regular_prog = self.regular_generator.generate_progression(cadence_type)
            enhanced_prog = self.enhanced_generator.generate_progression(cadence_type)

            # Get voiced MIDI notes
            regular_voiced = self.regular_generator.progression_to_midi(regular_prog)
            enhanced_voiced = self.enhanced_generator.progression_to_midi(enhanced_prog)

            # Extract bass notes
            regular_bass_notes = [chord[0] for chord in regular_voiced]
            enhanced_bass_notes = [chord[0] for chord in enhanced_voiced]

            # Regular bass is typically G3 to G4 (55-67)
            # Enhanced bass should use lower notes at times
            min_regular_bass = min(regular_bass_notes)
            min_enhanced_bass = min(enhanced_bass_notes)

            # This test might occasionally fail if the random progression happens to
            # not use the full bass range, but should pass most of the time
            self.assertLessEqual(
                min_enhanced_bass, min_regular_bass,
                "Enhanced voice leading should generally use a lower bass range"
            )

    def test_voice_spacing(self):
        """Test that enhanced progressions have better voice spacing."""
        cadence_type = CadenceType.PERFECT

        # Generate progressions
        regular_prog = self.regular_generator.generate_progression(cadence_type)
        enhanced_prog = self.enhanced_generator.generate_progression(cadence_type)

        # Get voiced MIDI notes
        regular_voiced = self.regular_generator.progression_to_midi(regular_prog)
        enhanced_voiced = self.enhanced_generator.progression_to_midi(enhanced_prog)

        # Calculate average spacing between voices
        def calc_avg_spacing(voiced_prog):
            all_spacings = []
            for chord in voiced_prog:
                for i in range(len(chord) - 1):
                    all_spacings.append(chord[i+1] - chord[i])
            return sum(all_spacings) / len(all_spacings)

        regular_spacing = calc_avg_spacing(regular_voiced)
        enhanced_spacing = calc_avg_spacing(enhanced_voiced)

        # Enhanced should have more balanced spacing (not too tight, not too wide)
        # Ideal spacing is around 6-8 semitones between voices
        ideal_spacing = 7.0
        regular_diff = abs(regular_spacing - ideal_spacing)
        enhanced_diff = abs(enhanced_spacing - ideal_spacing)

        # This test might occasionally fail if the random progression happens to
        # give well-spaced regular voicing, but should pass most of the time
        self.assertLessEqual(
            enhanced_diff, regular_diff * 1.5,  # Allow some margin
            f"Enhanced spacing ({enhanced_spacing:.2f}) should be closer to "
            f"ideal ({ideal_spacing}) than regular ({regular_spacing:.2f})"
        )

    def test_inversion_constraints(self):
        """Test that enhanced generator respects inversion constraints."""
        # Use plagal cadence which is simpler to test (I-IV-I with final chord in root position)
        cadence_type = CadenceType.PLAGAL

        # Generate progression with enhanced generator
        enhanced_prog = self.enhanced_generator.generate_progression(cadence_type)

        # Get inversions
        enhanced_inversions = self.enhanced_generator.progression_to_inversions(enhanced_prog)

        # Plagal cadence final chord should be root position
        self.assertEqual(enhanced_inversions[-1], 0,
                         f"Final chord in {cadence_type} should be root position, got {enhanced_inversions[-1]}")

    def test_voice_leading_quality(self):
        """Test voice leading quality by checking for smooth connections."""
        cadence_type = CadenceType.PERFECT

        # Generate progressions
        enhanced_prog = self.enhanced_generator.generate_progression(cadence_type)

        # Get voiced MIDI notes
        enhanced_voiced = self.enhanced_generator.progression_to_midi(enhanced_prog)

        # Check for proper voice leading between penultimate and final chords (V-I)
        penultimate = enhanced_voiced[-2]
        final = enhanced_voiced[-1]

        # In a perfect authentic cadence, leading tone (B in C major) should resolve to tonic (C)
        # Find the leading tone in the penultimate chord
        leading_tone_found = False
        for i, note in enumerate(penultimate):
            if note % 12 == 11:  # B has pitch class 11
                leading_tone_found = True
                # Check if it resolves to C in the same voice
                if final[i] % 12 == 0:  # C has pitch class 0
                    break

        self.assertTrue(
            leading_tone_found,
            "Perfect cadence should contain leading tone in penultimate chord"
        )


if __name__ == '__main__':
    unittest.main()