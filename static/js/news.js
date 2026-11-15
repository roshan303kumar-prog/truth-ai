/**
 * TRUTH AI — News & Claim Verification Client Controller
 */

document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("news-verify-form");
    if (!form) return;

    // Initialize Voice Features
    setupVoiceInput();
    setupVoiceExplanation();

    const claimInput = document.getElementById("claim-input");
    const submitBtn = document.getElementById("news-submit-btn");
    const progressOverlay = document.getElementById("analysis-progress");
    const resultContainer = document.getElementById("news-result-container");
    const stepItems = document.querySelectorAll(".progress-step-item");

    form.addEventListener("submit", async (e) => {
        e.preventDefault();
        const claim = claimInput.value.trim();
        if (!claim || claim.length < 5) {
            alert("Please enter a valid claim or news headline (min 5 characters).");
            claimInput.focus();
            return;
        }

        // Show progress overlay and disable button
        submitBtn.disabled = true;
        progressOverlay.style.display = "block";
        resultContainer.style.display = "none";

        // Animated step sequencer
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

        try {
            const response = await fetch("/api/verify-news", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ claim: claim }),
            });

            clearInterval(stepInterval);
            stepItems.forEach(item => item.classList.add("completed"));

            const data = await response.json();
            progressOverlay.style.display = "none";
            submitBtn.disabled = false;

            if (response.ok && data.success) {
                renderNewsResult(data);
                resultContainer.style.display = "block";
                resultContainer.scrollIntoView({ behavior: "smooth", block: "start" });
            } else {
                alert(data.error || "Verification failed. Please try again.");
            }
        } catch (err) {
            clearInterval(stepInterval);
            progressOverlay.style.display = "none";
            submitBtn.disabled = false;
            console.error(err);
            alert("A network error occurred while connecting to the verification engine.");
        }
    });
});

function getBadgeClass(verdict) {
    if (!verdict) return "badge-insufficient";
    if (verdict.includes("Supported") || verdict.includes("Authentic") || verdict.includes("Verified")) return "badge-supported";
    if (verdict.includes("False") || verdict.includes("Debunked") || verdict.includes("Sensational") || verdict.includes("War Claim")) return "badge-false";
    if (verdict.includes("Misleading")) return "badge-misleading";
    if (verdict.includes("Unverified")) return "badge-unverified";
    return "badge-insufficient";
}

function getVerdictIcon(verdict) {
    if (!verdict) return "fa-circle-info";
    if (verdict.includes("Supported") || verdict.includes("Authentic") || verdict.includes("Verified")) return "fa-circle-check";
    if (verdict.includes("False") || verdict.includes("Debunked") || verdict.includes("Sensational") || verdict.includes("War Claim")) return "fa-triangle-exclamation";
    if (verdict.includes("Misleading")) return "fa-triangle-exclamation";
    if (verdict.includes("Unverified")) return "fa-circle-question";
    return "fa-circle-info";
}

