"""
Shiny module for cadence identification.

This module defines the UI and server functions for the cadence identification feature.
"""
from shiny import module, ui, reactive, render
from config.app_config import CADENCE_TYPES_BY_GRADE

from state.cadence_state import ProgressionState, FeedbackState, GameFlowState
from .components import (
    create_control_section,
    create_answer_section,
    create_feedback_section,
    create_next_button_section,
    create_notation_section
)
from .handlers import (
    validate_guess,
    handle_correct_answer,
    handle_incorrect_answer,
    initialize_new_cadence,
    generate_new_cadence_data
)


@module.ui
def cadence_ui(id):
    """Create UI for cadence identification tab."""
    return ui.div(
        create_control_section(id),
        create_answer_section(id),
        create_feedback_section(id),
        create_next_button_section(id),
        create_notation_section(id),
    )


@module.server
def cadence_server(id, input, output, session, progression_state, feedback_state, game_flow, app_state, generator):
    """
    Server logic for cadence identification tab.

    Args:
        id: Module ID function
        input: Module input
        output: Module output
        session: Shiny session
        progression_state: ProgressionState instance
        feedback_state: FeedbackState instance
        game_flow: GameFlowState instance
        app_state: AppState instance
        generator: ChordProgressionGenerator reactive value
    """
    # Generate new cadence locally
    async def fetch_new_cadence():
        try:
            # Generate cadence data
            current_grade = app_state.level()
            allowed_cadences = CADENCE_TYPES_BY_GRADE[current_grade]
            gen = generator()
            cadence_data = generate_new_cadence_data(gen, current_grade, allowed_cadences)

            # Initialize UI and state for new cadence
            await initialize_new_cadence(
                session,
                progression_state,
                feedback_state,
                game_flow,
                cadence_data
            )

        except Exception as e:
            feedback_state.set(f"Error generating cadence: {str(e)}", "error")

    # Handle audio loading (first play only)
    @reactive.effect
    @reactive.event(input.audio_loading)
    async def _():
        if input.audio_loading():
            feedback_state.set("Loading piano samples... (first time only)", "info")

    # Play button click handler
    @reactive.Effect
    @reactive.event(input.play_btn)
    async def _():
        if progression_state.progression() is None:
            return

        game_flow.is_playing.set(True)
        feedback_state.set("Playing..." if not game_flow.has_played() else "Replaying...", "info")

        # Send progression to JavaScript for playback
        await session.send_custom_message("playProgression", {
            "progression": progression_state.progression(),
            "noteNames": progression_state.note_names()
        })

        # Note: JavaScript will send message back when playback completes

    # Handle playback completion (called from JavaScript)
    @reactive.effect
    @reactive.event(input.playback_complete)
    async def _():
        game_flow.is_playing.set(False)
        game_flow.has_played.set(True)
        feedback_state.set("Now select the cadence type", "info")

        # Enable answer buttons
        await session.send_custom_message("updateButtonStates", {
            "playEnabled": True,
            "answersEnabled": True,
            "nextVisible": False
        })

    # Answer button handlers
    async def handle_guess(cadence_type: str, button_id: str):
        if not game_flow.has_played():
            feedback_state.set("Please play the cadence first!", "error")
            return

        if progression_state.cadence_type() is None:
            feedback_state.set("No cadence loaded yet!", "error")
            return

        # Disable buttons during validation
        await session.send_custom_message("updateButtonStates", {
            "playEnabled": False,
            "answersEnabled": False,
            "nextVisible": False
        })

        try:
            # Validate guess
            correct_cadence = progression_state.cadence_type()
            is_correct = validate_guess(cadence_type, correct_cadence)

            if is_correct:
                await handle_correct_answer(
                    session,
                    progression_state,
                    feedback_state,
                    game_flow,
                    button_id,
                    cadence_type,
                    correct_cadence
                )
            else:
                await handle_incorrect_answer(
                    session,
                    game_flow,
                    feedback_state,
                    button_id,
                    cadence_type
                )

        except Exception as e:
            feedback_state.set(f"Error validating answer: {str(e)}", "error")

            # Re-enable buttons
            await session.send_custom_message("updateButtonStates", {
                "playEnabled": True,
                "answersEnabled": True,
                "nextVisible": False
            })

    # Factory function to create button event handlers
    def create_answer_handler(cadence_type: str, button_id: str):
        @reactive.Effect
        @reactive.event(getattr(input, button_id))
        async def _():
            await handle_guess(cadence_type, button_id)
        return _

    # Register answer button handlers using factory
    _perfect_handler = create_answer_handler("perfect", "perfect_btn")
    _plagal_handler = create_answer_handler("plagal", "plagal_btn")
    _imperfect_handler = create_answer_handler("imperfect", "imperfect_btn")
    _interrupted_handler = create_answer_handler("interrupted", "interrupted_btn")

    # Hint button handler
    @reactive.Effect
    @reactive.event(input.hint_btn)
    async def _():
        if progression_state.progression() is None or progression_state.cadence_type() is None:
            feedback_state.set("No cadence loaded yet!", "error")
            return

        # Show the hint message
        feedback_state.set(f"Hint: Here's the sheet music.", "info")
        game_flow.state.set("hint_shown")

        # Show notation with the correct answer
        await session.send_custom_message("renderNotation", {
            "progression": progression_state.progression(),
            "noteNames": progression_state.note_names(),
            "chordSymbols": progression_state.chord_symbols(),
            "cadenceType": progression_state.cadence_type(),
            "key": progression_state.key()
        })

        # Show notation section and next button, disable answer buttons, hide hint button
        await session.send_custom_message("updateButtonStates", {
            "playEnabled": True,
            "answersEnabled": False,
            "nextVisible": True,
            "showNotation": True,
            "hintVisible": False
        })

    # Next button handler
    @reactive.Effect
    @reactive.event(input.next_btn)
    async def _():
        game_flow.state.set("initial")
        await fetch_new_cadence()

    # Render feedback message
    @output
    @render.ui
    def feedback_message():
        msg = feedback_state.message()
        msg_type = feedback_state.type()

        if not msg:
            return ui.div()

        css_class = f"alert alert-{msg_type}"
        return ui.div(msg, class_=css_class)

    # Return fetch_new_cadence for use in grade initialization
    return fetch_new_cadence