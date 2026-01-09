"""
Application configuration for g8aural cadence training.

This module contains configuration dictionaries for different grade levels,
including key signatures, cadence types, and generator parameters.
"""
from modules.music_theory.cadences import CadenceType

# Keys with up to 3 sharps or flats (Grades 6-8 requirement)
KEYS_BY_GRADE = {
    6: ['C', 'G', 'F', 'D', 'Bb', 'A', 'Eb',  # Major keys
        'a', 'e', 'd', 'b', 'g', 'f#', 'c'],   # Minor keys
    7: ['C', 'G', 'F', 'D', 'Bb', 'A', 'Eb',
        'a', 'e', 'd', 'b', 'g', 'f#', 'c'],
    8: ['C', 'G', 'F', 'D', 'Bb', 'A', 'Eb',
        'a', 'e', 'd', 'b', 'g', 'f#', 'c']
}

# Cadence types allowed for each grade
CADENCE_TYPES_BY_GRADE = {
    6: [CadenceType.PERFECT, CadenceType.IMPERFECT],
    7: [CadenceType.PERFECT, CadenceType.IMPERFECT, CadenceType.INTERRUPTED],
    8: [CadenceType.PERFECT, CadenceType.PLAGAL,
        CadenceType.IMPERFECT, CadenceType.INTERRUPTED]
}

# Generator configuration by grade level
GENERATOR_CONFIG = {
    6: {
        'min_length': 3,  # Not used in pure 3-chord mode
        'max_length': 3,  # Not used in pure 3-chord mode
        'use_voice_leading': False,  # Simple root position only
        'use_sevenths': False,  # No 7th chords
        'use_corpus': True,  # Still use Bach patterns
        'corpus_temperature': 0.7,  # More predictable
        'keys': KEYS_BY_GRADE[6],
        'use_strict_cadence': False  # Pure 3-chord cadences (no lead-in)
    },
    7: {
        'min_length': 4,  # Not used in pure 3-chord mode
        'max_length': 5,  # Not used in pure 3-chord mode
        'use_voice_leading': False,  # Still root position
        'use_sevenths': False,  # Keep triads only
        'use_corpus': True,
        'corpus_temperature': 0.7,
        'keys': KEYS_BY_GRADE[7],
        'use_strict_cadence': False  # Pure 3-chord cadences (no lead-in)
    },
    8: {
        'min_length': 4,  # Minimum total progression length (4 chords)
        'max_length': 8,  # Maximum total progression length (8 chords)
        'use_voice_leading': True,  # Full SATB with inversions
        'use_sevenths': True,  # Grade 8 uses V7
        'use_corpus': True,
        'corpus_temperature': 0.8,  # More variation
        'keys': KEYS_BY_GRADE[8],
        'use_strict_cadence': True  # Hybrid mode: 1-5 lead-in + strict 3-chord cadence (4-8 total)
    }
}


def validate_config():
    """
    Validate configuration structure and completeness.

    Raises:
        ValueError: If configuration is invalid
    """
    # Check all grades have keys
    for grade in [6, 7, 8]:
        if grade not in KEYS_BY_GRADE:
            raise ValueError(f"Missing keys configuration for grade {grade}")
        if len(KEYS_BY_GRADE[grade]) == 0:
            raise ValueError(f"Empty keys list for grade {grade}")

    # Check all grades have cadence types
    for grade in [6, 7, 8]:
        if grade not in CADENCE_TYPES_BY_GRADE:
            raise ValueError(f"Missing cadence types for grade {grade}")
        if len(CADENCE_TYPES_BY_GRADE[grade]) == 0:
            raise ValueError(f"Empty cadence types list for grade {grade}")

    # Check all grades have generator config
    for grade in [6, 7, 8]:
        if grade not in GENERATOR_CONFIG:
            raise ValueError(f"Missing generator config for grade {grade}")

        config = GENERATOR_CONFIG[grade]
        required_keys = ['keys', 'use_voice_leading', 'use_strict_cadence',
                        'use_corpus', 'corpus_temperature', 'use_sevenths']
        for key in required_keys:
            if key not in config:
                raise ValueError(f"Missing '{key}' in grade {grade} generator config")

    return True
