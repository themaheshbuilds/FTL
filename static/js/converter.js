/**
 * LinkForge - File Converter Hub Controller (Frontend)
 * Supports PDF to Images, Images to PDF, Video to Audio, DOCX to PDF, and more.
 */

const Converter = {
    activeTool: null,
    selectedFiles: [],
    currentBlobUrl: null,

    tools: {
        pdf_to_images: {
            id: "pdf_to_images",
            title: "PDF to Images",
            category: "docs",
            icon: "📄",
            badge: "PDF → JPG/PNG (Any Size)",
            description: "Extract pages of any PDF into high-resolution JPG or PNG images directly in your browser (unlimited file size).",
            accept: ".pdf",
            multiple: false,
            outputFormats: [
                { value: "jpg", label: "JPG Images (.jpg)" },
                { value: "png", label: "PNG Images (.png)" }
            ]
        },
        images_to_pdf: {
            id: "images_to_pdf",
            title: "Images to PDF",
            category: "docs",
            icon: "🖼️",
            badge: "Images → PDF",
            description: "Combine multiple JPG, PNG, or WebP images into a single multi-page PDF document.",
            accept: ".jpg,.jpeg,.png,.webp,.bmp",
            multiple: true,
            outputFormats: [
                { value: "pdf", label: "PDF Document (.pdf)" }
            ]
        },
        video_to_audio: {
            id: "video_to_audio",
            title: "Video to Audio",
            category: "media",
            icon: "🎬",
            badge: "Video → MP3/M4A",
            description: "Extract crystal-clear audio from any MP4, MKV, WebM, MOV, or AVI video.",
            accept: ".mp4,.mkv,.webm,.mov,.avi,.flv",
            multiple: false,
            outputFormats: [
                { value: "mp3", label: "MP3 Audio (192 kbps)" },
                { value: "m4a", label: "M4A Audio (AAC)" }
            ]
        },
        docx_to_pdf: {
            id: "docx_to_pdf",
            title: "Word (DOCX) to PDF",
            category: "docs",
            icon: "📝",
            badge: "DOCX → PDF",
            description: "Convert Word documents (.docx) to PDF with crisp layout and typography.",
            accept: ".docx,.doc",
            multiple: false,
            outputFormats: [
                { value: "pdf", label: "PDF Document (.pdf)" }
            ]
        },
        pdf_to_docx: {
            id: "pdf_to_docx",
            title: "PDF to Word (DOCX)",
            category: "docs",
            icon: "🗜️",
            badge: "PDF → DOCX",
            description: "Extract text and embedded images from PDF into an editable Word document.",
            accept: ".pdf",
            multiple: false,
            outputFormats: [
                { value: "docx", label: "Word Document (.docx)" }
            ]
        },
        video_converter: {
            id: "video_converter",
            title: "Video Converter",
            category: "media",
            icon: "🎞️",
            badge: "MP4 ↔ MKV ↔ WebM",
            description: "Convert video files between MP4, MKV, and WebM multimedia containers.",
            accept: ".mp4,.mkv,.webm,.mov,.avi",
            multiple: false,
            outputFormats: [
                { value: "mp4", label: "MP4 Video (.mp4)" },
                { value: "mkv", label: "MKV Video (.mkv)" },
                { value: "webm", label: "WebM Video (.webm)" }
            ]
        },
        image_converter: {
            id: "image_converter",
            title: "Image Converter",
            category: "images",
            icon: "🎨",
            badge: "JPG ↔ PNG ↔ WebP",
            description: "Convert image files between JPG, PNG, and WebP format.",
            accept: ".jpg,.jpeg,.png,.webp,.bmp",
            multiple: false,
            outputFormats: [
                { value: "png", label: "PNG (.png)" },
                { value: "jpg", label: "JPG (.jpg)" },
                { value: "webp", label: "WebP (.webp)" }
            ]
        }
    },

    init() {
        this.bindModeTabs();
        this.renderToolCards();
        this.bindWorkspaceEvents();

        // Initialize PDF.js worker if available
        if (window.pdfjsLib) {
            pdfjsLib.GlobalWorkerOptions.workerSrc = "https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js";
        }
    },

    bindModeTabs() {
        const tabDownloader = document.getElementById("tab-downloader");
        const tabConverter = document.getElementById("tab-converter");
        const viewDownloader = document.getElementById("downloader-view");
        const viewConverter = document.getElementById("converter-view");

        if (tabDownloader && tabConverter) {
            tabDownloader.addEventListener("click", () => {
                tabDownloader.classList.add("active");
                tabConverter.classList.remove("active");
                if (viewDownloader) viewDownloader.style.display = "block";
                if (viewConverter) viewConverter.style.display = "none";
            });

            tabConverter.addEventListener("click", () => {
                tabConverter.classList.add("active");
                tabDownloader.classList.remove("active");
                if (viewDownloader) viewDownloader.style.display = "none";
                if (viewConverter) viewConverter.style.display = "block";
            });
        }
    },

    renderToolCards(filterCategory = "all") {
        const grid = document.getElementById("converter-tools-grid");
        if (!grid) return;

        grid.innerHTML = "";

        Object.values(this.tools).forEach(tool => {
            if (filterCategory !== "all" && tool.category !== filterCategory) return;

            const card = document.createElement("div");
            card.className = "tool-card";
            card.innerHTML = `
                <div class="tool-card-header">
                    <span class="tool-card-icon">${tool.icon}</span>
                    <span class="tool-card-badge">${tool.badge}</span>
                </div>
                <h3 class="tool-card-title">${tool.title}</h3>
                <p class="tool-card-desc">${tool.description}</p>
                <button type="button" class="tool-card-btn" data-tool-id="${tool.id}">
                    Select Tool →
                </button>
            `;

            card.querySelector(".tool-card-btn").addEventListener("click", () => {
                this.selectTool(tool.id);
            });

            grid.appendChild(card);
        });

        // Filter pills
        const filterBtns = document.querySelectorAll(".tool-filter-btn");
        filterBtns.forEach(btn => {
            btn.onclick = () => {
                filterBtns.forEach(b => b.classList.remove("active"));
                btn.classList.add("active");
                this.renderToolCards(btn.dataset.category);
            };
        });
    },

    selectTool(toolId) {
        const tool = this.tools[toolId];
        if (!tool) return;

        this.activeTool = tool;
        this.selectedFiles = [];

        // Scroll to workspace smoothly
        const workspace = document.getElementById("converter-workspace");
        if (workspace) {
            workspace.style.display = "block";
            workspace.scrollIntoView({ behavior: "smooth", block: "start" });
        }

        // Hide tools catalog or collapse
        document.getElementById("active-tool-icon").textContent = tool.icon;
        document.getElementById("active-tool-title").textContent = tool.title;
        document.getElementById("active-tool-desc").textContent = tool.description;

        const fileInput = document.getElementById("converter-file-input");
        fileInput.value = "";
        fileInput.accept = tool.accept;
        fileInput.multiple = tool.multiple;

        // Populate output format selector
        const formatSelect = document.getElementById("converter-format-select");
        formatSelect.innerHTML = "";
        tool.outputFormats.forEach(fmt => {
            const opt = document.createElement("option");
            opt.value = fmt.value;
            opt.textContent = fmt.label;
            formatSelect.appendChild(opt);
        });

        // Reset filename input
        const nameInput = document.getElementById("converter-filename-input");
        if (nameInput) nameInput.value = "";

        this.renderSelectedFiles();
        this.hideWorkspaceSubsections();
        document.getElementById("converter-upload-form").style.display = "block";
    },

    bindWorkspaceEvents() {
        const dropZone = document.getElementById("converter-dropzone");
        const fileInput = document.getElementById("converter-file-input");
        const browseBtn = document.getElementById("converter-browse-btn");
        const convertBtn = document.getElementById("btn-do-convert");
        const backBtn = document.getElementById("btn-back-to-tools");
        const resetSuccessBtn = document.getElementById("btn-reset-converter-success");
        const resetErrorBtn = document.getElementById("btn-reset-converter-error");

        if (browseBtn && fileInput) {
            browseBtn.onclick = () => fileInput.click();
        }

        if (fileInput) {
            fileInput.onchange = (e) => {
                if (e.target.files && e.target.files.length > 0) {
                    this.addFiles(Array.from(e.target.files));
                }
            };
        }

        if (dropZone) {
            ["dragenter", "dragover"].forEach(eventName => {
                dropZone.addEventListener(eventName, (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    dropZone.classList.add("dragover");
                });
            });

            ["dragleave", "drop"].forEach(eventName => {
                dropZone.addEventListener(eventName, (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    dropZone.classList.remove("dragover");
                });
            });

            dropZone.addEventListener("drop", (e) => {
                const dt = e.dataTransfer;
                if (dt && dt.files && dt.files.length > 0) {
                    this.addFiles(Array.from(dt.files));
                }
            });
        }

        if (convertBtn) {
            convertBtn.onclick = () => this.submitConversion();
        }

        if (backBtn) {
            backBtn.onclick = () => {
                const workspace = document.getElementById("converter-workspace");
                if (workspace) workspace.style.display = "none";
                const grid = document.getElementById("converter-tools-grid");
                if (grid) grid.scrollIntoView({ behavior: "smooth" });
            };
        }

        if (resetSuccessBtn) {
            resetSuccessBtn.onclick = () => this.resetWorkspace();
        }

        if (resetErrorBtn) {
            resetErrorBtn.onclick = () => this.resetWorkspace();
        }
    },

    addFiles(files) {
        if (!this.activeTool) return;

        if (!this.activeTool.multiple) {
            this.selectedFiles = [files[0]];
        } else {
            // Append and deduplicate
            files.forEach(f => {
                if (!this.selectedFiles.some(existing => existing.name === f.name && existing.size === f.size)) {
                    this.selectedFiles.push(f);
                }
            });
        }

        this.renderSelectedFiles();
    },

    removeFile(idx) {
        this.selectedFiles.splice(idx, 1);
        this.renderSelectedFiles();
    },

    renderSelectedFiles() {
        const container = document.getElementById("converter-selected-files");
        const convertBtn = document.getElementById("btn-do-convert");
        if (!container) return;

        container.innerHTML = "";

        if (this.selectedFiles.length === 0) {
            container.style.display = "none";
            if (convertBtn) convertBtn.disabled = true;
            return;
        }

        container.style.display = "flex";
        if (convertBtn) convertBtn.disabled = false;

        this.selectedFiles.forEach((file, idx) => {
            const chip = document.createElement("div");
            chip.className = "selected-file-chip";

            const sizeText = file.size < 1024 * 1024
                ? `${(file.size / 1024).toFixed(1)} KB`
                : `${(file.size / (1024 * 1024)).toFixed(2)} MB`;

            chip.innerHTML = `
                <span class="chip-name" title="${file.name}">${file.name}</span>
                <span class="chip-size">${sizeText}</span>
                <button type="button" class="chip-remove-btn" title="Remove file">✕</button>
            `;

            chip.querySelector(".chip-remove-btn").onclick = (e) => {
                e.stopPropagation();
                this.removeFile(idx);
            };

            container.appendChild(chip);
        });

        // Auto prefill custom filename placeholder if 1 file
        const nameInput = document.getElementById("converter-filename-input");
        if (nameInput && this.selectedFiles.length === 1 && !nameInput.value) {
            nameInput.placeholder = this.selectedFiles[0].name.replace(/\.[^/.]+$/, "");
        }
    },

    async submitConversion() {
        if (!this.activeTool || this.selectedFiles.length === 0) return;

        const formatSelect = document.getElementById("converter-format-select");
        const outputFormat = formatSelect ? formatSelect.value : "";
        const nameInput = document.getElementById("converter-filename-input");
        const customFilename = nameInput ? nameInput.value.trim() : "";

        // High-Capacity Client-Side Processing for PDF to Images (Bypasses Vercel 4.5 MB payload limit)
        if (this.activeTool.id === "pdf_to_images" && window.pdfjsLib && window.JSZip) {
            try {
                await this.convertPdfToImagesClientSide(this.selectedFiles[0], outputFormat, customFilename);
                return;
            } catch (clientErr) {
                console.warn("Client-side PDF conversion error, checking fallback:", clientErr);
                // If file is larger than 4.5 MB, serverless upload will be rejected with 413, so report client error clearly
                if (this.selectedFiles[0].size > 4.5 * 1024 * 1024) {
                    this.showError(`PDF conversion failed: ${clientErr.message || "Unable to parse PDF pages."}`);
                    return;
                }
                // If under 4.5 MB, fall through to server conversion as fallback
            }
        }

        // High-Capacity Client-Side Processing for Image Converter (JPG, PNG, WebP)
        if (this.activeTool.id === "image_converter") {
            try {
                await this.convertImageClientSide(this.selectedFiles[0], outputFormat, customFilename);
                return;
            } catch (imgErr) {
                console.warn("Client-side image conversion error, falling back to server:", imgErr);
            }
        }

        // Standard Server-Side Conversion (Localhost or Supported Cloud Conversions)
        const formData = new FormData();
        formData.append("conversion_type", this.activeTool.id);
        formData.append("output_format", outputFormat);
        formData.append("custom_filename", customFilename);

        this.selectedFiles.forEach(file => {
            formData.append("files", file);
        });

        // Show loading state
        this.hideWorkspaceSubsections();
        const loadingCard = document.getElementById("converter-loading-card");
        this.setLoadingStatus("Processing Conversion...", "Converting with native high-performance engines.");
        loadingCard.style.display = "block";

        try {
            const response = await fetch("/api/convert", {
                method: "POST",
                body: formData
            });

            if (response.status === 413) {
                this.showError("File exceeds the serverless upload limit (4.5 MB on Vercel). Please upload a smaller file or run locally for files up to 500 MB.");
                return;
            }

            const contentType = response.headers.get("content-type") || "";
            if (!contentType.includes("application/json")) {
                const text = await response.text();
                this.showError(text || `Server returned error (${response.status})`);
                return;
            }

            const data = await response.json();

            if (!response.ok || !data.success) {
                const message = (data.error && data.error.message) || "Conversion failed.";
                this.showError(message);
                return;
            }

            this.showSuccess(data);
        } catch (err) {
            this.showError(err.message || "Network error occurred during conversion.");
        }
    },

    async convertPdfToImagesClientSide(file, outputFormat, customFilename) {
        this.hideWorkspaceSubsections();
        const loadingCard = document.getElementById("converter-loading-card");
        loadingCard.style.display = "block";
        this.setLoadingStatus("Processing PDF In-Browser...", "Loading PDF document (zero server upload)...");

        if (!pdfjsLib.GlobalWorkerOptions.workerSrc) {
            pdfjsLib.GlobalWorkerOptions.workerSrc = "https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js";
        }

        const outFormat = (outputFormat || "jpg").toLowerCase();
        const isPng = outFormat === "png";
        const mimeType = isPng ? "image/png" : "image/jpeg";
        const ext = isPng ? "png" : "jpg";

        const arrayBuffer = await file.arrayBuffer();
        const loadingTask = pdfjsLib.getDocument({ data: arrayBuffer });
        const pdf = await loadingTask.promise;
        const numPages = pdf.numPages;

        if (numPages === 0) {
            throw new Error("The selected PDF document contains no pages.");
        }

        const rawName = customFilename || file.name.replace(/\.[^/.]+$/, "");
        const safeBase = rawName.replace(/[^a-zA-Z0-9_\-]/g, "_").replace(/^_+|_+$/g, "") || "converted_file";

        if (numPages === 1) {
            this.setLoadingStatus("Rendering Page 1 of 1...", "Exporting high-resolution image...");
            const page = await pdf.getPage(1);
            const viewport = page.getViewport({ scale: 2.0 });

            const canvas = document.createElement("canvas");
            canvas.width = Math.floor(viewport.width);
            canvas.height = Math.floor(viewport.height);
            const ctx = canvas.getContext("2d");

            await page.render({ canvasContext: ctx, viewport: viewport }).promise;

            const blob = await new Promise((resolve, reject) => {
                canvas.toBlob(b => b ? resolve(b) : reject(new Error("Canvas export failed")), mimeType, 0.92);
            });

            const blobUrl = URL.createObjectURL(blob);
            const outFilename = `${safeBase}.${ext}`;
            const sizeFormatted = blob.size < 1024 * 1024
                ? `${(blob.size / 1024).toFixed(1)} KB`
                : `${(blob.size / (1024 * 1024)).toFixed(2)} MB`;

            this.showSuccess({
                filename: outFilename,
                size_formatted: sizeFormatted,
                blobUrl: blobUrl,
                isClientSide: true
            });
        } else {
            const zip = new JSZip();
            const padDigits = Math.max(2, String(numPages).length);

            for (let i = 1; i <= numPages; i++) {
                const percent = Math.round((i / numPages) * 100);
                this.setLoadingStatus("Rendering PDF Pages...", `Rendering page ${i} of ${numPages} (${percent}%)...`);

                const page = await pdf.getPage(i);
                const viewport = page.getViewport({ scale: 2.0 });

                const canvas = document.createElement("canvas");
                canvas.width = Math.floor(viewport.width);
                canvas.height = Math.floor(viewport.height);
                const ctx = canvas.getContext("2d");

                await page.render({ canvasContext: ctx, viewport: viewport }).promise;

                const pageBlob = await new Promise((resolve, reject) => {
                    canvas.toBlob(b => b ? resolve(b) : reject(new Error("Canvas export failed")), mimeType, 0.92);
                });

                const pageNumStr = String(i).padStart(padDigits, "0");
                zip.file(`page_${pageNumStr}.${ext}`, pageBlob);
            }

            this.setLoadingStatus("Packaging Archive...", "Compressing all rendered pages into ZIP...");
            const zipBlob = await zip.generateAsync({ type: "blob", compression: "DEFLATE" }, (metadata) => {
                this.setLoadingStatus("Packaging Archive...", `Compressing ZIP: ${Math.round(metadata.percent)}%...`);
            });

            const blobUrl = URL.createObjectURL(zipBlob);
            const outFilename = `${safeBase}_pages.zip`;
            const sizeFormatted = zipBlob.size < 1024 * 1024
                ? `${(zipBlob.size / 1024).toFixed(1)} KB`
                : `${(zipBlob.size / (1024 * 1024)).toFixed(2)} MB`;

            this.showSuccess({
                filename: outFilename,
                size_formatted: sizeFormatted,
                blobUrl: blobUrl,
                isClientSide: true
            });
        }
    },

    async convertImageClientSide(file, outputFormat, customFilename) {
        this.hideWorkspaceSubsections();
        const loadingCard = document.getElementById("converter-loading-card");
        loadingCard.style.display = "block";
        this.setLoadingStatus("Converting Image...", "Processing image locally in browser...");

        const outFormat = (outputFormat || "png").toLowerCase();
        let mimeType = "image/png";
        if (outFormat === "jpg" || outFormat === "jpeg") mimeType = "image/jpeg";
        else if (outFormat === "webp") mimeType = "image/webp";

        const rawName = customFilename || file.name.replace(/\.[^/.]+$/, "");
        const safeBase = rawName.replace(/[^a-zA-Z0-9_\-]/g, "_").replace(/^_+|_+$/g, "") || "converted_image";

        const imageBitmap = await createImageBitmap(file);
        const canvas = document.createElement("canvas");
        canvas.width = imageBitmap.width;
        canvas.height = imageBitmap.height;
        const ctx = canvas.getContext("2d");
        ctx.drawImage(imageBitmap, 0, 0);

        const blob = await new Promise((resolve, reject) => {
            canvas.toBlob(b => b ? resolve(b) : reject(new Error("Image export failed")), mimeType, 0.95);
        });

        const blobUrl = URL.createObjectURL(blob);
        const outFilename = `${safeBase}.${outFormat === "jpeg" ? "jpg" : outFormat}`;
        const sizeFormatted = blob.size < 1024 * 1024
            ? `${(blob.size / 1024).toFixed(1)} KB`
            : `${(blob.size / (1024 * 1024)).toFixed(2)} MB`;

        this.showSuccess({
            filename: outFilename,
            size_formatted: sizeFormatted,
            blobUrl: blobUrl,
            isClientSide: true
        });
    },

    setLoadingStatus(title, subtitle) {
        const loadingCard = document.getElementById("converter-loading-card");
        if (loadingCard) {
            const titleEl = loadingCard.querySelector(".status-title");
            const subEl = loadingCard.querySelector(".status-subtitle");
            if (titleEl && title) titleEl.textContent = title;
            if (subEl && subtitle) subEl.textContent = subtitle;
        }
    },

    showSuccess(data) {
        this.hideWorkspaceSubsections();

        // Revoke previous blob URL to prevent memory leaks
        if (this.currentBlobUrl) {
            URL.revokeObjectURL(this.currentBlobUrl);
            this.currentBlobUrl = null;
        }

        const successCard = document.getElementById("converter-success-card");
        document.getElementById("converter-success-filename").textContent = data.filename || "converted_file";
        document.getElementById("converter-success-filesize").textContent = data.size_formatted || "Ready";

        const directBtn = document.getElementById("converter-direct-download-btn");
        const expiryNotice = successCard.querySelector(".expiry-notice");

        if (data.blobUrl) {
            this.currentBlobUrl = data.blobUrl;
            directBtn.href = data.blobUrl;
            directBtn.setAttribute("download", data.filename || "converted_file");
            if (expiryNotice) {
                expiryNotice.textContent = "⚡ Rendered instantly on your device — Zero server upload, zero file size limits.";
            }
        } else {
            directBtn.href = `/download/${encodeURIComponent(data.file_id)}`;
            directBtn.removeAttribute("download");
            if (expiryNotice) {
                expiryNotice.textContent = "⏳ Stored securely in isolated temporary workspace for 30 minutes.";
            }
        }

        successCard.style.display = "block";
    },

    showError(msg) {
        this.hideWorkspaceSubsections();
        const errCard = document.getElementById("converter-error-card");
        document.getElementById("converter-error-message").textContent = msg;
        errCard.style.display = "block";
    },

    hideWorkspaceSubsections() {
        document.getElementById("converter-upload-form").style.display = "none";
        document.getElementById("converter-loading-card").style.display = "none";
        document.getElementById("converter-success-card").style.display = "none";
        document.getElementById("converter-error-card").style.display = "none";
    },

    resetWorkspace() {
        if (this.currentBlobUrl) {
            URL.revokeObjectURL(this.currentBlobUrl);
            this.currentBlobUrl = null;
        }
        this.selectedFiles = [];
        this.renderSelectedFiles();
        this.hideWorkspaceSubsections();
        this.setLoadingStatus("Processing Conversion...", "Converting with native high-performance engines.");
        document.getElementById("converter-upload-form").style.display = "block";
    }
};

document.addEventListener("DOMContentLoaded", () => {
    Converter.init();
});

window.Converter = Converter;
