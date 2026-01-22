"""
Sharp Ear - Shiny for Python Frontend
"""
from shiny import App, ui, reactive, render
from pathlib import Path
from config.app_config import CADENCE_TYPES_BY_GRADE, GENERATOR_CONFIG, VOICE_CONFIG_BY_GRADE
from lib.music_theory.progression import ChordProgressionGenerator
from state.app_state import AppState
from state.cadence_state import ProgressionState, FeedbackState, GameFlowState
from state.voice_state import VoiceState

# Server-side handlers - direct imports instead of module imports
from modules.cadence.handlers import (
    validate_guess,
    handle_correct_answer,
    handle_incorrect_answer,
    initialize_new_cadence,
    generate_new_cadence_data
)
from modules.voice.handlers import (
    generate_voice_melody,
    replay_voice_melody
)

# Define UI directly in app.py
def app_ui(request):
    """Main application UI."""

    # Create our own component functions that don't rely on Shiny modules
    def create_ui_components():
        """Create all UI components for the application."""

        # Header
        header = ui.div(
            ui.h1("Sharp Ear - Aural Training"),
            ui.p("Practice identifying cadences and develop your ear for harmony"),
            class_="header"
        )

        # Grade selection slider
        grade_selection = ui.div(
            ui.div(
                ui.h3("Select Grade Level", class_="grade-label"),
                ui.input_slider(
                    "grade_slider",
                    None,
                    min=5,
                    max=8,
                    value=6,
                    step=1,
                    ticks=True
                ),
                ui.div(
                    ui.span("Grade 5", style="text-align: left;"),
                    ui.span("Grade 6"),
                    ui.span("Grade 7"),
                    ui.span("Grade 8", style="text-align: right;"),
                    class_="grade-markers"
                ),
                class_="form-group shiny-input-container",
                style="width: 300px; margin: 0 auto;"
            ),
            ui.div(
                ui.tags.button(
                    ui.tags.i(class_="fa fa-info"),
                    id="grade-info-button",
                    class_="info-btn"
                ),
                class_="grade-info-container"
            ),
            class_="grade-selection"
        )

        # Cadence identification components
        cadence_control_section = ui.div(
            ui.input_action_button(
                "cadence_play_btn",
                "Play Cadence",
                class_="btn-primary btn-lg"
            ),
            ui.input_action_button(
                "cadence_hint_btn",
                "Show Hint",
                class_="btn-warning btn-lg",
                style="margin-left: 10px;"
            ),
            class_="control-section"
        )

        cadence_answer_section = ui.div(
            ui.h3("Select the cadence type:"),
            ui.div(
                ui.input_action_button("cadence_perfect_btn", "Perfect", class_="cadence-btn"),
                ui.input_action_button("cadence_plagal_btn", "Plagal", class_="cadence-btn"),
                ui.input_action_button("cadence_imperfect_btn", "Imperfect", class_="cadence-btn"),
                ui.input_action_button("cadence_interrupted_btn", "Interrupted", class_="cadence-btn"),
                class_="answer-grid"
            ),
            class_="answer-section"
        )

        cadence_feedback_section = ui.div(
            ui.output_ui("cadence_feedback_message"),
            class_="feedback-section"
        )

        cadence_next_button_section = ui.div(
            ui.input_action_button(
                "cadence_next_btn",
                "Next Cadence",
                class_="btn-success btn-lg",
                style="display: none;"
            ),
            class_="next-section"
        )

        cadence_notation_section = ui.div(
            ui.div(id="cadence-notation-container"),
            class_="notation-section",
            style="display: none;"
        )

        # Voice singing components
        voice_instructions = ui.div(
            ui.output_ui("voice_instructions_text"),
            ui.output_ui("voice_target_indicator"),
            class_="voice-instructions"
        )

        voice_control_section = ui.div(
            ui.input_action_button(
                "voice_start_btn",
                "Start Task",
                class_="btn-primary btn-lg"
            ),
            ui.input_action_button(
                "voice_try_again_btn",
                "Try Again",
                class_="btn-warning btn-lg",
                style="margin-left: 10px; display: none;"
            ),
            class_="control-section"
        )

        voice_recording_indicator = ui.div(
            ui.div(
                ui.span("", class_="recording-dot"),
                ui.span("Recording...", style="margin-left: 8px;"),
                id="voice-recording-indicator",
                class_="recording-indicator",
                style="display: none;"
            ),
            ui.tags.canvas(
                id="voice-live-pitch-canvas",
                width="600",
                height="150",
                style="display: none; border: 1px solid #ccc; background: #f9f9f9; margin-top: 10px; margin: 0 auto;"
            ),
            class_="recording-section"
        )

        voice_feedback_section = ui.div(
            ui.output_ui("voice_feedback_message"),
            ui.div(id="voice-pitch-plot", style="margin-top: 20px;"),
            class_="feedback-section"
        )

        voice_notation_section = ui.div(
            ui.div(id="voice-notation-container"),
            class_="notation-section",
            style="display: none;"
        )

        return {
            "header": header,
            "grade_selection": grade_selection,
            "cadence_control_section": cadence_control_section,
            "cadence_answer_section": cadence_answer_section,
            "cadence_feedback_section": cadence_feedback_section,
            "cadence_next_button_section": cadence_next_button_section,
            "cadence_notation_section": cadence_notation_section,
            "voice_instructions": voice_instructions,
            "voice_control_section": voice_control_section,
            "voice_recording_indicator": voice_recording_indicator,
            "voice_feedback_section": voice_feedback_section,
            "voice_notation_section": voice_notation_section
        }

    # Get all UI components
    components = create_ui_components()

    # Build the final UI
    return ui.page_fluid(
        # Include custom CSS and JavaScript
        ui.tags.head(
            ui.tags.link(rel="stylesheet", href="styles.css"),
            # Include Font Awesome for icons
            ui.tags.link(rel="stylesheet", href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.2/css/all.min.css"),
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
        components["header"],
        components["grade_selection"],
        # Tab navigation
        ui.navset_tab(
            ui.nav_panel(
                "Cadence Identification",
                # Build cadence UI directly from components
                ui.div(
                    components["cadence_control_section"],
                    components["cadence_answer_section"],
                    components["cadence_feedback_section"],
                    components["cadence_next_button_section"],
                    components["cadence_notation_section"],
                )
            ),
            ui.nav_panel(
                "Voice Singing",
                # Build voice UI directly from components
                ui.div(
                    components["voice_instructions"],
                    components["voice_control_section"],
                    components["voice_recording_indicator"],
                    components["voice_feedback_section"],
                    components["voice_notation_section"],
                )
            ),
            id="main_tabs"
        ),
    )

def app_server(input, output, session):
    """Main application server logic, rewritten to avoid module system."""
    # Create state objects directly
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
    voice_generator = reactive.Value(
        create_voice_generator(8)
    )

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
    @reactive.event(input.cadence_audio_loading)
    async def _():
        if input.cadence_audio_loading():
            feedback_state.set("Loading piano samples... (first time only)", "info")

    # Play button click handler
    @reactive.Effect
    @reactive.event(input.cadence_play_btn)
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
    async def handle_guess(cadence_type, button_id):
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

    # Cadence answer button handlers
    @reactive.Effect
    @reactive.event(input.cadence_perfect_btn)
    async def _():
        await handle_guess("perfect", "cadence_perfect_btn")

    @reactive.Effect
    @reactive.event(input.cadence_plagal_btn)
    async def _():
        await handle_guess("plagal", "cadence_plagal_btn")

    @reactive.Effect
    @reactive.event(input.cadence_imperfect_btn)
    async def _():
        await handle_guess("imperfect", "cadence_imperfect_btn")

    @reactive.Effect
    @reactive.event(input.cadence_interrupted_btn)
    async def _():
        await handle_guess("interrupted", "cadence_interrupted_btn")

    # Hint button handler
    @reactive.Effect
    @reactive.event(input.cadence_hint_btn)
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
    @reactive.event(input.cadence_next_btn)
    async def _():
        game_flow.state.set("initial")
        await fetch_new_cadence()

    # Render cadence feedback message
    @output
    @render.ui
    def cadence_feedback_message():
        msg = feedback_state.message()
        msg_type = feedback_state.type()

        if not msg:
            return ui.div()

        css_class = f"alert alert-{msg_type}"
        return ui.div(msg, class_=css_class)

    # Voice singing handlers
    # Handle "Try Again" button - replay the same melody
    @reactive.Effect
    @reactive.event(input.voice_try_again_btn)
    async def _():
        # Clear only recording/grading state, keep the melodies
        voice_state.recorded_pitch.set(None)
        voice_state.grading_result.set(None)
        voice_state.is_recording.set(False)

        # Hide plot and try again button
        await session.send_custom_message("clearVoicePlot", {})

        # Replay the same melody
        await replay_voice_melody(
            voice_state,
            app_state,
            session,
            voice_generator
        )

    # Generate melody and start playback when "Start Task" is clicked
    @reactive.Effect
    @reactive.event(input.voice_start_btn)
    async def _():
        await generate_voice_melody(
            voice_state,
            app_state,
            session,
            voice_generator
        )

    # Handle voice playback completion
    @reactive.effect
    @reactive.event(input.voice_playback_complete)
    async def _():
        # Keep recording for 2 more seconds (handled by JavaScript)
        pass

    # Handle recording stopped
    @reactive.effect
    @reactive.event(input.recording_stopped)
    async def _():
        voice_state.is_recording.set(False)

    # Handle recorded pitch data
    @reactive.effect
    @reactive.event(input.recorded_pitch)
    async def _():
        pitch_data = input.recorded_pitch()
        if not pitch_data:
            return

        try:
            from lib.music_theory.voice_analysis import (
                melody_to_pitch_contour,
                hz_to_midi,
                apply_median_filter,
                align_performance,
                detect_voice_error,
                grade_performance,
                find_best_octave_shift
            )
            import numpy as np

            # Store in state
            voice_state.recorded_pitch.set(pitch_data)

            # Extract recorded frequencies (filter out null values)
            recorded_data = pitch_data.get('data', [])
            recorded_frequencies = []
            for sample in recorded_data:
                freq = sample.get('frequency')
                if freq is not None and freq > 0:
                    recorded_frequencies.append(freq)

            if len(recorded_frequencies) < 10:
                voice_state.grading_result.set({
                    'feedback': 'Not enough clear singing detected. Please try again.',
                    'mae_cents': 0,
                    'detected_voice': 'unknown'
                })
                return

            # Convert to numpy array
            recorded_freq = np.array(recorded_frequencies)

            # Convert to MIDI
            recorded_midi = hz_to_midi(recorded_freq)

            # Apply median filter to remove octave jumps
            recorded_midi_filtered = apply_median_filter(recorded_midi, kernel_size=5)

            # Get target melody based on grade-specific target voice
            target_melody = voice_state.get_target_melody()
            target_voice_name = voice_state.target_voice()
            grade = app_state.level()

            if target_melody is None:
                return

            # Use the actual recording sample rate for target generation
            # This ensures time alignment between target and recording
            recording_sample_rate = pitch_data.get('sampleRate', 20)

            # Convert target melody to pitch contour at recording sample rate
            target_contour = melody_to_pitch_contour(target_melody, sample_rate=recording_sample_rate)

            # Convert to MIDI
            target_midi = hz_to_midi(target_contour[target_contour > 0])

            # For grades with multiple voices, detect which voice was sung
            if grade > 5:
                # Get both melodies for comparison
                soprano_melody = voice_state.soprano_melody()
                bass_melody = voice_state.bass_melody()

                if soprano_melody and bass_melody:
                    soprano_contour = melody_to_pitch_contour(soprano_melody, sample_rate=recording_sample_rate)
                    bass_contour = melody_to_pitch_contour(bass_melody, sample_rate=recording_sample_rate)
                    soprano_midi = hz_to_midi(soprano_contour[soprano_contour > 0])
                    bass_midi = hz_to_midi(bass_contour[bass_contour > 0])

                    detected_voice, _ = detect_voice_error(
                        recorded_midi_filtered,
                        soprano_midi,
                        bass_midi
                    )

                    # Check if correct voice was sung
                    if detected_voice == target_voice_name:
                        feedback_prefix = f"✓ You sang the {target_voice_name} voice. "
                    else:
                        feedback_prefix = f"⚠️ You sang the {detected_voice} voice instead of the {target_voice_name} voice. "
                else:
                    feedback_prefix = f"✓ Grading against {target_voice_name} voice. "
            else:
                # Grade 5: single melody, no voice detection needed
                feedback_prefix = "✓ "
                detected_voice = target_voice_name

            # Find the best octave shift (-1, 0, or +1 octaves)
            best_octave_shift, _ = find_best_octave_shift(
                recorded_midi_filtered,
                target_midi
            )

            # Align recorded to target using DTW with octave shift
            # DTW handles different sequence lengths naturally
            shifted_recorded = recorded_midi_filtered + best_octave_shift
            aligned_path, _ = align_performance(
                shifted_recorded,
                target_midi
            )

            # Grade performance with octave shift
            mae_cents = grade_performance(
                recorded_midi_filtered,
                target_midi,
                aligned_path,
                octave_shift=best_octave_shift
            )

            # Generate feedback based on thresholds
            if mae_cents <= 25:
                accuracy_msg = "Excellent pitch accuracy!"
            elif mae_cents <= 50:
                accuracy_msg = "Good, but could be more precise."
            elif mae_cents <= 100:
                accuracy_msg = "Pitch needs work - try again."
            else:
                accuracy_msg = "Many wrong notes - listen again carefully."

            # Add octave shift information if present
            # Note: positive shift means we shifted UP to match, so user sang LOWER
            if best_octave_shift != 0:
                octave_direction = "lower" if best_octave_shift > 0 else "higher"
                octave_msg = f" (You sang 1 octave {octave_direction} than written.)"
            else:
                octave_msg = ""

            feedback_msg = feedback_prefix + accuracy_msg + octave_msg

            # Store grading result
            voice_state.grading_result.set({
                'feedback': feedback_msg,
                'mae_cents': mae_cents,
                'detected_voice': detected_voice,
                'octave_shift': best_octave_shift
            })

            # Create pitch plot
            try:
                from lib.music_theory.voice_analysis import create_pitch_plot

                # Apply octave shift to recorded data for visualization
                shifted_recorded_for_plot = recorded_midi_filtered + best_octave_shift

                # Create timestamps for target data using actual recording sample rate
                target_timestamps = np.linspace(0, len(target_midi) / recording_sample_rate, len(target_midi))

                print("Creating pitch plot with data:", {
                    "recorded_length": len(shifted_recorded_for_plot),
                    "target_length": len(target_midi),
                    "timestamps_length": len(target_timestamps)
                })

                # Create the plot with shifted data (full length, not truncated)
                plot_base64 = create_pitch_plot(
                    shifted_recorded_for_plot,
                    target_midi,
                    target_timestamps
                )

                print("Pitch plot created successfully, length:", len(plot_base64) if plot_base64 else 0)

                # Send to JavaScript for display
                await session.send_custom_message("displayPitchPlot", {
                    "imageData": plot_base64
                })

            except ImportError as e:
                print(f"Missing plotting dependency: {str(e)}")
                # Send empty plot data to show placeholder
                await session.send_custom_message("displayPitchPlot", {
                    "imageData": ""
                })

            except Exception as e:
                # Plot creation failed, log the error
                print(f"Error creating pitch plot: {str(e)}")
                # Send empty plot data to show placeholder
                await session.send_custom_message("displayPitchPlot", {
                    "imageData": ""
                })

            finally:
                # Always show Try Again button, whether the plot succeeded or failed
                await session.send_custom_message("updateVoiceButtons", {
                    "tryAgainVisible": True
                })

        except Exception as e:
            voice_state.grading_result.set({
                'feedback': f'Error processing recording: {str(e)}',
                'mae_cents': 0,
                'detected_voice': 'error'
            })

    # Render grade-adaptive voice instructions
    @output
    @render.ui
    def voice_instructions_text():
        """Dynamic instructions based on grade level."""
        grade = app_state.level()

        instructions = {
            5: [
                "Listen to the melody played twice",
                "Sing back the complete melody from memory",
                "Your pitch will be analyzed and graded"
            ],
            6: [
                "Listen to the two-part phrase played twice",
                "Sing back the UPPER part (soprano) from memory",
                "The lower part provides harmonic context"
            ],
            7: [
                "Listen to the two-part phrase played twice",
                "Sing back the LOWER part (bass) from memory",
                "The upper part provides harmonic context"
            ],
            8: [
                "Listen to the three-part phrase played twice",
                "Sing back the LOWEST part (bass) from memory",
                "The upper voices provide harmonic context"
            ]
        }

        current_instructions = instructions.get(grade, instructions[8])

        return ui.div(
            ui.h3(f"Grade {grade} - Voice Singing"),
            ui.tags.ol(*[ui.tags.li(instr) for instr in current_instructions]),
            ui.p(ui.strong("Note:"), " You'll hear the melody twice before recording begins."),
            class_="voice-instructions-content"
        )

    # Render voice target indicator
    @output
    @render.ui
    def voice_target_indicator():
        """Show which voice the user should sing."""
        grade = app_state.level()
        config = VOICE_CONFIG_BY_GRADE.get(grade, VOICE_CONFIG_BY_GRADE[8])

        target_voice = config['target_voice']
        num_voices = config['num_voices']

        if target_voice is None:
            # Grade 5 - single melody
            return ui.div(
                ui.span("🎵 Sing the melody", class_="voice-target-label"),
                class_="voice-target-indicator"
            )
        else:
            voice_labels = {
                'soprano': '🎵 Sing the UPPER part (soprano)',
                'bass': '🎵 Sing the LOWER part (bass)'
            }

            return ui.div(
                ui.span(voice_labels.get(target_voice, target_voice.upper()),
                       class_="voice-target-label"),
                ui.p(f"{num_voices}-part harmony", class_="voice-context-label"),
                class_="voice-target-indicator"
            )

    # Render voice feedback message
    @output
    @render.ui
    def voice_feedback_message():
        result = voice_state.grading_result()
        if result is None:
            return ui.div("Ready to start. Click 'Start Task' to hear the melody.")

        # Display grading result
        feedback = result.get('feedback', 'No feedback available')
        mae_cents = result.get('mae_cents', 0)
        detected_voice = result.get('detected_voice', 'unknown')
        octave_shift = result.get('octave_shift', 0)

        # Build octave shift display
        # Note: positive shift means we shifted UP to match, so user sang LOWER
        if octave_shift != 0:
            octave_direction = "lower" if octave_shift > 0 else "higher"
            octave_info = f"Octave adjustment: {octave_shift:+d} semitones (you sang 1 octave {octave_direction})"
        else:
            octave_info = "Octave adjustment: none (correct octave)"

        return ui.div(
            ui.p(feedback),
            ui.p(f"Mean error: {mae_cents:.1f} cents"),
            ui.p(octave_info),
            ui.p(f"Detected voice: {detected_voice}"),
            class_="alert alert-info"
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

    # Handle info button click - show grade info modal
    @reactive.Effect
    @reactive.event(input.grade_info_button)
    async def _():
        current_grade = app_state.level()

        # Create grade-specific content
        if current_grade == 5:
            modal_content = ui.div(
                ui.h3(f"Grade {current_grade} - Voice Singing Only"),
                ui.p("At this level:"),
                ui.tags.ul(
                    ui.tags.li("Focus on single voice singing exercises"),
                    ui.tags.li("Simple melodies for voice practice"),
                    ui.tags.li("Grade 5 does not include cadence identification")
                ),
                ui.p(ui.strong("Tip:"), " Select Grade 6 or higher for cadence identification exercises.")
            )
        else:
            # Different cadence types available by grade
            cadence_types = [ct.value.capitalize() for ct in CADENCE_TYPES_BY_GRADE[current_grade]]
            cadence_list = ", ".join(cadence_types[:-1]) + f" and {cadence_types[-1]}" if len(cadence_types) > 1 else cadence_types[0]

            voice_info = ""
            if current_grade == 6:
                voice_info = "In Voice Singing, you'll focus on the upper (soprano) part."
            elif current_grade >= 7:
                voice_info = "In Voice Singing, you'll focus on the lower (bass) part."

            modal_content = ui.div(
                ui.h3(f"Grade {current_grade} Information"),
                ui.p("At this level:"),
                ui.tags.ul(
                    ui.tags.li(f"Cadence types: {cadence_list}"),
                    ui.tags.li(f"{'Three' if current_grade == 8 else 'Two'}-part harmony exercises"),
                    ui.tags.li(voice_info)
                ),
                ui.p(ui.strong("Tip:"), " Listen carefully to the relationship between the final two chords.")
            )

        # Show the modal
        ui.modal_show(
            ui.modal(
                modal_content,
                title=f"Grade {current_grade} Information",
                easy_close=True,
                footer=ui.div(
                    ui.input_action_button("modal_close", "Close", class_="btn-primary")
                )
            )
        )

    # Reactive effect: Update voice generator when grade changes
    @reactive.Effect
    def _():
        current_grade = app_state.level()
        voice_generator.set(create_voice_generator(current_grade))

# Create app with static files from www directory
www_dir = Path(__file__).parent / "www"
app = App(app_ui, app_server, static_assets=www_dir)