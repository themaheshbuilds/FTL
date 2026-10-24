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

        // Torrent / Magnet listeners
        const torrentUploadBtn = document.getElementById("torrent-upload-btn");
        const torrentFileInput = document.getElementById("torrent-file-input");
        const btnCancelTorrent = document.getElementById("btn-cancel-torrent");
        const btnTorrentSaveAll = document.getElementById("btn-torrent-save-all");

        if (torrentUploadBtn && torrentFileInput) {
            torrentUploadBtn.addEventListener("click", () => torrentFileInput.click());
            torrentFileInput.addEventListener("change", (e) => {
                const file = e.target.files && e.target.files[0];
                if (file) {
                    this.startTorrent(file);
                }
            });
        }

        if (btnCancelTorrent) {
            btnCancelTorrent.addEventListener("click", () => {
                this.stopTorrent();
                this.showView("input-view");
            });
        }

        if (btnTorrentSaveAll) {
            btnTorrentSaveAll.addEventListener("click", () => {
                this.saveAllTorrentFiles();
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
        const views = ["input-view", "loading-view", "options-view", "downloading-view", "success-view", "torrent-view", "error-view"];
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
        this.stopTorrent();
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
        if (!url) return;
        const low = url.trim().toLowerCase();

        // 1. BitTorrent Magnet Link or .torrent URL: Direct Client-Side P2P Engine ($0 Serverless Cost)
        if (low.startsWith("magnet:") || low.endsWith(".torrent")) {
            this.startTorrent(url.trim());
            return;
        }

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

                    const isYouTube = (data.platform === "YouTube") || (vid.url && /(?:youtube\.com|youtu\.be)/i.test(vid.url));
                    const ytMatch = (vid.url || this.currentUrl || "").match(/(?:v=|youtu\.be\/|embed\/|shorts\/)([a-zA-Z0-9_-]{11})/);
                    const ytId = ytMatch ? ytMatch[1] : null;

                    let previewHtml = "";
                    if (isYouTube && ytId) {
                        previewHtml = `
                            <iframe
                                src="https://www.youtube-nocookie.com/embed/${ytId}?autoplay=0"
                                title="${vid.title || 'YouTube Video'}"
                                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                                allowfullscreen
                                style="width:100%;height:220px;border:none;border-radius:10px;background:#000;">
                            </iframe>
                        `;
                    } else if (vid.url && !vid.url.includes("youtube.com") && !vid.url.includes("youtu.be")) {
                        previewHtml = `<video controls preload="metadata" poster="${vid.thumbnail_url || ''}" src="${vid.url}"></video>`;
                    } else {
                        previewHtml = `
                            <img src="${vid.thumbnail_url || ''}" alt="Video thumbnail">
                            <div class="video-play-badge">&#x25B6;</div>
                        `;
                    }

                    card.innerHTML = `
                        <div class="video-preview-wrapper">
                            ${previewHtml}
                        </div>
                        <div class="video-item-info">
                            <div class="video-item-title">${vid.title || `Video #${i + 1}`}</div>
                            <div class="video-actions-row">
                                <button type="button" class="btn-video-action btn-mp4" data-index="${vid.origIndex}">
                                    &#x2193; Download MP4 (Highest Quality)
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
                            const chosenQuality = document.getElementById("quality-select")?.value || "highest";
                            this.startDownload({
                                format: "mp4",
                                quality: chosenQuality,
                                selected_indices: [vid.origIndex],
                                custom_filename: `video_${i + 1}`
                            });
                        });
                    }

                    if (mkvBtn) {
                        mkvBtn.addEventListener("click", () => {
                            const chosenQuality = document.getElementById("quality-select")?.value || "highest";
                            this.startDownload({
                                format: "mkv",
                                quality: chosenQuality,
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
                mp4: { format: "mp4", label: "MP4 Video", badge: "MP4", desc: "Highest quality video merged with audio (4K / 1080p)" },
                video: { format: "mp4", label: "MP4 Video", badge: "MP4", desc: "Original video stream packaged in MP4 container" },
                mkv: { format: "mkv", label: "MKV Video", badge: "MKV", desc: "Lossless Matroska container in maximum resolution" },
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

        // Video Quality & Caption Setting Groups
        const qualityGroup = document.getElementById("quality-setting-group");
        const qualitySelect = document.getElementById("quality-select");
        const hasVideos = videos.length > 0 || (data.content_type && data.content_type.includes("video"));

        if (qualityGroup && qualitySelect) {
            if (hasVideos) {
                qualityGroup.style.display = "flex";
                qualitySelect.innerHTML = `
                    <option value="highest" selected>⚡ Highest Quality Available (Original / 4K / 1080p)</option>
                    <option value="1080p">1080p Full HD</option>
                    <option value="720p">720p HD (Faster download)</option>
                    <option value="480p">480p SD</option>
                `;
            } else {
                qualityGroup.style.display = "none";
                qualitySelect.innerHTML = "";
            }
        }

        const captionGroup = document.getElementById("caption-setting-group");
        if (captionGroup) {
            captionGroup.style.display = data.description ? "flex" : "none";
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
        const quality = options.quality || document.getElementById("quality-select")?.value || "highest";
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

    dataUrlToBlobUrl(dataUrl) {
        if (!dataUrl || typeof dataUrl !== "string" || !dataUrl.startsWith("data:")) return dataUrl;
        try {
            const parts = dataUrl.split(";base64,");
            if (parts.length === 2) {
                const mimeType = parts[0].replace(/^data:/, "") || "application/octet-stream";
                const byteCharacters = atob(parts[1]);
                const byteNumbers = new Uint8Array(byteCharacters.length);
                for (let i = 0; i < byteCharacters.length; i++) {
                    byteNumbers[i] = byteCharacters.charCodeAt(i);
                }
                const blob = new Blob([byteNumbers], { type: mimeType });
                return URL.createObjectURL(blob);
            }
        } catch (e) {
            console.warn("Could not convert data_url to Blob URL:", e);
        }
        return dataUrl;
    },

    showSuccess(data, format) {
        const fnEl = document.getElementById("success-filename");
        const szEl = document.getElementById("success-filesize");
        const fmtEl = document.getElementById("success-format");
        const dlBtn = document.getElementById("direct-download-btn");

        const filename = data.filename || "download_file";
        if (fnEl) fnEl.textContent = filename;
        if (szEl) szEl.textContent = data.size_formatted || (data.filesize ? `${(data.filesize / (1024 * 1024)).toFixed(2)} MB` : "Ready");
        if (fmtEl) fmtEl.textContent = (format || this.selectedFormat || "FILE").toUpperCase();

        const rawUrl = data.data_url || data.direct_url || data.download_url || `/download/${encodeURIComponent(data.file_id)}`;
        const downloadUrl = data.data_url ? this.dataUrlToBlobUrl(data.data_url) : rawUrl;
        if (dlBtn) {
            dlBtn.href = downloadUrl;
            dlBtn.setAttribute("download", filename);
        }

        // Trigger automatic browser download immediately via Blob Object URL
        if (downloadUrl) {
            const autoLink = document.createElement("a");
            autoLink.href = downloadUrl;
            autoLink.setAttribute("download", filename);
            document.body.appendChild(autoLink);
            autoLink.click();
            setTimeout(() => {
                try { document.body.removeChild(autoLink); } catch (e) {}
            }, 600);
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
    },

    // ============================================================
    // WEBTORRENT LIVE P2P ENGINE (100% Free / $0 Vercel Bandwidth)
    // ============================================================
    torrentClient: null,
    activeTorrent: null,
    DEFAULT_TRACKERS: [
        "wss://tracker.openwebtorrent.com",
        "wss://tracker.webtorrent.dev",
        "wss://tracker.files.fm:7073/announce",
        "wss://tracker.btorrent.xyz"
    ],

    stopTorrent() {
        if (this.activeTorrent) {
            try {
                this.activeTorrent.destroy();
            } catch (e) {
                console.warn("Torrent destroy warning:", e);
            }
            this.activeTorrent = null;
        }
    },

    formatBytes(bytes) {
        if (!bytes || bytes <= 0 || isNaN(bytes)) return "0 B";
        const k = 1024;
        const dm = 2;
        const sizes = ["B", "KB", "MB", "GB", "TB"];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + " " + sizes[i];
    },

    formatETA(ms) {
        if (!ms || ms === Infinity || isNaN(ms)) return "Connecting...";
        const seconds = Math.floor(ms / 1000);
        if (seconds < 60) return `${seconds}s`;
        const minutes = Math.floor(seconds / 60);
        const remSecs = seconds % 60;
        if (minutes < 60) return `${minutes}m ${remSecs}s`;
        const hours = Math.floor(minutes / 60);
        return `${hours}h ${minutes % 60}m`;
    },

    startTorrent(torrentIdOrFile) {
        if (typeof WebTorrent === "undefined") {
            this.showError("WebTorrent engine could not be loaded in your browser. Please check your network connection.");
            return;
        }

        this.stopTorrent();
        this.showView("torrent-view");

        // Reset UI metrics
        const titleEl = document.getElementById("torrent-title");
        const statusEl = document.getElementById("torrent-status-summary");
        const dlEl = document.getElementById("torrent-dl-speed");
        const ulEl = document.getElementById("torrent-ul-speed");
        const peersEl = document.getElementById("torrent-peers");
        const etaEl = document.getElementById("torrent-eta");
        const progBar = document.getElementById("torrent-progress-bar");
        const bytesInfo = document.getElementById("torrent-bytes-info");
        const fileList = document.getElementById("torrent-files-list");
        const playerCont = document.getElementById("torrent-player-container");
        const playerWrapper = document.getElementById("torrent-video-wrapper");

        if (titleEl) titleEl.textContent = "Connecting to Torrent Swarm...";
        if (statusEl) statusEl.textContent = "Discovering WebRTC peers and trackers...";
        if (dlEl) dlEl.textContent = "0 KB/s";
        if (ulEl) ulEl.textContent = "0 KB/s";
        if (peersEl) peersEl.textContent = "0 peers";
        if (etaEl) etaEl.textContent = "Connecting...";
        if (progBar) progBar.style.width = "0%";
        if (bytesInfo) bytesInfo.textContent = "0 MB / 0 MB (0%)";
        if (fileList) fileList.innerHTML = "<div style='color:var(--text-muted);font-size:13px;padding:8px 0'>Fetching torrent metadata from swarm...</div>";
        if (playerCont) playerCont.style.display = "none";
        if (playerWrapper) playerWrapper.innerHTML = "";

        if (!this.torrentClient) {
            try {
                this.torrentClient = new WebTorrent({
                    tracker: {
                        rtcConfig: {
                            iceServers: [
                                { urls: "stun:stun.l.google.com:19302" },
                                { urls: "stun:global.stun.twilio.com:3478" }
                            ]
                        }
                    }
                });
            } catch (ce) {
                console.error("WebTorrent init error:", ce);
                this.showError("Could not initialize WebTorrent client: " + ce.message);
                return;
            }
        }

        try {
            this.torrentClient.add(torrentIdOrFile, { announce: this.DEFAULT_TRACKERS }, (torrent) => {
                this.activeTorrent = torrent;
                this.renderTorrent(torrent);
            });
        } catch (err) {
            console.error("Failed to add torrent:", err);
            this.showError("Invalid torrent or magnet link. " + (err.message || ""));
        }
    },

    renderTorrent(torrent) {
        const titleEl = document.getElementById("torrent-title");
        const hashBadge = document.getElementById("torrent-hash-badge");
        const fileCountEl = document.getElementById("torrent-file-count");
        const statusEl = document.getElementById("torrent-status-summary");

        if (titleEl) titleEl.textContent = torrent.name || "BitTorrent Download";
        if (hashBadge) hashBadge.textContent = (torrent.infoHash || "Swarm").substring(0, 10).toUpperCase();
        if (fileCountEl) fileCountEl.textContent = torrent.files.length;
        if (statusEl) statusEl.textContent = `${torrent.files.length} file${torrent.files.length > 1 ? 's' : ''} • Total: ${this.formatBytes(torrent.length)}`;

        const filesList = document.getElementById("torrent-files-list");
        if (filesList) filesList.innerHTML = "";

        const btnSaveAll = document.getElementById("btn-torrent-save-all");
        if (btnSaveAll) {
            btnSaveAll.style.display = torrent.files.length > 1 ? "inline-flex" : "none";
        }

        // Check if there is a playable video file
        const videoFile = torrent.files.find(f => {
            const ext = f.name.split('.').pop().toLowerCase();
            return ["mp4", "webm", "mkv", "mov"].includes(ext);
        });

        if (videoFile) {
            const playerCont = document.getElementById("torrent-player-container");
            const playerWrapper = document.getElementById("torrent-video-wrapper");
            if (playerCont && playerWrapper) {
                playerCont.style.display = "block";
                playerWrapper.innerHTML = "";

                const vidEl = document.createElement("video");
                vidEl.controls = true;
                vidEl.autoplay = false;
                vidEl.playsInline = true;
                playerWrapper.appendChild(vidEl);

                try {
                    videoFile.renderTo(vidEl, (err) => {
                        if (err) console.warn("Video stream render warning:", err);
                    });
                } catch (ve) {
                    console.warn("renderTo error:", ve);
                }
            }
        }

        // Render each file in the torrent
        if (filesList) {
            torrent.files.forEach((file, idx) => {
                const row = document.createElement("div");
                row.className = "torrent-file-row";
                const ext = file.name.split('.').pop().toLowerCase();
                let icon = "📄";
                if (["mp4", "mkv", "webm", "mov", "avi"].includes(ext)) icon = "🎬";
                else if (["mp3", "m4a", "flac", "wav", "ogg"].includes(ext)) icon = "🎵";
                else if (["jpg", "jpeg", "png", "webp", "gif"].includes(ext)) icon = "🖼️";
                else if (["zip", "rar", "7z", "tar", "gz", "iso"].includes(ext)) icon = "📦";
                else if (["pdf", "docx", "txt", "epub"].includes(ext)) icon = "📑";

                row.innerHTML = `
                    <div class="torrent-file-info">
                        <span class="torrent-file-icon">${icon}</span>
                        <div style="min-width:0">
                            <div class="torrent-file-title" title="${file.name}">${file.name}</div>
                            <div class="torrent-file-sub" id="file-prog-${idx}">${this.formatBytes(file.length)} • 0% ready</div>
                        </div>
                    </div>
                    <div class="torrent-file-actions">
                        <button type="button" class="btn-file-save" id="btn-save-file-${idx}">
                            ⬇️ Save File
                        </button>
                    </div>
                `;

                const saveBtn = row.querySelector(`#btn-save-file-${idx}`);
                if (saveBtn) {
                    saveBtn.addEventListener("click", () => {
                        saveBtn.textContent = "⏳ Preparing...";
                        file.getBlobURL((err, url) => {
                            if (err) {
                                alert("Could not generate file: " + err.message);
                                saveBtn.textContent = "⬇️ Save File";
                                return;
                            }
                            const a = document.createElement("a");
                            a.href = url;
                            a.download = file.name;
                            document.body.appendChild(a);
                            a.click();
                            setTimeout(() => {
                                if (document.body.contains(a)) document.body.removeChild(a);
                                saveBtn.textContent = "✓ Saved";
                            }, 500);
                        });
                    });
                }

                filesList.appendChild(row);
            });
        }

        // Throttle progress updates to 200ms
        let lastUpdate = 0;
        const onProgressUpdate = () => {
            const now = Date.now();
            if (now - lastUpdate < 150) return;
            lastUpdate = now;

            const percent = (torrent.progress * 100).toFixed(1);
            const dlEl = document.getElementById("torrent-dl-speed");
            const ulEl = document.getElementById("torrent-ul-speed");
            const peersEl = document.getElementById("torrent-peers");
            const etaEl = document.getElementById("torrent-eta");
            const progBar = document.getElementById("torrent-progress-bar");
            const bytesInfo = document.getElementById("torrent-bytes-info");

            if (dlEl) dlEl.textContent = this.formatBytes(torrent.downloadSpeed) + "/s";
            if (ulEl) ulEl.textContent = this.formatBytes(torrent.uploadSpeed) + "/s";
            if (peersEl) peersEl.textContent = `${torrent.numPeers} peer${torrent.numPeers !== 1 ? 's' : ''}`;
            if (etaEl) etaEl.textContent = this.formatETA(torrent.timeRemaining);
            if (progBar) progBar.style.width = `${percent}%`;
            if (bytesInfo) bytesInfo.textContent = `${this.formatBytes(torrent.downloaded)} / ${this.formatBytes(torrent.length)} (${percent}%)`;

            // Update individual file progress indicators
            torrent.files.forEach((file, idx) => {
                const sub = document.getElementById(`file-prog-${idx}`);
                if (sub) {
                    const fprog = (file.progress * 100).toFixed(0);
                    sub.textContent = `${this.formatBytes(file.length)} • ${fprog}% ready`;
                }
            });
        };

        torrent.on("download", onProgressUpdate);
        torrent.on("upload", onProgressUpdate);

        torrent.on("done", () => {
            const progBar = document.getElementById("torrent-progress-bar");
            const bytesInfo = document.getElementById("torrent-bytes-info");
            const statusEl = document.getElementById("torrent-status-summary");
            const etaEl = document.getElementById("torrent-eta");

            if (progBar) progBar.style.width = "100%";
            if (bytesInfo) bytesInfo.textContent = `${this.formatBytes(torrent.length)} / ${this.formatBytes(torrent.length)} (100% Complete!)`;
            if (statusEl) statusEl.textContent = "Download complete! All files ready to save.";
            if (etaEl) etaEl.textContent = "Finished!";
        });
    },

    saveAllTorrentFiles() {
        if (!this.activeTorrent) return;
        this.activeTorrent.files.forEach(file => {
            file.getBlobURL((err, url) => {
                if (!err && url) {
                    const a = document.createElement("a");
                    a.href = url;
                    a.download = file.name;
                    document.body.appendChild(a);
                    a.click();
                    setTimeout(() => {
                        if (document.body.contains(a)) document.body.removeChild(a);
                    }, 500);
                }
            });
        });
    }
};

document.addEventListener("DOMContentLoaded", () => {
    DownloaderApp.init();
});
