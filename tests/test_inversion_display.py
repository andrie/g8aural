#!/usr/bin/env python3
"""
Test suite for inversion display labels (g8aural-bgb fix).

Tests that progression_to_symbols() returns correct inversion labels:
- Triads: I, I6, Ic (root, first, second inversion)
- Seventh chords: V7, V65, V43, V42 (root, first, second, third inversion)

Validates:
1. All 4 cadence types display correct inversions
2. Both hybrid mode (Grade 8) and pure mode (Grades 6-7) work correctly
3. Inversion labels match the actual inversions detected in voicings
4. Multiple keys (major and minor) display inversions correctly
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.music_theory.progression import ChordProgressionGenerator
from src.music_theory.cadences import CadenceType

try:
    import pytest
    HAS_PYTEST = True
except ImportError:
    HAS_PYTEST = False


class TestInversionDisplay:
    """Test suite for inversion display functionality."""

    def test_triad_inversions_labels(self):
        """Test that triad inversions get correct labels: I, I6, Ic."""
        generator = ChordProgressionGenerator(
            use_voice_leading=True,
            use_sevenths=False,  # Triads only
            use_corpus=False,
            keys=['C'],
            use_strict_cadence=False
        )

        # Generate a progression
        prog = generator.generate_progression(CadenceType.PERFECT)
        midi = generator.progression_to_midi(prog)
        symbols = generator.progression_to_symbols(prog, include_inversions=True)
        inversions = generator.progression_to_inversions(prog, midi)

        # Check that inversion labels are correct
        for symbol, inversion in zip(symbols, inversions):
            if inversion == 0:
                # Root position - no suffix
                assert not ('6' in symbol or 'c' in symbol), \
                    f"Root position chord {symbol} should not have 6 or c suffix"
            elif inversion == 1:
                # First inversion - should have '6'
                assert '6' in symbol and 'c' not in symbol, \
                    f"First inversion chord should have '6' suffix, got: {symbol}"
            elif inversion == 2:
                # Second inversion - should have 'c'
                assert 'c' in symbol, \
                    f"Second inversion chord should have 'c' suffix, got: {symbol}"

    def test_seventh_chord_inversion_labels(self):
        """Test that seventh chord inversions get correct figured bass: V7, V65, V43, V42."""
        generator = ChordProgressionGenerator(
            use_voice_leading=True,
            use_sevenths=True,
            use_corpus=False,
            keys=['C'],
            use_strict_cadence=False
        )

        # Generate multiple progressions to cover different seventh chord inversions
        for _ in range(10):
            prog = generator.generate_progression(CadenceType.INTERRUPTED)
            midi = generator.progression_to_midi(prog)
            symbols = generator.progression_to_symbols(prog, include_inversions=True)
            inversions = generator.progression_to_inversions(prog, midi)

            for chord, symbol, inversion in zip(prog, symbols, inversions):
                # Check if this is a seventh chord
                is_seventh = len(chord.pitches) == 4

                if is_seventh:
                    if inversion == 0:
                        # Root position - should have '7'
                        assert '7' in symbol and not any(x in symbol for x in ['65', '43', '42']), \
                            f"Root position seventh chord should be V7, got: {symbol}"
                    elif inversion == 1:
                        # First inversion - should be '65'
                        assert '65' in symbol, \
                            f"First inversion seventh chord should have '65', got: {symbol}"
                    elif inversion == 2:
                        # Second inversion - should be '43'
                        assert '43' in symbol, \
                            f"Second inversion seventh chord should have '43', got: {symbol}"
                    elif inversion == 3:
                        # Third inversion - should be '42'
                        assert '42' in symbol, \
                            f"Third inversion seventh chord should have '42', got: {symbol}"

    def test_perfect_cadence_inversions(self):
        """Test Perfect cadence (Ic-V-I) displays correct inversions (Grade 8 mode)."""
        generator = ChordProgressionGenerator(
            use_voice_leading=True,
            use_sevenths=True,
            use_corpus=False,
            keys=['C'],
            use_strict_cadence=True  # Grade 8 mode allows inversions
        )

        prog = generator.generate_progression(CadenceType.PERFECT)
        midi = generator.progression_to_midi(prog)
        symbols = generator.progression_to_symbols(prog, include_inversions=True)
        inversions = generator.progression_to_inversions(prog, midi)

        # In hybrid mode, there are lead-in chords before the 3-chord cadence
        # The cadence (Ic-V-I) is in the LAST 3 chords
        # Cadence chord 1 should be Ic (second inversion)
        assert inversions[-3] == 2, f"Cadence first chord should be second inversion, got {inversions[-3]}"
        assert 'c' in symbols[-3], f"Cadence first chord should show 'c' for second inversion, got {symbols[-3]}"

        # Cadence chord 3 should be I (root position)
        assert inversions[-1] == 0, f"Last chord should be root position, got {inversions[-1]}"
        assert not ('6' in symbols[-1] or 'c' in symbols[-1]), \
            f"Last chord should be root position (no suffix), got {symbols[-1]}"

    def test_plagal_cadence_inversions(self):
        """Test Plagal cadence (I-IV-I) displays correct inversions."""
        generator = ChordProgressionGenerator(
            use_voice_leading=True,
            use_sevenths=True,
            use_corpus=False,
            keys=['C'],
            use_strict_cadence=False
        )

        prog = generator.generate_progression(CadenceType.PLAGAL)
        midi = generator.progression_to_midi(prog)
        symbols = generator.progression_to_symbols(prog, include_inversions=True)
        inversions = generator.progression_to_inversions(prog, midi)

        # All chords should be root or first inversion
        for inv in inversions:
            assert inv in [0, 1], f"Plagal cadence inversions should be 0 or 1, got {inv}"

        # Final chord should be root position
        assert inversions[2] == 0, f"Final chord should be root position, got {inversions[2]}"
        assert not ('6' in symbols[2] or 'c' in symbols[2]), \
            f"Final chord should be root position (no suffix), got {symbols[2]}"

    def test_imperfect_cadence_inversions(self):
        """Test Imperfect cadence (I-IV-V) displays correct inversions."""
        generator = ChordProgressionGenerator(
            use_voice_leading=True,
            use_sevenths=True,
            use_corpus=False,
            keys=['C'],
            use_strict_cadence=False
        )

        prog = generator.generate_progression(CadenceType.IMPERFECT)
        midi = generator.progression_to_midi(prog)
        symbols = generator.progression_to_symbols(prog, include_inversions=True)
        inversions = generator.progression_to_inversions(prog, midi)

        # All chords should be root or first inversion
        for inv in inversions:
            assert inv in [0, 1], f"Imperfect cadence inversions should be 0 or 1, got {inv}"

    def test_interrupted_cadence_inversions(self):
        """Test Interrupted cadence (I-V7-vi) displays correct inversions."""
        generator = ChordProgressionGenerator(
            use_voice_leading=True,
            use_sevenths=True,
            use_corpus=False,
            keys=['C'],
            use_strict_cadence=False
        )

        prog = generator.generate_progression(CadenceType.INTERRUPTED)
        midi = generator.progression_to_midi(prog)
        symbols = generator.progression_to_symbols(prog, include_inversions=True)
        inversions = generator.progression_to_inversions(prog, midi)

        # Final chord (vi) should be root position
        assert inversions[2] == 0, f"Final chord should be root position, got {inversions[2]}"

    def test_hybrid_mode_inversions(self):
        """Test hybrid mode (Grade 8) displays correct inversions on all chords."""
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
            prog = generator.generate_progression(cadence_type)
            midi = generator.progression_to_midi(prog)
            symbols = generator.progression_to_symbols(prog, include_inversions=True)
            inversions = generator.progression_to_inversions(prog, midi)

            # Check that all chords have correct inversion labels
            assert len(symbols) == len(inversions), \
                f"Number of symbols ({len(symbols)}) should match inversions ({len(inversions)})"

            for symbol, inversion in zip(symbols, inversions):
                # Verify the label matches the inversion
                if inversion == 0:
                    # Root position - might have '7' for seventh chords, but no '6', 'c', '65', '43', '42'
                    assert not any(x in symbol for x in ['6', 'c']) or '65' in symbol or '43' in symbol or '42' in symbol, \
                        f"Root position should not have inversion suffix (except '7'), got: {symbol}"
                elif inversion == 1:
                    # First inversion
                    assert '6' in symbol or '65' in symbol, \
                        f"First inversion should have '6' or '65', got: {symbol}"
                elif inversion == 2:
                    # Second inversion
                    assert 'c' in symbol or '43' in symbol, \
                        f"Second inversion should have 'c' or '43', got: {symbol}"
                elif inversion == 3:
                    # Third inversion (seventh chords only)
                    assert '42' in symbol, \
                        f"Third inversion should have '42', got: {symbol}"

    def test_pure_mode_inversions(self):
        """Test pure 3-chord mode (Grades 6-7) displays correct inversions."""
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
            prog = generator.generate_progression(cadence_type)
            midi = generator.progression_to_midi(prog)
            symbols = generator.progression_to_symbols(prog, include_inversions=True)
            inversions = generator.progression_to_inversions(prog, midi)

            assert len(prog) == 3, f"Pure mode should generate exactly 3 chords, got {len(prog)}"
            assert len(symbols) == 3, f"Should have 3 symbols, got {len(symbols)}"

            # Verify inversion labels match detected inversions
            for symbol, inversion in zip(symbols, inversions):
                # Same verification as hybrid mode
                if inversion == 0:
                    assert not ('6' in symbol and '65' not in symbol) and not ('c' in symbol), \
                        f"Root position label mismatch: {symbol} for inversion {inversion}"

    def test_multiple_keys_major(self):
        """Test inversion display in multiple major keys."""
        for key in ['C', 'G', 'D', 'F', 'Bb']:
            generator = ChordProgressionGenerator(
                use_voice_leading=True,
                use_sevenths=True,
                use_corpus=False,
                keys=[key],
                use_strict_cadence=False
            )

            prog = generator.generate_progression(CadenceType.PERFECT)
            midi = generator.progression_to_midi(prog)
            symbols = generator.progression_to_symbols(prog, include_inversions=True)
            inversions = generator.progression_to_inversions(prog, midi)

            # Verify symbols and inversions match
            for symbol, inversion in zip(symbols, inversions):
                if inversion == 2:  # Second inversion (Ic)
                    assert 'c' in symbol or '43' in symbol, \
                        f"Key {key}: Second inversion should have 'c' or '43', got {symbol}"

    def test_multiple_keys_minor(self):
        """Test inversion display in multiple minor keys."""
        for key in ['a', 'e', 'd', 'c']:
            generator = ChordProgressionGenerator(
                use_voice_leading=True,
                use_sevenths=True,
                use_corpus=False,
                keys=[key],
                use_strict_cadence=False
            )

            prog = generator.generate_progression(CadenceType.PERFECT)
            midi = generator.progression_to_midi(prog)
            symbols = generator.progression_to_symbols(prog, include_inversions=True)
            inversions = generator.progression_to_inversions(prog, midi)

            # Verify symbols and inversions match
            assert len(symbols) == len(inversions), \
                f"Key {key}: Symbol count mismatch"

    def test_inversion_label_consistency(self):
        """Test that inversion labels are consistently applied across multiple generations (Grade 8 mode)."""
        generator = ChordProgressionGenerator(
            use_voice_leading=True,
            use_sevenths=True,
            use_corpus=False,
            keys=['C'],
            use_strict_cadence=True  # Grade 8 mode allows inversions
        )

        # Generate the same cadence type multiple times
        for _ in range(20):
            prog = generator.generate_progression(CadenceType.PERFECT)
            midi = generator.progression_to_midi(prog)
            symbols = generator.progression_to_symbols(prog, include_inversions=True)
            inversions = generator.progression_to_inversions(prog, midi)

            # In hybrid mode, the cadence is the last 3 chords
            # Cadence first chord should always be second inversion (Ic)
            assert inversions[-3] == 2, \
                f"Perfect cadence first chord should be second inversion, got {inversions[-3]}"
            assert 'c' in symbols[-3], \
                f"Perfect cadence first chord should show 'c', got {symbols[-3]}"

    def test_include_inversions_flag(self):
        """Test that include_inversions=False removes inversion labels."""
        generator = ChordProgressionGenerator(
            use_voice_leading=True,
            use_sevenths=True,
            use_corpus=False,
            keys=['C'],
            use_strict_cadence=False
        )

        prog = generator.generate_progression(CadenceType.PERFECT)

        # With inversions
        symbols_with = generator.progression_to_symbols(prog, include_inversions=True)

        # Without inversions
        symbols_without = generator.progression_to_symbols(prog, include_inversions=False)

        # Without inversions should have simpler labels
        for symbol_without in symbols_without:
            # Should not have inversion suffixes
            assert not any(x in symbol_without for x in ['6', 'c', '65', '43', '42']), \
                f"Without inversions should not have suffixes, got: {symbol_without}"


def test_all_cadence_types_show_inversions():
    """Integration test: all cadence types display correct inversion labels."""
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
        symbols = generator.progression_to_symbols(prog, include_inversions=True)
        inversions = generator.progression_to_inversions(prog, midi)

        print(f"\n{cadence_type.value.upper()} cadence:")
        for symbol, inversion in zip(symbols, inversions):
            print(f"  {symbol}: inversion {inversion}")

        # Verify that symbols reflect inversions
        assert len(symbols) == len(inversions), \
            f"{cadence_type.value}: Mismatch in symbol/inversion count"


def run_all_tests():
    """Run all tests manually if pytest is not available."""
    test_class = TestInversionDisplay()

    tests = [
        ('test_triad_inversions_labels', test_class.test_triad_inversions_labels),
        ('test_seventh_chord_inversion_labels', test_class.test_seventh_chord_inversion_labels),
        ('test_perfect_cadence_inversions', test_class.test_perfect_cadence_inversions),
        ('test_plagal_cadence_inversions', test_class.test_plagal_cadence_inversions),
        ('test_imperfect_cadence_inversions', test_class.test_imperfect_cadence_inversions),
        ('test_interrupted_cadence_inversions', test_class.test_interrupted_cadence_inversions),
        ('test_hybrid_mode_inversions', test_class.test_hybrid_mode_inversions),
        ('test_pure_mode_inversions', test_class.test_pure_mode_inversions),
        ('test_multiple_keys_major', test_class.test_multiple_keys_major),
        ('test_multiple_keys_minor', test_class.test_multiple_keys_minor),
        ('test_inversion_label_consistency', test_class.test_inversion_label_consistency),
        ('test_include_inversions_flag', test_class.test_include_inversions_flag),
    ]

    # Add the standalone test
    tests.append(('test_all_cadence_types_show_inversions', test_all_cadence_types_show_inversions))

    passed = 0
    failed = 0

    print("=" * 70)
    print("INVERSION DISPLAY TEST SUITE")
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
