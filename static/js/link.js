/**
 * TRUTH AI — Link & URL Phishing Scanner Client Controller
 * Detects fake, fraud, phishing, and certified links.
 * Features:
 *  - Real-time heuristic forensics & institutional whitelist audit
 *  - Speech-to-Text Voice Input for reading links
 *  - Text-to-Speech AI Voice Result Explanation with Female / Male Voice Selector
 *  - Clipboard 1-Click Paste
 */

// Voice & Speech Globals
let linkRecognition = null;
let isLinkRecording = false;
let currentLinkVoiceScript = "";
let isLinkSpeaking = false;
let selectedVoiceGender = localStorage.getItem("truth_ai_voice_gender") || "female";

document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("link-verify-form");
    if (!form) return;

    // Initialize Voice and Clipboard Features
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
            alert("Please enter a valid web link or URL to scan.");
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
        }, 550);

        try {
            const response = await fetch("/api/verify-link", {
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
                renderLinkResult(data);
                resultContainer.style.display = "block";
                resultContainer.scrollIntoView({ behavior: "smooth", block: "start" });
            } else {
                alert(data.error || "Link scan failed. Please check the URL and try again.");
            }
        } catch (err) {
            clearInterval(stepInterval);
            progressOverlay.style.display = "none";
            submitBtn.disabled = false;
            console.error(err);
            alert("A network error occurred while contacting the TRUTH AI URL scanner.");
        }
    });
});

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
                    alert("Clipboard is currently empty. Please copy a link first.");
                }
            } else {
                const manual = prompt("Paste your link here:");
                if (manual) urlInput.value = manual.trim();
            }
        } catch (err) {
            console.warn("Clipboard access denied or unsupported:", err);
            const manual = prompt("Paste your link here:");
            if (manual) urlInput.value = manual.trim();
        }
    });
}

/**
 * Speech-to-Text Voice Input for Web Links
 */
