# Voice Leading Improvements and Chord Test App Plan

## Overview

This plan addresses two main objectives:
1. Improve voice leading in chord generation to create more musical progressions
2. Create a chord test app for collecting feedback on generated chords

The current implementation generates cadences with correct chord progressions but lacks musical voice leading. Specifically, the chords:
- Are often too close rather than having good spacing
- Use only 3-note triads instead of 4-part harmony (despite having a voice leading algorithm for SATB)
- Have voices that move in parallel rather than following good voice leading principles
- Only span the treble clef range

## Current Implementation Analysis

### Voice Leading Implementation

The codebase has a sophisticated voice leading system in `/lib/music_theory/voice_leading.py`:

- **VoiceLeader** class: Implements SATB (Soprano, Alto, Tenor, Bass) voice leading with:
  - Voice ranges defined for each part (SATB)
  - Dynamic programming with 1-step lookahead optimization
  - Checks for parallel fifths/octaves using `music21.voiceLeading.VoiceLeadingQuartet`
  - Enforces inversion constraints and provides graceful fallbacks
  - Handles close vs. open voicing with spacing rules

### Chord Progression Generation

The chord generation system in `/lib/music_theory/progression.py` has:

- **ChordProgressionGenerator**: Creates progressions with two operating modes:
  - Hybrid Mode (Grade 8): 1-5 lead-in chords + 3-chord cadence (total 4-8 chords)
  - Pure 3-Chord Mode (Grades 6-7): Only 3-chord cadences without lead-in
- **Cadence Definitions**: Defined in `/lib/music_theory/cadences.py` with four types:
  - Perfect (Ic→V→I)
  - Plagal (I→IV→I)
  - Imperfect (I→IV→V)
  - Interrupted (I→V→vi)
- **Voice Leading Integration**: Voicing is handled by calling `VoiceLeader.voice_progression()`

## Voice Leading Improvements

Based on the analysis, I've identified the following improvements to make chord progressions more musical:

### 1. Enhanced Voice Range Definitions

```python
# Current voice ranges (MIDI note numbers)
VOICE_RANGES = {
    'bass': (55, 67),      # G3 to G4 (bottom of treble clef)
    'tenor': (60, 72),     # C4 (middle C) to C5
    'alto': (64, 76),      # E4 to E5
    'soprano': (67, 79),   # G4 to G5
}

# Proposed voice ranges with wider bass range
VOICE_RANGES = {
    'bass': (40, 60),      # E2 to C4
    'tenor': (48, 69),     # C3 to A4
    'alto': (55, 74),      # G3 to D5
    'soprano': (60, 81),   # C4 to A5
}
```

The bass range needs to be extended lower to allow for proper SATB voice leading and to avoid too many chord inversions. The current range (G3-G4) is too high for bass.

### 2. Improved Voice Motion Rules

Enhance the `_evaluate_transition` method in `VoiceLeader` to prioritize:
- Contrary motion between soprano and bass
- Common tone retention (keep notes that are common between consecutive chords)
- Stepwise motion preference for soprano and other voices
- Proper resolution of tendency tones (e.g., leading tone to tonic)

```python
def _evaluate_transition(self, voicing1, voicing2, chord1, chord2):
    # Base cost: total voice motion (already implemented)
    motion = sum(abs(v2 - v1) for v1, v2 in zip(voicing1, voicing2))

    penalty = 0.0
    reward = 0.0

    # Convert MIDI to pitch objects for analysis
    v1_pitches = [pitch.Pitch(midi=m) for m in voicing1]
    v2_pitches = [pitch.Pitch(midi=m) for m in voicing2]

    # Check for existing rules (parallel 5ths/8ves)
    # [existing code remains]

    # NEW: Reward common tone retention
    for v1, v2 in zip(voicing1, voicing2):
        if v1 == v2:  # Common tone retained
            reward += 3.0

    # NEW: Reward contrary motion between outer voices
    bass_direction = 1 if voicing2[0] > voicing1[0] else -1 if voicing2[0] < voicing1[0] else 0
    soprano_direction = 1 if voicing2[-1] > voicing1[-1] else -1 if voicing2[-1] < voicing1[-1] else 0
    if bass_direction != 0 and soprano_direction != 0 and bass_direction != soprano_direction:
        # Contrary motion between outer voices
        reward += 5.0

    # NEW: Reward stepwise motion in all voices
    for v1, v2 in zip(voicing1, voicing2):
        step = abs(v2 - v1)
        if step == 1 or step == 2:  # Semitone or whole tone
            reward += 1.5

    # NEW: Check for proper leading tone resolution
    # [implementation details]

    return motion + penalty - reward  # Lower score is better
```

