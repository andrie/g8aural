/**
 * Shared notation module for VexFlow integration.
 * Used by both the main app and chord_test_app.
 */

const VF = typeof Vex !== 'undefined' ? Vex.Flow : null;

// Module state
let renderer = null;
let context = null;

// Store notes for potential highlighting
let trebleNotes = [];
let bassNotes = [];

// Store staves for highlighting redraw
let currentTrebleStave = null;
let currentBassStave = null;

/**
 * Initialize VexFlow renderer.
 * @param {string} containerId - The ID of the container element
 * @param {Object} options - Renderer options
 * @returns {Object} - The renderer context
 */
function initNotation(containerId = "notation-container", options = {}) {
    const container = document.getElementById(containerId);
    if (!container) {
        console.error("Notation container not found:", containerId);
        return null;
    }

    // Clear existing content
    container.innerHTML = "";

    // Create renderer
    const width = options.width || 700;
    const height = options.height || 300;

    renderer = new VF.Renderer(container, VF.Renderer.Backends.SVG);
    renderer.resize(width, height);
    context = renderer.getContext();

    return context;
}

/**
 * Convert MIDI number to VexFlow note notation.
 * @param {number} midiNumber - MIDI note number
 * @returns {string} - VexFlow note notation (e.g., "c/4")
 */
function midiToVexFlowNote(midiNumber) {
    const noteNames = ["c", "c#", "d", "d#", "e", "f", "f#", "g", "g#", "a", "a#", "b"];
    const octave = Math.floor(midiNumber / 12) - 1;
    const note = noteNames[midiNumber % 12];
    return `${note}/${octave}`;
}

/**
 * Map music21 key names to VexFlow key signatures.
 * @param {string} keyName - Key name from music21
 * @returns {string} - VexFlow key signature
 */
function getKeySignature(keyName) {
    const signatures = {
        'C': 'C', 'G': 'G', 'D': 'D', 'A': 'A', 'F': 'F',
        'Bb': 'Bb', 'B-': 'Bb', 'Eb': 'Eb', 'E-': 'Eb',
        'a': 'Am', 'e': 'Em', 'b': 'Bm', 'd': 'Dm',
        'g': 'Gm', 'c': 'Cm', 'f#': 'F#m', 'f\u266f': 'F#m'
    };
    return signatures[keyName] || 'C';
}

/**
 * Format a note name for VexFlow.
 * @param {string} note - Note name (e.g., "C4" or "E-4")
 * @returns {string} - VexFlow format (e.g., "c/4" or "eb/4")
 */
