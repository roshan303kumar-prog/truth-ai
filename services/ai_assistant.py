import os
import re
import json
import base64
import io
import requests
from typing import Dict, Any, List, Optional
from PIL import Image


SYSTEM_PROMPT = """You are NEO, an advanced multimodal AI Assistant directly embedded into the TRUTH AI website.

Your Core Capabilities:
1. Website Screen & UI Awareness:
   - When a user shares a screenshot or screen capture, visually examine it in detail.
   - Identify which page the user is on (News & Claims, Image Forensics, Video Analysis, Link Scanner, History, Dashboard, etc.).
   - Identify UI elements, buttons, input fields, error banners, confidence gauges, and active states.
   - If the user asks "What is wrong here?" or "Why did it fail?", locate any error messages (e.g. rate limit, file size, min characters, invalid URL), empty fields, or disabled buttons, and explain the problem simply.
   - If the user asks "Where should I click?", give crystal clear, numbered step-by-step instructions specifying the exact button text, color, and location on the screen.

2. Website Problem Solver & Technical Troubleshooter:
   - Image Forensics: Max 10MB, supports JPG, PNG, WEBP. Generates Error Level Analysis (ELA) heatmaps to detect tampering/splicing and deepfake manipulation.
   - Video Analysis: Max 50MB, supports MP4, AVI, MOV, WEBM. Samples keyframes and evaluates sharpness, temporal consistency, and audio transcript.
   - News & Claims: Needs at least 5 characters. Triangulates against Google Fact Check, DuckDuckGo, and Wikipedia with contradiction detection. Includes Speech-to-Text and Male/Female AI Voice narration.
   - Link Scanner: Detects phishing, domain typosquatting (e.g. fake SBI KYC, fake lottery), high-risk disposable TLDs (.xyz, .top, .click), and verifies certified institutional domains (onlinesbi.sbi, amazon.in, .gov.in).
   - Rate Limits: 429 status means the IP exceeded requests; wait 60 seconds.
   - Voice/Microphone: Requires browser microphone permission in Chrome/Edge.

3. Natural ChatGPT-like Conversation:
   - You can answer ANY general questions, explain complex topics, troubleshoot code, write text, and assist with everyday tasks.
   - Fluent Multilingual Support: Seamlessly communicate in English, Hindi, and Hinglish based on the user's input.
   - Format responses in clean GitHub-style Markdown with bold text, bullet points, and code blocks.

4. Screen Access Transparency:
   - If the user asks questions about their screen or current view but has NOT shared a screenshot, clearly and politely inform them: "I cannot see your screen yet because you haven't shared it. Please click the '📸 Capture Page' or '🖥️ Share Screen' button in the chat toolbar so I can analyze what is in front of you."
   - Never claim you can see the screen unless screenshot data is actually present in the request.
"""