function renderNewsResult(data) {
    const verdictBadge = document.getElementById("res-verdict-badge");
    const verdictIcon = document.getElementById("res-verdict-icon");
    const verdictText = document.getElementById("res-verdict-text");
    const confidenceScore = document.getElementById("res-confidence-score");
    const confidenceBar = document.getElementById("res-confidence-bar");
    const explanationText = document.getElementById("res-explanation-text");
    const supportingList = document.getElementById("res-supporting-list");
    const contradictingList = document.getElementById("res-contradicting-list");
    const sourceLinksList = document.getElementById("res-sources-list");
    const limitationsList = document.getElementById("res-limitations-list");
    const fullReportBtn = document.getElementById("res-full-report-link");

    // Extracted Link Meta Box
    const linkMetaBox = document.getElementById("res-link-meta-box");
    const linkPublisher = document.getElementById("res-link-publisher");
    const linkType = document.getElementById("res-link-type");
    const linkTitle = document.getElementById("res-link-title");

    if (linkMetaBox && data.title && (data.publisher || data.host)) {
        linkMetaBox.style.display = "block";
        linkTitle.textContent = data.title;
        linkPublisher.textContent = `Source: ${data.publisher || data.host}`;
        if (linkType) {
            linkType.innerHTML = data.is_video ? '<i class="fa-brands fa-youtube me-1 text-danger"></i> Online Video' : '<i class="fa-solid fa-newspaper me-1 text-info"></i> News Article';
        }
    } else if (linkMetaBox) {
        linkMetaBox.style.display = "none";
    }

    // Verdict
    const badgeClass = getBadgeClass(data.verdict);
    verdictBadge.className = `verdict-badge ${badgeClass}`;
    verdictIcon.className = `fa-solid ${getVerdictIcon(data.verdict)}`;
    verdictText.textContent = data.verdict;

    // Confidence Calculation (Never NaN)
    const rawScore = Number(data.confidence_score ?? data.authenticity_score ?? 50);
    const score = isNaN(rawScore) ? 50 : Math.round(rawScore);
    confidenceScore.textContent = `${score}%`;
    confidenceBar.style.width = `${score}%`;
    if (data.verdict && (data.verdict.includes("Supported") || data.verdict.includes("Authentic") || data.verdict.includes("Verified"))) {
        confidenceBar.style.backgroundColor = "#10b981";
    } else if (data.verdict && (data.verdict.includes("False") || data.verdict.includes("Debunked") || data.verdict.includes("Sensational") || data.verdict.includes("War Claim"))) {
        confidenceBar.style.backgroundColor = "#ef4444";
    } else if (data.verdict && data.verdict.includes("Misleading")) {
        confidenceBar.style.backgroundColor = "#f59e0b";
    } else if (data.verdict && data.verdict.includes("Unverified")) {
        confidenceBar.style.backgroundColor = "#00e5ff";
    } else {
        confidenceBar.style.backgroundColor = "#94a3b8";
    }

    // Explanation
    explanationText.textContent = data.explanation;

    // Supporting Evidence
    supportingList.innerHTML = "";
    if (data.supporting_evidence && data.supporting_evidence.length > 0) {
        data.supporting_evidence.forEach(item => {
            const card = document.createElement("div");
            card.className = "p-3 mb-2 rounded bg-dark border border-secondary border-opacity-25";
            card.innerHTML = `
                <div class="d-flex justify-content-between align-items-center mb-1">
                    <span class="badge bg-success bg-opacity-25 text-success border border-success border-opacity-50">${escapeHtml(item.source)}</span>
                    <small class="text-secondary">${item.published_date || "Public Archive"}</small>
                </div>
                <h6 class="text-white mb-1">${escapeHtml(item.title)}</h6>
                <p class="text-secondary small mb-1">${escapeHtml(item.snippet)}</p>
                ${item.url ? `<a href="${encodeURI(item.url)}" target="_blank" rel="noopener noreferrer" class="small"><i class="fa-solid fa-arrow-up-right-from-square me-1"></i>View Primary Source</a>` : ""}
            `;
            supportingList.appendChild(card);
        });
    } else {
        supportingList.innerHTML = `<p class="text-secondary small italic">No explicit corroborating sources found matching this specific claim phrasing.</p>`;
    }

    // Contradicting Evidence
    contradictingList.innerHTML = "";
    if (data.contradicting_evidence && data.contradicting_evidence.length > 0) {
        data.contradicting_evidence.forEach(item => {
            const card = document.createElement("div");
            card.className = "p-3 mb-2 rounded bg-dark border border-danger border-opacity-25";
            card.innerHTML = `
                <div class="d-flex justify-content-between align-items-center mb-1">
                    <span class="badge bg-danger bg-opacity-25 text-danger border border-danger border-opacity-50">${escapeHtml(item.source)}</span>
                    <small class="text-secondary">${item.published_date || "Investigation"}</small>
                </div>
                <h6 class="text-white mb-1">${escapeHtml(item.title)}</h6>
                <p class="text-secondary small mb-1">${escapeHtml(item.snippet)}</p>
                ${item.url ? `<a href="${encodeURI(item.url)}" target="_blank" rel="noopener noreferrer" class="small text-danger"><i class="fa-solid fa-arrow-up-right-from-square me-1"></i>View Fact Check</a>` : ""}
            `;
            contradictingList.appendChild(card);
        });
    } else {
        contradictingList.innerHTML = `<p class="text-secondary small italic">No direct authoritative refutations or counter-evidence retrieved.</p>`;
    }

    // Direct Sources
    sourceLinksList.innerHTML = "";
    if (data.source_links && data.source_links.length > 0) {
        data.source_links.forEach(src => {
            const li = document.createElement("li");
            li.className = "mb-2";
            li.innerHTML = `
                <a href="${encodeURI(src.url)}" target="_blank" rel="noopener noreferrer" class="text-info">
                    <i class="fa-solid fa-link me-1"></i> ${escapeHtml(src.title || src.publisher)}
                </a>
                <span class="text-secondary small ms-2">(${escapeHtml(src.publisher)})</span>
            `;
            sourceLinksList.appendChild(li);
        });
    } else {
        sourceLinksList.innerHTML = `<li class="text-secondary small">No external web citations linked.</li>`;
    }

    // Limitations
    limitationsList.innerHTML = "";
    if (data.limitations) {
        data.limitations.forEach(lim => {
            const li = document.createElement("li");
            li.className = "mb-1";
            li.textContent = lim;
            limitationsList.appendChild(li);
        });
    }

    // Full Report Link
    if (data.report_id) {
        fullReportBtn.href = `/report/${data.report_id}`;
        fullReportBtn.style.display = "inline-flex";
    }

    // Prepare AI Voice Narration
    currentVoiceScript = data.voice_script || (data.explanation ? `${data.verdict}. ${data.explanation}` : "");
    if (window.speechSynthesis) window.speechSynthesis.cancel();
    const playBtn = document.getElementById("voice-play-btn");
    const playIcon = document.getElementById("voice-play-icon");
    const audioWave = document.getElementById("voice-audio-wave");
    const stopBtn = document.getElementById("voice-stop-btn");
    const statusBadge = document.getElementById("voice-status-badge");
    if (playBtn) playBtn.classList.remove("speaking");
    if (playIcon) playIcon.className = "fa-solid fa-volume-high";
    if (audioWave) audioWave.style.display = "none";
    if (stopBtn) stopBtn.style.display = "none";
    if (statusBadge) {
        statusBadge.className = "badge bg-info bg-opacity-20 text-info border border-info border-opacity-25 small";
        statusBadge.textContent = "Ready to Speak";
    }
}

