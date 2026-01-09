"""
Tests for application configuration (config/app_config.py).

Tests configuration dictionaries for grade levels, keys, cadence types,
and generator parameters.
"""

import pytest
from modules.music_theory.cadences import CadenceType
from config.app_config import (
    KEYS_BY_GRADE,
    CADENCE_TYPES_BY_GRADE,
    GENERATOR_CONFIG,
    validate_config
)


@pytest.mark.unit
class TestKeysConfiguration:
    """Test key configuration for different grades."""

    def test_all_grades_have_keys(self):
        """Verify all grades 6-8 have key configurations."""
        for grade in [6, 7, 8]:
            assert grade in KEYS_BY_GRADE, f"Grade {grade} missing from KEYS_BY_GRADE"
            assert len(KEYS_BY_GRADE[grade]) > 0, f"Grade {grade} has empty keys list"

    def test_keys_are_strings(self):
        """Verify all keys are string values."""
        for grade, keys in KEYS_BY_GRADE.items():
            for key in keys:
                assert isinstance(key, str), f"Grade {grade} has non-string key: {key}"
                assert len(key) > 0, f"Grade {grade} has empty key string"

    def test_keys_include_major_and_minor(self):
        """Verify each grade has both major and minor keys."""
        for grade, keys in KEYS_BY_GRADE.items():
            # Major keys are uppercase, minor are lowercase
            major_keys = [k for k in keys if k[0].isupper()]
            minor_keys = [k for k in keys if k[0].islower()]

            assert len(major_keys) > 0, f"Grade {grade} has no major keys"
            assert len(minor_keys) > 0, f"Grade {grade} has no minor keys"

    def test_keys_within_three_accidentals(self):
        """
        Verify keys are within 3 sharps/flats (ABRSM requirement).

        Major keys: C, G, D, A, F, Bb, Eb (0-3 accidentals)
        Minor keys: a, e, b, f#, d, g, c (0-3 accidentals)
        """
        valid_major = ['C', 'G', 'D', 'A', 'F', 'Bb', 'Eb']
        valid_minor = ['a', 'e', 'b', 'f#', 'd', 'g', 'c']
        valid_keys = valid_major + valid_minor

        for grade, keys in KEYS_BY_GRADE.items():
            for key in keys:
                assert key in valid_keys, f"Grade {grade} has invalid key '{key}' (>3 accidentals)"


@pytest.mark.unit
class TestCadenceTypesConfiguration:
    """Test cadence type configuration for different grades."""

    def test_all_grades_have_cadence_types(self):
        """Verify all grades 6-8 have cadence type configurations."""
        for grade in [6, 7, 8]:
            assert grade in CADENCE_TYPES_BY_GRADE, f"Grade {grade} missing from CADENCE_TYPES_BY_GRADE"
            assert len(CADENCE_TYPES_BY_GRADE[grade]) > 0, f"Grade {grade} has empty cadence list"

    def test_cadence_types_are_enum_values(self):
        """Verify all cadence types are CadenceType enum values."""
        for grade, cadences in CADENCE_TYPES_BY_GRADE.items():
            for cadence in cadences:
                assert isinstance(cadence, CadenceType), f"Grade {grade} has non-CadenceType: {cadence}"

    def test_grade_6_has_two_cadences(self):
        """Grade 6: Perfect and Imperfect only."""
        grade_6_cadences = CADENCE_TYPES_BY_GRADE[6]
        assert len(grade_6_cadences) == 2
        assert CadenceType.PERFECT in grade_6_cadences
        assert CadenceType.IMPERFECT in grade_6_cadences

    def test_grade_7_has_three_cadences(self):
        """Grade 7: Perfect, Imperfect, and Interrupted."""
        grade_7_cadences = CADENCE_TYPES_BY_GRADE[7]
        assert len(grade_7_cadences) == 3
        assert CadenceType.PERFECT in grade_7_cadences
        assert CadenceType.IMPERFECT in grade_7_cadences
        assert CadenceType.INTERRUPTED in grade_7_cadences

    def test_grade_8_has_four_cadences(self):
        """Grade 8: All four cadence types."""
        grade_8_cadences = CADENCE_TYPES_BY_GRADE[8]
        assert len(grade_8_cadences) == 4
        assert CadenceType.PERFECT in grade_8_cadences
        assert CadenceType.PLAGAL in grade_8_cadences
        assert CadenceType.IMPERFECT in grade_8_cadences
        assert CadenceType.INTERRUPTED in grade_8_cadences

    def test_progressive_difficulty(self):
        """Each higher grade includes all previous cadences."""
        # Grade 6 cadences should be subset of Grade 7
        assert set(CADENCE_TYPES_BY_GRADE[6]).issubset(set(CADENCE_TYPES_BY_GRADE[7]))
        # Grade 7 cadences should be subset of Grade 8
        assert set(CADENCE_TYPES_BY_GRADE[7]).issubset(set(CADENCE_TYPES_BY_GRADE[8]))


