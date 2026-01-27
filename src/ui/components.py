"""
Shared UI components for g8aural application.

This module provides reusable UI component creation functions that can be used
across multiple modules with appropriate namespace handling.
"""
from shiny import ui


def create_feedback_section(id=None):
    """
    Create a feedback message section.

    Args:
        id: Optional namespace function for modular usage

    Returns:
        Feedback section UI component
    """
    output_id = "feedback_message" if id is None else id("feedback_message")

    return ui.div(
        ui.output_ui(output_id),
        class_="feedback-section"
    )


def create_next_button_section(id=None):
    """
    Create the next cadence button section.

    Args:
        id: Optional namespace function for modular usage

    Returns:
        Next button section UI component
    """
    btn_id = "next_btn" if id is None else id("next_btn")

    return ui.div(
        ui.input_action_button(
            btn_id,
            "Next Cadence",
            class_="btn-success btn-lg",
            style="display: none;"
        ),
        class_="next-section"
    )


def create_notation_section(id=None):
    """
    Create the notation display section.

    Args:
        id: Optional namespace function for modular usage

    Returns:
        Notation section UI component
    """
    container_id = "notation-container" if id is None else f"{id._ns_name}-notation-container"

    return ui.div(
        ui.div(id=container_id),
        class_="notation-section",
        style="display: none;"
    )


def create_voice_notation_section(id=None):
    """
    Create notation display section for voice melodies.

    Args:
        id: Optional namespace function for modular usage

    Returns:
        Voice notation section UI component
    """
    container_id = "voice-notation-container" if id is None else f"{id._ns_name}-voice-notation-container"

    return ui.div(
        ui.div(id=container_id),
        class_="notation-section",
        style="display: none;"
    )