#!/usr/bin/env python3
"""
Test suite for unique pitch validation (duplicate pitch fix).

Validates that every generated chord has exactly 4 unique MIDI note numbers
with no duplicate pitches in the same octave.

Tests:
1. All 4 cadence types generate chords with 4 unique MIDI notes
2. No duplicate pitches in the same octave
3. Both triads and 7th chords have unique pitches
4. Multiple keys (major and minor) maintain uniqueness
5. Both hybrid and pure modes avoid duplicates
6. Large-scale validation (50-100 progressions)
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from modules.music_theory.progression import ChordProgressionGenerator
from modules.music_theory.cadences import CadenceType

try:
    import pytest
    HAS_PYTEST = True
except ImportError:
    HAS_PYTEST = False


class TestUniquePitches:
    """Test suite for unique pitch validation."""

    def test_all_chords_have_four_notes(self):
        """Test that every chord has exactly 4 notes (SATB)."""
        generator = ChordProgressionGenerator(
            use_voice_leading=True,
            use_sevenths=True,
            use_corpus=False,
            keys=['C'],
            use_strict_cadence=False
        )

        for cadence_type in CadenceType:
            prog = generator.generate_progression(cadence_type)
            midi = generator.progression_to_midi(prog)

            for i, chord_voicing in enumerate(midi):
                assert len(chord_voicing) == 4, \
                    f"{cadence_type.value}, chord {i+1}: Expected 4 notes, got {len(chord_voicing)}"

    def test_all_chords_have_unique_pitches(self):
        """Test that every chord has 4 unique MIDI note numbers (no duplicates)."""
        generator = ChordProgressionGenerator(
            use_voice_leading=True,
            use_sevenths=True,
            use_corpus=False,
            keys=['C'],
            use_strict_cadence=False
        )

        for cadence_type in CadenceType:
            prog = generator.generate_progression(cadence_type)
            midi = generator.progression_to_midi(prog)

            for i, chord_voicing in enumerate(midi):
                unique_notes = set(chord_voicing)
                assert len(unique_notes) == 4, \
                    f"{cadence_type.value}, chord {i+1}: Expected 4 unique notes, got {len(unique_notes)}. " \
                    f"Voicing: {chord_voicing}, Duplicates: {[n for n in chord_voicing if chord_voicing.count(n) > 1]}"

    def test_no_duplicate_pitches_in_same_octave(self):
        """Test that no two voices have the same MIDI note number."""
        generator = ChordProgressionGenerator(
            use_voice_leading=True,
            use_sevenths=True,
            use_corpus=False,
            keys=['C'],
            use_strict_cadence=False
        )

        for cadence_type in CadenceType:
            prog = generator.generate_progression(cadence_type)
            midi = generator.progression_to_midi(prog)

            for i, chord_voicing in enumerate(midi):
                # Check for duplicate MIDI numbers
                seen = set()
                duplicates = []
                for note in chord_voicing:
                    if note in seen:
                        duplicates.append(note)
                    seen.add(note)

                assert len(duplicates) == 0, \
                    f"{cadence_type.value}, chord {i+1}: Found duplicate MIDI notes: {duplicates}. " \
                    f"Full voicing: {chord_voicing}"

    def test_perfect_cadence_unique_pitches(self):
        """Test Perfect cadence (Ic-V-I) has unique pitches in all chords."""
        generator = ChordProgressionGenerator(
            use_voice_leading=True,
            use_sevenths=True,
            use_corpus=False,
            keys=['C'],
            use_strict_cadence=False
        )

        for _ in range(20):
            prog = generator.generate_progression(CadenceType.PERFECT)
            midi = generator.progression_to_midi(prog)

            for chord_voicing in midi:
                assert len(set(chord_voicing)) == 4, \
                    f"Perfect cadence has duplicate pitches: {chord_voicing}"

    def test_plagal_cadence_unique_pitches(self):
        """Test Plagal cadence (I-IV-I) has unique pitches in all chords."""
        generator = ChordProgressionGenerator(
            use_voice_leading=True,
            use_sevenths=True,
            use_corpus=False,
            keys=['C'],
            use_strict_cadence=False
        )

        for _ in range(20):
            prog = generator.generate_progression(CadenceType.PLAGAL)
            midi = generator.progression_to_midi(prog)

            for chord_voicing in midi:
                assert len(set(chord_voicing)) == 4, \
                    f"Plagal cadence has duplicate pitches: {chord_voicing}"

    def test_imperfect_cadence_unique_pitches(self):
        """Test Imperfect cadence (I-IV-V) has unique pitches in all chords."""
        generator = ChordProgressionGenerator(
            use_voice_leading=True,
            use_sevenths=True,
            use_corpus=False,
            keys=['C'],
            use_strict_cadence=False
        )

        for _ in range(20):
            prog = generator.generate_progression(CadenceType.IMPERFECT)
            midi = generator.progression_to_midi(prog)

            for chord_voicing in midi:
                assert len(set(chord_voicing)) == 4, \
                    f"Imperfect cadence has duplicate pitches: {chord_voicing}"

    def test_interrupted_cadence_unique_pitches(self):
        """Test Interrupted cadence (I-V7-vi) has unique pitches in all chords."""
        generator = ChordProgressionGenerator(
            use_voice_leading=True,
            use_sevenths=True,
            use_corpus=False,
            keys=['C'],
            use_strict_cadence=False
        )

        for _ in range(20):
            prog = generator.generate_progression(CadenceType.INTERRUPTED)
            midi = generator.progression_to_midi(prog)

            for chord_voicing in midi:
                assert len(set(chord_voicing)) == 4, \
                    f"Interrupted cadence has duplicate pitches: {chord_voicing}"

    def test_triads_have_unique_pitches(self):
        """Test triads (without sevenths) have unique pitches."""
        generator = ChordProgressionGenerator(
            use_voice_leading=True,
            use_sevenths=False,  # Triads only
            use_corpus=False,
            keys=['C'],
            use_strict_cadence=False
        )

        for cadence_type in CadenceType:
            prog = generator.generate_progression(cadence_type)
            midi = generator.progression_to_midi(prog)

            for i, chord_voicing in enumerate(midi):
                assert len(set(chord_voicing)) == 4, \
                    f"{cadence_type.value} (triad), chord {i+1}: Has duplicate pitches: {chord_voicing}"

    def test_seventh_chords_have_unique_pitches(self):
        """Test seventh chords have unique pitches (4 unique pitch classes)."""
        generator = ChordProgressionGenerator(
            use_voice_leading=True,
            use_sevenths=True,  # Allow seventh chords
            use_corpus=False,
            keys=['C'],
            use_strict_cadence=False
        )

        # Test cadences that use seventh chords
        for _ in range(10):
            prog = generator.generate_progression(CadenceType.INTERRUPTED)  # Uses V7
            midi = generator.progression_to_midi(prog)

            # Check the V7 chord (usually second chord)
            for i, (chord, voicing) in enumerate(zip(prog, midi)):
                if len(chord.pitches) == 4:  # This is a seventh chord
                    assert len(set(voicing)) == 4, \
                        f"Seventh chord at position {i+1} has duplicate pitches: {voicing}"

                    # Also verify all 4 pitch classes are present
                    pitch_classes = [note % 12 for note in voicing]
                    assert len(set(pitch_classes)) == 4, \
                        f"Seventh chord should have 4 unique pitch classes, got {len(set(pitch_classes))}: {pitch_classes}"

    def test_major_keys_unique_pitches(self):
        """Test multiple major keys maintain unique pitches."""
        for key in ['C', 'G', 'D', 'F', 'Bb', 'A', 'E']:
            generator = ChordProgressionGenerator(
                use_voice_leading=True,
                use_sevenths=True,
                use_corpus=False,
                keys=[key],
                use_strict_cadence=False
            )

            prog = generator.generate_progression(CadenceType.PERFECT)
            midi = generator.progression_to_midi(prog)

            for i, chord_voicing in enumerate(midi):
                assert len(set(chord_voicing)) == 4, \
                    f"Key {key}, chord {i+1}: Has duplicate pitches: {chord_voicing}"

    def test_minor_keys_unique_pitches(self):
        """Test multiple minor keys maintain unique pitches."""
        for key in ['a', 'e', 'd', 'g', 'c', 'b']:
            generator = ChordProgressionGenerator(
                use_voice_leading=True,
                use_sevenths=True,
                use_corpus=False,
                keys=[key],
                use_strict_cadence=False
            )

            prog = generator.generate_progression(CadenceType.PERFECT)
            midi = generator.progression_to_midi(prog)

            for i, chord_voicing in enumerate(midi):
                assert len(set(chord_voicing)) == 4, \
                    f"Key {key}, chord {i+1}: Has duplicate pitches: {chord_voicing}"

    def test_hybrid_mode_unique_pitches(self):
        """Test hybrid mode (Grade 8, 4-8 chords) maintains unique pitches."""
        generator = ChordProgressionGenerator(
            min_length=4,
            max_length=8,
            use_voice_leading=True,
            use_sevenths=True,
            use_corpus=True,
            keys=['C'],
            use_strict_cadence=True  # Hybrid mode
        )

        for cadence_type in CadenceType:
            for _ in range(10):
                prog = generator.generate_progression(cadence_type)
                midi = generator.progression_to_midi(prog)

                for i, chord_voicing in enumerate(midi):
                    assert len(set(chord_voicing)) == 4, \
                        f"Hybrid mode, {cadence_type.value}, chord {i+1}: Has duplicate pitches: {chord_voicing}"

    def test_pure_mode_unique_pitches(self):
        """Test pure 3-chord mode (Grades 6-7) maintains unique pitches."""
        generator = ChordProgressionGenerator(
            min_length=3,
            max_length=3,
            use_voice_leading=True,
            use_sevenths=True,
            use_corpus=False,
            keys=['C'],
            use_strict_cadence=False  # Pure mode
        )

        for cadence_type in CadenceType:
            for _ in range(10):
                prog = generator.generate_progression(cadence_type)
                midi = generator.progression_to_midi(prog)

                assert len(midi) == 3, "Pure mode should generate 3 chords"

                for i, chord_voicing in enumerate(midi):
                    assert len(set(chord_voicing)) == 4, \
                        f"Pure mode, {cadence_type.value}, chord {i+1}: Has duplicate pitches: {chord_voicing}"

    def test_large_scale_validation_50_progressions(self):
        """Large-scale test: generate 50 progressions and verify all have unique pitches."""
        generator = ChordProgressionGenerator(
            use_voice_leading=True,
            use_sevenths=True,
            use_corpus=False,
            keys=['C'],
            use_strict_cadence=False
        )

        total_chords = 0
        total_progressions = 0

        for _ in range(50):
            for cadence_type in CadenceType:
                prog = generator.generate_progression(cadence_type)
                midi = generator.progression_to_midi(prog)
                total_progressions += 1

                for chord_voicing in midi:
                    total_chords += 1
                    assert len(set(chord_voicing)) == 4, \
                        f"Progression {total_progressions}, found duplicate pitches: {chord_voicing}"

        print(f"\n✓ Validated {total_chords} chords across {total_progressions} progressions")

    def test_large_scale_validation_100_hybrid_progressions(self):
        """Large-scale test: generate 100 hybrid mode progressions and verify unique pitches."""
        generator = ChordProgressionGenerator(
            min_length=4,
            max_length=8,
            use_voice_leading=True,
            use_sevenths=True,
            use_corpus=True,
            keys=['C', 'G', 'D', 'a', 'e'],
            use_strict_cadence=True  # Hybrid mode
        )

        total_chords = 0
        total_progressions = 0

        for _ in range(25):
            for cadence_type in CadenceType:
                prog = generator.generate_progression(cadence_type)
                midi = generator.progression_to_midi(prog)
                total_progressions += 1

                for i, chord_voicing in enumerate(midi):
                    total_chords += 1
                    assert len(set(chord_voicing)) == 4, \
                        f"Hybrid progression {total_progressions}, chord {i+1}: " \
                        f"Has duplicate pitches: {chord_voicing}"

        print(f"\n✓ Validated {total_chords} chords across {total_progressions} hybrid progressions")

    def test_voice_ranges_no_duplicates(self):
        """Test that voice ranges don't cause duplicate pitches."""
        generator = ChordProgressionGenerator(
            use_voice_leading=True,
            use_sevenths=True,
            use_corpus=False,
            keys=['C'],
            use_strict_cadence=False
        )

        prog = generator.generate_progression(CadenceType.PERFECT)
        midi = generator.progression_to_midi(prog)

        for chord_voicing in midi:
            # Check SATB ordering (bass < tenor < alto < soprano)
            assert chord_voicing[0] < chord_voicing[1] < chord_voicing[2] < chord_voicing[3], \
                f"Voice ordering violated: {chord_voicing}"

            # Check no duplicates
            assert len(set(chord_voicing)) == 4, \
                f"Voice ranges caused duplicate pitches: {chord_voicing}"

    def test_all_inversions_have_unique_pitches(self):
        """Test that all inversions (root, first, second, third) have unique pitches."""
        generator = ChordProgressionGenerator(
            use_voice_leading=True,
            use_sevenths=True,
            use_corpus=False,
            keys=['C'],
            use_strict_cadence=False
        )

        # Generate multiple progressions to cover different inversions
        inversions_found = set()

        for _ in range(50):
            for cadence_type in CadenceType:
                prog = generator.generate_progression(cadence_type)
                midi = generator.progression_to_midi(prog)
                inversions = generator.progression_to_inversions(prog, midi)

                for inv, voicing in zip(inversions, midi):
                    inversions_found.add(inv)

                    # Verify unique pitches regardless of inversion
                    assert len(set(voicing)) == 4, \
                        f"Inversion {inv} has duplicate pitches: {voicing}"

        print(f"\n✓ Tested inversions: {sorted(inversions_found)}")

    def test_edge_case_voice_leading_transitions(self):
        """Test that voice leading transitions don't create duplicate pitches."""
        generator = ChordProgressionGenerator(
            min_length=6,
            max_length=8,
            use_voice_leading=True,
            use_sevenths=True,
            use_corpus=True,
            keys=['C'],
            use_strict_cadence=True
        )

        # Test multiple progressions with various voice leading scenarios
        for _ in range(20):
            prog = generator.generate_progression(CadenceType.PERFECT)
            midi = generator.progression_to_midi(prog)

            # Check each chord
            for i, chord_voicing in enumerate(midi):
                assert len(set(chord_voicing)) == 4, \
                    f"Voice leading transition created duplicate at chord {i+1}: {chord_voicing}"

            # Check transitions
            for i in range(len(midi) - 1):
                voicing1 = midi[i]
                voicing2 = midi[i + 1]

                assert len(set(voicing1)) == 4, f"Chord {i+1} before transition has duplicates"
                assert len(set(voicing2)) == 4, f"Chord {i+2} after transition has duplicates"


