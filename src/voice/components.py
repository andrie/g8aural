"""
UI components for the voice singing module.

This module provides UI component factory functions specific to the voice singing feature.
"""
from shiny import ui


def create_voice_control_section(id):
    """Create the control section for voice singing tab."""
    return ui.div(
        ui.input_action_button(
            id("voice_start_btn"),
            "Start Task",
            class_="btn-primary btn-lg"
        ),
        ui.input_action_button(
            id("voice_try_again_btn"),
            "Try Again",
            class_="btn-warning btn-lg",
            style="margin-left: 10px; display: none;"
        ),
        class_="control-section"
    )


def create_voice_instructions(id):
    """Create grade-adaptive instructions section for voice singing task."""
    return ui.div(
        ui.output_ui(id("voice_instructions_text")),
        ui.output_ui(id("voice_target_indicator")),
        class_="voice-instructions"
    )


def create_voice_recording_indicator(id):
    """Create recording status indicator with live pitch visualization."""
    return ui.div(
        ui.div(
            ui.span("", class_="recording-dot"),
            ui.span("Recording...", style="margin-left: 8px;"),
            id=f"{id._ns_name}-recording-indicator",
            class_="recording-indicator",
            style="display: none;"
        ),
        ui.tags.canvas(
            id=f"{id._ns_name}-live-pitch-canvas",
            width="600",
            height="150",
            style="display: none; border: 1px solid #ccc; background: #f9f9f9; margin-top: 10px;"
        ),
        class_="recording-section"
    )


def create_voice_feedback_section(id):
    """Create feedback section for voice singing results."""
    return ui.div(
        ui.output_ui(id("voice_feedback_message")),
        ui.div(id=f"{id._ns_name}-voice-pitch-plot", style="margin-top: 20px;"),
        class_="feedback-section"
    )


def create_voice_notation_section(id):
    """Create notation display section for voice melodies."""
    return ui.div(
        ui.div(id=f"{id._ns_name}-voice-notation-container"),
        class_="notation-section",
        style="display: none;"
    )