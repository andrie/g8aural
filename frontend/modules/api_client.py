"""
API client for communicating with the FastAPI backend.
"""
import httpx
from typing import Dict, List, Optional

BACKEND_URL = "http://localhost:8000"

async def generate_cadence() -> Dict:
    """
    Call the backend to generate a new cadence progression.

    Returns:
        Dict with keys: session_id, cadence_type, progression, chord_symbols
    """
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BACKEND_URL}/api/cadence/generate",
            json={},
            timeout=10.0
        )
        response.raise_for_status()
        return response.json()

async def check_guess(session_id: str, guess: str) -> Dict:
    """
    Check if the student's guess is correct.

    Args:
        session_id: The session ID from generate_cadence
        guess: The cadence type guessed ("perfect", "plagal", "imperfect", "interrupted")

    Returns:
        Dict with keys: correct (bool), message (str), cadence_type (str or None)
    """
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BACKEND_URL}/api/cadence/check",
            json={"session_id": session_id, "guess": guess},
            timeout=10.0
        )
        response.raise_for_status()
        return response.json()