def test_comprehensive_unique_pitches():
    """Comprehensive integration test for unique pitches across all scenarios."""
    test_cases = [
        # (use_sevenths, use_corpus, use_strict_cadence, keys, description)
        (True, False, False, ['C'], "Pure 3-chord with sevenths"),
        (False, False, False, ['C'], "Pure 3-chord triads only"),
        (True, True, True, ['C'], "Hybrid mode with corpus"),
        (True, False, True, ['C'], "Hybrid mode without corpus"),
        (True, True, False, ['C', 'G'], "Multi-key pure mode"),
        (True, True, True, ['C', 'a'], "Hybrid mode major/minor mix"),
    ]

    for use_sevenths, use_corpus, use_strict_cadence, keys, description in test_cases:
        print(f"\nTesting: {description}")

        generator = ChordProgressionGenerator(
            min_length=4 if use_strict_cadence else 3,
            max_length=8 if use_strict_cadence else 3,
            use_voice_leading=True,
            use_sevenths=use_sevenths,
            use_corpus=use_corpus,
            keys=keys,
            use_strict_cadence=use_strict_cadence
        )

        for cadence_type in CadenceType:
            prog = generator.generate_progression(cadence_type)
            midi = generator.progression_to_midi(prog)

            for i, chord_voicing in enumerate(midi):
                assert len(set(chord_voicing)) == 4, \
                    f"{description}, {cadence_type.value}, chord {i+1}: Duplicate pitches: {chord_voicing}"

        print(f"  ✓ Passed")