// Global Voice Variables
let recognition = null;
let isRecording = false;
let currentVoiceScript = "";
let isSpeaking = false;

/**
 * Feature 1: Speech-to-Text Voice Input
 */
function setupVoiceInput() {
    const voiceBtn = document.getElementById("voice-input-btn");
    const voiceLabel = document.getElementById("voice-input-label");
    const listeningStatus = document.getElementById("voice-listening-status");
    const listeningText = document.getElementById("voice-listening-text");
    const claimInput = document.getElementById("claim-input");
    if (!voiceBtn || !claimInput) return;

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
        voiceBtn.addEventListener("click", () => {
            alert("Speech Recognition is not supported by your current browser. Please open TRUTH AI in Google Chrome, Microsoft Edge, or a browser with Web Speech API enabled.");
        });
        return;
    }

    try {
        recognition = new SpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = true;
        recognition.lang = "en-US";

        function stopRecording() {
            isRecording = false;
            voiceBtn.classList.remove("voice-recording-active");
            if (voiceLabel) voiceLabel.textContent = "Speak your news";
        }

        recognition.onstart = () => {
            isRecording = true;
            voiceBtn.classList.add("voice-recording-active");
            if (voiceLabel) voiceLabel.textContent = "Listening... Speak now";
            if (listeningStatus) listeningStatus.style.display = "block";
        };

        recognition.onresult = (event) => {
            let transcript = "";
            for (let i = 0; i < event.results.length; i++) {
                transcript += event.results[i][0].transcript;
            }
            claimInput.value = transcript;
        };

        recognition.onerror = (event) => {
            console.warn("Speech recognition error:", event.error);
            stopRecording();
            if (event.error === "not-allowed") {
                alert("Microphone permission was denied. Please allow microphone access in your browser to speak your claim.");
            }
        };

        recognition.onend = () => {
            stopRecording();
            if (listeningStatus) {
                listeningText.textContent = "Voice captured successfully! Click 'Verify News' to check.";
                setTimeout(() => {
                    listeningStatus.style.display = "none";
                    listeningText.textContent = "Listening to microphone... Speak clearly into your mic.";
                }, 4000);
            }
        };

        voiceBtn.addEventListener("click", () => {
            if (isRecording) {
                recognition.stop();
                stopRecording();
            } else {
                try {
                    recognition.start();
                } catch (err) {
                    console.error("Speech recognition start failed:", err);
                }
            }
        });
    } catch (e) {
        console.warn("Speech recognition setup error:", e);
    }
}

/**
 * Feature 2: Text-to-Speech AI Voice Result Narration (Female / Male Selector)
 */
let selectedVoiceGender = localStorage.getItem("truth_ai_voice_gender") || "female";