### 3. Enhanced Initial Voicing Selection

Improve the `_choose_initial_voicing` method to favor open position more often:

```python
def _choose_initial_voicing(self, candidates):
    # [existing code with modified scoring]

    # Modified scoring to favor open position more often
    for voicing in candidates:
        # Prefer open position (evenly distributed voices)
        spans = [voicing[i+1] - voicing[i] for i in range(len(voicing)-1)]
        spacing_variance = sum((s - sum(spans)/len(spans))**2 for s in spans)

        # Lower variance means more even spacing
        # Combine with existing scoring logic
        score = span + spacing_penalty - (10.0 / (spacing_variance + 1.0))

        if score < best_score:
            best_score = score
            best_voicing = voicing
```

### 4. Cadence-Specific Voice Leading

Add special handling for common cadential patterns:

```python
def _voice_with_lookahead(self, candidates_current, candidates_next, prev_voicing, prev_chord, chord_current, chord_next):
    # [existing code]

    # Special case handling for cadential patterns
    is_cadential_64 = (chord_current.figure == 'I' and
                       self._detect_voicing_inversion(chord_current, candidate_current) == 2 and
                       chord_next.figure == 'V')

    if is_cadential_64:
        # Apply specific voice leading rules for cadential 6/4
        # [implementation]
```

## Chord Test App Implementation

Create a new app for testing chord progressions and collecting feedback:

### 1. App Structure

```
g8aural/
  ├── app.py                  # Main Shiny app (existing)
  ├── chord_test_app.py       # New chord test app (entry point)
  ├── modules/
  │   └── chord_test/         # New module for chord testing
  │       ├── handlers.py     # Test app logic
  │       └── components.py   # UI components
  └── www/
      └── js/
          └── chord_test/
              ├── audio.js    # Reuse audio playback from cadence module
              └── notation.js # Reuse notation from cadence module
```

### 2. Chord Test App UI

The chord test app will have:
- Grade selector (5-8)
- Cadence type selector (Perfect, Plagal, Imperfect, Interrupted)
- Generate button to create new chord progressions
- Staff notation display (using VexFlow)
- Play button to hear the progression
- 5-point rating scale for feedback
- Comments field for specific observations
- Submit button to save feedback

### 3. Feedback Data Structure

Feedback will be stored in JSONL format in a `feedback` folder:

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
  "algorithm_version": "enhanced_v1"
}
```

### 4. Chord Test App Implementation

```python
# chord_test_app.py
from shiny import App, ui, reactive
import modules.chord_test.components as components
import modules.chord_test.handlers as handlers

def app_ui():
    return ui.page_fluid(
        ui.h2("Chord Voice Leading Test App"),
        ui.row(
            ui.column(4,
                ui.input_select("grade", "Grade Level", [5, 6, 7, 8], selected=8),
                ui.input_select("cadence_type", "Cadence Type",
                                ["Perfect", "Plagal", "Imperfect", "Interrupted"],
                                selected="Perfect"),
                ui.input_checkbox("use_enhanced", "Use Enhanced Voice Leading", value=True),
                ui.input_action_button("generate", "Generate New Progression")
            ),
            ui.column(8,
                ui.div({"id": "notation-container", "class": "notation-section"})
            )
        ),
        ui.row(
            ui.column(12,
                ui.div({"class": "audio-controls"},
                    ui.input_action_button("play", "Play Progression", class_="btn-primary")
                )
            )
        ),
        ui.row(
            ui.column(12,
                ui.h3("Feedback"),
                ui.div({"class": "rating-controls"},
                    ui.input_radio_buttons("rating", "Rate Voice Leading Quality:",
                                          choices=[1, 2, 3, 4, 5],
                                          selected=None,
                                          inline=True)
                ),
                ui.input_text_area("comments", "Comments:", rows=3),
                ui.input_action_button("submit_feedback", "Submit Feedback", class_="btn-success")
            )
        )
    )

