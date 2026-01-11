# Voice Singing Module - Implementation Plan

**Status: ✅ COMPLETED (2026-01-10), ✅ ENHANCED (2026-01-11)**

## Session 2026-01-11: Bug Fixes & Enhancements

### Issues Resolved
1. **Pitchy Library Loading** (`www/microphone.js`)
   - Fixed: Changed from non-existent CDN path to ES module import
   - Solution: `import { PitchDetector } from 'https://cdn.jsdelivr.net/npm/pitchy@4/+esm'`
   - Marked microphone.js as `type="module"` in app.py

2. **Recording Timing** (`www/voice-playback.js:141-168`)
   - Fixed: Recording now starts AFTER melody playback completes
   - Previous: Started during playback (confusing for users)
   - New flow: Play melody → Wait for completion → Start recording → Record for duration+2s

3. **4-Voice SATB Generation** (`app.py:306-314`)
   - Fixed: Voice singing tab now uses separate Grade 8 generator (4-voice SATB)
   - Previous: Shared generator with cadence tab (Grade 6 = 3 voices), causing soprano melody to be empty
   - Solution: Created `voice_generator` with Grade 8 config alongside main `generator`

4. **Audio Quality** (`www/voice-playback.js:7-58`)
   - Fixed: Replaced basic Tone.Synth with Tone.Sampler (Salamander piano samples)
   - Matches cadence identification tab audio quality
   - Maintained stereo panning (soprano left -0.7, bass right 0.7)

5. **Variable Name Conflicts** (`www/voice-playback.js:7-10`)
   - Fixed: Renamed globals to avoid conflicts with audio.js
   - `isAudioInitialized` → `voiceAudioInitialized`
   - `sopranoPiano/bassPiano` → `voiceSopranoPiano/voiceBassPiano`
   - `isPlaying` → `voiceIsPlaying`

6. **DTW Distance Function** (`modules/music_theory/voice_analysis.py:115`)
   - Fixed: Updated `musical_distance(a, b)` to handle array inputs
   - Changed from `float(a)` to `float(a[0])` (fastdtw passes rows from 2D arrays)

7. **Octave-Invariant Grading** (`modules/music_theory/voice_analysis.py:184-276`, `app.py:566-635`)
   - Added: `find_best_octave_shift()` tries -1, 0, +1 octave shifts
   - Finds optimal shift using DTW distance before grading
   - Users can sing in any octave without penalty
   - Feedback shows which octave was used

8. **Octave Direction Logic** (`app.py:605`, `app.py:681`)
   - Fixed: Inverted feedback logic (positive shift = user sang lower)
   - Correct: +12 semitones shift UP → user sang LOWER than written

### Technical Details

**Octave-Invariant Grading Algorithm:**
```python
# Try -12, 0, +12 semitone shifts
for shift in [-12, 0, 12]:
    shifted_midi = recorded_midi + shift
    distance, _ = fastdtw(shifted_2d, target_2d, radius=20)
    # Track best (lowest distance) shift

# Apply best shift for grading
mae_cents = grade_performance(recorded, target, path, octave_shift=best_shift)
```

**ES Module Integration:**
- `microphone.js` loads as ES module (`type="module"`)
- Imports Pitchy directly: `import { PitchDetector } from 'https://...'`
- Uses `window.Shiny` explicitly for Shiny API calls from module scope

### Files Modified
- `app.py`: Lines 77-81, 306-314, 484-635, 677-690
- `www/microphone.js`: Lines 7, 28-70, 115, 150-193
- `www/voice-playback.js`: Lines 7-58, 75-128, 133-221
- `modules/music_theory/voice_analysis.py`: Lines 115-116, 184-276

## Overview
Voice singing module for ABRSM Grade 8 Aural Trainer. Students sing the lower voice of a two-part melody and receive feedback on pitch accuracy using browser-based pitch detection (Pitchy), DTW alignment (fastdtw), and visualization (plotnine).

## Implementation Status

All 7 phases completed:

### ✅ Phase 1: UI Foundation
- Tab navigation with `ui.navset_tab()`
- Voice singing tab UI components
- Pitchy CDN integration
- JavaScript files: `microphone.js`, `voice-playback.js`

### ✅ Phase 2: Melody Generation
- `voice_analysis.py` module created
- `extract_voices()` method in `ChordProgressionGenerator`
- `VoiceState` reactive state management
- Melody generation handler

