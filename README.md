# TRUTH AI — AI-Powered Fake News & Multi-Modal Media Verification Engine

> **Tagline:** *"Verify. Analyze. Trust."*  
> **Academic Level:** Level 4 / Senior Capstone Final Year Project  
> **Target OS:** Windows 10 / 11 (with 1-click `start.bat` launcher)

---

## 1. Executive Summary & Project Introduction

In the contemporary digital landscape, information warfare, deepfake technology, viral rumors, and synthetic media threaten public discourse, institutional trust, and journalistic integrity. Conventional verification systems often suffer from two major flaws:
1. **Keyword Overfitting:** Classifying text as "fake" simply because it contains controversial words, or declaring it "authentic" because a matching web search result was retrieved.
2. **Black-Box Finality:** Declaring content fake with arbitrary percentage confidence without disclosing the evidence, source discrepancies, or technical limitations.

**TRUTH AI** is a complete, production-grade web application built to address these challenges with **multi-source evidence triangulation**, **deep optical forensics**, and **explainable AI (XAI)**.

### Core Ethical Axioms of TRUTH AI:
* **The Principle of Multi-Source Triangulation:** Finding a matching search result does not prove a claim is authentic. Independent corroboration across multiple reliable records is required.
* **The Principle of Uncertainty:** If insufficient public evidence exists, the system marks the claim as **"Insufficient evidence"** or **"Unverified"**. It **never** fabricates evidence or falsely condemns claims without verifiable contradictions.
* **Separation of Technical Observation from Conclusion:** Technical markers (e.g., absent camera EXIF tags, localized Error Level Analysis compression spikes) are transparently distinguished from definitive verdicts.

---

## 2. System Architecture & Modalities

```
                        +---------------------------------------+
                        |       TRUTH AI Web Client (UI)        |
                        |   HTML5 / CSS3 Glassmorphism / JS     |
                        +-------------------+-------------------+
                                            |
                                  REST API / Web Form
                                            v
                        +---------------------------------------+
                        |           Flask Application           |
                        |     (Python 3.12 / SQLAlchemy)        |
                        +---+---------------+---------------+---+
                            |               |               |
            +---------------+               |               +---------------+
            v                               v                               v
+-----------------------+       +-----------------------+       +-----------------------+
|  News & Claim Engine  |       |    Photo Forensics    |       |   Video Inspection    |
| - NLP Tokenization    |       | - EXIF & GPS Audit    |       | - OpenCV Keyframes    |
| - Sensationalism Scan |       | - Error Level (ELA)   |       | - Focal Sharpness     |
| - Multi-Source Search |       | - Spectral AI Detect  |       | - Temporal Continuity |
| - Stance Alignment    |       | - Optical OCR Extract |       | - Banner OCR Extract  |
+-----------+-----------+       +-----------+-----------+       +-----------+-----------+
            |                               |                               |
            +-------------------------------+-------------------------------+
                                            |
                                            v
                        +---------------------------------------+
                        |        Explainable Synthesis          |
                        | - 5 Standardized Verdicts             |
                        | - Confidence Tier (0-100%)            |
                        | - Explicit Limitations Disclosure     |
                        | - Direct Source Citations             |
                        +---------------------------------------+
```

### The 5 Standard Verification Categories:
1. `Supported by available evidence` — Confirmed by multiple reliable, independent sources or official documentation.
2. `False or contradicted by reliable evidence` — Directly refuted by investigative findings and reliable records.
3. `Misleading or missing context` — Partial truths combined with selective omissions or distorted framing.
4. `Unverified` — Single source available or conflicting accounts without investigative consensus.
5. `Insufficient evidence` — No public records or fact-checking databases currently index the specific assertion.

---

## 3. Technologies Used

### Frontend Stack
* **HTML5 & CSS3:** Bespoke modern design system featuring dark navy (`#070b14`), midnight blue (`#0c1322`), and cyan (`#00e5ff`) accents with subtle glassmorphism (`backdrop-filter: blur(14px)`).
* **JavaScript (ES6+):** Pure Fetch API for asynchronous background verification without page reloads.
* **Bootstrap 5.3:** Fluid, responsive grid engineered for desktops, tablets, and smartphones.
* **Font Awesome 6:** Comprehensive visual icons for verdicts, metrics, and navigation.
* **Chart.js 4.4:** Interactive canvas data visualizations for verification breakdown and modality analytics.

