/**
 * TRUTH AI — Link & Content Fact-Checker Client Controller
 * Features:
 *  - Phishing & URL threat heuristic forensics
 *  - Real-time News & Video Fact-Checking by URL (YouTube, News Articles, Blogs)
 *  - Speech-to-Text Voice Input for reading links
 *  - Text-to-Speech AI Voice Result Explanation with Female / Male Voice Selector
 *  - 1-Click Clipboard Paste & Quick Test Presets
 */

// Voice & Speech Globals
let linkRecognition = null;
let isLinkRecording = false;
let currentLinkVoiceScript = "";
let isLinkSpeaking = false;
let selectedVoiceGender = localStorage.getItem("truth_ai_voice_gender") || "female";
let activeScanMode = "all"; // 'all' (auto), 'content', 'security'

document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("link-verify-form");
    if (!form) return;

    // Initialize Voice, Modes and Clipboard Features
    setupScanModes();
    setupLinkVoiceInput();
    setupLinkVoiceExplanation();
    setupClipboardPaste();

    const urlInput = document.getElementById("url-input");
    const submitBtn = document.getElementById("link-submit-btn");
    const progressOverlay = document.getElementById("analysis-progress");
    const resultContainer = document.getElementById("link-result-container");
    const stepItems = document.querySelectorAll(".progress-step-item");

    form.addEventListener("submit", async (e) => {
        e.preventDefault();
        const rawUrl = urlInput.value.trim();
        if (!rawUrl || rawUrl.length < 3) {
            alert("Please enter a valid News, Video, or Website link to verify.");
            urlInput.focus();
            return;
        }

        // Display progress overlay
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
        }, 500);

        try {
            // Determine endpoint based on active mode & URL type
            const isVideo = isVideoUrl(rawUrl);
            const isNewsLikely = isNewsUrl(rawUrl);
            let endpoint = "/api/verify-link";

            if (activeScanMode === "content" || (activeScanMode === "all" && (isVideo || isNewsLikely))) {
                endpoint = "/api/verify-content-link";
            }

            const response = await fetch(endpoint, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ url: rawUrl }),
            });

            clearInterval(stepInterval);
            stepItems.forEach((item) => item.classList.add("completed"));

            const data = await response.json();
            progressOverlay.style.display = "none";
            submitBtn.disabled = false;

            if (response.ok && data.success) {
                renderVerificationResult(data, endpoint);
                resultContainer.style.display = "block";
                resultContainer.scrollIntoView({ behavior: "smooth", block: "start" });
            } else {
                alert(data.error || "Verification failed. Please check the URL and try again.");
            }
        } catch (err) {
            clearInterval(stepInterval);
            progressOverlay.style.display = "none";
            submitBtn.disabled = false;
            console.error(err);
            alert("A network error occurred while contacting the TRUTH AI verification service.");
        }
    });
});

/**
 * Scan Mode Pill Selector
 */
function setupScanModes() {
    const pills = document.querySelectorAll(".mode-pill-btn");
    pills.forEach((pill) => {
        pill.addEventListener("click", () => {
            pills.forEach((p) => {
                p.classList.remove("active");
                p.classList.add("text-secondary");
            });
            pill.classList.add("active");
            pill.classList.remove("text-secondary");
            activeScanMode = pill.getAttribute("data-mode") || "all";

            const label = document.getElementById("url-input-label");
            const icon = document.getElementById("url-type-icon");
            if (activeScanMode === "content") {
                if (label) label.innerHTML = 'Enter News Article or YouTube Video URL <span class="text-danger">*</span>';
                if (icon) icon.className = "fa-solid fa-newspaper";
            } else if (activeScanMode === "security") {
                if (label) label.innerHTML = 'Enter Web Link or Banking/Payment URL <span class="text-danger">*</span>';
                if (icon) icon.className = "fa-solid fa-shield-virus";
            } else {
                if (label) label.innerHTML = 'Enter News Link, YouTube Video, or Web URL <span class="text-danger">*</span>';
                if (icon) icon.className = "fa-solid fa-link";
            }
        });
    });
}

