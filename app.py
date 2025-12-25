"""
ABRSM Grade 8 Cadence Training - Shiny for Python Frontend
"""
from shiny import App, ui, render, reactive
import random
from pathlib import Path
from modules.music_theory.cadences import CadenceType
from modules.music_theory.progression import ChordProgressionGenerator

# Initialize progression generator (singleton for app lifetime)
generator = ChordProgressionGenerator(
    min_length=4,
    max_length=8,
    use_voice_leading=True,  # Enable automatic voice leading
    use_sevenths=True,        # Enable 7th chords
    use_corpus=True,          # Use Bach corpus patterns
    corpus_temperature=0.8,   # Balance predictability/surprise
    key='C'                   # Key for progressions
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
    ),

    # Header
    ui.div(
        ui.h1("ABRSM Grade 8 Cadence Training"),
        ui.p("Practice identifying cadences by ear"),
        class_="header"
    ),

    # Control Section
    ui.div(
        ui.input_action_button(
            "play_btn",
            "Play Cadence",
            class_="btn-primary btn-lg"
        ),
        ui.input_action_button(
            "hint_btn",
            "Show Hint",
            class_="btn-warning btn-lg",
            style="margin-left: 10px;"
        ),
        class_="control-section"
    ),

    # Answer Section
    ui.div(
        ui.h3("Select the cadence type:"),
        ui.div(
            ui.input_action_button("perfect_btn", "Perfect (V-I)", class_="cadence-btn"),
            ui.input_action_button("plagal_btn", "Plagal (IV-I)", class_="cadence-btn"),
            ui.input_action_button("imperfect_btn", "Imperfect (I-V)", class_="cadence-btn"),
            ui.input_action_button("interrupted_btn", "Interrupted (V-vi)", class_="cadence-btn"),
            class_="answer-grid"
        ),
        class_="answer-section"
    ),

    # Feedback Section
    ui.div(
        ui.output_ui("feedback_message"),
        class_="feedback-section"
    ),

    # Notation Section
    ui.div(
        ui.div(id="notation-container"),
        class_="notation-section",
        style="display: none;"
    ),

    # Next Cadence Button
    ui.div(
        ui.input_action_button(
            "next_btn",
            "Next Cadence",
            class_="btn-success btn-lg",
            style="display: none;"
        ),
        class_="next-section"
    ),
)

# Server logic
def server(input, output, session):
    # Reactive values for state management
    current_progression = reactive.Value(None)
    current_chord_symbols = reactive.Value(None)
    current_cadence_type = reactive.Value(None)
    has_played = reactive.Value(False)
    is_playing = reactive.Value(False)
    game_state = reactive.Value("initial")  # "initial", "ready", "guessing", "correct", "hint_shown"
    feedback_msg = reactive.Value("")
    feedback_type = reactive.Value("info")  # "info", "error", "success"

    # Initialize: Fetch first cadence on app start
    @reactive.Effect
    async def _():
        if game_state() == "initial":
            await fetch_new_cadence()

    # Generate new cadence locally
    async def fetch_new_cadence():
        try:
            # Randomly select a cadence type
            cadence_type = random.choice(list(CadenceType))

            # Generate the progression locally
            progression = generator.generate_progression(cadence_type)
            midi_progression = generator.progression_to_midi(progression)
            chord_symbols = generator.progression_to_symbols(progression)

            # Store the generated data and correct answer
            current_progression.set(midi_progression)
            current_chord_symbols.set(chord_symbols)
            current_cadence_type.set(cadence_type.value)  # "perfect", "plagal", etc.

            # Reset game state
            has_played.set(False)
            is_playing.set(False)
            game_state.set("ready")
            feedback_msg.set("Click 'Play Cadence' to begin")
            feedback_type.set("info")

            # Update UI: enable play button, disable answer buttons
            await session.send_custom_message("updateButtonStates", {
                "playEnabled": True,
                "answersEnabled": False,
                "nextVisible": False
            })

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
            "progression": current_progression()
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
    async def handle_guess(cadence_type: str):
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
                # Correct answer
                feedback_msg.set("Correct! Well done!")
                feedback_type.set("success")
                game_state.set("correct")

                # Show notation
                await session.send_custom_message("renderNotation", {
                    "progression": current_progression(),
                    "chordSymbols": current_chord_symbols(),
                    "cadenceType": correct_cadence
                })

                # Show notation section and next button
                await session.send_custom_message("updateButtonStates", {
                    "playEnabled": True,
                    "answersEnabled": False,
                    "nextVisible": True,
                    "showNotation": True
                })
            else:
                # Incorrect answer
                feedback_msg.set("Not quite. Try again!")
                feedback_type.set("error")

                # Re-enable answer buttons for retry
                await session.send_custom_message("updateButtonStates", {
                    "playEnabled": True,
                    "answersEnabled": True,
                    "nextVisible": False
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
        await handle_guess("perfect")

    @reactive.Effect
    @reactive.event(input.plagal_btn)
    async def _():
        await handle_guess("plagal")

    @reactive.Effect
    @reactive.event(input.imperfect_btn)
    async def _():
        await handle_guess("imperfect")

    @reactive.Effect
    @reactive.event(input.interrupted_btn)
    async def _():
        await handle_guess("interrupted")

    # Hint button handler
    @reactive.Effect
    @reactive.event(input.hint_btn)
    async def _():
        if current_progression() is None or current_cadence_type() is None:
            feedback_msg.set("No cadence loaded yet!")
            feedback_type.set("error")
            return

        # Show the hint message
        feedback_msg.set(f"Hint: Here's the sheet music. The answer is {current_cadence_type().title()}.")
        feedback_type.set("info")
        game_state.set("hint_shown")

        # Show notation with the correct answer
        await session.send_custom_message("renderNotation", {
            "progression": current_progression(),
            "chordSymbols": current_chord_symbols(),
            "cadenceType": current_cadence_type()
        })

        # Show notation section and next button, disable answer buttons
        await session.send_custom_message("updateButtonStates", {
            "playEnabled": True,
            "answersEnabled": False,
            "nextVisible": True,
            "showNotation": True
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