def server(input, output, session):
    # Initialize state
    progression_state = reactive.Value(None)
    feedback_state = reactive.Value({"submitted": False})

    # Generate new progression
    @reactive.Effect
    @reactive.event(input.generate)
    def generate_progression():
        grade = input.grade()
        cadence_type = input.cadence_type().lower()
        use_enhanced = input.use_enhanced()

        # Generate progression using enhanced or regular algorithm
        progression = handlers.generate_chord_progression(
            grade=grade,
            cadence_type=cadence_type,
            use_enhanced=use_enhanced
        )

        progression_state.set(progression)

        # Send to frontend for rendering
        session.send_custom_message("renderNotation", {
            "progression": progression["progression"],
            "noteNames": progression["note_names"],
            "symbols": progression["symbols"],
            "key": progression["key"]
        })

        # Reset feedback
        feedback_state.set({"submitted": False})

    # Play progression
    @reactive.Effect
    @reactive.event(input.play)
    def play_progression():
        if progression_state() is not None:
            progression = progression_state()
            session.send_custom_message("playProgression", {
                "progression": progression["progression"],
                "noteNames": progression["note_names"]
            })

    # Submit feedback
    @reactive.Effect
    @reactive.event(input.submit_feedback)
    def submit_feedback():
        if progression_state() is not None and input.rating() is not None:
            # Create feedback entry
            feedback = {
                "timestamp": handlers.get_timestamp(),
                "grade": input.grade(),
                "cadence_type": input.cadence_type().lower(),
                "progression": progression_state(),
                "rating": input.rating(),
                "comments": input.comments(),
                "algorithm_version": "enhanced" if input.use_enhanced() else "original"
            }

            # Save feedback to file
            handlers.save_feedback(feedback)

            # Update feedback state
            feedback_state.set({"submitted": True})

            # Show success message
            session.send_notification(
                ui.notification_show("Feedback submitted successfully!",
                                    duration=3,
                                    type="success")
            )

app = App(app_ui, server)
```

### 5. Chord Test Handlers

```python
# modules/chord_test/handlers.py
import os
import json
import datetime
from typing import Dict, Any
from lib.music_theory.cadences import CadenceType
from lib.music_theory.progression import ChordProgressionGenerator

def get_timestamp() -> str:
    """Get current timestamp in ISO format."""
    return datetime.datetime.now().isoformat()

def ensure_feedback_dir():
    """Ensure feedback directory exists."""
    os.makedirs("feedback", exist_ok=True)

def save_feedback(feedback: Dict[str, Any]):
    """Save feedback to JSONL file."""
    ensure_feedback_dir()

    # Create filename with date
    date = datetime.datetime.now().strftime("%Y-%m-%d")
    filename = f"feedback/chord_feedback_{date}.jsonl"

    # Append feedback to file
    with open(filename, "a") as f:
        f.write(json.dumps(feedback) + "\n")

