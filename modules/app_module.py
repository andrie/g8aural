"""
Main application module for g8aural.

This module defines the UI and server functions for the main application.
It serves as the entry point for the modular Shiny application.
"""
from shiny import module, ui, reactive
from config.app_config import KEYS_BY_GRADE, CADENCE_TYPES_BY_GRADE, GENERATOR_CONFIG, VOICE_CONFIG_BY_GRADE
from lib.music_theory.progression import ChordProgressionGenerator
from state.app_state import AppState
from state.cadence_state import ProgressionState, FeedbackState, GameFlowState
from state.voice_state import VoiceState
from ui.layout import create_header, create_grade_selection
from modules.cadence.module import cadence_ui, cadence_server
from modules.voice.module import voice_ui, voice_server


@module.ui
def app_module_ui(id):
    """Main application UI."""
    return ui.page_fluid(
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
            # Load microphone.js as ES module (imports Pitchy internally)
            ui.tags.script(src="microphone.js", type="module"),
            ui.tags.script(src="voice-playback.js"),
            ui.tags.script(src="pitch-plot.js"),
        ),
        # Header and grade selection (shared across all tabs)
        create_header(),
        *create_grade_selection(),  # Unpacks list of components
        # Tab navigation
        ui.navset_tab(
            ui.nav_panel(
                "Cadence Identification",
                cadence_ui(id("cadence"))
            ),
            ui.nav_panel(
                "Voice Singing",
                voice_ui(id("voice"))
            ),
            id=id("main_tabs")
        ),
    )


@module.server
def app_server(id, input, output, session):
    """Main application server logic."""
    # Grouped reactive state
    app_state = AppState.create()
    progression_state = ProgressionState.create()
    feedback_state = FeedbackState.create()
    game_flow = GameFlowState.create()
    voice_state = VoiceState.create()

    # Reactive generator for cadence identification
    generator = reactive.Value(
        ChordProgressionGenerator(**GENERATOR_CONFIG[6])
    )

    # Helper function to create voice generator based on grade level
    def create_voice_generator(grade):
        """Create voice generator based on grade level."""
        config = VOICE_CONFIG_BY_GRADE.get(grade, VOICE_CONFIG_BY_GRADE[8])

        return ChordProgressionGenerator(
            min_length=config['min_length'],
            max_length=config['max_length'],
            use_voice_leading=config['use_voice_leading'],
            use_sevenths=config['use_sevenths'],
            use_corpus=config['use_corpus'],
            corpus_temperature=config['corpus_temperature'],
            keys=config['keys'],
            use_strict_cadence=config['use_strict_cadence']
        )

    # Separate generator for voice singing (reactive to grade changes)
    # Initialize with Grade 8 (default), will be updated by reactive effect
    voice_generator = reactive.Value(
        create_voice_generator(8)
    )

    # Initialize cadence tab server logic and get fetch_new_cadence function
    fetch_new_cadence = cadence_server(
        id("cadence"),
        input, output, session,
        progression_state, feedback_state,
        game_flow, app_state, generator
    )

    # Initialize voice module server logic
    voice_server(
        id("voice"),
        input, output, session,
        voice_state, app_state, voice_generator
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
        if saved_grade and saved_grade in [5, 6, 7, 8]:
            app_state.level.set(saved_grade)
            # Reinitialize cadence generator (only for grades 6-8)
            if saved_grade >= 6:
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
        app_state.restored.set(True)

    # Handle grade level changes
    @reactive.Effect
    @reactive.event(input.grade_slider)
    async def _():
        # Don't process slider changes until grade restoration is complete
        # This prevents the slider's initial value (6) from overwriting the restored grade
        if not app_state.restored():
            return

        new_grade = int(input.grade_slider())

        # Only process if grade actually changed (avoid duplicate updates)
        if new_grade == app_state.level():
            return

        app_state.level.set(new_grade)

        # Save to localStorage
        await session.send_custom_message("saveGradeLevel", {
            "grade": new_grade
        })

        # Reinitialize cadence generator (only for grades 6-8)
        if new_grade >= 6:
            config = GENERATOR_CONFIG[new_grade]
            generator.set(ChordProgressionGenerator(**config))

            # Update button visibility for cadence tab
            await session.send_custom_message("updateGradeUI", {
                "grade": new_grade,
                "availableCadences": [ct.value for ct in CADENCE_TYPES_BY_GRADE[new_grade]]
            })

        # Show toast notification
        if new_grade == 5:
            toast_msg = f"Grade changed to {new_grade}. Try the Voice Singing tab!"
        else:
            toast_msg = f"Grade changed to {new_grade}. Click 'Next Cadence' to start."

        await session.send_custom_message("showToast", {
            "message": toast_msg
        })

    # Reactive effect: Update voice generator when grade changes
    @reactive.Effect
    def _():
        current_grade = app_state.level()
        voice_generator.set(create_voice_generator(current_grade))