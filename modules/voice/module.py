"""
Shiny module for voice singing.

This module defines the UI and server functions for the voice singing feature.
"""
import logging
from shiny import module, ui, reactive, render
from config.app_config import VOICE_CONFIG_BY_GRADE

from state.voice_state import VoiceState
from .components import (
    create_voice_control_section,
    create_voice_instructions,
    create_voice_recording_indicator,
    create_voice_feedback_section,
    create_voice_notation_section
)
from .handlers import (
    generate_voice_melody,
    replay_voice_melody
)

logger = logging.getLogger(__name__)


@module.ui
def voice_ui(id):
    """Create UI for voice singing tab."""
    return ui.div(
        create_voice_instructions(id),
        create_voice_control_section(id),
        create_voice_recording_indicator(id),
        create_voice_feedback_section(id),
        create_voice_notation_section(id),
    )


@module.server
def voice_server(id, input, output, session, voice_state, app_state, voice_generator):
    """
    Server logic for voice singing tab.

    Args:
        id: Module ID function
        input: Module input
        output: Module output
        session: Shiny session
        voice_state: VoiceState instance
        app_state: AppState instance
        voice_generator: Voice generator reactive value
    """
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
        logger.info("Voice playback completed")
        # Keep recording for 2 more seconds (handled by JavaScript)

    # Handle recording stopped
    @reactive.effect
    @reactive.event(input.recording_stopped)
    async def _():
        voice_state.is_recording.set(False)
        logger.info("Recording stopped")

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

            logger.info(f"Received pitch data: {len(pitch_data.get('data', []))} samples")
            logger.info(f"Duration: {pitch_data.get('duration', 0):.2f}s")
            logger.info(f"Sample rate: {pitch_data.get('sampleRate', 0):.1f} Hz")

            # Store in state
            voice_state.recorded_pitch.set(pitch_data)

            # Extract recorded frequencies (filter out null values)
            recorded_data = pitch_data.get('data', [])
            recorded_frequencies = []
            for sample in recorded_data:
                freq = sample.get('frequency')
                if freq is not None and freq > 0:
                    recorded_frequencies.append(freq)

            logger.info(f"Valid pitch samples: {len(recorded_frequencies)} / {len(recorded_data)} ({len(recorded_frequencies)/len(recorded_data)*100:.1f}%)")

            if len(recorded_frequencies) < 10:
                logger.warning("Not enough valid pitch data for grading")
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
                logger.error(f"No target melody for voice: {target_voice_name}")
                return

            logger.info(f"[Voice Grading] Grade {grade}: Grading against {target_voice_name} voice")
            logger.info(f"  Target melody: {len(target_melody)} notes")

            # Use the actual recording sample rate for target generation
            # This ensures time alignment between target and recording
            recording_sample_rate = pitch_data.get('sampleRate', 20)
            logger.info(f"  Using sample rate: {recording_sample_rate:.1f} Hz (from recording)")

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
                    logger.info(f"Detected voice: {detected_voice} (distance: {voice_distance:.2f} semitones)")

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

            # Find the best octave shift (-1, 0, or +1 octaves)
            best_octave_shift, shift_distance = find_best_octave_shift(
                recorded_midi_filtered,
                target_midi
            )

            logger.info(f"Best octave shift: {best_octave_shift} semitones ({best_octave_shift // 12:+d} octave)")

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

            logger.info(f"DTW Alignment:")
            logger.info(f"  Path length: {len(aligned_path)} pairs")
            logger.info(f"  Recorded coverage: {len(recorded_indices_used)}/{len(recorded_midi_filtered)} samples ({coverage_recorded:.1f}%)")
            logger.info(f"  Target coverage: {len(target_indices_used)}/{len(target_midi)} samples ({coverage_target:.1f}%)")

            # Grade performance with octave shift
            mae_cents = grade_performance(
                recorded_midi_filtered,
                target_midi,
                aligned_path,
                octave_shift=best_octave_shift
            )

            logger.info(f"MAE: {mae_cents:.1f} cents")
            logger.info(f"DTW distance: {dtw_distance:.1f}")

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

                logger.info("Pitch plot generated and sent to UI")

                # Show Try Again button after grading is complete
                await session.send_custom_message("updateVoiceButtons", {
                    "tryAgainVisible": True
                })

            except Exception as plot_error:
                logger.error(f"Error creating pitch plot: {plot_error}")

        except Exception as e:
            logger.error(f"Error during grading: {e}")
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