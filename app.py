"""
ABRSM Grade 8 Cadence Training - Shiny for Python Frontend
"""
from shiny import App, ui, render, reactive
import random
from pathlib import Path
from modules.music_theory.cadences import CadenceType
from modules.music_theory.progression import ChordProgressionGenerator
from config.app_config import KEYS_BY_GRADE, CADENCE_TYPES_BY_GRADE, GENERATOR_CONFIG, VOICE_CONFIG_BY_GRADE
from ui.components import (
    create_header,
    create_grade_selection,
    create_control_section,
    create_answer_section,
    create_feedback_section,
    create_next_button_section,
    create_notation_section,
    create_voice_control_section,
    create_voice_instructions,
    create_voice_recording_indicator,
    create_voice_feedback_section,
    create_voice_notation_section
)
from state.game_state import ProgressionState, FeedbackState, GameFlowState, GradeState, VoiceState
from handlers.game_logic import (
    validate_guess,
    generate_new_cadence_data,
    handle_correct_answer,
    handle_incorrect_answer,
    initialize_new_cadence
)


# Tab UI Components
def create_cadence_tab_ui():
    """
    Create UI for cadence identification tab.

    Returns:
        List of UI components for cadence identification
    """
    return [
        create_control_section(),
        create_answer_section(),
        create_feedback_section(),
        create_next_button_section(),
        create_notation_section(),
    ]


def create_voice_singing_tab_ui():
    """
    Create UI for voice singing tab.

    Returns:
        List of UI components for voice singing
    """
    return [
        create_voice_instructions(),
        create_voice_control_section(),
        create_voice_recording_indicator(),
        create_voice_feedback_section(),
        create_voice_notation_section(),
    ]


# UI Layout with tab structure
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
        # Load microphone.js as ES module (imports Pitchy internally)
        ui.tags.script(src="microphone.js", type="module"),
        ui.tags.script(src="voice-playback.js"),
        ui.tags.script(src="pitch-plot.js"),
    ),
    # Header and grade selection (shared across all tabs)
    create_header(),
    *create_grade_selection(),  # Unpacks list of components (slider + modal)
    # Tab navigation
    ui.navset_tab(
        ui.nav_panel(
            "Cadence Identification",
            *create_cadence_tab_ui()
        ),
        ui.nav_panel(
            "Voice Singing",
            *create_voice_singing_tab_ui()
        ),
        id="main_tabs"
    ),
)

# Tab Server Logic
def create_cadence_tab_server(input, output, session, progression_state, feedback_state, game_flow, grade_state, generator):
    """
    Create server logic for cadence identification tab.

    Args:
        input: Shiny input object
        output: Shiny output object
        session: Shiny session object
        progression_state: ProgressionState instance
        feedback_state: FeedbackState instance
        game_flow: GameFlowState instance
        grade_state: GradeState instance
        generator: Reactive value containing ChordProgressionGenerator
    """
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