function isVideoUrl(url) {
    const l = url.toLowerCase();
    return l.includes("youtube.com") || l.includes("youtu.be") || l.includes("vimeo.com") || l.includes("dailymotion.com");
}

function isNewsUrl(url) {
    const l = url.toLowerCase();
    const newsKeywords = [
        "ndtv.com", "thehindu.com", "indianexpress.com", "timesofindia", "aajtak.in",
        "indiatoday.in", "livemint.com", "bbc.com", "bbc.co.uk", "reuters.com",
        "apnews.com", "cnn.com", "theguardian.com", "news", "article", "story", "theonion.com"
    ];
    return newsKeywords.some((k) => l.includes(k));
}

/**
 * Select a Demonstration Test Scenario
 */
window.selectQuickTest = function (url, mode) {
    const input = document.getElementById("url-input");
    if (input) {
        input.value = url;
        input.focus();
    }
    const modeBtn = document.querySelector(`.mode-pill-btn[data-mode="${mode}"]`);
    if (modeBtn) modeBtn.click();
};

/**
 * Main Dynamic Result Renderer
 */
function renderVerificationResult(data, endpoint) {
    const isContentResult = endpoint === "/api/verify-content-link" || data.authenticity_score !== undefined;

    const contentSection = document.getElementById("content-factcheck-section");
    const securitySection = document.getElementById("security-audit-section");
    const securityDetails = document.getElementById("security-details-section");
    const telemetrySection = document.getElementById("telemetry-section");

    if (isContentResult) {
        // Render News / Video Fact-Check Report
        if (contentSection) contentSection.style.display = "block";
        if (securitySection) securitySection.style.display = "none";
        if (securityDetails) securityDetails.style.display = "none";
        if (telemetrySection) telemetrySection.style.display = "none";

        renderContentFactCheck(data);
    } else {
        // Render Link Phishing & Security Report
        if (contentSection) contentSection.style.display = "none";
        if (securitySection) securitySection.style.display = "block";
        if (securityDetails) securityDetails.style.display = "flex";
        if (telemetrySection) telemetrySection.style.display = "block";

        renderSecurityAudit(data);
    }

    // Prepare voice narration
    prepareVoiceScript(data, isContentResult);
}

/**
 * Render News & Video Fact-Check Card
 */
