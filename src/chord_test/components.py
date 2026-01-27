"""
UI components for chord test app.

These components define the interface elements and JavaScript callbacks
for the chord test app.
"""
from shiny import ui


def notation_component():
    """
    Create a notation display component.

    Returns:
        UI component for notation display
    """
    return ui.div(
        ui.div(id="notation-container", class_="notation-section"),
        ui.tags.script("""
        $(document).ready(function() {
            // Initialize VexFlow renderer
            const VF = Vex.Flow;
            let renderer = null;

            // Listen for the custom message to render notation
            Shiny.addCustomMessageHandler('renderNotation', function(data) {
                // Clear previous notation
                $('#notation-container').empty();

                // Create renderer
                renderer = new VF.Renderer(
                    document.getElementById('notation-container'),
                    VF.Renderer.Backends.SVG
                );

                // Size renderer
                renderer.resize(800, 200);
                const context = renderer.getContext();

                // Create stave
                const stave = new VF.Stave(10, 40, 780);
                stave.addClef('treble').addKeySignature(data.key);
                stave.setContext(context).draw();

                // Create notes for each chord
                const chords = [];
                for (let i = 0; i < data.noteNames.length; i++) {
                    const chord = data.noteNames[i];
                    const notes = [];

                    // Create StaveNotes for each note in the chord
                    for (let j = 0; j < chord.length; j++) {
                        const noteName = chord[j];
                        const note = new VF.StaveNote({
                            clef: 'treble',
                            keys: [noteName.toLowerCase()],
                            duration: 'q'
                        });

                        // Handle accidentals
                        if (noteName.includes('#')) {
                            note.addAccidental(0, new VF.Accidental('#'));
                        } else if (noteName.includes('b')) {
                            note.addAccidental(0, new VF.Accidental('b'));
                        }

                        notes.push(note);
                    }

                    // Group notes into a chord
                    const chord = new VF.StaveNote({
                        clef: 'treble',
                        keys: chord.map(n => n.toLowerCase()),
                        duration: 'q'
                    });

                    // Add accidentals
                    for (let j = 0; j < chord.keys.length; j++) {
                        const key = chord.keys[j];
                        if (key.includes('#')) {
                            chord.addAccidental(j, new VF.Accidental('#'));
                        } else if (key.includes('b')) {
                            chord.addAccidental(j, new VF.Accidental('b'));
                        }
                    }

                    chords.push(chord);
                }

                // Add chord symbols above
                if (data.symbols) {
                    for (let i = 0; i < chords.length; i++) {
                        const x = stave.x + 100 + i * 150;
                        const y = stave.y - 10;
                        context.fillText(data.symbols[i], x, y);
                    }
                }

                // Create voice and formatter
                const voice = new VF.Voice({num_beats: chords.length, beat_value: 4});
                voice.addTickables(chords);
                new VF.Formatter().joinVoices([voice]).format([voice], 750);

                // Draw the voice
                voice.draw(context, stave);
            });
        });
        """)
    )


def audio_component():
    """
    Create an audio playback component.

    Returns:
        UI component for audio playback
    """
    return ui.div(
        ui.div(id="audio-controls", class_="audio-controls",
            ui.input_action_button("play", "Play Progression", class_="btn-primary")
        ),
        ui.tags.script("""
        // Initialize Tone.js
        const piano = new Tone.Sampler({
            urls: {
                C4: "C4.mp3",
                G4: "G4.mp3"
            },
            baseUrl: "samples/piano/",
            onload: () => {
                console.log("Piano samples loaded");
            }
        }).toDestination();

        // Handle playback
        Shiny.addCustomMessageHandler('playProgression', function(data) {
            const progression = data.progression;
            const noteNames = data.noteNames;

            // Schedule chords
            Tone.Transport.cancel();

            progression.forEach((chord, i) => {
                Tone.Transport.schedule((time) => {
                    // Convert MIDI to frequency
                    const freqs = chord.map(midi => Tone.Frequency(midi, "midi"));
                    piano.triggerAttackRelease(freqs, "2n", time);
                }, i);
            });

            // Start transport
            Tone.Transport.bpm.value = 60;
            Tone.Transport.start();
        });

        // Play button handler
        $(document).on('click', '#play', function() {
            // Need to resume audio context on user gesture
            if (Tone.context.state !== 'running') {
                Tone.context.resume();
            }

            // This will trigger the Shiny event that sends the playProgression message
        });
        """)
    )


def feedback_component():
    """
    Create a feedback collection component.

    Returns:
        UI component for feedback collection
    """
    return ui.div(
        ui.h3("Feedback"),
        ui.div({"class": "rating-controls"},
            ui.input_radio_buttons("rating", "Rate Voice Leading Quality:",
                                  choices=[1, 2, 3, 4, 5],
                                  selected=None,
                                  inline=True)
        ),
        ui.input_text_area("comments", "Comments:", rows=3),
        ui.input_action_button("submit_feedback", "Submit Feedback", class_="btn-success")
    )