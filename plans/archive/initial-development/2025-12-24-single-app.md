# Migration Plan: Self-Contained Shiny Application

**Date:** 2025-12-24
**Goal:** Migrate backend music theory logic into the Shiny frontend to create a single, self-contained application

## Overview

Currently, the application runs as two separate processes:
- **Backend (FastAPI):** Generates cadence progressions and validates answers
- **Frontend (Shiny):** Provides UI and communicates with backend via HTTP

After migration, all logic will run in a single Shiny application with no external dependencies.

---

## Architecture Change

### Current Architecture
```
Browser → Shiny Frontend → HTTP API → FastAPI Backend → Music Theory Logic
```

### Target Architecture
```
Browser → Shiny Frontend (with embedded Music Theory Logic)
```

**Benefits:**
- Single process to deploy and manage
- No network latency (< 1ms vs 100-300ms)
- Simpler state management (no session IDs)
- No CORS or network error handling needed
- Easier deployment

---

## Files to Migrate

### 1. Copy Music Theory Modules (Backend → Frontend)

Copy these 4 files from `backend/app/music_theory/` to `frontend/modules/music_theory/`:

```
backend/app/music_theory/__init__.py    → frontend/modules/music_theory/__init__.py
backend/app/music_theory/notes.py       → frontend/modules/music_theory/notes.py
backend/app/music_theory/cadences.py    → frontend/modules/music_theory/cadences.py
backend/app/music_theory/progression.py → frontend/modules/music_theory/progression.py
```

**Module Summary:**
- **notes.py** (156 lines): Note and Chord classes with MIDI conversion
- **cadences.py** (76 lines): CadenceType enum and pattern definitions
- **progression.py** (216 lines): ChordProgressionGenerator with rule-based composition

These modules use only Python standard library (`enum`, `random`, `typing`) - no external dependencies.

### 2. Delete API Client

Remove `frontend/modules/api_client.py` - no longer needed.

---

## Code Changes in frontend/app.py

### Change 1: Update Imports (Lines 4-7)

**Remove:**
```python
from modules import api_client
import asyncio
```

**Add:**
```python
import random
from modules.music_theory.cadences import CadenceType
from modules.music_theory.progression import ChordProgressionGenerator

# Initialize progression generator (singleton for app lifetime)
generator = ChordProgressionGenerator(min_length=4, max_length=8)
```

### Change 2: Remove session_id from State (Line 87)

**Remove:**
```python
current_session_id = reactive.Value(None)
```

**Rationale:** Session IDs were only needed for backend API to track which cadence belongs to which user. With local generation, we store the correct answer directly in `current_cadence_type`.

### Change 3: Replace fetch_new_cadence() Function (Lines 104-129)

**Current logic:**
1. Call `api_client.generate_cadence()`
2. Store session_id, progression, chord_symbols, cadence_type
3. Update UI state

**New logic:**
1. Randomly select a cadence type
2. Generate progression locally using `generator.generate_progression()`
3. Convert to MIDI using `generator.progression_to_midi()`
4. Get chord symbols using `generator.progression_to_symbols()`
5. Store correct answer in `current_cadence_type`
6. Update UI state (same as before)

**Implementation:**
```python
async def fetch_new_cadence():
    try:
        # Randomly select a cadence type
        cadence_type = random.choice(list(CadenceType))

        # Generate the progression locally
        progression = generator.generate_progression(cadence_type)
        midi_progression = generator.progression_to_midi(progression)
        chord_symbols = generator.progression_to_symbols(progression)

        # Store the generated data and correct answer
        current_progression.set(midi_progression)
        current_chord_symbols.set(chord_symbols)
        current_cadence_type.set(cadence_type.value)  # "perfect", "plagal", etc.

        # Reset game state
        has_played.set(False)
        is_playing.set(False)
        game_state.set("ready")
        feedback_msg.set("Click 'Play Cadence' to begin")
        feedback_type.set("info")

        # Update UI (same as before)
        await session.send_custom_message("updateButtonStates", {
            "playEnabled": True,
            "answersEnabled": False,
            "nextVisible": False
        })
        await session.send_custom_message("clearNotation", {})

    except Exception as e:
        feedback_msg.set(f"Error generating cadence: {str(e)}")
        feedback_type.set("error")
```

### Change 4: Replace handle_guess() Function (Lines 174-235)

**Current logic:**
1. Check if cadence has been played
2. Check if session_id exists
3. Call `api_client.check_guess(session_id, guess)`
4. Handle correct/incorrect response
5. Update UI based on result