function renderContentFactCheck(data) {
    // Title & URL
    const titleEl = document.getElementById("content-title-text");
    if (titleEl) titleEl.textContent = data.title || "Extracted Online Content";

    const urlEl = document.getElementById("content-url-display");
    if (urlEl) urlEl.textContent = data.url;

    const typeLabel = document.getElementById("content-type-label");
    const typeIcon = document.getElementById("content-type-icon");
    if (typeLabel) typeLabel.textContent = `${data.content_type || "Content"} Fact-Check`;
    if (typeIcon) typeIcon.className = data.is_video ? "fa-brands fa-youtube me-1" : "fa-regular fa-newspaper me-1";

    // Publisher & Badge
    const pubEl = document.getElementById("content-publisher-name");
    if (pubEl) pubEl.textContent = data.publisher || data.host;

    const badgeEl = document.getElementById("content-publisher-badge");
    if (badgeEl) {
        badgeEl.textContent = data.source_badge || `Source: ${data.publisher || data.host}`;
    }

    // Verdict Badge
    const vBadge = document.getElementById("content-verdict-badge");
    const vText = document.getElementById("content-verdict-text");
    const vIcon = document.getElementById("content-verdict-icon");

    if (vBadge && vText && vIcon) {
        vBadge.className = "verdict-badge";
        const vClass = data.verdict_class || "warning";
        vBadge.classList.add(`badge-${vClass}`);
        vText.textContent = data.verdict;

        if (vClass === "success") {
            vIcon.className = "fa-solid fa-circle-check text-success me-1";
        } else if (vClass === "danger") {
            vIcon.className = "fa-solid fa-triangle-exclamation text-danger me-1";
        } else {
            vIcon.className = "fa-solid fa-circle-exclamation text-warning me-1";
        }
    }

    // Score & Progress Bar
    const scoreNum = document.getElementById("content-score-num");
    const scoreLabel = document.getElementById("content-score-label");
    const scoreBar = document.getElementById("content-score-bar");
    const score = Math.round(data.authenticity_score || 50);

    if (scoreNum) scoreNum.textContent = `${score}%`;
    if (scoreBar) {
        scoreBar.style.width = `${score}%`;
        scoreBar.className = "confidence-meter-bar";
        if (score >= 80) scoreBar.classList.add("bg-success");
        else if (score >= 50) scoreBar.classList.add("bg-warning");
        else scoreBar.classList.add("bg-danger");
    }

    if (scoreLabel) {
        if (score >= 80) {
            scoreLabel.textContent = "Authentic & Verified";
            scoreLabel.className = "d-block small text-success";
        } else if (score >= 50) {
            scoreLabel.textContent = "Questionable / Needs Caution";
            scoreLabel.className = "d-block small text-warning";
        } else {
            scoreLabel.textContent = "High Risk / Debunked Fake";
            scoreLabel.className = "d-block small text-danger";
        }
    }

    // Explanation
    const explEl = document.getElementById("content-explanation-text");
    if (explEl) explEl.textContent = data.explanation || "Verification analysis complete.";

    // Key Findings List
    const findingsList = document.getElementById("content-findings-list");
    if (findingsList) {
        findingsList.innerHTML = "";
        const items = data.key_findings || [];
        items.forEach((finding) => {
            const row = document.createElement("div");
            row.className = "p-2 rounded bg-dark bg-opacity-50 border border-secondary border-opacity-25 text-light small d-flex align-items-center gap-2";
            row.innerHTML = `<i class="fa-solid fa-check text-info"></i> <span>${escapeHtml(finding)}</span>`;
            findingsList.appendChild(row);
        });
    }

    // Recommendation Text
    const recEl = document.getElementById("res-recommendation-text");
    if (recEl) {
        if (score >= 80) {
            recEl.textContent = `This news report is corroborated by verified media outlets (${data.publisher}). The central facts appear accurate and reliable to reference or share.`;
        } else if (score <= 35) {
            recEl.textContent = `Warning: The claims in this content have been debunked or originate from an unverified or satirical source. Do not circulate this as real factual news on social media.`;
        } else {
            recEl.textContent = `Notice: This content lacks independent multi-source corroboration or contains sensational claims. We recommend cross-checking with official releases before trusting.`;
        }
    }
}

/**
 * Render Link Security & Phishing Card
 */
