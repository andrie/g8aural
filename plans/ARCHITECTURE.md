# G8aural Architecture Overview

## Application Structure

G8aural is implemented as a single self-contained Shiny for Python application that combines both frontend UI and backend music theory logic within one process.

### Applications

The project includes two Shiny applications:

1. **Main App (`app.py`)**: The primary application for aural training
   - Cadence identification exercises
   - Voice singing exercises
   - Grade-specific configurations

2. **Chord Test App (`chord_test_app.py`)**: A development/testing tool
   - Voice leading quality evaluation
   - Visual chord highlighting during playback
   - Feedback collection for algorithm improvements

Both apps share the same JavaScript modules (`www/js/shared/`) and music theory engine (`lib/music_theory/`).

### Core Components

```
Browser
  ↓
Shiny App (app.py)
  ├── Python: Chord generation + game logic (music21-based)
  │   ├── Cadence Module: Cadence identification features
  │   └── Voice Module: Voice singing features
  └── JavaScript: Audio playback (Tone.js) + notation rendering (VexFlow)
```

### Module Organization

The application uses a modular architecture with the following components:

#### 1. Server-Side Components

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

#### 2. Client-Side Components

- **JavaScript Architecture**: Feature-specific JS modules in `www/`
   - Each module focuses on a single responsibility
   - Communicates with Shiny server via custom message handlers

- **JavaScript Module Organization** (`www/js/`):
   - `shared/audio.js`: Tone.js audio playback (used by both apps)
   - `shared/notation.js`: VexFlow notation rendering (used by both apps)
   - `common/grade-ui.js`: Grade selection UI functionality
   - `voice/microphone.js`: Voice recording using Web Audio API
   - `voice/voice-playback.js`: Voice playback and recording coordination
   - `voice/pitch-plot.js`: Visualization of pitch data
   - `chord_test/highlighting.js`: Chord highlighting for test app

#### 3. UI Components

- **Shared Components**: Common UI elements in `ui/components.py`
- **Layout Elements**: Page layout components in `ui/layout.py`

### Technology Stack

- **Framework**: Shiny for Python (reactive web framework)
- **Music Theory**: music21 library (professional music toolkit with Bach corpus integration)
- **Audio**: Tone.js (JavaScript library via CDN)
- **Notation**: VexFlow (JavaScript library via CDN)
- **Pitch Detection**: Pitchy (JavaScript pitch detection via CDN)
- **DTW Alignment**: fastdtw (Python library for sequence alignment)

## Key Technical Features

### 1. Music Theory Engine

- **Bach Corpus-Based Generation**: Uses Markov chains trained on Bach chorales
- **Voice Leading**: Sophisticated voice leading algorithm with lookahead optimization
- **Grade-Specific Configuration**: Different configurations per ABRSM grade
- **Pure vs. Hybrid Modes**:
  - **Hybrid Mode** (Grade 8): 1-5 lead-in chords + 3-chord strict cadence
  - **Pure Mode** (Grades 6-7): 3-chord cadences only

### 2. Pitch Detection System

- **Real-Time Processing**: Uses Web Audio API and Pitchy for pitch detection
- **DTW Alignment**: Uses fastdtw to align recorded pitch with target melody
- **Octave-Invariant Analysis**: Allows singing in any comfortable octave
- **Musical Distance Metric**: Uses cents-based error measurement

### 3. Grade-Specific Features

- **Keys**: Up to 3 sharps/flats for all grades
- **Voice Configuration**:
  - Grade 5: Single melody (monophonic)
  - Grade 6: Two-part harmony (sing upper part)
  - Grade 7: Two-part harmony (sing lower part)
  - Grade 8: Three-part harmony (sing lowest part)

## Technical Constraints

- **Always 4 voices**: Voice leading produces 4-note chords (SATB). Each voice has a distinct note.
- **Hybrid progression architecture**: Grade 8 uses 1-5 lead-in + 3-chord cadence. Grades 6-7 use pure 3-chord.
- **Inversion constraints**: Only apply to final 3 chords in hybrid mode, all 3 in pure mode.
- **music21 required**: Don't replace with simpler implementation. Musical quality depends on music21.
- **Corpus data is precomputed**: Don't load Bach chorales at runtime. Use precomputed JSON.
- **No backend server**: Single Shiny app. Don't split into frontend/backend.