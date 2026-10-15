/**
 * LinkForge - Advanced Link Downloader Controller
 * Handles URL analysis, multi-item carousels, segregated media sections (Images, Videos, Music),
 * selective bulk actions (ZIP, PDF, DOCX), individual downloads, and email delivery.
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
                    console.warn("Clipboard access denied", e);
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

        // Global start generation / download button
        if (btnStartDownload) {
            btnStartDownload.addEventListener("click", () => {
                // If there are multiple images, gather selected image indices
                const selected = this.getSelectedImageIndices();
                this.startDownload({
                    format: this.selectedFormat,
                    selected_indices: selected.length > 0 ? selected : null
                });
            });
        }

        // Reset buttons
        if (btnResetOptions) btnResetOptions.addEventListener("click", () => this.showView("input-view"));
        if (btnResetSuccess) btnResetSuccess.addEventListener("click", () => this.resetToHome());
        if (btnResetError) btnResetError.addEventListener("click", () => this.showView("input-view"));

        // Email delivery widget
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
                this.showError(`Service connection error (Status ${response.status}). Please verify the link or try again.`);
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

    getSelectedImageIndices() {
        const checkboxes = document.querySelectorAll(".img-select-check:checked");
        return Array.from(checkboxes).map(cb => parseInt(cb.getAttribute("data-index"), 10)).filter(n => !isNaN(n));
    },

    renderOptions(data) {
        // Badges & Meta
        const platformBadge = document.getElementById("res-platform");
        const typeBadge = document.getElementById("res-type");
        const titleEl = document.getElementById("res-title");
        const summaryEl = document.getElementById("res-summary");

        if (platformBadge) platformBadge.textContent = data.platform || "Direct Web";
        if (typeBadge) typeBadge.textContent = (data.content_type || "Media").replace(/_/g, " ");

        // Partition items into images, videos, audios, and documents/files
        const items = data.items || [];
        const images = items.map((it, idx) => ({ ...it, origIndex: idx })).filter(it => it.media_type === "image");
        const videos = items.map((it, idx) => ({ ...it, origIndex: idx })).filter(it => it.media_type === "video");
        const audios = items.map((it, idx) => ({ ...it, origIndex: idx })).filter(it => it.media_type === "audio");
        const otherFiles = items.map((it, idx) => ({ ...it, origIndex: idx })).filter(it => it.media_type !== "image" && it.media_type !== "video" && it.media_type !== "audio");

        if (titleEl) {
            titleEl.textContent = data.title || `${data.platform || "Media"} Download`;
        }

        if (summaryEl) {
            const parts = [];
            if (images.length > 0) parts.push(`${images.length} Image${images.length > 1 ? "s" : ""}`);
            if (videos.length > 0) parts.push(`${videos.length} Video${videos.length > 1 ? "s" : ""}`);
            if (audios.length > 0) parts.push(`${audios.length} Audio Track`);
            if (otherFiles.length > 0) parts.push(`${otherFiles.length} File${otherFiles.length > 1 ? "s" : ""}`);
            summaryEl.textContent = parts.length > 0 ? parts.join(" • ") + " detected." : "Ready to package and download.";
        }

        // Segregated Media Container
        const previewContainer = document.getElementById("preview-container");
        if (previewContainer) {
            previewContainer.innerHTML = "";

            // 1. IMAGES SECTION
            if (images.length > 0) {
                const imgSection = document.createElement("div");
                imgSection.className = "media-seg-section";
                imgSection.innerHTML = `
                    <div class="media-seg-header">
                        <div class="media-seg-title">
                            <span>&#x1F5BC;&#xFE0F;</span> Images (${images.length})
                        </div>
                        <div class="media-seg-controls">
                            <label class="select-all-label">
                                <input type="checkbox" id="select-all-images" checked>
                                <span>Select All</span>
                            </label>
                            <span class="selection-pill" id="images-selected-pill">${images.length} of ${images.length} selected</span>
                        </div>
                    </div>

                    ${images.length > 1 ? `
                    <div class="batch-action-bar">
                        <button type="button" class="batch-btn batch-zip" id="btn-batch-zip">
                            &#x1F4E6; Download Selected (ZIP)
                        </button>
                        <button type="button" class="batch-btn batch-pdf" id="btn-batch-pdf">
                            &#x1F4C4; Convert Selected to PDF
                        </button>
                        <button type="button" class="batch-btn batch-docx" id="btn-batch-docx">
                            &#x1F4DD; Convert Selected to DOCX
                        </button>
                    </div>
                    ` : ''}

                    <div class="images-collection-grid" id="images-collection-grid"></div>
                `;

                previewContainer.appendChild(imgSection);

                // Render image cards
                const grid = imgSection.querySelector("#images-collection-grid");
                images.forEach((img, i) => {
                    const card = document.createElement("div");
                    card.className = "image-item-card selected";
                    card.setAttribute("data-index", img.origIndex);
                    const thumbUrl = img.thumbnail_url || img.url;

                    card.innerHTML = `
                        <div class="image-card-top">
                            <label class="image-checkbox-wrapper" onclick="event.stopPropagation();">
                                <input type="checkbox" class="img-select-check" data-index="${img.origIndex}" checked>
                                <span class="checkbox-custom"></span>
                            </label>
                            <span class="image-index-badge">#${i + 1}</span>
                        </div>
                        <div class="image-thumb-wrapper" title="Click to view full image">
                            <img src="${thumbUrl}" alt="Photo ${i + 1}" loading="lazy">
                            <div class="image-zoom-overlay"><span>&#x1F50D; Preview</span></div>
                        </div>
                        <div class="image-card-actions">
                            <button type="button" class="btn-single-image-dl" data-index="${img.origIndex}" title="Download this single image">
                                &#x2193; Download
                            </button>
                        </div>
                    `;

                    // Click checkbox toggles selection
                    const cb = card.querySelector(".img-select-check");
                    cb.addEventListener("change", () => {
                        card.classList.toggle("selected", cb.checked);
                        this.updateImagesSelectedCounter(images.length);
                    });

                    // Click thumbnail opens image in full modal/lightbox
                    const thumb = card.querySelector(".image-thumb-wrapper");
                    thumb.addEventListener("click", () => {
                        this.openImageLightbox(img.url || thumbUrl, `Image #${i + 1}`);
                    });

                    // Single image download button
                    const dlBtn = card.querySelector(".btn-single-image-dl");
                    dlBtn.addEventListener("click", (e) => {
                        e.stopPropagation();
                        this.startDownload({
                            format: "original",
                            selected_indices: [img.origIndex],
                            custom_filename: `image_${i + 1}`
                        });
                    });

                    grid.appendChild(card);
                });

                // Bind Select All
                const selectAll = imgSection.querySelector("#select-all-images");
                if (selectAll) {
                    selectAll.addEventListener("change", () => {
                        const allChecks = imgSection.querySelectorAll(".img-select-check");
                        allChecks.forEach(c => {
                            c.checked = selectAll.checked;
                            c.closest(".image-item-card")?.classList.toggle("selected", selectAll.checked);
                        });
                        this.updateImagesSelectedCounter(images.length);
                    });
                }

                // Bind batch action buttons
                const btnBatchZip = imgSection.querySelector("#btn-batch-zip");
                const btnBatchPdf = imgSection.querySelector("#btn-batch-pdf");
                const btnBatchDocx = imgSection.querySelector("#btn-batch-docx");

                if (btnBatchZip) {
                    btnBatchZip.addEventListener("click", () => {
                        const selected = this.getSelectedImageIndices();
                        if (selected.length === 0) {
                            alert("Please select at least 1 image to download.");
                            return;
                        }
                        this.startDownload({ format: "zip", selected_indices: selected });
                    });
                }

                if (btnBatchPdf) {
                    btnBatchPdf.addEventListener("click", () => {
                        const selected = this.getSelectedImageIndices();
                        if (selected.length === 0) {
                            alert("Please select at least 1 image to convert to PDF.");
                            return;
                        }
                        this.startDownload({ format: "pdf", selected_indices: selected });
                    });
                }

                if (btnBatchDocx) {
                    btnBatchDocx.addEventListener("click", () => {
                        const selected = this.getSelectedImageIndices();
                        if (selected.length === 0) {
                            alert("Please select at least 1 image to convert to Word.");
                            return;
                        }
                        this.startDownload({ format: "docx", selected_indices: selected });
                    });
                }
            }

            // 2. VIDEOS SECTION
            if (videos.length > 0) {
                const vidSection = document.createElement("div");
                vidSection.className = "media-seg-section";
                vidSection.innerHTML = `
                    <div class="media-seg-header">
                        <div class="media-seg-title">
                            <span>&#x1F3AC;</span> Videos (${videos.length})
                        </div>
                    </div>
                    <div class="videos-collection-grid" id="videos-collection-grid"></div>
                `;

                previewContainer.appendChild(vidSection);
                const vidGrid = vidSection.querySelector("#videos-collection-grid");

                videos.forEach((vid, i) => {
                    const card = document.createElement("div");
                    card.className = "video-item-card";
                    card.innerHTML = `
                        <div class="video-preview-wrapper">
                            ${vid.url ? `<video controls preload="metadata" poster="${vid.thumbnail_url || ''}" src="${vid.url}"></video>` : `
                                <img src="${vid.thumbnail_url || ''}" alt="Video thumbnail">
                                <div class="video-play-badge">&#x25B6;</div>
                            `}
                        </div>
                        <div class="video-item-info">
                            <div class="video-item-title">${vid.title || `Video #${i + 1}`}</div>
                            <div class="video-actions-row">
                                <button type="button" class="btn-video-action btn-mp4" data-index="${vid.origIndex}">
                                    &#x2193; Download MP4 Video
                                </button>
                                <button type="button" class="btn-video-action btn-mkv" data-index="${vid.origIndex}">
                                    &#x2193; Download MKV (Lossless)
                                </button>
                            </div>
                        </div>
                    `;

                    const mp4Btn = card.querySelector(".btn-mp4");
                    const mkvBtn = card.querySelector(".btn-mkv");

                    if (mp4Btn) {
                        mp4Btn.addEventListener("click", () => {
                            this.startDownload({
                                format: "mp4",
                                selected_indices: [vid.origIndex],
                                custom_filename: `video_${i + 1}`
                            });
                        });
                    }

                    if (mkvBtn) {
                        mkvBtn.addEventListener("click", () => {
                            this.startDownload({
                                format: "mkv",
                                selected_indices: [vid.origIndex],
                                custom_filename: `video_${i + 1}`
                            });
                        });
                    }

                    vidGrid.appendChild(card);
                });
            }

            // 3. MUSIC & BACKGROUND AUDIO SECTION
            if (audios.length > 0) {
                const audSection = document.createElement("div");
                audSection.className = "media-seg-section";
                audSection.innerHTML = `
                    <div class="media-seg-header">
                        <div class="media-seg-title">
                            <span>&#x1F3B5;</span> Music &amp; Audio Track (${audios.length})
                        </div>
                    </div>
                    <div class="audios-collection-grid" id="audios-collection-grid"></div>
                `;

                previewContainer.appendChild(audSection);
                const audGrid = audSection.querySelector("#audios-collection-grid");

                audios.forEach((aud, i) => {
                    const card = document.createElement("div");
                    card.className = "audio-item-card";
                    card.innerHTML = `
                        <div class="audio-card-icon-box">&#x1F3B5;</div>
                        <div class="audio-card-details">
                            <div class="audio-track-title">${aud.title || "Background Audio Track"}</div>
                            <div class="audio-player-wrapper">
                                <audio controls preload="none" src="${aud.url}"></audio>
                            </div>
                        </div>
                        <div class="audio-card-actions">
                            <button type="button" class="btn-audio-action btn-mp3" data-index="${aud.origIndex}">
                                &#x2193; Download MP3
                            </button>
                            <button type="button" class="btn-audio-action btn-m4a" data-index="${aud.origIndex}">
                                &#x2193; Download M4A
                            </button>
                        </div>
                    `;

                    const mp3Btn = card.querySelector(".btn-mp3");
                    const m4aBtn = card.querySelector(".btn-m4a");

                    if (mp3Btn) {
                        mp3Btn.addEventListener("click", () => {
                            this.startDownload({
                                format: "audio",
                                selected_indices: [aud.origIndex],
                                custom_filename: `${aud.title || 'audio_track'}`
                            });
                        });
                    }

                    if (m4aBtn) {
                        m4aBtn.addEventListener("click", () => {
                            this.startDownload({
                                format: "m4a",
                                selected_indices: [aud.origIndex],
                                custom_filename: `${aud.title || 'audio_track'}`
                            });
                        });
                    }

                    audGrid.appendChild(card);
                });
            }

            // 4. DOCUMENTS & GENERAL FILES SECTION
            if (otherFiles.length > 0) {
                const docSection = document.createElement("div");
                docSection.className = "media-seg-section";
                docSection.innerHTML = `
                    <div class="media-seg-header">
                        <div class="media-seg-title">
                            <span>&#x1F4C4;</span> Files &amp; Documents (${otherFiles.length})
                        </div>
                    </div>
                    <div class="audios-collection-grid" id="other-files-collection-grid"></div>
                `;

                previewContainer.appendChild(docSection);
                const fileGrid = docSection.querySelector("#other-files-collection-grid");

                otherFiles.forEach((fileItem, i) => {
                    const card = document.createElement("div");
                    card.className = "audio-item-card";
                    const fsizeStr = fileItem.filesize ? `${(fileItem.filesize / (1024 * 1024)).toFixed(2)} MB` : "Ready";
                    card.innerHTML = `
                        <div class="audio-card-icon-box">&#x1F4C4;</div>
                        <div class="audio-card-details">
                            <div class="audio-track-title">${fileItem.filename || fileItem.title || `File #${i + 1}`}</div>
                            <div class="video-item-sub">${fsizeStr} • ${(fileItem.mime_type || "Downloadable File")}</div>
                        </div>
                        <div class="audio-card-actions">
                            <button type="button" class="btn-audio-action btn-file-dl" data-index="${fileItem.origIndex}">
                                &#x2193; Download File
                            </button>
                        </div>
                    `;

                    const dlBtn = card.querySelector(".btn-file-dl");
                    if (dlBtn) {
                        dlBtn.addEventListener("click", () => {
                            this.startDownload({
                                format: "original",
                                selected_indices: [fileItem.origIndex],
                                custom_filename: fileItem.filename || `file_${i + 1}`
                            });
                        });
                    }

                    fileGrid.appendChild(card);
                });
            }

            // 5. Fallback card when no individual media items exist
            if (images.length === 0 && videos.length === 0 && audios.length === 0 && otherFiles.length === 0) {
                const genericCard = document.createElement("div");
                genericCard.className = "media-seg-section";
                genericCard.innerHTML = `
                    <div class="media-seg-header">
                        <div class="media-seg-title">
                            <span>&#x1F5BC;&#xFE0F;</span> Detected Media Package
                        </div>
                    </div>
                    <div style="padding: 16px 20px; background: rgba(255,255,255,0.85); border: 1px solid var(--border-light); border-radius: 12px; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 12px;">
                        <div>
                            <div style="font-weight: 700; color: var(--text-heading); font-size: 15px;">${data.title || "Ready to Package"}</div>
                            <div style="font-size: 13px; color: var(--text-muted); margin-top: 4px;">Select your preferred output format below and click Download.</div>
                        </div>
                    </div>
                `;
                previewContainer.appendChild(genericCard);
            }
        }

        // Format Selection Cards Grid
        const formatGrid = document.getElementById("format-cards-grid");
        if (formatGrid) {
            formatGrid.innerHTML = "";

            const FORMAT_META = {
                zip: { format: "zip", label: "ZIP Archive", badge: "ZIP", desc: "All original media packaged in a ZIP archive" },
                images_zip: { format: "zip", label: "Images ZIP", badge: "ZIP", desc: "Selected high-resolution images in a ZIP" },
                images: { format: "zip", label: "Images ZIP", badge: "ZIP", desc: "All extracted images in a ZIP" },
                all_zip: { format: "zip", label: "Complete ZIP", badge: "ZIP", desc: "Complete bundle of all media items extracted" },
                pdf: { format: "pdf", label: "PDF Document", badge: "PDF", desc: "Convert images/slides into a clean PDF document" },
                images_pdf: { format: "pdf", label: "PDF Document", badge: "PDF", desc: "Combine extracted images into a single PDF" },
                docx: { format: "docx", label: "Word Document", badge: "DOCX", desc: "Editable Microsoft Word document with images" },
                doc: { format: "docx", label: "Word Document", badge: "DOCX", desc: "Editable Microsoft Word document" },
                mp4: { format: "mp4", label: "MP4 Video", badge: "MP4", desc: "Universal video compatible with all devices" },
                video: { format: "mp4", label: "MP4 Video", badge: "MP4", desc: "Direct video stream packaged in MP4 container" },
                mkv: { format: "mkv", label: "MKV Video", badge: "MKV", desc: "Lossless Matroska container" },
                webm: { format: "webm", label: "WebM Video", badge: "WEBM", desc: "Web-optimized lightweight video" },
                audio: { format: "audio", label: "MP3 Audio", badge: "MP3", desc: "High-bitrate audio track (192 kbps)" },
                mp3: { format: "audio", label: "MP3 Audio", badge: "MP3", desc: "Standard high-fidelity MP3 stream" },
                m4a: { format: "m4a", label: "M4A Audio", badge: "AAC", desc: "Apple AAC high-clarity audio stream" },
                original: { format: "original", label: "Original Media", badge: "RAW", desc: "Direct source files in original resolution" }
            };

            const rawFormats = (data.formats && Array.isArray(data.formats) && data.formats.length > 0)
                ? data.formats
                : (data.available_formats || ["zip", "original"]);

            const seenKeys = new Set();
            const formatItems = [];

            rawFormats.forEach(f => {
                const key = typeof f === "string" ? f.toLowerCase().trim() : (f.format || "").toLowerCase().trim();
                const meta = FORMAT_META[key] || {
                    format: key || "original",
                    label: (key || "MEDIA").toUpperCase() + " File",
                    badge: (key || "FILE").toUpperCase(),
                    desc: `Download packaged as .${key}`
                };
                if (!seenKeys.has(meta.format)) {
                    seenKeys.add(meta.format);
                    formatItems.push(meta);
                }
            });

            if (formatItems.length === 0) {
                formatItems.push(FORMAT_META.zip);
            }

            this.selectedFormat = formatItems[0].format;

            formatItems.forEach((f, idx) => {
                const card = document.createElement("div");
                card.className = `format-card ${idx === 0 ? "active" : ""}`;
                card.setAttribute("data-format", f.format);
                card.innerHTML = `
                    <div class="format-card-header">
                        <span class="format-badge">${f.badge}</span>
                        <span class="format-title">${f.label}</span>
                    </div>
                    <p class="format-desc">${f.desc}</p>
                `;

                card.addEventListener("click", () => {
                    document.querySelectorAll(".format-card").forEach(c => c.classList.remove("active"));
                    card.classList.add("active");
                    this.selectedFormat = f.format;
                    const btn = document.getElementById("btn-start-download");
                    if (btn) btn.innerHTML = `&#x2193; Download as ${f.label}`;
                });

                formatGrid.appendChild(card);
            });

            const btn = document.getElementById("btn-start-download");
            if (btn) btn.innerHTML = `&#x2193; Download as ${formatItems[0].label}`;
        }

        // Custom Filename Input
        const customFilenameInput = document.getElementById("custom-filename-input");
        if (customFilenameInput) {
            customFilenameInput.value = "";
            customFilenameInput.placeholder = data.title || "custom_filename (optional)";
        }

        this.showView("options-view");
    },

    updateImagesSelectedCounter(total) {
        const selected = this.getSelectedImageIndices();
        const pill = document.getElementById("images-selected-pill");
        if (pill) {
            pill.textContent = `${selected.length} of ${total} selected`;
        }
        const selectAll = document.getElementById("select-all-images");
        if (selectAll) {
            selectAll.checked = selected.length === total;
            selectAll.indeterminate = selected.length > 0 && selected.length < total;
        }
    },

    openImageLightbox(imageUrl, title) {
        let modal = document.getElementById("image-lightbox-modal");
        if (!modal) {
            modal = document.createElement("div");
            modal.id = "image-lightbox-modal";
            modal.className = "modal-backdrop image-lightbox-backdrop";
            modal.innerHTML = `
                <div class="image-lightbox-dialog">
                    <button type="button" class="lightbox-close-btn">&times;</button>
                    <img id="lightbox-full-img" src="" alt="Full preview">
                    <div class="lightbox-footer">
                        <span id="lightbox-title">${title || "Image Preview"}</span>
                        <a href="#" id="lightbox-direct-link" target="_blank" class="lightbox-open-new">Open Original &#x2197;</a>
                    </div>
                </div>
            `;
            document.body.appendChild(modal);

            modal.querySelector(".lightbox-close-btn").addEventListener("click", () => {
                modal.classList.remove("show");
            });

            modal.addEventListener("click", (e) => {
                if (e.target === modal) modal.classList.remove("show");
            });
        }

        const img = modal.querySelector("#lightbox-full-img");
        const link = modal.querySelector("#lightbox-direct-link");
        const titleEl = modal.querySelector("#lightbox-title");

        if (img) img.src = imageUrl;
        if (link) link.href = imageUrl;
        if (titleEl) titleEl.textContent = title || "Image Preview";

        modal.classList.add("show");
    },

    async startDownload(options = {}) {
        if (!this.currentUrl) return;

        const format = options.format || this.selectedFormat || "zip";
        const selectedIndices = options.selected_indices !== undefined ? options.selected_indices : this.getSelectedImageIndices();
        const customFilename = (options.custom_filename || document.getElementById("custom-filename-input")?.value || "").trim();
        const quality = document.getElementById("quality-select")?.value || "best";
        const captionCheckbox = document.getElementById("include-caption-checkbox");
        const includeCaption = captionCheckbox ? captionCheckbox.checked : false;

        this.showView("downloading-view");

        try {
            const response = await fetch("/api/generate", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    url: this.currentUrl,
                    format: format,
                    selected_indices: selectedIndices && selectedIndices.length > 0 ? selectedIndices : null,
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
            this.showSuccess(data, format);
        } catch (err) {
            this.showError("Network interrupted while generating download package.");
        }
    },

    showSuccess(data, format) {
        const fnEl = document.getElementById("success-filename");
        const szEl = document.getElementById("success-filesize");
        const fmtEl = document.getElementById("success-format");
        const dlBtn = document.getElementById("direct-download-btn");

        if (fnEl) fnEl.textContent = data.filename || "download_file";
        if (szEl) szEl.textContent = data.size_formatted || (data.filesize ? `${(data.filesize / (1024 * 1024)).toFixed(2)} MB` : "Ready");
        if (fmtEl) fmtEl.textContent = (format || this.selectedFormat || "FILE").toUpperCase();

        if (dlBtn) {
            const downloadUrl = `/download/${encodeURIComponent(data.file_id)}`;
            dlBtn.href = downloadUrl;
            dlBtn.setAttribute("download", data.filename || "download_file");
        }

        // Trigger automatic browser download immediately
        if (data.file_id) {
            const autoLink = document.createElement("a");
            autoLink.href = `/download/${encodeURIComponent(data.file_id)}`;
            autoLink.setAttribute("download", data.filename || "download_file");
            document.body.appendChild(autoLink);
            autoLink.click();
            document.body.removeChild(autoLink);
        }

        // Reset email widget
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

        if (emailStatus) {
            emailStatus.className = "email-status-message";
            emailStatus.textContent = "Attaching file and sending via SMTP...";
        }

        try {
            const response = await fetch("/api/email", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    file_id: this.currentFileId,
                    email: email
                })
            });

            const data = await response.json();

            if (response.ok && data.success) {
                if (emailStatus) {
                    emailStatus.className = "email-status-message success";
                    emailStatus.textContent = `Attached & sent successfully to ${email}!`;
                }
                if (emailSendBtn) emailSendBtn.textContent = "Sent!";
            } else {
                const msg = (data.error && data.error.message) || "Failed to deliver email.";
                if (emailStatus) {
                    emailStatus.className = "email-status-message error";
                    emailStatus.textContent = msg;
                }
                if (emailSendBtn) {
                    emailSendBtn.disabled = false;
                    emailSendBtn.textContent = "Retry";
                }
            }
        } catch (err) {
            if (emailStatus) {
                emailStatus.className = "email-status-message error";
                emailStatus.textContent = "Network error sending email.";
            }
            if (emailSendBtn) {
                emailSendBtn.disabled = false;
                emailSendBtn.textContent = "Retry";
            }
        }
    },

    showError(msg) {
        const errorMsgEl = document.getElementById("error-message");
        if (errorMsgEl) {
            errorMsgEl.textContent = msg || "Unable to extract or package media from this URL.";
        }
        this.showView("error-view");
    },

    initModals() {
        const setupModal = (openBtnId, modalId, closeBtnId) => {
            const openBtn = document.getElementById(openBtnId);
            const modal = document.getElementById(modalId);
            const closeBtn = document.getElementById(closeBtnId);

            if (openBtn && modal) {
                openBtn.addEventListener("click", () => modal.classList.add("show"));
            }
            if (closeBtn && modal) {
                closeBtn.addEventListener("click", () => modal.classList.remove("show"));
            }
            if (modal) {
                modal.addEventListener("click", (e) => {
                    if (e.target === modal) modal.classList.remove("show");
                });
            }
        };

        setupModal("open-about-modal", "about-modal", "close-about-modal");
        setupModal("open-platforms-modal", "platforms-modal", "close-platforms-modal");
    }
};

document.addEventListener("DOMContentLoaded", () => {
    DownloaderApp.init();
});
