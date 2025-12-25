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
from datetime import datetime
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
        self.chorales_analyzed = 0

    def analyze_all_bach_chorales(self, limit: Optional[int] = None) -> None:
        """
        Parse all Bach chorales and extract progression patterns.

        Args:
            limit: Optional limit on number of chorales to process (for testing)
        """
        print("Loading Bach chorales from music21 corpus...")

        # Use direct chorales iterator (provides 371 chorales)
        chorales = list(corpus.chorales.Iterator())

        # Optional limit for testing
        if limit is not None:
            chorales = chorales[:limit]
            print(f"Limited to first {limit} chorales for testing")

        print(f"Found {len(chorales)} Bach chorales to analyze")
        print()

        successful_analyses = 0
        failed_chorales = []

        for idx, score in enumerate(chorales):
            if idx % 10 == 0:
                print(f"Processing chorale {idx+1}/{len(chorales)}...")

            try:
                self._analyze_chorale(score)
                successful_analyses += 1
                self.chorales_analyzed = successful_analyses
            except Exception as e:
                failed_chorales.append((idx, str(e)))
                print(f"Warning: Could not analyze chorale {idx+1}: {e}")
                continue

        print()
        print(f"Successfully analyzed {successful_analyses}/{len(chorales)} chorales")

        if failed_chorales:
            failure_rate = len(failed_chorales) / len(chorales) * 100
            print(f"Failure rate: {failure_rate:.1f}%")

            if failure_rate > 20:
                print("WARNING: High failure rate. Check music21 installation.")

    def _analyze_chorale(self, score: stream.Score) -> None:
        """Analyze a single chorale for chord progressions."""
        # Get the key
        try:
            chorale_key = score.analyze('key')
        except Exception as e:
            raise ValueError(f"Could not determine key: {e}")

        # Chordify to get vertical harmonies
        try:
            chords = score.chordify()
        except Exception as e:
            raise ValueError(f"Could not chordify score: {e}")

        # Extract Roman numeral analysis
        roman_numerals = []
        skipped_chords = 0

        for chord_obj in chords.flatten().notes:
            if chord_obj.isChord:
                try:
                    # Analyze chord in the context of the key
                    rn = roman.romanNumeralFromChord(chord_obj, chorale_key)
                    # Simplify to just the scale degree (I, ii, iii, IV, V, vi, vii)
                    figure = self._normalize_roman_numeral(rn.figure)

                    if figure:
                        roman_numerals.append(figure)
                    else:
                        skipped_chords += 1
                except Exception:
                    skipped_chords += 1
                    continue

        if not roman_numerals:
            raise ValueError(f"No valid chords extracted (skipped {skipped_chords})")

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
        Handles inversions, sevenths, diminished chords, and secondary dominants.
        """
        import re

        # Remove slash chords (secondary dominants like V/V)
        base = figure.split('/')[0]

        # Remove figured bass numbers (6, 65, 7, 42, etc.)
        base = re.sub(r'[0-9]+', '', base)

        # Remove quality indicators (° for diminished, + for augmented)
        base = re.sub(r'[o+°]', '', base)

        # Skip chromatic chords (bVI, #iv, augmented 6ths, Neapolitan)
        if base in ['It', 'Fr', 'Ger', 'N'] or base.startswith('b') or base.startswith('#'):
            return None

        # CRITICAL: Check longer numerals first to avoid substring matching
        valid_numerals = [
            'VII', 'vii',  # Check VII before VI and V
            'III', 'iii',  # Check III before II and I
            'VI', 'vi',    # Check VI before V
            'IV', 'iv',    # Check IV before I
            'II', 'ii',    # Check II before I
            'V', 'v',
            'I', 'i'       # Check I last
        ]

        for numeral in valid_numerals:
            if base.startswith(numeral):
                return numeral

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
                'total_chorales_analyzed': self.chorales_analyzed,
                'total_transitions': sum(self.total_transitions.values()),
                'unique_chord_types': len(probabilities),
                'analysis_date': datetime.now().isoformat()
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
