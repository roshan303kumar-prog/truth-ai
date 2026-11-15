/**
 * TRUTH AI — Multimodal AI Assistant Client Controller
 * ChatGPT-inspired experience with Website Screen Awareness, Screen Sharing & Visual Diagnostics
 */

(function () {
    // Session State
    let chatHistory = [];
    let currentAttachedScreenshot = null;
    let isWaitingForResponse = false;
    let isMaximized = false;

    document.addEventListener("DOMContentLoaded", () => {
        initAssistant();
    });

    function initAssistant() {
        const launcher = document.getElementById("assistant-launcher");
        const windowEl = document.getElementById("assistant-window");
        const closeBtn = document.getElementById("assistant-btn-close");
        const maximizeBtn = document.getElementById("assistant-btn-maximize");
        const themeBtn = document.getElementById("assistant-btn-theme");
        const newChatBtn = document.getElementById("assistant-btn-new-chat");
        const form = document.getElementById("assistant-chat-form");
        const textarea = document.getElementById("assistant-input");
        const capturePageBtn = document.getElementById("assistant-btn-capture-page");
        const shareScreenBtn = document.getElementById("assistant-btn-share-screen");
        const uploadImgBtn = document.getElementById("assistant-btn-upload-image");
        const fileInput = document.getElementById("assistant-file-input");
        const removeScreenBtn = document.getElementById("assistant-btn-remove-screen");

        if (!launcher || !windowEl) return;

        // Restore saved theme preference
        const savedTheme = localStorage.getItem("truth_assistant_theme");
        if (savedTheme === "light") {
            windowEl.classList.add("assistant-light-theme");
        }

        // Toggle Launcher Open / Close
        launcher.addEventListener("click", () => {
            const isHidden = windowEl.style.display === "none" || windowEl.style.display === "";
            if (isHidden) {
                windowEl.style.display = "flex";
                textarea.focus();
                scrollToBottom();
            } else {
                windowEl.style.display = "none";
            }
        });

        // Close button
        if (closeBtn) {
            closeBtn.addEventListener("click", () => {
                windowEl.style.display = "none";
            });
        }

        // Maximize / Restore
        if (maximizeBtn) {
            maximizeBtn.addEventListener("click", () => {
                isMaximized = !isMaximized;
                if (isMaximized) {
                    windowEl.classList.add("assistant-maximized");
                    maximizeBtn.innerHTML = '<i class="fa-solid fa-compress"></i>';
                    maximizeBtn.title = "Restore Window";
                } else {
                    windowEl.classList.remove("assistant-maximized");
                    maximizeBtn.innerHTML = '<i class="fa-solid fa-expand"></i>';
                    maximizeBtn.title = "Maximize Window";
                }
                scrollToBottom();
            });
        }

        // Theme Toggle (Dark / Light)
        if (themeBtn) {
            themeBtn.addEventListener("click", () => {
                windowEl.classList.toggle("assistant-light-theme");
                const isLight = windowEl.classList.contains("assistant-light-theme");
                localStorage.setItem("truth_assistant_theme", isLight ? "light" : "dark");
            });
        }

        // New Chat
        if (newChatBtn) {
            newChatBtn.addEventListener("click", () => {
                if (confirm("Start a new chat session? This will clear current conversation memory.")) {
                    resetChatSession();
                }
            });
        }

        // Suggestion Chips Click
        document.querySelectorAll(".assistant-prompt-chip").forEach((chip) => {
            chip.addEventListener("click", () => {
                const prompt = chip.getAttribute("data-prompt");
                if (prompt) {
                    textarea.value = prompt;
                    submitMessage();
                }
            });
        });

        // Form Submit
        if (form) {
            form.addEventListener("submit", (e) => {
                e.preventDefault();
                submitMessage();
            });
        }

        // Auto-expand Textarea & Shift+Enter support
        if (textarea) {
            textarea.addEventListener("keydown", (e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    submitMessage();
                }
            });

            textarea.addEventListener("input", () => {
                textarea.style.height = "auto";
                textarea.style.height = Math.min(textarea.scrollHeight, 120) + "px";
            });
        }

        // Feature 1: Capture Current Page Screenshot (html2canvas)
        if (capturePageBtn) {
            capturePageBtn.addEventListener("click", async () => {
                await captureCurrentPage();
            });
        }

        // Feature 2: Share Screen / Window (getDisplayMedia)
        if (shareScreenBtn) {
            shareScreenBtn.addEventListener("click", async () => {
                await shareDisplayMediaScreen();
            });
        }

        // Feature 3: Upload Screenshot Image File
        if (uploadImgBtn && fileInput) {
            uploadImgBtn.addEventListener("click", () => {
                fileInput.click();
            });

            fileInput.addEventListener("change", (e) => {
                const file = e.target.files && e.target.files[0];
                if (file) {
                    handleImageFile(file, file.name);
                }
                fileInput.value = "";
            });
        }

        // Feature 4: Clipboard Paste (Ctrl+V) for Screenshots
        window.addEventListener("paste", (e) => {
            if (windowEl.style.display === "none") return;
            const items = (e.clipboardData || window.clipboardData).items;
            for (let i = 0; i < items.length; i++) {
                if (items[i].type.indexOf("image") !== -1) {
                    const blob = items[i].getAsFile();
                    if (blob) {
                        handleImageFile(blob, "Clipboard Screenshot");
                        break;
                    }
                }
            }
        });

        // Remove Screen Attachment Button
        if (removeScreenBtn) {
            removeScreenBtn.addEventListener("click", () => {
                detachScreenshot();
            });
        }
    }

    /**
     * Capture current webpage DOM snapshot using html2canvas
     */
    async function captureCurrentPage() {
        const windowEl = document.getElementById("assistant-window");
        const launcher = document.getElementById("assistant-launcher-wrapper") || document.getElementById("assistant-launcher");

        // Temporarily hide assistant window so it doesn't photograph itself
        const prevWindowDisplay = windowEl.style.display;
        const prevLauncherDisplay = launcher ? launcher.style.display : "block";
        windowEl.style.display = "none";
        if (launcher) launcher.style.display = "none";

        try {
            if (typeof html2canvas === "undefined") {
                // If html2canvas not loaded from CDN, load dynamically
                await loadScript("https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js");
            }

            const canvas = await html2canvas(document.body, {
                useCORS: true,
                logging: false,
                scale: 1,
                windowWidth: document.documentElement.clientWidth,
                windowHeight: document.documentElement.clientHeight,
            });

            const dataUrl = canvas.toDataURL("image/jpeg", 0.85);
            attachScreenshot(dataUrl, `Current Page: ${document.title.split("—")[0].trim()}`);
        } catch (err) {
            console.warn("html2canvas capture error:", err);
            alert("Could not capture page DOM. Please use 'Share Screen' or 'Upload Image' instead.");
        } finally {
            windowEl.style.display = prevWindowDisplay;
            if (launcher) launcher.style.display = prevLauncherDisplay;
        }
    }

    /**
     * Capture live screen using Web Screen Share API (getDisplayMedia)
     */
    async function shareDisplayMediaScreen() {
        if (!navigator.mediaDevices || !navigator.mediaDevices.getDisplayMedia) {
            alert("Screen Sharing API is not supported by this browser. Please use 'Capture Page' or 'Upload Image'.");
            return;
        }

        try {
            const stream = await navigator.mediaDevices.getDisplayMedia({
                video: { cursor: "always" },
                audio: false,
            });

            const video = document.createElement("video");
            video.srcObject = stream;
            video.play();

            await new Promise((resolve) => (video.onloadedmetadata = resolve));

            // Grab snapshot from video stream
            const canvas = document.createElement("canvas");
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            const ctx = canvas.getContext("2d");
            ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

            // Stop screen sharing track immediately
            stream.getTracks().forEach((track) => track.stop());

            const dataUrl = canvas.toDataURL("image/jpeg", 0.85);
            attachScreenshot(dataUrl, "Shared Screen Capture");
        } catch (err) {
            if (err.name !== "NotAllowedError") {
                console.warn("Screen share error:", err);
                alert("Screen share could not be completed.");
            }
        }
    }

    /**
     * Process image file or pasted blob
     */
    function handleImageFile(file, label) {
        if (!file.type.startsWith("image/")) {
            alert("Please select a valid image or screenshot file.");
            return;
        }
        const reader = new FileReader();
        reader.onload = (e) => {
            attachScreenshot(e.target.result, label || "Attached Image");
        };
        reader.readAsDataURL(file);
    }

    /**
     * Attach screenshot to UI preview strip
     */
    function attachScreenshot(dataUrl, label) {
        currentAttachedScreenshot = dataUrl;
        const previewBar = document.getElementById("assistant-screen-preview-bar");
        const previewImg = document.getElementById("assistant-preview-img");
        const previewLabel = document.getElementById("assistant-preview-label");
        const textarea = document.getElementById("assistant-input");

        if (previewBar && previewImg) {
            previewImg.src = dataUrl;
            if (previewLabel) previewLabel.textContent = label || "Screen Attached";
            previewBar.style.display = "flex";
        }

        if (textarea) {
            textarea.focus();
            if (!textarea.value.trim()) {
                textarea.value = "What is on this screen? Where should I click or what should I check?";
            }
        }
    }

    /**
     * Detach screenshot
     */
    function detachScreenshot() {
        currentAttachedScreenshot = null;
        const previewBar = document.getElementById("assistant-screen-preview-bar");
        if (previewBar) previewBar.style.display = "none";
    }

    /**
     * Collect Page State & DOM Telemetry
     */
    function collectPageTelemetry() {
        const alerts = [];
        document.querySelectorAll(".alert").forEach((el) => {
            if (el.offsetParent !== null) {
                const text = el.innerText.trim();
                if (text) alerts.push(text.replace(/\s+/g, " "));
            }
        });

        const activeNav = document.querySelector(".navbar-nav .nav-link.active");
        const inputs = {};
        document.querySelectorAll("input[type='text'], textarea").forEach((inp) => {
            if (inp.id && inp.id !== "assistant-input") {
                inputs[inp.id] = inp.value ? `Filled (${inp.value.slice(0, 50)})` : "Empty";
            }
        });

        return {
            url: window.location.href,
            title: document.title,
            path: window.location.pathname,
            active_tab: activeNav ? activeNav.innerText.trim() : "",
            visible_alerts: alerts.slice(0, 3),
            form_state: inputs,
        };
    }

    /**
     * Submit message to Assistant API
     */
    async function submitMessage() {
        if (isWaitingForResponse) return;

        const textarea = document.getElementById("assistant-input");
        const sendBtn = document.getElementById("assistant-btn-send");
        const messageText = textarea ? textarea.value.trim() : "";

        if (!messageText && !currentAttachedScreenshot) return;

        // Hide welcome card once a conversation begins
        const welcomeCard = document.getElementById("assistant-welcome-card");
        if (welcomeCard) welcomeCard.style.display = "none";

        // Snapshot current attached screenshot & message
        const screenshotToSend = currentAttachedScreenshot;
        const textToSend = messageText || "Analyze this screen screenshot.";

        // Clear input and detach preview
        if (textarea) {
            textarea.value = "";
            textarea.style.height = "auto";
        }
        detachScreenshot();

        // Render user message bubble
        renderMessage("user", textToSend, screenshotToSend);

        // Show typing indicator
        setTyping(true);
        isWaitingForResponse = true;
        if (sendBtn) sendBtn.disabled = true;

        const telemetry = collectPageTelemetry();

        try {
            const response = await fetch("/api/assistant/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    message: textToSend,
                    screenshot: screenshotToSend,
                    page_context: telemetry,
                    history: chatHistory.slice(-8),
                }),
            });

            const data = await response.json();
            setTyping(false);
            isWaitingForResponse = false;
            if (sendBtn) sendBtn.disabled = false;

            if (response.ok && data.success) {
                renderMessage("assistant", data.reply, null, data.model_used);
                // Save turn to history
                chatHistory.push({ role: "user", content: textToSend });
                chatHistory.push({ role: "assistant", content: data.reply });
            } else {
                renderMessage("assistant", `⚠️ **Error:** ${data.error || "Unable to get a response from AI Assistant. Please try again."}`);
            }
        } catch (err) {
            console.error("Assistant chat error:", err);
            setTyping(false);
            isWaitingForResponse = false;
            if (sendBtn) sendBtn.disabled = false;
            renderMessage("assistant", "⚠️ **Connection Error:** Could not connect to TRUTH AI assistant server. Please check your internet connection.");
        }
    }

    /**
     * Render Message Bubble
     */
    function renderMessage(role, text, screenshotUrl, modelName) {
        const messagesContainer = document.getElementById("assistant-messages");
        if (!messagesContainer) return;

        const row = document.createElement("div");
        row.className = `assistant-message-row ${role === "user" ? "user-row" : "assistant-row"}`;

        if (role === "assistant") {
            const avatar = document.createElement("div");
            avatar.className = "assistant-avatar-small";
            avatar.innerHTML = '<i class="fa-solid fa-robot text-info"></i>';
            row.appendChild(avatar);
        }

        const bubble = document.createElement("div");
        bubble.className = `assistant-bubble ${role === "user" ? "user-bubble" : "assistant-bubble"}`;

        // If user attached screenshot
        if (screenshotUrl) {
            const img = document.createElement("img");
            img.src = screenshotUrl;
            img.alt = "Shared Screen";
            img.className = "assistant-msg-screenshot";
            img.title = "Click to open full screenshot";
            img.addEventListener("click", () => {
                const w = window.open("");
                w.document.write(`<img src="${screenshotUrl}" style="max-width:100%; height:auto;" />`);
            });
            bubble.appendChild(img);
        }

        // Render text
        if (role === "user") {
            const p = document.createElement("div");
            p.textContent = text;
            bubble.appendChild(p);
        } else {
            const contentDiv = document.createElement("div");
            contentDiv.innerHTML = formatMarkdown(text);
            bubble.appendChild(contentDiv);

            // Add Code block copy buttons
            contentDiv.querySelectorAll("pre").forEach((pre) => {
                const copyBtn = document.createElement("button");
                copyBtn.className = "assistant-code-copy-btn";
                copyBtn.innerHTML = '<i class="fa-regular fa-copy me-1"></i>Copy';
                copyBtn.addEventListener("click", () => {
                    const code = pre.querySelector("code") || pre;
                    navigator.clipboard.writeText(code.innerText).then(() => {
                        copyBtn.innerHTML = '<i class="fa-solid fa-check me-1 text-success"></i>Copied';
                        setTimeout(() => (copyBtn.innerHTML = '<i class="fa-regular fa-copy me-1"></i>Copy'), 2000);
                    });
                });
                pre.appendChild(copyBtn);
            });

            // Action toolbar (Copy Message)
            const actions = document.createElement("div");
            actions.className = "assistant-bubble-actions";
            actions.innerHTML = `
                ${modelName ? `<span class="text-secondary small me-auto" style="font-size:0.68rem;"><i class="fa-solid fa-microchip text-info me-1"></i>${escapeHtml(modelName)}</span>` : ""}
                <button type="button" class="assistant-action-btn copy-msg-btn" title="Copy full response">
                    <i class="fa-regular fa-copy me-1"></i> Copy
                </button>
            `;
            const copyBtn = actions.querySelector(".copy-msg-btn");
            if (copyBtn) {
                copyBtn.addEventListener("click", () => {
                    navigator.clipboard.writeText(text).then(() => {
                        copyBtn.innerHTML = '<i class="fa-solid fa-check me-1 text-success"></i> Copied!';
                        setTimeout(() => (copyBtn.innerHTML = '<i class="fa-regular fa-copy me-1"></i> Copy'), 2000);
                    });
                });
            }
            bubble.appendChild(actions);
        }

        row.appendChild(bubble);
        messagesContainer.appendChild(row);
        scrollToBottom();
    }

    /**
     * Markdown Formatter with marked.js or lightweight fallback
     */
    function formatMarkdown(text) {
        if (!text) return "";
        if (window.marked && typeof window.marked.parse === "function") {
            try {
                return window.marked.parse(text);
            } catch (e) {
                console.warn("marked.parse error:", e);
            }
        }

        // Lightweight Markdown Fallback
        let formatted = escapeHtml(text);
        formatted = formatted.replace(/^### (.*$)/gim, "<h3>$1</h3>");
        formatted = formatted.replace(/^## (.*$)/gim, "<h2>$1</h2>");
        formatted = formatted.replace(/^# (.*$)/gim, "<h1>$1</h1>");
        formatted = formatted.replace(/\*\*(.*?)\*\*/gim, "<strong>$1</strong>");
        formatted = formatted.replace(/\*(.*?)\*/gim, "<em>$1</em>");
        formatted = formatted.replace(/`([^`]+)`/gim, "<code>$1</code>");
        formatted = formatted.replace(/^\s*-\s+(.*$)/gim, "<li>$1</li>");
        formatted = formatted.replace(/(<li>.*<\/li>)/gims, "<ul>$1</ul>");
        formatted = formatted.replace(/\n\n/gim, "<br><br>");
        return formatted;
    }

    /**
     * Typing Indicator Control
     */
    function setTyping(show) {
        const indicator = document.getElementById("assistant-typing-indicator");
        if (indicator) {
            indicator.style.display = show ? "flex" : "none";
            if (show) scrollToBottom();
        }
    }

    /**
     * Reset Chat Session
     */
    function resetChatSession() {
        chatHistory = [];
        detachScreenshot();
        const messagesContainer = document.getElementById("assistant-messages");
        if (messagesContainer) {
            // Keep welcome card only
            const welcomeCard = document.getElementById("assistant-welcome-card");
            messagesContainer.innerHTML = "";
            if (welcomeCard) {
                welcomeCard.style.display = "block";
                messagesContainer.appendChild(welcomeCard);
            }
        }
        setTyping(false);
    }

    /**
     * Scroll Messages to bottom
     */
    function scrollToBottom() {
        const messagesContainer = document.getElementById("assistant-messages");
        if (messagesContainer) {
            setTimeout(() => {
                messagesContainer.scrollTop = messagesContainer.scrollHeight;
            }, 60);
        }
    }

    /**
     * Helper to load external scripts dynamically
     */
    function loadScript(src) {
        return new Promise((resolve, reject) => {
            const script = document.createElement("script");
            script.src = src;
            script.onload = resolve;
            script.onerror = reject;
            document.head.appendChild(script);
        });
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
})();
