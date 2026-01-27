"""
Voice analysis module for pitch detection and grading.

This module provides utilities for:
- Converting melodies to pitch contours
- Aligning recorded performances using DTW
- Detecting wrong voice errors
- Grading performance accuracy
- Visualizing pitch contours
"""
import numpy as np
from typing import List, Tuple, Optional, Dict


def melody_to_pitch_contour(
    melody: List[Tuple[int, float, float]],
    sample_rate: int = 20
) -> np.ndarray:
    """
    Convert melody to pitch contour (time series of frequencies).

    Args:
        melody: List of (midi_note, start_time, duration) tuples
        sample_rate: Samples per second for output contour

    Returns:
        Array of frequencies (Hz) sampled at specified rate
    """
    if not melody:
        return np.array([])

    # Find the total duration
    max_end_time = max(start + duration for _, start, duration in melody)
    total_samples = int(max_end_time * sample_rate)

    # Initialize contour array
    contour = np.zeros(total_samples)

    # Fill in each note
    for midi_note, start_time, duration in melody:
        # Convert MIDI to frequency: f = 440 * 2^((m - 69) / 12)
        freq = 440.0 * (2.0 ** ((midi_note - 69) / 12.0))

        # Calculate sample indices
        start_idx = int(start_time * sample_rate)
        end_idx = int((start_time + duration) * sample_rate)

        # Clamp to array bounds
        start_idx = max(0, min(start_idx, total_samples))
        end_idx = max(0, min(end_idx, total_samples))

        # Fill in the frequency
        contour[start_idx:end_idx] = freq

    return contour


def hz_to_midi(frequencies: np.ndarray) -> np.ndarray:
    """
    Convert frequencies in Hz to MIDI note numbers.

    Args:
        frequencies: Array of frequencies (Hz), may contain None/null values

    Returns:
        Array of MIDI note numbers
    """
    # Handle array of frequencies
    # Formula: m = 69 + 12 * log2(f / 440)
    midi_values = 69 + 12 * np.log2(frequencies / 440.0)
    return midi_values


def apply_median_filter(
    midi_values: np.ndarray,
    kernel_size: int = 5
) -> np.ndarray:
    """
    Apply median filter to remove octave jumps and pitch tracking errors.

    Args:
        midi_values: Array of MIDI note numbers
        kernel_size: Size of median filter window (odd number)

    Returns:
        Filtered MIDI values
    """
    from scipy.signal import medfilt

    # Apply median filter with specified kernel size
    filtered = medfilt(midi_values, kernel_size=kernel_size)
    return filtered


def align_performance(
    recorded: np.ndarray,
    target: np.ndarray
) -> Tuple[List[Tuple[int, int]], float]:
    """
    Align recorded performance to target using Dynamic Time Warping.

    Args:
        recorded: Recorded MIDI note sequence
        target: Target MIDI note sequence

    Returns:
        Tuple of (alignment_path, dtw_distance)
        alignment_path: List of (recorded_index, target_index) pairs
        dtw_distance: Total DTW distance
    """
    from fastdtw import fastdtw

    # Define distance metric: L1 distance in semitones
    # fastdtw passes rows from the 2D arrays, so a and b are arrays
    def musical_distance(a, b):
        return abs(float(a[0]) - float(b[0]))

    # Reshape arrays for fastdtw (needs 2D arrays)
    recorded_2d = recorded.reshape(-1, 1)
    target_2d = target.reshape(-1, 1)

    # Run DTW with constraint window
    distance, path = fastdtw(
        recorded_2d,
        target_2d,
        radius=20,  # Constraint window for faster computation
        dist=musical_distance
    )

    return path, distance


def detect_voice_error(
    recorded_midi: np.ndarray,
    soprano_midi: np.ndarray,
    bass_midi: np.ndarray
) -> Tuple[str, float]:
    """
    Detect if student sang wrong voice (octave-invariant).

    Args:
        recorded_midi: Student's recorded MIDI notes
        soprano_midi: Target soprano voice MIDI notes
        bass_midi: Target bass voice MIDI notes

    Returns:
        Tuple of (detected_voice, distance)
        detected_voice: "soprano" or "bass"
        distance: Mean distance to detected voice (semitones)
    """
    # Use pitch class (mod 12) to handle octave shifts
    recorded_pc = recorded_midi % 12
    soprano_pc = soprano_midi % 12
    bass_pc = bass_midi % 12

    # Calculate minimum distance considering octave equivalence
    # For each recorded pitch class, find the minimum distance to each target
    def min_octave_distance(rec_pc, target_pc):
        """Calculate minimum distance considering octave equivalence."""
        distances = [
            np.abs(rec_pc - target_pc),
            np.abs(rec_pc - target_pc + 12),
            np.abs(rec_pc - target_pc - 12)
        ]
        return np.minimum.reduce(distances)

    # Align lengths by truncating to shorter
    min_len = min(len(recorded_pc), len(soprano_pc), len(bass_pc))
    recorded_pc = recorded_pc[:min_len]
    soprano_pc = soprano_pc[:min_len]
    bass_pc = bass_pc[:min_len]

    # Calculate mean distances
    soprano_distance = np.mean(min_octave_distance(recorded_pc, soprano_pc))
    bass_distance = np.mean(min_octave_distance(recorded_pc, bass_pc))

    # Determine which voice is closer (no bias)
    if soprano_distance < bass_distance:
        return "soprano", float(soprano_distance)
    else:
        return "bass", float(bass_distance)


