"""
Markov chain model for probabilistic chord selection based on Bach corpus analysis.

Uses precomputed transition probabilities from Bach chorales to select
next chords that sound musically natural.
"""

import json
import random
from pathlib import Path
from typing import Dict, Optional, List
from .cadences import CadenceType


class MarkovChordSelector:
    """Selects chords using Bach corpus transition probabilities."""

    # Map Roman numerals to scale degrees
    ROMAN_TO_DEGREE = {
        'I': 1, 'i': 1,
        'II': 2, 'ii': 2,
        'III': 3, 'iii': 3,
        'IV': 4, 'iv': 4,
        'V': 5, 'v': 5,
        'VI': 6, 'vi': 6,
        'VII': 7, 'vii': 7
    }

    # Map scale degrees back to Roman numerals (major key)
    DEGREE_TO_ROMAN = {
        1: 'I',
        2: 'ii',
        3: 'iii',
        4: 'IV',
        5: 'V',
        6: 'vi',
        7: 'vii'
    }

    def __init__(self, data_path: Optional[str] = None):
        """
        Load precomputed transition matrix.

        Args:
            data_path: Path to bach_transitions.json. If None, uses default location.
        """
        if data_path is None:
            data_path = Path(__file__).parent / 'data' / 'bach_transitions.json'

        self.transitions = {}
        self.cadence_approaches = {}

        try:
            with open(data_path, 'r') as f:
                data = json.load(f)
                self.transitions = data.get('transitions', {})
                self.cadence_approaches = data.get('cadence_approaches', {})
        except FileNotFoundError:
            print(f"Warning: Could not find {data_path}. Using empty transition matrix.")
            # Provide fallback transitions for basic functionality
            self._initialize_fallback_transitions()

    def _initialize_fallback_transitions(self):
        """Initialize basic transition probabilities if corpus data not available."""
        self.transitions = {
            'I': {'IV': 0.30, 'V': 0.35, 'vi': 0.20, 'ii': 0.10, 'iii': 0.05},
            'ii': {'V': 0.70, 'IV': 0.15, 'I': 0.10, 'vi': 0.05},
            'iii': {'vi': 0.40, 'IV': 0.30, 'ii': 0.20, 'I': 0.10},
            'IV': {'V': 0.45, 'I': 0.30, 'ii': 0.15, 'vi': 0.10},
            'V': {'I': 0.60, 'vi': 0.25, 'IV': 0.10, 'ii': 0.05},
            'vi': {'IV': 0.35, 'ii': 0.30, 'V': 0.20, 'iii': 0.15},
            'vii': {'I': 0.80, 'iii': 0.10, 'V': 0.10}
        }

        self.cadence_approaches = {
            'perfect': {'I-IV-V': 10, 'I-ii-V': 8, 'vi-ii-V': 7},
            'plagal': {'I-V-IV': 8, 'V-I-IV': 6},
            'imperfect': {'I-IV-I': 5, 'I-ii-I': 4},
            'interrupted': {'I-IV-V': 8, 'I-ii-V': 6}
        }

    def get_next_chord(self, current_degree: int,
                       cadence_type: CadenceType,
                       temperature: float = 0.8) -> Optional[int]:
        """
        Select next chord using weighted random choice.

        Args:
            current_degree: Current scale degree (1-7)
            cadence_type: Target cadence (for context-aware selection)
            temperature: Randomness (0.0=deterministic, 2.0=very random)

        Returns:
            Next scale degree, or None if no valid transition

        Examples:
            >>> selector = MarkovChordSelector()
            >>> next_chord = selector.get_next_chord(1, CadenceType.PERFECT, 0.8)
            >>> next_chord in [2, 4, 5, 6]  # Common progressions from I
            True
        """
        # Convert degree to Roman numeral
        current_roman = self.DEGREE_TO_ROMAN.get(current_degree, 'I')

        # Get transition probabilities
        transitions = self.transitions.get(current_roman, {})

        if not transitions:
            return None

        # Apply temperature scaling
        # Lower temperature = more deterministic (follow corpus closely)
        # Higher temperature = more random (explore more options)
        if temperature != 1.0:
            scaled_probs = {}
            for chord, prob in transitions.items():
                scaled_probs[chord] = pow(prob, 1.0 / temperature)

            # Normalize
            total = sum(scaled_probs.values())
            transitions = {k: v / total for k, v in scaled_probs.items()}

        # Optionally boost probabilities based on cadence context
        transitions = self._apply_cadence_context(
            transitions, current_degree, cadence_type
        )

        # Weighted random choice
        chords = list(transitions.keys())
        probabilities = list(transitions.values())

        chosen_roman = random.choices(chords, weights=probabilities, k=1)[0]

        # Convert back to scale degree
        chosen_degree = self.ROMAN_TO_DEGREE.get(chosen_roman)

        return chosen_degree

    def _apply_cadence_context(self, transitions: Dict[str, float],
                               current_degree: int,
                               cadence_type: CadenceType) -> Dict[str, float]:
        """
        Adjust transition probabilities based on target cadence type.

        This encourages the model to pick chords that are commonly found
        in approaches to the target cadence.

        Args:
            transitions: Current transition probabilities
            current_degree: Current scale degree
            cadence_type: Target cadence type

        Returns:
            Adjusted transition probabilities
        """
        # Map CadenceType to string key
        cadence_map = {
            CadenceType.PERFECT: 'perfect',
            CadenceType.PLAGAL: 'plagal',
            CadenceType.IMPERFECT: 'imperfect',
            CadenceType.INTERRUPTED: 'interrupted'
        }

        cadence_key = cadence_map.get(cadence_type)
        if not cadence_key or cadence_key not in self.cadence_approaches:
            return transitions

        # Get common approach patterns for this cadence
        approaches = self.cadence_approaches[cadence_key]

        # Boost chords that appear in common approaches
        adjusted = transitions.copy()
        boost_factor = 1.2  # 20% boost for chords in common approaches

        for pattern, count in approaches.items():
            chords_in_pattern = pattern.split('-')
            # If current degree matches any position in the pattern,
            # boost the next chord in that pattern
            current_roman = self.DEGREE_TO_ROMAN.get(current_degree, 'I')

            for i, chord in enumerate(chords_in_pattern[:-1]):
                if chord == current_roman and i < len(chords_in_pattern) - 1:
                    next_chord = chords_in_pattern[i + 1]
                    if next_chord in adjusted:
                        adjusted[next_chord] *= boost_factor

        # Renormalize
        total = sum(adjusted.values())
        if total > 0:
            adjusted = {k: v / total for k, v in adjusted.items()}

        return adjusted

    def get_transition_probability(self, from_degree: int,
                                   to_degree: int) -> float:
        """
        Get the probability of transitioning from one degree to another.

        Args:
            from_degree: Starting scale degree (1-7)
            to_degree: Target scale degree (1-7)

        Returns:
            Probability (0.0-1.0), or 0.0 if transition not found

        Examples:
            >>> selector = MarkovChordSelector()
            >>> prob = selector.get_transition_probability(5, 1)  # V -> I
            >>> prob > 0.5  # V->I is very common
            True
        """
        from_roman = self.DEGREE_TO_ROMAN.get(from_degree, 'I')
        to_roman = self.DEGREE_TO_ROMAN.get(to_degree, 'I')

        transitions = self.transitions.get(from_roman, {})
        return transitions.get(to_roman, 0.0)