def run_all_tests():
    """Run all tests manually if pytest is not available."""
    test_class = TestUniquePitches()

    tests = [
        ('test_all_chords_have_four_notes', test_class.test_all_chords_have_four_notes),
        ('test_all_chords_have_unique_pitches', test_class.test_all_chords_have_unique_pitches),
        ('test_no_duplicate_pitches_in_same_octave', test_class.test_no_duplicate_pitches_in_same_octave),
        ('test_perfect_cadence_unique_pitches', test_class.test_perfect_cadence_unique_pitches),
        ('test_plagal_cadence_unique_pitches', test_class.test_plagal_cadence_unique_pitches),
        ('test_imperfect_cadence_unique_pitches', test_class.test_imperfect_cadence_unique_pitches),
        ('test_interrupted_cadence_unique_pitches', test_class.test_interrupted_cadence_unique_pitches),
        ('test_triads_have_unique_pitches', test_class.test_triads_have_unique_pitches),
        ('test_seventh_chords_have_unique_pitches', test_class.test_seventh_chords_have_unique_pitches),
        ('test_major_keys_unique_pitches', test_class.test_major_keys_unique_pitches),
        ('test_minor_keys_unique_pitches', test_class.test_minor_keys_unique_pitches),
        ('test_hybrid_mode_unique_pitches', test_class.test_hybrid_mode_unique_pitches),
        ('test_pure_mode_unique_pitches', test_class.test_pure_mode_unique_pitches),
        ('test_large_scale_validation_50_progressions', test_class.test_large_scale_validation_50_progressions),
        ('test_large_scale_validation_100_hybrid_progressions', test_class.test_large_scale_validation_100_hybrid_progressions),
        ('test_voice_ranges_no_duplicates', test_class.test_voice_ranges_no_duplicates),
        ('test_all_inversions_have_unique_pitches', test_class.test_all_inversions_have_unique_pitches),
        ('test_edge_case_voice_leading_transitions', test_class.test_edge_case_voice_leading_transitions),
    ]

    # Add the standalone test
    tests.append(('test_comprehensive_unique_pitches', test_comprehensive_unique_pitches))

    passed = 0
    failed = 0

    print("=" * 70)
    print("UNIQUE PITCHES TEST SUITE")
    print("=" * 70)

    for test_name, test_func in tests:
        try:
            print(f"\nRunning {test_name}...", end=" ")
            test_func()
            print("✓ PASSED")
            passed += 1
        except AssertionError as e:
            print(f"✗ FAILED")
            print(f"  Error: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ ERROR")
            print(f"  Exception: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print("\n" + "=" * 70)
    print(f"RESULTS: {passed} passed, {failed} failed out of {len(tests)} tests")
    print("=" * 70)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    if HAS_PYTEST:
        # Run tests with pytest
        pytest.main([__file__, "-v", "--tb=short"])
    else:
        # Run tests manually
        sys.exit(run_all_tests())
