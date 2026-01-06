# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Web application for ABRSM Grade 8 aural training where students listen to chord progressions and identify cadence types (Perfect, Plagal, Imperfect, Interrupted). Built with Shiny for Python.

**Single self-contained application**: No separate backend server or API. Everything runs in one Python process.

## Quick Start

### Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**Note**: First-time setup takes ~1.5 seconds for music21 to initialize and download corpus data.

### Run the Application

```bash
source .venv/bin/activate
shiny run app.py --port 8080 --reload
```

Access at: http://localhost:8080

### Debug Mode

```bash
shiny run app.py --log-level debug
```

## Technology Stack

- **Framework**: Shiny for Python (reactive web framework)
- **Music Theory**: music21 library (professional music toolkit with Bach corpus integration)
- **Audio**: Tone.js (JavaScript library via CDN)
- **Notation**: VexFlow (JavaScript library via CDN)

## Architecture

```
Browser
  ↓
Shiny App (app.py)
  ├── Python: Chord generation + game logic (music21-based)
  └── JavaScript: Audio playback (Tone.js) + notation rendering (VexFlow)
```

### Communication Layer

**Python → JavaScript** (send commands):
```python
await session.send_custom_message("playProgression", {
    "progression": [[60, 64, 67, 72], [67, 71, 74, 79]],  # MIDI notes (4-voice SATB)
    "noteNames": [["C4", "E4", "G4", "C5"], ["G4", "B4", "D5", "G5"]]
})
```

**JavaScript → Python** (send events):
```javascript
Shiny.setInputValue("playback_complete", Math.random(), { priority: "event" });
```

## Project Structure

```
g8aural/
├── app.py                          # Main Shiny application (UI + server logic)
├── requirements.txt                # Python dependencies
├── modules/
│   └── music_theory/               # music21-based music engine
│       ├── cadences.py             # Cadence type definitions
│       ├── roman_numerals.py       # music21 RomanNumeral wrapper
│       ├── markov_model.py         # Bach corpus Markov chain
│       ├── progression.py          # Chord progression generator
│       ├── voice_leading.py        # 4-voice SATB with lookahead
│       ├── corpus_analyzer.py      # Offline Bach analysis script
│       └── data/
│           └── bach_transitions.json  # Precomputed corpus data (189 chorales)
└── www/                            # Static assets
    ├── audio.js                    # Tone.js integration
    ├── notation.js                 # VexFlow integration
    └── styles.css                  # UI styles
```

## Music Theory Engine

The core of this application is a sophisticated music theory engine that generates musically natural chord progressions:

### Components

1. **cadences.py**: Defines the four cadence types and their chord patterns
   - Perfect: V → I
   - Plagal: IV → I
   - Imperfect: I → V (or ii → V)
   - Interrupted: V → vi

2. **roman_numerals.py**: Wrapper around music21's RomanNumeral class (`ChordFactory`)
   - Simplifies chord creation and MIDI conversion
   - Handles multi-key support

3. **markov_model.py**: Markov chain using Bach corpus transition probabilities
   - Trained on 189 Bach chorales
   - Configurable temperature for randomness vs. predictability

4. **progression.py**: Main generator (`ChordProgressionGenerator`)
   - Hybrid approach: Bach corpus patterns + rule-based fallback
   - Ensures progressions end with specified cadence type
   - Generates 4-8 chord progressions

5. **voice_leading.py**: 4-voice SATB voice leading with 1-step lookahead
   - Uses music21's VoiceLeadingQuartet for validation
   - Prevents parallel fifths/octaves
   - Optimizes for smooth voice motion
   - Always produces 4 voices (SATB)
   - MIDI range: 55-79 (optimized for treble clef)

6. **corpus_analyzer.py**: Offline script to extract patterns from Bach chorales
   - Run manually to regenerate corpus data: `python modules/music_theory/corpus_analyzer.py`
   - Takes ~30-60 seconds
   - Updates bach_transitions.json

### Generator Configuration

Key parameters in `app.py:11-19`:

```python
generator = ChordProgressionGenerator(
    min_length=4,              # Minimum chords in progression
    max_length=8,              # Maximum chords in progression
    use_voice_leading=True,    # Enable 4-voice SATB
    use_sevenths=True,         # Allow 7th chords (V7, etc.)
    use_corpus=True,           # Use Bach corpus patterns
    corpus_temperature=0.8,    # Balance: 0.0=deterministic, 2.0=very random
    keys=['C', 'c']           # Supported keys (C major, C minor)
)
```

**Important**: `keys` is now a list. Generator randomly selects one key per progression for variety.

## State Management

All state stored in Shiny reactive values (no sessions, no database):

```python
current_progression = reactive.Value(None)       # MIDI notes (4-voice)
current_note_names = reactive.Value(None)        # Note names for display
current_chord_symbols = reactive.Value(None)     # Roman numerals
current_cadence_type = reactive.Value(None)      # Correct answer
has_played = reactive.Value(False)               # Has user heard cadence?
game_state = reactive.Value("initial")           # Game flow state
```

## Common Development Tasks

### Test Chord Generation

```bash
python3 << 'EOF'
from modules.music_theory.progression import ChordProgressionGenerator
from modules.music_theory.cadences import CadenceType

gen = ChordProgressionGenerator(
    use_voice_leading=True,
    use_sevenths=True,
    use_corpus=True,
    corpus_temperature=0.8,
    keys=['C']
)

for cadence_type in CadenceType:
    prog = gen.generate_progression(cadence_type)
    midi = gen.progression_to_midi(prog)
    symbols = gen.progression_to_symbols(prog)
    print(f'{cadence_type.value}: {" → ".join(symbols)} ({len(midi[0])} voices)')
EOF
```

### Test Different Keys

