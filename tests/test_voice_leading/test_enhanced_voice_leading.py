"""
Test enhanced voice leading functionality.

This module tests the enhanced voice leading implementation to ensure
it follows proper voice leading rules and creates musical progressions.
"""

import unittest
from music21 import roman, pitch, key
from lib.music_theory.voice_leading import VoiceLeader
from lib.music_theory.enhanced_voice_leading import EnhancedVoiceLeader


class TestEnhancedVoiceLeading(unittest.TestCase):
    """Tests for enhanced voice leading functionality."""

    def setUp(self):
        """Set up test environment."""
        self.regular_vl = VoiceLeader()
        self.enhanced_vl = EnhancedVoiceLeader()

    def test_voice_ranges(self):
        """Test that enhanced voice ranges are wider than regular."""
        # Check bass range specifically
        regular_bass_range = self.regular_vl.VOICE_RANGES['bass']
        enhanced_bass_range = self.enhanced_vl.VOICE_RANGES['bass']

        # Regular bass is G3 to G4 (55-67)
        # Enhanced bass should be lower: E2 to C4 (40-60)
        self.assertLess(
            enhanced_bass_range[0], regular_bass_range[0],
            "Enhanced bass range should extend lower than regular"
        )

        # Check soprano range
        regular_soprano_range = self.regular_vl.VOICE_RANGES['soprano']
        enhanced_soprano_range = self.enhanced_vl.VOICE_RANGES['soprano']

        # Regular soprano is G4 to G5 (67-79)
        # Enhanced soprano should be higher: C4 to A5 (60-81)
        self.assertGreaterEqual(
            enhanced_soprano_range[1], regular_soprano_range[1],
            "Enhanced soprano range should extend at least as high as regular"
        )

    def test_common_tone_retention(self):
        """Test that voice leading prefers common tone retention."""
        # Create two chords that share common tones
        chord1 = roman.RomanNumeral('I', 'C')  # C E G
        chord2 = roman.RomanNumeral('vi', 'C')  # A C E

        # Voice the progression with both voice leaders
        regular_voicing = self.regular_vl.voice_progression([chord1, chord2])
        enhanced_voicing = self.enhanced_vl.voice_progression([chord1, chord2])

        # Count common tones retained in each version
        regular_common_tones = sum(
            1 for a, b in zip(regular_voicing[0], regular_voicing[1]) if a == b
        )
        enhanced_common_tones = sum(
            1 for a, b in zip(enhanced_voicing[0], enhanced_voicing[1]) if a == b
        )

        # Enhanced should retain at least as many common tones as regular
        self.assertGreaterEqual(
            enhanced_common_tones, regular_common_tones,
            "Enhanced voice leading should retain at least as many common tones"
        )

    def test_contrary_motion_preference(self):
        """Test that the evaluate_transition method rewards contrary motion."""
        # Create test chord progression
        chord1 = roman.RomanNumeral('I', 'C')
        chord2 = roman.RomanNumeral('V', 'C')

        # Create example voicings with contrary motion
        voicing1 = [48, 60, 64, 67]  # C3 C4 E4 G4

        # One with contrary motion (bass down, soprano up)
        contrary_voicing = [43, 62, 67, 71]  # G2 D4 G4 B4

        # One with parallel motion (both up)
        parallel_voicing = [55, 62, 67, 74]  # G3 D4 G4 D5

        # Score both transitions using the enhanced voice leading evaluator
        contrary_score = self.enhanced_vl._evaluate_transition(voicing1, contrary_voicing, chord1, chord2)
        parallel_score = self.enhanced_vl._evaluate_transition(voicing1, parallel_voicing, chord1, chord2)

        # The contrary motion should get a better (lower) score
        # Lower score means better voice leading in the evaluation function
        self.assertLess(
            contrary_score, parallel_score,
            "Contrary motion should receive a better (lower) score than parallel motion"
        )

    def create_manual_cadential_64(self):
        """Create a manually controlled cadential 6/4 chord."""
        # Create a C major key context
        c_major = key.Key('C')

        # Create chord with explicit inversion number for cadential 6/4
        cadential = roman.RomanNumeral('I64', c_major)

        # Ensure the 6/4 is constructed correctly
        self.assertEqual(cadential.inversion(), 2, "Roman numeral I64 should create second inversion")

        return cadential

    def test_cadential_64_manual(self):
        """Test for manual creation and voicing of a cadential 6/4 chord."""
        # Create a manually controlled cadential 6/4 chord in C
        c_major = key.Key('C')

        # Create a progression with cadential 6/4 - V - I
        chord1 = roman.RomanNumeral('I64', c_major)  # Cadential 6/4
        chord2 = roman.RomanNumeral('V7', c_major)   # Dominant 7th
        chord3 = roman.RomanNumeral('I', c_major)    # Tonic

        # Voice with enhanced voice leading
        voicing = self.enhanced_vl.voice_progression([chord1, chord2, chord3])

        # The bass of a cadential 6/4 should be the dominant (G in C major)
        bass_midi = voicing[0][0]  # First chord, bass voice

        # Get the dominant pitch class in C major (G = 7)
        dominant_pc = c_major.pitchFromDegree(5).pitchClass

        # The bass pitch class should match the dominant
        bass_pc = bass_midi % 12

        self.assertEqual(
            bass_pc, dominant_pc,
            f"Bass of I64 should be dominant (pitch class {dominant_pc}), got {bass_pc}"
        )

    def test_stepwise_motion_preference(self):
        """Test that voice leading prefers stepwise motion where possible."""
        chord1 = roman.RomanNumeral('IV', 'C')  # F A C
        chord2 = roman.RomanNumeral('V', 'C')   # G B D

        # These chords should allow for stepwise motion in most voices
        enhanced_voicing = self.enhanced_vl.voice_progression([chord1, chord2])

        # Count stepwise motions (1 or 2 semitones)
        stepwise_count = 0
        for v1, v2 in zip(enhanced_voicing[0], enhanced_voicing[1]):
            step = abs(v2 - v1)
            if step == 1 or step == 2:
                stepwise_count += 1

        # At least 2 of the 4 voices should move by step
        self.assertGreaterEqual(
            stepwise_count, 2,
            f"Expected at least 2 stepwise motions, got {stepwise_count}"
        )


if __name__ == '__main__':
    unittest.main()