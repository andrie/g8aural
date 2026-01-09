// Notation module for VexFlow integration with Shiny
const VF = typeof Vex !== 'undefined' ? Vex.Flow : null;
let renderer = null;
let context = null;

// Initialize VexFlow renderer
function initNotation() {
    const container = document.getElementById("notation-container");
    if (!container) {
        console.error("Notation container not found");
        return;
    }

    // Clear existing content
    container.innerHTML = "";

    // Create renderer
    renderer = new VF.Renderer(container, VF.Renderer.Backends.SVG);
    renderer.resize(700, 200);
    context = renderer.getContext();
}

// Convert MIDI number to VexFlow note notation
function midiToVexFlowNote(midiNumber) {
    const noteNames = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"];
    const octave = Math.floor(midiNumber / 12) - 1;
    const note = noteNames[midiNumber % 12].replace("#", "#");
    return `${note}/${octave}`;
}

// Map music21 key names to VexFlow key signatures
function getKeySignature(keyName) {
    // Map music21 key format to VexFlow key signature format
    // music21 uses lowercase for minor (e.g., 'a', 'd', 'f#')
    // VexFlow uses major key names with 'm' suffix for minor (e.g., 'Am', 'Dm', 'F#m')
    const signatures = {
        'C': 'C',      // C major: 0 sharps/flats
        'G': 'G',      // G major: 1 sharp
        'D': 'D',      // D major: 2 sharps
        'A': 'A',      // A major: 3 sharps
        'F': 'F',      // F major: 1 flat
        'Bb': 'Bb',    // Bb major: 2 flats
        'B-': 'Bb',    // Alternative notation
        'Eb': 'Eb',    // Eb major: 3 flats
        'E-': 'Eb',    // Alternative notation
        'a': 'Am',     // A minor: 0 sharps/flats
        'e': 'Em',     // E minor: 1 sharp
        'b': 'Bm',     // B minor: 2 sharps
        'd': 'Dm',     // D minor: 1 flat
        'g': 'Gm',     // G minor: 2 flats
        'c': 'Cm',     // C minor: 3 flats
        'f#': 'F#m',   // F# minor: 3 sharps
        'f♯': 'F#m'    // Alternative notation
    };

    return signatures[keyName] || 'C';  // Default to C major if key not found
}

// Render the chord progression as notation
function renderNotation(progression, noteNames, chordSymbols, cadenceType, key) {
    try {
        // Initialize renderer
        initNotation();

        // Create stave with key signature
        const stave = new VF.Stave(10, 40, 680);
        stave.addClef("treble");

        // Add key signature if key is provided
        if (key) {
            const vexflowKey = getKeySignature(key);
            stave.addKeySignature(vexflowKey);
        }

        stave.setContext(context).draw();

        // Convert progression to VexFlow notes
        const notes = [];
        const chordCount = progression.length;

        progression.forEach((chord, index) => {
            // Use provided note names (with correct enharmonic spelling)
            // Convert from ["C4", "E-4", "G4"] to ["C/4", "Eb/4", "G/4"]
            // music21 uses "-" for flats, VexFlow expects "b"
            const noteStrings = noteNames[index].map(name =>
                name.replace(/-/g, 'b').replace(/(\d)$/, '/$1'));

            // Create chord (stacked notes)
            const staveNote = new VF.StaveNote({
                keys: noteStrings,
                duration: "w" // Whole note
            });

            // Add chord symbol annotation
            if (chordSymbols && chordSymbols[index]) {
                staveNote.addModifier(
                    new VF.Annotation(chordSymbols[index])
                        .setFont("Arial", 12, "bold")
                        .setVerticalJustification(VF.Annotation.VerticalJustify.TOP),
                    0
                );
            }

            notes.push(staveNote);
        });

        // Create voice and format
        const voice = new VF.Voice({ num_beats: chordCount * 4, beat_value: 4 });
        voice.addTickables(notes);

        // Format and draw
        new VF.Formatter()
            .joinVoices([voice])
            .format([voice], 650);

        voice.draw(context, stave);

        // Add cadence type label
        context.fillStyle = "black";
        context.font = "16px Arial";
        context.fillText(`Cadence: ${cadenceType.charAt(0).toUpperCase() + cadenceType.slice(1)}`, 10, 180);

    } catch (error) {
        console.error("Error rendering notation:", error);
    }
}

