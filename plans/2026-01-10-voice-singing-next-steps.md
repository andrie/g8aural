# Voice Singing Module - Next Steps & Enhancements

**Date:** 2026-01-10
**Status:** Recommendations for post-MVP improvements

## Immediate Priorities (Next Session)

### 1. Real-World Testing & Bug Fixes
**Estimated Effort:** 2-4 hours

**Tasks:**
- Test with actual microphone recordings in browser
- Verify pitch detection accuracy with real singing voices
- Test edge cases:
  - Very quiet singing (low RMS)
  - Breathy voice (low clarity)
  - Quick ornaments/vibrato
  - Octave transpositions (intentional and unintentional)
- Fix any issues discovered during testing

**Success Criteria:**
- Successfully records and grades 5 different singers
- <10% false positive rate on wrong voice detection
- Grading correlates with subjective accuracy assessment

### 2. Add Notation Display
**Estimated Effort:** 1-2 hours

The voice singing tab should display sheet music for the melody using VexFlow (already loaded). This helps students learn the melody visually.

**Tasks:**
- Reuse existing `notation.js` for VexFlow rendering
- Add `voice-notation-container` display logic
- Show notation after "Start Task" is clicked
- Highlight bass voice in different color
- Display key signature

**Files to Modify:**
- `www/voice-playback.js` - trigger notation display
- Add custom message handler for `renderVoiceMelody`

### 3. Install Missing Dependencies
**Estimated Effort:** 15 minutes

```bash
source .venv/bin/activate
pip install -r requirements.txt
```

Verify all new packages install correctly:
- fastdtw
- scipy
- plotnine
- pandas
- matplotlib

## Short-Term Enhancements (1-2 weeks)

### 4. Add Countdown Timer
**Estimated Effort:** 2-3 hours

Add a 4-beat visual countdown before recording starts. This gives students time to prepare.

**Implementation:**
- Create countdown animation (4...3...2...1...Start!)
- Display in modal or overlay
- Use metronome clicks (optional audio cues)
- Start playback immediately after countdown

**Files to Create/Modify:**
- `www/voice-playback.js` - add countdown logic
- `www/styles.css` - countdown animation styles

### 5. Improve Feedback Messages
**Estimated Effort:** 1 hour

Current feedback is basic. Add more detailed, actionable guidance.

**Enhanced Feedback Examples:**
- "Good pitch on most notes, but you went sharp on the 3rd note"
- "You started well but lost pitch accuracy toward the end"
- "Try singing more loudly - many notes were too quiet to detect"

**Implementation:**
- Analyze error distribution across time
- Identify problematic sections
- Add section-by-section feedback
- Color-code pitch plot segments (green=good, yellow=ok, red=needs work)

### 6. Add Difficulty Settings
**Estimated Effort:** 3-4 hours

Allow users to choose melody length and complexity.

**Settings:**
- **Melody Length:** 4, 8, or 16 bars
- **Voice Pair:** Soprano+Bass (default), Soprano+Alto, Tenor+Bass
- **Tempo:** Slow (80 BPM), Medium (100 BPM), Fast (120 BPM)

**Implementation:**
- Add UI controls for settings
- Modify `generate_voice_melody()` to respect settings
- Adjust note duration based on tempo
- Store user preferences in localStorage

## Medium-Term Features (1-2 months)

### 7. Real-Time Pitch Display
**Estimated Effort:** 1-2 weeks

Show live pitch while recording (like a tuner app).

**Features:**
- Real-time pitch needle/bar display
- Color indicator: green (in tune), yellow (slightly off), red (off)
- Target pitch reference line
- Rolling window of recent pitches

**Technical Approach:**
- Display pitch in `microphone.js` during recording
- Use requestAnimationFrame for smooth updates
- Add toggle to enable/disable (may be distracting for beginners)

### 8. Progress Tracking & History
**Estimated Effort:** 1 week

Track user progress over time.

**Features:**
- localStorage-based attempt history
- Show improvement trend (MAE over time)
- "Best attempt" vs "Current attempt" comparison
- Weekly/monthly statistics

**Data Structure:**
```javascript
{
  attempts: [
    {
      timestamp: "2026-01-10T10:30:00Z",
      cadenceType: "perfect",
      key: "C",
      maeGents: 35.2,
      detectedVoice: "bass",
      duration: 8.5
    },
    ...
  ]
}
```

### 9. Export Capabilities
**Estimated Effort:** 1 week

Allow users to download recordings and reports.

**Features:**
- Download recording as WAV file
- Export pitch plot as PNG
- Generate PDF practice report with:
  - Pitch plot
  - Grading summary
  - Feedback notes
  - Timestamp

**Technical Approach:**
- Use MediaRecorder API for WAV export
- plotnine already generates PNG (just need download button)
- Use reportlab or weasyprint for PDF generation

### 10. Advanced Voice Detection
**Estimated Effort:** 1-2 weeks

Improve voice detection accuracy and add confidence scores.

**Enhancements:**
- Calculate confidence score for voice detection
- Handle ambiguous cases (e.g., singing between soprano and bass)
- Add "Unknown voice" category for very inaccurate singing
- Use harmonic analysis to detect voice timbre differences

## Long-Term Vision (3-6 months)