function renderSecurityAudit(data) {
    const verdictBadge = document.getElementById("res-verdict-badge");
    const verdictIcon = document.getElementById("res-verdict-icon");
    const verdictText = document.getElementById("res-verdict-text");
    const riskScore = document.getElementById("res-risk-score");
    const riskLabel = document.getElementById("res-risk-label");
    const riskBar = document.getElementById("res-risk-bar");
    const explanationText = document.getElementById("res-explanation-text");
    const recommendationText = document.getElementById("res-recommendation-text");

    const threatList = document.getElementById("res-threat-list");
    const securityList = document.getElementById("res-security-list");

    const impersonationAlert = document.getElementById("res-impersonation-alert");
    const impersonationText = document.getElementById("res-impersonation-text");
    const officialBrandDomain = document.getElementById("res-official-brand-domain");

    // Verdict Styling
    verdictBadge.className = "verdict-badge";
    const risk = data.risk_score || 0;
    riskScore.textContent = `${risk}%`;
    riskBar.style.width = `${risk}%`;

    if (risk >= 70) {
        verdictBadge.classList.add("badge-danger");
        verdictIcon.className = "fa-solid fa-triangle-exclamation text-danger me-1";
        riskLabel.textContent = "Critical Risk (Likely Phishing / Scam)";
        riskLabel.className = "d-block small text-danger";
        riskBar.className = "confidence-meter-bar bg-danger";
    } else if (risk >= 35) {
        verdictBadge.classList.add("badge-warning");
        verdictIcon.className = "fa-solid fa-circle-exclamation text-warning me-1";
        riskLabel.textContent = "Moderate Suspicion (Proceed with Caution)";
        riskLabel.className = "d-block small text-warning";
        riskBar.className = "confidence-meter-bar bg-warning";
    } else {
        verdictBadge.classList.add("badge-success");
        verdictIcon.className = "fa-solid fa-circle-check text-success me-1";
        riskLabel.textContent = "Safe / Legitimate Web Destination";
        riskLabel.className = "d-block small text-success";
        riskBar.className = "confidence-meter-bar bg-success";
    }

    verdictText.textContent = data.verdict;
    explanationText.textContent = data.explanation;
    recommendationText.textContent = data.recommendation;

    // Brand Impersonation Alert
    if (data.impersonated_brand && data.official_brand_domain) {
        impersonationAlert.style.display = "block";
        impersonationText.textContent = `This link attempts to mimic the brand name "${data.impersonated_brand}", but does NOT match the authentic official domain.`;
        officialBrandDomain.textContent = data.official_brand_domain;
    } else {
        impersonationAlert.style.display = "none";
    }

    // Threat Flags List
    threatList.innerHTML = "";
    if (data.risk_flags && data.risk_flags.length > 0) {
        data.risk_flags.forEach((flag) => {
            const item = document.createElement("div");
            item.className = "small text-danger mb-2 d-flex align-items-start gap-2";
            item.innerHTML = `<i class="fa-solid fa-xmark mt-1"></i> <span>${escapeHtml(flag)}</span>`;
            threatList.appendChild(item);
        });
    } else {
        threatList.innerHTML = '<span class="text-secondary small fst-italic">No critical threat indicators detected.</span>';
    }

    // Security Flags List
    securityList.innerHTML = "";
    if (data.positive_flags && data.positive_flags.length > 0) {
        data.positive_flags.forEach((flag) => {
            const item = document.createElement("div");
            item.className = "small text-success mb-2 d-flex align-items-start gap-2";
            item.innerHTML = `<i class="fa-solid fa-check mt-1"></i> <span>${escapeHtml(flag)}</span>`;
            securityList.appendChild(item);
        });
    } else {
        securityList.innerHTML = '<span class="text-secondary small fst-italic">No positive security endorsements.</span>';
    }

    // Telemetry
    if (data.technical_audit) {
        const audit = data.technical_audit;
        const setVal = (id, val) => {
            const el = document.getElementById(id);
            if (el) el.textContent = val;
        };
        setVal("audit-protocol", (audit.scheme || "http").toUpperCase());
        setVal("audit-tld", audit.tld ? `.${audit.tld.toUpperCase()}` : "N/A");
        setVal("audit-entropy", audit.entropy_score > 3.8 ? "High (Random)" : "Low (Normal)");
        setVal("audit-ip", audit.is_ip_address ? "Yes (Alert)" : "No");
        setVal("audit-shortened", audit.is_shortened ? "Yes (Masked)" : "No");
    }
}

/**
 * 1-Click Clipboard Paste Support
 */
function setupClipboardPaste() {
    const pasteBtn = document.getElementById("paste-btn");
    const urlInput = document.getElementById("url-input");
    if (!pasteBtn || !urlInput) return;

    pasteBtn.addEventListener("click", async () => {
        try {
            if (navigator.clipboard && navigator.clipboard.readText) {
                const text = await navigator.clipboard.readText();
                if (text) {
                    urlInput.value = text.trim();
                    urlInput.focus();
                } else {
                    alert("Clipboard is empty.");
                }
            } else {
                alert("Clipboard access is not permitted in this browser.");
            }
        } catch (err) {
            console.error(err);
            alert("Could not read clipboard. Please paste manually using Ctrl + V.");
        }
    });
}

