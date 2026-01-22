/**
 * Pitch plot visualization handler for voice singing module
 */

/**
 * Handle custom message from Python to display pitch plot
 */
Shiny.addCustomMessageHandler("displayPitchPlot", function(message) {
    const { imageData } = message;

    console.log("Received pitch plot data");

    // Get the plot container
    const plotContainer = document.getElementById('voice-pitch-plot');
    if (!plotContainer) {
        console.error("Plot container not found");
        return;
    }

    // Create image element
    const img = document.createElement('img');
    img.src = `data:image/png;base64,${imageData}`;
    img.alt = 'Pitch Accuracy Comparison';
    img.style.width = '100%';
    img.style.maxWidth = '800px';
    img.style.height = 'auto';
    img.style.border = '1px solid #ddd';
    img.style.borderRadius = '4px';
    img.style.marginTop = '20px';

    // Clear previous plot and add new one
    plotContainer.innerHTML = '';
    plotContainer.appendChild(img);

    console.log("Pitch plot displayed");
});

/**
 * Handle custom message to clear pitch plot
 */
Shiny.addCustomMessageHandler("clearVoicePlot", function(message) {
    const plotContainer = document.getElementById('voice-pitch-plot');
    if (plotContainer) {
        plotContainer.innerHTML = '';
    }
    console.log("Pitch plot cleared");
});

/**
 * Handle custom message to update voice button visibility
 */
Shiny.addCustomMessageHandler("updateVoiceButtons", function(message) {
    const { tryAgainVisible } = message;

    const tryAgainBtn = document.getElementById('voice_try_again_btn');
    if (tryAgainBtn) {
        tryAgainBtn.style.display = tryAgainVisible ? 'inline-block' : 'none';
    }

    console.log(`Try Again button visibility: ${tryAgainVisible}`);
});
