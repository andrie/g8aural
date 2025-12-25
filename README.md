# ABRSM Grade 8 Cadence Training - Frontend (Shiny for Python)

## Overview

This is the Shiny for Python frontend for the ABRSM Grade 8 cadence training application. It provides an interactive web interface for students to practice identifying cadences by ear.

## Features

- **Interactive Audio Playback**: Play cadence progressions using Tone.js
- **Visual Notation Display**: See the musical notation after correct answers using VexFlow
- **Real-time Feedback**: Immediate validation of student guesses
- **Responsive Design**: Works on desktop and mobile devices
- **Progress Tracking**: Statistics on correct/incorrect attempts

## Prerequisites

- Python 3.12+
- Backend server running on http://localhost:8000
- Modern web browser (Chrome, Firefox, Safari, or Edge)

## Installation

### 1. Create Virtual Environment

```bash
cd /home/andrie/wsl-github/g8aural/frontend
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install Dependencies

```bash
.venv/bin/pip install -r requirements.txt
```

## Running the Application

### 1. Start the Backend Server (Terminal 1)

```bash
cd /home/andrie/wsl-github/g8aural/backend
source .venv/bin/activate
.venv/bin/uvicorn app.main:app --reload --port 8000
```

### 2. Start the Shiny Frontend (Terminal 2)

```bash
cd /home/andrie/wsl-github/g8aural/frontend
source .venv/bin/activate
shiny run --reload --port 8080 app.py
```

### 3. Access the Application

Open your browser to: http://localhost:8080

## Architecture

### Technology Stack

- **Framework**: Shiny for Python (reactive web framework)
- **Audio**: Tone.js (JavaScript audio library)
- **Notation**: VexFlow (JavaScript music notation library)
- **Backend Communication**: httpx (async HTTP client)
- **State Management**: Shiny reactive values

### File Structure

```
frontend/
├── app.py                      # Main Shiny application
├── requirements.txt            # Python dependencies
├── modules/
│   ├── __init__.py
│   └── api_client.py          # Backend API communication
└── www/
    ├── styles.css             # Custom CSS styling
    ├── audio.js               # Tone.js audio playback logic
    └── notation.js            # VexFlow notation rendering logic
```

## How It Works

### 1. Application Flow

1. User clicks "Play Cadence" button
2. Frontend requests new cadence from backend API
3. Audio module plays the progression using Tone.js
4. User selects cadence type (Perfect, Plagal, Imperfect, or Interrupted)
5. Frontend validates guess against backend
6. If correct, notation is displayed using VexFlow
7. User can proceed to next cadence

### 2. API Integration

#### Generate Cadence Endpoint

```python
# Endpoint: POST /api/cadence/generate
# Response:
{
    "session_id": "uuid-string",
    "cadence_type": "hidden",  # Always "hidden" - not revealed to frontend
    "progression": [[60, 64, 67], [67, 71, 74], ...],  # MIDI notes
    "chord_symbols": ["I", "V", "I"]
}
```

#### Check Guess Endpoint

```python
# Endpoint: POST /api/cadence/check
# Request:
{
    "session_id": "uuid-string",
    "guess": "perfect"  # One of: perfect, plagal, imperfect, interrupted
}

# Response:
{
    "correct": true,
    "message": "Correct! This is a perfect cadence.",
    "cadence_type": "perfect"  # Only revealed when correct
}
```

### 3. Shiny-JavaScript Communication

#### Python to JavaScript

```python
# Send message to JavaScript
await session.send_custom_message("playProgression", {
    "progression": [[60, 64, 67], [67, 71, 74]]
})
```

#### JavaScript to Python

```javascript
// Send message to Python
Shiny.setInputValue("playback_complete", Math.random(), { priority: "event" });
```

## MIDI Reference

### C Major Scale MIDI Numbers

- C4 (Middle C) = 60
- D4 = 62
- E4 = 64
- F4 = 65
- G4 = 67
- A4 = 69
- B4 = 71
- C5 = 72

### Common C Major Chords

- **I (C major)**: [60, 64, 67]
- **ii (D minor)**: [62, 65, 69]
- **IV (F major)**: [65, 69, 72]
- **V (G major)**: [67, 71, 74]
- **vi (A minor)**: [69, 72, 76]

## Development

### Debugging

#### Enable Shiny Debug Logging

```bash
shiny run --reload --log-level debug app.py
```

#### Check Browser Console

Open browser developer tools (F12) to see:
- JavaScript errors
- Audio initialization messages
- Network requests to backend API
- VexFlow rendering logs

#### Verify Backend Connection

```bash
# Test backend health endpoint
curl http://localhost:8000/api/health

