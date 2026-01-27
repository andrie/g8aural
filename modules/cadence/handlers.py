"""
Event handlers for the cadence identification module.

This module contains extracted business logic functions for cadence identification.
"""
import random
from typing import List, Dict, Any

from lib.music_theory.cadences import CadenceType


def validate_guess(guess: str, correct_answer: str) -> bool:
    """
    Check if guess matches correct answer.

    Args:
        guess: The user's guess (e.g., "perfect")
        correct_answer: The correct cadence type (e.g., "perfect")

    Returns:
        True if guess matches, False otherwise
    """
    guess_normalized = guess.lower().strip()
    return guess_normalized == correct_answer


def get_feedback_message(is_correct: bool, is_first_attempt: bool = True) -> tuple[str, str]:
    """
    Get feedback message and type based on result.

    Args:
        is_correct: Whether the answer was correct
        is_first_attempt: Whether this is the first attempt

    Returns:
        Tuple of (message, type) where type is "success" or "error"
    """
    if is_correct:
        return ("Correct! Well done!", "success")
    elif is_first_attempt:
        return ("Not quite. Try again!", "error")
    else:
        return ("Keep trying!", "error")


def generate_new_cadence_data(generator, grade_level: int, allowed_cadences: List) -> Dict[str, Any]:
    """
    Generate a new cadence progression using the provided generator.

    Args:
        generator: ChordProgressionGenerator instance
        grade_level: Current grade level (6, 7, or 8)
        allowed_cadences: List of allowed CadenceType values for this grade

    Returns:
        Dictionary containing:
        - cadence_type: The chosen cadence type value (str)
        - progression: MIDI notes list
        - note_names: Note names list
        - symbols: Chord symbols list
        - key: Key of the progression (str)
    """
    # Randomly select a cadence type
    cadence_type = random.choice(allowed_cadences)

    # Generate the progression
    progression = generator.generate_progression(cadence_type)
    midi_progression = generator.progression_to_midi(progression)
    note_names = generator.progression_to_note_names(progression)
    chord_symbols = generator.progression_to_symbols(progression)

    # Extract the key from the first chord
    progression_key = str(progression[0].key).split()[0] if progression else 'C'

    return {
        'cadence_type': cadence_type.value,  # "perfect", "plagal", etc.
        'progression': midi_progression,
        'note_names': note_names,
        'symbols': chord_symbols,
        'key': progression_key
    }


async def handle_correct_answer(
    session,
    progression_state,
    feedback_state,
    game_flow,
    button_id: str,
    cadence_type: str,
    correct_cadence: str
):
    """
    Handle the logic when user guesses correctly.

    Args:
        session: Shiny session object
        progression_state: ProgressionState instance
        feedback_state: FeedbackState instance
        game_flow: GameFlowState instance
        button_id: ID of the clicked button
        cadence_type: The cadence type that was guessed
        correct_cadence: The correct answer
    """
    # Add checkmark
    await session.send_custom_message("updateButtonFeedback", {
        "btnId": button_id,
        "emoji": "✓",
        "originalText": cadence_type.capitalize()
    })

    # Update state
    feedback_state.set("Correct! Well done!", "success")
    game_flow.state.set("correct")

    # Show notation
    await session.send_custom_message("renderNotation", {
        "progression": progression_state.progression(),
        "noteNames": progression_state.note_names(),
        "chordSymbols": progression_state.chord_symbols(),
        "cadenceType": correct_cadence,
        "key": progression_state.key(),
        "containerId": "cadence-notation-container"
    })

    # Show notation section and next button, hide hint button
    await session.send_custom_message("updateButtonStates", {
        "playEnabled": True,
        "answersEnabled": False,
        "nextVisible": True,
        "showNotation": True,
        "hintVisible": False
    })


async def handle_incorrect_answer(
    session,
    game_flow,
    feedback_state,
    button_id: str,
    cadence_type: str
):
    """
    Handle the logic when user guesses incorrectly.

    Args:
        session: Shiny session object
        game_flow: GameFlowState instance
        feedback_state: FeedbackState instance
        button_id: ID of the clicked button
        cadence_type: The cadence type that was guessed
    """
    # Add cross
    await session.send_custom_message("updateButtonFeedback", {
        "btnId": button_id,
        "emoji": "✗",
        "originalText": cadence_type.capitalize()
    })

    # Add this button to disabled list
    current_disabled = game_flow.disabled_buttons()
    current_disabled.append(button_id)
    game_flow.disabled_buttons.set(current_disabled)

    # Update feedback
    feedback_state.set("Not quite. Try again!", "error")

    # Re-enable answer buttons for retry (except disabled ones)
    await session.send_custom_message("updateButtonStates", {
        "playEnabled": True,
        "answersEnabled": True,
        "nextVisible": False,
        "disabledButtons": current_disabled
    })


async def initialize_new_cadence(
    session,
    progression_state,
    feedback_state,
    game_flow,
    cadence_data: Dict[str, Any]
):
    """
    Initialize UI and state for a new cadence.

    Args:
        session: Shiny session object
        progression_state: ProgressionState instance
        feedback_state: FeedbackState instance
        game_flow: GameFlowState instance
        cadence_data: Dictionary from generate_new_cadence_data()
    """
    # Update progression state atomically
    progression_state.set_all(
        cadence_data['progression'],
        cadence_data['note_names'],
        cadence_data['symbols'],
        cadence_data['cadence_type'],
        cadence_data['key']
    )

    # Reset game state
    game_flow.has_played.set(False)
    game_flow.is_playing.set(False)
    game_flow.state.set("ready")
    game_flow.disabled_buttons.set([])

    # Set feedback
    feedback_state.set("Click 'Play Cadence' to begin", "info")

    # Update UI: enable play button, disable answer buttons, show hint button
    await session.send_custom_message("updateButtonStates", {
        "playEnabled": True,
        "answersEnabled": False,
        "nextVisible": False,
        "hintVisible": True
    })

    # Reset button text (clear any emoji feedback)
    await session.send_custom_message("resetButtonText", {})

    # Clear notation
    await session.send_custom_message("clearNotation", {"containerId": "cadence-notation-container"})