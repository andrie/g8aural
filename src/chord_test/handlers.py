"""
Handlers for chord test app.

These functions handle the generation of chord progressions and
the collection and storage of feedback data.
"""
import os
import json
import datetime
from typing import Dict, Any

from src.music_theory.cadences import CadenceType
from src.music_theory.progression import ChordProgressionGenerator
from src.music_theory.enhanced_progression import EnhancedChordProgressionGenerator


def get_timestamp() -> str:
    """Get current timestamp in ISO format."""
    return datetime.datetime.now().isoformat()


def ensure_feedback_dir():
    """Ensure feedback directory exists."""
    os.makedirs("feedback", exist_ok=True)


def save_feedback(feedback: Dict[str, Any]):
    """
    Save feedback to JSONL file.

    Args:
        feedback: Feedback data to save
    """
    ensure_feedback_dir()

    # Create filename with date
    date = datetime.datetime.now().strftime("%Y-%m-%d")
    filename = f"feedback/chord_feedback_{date}.jsonl"

    # Append feedback to file
    with open(filename, "a") as f:
        # Convert non-serializable objects to strings
        serializable_feedback = {}
        for key, value in feedback.items():
            if key == "progression":
                # Extract only the necessary data from the progression
                serializable_feedback[key] = {
                    "key": value.get("key", ""),
                    "chord_symbols": value.get("symbols", []),
                    "note_names": value.get("note_names", [])
                }
            else:
                serializable_feedback[key] = value

        f.write(json.dumps(serializable_feedback) + "\n")


def generate_chord_progression(grade: int, cadence_type: str, use_enhanced: bool = False) -> Dict[str, Any]:
    """
    Generate chord progression with either regular or enhanced voice leading.

    Args:
        grade: Grade level (5-8)
        cadence_type: Type of cadence (perfect, plagal, imperfect, interrupted)
        use_enhanced: Whether to use enhanced voice leading

    Returns:
        Dictionary with progression data
    """
    cadence_type_enum = CadenceType(cadence_type)

    # Convert grade to int since it's coming from the UI as a string
    grade = int(grade)

    # Configure generator based on grade
    use_strict_cadence = (grade == 8)
    use_sevenths = (grade >= 7)

    # Select algorithm version
    if use_enhanced:
        # Create enhanced generator with improved voice leading
        generator = EnhancedChordProgressionGenerator(
            use_strict_cadence=use_strict_cadence,
            use_sevenths=use_sevenths,
            keys=["C", "G", "F", "D", "Bb", "A", "Eb"]  # Common keys
        )
    else:
        # Use regular generator
        generator = ChordProgressionGenerator(
            use_strict_cadence=use_strict_cadence,
            use_sevenths=use_sevenths,
            keys=["C", "G", "F", "D", "Bb", "A", "Eb"]
        )

    # Generate progression
    progression = generator.generate_progression(cadence_type_enum)

    # Convert to format needed for UI
    # Format the key for VexFlow compatibility (convert flats to proper format)
    key_name = progression[0].key.tonicPitchNameWithCase
    # VexFlow doesn't handle flat notation with '-', it needs 'b'
    if '-' in key_name:
        key_name = key_name.replace('-', 'b')

    # Get the note names with proper formatting for the UI
    note_names = generator.progression_to_note_names(progression)

    # Process the note names to ensure they're in the correct format for VexFlow
    # VexFlow requires notes in format: "note/octave" (e.g., "c/4", "eb/4")
    processed_note_names = []

    for chord in note_names:
        processed_chord = []
        for note in chord:
            # First, ensure flats use 'b' instead of '-'
            if '-' in note:
                note = note.replace('-', 'b')

            # Extract note name (first character)
            note_name = note[0].lower()

            # Extract accidental if present (second character)
            if len(note) > 1 and (note[1] == '#' or note[1] == 'b'):
                note_name += note[1]

            # Extract octave (digit)
            octave = ''.join(filter(str.isdigit, note))

            # Format as "note/octave"
            formatted_note = f"{note_name}/{octave}"
            processed_chord.append(formatted_note)

        processed_note_names.append(processed_chord)

    return {
        "progression": generator.progression_to_midi(progression),
        "note_names": processed_note_names,  # Use the processed note_names in VexFlow format
        "symbols": generator.progression_to_symbols(progression),
        "key": key_name
    }