# Test cadence generation
curl -X POST http://localhost:8000/api/cadence/generate -H "Content-Type: application/json" -d "{}"
```

## Troubleshooting

### Common Issues

#### 1. Shiny app won't start

- **Solution**: Verify virtual environment is activated
  ```bash
  source .venv/bin/activate
  pip list | grep shiny
  ```
- Check for Python syntax errors in app.py

#### 2. Backend connection fails

- **Error**: `Error loading cadence: Connection refused`
- **Solution**: Ensure backend is running on port 8000
  ```bash
  curl http://localhost:8000/api/health
  ```

#### 3. Audio doesn't play

- **Solution**: Check browser console for JavaScript errors
- Verify Tone.js CDN is accessible: https://cdnjs.cloudflare.com/ajax/libs/tone/14.8.49/Tone.js
- Try a different browser (Chrome recommended)
- Check browser autoplay policy (user interaction required)

#### 3a. AudioContext warning in console (NORMAL - Can be ignored)

- **Warning**: `"An AudioContext was prevented from starting automatically..."`
- **This is completely normal!** Modern browsers prevent audio from auto-playing without user interaction (security feature)
- The app handles this correctly - audio starts when you click "Play Cadence"
- This warning appears on page load but doesn't affect functionality
- No action needed - the audio will work perfectly when you click the button

#### 4. Notation doesn't render

- **Solution**: Check browser console for VexFlow errors
- Verify VexFlow CDN is accessible: https://cdn.jsdelivr.net/npm/vexflow@4.2.2/build/cjs/vexflow.js
- Inspect that `#notation-container` element exists
- Check for MIDI conversion errors

#### 5. Buttons don't respond

- **Solution**: Check Shiny reactive values are updating
- Verify button IDs match between Python and JavaScript
- Look for JavaScript errors in browser console
- Test with Shiny reactive log: `shiny run --reload --log-level debug`

#### 6. Port already in use

```bash
# Find and kill process on port 8080
lsof -i :8080
kill -9 <PID>

# Or use different port
shiny run --port 8081 app.py
```

## Testing

### Manual Testing Checklist

- [ ] App starts without errors
- [ ] UI renders correctly on load
- [ ] "Play Cadence" button plays audio
- [ ] Audio playback completes without errors
- [ ] Answer buttons enable after playback
- [ ] Correct guesses show notation
- [ ] Incorrect guesses allow retry
- [ ] "Next Cadence" button loads new progression
- [ ] All four cadence types work correctly
- [ ] Notation displays chord symbols
- [ ] Final two chords are highlighted in blue
- [ ] Responsive design works on mobile

### Testing Strategy

1. Test backend API independently first
2. Test Shiny UI without JavaScript initially
3. Test JavaScript modules with browser console
4. Use Shiny's reactive log for debugging
5. Test audio/notation with hardcoded data before full integration
6. Use browser Network tab to verify API calls

## Deployment

### Production Considerations

1. **Environment Variables**: Set `BACKEND_URL` in `modules/api_client.py`
2. **HTTPS**: Use HTTPS for production deployment
3. **CDN Fallbacks**: Consider hosting Tone.js and VexFlow locally
4. **Error Logging**: Implement proper error tracking
5. **Performance**: Enable Shiny caching where appropriate

### Deployment Options

- **Shiny Server**: Deploy to Posit Shiny Server
- **ShinyApps.io**: Deploy to Posit's cloud platform
- **Docker**: Containerize with Docker Compose
- **Cloud Platforms**: AWS, Google Cloud, Azure

## Advantages of Shiny for Python

1. **Reactive Programming**: Automatic UI updates when state changes
2. **Python Integration**: Direct access to Python ecosystem
3. **Less Boilerplate**: Simpler than managing raw HTML/JS state
4. **Built-in Session Management**: No manual session handling needed
5. **Hot Reload**: Automatic reload during development
6. **Type Safety**: Python type hints for better code quality
7. **Easy Deployment**: Simple deployment to various platforms

## Future Enhancements

### Phase 3: Integration and Polish
- End-to-end testing with both servers
- Performance optimization
- Cross-browser compatibility testing
- User experience refinements
- Deployment preparation

### Phase 4: Advanced Features
- Progress tracking and statistics
- Difficulty settings (more chords, complex progressions)
- Sound quality improvements (better piano samples)
- Keyboard shortcuts for accessibility
- User accounts and progress saving

## Contributing

When making changes:
1. Update tests if adding new features
2. Follow PEP 8 style guidelines
3. Add type hints to all functions
4. Update this README with new features
5. Test in multiple browsers

## License

[Specify license here]

## Support

For issues or questions:
- Check the troubleshooting section above
- Review browser console logs
- Check backend API logs
- Open an issue on the project repository

## References

- [Shiny for Python Documentation](https://shiny.posit.co/py/)
- [Tone.js Documentation](https://tonejs.github.io/)
- [VexFlow Documentation](https://github.com/0xfe/vexflow)
- [ABRSM Grade 8 Music Theory](https://www.abrsm.org/en/music-theory/)
