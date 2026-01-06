// Audio module for Tone.js integration with Shiny

let piano = null;
let isAudioInitialized = false;

// Audio quality setting: "synthesized" or "sampled"
// "sampled" uses real piano samples (best quality, requires internet)
// "synthesized" uses enhanced synthesis (good quality, works offline)
const AUDIO_QUALITY = "sampled";

// Initialize audio on first user interaction
async function initAudio() {
    if (isAudioInitialized) return;

    try {
        await Tone.start();

        if (AUDIO_QUALITY === "sampled") {
            // Option 1: Use real piano samples (best quality)
            piano = new Tone.Sampler({
                urls: {
                    "C4": "C4.mp3",
                    "D#4": "Ds4.mp3",
                    "F#4": "Fs4.mp3",
                    "A4": "A4.mp3",
                },
                baseUrl: "https://tonejs.github.io/audio/salamander/",
            }).toDestination();

            // Wait for samples to load
            await Tone.loaded();
        } else {
            // Option 2: Enhanced synthesis for piano-like sound
            piano = new Tone.PolySynth(Tone.Synth, {
                oscillator: {
                    type: "fatsawtooth",  // Richer harmonics than sine
                    count: 3,
                    spread: 20
                },
                envelope: {
                    attack: 0.002,    // Very fast attack like piano hammer
                    decay: 0.3,       // Moderate decay
                    sustain: 0.1,     // Low sustain (piano notes decay)
                    release: 1.2      // Longer release for realism
                },
                volume: -8           // Reduce volume slightly for clarity
            }).toDestination();

            // Add reverb for more realistic sound
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

// Convert MIDI number to note name
function midiToNoteName(midiNumber) {
    const noteNames = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"];
    const octave = Math.floor(midiNumber / 12) - 1;
    const note = noteNames[midiNumber % 12];
    return `${note}${octave}`;
}

// Play a chord progression
async function playProgression(progression) {
    try {
        // Initialize audio if needed (first time only)
        if (!isAudioInitialized) {
            // Notify Shiny we're loading
            if (window.Shiny && AUDIO_QUALITY === "sampled") {
                Shiny.setInputValue("audio_loading", true, { priority: "event" });
            }
        }

        await initAudio();

        // Stop any existing playback
        Tone.Transport.stop();
        Tone.Transport.cancel();

        // Convert MIDI numbers to note names
        const chordNames = progression.map(chord =>
            chord.map(midi => midiToNoteName(midi))
        );

        // Schedule chords
        const chordDuration = "1n"; // Whole note duration
        const now = Tone.now();

        chordNames.forEach((chord, index) => {
            piano.triggerAttackRelease(chord, chordDuration, now + index);
        });

        // Calculate total duration and notify Shiny when complete
        const totalDuration = chordNames.length;

        setTimeout(() => {
            Shiny.setInputValue("playback_complete", Math.random(), { priority: "event" });
        }, totalDuration * 1000 + 500); // Add 500ms buffer

    } catch (error) {
        console.error("Error playing progression:", error);
        alert("Audio playback failed. Please refresh and try again.");
    }
}

// Listen for custom messages from Shiny
if (window.Shiny) {
    Shiny.addCustomMessageHandler("playProgression", function(message) {
        playProgression(message.progression);
    });
} else {
    console.error("Shiny object not found - audio module cannot initialize");
}