**New logic:**
1. Check if cadence has been played
2. Check if cadence_type exists (correct answer)
3. Validate guess locally by comparing strings
4. Handle correct/incorrect response (same messages)
5. Update UI based on result (same as before)

**Implementation:**
```python
async def handle_guess(cadence_type: str):
    if not has_played():
        feedback_msg.set("Please play the cadence first!")
        feedback_type.set("error")
        return

    if current_cadence_type() is None:
        feedback_msg.set("No cadence loaded yet!")
        feedback_type.set("error")
        return

    # Disable buttons during validation
    await session.send_custom_message("updateButtonStates", {
        "playEnabled": False,
        "answersEnabled": False,
        "nextVisible": False
    })

    try:
        # Validate guess locally
        correct_cadence = current_cadence_type()
        guess_normalized = cadence_type.lower().strip()
        is_correct = guess_normalized == correct_cadence

        if is_correct:
            # Correct answer
            feedback_msg.set("Correct! Well done!")
            feedback_type.set("success")
            game_state.set("correct")

            # Show notation (same as before)
            await session.send_custom_message("renderNotation", {
                "progression": current_progression(),
                "chordSymbols": current_chord_symbols(),
                "cadenceType": correct_cadence
            })

            await session.send_custom_message("updateButtonStates", {
                "playEnabled": True,
                "answersEnabled": False,
                "nextVisible": True,
                "showNotation": True
            })
        else:
            # Incorrect answer
            feedback_msg.set("Not quite. Try again!")
            feedback_type.set("error")

            # Re-enable answer buttons for retry
            await session.send_custom_message("updateButtonStates", {
                "playEnabled": True,
                "answersEnabled": True,
                "nextVisible": False
            })

    except Exception as e:
        feedback_msg.set(f"Error validating answer: {str(e)}")
        feedback_type.set("error")

        await session.send_custom_message("updateButtonStates", {
            "playEnabled": True,
            "answersEnabled": True,
            "nextVisible": False
        })
```

**Key Points:**
- Validation logic is identical to backend (routes.py lines 76-95)
- Same user-facing messages: "Correct! Well done!" and "Not quite. Try again!"
- Same UI state transitions
- No session cleanup needed (state overwritten on next cadence)

---

## Dependency Changes

### Update frontend/requirements.txt

**Remove:**
```
httpx>=0.27.0
```

**Final requirements.txt:**
```
shiny>=0.10.0
```

**Rationale:**
- `httpx` was only used by `api_client.py` for HTTP requests
- Music theory modules use only Python standard library
- No new dependencies needed

---

## Files NOT Modified

These files remain unchanged:

### JavaScript Layer
- `frontend/www/audio.js` - Only communicates with Shiny via messages
- `frontend/www/notation.js` - Only communicates with Shiny via messages
- `frontend/www/styles.css` - Pure CSS, no logic

### Other Frontend Code
All other functions in `app.py` remain unchanged:
- Play button handler
- Playback completion handler
- Audio loading handler
- Answer button handlers (perfect, plagal, imperfect, interrupted)
- Hint button handler
- Next button handler
- Feedback message renderer

These functions only use reactive values and send messages to JavaScript - no interaction with API client.

---

## Implementation Steps

### Step 1: Backup Current State
```bash
cd /home/andrie/wsl-github/g8aural
git add .
git commit -m "Backup before migration"
git checkout -b backup-before-migration
git checkout main
```

### Step 2: Copy Music Theory Modules
```bash
cd /home/andrie/wsl-github/g8aural
mkdir -p frontend/modules/music_theory
cp backend/app/music_theory/__init__.py frontend/modules/music_theory/
cp backend/app/music_theory/notes.py frontend/modules/music_theory/
cp backend/app/music_theory/cadences.py frontend/modules/music_theory/
cp backend/app/music_theory/progression.py frontend/modules/music_theory/
```

### Step 3: Verify Imports
```bash
cd /home/andrie/wsl-github/g8aural/frontend
python3 -c "from modules.music_theory.cadences import CadenceType; print('✓ Imports work')"
```

### Step 4: Modify app.py
1. Update imports (lines 4-11)
2. Remove `current_session_id` from state (line 87)
3. Replace `fetch_new_cadence()` function (lines 104-129)
4. Replace `handle_guess()` function (lines 174-235)

### Step 5: Update requirements.txt
```bash
cd /home/andrie/wsl-github/g8aural/frontend
# Edit requirements.txt - remove httpx line
```

### Step 6: Delete API Client
```bash
cd /home/andrie/wsl-github/g8aural/frontend/modules
rm api_client.py
```

