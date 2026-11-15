/**
 * TRUTH AI — Video Verification Client Controller
 */

document.addEventListener("DOMContentLoaded", () => {
    const dropzone = document.getElementById("video-dropzone");
    const fileInput = document.getElementById("video-file-input");
    const previewContainer = document.getElementById("video-preview-container");
    const videoPlayer = document.getElementById("video-player");
    const previewName = document.getElementById("video-preview-filename");
    const previewSize = document.getElementById("video-preview-filesize");
    const verifyBtn = document.getElementById("video-verify-btn");
    const progressOverlay = document.getElementById("video-analysis-progress");
    const resultContainer = document.getElementById("video-result-container");
    const stepItems = document.querySelectorAll("#video-analysis-progress .progress-step-item");

    let selectedFile = null;

    if (!dropzone || !fileInput) return;

    dropzone.addEventListener("click", () => fileInput.click());
    dropzone.addEventListener("dragover", (e) => {
        e.preventDefault();
        dropzone.classList.add("dragover");
    });
    dropzone.addEventListener("dragleave", () => dropzone.classList.remove("dragover"));
    dropzone.addEventListener("drop", (e) => {
        e.preventDefault();
        dropzone.classList.remove("dragover");
        if (e.dataTransfer.files && e.dataTransfer.files[0]) {
            handleFileSelect(e.dataTransfer.files[0]);
        }
    });

    fileInput.addEventListener("change", (e) => {
        if (e.target.files && e.target.files[0]) {
            handleFileSelect(e.target.files[0]);
        }
    });

    function handleFileSelect(file) {
        const validExtensions = ["mp4", "webm", "avi", "mov"];
        const ext = file.name.split(".").pop().toLowerCase();

        if (!validExtensions.includes(ext)) {
            alert(`Unsupported format: .${ext}. Allowed: MP4, WEBM, AVI, MOV.`);
            return;
        }

        if (file.size > 50 * 1024 * 1024) {
            alert("Video exceeds 50MB limit. Please upload a shorter clip.");
            return;
        }

        selectedFile = file;
        previewName.textContent = file.name;
        previewSize.textContent = `${(file.size / (1024 * 1024)).toFixed(2)} MB`;

        const fileURL = URL.createObjectURL(file);
        videoPlayer.src = fileURL;
        previewContainer.style.display = "block";
        verifyBtn.disabled = false;
    }

    verifyBtn.addEventListener("click", async () => {
        if (!selectedFile) return;

        verifyBtn.disabled = true;
        progressOverlay.style.display = "block";
        resultContainer.style.display = "none";

        let currentStep = 0;
        const stepInterval = setInterval(() => {
            if (currentStep < stepItems.length) {
                stepItems.forEach((item, idx) => {
                    item.classList.remove("active");
                    if (idx < currentStep) item.classList.add("completed");
                });
                stepItems[currentStep].classList.add("active");
                currentStep++;
            }
        }, 700);

        const formData = new FormData();
        formData.append("video", selectedFile);

        try {
            const response = await fetch("/api/verify-video", {
                method: "POST",
                body: formData,
            });

            clearInterval(stepInterval);
            stepItems.forEach(item => item.classList.add("completed"));

            const data = await response.json();
            progressOverlay.style.display = "none";
            verifyBtn.disabled = false;

            if (response.ok && data.success) {
                renderVideoResult(data);
                resultContainer.style.display = "block";
                resultContainer.scrollIntoView({ behavior: "smooth", block: "start" });
            } else {
                alert(data.error || "Video analysis failed.");
            }
        } catch (err) {
            clearInterval(stepInterval);
            progressOverlay.style.display = "none";
            verifyBtn.disabled = false;
            console.error("Video verification client error:", err);
            alert("Analysis notice: " + (err.message || "Failed to parse response."));
        }
    });
});

