"""
Pydantic models for API request and response schemas.
"""
from typing import List, Optional
from pydantic import BaseModel


class CadenceRequest(BaseModel):
    """Request model for generating a new cadence (currently empty, for future params)."""
    pass


class CadenceResponse(BaseModel):
    """Response model for cadence generation."""
    session_id: str
    cadence_type: str
    progression: List[List[int]]  # List of chords, each chord is list of MIDI notes
    chord_symbols: List[str]  # Roman numeral notation for each chord


class GuessRequest(BaseModel):
    """Request model for checking a student's guess."""
    session_id: str
    guess: str  # The cadence type guessed by student


class GuessResponse(BaseModel):
    """Response model for guess validation."""
    correct: bool
    message: str
    cadence_type: Optional[str] = None  # Only returned if incorrect to help with retry
