"""
Chord Test App for evaluating voice leading quality.

This app allows testing of chord progressions with different voice leading algorithms
and collecting feedback on musicality.
"""
from pathlib import Path
from shiny import App, ui, reactive
import modules.chord_test.handlers as handlers


def app_ui(request):
    """Create the user interface for the chord test app."""
    return ui.page_fluid(
        ui.tags.head(
            ui.tags.link(rel="stylesheet", href="https://cdn.jsdelivr.net/npm/bootstrap@5.2.3/dist/css/bootstrap.min.css"),
            ui.tags.link(rel="stylesheet", href="/css/chord_test.css"),
            # Include external JS libraries
            ui.tags.script(src="https://cdnjs.cloudflare.com/ajax/libs/tone/14.8.49/Tone.js"),
            ui.tags.script(src="https://cdn.jsdelivr.net/npm/vexflow@4.2.2/build/cjs/vexflow.js"),
            # Include shared JS modules
            ui.tags.script(src="/js/shared/audio.js"),
            ui.tags.script(src="/js/shared/notation.js"),
            # Include chord_test-specific modules
            ui.tags.script(src="/js/chord_test/highlighting.js"),
        ),

        # App header
        ui.div(
            ui.h2("Chord Voice Leading Test App"),
            class_="mt-4 mb-4"
        ),

        # Main content
        ui.row(
            ui.column(4,
                ui.card(
                    ui.card_header("Settings"),
                    ui.card_body(
                        ui.input_select("grade", "Grade Level", [5, 6, 7, 8], selected=8),
                        ui.input_select("cadence_type", "Cadence Type",
                                        ["Perfect", "Plagal", "Imperfect", "Interrupted"],
                                        selected="Perfect"),
                        ui.input_checkbox("use_enhanced", "Use Enhanced Voice Leading", value=True),
                        ui.input_action_button("generate", "Generate New Progression",
                                             class_="btn-primary mt-3")
                    )
                )
            ),
            ui.column(8,
                ui.card(
                    ui.card_header("Chord Notation"),
                    ui.card_body(
                        ui.div(id="notation-container", class_="notation-section")
                    )
                )
            )
        ),

        # Audio controls
        ui.row(
            ui.column(12,
                ui.div(
                    ui.input_action_button("play", "Play Progression",
                                         class_="btn-primary"),
                    class_="audio-controls"
                )
            )
        ),

        # Feedback section
        ui.row(
            ui.column(12,
                ui.card(
                    ui.card_header("Feedback"),
                    ui.card_body(
                        ui.div(
                            ui.input_radio_buttons("rating", "Rate Voice Leading Quality:",
                                                 choices=[1, 2, 3, 4, 5],
                                                 selected=None,
                                                 inline=True),
                            class_="rating-controls"
                        ),
                        ui.input_text_area("comments", "Comments:", rows=3),
                        ui.input_action_button("submit_feedback", "Submit Feedback",
                                             class_="btn-success mt-2")
                    )
                )
            )
        ),

        # JavaScript initialization (no jQuery required)
        ui.tags.script("""
        document.addEventListener('DOMContentLoaded', function() {
            console.log("Chord test app initialized");
        });
        """)
    )


def server(input, output, session):  # pylance-ignore: output is used by Shiny framework
    """Create the server logic for the chord test app."""
    # Initialize state
    progression_state = reactive.Value(None)
    feedback_state = reactive.Value({"submitted": False})

    # Generate an initial progression when the app loads
    @reactive.Effect
    async def _initialize():  # pylance-ignore: used by reactive framework
        # Generate a default progression when the app starts
        print("Initializing with default chord progression")
        progression = handlers.generate_chord_progression(
            grade=8,
            cadence_type="perfect",
            use_enhanced=True
        )
        progression_state.set(progression)

        # Send to frontend for rendering
        await session.send_custom_message("renderNotation", {
            "progression": progression["progression"],
            "noteNames": progression["note_names"],
            "symbols": progression["symbols"],
            "key": progression["key"]
        })
        print("Initial chord progression sent to frontend")

    # Generate new progression
    # Note: Function not directly accessed but used by Shiny's reactive framework
    @reactive.Effect
    @reactive.event(input.generate)
    async def _generate_progression():  # pylance-ignore: used by reactive framework
        grade = input.grade()
        cadence_type = input.cadence_type().lower()
        use_enhanced = input.use_enhanced()

        # Generate progression using enhanced or regular algorithm
        print(f"Generating chord progression: grade={grade}, cadence_type={cadence_type}, use_enhanced={use_enhanced}")
        progression = handlers.generate_chord_progression(
            grade=grade,
            cadence_type=cadence_type,
            use_enhanced=use_enhanced
        )

        progression_state.set(progression)
        print(f"Progression generated: {progression}")

        # Send to frontend for rendering
        print(f"Sending to frontend for rendering")
        await session.send_custom_message("renderNotation", {
            "progression": progression["progression"],
            "noteNames": progression["note_names"],
            "symbols": progression["symbols"],
            "key": progression["key"]
        })
        print(f"Sent to frontend")

        # Reset feedback
        feedback_state.set({"submitted": False})

    # Play progression
    # Note: Function not directly accessed but used by Shiny's reactive framework
    @reactive.Effect
    @reactive.event(input.play)
    async def _play_progression():  # pylance-ignore: used by reactive framework
        if progression_state() is not None:
            progression = progression_state()
            await session.send_custom_message("playProgression", {
                "progression": progression["progression"],
                "noteNames": progression["note_names"]
            })

    # Submit feedback
    # Note: Function not directly accessed but used by Shiny's reactive framework
    @reactive.Effect
    @reactive.event(input.submit_feedback)
    async def _submit_feedback():  # pylance-ignore: used by reactive framework
        if progression_state() is not None and input.rating() is not None:
            # Create feedback entry
            feedback = {
                "timestamp": handlers.get_timestamp(),
                "grade": input.grade(),
                "cadence_type": input.cadence_type().lower(),
                "progression": progression_state(),
                "rating": input.rating(),
                "comments": input.comments(),
                "algorithm_version": "enhanced" if input.use_enhanced() else "original"
            }

            # Save feedback to file
            handlers.save_feedback(feedback)

            # Update feedback state
            feedback_state.set({"submitted": True})

            # Show success message
            await session.send_notification(
                ui.notification_show("Feedback submitted successfully!",
                                    duration=3,
                                    type="success")
            )


# Create app with static files from www directory
www_dir = Path(__file__).parent / "www"
app = App(app_ui, server, static_assets=www_dir)