def generate_chord_progression(grade: int, cadence_type: str, use_enhanced: bool = False) -> Dict[str, Any]:
    """Generate chord progression with either regular or enhanced voice leading."""
    cadence_type_enum = CadenceType(cadence_type)

    # Configure generator based on grade
    use_strict_cadence = (grade == 8)
    use_sevenths = (grade >= 7)

    # Select algorithm version
    if use_enhanced:
        # Create enhanced generator with improved voice leading
        generator = EnhancedChordProgressionGenerator(
            use_strict_cadence=use_strict_cadence,
            use_sevenths=use_sevenths,
            keys=["C", "G", "F", "D", "Bb", "A", "Eb"]  # Common keys
        )
    else:
        # Use regular generator
        generator = ChordProgressionGenerator(
            use_strict_cadence=use_strict_cadence,
            use_sevenths=use_sevenths,
            keys=["C", "G", "F", "D", "Bb", "A", "Eb"]
        )

    # Generate progression
    progression = generator.generate_progression(cadence_type_enum)

    # Convert to format needed for UI
    return {
        "progression": generator.progression_to_midi(progression),
        "note_names": generator.progression_to_note_names(progression),
        "symbols": generator.progression_to_symbols(progression),
        "key": progression[0].key.tonicPitchNameWithCase
    }
```

### 6. Enhanced Voice Leading Generator

```python
# lib/music_theory/enhanced_voice_leading.py
from .voice_leading import VoiceLeader
from typing import List
from music21 import roman, pitch, voiceLeading

class EnhancedVoiceLeader(VoiceLeader):
    """Enhanced voice leading with improved rules."""

    # Extended voice ranges with wider bass range
    VOICE_RANGES = {
        'bass': (48, 67),      # C3 to G4 (expanded lower range)
        'tenor': (60, 72),     # C4 to C5
        'alto': (64, 76),      # E4 to E5
        'soprano': (67, 79),   # G4 to G5
    }

    def _evaluate_transition(self, voicing1, voicing2, chord1, chord2):
        """
        Score a voice leading transition with enhanced rules.
        """
        # Base cost: total voice motion
        motion = sum(abs(v2 - v1) for v1, v2 in zip(voicing1, voicing2))

        penalty = 0.0
        reward = 0.0

        # Convert MIDI to pitch objects for analysis
        try:
            v1_pitches = [pitch.Pitch(midi=m) for m in voicing1]
            v2_pitches = [pitch.Pitch(midi=m) for m in voicing2]

            # Check each pair of voices for parallel motion
            for i in range(len(voicing1)):
                for j in range(i + 1, len(voicing1)):
                    vlq = voiceLeading.VoiceLeadingQuartet(
                        v1_pitches[i], v1_pitches[j],
                        v2_pitches[i], v2_pitches[j]
                    )

                    # Parallel fifths (prohibited)
                    if vlq.parallelFifth():
                        penalty += 100.0

                    # Parallel octaves (prohibited)
                    if vlq.parallelOctave():
                        penalty += 100.0

                    # Voice crossing (penalize but not as heavily)
                    if vlq.voiceCrossing():
                        penalty += 20.0

            # NEW: Reward contrary motion between outer voices
            bass_direction = 1 if voicing2[0] > voicing1[0] else -1 if voicing2[0] < voicing1[0] else 0
            soprano_direction = 1 if voicing2[-1] > voicing1[-1] else -1 if voicing2[-1] < voicing1[-1] else 0
            if bass_direction != 0 and soprano_direction != 0 and bass_direction != soprano_direction:
                # Contrary motion between outer voices
                reward += 5.0

            # NEW: Reward common tone retention
            for v1, v2 in zip(voicing1, voicing2):
                if v1 == v2:  # Common tone retained
                    reward += 3.0

            # NEW: Reward stepwise motion in all voices
            for v1, v2 in zip(voicing1, voicing2):
                step = abs(v2 - v1)
                if step == 1 or step == 2:  # Semitone or whole tone
                    reward += 1.5

        except Exception:
            # If music21 analysis fails, fall back to simple checks
            pass

        # Penalize large leaps (more than a perfect 5th = 7 semitones)
        for i, (v1, v2) in enumerate(zip(voicing1, voicing2)):
            leap = abs(v2 - v1)
            if leap > 7:
                # Penalize large leaps more in inner voices
                if i == 1 or i == 2:  # Tenor or alto
                    penalty += (leap - 7) * 4.0
                else:  # Bass or soprano
                    penalty += (leap - 7) * 3.0

            # Specially penalize tritone leaps (augmented 4th/diminished 5th)
            if leap == 6:  # Tritone in semitones
                penalty += 5.0

        return motion + penalty - reward  # Lower score is better

    def _choose_initial_voicing(self, candidates):
        """Choose best initial voicing with preference for open position."""
        if not candidates:
            # Fallback: create a basic C major chord in open position
            return [48, 64, 60, 72]  # C3, E4, G4, C5

        # Score each candidate
        best_voicing = candidates[0]
        best_score = float('inf')

        for voicing in candidates:
            # Prefer voicings with reasonable spacing
            spacing_penalty = 0
            spans = []

            for i in range(len(voicing) - 1):
                interval = voicing[i + 1] - voicing[i]
                spans.append(interval)
                if interval > 12:
                    spacing_penalty += (interval - 12)
                elif interval < 3:
                    spacing_penalty += (3 - interval) * 2  # Penalize very close voices

            # Calculate variance - prefer even spacing between voices
            if len(spans) > 0:
                mean_span = sum(spans) / len(spans)
                variance = sum((s - mean_span) ** 2 for s in spans) / len(spans)

                # Prefer open position (lower variance, more even spacing)
                score = spacing_penalty + variance * 0.5

                if score < best_score:
                    best_score = score
                    best_voicing = voicing

        return best_voicing
