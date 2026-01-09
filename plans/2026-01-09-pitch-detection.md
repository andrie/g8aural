# Specification: ABRSM Grade 8 Aural Trainer - Voice Singing Module

## 1. Project Objective
Extend the existing **ABRSM Grade 8 Aural Trainer** Shiny application to include a second training mode: **Voice Singing**. This module assesses a user's ability to sing the lower voice of a two-part melody. The app plays a two-part MIDI/audio texture, records the user's singing via the browser, extracts pitch data, and compares it against a ground truth lower-voice reference.

This is a **separate task** from the existing cadence identification module, integrated via **tab navigation**.

## 2. UI Navigation Strategy

### Tab-Based Architecture
Use Shiny's `ui.navset_tab()` to create two distinct training modes:

```python
app_ui = ui.page_fluid(
    ui.tags.head(...),  # Shared CDN resources

    ui.div(
        ui.h1("ABRSM Grade 8 Aural Training"),
        class_="header"
    ),

    ui.navset_tab(
        ui.nav_panel(
            "Cadence Identification",
            # Existing cadence UI content
        ),
        ui.nav_panel(
            "Voice Singing",
            # New pitch detection UI content
        ),
        id="training_mode"
    )
)
```

**Key Benefits:**
- Clear separation of concerns (distinct reactive states per tab)
- Shared infrastructure (music21, Tone.js, VexFlow)
- Natural user flow (switch between training exercises)
- Easy to add future modules (e.g., "Modulation", "Melodic Memory")

### Shared Resources
Both tabs share:
- JavaScript libraries (Tone.js, VexFlow loaded once in `<head>`)
- Music theory engine (`modules/music_theory/`)
- Python dependencies (music21, numpy)
- CSS styles (`www/styles.css`)

### Independent Resources
Each tab has:
- **Cadence Tab**: `www/audio.js`, `www/notation.js`, `www/grade-ui.js`
- **Voice Tab**: `www/microphone.js`, `www/voice-playback.js`, `www/pitch-plot.js` (new)

## 3. Technical Stack

### Existing (Reused)
* **Backend:** Shiny for Python
* **Audio Playback:** Tone.js (already loaded)
* **Music Theory:** music21 (already integrated)
* **Notation Display:** VexFlow (already loaded)

