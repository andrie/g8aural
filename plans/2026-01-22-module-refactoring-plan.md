# G8Aural Module Refactoring Implementation Plan

This document provides a detailed step-by-step guide for refactoring the g8aural application to use a Shiny-appropriate module-based architecture. The goal is to improve maintainability and organization while aligning with Shiny for Python best practices.

## Target Directory Structure

```
g8aural/
├── app.py                        # Main entry point (minimal - just app initialization)
├── requirements.txt              # Python dependencies
├── requirements-dev.txt          # Development dependencies
│
├── modules/                      # Shiny modules (ui + server pairs)
│   ├── __init__.py
│   ├── app_module.py             # Main app module (shared layout, global state)
│   ├── cadence/                  # Cadence identification module
│   │   ├── __init__.py
│   │   ├── module.py             # Cadence module ui/server functions
│   │   ├── components.py         # UI components specific to cadence module
│   │   └── handlers.py           # Event handlers and business logic
│   └── voice/                    # Voice singing module
│       ├── __init__.py
│       ├── module.py             # Voice module ui/server functions
│       ├── components.py         # UI components specific to voice module
│       └── handlers.py           # Event handlers and business logic
│
├── lib/                          # Core application libraries
│   ├── __init__.py
│   └── music_theory/             # Music theory engine (moved from modules/)
│       ├── __init__.py
│       ├── cadences.py
│       ├── roman_numerals.py
│       ├── markov_model.py
│       ├── progression.py
│       ├── voice_leading.py
│       ├── corpus_analyzer.py
│       ├── voice_analysis.py
│       └── data/
│           └── bach_transitions.json
│
├── ui/                           # Shared UI components
│   ├── __init__.py
│   ├── layout.py                 # Shared layout components
│   └── components.py             # Reusable UI components
│
├── state/                        # Reactive state management
│   ├── __init__.py
│   ├── app_state.py              # Application-wide state (grade, settings)
│   ├── cadence_state.py          # Cadence-specific state
│   └── voice_state.py            # Voice-specific state
│
├── config/                       # Configuration (unchanged)
│   ├── __init__.py
│   └── app_config.py
│
├── www/                          # Static assets (reorganized)
│   ├── css/
│   │   └── styles.css
│   ├── js/
│   │   ├── common/
│   │   │   └── ui-helpers.js
│   │   ├── cadence/
│   │   │   ├── audio.js
│   │   │   └── notation.js
│   │   └── voice/
│   │       ├── microphone.js
│   │       ├── pitch-plot.js
│   │       └── voice-playback.js
│   └── media/                    # Any media assets
│
├── tests/                        # Test modules
│   ├── __init__.py
│   ├── conftest.py
│   └── test_modules/
│       ├── __init__.py
│       ├── test_cadence.py
│       └── test_voice.py
│
└── .claude/                      # Documentation for Claude
    └── guides/
        ├── SETUP.md
        ├── STRUCTURE.md
        ├── MUSIC_THEORY.md
        ├── DEVELOPMENT.md
        ├── EXTENSIONS.md
        └── ISSUES.md
```

## Implementation Plan

### Phase 1: Setup Directory Structure

1. Create the new directory structure:
```bash
mkdir -p modules/{cadence,voice}
mkdir -p lib
mkdir -p ui
mkdir -p www/{css,js/{common,cadence,voice}}
mkdir -p .claude/guides
```

2. Create initial `__init__.py` files:
```bash
touch modules/__init__.py
touch modules/cadence/__init__.py
touch modules/voice/__init__.py
touch lib/__init__.py
touch ui/__init__.py
touch state/__init__.py
```

### Phase 2: Refactor Music Theory Module

1. Move `modules/music_theory` to `lib/music_theory`:
```bash
mkdir -p lib/music_theory/data
cp -r modules/music_theory/* lib/music_theory/
touch lib/music_theory/__init__.py
```

2. Update imports in music theory files to reflect new structure.

### Phase 3: Set Up Shared UI Components

