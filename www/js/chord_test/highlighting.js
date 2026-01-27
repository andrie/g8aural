/**
 * Chord highlighting functionality for chord_test_app.
 * Extends the shared notation module with visual highlighting during playback.
 */

/**
 * Highlight the currently playing chord in the notation.
 * @param {number} index - Index of the chord to highlight
 */
function highlightCurrentChord(index) {
    // Get notes from shared notation module
    const notes = window.sharedNotation ? window.sharedNotation.getNotes() : null;

    if (!notes) {
        console.warn("Shared notation module not available");
        return;
    }

    const { trebleNotes, bassNotes, context, trebleStave, bassStave } = notes;

    if (!trebleNotes || !bassNotes) {
        console.warn("No notes available for highlighting");
        return;
    }

    try {
        // Reset all notes to black
        trebleNotes.forEach(note => {
            try {
                note.setStyle({ fillStyle: 'black', strokeStyle: 'black' });
            } catch (e) {
                // Ignore errors on individual notes
            }
        });

        bassNotes.forEach(note => {
            try {
                note.setStyle({ fillStyle: 'black', strokeStyle: 'black' });
            } catch (e) {
                // Ignore errors on individual notes
            }
        });

        // Highlight the current chord if it exists
        if (index >= 0 && index < trebleNotes.length) {
            try {
                trebleNotes[index].setStyle({ fillStyle: 'blue', strokeStyle: 'blue' });
            } catch (e) {
                console.warn("Error setting treble highlight style:", e);
            }
        }

        if (index >= 0 && index < bassNotes.length) {
            try {
                bassNotes[index].setStyle({ fillStyle: 'blue', strokeStyle: 'blue' });
            } catch (e) {
                console.warn("Error setting bass highlight style:", e);
            }
        }

        // Note: VexFlow doesn't support dynamic style changes after drawing.
        // The style will be visible only on next full redraw.
        // For production use, consider using CSS overlays or SVG manipulation.

    } catch (e) {
        console.warn("Error highlighting chord:", e);
    }
}

/**
 * Clear all chord highlighting.
 */
function clearHighlighting() {
    const notes = window.sharedNotation ? window.sharedNotation.getNotes() : null;

    if (!notes) return;

    const { trebleNotes, bassNotes } = notes;

    trebleNotes.forEach(note => {
        try {
            note.setStyle({ fillStyle: 'black', strokeStyle: 'black' });
        } catch (e) {
            // Ignore errors
        }
    });

    bassNotes.forEach(note => {
        try {
            note.setStyle({ fillStyle: 'black', strokeStyle: 'black' });
        } catch (e) {
            // Ignore errors
        }
    });
}

// Make function globally available for audio module callback
window.highlightCurrentChord = highlightCurrentChord;
window.clearHighlighting = clearHighlighting;

// Chord test-specific Shiny handlers
// These are registered IMMEDIATELY (not deferred) to take priority over
// the shared modules' deferred handlers
(function() {
    if (typeof Shiny === 'undefined' || !Shiny) return;

    // Override renderNotation to use quarter notes for chord_test
    Shiny.addCustomMessageHandler("renderNotation", function(message) {
        if (window.sharedNotation) {
            window.sharedNotation.renderNotation(
                message.noteNames,
                message.chordSymbols || message.symbols,
                message.key,
                {
                    containerId: message.containerId || "notation-container",
                    noteDuration: "q",  // Quarter notes for chord_test
                    cadenceType: message.cadenceType
                }
            );
        }
    });

    // Override playProgression to use timer-based playback with highlighting
    Shiny.addCustomMessageHandler("playProgression", function(message) {
        if (window.sharedAudio) {
            window.sharedAudio.playProgression(message.progression, {
                beatDuration: 1.5,  // 1.5 seconds per chord
                useScheduling: false,  // Use setTimeout for sync with highlighting
                onChordStart: function(index) {
                    highlightCurrentChord(index);
                },
                onComplete: function() {
                    clearHighlighting();
                }
            });
        }
    });
})();

// Export for ES module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { highlightCurrentChord, clearHighlighting };
}
