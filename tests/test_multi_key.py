#!/usr/bin/env python3
"""
Test 3-chord cadences with multiple keys (major and minor).
"""

import sys
from src.music_theory.progression import ChordProgressionGenerator
from src.music_theory.cadences import CadenceType

def test_keys():
    """Test cadences in different keys."""
    print("="*60)
    print("Multi-Key Cadence Test")
    print("="*60)

    # Test with multiple keys
    generator = ChordProgressionGenerator(
        use_voice_leading=True,
        use_sevenths=True,
        use_corpus=False,
        keys=['C', 'G', 'D', 'c', 'd']  # Mix of major and minor keys
    )

    success_count = 0
    total_count = 0

    for key in ['C', 'G', 'D', 'c', 'd']:
        print(f"\n{'='*60}")
        print(f"Testing in key: {key.upper() if key.isupper() else key + ' minor'}")
        print(f"{'='*60}")

        # Create generator for this specific key
        gen = ChordProgressionGenerator(
            use_voice_leading=True,
            use_sevenths=True,
            use_corpus=False,
            keys=[key]
        )

        for cadence_type in CadenceType:
            total_count += 1

            try:
                prog = gen.generate_progression(cadence_type)
                symbols = gen.progression_to_symbols(prog)
                midi = gen.progression_to_midi(prog)
                inversions = gen.progression_to_inversions(prog, midi)
                constraints = gen._generate_inversion_constraints(cadence_type)

                constraints_satisfied = all(
                    inv in expected for inv, expected in zip(inversions, constraints)
                )

                if constraints_satisfied:
                    status = "✓"
                    success_count += 1
                else:
                    status = "✗"

                print(f"  {cadence_type.value:12s}: {' → '.join(symbols):20s} | "
                      f"Inversions: {inversions} {status}")

            except Exception as e:
                print(f"  {cadence_type.value:12s}: FAILED - {e}")

    print(f"\n{'='*60}")
    print(f"Total: {success_count}/{total_count} tests passed")
    print(f"{'='*60}")

    return 0 if success_count == total_count else 1

if __name__ == "__main__":
    sys.exit(test_keys())
