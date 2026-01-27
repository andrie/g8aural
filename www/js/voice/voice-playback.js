/**
 * Two-part melody playback for voice singing module
 * Uses Tone.js with stereo panning to distinguish soprano and bass voices
 */

// Global state for voice playback (use unique names to avoid conflicts with audio.js)
let voiceSopranoPiano = null;
let voiceAltoPiano = null;
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
        voiceSopranoPiano.volume.value = -3; // Moderately quieter but audible

        // Alto piano (center-left channel) for Grade 8
        const altoPanner = new Tone.Panner(-0.3).toDestination();
        voiceAltoPiano = new Tone.Sampler({
            urls: {
                "C4": "C4.mp3",
                "D#4": "Ds4.mp3",
                "F#4": "Fs4.mp3",
                "A4": "A4.mp3",
            },
            baseUrl: "https://tonejs.github.io/audio/salamander/",
        }).connect(altoPanner);
        voiceAltoPiano.volume.value = -3; // Moderately quieter but audible

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
        voiceBassPiano.volume.value = 0; // Normal volume (target voice for Grades 7-8)

        // Wait for samples to load
        await Tone.loaded();

        voiceAudioInitialized = true;
        console.log("Voice playback pianos initialized (3 voices)");
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
 * Play multi-voice melody with stereo separation (plays twice for ABRSM)
 * @param {Array} sopranoMelody - Array of [midi, startTime, duration] tuples
 * @param {Array} bassMelody - Array of [midi, startTime, duration] tuples
 * @param {Array} altoMelody - Optional array for Grade 8 (default: null)
 * @param {number} repetitions - Number of times to play (default: 2 for ABRSM)
 */
