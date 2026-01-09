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

from modules.music_theory.progression import ChordProgressionGenerator
from modules.music_theory.cadences import CadenceType

def test_cadence_type(cadence_type: CadenceType, generator: ChordProgressionGenerator):
    """Test a specific cadence type."""
    print(f"\n{'='*60}")
    print(f"Testing {cadence_type.value.upper()} cadence")
    print(f"{'='*60}")

    try:
        # Generate progression
        prog = generator.generate_progression(cadence_type)

        # Get symbols and MIDI
        symbols = generator.progression_to_symbols(prog)
        midi = generator.progression_to_midi(prog)
        inversions = generator.progression_to_inversions(prog, midi)
        note_names = generator.progression_to_note_names(prog)

        # Get expected constraints
        constraints = generator._generate_inversion_constraints(cadence_type)

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

        # Validation
        print(f"\nValidation:")
        print(f"  - Length is 3: {'✓' if len(prog) == 3 else '✗ FAILED'}")
        print(f"  - All chords have 4 voices: {'✓' if all(len(v) == 4 for v in midi) else '✗ FAILED'}")

        constraints_satisfied = all(
            inv in expected for inv, expected in zip(inversions, constraints)
        )
        print(f"  - Inversion constraints satisfied: {'✓' if constraints_satisfied else '✗ FAILED'}")

        if constraints_satisfied:
            print(f"\n✓ {cadence_type.value.upper()} cadence test PASSED")
            return True
        else:
            print(f"\n✗ {cadence_type.value.upper()} cadence test FAILED")
            return False

    except Exception as e:
        print(f"\n✗ {cadence_type.value.upper()} cadence test FAILED with exception:")
        print(f"  {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    print("="*60)
    print("3-Chord Cadence Generator Test Suite")
    print("="*60)

    # Create generator with voice leading enabled (pure 3-chord mode)
    generator = ChordProgressionGenerator(
        min_length=3,
        max_length=3,
        use_voice_leading=True,
        use_sevenths=True,
        use_corpus=False,  # Disable corpus for predictable testing
        keys=['C'],
        use_strict_cadence=False  # Pure 3-chord mode
    )

    # Test each cadence type
    results = {}
    for cadence_type in CadenceType:
        results[cadence_type] = test_cadence_type(cadence_type, generator)

    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)

    passed = sum(1 for result in results.values() if result)
    total = len(results)

    for cadence_type, result in results.items():
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"  {cadence_type.value:12s}: {status}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n✓ All tests passed!")
        return 0
    else:
        print(f"\n✗ {total - passed} test(s) failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
