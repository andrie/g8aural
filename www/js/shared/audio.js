/**
 * Shared audio module for Tone.js integration.
 * Used by both the main app and chord_test_app.
 */
console.log("[Audio] audio.js loaded");

let piano = null;
let isAudioInitialized = false;

// Audio quality setting: "synthesized" or "sampled"
const AUDIO_QUALITY = "sampled";

/**
 * Initialize audio on first user interaction.
 * @returns {Promise} - Resolves when audio is initialized
 */
async function initAudio() {
    if (isAudioInitialized) {
        console.log("[Audio] Already initialized");
        return;
    }

    try {
        console.log("[Audio] Starting Tone.js...");
        await Tone.start();
        console.log("[Audio] Tone.js started, context state:", Tone.context.state);

        if (AUDIO_QUALITY === "sampled") {
            console.log("[Audio] Creating sampler...");
            piano = new Tone.Sampler({
                urls: {
                    "C4": "C4.mp3",
                    "D#4": "Ds4.mp3",
                    "F#4": "Fs4.mp3",
                    "A4": "A4.mp3",
                },
                baseUrl: "https://tonejs.github.io/audio/salamander/",
            }).toDestination();
            piano.volume.value = -12; // Reduce volume (dB)

            console.log("[Audio] Waiting for samples to load...");
            await Tone.loaded();
            console.log("[Audio] Samples loaded");
        } else {
            piano = new Tone.PolySynth(Tone.Synth, {
                oscillator: {
                    type: "fatsawtooth",
                    count: 3,
                    spread: 20
                },
                envelope: {
                    attack: 0.002,
                    decay: 0.3,
                    sustain: 0.1,
                    release: 1.2
                },
                volume: -8
            }).toDestination();

            const reverb = new Tone.Reverb({
                decay: 2.5,
                wet: 0.3
            }).toDestination();

            piano.connect(reverb);
        }

        isAudioInitialized = true;
    } catch (error) {
        console.error("Failed to initialize audio:", error);
        throw error;
    }
}

/**
 * Convert MIDI number to note name.
 * @param {number} midiNumber - MIDI note number
 * @returns {string} - Note name (e.g., "C4")
 */
function midiToNoteName(midiNumber) {
    const noteNames = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"];
    const octave = Math.floor(midiNumber / 12) - 1;
    const note = noteNames[midiNumber % 12];
    return `${note}${octave}`;
}

/**
 * Play a chord progression.
 * @param {Array} progression - Array of chord arrays (MIDI numbers)
 * @param {Object} options - Playback options
 *   - beatDuration: Duration per chord in seconds (default: 1.0)
 *   - onChordStart: Callback(index) called when each chord starts
 *   - onComplete: Callback called when playback completes
 *   - useScheduling: If true, use Tone.js scheduling; if false, use setTimeout (default: false)
 * @returns {Promise} - Resolves when playback is complete
 */
async function playProgression(progression, options = {}) {
    const beatDuration = options.beatDuration || 1.0;
    const onChordStart = options.onChordStart || null;
    const onComplete = options.onComplete || null;
    const useScheduling = options.useScheduling !== false;

    console.log("[Audio] playProgression called with:", progression?.length, "chords");

    if (!progression || !Array.isArray(progression) || progression.length === 0) {
        console.error("[Audio] Invalid progression data:", progression);
        return;
    }

    try {
        // Initialize audio if needed
        if (!isAudioInitialized) {
            console.log("[Audio] Initializing audio...");
            if (typeof Shiny !== 'undefined' && Shiny && AUDIO_QUALITY === "sampled") {
                Shiny.setInputValue("audio_loading", true, { priority: "event" });
            }
        }

        await initAudio();
        console.log("[Audio] Audio initialized, piano:", piano ? "ready" : "null");

        // Resume audio context if needed
        if (Tone.context.state !== 'running') {
            console.log("[Audio] Resuming audio context...");
            await Tone.context.resume();
        }
        console.log("[Audio] Audio context state:", Tone.context.state);

        // Stop any existing playback
        Tone.Transport.stop();
        Tone.Transport.cancel();

        // Convert MIDI numbers to note names
        const chordNames = progression.map(chord =>
            chord.map(midi => midiToNoteName(midi))
        );
        console.log("[Audio] First chord notes:", chordNames[0]);

        if (useScheduling) {
            // Use Tone.js scheduling (more precise timing)
            const now = Tone.now();
            console.log("[Audio] Using scheduling, now:", now, "beatDuration:", beatDuration);

            chordNames.forEach((chord, index) => {
                const startTime = now + index * beatDuration;

                // Schedule chord start callback
                if (onChordStart) {
                    Tone.Transport.schedule(() => {
                        onChordStart(index);
                    }, startTime);
                }

                // Play the chord
                console.log("[Audio] Scheduling chord", index, "at", startTime, ":", chord);
                piano.triggerAttackRelease(chord, "1n", startTime);
            });
            console.log("[Audio] All chords scheduled");

            // Schedule completion callback
            const totalDuration = chordNames.length * beatDuration;
            if (onComplete) {
                setTimeout(() => {
                    onComplete();
                }, (totalDuration + 0.5) * 1000);
            }

            // Notify Shiny of completion
            if (typeof Shiny !== 'undefined' && Shiny) {
                setTimeout(() => {
                    Shiny.setInputValue("playback_complete", Math.random(), { priority: "event" });
                }, (totalDuration + 0.5) * 1000);
            }

        } else {
            // Use setTimeout-based playback (for visual highlighting sync)
            let currentIndex = 0;

            function playNextChord() {
                if (currentIndex >= chordNames.length) {
                    if (onComplete) onComplete();
                    return;
                }

                const chord = chordNames[currentIndex];

                // Call chord start callback
                if (onChordStart) {
                    onChordStart(currentIndex);
                }

                // Play the chord
                if (piano) {
                    piano.triggerAttackRelease(chord, "1n");
                }

                currentIndex++;
                if (currentIndex < chordNames.length) {
                    setTimeout(playNextChord, beatDuration * 1000);
                } else {
                    // Schedule completion callback after last chord
                    setTimeout(() => {
                        if (onComplete) onComplete();
                    }, beatDuration * 1000);
                }
            }

            playNextChord();
        }

    } catch (error) {
        console.error("Error playing progression:", error);
        throw error;
    }
}

/**
 * Check if audio is initialized.
 * @returns {boolean} - True if audio is ready
 */
function isReady() {
    return isAudioInitialized;
}

// Register default Shiny handlers (can be overridden by app-specific scripts)
function registerDefaultAudioHandlers() {
    if (typeof Shiny === 'undefined' || !Shiny) {
        console.log("[Audio] Shiny not available, skipping handler registration");
        return;
    }

    try {
        Shiny.addCustomMessageHandler("playProgression", function(message) {
            console.log("[Audio] Received playProgression message:", message);
            playProgression(message.progression, {
                beatDuration: message.beatDuration || 1.0,
                useScheduling: true
            });
        });
        console.log("[Audio] playProgression handler registered");
    } catch (e) {
        console.log("[Audio] Handler registration error:", e.message);
        // Handler already registered by app-specific script
    }
}

// Register handlers after DOM is ready (to allow app-specific overrides)
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', registerDefaultAudioHandlers);
} else {
    registerDefaultAudioHandlers();
}

// Export for use by other modules
window.sharedAudio = {
    initAudio,
    playProgression,
    midiToNoteName,
    isReady
};
