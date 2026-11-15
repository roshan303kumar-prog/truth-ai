/**
 * TRUTH AI — Image Verification Client Controller
 */

document.addEventListener("DOMContentLoaded", () => {
    const dropzone = document.getElementById("image-dropzone");
    const fileInput = document.getElementById("image-file-input");
    const previewContainer = document.getElementById("image-preview-container");
    const previewImg = document.getElementById("image-preview");
    const previewName = document.getElementById("preview-filename");
    const previewSize = document.getElementById("preview-filesize");
    const verifyBtn = document.getElementById("image-verify-btn");
    const progressOverlay = document.getElementById("image-analysis-progress");
    const resultContainer = document.getElementById("image-result-container");
    const stepItems = document.querySelectorAll("#image-analysis-progress .progress-step-item");

    let selectedFile = null;

    if (!dropzone || !fileInput) return;

    // Dropzone events
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
        const validExtensions = ["jpg", "jpeg", "png", "webp"];
        const ext = file.name.split(".").pop().toLowerCase();

        if (!validExtensions.includes(ext)) {
            alert(`Unsupported format: .${ext}. Please upload JPG, JPEG, PNG, or WEBP.`);
            return;
        }

        if (file.size > 10 * 1024 * 1024) {
            alert("File exceeds 10MB limit. Please upload a smaller image.");
            return;
        }

        selectedFile = file;
        previewName.textContent = file.name;
        previewSize.textContent = `${(file.size / (1024 * 1024)).toFixed(2)} MB`;

        const reader = new FileReader();
        reader.onload = (e) => {
            previewImg.src = e.target.result;
            previewContainer.style.display = "block";
            verifyBtn.disabled = false;
        };
        reader.readAsDataURL(file);
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
        }, 650);

        const formData = new FormData();
        formData.append("image", selectedFile);

        try {
            const response = await fetch("/api/verify-image", {
                method: "POST",
                body: formData,
            });

            clearInterval(stepInterval);
            stepItems.forEach(item => item.classList.add("completed"));

            const data = await response.json();
            progressOverlay.style.display = "none";
            verifyBtn.disabled = false;

            if (response.ok && data.success) {
                renderImageResult(data);
                resultContainer.style.display = "block";
                resultContainer.scrollIntoView({ behavior: "smooth", block: "start" });
            } else {
                alert(data.error || "Image analysis failed.");
            }
        } catch (err) {
            clearInterval(stepInterval);
            progressOverlay.style.display = "none";
            verifyBtn.disabled = false;
            console.error("Image verification client error:", err);
            alert("Analysis notice: " + (err.message || "Failed to parse response."));
        }
    });
});

function renderImageResult(data) {
    const verdictBadge = document.getElementById("img-verdict-badge");
    const verdictIcon = document.getElementById("img-verdict-icon");
    const verdictText = document.getElementById("img-verdict-text");
    const detectedTypeBadge = document.getElementById("img-detected-type");
    const confidenceScore = document.getElementById("img-confidence-score");
    const confidenceBar = document.getElementById("img-confidence-bar");
    const explanationText = document.getElementById("img-explanation-text");
    const originalDisplay = document.getElementById("img-original-display");
    const elaDisplay = document.getElementById("img-ela-display");
    const elaNotes = document.getElementById("img-ela-notes");
    const metaTable = document.getElementById("img-metadata-table");
    const aiRiskScore = document.getElementById("img-ai-risk-score");
    const aiAssessment = document.getElementById("img-ai-assessment");
    const aiIndicators = document.getElementById("img-ai-indicators");
    const ocrText = document.getElementById("img-ocr-text");
    const fullReportLink = document.getElementById("img-full-report-link");

    // Verdict
    const badgeClass = typeof getBadgeClass === "function" ? getBadgeClass(data.verdict) : "badge-unverified";
    const iconClass = typeof getVerdictIcon === "function" ? getVerdictIcon(data.verdict) : "fa-circle-info";
    
    if (verdictBadge) verdictBadge.className = `verdict-badge ${badgeClass}`;
    if (verdictIcon) verdictIcon.className = `fa-solid ${iconClass}`;
    if (verdictText) verdictText.textContent = data.verdict;

    if (detectedTypeBadge) {
        const dType = data.image_properties?.detected_type || data.ai_generation_assessment?.detected_modality || "Image";
        detectedTypeBadge.innerHTML = `<i class="fa-solid fa-layer-group me-1"></i> ${escapeHtml(dType)}`;
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

    // Side-by-side images
    if (data.saved_filename && originalDisplay) {
        originalDisplay.src = `/uploads/images/${data.saved_filename}`;
    }
    if (data.ela_image_filename && elaDisplay) {
        elaDisplay.src = `/uploads/ela/${data.ela_image_filename}`;
    }
    if (data.ela_analysis && elaNotes) {
        elaNotes.textContent = data.ela_analysis.notes || `Max variance: ${data.ela_analysis.max_difference}`;
    }

    // Metadata table
    const meta = data.metadata_findings || {};
    if (metaTable) {
        metaTable.innerHTML = `
            <tr><td><strong>Camera Make / Model:</strong></td><td>${meta.camera_make || "Unknown"} / ${meta.camera_model || "Unknown"}</td></tr>
            <tr><td><strong>Software Used:</strong></td><td><span class="${meta.detected_editor ? 'text-warning font-monospace' : ''}">${meta.software || "None recorded"}</span></td></tr>
            <tr><td><strong>Original Timestamp:</strong></td><td>${meta.datetime_original || "Not recorded"}</td></tr>
            <tr><td><strong>Color Space:</strong></td><td>${meta.color_space || "sRGB"}</td></tr>
            <tr><td><strong>GPS Coordinates:</strong></td><td>${Object.keys(meta.gps_info || {}).length > 0 ? "Geotagging present" : "None"}</td></tr>
            <tr><td><strong>Resolution / Dimensions:</strong></td><td>${data.image_properties?.dimensions || "N/A"} (${data.image_properties?.format || "N/A"})</td></tr>
        `;
    }

    // AI Generation assessment
    const ai = data.ai_generation_assessment || {};
    if (aiRiskScore) aiRiskScore.textContent = `${ai.ai_probability_score || 0}%`;
    if (aiAssessment) aiAssessment.textContent = ai.assessment || "Inconclusive";
    if (aiIndicators) {
        aiIndicators.innerHTML = "";
        (ai.indicators || []).forEach(ind => {
            const li = document.createElement("li");
            li.textContent = ind;
            aiIndicators.appendChild(li);
        });
    }

    // OCR findings
    if (ocrText) ocrText.textContent = data.ocr_findings?.extracted_text || "No text identified in the image.";

    if (data.report_id && fullReportLink) {
        fullReportLink.href = `/report/${data.report_id}`;
        fullReportLink.style.display = "inline-flex";
    }
}
