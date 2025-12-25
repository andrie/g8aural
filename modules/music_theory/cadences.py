"""
Cadence definitions and patterns for ABRSM Grade 8 aural training.
"""
from enum import Enum
from typing import List, Tuple


class CadenceType(Enum):
    """Types of cadences for Grade 8 aural training."""
    PERFECT = "perfect"      # V → I
    PLAGAL = "plagal"        # IV → I
    IMPERFECT = "imperfect"  # (any) → V
    INTERRUPTED = "interrupted"  # V → vi


class CadencePattern:
    """Defines the chord pattern for each cadence type."""

    @staticmethod
    def get_cadence_chords(cadence_type: CadenceType) -> Tuple[int, int]:
        """
        Get the final two scale degrees for a cadence type.

        Args:
            cadence_type: The type of cadence

        Returns:
            Tuple of (penultimate_degree, final_degree)
        """
        patterns = {
            CadenceType.PERFECT: (5, 1),      # V → I
            CadenceType.PLAGAL: (4, 1),       # IV → I
            CadenceType.IMPERFECT: (1, 5),    # I → V (common choice)
            CadenceType.INTERRUPTED: (5, 6),  # V → vi
        }
        return patterns[cadence_type]

    @staticmethod
    def get_common_approach_chords(cadence_type: CadenceType) -> List[int]:
        """
        Get common chord progressions that approach each cadence.

        Args:
            cadence_type: The type of cadence

        Returns:
            List of scale degrees that commonly precede this cadence
        """
        # These are chords that work well before the final two chords
        approaches = {
            CadenceType.PERFECT: [1, 4, 6],       # I, IV, vi work well before V-I
            CadenceType.PLAGAL: [1, 5, 2],        # I, V, ii work well before IV-I
            CadenceType.IMPERFECT: [1, 4, 6],     # I, IV, vi work well before I-V
            CadenceType.INTERRUPTED: [1, 4, 2],   # I, IV, ii work well before V-vi
        }
        return approaches[cadence_type]

    @staticmethod
    def get_display_name(cadence_type: CadenceType) -> str:
        """
        Get human-readable display name for cadence.

        Args:
            cadence_type: The type of cadence

        Returns:
            Display name string
        """
        names = {
            CadenceType.PERFECT: "Perfect Cadence (V-I)",
            CadenceType.PLAGAL: "Plagal Cadence (IV-I)",
            CadenceType.IMPERFECT: "Imperfect Cadence (I-V)",
            CadenceType.INTERRUPTED: "Interrupted Cadence (V-vi)",
        }
        return names[cadence_type]