@pytest.mark.unit
class TestGeneratorConfiguration:
    """Test generator configuration for different grades."""

    def test_all_grades_have_generator_config(self):
        """Verify all grades 6-8 have generator configurations."""
        for grade in [6, 7, 8]:
            assert grade in GENERATOR_CONFIG, f"Grade {grade} missing from GENERATOR_CONFIG"

    def test_required_config_keys_present(self):
        """Verify all required configuration keys are present."""
        required_keys = [
            'keys', 'use_voice_leading', 'use_strict_cadence',
            'use_corpus', 'corpus_temperature', 'use_sevenths',
            'min_length', 'max_length'
        ]

        for grade, config in GENERATOR_CONFIG.items():
            for key in required_keys:
                assert key in config, f"Grade {grade} missing required key '{key}'"

    def test_grade_6_configuration(self):
        """Grade 6: Simple root position, no voice leading, no 7ths."""
        config = GENERATOR_CONFIG[6]
        assert config['use_voice_leading'] is False
        assert config['use_sevenths'] is False
        assert config['use_strict_cadence'] is False  # Pure 3-chord mode
        assert config['min_length'] == 3
        assert config['max_length'] == 3

    def test_grade_7_configuration(self):
        """Grade 7: Still root position, no voice leading, no 7ths."""
        config = GENERATOR_CONFIG[7]
        assert config['use_voice_leading'] is False
        assert config['use_sevenths'] is False
        assert config['use_strict_cadence'] is False  # Pure 3-chord mode

    def test_grade_8_configuration(self):
        """Grade 8: Full SATB voice leading with inversions and 7ths."""
        config = GENERATOR_CONFIG[8]
        assert config['use_voice_leading'] is True
        assert config['use_sevenths'] is True
        assert config['use_strict_cadence'] is True  # Hybrid mode
        assert config['min_length'] >= 4
        assert config['max_length'] <= 8

    def test_temperature_values_valid(self):
        """Verify corpus temperature is in reasonable range (0.0-2.0)."""
        for grade, config in GENERATOR_CONFIG.items():
            temp = config['corpus_temperature']
            assert isinstance(temp, (int, float)), f"Grade {grade} temperature not numeric"
            assert 0.0 <= temp <= 2.0, f"Grade {grade} temperature {temp} out of range"

    def test_length_constraints_valid(self):
        """Verify min_length <= max_length."""
        for grade, config in GENERATOR_CONFIG.items():
            min_len = config['min_length']
            max_len = config['max_length']
            assert min_len <= max_len, f"Grade {grade}: min_length > max_length"
            assert min_len >= 3, f"Grade {grade}: min_length < 3"

    def test_keys_match_keys_by_grade(self):
        """Verify generator config keys reference correct KEYS_BY_GRADE."""
        for grade, config in GENERATOR_CONFIG.items():
            assert config['keys'] == KEYS_BY_GRADE[grade], \
                f"Grade {grade} generator keys don't match KEYS_BY_GRADE"


@pytest.mark.unit
class TestConfigValidation:
    """Test the validate_config() function."""

    def test_validate_config_passes(self):
        """Verify current configuration passes validation."""
        assert validate_config() is True

    def test_validation_detects_missing_keys(self, monkeypatch):
        """Test that validation catches missing keys configuration."""
        # Temporarily remove grade 8
        original = KEYS_BY_GRADE.copy()
        monkeypatch.setitem(KEYS_BY_GRADE, 8, [])

        with pytest.raises(ValueError, match="Empty keys list for grade 8"):
            validate_config()

    def test_validation_detects_missing_generator_config(self, monkeypatch):
        """Test that validation catches missing generator configuration."""
        # Temporarily remove a required key
        original_config = GENERATOR_CONFIG[8].copy()
        config_without_keys = {k: v for k, v in original_config.items() if k != 'keys'}
        monkeypatch.setitem(GENERATOR_CONFIG, 8, config_without_keys)

        with pytest.raises(ValueError, match="Missing 'keys' in grade 8 generator config"):
            validate_config()
