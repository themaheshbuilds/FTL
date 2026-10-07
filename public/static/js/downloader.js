/**
 * LinkForge - Downloader Service (Frontend)
 * Responsible for requesting file generation and initiating downloads.
 */

const Downloader = {
    async requestGeneration(url, outputFormat, quality = "best", customFilename = "", includeCaption = false) {
        try {
            const response = await fetch("/api/generate", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    url: url,
                    output_format: outputFormat,
                    quality: quality,
                    custom_filename: customFilename,
                    include_caption: includeCaption
                })
            });

            const contentType = response.headers.get("content-type") || "";
            if (!contentType.includes("application/json")) {
                const text = await response.text();
                throw new Error(text || `Server error (${response.status})`);
            }

            const data = await response.json();

            if (!response.ok || !data.success) {
                const message = (data.error && data.error.message) || "Failed to generate file.";
                throw new Error(message);
            }

            return data;
        } catch (err) {
            console.error("Generation error:", err);
            throw err;
        }
    },

    triggerDownload(fileId) {
        // Direct download using safe URL
        window.location.href = `/download/${encodeURIComponent(fileId)}`;
    }
};

window.Downloader = Downloader;