```

### 7. Feedback Analysis Module

```python
# modules/chord_test/feedback_analysis.py
import json
import os
import pandas as pd
import matplotlib.pyplot as plt
from typing import Dict, List, Any

def load_feedback_data(directory="feedback") -> List[Dict[str, Any]]:
    """Load all feedback data from JSONL files."""
    all_feedback = []

    for filename in os.listdir(directory):
        if filename.endswith(".jsonl"):
            with open(os.path.join(directory, filename), "r") as f:
                for line in f:
                    try:
                        feedback = json.loads(line.strip())
                        all_feedback.append(feedback)
                    except json.JSONDecodeError:
                        continue

    return all_feedback

def analyze_feedback(feedback_data: List[Dict[str, Any]]):
    """Analyze feedback data and generate reports."""
    # Convert to pandas DataFrame for analysis
    df = pd.DataFrame(feedback_data)

    # Calculate average ratings by algorithm version
    avg_by_algorithm = df.groupby("algorithm_version")["rating"].mean()

    # Calculate average ratings by cadence type
    avg_by_cadence = df.groupby(["cadence_type", "algorithm_version"])["rating"].mean().unstack()

    # Generate plots
    plt.figure(figsize=(12, 6))

    # Plot average ratings by algorithm version
    plt.subplot(1, 2, 1)
    avg_by_algorithm.plot(kind="bar")
    plt.title("Average Rating by Algorithm Version")
    plt.ylabel("Rating (1-5)")

    # Plot average ratings by cadence type
    plt.subplot(1, 2, 2)
    avg_by_cadence.plot(kind="bar")
    plt.title("Average Rating by Cadence Type")
    plt.ylabel("Rating (1-5)")

    # Save plots
    plt.tight_layout()
    plt.savefig("feedback/analysis_report.png")

    # Return summary stats
    return {
        "total_feedback": len(df),
        "avg_by_algorithm": avg_by_algorithm.to_dict(),
        "avg_by_cadence": avg_by_cadence.to_dict(),
        "common_comments": extract_common_comments(feedback_data)
    }

def extract_common_comments(feedback_data: List[Dict[str, Any]]) -> Dict[str, int]:
    """Extract common themes from feedback comments."""
    # Simple keyword analysis
    keywords = [
        "spacing", "voice leading", "bass", "soprano",
        "leap", "smooth", "awkward", "unmusical", "musical"
    ]

    counts = {keyword: 0 for keyword in keywords}

    for entry in feedback_data:
        if "comments" in entry and entry["comments"]:
            comment = entry["comments"].lower()
            for keyword in keywords:
                if keyword in comment:
                    counts[keyword] += 1

    return counts