# Server logic
def server(input, output, session):
    # Grouped reactive state
    progression_state = ProgressionState.create()
    feedback_state = FeedbackState.create()
    game_flow = GameFlowState.create()
    grade_state = GradeState.create()
    voice_state = VoiceState.create()  # Voice singing tab state

    # Reactive generator for cadence identification (no global variable!)
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
    fetch_new_cadence = create_cadence_tab_server(
        input, output, session,
        progression_state, feedback_state, game_flow, grade_state, generator
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
            grade_state.level.set(saved_grade)
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
        current_grade = grade_state.level()
        voice_generator.set(create_voice_generator(current_grade))
        print(f"[Voice Tab] Voice generator updated to Grade {current_grade}")

    # ========================================
    # Voice Singing Tab Handlers
    # ========================================

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
        await replay_voice_melody()

    # Helper function to replay the current melody
    async def replay_voice_melody():
        """Replay the current melody without generating a new one."""
        try:
            # Get current grade and stored melodies
            current_grade = grade_state.level()
            config = VOICE_CONFIG_BY_GRADE.get(current_grade, VOICE_CONFIG_BY_GRADE[8])
            target_voice_name = voice_state.target_voice()

            # Get stored melodies
            soprano_melody = voice_state.soprano_melody()
            bass_melody = voice_state.bass_melody()

            if not soprano_melody and not bass_melody:
                print("[Voice Tab] No melody to replay - generating new one")
                await generate_voice_melody()
                return

            # Reconstruct melodies dict based on grade
            voice_parts = config['voice_parts']
            melodies = {}
            if 'soprano' in voice_parts and soprano_melody:
                melodies['soprano'] = soprano_melody
            if 'bass' in voice_parts and bass_melody:
                melodies['bass'] = bass_melody

            # Get key from stored state
            current_key = voice_state.target_key()

            print(f"[Voice Tab] Grade {current_grade}: Replaying {len(voice_parts)}-voice melody")
            print(f"  Target voice: {target_voice_name}")

            # Send to JavaScript for playback
            await session.send_custom_message("playVoiceMelody", {
                "melodies": melodies,
                "targetVoice": target_voice_name,
                "key": current_key,
                "grade": current_grade
            })

            # Start recording (will be triggered by JavaScript)
            voice_state.is_recording.set(True)

            # Hide try again button during recording
            await session.send_custom_message("updateVoiceButtons", {
                "tryAgainVisible": False
            })

        except Exception as e:
            print(f"[Voice Tab] Error replaying voice melody: {e}")
            import traceback
            traceback.print_exc()

    # Helper function to generate and play melody
    async def generate_voice_melody():
        """Generate grade-appropriate melody and start playback."""
        try:
            # Get current grade and config
            current_grade = grade_state.level()
            config = VOICE_CONFIG_BY_GRADE.get(current_grade, VOICE_CONFIG_BY_GRADE[8])
            gen = voice_generator()

            # Generate progression
            cadence_type = random.choice(list(CadenceType))
            progression = gen.generate_progression(cadence_type)

            # Extract voices based on grade configuration
            voice_parts = config['voice_parts']
            melodies = gen.extract_voices(progression, voices=voice_parts)

            # Transpose melodies to comfortable singing range for grades where user sings soprano
            # Grade 5: User sings soprano (single melody)
            # Grade 6: User sings soprano (upper part of 2-voice)
            # Default soprano range: G4-D5 (MIDI 67-74, 392-587 Hz) - too high for most!
            # Transpose down 12 semitones to G3-D4 (MIDI 55-62, 196-294 Hz) - comfortable tenor/alto range
            if current_grade in [5, 6]:
                for voice_name in melodies:
                    transposed_melody = []
                    for midi_note, start_time, duration in melodies[voice_name]:
                        transposed_melody.append((midi_note - 12, start_time, duration))
                    melodies[voice_name] = transposed_melody
                print(f"  Transposed all voices down 1 octave for Grade {current_grade}")

            # Get target voice for grading
            target_voice = config['target_voice']
            if target_voice is None:
                # Grade 5: single melody, user sings the only voice
                target_voice = 'soprano'

            # Get key
            current_key = progression[0].key.name if progression else 'C'

            # Debug logging
            print(f"[Voice Tab] Grade {current_grade}: Generated {len(voice_parts)}-voice melody")
            print(f"  Cadence: {cadence_type.value} in {current_key}")
            print(f"  Voice parts: {voice_parts}")
            print(f"  Target voice (user sings): {target_voice}")
            for voice_name in voice_parts:
                melody = melodies[voice_name]
                print(f"  {voice_name.capitalize()}: {len(melody)} notes")

            # Store in state (handle Grade 5 single melody)
            if current_grade == 5:
                # Grade 5: only soprano melody
                voice_state.set_melodies(
                    soprano=melodies['soprano'],
                    bass=None,  # No bass in Grade 5
                    key=current_key
                )
            else:
                # Grades 6-8: multiple voices
                voice_state.set_melodies(
                    soprano=melodies.get('soprano', None),
                    bass=melodies.get('bass', None),
                    key=current_key
                )

            # Store target voice for grading
            voice_state.target_voice.set(target_voice)

            # Send to JavaScript for playback
            await session.send_custom_message("playVoiceMelody", {
                "melodies": melodies,
                "targetVoice": target_voice,
                "key": current_key,
                "grade": current_grade
            })

            # Start recording (will be triggered by JavaScript)
            voice_state.is_recording.set(True)

            # Hide try again button during recording
            await session.send_custom_message("updateVoiceButtons", {
                "tryAgainVisible": False
            })

        except Exception as e:
            print(f"[Voice Tab] Error generating voice melody: {e}")

    # Generate melody and start playback when "Start Task" is clicked
    @reactive.Effect
    @reactive.event(input.voice_start_btn)
    async def _():
        await generate_voice_melody()

    # Handle voice playback completion
    @reactive.effect
    @reactive.event(input.voice_playback_complete)
    async def _():
        print("Voice playback completed")
        # Keep recording for 2 more seconds (handled by JavaScript)

    # Handle recording stopped
    @reactive.effect
    @reactive.event(input.recording_stopped)
    async def _():
        voice_state.is_recording.set(False)
        print("Recording stopped")

    # Handle recorded pitch data (Phase 5 - DTW and grading)
    @reactive.effect
    @reactive.event(input.recorded_pitch)
    async def _():
        pitch_data = input.recorded_pitch()
        if not pitch_data:
            return

        try:
            from modules.music_theory.voice_analysis import (
                melody_to_pitch_contour,
                hz_to_midi,
                apply_median_filter,
                align_performance,
                detect_voice_error,
                grade_performance,
                find_best_octave_shift
            )
            import numpy as np

            print(f"Received pitch data: {len(pitch_data.get('data', []))} samples")
            print(f"Duration: {pitch_data.get('duration', 0):.2f}s")
            print(f"Sample rate: {pitch_data.get('sampleRate', 0):.1f} Hz")

            # Store in state
            voice_state.recorded_pitch.set(pitch_data)

            # Extract recorded frequencies (filter out null values)
            recorded_data = pitch_data.get('data', [])
            recorded_frequencies = []
            for sample in recorded_data:
                freq = sample.get('frequency')
                if freq is not None and freq > 0:
                    recorded_frequencies.append(freq)

            print(f"Valid pitch samples: {len(recorded_frequencies)} / {len(recorded_data)} ({len(recorded_frequencies)/len(recorded_data)*100:.1f}%)")

            if len(recorded_frequencies) < 10:
                print("Not enough valid pitch data for grading")
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
            grade = grade_state.level()

            if target_melody is None:
                print(f"No target melody for voice: {target_voice_name}")
                return

            print(f"[Voice Grading] Grade {grade}: Grading against {target_voice_name} voice")
            print(f"  Target melody: {len(target_melody)} notes")

            # Use the actual recording sample rate for target generation
            # This ensures time alignment between target and recording
            recording_sample_rate = pitch_data.get('sampleRate', 20)
            print(f"  Using sample rate: {recording_sample_rate:.1f} Hz (from recording)")

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

                    detected_voice, voice_distance = detect_voice_error(
                        recorded_midi_filtered,
                        soprano_midi,
                        bass_midi
                    )
                    print(f"Detected voice: {detected_voice} (distance: {voice_distance:.2f} semitones)")

                    # Check if correct voice was sung
                    if detected_voice == target_voice_name:
                        feedback_prefix = f"✓ You sang the {target_voice_name} voice. "
                    else:
                        other_voice = "soprano" if target_voice_name == "bass" else "bass"
                        feedback_prefix = f"⚠️ You sang the {detected_voice} voice instead of the {target_voice_name} voice. "
                else:
                    feedback_prefix = f"✓ Grading against {target_voice_name} voice. "
            else:
                # Grade 5: single melody, no voice detection needed
                feedback_prefix = "✓ "
                detected_voice = target_voice_name

            # Don't truncate! DTW can handle different length sequences
            # This allows users to sing at their own pace
            print(f"  Recorded: {len(recorded_midi_filtered)} samples")
            print(f"  Target: {len(target_midi)} samples")

            # Find the best octave shift (-1, 0, or +1 octaves)
            best_octave_shift, shift_distance = find_best_octave_shift(
                recorded_midi_filtered,
                target_midi
            )

            print(f"Best octave shift: {best_octave_shift} semitones ({best_octave_shift // 12:+d} octave)")

            # Align recorded to target using DTW with octave shift
            # DTW handles different sequence lengths naturally
            shifted_recorded = recorded_midi_filtered + best_octave_shift
            aligned_path, dtw_distance = align_performance(
                shifted_recorded,
                target_midi
            )

            # Analyze DTW alignment coverage
            recorded_indices_used = set(i for i, j in aligned_path)
            target_indices_used = set(j for i, j in aligned_path)
            coverage_recorded = len(recorded_indices_used) / len(recorded_midi_filtered) * 100
            coverage_target = len(target_indices_used) / len(target_midi) * 100

            print(f"DTW Alignment:")
            print(f"  Path length: {len(aligned_path)} pairs")
            print(f"  Recorded coverage: {len(recorded_indices_used)}/{len(recorded_midi_filtered)} samples ({coverage_recorded:.1f}%)")
            print(f"  Target coverage: {len(target_indices_used)}/{len(target_midi)} samples ({coverage_target:.1f}%)")

            # Grade performance with octave shift
            mae_cents = grade_performance(
                recorded_midi_filtered,
                target_midi,
                aligned_path,
                octave_shift=best_octave_shift
            )

            print(f"MAE: {mae_cents:.1f} cents")
            print(f"DTW distance: {dtw_distance:.1f}")

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
                from modules.music_theory.voice_analysis import create_pitch_plot

                # Apply octave shift to recorded data for visualization
                shifted_recorded_for_plot = recorded_midi_filtered + best_octave_shift

                # Create timestamps for target data using actual recording sample rate
                target_timestamps = np.linspace(0, len(target_midi) / recording_sample_rate, len(target_midi))

                # Create the plot with shifted data (full length, not truncated)
                plot_base64 = create_pitch_plot(
                    shifted_recorded_for_plot,
                    target_midi,
                    target_timestamps
                )

                # Send to JavaScript for display
                await session.send_custom_message("displayPitchPlot", {
                    "imageData": plot_base64
                })

                print("Pitch plot generated and sent to UI")

                # Show Try Again button after grading is complete
                await session.send_custom_message("updateVoiceButtons", {
                    "tryAgainVisible": True
                })

            except Exception as plot_error:
                print(f"Error creating pitch plot: {plot_error}")
                import traceback
                traceback.print_exc()

        except Exception as e:
            print(f"Error during grading: {e}")
            import traceback
            traceback.print_exc()
            voice_state.grading_result.set({
                'feedback': f'Error processing recording: {str(e)}',
                'mae_cents': 0,
                'detected_voice': 'error'
            })

    # Render voice feedback message (placeholder for Phase 5)
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

# Create app with static files from www directory
www_dir = Path(__file__).parent / "www"
app = App(app_ui, server, static_assets=www_dir)
