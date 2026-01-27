#!/usr/bin/env python3
"""
Test script for voice leading with inversion constraints.

Tests the updated voice_progression() and _generate_candidates() methods
to ensure they properly enforce inversion constraints from GRADE_8_INVERSION_RULES.
"""

from music21 import roman
from src.music_theory.voice_leading import VoiceLeader
from src.music_theory.cadences import CadenceType, CadencePattern, GRADE_8_INVERSION_RULES
from src.music_theory.roman_numerals import ChordFactory


def test_perfect_cadence():
    """Test Perfect cadence: Ic → V(7) → I"""
    print("\n=== Testing PERFECT CADENCE (Ic → V → I) ===")

    # Get the inversion constraints
    constraints = GRADE_8_INVERSION_RULES[CadenceType.PERFECT]
    print(f"Inversion constraints: {constraints}")
    print(f"  Chord 1 (I): allowed inversions = {constraints[0]} (should be [2] for Ic)")
    print(f"  Chord 2 (V): allowed inversions = {constraints[1]}")
    print(f"  Chord 3 (I): allowed inversions = {constraints[2]} (should be [0] for root)")

    # Create chords
    chords = [
        roman.RomanNumeral('I', 'C'),
        roman.RomanNumeral('V', 'C'),
        roman.RomanNumeral('I', 'C')
    ]

    # Voice with constraints
    vl = VoiceLeader()
    voicings = vl.voice_progression(chords, inversion_constraints=constraints)

    print(f"\nGenerated voicings:")
    for i, (chord, voicing) in enumerate(zip(chords, voicings)):
        inversion = vl._detect_voicing_inversion(chord, voicing)
        print(f"  Chord {i+1} ({chord.figure}): {voicing}")
        print(f"    Inversion: {inversion} (allowed: {constraints[i]})")
        print(f"    Valid: {inversion in constraints[i]}")

        if inversion not in constraints[i]:
            print(f"    ❌ ERROR: Inversion {inversion} not in allowed list {constraints[i]}")
            return False

    print("\n✓ All inversions are valid for Perfect cadence")
    return True


def test_plagal_cadence():
    """Test Plagal cadence: I → IV → I"""
    print("\n=== Testing PLAGAL CADENCE (I → IV → I) ===")

    constraints = GRADE_8_INVERSION_RULES[CadenceType.PLAGAL]
    print(f"Inversion constraints: {constraints}")

    chords = [
        roman.RomanNumeral('I', 'C'),
        roman.RomanNumeral('IV', 'C'),
        roman.RomanNumeral('I', 'C')
    ]

    vl = VoiceLeader()
    voicings = vl.voice_progression(chords, inversion_constraints=constraints)

    print(f"\nGenerated voicings:")
    for i, (chord, voicing) in enumerate(zip(chords, voicings)):
        inversion = vl._detect_voicing_inversion(chord, voicing)
        print(f"  Chord {i+1} ({chord.figure}): {voicing}")
        print(f"    Inversion: {inversion} (allowed: {constraints[i]})")

        if inversion not in constraints[i]:
            print(f"    ❌ ERROR: Inversion {inversion} not in allowed list {constraints[i]}")
            return False

    print("\n✓ All inversions are valid for Plagal cadence")
    return True


def test_imperfect_cadence():
    """Test Imperfect cadence: I → IV → V"""
    print("\n=== Testing IMPERFECT CADENCE (I → IV → V) ===")

    constraints = GRADE_8_INVERSION_RULES[CadenceType.IMPERFECT]
    print(f"Inversion constraints: {constraints}")

    chords = [
        roman.RomanNumeral('I', 'C'),
        roman.RomanNumeral('IV', 'C'),
        roman.RomanNumeral('V', 'C')
    ]

    vl = VoiceLeader()
    voicings = vl.voice_progression(chords, inversion_constraints=constraints)

    print(f"\nGenerated voicings:")
    for i, (chord, voicing) in enumerate(zip(chords, voicings)):
        inversion = vl._detect_voicing_inversion(chord, voicing)
        print(f"  Chord {i+1} ({chord.figure}): {voicing}")
        print(f"    Inversion: {inversion} (allowed: {constraints[i]})")

        if inversion not in constraints[i]:
            print(f"    ❌ ERROR: Inversion {inversion} not in allowed list {constraints[i]}")
            return False

    print("\n✓ All inversions are valid for Imperfect cadence")
    return True