### Backend Stack
* **Python 3.12:** High-performance, maintainable backend runtime.
* **Flask 3.x:** Modular web framework utilizing the Application Factory Pattern and Blueprints (`views_bp`, `auth_bp`, `api_bp`).
* **Flask-Login:** Session management, persistent authentication, and protected views.
* **Flask-SQLAlchemy:** Database ORM supporting user profiles, audit logs, and settings.
* **Werkzeug:** Industrial-grade password encryption utilizing salted `scrypt` hashing.
* **Flask-CORS:** Secure cross-origin resource sharing for API endpoints.
* **Python-Dotenv:** Seamless environment variable management.

### Database
* **SQLite (Production Embedded):** Zero-configuration, zero-downtime database engine stored at `database/truth_ai.db`.
* **SQLAlchemy Schema:**
  * `User`: Credentials, session metadata, relationships.
  * `VerificationReport`: Polymorphic storage for news, photo, and video verification outputs, serialized JSON arrays for evidence, technical findings, and citations.
  * `UserSettings`: Custom verification toggles and notification preferences.
  * `FeedbackMessage`: Public contact inquiries and academic feedback.

### Computer Vision & Forensic AI
* **Pillow (PIL):** High-precision image manipulation, metadata extraction, and Error Level Analysis (ELA) generation.
* **OpenCV (`opencv-python-headless`):** High-speed video keyframe sampling, Laplacian focal variance computation, and intra-frame continuity analysis.
* **Tesseract OCR (Integration Hook):** Optical character recognition for extracted video banners and text-heavy images.
* **Multi-Provider Search Aggregator:**
  * `Google Fact Check Tools API`: IFCN-certified ClaimReview schema search.
  * `DuckDuckGo Live Search`: Real-time public web indexing and news retrieval.
  * `Wikipedia Reference API`: Encyclopedic and historical grounding.
  * `Curated Ground Truth Engine`: Peer-reviewed scientific database for offline reliability.

---

## 4. Key Features

### 1. Multi-Source News & Claim Verification
* Extracts factual assertions, entities, and numerical claims.
* Scans for clickbait and sensationalism markers (capitalization ratio, emotional urgency terms).
* Retrieves corroborating and contradicting evidence from independent web databases.
* Compares source stances and presents side-by-side evidence tables with direct source links.

### 2. Forensic Image & Splicing Analysis
* **Error Level Analysis (ELA):** Re-saves images at a known compression level (90%) and amplifies pixel difference errors to generate a visual heatmap. Spliced elements and altered regions stand out with elevated error levels.
* **EXIF Metadata Inspector:** Reads camera make, model, lens, original timestamps, and flags editing software signatures (e.g., Photoshop, GIMP, Canva).
* **AI Synthesis Detection:** Identifies generative diffusion parameters (Stable Diffusion chunks, Midjourney prompts) and resolution signatures.
* **Reverse Image Queries:** Generates one-click direct links to Google Lens, TinEye, and Yandex Visual Search.

### 3. Temporal Video & Deepfake Inspection
* Decompresses video containers (MP4, WEBM, AVI, MOV) and samples uniform keyframes.
* Calculates frame-by-frame Laplacian sharpness variance and mean brightness deltas.
* Flags abrupt visual jump cuts, focal shifts, or lighting anomalies.
* Extracts on-screen chyrons and breaking news banners using optical character recognition.

### 4. Interactive Analytics Dashboard
* Real-time metrics counters (Total Checks, Supported, Contradicted, Misleading, Unverified).
* Chart.js Doughnut Chart displaying verdict distributions.
* Chart.js Bar Chart breaking down activity by modality (News, Photos, Videos).
* Recent activity log and bookmarked reports drawer.

---

## 5. Project Directory Structure

