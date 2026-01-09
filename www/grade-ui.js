/**
 * Grade UI Handlers for Multi-Grade Cadence Training
 *
 * Handles communication between Shiny (Python) and JavaScript for:
 * - Grade selection persistence (localStorage)
 * - Cadence button visibility by grade
 * - Toast notifications
 * - UI synchronization
 */

// Constants
const GRADE_STORAGE_KEY = 'g8aural_grade_level';

/**
 * Handler: Save grade to localStorage
 * Called when user changes grade slider
 */
Shiny.addCustomMessageHandler("saveGradeLevel", function(data) {
    try {
        localStorage.setItem(GRADE_STORAGE_KEY, data.grade);
        console.log(`Grade ${data.grade} saved to localStorage`);
    } catch (e) {
        console.warn('localStorage unavailable (private browsing?), grade will not persist:', e);
    }
});

/**
 * Handler: Request saved grade from localStorage
 * Called on app initialization to restore user's last selected grade
 */
Shiny.addCustomMessageHandler("requestSavedGrade", function(data) {
    let grade = 6; // Default to Grade 6

    try {
        const savedGrade = localStorage.getItem(GRADE_STORAGE_KEY);
        if (savedGrade) {
            const parsedGrade = parseInt(savedGrade);
            // Validate grade is 6, 7, or 8
            if ([6, 7, 8].includes(parsedGrade)) {
                grade = parsedGrade;
                console.log(`Restored grade ${grade} from localStorage`);
            }
        }
    } catch (e) {
        console.warn('localStorage unavailable, using default grade 6:', e);
    }

    // Send grade back to Shiny
    Shiny.setInputValue("saved_grade_level", grade, { priority: "event" });

    // Update slider UI to match
    const slider = document.getElementById("grade_slider");
    if (slider) {
        slider.value = grade;
    }
});

/**
 * Handler: Update UI based on grade level
 * Shows/hides cadence buttons and updates grade label
 */
Shiny.addCustomMessageHandler("updateGradeUI", function(data) {
    const grade = data.grade;
    const availableCadences = data.availableCadences;

    console.log(`Updating UI for Grade ${grade}, available cadences:`, availableCadences);

    // Map cadence types to button IDs
    const buttonMapping = {
        'perfect': 'perfect_btn',
        'plagal': 'plagal_btn',
        'imperfect': 'imperfect_btn',
        'interrupted': 'interrupted_btn'
    };

    // Show/hide buttons based on available cadences for this grade
    for (const [cadenceType, buttonId] of Object.entries(buttonMapping)) {
        const button = document.getElementById(buttonId);
        if (button) {
            if (availableCadences.includes(cadenceType)) {
                button.style.display = 'inline-block';
            } else {
                button.style.display = 'none';
            }
        }
    }

    // Update grade level label
    const label = document.getElementById("grade-label");
    if (label) {
        label.textContent = `Current Level: Grade ${grade}`;
    }
});

/**
 * Handler: Show toast notification
 * Displays temporary message at bottom of screen
 */
Shiny.addCustomMessageHandler("showToast", function(data) {
    // Create toast element
    const toast = document.createElement("div");
    toast.className = "toast-notification";
    toast.textContent = data.message;
    document.body.appendChild(toast);

    // Show toast with animation (small delay for CSS transition)
    setTimeout(() => {
        toast.classList.add("show");
    }, 10);

    // Hide and remove toast after 3 seconds
    setTimeout(() => {
        toast.classList.remove("show");
        // Remove from DOM after fade-out animation completes
        setTimeout(() => {
            toast.remove();
        }, 300);
    }, 3000);
});