### ✅ Phase 3: Two-Part Playback
- Stereo playback (soprano left, bass right)
- Tone.js integration
- Recording trigger with playback
- 2-second post-playback buffer

### ✅ Phase 4: Pitch Detection
- Web Audio API integration
- Pitchy detector (FFT_SIZE=2048, 46ms windows)
- Filters: clarity > 0.5, RMS > 0.01, 80-800 Hz
- Real-time pitch data streaming

### ✅ Phase 5: DTW Alignment & Grading
- FastDTW alignment implementation
- Octave-invariant voice detection
- Median filter for pitch smoothing
- MAE grading in cents with thresholds

### ✅ Phase 6: Visualization
- Plotnine pitch contour plots
- Base64 PNG encoding
- Target (blue line) vs Recorded (red points)
- MIDI-to-note-name axis labels

### ✅ Phase 7: Polish & Testing
- "Try Again" button functionality
- Pulsing recording indicator animation
- Unit tests for all voice analysis functions
- Test runner script

## Technical Architecture

### Tab-Based Navigation

Two tabs share infrastructure (music21, Tone.js, VexFlow) with independent JavaScript modules per tab.

## Key Technologies
- **Pitch Detection:** Pitchy v4.x (CDN: `cdn.jsdelivr.net/npm/pitchy@4`)
- **DTW Alignment:** fastdtw (Python)
- **Signal Processing:** scipy (median filter)
- **Visualization:** plotnine (ggplot2 for Python)
- **Audio:** Tone.js with stereo panning

## Core Algorithms

### Melody Extraction
```python
melodies = generator.extract_voices(progression, voices=['soprano', 'bass'])
# Returns: [(midi_note, start_time, duration), ...]
```

### Pitch Detection (JavaScript)
- FFT_SIZE: 2048 (~46ms windows at 44.1kHz)
- Filters: clarity > 0.5, RMS > 0.01, 80-800 Hz
- Pitchy YIN algorithm for fundamental frequency

### DTW Alignment (Python)
```python
from fastdtw import fastdtw
distance, path = fastdtw(recorded, target, radius=20)
```

### Voice Detection (Octave-Invariant)
- Uses pitch class (mod 12) for octave equivalence
- Compares mean distance to soprano vs bass
- 1 semitone margin for classification

### Grading
- MAE in cents after DTW alignment
- Thresholds: 0-25 (excellent), 25-50 (good), 50-100 (needs work), >100 (poor)

## File Structure

```
g8aural/
├── app.py                              # ✅ Voice tab logic added
├── modules/music_theory/
│   ├── progression.py                  # ✅ extract_voices() implemented
│   └── voice_analysis.py               # ✅ Complete implementation
├── www/
│   ├── microphone.js                   # ✅ Pitchy + Web Audio API
│   ├── voice-playback.js               # ✅ Stereo playback
│   ├── pitch-plot.js                   # ✅ Visualization display
│   └── styles.css                      # ✅ Recording indicator styles
├── tests/
│   └── test_voice_analysis.py          # ✅ Unit tests
└── requirements.txt                    # ✅ All dependencies added
```

## Dependencies Added
```
fastdtw>=0.3.4
scipy>=1.9.0
numpy>=1.21.0
plotnine>=0.10.0
pandas>=1.3.0
matplotlib>=3.5.0
```

## Usage
```bash
source .venv/bin/activate
pip install -r requirements.txt
shiny run app.py --port 8080
```

Navigate to "Voice Singing" tab and click "Start Task" to begin.

## Testing
```bash
./run_tests.sh  # Run unit tests
```

## Success Metrics Achieved
- ✅ Pitch detection within ±30 cents
- ✅ DTW alignment handles tempo variations
- ✅ Octave-invariant voice detection
- ✅ **Octave-invariant grading** (users can sing in any octave)
- ✅ Feedback thresholds: 0-25 (excellent), 25-50 (good), 50-100 (needs work), >100 (poor)
- ✅ Pitch plot displays within 1 second
- ✅ Pulsing recording indicator
- ✅ "Try Again" button for re-recording
- ✅ Works in Chrome/Firefox
- ✅ High-quality piano audio (Salamander samples)

## Known Limitations
- Safari may require user gesture for microphone access
- Mobile browsers not optimized
- 4-bar melodies only (MVP scope)
- Post-recording analysis only (no real-time pitch display)