function setupLinkVoiceInput() {
    const voiceBtn = document.getElementById("voice-input-btn");
    const voiceLabel = document.getElementById("voice-input-label");
    const listeningStatus = document.getElementById("voice-listening-status");
    const listeningText = document.getElementById("voice-listening-text");
    const urlInput = document.getElementById("url-input");
    if (!voiceBtn || !urlInput) return;

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
        voiceBtn.addEventListener("click", () => {
            alert("Speech Recognition is not supported by your browser. Please use Chrome, Edge, or a Web Speech-enabled browser.");
        });
        return;
    }

    try {
        linkRecognition = new SpeechRecognition();
        linkRecognition.continuous = false;
        linkRecognition.interimResults = true;
        linkRecognition.lang = "en-US";

        function stopRecording() {
            isLinkRecording = false;
            voiceBtn.classList.remove("voice-recording-active");
            if (voiceLabel) voiceLabel.textContent = "Voice Input";
        }

        linkRecognition.onstart = () => {
            isLinkRecording = true;
            voiceBtn.classList.add("voice-recording-active");
            if (voiceLabel) voiceLabel.textContent = "Listening...";
            if (listeningStatus) listeningStatus.style.display = "block";
            if (listeningText) listeningText.textContent = "Listening... Speak the web address or domain name.";
        };

        linkRecognition.onresult = (event) => {
            let transcript = "";
            for (let i = 0; i < event.results.length; i++) {
                transcript += event.results[i][0].transcript;
            }
            // Format spoken dots and slashes e.g. "amazon dot in" -> "amazon.in"
            let cleaned = transcript
                .toLowerCase()
                .replace(/\s+dot\s+/g, ".")
                .replace(/\s+slash\s+/g, "/")
                .replace(/\s+/g, "");
            urlInput.value = cleaned;
        };

        linkRecognition.onerror = (event) => {
            console.warn("Speech recognition error:", event.error);
            stopRecording();
            if (event.error === "not-allowed") {
                alert("Microphone permission was denied. Please allow microphone access to speak.");
            }
        };

        linkRecognition.onend = () => {
            stopRecording();
            if (listeningStatus) {
                if (listeningText) listeningText.textContent = "Web address captured! Click 'Scan Link Now'.";
                setTimeout(() => {
                    listeningStatus.style.display = "none";
                }, 3500);
            }
        };

        voiceBtn.addEventListener("click", () => {
            if (isLinkRecording) {
                linkRecognition.stop();
                stopRecording();
            } else {
                try {
                    linkRecognition.start();
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
 * Text-to-Speech AI Voice Result Narration (Female / Male Selector)
 */
function setupLinkVoiceExplanation() {
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
            if (isLinkSpeaking) {
                speakLinkResult();
            }
        });
    }

    if (maleBtn) {
        maleBtn.addEventListener("click", () => {
            selectedVoiceGender = "male";
            localStorage.setItem("truth_ai_voice_gender", "male");
            updateVoiceGenderUI();
            if (isLinkSpeaking) {
                speakLinkResult();
            }
        });
    }

    updateVoiceGenderUI();

    if (window.speechSynthesis.onvoiceschanged !== undefined) {
        window.speechSynthesis.onvoiceschanged = () => {
            window.speechSynthesis.getVoices();
        };
    }

    function getBestVoiceForGender(gender, voices) {
        if (!voices || voices.length === 0) return null;

        const enVoices = voices.filter((v) => v.lang.startsWith("en"));
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
            const found = searchPool.find((v) => v.name.toLowerCase().includes(name));
            if (found) return found;
        }

        if (gender === "female") {
            const femaleHeuristic = searchPool.find((v) =>
                v.name.toLowerCase().includes("female") ||
                v.name.includes("Zira") ||
                v.name.includes("Jenny") ||
                v.name.includes("Aria")
            );
            if (femaleHeuristic) return femaleHeuristic;
        } else {
            const maleHeuristic = searchPool.find((v) =>
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
        isLinkSpeaking = false;
        playBtn.classList.remove("speaking");
        if (playIcon) playIcon.className = "fa-solid fa-volume-high";
        if (audioWave) audioWave.style.display = "none";
        if (stopBtn) stopBtn.style.display = "none";
        if (statusBadge) {
            statusBadge.className = "badge bg-info bg-opacity-20 text-info border border-info border-opacity-25 small";
            statusBadge.textContent = "Ready to Speak";
        }
    }

    function speakLinkResult() {
        if (!currentLinkVoiceScript) {
            alert("No link analysis narration available to speak.");
            return;
        }

        window.speechSynthesis.cancel();

        const utterance = new SpeechSynthesisUtterance(currentLinkVoiceScript);
        utterance.rate = 0.98;
        utterance.pitch = selectedVoiceGender === "female" ? 1.05 : 0.92;

        const voices = window.speechSynthesis.getVoices();
        const chosenVoice = getBestVoiceForGender(selectedVoiceGender, voices);
        if (chosenVoice) {
            utterance.voice = chosenVoice;
        }

        utterance.onstart = () => {
            isLinkSpeaking = true;
            playBtn.classList.add("speaking");
            if (playIcon) playIcon.className = "fa-solid fa-waveform-lines fa-fade";
            if (audioWave) audioWave.style.display = "flex";
            if (stopBtn) stopBtn.style.display = "inline-flex";
            if (statusBadge) {
                const label = selectedVoiceGender === "female" ? "Speaking (Female AI)" : "Speaking (Male AI)";
                statusBadge.className = "badge bg-success bg-opacity-20 text-success border border-success border-opacity-25 small";
                statusBadge.textContent = label;
            }
        };

        utterance.onend = () => {
            stopSpeaking();
        };

        utterance.onerror = (e) => {
            console.warn("Speech synthesis utterance error:", e);
            stopSpeaking();
        };

        window.speechSynthesis.speak(utterance);
    }

    playBtn.addEventListener("click", () => {
        if (isLinkSpeaking) {
            stopSpeaking();
        } else {
            speakLinkResult();
        }
    });

    if (stopBtn) {
        stopBtn.addEventListener("click", stopSpeaking);
    }
}

/**
 * Render Link Forensic Result
 */
function renderLinkResult(data) {
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
    const fullReportLink = document.getElementById("res-full-report-link");

    // Verdict Badge & Colors
    let badgeClass = "badge-insufficient";
    let iconClass = "fa-circle-info";
    let barColor = "#94a3b8";

    if (data.risk_score > 55) {
        badgeClass = "badge-false";
        iconClass = "fa-circle-xmark";
        barColor = "#ef4444";
    } else if (data.risk_score > 25) {
        badgeClass = "badge-misleading";
        iconClass = "fa-triangle-exclamation";
        barColor = "#f59e0b";
    } else {
        badgeClass = "badge-supported";
        iconClass = "fa-circle-check";
        barColor = "#10b981";
    }

    verdictBadge.className = `verdict-badge ${badgeClass}`;
    verdictIcon.className = `fa-solid ${iconClass}`;
    verdictText.textContent = data.verdict;

    // Risk Meter Bar
    const scoreVal = Math.round(data.risk_score);
    riskScore.textContent = `${scoreVal}%`;
    riskScore.style.color = barColor;
    riskLabel.textContent = data.risk_level;
    riskLabel.style.color = barColor;

    riskBar.style.width = `${Math.max(scoreVal, 4)}%`;
    riskBar.style.backgroundColor = barColor;

    // Explanation & Recommendation
    explanationText.textContent = data.explanation;
    recommendationText.textContent = data.recommendation;

    // Impersonation Alert Banner
    if (data.impersonated_brand) {
        impersonationAlert.style.display = "block";
        impersonationText.innerHTML = `This link attempts to mimic <strong>${escapeHtml(data.impersonated_brand)}</strong> without using their legitimate institutional domain name. It is designed to capture login passwords, OTPs, or financial credentials.`;
        officialBrandDomain.textContent = data.official_brand_domain || "Official Website";
    } else {
        impersonationAlert.style.display = "none";
    }

    // Threat Indicators List
    threatList.innerHTML = "";
    if (data.risk_flags && data.risk_flags.length > 0) {
        data.risk_flags.forEach((flag) => {
            const row = document.createElement("div");
            row.className = "p-2 mb-2 rounded bg-dark border border-danger border-opacity-25 small text-white d-flex align-items-center gap-2";
            row.innerHTML = `<i class="fa-solid fa-triangle-exclamation text-danger flex-shrink-0"></i><span>${escapeHtml(flag)}</span>`;
            threatList.appendChild(row);
        });
    } else {
        threatList.innerHTML = `<p class="text-secondary small fst-italic mb-0">No active threat or phishing indicators triggered for this URL.</p>`;
    }

    // Security & Authentication Checks List
    securityList.innerHTML = "";
    if (data.positive_flags && data.positive_flags.length > 0) {
        data.positive_flags.forEach((flag) => {
            const row = document.createElement("div");
            row.className = "p-2 mb-2 rounded bg-dark border border-success border-opacity-25 small text-white d-flex align-items-center gap-2";
            row.innerHTML = `<i class="fa-solid fa-circle-check text-success flex-shrink-0"></i><span>${escapeHtml(flag)}</span>`;
            securityList.appendChild(row);
        });
    } else {
        securityList.innerHTML = `<p class="text-secondary small fst-italic mb-0">No official institutional certificate or whitelist record found for this domain.</p>`;
    }

    // Technical Telemetry
    const audit = data.technical_audit || {};
    const entropyVal = typeof audit.entropy === "number" ? audit.entropy : (audit.domain_entropy || 0);
    const isSuspiciousEntropy = entropyVal > 3.8 || Boolean(audit.is_suspicious_entropy);
    const isShortened = Boolean(audit.is_shortened || audit.is_shortener);

    document.getElementById("audit-protocol").textContent = (audit.protocol || "HTTP").toUpperCase();
    document.getElementById("audit-tld").textContent = audit.tld ? `.${audit.tld.toUpperCase()}` : "N/A";
    document.getElementById("audit-entropy").textContent = `${entropyVal.toFixed(2)} (${isSuspiciousEntropy ? "High" : "Low"})`;
    document.getElementById("audit-ip").textContent = audit.is_ip_address ? "Yes (High Risk)" : "No";
    document.getElementById("audit-shortened").textContent = isShortened ? "Yes (Masked)" : "No";

    // Printable Full Report Link
    if (data.report_id) {
        fullReportLink.href = `/report/${data.report_id}`;
        fullReportLink.style.display = "inline-flex";
    }

    // Prepare AI Voice Narration
    currentLinkVoiceScript = data.voice_script || `${data.verdict}. ${data.explanation} ${data.recommendation}`;
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

function escapeHtml(text) {
    if (!text) return "";
    const map = {
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#039;",
    };
    return text.toString().replace(/[&<>"']/g, (m) => map[m]);
}

function copyShareLink() {
    const url = window.location.href;
    if (navigator.clipboard) {
        navigator.clipboard.writeText(url).then(() => {
            alert("Audit link copied to clipboard!");
        });
    } else {
        prompt("Copy this URL:", url);
    }
}
