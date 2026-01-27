/**
 * Pitch plot visualization handler for voice singing module
 */

/**
 * Handle custom message from Python to display pitch plot
 */
Shiny.addCustomMessageHandler("displayPitchPlot", function(message) {
    const { imageData } = message;

    console.log("Received pitch plot data, length:", imageData ? imageData.length : 0);

    // Get the plot container
    const plotContainer = document.getElementById('voice-pitch-plot');
    if (!plotContainer) {
        console.error("Plot container not found");
        return;
    }

    // Clear previous plot
    plotContainer.innerHTML = '';

    // Check if we have valid image data
    if (!imageData || imageData.length < 100) {
        console.warn("No valid image data received for pitch plot");
        // Add a placeholder message
        const placeholder = document.createElement('p');
        placeholder.textContent = 'Pitch visualization is not available.';
        placeholder.style.padding = '20px';
        placeholder.style.textAlign = 'center';
        placeholder.style.color = '#666';
        plotContainer.appendChild(placeholder);
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

    // Add new plot
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
