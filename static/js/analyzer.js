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

            const contentType = response.headers.get("content-type") || "";
            if (!contentType.includes("application/json")) {
                const text = await response.text();
                this.showError(text || `Server returned error (${response.status})`, "SERVER_ERROR");
                return;
            }

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

        const formatConfig = {
            "mp4": { label: "Standard Video", ext: ".mp4", icon: "🎬" },
            "mkv": { label: "Matroska Video", ext: ".mkv", icon: "🎞️" },
            "webm": { label: "WebM Video", ext: ".webm", icon: "🌐" },
            "video": { label: "Video", ext: ".mp4", icon: "🎬" },
            "audio": { label: "Audio Track", ext: ".mp3", icon: "🎵" },
            "mp3": { label: "MP3 Audio", ext: ".mp3", icon: "🎵" },
            "m4a": { label: "AAC Audio", ext: ".m4a", icon: "🎧" },
            "pdf": { label: isCollection ? `Convert to PDF (${count} Pages)` : "PDF Document", ext: ".pdf", icon: "📄" },
            "images_pdf": { label: `Images as PDF (${count} Pages)`, ext: ".pdf", icon: "📄" },
            "docx": { label: isCollection ? `Word Doc (${count} Pages)` : "Word Document", ext: ".docx", icon: "📝" },
            "doc": { label: "Word Document", ext: ".docx", icon: "📝" },
            "zip": { label: isCollection ? `ZIP Archive (${count} Files)` : "Download as ZIP", ext: ".zip", icon: "🗂️" },
            "images_zip": { label: `Images as ZIP (${count} Files)`, ext: ".zip", icon: "🗂️" },
            "images": { label: `All Images (${count} Files)`, ext: ".zip", icon: "🗂️" },
            "all_zip": { label: `Complete ZIP (${count} Files)`, ext: ".zip", icon: "🗂️" }
        };

        const formats = Array.isArray(data.formats) && data.formats.length > 0
            ? data.formats
            : ["original"];

        formats.forEach(formatKey => {
            const btn = document.createElement("button");
            btn.type = "button";
            btn.className = "format-btn";
            btn.dataset.format = formatKey;

            const cfg = formatConfig[formatKey] || {};
            let icon = cfg.icon || "📦";
            let label = cfg.label;
            let ext = cfg.ext;

            if (!ext) {
                if (formatKey.includes("pdf")) { ext = ".pdf"; icon = "📄"; }
                else if (formatKey.includes("doc")) { ext = ".docx"; icon = "📝"; }
                else if (formatKey.includes("zip")) { ext = ".zip"; icon = "🗂️"; }
                else if (formatKey.includes("mp4")) { ext = ".mp4"; icon = "🎬"; }
                else if (formatKey.includes("mkv")) { ext = ".mkv"; icon = "🎞️"; }
                else if (formatKey.includes("webm")) { ext = ".webm"; icon = "🌐"; }
                else if (formatKey.includes("audio") || formatKey === "mp3") { ext = ".mp3"; icon = "🎵"; }
                else if (formatKey === "m4a") { ext = ".m4a"; icon = "🎧"; }
                else {
                    let itemExt = "";
                    if (data.items && data.items[0] && data.items[0].filename) {
                        const parts = data.items[0].filename.split(".");
                        if (parts.length > 1) itemExt = parts.pop().toLowerCase();
                    }
                    ext = itemExt ? `.${itemExt}` : `.${formatKey.toLowerCase()}`;
                }
            }

            if (!label) {
                label = formatKey === "original" ? "Original File" : formatKey.replace(/_/g, " ").replace(/\b\w/g, l => l.toUpperCase());
            }

            btn.innerHTML = `
                <span class="format-btn-left">
                    <span class="format-btn-icon">${icon}</span>
                    <span class="format-btn-label">${label}</span>
                </span>
                <span class="format-btn-ext">${ext}</span>
            `;

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
        const downloadUrl = `/download/${encodeURIComponent(data.file_id)}`;
        directBtn.href = downloadUrl;
        directBtn.setAttribute("download", data.filename || "download_file");

        successCard.style.display = "block";

        // Auto trigger download prompt so user gets the file immediately
        try {
            const dlLink = document.createElement("a");
            dlLink.href = downloadUrl;
            dlLink.download = data.filename || "download_file";
            document.body.appendChild(dlLink);
            dlLink.click();
            document.body.removeChild(dlLink);
        } catch (e) {
            console.warn("Auto-download trigger skipped:", e);
        }
    },

    showError(message, code) {
        this.hideAllSections();
        const errorCard = document.getElementById("error-card");
        const errorTitle = document.getElementById("error-title");
        const errorBadge = errorCard.querySelector(".error-icon-badge");

        if (code === "COMING_SOON") {
            if (errorTitle) errorTitle.textContent = "YouTube Downloader — Coming Soon!";
            if (errorBadge) {
                errorBadge.textContent = "🚀";
                errorBadge.style.backgroundColor = "rgba(37, 99, 235, 0.15)";
                errorBadge.style.color = "var(--brand-primary)";
            }
        } else {
            if (errorTitle) errorTitle.textContent = "Unable to access this content";
            if (errorBadge) {
                errorBadge.textContent = "⚠️";
                errorBadge.style.backgroundColor = "var(--accent-rose-light)";
                errorBadge.style.color = "var(--accent-rose)";
            }
        }

        document.getElementById("error-message").textContent = message;

        const fallbackContainer = document.getElementById("error-fallback-container");
        const errorReasons = document.getElementById("error-reasons");

        const targetUrl = this.currentUrl || (document.getElementById("url-input") ? document.getElementById("url-input").value.trim() : "");
        const ytMatch = targetUrl.match(/(?:youtu\.be\/|youtube\.com\/(?:watch\?.*v=|embed\/|shorts\/))([a-zA-Z0-9_-]{11})/i);

        if (fallbackContainer) {
            if (ytMatch && ytMatch[1]) {
                const vid = ytMatch[1];
                const mirror10dl = document.getElementById("btn-mirror-10dl");
                const mirrorY2 = document.getElementById("btn-mirror-y2mate");
                const mirrorCobalt = document.getElementById("btn-mirror-cobalt");
                const mirrorLocal = document.getElementById("btn-mirror-local");

                if (mirror10dl) mirror10dl.href = `https://10downloader.com/download?v=https://youtu.be/${vid}`;
                if (mirrorY2) mirrorY2.href = `https://www.y2mate.com/youtube/${vid}`;
                if (mirrorCobalt) mirrorCobalt.href = `https://cobalt.tools`;

                if (mirrorLocal) {
                    mirrorLocal.onclick = async () => {
                        mirrorLocal.disabled = true;
                        mirrorLocal.innerHTML = `<span>⏳</span> Connecting to localhost:5000...`;
                        try {
                            const res = await fetch("http://127.0.0.1:5000/api/analyze", {
                                method: "POST",
                                headers: { "Content-Type": "application/json" },
                                body: JSON.stringify({ url: targetUrl })
                            });
                            const data = await res.json();
                            if (res.ok && data.success) {
                                window.open(`http://127.0.0.1:5000/?url=${encodeURIComponent(targetUrl)}`, "_blank");
                            } else {
                                alert("Local server is reachable but reported: " + ((data.error && data.error.message) || "Unknown issue"));
                            }
                        } catch (e) {
                            alert("Local server on port 5000 is not running. To use the local engine, run 'python app.py' in your terminal!");
                        } finally {
                            mirrorLocal.disabled = false;
                            mirrorLocal.innerHTML = `<span>💻</span> Local App (Port 5000)`;
                        }
                    };
                }

                fallbackContainer.style.display = "block";
                if (errorReasons) errorReasons.style.display = "none";
            } else {
                fallbackContainer.style.display = "none";
                if (errorReasons) errorReasons.style.display = "block";
            }
        }

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
