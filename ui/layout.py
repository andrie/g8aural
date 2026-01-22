"""
Shared layout components for g8aural application.

This module provides common layout components used across multiple modules.
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
                "Current Level: Grade 5",
                id="grade-label",
                class_="grade-label"
            ),
            ui.input_slider(
                "grade_slider",
                label=None,  # No label (using custom label above)
                min=5,
                max=8,
                value=5,
                step=1,
                width="300px"
            ),
            ui.div(
                ui.span("Grade 5"),
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