/**
 * LinkForge - Dedicated Tool Converter Controller
 * Used on /converter/<tool_slug> pages.
 */

const DedicatedToolConverter = {
    selectedFiles: [],
    currentFileId: null,

    init() {
        this.bindEvents();
        this.initModals();
    },

    bindEvents() {
        const dropzone = document.getElementById("tool-dropzone");
        const fileInput = document.getElementById("tool-file-input");
        const browseBtn = document.getElementById("tool-browse-btn");

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

        // Start Conversion
        const btnConvert = document.getElementById("btn-start-tool-convert");
        if (btnConvert) {
            btnConvert.addEventListener("click", () => this.startConversion());
        }

        // Reset buttons
        const btnResetConfig = document.getElementById("btn-reset-tool-config");
        const btnResetSuccess = document.getElementById("btn-reset-tool-success");
        const btnResetError = document.getElementById("btn-reset-tool-error");

        if (btnResetConfig) btnResetConfig.addEventListener("click", () => this.resetFiles());
        if (btnResetSuccess) btnResetSuccess.addEventListener("click", () => this.resetFiles());
        if (btnResetError) btnResetError.addEventListener("click", () => this.showView("upload-view"));

        // Email delivery toggle
        const emailToggle = document.getElementById("tool-email-toggle-btn");
        const emailWidget = document.getElementById("tool-email-widget");
        const emailSendBtn = document.getElementById("tool-email-send-btn");

        if (emailToggle && emailWidget) {
            emailToggle.addEventListener("click", () => {
                emailWidget.classList.toggle("open");
            });
        }

        if (emailSendBtn) {
            emailSendBtn.addEventListener("click", () => this.sendEmail());
        }
    },

    handleFiles(files) {
        if (!files || files.length === 0) return;

        if (window.TOOL_CONFIG && !window.TOOL_CONFIG.multiple) {
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
                <span class="staged-file-icon">&#x1F4C1;</span>
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
        const fileInput = document.getElementById("tool-file-input");
        if (fileInput) fileInput.value = "";
        this.showView("upload-view");
    },

    showView(viewName) {
        const views = ["upload-view", "config-view", "processing-view", "success-view", "error-view"];
        views.forEach(v => {
            const el = document.getElementById(`tool-${v}`);
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
        if (this.selectedFiles.length === 0 || !window.TOOL_CONFIG) return;

        this.showView("processing-view");

        const formatSelect = document.getElementById("tool-format-select");
        const customFilenameInput = document.getElementById("tool-custom-filename");

        const outputFormat = formatSelect ? formatSelect.value : "";
        const customFilename = customFilenameInput ? customFilenameInput.value.trim() : "";

        const formData = new FormData();
        formData.append("conversion_type", window.TOOL_CONFIG.id);
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
                const msg = (data.error && data.error.message) || "Conversion failed. Please verify your file.";
                this.showError(msg);
                return;
            }

            this.currentFileId = data.file_id;
            this.showSuccess(data, outputFormat);
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

    showSuccess(data, outputFormat) {
        const fnEl = document.getElementById("tool-success-filename");
        const szEl = document.getElementById("tool-success-filesize");
        const fmtEl = document.getElementById("tool-success-format");
        const dlBtn = document.getElementById("tool-direct-download-btn");

        const filename = data.filename || "converted_file";
        if (fnEl) fnEl.textContent = filename;
        if (szEl) szEl.textContent = data.size_formatted || (data.filesize ? `${(data.filesize / (1024 * 1024)).toFixed(2)} MB` : "Ready");
        if (fmtEl) fmtEl.textContent = (outputFormat || "FILE").toUpperCase();

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
        const emailWidget = document.getElementById("tool-email-widget");
        const emailInput = document.getElementById("tool-email-input");
        const emailStatus = document.getElementById("tool-email-status-message");
        const emailSendBtn = document.getElementById("tool-email-send-btn");

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

        const emailInput = document.getElementById("tool-email-input");
        const emailStatus = document.getElementById("tool-email-status-message");
        const emailSendBtn = document.getElementById("tool-email-send-btn");

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
        const errorEl = document.getElementById("tool-error-message");
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

        if (openAbout && aboutModal) openAbout.addEventListener("click", () => aboutModal.classList.add("show"));
        if (closeAbout && aboutModal) closeAbout.addEventListener("click", () => aboutModal.classList.remove("show"));
        if (openFormats && formatsModal) openFormats.addEventListener("click", () => formatsModal.classList.add("show"));
        if (closeFormats && formatsModal) closeFormats.addEventListener("click", () => formatsModal.classList.remove("show"));

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
    DedicatedToolConverter.init();
});