```
truth-ai/
├── app.py                      # Application Factory and runtime entrypoint
├── config.py                   # Configuration classes (Development, Testing)
├── requirements.txt            # Pinned, tested dependencies
├── .env.example                # Environment variables template
├── .env                        # Active environment configuration
├── setup.bat                   # 1-Click automated Windows installation script
├── start.bat                   # 1-Click automated Windows startup script
├── seed_db.py                  # Database initialization and demo seeder
├── README.md                   # Full technical and user documentation
│
├── database/                   # Database ORM models and SQLite storage
│   ├── __init__.py             # SQLAlchemy instance
│   ├── models.py               # User, VerificationReport, UserSettings models
│   └── truth_ai.db             # SQLite database file
│
├── services/                   # Core Verification & AI Engines
│   ├── __init__.py
│   ├── evidence_search.py      # Multi-provider search adapters (Google, DDG, Wiki)
│   ├── news_verifier.py        # NLP claim parsing, stance scoring & verdict synthesis
│   ├── image_verifier.py       # EXIF audit, ELA heatmap generator & AI detection
│   ├── video_verifier.py       # OpenCV keyframe extractor & temporal analysis
│   └── ai_explainer.py         # Evidence-grounded plain-English explanations
│
├── routes/                     # Blueprint Route Controllers
│   ├── __init__.py             # Blueprint registrations
│   ├── auth_routes.py          # Registration, login, logout (HTML + JSON API)
│   ├── api_routes.py           # REST endpoints (/api/verify-*, /api/history, etc.)
│   └── view_routes.py          # Page views (Home, News, Image, Video, Dashboard)
│
├── utils/                      # Helper & Security Utilities
│   ├── __init__.py
│   ├── security.py             # Magic byte sniffing, rate limiter, sanitizers
│   └── helpers.py              # Verdict styling, confidence tiers, relative dates
│
├── uploads/                    # Local storage for user uploads
│   ├── images/                 # Uploaded photos
│   ├── videos/                 # Uploaded video files
│   │   └── frames/             # Extracted OpenCV keyframe images
│   └── ela/                    # Generated Error Level Analysis heatmaps
│
├── templates/                  # Jinja2 HTML5 UI Templates
│   ├── base.html               # Master layout with navbar and footer
│   ├── index.html              # Homepage with hero, quick verify & highlights
│   ├── news.html               # News & claim verification studio
│   ├── image.html              # Image forensics & ELA visualizer
│   ├── video.html              # Video temporal analysis & keyframe gallery
│   ├── history.html            # Searchable verification log
│   ├── report.html             # Printable permalink report view
│   ├── dashboard.html          # User analytics & Chart.js graphs
│   ├── about.html              # Project genesis, objectives & architecture
│   ├── how_it_works.html       # Visual pipeline breakdown
│   ├── login.html              # Modern login with demo account auto-fill
│   ├── register.html           # User signup with password strength meter
│   ├── contact.html            # Academic feedback & inquiry form
│   ├── privacy.html            # Transparent privacy policy & ethical standards
│   └── errors/                 # Friendly, safe error templates (400, 404, 500)
│
├── static/                     # Frontend Assets
│   ├── css/
│   │   └── style.css           # Custom dark navy / cyan glassmorphism CSS
│   └── js/
│       ├── main.js             # Global utilities (bookmarks, share links)
│       ├── news.js             # AJAX news submission & step animator
│       ├── image.js            # Image dropzone & ELA side-by-side renderer
│       ├── video.js            # Video dropzone & keyframe carousel renderer
│       └── dashboard.js        # Chart.js initialization & live updates
│
└── tests/                      # Automated Pytest Test Suite (24 Tests)
    ├── __init__.py
    ├── conftest.py             # App fixtures, test client, in-memory DB
    ├── test_auth.py            # Authentication, registration & session tests
    ├── test_news_verifier.py   # Claim NLP, stance detection & fallback tests
    ├── test_image_verifier.py  # Image inspection, EXIF & ELA tests
    ├── test_video_verifier.py  # Keyframe extraction & temporal analysis tests
    ├── test_api_routes.py      # REST API endpoints & JSON response tests
    └── test_security.py        # Magic byte validation & rate limiter tests
```

---

