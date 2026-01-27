#!/usr/bin/env python3
"""
Test script for 3-chord cadence generation with inversion constraints.

Tests all four cadence types (Perfect, Plagal, Imperfect, Interrupted) to ensure:
1. Progressions are exactly 3 chords
2. Inversion constraints are satisfied
3. Voice leading produces valid 4-voice SATB
"""

import sys
import os
# Add parent directory to path so we can import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.music_theory.progression import ChordProgressionGenerator
from src.music_theory.cadences import CadenceType

try:
    import pytest
    HAS_PYTEST = True
except ImportError:
    HAS_PYTEST = False


class TestProgressionGeneration:
    """Test suite for 3-chord cadence generation with inversion constraints."""

    @classmethod
    def setup_class(cls):
        """Create generator instance for all tests."""
        cls.generator = ChordProgressionGenerator(
            min_length=3,
            max_length=3,
            use_voice_leading=True,
            use_sevenths=True,
            use_corpus=False,  # Disable corpus for predictable testing
            keys=['C'],
            use_strict_cadence=False  # Pure 3-chord mode
        )

    def _validate_cadence(self, cadence_type: CadenceType, verbose: bool = False):
        """
        Validate a specific cadence type.

        Args:
            cadence_type: The cadence type to test
            verbose: If True, print detailed output (useful for standalone execution)

        Raises:
            AssertionError: If validation fails
        """
        if verbose:
            print(f"\n{'='*60}")
            print(f"Testing {cadence_type.value.upper()} cadence")
            print(f"{'='*60}")

        # Generate progression
        prog = self.generator.generate_progression(cadence_type)

        # Get symbols and MIDI
        symbols = self.generator.progression_to_symbols(prog)
        midi = self.generator.progression_to_midi(prog)
        inversions = self.generator.progression_to_inversions(prog, midi)
        note_names = self.generator.progression_to_note_names(prog)

        # Get expected constraints
        constraints = self.generator._generate_inversion_constraints(cadence_type)

        if verbose:
            # Display results
            print(f"\nProgression length: {len(prog)}")
            print(f"Chord symbols: {' → '.join(symbols)}")
            print(f"\nDetailed chord information:")

            for i, (symbol, voicing, inversion, names, expected_inversions) in enumerate(
                zip(symbols, midi, inversions, note_names, constraints)
            ):
                status = "✓" if inversion in expected_inversions else "✗"
                print(f"  Chord {i+1}: {symbol:6s} | Inversion: {inversion} | Expected: {expected_inversions} {status}")
                print(f"           MIDI: {voicing}")
                print(f"           Notes: {names}")

        # Validation with assertions
        assert len(prog) == 3, f"Expected 3 chords, got {len(prog)}"

        if verbose:
            print(f"\nValidation:")
            print(f"  - Length is 3: ✓")

        assert all(len(v) == 4 for v in midi), "All chords must have 4 voices"

        if verbose:
            print(f"  - All chords have 4 voices: ✓")

        constraints_satisfied = all(
            inv in expected for inv, expected in zip(inversions, constraints)
        )

        if not constraints_satisfied:
            # Build detailed error message
            violations = []
            for i, (inv, expected) in enumerate(zip(inversions, constraints)):
                if inv not in expected:
                    violations.append(f"Chord {i+1}: got inversion {inv}, expected one of {expected}")
            error_msg = f"Inversion constraints not satisfied:\n  " + "\n  ".join(violations)
            assert False, error_msg

        if verbose:
            print(f"  - Inversion constraints satisfied: ✓")
            print(f"\n✓ {cadence_type.value.upper()} cadence test PASSED")

    def test_perfect_cadence(self):
        """Test Perfect cadence (Ic → V → I) with inversion constraints."""
        self._validate_cadence(CadenceType.PERFECT)

    def test_plagal_cadence(self):
        """Test Plagal cadence (I → IV → I) with inversion constraints."""
        self._validate_cadence(CadenceType.PLAGAL)

    def test_imperfect_cadence(self):
        """Test Imperfect cadence (I → IV → V) with inversion constraints."""
        self._validate_cadence(CadenceType.IMPERFECT)

    def test_interrupted_cadence(self):
        """Test Interrupted cadence (I → V7 → vi) with inversion constraints."""
        self._validate_cadence(CadenceType.INTERRUPTED)

    def test_all_cadences_integration(self):
        """Integration test: all cadence types work correctly."""
        for cadence_type in CadenceType:
            self._validate_cadence(cadence_type)


def run_all_tests():
    """Run all tests manually if pytest is not available."""
    print("="*60)
    print("3-Chord Cadence Generator Test Suite")
    print("="*60)

    test_class = TestProgressionGeneration()
    test_class.setup_class()

    tests = [
        ('test_perfect_cadence', test_class.test_perfect_cadence, CadenceType.PERFECT),
        ('test_plagal_cadence', test_class.test_plagal_cadence, CadenceType.PLAGAL),
        ('test_imperfect_cadence', test_class.test_imperfect_cadence, CadenceType.IMPERFECT),
        ('test_interrupted_cadence', test_class.test_interrupted_cadence, CadenceType.INTERRUPTED),
    ]

    passed = 0
    failed = 0

    for test_name, test_func, cadence_type in tests:
        try:
            # Run with verbose output for standalone mode
            test_class._validate_cadence(cadence_type, verbose=True)
            passed += 1
        except AssertionError as e:
            print(f"\n✗ {cadence_type.value.upper()} cadence test FAILED")
            print(f"  Error: {e}")
            failed += 1
        except Exception as e:
            print(f"\n✗ {cadence_type.value.upper()} cadence test FAILED with exception:")
            print(f"  {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)

    total = len(tests)
    for test_name, test_func, cadence_type in tests:
        # Determine status based on whether we passed
        status = "✓ PASSED" if failed == 0 or test_name not in [
            name for name, _, _ in tests[:total - passed]
        ] else "✗ FAILED"
        print(f"  {cadence_type.value:12s}: {status}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n✓ All tests passed!")
        return 0
    else:
        print(f"\n✗ {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    if HAS_PYTEST:
        # Run with pytest for better reporting
        sys.exit(pytest.main([__file__, "-v", "--tb=short"]))
    else:
        # Fall back to manual execution
        sys.exit(run_all_tests())
