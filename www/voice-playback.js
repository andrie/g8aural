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
        // Support both old format (soprano, bass, key) and new format (melodies, grade, key)
        let soprano, bass, key, grade;

        if (message.melodies) {
            // New format (Phase 1+)
            soprano = message.melodies.soprano || [];
            bass = message.melodies.bass || [];
            key = message.key;
            grade = message.grade || 8;  // Default to Grade 8
        } else {
            // Old format (backward compatibility)
            soprano = message.soprano || [];
            bass = message.bass || [];
            key = message.key;
            grade = 8;  // Assume Grade 8 for old format
        }

        console.log("Received voice melody:", {
            grade: grade,
            sopranoNotes: soprano.length,
            bassNotes: bass.length,
            key: key
        });

        try {
            console.log(`Starting Grade ${grade} voice melody playback...`);

            // Check if melodies are empty
            if (soprano.length === 0 && bass.length === 0) {
                console.error("Both melodies are empty!");
                return;
            }

            // Grade 5: Play only soprano (centered)
            if (grade === 5) {
                console.log("Grade 5: Playing single melody (centered)");

                // Initialize just soprano piano with centered panning
                await Tone.start();
                const centerPanner = new Tone.Panner(0).toDestination();  // Pan = 0 (center)
                const centeredPiano = new Tone.Sampler({
                    urls: {
                        "C4": "C4.mp3",
                        "D#4": "Ds4.mp3",
                        "F#4": "Fs4.mp3",
                        "A4": "A4.mp3",
                    },
                    baseUrl: "https://tonejs.github.io/audio/salamander/",
                }).connect(centerPanner);
                centeredPiano.volume.value = 0;  // Normal volume

                await Tone.loaded();

                // Schedule notes
                const now = Tone.now();
                soprano.forEach(([midi, startTime, duration]) => {
                    const noteName = midiToNoteName(midi);
                    centeredPiano.triggerAttackRelease(noteName, duration, now + startTime);
                });

                // Calculate duration
                const sopranoEnd = soprano.length > 0 ? Math.max(...soprano.map(([m, s, d]) => s + d)) : 0;
                const totalDuration = sopranoEnd;

                // Send playback complete after melody finishes
                setTimeout(() => {
                    voiceIsPlaying = false;
                    console.log("Grade 5 melody playback complete");
                    window.Shiny.setInputValue("voice_playback_complete", Math.random(), { priority: "event" });
                }, (totalDuration + 0.5) * 1000);

                // Start recording after playback (for Grade 5)
                setTimeout(async () => {
                    if (window.voiceMicrophone) {
                        await window.voiceMicrophone.startRecording();

                        const indicator = document.getElementById('recording-indicator');
                        if (indicator) {
                            indicator.style.display = 'flex';
                        }

                        setTimeout(() => {
                            if (window.voiceMicrophone) {
                                window.voiceMicrophone.stopRecording();

                                const indicator = document.getElementById('recording-indicator');
                                if (indicator) {
                                    indicator.style.display = 'none';
                                }
                            }
                        }, (totalDuration + 2.0) * 1000);
                    }
                }, totalDuration * 1000);

            } else {
                // Grades 6-8: Play both voices in stereo (existing behavior)
                const duration = await playVoiceMelody(soprano, bass);

                // After melody ends, start recording (existing behavior)
                setTimeout(async () => {
                    if (window.voiceMicrophone) {
                        await window.voiceMicrophone.startRecording();

                        const indicator = document.getElementById('recording-indicator');
                        if (indicator) {
                            indicator.style.display = 'flex';
                        }

                        setTimeout(() => {
                            if (window.voiceMicrophone) {
                                window.voiceMicrophone.stopRecording();

                                const indicator = document.getElementById('recording-indicator');
                                if (indicator) {
                                    indicator.style.display = 'none';
                                }
                            }
                        }, (duration + 2.0) * 1000);
                    }
                }, duration * 1000);
            }

        } catch (error) {
            console.error("Error playing voice melody:", error);
            window.Shiny.setInputValue("voice_playback_error", {
                message: error.message,
                timestamp: Date.now()
            }, { priority: "event" });

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
