/**
 * LinkForge - Link Downloader Controller
 * Handles URL analysis, format configuration, file generation, and email delivery.
 */

const DownloaderApp = {
    currentUrl: "",
    analysisData: null,
    selectedFormat: null,
    currentFileId: null,

    init() {
        this.bindEvents();
        this.checkQueryParam();
    },

    bindEvents() {
        const urlForm = document.getElementById("url-form");
        const urlInput = document.getElementById("url-input");
        const pasteBtn = document.getElementById("paste-btn");
        const clearBtn = document.getElementById("clear-btn");
        const btnStartDownload = document.getElementById("btn-start-download");
        const btnResetOptions = document.getElementById("btn-reset-options");
        const btnResetSuccess = document.getElementById("btn-reset-success");
        const btnResetError = document.getElementById("btn-reset-error");

        // Input typing listener
        if (urlInput) {
            urlInput.addEventListener("input", () => {
                if (clearBtn) {
                    clearBtn.style.display = urlInput.value.trim().length > 0 ? "inline-flex" : "none";
                }
            });
        }

        // Clear button
        if (clearBtn) {
            clearBtn.addEventListener("click", () => {
                urlInput.value = "";
                clearBtn.style.display = "none";
                urlInput.focus();
            });
        }

        // Paste button
        if (pasteBtn) {
            pasteBtn.addEventListener("click", async () => {
                try {
                    if (navigator.clipboard && navigator.clipboard.readText) {
                        const text = await navigator.clipboard.readText();
                        if (text) {
                            urlInput.value = text.trim();
                            if (clearBtn) clearBtn.style.display = "inline-flex";
                            urlInput.focus();
                        }
                    }
                } catch (e) {
                    console.warn("Clipboard access denied or unavailable", e);
                    urlInput.focus();
                }
            });
        }

        // Platform chips click
        document.querySelectorAll(".platform-chip").forEach(chip => {
            chip.addEventListener("click", () => {
                const example = chip.getAttribute("data-example");
                if (example && urlInput) {
                    urlInput.value = example;
                    if (clearBtn) clearBtn.style.display = "inline-flex";
                    this.analyzeUrl(example);
                }
            });
        });

        // Form submit
        if (urlForm) {
            urlForm.addEventListener("submit", (e) => {
                e.preventDefault();
                const url = urlInput.value.trim();
                if (!url) return;
                this.analyzeUrl(url);
            });
        }

        // Start generation / download
        if (btnStartDownload) {
            btnStartDownload.addEventListener("click", () => {
                this.startDownload();
            });
        }

        // Reset buttons
        if (btnResetOptions) btnResetOptions.addEventListener("click", () => this.showView("input-view"));
        if (btnResetSuccess) btnResetSuccess.addEventListener("click", () => this.resetToHome());
        if (btnResetError) btnResetError.addEventListener("click", () => this.showView("input-view"));

        // Email delivery toggle
        const emailToggle = document.getElementById("email-toggle-btn");
        const emailWidget = document.getElementById("email-widget");
        const emailSendBtn = document.getElementById("email-send-btn");

        if (emailToggle && emailWidget) {
            emailToggle.addEventListener("click", () => {
                emailWidget.classList.toggle("open");
            });
        }

        if (emailSendBtn) {
            emailSendBtn.addEventListener("click", () => {
                this.sendEmail();
            });
        }

        // Modal triggers
        this.initModals();
    },

    checkQueryParam() {
        const urlParams = new URLSearchParams(window.location.search);
        const queryUrl = urlParams.get("url");
        if (queryUrl && queryUrl.trim()) {
            const urlInput = document.getElementById("url-input");
            const clearBtn = document.getElementById("clear-btn");
            if (urlInput) {
                urlInput.value = queryUrl.trim();
                if (clearBtn) clearBtn.style.display = "inline-flex";
                this.analyzeUrl(queryUrl.trim());
            }
        }
    },

    showView(viewName) {
        const views = ["input-view", "loading-view", "options-view", "downloading-view", "success-view", "error-view"];
        views.forEach(v => {
            const el = document.getElementById(v);
            if (el) {
                if (v === viewName) {
                    el.classList.remove("hidden");
                } else {
                    el.classList.add("hidden");
                }
            }
        });
    },

    resetToHome() {
        const urlInput = document.getElementById("url-input");
        const clearBtn = document.getElementById("clear-btn");
        if (urlInput) urlInput.value = "";
        if (clearBtn) clearBtn.style.display = "none";
        this.currentUrl = "";
        this.analysisData = null;
        this.selectedFormat = null;
        this.currentFileId = null;
        this.showView("input-view");
        if (urlInput) urlInput.focus();
    },

    async analyzeUrl(url) {
        this.currentUrl = url;
        this.showView("loading-view");

        // Animated step simulation for smooth feedback
        const stepPlatform = document.getElementById("step-platform");
        const stepContent = document.getElementById("step-content");
        const stepMedia = document.getElementById("step-media");

        if (stepPlatform) stepPlatform.className = "step-item active";
        if (stepContent) stepContent.className = "step-item";
        if (stepMedia) stepMedia.className = "step-item";

        const t1 = setTimeout(() => {
            if (stepPlatform) stepPlatform.className = "step-item completed";
            if (stepContent) stepContent.className = "step-item active";
        }, 600);

        const t2 = setTimeout(() => {
            if (stepContent) stepContent.className = "step-item completed";
            if (stepMedia) stepMedia.className = "step-item active";
        }, 1200);

        try {
            const response = await fetch("/api/analyze", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ url: url })
            });

            clearTimeout(t1);
            clearTimeout(t2);

            const contentType = response.headers.get("content-type") || "";
            if (!contentType.includes("application/json")) {
                const text = await response.text();
                this.showError(text || `Server returned status ${response.status}`);
                return;
            }

            const data = await response.json();

            if (!response.ok || !data.success) {
                const msg = (data.error && data.error.message) || "Unable to extract content from this link.";
                this.showError(msg);
                return;
            }

            this.analysisData = data;
            this.renderOptions(data);
        } catch (err) {
            clearTimeout(t1);
            clearTimeout(t2);
            this.showError("Network connection failed. Please verify the URL and try again.");
        }
    },

    renderOptions(data) {
        // Badges and Meta
        const platformBadge = document.getElementById("res-platform");
        const typeBadge = document.getElementById("res-type");
        const titleEl = document.getElementById("res-title");
        const summaryEl = document.getElementById("res-summary");

        if (platformBadge) platformBadge.textContent = data.platform || "Direct Web";
        if (typeBadge) typeBadge.textContent = (data.content_type || "Media").replace(/_/g, " ");

        const count = data.media_count || 1;
        if (titleEl) {
            if (count > 1) {
                titleEl.textContent = `${data.platform || "Platform"} Collection (${count} Items)`;
            } else {
                titleEl.textContent = data.title || `${data.platform || "Media"} Download`;
            }
        }

        if (summaryEl) {
            if (count > 1) {
                summaryEl.textContent = `All ${count} items detected and ready to be packaged in your preferred format.`;
            } else {
                summaryEl.textContent = "1 item ready to download. Select your format options below.";
            }
        }

        // Previews
        const previewContainer = document.getElementById("preview-container");
        if (previewContainer) {
            previewContainer.innerHTML = "";
            if (Array.isArray(data.previews) && data.previews.length > 0) {
                if (data.previews.length === 1) {
                    const box = document.createElement("div");
                    box.className = "single-preview-box";
                    const img = document.createElement("img");
                    img.src = data.previews[0];
                    img.alt = "Media preview";
                    img.loading = "lazy";
                    box.appendChild(img);
                    previewContainer.appendChild(box);
                } else {
                    const header = document.createElement("div");
                    header.className = "preview-grid-header";
                    header.innerHTML = `
                        <span class="preview-count-pill">${data.previews.length} Items Detected</span>
                        <button type="button" class="preview-toggle-btn" id="toggle-previews">Show all</button>
                    `;
                    previewContainer.appendChild(header);

                    const grid = document.createElement("div");
                    grid.className = "preview-grid";

                    const renderGrid = (limit) => {
                        grid.innerHTML = "";
                        const list = limit ? data.previews.slice(0, limit) : data.previews;
                        list.forEach((url, i) => {
                            const item = document.createElement("div");
                            item.className = "preview-grid-item";
                            item.innerHTML = `
                                <img src="${url}" alt="Item ${i + 1}" loading="lazy">
                                <span class="page-badge">#${i + 1}</span>
                            `;
                            grid.appendChild(item);
                        });
                    };

                    let showingAll = data.previews.length <= 8;
                    renderGrid(showingAll ? null : 8);
                    previewContainer.appendChild(grid);

                    const toggleBtn = header.querySelector("#toggle-previews");
                    if (toggleBtn) {
                        if (data.previews.length <= 8) {
                            toggleBtn.style.display = "none";
                        } else {
                            toggleBtn.addEventListener("click", () => {
                                showingAll = !showingAll;
                                renderGrid(showingAll ? null : 8);
                                toggleBtn.textContent = showingAll ? "Show less" : "Show all";
                            });
                        }
                    }
                }
            }
        }

        // Format Selection Cards
        const formatGrid = document.getElementById("format-cards-grid");
        if (formatGrid) {
            formatGrid.innerHTML = "";

            const FORMAT_META = {
                pdf: { format: "pdf", label: "PDF Document", badge: "PDF", desc: "All pages/slides merged into a clean PDF document" },
                images_pdf: { format: "pdf", label: "PDF Document", badge: "PDF", desc: "Combine all extracted slides into a single PDF" },
                zip: { format: "zip", label: "ZIP Archive", badge: "ZIP", desc: "All original images and videos packaged in a ZIP archive" },
                images_zip: { format: "zip", label: "Images ZIP", badge: "ZIP", desc: "High-resolution extracted images packaged in a ZIP" },
                images: { format: "zip", label: "Images ZIP", badge: "ZIP", desc: "All individual extracted images in a ZIP" },
                all_zip: { format: "zip", label: "Complete ZIP", badge: "ZIP", desc: "Complete bundle of all media items extracted from this link" },
                docx: { format: "docx", label: "Word Document", badge: "DOCX", desc: "Editable Microsoft Word document with embedded media" },
                doc: { format: "docx", label: "Word Document", badge: "DOCX", desc: "Editable Microsoft Word document" },
                mp4: { format: "mp4", label: "MP4 Video", badge: "MP4", desc: "Universal video compatible with all devices and players" },
                video: { format: "mp4", label: "MP4 Video", badge: "MP4", desc: "Direct video stream packaged in MP4 container" },
                mkv: { format: "mkv", label: "MKV Video", badge: "MKV", desc: "Lossless Matroska container preserving all tracks" },
                webm: { format: "webm", label: "WebM Video", badge: "WEBM", desc: "Web-optimized lightweight video format" },
                audio: { format: "audio", label: "MP3 Audio", badge: "MP3", desc: "Extracted high-bitrate audio track (192 kbps)" },
                mp3: { format: "audio", label: "MP3 Audio", badge: "MP3", desc: "Standard high-fidelity MP3 audio stream" },
                m4a: { format: "m4a", label: "M4A Audio", badge: "AAC", desc: "Pristine Apple AAC high-clarity audio stream" },
                original: { format: "original", label: "Original Media", badge: "RAW", desc: "Direct source file in native original resolution" }
            };

            const rawFormats = (data.formats && Array.isArray(data.formats) && data.formats.length > 0)
                ? data.formats
                : (data.available_formats || ["original"]);

            // Deduplicate formats
            const seenKeys = new Set();
            const formatItems = [];

            rawFormats.forEach(f => {
                const key = typeof f === "string" ? f.toLowerCase().trim() : (f.format || "").toLowerCase().trim();
                const meta = FORMAT_META[key] || {
                    format: key || "original",
                    label: (key || "MEDIA").toUpperCase() + " File",
                    badge: (key || "FILE").toUpperCase(),
                    desc: `Download content packaged as .${key}`
                };
                if (!seenKeys.has(meta.format)) {
                    seenKeys.add(meta.format);
                    formatItems.push(meta);
                }
            });

            if (formatItems.length === 0) {
                formatItems.push(FORMAT_META.original);
            }

            this.selectedFormat = formatItems[0].format;

            const updateDownloadButtonText = (label) => {
                const btn = document.getElementById("btn-start-download");
                if (btn) {
                    btn.innerHTML = `&#x2193; Download as ${label}`;
                }
            };

            const updateQualityVisibility = (formatKey) => {
                const isVideo = ["mp4", "mkv", "webm", "video"].includes(String(formatKey).toLowerCase());
                const qualityRow = document.getElementById("quality-setting-group");
                if (qualityRow) {
                    qualityRow.style.display = (isVideo && data.available_qualities && data.available_qualities.length > 0) ? "flex" : "none";
                }
            };

            formatItems.forEach((fmt, index) => {
                const card = document.createElement("div");
                card.className = `format-card ${index === 0 ? "selected" : ""}`;
                card.setAttribute("data-format", fmt.format);
                card.innerHTML = `
                    <div class="format-card-top">
                        <span class="format-badge-pill">${fmt.badge}</span>
                        <span class="format-check-icon">${index === 0 ? "&#x2713;" : ""}</span>
                    </div>
                    <div class="format-label">${fmt.label}</div>
                    <div class="format-desc">${fmt.desc}</div>
                `;

                card.addEventListener("click", () => {
                    formatGrid.querySelectorAll(".format-card").forEach(c => {
                        c.classList.remove("selected");
                        const icon = c.querySelector(".format-check-icon");
                        if (icon) icon.innerHTML = "";
                    });
                    card.classList.add("selected");
                    const icon = card.querySelector(".format-check-icon");
                    if (icon) icon.innerHTML = "&#x2713;";
                    this.selectedFormat = fmt.format;
                    updateDownloadButtonText(fmt.label);
                    updateQualityVisibility(fmt.format);
                });

                formatGrid.appendChild(card);
            });

            updateDownloadButtonText(formatItems[0].label);
            updateQualityVisibility(formatItems[0].format);
        }

        // Quality Selector (if video)
        const qualityRow = document.getElementById("quality-setting-group");
        const qualitySelect = document.getElementById("quality-select");
        if (qualityRow && qualitySelect) {
            if (Array.isArray(data.available_qualities) && data.available_qualities.length > 0) {
                qualitySelect.innerHTML = "";
                data.available_qualities.forEach(q => {
                    const opt = document.createElement("option");
                    opt.value = q.value || q;
                    opt.textContent = q.label || q;
                    qualitySelect.appendChild(opt);
                });
                qualityRow.style.display = "flex";
            } else {
                qualityRow.style.display = "none";
            }
        }

        // Custom Filename Input
        const customFilenameInput = document.getElementById("custom-filename-input");
        if (customFilenameInput) {
            customFilenameInput.value = "";
            customFilenameInput.placeholder = data.title || "custom_filename (optional)";
        }

        // Caption toggle (if supported)
        const captionToggleRow = document.getElementById("caption-setting-group");
        if (captionToggleRow) {
            captionToggleRow.style.display = data.has_caption ? "flex" : "none";
        }

        this.showView("options-view");
    },

    async startDownload() {
        if (!this.currentUrl || !this.selectedFormat) return;

        this.showView("downloading-view");

        const customFilename = (document.getElementById("custom-filename-input")?.value || "").trim();
        const quality = document.getElementById("quality-select")?.value || "";
        const captionCheckbox = document.getElementById("include-caption-checkbox");
        const includeCaption = captionCheckbox ? captionCheckbox.checked : false;

        try {
            const response = await fetch("/api/generate", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    url: this.currentUrl,
                    format: this.selectedFormat,
                    quality: quality,
                    custom_filename: customFilename,
                    include_caption: includeCaption
                })
            });

            const data = await response.json();

            if (!response.ok || !data.success) {
                const msg = (data.error && data.error.message) || "Failed to package download.";
                this.showError(msg);
                return;
            }

            this.currentFileId = data.file_id;
            this.showSuccess(data);
        } catch (err) {
            this.showError("Network interrupted while generating download package.");
        }
    },

    showSuccess(data) {
        const fnEl = document.getElementById("success-filename");
        const szEl = document.getElementById("success-filesize");
        const fmtEl = document.getElementById("success-format");
        const dlBtn = document.getElementById("direct-download-btn");

        if (fnEl) fnEl.textContent = data.filename || "download_file";
        if (szEl) szEl.textContent = data.size_formatted || (data.filesize ? `${(data.filesize / (1024 * 1024)).toFixed(2)} MB` : "Ready");
        if (fmtEl) fmtEl.textContent = (this.selectedFormat || "FILE").toUpperCase();

        if (dlBtn) {
            const downloadUrl = `/download/${encodeURIComponent(data.file_id)}`;
            dlBtn.href = downloadUrl;
            dlBtn.setAttribute("download", data.filename || "download_file");
        }

        // Reset email widget state
        const emailWidget = document.getElementById("email-widget");
        const emailInput = document.getElementById("email-input");
        const emailStatus = document.getElementById("email-status-message");
        const emailSendBtn = document.getElementById("email-send-btn");

        if (emailWidget) emailWidget.classList.remove("open");
        if (emailInput) emailInput.value = "";
        if (emailStatus) {
            emailStatus.className = "email-status-message";
            emailStatus.textContent = "";
        }
        if (emailSendBtn) emailSendBtn.disabled = false;

        this.showView("success-view");
    },

    async sendEmail() {
        if (!this.currentFileId) return;

        const emailInput = document.getElementById("email-input");
        const emailStatus = document.getElementById("email-status-message");
        const emailSendBtn = document.getElementById("email-send-btn");

        const email = emailInput?.value.trim() || "";
        if (!email || !email.includes("@")) {
            if (emailStatus) {
                emailStatus.className = "email-status-message error";
                emailStatus.textContent = "Please enter a valid email address.";
            }
            return;
        }

        if (emailSendBtn) {
            emailSendBtn.disabled = true;
            emailSendBtn.textContent = "Sending...";
        }

        try {
            const response = await fetch("/api/send-email", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    file_id: this.currentFileId,
                    email: email
                })
            });

            const data = await response.json();

            if (emailSendBtn) {
                emailSendBtn.disabled = false;
                emailSendBtn.textContent = "Send";
            }

            if (response.ok && data.success) {
                if (emailStatus) {
                    emailStatus.className = "email-status-message success";
                    emailStatus.textContent = data.message || `File successfully delivered to ${email}!`;
                }
            } else {
                if (emailStatus) {
                    emailStatus.className = "email-status-message error";
                    emailStatus.textContent = (data.error && data.error.message) || "Could not deliver email. Please try again.";
                }
            }
        } catch (err) {
            if (emailSendBtn) {
                emailSendBtn.disabled = false;
                emailSendBtn.textContent = "Send";
            }
            if (emailStatus) {
                emailStatus.className = "email-status-message error";
                emailStatus.textContent = "Network error delivering email.";
            }
        }
    },

    showError(msg) {
        const errorEl = document.getElementById("error-message");
        if (errorEl) errorEl.textContent = msg || "An unexpected error occurred. Please try again.";
        this.showView("error-view");
    },

    initModals() {
        const openAbout = document.getElementById("open-about-modal");
        const closeAbout = document.getElementById("close-about-modal");
        const aboutModal = document.getElementById("about-modal");

        const openPlatforms = document.getElementById("open-platforms-modal");
        const closePlatforms = document.getElementById("close-platforms-modal");
        const platformsModal = document.getElementById("platforms-modal");

        if (openAbout && aboutModal) {
            openAbout.addEventListener("click", () => aboutModal.classList.add("show"));
        }
        if (closeAbout && aboutModal) {
            closeAbout.addEventListener("click", () => aboutModal.classList.remove("show"));
        }
        if (openPlatforms && platformsModal) {
            openPlatforms.addEventListener("click", () => platformsModal.classList.add("show"));
        }
        if (closePlatforms && platformsModal) {
            closePlatforms.addEventListener("click", () => platformsModal.classList.remove("show"));
        }

        // Close on backdrop click
        [aboutModal, platformsModal].forEach(modal => {
            if (modal) {
                modal.addEventListener("click", (e) => {
                    if (e.target === modal) modal.classList.remove("show");
                });
            }
        });
    }
};

document.addEventListener("DOMContentLoaded", () => {
    DownloaderApp.init();
});
