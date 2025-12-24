# ABRSM Grade 8 Cadence Training - Backend API

FastAPI backend for the ABRSM Grade 8 aural training application. Generates musical chord progressions ending in one of four cadence types and validates student answers.

## Features

- **Music Theory Engine**: Rule-based chord progression generator following music theory principles
- **Four Cadence Types**: Perfect (V-I), Plagal (IV-I), Imperfect (I-V), Interrupted (V-vi)
- **REST API**: JSON endpoints for progression generation and answer validation
- **C Major Only**: MVP focuses on C major scale (extensible to other keys)

## Prerequisites

- Python 3.12 or higher
- Virtual environment support

## Installation

### 1. Navigate to Backend Directory

```bash
cd backend
```

### 2. Create Virtual Environment

```bash
python3 -m venv .venv
```

Or using uv (if installed):

```bash
uv venv
```

### 3. Activate Virtual Environment

```bash
source .venv/bin/activate
```

### 4. Install Dependencies

```bash
.venv/bin/python3 -m pip install -r requirements.txt
```

Or using uv:

```bash
uv pip install -r requirements.txt
```

## Running the Server

### Start the Development Server

```bash
.venv/bin/uvicorn app.main:app --reload --port 8000
```

The server will start at `http://localhost:8000` with auto-reload enabled.

### Verify Server is Running

```bash
curl http://localhost:8000/
```

Expected response:
```json
{
  "message": "ABRSM Grade 8 Cadence Training API",
  "version": "1.0.0",
  "docs": "/docs"
}
```

## API Documentation

Once the server is running, visit:
- **Interactive API docs**: http://localhost:8000/docs
- **Alternative docs**: http://localhost:8000/redoc

## API Endpoints

### 1. Health Check

Check if the server is running and see active sessions.

```bash
curl http://localhost:8000/api/health
```

**Response:**
```json
{
  "status": "healthy",
  "active_sessions": 0
}
```

### 2. Generate Cadence

Generate a new random chord progression with a cadence.

```bash
curl -X POST http://localhost:8000/api/cadence/generate \
  -H "Content-Type: application/json" \
  -d "{}"
```

**Response:**
```json
{
  "session_id": "d946cf20-b469-475a-acb8-58f3a57f1d06",
  "cadence_type": "hidden",
  "progression": [
    [60, 64, 67],
    [67, 71, 74],
    [60, 64, 67]
  ],
  "chord_symbols": ["I", "V", "I"]
}
```

**Fields:**
- `session_id`: Unique identifier for this progression (use when submitting guesses)
- `cadence_type`: Hidden until correct answer (always returns "hidden")
- `progression`: Array of chords, each chord is array of MIDI note numbers
- `chord_symbols`: Roman numeral notation for each chord

### 3. Check Guess

Validate a student's cadence identification.

```bash
curl -X POST http://localhost:8000/api/cadence/check \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "d946cf20-b469-475a-acb8-58f3a57f1d06",
    "guess": "perfect"
  }'
```

**Valid guess values:** `perfect`, `plagal`, `imperfect`, `interrupted`

**Response (Correct):**
```json
{
  "correct": true,
  "message": "Correct! Well done!",
  "cadence_type": "perfect"
}
```

**Response (Incorrect):**
```json
{
  "correct": false,
  "message": "Not quite. Try again!",
  "cadence_type": null
}
```

## Testing

### Run Unit Tests

Manual test script (pytest not required):

```bash
.venv/bin/python3 << 'EOF'
import sys
sys.path.insert(0, '/home/andrie/wsl-github/g8aural/backend')

from app.music_theory.notes import Note, NoteName, Chord
from app.music_theory.cadences import CadenceType, CadencePattern
from app.music_theory.progression import ChordProgressionGenerator

# Test basic functionality
note = Note(NoteName.C, 4)
assert note.to_midi() == 60
print("✓ Note class works")

chord = Chord(1)
assert chord.get_roman_numeral() == "I"
print("✓ Chord class works")

generator = ChordProgressionGenerator(4, 8)
for cadence_type in CadenceType:
    progression = generator.generate_progression(cadence_type)
    assert 4 <= len(progression) <= 8
print("✓ Progression generator works")

print("\nAll tests passed!")
EOF
```

### Test Complete Workflow

Complete workflow test script:

```bash
#!/bin/bash

echo "Testing complete workflow..."

# 1. Generate a cadence
echo "1. Generating cadence..."
RESPONSE=$(curl -s -X POST http://localhost:8000/api/cadence/generate \
  -H "Content-Type: application/json" -d "{}")

SESSION_ID=$(echo "$RESPONSE" | grep -o '"session_id":"[^"]*"' | cut -d'"' -f4)
echo "   Session ID: $SESSION_ID"

# 2. Try incorrect guess
echo "2. Testing incorrect guess..."
RESULT=$(curl -s -X POST http://localhost:8000/api/cadence/check \
  -H "Content-Type: application/json" \
  -d "{\"session_id\": \"$SESSION_ID\", \"guess\": \"perfect\"}")
echo "   Response: $RESULT"

# 3. Try all cadence types until correct
echo "3. Finding correct answer..."
for cadence in "perfect" "plagal" "imperfect" "interrupted"; do
  RESULT=$(curl -s -X POST http://localhost:8000/api/cadence/check \
    -H "Content-Type: application/json" \
    -d "{\"session_id\": \"$SESSION_ID\", \"guess\": \"$cadence\"}")

  if echo "$RESULT" | grep -q '"correct":true'; then
    echo "   ✓ Correct answer: $cadence"
    break
  fi
done

echo "✓ Workflow test complete!"
```

### Verify All Cadence Types

```bash
echo "Generating 20 progressions to verify all cadence types..."

for i in {1..20}; do
  RESPONSE=$(curl -s -X POST http://localhost:8000/api/cadence/generate \
    -H "Content-Type: application/json" -d "{}")

  SYMBOLS=$(echo "$RESPONSE" | grep -o '"chord_symbols":\[[^]]*\]')
  echo "$SYMBOLS" | tail -c 20
done

echo "Check output above for: V,I (Perfect), IV,I (Plagal), I,V (Imperfect), V,vi (Interrupted)"
```

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app entry point
│   ├── models.py               # Pydantic models
│   ├── music_theory/
│   │   ├── __init__.py
│   │   ├── cadences.py         # Cadence definitions
│   │   ├── notes.py            # Note/chord representations
│   │   └── progression.py      # Chord progression generator
│   └── api/
│       ├── __init__.py
│       └── routes.py           # API endpoints
├── tests/
│   ├── __init__.py
│   └── test_progression.py     # Unit tests
├── requirements.txt
└── README.md
```

## Development

### Stop the Server

Press `Ctrl+C` in the terminal where uvicorn is running.

### View Server Logs

Server logs appear in the terminal where uvicorn is running. Look for:
- Request logs: `INFO: 127.0.0.1:xxxxx - "POST /api/cadence/generate HTTP/1.1" 200 OK`
- Error logs: `ERROR: Exception in ASGI application`

### Auto-Reload

The server runs with `--reload` flag, so code changes automatically restart the server.

## Troubleshooting

### Port Already in Use

If port 8000 is already in use:

```bash
# Find process using port 8000
lsof -i :8000

# Kill the process
kill -9 <PID>

# Or use a different port
.venv/bin/uvicorn app.main:app --reload --port 8001
```

### Module Import Errors

Make sure you're in the backend directory and the virtual environment is activated:

```bash
pwd  # Should show: .../g8aural/backend
which python3  # Should show: .../backend/.venv/bin/python3
```

### Dependencies Not Installed

```bash
# Reinstall all dependencies
.venv/bin/python3 -m pip install -r requirements.txt --force-reinstall
```

### CORS Errors from Frontend

The server is configured to allow requests from:
- http://localhost:8080
- http://127.0.0.1:8080
- http://localhost:5500 (Live Server)
- http://127.0.0.1:5500

To add more origins, edit `app/main.py`:

```python
allow_origins=[
    "http://localhost:8080",
    "http://your-origin-here",
]
```

## Quick Reference

### Common Commands

```bash
# Start server
.venv/bin/uvicorn app.main:app --reload --port 8000

# Health check
curl http://localhost:8000/api/health

# Generate cadence
curl -X POST http://localhost:8000/api/cadence/generate \
  -H "Content-Type: application/json" -d "{}"

# Check guess
curl -X POST http://localhost:8000/api/cadence/check \
  -H "Content-Type: application/json" \
  -d '{"session_id": "YOUR_SESSION_ID", "guess": "perfect"}'
```

### MIDI Note Reference

- Middle C (C4) = 60
- C major chord = [60, 64, 67] (C4, E4, G4)
- G major chord = [67, 71, 74] (G4, B4, D5)
- F major chord = [65, 69, 72] (F4, A4, C5)

### Cadence Patterns

- **Perfect (V-I)**: Strong conclusive cadence
- **Plagal (IV-I)**: "Amen" cadence
- **Imperfect (I-V)**: Sounds unfinished, asking a question
- **Interrupted (V-vi)**: Deceptive cadence, resolves to vi instead of I

## Next Steps

- Frontend implementation (Phase 2)
- Additional keys beyond C major
- Progress tracking
- User authentication

## License

Copyright 2024 - ABRSM Grade 8 Cadence Training