### 11. Rhythm Analysis
**Current Scope:** Pitch only
**Future:** Add rhythm/timing accuracy

**Features:**
- Detect note onset times
- Compare onset timing to target
- Calculate rhythm accuracy score separate from pitch
- Provide feedback on rushed/dragged notes

### 12. Adaptive Difficulty
Use machine learning to adjust difficulty based on user performance.

**Approach:**
- Track user success rate per difficulty level
- Automatically suggest easier/harder exercises
- Generate melodies targeting user's weak areas
- Provide personalized practice recommendations

### 13. Multi-User & Classroom Mode
**For Teachers/Schools:**
- Teacher dashboard to track multiple students
- Assign specific exercises to students
- Compare student performance
- Generate class reports
- Leaderboard (optional, gamification)

### 14. Mobile App Version
**Native Apps:**
- iOS: Swift + Core Audio + AVFoundation
- Android: Kotlin + AudioRecord + MediaExtractor
- Share backend logic (music generation, grading)
- Optimize UI for touch interfaces

## Technical Debt & Refactoring

### Code Organization
- **Extract grading logic:** Move grading handler to separate function (currently inline)
- **Create voice tab module:** Move voice tab logic to `handlers/voice_logic.py`
- **Refactor pitch plot:** Extract plotting code to dedicated module
- **Add type hints:** Complete type annotations for voice_analysis.py

### Performance Optimization
- **Lazy load plotnine:** Only import when plotting (saves ~2s startup time)
- **Cache melodies:** Avoid regenerating same progression for "Try Again"
- **Optimize DTW:** Profile and optimize alignment for longer melodies
- **Web Worker pitch detection:** Move pitch detection to background thread

### Testing Improvements
- **Integration tests:** Add end-to-end tests with synthetic audio
- **Mock tests:** Mock microphone input for CI/CD
- **Performance tests:** Measure DTW latency for various melody lengths
- **Browser compatibility tests:** Automated tests for Chrome, Firefox, Safari

## Open Questions & Trade-offs

### Question 1: Real-Time vs Post-Recording Analysis
**Current:** Post-recording only
**Trade-off:**
- Real-time: More engaging, immediate feedback, but complex UI and potential distraction
- Post-recording: Simpler, clearer visualization, less cognitive load during singing

**Recommendation:** Keep post-recording as default, add real-time as optional "Expert Mode"

### Question 2: Strict vs Forgiving Grading
**Current:** Strict (MAE in cents, no leniency)
**Trade-off:**
- Strict: Better for advanced students, objective measurement
- Forgiving: More encouraging for beginners, accounts for recording artifacts

**Recommendation:** Add difficulty-based grading curves (beginners get wider thresholds)

### Question 3: Audio Recording Storage
**Current:** No storage (pitch data only)
**Trade-off:**
- Store audio: Allows playback review, better debugging, but privacy concerns and storage costs
- Pitch data only: Lightweight, privacy-friendly, but can't review actual singing

**Recommendation:** Add opt-in audio recording with clear privacy notice and local-only storage

### Question 4: Voice Pair Selection
**Current:** Always soprano + bass
**Options:**
1. User selects voice pair (soprano+alto, tenor+bass)
2. Automatically vary based on user's vocal range
3. Let user select which voice to sing (soprano or bass)

**Recommendation:** Start with #3 (most flexible), then add #1 for variety

## Dependencies for Future Work

### New Python Packages
```
# Rhythm analysis
librosa>=0.9.0  # Audio feature extraction

# PDF export
reportlab>=3.6.0  # PDF generation

# Performance optimization
numba>=0.56.0  # JIT compilation for DTW
```

### New JavaScript Libraries
```html
<!-- Real-time pitch display -->
<script src="https://cdn.jsdelivr.net/npm/chart.js@4"></script>

<!-- Audio recording export -->
<!-- (Use built-in MediaRecorder API) -->
```

## Resources & References

### Similar Projects
- [SingScope](https://www.singscope.com/) - Professional singing analysis
- [Vocal Pitch Monitor](https://github.com/cutelabnyc/vocal-pitch-monitor) - Open source pitch tracker
- [Praat](https://www.fon.hum.uva.nl/praat/) - Phonetics analysis software

### Research Papers
- Müller, M. (2007). "Information Retrieval for Music and Motion" - DTW algorithms
- de Cheveigné, A. & Kawahara, H. (2002). "YIN: A fundamental frequency estimator" - Pitch detection

### Documentation
- [Web Audio API](https://developer.mozilla.org/en-US/docs/Web/API/Web_Audio_API)
- [Pitchy Library](https://github.com/ianprime0509/pitchy)
- [FastDTW Paper](https://cs.fit.edu/~pkc/papers/tdm04.pdf)

## Summary

The Voice Singing Module MVP is complete and functional. Immediate priorities focus on real-world testing and bug fixes. Short-term enhancements will improve UX with countdown timers, better feedback, and difficulty settings. Long-term vision includes rhythm analysis, adaptive difficulty, and multi-user support.

**Recommended Next Session:**
1. Test with real microphone recordings (30 min)
2. Fix any bugs discovered (1-2 hours)
3. Add notation display (1-2 hours)
4. Create issues for remaining enhancements

**Total Estimated Effort for Next Iteration:** 4-8 hours
