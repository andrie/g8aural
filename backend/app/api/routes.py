"""
API routes for cadence training application.
"""
import random
import uuid
from typing import Dict
from fastapi import APIRouter, HTTPException

from ..models import CadenceRequest, CadenceResponse, GuessRequest, GuessResponse
from ..music_theory.cadences import CadenceType
from ..music_theory.progression import ChordProgressionGenerator

router = APIRouter()

# In-memory session storage (for MVP - would use database in production)
# Maps session_id to cadence_type
sessions: Dict[str, str] = {}

# Initialize progression generator
generator = ChordProgressionGenerator(min_length=4, max_length=8)


@router.post("/api/cadence/generate", response_model=CadenceResponse)
async def generate_cadence(request: CadenceRequest = None):
    """
    Generate a new random cadence progression.

    Returns:
        CadenceResponse with session_id, progression data, and chord symbols
    """
    # Randomly select a cadence type
    cadence_type = random.choice(list(CadenceType))

    # Generate the progression
    progression = generator.generate_progression(cadence_type)

    # Convert to MIDI
    midi_progression = generator.progression_to_midi(progression)

    # Get chord symbols
    chord_symbols = generator.progression_to_symbols(progression)

    # Create session ID
    session_id = str(uuid.uuid4())

    # Store the correct answer in session
    sessions[session_id] = cadence_type.value

    # Return response (don't reveal the cadence type to client)
    return CadenceResponse(
        session_id=session_id,
        cadence_type="hidden",  # Don't reveal until correct guess
        progression=midi_progression,
        chord_symbols=chord_symbols
    )


@router.post("/api/cadence/check", response_model=GuessResponse)
async def check_guess(request: GuessRequest):
    """
    Check if the student's guess is correct.

    Args:
        request: GuessRequest with session_id and guess

    Returns:
        GuessResponse indicating if guess was correct
    """
    # Validate session exists
    if request.session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    # Get correct answer
    correct_cadence = sessions[request.session_id]

    # Normalize guess (lowercase, remove spaces)
    guess_normalized = request.guess.lower().strip()

    # Check if correct
    is_correct = guess_normalized == correct_cadence

    if is_correct:
        # Clean up session after correct answer
        del sessions[request.session_id]
        return GuessResponse(
            correct=True,
            message="Correct! Well done!",
            cadence_type=correct_cadence
        )
    else:
        return GuessResponse(
            correct=False,
            message="Not quite. Try again!",
            cadence_type=None  # Don't reveal answer on incorrect guess
        )


@router.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "active_sessions": len(sessions)}
