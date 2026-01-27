# Plan: Fix Module Duplication and Grade-Specific Inversion Rules

## Problem Summary

The app shows `Ic V I` progressions in Grade 7 instead of root position only because:

1. **Critical Bug**: `EnhancedChordProgressionGenerator._generate_inversion_constraints()` calls `CadencePattern.get_allowed_inversions(cadence_type)` WITHOUT passing `use_strict_cadence`, so Grade 6-7 uses Grade 8 rules
2. **Module Duplication**: `modules/music_theory/` is a re-export layer but incomplete (missing enhanced variants) and has duplicate files
3. **Test Import Inconsistencies**: Mixed imports (`modules.` vs `lib.`) cause enum comparison failures
4. **Documentation Gaps**: No docs for enhanced variants or module structure

## Phase 1: Fix Critical Bug (HIGHEST PRIORITY)

**File**: `/home/andrie/github/g8aural/lib/music_theory/enhanced_progression.py`

**Change at line 100**:
```python
# Before (BUG):
constraints = CadencePattern.get_allowed_inversions(cadence_type)

# After (FIXED):
constraints = CadencePattern.get_allowed_inversions(cadence_type, self.use_strict_cadence)
```

**Verification**:
- Run app, set Grade 6 or 7, generate cadences - all should be root position (I V I, not Ic V I)
- Run `pytest tests/test_grade8_compliance.py` - should pass

## Phase 2: Clean Up Module Duplication

### 2a. Delete duplicate file
- Delete `/home/andrie/github/g8aural/modules/music_theory/corpus_analyzer.py` (identical to lib version)

### 2b. Add missing re-exports to `modules/music_theory/__init__.py`
```python
from lib.music_theory.enhanced_progression import EnhancedChordProgressionGenerator
from lib.music_theory.enhanced_voice_leading import EnhancedVoiceLeader
```

### 2c. Add missing re-exports to `modules/music_theory/progression.py`
```python
from lib.music_theory.enhanced_progression import EnhancedChordProgressionGenerator
__all__ = ['ChordProgressionGenerator', 'EnhancedChordProgressionGenerator']
```

### 2d. Add missing re-exports to `modules/music_theory/voice_leading.py`
```python
from lib.music_theory.enhanced_voice_leading import EnhancedVoiceLeader
__all__ = ['VoiceLeader', 'EnhancedVoiceLeader']
```

## Phase 3: Standardize Test Imports

Change `from modules.music_theory` to `from lib.music_theory` in:

| File | Lines |
|------|-------|
| `tests/test_progression.py` | 16-17 |
| `tests/test_unique_pitches.py` | 21-22 |
| `tests/test_game_logic.py` | 9 |
| `tests/test_multi_key.py` | 7-8 |
| `tests/test_app.py` | 141 |
| `tests/test_voice_analysis.py` | 8 |
| `tests/test_voice_leading.py` | 10-12 |
| `tests/test_inversion_display.py` | 20-21 |
| `tests/conftest.py` | 8-9 |

**Verification**: `pytest tests/` - all tests should pass

## Phase 4: Update Documentation

### 4a. Update `.claude/guides/STRUCTURE.md`
Add section explaining:
- `lib/music_theory/` = primary implementations
- `modules/music_theory/` = re-export layer for backward compatibility
- Always import from `lib.music_theory` in new code

### 4b. Update `.claude/guides/MUSIC_THEORY.md`
Add documentation for:
- `EnhancedChordProgressionGenerator` - uses `EnhancedVoiceLeader` for better voicings
- `EnhancedVoiceLeader` - wider bass range, better spacing
- Grade 6-7 root position requirement

### 4c. Update `./plans/` if needed
- Review and update any planning documents that reference old module paths

## Phase 5: Test Suite Overhaul

### 5a. Audit Existing Tests

Review each test file for relevance and correctness:

| File | Status | Issue |
|------|--------|-------|
| `test_grade8_compliance.py` | Review | May not catch Grade 6-7 syllabus violations |
| `test_progression.py` | Review | Tests pass but don't verify inversions per grade |
| `test_voice_leading.py` | Review | Slow - generates many progressions |
| `test_unique_pitches.py` | Review | May be redundant with other tests |
| `test_inversion_display.py` | Review | Unclear if still relevant |
| `test_multi_key.py` | Review | Slow - tests many key combinations |

