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

# Initialize progression generator (will be updated based on grade_level)
# Default to Grade 6 configuration
generator = ChordProgressionGenerator(**GENERATOR_CONFIG[6])

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
    # Reactive values for state management
    current_progression = reactive.Value(None)
    current_note_names = reactive.Value(None)
    current_chord_symbols = reactive.Value(None)
    current_cadence_type = reactive.Value(None)
    current_key = reactive.Value(None)  # Store the key of the current progression
    has_played = reactive.Value(False)
    is_playing = reactive.Value(False)
    game_state = reactive.Value("initial")  # "initial", "ready", "guessing", "correct", "hint_shown"
    feedback_msg = reactive.Value("")
    feedback_type = reactive.Value("info")  # "info", "error", "success"
    disabled_buttons = reactive.Value([])  # Track buttons disabled due to wrong answers
    grade_level = reactive.Value(6)  # Default to Grade 6 (easiest level)
    grade_restored = reactive.Value(False)  # Track whether grade restoration from localStorage is complete

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
            grade_level.set(saved_grade)
            # Reinitialize generator with saved grade
            global generator
            config = GENERATOR_CONFIG[saved_grade]
            generator = ChordProgressionGenerator(**config)

            # Update slider to reflect saved grade (must use Shiny's API)
            ui.update_slider("grade_slider", value=saved_grade)

            # Update UI to reflect saved grade
            await session.send_custom_message("updateGradeUI", {
                "grade": saved_grade,
                "availableCadences": [ct.value for ct in CADENCE_TYPES_BY_GRADE[saved_grade]]
            })

            # Generate first cadence after restoring grade
            if game_state() == "initial":
                await fetch_new_cadence()

        # Always mark grade restoration as complete (even if no valid saved grade)
        # This allows the slider to start working after initialization
        grade_restored.set(True)

    # Handle grade level changes
    @reactive.Effect
    @reactive.event(input.grade_slider)
    async def _():
        # Don't process slider changes until grade restoration is complete
        # This prevents the slider's initial value (6) from overwriting the restored grade
        if not grade_restored():
            return

        new_grade = int(input.grade_slider())

        # Only process if grade actually changed (avoid duplicate updates)
        if new_grade == grade_level():
            return

        grade_level.set(new_grade)

        # Save to localStorage
        await session.send_custom_message("saveGradeLevel", {
            "grade": new_grade
        })

        # Reinitialize generator with new config
        global generator
        config = GENERATOR_CONFIG[new_grade]
        generator = ChordProgressionGenerator(**config)

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
            # Randomly select a cadence type based on current grade
            current_grade = grade_level()
            allowed_cadences = CADENCE_TYPES_BY_GRADE[current_grade]
            cadence_type = random.choice(allowed_cadences)

            # Generate the progression locally
            progression = generator.generate_progression(cadence_type)
            midi_progression = generator.progression_to_midi(progression)
            note_names = generator.progression_to_note_names(progression)
            chord_symbols = generator.progression_to_symbols(progression)

            # Extract the key from the first chord in the progression
            # RomanNumeral objects have a key attribute (music21.key.Key object)
            progression_key = str(progression[0].key).split()[0] if progression else 'C'

            # Store the generated data and correct answer
            current_progression.set(midi_progression)
            current_note_names.set(note_names)
            current_chord_symbols.set(chord_symbols)
            current_cadence_type.set(cadence_type.value)  # "perfect", "plagal", etc.
            current_key.set(progression_key)

            # Reset game state
            has_played.set(False)
            is_playing.set(False)
            game_state.set("ready")
            feedback_msg.set("Click 'Play Cadence' to begin")
            feedback_type.set("info")
            disabled_buttons.set([])  # Reset disabled buttons for new cadence

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
            await session.send_custom_message("clearNotation", {})

        except Exception as e:
            feedback_msg.set(f"Error generating cadence: {str(e)}")
            feedback_type.set("error")

    # Handle audio loading (first play only)
    @reactive.effect
    @reactive.event(input.audio_loading)
    async def _():
        if input.audio_loading():
            feedback_msg.set("Loading piano samples... (first time only)")
            feedback_type.set("info")

    # Play button click handler
    @reactive.Effect
    @reactive.event(input.play_btn)
    async def _():
        if current_progression() is None:
            return

        is_playing.set(True)
        feedback_msg.set("Playing..." if not has_played() else "Replaying...")
        feedback_type.set("info")

        # Send progression to JavaScript for playback
        await session.send_custom_message("playProgression", {
            "progression": current_progression(),
            "noteNames": current_note_names()
        })

        # Note: JavaScript will send message back when playback completes

    # Handle playback completion (called from JavaScript)
    @reactive.effect
    @reactive.event(input.playback_complete)
    async def _():
        is_playing.set(False)
        has_played.set(True)
        feedback_msg.set("Now select the cadence type")
        feedback_type.set("info")

        # Enable answer buttons
        await session.send_custom_message("updateButtonStates", {
            "playEnabled": True,
            "answersEnabled": True,
            "nextVisible": False
        })

    # Answer button handlers
    async def handle_guess(cadence_type: str, button_id: str):
        if not has_played():
            feedback_msg.set("Please play the cadence first!")
            feedback_type.set("error")
            return

        if current_cadence_type() is None:
            feedback_msg.set("No cadence loaded yet!")
            feedback_type.set("error")
            return

        # Disable buttons during validation
        await session.send_custom_message("updateButtonStates", {
            "playEnabled": False,
            "answersEnabled": False,
            "nextVisible": False
        })

        try:
            # Validate guess locally
            correct_cadence = current_cadence_type()
            guess_normalized = cadence_type.lower().strip()
            is_correct = guess_normalized == correct_cadence

            if is_correct:
                # Correct answer - add checkmark
                await session.send_custom_message("updateButtonFeedback", {
                    "btnId": button_id,
                    "emoji": "✓",
                    "originalText": cadence_type.capitalize()
                })

                feedback_msg.set("Correct! Well done!")
                feedback_type.set("success")
                game_state.set("correct")

                # Show notation
                await session.send_custom_message("renderNotation", {
                    "progression": current_progression(),
                    "noteNames": current_note_names(),
                    "chordSymbols": current_chord_symbols(),
                    "cadenceType": correct_cadence,
                    "key": current_key()
                })

                # Show notation section and next button, hide hint button
                await session.send_custom_message("updateButtonStates", {
                    "playEnabled": True,
                    "answersEnabled": False,
                    "nextVisible": True,
                    "showNotation": True,
                    "hintVisible": False
                })
            else:
                # Incorrect answer - add cross
                await session.send_custom_message("updateButtonFeedback", {
                    "btnId": button_id,
                    "emoji": "✗",
                    "originalText": cadence_type.capitalize()
                })

                # Add this button to disabled list
                current_disabled = disabled_buttons()
                current_disabled.append(button_id)
                disabled_buttons.set(current_disabled)

                feedback_msg.set("Not quite. Try again!")
                feedback_type.set("error")

                # Re-enable answer buttons for retry (except disabled ones)
                await session.send_custom_message("updateButtonStates", {
                    "playEnabled": True,
                    "answersEnabled": True,
                    "nextVisible": False,
                    "disabledButtons": current_disabled
                })

        except Exception as e:
            feedback_msg.set(f"Error validating answer: {str(e)}")
            feedback_type.set("error")

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
        if current_progression() is None or current_cadence_type() is None:
            feedback_msg.set("No cadence loaded yet!")
            feedback_type.set("error")
            return

        # Show the hint message
        feedback_msg.set(f"Hint: Here's the sheet music.")
        feedback_type.set("info")
        game_state.set("hint_shown")

        # Show notation with the correct answer
        await session.send_custom_message("renderNotation", {
            "progression": current_progression(),
            "noteNames": current_note_names(),
            "chordSymbols": current_chord_symbols(),
            "cadenceType": current_cadence_type(),
            "key": current_key()
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
        game_state.set("initial")
        await fetch_new_cadence()

    # Render feedback message
    @output
    @render.ui
    def feedback_message():
        msg = feedback_msg()
        msg_type = feedback_type()

        if not msg:
            return ui.div()

        css_class = f"alert alert-{msg_type}"
        return ui.div(msg, class_=css_class)

# Create app with static files from www directory
www_dir = Path(__file__).parent / "www"
app = App(app_ui, server, static_assets=www_dir)