1. Create `ui/layout.py` with shared layout components:
```python
# ui/layout.py
from shiny import ui

def create_header():
    """Create the header section with title and description."""
    return ui.div(
        ui.h1("Sharp Ear"),
        ui.p("Interactive Aural Training for ABRSM Grades 6–8"),
        class_="header"
    )

def create_grade_selection():
    """Create the grade selection section with slider and info modal."""
    # Copy from existing ui/components.py
    # ...
```

2. Create `ui/components.py` with shared UI components:
```python
# ui/components.py
from shiny import ui

def create_feedback_section(id):
    """Create a feedback message section with the given ID."""
    return ui.div(
        ui.output_ui(id("feedback_message")),
        class_="feedback-section"
    )

# Add other shared components...
```

### Phase 4: Refactor State Management

1. Create `state/app_state.py`:
```python
# state/app_state.py
from dataclasses import dataclass
from shiny import reactive

@dataclass
class AppState:
    """Application-wide state."""

    level: reactive.Value  # Current grade level (5, 6, 7, or 8)
    restored: reactive.Value  # Whether grade restoration is complete

    @staticmethod
    def create(default_level: int = 6):
        """Factory function to create initialized state."""
        return AppState(
            level=reactive.Value(default_level),
            restored=reactive.Value(False)
        )
```

2. Create `state/cadence_state.py` (extract from existing game_state.py):
```python
# state/cadence_state.py
from dataclasses import dataclass
from shiny import reactive
from lib.music_theory.cadences import CadenceType

@dataclass
class ProgressionState:
    """Groups all data about the current progression."""
    # Copy from existing state/game_state.py
    # ...

@dataclass
class FeedbackState:
    """Groups feedback-related state."""
    # Copy from existing state/game_state.py
    # ...

@dataclass
class GameFlowState:
    """Groups game flow state."""
    # Copy from existing state/game_state.py
    # ...
```

3. Create `state/voice_state.py`:
```python
# state/voice_state.py
from dataclasses import dataclass
from shiny import reactive

@dataclass
class VoiceState:
    """Groups voice singing tab state."""
    # Copy from existing state/game_state.py
    # ...
```

### Phase 5: Create Cadence Module

1. Create `modules/cadence/components.py`:
```python
# modules/cadence/components.py
from shiny import ui

def create_control_section(id):
    """Create the control section with Play and Hint buttons."""
    return ui.div(
        ui.input_action_button(
            id("play_btn"),
            "Play Cadence",
            class_="btn-primary btn-lg"
        ),
        ui.input_action_button(
            id("hint_btn"),
            "Show Hint",
            class_="btn-warning btn-lg",
            style="margin-left: 10px;"
        ),
        class_="control-section"
    )

def create_answer_section(id):
    """Create the answer section with cadence type buttons."""
    # Modified from ui/components.py to use module namespace
    # ...
```

2. Create `modules/cadence/handlers.py`:
```python
# modules/cadence/handlers.py
import random
from typing import Dict, Any, List
from lib.music_theory.cadences import CadenceType

async def handle_correct_answer(
    session, progression_state, feedback_state, game_flow,
    button_id, cadence_type, correct_cadence
):
    """Handle the logic when user guesses correctly."""
    # Copy from handlers/game_logic.py
    # ...

# Add other handler functions...
```

3. Create `modules/cadence/module.py`:
```python
# modules/cadence/module.py
from shiny import module, ui, reactive, render
from state.cadence_state import ProgressionState, FeedbackState, GameFlowState
from .components import (
    create_control_section, create_answer_section,
    create_feedback_section, create_next_button_section,
    create_notation_section
)
from .handlers import (
    validate_guess, handle_correct_answer, handle_incorrect_answer,
    initialize_new_cadence, generate_new_cadence_data
)

@module.ui
def cadence_ui(id):
    """Create UI for cadence identification tab."""
    return ui.div(
        create_control_section(id),
        create_answer_section(id),
        create_feedback_section(id),
        create_next_button_section(id),
        create_notation_section(id),
    )

@module.server
def cadence_server(id, input, output, session, progression_state, feedback_state, game_flow, grade_state, generator):
    """Server logic for cadence identification tab."""

    # Extract from app.py, adapting to use module namespace
    # ...
```