```bash
python3 << 'EOF'
from modules.music_theory.progression import ChordProgressionGenerator
from modules.music_theory.cadences import CadenceType

for key in ['C', 'G', 'D', 'a', 'd']:  # lowercase = minor keys
    gen = ChordProgressionGenerator(keys=[key])
    prog = gen.generate_progression(CadenceType.PERFECT)
    symbols = gen.progression_to_symbols(prog)
    print(f'{key}: {" → ".join(symbols)}')
EOF
```

### Regenerate Bach Corpus Data

When you need to update the transition probabilities:

```bash
python modules/music_theory/corpus_analyzer.py
```

This analyzes all 189 Bach chorales in the music21 corpus and updates `modules/music_theory/data/bach_transitions.json`.

## Important Implementation Details

### music21 Performance

- **Cold start**: ~1.5 seconds (first import loads corpus index)
- **Warm generation**: ~50-100ms per progression
- This is normal behavior; don't try to "fix" the cold start

### MIDI Format

All progressions use 4-voice SATB format:
- List of chords: `[[60, 64, 67, 72], [67, 71, 74, 79], ...]`
- Each chord has exactly 4 notes (bass, tenor, alto, soprano)
- MIDI range: 55 (G3) to 79 (G5)

### Voice Leading

The voice leading engine uses 1-step lookahead:
- Generates multiple candidates for each chord
- Evaluates each candidate by simulating the next chord
- Selects the voicing that enables the smoothest continuation
- Falls back to greedy algorithm if lookahead fails

### Cadence Type Determination

Progressions are generated to end with a specific cadence:
1. Generator creates 4-8 chord progression using Bach patterns
2. Last two chords are replaced with the target cadence pattern
3. Voice leading is applied across the entire progression
4. Final cadence chords are highlighted in blue in notation

## Extension Points

### Add New Cadence Type

1. Add to `CadenceType` enum in `modules/music_theory/cadences.py:8-13`
2. Add pattern to `CadencePattern.patterns` dict in `cadences.py:30-36`
3. Add button to UI in `app.py:59-68`
4. Add event handler in `app.py:266-284`

### Change Key(s)

Modify `keys` parameter in `app.py:18`:
```python
keys=['G']          # G major only
keys=['D', 'd']     # D major and D minor
keys=['C', 'G', 'D', 'A']  # Multiple major keys
```

**Note**: You may need to update `notation.js` to display correct key signature.

### Adjust Musical Style

Modify `corpus_temperature` in `app.py:17`:
- `0.0-0.5`: Very predictable, close to Bach
- `0.6-1.0`: Balanced (default: 0.8)
- `1.0-2.0`: More adventurous, explores unusual progressions

### Disable Bach Corpus

Set `use_corpus=False` in `app.py:16` to use pure rule-based generation (faster, less musical).

### Change Audio Quality

Edit `www/audio.js:9`:
- `"sampled"`: Real piano samples (requires internet)
- `"synthesized"`: Synthesized sound (works offline)

## Planning & Issue Tracking

This project uses **bd** (beads) for planning and issue tracking. When working in this repository, follow this workflow:

### Planning Workflow

**When planning new work:**
1. **Create issues for each planned task**:
   ```bash
   bd create "Add key signature display" -t feature -p 2
   bd create "Fix voice leading edge case" -t bug -p 0
   bd create "Add modulation support" -t feature -p 3
   ```

2. **Add dependencies when tasks block each other**:
   ```bash
   bd dep add <blocked-issue> <blocking-issue>
   # Example: bd dep add g8aural-abc123 g8aural-def456
   ```

3. **Document your plan** in the issue description or create a markdown file in `.claude/plans/`

**When starting work:**
1. Find available work: `bd ready`
2. Claim an issue: `bd update <id> --status in_progress`
3. Work on the task
4. When complete: `bd close <id>`

**Common Commands:**
```bash
bd list                        # List all issues
bd list --status open          # Show open issues
bd ready                       # Show issues ready to work on (no blockers)
bd show <id>                   # View issue details
bd dep tree <id>               # Visualize dependency tree
bd update <id> --priority 0    # Set priority (0=highest, 4=lowest)
```

**Priority Levels:**
- 0: Critical (blocking other work, bugs in production)
- 1: High (important features, significant bugs)
- 2: Medium (regular features, minor bugs)
- 3: Low (nice-to-have features)
- 4: Backlog (future consideration)

**Issue Types:**
- `feature`: New functionality
- `bug`: Something broken
- `chore`: Maintenance, refactoring, documentation
- `epic`: Large feature broken into subtasks

### Automatic Issue Creation

When you discover new work while implementing a feature:
- **Always create a beads issue** instead of just noting it in comments
- Use dependencies to track what blocks what
- This ensures work doesn't get lost and provides visibility

Example:
```bash
# Discovered while implementing voice leading
bd create "Optimize voice leading candidate generation" -t chore -p 3
bd create "Add unit tests for voice_leading.py" -t chore -p 2
```

## Documentation

Additional architecture documentation in `.claude/architecture/`:
- `overview.md`: High-level architecture summary
- `dev-guide.md`: Detailed development guide
- `music21-migration.md`: Migration notes from custom implementation
- `shiny-javascript.md`: Shiny-JavaScript communication patterns
- `music-theory-api.md`: Complete music theory API reference

## Key Constraints

- **Always 4 voices**: Voice leading always produces 4-note chords (SATB). Don't try to generate 3-voice chords. Do not use duplicated notes - each voice should have a distinct note.
- **music21 is required**: Don't try to replace with simpler implementation. The musical quality depends on music21.
- **Corpus data is precomputed**: Don't load Bach chorales at runtime. Use the precomputed JSON file.
- **No backend server**: This is a single Shiny app. Don't split into separate frontend/backend.