/**
 * Two-part melody playback for voice singing module
 * Uses Tone.js with stereo panning to distinguish soprano and bass voices
 */

// Global state for voice playback (use unique names to avoid conflicts with audio.js)
let voiceSopranoPiano = null;
let voiceBassPiano = null;
let voiceIsPlaying = false;
let voiceAudioInitialized = false;

/**
 * Initialize piano samplers with stereo panning
 */
async function initializeVoicePianos() {
    if (voiceAudioInitialized) {
        return; // Already initialized
    }

    try {
        await Tone.start();

        // Soprano piano (left channel)
        const sopranoPanner = new Tone.Panner(-0.7).toDestination();
        voiceSopranoPiano = new Tone.Sampler({
            urls: {
                "C4": "C4.mp3",
                "D#4": "Ds4.mp3",
                "F#4": "Fs4.mp3",
                "A4": "A4.mp3",
            },
            baseUrl: "https://tonejs.github.io/audio/salamander/",
        }).connect(sopranoPanner);
        voiceSopranoPiano.volume.value = -6; // Slightly quieter

        // Bass piano (right channel)
        const bassPanner = new Tone.Panner(0.7).toDestination();
        voiceBassPiano = new Tone.Sampler({
            urls: {
                "C4": "C4.mp3",
                "D#4": "Ds4.mp3",
                "F#4": "Fs4.mp3",
                "A4": "A4.mp3",
            },
            baseUrl: "https://tonejs.github.io/audio/salamander/",
        }).connect(bassPanner);
        voiceBassPiano.volume.value = -3; // Slightly louder

        // Wait for samples to load
        await Tone.loaded();

        voiceAudioInitialized = true;
        console.log("Voice playback pianos initialized");
    } catch (error) {
        console.error("Failed to initialize pianos:", error);
        throw error;
    }
}

/**
 * Convert MIDI note number to note name (e.g., 60 -> "C4")
 */
function midiToNoteName(midi) {
    const noteNames = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"];
    const octave = Math.floor(midi / 12) - 1;
    const noteName = noteNames[midi % 12];
    return noteName + octave;
}

/**
 * Play a two-part melody with stereo separation
 * @param {Array} sopranoMelody - Array of [midi, startTime, duration] tuples
 * @param {Array} bassMelody - Array of [midi, startTime, duration] tuples
 */
async function playVoiceMelody(sopranoMelody, bassMelody) {
    if (voiceIsPlaying) {
        console.warn("Already playing a melody");
        return;
    }

    try {
        console.log("Initializing pianos...");
        // Initialize pianos if needed
        await initializeVoicePianos();
        console.log("Pianos initialized, starting playback");

        voiceIsPlaying = true;
        console.log("Playing two-part melody...");

        // Schedule soprano notes
        const now = Tone.now();
        console.log(`Scheduling ${sopranoMelody.length} soprano notes`);
        sopranoMelody.forEach(([midi, startTime, duration]) => {
            const noteName = midiToNoteName(midi);
            console.log(`Soprano: ${noteName} at ${startTime}s for ${duration}s`);
            voiceSopranoPiano.triggerAttackRelease(noteName, duration, now + startTime);
        });

        // Schedule bass notes
        console.log(`Scheduling ${bassMelody.length} bass notes`);
        bassMelody.forEach(([midi, startTime, duration]) => {
            const noteName = midiToNoteName(midi);
            console.log(`Bass: ${noteName} at ${startTime}s for ${duration}s`);
            voiceBassPiano.triggerAttackRelease(noteName, duration, now + startTime);
        });

        // Calculate total duration
        const sopranoEnd = sopranoMelody.length > 0 ? Math.max(...sopranoMelody.map(([m, s, d]) => s + d)) : 0;
        const bassEnd = bassMelody.length > 0 ? Math.max(...bassMelody.map(([m, s, d]) => s + d)) : 0;
        const totalDuration = Math.max(sopranoEnd, bassEnd);
        console.log(`Total duration: ${totalDuration}s`);

        // Send playback complete message after melody finishes
        setTimeout(() => {
            voiceIsPlaying = false;
            console.log("Melody playback complete");
            if (typeof window.Shiny !== 'undefined') {
                window.Shiny.setInputValue("voice_playback_complete", Math.random(), { priority: "event" });
            }
        }, (totalDuration + 0.5) * 1000); // Add 0.5s buffer

        return totalDuration;
    } catch (error) {
        console.error("Error in playVoiceMelody:", error);
        voiceIsPlaying = false;
        throw error;
    }
}

/**
 * Stop playback
 */
function stopVoicePlayback() {
    if (voiceSopranoPiano) {
        voiceSopranoPiano.releaseAll();
    }
    if (voiceBassPiano) {
        voiceBassPiano.releaseAll();
    }
    voiceIsPlaying = false;
    console.log("Voice playback stopped");
}

/**
 * Handle custom message from Python
 */
if (typeof window.Shiny !== 'undefined') {
    window.Shiny.addCustomMessageHandler("playVoiceMelody", async function(message) {
    const { soprano, bass, key } = message;

    console.log("Received voice melody:", {
        sopranoNotes: soprano.length,
        bassNotes: bass.length,
        key: key,
        soprano: soprano,
        bass: bass
    });

    try {
        console.log("Starting voice melody playback...");

        // Check if melodies are empty
        if (soprano.length === 0 && bass.length === 0) {
            console.error("Both melodies are empty!");
            return;
        }
        // Play melody first (user listens)
        const duration = await playVoiceMelody(soprano, bass);

        // After melody ends, start recording for user to sing back
        setTimeout(async () => {
            if (window.voiceMicrophone) {
                await window.voiceMicrophone.startRecording();

                // Show recording indicator
                const indicator = document.getElementById('recording-indicator');
                if (indicator) {
                    indicator.style.display = 'flex';
                }

                // Stop recording after duration + 2 seconds
                setTimeout(() => {
                    if (window.voiceMicrophone) {
                        window.voiceMicrophone.stopRecording();

                        // Hide recording indicator
                        const indicator = document.getElementById('recording-indicator');
                        if (indicator) {
                            indicator.style.display = 'none';
                        }
                    }
                }, (duration + 2.0) * 1000);
            }
        }, duration * 1000);

    } catch (error) {
        console.error("Error playing voice melody:", error);
        if (typeof window.Shiny !== 'undefined') {
            window.Shiny.setInputValue("voice_playback_error", {
                message: error.message,
                timestamp: Date.now()
            }, { priority: "event" });
        }

        // Hide recording indicator on error
        const indicator = document.getElementById('recording-indicator');
        if (indicator) {
            indicator.style.display = 'none';
        }
    }
    });
} else {
    console.error('Shiny not available - voice playback will not work');
}

// Make functions available globally
window.voicePlayback = {
    play: playVoiceMelody,
    stop: stopVoicePlayback,
    isPlaying: () => voiceIsPlaying
};
