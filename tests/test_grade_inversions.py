#!/usr/bin/env python3
"""
Regression tests for grade-specific inversion rules.

Tests that:
- Grades 6-7 use root position only (use_strict_cadence=False)
- Grade 8 allows inversions (use_strict_cadence=True)
- CadencePattern.get_allowed_inversions() respects use_strict_cadence parameter

These tests guard against regression of the bug where EnhancedChordProgressionGenerator
didn't pass use_strict_cadence to CadencePattern.get_allowed_inversions().
"""

import pytest
from src.music_theory.progression import ChordProgressionGenerator
from src.music_theory.enhanced_progression import EnhancedChordProgressionGenerator
from src.music_theory.cadences import CadenceType, CadencePattern


class TestGradeSpecificInversions:
    """Test that inversion rules differ by grade level."""

    def test_grades_6_7_root_position_only(self):
        """Grades 6-7 (use_strict_cadence=False) should generate root position only."""
        generator = ChordProgressionGenerator(
            use_voice_leading=True,
            use_sevenths=True,
            use_corpus=False,
            keys=['C'],
            use_strict_cadence=False  # Grades 6-7
        )

        # Generate multiple progressions for each cadence type
        for cadence_type in CadenceType:
            for _ in range(5):
                prog = generator.generate_progression(cadence_type)
                midi = generator.progression_to_midi(prog)
                inversions = generator.progression_to_inversions(prog, midi)

                # All chords should be root position
                for i, inv in enumerate(inversions):
                    assert inv == 0, \
                        f"Grades 6-7 should use root position only, but chord {i} " \
                        f"of {cadence_type.value} has inversion {inv}"

    def test_grade_8_allows_inversions(self):
        """Grade 8 (use_strict_cadence=True) should allow inversions for Perfect cadence."""
        generator = ChordProgressionGenerator(
            use_voice_leading=True,
            use_sevenths=True,
            use_corpus=False,
            keys=['C'],
            use_strict_cadence=True  # Grade 8
        )

        # Perfect cadence should have Ic (second inversion) as antepenultimate chord
        found_inversion = False
        for _ in range(10):
            prog = generator.generate_progression(CadenceType.PERFECT)
            midi = generator.progression_to_midi(prog)
            inversions = generator.progression_to_inversions(prog, midi)

            # The antepenultimate chord (first of the 3-chord cadence) should be second inversion
            # In hybrid mode, this is the third-from-last chord
            if inversions[-3] == 2:
                found_inversion = True
                break

        assert found_inversion, \
            "Grade 8 Perfect cadence should have Ic (second inversion) as antepenultimate chord"


class TestEnhancedGeneratorInversions:
    """Test that EnhancedChordProgressionGenerator respects grade-specific rules."""

    def test_enhanced_grades_6_7_root_position_only(self):
        """EnhancedGenerator with use_strict_cadence=False should generate root position only."""
        generator = EnhancedChordProgressionGenerator(
            use_voice_leading=True,
            use_sevenths=True,
            use_corpus=False,
            keys=['C'],
            use_strict_cadence=False  # Grades 6-7
        )

        # Generate multiple progressions for each cadence type
        for cadence_type in CadenceType:
            for _ in range(5):
                prog = generator.generate_progression(cadence_type)
                midi = generator.progression_to_midi(prog)
                inversions = generator.progression_to_inversions(prog, midi)

                # All chords should be root position
                for i, inv in enumerate(inversions):
                    assert inv == 0, \
                        f"EnhancedGenerator with use_strict_cadence=False should use root position only, " \
                        f"but chord {i} of {cadence_type.value} has inversion {inv}"

    def test_enhanced_grade_8_allows_inversions(self):
        """EnhancedGenerator with use_strict_cadence=True should allow inversions."""
        generator = EnhancedChordProgressionGenerator(
            use_voice_leading=True,
            use_sevenths=True,
            use_corpus=False,
            keys=['C'],
            use_strict_cadence=True  # Grade 8
        )

        # Perfect cadence should have Ic (second inversion) as antepenultimate chord
        found_inversion = False
        for _ in range(10):
            prog = generator.generate_progression(CadenceType.PERFECT)
            midi = generator.progression_to_midi(prog)
            inversions = generator.progression_to_inversions(prog, midi)

            # The antepenultimate chord (first of the 3-chord cadence) should be second inversion
            if inversions[-3] == 2:
                found_inversion = True
                break

        assert found_inversion, \
            "EnhancedGenerator Grade 8 Perfect cadence should have Ic (second inversion)"


class TestCadencePatternAPI:
    """Test CadencePattern.get_allowed_inversions() API."""

    def test_get_allowed_inversions_respects_use_strict_cadence_true(self):
        """get_allowed_inversions() with use_strict_cadence=True should return Grade 8 rules."""
        constraints = CadencePattern.get_allowed_inversions(CadenceType.PERFECT, use_strict_cadence=True)

        # Perfect cadence in Grade 8: Ic-V-I
        # First chord must be second inversion (2)
        assert constraints[0] == [2], \
            f"Grade 8 Perfect cadence first chord should be second inversion only, got {constraints[0]}"

    def test_get_allowed_inversions_respects_use_strict_cadence_false(self):
        """get_allowed_inversions() with use_strict_cadence=False should return root position only."""
        for cadence_type in CadenceType:
            constraints = CadencePattern.get_allowed_inversions(cadence_type, use_strict_cadence=False)

            # All chords should only allow root position
            for i, allowed in enumerate(constraints):
                assert allowed == [0], \
                    f"Grades 6-7 {cadence_type.value} chord {i} should only allow root position, got {allowed}"

    def test_get_allowed_inversions_default_is_grade_8(self):
        """get_allowed_inversions() with default use_strict_cadence should return Grade 8 rules."""
        # Default should be use_strict_cadence=True (Grade 8)
        constraints_default = CadencePattern.get_allowed_inversions(CadenceType.PERFECT)
        constraints_explicit = CadencePattern.get_allowed_inversions(CadenceType.PERFECT, use_strict_cadence=True)

        assert constraints_default == constraints_explicit, \
            "Default should be equivalent to use_strict_cadence=True"


def test_regression_guard_enhanced_generator_passes_use_strict_cadence():
    """
    Regression test: EnhancedChordProgressionGenerator._generate_inversion_constraints()
    must pass use_strict_cadence to CadencePattern.get_allowed_inversions().

    This test guards against the bug fixed in enhanced_progression.py where
    the method didn't pass the use_strict_cadence parameter.
    """
    # Create generators with different settings
    grade_8_gen = EnhancedChordProgressionGenerator(
        use_voice_leading=True,
        use_corpus=False,
        keys=['C'],
        use_strict_cadence=True
    )
    grades_6_7_gen = EnhancedChordProgressionGenerator(
        use_voice_leading=True,
        use_corpus=False,
        keys=['C'],
        use_strict_cadence=False
    )

    # Get inversion constraints for Perfect cadence
    grade_8_constraints = grade_8_gen._generate_inversion_constraints(CadenceType.PERFECT)
    grades_6_7_constraints = grades_6_7_gen._generate_inversion_constraints(CadenceType.PERFECT)

    # Grade 8 should allow second inversion for first chord
    assert 2 in grade_8_constraints[0], \
        f"Grade 8 should allow second inversion for first chord, got {grade_8_constraints[0]}"

    # Grades 6-7 should only allow root position
    assert grades_6_7_constraints[0] == [0], \
        f"Grades 6-7 should only allow root position, got {grades_6_7_constraints[0]}"
