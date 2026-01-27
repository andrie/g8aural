# Chord Test App

A testing application for evaluating the musical quality of chord progressions with different voice leading algorithms.

## Overview

This application allows comparison between:
- Standard voice leading implementation
- Enhanced voice leading with improved musicality

The app generates chord progressions using either algorithm and collects user feedback to guide further improvements.

## Features

- Grade-specific chord progressions (Grades 5-8)
- Four cadence types (Perfect, Plagal, Imperfect, Interrupted)
- Toggle between standard and enhanced voice leading
- Visual notation rendering with VexFlow
- Audio playback with piano samples (Tone.js)
- User feedback collection system

## Enhanced Voice Leading Improvements

The enhanced voice leading algorithm includes:
1. **Extended voice ranges** - Particularly wider bass range (E2-C4)
2. **Improved voice motion rules**:
   - Contrary motion between outer voices
   - Common tone retention
   - Stepwise motion preference
   - Leading tone resolution
3. **Better spacing** - More even distribution of voices
4. **Special handling** for cadential patterns

## Running the App

```bash
# Run the main application
shiny run app.py

# Run the chord test app
shiny run chord_test_app.py
```

## Feedback Analysis

The application collects and stores feedback in the `feedback/` directory as JSONL files. The feedback analysis module can generate statistical reports and visualizations to help identify strengths and weaknesses in the voice leading algorithms.

## Implementation Plan

The implementation follows this phased approach:

1. **Enhanced Voice Leading**:
   - Extended voice ranges
   - Improved voice motion rules
   - Better spacing algorithms
   - Special cadential pattern handling

2. **Enhanced Progression Generator**:
   - Integration with enhanced voice leading
   - Better inversion handling
   - Maintaining compatibility

3. **Chord Test App**:
   - User interface for testing and feedback
   - A/B testing between algorithms
   - Feedback collection and storage

4. **Analysis Tools**:
   - Statistical analysis of feedback
   - Visualization generation
   - Insight extraction for future improvements