def find_best_octave_shift(
    recorded_midi: np.ndarray,
    target_midi: np.ndarray
) -> Tuple[int, float]:
    """
    Find the best octave shift for the recorded performance.

    Tries shifting by -1, 0, or +1 octaves and returns the shift
    that gives the best (lowest) alignment distance.

    Args:
        recorded_midi: Student's recorded MIDI notes
        target_midi: Target MIDI notes

    Returns:
        Tuple of (best_shift_semitones, best_distance)
        best_shift_semitones: Optimal shift in semitones (-12, 0, or +12)
        best_distance: DTW distance with optimal shift
    """
    from fastdtw import fastdtw

    # Define distance metric
    def musical_distance(a, b):
        return abs(float(a[0]) - float(b[0]))

    best_shift = 0
    best_distance = float('inf')

    # Try -1 octave, 0 octaves, +1 octave
    for shift in [-12, 0, 12]:
        # Apply octave shift
        shifted_midi = recorded_midi + shift

        # Truncate to same length
        min_len = min(len(shifted_midi), len(target_midi))
        shifted_truncated = shifted_midi[:min_len]
        target_truncated = target_midi[:min_len]

        # Reshape for fastdtw
        shifted_2d = shifted_truncated.reshape(-1, 1)
        target_2d = target_truncated.reshape(-1, 1)

        # Calculate DTW distance
        distance, _ = fastdtw(
            shifted_2d,
            target_2d,
            radius=20,
            dist=musical_distance
        )

        # Track best shift
        if distance < best_distance:
            best_distance = distance
            best_shift = shift

    return best_shift, best_distance


def grade_performance(
    recorded_midi: np.ndarray,
    target_midi: np.ndarray,
    aligned_path: List[Tuple[int, int]],
    octave_shift: int = 0
) -> float:
    """
    Calculate mean absolute error in cents after DTW alignment.

    Args:
        recorded_midi: Student's recorded MIDI notes
        target_midi: Target MIDI notes
        aligned_path: DTW alignment path
        octave_shift: Octave shift to apply to recorded (in semitones)

    Returns:
        Mean absolute error in cents (1 semitone = 100 cents)
    """
    # Apply octave shift to recorded performance
    shifted_recorded = recorded_midi + octave_shift

    # Extract aligned sequences
    aligned_recorded = np.array([shifted_recorded[i] for i, j in aligned_path])
    aligned_target = np.array([target_midi[j] for i, j in aligned_path])

    # Calculate error in semitones
    error_semitones = np.abs(aligned_recorded - aligned_target)

    # Convert to cents (1 semitone = 100 cents)
    error_cents = error_semitones * 100.0

    # Calculate mean absolute error
    mae_cents = float(np.mean(error_cents))

    return mae_cents


def create_pitch_plot(
    recorded: np.ndarray,
    target: np.ndarray,
    timestamps: np.ndarray
) -> str:
    """
    Create pitch contour plot using plotnine.

    Args:
        recorded: Recorded pitch values (MIDI note numbers)
        target: Target pitch values (MIDI note numbers)
        timestamps: Time values for x-axis (seconds)

    Returns:
        Base64-encoded PNG image
    """
    try:
        import pandas as pd
        import io
        import base64

        # Try to import plotnine - might not be installed
        try:
            from plotnine import ggplot, aes, geom_line, geom_point, labs, theme_minimal, scale_y_continuous
            import matplotlib.pyplot as plt
        except ImportError:
            print("plotnine or matplotlib not installed. Using fallback plot method.")
            # Create a simple fallback image
            return create_fallback_plot()

        # Convert MIDI to note names for y-axis labels
        def midi_to_note_name(midi):
            """Convert MIDI number to note name (e.g., 60 -> C4)."""
            note_names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
            octave = int(midi / 12) - 1
            note = note_names[int(midi % 12)]
            return f"{note}{octave}"

        # Align lengths by truncating to shorter
        min_len = min(len(recorded), len(target), len(timestamps))
        recorded = recorded[:min_len]
        target = target[:min_len]
        timestamps = timestamps[:min_len]

        # Create dataframe for target (blue line)
        target_df = pd.DataFrame({
            'time': timestamps,
            'midi': target,
            'type': 'Target'
        })

        # Create dataframe for recorded (red points)
        recorded_df = pd.DataFrame({
            'time': timestamps,
            'midi': recorded,
            'type': 'Recorded'
        })

        # Combine dataframes
        df = pd.concat([target_df, recorded_df], ignore_index=True)

        # Create plot
        plot = (
            ggplot(df, aes(x='time', y='midi', color='type'))
            + geom_line(data=target_df, size=1.5)
            + geom_point(data=recorded_df, size=2, alpha=0.7)
            + labs(
                title='Pitch Accuracy Comparison',
                x='Time (seconds)',
                y='Pitch (MIDI note)',
                color='Voice'
            )
            + theme_minimal()
            + scale_y_continuous(
                breaks=range(int(df['midi'].min()), int(df['midi'].max()) + 1, 2),
                labels=lambda midi_list: [midi_to_note_name(m) for m in midi_list]
            )
        )

        # Save to base64 string
        buf = io.BytesIO()
        plot.save(buf, format='png', dpi=100, width=10, height=6, verbose=False)
        buf.seek(0)
        img_base64 = base64.b64encode(buf.read()).decode('utf-8')
        plt.close()  # Clean up

        return img_base64

    except Exception as e:
        print(f"Error creating pitch plot: {str(e)}")
        return create_fallback_plot()


def create_fallback_plot() -> str:
    """Create a simple fallback plot when plotnine is not available."""
    # Base64 encoded small transparent PNG
    return "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
