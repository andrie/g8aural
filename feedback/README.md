# Chord Test Feedback

This directory contains feedback data collected from the chord test app.

## File Structure

- `chord_feedback_YYYY-MM-DD.jsonl`: Daily feedback files in JSONL format
- `analysis_report.png`: Generated visualization of feedback analysis

## Feedback Format

Each entry in the JSONL files follows this format:

```json
{
  "timestamp": "2026-01-23T14:30:45.123Z",
  "grade": 8,
  "cadence_type": "perfect",
  "progression": {
    "key": "C",
    "chord_symbols": ["I", "IV", "V7", "I"],
    "note_names": [
      ["C4", "E4", "G4", "C5"],
      ["F3", "A3", "C4", "F4"],
      ["G3", "B3", "D4", "F4"],
      ["C3", "E3", "G3", "C4"]
    ]
  },
  "rating": 4,
  "comments": "Good voice leading between V7 and I, but bass leap is too large",
  "algorithm_version": "enhanced"
}
```

## Analysis

To generate an analysis report, use the feedback analysis module:

```python
from modules.chord_test.feedback_analysis import generate_report
report = generate_report()
print(f"Total feedback collected: {report['total_feedback']}")
```

This will create visual reports in this directory and return summary statistics.