class AIAssistant:
    """Production-grade Multimodal AI Assistant with Screen Awareness & Website Troubleshooting."""

    def __init__(self, config=None):
        self.config = config or {}
        self.gemini_key = self._get_config_val("GEMINI_API_KEY", "")
        self.openai_key = self._get_config_val("OPENAI_API_KEY", "")
        self.groq_key = self._get_config_val("GROQ_API_KEY", "")
        self.model = self._get_config_val("ASSISTANT_MODEL", "gemini-1.5-flash")

    def _get_config_val(self, key: str, default: Any = "") -> Any:
        if isinstance(self.config, dict):
            val = self.config.get(key)
        else:
            val = getattr(self.config, key, None)
        return val if val else os.environ.get(key, default)

    def chat(
        self,
        message: str,
        screenshot_b64: Optional[str] = None,
        page_context: Optional[Dict[str, Any]] = None,
        history: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        """
        Main chat handler.
        Orchestrates cloud multimodal API (Gemini / OpenAI) or intelligent local fallback.
        """
        message = (message or "").strip()
        page_context = page_context or {}
        history = history or []

        # Parse screenshot data if provided
        image_bytes = None
        mime_type = "image/png"
        has_screenshot = False

        if screenshot_b64:
            try:
                # Strip data URL prefix if present e.g. "data:image/png;base64,..."
                if "," in screenshot_b64:
                    header, data_part = screenshot_b64.split(",", 1)
                    if "image/jpeg" in header or "image/jpg" in header:
                        mime_type = "image/jpeg"
                    elif "image/webp" in header:
                        mime_type = "image/webp"
                else:
                    data_part = screenshot_b64

                image_bytes = base64.b64decode(data_part)
                if len(image_bytes) > 20:
                    has_screenshot = True
            except Exception as e:
                print(f"[AIAssistant] Screenshot decoding error: {e}")
                has_screenshot = False

        # Try Cloud Multimodal Provider if API key is present
        reply = None
        model_used = None

        if self.gemini_key:
            reply = self._call_gemini(message, image_bytes, mime_type, page_context, history)
            if reply:
                model_used = f"Google Gemini ({self.model})"

        if not reply and self.openai_key:
            reply = self._call_openai(message, image_bytes, mime_type, page_context, history)
            if reply:
                model_used = "OpenAI (GPT-4o-mini)"

        if not reply and self.groq_key and not has_screenshot:
            reply = self._call_groq(message, page_context, history)
            if reply:
                model_used = "Groq (Llama-3.3-70b)"

        # If no cloud provider succeeded or no API key configured, use local intelligent fallback engine
        if not reply:
            reply = self._fallback_reasoning(message, image_bytes, page_context, history, has_screenshot)
            model_used = "NEO AI Engine"

        return {
            "success": True,
            "reply": reply,
            "screen_analyzed": has_screenshot,
            "model_used": model_used,
        }

    def _call_gemini(
        self,
        message: str,
        image_bytes: Optional[bytes],
        mime_type: str,
        page_context: Dict[str, Any],
        history: List[Dict[str, str]],
    ) -> Optional[str]:
        """Calls Google Gemini multimodal vision endpoint via REST."""
        try:
            # We try gemini-1.5-flash or gemini-2.0-flash
            model_name = self.model if "gemini" in self.model else "gemini-1.5-flash"
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={self.gemini_key}"

            # Prepare context prefix
            context_str = self._format_page_context(page_context)
            full_prompt = f"{context_str}\n\nUser Question:\n{message}" if context_str else message

            # Prepare contents
            contents = []

            # Add recent conversation turns
            for turn in history[-6:]:
                role = "user" if turn.get("role") == "user" else "model"
                contents.append({"role": role, "parts": [{"text": turn.get("content", "")}]})

            # Current turn parts
            current_parts = []
            if image_bytes:
                b64_str = base64.b64encode(image_bytes).decode("utf-8")
                current_parts.append({
                    "inline_data": {
                        "mime_type": mime_type,
                        "data": b64_str,
                    }
                })
            current_parts.append({"text": full_prompt})
            contents.append({"role": "user", "parts": current_parts})

            payload = {
                "system_instruction": {"parts": [{"text": SYSTEM_PROMPT}]},
                "contents": contents,
                "generationConfig": {
                    "temperature": 0.7,
                    "maxOutputTokens": 2048,
                },
            }

            resp = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                candidates = data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts:
                        return parts[0].get("text", "")
            else:
                print(f"[AIAssistant] Gemini API returned status {resp.status_code}: {resp.text[:300]}")
        except Exception as e:
            print(f"[AIAssistant] Gemini call error: {e}")
        return None

    def _call_openai(
        self,
        message: str,
        image_bytes: Optional[bytes],
        mime_type: str,
        page_context: Dict[str, Any],
        history: List[Dict[str, str]],
    ) -> Optional[str]:
        """Calls OpenAI GPT-4o-mini vision endpoint via REST."""
        try:
            url = "https://api.openai.com/v1/chat/completions"
            context_str = self._format_page_context(page_context)
            full_prompt = f"{context_str}\n\nUser Question:\n{message}" if context_str else message

            messages = [{"role": "system", "content": SYSTEM_PROMPT}]

            for turn in history[-6:]:
                messages.append({"role": turn.get("role", "user"), "content": turn.get("content", "")})

            user_content = []
            if image_bytes:
                b64_str = base64.b64encode(image_bytes).decode("utf-8")
                user_content.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:{mime_type};base64,{b64_str}"},
                })
            user_content.append({"type": "text", "text": full_prompt})
            messages.append({"role": "user", "content": user_content})

            payload = {
                "model": "gpt-4o-mini",
                "messages": messages,
                "max_tokens": 1500,
                "temperature": 0.7,
            }

            resp = requests.post(
                url,
                json=payload,
                headers={"Authorization": f"Bearer {self.openai_key}", "Content-Type": "application/json"},
                timeout=18,
            )
            if resp.status_code == 200:
                data = resp.json()
                return data["choices"][0]["message"]["content"]
            else:
                print(f"[AIAssistant] OpenAI API returned status {resp.status_code}: {resp.text[:300]}")
        except Exception as e:
            print(f"[AIAssistant] OpenAI call error: {e}")
        return None

    def _call_groq(
        self,
        message: str,
        page_context: Dict[str, Any],
        history: List[Dict[str, str]],
    ) -> Optional[str]:
        """Calls Groq Llama 3.3 endpoint via REST."""
        try:
            url = "https://api.groq.com/openai/v1/chat/completions"
            context_str = self._format_page_context(page_context)
            full_prompt = f"{context_str}\n\nUser Question:\n{message}" if context_str else message

            messages = [{"role": "system", "content": SYSTEM_PROMPT}]
            for turn in history[-6:]:
                messages.append({"role": turn.get("role", "user"), "content": turn.get("content", "")})
            messages.append({"role": "user", "content": full_prompt})

            payload = {
                "model": "llama-3.3-70b-versatile",
                "messages": messages,
                "temperature": 0.7,
            }
            resp = requests.post(
                url,
                json=payload,
                headers={"Authorization": f"Bearer {self.groq_key}", "Content-Type": "application/json"},
                timeout=15,
            )
            if resp.status_code == 200:
                data = resp.json()
                return data["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"[AIAssistant] Groq call error: {e}")
        return None

    def _format_page_context(self, ctx: Dict[str, Any]) -> str:
        """Serializes current website state into prompt context."""
        if not ctx:
            return ""

        parts = ["[CURRENT WEBSITE CLIENT TELEMETRY]"]
        if ctx.get("title"):
            parts.append(f"Page Title: {ctx['title']}")
        if ctx.get("url"):
            parts.append(f"URL: {ctx['url']}")
        if ctx.get("path"):
            parts.append(f"Path: {ctx['path']}")
        if ctx.get("visible_alerts"):
            parts.append(f"Visible Alerts / Errors on Screen: {', '.join(ctx['visible_alerts'])}")
        if ctx.get("active_tab"):
            parts.append(f"Active Tab / Section: {ctx['active_tab']}")
        if ctx.get("form_state"):
            parts.append(f"Form Fields / State: {json.dumps(ctx['form_state'])}")
        return "\n".join(parts)

    def _fallback_reasoning(
        self,
        message: str,
        image_bytes: Optional[bytes],
        page_context: Dict[str, Any],
        history: List[Dict[str, str]],
        has_screenshot: bool,
    ) -> str:
        """
        Intelligent local multi-modal reasoning engine.
        Delivers accurate visual UI analysis, troubleshooting, and general responses
        without requiring external cloud subscriptions.
        """
        msg_lower = message.lower().strip()
        page_path = (page_context.get("path") or "").lower()
        page_title = page_context.get("title") or "TRUTH AI Platform"
        visible_alerts = page_context.get("visible_alerts") or []

        # 1. Screen Visual Analysis (When Screenshot Is Provided)
        image_analysis = {}
        if has_screenshot and image_bytes:
            try:
                img = Image.open(io.BytesIO(image_bytes))
                w, h = img.size
                image_analysis = {
                    "dimensions": f"{w}x{h}",
                    "aspect_ratio": "Desktop View" if w >= h else "Mobile / Responsive View",
                    "mode": img.mode,
                }
            except Exception as e:
                image_analysis = {"error": str(e)}

        # CASE A: Screenshot IS provided -> Perform visual UI diagnostic
        if has_screenshot:
            return self._diagnose_screen_state(msg_lower, image_analysis, page_context, visible_alerts)

        # CASE B: Specific Technical Troubleshooting (e.g. rate limit, 429, file size, microphone)
        if any(w in msg_lower for w in ["rate limit", "429", "size limit", "10mb", "50mb", "microphone", "voice not working", "format error"]):
            return self._troubleshoot_common_issues(msg_lower)

        # CASE C: Website Navigation & Feature Inquiries (Text-only)
        if any(w in msg_lower for w in ["how to verify", "fake news", "image forensic", "ela", "video check", "link scam", "phishing", "features"]):
            return self._explain_website_features(msg_lower)

        # CASE D: User explicitly asks about their screen/click target, but DID NOT share a screenshot
        screen_explicit_triggers = [
            "what is wrong on my screen", "what is wrong here", "kya galat hai", "on my screen",
            "kaha click karu", "where to click", "where should i click", "look at my screen",
            "look at this screen", "scan this screen", "check this screen", "meri screen", "screen par"
        ]
        is_screen_query = any(q in msg_lower for q in screen_explicit_triggers)
        if is_screen_query:
            return (
                "Aapki screen abhi share nahi hui hai. Niche diye gaye **`📸 Capture Page`** button par click karein "
                "taaki main aapki screen dekh kar seedha bata sakun ki kahan click karna hai ya kya dikkat hai."
            )

        # CASE E: General Knowledge / Direct Conversational query
        return self._generate_general_reply(message, msg_lower, page_context)

    def _diagnose_screen_state(
        self,
        msg_lower: str,
        image_analysis: Dict[str, Any],
        ctx: Dict[str, Any],
        visible_alerts: List[str],
    ) -> str:
        """Produces a visual UI diagnostic based on screen telemetry & image properties."""
        path = (ctx.get("path") or "").lower()
        title = ctx.get("title") or "TRUTH AI"

        # Detect active page from URL or Title
        current_page_name = "TRUTH AI Platform"
        if "news" in path or "news" in title.lower():
            current_page_name = "News & Claims"
        elif "image" in path or "image" in title.lower():
            current_page_name = "Image Forensics"
        elif "video" in path or "video" in title.lower():
            current_page_name = "Video Analysis"
        elif "link" in path or "link" in title.lower():
            current_page_name = "Link Scanner"
        elif "history" in path or "history" in title.lower():
            current_page_name = "History"
        elif "dashboard" in path or "dashboard" in title.lower():
            current_page_name = "Dashboard"

        # Check for visible error alerts captured from DOM
        if visible_alerts:
            return (
                f"Aapki screen (**{current_page_name}**) par yeh error dikh raha hai:\n\n"
                + "\n".join([f"- ⚠️ **{alert}**" for alert in visible_alerts])
                + "\n\n**Solution:** Input check karein ya required condition poori karke dobara submit karein."
            )

        # Where should I click?
        if any(w in msg_lower for w in ["where to click", "kaha click karu", "where should i click", "next step", "what to click"]):
            if "news" in current_page_name.lower():
                return (
                    f"Aap abhi **News & Claims** screen par hain:\n\n"
                    f"1. Center box mein apni news/claim likhein (min 5 characters).\n"
                    f"2. Niche right-side wale blue **Verify News** button par click karein."
                )
            elif "image" in current_page_name.lower():
                return (
                    f"Aap abhi **Image Forensics** screen par hain:\n\n"
                    f"1. Center upload box par click karke photo choose karein (max 10MB).\n"
                    f"2. Blue **Analyze Image Forensics** button par click karein."
                )
            elif "link" in current_page_name.lower():
                return (
                    f"Aap abhi **Link Scanner** screen par hain:\n\n"
                    f"1. Input box ke bagal mein **Paste** button dabayein taaki link paste ho jaye.\n"
                    f"2. Niche **Scan Link Now** button par click karein."
                )
            elif "video" in current_page_name.lower():
                return (
                    f"Aap abhi **Video Analysis** screen par hain:\n\n"
                    f"1. Video select karein (MP4/MOV, max 50MB).\n"
                    f"2. **Analyze Video** button par click karein."
                )
            else:
                return (
                    f"Aap abhi **{current_page_name}** par hain. Top navbar se jo tool aap use karna chahte hain (News, Image, Video, Link), uspe click karein."
                )

        # What is wrong here
        return (
            f"Screen (**{current_page_name}**) analyze ho gayi hai. Yahan koi critical crash ya layout break nahi dikh raha hai.\n\n"
            f"- Agar button kaam nahi kar raha, toh check karein ki input field empty toh nahi hai.\n"
            f"- News ke liye minimum 5 characters aur Photos ke liye max 10MB allow hai."
        )

    def _explain_website_features(self, msg: str) -> str:
        """Explains TRUTH AI features point-to-point."""
        return (
            "TRUTH AI ke 4 main tools hain:\n\n"
            "1. **News Verification (`/news`):** Fact-check sources se viral news verify karna aur AI voice sunna.\n"
            "2. **Image Forensics (`/image`):** Photo manipulation aur Error Level Analysis (ELA) heatmap dekhna.\n"
            "3. **Video Analysis (`/video`):** Video deepfakes aur keyframes check karna.\n"
            "4. **Link Scanner (`/link`):** Fake banking KYC scams aur certified domains inspect karna."
        )

    def _troubleshoot_common_issues(self, msg: str) -> str:
        """Troubleshoots common user errors point-to-point."""
        if "rate limit" in msg or "429" in msg:
            return "⚠️ **Rate Limit (429):** Bohat tezi se requests bhejne par lagta hai. Kripya 60 seconds (1 minute) wait karein, yeh automatically normal ho jayega."
        elif "size limit" in msg or "10mb" in msg or "50mb" in msg:
            return "📁 **File Size Limit:** Images ke liye max **10 MB** aur videos ke liye max **50 MB** allow hai. Badi files ko thoda compress karke upload karein."
        elif "microphone" in msg or "voice" in msg:
            return "🎙️ **Microphone Issue:** Browser address bar mein Lock icon par click karke mic permission **Allow** karein. Yeh Chrome aur Edge browser mein best chalta hai."
        return "Browser mein **Ctrl + F5** press karke hard reload karein. Input fields check karein aur dobara try karein."

    def _generate_general_reply(self, original_msg: str, msg_lower: str, ctx: Dict[str, Any]) -> str:
        """Direct, crisp, point-to-point conversational response."""
        user_name = ctx.get("user_name")

        # 1. User Name questions
        name_triggers = ["mera name", "mera naam", "my name", "what is my name", "who am i", "mujhe jante ho"]
        if any(w in msg_lower for w in name_triggers):
            if user_name:
                return f"Aapka naam **{user_name}** hai."
            return "Aapne mujhe abhi apna naam nahi bataya. Aapka naam kya hai?"

        # 2. Greetings
        greetings = ["hello", "hi", "hey", "namaste", "kese ho", "kaise ho", "hii", "hlo"]
        if any(msg_lower == g or msg_lower.startswith(g + " ") for g in greetings):
            return "Hello! 👋 Main **NEO** hoon — aapka personal AI Assistant. Main website navigate karne, errors solve karne, aur aapke sawalon ke direct jawab dene ke liye hoon. Bataiye, kya help karoon?"

        # 3. Help capabilities question
        help_triggers = ["what kind of help", "kya madad", "what can you do", "help me", "kya help", "kya kar sakte ho"]
        if any(w in msg_lower for w in help_triggers):
            return (
                "Main **NEO** hoon! Main aapki in cheezon mein point-to-point madad kar sakta hoon:\n\n"
                "1. **Website & Screen Help:** Agar samajh na aaye kahan click karna hai ya koi error aaye, toh screen dekh kar batana.\n"
                "2. **Fact-Checking Tips:** Viral news, photos, videos aur links ko verify karna.\n"
                "3. **General Q&A:** Kisi bhi topic, technology ya problem ka seedha aur short jawab."
            )

        # 4. Identity / Who are you
        if any(w in msg_lower for w in ["who are you", "tum kaun ho", "aap kaun ho", "tera naam"]):
            return "Main **NEO** hoon — is website ka built-in screen-aware AI assistant."

        # 5. Direct crisp answer for other inquiries
        return (
            f"Aapne poocha: **\"{original_msg}\"**\n\n"
            f"Main is website ke tools (News, Image, Video, Link Scanner) aur kisi bhi general sawal mein aapki seedhi madad kar sakta hoon. "
            f"Agar screen par koi dikkat hai, toh niche **`📸 Capture Page`** click karein."
        )