/**
 * Speech-to-Text Voice Input
 */
function setupLinkVoiceInput() {
    const btn = document.getElementById("voice-input-btn");
    const label = document.getElementById("voice-input-label");
    const status = document.getElementById("voice-listening-status");
    const urlInput = document.getElementById("url-input");
    if (!btn || !urlInput) return;

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
        btn.style.display = "none";
        return;
    }

    linkRecognition = new SpeechRecognition();
    linkRecognition.continuous = false;
    linkRecognition.interimResults = false;
    linkRecognition.lang = "en-US";

    linkRecognition.onstart = () => {
        isLinkRecording = true;
        btn.classList.add("btn-danger");
        btn.classList.remove("btn-outline-info");
        if (label) label.textContent = "Listening...";
        if (status) status.style.display = "block";
    };

    linkRecognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        if (transcript) {
            let formatted = transcript.trim().toLowerCase().replace(/\s+dot\s+/g, ".").replace(/\s+/g, "");
            if (!formatted.startsWith("http://") && !formatted.startsWith("https://")) {
                formatted = "https://" + formatted;
            }
            urlInput.value = formatted;
        }
    };

    linkRecognition.onerror = (e) => {
        console.warn("Speech recognition error:", e);
        stopLinkRecording();
    };

    linkRecognition.onend = () => {
        stopLinkRecording();
    };

    btn.addEventListener("click", () => {
        if (isLinkRecording) {
            linkRecognition.stop();
        } else {
            try {
                linkRecognition.start();
            } catch (err) {
                console.error(err);
            }
        }
    });

    function stopLinkRecording() {
        isLinkRecording = false;
        btn.classList.remove("btn-danger");
        btn.classList.add("btn-outline-info");
        if (label) label.textContent = "Voice Input";
        if (status) status.style.display = "none";
    }
}

/**
 * Text-to-Speech AI Voice Explanation with Female/Male Voice Selector
 */
function setupLinkVoiceExplanation() {
    const playBtn = document.getElementById("voice-play-btn");
    const stopBtn = document.getElementById("voice-stop-btn");
    const femaleBtn = document.getElementById("voice-gender-female");
    const maleBtn = document.getElementById("voice-gender-male");

    if (femaleBtn && maleBtn) {
        if (selectedVoiceGender === "male") {
            maleBtn.classList.add("active");
            femaleBtn.classList.remove("active");
        } else {
            femaleBtn.classList.add("active");
            maleBtn.classList.remove("active");
        }

        femaleBtn.addEventListener("click", () => {
            selectedVoiceGender = "female";
            localStorage.setItem("truth_ai_voice_gender", "female");
            femaleBtn.classList.add("active");
            maleBtn.classList.remove("active");
            if (isLinkSpeaking) speakCurrentScript();
        });

        maleBtn.addEventListener("click", () => {
            selectedVoiceGender = "male";
            localStorage.setItem("truth_ai_voice_gender", "male");
            maleBtn.classList.add("active");
            femaleBtn.classList.remove("active");
            if (isLinkSpeaking) speakCurrentScript();
        });
    }

    if (playBtn) {
        playBtn.addEventListener("click", () => {
            if (isLinkSpeaking) {
                stopVoiceSpeech();
            } else {
                speakCurrentScript();
            }
        });
    }

    if (stopBtn) {
        stopBtn.addEventListener("click", () => {
            stopVoiceSpeech();
        });
    }
}