```

## Implementation Plan

### Phase 1: Voice Leading Improvements

1. **Create Enhanced Voice Leading Class**
   - Implement `EnhancedVoiceLeader` extending `VoiceLeader`
   - Implement improved transition evaluation
   - Add wider bass range and better spacing rules
   - Add handling for common cadential patterns

2. **Create Enhanced Progression Generator**
   - Implement `EnhancedChordProgressionGenerator` using the enhanced voice leader
   - Add better handling of lead-in to cadence transitions
   - Maintain backward compatibility with existing code

3. **Add Unit Tests**
   - Test for proper voice leading rule enforcement
   - Test for musical quality metrics
   - Test for inversion constraint satisfaction

### Phase 2: Chord Test App Development

1. **Create Basic Test App Structure**
   - Implement `chord_test_app.py` entry point
   - Create UI components for chord generation and playback
   - Reuse existing audio and notation components

2. **Implement Feedback Collection**
   - Add rating scale and comments field
   - Implement feedback storage in JSONL format
   - Create feedback directory structure

3. **Implement A/B Testing**
   - Add toggle for switching between regular and enhanced algorithms
   - Store algorithm version with feedback data
   - Implement blind testing mode (optional)

### Phase 3: Feedback Analysis

1. **Create Analysis Module**
   - Implement feedback data loading and parsing
   - Create basic statistical analysis functions
   - Generate visualizations of ratings

2. **Implement Interactive Analysis**
   - Add ability to filter and sort feedback
   - Create dashboard for viewing feedback trends
   - Implement export for further analysis

## Testing Plan

1. **Voice Leading Validation**
   - Check for absence of parallel fifths and octaves
   - Verify proper resolution of tendency tones
   - Ensure good spacing between voices
   - Confirm bass range is appropriate

2. **Cadence Pattern Testing**
   - Test all four cadence types
   - Verify inversion constraints are satisfied
   - Check that voice leading is musical across transitions
   - Test with and without lead-in chords

3. **Chord Test App Validation**
   - Verify notation display matches generated chords
   - Ensure audio playback works correctly
   - Test feedback submission and storage
   - Verify analysis tools process feedback correctly

## Success Criteria

The implementation will be considered successful if:

1. **Improved Voice Leading**
   - No parallel fifths or octaves
   - More stepwise motion in all voices
   - Better spacing between voices
   - Appropriate bass range and voice ranges
   - Common tone retention where possible
   - Proper resolution of tendency tones

2. **Functional Chord Test App**
   - Generates cadences for all grade levels
   - Displays notation correctly
   - Plays audio accurately
   - Collects and stores feedback reliably
   - Supports A/B testing between algorithms

3. **Useful Feedback Analysis**
   - Provides clear metrics on algorithm performance
   - Identifies common issues in voice leading
   - Shows improvement trends over time
   - Supports data-driven refinement of algorithms

## Implemented Improvements

### Grand Staff Notation with SATB Voice Distribution (Completed January 2026)

The notation system has been updated to display chord progressions using a proper grand staff with correct SATB voice distribution. This implementation addresses two issues from the original plan:
1. Chords now display on both treble and bass clefs (not just treble)
2. Chord symbols are properly aligned with their corresponding chords

#### Files Modified

- **`www/notation.js`** - Main app notation (this is the file loaded by `app.py`)
- **`www/js/cadence/notation.js`** - Cadence module version (not currently loaded, but kept in sync)
- **`www/js/chord_test/notation.js`** - Chord test app notation

#### Key Implementation Details

1. **SATB-Based Voice Distribution** (not MIDI-based):
   - The Python voice leading returns notes in order: `[bass, tenor, alto, soprano]`
   - Notes are split by voice index, NOT by MIDI value:
     - Indices 0, 1 (Bass, Tenor) → Bass clef
     - Indices 2, 3 (Alto, Soprano) → Treble clef
   - This ensures correct notation regardless of actual pitch values

2. **Grand Staff Structure**:
   - Two staves with treble and bass clefs
   - Brace connector on the left
   - Both staves share the same key signature
   - Renderer height increased from 200px to 300px

3. **Chord Symbol Alignment**:
   - Symbols are added as VexFlow `Annotation` modifiers attached to treble notes
   - This ensures symbols are automatically centered above each chord
   - Previously, symbols were manually positioned and misaligned

#### Core Implementation Pattern

```javascript
// Process each chord - SATB order: [bass, tenor, alto, soprano]
// Bass (0) and Tenor (1) go to bass clef
// Alto (2) and Soprano (3) go to treble clef
noteNames.forEach((chord, index) => {
    const formattedNotes = chord.map(formatNoteForVexFlow);

    // Split by voice index (not MIDI value)
    const bassClefNotes = formattedNotes.slice(0, 2);  // bass, tenor
    const trebleClefNotes = formattedNotes.slice(2, 4); // alto, soprano

    // Create treble stave note with chord symbol
    if (trebleClefNotes.length > 0) {
        const trebleNote = new VF.StaveNote({
            clef: "treble",
            keys: trebleClefNotes,
            duration: "w"
        });
        addAccidentals(trebleNote, trebleClefNotes);

        // Add chord symbol as annotation (properly aligned)
        if (chordSymbols && chordSymbols[index]) {
            trebleNote.addModifier(
                new VF.Annotation(chordSymbols[index])
                    .setFont("Arial", 12, "bold")
                    .setVerticalJustification(VF.Annotation.VerticalJustify.TOP),
                0
            );
        }
        trebleNotes.push(trebleNote);
    }

    // Create bass stave note
    if (bassClefNotes.length > 0) {
        const bassNote = new VF.StaveNote({
            clef: "bass",
            keys: bassClefNotes,
            duration: "w"
        });
        addAccidentals(bassNote, bassClefNotes);
        bassNotes.push(bassNote);
    }
});

