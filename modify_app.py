#!/usr/bin/env python3
"""Script to add grade UI components to app.py"""

# Read the current file
with open('app.py', 'r') as f:
    content = f.read()

# Check if grade-ui.js is already added
if 'grade-ui.js' not in content:
    # Add grade-ui.js script reference
    content = content.replace(
        '        ui.tags.script(src="notation.js"),\n    ),',
        '        ui.tags.script(src="notation.js"),\n        ui.tags.script(src="grade-ui.js"),\n    ),'
    )

# Check if grade selection section is already added
if 'Grade Selection Section' not in content:
    # Add grade selection UI section
    grade_section = '''
    # Grade Selection Section
    ui.div(
        ui.div(
            id="grade-label",
            "Current Level: Grade 6",
            class_="grade-label"
        ),
        ui.input_slider(
            "grade_slider",
            None,  # No label (using custom label above)
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
                ui.tags.li(ui.tags.strong("Grade 7:"), " Perfect, Imperfect & Interrupted cadences (4-5 chords, root position)"),
                ui.tags.li(ui.tags.strong("Grade 8:"), " All four cadence types including Plagal (6-8 chords, complex inversions)")
            ),
            ui.p(ui.tags.em("All grades use keys with up to 3 sharps or flats (ABRSM syllabus requirement)")),
            id="grade-info-content"
        ),
        id="grade-info-modal",
        class_="grade-info-modal",
        style="display: none;"
    ),

'''

    # Insert after header section, before Control Section
    content = content.replace(
        '    ),\n\n    # Control Section',
        '),' + grade_section + '    # Control Section'
    )

# Write the modified content
with open('app.py', 'w') as f:
    f.write(content)

print("Successfully added grade UI components to app.py")