### Step 7: Test Imports
```bash
cd /home/andrie/wsl-github/g8aural/frontend
python3 -c "import app; print('✓ App imports successfully')"
```

### Step 8: Start Application
```bash
cd /home/andrie/wsl-github/g8aural/frontend
shiny run app.py --port 8080 --reload
```

### Step 9: Functional Testing
Open http://localhost:8080 and verify:
- [ ] App loads without errors
- [ ] "Play Cadence" button works
- [ ] Audio plays correctly
- [ ] Answer buttons work
- [ ] Correct answer shows notation
- [ ] Incorrect answer allows retry
- [ ] Hint button works
- [ ] "Next Cadence" button generates new progression
- [ ] All four cadence types work

---

## Testing Strategy

### Unit Test: Music Theory Modules
```bash
cd /home/andrie/wsl-github/g8aural/frontend
python3 << 'EOF'
from modules.music_theory.progression import ChordProgressionGenerator
from modules.music_theory.cadences import CadenceType

gen = ChordProgressionGenerator()
for cadence_type in CadenceType:
    prog = gen.generate_progression(cadence_type)
    midi = gen.progression_to_midi(prog)
    symbols = gen.progression_to_symbols(prog)
    print(f'✓ {cadence_type.value}: {symbols}')
EOF
```

### Integration Test: Full Workflow
1. Load app (should generate first cadence)
2. Click "Play Cadence" (audio should play)
3. Try incorrect answer (should show error, allow retry)
4. Try correct answer (should show notation, enable next)
5. Click "Next Cadence" (should generate new progression)

### Browser Console Check
Open Developer Tools (F12) and verify:
- No JavaScript errors
- Audio initialization messages appear
- Shiny messages sent/received correctly

---

## Rollback Plan

If migration fails, restore from backup:

```bash
cd /home/andrie/wsl-github/g8aural
git checkout backup-before-migration

# Or restore specific files:
git checkout backup-before-migration -- frontend/app.py
git checkout backup-before-migration -- frontend/modules/api_client.py
git checkout backup-before-migration -- frontend/requirements.txt
rm -rf frontend/modules/music_theory/
pip install httpx>=0.27.0
```

Then restart backend server:
```bash
cd /home/andrie/wsl-github/g8aural/backend
source .venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

---

## Expected Outcomes

### Performance Improvements
- **Response Time:** ~100-300ms (API call) → < 1ms (local generation)
- **Reliability:** No network errors possible
- **Startup:** One process instead of two

### Simplified Deployment
- **Before:** Deploy FastAPI backend + Shiny frontend separately
- **After:** Deploy single Shiny application

### Simplified State Management
- **Before:** Sessions dict on backend, session_id in frontend
- **After:** All state in Shiny reactive values

### Unchanged User Experience
- Same UI and interactions
- Same audio playback and notation display
- Same feedback messages
- Same game flow

---

## Critical Files

### Must Modify
1. `/home/andrie/wsl-github/g8aural/frontend/app.py` - Main application (2 functions, imports, state)
2. `/home/andrie/wsl-github/g8aural/frontend/requirements.txt` - Remove httpx

### Must Copy
3. `/home/andrie/wsl-github/g8aural/backend/app/music_theory/notes.py` → `frontend/modules/music_theory/`
4. `/home/andrie/wsl-github/g8aural/backend/app/music_theory/cadences.py` → `frontend/modules/music_theory/`
5. `/home/andrie/wsl-github/g8aural/backend/app/music_theory/progression.py` → `frontend/modules/music_theory/`

### Must Delete
6. `/home/andrie/wsl-github/g8aural/frontend/modules/api_client.py` - No longer needed

### Keep Unchanged
- All JavaScript files (audio.js, notation.js)
- CSS file (styles.css)
- All other functions in app.py

---

## Success Criteria

Migration is complete and successful when:
1. ✅ App starts without errors
2. ✅ All imports work correctly
3. ✅ Cadence generation works locally
4. ✅ Audio playback functions correctly
5. ✅ Answer validation works (correct and incorrect)
6. ✅ Notation displays on correct answer
7. ✅ All four cadence types generate successfully
8. ✅ No backend server needed
9. ✅ User experience unchanged

---

## Post-Migration

### Optional Backend Cleanup
Once frontend is working, the backend can be:
- Kept as reference/documentation
- Archived
- Removed (if no longer needed)

### Future Enhancements
With self-contained app, easier to add:
- Difficulty levels (chord count, complexity)
- Progress tracking and statistics
- Offline functionality
- Desktop application (PyInstaller)
- Mobile deployment (PWA)