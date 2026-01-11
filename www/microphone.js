/**
 * Microphone recording and pitch detection for voice singing module
 * Uses Web Audio API and Pitchy for real-time pitch extraction
 */

// Import Pitchy from CDN as ES module
import { PitchDetector } from 'https://cdn.jsdelivr.net/npm/pitchy@4/+esm';

// Check if Shiny is available
if (typeof window.Shiny === 'undefined') {
    console.error('Shiny is not defined! Microphone module may not work correctly.');
} else {
    console.log('Shiny is available in microphone module');
}

// Global state
let audioContext = null;
let mediaStream = null;
let analyzerNode = null;
let scriptProcessor = null;
let pitchDetector = null;
let isRecording = false;
let recordedPitches = [];
let recordingStartTime = null;

// Configuration
const FFT_SIZE = 2048;              // ~46ms window at 44.1kHz
const HOP_SIZE = FFT_SIZE / 2;      // 50% overlap
const SAMPLE_RATE = 44100;
const CLARITY_THRESHOLD = 0.5;      // YIN clarity threshold (relaxed)
const RMS_THRESHOLD = 0.01;         // Noise floor
const MIN_FREQUENCY = 80;           // Hz (singing voice range)
const MAX_FREQUENCY = 800;          // Hz

/**
 * Request microphone access and initialize audio context
 */
async function initializeMicrophone() {
    try {
        // Request microphone access
        mediaStream = await navigator.mediaDevices.getUserMedia({
            audio: {
                echoCancellation: false,
                noiseSuppression: false,
                autoGainControl: false
            }
        });

        // Create audio context
        audioContext = new (window.AudioContext || window.webkitAudioContext)({
            sampleRate: SAMPLE_RATE
        });

        // Create analyzer node
        analyzerNode = audioContext.createAnalyser();
        analyzerNode.fftSize = FFT_SIZE;

        // Create script processor for audio processing
        scriptProcessor = audioContext.createScriptProcessor(HOP_SIZE, 1, 1);

        // Connect nodes
        const source = audioContext.createMediaStreamSource(mediaStream);
        source.connect(analyzerNode);
        analyzerNode.connect(scriptProcessor);
        scriptProcessor.connect(audioContext.destination);

        // Initialize Pitchy detector (now using imported PitchDetector class)
        pitchDetector = PitchDetector.forFloat32Array(analyzerNode.fftSize);

        console.log("Microphone initialized successfully");
        return true;
    } catch (error) {
        console.error("Failed to initialize microphone:", error);
        if (typeof window.Shiny !== 'undefined') {
            window.Shiny.setInputValue("microphone_error", {
                message: error.message,
                timestamp: Date.now()
            }, { priority: "event" });
        }
        return false;
    }
}

/**
 * Calculate RMS (root mean square) of audio buffer
 */
function calculateRMS(buffer) {
    let sum = 0;
    for (let i = 0; i < buffer.length; i++) {
        sum += buffer[i] * buffer[i];
    }
    return Math.sqrt(sum / buffer.length);
}

/**
 * Start recording pitch data
 */
async function startRecording() {
    if (isRecording) {
        console.warn("Already recording");
        return;
    }

    // Initialize microphone if needed
    if (!audioContext || !pitchDetector) {
        const success = await initializeMicrophone();
        if (!success) {
            return;
        }
    }

    // Reset state
    recordedPitches = [];
    recordingStartTime = audioContext.currentTime;
    isRecording = true;

    // Set up audio processing
    scriptProcessor.onaudioprocess = (event) => {
        if (!isRecording) return;

        // Get FFT_SIZE samples from analyzer node (not from script processor buffer)
        const buffer = new Float32Array(analyzerNode.fftSize);
        analyzerNode.getFloatTimeDomainData(buffer);

        const currentTime = audioContext.currentTime - recordingStartTime;

        // Calculate RMS to detect silence
        const rms = calculateRMS(buffer);

        // Detect pitch using Pitchy
        let frequency = null;
        if (rms > RMS_THRESHOLD) {
            const [pitch, clarity] = pitchDetector.findPitch(buffer, SAMPLE_RATE);

            // Apply filters
            if (clarity > CLARITY_THRESHOLD &&
                pitch >= MIN_FREQUENCY &&
                pitch <= MAX_FREQUENCY) {
                frequency = pitch;
            }
        }

        // Store pitch data (null for silence/unvoiced)
        recordedPitches.push({
            time: currentTime,
            frequency: frequency
        });
    };

    console.log("Recording started");
    if (typeof window.Shiny !== 'undefined') {
        window.Shiny.setInputValue("recording_started", true, { priority: "event" });
    }
}

/**
 * Stop recording and send data to Python
 */
function stopRecording() {
    if (!isRecording) {
        console.warn("Not currently recording");
        return;
    }

    isRecording = false;
    const duration = audioContext ? audioContext.currentTime - recordingStartTime : 0;

    console.log(`Recording stopped. Duration: ${duration.toFixed(2)}s, Samples: ${recordedPitches.length}`);

    // Calculate actual sample rate
    const sampleRate = recordedPitches.length / duration;

    // Count non-null frequencies
    const validSamples = recordedPitches.filter(p => p.frequency !== null).length;
    console.log(`Valid pitch samples: ${validSamples} / ${recordedPitches.length}`);

    // Send recorded pitch data to Python
    const pitchData = {
        data: recordedPitches,
        duration: duration,
        sampleRate: sampleRate
    };
    console.log("Sending pitch data to Python:", pitchData);

    if (typeof window.Shiny !== 'undefined') {
        window.Shiny.setInputValue("recorded_pitch", pitchData, { priority: "event" });
        console.log("Sent recorded_pitch to Shiny");

        window.Shiny.setInputValue("recording_stopped", true, { priority: "event" });
        console.log("Sent recording_stopped to Shiny");
    } else {
        console.error("Shiny not available - cannot send pitch data!");
    }
}

/**
 * Clean up resources
 */
function cleanupMicrophone() {
    if (scriptProcessor) {
        scriptProcessor.disconnect();
        scriptProcessor = null;
    }
    if (analyzerNode) {
        analyzerNode.disconnect();
        analyzerNode = null;
    }
    if (mediaStream) {
        mediaStream.getTracks().forEach(track => track.stop());
        mediaStream = null;
    }
    if (audioContext) {
        audioContext.close();
        audioContext = null;
    }
    isRecording = false;
    recordedPitches = [];
    console.log("Microphone cleaned up");
}

// Make functions available globally
window.voiceMicrophone = {
    initialize: initializeMicrophone,
    startRecording: startRecording,
    stopRecording: stopRecording,
    cleanup: cleanupMicrophone,
    isRecording: () => isRecording
};
