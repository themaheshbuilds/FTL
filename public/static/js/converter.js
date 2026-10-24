/**
 * LinkForge - File Converter Hub Controller
 * Handles local file upload, tool selection, format configuration, and email delivery.
 */

const ConverterApp = {
    activeTool: null,
    selectedFiles: [],
    currentFileId: null,

    tools: [
        {
            id: "pdf_to_images",
            title: "PDF to Images",
            category: "docs",
            icon: "&#x1F4C4;",
            badge: "PDF &#x2192; JPG/PNG",
            desc: "Extract pages of any PDF into high-res JPG or PNG images inside a ZIP archive.",
            accept: ".pdf",
            multiple: false,
            formats: [
                { value: "jpg", label: "JPG Images in ZIP (.zip)" },
                { value: "png", label: "PNG Images in ZIP (.zip)" }
            ]
        },
        {
            id: "images_to_pdf",
            title: "Images to PDF",
            category: "docs",
            icon: "&#x1F5BC;&#xFE0F;",
            badge: "Images &#x2192; PDF",
            desc: "Combine multiple JPG, PNG, or WebP images into a single multi-page PDF document.",
            accept: ".jpg,.jpeg,.png,.webp,.bmp",
            multiple: true,
            formats: [
                { value: "pdf", label: "PDF Document (.pdf)" }
            ]
        },
        {
            id: "video_to_audio",
            title: "Video to Audio",
            category: "media",
            icon: "&#x1F3A7;",
            badge: "Video &#x2192; MP3/M4A",
            desc: "Extract pristine audio track from any MP4, MKV, WebM, MOV, or AVI video.",
            accept: ".mp4,.mkv,.webm,.mov,.avi,.flv",
            multiple: false,
            formats: [
                { value: "mp3", label: "MP3 Audio (192 kbps)" },
                { value: "m4a", label: "M4A Audio (AAC)" }
            ]
        },
        {
            id: "docx_to_pdf",
            title: "Word (DOCX) to PDF",
            category: "docs",
            icon: "&#x1F4DD;",
            badge: "DOCX &#x2192; PDF",
            desc: "Convert Word documents (.docx) to PDF with crisp formatting and typography.",
            accept: ".docx,.doc",
            multiple: false,
            formats: [
                { value: "pdf", label: "PDF Document (.pdf)" }
            ]
        },
        {
            id: "pdf_to_docx",
            title: "PDF to Word (DOCX)",
            category: "docs",
            icon: "&#x1F4CB;",
            badge: "PDF &#x2192; DOCX",
            desc: "Extract text and layout from PDF into an editable Microsoft Word document.",
            accept: ".pdf",
            multiple: false,
            formats: [
                { value: "docx", label: "Word Document (.docx)" }
            ]
        },
        {
            id: "video_converter",
            title: "Video Converter",
            category: "media",
            icon: "&#x1F3AC;",
            badge: "Video &#x2192; MP4/MKV",
            desc: "Transcode video files across MP4, MKV, and WebM container formats.",
            accept: ".mp4,.mkv,.webm,.mov,.avi,.flv",
            multiple: false,
            formats: [
                { value: "mp4", label: "MP4 Video (H.264)" },
                { value: "mkv", label: "MKV Video (Lossless)" },
                { value: "webm", label: "WebM Video" }
            ]
        },
        {
            id: "image_converter",
            title: "Image Converter",
            category: "images",
            icon: "&#x1F3A8;",
            badge: "PNG/JPG &#x2192; WebP",
            desc: "Convert and optimize images between PNG, JPG, and lightweight WebP formats.",
            accept: ".png,.jpg,.jpeg,.webp,.bmp",
            multiple: false,
            formats: [
                { value: "webp", label: "WebP (Ultra Compressed)" },
                { value: "png", label: "PNG (Lossless)" },
                { value: "jpg", label: "JPG (Standard)" }
            ]
        }
    ],

    init() {
        this.renderToolGrid("all");
        this.selectTool(this.tools[0].id);
        const fileInput = document.getElementById("converter-file-input");
        if (fileInput) {
            fileInput.accept = ".pdf,.docx,.doc,.jpg,.jpeg,.png,.webp,.bmp,.mp4,.mkv,.webm,.mov,.avi,.flv";
            fileInput.multiple = true;
        }
        this.bindEvents();
    },

    bindEvents() {
        // Category filters
        document.querySelectorAll(".category-tab").forEach(tab => {
            tab.addEventListener("click", () => {
                document.querySelectorAll(".category-tab").forEach(t => t.classList.remove("active"));
                tab.classList.add("active");
                const cat = tab.getAttribute("data-category") || "all";
                this.renderToolGrid(cat);
            });
        });

        // Dropzone interactions
        const dropzone = document.getElementById("converter-dropzone");
        const fileInput = document.getElementById("converter-file-input");
        const browseBtn = document.getElementById("converter-browse-btn");

        if (browseBtn && fileInput) {
            browseBtn.addEventListener("click", (e) => {
                e.stopPropagation();
                fileInput.click();
            });
        }

        if (dropzone && fileInput) {
            dropzone.addEventListener("click", () => fileInput.click());

            dropzone.addEventListener("dragover", (e) => {
                e.preventDefault();
                dropzone.classList.add("dragover");
            });

            dropzone.addEventListener("dragleave", () => {
                dropzone.classList.remove("dragover");
            });

            dropzone.addEventListener("drop", (e) => {
                e.preventDefault();
                dropzone.classList.remove("dragover");
                if (e.dataTransfer && e.dataTransfer.files) {
                    this.handleFiles(Array.from(e.dataTransfer.files));
                }
            });

            fileInput.addEventListener("change", (e) => {
                if (e.target.files) {
                    this.handleFiles(Array.from(e.target.files));
                }
            });
        }

        // Convert action button
        const btnConvert = document.getElementById("btn-start-convert");
        if (btnConvert) {
            btnConvert.addEventListener("click", () => this.startConversion());
        }

        // Reset buttons
        const btnResetConfig = document.getElementById("btn-reset-converter-config");
        const btnResetSuccess = document.getElementById("btn-reset-converter-success");
        const btnResetError = document.getElementById("btn-reset-converter-error");

        if (btnResetConfig) btnResetConfig.addEventListener("click", () => this.resetFiles());
        if (btnResetSuccess) btnResetSuccess.addEventListener("click", () => this.resetFiles());
        if (btnResetError) btnResetError.addEventListener("click", () => this.showView("upload-view"));

        // Email delivery toggle
        const emailToggle = document.getElementById("conv-email-toggle-btn");
        const emailWidget = document.getElementById("conv-email-widget");
        const emailSendBtn = document.getElementById("conv-email-send-btn");

        if (emailToggle && emailWidget) {
            emailToggle.addEventListener("click", () => {
                emailWidget.classList.toggle("open");
            });
        }

        if (emailSendBtn) {
            emailSendBtn.addEventListener("click", () => this.sendEmail());
        }

        // Modals
        this.initModals();
    },

    renderToolGrid(category) {
        const grid = document.getElementById("converter-tools-grid");
        if (!grid) return;

        grid.innerHTML = "";
        const filtered = category === "all" ? this.tools : this.tools.filter(t => t.category === category);

        filtered.forEach(tool => {
            const slug = tool.id.replace(/_/g, '-');
            const card = document.createElement("div");
            card.className = `tool-card ${this.activeTool && this.activeTool.id === tool.id ? "active" : ""}`;
            card.setAttribute("data-tool-id", tool.id);
            card.innerHTML = `
                <div class="tool-card-icon-box">${tool.icon}</div>
                <div class="tool-card-title">${tool.title}</div>
                <div class="tool-card-badge">${tool.badge}</div>
                <div class="tool-card-desc">${tool.desc}</div>
                <div class="tool-card-actions">
                    <span class="tool-select-tag">Use Here</span>
                    <a href="/converter/${slug}" class="tool-page-link" onclick="event.stopPropagation();" title="Open dedicated page for ${tool.title}">
                        Dedicated Page &#x2197;
                    </a>
                </div>
            `;

            card.addEventListener("click", () => {
                this.selectTool(tool.id);
            });

            grid.appendChild(card);
        });
    },

    selectTool(toolId) {
        const tool = this.tools.find(t => t.id === toolId);
        if (!tool) return;

        this.activeTool = tool;

        // Highlight in grid
        document.querySelectorAll(".tool-card").forEach(c => {
            c.classList.toggle("active", c.getAttribute("data-tool-id") === toolId);
        });

        // Update Dropzone hints
        const toolBadge = document.getElementById("active-tool-badge");
        const dropzoneTitle = document.getElementById("active-dropzone-title");
        const dropzoneSub = document.getElementById("active-dropzone-sub");

        if (toolBadge) toolBadge.innerHTML = `${tool.icon} ${tool.title}`;
        if (dropzoneTitle) dropzoneTitle.textContent = `Upload files for ${tool.title}`;
        if (dropzoneSub) dropzoneSub.textContent = `Supported formats: ${tool.accept.replace(/,/g, ", ")}`;

        // Populate format select
        const formatSelect = document.getElementById("converter-format-select");
        if (formatSelect) {
            formatSelect.innerHTML = "";
            tool.formats.forEach(f => {
                const opt = document.createElement("option");
                opt.value = f.value;
                opt.textContent = f.label;
                formatSelect.appendChild(opt);
            });
        }

        // If files already selected, re-render
        if (this.selectedFiles.length > 0) {
            this.showView("config-view");
        }
    },

    detectToolForFiles(files) {
        if (!files || files.length === 0) return this.tools[0];
        const firstExt = (files[0].name.split('.').pop() || "").toLowerCase();

        // 1. Images
        if (['jpg', 'jpeg', 'png', 'webp', 'bmp'].includes(firstExt)) {
            if (files.length > 1) {
                return this.tools.find(t => t.id === 'images_to_pdf') || this.tools.find(t => t.id === 'image_converter');
            }
            return this.tools.find(t => t.id === 'image_converter');
        }

        // 2. PDF
        if (firstExt === 'pdf') {
            return this.tools.find(t => t.id === 'pdf_to_images') || this.tools.find(t => t.id === 'pdf_to_docx');
        }

        // 3. Word Documents
        if (['docx', 'doc'].includes(firstExt)) {
            return this.tools.find(t => t.id === 'docx_to_pdf');
        }

        // 4. Video files
        if (['mp4', 'mkv', 'webm', 'mov', 'avi', 'flv'].includes(firstExt)) {
            return this.tools.find(t => t.id === 'video_to_audio') || this.tools.find(t => t.id === 'video_converter');
        }

        return this.activeTool || this.tools[0];
    },

    handleFiles(files) {
        if (!files || files.length === 0) return;

        // Automatically detect best converter tool based on uploaded file type
        const autoTool = this.detectToolForFiles(files);
        if (autoTool) {
            this.selectTool(autoTool.id);
        }

        if (this.activeTool && !this.activeTool.multiple) {
            this.selectedFiles = [files[0]];
        } else {
            this.selectedFiles = files;
        }

        this.renderStagedFiles();
        this.showView("config-view");
    },

    renderStagedFiles() {
        const container = document.getElementById("staged-files-list");
        if (!container) return;

        container.innerHTML = "";
        this.selectedFiles.forEach((file, index) => {
            const sizeStr = (file.size / (1024 * 1024)).toFixed(2) + " MB";
            const row = document.createElement("div");
            row.className = "staged-file-card";
            row.innerHTML = `
                <span class="staged-file-icon">${this.activeTool ? this.activeTool.icon : "&#x1F4C1;"}</span>
                <span class="staged-file-name">${file.name}</span>
                <span class="staged-file-size">${sizeStr}</span>
                <button type="button" class="staged-file-remove" title="Remove file">&times;</button>
            `;

            row.querySelector(".staged-file-remove").addEventListener("click", () => {
                this.selectedFiles.splice(index, 1);
                if (this.selectedFiles.length === 0) {
                    this.showView("upload-view");
                } else {
                    this.renderStagedFiles();
                }
            });

            container.appendChild(row);
        });
    },

    resetFiles() {
        this.selectedFiles = [];
        const fileInput = document.getElementById("converter-file-input");
        if (fileInput) fileInput.value = "";
        this.showView("upload-view");
    },

    showView(viewName) {
        const views = ["upload-view", "config-view", "processing-view", "success-view", "error-view"];
        views.forEach(v => {
            const el = document.getElementById(`converter-${v}`);
            if (el) {
                if (v === viewName) {
                    el.classList.remove("hidden");
                } else {
                    el.classList.add("hidden");
                }
            }
        });
    },

    async startConversion() {
        if (!this.activeTool || this.selectedFiles.length === 0) return;

        this.showView("processing-view");

        const formatSelect = document.getElementById("converter-format-select");
        const customFilenameInput = document.getElementById("converter-custom-filename");

        const outputFormat = formatSelect ? formatSelect.value : "";
        const customFilename = customFilenameInput ? customFilenameInput.value.trim() : "";

        const formData = new FormData();
        formData.append("conversion_type", this.activeTool.id);
        formData.append("output_format", outputFormat);
        formData.append("custom_filename", customFilename);

        this.selectedFiles.forEach(file => {
            formData.append("files", file);
        });

        try {
            const response = await fetch("/api/convert", {
                method: "POST",
                body: formData
            });

            const data = await response.json();

            if (!response.ok || !data.success) {
                const msg = (data.error && data.error.message) || "Conversion failed. Please try again.";
                this.showError(msg);
                return;
            }

            this.currentFileId = data.file_id;
            this.showSuccess(data);
        } catch (err) {
            this.showError("Network interruption occurred while converting file.");
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

    showSuccess(data) {
        const fnEl = document.getElementById("conv-success-filename");
        const szEl = document.getElementById("conv-success-filesize");
        const fmtEl = document.getElementById("conv-success-format");
        const dlBtn = document.getElementById("conv-direct-download-btn");

        const filename = data.filename || "converted_file";
        if (fnEl) fnEl.textContent = filename;
        if (szEl) szEl.textContent = data.size_formatted || (data.filesize ? `${(data.filesize / (1024 * 1024)).toFixed(2)} MB` : "Ready");
        if (fmtEl) fmtEl.textContent = (document.getElementById("converter-format-select")?.value || "FILE").toUpperCase();

        const rawUrl = data.data_url || `/download/${encodeURIComponent(data.file_id)}`;
        const downloadUrl = data.data_url ? this.dataUrlToBlobUrl(data.data_url) : rawUrl;

        if (dlBtn) {
            dlBtn.href = downloadUrl;
            dlBtn.setAttribute("download", filename);
        }

        // AUTO-DOWNLOAD TRIGGER: Instantly downloads converted file to user's computer via Blob Object URL
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

        // Reset email widget state
        const emailWidget = document.getElementById("conv-email-widget");
        const emailInput = document.getElementById("conv-email-input");
        const emailStatus = document.getElementById("conv-email-status-message");
        const emailSendBtn = document.getElementById("conv-email-send-btn");

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

        const emailInput = document.getElementById("conv-email-input");
        const emailStatus = document.getElementById("conv-email-status-message");
        const emailSendBtn = document.getElementById("conv-email-send-btn");

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
                    emailStatus.textContent = (data.error && data.error.message) || "Could not deliver email.";
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
        const errorEl = document.getElementById("conv-error-message");
        if (errorEl) errorEl.textContent = msg || "An error occurred during conversion.";
        this.showView("error-view");
    },

    initModals() {
        const openAbout = document.getElementById("open-about-modal");
        const closeAbout = document.getElementById("close-about-modal");
        const aboutModal = document.getElementById("about-modal");

        const openFormats = document.getElementById("open-formats-modal");
        const closeFormats = document.getElementById("close-formats-modal");
        const formatsModal = document.getElementById("formats-modal");

        if (openAbout && aboutModal) {
            openAbout.addEventListener("click", () => aboutModal.classList.add("show"));
        }
        if (closeAbout && aboutModal) {
            closeAbout.addEventListener("click", () => aboutModal.classList.remove("show"));
        }
        if (openFormats && formatsModal) {
            openFormats.addEventListener("click", () => formatsModal.classList.add("show"));
        }
        if (closeFormats && formatsModal) {
            closeFormats.addEventListener("click", () => formatsModal.classList.remove("show"));
        }

        [aboutModal, formatsModal].forEach(modal => {
            if (modal) {
                modal.addEventListener("click", (e) => {
                    if (e.target === modal) modal.classList.remove("show");
                });
            }
        });
    }
};

document.addEventListener("DOMContentLoaded", () => {
    ConverterApp.init();
});