function setupVoiceExplanation() {
    const playBtn = document.getElementById("voice-play-btn");
    const playIcon = document.getElementById("voice-play-icon");
    const stopBtn = document.getElementById("voice-stop-btn");
    const statusBadge = document.getElementById("voice-status-badge");
    const audioWave = document.getElementById("voice-audio-wave");
    const femaleBtn = document.getElementById("voice-gender-female");
    const maleBtn = document.getElementById("voice-gender-male");
    if (!playBtn) return;

    if (!('speechSynthesis' in window)) {
        playBtn.addEventListener("click", () => {
            alert("Text-to-speech audio narration is not supported in this browser.");
        });
        return;
    }

    function updateVoiceGenderUI() {
        if (femaleBtn && maleBtn) {
            if (selectedVoiceGender === "female") {
                femaleBtn.classList.add("active");
                maleBtn.classList.remove("active");
            } else {
                maleBtn.classList.add("active");
                femaleBtn.classList.remove("active");
            }
        }
    }

    if (femaleBtn) {
        femaleBtn.addEventListener("click", () => {
            selectedVoiceGender = "female";
            localStorage.setItem("truth_ai_voice_gender", "female");
            updateVoiceGenderUI();
            if (isSpeaking) {
                speakResult();
            }
        });
    }

    if (maleBtn) {
        maleBtn.addEventListener("click", () => {
            selectedVoiceGender = "male";
            localStorage.setItem("truth_ai_voice_gender", "male");
            updateVoiceGenderUI();
            if (isSpeaking) {
                speakResult();
            }
        });
    }

    updateVoiceGenderUI();

    // Chromium loads voices asynchronously
    if (window.speechSynthesis.onvoiceschanged !== undefined) {
        window.speechSynthesis.onvoiceschanged = () => {
            window.speechSynthesis.getVoices();
        };
    }

    function getBestVoiceForGender(gender, voices) {
        if (!voices || voices.length === 0) return null;

        const enVoices = voices.filter(v => v.lang.startsWith("en"));
        const searchPool = enVoices.length > 0 ? enVoices : voices;

        const femaleNames = [
            "zira", "jenny", "aria", "samantha", "victoria", "karen", "female", "girl", "woman",
            "hazel", "susan", "catherine", "linda", "joanna", "kendra", "ivy", "kimberly", "salli"
        ];
        const maleNames = [
            "david", "guy", "george", "daniel", "alex", "fred", "male", "boy", "man",
            "mark", "james", "richard", "oliver", "matthew", "joey", "justin", "brian"
        ];

        const targetList = gender === "female" ? femaleNames : maleNames;

        for (const name of targetList) {
            const found = searchPool.find(v => v.name.toLowerCase().includes(name));
            if (found) return found;
        }

        if (gender === "female") {
            const femaleHeuristic = searchPool.find(v =>
                v.name.toLowerCase().includes("female") ||
                v.name.includes("Zira") ||
                v.name.includes("Jenny") ||
                v.name.includes("Aria")
            );
            if (femaleHeuristic) return femaleHeuristic;
        } else {
            const maleHeuristic = searchPool.find(v =>
                v.name.toLowerCase().includes("male") ||
                v.name.includes("David") ||
                v.name.includes("Guy") ||
                v.name.includes("George")
            );
            if (maleHeuristic) return maleHeuristic;
        }

        return searchPool[0];
    }

    function stopSpeaking() {
        if (window.speechSynthesis) {
            window.speechSynthesis.cancel();
        }
        isSpeaking = false;
        playBtn.classList.remove("speaking");
        if (playIcon) playIcon.className = "fa-solid fa-volume-high";
        if (audioWave) audioWave.style.display = "none";
        if (stopBtn) stopBtn.style.display = "none";
        if (statusBadge) {
            statusBadge.className = "badge bg-info bg-opacity-20 text-info border border-info border-opacity-25 small";
            statusBadge.textContent = "Ready to Speak";
        }
    }

    function speakResult() {
        if (!currentVoiceScript) return;

        window.speechSynthesis.cancel();

        const utterance = new SpeechSynthesisUtterance(currentVoiceScript);

        const voices = window.speechSynthesis.getVoices();
        const matchedVoice = getBestVoiceForGender(selectedVoiceGender, voices);
        if (matchedVoice) {
            utterance.voice = matchedVoice;
        }

        if (selectedVoiceGender === "female") {
            utterance.pitch = matchedVoice ? 1.05 : 1.25;
            utterance.rate = 1.0;
        } else {
            utterance.pitch = matchedVoice ? 0.95 : 0.85;
            utterance.rate = 0.98;
        }

        utterance.onstart = () => {
            isSpeaking = true;
            playBtn.classList.add("speaking");
            if (playIcon) playIcon.className = "fa-solid fa-pause";
            if (audioWave) audioWave.style.display = "inline-flex";
            if (stopBtn) stopBtn.style.display = "inline-block";
            if (statusBadge) {
                statusBadge.className = "badge bg-success bg-opacity-25 text-success border border-success border-opacity-50 small";
                statusBadge.textContent = selectedVoiceGender === "female" ? "Speaking (Female AI)..." : "Speaking (Male AI)...";
            }
        };

        utterance.onend = () => {
            stopSpeaking();
        };

        utterance.onerror = (e) => {
            console.warn("Speech synthesis error:", e);
            stopSpeaking();
        };

        window.speechSynthesis.speak(utterance);
    }

    playBtn.addEventListener("click", () => {
        if (isSpeaking) {
            stopSpeaking();
        } else {
            speakResult();
        }
    });

    if (stopBtn) {
        stopBtn.addEventListener("click", stopSpeaking);
    }
}

function escapeHtml(str) {
    if (!str) return "";
    const div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
}