def test_interrupted_cadence():
    """Test Interrupted cadence: I → V(7) → vi"""
    print("\n=== Testing INTERRUPTED CADENCE (I → V7 → vi) ===")

    constraints = GRADE_8_INVERSION_RULES[CadenceType.INTERRUPTED]
    print(f"Inversion constraints: {constraints}")

    chords = [
        roman.RomanNumeral('I', 'C'),
        roman.RomanNumeral('V7', 'C'),
        roman.RomanNumeral('vi', 'C')
    ]

    vl = VoiceLeader()
    voicings = vl.voice_progression(chords, inversion_constraints=constraints)

    print(f"\nGenerated voicings:")
    for i, (chord, voicing) in enumerate(zip(chords, voicings)):
        inversion = vl._detect_voicing_inversion(chord, voicing)
        print(f"  Chord {i+1} ({chord.figure}): {voicing}")
        print(f"    Inversion: {inversion} (allowed: {constraints[i]})")

        if inversion not in constraints[i]:
            print(f"    ❌ ERROR: Inversion {inversion} not in allowed list {constraints[i]}")
            return False

    print("\n✓ All inversions are valid for Interrupted cadence")
    return True


def test_candidate_generation():
    """Test that _generate_candidates properly filters by inversion"""
    print("\n=== Testing _generate_candidates filtering ===")

    vl = VoiceLeader()
    chord = roman.RomanNumeral('I', 'C')

    # Test without constraints
    all_candidates = vl._generate_candidates(chord, allowed_inversions=None)
    print(f"\nWithout constraints: {len(all_candidates)} candidates")

    # Count inversions
    inversion_counts = {}
    for voicing in all_candidates:
        inv = vl._detect_voicing_inversion(chord, voicing)
        inversion_counts[inv] = inversion_counts.get(inv, 0) + 1

    print(f"  Inversion distribution: {inversion_counts}")

    # Test with constraint: only root position
    root_only = vl._generate_candidates(chord, allowed_inversions=[0])
    print(f"\nWith [0] constraint (root only): {len(root_only)} candidates")

    for voicing in root_only:
        inv = vl._detect_voicing_inversion(chord, voicing)
        if inv != 0:
            print(f"  ❌ ERROR: Found non-root voicing: {voicing} (inversion {inv})")
            return False

    # Test with constraint: only second inversion (for Ic)
    second_only = vl._generate_candidates(chord, allowed_inversions=[2])
    print(f"\nWith [2] constraint (2nd inv only): {len(second_only)} candidates")

    for voicing in second_only:
        inv = vl._detect_voicing_inversion(chord, voicing)
        if inv != 2:
            print(f"  ❌ ERROR: Found non-2nd-inv voicing: {voicing} (inversion {inv})")
            return False

    # Test with multiple allowed inversions
    root_and_first = vl._generate_candidates(chord, allowed_inversions=[0, 1])
    print(f"\nWith [0, 1] constraint: {len(root_and_first)} candidates")

    for voicing in root_and_first:
        inv = vl._detect_voicing_inversion(chord, voicing)
        if inv not in [0, 1]:
            print(f"  ❌ ERROR: Found invalid voicing: {voicing} (inversion {inv})")
            return False

    print("\n✓ Candidate filtering works correctly")
    return True


def main():
    """Run all tests"""
    print("=" * 60)
    print("Testing Voice Leading with Inversion Constraints")
    print("=" * 60)

    tests = [
        test_candidate_generation,
        test_perfect_cadence,
        test_plagal_cadence,
        test_imperfect_cadence,
        test_interrupted_cadence,
    ]

    results = []
    for test_func in tests:
        try:
            result = test_func()
            results.append(result)
        except Exception as e:
            print(f"\n❌ Test {test_func.__name__} failed with exception: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)

    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = sum(results)
    total = len(results)

    for test_func, result in zip(tests, results):
        status = "✓ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_func.__name__}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    exit(main())
