# CLAUDE.md

## Project Overview

Web application for ABRSM aural training where students listen to chord progressions and identify cadence types (Perfect, Plagal, Imperfect, Interrupted). Built with Shiny for Python.

**Single self-contained application**: Everything runs in one Python process.

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

- **Music Theory Engine**: Generates chord progressions with voice leading
- **Reactive UI**: Interactive user interface based on Shiny's reactive model
- **Tab Modules**: Feature-specific modules for cadence identification and voice singing

## Quick Links

- Setup and run instructions: [SETUP.md](./.claude/guides/SETUP.md)
- Project structure: [STRUCTURE.md](./.claude/guides/STRUCTURE.md)
- Music theory engine details: [MUSIC_THEORY.md](./.claude/guides/MUSIC_THEORY.md)
- Common development tasks: [DEVELOPMENT.md](./.claude/guides/DEVELOPMENT.md)

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

## Architecture Details

The application uses a modular architecture with the following components:

### 1. Server-Side Components

- **Main App (app.py)**: Central application file that defines both UI and server logic
   - Uses direct handler imports instead of Shiny modules
   - Defines UI components directly in app_ui function
   - Implements server logic in app_server function including reactive effects

- **State Management**: Reactive state objects in `state/`
   - `app_state.py`: Application-wide state (grade level, settings)
   - `cadence_state.py`: Cadence-specific state (ProgressionState, FeedbackState, GameFlowState)
   - `voice_state.py`: Voice-specific state (melody data, recording state)

- **Logic Handlers**: Feature-specific handlers in `modules/` directory
   - `modules/cadence/handlers.py`: Functions for cadence identification
   - `modules/voice/handlers.py`: Functions for voice singing features
   - Each handler exports specific functions imported directly by app.py

- **Music Theory Engine**: Core music theory functionality in `lib/music_theory/`
   - `progression.py`: Chord progression generator
   - `voice_analysis.py`: Voice singing analysis and grading logic

### 2. Client-Side Components

- **JavaScript Architecture**: Feature-specific JS modules in `www/`
   - Each module focuses on a single responsibility
   - Communicates with Shiny server via custom message handlers

- **Key JavaScript Modules**:
   - `audio.js`: Cadence playback using Tone.js
   - `notation.js`: Music notation rendering with VexFlow
   - `grade-ui.js`: Grade selection UI functionality
   - `microphone.js`: Voice recording using Web Audio API
   - `voice-playback.js`: Voice playback and recording coordination
   - `pitch-plot.js`: Visualization of pitch data

### 3. UI Components

- **Shared Components**: Common UI elements in `ui/components.py`
- **Layout Elements**: Page layout components in `ui/layout.py`

This architecture uses direct imports rather than traditional Shiny modules, with clear separation between state management, handlers, and UI components.

## Key Constraints

- **Always 4 voices**: Voice leading produces 4-note chords (SATB). Each voice has a distinct note.
- **Hybrid progression architecture**: Grade 8 uses 1-5 lead-in + 3-chord cadence. Grades 6-7 use pure 3-chord.
- **Inversion constraints**: Only apply to final 3 chords in hybrid mode, all 3 in pure mode.
- **music21 required**: Don't replace with simpler implementation. Musical quality depends on music21.
- **Corpus data is precomputed**: Don't load Bach chorales at runtime. Use precomputed JSON.
- **No backend server**: Single Shiny app. Don't split into frontend/backend.