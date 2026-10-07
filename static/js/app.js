/**
 * LinkForge - Main Application Controller
 */

document.addEventListener("DOMContentLoaded", () => {
    const urlForm = document.getElementById("url-form");
    const urlInput = document.getElementById("url-input");
    const pasteBtn = document.getElementById("paste-btn");
    const clearBtn = document.getElementById("clear-btn");
    const btnResetResult = document.getElementById("btn-reset-result");
    const btnResetSuccess = document.getElementById("btn-reset-success");
    const btnTryAgain = document.getElementById("btn-try-again");

    // Modals
    const aboutModal = document.getElementById("about-modal");
    const platformsModal = document.getElementById("platforms-modal");
    const openAboutBtn = document.getElementById("open-about-modal");
    const closeAboutBtn = document.getElementById("close-about-modal");
    const openPlatformsBtn = document.getElementById("open-platforms-modal");
    const closePlatformsBtn = document.getElementById("close-platforms-modal");

    // Input changes & clear button toggle
    urlInput.addEventListener("input", () => {
        if (urlInput.value.trim().length > 0) {
            clearBtn.style.display = "inline-block";
        } else {
            clearBtn.style.display = "none";
        }
    });

    // Clear input
    clearBtn.addEventListener("click", () => {
        urlInput.value = "";
        clearBtn.style.display = "none";
        urlInput.focus();
    });

    // Clipboard Paste
    pasteBtn.addEventListener("click", async () => {
        try {
            if (navigator.clipboard && navigator.clipboard.readText) {
                const text = await navigator.clipboard.readText();
                if (text) {
                    urlInput.value = text.trim();
                    clearBtn.style.display = "inline-block";
                    urlInput.focus();
                }
            } else {
                urlInput.focus();
            }
        } catch (err) {
            console.warn("Clipboard access denied or unsupported", err);
            urlInput.focus();
        }
    });

    // Form Submit
    urlForm.addEventListener("submit", (e) => {
        e.preventDefault();
        const url = urlInput.value.trim();
        if (!url) return;

        Analyzer.analyze(url);
    });

    // Reset Buttons
    if (btnResetResult) {
        btnResetResult.addEventListener("click", () => Analyzer.resetToHome());
    }
    if (btnResetSuccess) {
        btnResetSuccess.addEventListener("click", () => Analyzer.resetToHome());
    }
    if (btnTryAgain) {
        btnTryAgain.addEventListener("click", () => Analyzer.resetToHome());
    }

    // Modal Events
    if (openAboutBtn) {
        openAboutBtn.addEventListener("click", () => {
            aboutModal.style.display = "flex";
        });
    }
    if (closeAboutBtn) {
        closeAboutBtn.addEventListener("click", () => {
            aboutModal.style.display = "none";
        });
    }
    if (openPlatformsBtn) {
        openPlatformsBtn.addEventListener("click", () => {
            platformsModal.style.display = "flex";
        });
    }
    if (closePlatformsBtn) {
        closePlatformsBtn.addEventListener("click", () => {
            platformsModal.style.display = "none";
        });
    }

    // Close modals on clicking backdrop
    window.addEventListener("click", (e) => {
        if (e.target === aboutModal) aboutModal.style.display = "none";
        if (e.target === platformsModal) platformsModal.style.display = "none";
    });

    // Check for ?url= query parameter (e.g. from fallback bridge)
    const urlParams = new URLSearchParams(window.location.search);
    const queryUrl = urlParams.get("url");
    if (queryUrl && queryUrl.trim()) {
        urlInput.value = queryUrl.trim();
        clearBtn.style.display = "inline-block";
        Analyzer.analyze(queryUrl.trim());
    }
});
