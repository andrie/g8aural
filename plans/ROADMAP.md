# G8aural Development Roadmap

## Current Status

G8aural has successfully implemented its core features:

- ✅ Cadence identification (Grades 6-8)
- ✅ Voice singing exercises (Grades 5-8)
- ✅ Bach corpus integration
- ✅ Real-time pitch detection
- ✅ Grade-adaptive user interface
- ✅ Voice leading with inversions
- ✅ Tabbed interface with shared grade selection

## Immediate Priorities

### 1. Voice Singing Enhancements

- **Real-Time Pitch Display**:
  - Live frequency visualization during recording
  - Note reference indicators
  - Countdown timer before recording starts

- **Notation Display**:
  - Show sheet music for melodies using VexFlow
  - Highlight target voice in different color
  - Display key signature

- **Improved Feedback**:
  - More detailed, actionable guidance
  - Section-specific feedback
  - Color-coded pitch plot segments

### 2. Modular Refactoring

The current codebase needs refactoring to improve maintainability and organization:

- **Shiny Module Pattern**:
  - Convert direct imports to proper Shiny modules
  - Create module-specific UI and server functions
  - Separate app.py into smaller, focused modules

- **Directory Reorganization**:
  - Move music theory engine to lib/
  - Group modules by feature area
  - Reorganize JavaScript files by feature

- **State Management**:
  - Continue using reactive dataclasses pattern
  - Improve isolation between module states
  - Add type hints throughout

### 3. UI/UX Improvements

- **Visual Feedback Enhancements**:
  - Add checkmark/cross emoji feedback for buttons
  - Move "Next" button above staff notation
  - Hide hint button after correct answer
  - Disable wrong answer buttons

- **Mobile Optimization**:
  - Improve responsive layout
  - Optimize touch targets
  - Enhance microphone access reliability

## Medium-Term Goals (1-3 months)

### 1. Performance Optimization

- **Lazy Loading**:
  - Only import plotnine when plotting (saves ~2s startup time)
  - Optimize DTW alignment for longer melodies
  - Add caching for repeated melodies

- **JavaScript Improvements**:
  - Move pitch detection to Web Worker
  - Optimize VexFlow rendering
  - Add loading indicators for long operations

### 2. Feature Expansion

- **Difficulty Settings**:
  - Melody length options (4, 8, or 16 bars)
  - Voice pair selection (Soprano+Bass, Soprano+Alto, Tenor+Bass)
  - Tempo options (Slow, Medium, Fast)

- **Progress Tracking**:
  - localStorage-based attempt history
  - Performance trends over time
  - "Best attempt" tracking
  - Weekly/monthly statistics

- **Export Capabilities**:
  - Download recording as WAV file
  - Export pitch plot as PNG
  - Generate PDF practice report

## Long-Term Vision (3-6 months)

### 1. Mobile Strategy

To overcome browser limitations with microphone access, consider:

#### Option 1: API-First Mobile Hybrid Architecture
- Separate backend and frontend components
- React Native mobile apps for reliable microphone access
- FastAPI backend with the music theory engine
- React web frontend for desktop/tablet

#### Option 2: Progressive Web App
- Progressive enhancement techniques
- Service workers for offline functionality
- Fallback recording options
- Local storage for user progress

### 2. Additional Educational Features

- **Rhythm Analysis**:
  - Detect note onset times
  - Compare rhythm accuracy to target
  - Separate pitch and rhythm scores

- **Adaptive Difficulty**:
  - Machine learning to adjust difficulty based on performance
  - Generate melodies targeting user's weak areas
  - Personalized practice recommendations

- **Additional Exercise Types**:
  - Melodic dictation
  - Interval identification
  - Scale recognition
  - Chord quality identification

### 3. Multi-User Features

- **Teacher Dashboard**:
  - Track multiple students
  - Assign specific exercises
  - Generate reports
  - Compare student performance

## Implementation Timeline

### Q1-Q2 2026
- Voice singing enhancements
- Module refactoring
- UI/UX improvements

### Q2-Q3 2026
- Performance optimization
- Progress tracking
- Difficulty settings

### Q3-Q4 2026
- Mobile application development (if Option 1)
- Or Progressive Web App enhancements (if Option 2)
- Additional exercise types

## Technical Debt Areas

- **Code Organization**: Extract functionality into proper modules
- **Test Coverage**: Add UI/integration tests
- **Type Hints**: Complete type annotations throughout codebase
- **Documentation**: Improve inline documentation and README
- **Error Handling**: Add more robust error handling