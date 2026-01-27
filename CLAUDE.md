# CLAUDE.md

## Project Overview

G8aural is a web application for ABRSM aural training where students practice two key skills:
1. **Cadence Identification** - Listen to chord progressions and identify cadence types (Perfect, Plagal, Imperfect, Interrupted)
2. **Voice Singing** - Sing back melodies from memory with real-time pitch detection and feedback

Built as a single self-contained Shiny for Python application where everything runs in one process.

## Architecture Overview

```
Browser
  ↓
Shiny App (app.py)
  ├── Python: Chord generation + game logic (music21-based)
  │   ├── Cadence Module: Cadence identification features
  │   └── Voice Module: Voice singing features
  └── JavaScript: Audio playback (Tone.js) + notation rendering (VexFlow)
```

## Core Components

- **Music Theory Engine**: Generates chord progressions with voice leading using music21
- **Reactive UI**: Interactive user interface based on Shiny's reactive model
- **Tab Modules**: Feature-specific modules for cadence identification and voice singing
- **Pitch Detection**: Real-time pitch analysis and feedback for voice singing exercises

## Documentation Resources

The project documentation is organized in the following structure:

- **Project Vision and Plans**:
  - [VISION.md](./plans/VISION.md) - Educational purpose and core features
  - [ARCHITECTURE.md](./plans/ARCHITECTURE.md) - Technical architecture details
  - [ROADMAP.md](./plans/ROADMAP.md) - Future development plans

- **Technical Guides**:
  - [SETUP.md](./.claude/guides/SETUP.md) - Installation and setup instructions
  - [STRUCTURE.md](./.claude/guides/STRUCTURE.md) - Project structure details
  - [MUSIC_THEORY.md](./.claude/guides/MUSIC_THEORY.md) - Music theory engine details
  - [DEVELOPMENT.md](./.claude/guides/DEVELOPMENT.md) - Common development tasks

- **Historical Documentation**:
  - [Plans Archive](./plans/archive/) - Historical planning documents organized by development phase

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

### Run the Test App (Voice Leading Development)

```bash
shiny run chord_test_app.py --port 8081 --reload
```

Access at: http://localhost:8081

## Key Constraints

- **Always 4 voices**: Voice leading produces 4-note chords (SATB). Each voice has a distinct note.
- **Hybrid progression architecture**: Grade 8 uses 1-5 lead-in + 3-chord cadence. Grades 6-7 use pure 3-chord.
- **Inversion constraints**: Only apply to final 3 chords in hybrid mode, all 3 in pure mode.
- **music21 required**: Don't replace with simpler implementation. Musical quality depends on music21.
- **Corpus data is precomputed**: Don't load Bach chorales at runtime. Use precomputed JSON.
- **No backend server**: Single Shiny app. Don't split into frontend/backend.

## Testing Requirements

**IMPORTANT: Always use pytest to run tests. Never create inline or temporary test files.**

- All tests live in `tests/` directory
- Run tests with pytest, not inline Python:
  ```bash
  pytest tests/                    # Run all tests
  pytest tests/test_specific.py   # Run specific file
  pytest -k 'test_name'           # Run tests matching pattern
  pytest -x                       # Stop on first failure
  ```
- Add new tests to `tests/test_*.py` files, not temporary files
- Never use `python -c` with test assertions
- Never create test files in `/tmp/` or outside `tests/`
- The `pytest.ini` configures test discovery and output options

## Feature Overview

### 1. Cadence Identification (Grades 6-8)
- Students listen to chord progressions played with piano sounds
- Students identify the cadence type (Perfect, Plagal, Imperfect, Interrupted)
- Grade-specific difficulty levels (6-8) with appropriate cadence types
- Musical-quality progressions using Bach corpus patterns
- Interactive feedback with visual notation after correct answers

### 2. Voice Singing (Grades 5-8)
- Grade-specific melodic exercises:
  - Grade 5: Single melody to sing from memory
  - Grade 6: Upper part of two-part phrase
  - Grade 7: Lower part of two-part phrase
  - Grade 8: Lowest part of three-part phrase
- Real-time pitch detection and analysis
- Octave-invariant grading system
- Visual feedback with pitch contour display