"""
Application configuration for g8aural cadence training.

This module contains configuration dictionaries for different grade levels,
including key signatures, cadence types, and generator parameters.
"""
from src.music_theory.cadences import CadenceType

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
        'use_voice_leading': True,  # SATB voice leading for 4-note chords
        'use_sevenths': False,  # No 7th chords
        'use_corpus': True,  # Still use Bach patterns
        'corpus_temperature': 0.7,  # More predictable
        'keys': KEYS_BY_GRADE[6],
        'use_strict_cadence': False  # Pure 3-chord cadences (no lead-in)
    },
    7: {
        'min_length': 4,  # Not used in pure 3-chord mode
        'max_length': 5,  # Not used in pure 3-chord mode
        'use_voice_leading': True,  # SATB voice leading for 4-note chords
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

# Voice singing configuration by grade (for Voice Singing tab)
# Defines voice parts, target voice, and generator settings for each grade
VOICE_CONFIG_BY_GRADE = {
    5: {
        'num_voices': 1,        # Single melody
        'target_voice': None,   # User sings the only voice (soprano)
        'voice_parts': ['soprano'],
        'min_length': 4,
        'max_length': 8,
        'keys': KEYS_BY_GRADE[6],  # Reuse Grade 6 keys (up to 3♯/♭)
        'use_voice_leading': False,  # Simple melody, no harmony
        'use_sevenths': False,
        'use_corpus': True,
        'corpus_temperature': 0.7,
        'use_strict_cadence': False  # Pure 3-chord cadence mode
    },
    6: {
        'num_voices': 2,
        'target_voice': 'soprano',  # User sings UPPER part
        'voice_parts': ['soprano', 'alto'],  # Changed from ['soprano', 'bass'] to avoid octave doubling
        'min_length': 4,
        'max_length': 6,
        'keys': KEYS_BY_GRADE[6],
        'use_voice_leading': True,  # Two-voice harmony
        'use_sevenths': False,
        'use_corpus': True,
        'corpus_temperature': 0.7,
        'use_strict_cadence': False
    },
    7: {
        'num_voices': 2,
        'target_voice': 'bass',    # User sings LOWER part
        'voice_parts': ['alto', 'bass'],  # Changed from ['soprano', 'bass'] to avoid octave doubling
        'min_length': 4,
        'max_length': 6,
        'keys': KEYS_BY_GRADE[7],
        'use_voice_leading': True,
        'use_sevenths': False,
        'use_corpus': True,
        'corpus_temperature': 0.7,
        'use_strict_cadence': False
    },
    8: {
        'num_voices': 3,
        'target_voice': 'bass',    # User sings LOWEST part
        'voice_parts': ['soprano', 'alto', 'bass'],
        'min_length': 4,
        'max_length': 8,
        'keys': KEYS_BY_GRADE[8],
        'use_voice_leading': True,  # Full SATB
        'use_sevenths': True,   # Grade 8 uses V7
        'use_corpus': True,
        'corpus_temperature': 0.8,
        'use_strict_cadence': True  # Hybrid mode with lead-in
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

    # Check all grades have voice config (grades 5-8)
    for grade in [5, 6, 7, 8]:
        if grade not in VOICE_CONFIG_BY_GRADE:
            raise ValueError(f"Missing voice config for grade {grade}")

        voice_config = VOICE_CONFIG_BY_GRADE[grade]
        required_keys = ['num_voices', 'target_voice', 'voice_parts', 'keys',
                        'use_voice_leading', 'use_corpus', 'corpus_temperature',
                        'use_sevenths', 'use_strict_cadence']
        for key in required_keys:
            if key not in voice_config:
                raise ValueError(f"Missing '{key}' in grade {grade} voice config")

        # Validate voice_parts is not empty
        if len(voice_config['voice_parts']) == 0:
            raise ValueError(f"Empty voice_parts list for grade {grade}")

        # Validate num_voices matches voice_parts length
        if voice_config['num_voices'] != len(voice_config['voice_parts']):
            raise ValueError(f"num_voices ({voice_config['num_voices']}) does not match voice_parts length ({len(voice_config['voice_parts'])}) for grade {grade}")

    return True