### Phase 6: Create Voice Module

1. Create `modules/voice/components.py`:
```python
# modules/voice/components.py
from shiny import ui

def create_voice_control_section(id):
    """Create the control section for voice singing tab."""
    # Modified from ui/components.py to use module namespace
    # ...
```

2. Create `modules/voice/handlers.py`:
```python
# modules/voice/handlers.py
import random
import numpy as np
from typing import Dict, Any, List

async def generate_voice_melody(voice_state, grade_state, session, voice_generator):
    """Generate grade-appropriate melody and start playback."""
    # Extracted from app.py
    # ...
```

3. Create `modules/voice/module.py`:
```python
# modules/voice/module.py
from shiny import module, ui, reactive, render
from state.voice_state import VoiceState
from .components import (
    create_voice_control_section, create_voice_instructions,
    create_voice_recording_indicator, create_voice_feedback_section,
    create_voice_notation_section
)
from .handlers import generate_voice_melody, replay_voice_melody

@module.ui
def voice_ui(id):
    """Create UI for voice singing tab."""
    return ui.div(
        create_voice_instructions(id),
        create_voice_control_section(id),
        create_voice_recording_indicator(id),
        create_voice_feedback_section(id),
        create_voice_notation_section(id),
    )

@module.server
def voice_server(id, input, output, session, voice_state, grade_state, voice_generator):
    """Server logic for voice singing tab."""

    # Extract from app.py, adapting to use module namespace
    # ...
```

### Phase 7: Create Main App Module

1. Create `modules/app_module.py`:
```python
# modules/app_module.py
from shiny import module, ui, reactive
from config.app_config import KEYS_BY_GRADE, CADENCE_TYPES_BY_GRADE, GENERATOR_CONFIG, VOICE_CONFIG_BY_GRADE
from lib.music_theory.progression import ChordProgressionGenerator
from state.app_state import AppState
from state.cadence_state import ProgressionState, FeedbackState, GameFlowState
from state.voice_state import VoiceState
from ui.layout import create_header, create_grade_selection
from modules.cadence.module import cadence_ui, cadence_server
from modules.voice.module import voice_ui, voice_server

@module.ui
def app_ui(id):
    """Main application UI."""
    return ui.page_fluid(
        # Include custom CSS and JavaScript
        ui.tags.head(
            ui.tags.link(rel="stylesheet", href="css/styles.css"),
            # Include JavaScript files
            # ...
        ),
        # Header and grade selection (shared across all tabs)
        create_header(),
        *create_grade_selection(),  # Unpacks list of components
        # Tab navigation
        ui.navset_tab(
            ui.nav_panel(
                "Cadence Identification",
                cadence_ui(id("cadence"))
            ),
            ui.nav_panel(
                "Voice Singing",
                voice_ui(id("voice"))
            ),
            id=id("main_tabs")
        ),
    )

@module.server
def app_server(id, input, output, session):
    """Main application server logic."""
    # Grouped reactive state
    app_state = AppState.create()
    progression_state = ProgressionState.create()
    feedback_state = FeedbackState.create()
    game_flow = GameFlowState.create()
    voice_state = VoiceState.create()

    # Reactive generator for cadence identification
    generator = reactive.Value(
        ChordProgressionGenerator(**GENERATOR_CONFIG[6])
    )

    # Initialize voice generator
    voice_generator = reactive.Value(
        create_voice_generator(8)
    )

    # Initialize module servers
    cadence_server(
        id("cadence"),
        input, output, session,
        progression_state, feedback_state,
        game_flow, app_state, generator
    )

    voice_server(
        id("voice"),
        input, output, session,
        voice_state, app_state, voice_generator
    )

    # Handle grade level changes
    # ...

def create_voice_generator(grade):
    """Create voice generator based on grade level."""
    # Copy from app.py
    # ...
```

