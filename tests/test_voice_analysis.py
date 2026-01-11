"""
Unit tests for voice analysis module.

Run with: pytest tests/test_voice_analysis.py
"""
import numpy as np
import pytest
from modules.music_theory.voice_analysis import (
    melody_to_pitch_contour,
    hz_to_midi,
    apply_median_filter,
    align_performance,
    detect_voice_error,
    grade_performance
)


def test_melody_to_pitch_contour():
    """Test melody to pitch contour conversion."""
    # Create simple melody: C4 for 1s, D4 for 1s
    melody = [
        (60, 0.0, 1.0),  # C4
        (62, 1.0, 1.0),  # D4
    ]

    contour = melody_to_pitch_contour(melody, sample_rate=20)

    # Should have 40 samples total (2 seconds * 20 samples/sec)
    assert len(contour) == 40

    # First 20 samples should be C4 frequency (~261.63 Hz)
    c4_freq = 440.0 * (2.0 ** ((60 - 69) / 12.0))
    assert np.allclose(contour[:20], c4_freq, rtol=0.01)

    # Next 20 samples should be D4 frequency (~293.66 Hz)
    d4_freq = 440.0 * (2.0 ** ((62 - 69) / 12.0))
    assert np.allclose(contour[20:40], d4_freq, rtol=0.01)


def test_hz_to_midi():
    """Test Hz to MIDI conversion."""
    # A4 = 440 Hz = MIDI 69
    frequencies = np.array([440.0, 880.0, 220.0])
    midi = hz_to_midi(frequencies)

    assert np.allclose(midi[0], 69.0, atol=0.1)  # A4
    assert np.allclose(midi[1], 81.0, atol=0.1)  # A5 (octave up)
    assert np.allclose(midi[2], 57.0, atol=0.1)  # A3 (octave down)


def test_apply_median_filter():
    """Test median filter removes octave jumps."""
    # Create data with octave jump (outlier)
    midi_values = np.array([60.0, 60.0, 72.0, 60.0, 60.0])  # 72 is outlier (octave up)

    filtered = apply_median_filter(midi_values, kernel_size=3)

    # Outlier should be reduced
    assert filtered[2] < 65.0  # Should be closer to 60 than 72


def test_align_performance():
    """Test DTW alignment."""
    # Create synthetic recorded and target sequences
    recorded = np.array([60.0, 61.0, 62.0, 63.0])
    target = np.array([60.0, 60.0, 62.0, 63.0])

    path, distance = align_performance(recorded, target)

    # Path should be a list of tuples
    assert isinstance(path, list)
    assert len(path) > 0
    assert isinstance(path[0], tuple)

    # Distance should be positive
    assert distance >= 0


def test_detect_voice_error():
    """Test voice detection with octave equivalence."""
    # Soprano voice (higher)
    soprano_midi = np.array([72.0, 74.0, 76.0])  # C5, D5, E5

    # Bass voice (lower)
    bass_midi = np.array([48.0, 50.0, 52.0])  # C3, D3, E3

    # Recorded as bass (same pitch class, different octave)
    recorded_midi = np.array([60.0, 62.0, 64.0])  # C4, D4, E4

    detected_voice, distance = detect_voice_error(
        recorded_midi,
        soprano_midi,
        bass_midi
    )

    # Should detect bass voice (same pitch classes)
    assert detected_voice == "bass"
    assert distance < 1.0  # Should be very close (within 1 semitone)


def test_grade_performance():
    """Test performance grading."""
    # Perfect performance (no error)
    recorded = np.array([60.0, 62.0, 64.0])
    target = np.array([60.0, 62.0, 64.0])

    # Create simple 1:1 alignment path
    path = [(0, 0), (1, 1), (2, 2)]

    mae_cents = grade_performance(recorded, target, path)

    # Should have 0 cents error
    assert mae_cents == 0.0

    # Performance with 50 cents error (half semitone)
    recorded_off = np.array([60.5, 62.5, 64.5])

    mae_cents_off = grade_performance(recorded_off, target, path)

    # Should have 50 cents error
    assert np.isclose(mae_cents_off, 50.0, atol=1.0)


def test_melody_to_pitch_contour_empty():
    """Test melody to pitch contour with empty melody."""
    melody = []
    contour = melody_to_pitch_contour(melody)

    assert len(contour) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