### New Additions
* **Pitch Detection:** [Pitchy](https://github.com/ianprime0509/pitchy) v4.x (MIT license)
  - Load via CDN: `https://cdn.jsdelivr.net/npm/pitchy@4/dist/pitchy.min.js`
* **DTW Alignment:** `fastdtw` Python package
  - Add to requirements.txt: `fastdtw>=0.3.4`
* **Signal Processing:** `scipy` (likely already installed with music21)
* **Visualization:** `plotnine` (Python ggplot2 implementation for elegant pitch contour plots)

---

## 4. Functional Requirements

### A. Melody Generation (Backend - Python)
* **Two-Part Generation:** Extend `ChordProgressionGenerator` to extract two melodic lines:
  ```python
  soprano_melody, bass_melody = generator.extract_voices(
      progression,
      voices=['soprano', 'bass']
  )
  ```
* **Voice Characteristics:**
  - **Soprano (upper)**: Typically MIDI 60-79 (C4-G5)
  - **Bass (lower)**: Typically MIDI 48-67 (C3-G4)
* **Melody Storage:** Store as MIDI note sequences with onset times:
  ```python
  [(midi_note, start_time, duration), ...]
  ```

### B. Multi-Part Playback (Frontend - JavaScript)
* **Stereo Separation:** Use **Tone.js panning** to distinguish voices:
  ```javascript
  const sopranoSynth = new Tone.Synth().toDestination();
  sopranoSynth.pan.value = -0.7;  // Left channel

  const bassSynth = new Tone.Synth().toDestination();
  bassSynth.pan.value = 0.7;      // Right channel
  ```
* **Timbral Distinction:** Use different synthesis types:
  - Soprano: Bright sine wave or filtered sawtooth
  - Bass: Warmer triangle wave or filtered square
* **Control Flow:**
  1. User clicks "Start Task" button
  2. Display 4-beat visual countdown (optional, recommended)
  3. Play both melodies simultaneously
  4. Begin microphone recording concurrently with playback
  5. Continue recording for 2 seconds after playback ends
  6. Stop recording and send data to Python

### C. Real-Time Pitch Extraction (Frontend - JavaScript)
* **Capture:** Access microphone via **Web Audio API**:
  ```javascript
  const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
  const audioContext = new AudioContext({ sampleRate: 44100 });
  const source = audioContext.createMediaStreamSource(stream);
  ```
* **Processing Parameters:**
  ```javascript
  const FFT_SIZE = 2048;           // ~46ms window at 44.1kHz
  const HOP_SIZE = FFT_SIZE / 2;   // 50% overlap for smooth tracking
  const SAMPLE_RATE = 44100;
  ```
* **Pitch Detection with Pitchy:**
  ```javascript
  const detector = Pitchy.PitchDetector.forFloat32Array(FFT_SIZE);
  detector.findPitch(audioBuffer, SAMPLE_RATE);  // Returns [pitch, clarity]
  ```
* **Heuristics for Voice Filtering:**
  * **Clarity Filter:** Accept pitches only when YIN clarity > 0.5 (relaxed from 0.8)
  * **RMS Threshold:** Calculate RMS; reject frames below 0.01 (adaptive noise floor)
  * **Frequency Range:** Accept only 80-800 Hz (singing voice range, filters harmonics)
  * **Rest Handling:** Store `null` for rejected frames to maintain time alignment
* **Data Structure:** Accumulate in array:
  ```javascript
  const recording = [
      { time: 0.046, frequency: 196.0 },    // G3
      { time: 0.093, frequency: null },     // Breath/rest
      { time: 0.140, frequency: 195.8 },    // G3 (continued)
      ...
  ];
  ```
* **Data Transfer:** Send to Python when recording stops:
  ```javascript
  Shiny.setInputValue("recorded_pitch", recording, { priority: "event" });
  ```

### D. Scoring & Analysis (Backend - Python)
* **Ground Truth Conversion:** Convert target bass melody to pitch contour:
  ```python
  def melody_to_pitch_contour(melody, sample_rate=20):
      """Convert [(midi, start, duration)] to time-series [freq, freq, ...]"""
      contour = []
      for midi_note, start_time, duration in melody:
          freq = 440 * 2**((midi_note - 69) / 12)
          num_samples = int(duration * sample_rate)
          contour.extend([freq] * num_samples)
      return np.array(contour)
  ```
* **Signal Cleaning:**
  1. Convert recorded Hz to MIDI: $m = 69 + 12 \cdot \log_2(f/440)$
  2. Remove `null` values (keep time indices for later re-alignment)
  3. Apply **median filter** (window size 5-7) to remove octave jumps:
     ```python
     from scipy.signal import medfilt
     cleaned_midi = medfilt(recorded_midi, kernel_size=5)
     ```
* **Dynamic Time Warping Alignment:**
  ```python
  from fastdtw import fastdtw

  def align_performance(recorded, target):
      """Align recorded to target using DTW with musical distance metric."""
      distance, path = fastdtw(
          recorded.reshape(-1, 1),
          target.reshape(-1, 1),
          radius=20,  # Constraint window (faster computation)
          dist=lambda a, b: abs(a[0] - b[0])  # L1 distance in semitones
      )
      return path, distance
  ```
* **Wrong Voice Detection:**
  ```python
  def detect_voice_error(recorded_midi, soprano_midi, bass_midi):
      """Check if student sang wrong voice (handle octave transposition)."""
      # Use pitch class (mod 12) to handle octave shifts
      recorded_pc = recorded_midi % 12
      soprano_pc = soprano_midi % 12
      bass_pc = bass_midi % 12

      soprano_distance = np.mean(np.min([
          np.abs(recorded_pc - soprano_pc),
          np.abs(recorded_pc - soprano_pc + 12),
          np.abs(recorded_pc - soprano_pc - 12)
      ], axis=0))

      bass_distance = np.mean(np.min([
          np.abs(recorded_pc - bass_pc),
          np.abs(recorded_pc - bass_pc + 12),
          np.abs(recorded_pc - bass_pc - 12)
      ], axis=0))

      if soprano_distance < bass_distance - 1.0:  # 1 semitone margin
          return "soprano", soprano_distance
      else:
          return "bass", bass_distance
  ```
* **Grading (MAE in Cents):**
  ```python
  def grade_performance(recorded_midi, target_midi, aligned_path):
      """Calculate mean absolute error in cents after DTW alignment."""
      aligned_recorded = [recorded_midi[i] for i, j in aligned_path]
      aligned_target = [target_midi[j] for i, j in aligned_path]

      # Convert semitone error to cents (1 semitone = 100 cents)
      error_cents = np.abs(np.array(aligned_recorded) - np.array(aligned_target)) * 100
      mae_cents = np.mean(error_cents)

      return mae_cents
  ```
* **Feedback Thresholds:**
  - 0-25 cents: "Excellent pitch accuracy!"
  - 25-50 cents: "Good, but could be more precise"
  - 50-100 cents: "Pitch needs work - try again"
  - >100 cents: "Many wrong notes - listen again carefully"

---

## 5. Proposed Architecture

### File Structure
```
g8aural/
├── app.py                              # Main app with tab navigation
│   ├── Cadence tab UI (existing)
│   ├── Voice Singing tab UI (new)
│   └── Server logic for both tabs
│
├── modules/
│   └── music_theory/
│       ├── progression.py              # Extend with extract_voices() method
│       ├── voice_analysis.py           # NEW: DTW, median filter, grading
│       └── [existing files unchanged]
│
├── www/
│   ├── audio.js                        # Existing: chord playback
│   ├── notation.js                     # Existing: VexFlow rendering
│   ├── grade-ui.js                     # Existing: grade selection
│   ├── microphone.js                   # NEW: Pitchy + Web Audio API
│   ├── voice-playback.js               # NEW: Two-part melody playback
│   └── styles.css                      # Extend with voice tab styles
│
└── requirements.txt                    # Add: fastdtw>=0.3.4
```

### Module Responsibilities

| File | Responsibility |
| :--- | :--- |
| `app.py` | Tab navigation (`ui.navset_tab`), reactive state for both modes |
| `modules/music_theory/progression.py` | Add `extract_voices()` method to return soprano/bass melodies |
| `modules/music_theory/voice_analysis.py` | DTW alignment, median filtering, wrong-voice detection, grading |
| `www/microphone.js` | Microphone access, Pitchy pitch detection, data streaming to Python |
| `www/voice-playback.js` | Tone.js stereo playback of two-part melodies |
| `www/styles.css` | Add voice tab UI styles (recording indicator, pitch visualization) |

### Reactive State (Voice Tab Only)

```python
# Voice singing tab state (separate from cadence tab)
voice_soprano_melody = reactive.Value(None)      # [(midi, start, duration), ...]
voice_bass_melody = reactive.Value(None)         # [(midi, start, duration), ...]
voice_target_key = reactive.Value(None)          # 'C', 'G', 'd', etc.
voice_recorded_pitch = reactive.Value(None)      # [{time: float, freq: float|null}, ...]
voice_grading_result = reactive.Value(None)      # {mae_cents: float, detected_voice: str, feedback: str}
voice_is_recording = reactive.Value(False)       # Recording status
```

### Data Flow Diagram

```
[User clicks "Start Task"]
        ↓
[Python: Generate soprano + bass melodies]
        ↓
[Python → JS: Send melodies via send_custom_message]
        ↓
[JS: Play melodies with stereo panning + start recording]
        ↓
[JS: Pitchy extracts pitch every 46ms]
        ↓
[JS: Recording stops after playback + 2s buffer]
        ↓
[JS → Python: Send pitch array via Shiny.setInputValue]
        ↓
[Python: DTW alignment + grading]
        ↓
[Python → JS: Send visualization data]
        ↓
[JS: Display pitch contour plot + feedback]
```

### Python-JavaScript Communication

**Python → JavaScript:**
```python
await session.send_custom_message("playVoiceMelody", {
    "soprano": [[60, 0.0, 1.0], [62, 1.0, 1.0], ...],  # (midi, start, duration)
    "bass": [[48, 0.0, 1.0], [50, 1.0, 1.0], ...],
    "key": "C"
})

await session.send_custom_message("displayPitchPlot", {
    "recorded": [196.0, 196.0, null, 220.0, ...],
    "target": [196.0, 196.0, 196.0, 220.0, ...],
    "timestamps": [0.0, 0.046, 0.093, 0.140, ...]
})
```

**JavaScript → Python:**
```javascript
Shiny.setInputValue("recorded_pitch", {
    data: [{time: 0.0, frequency: 196.0}, ...],
    duration: 8.5,
    sample_rate: 21.7  // Actual samples per second
}, { priority: "event" });

Shiny.setInputValue("recording_started", true, { priority: "event" });
Shiny.setInputValue("recording_stopped", true, { priority: "event" });
```

---

## 6. Implementation Constraints & Success Criteria

### Constraints
1. **Browser-Side Pitch Detection:** Pitchy must run in JavaScript to avoid latency from streaming raw audio to the server. Target processing time: <10ms per frame.
2. **Robustness to Gaps:** System must handle breaths, stops, and unvoiced segments without breaking DTW alignment (use `null` values).
3. **Browser Compatibility:**
   - ✅ Chrome/Edge: Full Web Audio API support
   - ✅ Firefox: Full support
   - ⚠️ Safari: Limited (may require user gesture for microphone access)
   - ❌ Mobile browsers: Not prioritized (touch/mic issues)
4. **Real-Time Constraints:**
   - Pitch detection latency: <100ms
   - DTW computation: <500ms for 30-second recordings
   - UI responsiveness: Feedback within 1 second of recording stop

### Success Criteria
1. **Pitch Accuracy:** Detect pitches within ±10 Hz (±30 cents) for test recordings
2. **DTW Alignment:** >90% correct onset matching on validation dataset
3. **Wrong-Voice Detection:** <5% false positive rate (incorrect "wrong voice" flags)
4. **User Experience:**
   - Clear visual feedback during recording (animated indicator)
   - Pitch plot displays within 1 second of recording stop
   - Actionable feedback messages based on MAE thresholds
5. **Performance:** Handle 60-second recordings (longest Grade 8 melodies) without UI freezing

### Visual Feedback Requirements
After recording, display:
1. **Pitch Contour Plot:** Target (blue line) vs. Recorded (red line/dots)
   - X-axis: Time (seconds)
   - Y-axis: Pitch (MIDI note number or note names)
   - Gaps in recording shown as breaks in red line
2. **Alignment Visualization:** Optional heat map showing DTW path
3. **Grading Summary:**
   - MAE in cents
   - Detected voice (soprano/bass)
   - Feedback message
   - "Try Again" button

### Testing Plan
1. **Unit Tests:**
   - `melody_to_pitch_contour()`: Verify correct Hz conversion
   - `detect_voice_error()`: Test octave transposition handling
   - `align_performance()`: Validate DTW on synthetic data
2. **Integration Tests:**
   - Record synthetic audio (pure sine waves) and verify pitch detection
   - Test with intentionally wrong voice (soprano instead of bass)
   - Test with tempo variations (10% faster/slower)
3. **User Testing:**
   - Test with 3-5 Grade 8 students
   - Collect feedback on clarity of feedback messages
   - Measure task completion time and error rate

---

## 7. Implementation Phases

### Phase 1: UI Foundation (Week 1)
**Goal:** Create tab navigation and basic voice singing UI

**Tasks:**
1. Refactor `app.py` to use `ui.navset_tab()`
2. Move existing cadence UI into first tab panel
3. Create voice singing tab with placeholder content:
   - "Start Task" button
   - Recording status indicator
   - Feedback area
4. Add Pitchy CDN to `<head>` section
5. Create empty `www/microphone.js` and `www/voice-playback.js`

**Success Metric:** Both tabs visible and switchable, no functionality yet

---

### Phase 2: Melody Generation (Week 1-2)
**Goal:** Generate two-part melodies from existing progressions

**Tasks:**
1. Create `modules/music_theory/voice_analysis.py` (empty shell)
2. Extend `ChordProgressionGenerator` in `progression.py`:
   ```python
   def extract_voices(self, progression, voices=['soprano', 'bass']):
       """Extract melodic lines from 4-voice progression."""
       # Return [(midi, start_time, duration), ...]
   ```
3. Add reactive state for voice tab in `app.py`
4. Create "Generate Melody" button handler
5. Test generation with print statements (no playback yet)

**Success Metric:** Soprano and bass melodies generated and stored in reactive values

---

### Phase 3: Two-Part Playback (Week 2)
**Goal:** Play soprano and bass with stereo separation

**Tasks:**
1. Implement `www/voice-playback.js`:
   - Create two Tone.js synths with panning
   - Schedule notes from Python melody data
   - Send playback_complete event back to Python
2. Add custom message handler in Python
3. Wire up "Start Task" button to trigger playback
4. Add VexFlow notation display (reuse existing `notation.js`)

**Success Metric:** User hears two distinct melodies, sees notation

---

### Phase 4: Pitch Detection (Week 2-3)
**Goal:** Record microphone and extract pitch in real-time

**Tasks:**
1. Implement `www/microphone.js`:
   - Request microphone access
   - Set up Web Audio API nodes
   - Initialize Pitchy detector
   - Process audio buffers (46ms windows)
   - Apply clarity/RMS/frequency filters
   - Accumulate pitch data array
2. Start recording simultaneously with playback
3. Stop recording 2s after playback ends
4. Send pitch array to Python via `Shiny.setInputValue`
5. Display raw pitch data as JSON (debugging)

**Success Metric:** Python receives pitch array, displays in feedback area

---

### Phase 5: DTW Alignment & Grading (Week 3-4)
**Goal:** Align recorded pitch to target and calculate score

**Tasks:**
1. Implement in `modules/music_theory/voice_analysis.py`:
   - `melody_to_pitch_contour()`
   - `hz_to_midi()` and `apply_median_filter()`
   - `align_performance()` (FastDTW wrapper)
   - `detect_voice_error()` (octave-aware)
   - `grade_performance()` (MAE in cents)
2. Add `fastdtw` to `requirements.txt`
3. Create Python event handler for `input.recorded_pitch()`
4. Display grading result as text feedback

**Success Metric:** User sees MAE cents and voice detection result

---

### Phase 6: Visualization (Week 4)
**Goal:** Display pitch contour plot using plotnine

**Tasks:**
1. Implement `plotnine` pitch visualization in `voice_analysis.py`:
   ```python
   from plotnine import ggplot, aes, geom_line, geom_point, labs, theme_minimal

   def create_pitch_plot(recorded, target, timestamps):
       """Generate pitch contour plot as base64 image."""
       # Create dataframe with target and recorded data
       # Plot target as blue line, recorded as red points
       # Handle gaps (null values) in recorded data
       # Return base64-encoded PNG
   ```
2. Add `plotnine` to requirements.txt
3. Send base64 image to JavaScript via custom message
4. Display in UI as `<img>` tag
5. Add x-axis (time in seconds) and y-axis (note names: C4, D4, E4...)
6. Style plot with `theme_minimal()` for clean appearance

**Success Metric:** User sees visual comparison of target vs. performance

---

### Phase 7: Polish & Testing (Week 4-5)
**Goal:** Improve UX and validate accuracy

**Tasks:**
1. Add countdown before recording (4-beat metronome)
2. Improve feedback messages (use thresholds from spec)
3. Add "Try Again" button to replay/re-record
4. Style recording indicator (pulsing red dot)
5. Run unit tests (synthetic data)
6. Run integration tests (real recordings)
7. User testing with Grade 8 students
8. Performance optimization (if needed)

**Success Metric:** Smooth user experience, <5% error rate on validation set

---

## 8. MVP Design Decisions

**Focus:** Get to a working prototype quickly. Advanced features come later.

### Decisions Made

1. **Melody Length:** ✅ **4 bars (~8 seconds)**
   - Easier for beginners
   - Faster testing and iteration
   - Future: Add difficulty slider (4/8/16 bars)

2. **Visualization Library:** ✅ **plotnine**
   - Python ggplot2 implementation (elegant, familiar syntax)
   - Server-side rendering to base64 PNG
   - Clean, publication-quality plots with minimal code
   - Future: Consider interactive plots with Plotly if needed

3. **Real-Time Pitch Display:** ✅ **Not for MVP**
   - Focus on post-recording analysis first
   - Reduces technical complexity
   - Future: Add as "Expert Mode" with live tuner

4. **Microphone Calibration:** ✅ **Fixed threshold (0.01 RMS)**
   - Works for most microphones
   - Simpler implementation
   - Future: Add dynamic calibration in Phase 7 polish

5. **Multiple Attempts Tracking:** ✅ **Not for MVP**
   - Focus on core functionality first
   - Future: Add localStorage-based progress tracking

---

## 9. Risk Mitigation

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Browser mic permission denied | Medium | High | Clear instructions, test button to request permission early |
| Pitchy accuracy insufficient | Medium | High | Validate with test recordings, adjust clarity threshold, consider backup detector (Aubio.js) |
| DTW too slow (>1s latency) | Low | Medium | Downsample pitch contour (50Hz → 10Hz), use FastDTW radius constraint |
| Octave detection errors | High | Medium | Implement robust octave-invariant pitch class matching |
| Safari compatibility issues | Medium | Low | Test on Safari, document limitations, prioritize Chrome/Firefox |
| User confusion about feedback | Medium | Medium | User testing in Phase 7, iterate on messaging |

---

## 10. Future Enhancements (Post-MVP)

1. **Additional Voice Pairs:**
   - Soprano + Alto
   - Tenor + Bass
   - All four SATB voices (user selects which to sing)

2. **Difficulty Levels:**
   - Beginner: 4 bars, slower tempo, simple melodies
   - Intermediate: 8 bars, moderate tempo (current)
   - Advanced: 16 bars, complex rhythms, modulations

3. **Real-Time Feedback:**
   - Live pitch display during recording
   - Visual tuner (sharp/flat indicators)

4. **Progress Tracking:**
   - Save attempt history in localStorage
   - Show improvement over time (MAE trend chart)
   - Leaderboard (optional, for classroom use)

5. **Export Capabilities:**
   - Download recording as .wav
   - Export pitch plot as .png
   - Generate practice report PDF

6. **Advanced Analysis:**
   - Rhythm accuracy (not just pitch)
   - Vibrato detection and analysis
   - Onset/offset timing precision

7. **Accessibility:**
   - Keyboard shortcuts (space = play/record)
   - Screen reader support
   - High-contrast mode

---

## 11. Summary & Next Steps

This specification extends the ABRSM Grade 8 Aural Trainer with a voice singing module using tab-based navigation. The design leverages existing infrastructure (music21, Tone.js, VexFlow) while adding pitch detection (Pitchy) and DTW alignment (fastdtw).

**Key Design Decisions (MVP-Focused):**
- ✅ Separate tab using `ui.navset_tab()` (clean separation)
- ✅ Browser-side pitch detection with Pitchy (low latency)
- ✅ DTW alignment with fastdtw (handles tempo variation)
- ✅ Octave-invariant voice detection (robust to transposition)
- ✅ plotnine visualization (elegant, Pythonic plots)
- ✅ 4-bar melodies (simpler, faster iteration)
- ✅ Post-recording analysis only (no real-time display)
- ✅ Phased implementation (7 phases over 4-5 weeks)

**New Dependencies:**
Add to `requirements.txt`:
```
fastdtw>=0.3.4
plotnine>=0.10.0
```

**Immediate Next Steps:**
1. ✅ Review and approve this specification
2. Create beads issues for each implementation phase
3. Set up dependencies:
   ```bash
   pip install fastdtw plotnine
   # Test Pitchy CDN loads: https://cdn.jsdelivr.net/npm/pitchy@4/dist/pitchy.min.js
   ```
4. Begin Phase 1: UI Foundation (refactor to tabs)

**Success Criteria for MVP:**
- User can sing bass voice of 4-bar two-part melody
- System detects pitch with <30 cent accuracy
- DTW aligns performance despite tempo variation (±10%)
- Grading provides actionable feedback (MAE in cents + voice check)
- plotnine pitch plot displays target (blue) vs. recorded (red) contour
- Overall task completion time: <2 minutes per melody
- Works in Chrome/Firefox (Safari optional for MVP)

**Future Enhancements (Post-MVP):**
See Section 10 for full list including:
- Longer melodies (8/16 bars)
- Real-time pitch display
- Progress tracking
- Interactive plotly visualizations
- Additional voice pairs (soprano+alto, tenor+bass)