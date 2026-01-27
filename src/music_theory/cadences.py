"""
Cadence definitions and patterns for ABRSM Grade 8 aural training.
"""
from enum import Enum
from typing import List, Tuple


class CadenceType(Enum):
    """Types of cadences for Grade 8 aural training."""
    PERFECT = "perfect"      # Ic → V(7) → I
    PLAGAL = "plagal"        # I → IV → I
    IMPERFECT = "imperfect"  # I → IV → V
    INTERRUPTED = "interrupted"  # I → V(7) → vi


# Grade 6-7 inversion rules: ALL chords in root position
# Per ABRSM syllabus: "The chords forming the cadence will be in root position"
GRADES_6_7_INVERSION_RULES = {
    CadenceType.PERFECT: [[0], [0], [0]],
    CadenceType.PLAGAL: [[0], [0], [0]],
    CadenceType.IMPERFECT: [[0], [0], [0]],
    CadenceType.INTERRUPTED: [[0], [0], [0]],
}

# Grade 8 inversion rules for 3-chord cadence patterns
# Format: {CadenceType: [(chord1_inversions), (chord2_inversions), (chord3_inversions)]}
# Inversions: 0=root, 1=first, 2=second, 3=third (for 7th chords)
GRADE_8_INVERSION_RULES = {
    CadenceType.PERFECT: [
        [2],        # Ic (second inversion - cadential 6/4)
        [0, 1, 2],  # V or V7 (any inversion)
        [0]         # I (root position)
    ],
    CadenceType.PLAGAL: [
        [0, 1],     # I or I6 (root or first inversion)
        [0, 1],     # IV or IV6 (root or first inversion)
        [0]         # I (root position)
    ],
    CadenceType.IMPERFECT: [
        [0, 1],     # I or I6 (root or first inversion)
        [0, 1],     # IV or IV6 (root or first inversion)
        [0, 1]      # V or V6 (root or first inversion)
    ],
    CadenceType.INTERRUPTED: [
        [0, 1],     # I or I6 (root or first inversion)
        [0, 1, 2],  # V or V7 (any inversion)
        [0]         # vi (root position)
    ],
}


class CadencePattern:
    """Defines the chord pattern for each cadence type."""

    @staticmethod
    def get_cadence_chords(cadence_type: CadenceType) -> Tuple[int, int, int]:
        """
        Get the three scale degrees for a Grade 8 cadence pattern.

        Args:
            cadence_type: The type of cadence

        Returns:
            Tuple of (first_degree, second_degree, third_degree)
        """
        patterns = {
            CadenceType.PERFECT: (1, 5, 1),      # Ic → V(7) → I
            CadenceType.PLAGAL: (1, 4, 1),       # I → IV → I
            CadenceType.IMPERFECT: (1, 4, 5),    # I → IV → V
            CadenceType.INTERRUPTED: (1, 5, 6),  # I → V(7) → vi
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
    def get_allowed_inversions(cadence_type: CadenceType, use_strict_cadence: bool = True) -> List[List[int]]:
        """
        Get the allowed inversions for each chord in a cadence pattern.

        Args:
            cadence_type: The type of cadence
            use_strict_cadence: If True, use Grade 8 rules (allows inversions).
                               If False, use Grades 6-7 rules (root position only).

        Returns:
            List of three lists, each containing allowed inversion numbers for that chord.
            Inversions: 0=root, 1=first, 2=second, 3=third (for 7th chords)

        Example:
            >>> CadencePattern.get_allowed_inversions(CadenceType.PERFECT, use_strict_cadence=True)
            [[2], [0, 1, 2], [0]]  # Grade 8: Ic, V(7), I
            >>> CadencePattern.get_allowed_inversions(CadenceType.PERFECT, use_strict_cadence=False)
            [[0], [0], [0]]  # Grades 6-7: all root position
        """
        if use_strict_cadence:
            return GRADE_8_INVERSION_RULES[cadence_type]
        else:
            return GRADES_6_7_INVERSION_RULES[cadence_type]

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
            CadenceType.PERFECT: "Perfect Cadence (Ic-V-I)",
            CadenceType.PLAGAL: "Plagal Cadence (I-IV-I)",
            CadenceType.IMPERFECT: "Imperfect Cadence (I-IV-V)",
            CadenceType.INTERRUPTED: "Interrupted Cadence (I-V-vi)",
        }
        return names[cadence_type]