// Format both voices together so notes align vertically
new VF.Formatter()
    .joinVoices([trebleVoice])
    .joinVoices([bassVoice])
    .format([trebleVoice, bassVoice], width - 60);
```

#### Grand Staff Setup

```javascript
const width = 680;
const trebleY = 30;
const bassY = 130;

// Create staves
const trebleStave = new VF.Stave(10, trebleY, width);
trebleStave.addClef("treble");

const bassStave = new VF.Stave(10, bassY, width);
bassStave.addClef("bass");

// Add key signatures to both
if (key) {
    const vexflowKey = getKeySignature(key);
    trebleStave.addKeySignature(vexflowKey);
    bassStave.addKeySignature(vexflowKey);
}

// Draw staves
trebleStave.setContext(context).draw();
bassStave.setContext(context).draw();

// Add brace and barline connectors
const brace = new VF.StaveConnector(trebleStave, bassStave);
brace.setType(VF.StaveConnector.type.BRACE);
brace.setContext(context).draw();

const lineConnector = new VF.StaveConnector(trebleStave, bassStave);
lineConnector.setType(VF.StaveConnector.type.SINGLE_LEFT);
lineConnector.setContext(context).draw();
```

#### Note on Voice Ranges

The current voice ranges in `modules/music_theory/voice_leading.py` are:
```python
VOICE_RANGES = {
    'bass': (55, 67),      # G3 to G4
    'tenor': (60, 72),     # C4 to C5
    'alto': (64, 76),      # E4 to E5
    'soprano': (67, 79),   # G4 to G5
}
```

These ranges were originally optimized for single-staff treble clef display. With the grand staff implementation, bass notes around G3 will display well on the bass clef, but tenor notes at C4 and above will require ledger lines. This is acceptable for now, but the voice leading improvements in Phase 1 of this plan suggest extending the bass range lower (to E2-C4) for more traditional SATB spacing.

### Remaining Work

The notation improvements are complete. The remaining items from this plan are:

1. **Voice Leading Algorithm Improvements** (Phase 1):
   - Extend voice ranges for better spacing
   - Add rewards for contrary motion, common tone retention, stepwise motion
   - Implement cadence-specific voice leading rules

2. **Chord Test App** (Phase 2):
   - Basic structure exists in `chord_test_app.py`
   - Needs completion of feedback collection system

3. **Feedback Analysis** (Phase 3):
   - Not yet started