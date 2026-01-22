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

// Live pitch visualization state
let livePitchCanvas = null;
let livePitchContext = null;
let pitchHistory = [];
const MAX_PITCH_HISTORY = 100;  // ~5 seconds at 20 fps

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
 * Initialize live pitch plot canvas
 */
function initLivePitchPlot() {
    livePitchCanvas = document.getElementById('live-pitch-canvas');
    if (!livePitchCanvas) {
        console.warn("Live pitch canvas not found");
        return;
    }

    livePitchContext = livePitchCanvas.getContext('2d');
    pitchHistory = [];

    // Show canvas and recording indicator
    livePitchCanvas.style.display = 'block';
    const recordingIndicator = document.getElementById('recording-indicator');
    if (recordingIndicator) {
        recordingIndicator.style.display = 'block';
    }

    console.log("Live pitch plot initialized");
}

/**
 * Update live pitch plot with new frequency data
 * @param {number|null} frequency - Detected frequency in Hz (or null if no pitch detected)
 * @param {number} clarity - Confidence score from Pitchy (0-1)
 */
function updateLivePitchPlot(frequency, clarity) {
    if (!livePitchContext) return;

    // Add to history
    pitchHistory.push({
        freq: frequency,
        clarity: clarity,
        time: Date.now()
    });

    // Trim history to MAX_PITCH_HISTORY
    if (pitchHistory.length > MAX_PITCH_HISTORY) {
        pitchHistory.shift();
    }

    // Clear canvas
    const width = livePitchCanvas.width;
    const height = livePitchCanvas.height;
    livePitchContext.clearRect(0, 0, width, height);

    // Draw background grid
    livePitchContext.strokeStyle = '#e0e0e0';
    livePitchContext.lineWidth = 1;
    for (let i = 0; i < 5; i++) {
        const y = (height / 4) * i;
        livePitchContext.beginPath();
        livePitchContext.moveTo(0, y);
        livePitchContext.lineTo(width, y);
        livePitchContext.stroke();
    }

    // Draw pitch line if we have data
    if (pitchHistory.length < 2) return;

    // Map frequencies to Y coordinates (log scale for musical perception)
    // Typical singing range: 80 Hz (E2) to 1000 Hz (C6)
    const minFreq = 80;
    const maxFreq = 1000;

    function freqToY(freq) {
        if (!freq || freq < minFreq) return height;  // Bottom if no pitch
        const logMin = Math.log(minFreq);
        const logMax = Math.log(maxFreq);
        const logFreq = Math.log(Math.max(minFreq, Math.min(maxFreq, freq)));
        const normalized = (logFreq - logMin) / (logMax - logMin);
        return height - (normalized * height);  // Invert Y axis
    }

    // Draw line connecting pitch points
    livePitchContext.strokeStyle = '#4CAF50';  // Green
    livePitchContext.lineWidth = 2;
    livePitchContext.beginPath();

    let started = false;
    pitchHistory.forEach((point, i) => {
        const x = (i / MAX_PITCH_HISTORY) * width;
        const y = freqToY(point.freq);

        // Only draw if clarity is decent (avoid noise)
        if (point.clarity > 0.85) {
            if (!started) {
                livePitchContext.moveTo(x, y);
                started = true;
            } else {
                livePitchContext.lineTo(x, y);
            }
        }
    });

    livePitchContext.stroke();

    // Draw frequency labels
    livePitchContext.fillStyle = '#666';
    livePitchContext.font = '12px monospace';
    livePitchContext.textAlign = 'right';

    // Show reference frequencies
    [100, 200, 400, 800].forEach(freq => {
        const y = freqToY(freq);
        livePitchContext.fillText(`${freq} Hz`, width - 5, y + 4);
    });
}

/**
 * Clear and hide the live pitch plot
 */
function clearLivePitchPlot() {
    if (livePitchCanvas) {
        livePitchCanvas.style.display = 'none';
    }

    const recordingIndicator = document.getElementById('recording-indicator');
    if (recordingIndicator) {
        recordingIndicator.style.display = 'none';
    }

    pitchHistory = [];
    console.log("Live pitch plot cleared");
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

    // Initialize live pitch plot
    initLivePitchPlot();

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
        let clarity = 0;
        if (rms > RMS_THRESHOLD) {
            [frequency, clarity] = pitchDetector.findPitch(buffer, SAMPLE_RATE);

            // Apply filters
            if (clarity > CLARITY_THRESHOLD &&
                frequency >= MIN_FREQUENCY &&
                frequency <= MAX_FREQUENCY) {
                // frequency is valid, keep it
            } else {
                frequency = null;  // Invalid, set to null
            }
        }

        // Update live pitch plot
        updateLivePitchPlot(frequency, clarity);

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

    // Clear live pitch plot
    clearLivePitchPlot();

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