function prepareVoiceScript(data, isContentResult) {
    if (isContentResult) {
        const score = Math.round(data.authenticity_score || 50);
        let toneMsg = data.verdict;
        currentLinkVoiceScript = `Content Fact Check for ${data.title}. Reported by ${data.publisher}. The authenticity verdict is ${toneMsg}, with a credibility score of ${score} percent. ${data.explanation}`;
    } else {
        const risk = data.risk_score || 0;
        let verdictSpeech = data.verdict;
        if (risk >= 70) {
            verdictSpeech = `High alert! This link is dangerous and classified as ${data.verdict}.`;
        } else if (risk >= 35) {
            verdictSpeech = `Caution! This link is suspicious and classified as ${data.verdict}.`;
        } else {
            verdictSpeech = `Good news! This link is safe and verified as ${data.verdict}.`;
        }
        currentLinkVoiceScript = `${verdictSpeech} Threat risk score is ${risk} percent. ${data.explanation} ${data.recommendation}`;
    }
}

function speakCurrentScript() {
    if (!window.speechSynthesis || !currentLinkVoiceScript) return;
    window.speechSynthesis.cancel();

    const utterance = new SpeechSynthesisUtterance(currentLinkVoiceScript);
    utterance.rate = 1.0;
    utterance.pitch = selectedVoiceGender === "male" ? 0.85 : 1.15;

    const voices = window.speechSynthesis.getVoices();
    if (voices && voices.length > 0) {
        let chosenVoice = null;
        if (selectedVoiceGender === "female") {
            chosenVoice = voices.find((v) => v.lang.startsWith("en") && (v.name.includes("Female") || v.name.includes("Zira") || v.name.includes("Samantha") || v.name.includes("Google US English")));
        } else {
            chosenVoice = voices.find((v) => v.lang.startsWith("en") && (v.name.includes("Male") || v.name.includes("David") || v.name.includes("George") || v.name.includes("Google UK English Male")));
        }
        if (chosenVoice) utterance.voice = chosenVoice;
    }

    utterance.onstart = () => {
        isLinkSpeaking = true;
        updateVoiceUIState(true);
    };

    utterance.onend = () => {
        isLinkSpeaking = false;
        updateVoiceUIState(false);
    };

    utterance.onerror = () => {
        isLinkSpeaking = false;
        updateVoiceUIState(false);
    };

    window.speechSynthesis.speak(utterance);
}

function stopVoiceSpeech() {
    if (window.speechSynthesis) {
        window.speechSynthesis.cancel();
    }
    isLinkSpeaking = false;
    updateVoiceUIState(false);
}

function updateVoiceUIState(speaking) {
    const playIcon = document.getElementById("voice-play-icon");
    const statusBadge = document.getElementById("voice-status-badge");
    const wave = document.getElementById("voice-audio-wave");
    const stopBtn = document.getElementById("voice-stop-btn");

    if (speaking) {
        if (playIcon) playIcon.className = "fa-solid fa-pause";
        if (statusBadge) {
            statusBadge.textContent = "Speaking...";
            statusBadge.className = "badge bg-danger bg-opacity-20 text-danger border border-danger border-opacity-25 small";
        }
        if (wave) wave.style.display = "flex";
        if (stopBtn) stopBtn.style.display = "inline-block";
    } else {
        if (playIcon) playIcon.className = "fa-solid fa-volume-high";
        if (statusBadge) {
            statusBadge.textContent = "Ready to Speak";
            statusBadge.className = "badge bg-info bg-opacity-20 text-info border border-info border-opacity-25 small";
        }
        if (wave) wave.style.display = "none";
        if (stopBtn) stopBtn.style.display = "none";
    }
}

function escapeHtml(str) {
    if (!str) return "";
    return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#039;");
}

window.copyShareLink = function () {
    const input = document.getElementById("url-input");
    const url = input ? input.value.trim() : window.location.href;
    if (navigator.clipboard) {
        navigator.clipboard.writeText(url);
        alert("Link copied to clipboard!");
    } else {
        alert("URL: " + url);
    }
};