function formatNoteForVexFlow(note) {
    // Handle already formatted notes
    if (note.includes('/')) return note.toLowerCase();

    // Replace music21's "-" notation for flats with "b"
    note = note.replace(/-/g, 'b');

    // Extract note name and octave
    const match = note.match(/^([A-Ga-g][#b]?)(\d)$/);
    if (!match) {
        console.warn("Could not parse note:", note);
        return "c/4";
    }

    const noteName = match[1].toLowerCase();
    const octave = match[2];
    return `${noteName}/${octave}`;
}

/**
 * Get MIDI value from a formatted VexFlow note.
 * @param {string} formattedNote - VexFlow note (e.g., "c/4")
 * @returns {number} - MIDI note number
 */
function getMidiFromVexFlowNote(formattedNote) {
    const [notePart, octave] = formattedNote.split('/');
    const noteMap = {
        'c': 0, 'c#': 1, 'db': 1, 'd': 2, 'd#': 3, 'eb': 3,
        'e': 4, 'f': 5, 'f#': 6, 'gb': 6, 'g': 7, 'g#': 8,
        'ab': 8, 'a': 9, 'a#': 10, 'bb': 10, 'b': 11
    };
    const noteVal = noteMap[notePart] || 0;
    return (parseInt(octave) + 1) * 12 + noteVal;
}

/**
 * Add accidentals to a stave note.
 * @param {Object} staveNote - VexFlow StaveNote
 * @param {Array} formattedNotes - Array of formatted note strings
 */
function addAccidentals(staveNote, formattedNotes) {
    formattedNotes.forEach((note, i) => {
        if (note.includes('#')) {
            staveNote.addModifier(new VF.Accidental("#"), i);
        } else if (note.includes('b') && note[0] !== 'b') {
            staveNote.addModifier(new VF.Accidental("b"), i);
        }
    });
}

/**
 * Render chord progression as notation with grand staff.
 * @param {Array} noteNames - Array of chord note arrays
 * @param {Array} chordSymbols - Array of chord symbol strings
 * @param {string} key - Key signature
 * @param {Object} options - Rendering options
 *   - containerId: Container element ID (default: "notation-container")
 *   - noteDuration: "w" for whole notes, "q" for quarter notes (default: "w")
 *   - cadenceType: Type of cadence to display (optional)
 *   - width: Container width (default: 700)
 *   - height: Container height (default: 300)
 * @returns {Object} - Object with trebleNotes and bassNotes arrays for highlighting
 */
function renderNotation(noteNames, chordSymbols, key, options = {}) {
    try {
        const containerId = options.containerId || "notation-container";
        const noteDuration = options.noteDuration || "w";
        const cadenceType = options.cadenceType || null;
        const width = options.width || 700;
        const height = options.height || 300;

        // Initialize renderer
        initNotation(containerId, { width, height });

        const staveWidth = width - 20;
        const trebleY = 30;
        const bassY = 130;

        // Create treble stave
        const trebleStave = new VF.Stave(10, trebleY, staveWidth);
        trebleStave.addClef("treble");

        // Create bass stave
        const bassStave = new VF.Stave(10, bassY, staveWidth);
        bassStave.addClef("bass");

        // Store for highlighting
        currentTrebleStave = trebleStave;
        currentBassStave = bassStave;

        // Add key signature if provided
        if (key) {
            const vexflowKey = getKeySignature(key);
            trebleStave.addKeySignature(vexflowKey);
            bassStave.addKeySignature(vexflowKey);
        }

        // Draw staves
        trebleStave.setContext(context).draw();
        bassStave.setContext(context).draw();

        // Add brace and barline connectors
        const brace = new VF.StaveConnector(trebleStave, bassStave);
        brace.setType(VF.StaveConnector.type.BRACE);
        brace.setContext(context).draw();

        const lineConnector = new VF.StaveConnector(trebleStave, bassStave);
        lineConnector.setType(VF.StaveConnector.type.SINGLE_LEFT);
        lineConnector.setContext(context).draw();

        // Reset note arrays
        trebleNotes = [];
        bassNotes = [];

        const chordCount = noteNames.length;

        // Calculate beats per chord based on duration
        const beatsPerChord = noteDuration === "w" ? 4 : 1;

        // Process each chord - SATB order: [bass, tenor, alto, soprano]
        noteNames.forEach((chord, index) => {
            if (!chord || !chord.length) return;

            // Format all notes
            const formattedNotes = chord.map(formatNoteForVexFlow);

            // Split by voice index
            // Indices 0,1 = bass clef (bass, tenor)
            // Indices 2,3 = treble clef (alto, soprano)
            const bassClefNotes = formattedNotes.slice(0, 2);
            const trebleClefNotes = formattedNotes.slice(2, 4);

            // Create treble stave note
            if (trebleClefNotes.length > 0) {
                const trebleNote = new VF.StaveNote({
                    clef: "treble",
                    keys: trebleClefNotes,
                    duration: noteDuration
                });
                addAccidentals(trebleNote, trebleClefNotes);

                // Add chord symbol
                if (chordSymbols && chordSymbols[index]) {
                    trebleNote.addModifier(
                        new VF.Annotation(chordSymbols[index])
                            .setFont("Arial", 12, "bold")
                            .setVerticalJustification(VF.Annotation.VerticalJustify.TOP),
                        0
                    );
                }

                trebleNotes.push(trebleNote);
            }

            // Create bass stave note
            if (bassClefNotes.length > 0) {
                const bassNote = new VF.StaveNote({
                    clef: "bass",
                    keys: bassClefNotes,
                    duration: noteDuration
                });
                addAccidentals(bassNote, bassClefNotes);
                bassNotes.push(bassNote);
            }
        });

        // Create voices
        const trebleVoice = new VF.Voice({
            num_beats: chordCount * beatsPerChord,
            beat_value: 4
        });
        trebleVoice.addTickables(trebleNotes);

        const bassVoice = new VF.Voice({
            num_beats: chordCount * beatsPerChord,
            beat_value: 4
        });
        bassVoice.addTickables(bassNotes);

        // Format both voices together
        new VF.Formatter()
            .joinVoices([trebleVoice])
            .joinVoices([bassVoice])
            .format([trebleVoice, bassVoice], staveWidth - 60);

        // Draw voices
        trebleVoice.draw(context, trebleStave);
        bassVoice.draw(context, bassStave);

        // Add cadence type label if provided
        if (cadenceType) {
            context.fillStyle = "black";
            context.font = "16px Arial";
            const label = `Cadence: ${cadenceType.charAt(0).toUpperCase() + cadenceType.slice(1)}`;
            context.fillText(label, 10, height - 20);
        }

        // Return note references for highlighting
        return {
            trebleNotes: trebleNotes,
            bassNotes: bassNotes,
            context: context,
            trebleStave: trebleStave,
            bassStave: bassStave
        };

    } catch (error) {
        console.error("Error rendering notation:", error);
        return null;
    }
}

/**
 * Clear notation display.
 * @param {string} containerId - Container element ID
 */
function clearNotation(containerId = "notation-container") {
    const container = document.getElementById(containerId);
    if (container) {
        container.innerHTML = "";
    }
    trebleNotes = [];
    bassNotes = [];
}

/**
 * Get current note arrays (for highlighting).
 * @returns {Object} - Object with trebleNotes and bassNotes arrays
 */
function getNotes() {
    return {
        trebleNotes: trebleNotes,
        bassNotes: bassNotes,
        context: context,
        trebleStave: currentTrebleStave,
        bassStave: currentBassStave
    };
}

// Update button states and UI visibility (used by main app)
function updateButtonStates(states) {
    // Update play button
    const playBtn = document.getElementById("play_btn") ||
                    document.getElementById("cadence_play_btn");
    if (playBtn && states.playEnabled !== undefined) {
        playBtn.disabled = !states.playEnabled;
    }

    // Update hint button visibility
    const hintBtn = document.getElementById("hint_btn") ||
                    document.getElementById("cadence_hint_btn");
    if (hintBtn && states.hintVisible !== undefined) {
        hintBtn.style.display = states.hintVisible ? "inline-block" : "none";
    }

    // Update answer buttons
    const answerButtons = [
        "perfect_btn", "plagal_btn", "imperfect_btn", "interrupted_btn",
        "cadence_perfect_btn", "cadence_plagal_btn", "cadence_imperfect_btn", "cadence_interrupted_btn"
    ];

    answerButtons.forEach(btnId => {
        const btn = document.getElementById(btnId);
        if (btn && states.answersEnabled !== undefined) {
            const isDisabled = states.disabledButtons && states.disabledButtons.includes(btnId);
            btn.disabled = !states.answersEnabled || isDisabled;
        }
    });

    // Update next button visibility
    const nextBtn = document.getElementById("next_btn") ||
                    document.getElementById("cadence_next_btn");
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

    const label = btn.querySelector('.action-label');
    if (!label) {
        console.error(`Action label span not found in button: ${btnId}`);
        return;
    }

    if (!btn.dataset.originalText) {
        btn.dataset.originalText = originalText;
    }

    if (emoji) {
        label.textContent = `${originalText} ${emoji}`;
        if (emoji === "\u2713") {
            btn.classList.add("correct");
            btn.classList.remove("incorrect");
        } else if (emoji === "\u2717") {
            btn.classList.add("incorrect");
            btn.classList.remove("correct");
        }
    } else {
        label.textContent = originalText;
        btn.classList.remove("correct", "incorrect");
    }
}

// Reset all cadence button text
function resetButtonText() {
    const buttonLabels = {
        "perfect_btn": "Perfect", "plagal_btn": "Plagal",
        "imperfect_btn": "Imperfect", "interrupted_btn": "Interrupted",
        "cadence_perfect_btn": "Perfect", "cadence_plagal_btn": "Plagal",
        "cadence_imperfect_btn": "Imperfect", "cadence_interrupted_btn": "Interrupted"
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

// Register default Shiny handlers (can be overridden by app-specific scripts)
// Apps that need custom behavior should load their handlers AFTER this script
// and use window.sharedNotation functions directly
function registerDefaultNotationHandlers() {
    if (typeof Shiny === 'undefined' || !Shiny) return;

    // Check if handlers are already registered (e.g., by chord_test)
    // This allows app-specific scripts to register first
    try {
        Shiny.addCustomMessageHandler("renderNotation", function(message) {
            renderNotation(
                message.noteNames,
                message.chordSymbols || message.symbols,
                message.key,
                {
                    cadenceType: message.cadenceType,
                    containerId: message.containerId || "notation-container",
                    noteDuration: message.noteDuration || "w"
                }
            );
        });
    } catch (e) {
        // Handler already registered by app-specific script
    }

    try {
        Shiny.addCustomMessageHandler("clearNotation", function(message) {
            clearNotation(message.containerId || "notation-container");
        });
    } catch (e) {
        // Handler already registered
    }

    try {
        Shiny.addCustomMessageHandler("updateButtonStates", function(message) {
            updateButtonStates(message);
        });
    } catch (e) {
        // Handler already registered
    }

    try {
        Shiny.addCustomMessageHandler("updateButtonFeedback", function(message) {
            updateButtonFeedback(message.btnId, message.emoji, message.originalText);
        });
    } catch (e) {
        // Handler already registered
    }

    try {
        Shiny.addCustomMessageHandler("resetButtonText", function(message) {
            resetButtonText();
        });
    } catch (e) {
        // Handler already registered
    }
}

// Register handlers after DOM is ready (to allow app-specific overrides)
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', registerDefaultNotationHandlers);
} else {
    registerDefaultNotationHandlers();
}

// Export for use by other modules
window.sharedNotation = {
    renderNotation,
    clearNotation,
    getNotes,
    formatNoteForVexFlow,
    getMidiFromVexFlowNote,
    initNotation,
    updateButtonStates,
    updateButtonFeedback,
    resetButtonText
};
