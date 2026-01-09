# ABRSM Grade 8 Cadence Training App - MVP Implementation Plan

## Project Overview
Create a web-based aural training application for ABRSM Grade 8 students to practice identifying cadences. The app will play short chord progressions ending in one of four cadence types, allow students to identify the cadence, and display the musical notation after correct identification.

## Requirements Summary

### Functional Requirements
- **Cadence Types**: Perfect (V-I), Plagal (IV-I), Imperfect (I-V), Interrupted (V-VI)
- **Presentation**: 4-8 chord progression establishing key and ending with target cadence
- **Key**: C major only (for MVP)
- **Audio**: Authentic piano sound using Web Audio API (Tone.js with sampled piano)
- **Interaction**: Multiple choice buttons for cadence selection
- **Feedback**: Allow retry on incorrect answers; show notation only after correct answer
- **Notation Display**: Full staff notation showing the chord progression

### Technical Stack
- **Backend**: FastAPI (Python)
- **Frontend**: HTML/CSS/JavaScript
- **Audio Library**: Tone.js with piano samples
- **Notation Library**: VexFlow
- **Deployment**: Local development initially
- **Progression Generation**: Rule-based following music theory principles

### Future Considerations
- Design to allow progress tracking later
- Extensible to additional keys
- Potential for different difficulty levels

## Architecture

### Project Structure
```
g8aural/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                 # FastAPI app entry point
│   │   ├── models.py               # Pydantic models for API
│   │   ├── music_theory/
│   │   │   ├── __init__.py
│   │   │   ├── cadences.py         # Cadence definitions
│   │   │   ├── progression.py      # Chord progression generator
│   │   │   └── notes.py            # Note/chord representations
│   │   └── api/
│   │       ├── __init__.py
│   │       └── routes.py           # API endpoints
│   ├── tests/
│   │   ├── __init__.py
│   │   └── test_progression.py
│   └── requirements.txt
├── frontend/
│   ├── index.html                  # Main HTML page
│   ├── css/
│   │   └── styles.css
│   ├── js/
│   │   ├── app.js                  # Main application logic
│   │   ├── audio.js                # Tone.js audio playback
│   │   └── notation.js             # VexFlow notation rendering
│   └── assets/
│       └── piano-samples/          # Piano sample files (if needed)
├── README.md
└── .gitignore
```

## Implementation Plan

### Phase 1: Backend Core - Music Theory Engine

#### 1.1 Set Up Python Environment
- Create `requirements.txt` with: fastapi, uvicorn, pydantic, python-multipart
- Set up virtual environment
- Install dependencies

#### 1.2 Implement Music Theory Module (`backend/app/music_theory/`)

**File: `notes.py`**
- Define `Note` class (name, octave, MIDI number)
- Define `Chord` class (root note, chord type, inversion)
- Implement chord generation for C major scale:
  - I (C major), ii (D minor), iii (E minor), IV (F major), V (G major), vi (A minor), vii (B dim)
- Convert chords to MIDI note numbers for JSON API response

**File: `cadences.py`**
- Define `CadenceType` enum: PERFECT, PLAGAL, IMPERFECT, INTERRUPTED
- Define cadence patterns:
  - Perfect: V → I
  - Plagal: IV → I
  - Imperfect: Any → V (common: I → V, IV → V)
  - Interrupted: V → vi
- Map each cadence type to its final two chord progression

**File: `progression.py`**
- Implement `ChordProgressionGenerator` class
- Method: `generate_progression(cadence_type: CadenceType) -> List[Chord]`
  - Create 4-8 chord progression in C major
  - Follow basic voice leading rules:
    - Establish tonic (start with I)
    - Use common chord progressions (I-IV-V, I-vi-IV-V, etc.)
    - End with specified cadence
  - Return list of Chord objects
- Method: `progression_to_midi(progression: List[Chord]) -> List[List[int]]`
  - Convert each chord to list of MIDI note numbers
  - Use appropriate voicing (root position or inversions)

#### 1.3 Build FastAPI Application (`backend/app/`)

**File: `models.py`**
- Define Pydantic models:
  - `CadenceRequest`: empty or with optional parameters
  - `CadenceResponse`:
    - `cadence_type`: str
    - `progression`: List[List[int]] (MIDI notes for each chord)
    - `notation`: str (chord symbol notation for each chord)

**File: `api/routes.py`**
- Endpoint: `POST /api/cadence/generate`
  - Randomly select a cadence type
  - Generate chord progression using `ChordProgressionGenerator`
  - Return `CadenceResponse` with MIDI data and chord symbols

- Endpoint: `POST /api/cadence/check`
  - Request body: `{"session_id": str, "guess": str}`
  - Validate student's guess against correct answer
  - Return: `{"correct": bool, "message": str}`

**File: `main.py`**
- Initialize FastAPI app
- Configure CORS for local development
- Include API routes
- Add basic error handling

#### 1.4 Backend Testing
- Write unit tests for chord progression generation
- Test each cadence type generates valid progressions
- Test API endpoints return correct data structure

### Phase 2: Frontend Core - UI and Audio

#### 2.1 Set Up HTML Structure (`frontend/index.html`)
- Basic page layout with sections:
  - Header: "ABRSM Grade 8 Cadence Training"
  - Play button: "Play Cadence"
  - Multiple choice buttons: 4 buttons (Perfect, Plagal, Imperfect, Interrupted)
  - Feedback area: Display messages
  - Notation area: Canvas/div for VexFlow rendering
- Include CDN links:
  - Tone.js
  - VexFlow
  - Custom CSS and JS files