async function playVoiceMelody(sopranoMelody, bassMelody, altoMelody = null, repetitions = 2) {
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
        const voiceCount = altoMelody ? 3 : 2;
        console.log(`Playing ${voiceCount}-voice melody ${repetitions} times...`);

        // Calculate single repetition duration
        const sopranoEnd = sopranoMelody.length > 0 ? Math.max(...sopranoMelody.map(([m, s, d]) => s + d)) : 0;
        const altoEnd = altoMelody && altoMelody.length > 0 ? Math.max(...altoMelody.map(([m, s, d]) => s + d)) : 0;
        const bassEnd = bassMelody.length > 0 ? Math.max(...bassMelody.map(([m, s, d]) => s + d)) : 0;
        const singleDuration = Math.max(sopranoEnd, altoEnd, bassEnd);
        const pauseBetweenReps = 1.0; // 1 second pause between repetitions

        // Schedule notes for all repetitions
        const now = Tone.now();

        for (let rep = 0; rep < repetitions; rep++) {
            const repOffset = rep * (singleDuration + pauseBetweenReps);
            console.log(`Scheduling repetition ${rep + 1}/${repetitions} at offset ${repOffset.toFixed(2)}s`);

            // Schedule soprano notes for this repetition
            sopranoMelody.forEach(([midi, startTime, duration]) => {
                const noteName = midiToNoteName(midi);
                voiceSopranoPiano.triggerAttackRelease(noteName, duration, now + repOffset + startTime);
            });

            // Schedule alto notes (if present, for Grade 8)
            if (altoMelody) {
                altoMelody.forEach(([midi, startTime, duration]) => {
                    const noteName = midiToNoteName(midi);
                    voiceAltoPiano.triggerAttackRelease(noteName, duration, now + repOffset + startTime);
                });
            }

            // Schedule bass notes for this repetition
            bassMelody.forEach(([midi, startTime, duration]) => {
                const noteName = midiToNoteName(midi);
                voiceBassPiano.triggerAttackRelease(noteName, duration, now + repOffset + startTime);
            });
        }

        // Total duration including all repetitions and pauses
        const totalDuration = (singleDuration * repetitions) + (pauseBetweenReps * (repetitions - 1));
        console.log(`Single repetition: ${singleDuration}s, Total duration: ${totalDuration}s`);

        // Send playback complete message after all repetitions finish
        setTimeout(() => {
            voiceIsPlaying = false;
            console.log("Melody playback complete (all repetitions)");
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
    if (voiceAltoPiano) {
        voiceAltoPiano.releaseAll();
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
        let soprano, alto, bass, key, grade;

        if (message.melodies) {
            // New format (Phase 1+)
            soprano = message.melodies.soprano || [];
            alto = message.melodies.alto || null;  // May be null for Grades 5-7
            bass = message.melodies.bass || [];
            key = message.key;
            grade = message.grade || 8;  // Default to Grade 8
        } else {
            // Old format (backward compatibility)
            soprano = message.soprano || [];
            alto = null;
            bass = message.bass || [];
            key = message.key;
            grade = 8;  // Assume Grade 8 for old format
        }

        console.log("Received voice melody:", {
            grade: grade,
            sopranoNotes: soprano.length,
            altoNotes: alto ? alto.length : 0,
            bassNotes: bass.length,
            key: key
        });

        try {
            // MOBILE FIX: Initialize microphone BEFORE melody playback starts
            // Mobile browsers require getUserMedia() to be called during a user gesture.
            // Shiny message handlers run shortly after button clicks, so we initialize
            // the microphone here while the gesture context is still valid.
            if (window.voiceMicrophone) {
                console.log("Pre-initializing microphone for mobile compatibility...");
                const micInitialized = await window.voiceMicrophone.initialize();
                if (micInitialized) {
                    console.log("Microphone pre-initialized successfully");
                } else {
                    console.warn("Microphone pre-initialization failed - recording may not work");
                }
            }

            console.log(`Starting Grade ${grade} voice melody playback...`);

            // Check if melodies are empty
            if (soprano.length === 0 && bass.length === 0) {
                console.error("Both melodies are empty!");
                return;
            }

            // Grade 5: Play only soprano (centered), twice for ABRSM
            if (grade === 5) {
                console.log("Grade 5: Playing single melody twice (centered)");

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

                // Calculate single repetition duration
                const sopranoEnd = soprano.length > 0 ? Math.max(...soprano.map(([m, s, d]) => s + d)) : 0;
                const singleDuration = sopranoEnd;
                const pauseBetweenReps = 1.0; // 1 second pause
                const repetitions = 2;

                // Schedule notes for both repetitions
                const now = Tone.now();
                for (let rep = 0; rep < repetitions; rep++) {
                    const repOffset = rep * (singleDuration + pauseBetweenReps);
                    console.log(`Grade 5: Scheduling repetition ${rep + 1}/${repetitions} at offset ${repOffset.toFixed(2)}s`);

                    soprano.forEach(([midi, startTime, duration]) => {
                        const noteName = midiToNoteName(midi);
                        centeredPiano.triggerAttackRelease(noteName, duration, now + repOffset + startTime);
                    });
                }

                // Total duration including both repetitions and pause
                const totalDuration = (singleDuration * repetitions) + (pauseBetweenReps * (repetitions - 1));
                console.log(`Grade 5: Single repetition ${singleDuration}s, Total duration: ${totalDuration}s`);

                // Send playback complete after melody finishes
                setTimeout(() => {
                    voiceIsPlaying = false;
                    console.log("Grade 5 melody playback complete (both repetitions)");
                    window.Shiny.setInputValue("voice_playback_complete", Math.random(), { priority: "event" });
                }, (totalDuration + 0.5) * 1000);

                // Start recording after playback (for Grade 5)
                setTimeout(async () => {
                    if (window.voiceMicrophone) {
                        // Initialize microphone early to give browser time to set up
                        await window.voiceMicrophone.initialize();

                        console.log("Grade 5: Microphone initialized, starting recording...");
                        await window.voiceMicrophone.startRecording();

                        const indicator = document.getElementById('voice-recording-indicator');
                        if (indicator) {
                            indicator.style.display = 'flex';
                        }

                        setTimeout(() => {
                            if (window.voiceMicrophone) {
                                window.voiceMicrophone.stopRecording();

                                const indicator = document.getElementById('voice-recording-indicator');
                                if (indicator) {
                                    indicator.style.display = 'none';
                                }
                            }
                        }, (singleDuration + 2.0) * 1000);
                    }
                }, totalDuration * 1000);

            } else {
                // Grades 6-8: Play 2 or 3 voices in stereo
                const duration = await playVoiceMelody(soprano, bass, alto);

                // After melody ends, start recording
                setTimeout(async () => {
                    if (window.voiceMicrophone) {
                        // Initialize microphone early to give browser time to set up
                        await window.voiceMicrophone.initialize();

                        console.log("Microphone initialized, starting recording...");
                        await window.voiceMicrophone.startRecording();

                        const indicator = document.getElementById('voice-recording-indicator');
                        if (indicator) {
                            indicator.style.display = 'flex';
                        }

                        setTimeout(() => {
                            if (window.voiceMicrophone) {
                                window.voiceMicrophone.stopRecording();

                                const indicator = document.getElementById('voice-recording-indicator');
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

            const indicator = document.getElementById('voice-recording-indicator');
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

/**
 * MOBILE FIX: Attach direct click handler to voice_start_btn
 *
 * Mobile browsers require getUserMedia() and AudioContext creation to happen
 * during an actual user gesture (tap/click). Shiny's message handlers run
 * asynchronously after the button click, which may be "too late" for mobile.
 *
 * This direct click handler ensures microphone initialization happens
 * immediately during the user gesture, before Shiny processes the click.
 */
function attachMicrophonePreInitHandler() {
    // Attach to Start Task button
    const startBtn = document.getElementById('voice_start_btn');
    if (startBtn && !startBtn._micHandlerAttached) {
        startBtn.addEventListener('click', function(event) {
            console.log("Start button clicked - pre-initializing microphone for mobile...");
            if (window.voiceMicrophone) {
                // Don't await here to avoid blocking Shiny's click processing
                // The initialization will complete before the melody finishes
                window.voiceMicrophone.initialize().then(success => {
                    if (success) {
                        console.log("Microphone pre-initialized on button click");
                    } else {
                        console.warn("Microphone pre-init failed on button click");
                    }
                }).catch(err => {
                    console.error("Microphone pre-init error:", err);
                });
            }
        }, { capture: true }); // Use capture phase to run before Shiny handlers
        startBtn._micHandlerAttached = true;
        console.log("Microphone pre-init handler attached to Start button");
    }

    // Attach to Try Again button
    const tryAgainBtn = document.getElementById('voice_try_again_btn');
    if (tryAgainBtn && !tryAgainBtn._micHandlerAttached) {
        tryAgainBtn.addEventListener('click', function(event) {
            console.log("Try Again button clicked - pre-initializing microphone for mobile...");
            if (window.voiceMicrophone) {
                window.voiceMicrophone.initialize().then(success => {
                    if (success) {
                        console.log("Microphone pre-initialized on Try Again click");
                    } else {
                        console.warn("Microphone pre-init failed on Try Again click");
                    }
                }).catch(err => {
                    console.error("Microphone pre-init error:", err);
                });
            }
        }, { capture: true });
        tryAgainBtn._micHandlerAttached = true;
        console.log("Microphone pre-init handler attached to Try Again button");
    }
}

// Attach handler when DOM is ready, or use MutationObserver for dynamic content
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', attachMicrophonePreInitHandler);
} else {
    attachMicrophonePreInitHandler();
}

// Also use MutationObserver to handle Shiny's dynamic rendering
const observer = new MutationObserver(function(mutations) {
    attachMicrophonePreInitHandler();
});
observer.observe(document.body, { childList: true, subtree: true });