### Phase 8: Update Main App Entry Point

Refactor `app.py` to use the new module structure:

```python
"""
ABRSM Grade 8 Cadence Training - Shiny for Python Frontend
"""
from shiny import App
from pathlib import Path
from modules.app_module import app_ui, app_server

# Create app with static files from www directory
www_dir = Path(__file__).parent / "www"
app = App(app_ui("app"), app_server, static_assets=www_dir)
```

### Phase 9: Reorganize Static Assets

1. Move and reorganize CSS:
```bash
mv www/styles.css www/css/styles.css
```

2. Update JavaScript files with appropriate namespacing:
```bash
mkdir -p www/js/{common,cadence,voice}
mv www/audio.js www/js/cadence/audio.js
mv www/notation.js www/js/cadence/notation.js
mv www/microphone.js www/js/voice/microphone.js
mv www/pitch-plot.js www/js/voice/pitch-plot.js
mv www/voice-playback.js www/js/voice/voice-playback.js
mv www/grade-ui.js www/js/common/grade-ui.js
```

3. Update JavaScript imports in `modules/app_module.py`.

### Phase 10: Update Documentation

1. Create `.claude/guides/STRUCTURE.md`:
```markdown
# Project Structure

## Directory Organization
g8aural/
├── app.py                      # Main entry point
├── requirements.txt            # Python dependencies
├── modules/                    # Shiny modules (ui + server pairs)
│   ├── app_module.py           # Main app module
│   ├── cadence/                # Cadence identification module
│   └── voice/                  # Voice singing module
├── lib/                        # Core application libraries
│   └── music_theory/           # Music theory engine
├── ui/                         # Shared UI components
├── state/                      # Reactive state management
├── config/                     # Configuration
└── www/                        # Static assets
```

2. Create other documentation files in `.claude/guides/`:
   - SETUP.md
   - MUSIC_THEORY.md
   - DEVELOPMENT.md
   - EXTENSIONS.md
   - ISSUES.md

3. Create a streamlined CLAUDE.md main file:
```markdown
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
- Extension points: [EXTENSIONS.md](./.claude/guides/EXTENSIONS.md)
- Issue tracking workflow: [ISSUES.md](./.claude/guides/ISSUES.md)

## Key Constraints

- **Always 4 voices**: Voice leading produces 4-note chords (SATB). Each voice has a distinct note.
- **Hybrid progression architecture**: Grade 8 uses 1-5 lead-in + 3-chord cadence. Grades 6-7 use pure 3-chord.
- **Inversion constraints**: Only apply to final 3 chords in hybrid mode, all 3 in pure mode.
- **music21 required**: Don't replace with simpler implementation. Musical quality depends on music21.
- **Corpus data is precomputed**: Don't load Bach chorales at runtime. Use precomputed JSON.
- **No backend server**: Single Shiny app. Don't split into frontend/backend.
```

### Phase 11: Testing and Validation

1. Update import statements in test files.

2. Run tests to validate refactored code:
```bash
./run_tests.sh
```

3. Manually test the application to verify functionality:
```bash
shiny run app.py --reload
```

4. Fix any issues found during testing.

## Implementation Notes

1. When refactoring, maintain the exact same functionality - this is purely a structural change.

2. Update import paths throughout the codebase as you move files.

3. Make sure module namespacing is consistent (using `id` function for all module inputs/outputs).

4. When adapting the existing code, be careful with callback registration and reactive dependencies.

5. Some functions will need to be adapted to work with module namespaces - pay special attention to event handlers.

6. JavaScript files may need path updates in their imports and references.

7. The Shiny module pattern requires passing the `id` function to component functions to maintain proper namespacing.

This implementation plan provides a detailed roadmap for refactoring the g8aural application to use a Shiny-appropriate module-based architecture, improving maintainability while aligning with Shiny best practices.