"""
UI component factory functions for g8aural cadence training.

This module contains reusable UI component creation functions.
"""
from shiny import ui


def create_header():
    """Create the header section with title and description."""
    return ui.div(
        ui.h1("Sharp Ear"),
        ui.p("Interactive Aural Training for ABRSM Grades 6–8"),
        class_="header"
    )


def create_grade_selection():
    """Create the grade selection section with slider and info modal."""
    return [
        # Grade Selection Section
        ui.div(
            ui.div(
                "Current Level: Grade 6",
                id="grade-label",
                class_="grade-label"
            ),
            ui.input_slider(
                "grade_slider",
                label=None,  # No label (using custom label above)
                min=6,
                max=8,
                value=6,
                step=1,
                width="300px"
            ),
            ui.div(
                ui.span("Grade 6"),
                ui.span("Grade 7"),
                ui.span("Grade 8"),
                class_="grade-markers"
            ),
            # Help tooltip
            ui.div(
                ui.tags.button(
                    ui.HTML("&#9432;"),  # Info icon (ℹ)
                    id="grade-info-btn",
                    class_="info-btn",
                    onclick="document.getElementById('grade-info-modal').style.display='flex'"
                ),
                class_="grade-info-container"
            ),
            class_="grade-selection"
        ),
        # Grade info modal (hidden by default)
        ui.div(
            ui.div(
                ui.tags.span(
                    ui.HTML("&times;"),
                    class_="close-btn",
                    onclick="document.getElementById('grade-info-modal').style.display='none'"
                ),
                ui.h3("Grade Level Differences"),
                ui.tags.ul(
                    ui.tags.li(ui.tags.strong("Grade 6:"), " Perfect & Imperfect cadences only (3 chords, root position)"),
                    ui.tags.li(ui.tags.strong("Grade 7:"), " Perfect, Imperfect & Interrupted cadences (3 chords, root position)"),
                    ui.tags.li(ui.tags.strong("Grade 8:"), " All four cadence types including Plagal (4-8 chords: 1-5 lead-in + strict 3-chord cadence, complex inversions)")
                ),
                ui.p(ui.tags.em("All grades use keys with up to 3 sharps or flats (ABRSM syllabus requirement)")),
                id="grade-info-content"
            ),
            id="grade-info-modal",
            class_="grade-info-modal",
            style="display: none;"
        )
    ]


def create_control_section():
    """Create the control section with Play and Hint buttons."""
    return ui.div(
        ui.input_action_button(
            "play_btn",
            "Play Cadence",
            class_="btn-primary btn-lg"
        ),
        ui.input_action_button(
            "hint_btn",
            "Show Hint",
            class_="btn-warning btn-lg",
            style="margin-left: 10px;"
        ),
        class_="control-section"
    )


def create_answer_section():
    """Create the answer section with cadence type buttons."""
    return ui.div(
        ui.h3("Select the cadence type:"),
        ui.div(
            ui.input_action_button("perfect_btn", "Perfect", class_="cadence-btn"),
            ui.input_action_button("plagal_btn", "Plagal", class_="cadence-btn"),
            ui.input_action_button("imperfect_btn", "Imperfect", class_="cadence-btn"),
            ui.input_action_button("interrupted_btn", "Interrupted", class_="cadence-btn"),
            class_="answer-grid"
        ),
        class_="answer-section"
    )


def create_feedback_section():
    """Create the feedback message section."""
    return ui.div(
        ui.output_ui("feedback_message"),
        class_="feedback-section"
    )


def create_next_button_section():
    """Create the next cadence button section."""
    return ui.div(
        ui.input_action_button(
            "next_btn",
            "Next Cadence",
            class_="btn-success btn-lg",
            style="display: none;"
        ),
        class_="next-section"
    )


def create_notation_section():
    """Create the notation display section."""
    return ui.div(
        ui.div(id="notation-container"),
        class_="notation-section",
        style="display: none;"
    )


# ========================================
# Voice Singing Tab Components
# ========================================

def create_voice_control_section():
    """Create the control section for voice singing tab."""
    return ui.div(
        ui.input_action_button(
            "voice_start_btn",
            "Start Task",
            class_="btn-primary btn-lg"
        ),
        ui.input_action_button(
            "voice_try_again_btn",
            "Try Again",
            class_="btn-warning btn-lg",
            style="margin-left: 10px; display: none;"
        ),
        class_="control-section"
    )


def create_voice_instructions():
    """Create instructions section for voice singing task."""
    return ui.div(
        ui.h3("Instructions"),
        ui.tags.ol(
            ui.tags.li("Click 'Start Task' to hear a two-part melody"),
            ui.tags.li("Listen to both voices (soprano is higher, bass is lower)"),
            ui.tags.li("Sing the bass (lower) voice while recording"),
            ui.tags.li("Receive feedback on pitch accuracy")
        ),
        class_="voice-instructions"
    )


def create_voice_recording_indicator():
    """Create recording status indicator."""
    return ui.div(
        ui.div(
            ui.span("", class_="recording-dot"),
            ui.span("Recording...", style="margin-left: 8px;"),
            id="recording-indicator",
            class_="recording-indicator",
            style="display: none;"
        ),
        class_="recording-section"
    )


def create_voice_feedback_section():
    """Create feedback section for voice singing results."""
    return ui.div(
        ui.output_ui("voice_feedback_message"),
        ui.div(id="voice-pitch-plot", style="margin-top: 20px;"),
        class_="feedback-section"
    )


def create_voice_notation_section():
    """Create notation display section for voice melodies."""
    return ui.div(
        ui.div(id="voice-notation-container"),
        class_="notation-section",
        style="display: none;"
    )
