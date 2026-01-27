"""
UI components for the cadence identification module.

This module provides UI component factory functions specific to the cadence identification feature.
"""
from shiny import ui


def create_control_section(id):
    """Create the control section with Play and Hint buttons."""
    return ui.div(
        ui.input_action_button(
            id("play_btn"),
            "Play Cadence",
            class_="btn-primary btn-lg"
        ),
        ui.input_action_button(
            id("hint_btn"),
            "Show Hint",
            class_="btn-warning btn-lg",
            style="margin-left: 10px;"
        ),
        class_="control-section"
    )


def create_answer_section(id):
    """Create the answer section with cadence type buttons."""
    return ui.div(
        ui.h3("Select the cadence type:"),
        ui.div(
            ui.input_action_button(id("perfect_btn"), "Perfect", class_="cadence-btn"),
            ui.input_action_button(id("plagal_btn"), "Plagal", class_="cadence-btn"),
            ui.input_action_button(id("imperfect_btn"), "Imperfect", class_="cadence-btn"),
            ui.input_action_button(id("interrupted_btn"), "Interrupted", class_="cadence-btn"),
            class_="answer-grid"
        ),
        class_="answer-section"
    )


def create_feedback_section(id):
    """Create the feedback message section."""
    return ui.div(
        ui.output_ui(id("feedback_message")),
        class_="feedback-section"
    )


def create_next_button_section(id):
    """Create the next cadence button section."""
    return ui.div(
        ui.input_action_button(
            id("next_btn"),
            "Next Cadence",
            class_="btn-success btn-lg",
            style="display: none;"
        ),
        class_="next-section"
    )


def create_notation_section(id):
    """Create the notation display section."""
    return ui.div(
        ui.div(id=f"{id._ns_name}-notation-container"),
        class_="notation-section",
        style="display: none;"
    )