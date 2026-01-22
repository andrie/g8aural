"""
Event handlers for the voice singing module.

This module contains extracted business logic functions for voice singing.
"""
import random
import logging
from typing import Dict, Any
from config.app_config import VOICE_CONFIG_BY_GRADE
from lib.music_theory.cadences import CadenceType

logger = logging.getLogger(__name__)


async def generate_voice_melody(voice_state, app_state, session, voice_generator):
    """Generate grade-appropriate melody and start playback."""
    try:
        # Get current grade and config
        current_grade = app_state.level()
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
            logger.info(f"  Transposed all voices down 1 octave for Grade {current_grade}")

        # Get target voice for grading
        target_voice = config['target_voice']
        if target_voice is None:
            # Grade 5: single melody, user sings the only voice
            target_voice = 'soprano'

        # Get key
        current_key = progression[0].key.name if progression else 'C'

        # Debug logging
        logger.info(f"[Voice Tab] Grade {current_grade}: Generated {len(voice_parts)}-voice melody")
        logger.info(f"  Cadence: {cadence_type.value} in {current_key}")
        logger.info(f"  Voice parts: {voice_parts}")
        logger.info(f"  Target voice (user sings): {target_voice}")
        for voice_name in voice_parts:
            melody = melodies[voice_name]
            logger.info(f"  {voice_name.capitalize()}: {len(melody)} notes")

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
        logger.error(f"[Voice Tab] Error generating voice melody: {e}")
        raise


async def replay_voice_melody(voice_state, app_state, session, voice_generator):
    """Replay the current melody without generating a new one."""
    try:
        # Get current grade and stored melodies
        current_grade = app_state.level()
        config = VOICE_CONFIG_BY_GRADE.get(current_grade, VOICE_CONFIG_BY_GRADE[8])
        target_voice_name = voice_state.target_voice()

        # Get stored melodies
        soprano_melody = voice_state.soprano_melody()
        bass_melody = voice_state.bass_melody()

        if not soprano_melody and not bass_melody:
            logger.info("[Voice Tab] No melody to replay - generating new one")
            await generate_voice_melody(voice_state, app_state, session, voice_generator)
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

        logger.info(f"[Voice Tab] Grade {current_grade}: Replaying {len(voice_parts)}-voice melody")
        logger.info(f"  Target voice: {target_voice_name}")

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
        logger.error(f"[Voice Tab] Error replaying voice melody: {e}")
        raise