## 6. Beginner-Friendly Windows Setup & Quick Start

The project includes pre-configured automation scripts for Windows 10 and Windows 11.

### Prerequisites
* **Windows 10 / 11**
* **Python 3.12** installed from [python.org](https://www.python.org/downloads/).
  > *Important:* During installation, ensure you check the box: **"Add Python to PATH"**.

---

### Method A: 1-Click Launch (Recommended)
1. Navigate to the project root directory:
   ```cmd
   cd C:\Users\Hp\.gemini\antigravity\scratch\truth-ai
   ```
2. Double-click or run:
   ```cmd
   start.bat
   ```
3. `start.bat` will automatically:
   * Verify the virtual environment (`.venv`). If missing, it automatically triggers `setup.bat`.
   * Initialize the SQLite database and seed initial demo data.
   * Start the Flask development server on `http://127.0.0.1:5000`.
   * Automatically launch your default web browser to the homepage!

---

### Method B: Manual Step-by-Step Setup
If you prefer running commands manually in PowerShell or Command Prompt:

1. **Create and activate a Python 3.12 virtual environment:**
   ```cmd
   py -3.12 -m venv .venv
   .venv\Scripts\activate
   ```

2. **Install tested dependencies:**
   ```cmd
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   ```

3. **Initialize the database with demo accounts & sample reports:**
   ```cmd
   python seed_db.py
   ```

4. **Start the application:**
   ```cmd
   python app.py
   ```

5. **Open your browser:**
   Visit: `http://127.0.0.1:5000`

---

## 7. Pre-Configured Demo Credentials

For quick evaluation during college presentations or grading, a researcher account is pre-seeded into the database:

* **Username:** `demo_user` (or `demo@truth-ai.org`)
* **Password:** `TruthAI@2026`
* *Note:* On the login page, you can simply click the **"Auto-Fill Demo Credentials"** button to populate these fields instantly!

---

## 8. External API Keys & Free-Tier Documentation

TRUTH AI is engineered to be **100% functional out-of-the-box** without any paid services or mandatory API keys. Live search is handled automatically via DuckDuckGo and Wikipedia, backed by a curated ground-truth database.

If you wish to connect additional external providers, configure the following keys in your `.env` file:

| Provider | Purpose | How to Obtain | Free Tier Limitations |
| :--- | :--- | :--- | :--- |
| **Google Fact Check Tools API** | IFCN-certified ClaimReview database | [Google Cloud Console](https://console.cloud.google.com/) -> Enable *Fact Check Tools API* | Free: 10,000 queries per day |
| **DuckDuckGo Search** | Live web news & abstract retrieval | Built-in (no key required) | Free, open access |
| **Wikipedia Reference API** | Factual grounding on entities/history | Built-in (no key required) | Free, open access |
| **NewsAPI (Optional)** | Aggregated global news articles | [newsapi.org](https://newsapi.org) -> Register free API key | Free: 100 requests per day (dev use) |

### Sample `.env` Configuration:
```ini
SECRET_KEY=truth-ai-secure-dev-session-key-2026-xyz789
DATABASE_URL=sqlite:///database/truth_ai.db
GOOGLE_FACT_CHECK_API_KEY=
NEWS_API_KEY=
DUCKDUCKGO_ENABLED=True
WIKIPEDIA_ENABLED=True
OFFLINE_FALLBACK_ENABLED=True
ELA_QUALITY=90
ELA_SCALE=15
MAX_VIDEO_FRAMES=12
```

---

## 9. Automated Testing (Pytest)

The project includes an extensive test suite verifying authentication, linguistic analysis, image forensics, video keyframe analysis, REST API status codes, security magic bytes, and rate limiting.

### Running the Test Suite:
To run the automated tests, execute:
```cmd
.venv\Scripts\python.exe -m pytest -v
```

### Test Results Summary:
```
tests/test_api_routes.py::test_api_verify_news_endpoint PASSED           [  4%]
tests/test_api_routes.py::test_api_verify_news_short_claim_error PASSED  [  8%]
tests/test_api_routes.py::test_api_verify_image_endpoint PASSED          [ 12%]
tests/test_api_routes.py::test_api_history_and_report_detail PASSED      [ 16%]
tests/test_api_routes.py::test_api_dashboard_endpoint PASSED             [ 20%]
tests/test_api_routes.py::test_api_contact_endpoint PASSED               [ 25%]
tests/test_auth.py::test_registration_success PASSED                     [ 29%]
tests/test_auth.py::test_registration_duplicate_username PASSED          [ 33%]
tests/test_auth.py::test_registration_short_password PASSED              [ 37%]
tests/test_auth.py::test_login_success PASSED                            [ 41%]
tests/test_auth.py::test_login_invalid_password PASSED                   [ 45%]
tests/test_auth.py::test_logout PASSED                                   [ 50%]
tests/test_image_verifier.py::test_image_verification_with_generated_jpeg PASSED [ 54%]
tests/test_image_verifier.py::test_ai_generation_assessment_metadata PASSED [ 58%]
tests/test_news_verifier.py::test_sensationalism_detection PASSED        [ 62%]
tests/test_news_verifier.py::test_verify_known_debunked_claim PASSED     [ 66%]
tests/test_news_verifier.py::test_verify_supported_claim PASSED          [ 70%]
tests/test_news_verifier.py::test_verify_insufficient_evidence PASSED    [ 75%]
tests/test_security.py::test_sanitize_input_text PASSED                  [ 79%]
tests/test_security.py::test_validate_image_magic_bytes_spoofing PASSED  [ 83%]
tests/test_security.py::test_validate_image_valid_jpeg PASSED            [ 87%]
tests/test_security.py::test_rate_limiter PASSED                         [ 91%]
tests/test_video_verifier.py::test_video_verifier_temporal_analysis PASSED [ 95%]
tests/test_video_verifier.py::test_video_verifier_anomaly_detection PASSED [100%]

======================= 24 passed in 17.32s ========================
```

---

## 10. Security & Hardening Features

* **Magic Byte File Sniffing:** Uploaded files are inspected for real cryptographic headers (e.g., `\xff\xd8\xff` for JPEG, `\x89PNG` for PNG, `ftyp` for MP4). Disguised executables with `.jpg` or `.mp4` extensions are immediately rejected.
* **Strict Path Sanitization:** Uses `secure_filename` to prevent path traversal attacks (`../`).
* **Executable Shield:** Uploaded files are strictly stored in non-executable static directories and served via `send_from_directory`.
* **Rate Limiting:** Sliding-window rate limiter throttles automated scraping and spam attacks (40 requests per minute per IP).
* **Safe Error Handling:** Production error handlers (400, 404, 413, 429, 500) prevent stack trace exposure to end-users.
* **No Frontend API Exposure:** All external network communications occur server-side; private keys are never exposed in JavaScript bundles.

---

## 11. Academic Evaluation & Capstone Presentation Guide

When demonstrating this project to professors, evaluators, or project juries:

1. **Showcase the Multi-Modal Breadth:**
   * Test a **News Claim** (e.g., *"COVID vaccines contain 5G chips"* to demonstrate refutation, or *"James Webb discovered ancient distant galaxies"* to demonstrate corroboration).
   * Test an **Image** to demonstrate the live Error Level Analysis (ELA) heatmap generation and EXIF software audit.
   * Test a **Video** to demonstrate OpenCV keyframe extraction and temporal lighting consistency checking.
2. **Highlight the Dashboard & History:**
   * Navigate to the **User Dashboard** to display the Chart.js doughnut and bar charts visualizing verification statistics.
   * Open the **Verification History** page to demonstrate filtering by modality, bookmarking, and deletion.
3. **Emphasize Epistemic Honesty:**
   * Point out the **Limitations & Uncertainty** disclosure box on every report.
   * Explain how TRUTH AI rejects black-box certainty and assists human critical inquiry.

---

## 12. License & Author

* **Project:** TRUTH AI — AI-Powered Fake News & Media Verification Engine
* **Version:** 2.4.0 (Production / Capstone Release)
* **Author:** Senior Full-Stack & AI Engineering Team
* **Academic License:** MIT License — Open for academic, research, and educational demonstration.