### 5b. Remove or Fix Failing/Irrelevant Tests

- Identify tests that fail due to outdated assumptions
- Remove tests that no longer reflect app behavior
- Fix tests that should pass but have incorrect assertions

### 5c. Add Syllabus Compliance Tests

Create `/home/andrie/github/g8aural/tests/test_syllabus_compliance.py`:

```python
"""Tests that verify ABRSM syllabus requirements are met."""

class TestGrade6Syllabus:
    """Grade 6: Perfect and Imperfect cadences, root position only."""
    def test_only_perfect_and_imperfect_cadences(self): ...
    def test_all_chords_root_position(self): ...
    def test_no_seventh_chords(self): ...

class TestGrade7Syllabus:
    """Grade 7: Perfect, Imperfect, Interrupted cadences, root position only."""
    def test_cadence_types_available(self): ...
    def test_all_chords_root_position(self): ...
    def test_no_seventh_chords(self): ...

class TestGrade8Syllabus:
    """Grade 8: All 4 cadence types, inversions allowed, V7 allowed."""
    def test_all_four_cadence_types(self): ...
    def test_first_chord_always_root_position(self): ...
    def test_cadence_inversions_per_syllabus(self): ...
    def test_dominant_seventh_allowed(self): ...
    def test_progression_length_4_to_8(self): ...
```

### 5d. Optimize Slow Tests

**Problem**: Some tests generate many progressions, causing slow test runs.

**Solutions**:
- Reduce iteration counts where possible (e.g., test 3 progressions not 10)
- Use `@pytest.mark.slow` for comprehensive tests
- Create a fast test subset for quick iteration:
  ```bash
  pytest tests/ -m "not slow"  # Quick tests only
  pytest tests/ -m "slow"      # Slow tests only
  ```
- Mock random key selection in tests that don't specifically test keys

### 5e. Create Test Categories

Add pytest markers in `pytest.ini`:
```ini
markers =
    unit: Fast unit tests (no progression generation)
    integration: Tests that generate actual progressions
    slow: Tests that take >5 seconds
    syllabus: Tests that verify ABRSM syllabus compliance
```

### 5f. New Regression Test File

Create `/home/andrie/github/g8aural/tests/test_grade_inversions.py`:
- Test Grade 6-7 uses root position only (all 3 chords)
- Test Grade 8 first chord is always root position (to establish key)
- Test Grade 8 allows inversions in cadence portion (I Ic V I pattern)
- Test `CadencePattern.get_allowed_inversions()` respects `use_strict_cadence`

## Verification Checklist

After all phases:

**Functionality**:
- [ ] Grade 6 generates root position only (I V I, not Ic V I)
- [ ] Grade 7 generates root position only
- [ ] Grade 8: First chord always root position, then allows inversions (I Ic V I for Perfect, I Ic V vi for Interrupted)
- [ ] `shiny run app.py` works correctly for all grades
- [ ] `shiny run chord_test_app.py` works correctly

**Tests**:
- [ ] `pytest tests/ -m "not slow"` completes in <30 seconds
- [ ] `pytest tests/` passes with no enum comparison errors
- [ ] New syllabus compliance tests catch grade-specific violations
- [ ] No failing tests remain (either fixed or removed with justification)

**Documentation**:
- [ ] Documentation reflects actual module structure
- [ ] Test categories documented in pytest.ini

## Critical Files

| File | Purpose |
|------|---------|
| `lib/music_theory/enhanced_progression.py` | **BUG LOCATION** - line 100 |
| `lib/music_theory/cadences.py` | Has correct `get_allowed_inversions()` API |
| `lib/music_theory/progression.py` | Base class with correct implementation |
| `modules/music_theory/__init__.py` | Re-export hub - needs enhanced variants |
| `config/app_config.py` | Grade configs with `use_strict_cadence` settings |
| `app.py` | Uses `EnhancedChordProgressionGenerator` |