#### 2.2 Styling (`frontend/css/styles.css`)
- Clean, focused design
- Large, accessible buttons
- Clear visual states:
  - Disabled state for buttons during playback
  - Correct answer highlighting (green)
  - Incorrect answer indication (red, temporary)
- Responsive layout for different screen sizes
- Notation area with proper dimensions for VexFlow

#### 2.3 Audio Module (`frontend/js/audio.js`)

**Functionality:**
- Initialize Tone.js with piano sampler (use Tone.Sampler with basic piano samples or Tone.PolySynth as fallback)
- Function: `loadPianoSampler()` - preload piano sounds
- Function: `playProgression(progression, tempo)`:
  - Convert MIDI numbers to note names
  - Play each chord with appropriate timing (e.g., 1 second per chord)
  - Return Promise that resolves when playback complete
- Function: `stopPlayback()` - stop any playing audio

#### 2.4 Notation Module (`frontend/js/notation.js`)

**Functionality:**
- Initialize VexFlow renderer targeting notation div
- Function: `renderProgression(progression, cadenceType)`:
  - Create grand staff (treble and bass clefs)
  - Render each chord on the staff
  - Add chord symbols above staff
  - Highlight final two chords (the cadence)
  - Add cadence type label
- Function: `clearNotation()` - clear the notation area

#### 2.5 Main Application Logic (`frontend/js/app.js`)

**State Management:**
- Current cadence data (type, progression)
- Game state (waiting, playing, guessing, showing_answer)
- Attempt count for current cadence

**Functions:**
- `init()`: Initialize app, load piano samples, set up event listeners
- `fetchNewCadence()`: Call backend API to get new cadence
- `playCurrentCadence()`: Play the current progression using audio module
- `handleGuess(guessedType)`:
  - Check if guess is correct
  - If correct: show notation, display success message, enable "Next" button
  - If incorrect: show retry message, allow another attempt
  - Track attempt count
- `resetForNewCadence()`: Clear notation, reset buttons, fetch new cadence
- `updateUI(state)`: Update button states and visibility based on game state

**Event Handlers:**
- Play button click → `playCurrentCadence()`
- Cadence button clicks → `handleGuess(cadenceType)`
- Next button click → `resetForNewCadence()`

### Phase 3: Integration and Polish

#### 3.1 Connect Frontend to Backend
- Configure API base URL
- Implement fetch calls to backend endpoints
- Add loading states during API calls
- Handle network errors gracefully

#### 3.2 Audio Refinement
- Test piano sound quality
- Adjust timing between chords for musicality
- Add subtle volume envelope for more natural sound
- Ensure clean audio context initialization (handle browser autoplay policies)

#### 3.3 Notation Refinement
- Verify correct staff rendering for all chord types
- Ensure proper chord voicing display
- Add visual indicators for the cadence
- Test readability of chord symbols

#### 3.4 User Experience Polish
- Add keyboard shortcuts (Space to play, 1-4 for cadence selection)
- Smooth transitions between states
- Clear, encouraging feedback messages
- Prevent double-clicks and rapid interactions
- Add loading indicators

### Phase 4: Testing and Documentation

#### 4.1 Manual Testing
- Test each cadence type generates and plays correctly
- Verify correct/incorrect answer handling
- Test retry functionality
- Check notation display accuracy
- Test across browsers (Chrome, Firefox, Safari)

#### 4.2 Edge Cases
- Handle rapid button clicking
- Test audio playback interruption
- Verify behavior with slow network
- Test keyboard shortcut conflicts

#### 4.3 Documentation
- `README.md`: Setup instructions, how to run locally, architecture overview
- Code comments for complex music theory logic
- API documentation (can use FastAPI's automatic docs)

## Development Workflow

### Order of Implementation
1. Backend music theory engine (can be tested independently)
2. Backend API (test with curl/Postman)
3. Frontend HTML/CSS structure
4. Frontend audio module (test with hardcoded data)
5. Frontend notation module (test with hardcoded data)
6. Frontend main app logic
7. Integration
8. Polish and testing

### Running the Application
1. Backend: `cd backend && uvicorn app.main:app --reload --port 8000`
2. Frontend: Serve `frontend/` directory (e.g., `python -m http.server 8080` from frontend dir)
3. Access: http://localhost:8080

## Key Implementation Details

### Chord Progression Generation Algorithm
```
For cadence type X:
1. Start with I chord (tonic)
2. Add 2-6 intermediate chords following rules:
   - Prefer strong progressions: I→IV, I→V, IV→V, V→I, I→vi, vi→IV
   - Avoid weak progressions: V→IV (retrogression)
   - Use variety (not all I-IV-V-I)
3. End with the two chords that form cadence type X
4. Total length: 4-8 chords
```

### MIDI Representation
- Each chord represented as array of MIDI note numbers
- Example: C major chord (C4-E4-G4) = [60, 64, 67]
- Use appropriate octave ranges for piano (typically 3-5 for this application)

### Notation Chord Symbols
- Use standard Roman numeral notation: I, ii, iii, IV, V, vi
- Include chord quality when displaying

## Future Enhancements (Post-MVP)
- Add progress tracking database
- Multiple key support (all major and minor keys)
- Difficulty levels (longer progressions, more complex harmonies)
- Additional exercise types (interval identification, melodic dictation)
- User accounts and authentication
- Mobile app version
- Audio recording for student playback comparison

## Success Criteria
- ✅ App generates random cadence progressions in C major
- ✅ Piano audio plays smoothly and sounds authentic
- ✅ All 4 cadence types are correctly identified and generated
- ✅ Student can retry incorrect answers
- ✅ Staff notation displays correctly after correct answer
- ✅ UI is intuitive and responsive
- ✅ No crashes or errors during normal usage