function renderVideoResult(data) {
    const verdictBadge = document.getElementById("vid-verdict-badge");
    const verdictIcon = document.getElementById("vid-verdict-icon");
    const verdictText = document.getElementById("vid-verdict-text");
    const detectedTypeBadge = document.getElementById("vid-detected-type");
    const confidenceScore = document.getElementById("vid-confidence-score");
    const confidenceBar = document.getElementById("vid-confidence-bar");
    const explanationText = document.getElementById("vid-explanation-text");
    const propsTable = document.getElementById("vid-props-table");
    const frameGallery = document.getElementById("vid-frame-gallery");
    const anomaliesList = document.getElementById("vid-anomalies-list");
    const ocrList = document.getElementById("vid-ocr-list");
    const audioTranscript = document.getElementById("vid-audio-transcript");
    const fullReportLink = document.getElementById("vid-full-report-link");

    // Verdict
    const badgeClass = typeof getBadgeClass === "function" ? getBadgeClass(data.verdict) : "badge-unverified";
    const iconClass = typeof getVerdictIcon === "function" ? getVerdictIcon(data.verdict) : "fa-circle-info";
    
    if (verdictBadge) verdictBadge.className = `verdict-badge ${badgeClass}`;
    if (verdictIcon) verdictIcon.className = `fa-solid ${iconClass}`;
    if (verdictText) verdictText.textContent = data.verdict;

    // Detected Modality Badge
    const detectedType = data.detected_type || data.video_properties?.detected_type || "Standard Video Stream";
    if (detectedTypeBadge) {
        let typeIcon = "fa-film";
        let typeColor = "text-info border-info";
        if (detectedType.includes("Authentic")) {
            typeIcon = "fa-camera";
            typeColor = "text-success border-success";
        } else if (detectedType.includes("Manipulated") || detectedType.includes("Filter")) {
            typeIcon = "fa-masks-theater";
            typeColor = "text-danger border-danger";
        } else if (detectedType.includes("Synthetic") || detectedType.includes("AI")) {
            typeIcon = "fa-wand-magic-sparkles";
            typeColor = "text-warning border-warning";
        } else if (detectedType.includes("Edited") || detectedType.includes("Spliced")) {
            typeIcon = "fa-scissors";
            typeColor = "text-warning border-warning";
        }
        detectedTypeBadge.className = `badge bg-dark bg-opacity-75 ${typeColor} border py-2 px-3`;
        detectedTypeBadge.innerHTML = `<i class="fa-solid ${typeIcon} me-1"></i> ${escapeHtml(detectedType)}`;
    }

    // Confidence
    const score = Math.round(data.confidence_score || 0);
    if (confidenceScore) confidenceScore.textContent = `${score}%`;
    if (confidenceBar) {
        confidenceBar.style.width = `${score}%`;
        confidenceBar.style.backgroundColor = score >= 75 ? "#10b981" : (score >= 50 ? "#f59e0b" : "#3b82f6");
    }

    // Explanation
    if (explanationText) explanationText.textContent = data.explanation;

    // Properties table
    const props = data.video_properties || {};
    const avgSat = props.avg_saturation !== undefined ? `${props.avg_saturation}%` : "N/A";
    const satComment = props.avg_saturation < 3.0 ? " <span class='badge bg-danger ms-1'>Desaturated / Filtered</span>" : (props.avg_saturation > 25.0 ? " <span class='badge bg-success ms-1'>Natural Chromaticity</span>" : "");
    const correl = props.temporal_correlation || "N/A";

    if (propsTable) {
        propsTable.innerHTML = `
            <tr><td><strong>Modality:</strong></td><td class="text-white">${escapeHtml(detectedType)}</td></tr>
            <tr><td><strong>Duration:</strong></td><td>${props.duration || "N/A"}</td></tr>
            <tr><td><strong>Resolution:</strong></td><td>${props.resolution || "N/A"}</td></tr>
            <tr><td><strong>FPS:</strong></td><td>${props.fps || "N/A"}</td></tr>
            <tr><td><strong>Color Saturation:</strong></td><td>${avgSat}${satComment}</td></tr>
            <tr><td><strong>Motion Continuity:</strong></td><td>${correl}</td></tr>
            <tr><td><strong>Total Video Frames:</strong></td><td>${props.total_frames || "N/A"}</td></tr>
            <tr><td><strong>Keyframes Sampled:</strong></td><td>${props.analyzed_frames_count || 0}</td></tr>
        `;
    }

    // Keyframe Gallery
    if (frameGallery) {
        frameGallery.innerHTML = "";
        const frames = data.analyzed_frames || [];
        if (frames.length > 0) {
            frames.forEach(f => {
                const card = document.createElement("div");
                card.className = "frame-thumbnail-card";
                card.innerHTML = `
                    <img src="/uploads/videos/frames/${f.filename}" alt="Keyframe at ${f.timestamp}" loading="lazy">
                    <div class="frame-meta-tag">
                        <span>${f.timestamp}</span>
                        <span title="Focal Sharpness">${f.sharpness_score}</span>
                    </div>
                `;
                frameGallery.appendChild(card);
            });
        } else {
            frameGallery.innerHTML = `<p class="text-secondary small">No keyframes could be saved.</p>`;
        }
    }

    // Temporal anomalies & Forensic Indicators
    if (anomaliesList) {
        anomaliesList.innerHTML = "";
        const indicators = data.manipulation_indicators || [];
        const anomalies = data.temporal_analysis?.anomalies || [];
        const combined = [...indicators, ...anomalies.filter(a => !indicators.includes(a))];

        if (combined.length > 0) {
            combined.forEach(a => {
                const li = document.createElement("li");
                li.className = "text-warning small mb-1";
                li.innerHTML = `<i class="fa-solid fa-triangle-exclamation me-1"></i> ${escapeHtml(a)}`;
                anomaliesList.appendChild(li);
            });
        } else {
            anomaliesList.innerHTML = `<li class="text-success small"><i class="fa-solid fa-check me-1"></i> Stable focal transitions, natural lighting continuity, and authentic optical camera geometry across all sampled intervals.</li>`;
        }
    }

    // OCR findings
    if (ocrList) {
        ocrList.innerHTML = "";
        const ocrs = data.ocr_findings || [];
        if (ocrs.length > 0) {
            ocrs.forEach(o => {
                const li = document.createElement("li");
                li.className = "small mb-1";
                li.innerHTML = `<strong>[${o.timestamp}]</strong> ${escapeHtml(o.detected_text)}`;
                ocrList.appendChild(li);
            });
        } else {
            ocrList.innerHTML = `<li class="text-secondary small">No on-screen text or chyrons recognized in sampled keyframes.</li>`;
        }
    }

    // Audio status
    if (audioTranscript) {
        audioTranscript.textContent = data.audio_transcript?.status || "Audio inspection completed.";
    }

    if (data.report_id && fullReportLink) {
        fullReportLink.href = `/report/${data.report_id}`;
        fullReportLink.style.display = "inline-flex";
    }
}