// Clear notation display
function clearNotation() {
    const container = document.getElementById("notation-container");
    if (container) {
        container.innerHTML = "";
    }
}

// Update button states and UI visibility
function updateButtonStates(states) {
    // Update play button
    const playBtn = document.getElementById("play_btn");
    if (playBtn && states.playEnabled !== undefined) {
        playBtn.disabled = !states.playEnabled;
    }

    // Update hint button visibility
    const hintBtn = document.getElementById("hint_btn");
    if (hintBtn && states.hintVisible !== undefined) {
        hintBtn.style.display = states.hintVisible ? "inline-block" : "none";
    }

    // Update answer buttons
    const answerButtons = [
        "perfect_btn", "plagal_btn", "imperfect_btn", "interrupted_btn"
    ];

    answerButtons.forEach(btnId => {
        const btn = document.getElementById(btnId);
        if (btn && states.answersEnabled !== undefined) {
            // Check if this button is in the disabled list
            const isDisabled = states.disabledButtons && states.disabledButtons.includes(btnId);
            btn.disabled = !states.answersEnabled || isDisabled;
        }
    });

    // Update next button visibility
    const nextBtn = document.getElementById("next_btn");
    if (nextBtn && states.nextVisible !== undefined) {
        nextBtn.style.display = states.nextVisible ? "inline-block" : "none";
    }

    // Show/hide notation section
    const notationSection = document.querySelector(".notation-section");
    if (notationSection && states.showNotation !== undefined) {
        notationSection.style.display = states.showNotation ? "block" : "none";
    }
}

// Update button text with emoji feedback
function updateButtonFeedback(btnId, emoji, originalText) {
    const btn = document.getElementById(btnId);
    if (!btn) {
        console.error(`Button not found: ${btnId}`);
        return;
    }

    // Find the action-label span inside the button
    const label = btn.querySelector('.action-label');
    if (!label) {
        console.error(`Action label span not found in button: ${btnId}`);
        return;
    }

    // Store original text if not already stored
    if (!btn.dataset.originalText) {
        btn.dataset.originalText = originalText;
    }

    // Update text content of the span
    if (emoji) {
        label.textContent = `${originalText} ${emoji}`;

        // Add CSS class for styling
        if (emoji === "✓") {
            btn.classList.add("correct");
            btn.classList.remove("incorrect");
        } else if (emoji === "✗") {
            btn.classList.add("incorrect");
            btn.classList.remove("correct");
        }
    } else {
        // Reset to original state
        label.textContent = originalText;
        btn.classList.remove("correct", "incorrect");
    }
}

// Reset all cadence button text
function resetButtonText() {
    const buttonLabels = {
        "perfect_btn": "Perfect",
        "plagal_btn": "Plagal",
        "imperfect_btn": "Imperfect",
        "interrupted_btn": "Interrupted"
    };

    Object.entries(buttonLabels).forEach(([btnId, labelText]) => {
        const btn = document.getElementById(btnId);
        if (btn) {
            const label = btn.querySelector('.action-label');
            if (label) {
                label.textContent = labelText;
            }
            btn.classList.remove("correct", "incorrect");
            delete btn.dataset.originalText;
        }
    });
}

// Listen for custom messages from Shiny
if (window.Shiny) {
    Shiny.addCustomMessageHandler("renderNotation", function(message) {
        renderNotation(message.progression, message.noteNames, message.chordSymbols, message.cadenceType, message.key);
    });

    Shiny.addCustomMessageHandler("clearNotation", function(message) {
        clearNotation();
    });

    Shiny.addCustomMessageHandler("updateButtonStates", function(message) {
        updateButtonStates(message);
    });

    Shiny.addCustomMessageHandler("updateButtonFeedback", function(message) {
        updateButtonFeedback(message.btnId, message.emoji, message.originalText);
    });

    Shiny.addCustomMessageHandler("resetButtonText", function(message) {
        resetButtonText();
    });

    // Handle playback complete callback
    Shiny.addCustomMessageHandler("playbackComplete", function(message) {
        // This is called from audio.js, just acknowledge
    });
}
