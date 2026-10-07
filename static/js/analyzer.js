/**
 * LinkForge - URL Analyzer Service (Frontend)
 * Responsible for submitting URLs for analysis, managing loading states,
 * and dynamically building format selection options.
 */

const Analyzer = {
    currentUrl: "",
    analysisResult: null,

    async analyze(url) {
        this.currentUrl = url;
        this.showLoading();

        // Step animation timers for UX feedback
        const stepPlatform = document.getElementById("step-platform");
        const stepContent = document.getElementById("step-content");
        const stepMedia = document.getElementById("step-media");

        stepPlatform.className = "step-item active";
        stepContent.className = "step-item";
        stepMedia.className = "step-item";

        const t1 = setTimeout(() => {
            stepContent.className = "step-item active";
        }, 500);

        const t2 = setTimeout(() => {
            stepMedia.className = "step-item active";
        }, 1100);

        try {
            const response = await fetch("/api/analyze", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ url: url })
            });

            clearTimeout(t1);
            clearTimeout(t2);

            const data = await response.json();

            if (!response.ok || !data.success) {
                const message = (data.error && data.error.message) || "Unable to access or process this URL.";
                const code = (data.error && data.error.code) || "EXTRACTION_FAILED";
                this.showError(message, code);
                return;
            }

            this.analysisResult = data;
            this.showResult(data);
        } catch (err) {
            clearTimeout(t1);
            clearTimeout(t2);
            this.showError("Network or server connection failed. Please try again.", "NETWORK_ERROR");
        }
    },

    showLoading() {
        this.hideAllSections();
        document.getElementById("loading-card").style.display = "block";
    },

    showResult(data) {
        this.hideAllSections();
        const resultCard = document.getElementById("result-card");
        resultCard.style.display = "block";

        // Badges & Header
        document.getElementById("res-platform").textContent = data.platform || "Web";
        
        let readableType = (data.content_type || "media").replace(/_/g, " ");
        document.getElementById("res-type").textContent = readableType;

        const titleEl = document.getElementById("res-title");
        const summaryEl = document.getElementById("res-summary");

        const count = data.media_count || 1;
        const isCollection = count > 1;

        if (isCollection) {
            titleEl.textContent = `${data.platform || "Platform"} Collection (${count} Pages)`;
            summaryEl.textContent = `All ${count} pages / items detected. Choose your desired output format below.`;
        } else {
            titleEl.textContent = `${data.platform || "Platform"} ${readableType.toUpperCase()}`;
            summaryEl.textContent = "1 item detected and ready to package.";
        }

        // Preview container
        const previewContainer = document.getElementById("preview-container");
        previewContainer.innerHTML = "";

        if (Array.isArray(data.previews) && data.previews.length > 0) {
            if (data.previews.length === 1) {
                const previewBox = document.createElement("div");
                previewBox.className = "single-preview-box";
                const img = document.createElement("img");
                img.src = data.previews[0];
                img.alt = "Media preview";
                img.loading = "lazy";
                previewBox.appendChild(img);
                previewContainer.appendChild(previewBox);
            } else {
                // Header Bar with count & toggle
                const headerBar = document.createElement("div");
                headerBar.className = "preview-header-bar";
                
                const countPill = document.createElement("span");
                countPill.className = "preview-count-pill";
                countPill.textContent = `${data.previews.length} Pages / Slides Available`;
                headerBar.appendChild(countPill);

                let showingAll = data.previews.length <= 12;
                let toggleBtn = null;

                if (data.previews.length > 12) {
                    toggleBtn = document.createElement("button");
                    toggleBtn.type = "button";
                    toggleBtn.className = "preview-toggle-btn";
                    toggleBtn.textContent = `Show all ${data.previews.length} pages`;
                    headerBar.appendChild(toggleBtn);
                }

                previewContainer.appendChild(headerBar);

                const previewGrid = document.createElement("div");
                previewGrid.className = "preview-grid";

                const renderThumbnails = (limit) => {
                    previewGrid.innerHTML = "";
                    const itemsToRender = limit ? data.previews.slice(0, limit) : data.previews;
                    itemsToRender.forEach((previewUrl, idx) => {
                        const item = document.createElement("div");
                        item.className = "preview-grid-item";

                        const img = document.createElement("img");
                        img.src = previewUrl;
                        img.alt = `Page ${idx + 1}`;
                        img.loading = "lazy";

                        const badge = document.createElement("span");
                        badge.className = "page-badge";
                        badge.textContent = `Page ${idx + 1}`;

                        item.appendChild(img);
                        item.appendChild(badge);
                        previewGrid.appendChild(item);
                    });
                };

                renderThumbnails(showingAll ? null : 12);
                previewContainer.appendChild(previewGrid);

                if (toggleBtn) {
                    toggleBtn.addEventListener("click", () => {
                        showingAll = !showingAll;
                        if (showingAll) {
                            renderThumbnails(null);
                            toggleBtn.textContent = "Show fewer";
                        } else {
                            renderThumbnails(12);
                            toggleBtn.textContent = `Show all ${data.previews.length} pages`;
                        }
                    });
                }
            }
        }

        // Custom Filename Setup
        const filenameInput = document.getElementById("custom-filename-input");
        const clearFilenameBtn = document.getElementById("btn-clear-filename");
        if (filenameInput) {
            filenameInput.value = "";
            filenameInput.placeholder = data.title || "Enter custom file name (optional)";
            filenameInput.oninput = () => {
                if (clearFilenameBtn) {
                    clearFilenameBtn.style.display = filenameInput.value.length > 0 ? "inline-block" : "none";
                }
            };
            if (clearFilenameBtn) {
                clearFilenameBtn.onclick = () => {
                    filenameInput.value = "";
                    clearFilenameBtn.style.display = "none";
                    filenameInput.focus();
                };
            }
        }

        // Caption Selection Setup
        const captionPill = document.getElementById("caption-detected-pill");
        const captionSnippet = document.getElementById("caption-preview-snippet");
        const btnCaptionWithout = document.getElementById("btn-caption-without");
        const btnCaptionWith = document.getElementById("btn-caption-with");

        this.includeCaption = false;
        if (btnCaptionWithout && btnCaptionWith) {
            btnCaptionWithout.className = "caption-choice-btn active";
            btnCaptionWith.className = "caption-choice-btn";

            btnCaptionWithout.onclick = () => {
                this.includeCaption = false;
                btnCaptionWithout.className = "caption-choice-btn active";
                btnCaptionWith.className = "caption-choice-btn";
            };
            btnCaptionWith.onclick = () => {
                this.includeCaption = true;
                btnCaptionWith.className = "caption-choice-btn active";
                btnCaptionWithout.className = "caption-choice-btn";
            };
        }

        if (data.description && data.description.trim()) {
            if (captionPill) captionPill.style.display = "inline-block";
            if (captionSnippet) {
                captionSnippet.style.display = "block";
                captionSnippet.textContent = data.description.trim();
            }
        } else {
            if (captionPill) captionPill.style.display = "none";
            if (captionSnippet) captionSnippet.style.display = "none";
        }

        // Video options toggle
        const videoOptionsGroup = document.getElementById("video-options-group");
        const hasVideo = data.content_type === "video" || 
                         (Array.isArray(data.formats) && (data.formats.includes("mp4") || data.formats.includes("mkv") || data.formats.includes("webm") || data.formats.includes("video")));
        videoOptionsGroup.style.display = hasVideo ? "block" : "none";

        // Available Formats
        const formatActions = document.getElementById("format-actions");
        formatActions.innerHTML = "";

        const formatLabels = {
            "original": "Original File",
            "images": "All Images (ZIP)",
            "zip": isCollection ? `Download ZIP (${count} Files)` : "Download as ZIP",
            "pdf": isCollection ? `Convert to PDF (${count} Pages)` : "Convert to PDF",
            "docx": isCollection ? `Word Document (${count} Pages)` : "Word Document (.docx)",
            "doc": "Word Document (.docx)",
            "mp4": "Download MP4",
            "mkv": "Download MKV",
            "webm": "Download WebM",
            "video": "Download Video",
            "audio": "Download Audio (MP3)",
            "mp3": "Download MP3 Audio",
            "m4a": "Download M4A Audio",
            "images_zip": `Images as ZIP (${count} Files)`,
            "images_pdf": `Images as PDF (${count} Pages)`,
            "all_zip": `Download Everything (${count} Files)`
        };

        const formats = Array.isArray(data.formats) && data.formats.length > 0
            ? data.formats
            : ["original"];

        formats.forEach(formatKey => {
            const btn = document.createElement("button");
            btn.type = "button";
            btn.className = "format-btn";
            btn.dataset.format = formatKey;

            let icon = "📦";
            if (formatKey.includes("pdf")) icon = "📄";
            else if (formatKey.includes("doc")) icon = "📝";
            else if (formatKey.includes("zip")) icon = "🗂️";
            else if (formatKey === "mp4") icon = "🎬";
            else if (formatKey === "mkv") icon = "🎞️";
            else if (formatKey === "webm") icon = "🌐";
            else if (formatKey.includes("video")) icon = "🎬";
            else if (formatKey.includes("audio") || formatKey === "mp3") icon = "🎵";
            else if (formatKey === "m4a") icon = "🎧";
            else if (formatKey.includes("image")) icon = "🖼️";

            btn.innerHTML = `<span>${icon}</span> <span>${formatLabels[formatKey] || formatKey.toUpperCase()}</span>`;

            btn.addEventListener("click", () => this.handleFormatSelection(formatKey));
            formatActions.appendChild(btn);
        });
    },

    async handleFormatSelection(formatKey) {
        const qualitySelect = document.getElementById("quality-select");
        const quality = qualitySelect ? qualitySelect.value : "best";

        const filenameInput = document.getElementById("custom-filename-input");
        const customFilename = filenameInput ? filenameInput.value.trim() : "";
        const includeCaption = Boolean(this.includeCaption);

        // Switch to generating/loading state
        this.hideAllSections();
        const loadingCard = document.getElementById("loading-card");
        loadingCard.querySelector(".status-title").textContent = "Preparing your package...";
        document.getElementById("step-platform").className = "step-item active";
        document.getElementById("step-platform").innerHTML = `<span class="step-dot"></span> Fetching media`;
        document.getElementById("step-content").className = "step-item active";
        document.getElementById("step-content").innerHTML = `<span class="step-dot"></span> Packaging into ${formatKey.toUpperCase()}`;
        document.getElementById("step-media").className = "step-item";
        document.getElementById("step-media").innerHTML = `<span class="step-dot"></span> Finalizing download`;
        loadingCard.style.display = "block";

        try {
            const result = await Downloader.requestGeneration(
                this.currentUrl,
                formatKey,
                quality,
                customFilename,
                includeCaption
            );
            this.showSuccess(result);
        } catch (err) {
            this.showError(err.message || "File generation failed.", "GENERATION_ERROR");
        }
    },

    showSuccess(data) {
        this.hideAllSections();
        const successCard = document.getElementById("success-card");
        document.getElementById("success-filename").textContent = data.filename || "download_file";
        
        let sizeText = data.size_formatted || (data.filesize ? `${(data.filesize / (1024 * 1024)).toFixed(2)} MB` : "File ready");
        document.getElementById("success-filesize").textContent = sizeText;

        const directBtn = document.getElementById("direct-download-btn");
        directBtn.href = `/download/${encodeURIComponent(data.file_id)}`;

        successCard.style.display = "block";
    },

    showError(message, code) {
        this.hideAllSections();
        const errorCard = document.getElementById("error-card");
        document.getElementById("error-message").textContent = message;
        errorCard.style.display = "block";
    },

    hideAllSections() {
        document.getElementById("loading-card").style.display = "none";
        document.getElementById("result-card").style.display = "none";
        document.getElementById("success-card").style.display = "none";
        document.getElementById("error-card").style.display = "none";
    },

    resetToHome() {
        this.hideAllSections();
        const urlInput = document.getElementById("url-input");
        urlInput.value = "";
        document.getElementById("clear-btn").style.display = "none";
        urlInput.focus();
    }
};

window.Analyzer = Analyzer;
