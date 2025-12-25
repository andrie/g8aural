"""
Offline script to analyze Bach chorales and extract chord progression patterns.

This script:
1. Parses all Bach chorales from music21 corpus
2. Extracts chord progressions using Roman numeral analysis
3. Builds transition probability matrices
4. Identifies common cadence approach patterns
5. Saves results to bach_transitions.json

Usage:
    python modules/music_theory/corpus_analyzer.py
"""

import json
from collections import defaultdict, Counter
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import music21
from music21 import corpus, roman, key, stream


class BachCorpusAnalyzer:
    """Analyzes Bach chorales to extract chord progression patterns."""

    def __init__(self):
        """Initialize the analyzer."""
        self.transitions = defaultdict(lambda: defaultdict(int))
        self.cadence_approaches = defaultdict(Counter)
        self.total_transitions = defaultdict(int)

    def analyze_all_bach_chorales(self) -> None:
        """Parse all Bach chorales and extract progression patterns."""
        print("Loading Bach chorales from music21 corpus...")

        # Get all Bach chorales (BWV 1-438)
        bach_works = corpus.search('bach', field='composer')

        # Filter to just chorales (not other Bach works)
        chorales = [work for work in bach_works
                   if 'bwv' in str(work.sourcePath).lower()
                   and 'chorale' in str(work).lower()]

        if not chorales:
            # Fallback: try direct path pattern
            print("Trying alternative corpus loading method...")
            chorales = []
            for i in range(1, 439):
                try:
                    path = f'bach/bwv{i}.mxl'
                    score = corpus.parse(path)
                    chorales.append((path, score))
                except:
                    continue
        else:
            chorales = [(work.sourcePath, corpus.parse(work))
                       for work in chorales[:100]]  # Limit to first 100 for reasonable processing time

        print(f"Found {len(chorales)} Bach chorales to analyze")

        successful_analyses = 0
        for idx, (path, score) in enumerate(chorales):
            if idx % 10 == 0:
                print(f"Processing chorale {idx+1}/{len(chorales)}...")

            try:
                self._analyze_chorale(score)
                successful_analyses += 1
            except Exception as e:
                print(f"Warning: Could not analyze {path}: {e}")
                continue

        print(f"\nSuccessfully analyzed {successful_analyses} chorales")

    def _analyze_chorale(self, score: stream.Score) -> None:
        """Analyze a single chorale for chord progressions."""
        # Get the key
        chorale_key = score.analyze('key')

        # Chordify to get vertical harmonies
        chords = score.chordify()

        # Extract Roman numeral analysis
        roman_numerals = []
        for chord_obj in chords.flatten().notes:
            if chord_obj.isChord:
                try:
                    # Analyze chord in the context of the key
                    rn = roman.romanNumeralFromChord(chord_obj, chorale_key)
                    # Simplify to just the scale degree (I, ii, iii, IV, V, vi, vii)
                    figure = self._normalize_roman_numeral(rn.figure)
                    if figure:
                        roman_numerals.append(figure)
                except:
                    continue

        # Track transitions
        for i in range(len(roman_numerals) - 1):
            current = roman_numerals[i]
            next_chord = roman_numerals[i + 1]
            self.transitions[current][next_chord] += 1
            self.total_transitions[current] += 1

        # Track cadence approaches (last 3-4 chords)
        if len(roman_numerals) >= 4:
            self._track_cadence_approaches(roman_numerals)

    def _normalize_roman_numeral(self, figure: str) -> Optional[str]:
        """
        Normalize Roman numeral to basic scale degree.

        Converts things like 'V7', 'V65', 'vi' to just 'I', 'ii', 'iii', 'IV', 'V', 'vi', 'vii'
        """
        # Remove inversions, seventh figures, etc.
        base = figure.split('/')[0]  # Remove slash chords

        # Map to basic Roman numerals
        mapping = {
            'I': 'I', 'i': 'i',
            'II': 'II', 'ii': 'ii',
            'III': 'III', 'iii': 'iii',
            'IV': 'IV', 'iv': 'iv',
            'V': 'V', 'v': 'v',
            'VI': 'VI', 'vi': 'vi',
            'VII': 'VII', 'vii': 'vii'
        }

        # Extract base numeral
        for key in mapping.keys():
            if base.startswith(key):
                return mapping[key]

        return None

    def _track_cadence_approaches(self, roman_numerals: List[str]) -> None:
        """Track common cadence approach patterns."""
        # Look at last 3 chords
        last_three = tuple(roman_numerals[-3:])
        last_two = tuple(roman_numerals[-2:])

        # Identify cadence type
        if last_two == ('V', 'I'):
            self.cadence_approaches['perfect']['-'.join(last_three)] += 1
        elif last_two == ('IV', 'I'):
            self.cadence_approaches['plagal']['-'.join(last_three)] += 1
        elif last_two[1] == 'V':
            self.cadence_approaches['imperfect']['-'.join(last_three)] += 1
        elif last_two == ('V', 'vi'):
            self.cadence_approaches['interrupted']['-'.join(last_three)] += 1

    def compute_probabilities(self) -> Dict[str, Dict[str, float]]:
        """Convert transition counts to probabilities."""
        probabilities = {}

        for current, next_chords in self.transitions.items():
            total = self.total_transitions[current]
            if total > 0:
                probabilities[current] = {
                    next_chord: count / total
                    for next_chord, count in next_chords.items()
                }

        return probabilities

    def save_to_json(self, output_path: str) -> None:
        """Save analysis results to JSON file."""
        probabilities = self.compute_probabilities()

        # Convert cadence approaches to serializable format
        cadence_approaches_dict = {
            cadence_type: dict(patterns.most_common(10))  # Top 10 patterns per type
            for cadence_type, patterns in self.cadence_approaches.items()
        }

        output_data = {
            'transitions': probabilities,
            'cadence_approaches': cadence_approaches_dict,
            'metadata': {
                'total_chorales_analyzed': len(self.total_transitions),
                'total_transitions': sum(self.total_transitions.values())
            }
        }

        # Ensure output directory exists
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w') as f:
            json.dump(output_data, f, indent=2)

        print(f"\nSaved transition data to {output_path}")
        print(f"Total unique chords tracked: {len(probabilities)}")
        print(f"Total transitions: {sum(self.total_transitions.values())}")


def main():
    """Run the Bach corpus analysis."""
    print("=" * 70)
    print("Bach Corpus Analyzer")
    print("=" * 70)
    print()

    analyzer = BachCorpusAnalyzer()

    # Analyze all chorales
    analyzer.analyze_all_bach_chorales()

    # Save results
    output_path = Path(__file__).parent / 'data' / 'bach_transitions.json'
    analyzer.save_to_json(str(output_path))

    print()
    print("=" * 70)
    print("Analysis complete!")
    print("=" * 70)


if __name__ == '__main__':
    main()
