# g8aural Test Suite

Comprehensive test suite for the ABRSM Grade 8 Cadence Training application.

## Overview

This test suite includes:
- **Unit tests**: Fast, isolated tests for individual functions
- **Integration tests**: Tests for component interactions
- **Music theory tests**: Tests for music21-based chord generation

## Test Structure

```
tests/
├── conftest.py                 # Shared fixtures and test utilities
├── test_config.py              # Configuration validation tests (21 tests)
├── test_game_logic.py          # Game logic function tests (21 tests)
├── test_app.py                 # Application initialization tests (7 passed, 6 skipped)
├── test_grade8_compliance.py   # ABRSM Grade 8 syllabus compliance (12 tests) ⭐
├── test_progression.py         # Chord progression tests (existing)
├── test_voice_leading.py       # Voice leading tests (existing)
├── test_multi_key.py           # Multi-key support tests (existing)
├── test_unique_pitches.py      # Unique pitch validation tests (existing)
└── test_inversion_display.py  # Inversion display tests (existing)
```

## Running Tests

### Run all tests
```bash
pytest
```

### Run with verbose output
```bash
pytest -v
```

### Run specific test file
```bash
pytest tests/test_config.py
pytest tests/test_game_logic.py
pytest tests/test_app.py
```

### Run tests by marker
```bash
pytest -m unit              # Fast unit tests only
pytest -m integration       # Integration tests
pytest -m music_theory      # Music theory tests
pytest -m slow              # Slow-running tests
```

### Run with coverage (if pytest-cov installed)
```bash
pytest --cov=modules --cov=handlers --cov=state --cov=ui --cov=config --cov-report=html
```

### Use the convenience script
```bash
./run_tests.sh              # Run all tests
./run_tests.sh unit         # Run unit tests only
./run_tests.sh integration  # Run integration tests only
```

## Test Markers

Tests are categorized with markers:

- `@pytest.mark.unit` - Fast, isolated unit tests
- `@pytest.mark.integration` - Tests involving multiple components
- `@pytest.mark.music_theory` - Tests for music21-based functionality
- `@pytest.mark.ui` - Tests for UI components
- `@pytest.mark.slow` - Tests that take significant time

## Fixtures

The `conftest.py` file provides shared fixtures:

### Generator Fixtures
- `basic_generator` - Simple generator for testing (no corpus)
- `hybrid_generator` - Grade 8 hybrid mode (4-8 chords)
- `multi_key_generator` - Generator with multiple keys

### State Fixtures
- `progression_state` - Fresh ProgressionState instance
- `feedback_state` - Fresh FeedbackState instance
- `game_flow_state` - Fresh GameFlowState instance
- `grade_state` - Fresh GradeState instance

### Sample Data
- `all_cadence_types` - List of all CadenceType enum values
- `sample_progression` - Sample C major perfect cadence

### Utility Functions
- `assert_valid_midi_notes(progression)` - Validate MIDI note structure
- `assert_valid_note_names(note_names)` - Validate note name format
- `assert_valid_chord_symbols(symbols)` - Validate chord symbol format

## Test Coverage

### test_config.py (21 tests)
Tests application configuration:
- Key configuration for grades 6-8
- Cadence type configuration
- Generator configuration
- Configuration validation

### test_game_logic.py (21 tests)
Tests game logic functions:
- Answer validation
- Feedback message generation
- Cadence data generation
- Hybrid vs. pure mode behavior
- Multi-key support

### test_app.py (7 passed, 6 skipped)
Tests application initialization:
- Module imports
- Configuration validity
- State object creation (requires Shiny reactive context - skipped)
- Full workflow simulation

### test_grade8_compliance.py (12 tests) ⭐
**ABRSM Grade 8 Syllabus Compliance Suite**

Integration tests validating 100% syllabus compliance:
1. All four cadence types available
2. Keys within 3 sharps/flats
3. Four-part SATB harmony
4. No duplicate pitches
5. Proper voice leading
6. Chord inversions (triads and 7th chords)
7. Progression length 4-8 chords
8. Musical coherence (Bach corpus)
9. End-to-end integration test
10. Regression guards

This suite serves as:
- **Integration test** combining all requirements
- **Documentation** mapping code to ABRSM syllabus
- **Regression guard** preventing compliance breakage

### Existing Music Theory Tests
- `test_progression.py` - 3-chord cadence generation
- `test_voice_leading.py` - SATB voice leading validation
- `test_multi_key.py` - Multi-key progression generation
- `test_unique_pitches.py` - Unique pitch constraint validation
- `test_inversion_display.py` - Chord inversion display

## Writing New Tests

### Example Unit Test
```python
import pytest

@pytest.mark.unit
def test_my_function():
    """Test description."""
    result = my_function(input)
    assert result == expected
```

### Example Integration Test
```python
import pytest

@pytest.mark.integration
@pytest.mark.music_theory
def test_generator_workflow(basic_generator, all_cadence_types):
    """Test complete generation workflow."""
    for cadence_type in all_cadence_types:
        progression = basic_generator.generate_progression(cadence_type)
        assert len(progression) == 3
```

### Using Fixtures
```python
def test_with_fixture(progression_state, sample_progression):
    """Test using shared fixtures."""
    prog, notes, symbols, cadence, key = sample_progression
    progression_state.set_all(prog, notes, symbols, cadence, key)
    assert progression_state.cadence_type() == cadence
```

## Continuous Integration

To add these tests to CI:

```yaml
# .github/workflows/test.yml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.10'
      - run: pip install -r requirements.txt
      - run: pytest -v --tb=short
```

## Troubleshooting

### music21 initialization is slow
This is normal on first import (~1.5 seconds). Subsequent runs are fast.

### Tests are failing with ModuleNotFoundError
Ensure you're running pytest from the project root:
```bash
cd /path/to/g8aural
pytest
```

### Corpus-related tests are slow
Use the `basic_generator` fixture which has `use_corpus=False` for faster, predictable tests.

### Random test failures
Tests using `multi_key_generator` or testing randomness may need multiple iterations to cover all cases. Consider using `pytest-randomly` to detect order-dependent tests.

## Further Reading

- [pytest documentation](https://docs.pytest.org/)
- [pytest fixtures](https://docs.pytest.org/en/stable/fixture.html)
- [pytest markers](https://docs.pytest.org/en/stable/mark.html)
- [music21 documentation](https://web.mit.edu/music21/doc/)
