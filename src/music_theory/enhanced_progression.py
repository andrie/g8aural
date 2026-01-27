"""
Enhanced chord progression generator with improved voice leading.

This module extends the base ChordProgressionGenerator with:
- Enhanced voice leading for more musical progressions
- Better handling of cadential patterns
- Improved voice spacing and ranges
"""

import logging
from typing import List, Optional, Dict, Tuple
from music21 import roman

from .cadences import CadenceType, CadencePattern
from .progression import ChordProgressionGenerator
from .enhanced_voice_leading import EnhancedVoiceLeader
from .roman_numerals import ChordFactory

logger = logging.getLogger(__name__)


class EnhancedChordProgressionGenerator(ChordProgressionGenerator):
    """Generates chord progressions with enhanced voice leading for improved musicality."""

    def __init__(self,
                 min_length: int = 4,
                 max_length: int = 8,
                 use_voice_leading: bool = True,
                 use_sevenths: bool = True,
                 use_corpus: bool = True,
                 corpus_temperature: float = 0.8,
                 key: str = 'C',
                 keys: Optional[List[str]] = None,
                 use_strict_cadence: bool = True):
        """
        Initialize the enhanced generator.

        Args:
            min_length: Minimum total progression length (default 4) when use_strict_cadence=True
            max_length: Maximum total progression length (default 8) when use_strict_cadence=True
            use_voice_leading: Apply automatic voice leading (default True)
            use_sevenths: Use 7th chords where appropriate (default True)
            use_corpus: Use Bach corpus patterns (default True)
            corpus_temperature: Randomness for Markov model (0.0=deterministic, 2.0=very random)
            key: Key for progressions (e.g., 'C', 'G', 'd' for D minor)
            keys: Optional list of keys to randomly choose from (e.g., ['C', 'c'] for C major and minor)
            use_strict_cadence: If True, generates 1-5 lead-in chords + strict 3-chord Grade 8 cadence (4-8 total).
                                If False, generates pure 3-chord cadence only (for simpler grade levels).
        """
        # Initialize the base class
        super().__init__(
            min_length=min_length,
            max_length=max_length,
            use_voice_leading=use_voice_leading,
            use_sevenths=use_sevenths,
            use_corpus=use_corpus,
            corpus_temperature=corpus_temperature,
            key=key,
            keys=keys,
            use_strict_cadence=use_strict_cadence
        )

        # Override the voice leader with enhanced version
        if self.use_voice_leading:
            self.voice_leader = EnhancedVoiceLeader()

    def _select_antepenultimate(self, cadence_type: CadenceType, default_degree: int) -> int:
        """
        Select the antepenultimate (first) chord for the cadence with enhanced musicality.

        Args:
            cadence_type: The type of cadence
            default_degree: The default scale degree from CadencePattern

        Returns:
            Scale degree for the first chord
        """
        # For perfect cadences, I6 is often more musical than root position I
        # before the cadential 6/4 - this helps with smooth voice leading
        if cadence_type == CadenceType.PERFECT:
            return default_degree  # Still return 1 but enhanced voice leading will handle inversions

        # For imperfect cadences, sometimes vi can work well before IV-V
        # This would be handled by corpus patterns if available

        # For now, stick with the default but with better voicings
        return default_degree

    def _generate_inversion_constraints(self, cadence_type: CadenceType) -> List[List[int]]:
        """
        Get inversion constraints with some enhancements for musicality.

        Args:
            cadence_type: The type of cadence

        Returns:
            List of 3 lists, each containing allowed inversion numbers for that chord.
        """
        # Get the base constraints from the cadence pattern
        # Pass use_strict_cadence to respect grade-specific inversion rules
        constraints = CadencePattern.get_allowed_inversions(cadence_type, self.use_strict_cadence)

        # For perfect cadences, ensure the cadential 6/4 is properly voiced
        if cadence_type == CadenceType.PERFECT:
            # Already constrained as [2] in cadence patterns
            pass

        # For plagal cadences, sometimes IV6 flows better to I
        elif cadence_type == CadenceType.PLAGAL:
            # Already has [0, 1] for IV
            pass

        return constraints