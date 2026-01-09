"""
ABRSM Grade 8 Cadence Training - Shiny for Python Frontend
"""
from shiny import App, ui, render, reactive
import random
from pathlib import Path
from modules.music_theory.cadences import CadenceType
from modules.music_theory.progression import ChordProgressionGenerator
from config.app_config import KEYS_BY_GRADE, CADENCE_TYPES_BY_GRADE, GENERATOR_CONFIG
from ui.components import (
    create_header,
    create_grade_selection,
    create_control_section,
    create_answer_section,
    create_feedback_section,
    create_next_button_section,
    create_notation_section
)
from state.game_state import ProgressionState, FeedbackState, GameFlowState, GradeState
from handlers.game_logic import (
    validate_guess,
    generate_new_cadence_data,
    handle_correct_answer,
    handle_incorrect_answer,
    initialize_new_cadence
)

# UI Layout
app_ui = ui.page_fluid(
    # Include custom CSS and JavaScript
    ui.tags.head(
        ui.tags.link(rel="stylesheet", href="styles.css"),
        # Include Tone.js
        ui.tags.script(src="https://cdnjs.cloudflare.com/ajax/libs/tone/14.8.49/Tone.js"),
        # Include VexFlow
        ui.tags.script(src="https://cdn.jsdelivr.net/npm/vexflow@4.2.2/build/cjs/vexflow.js"),
        # Include custom JavaScript
        ui.tags.script(src="audio.js"),
        ui.tags.script(src="notation.js"),
        ui.tags.script(src="grade-ui.js"),
    ),
    # UI Components
    create_header(),
    *create_grade_selection(),  # Unpacks list of components (slider + modal)
    create_control_section(),
    create_answer_section(),
    create_feedback_section(),
    create_next_button_section(),
    create_notation_section(),
)

# Server logic
def server(input, output, session):
    # Grouped reactive state
    progression_state = ProgressionState.create()
    feedback_state = FeedbackState.create()
    game_flow = GameFlowState.create()
    grade_state = GradeState.create()

    # Reactive generator (no global variable!)
    generator = reactive.Value(
        ChordProgressionGenerator(**GENERATOR_CONFIG[6])
    )

    # Initialize: Request saved grade from localStorage
    @reactive.Effect
    async def _():
        # Request saved grade from localStorage
        await session.send_custom_message("requestSavedGrade", {})

    # Handle saved grade level restoration from localStorage
    @reactive.effect
    @reactive.event(input.saved_grade_level)
    async def _():
        saved_grade = input.saved_grade_level()
        if saved_grade and saved_grade in [6, 7, 8]:
            grade_state.level.set(saved_grade)
            # Reinitialize generator with saved grade
            config = GENERATOR_CONFIG[saved_grade]
            generator.set(ChordProgressionGenerator(**config))

            # Update slider to reflect saved grade (must use Shiny's API)
            ui.update_slider("grade_slider", value=saved_grade)

            # Update UI to reflect saved grade
            await session.send_custom_message("updateGradeUI", {
                "grade": saved_grade,
                "availableCadences": [ct.value for ct in CADENCE_TYPES_BY_GRADE[saved_grade]]
            })

            # Generate first cadence after restoring grade
            if game_flow.state() == "initial":
                await fetch_new_cadence()

        # Always mark grade restoration as complete (even if no valid saved grade)
        # This allows the slider to start working after initialization
        grade_state.restored.set(True)

    # Handle grade level changes
    @reactive.Effect
    @reactive.event(input.grade_slider)
    async def _():
        # Don't process slider changes until grade restoration is complete
        # This prevents the slider's initial value (6) from overwriting the restored grade
        if not grade_state.restored():
            return

        new_grade = int(input.grade_slider())

        # Only process if grade actually changed (avoid duplicate updates)
        if new_grade == grade_state.level():
            return

        grade_state.level.set(new_grade)

        # Save to localStorage
        await session.send_custom_message("saveGradeLevel", {
            "grade": new_grade
        })

        # Reinitialize generator with new config
        config = GENERATOR_CONFIG[new_grade]
        generator.set(ChordProgressionGenerator(**config))

        # Update button visibility
        await session.send_custom_message("updateGradeUI", {
            "grade": new_grade,
            "availableCadences": [ct.value for ct in CADENCE_TYPES_BY_GRADE[new_grade]]
        })

        # Show toast notification
        await session.send_custom_message("showToast", {
            "message": f"Grade changed to {new_grade}. Click 'Next Cadence' to start."
        })

    # Generate new cadence locally
    async def fetch_new_cadence():
        try:
            # Generate cadence data
            current_grade = grade_state.level()
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

    @reactive.Effect
    @reactive.event(input.perfect_btn)
    async def _():
        await handle_guess("perfect", "perfect_btn")

    @reactive.Effect
    @reactive.event(input.plagal_btn)
    async def _():
        await handle_guess("plagal", "plagal_btn")

    @reactive.Effect
    @reactive.event(input.imperfect_btn)
    async def _():
        await handle_guess("imperfect", "imperfect_btn")

    @reactive.Effect
    @reactive.event(input.interrupted_btn)
    async def _():
        await handle_guess("interrupted", "interrupted_btn")

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

# Create app with static files from www directory
www_dir = Path(__file__).parent / "www"
app = App(app_ui, server, static_assets=www_dir)
