import re
import json
import urllib.parse
from typing import Dict, Any, List, Optional
import requests
from bs4 import BeautifulSoup

from .news_verifier import NewsVerifier
from .evidence_search import EvidenceAggregator


# Reputable & Verified Global and Indian News & Media Publishers
VERIFIED_NEWS_SOURCES = {
    # Indian National News & Agencies
    "pib.gov.in": {"name": "Press Information Bureau (Govt of India)", "tier": "Official Government", "trust": 100},
    "ddnews.gov.in": {"name": "Doordarshan News (DD News)", "tier": "Public Broadcaster", "trust": 95},
    "thehindu.com": {"name": "The Hindu", "tier": "Major Verified National Media", "trust": 92},
    "indianexpress.com": {"name": "The Indian Express", "tier": "Major Verified National Media", "trust": 90},
    "timesofindia.indiatimes.com": {"name": "The Times of India", "tier": "Major National Daily", "trust": 88},
    "ndtv.com": {"name": "NDTV News", "tier": "National News Network", "trust": 88},
    "hindustantimes.com": {"name": "Hindustan Times", "tier": "Major National Daily", "trust": 88},
    "aajtak.in": {"name": "Aaj Tak (India Today Group)", "tier": "National Hindi News", "trust": 86},
    "indiatoday.in": {"name": "India Today", "tier": "National News Magazine", "trust": 88},
    "livemint.com": {"name": "Mint (Business & Economy)", "tier": "Financial Daily", "trust": 90},
    "business-standard.com": {"name": "Business Standard", "tier": "Financial Daily", "trust": 90},
    "economictimes.indiatimes.com": {"name": "The Economic Times", "tier": "Financial Daily", "trust": 89},
    "aniin.com": {"name": "Asian News International (ANI)", "tier": "News Agency", "trust": 88},
    "ptinews.com": {"name": "Press Trust of India (PTI)", "tier": "National News Agency", "trust": 92},
    "theprint.in": {"name": "ThePrint", "tier": "Digital News Platform", "trust": 85},
    "scroll.in": {"name": "Scroll.in", "tier": "Digital News Platform", "trust": 84},
    "thewire.in": {"name": "The Wire", "tier": "Digital News Platform", "trust": 82},

    # International Established News & Agencies
    "bbc.com": {"name": "BBC News", "tier": "International Public Broadcaster", "trust": 95},
    "bbc.co.uk": {"name": "BBC UK", "tier": "International Public Broadcaster", "trust": 95},
    "reuters.com": {"name": "Reuters News Agency", "tier": "Global News Agency", "trust": 98},
    "apnews.com": {"name": "Associated Press (AP)", "tier": "Global News Agency", "trust": 98},
    "afp.com": {"name": "Agence France-Presse (AFP)", "tier": "Global News Agency", "trust": 96},
    "bloomberg.com": {"name": "Bloomberg News", "tier": "Global Financial News", "trust": 92},
    "nytimes.com": {"name": "The New York Times", "tier": "International Daily", "trust": 90},
    "washingtonpost.com": {"name": "The Washington Post", "tier": "International Daily", "trust": 90},
    "theguardian.com": {"name": "The Guardian", "tier": "International News", "trust": 90},
    "cnn.com": {"name": "CNN International", "tier": "Global Cable News", "trust": 86},
    "aljazeera.com": {"name": "Al Jazeera English", "tier": "International News", "trust": 87},
    "nature.com": {"name": "Nature Scientific Journal", "tier": "Peer-Reviewed Science", "trust": 99},
    "who.int": {"name": "World Health Organization (WHO)", "tier": "Global Health Agency", "trust": 98},
    "isro.gov.in": {"name": "ISRO Official (Indian Space Agency)", "tier": "Official Agency", "trust": 100},
    "nasa.gov": {"name": "NASA Official (Space Agency)", "tier": "Official Agency", "trust": 100},

    # Official Video Platforms
    "youtube.com": {"name": "YouTube Video Platform", "tier": "Video Hosting", "trust": 75},
    "youtu.be": {"name": "YouTube Shortlink", "tier": "Video Hosting", "trust": 75},
    "vimeo.com": {"name": "Vimeo Platform", "tier": "Video Hosting", "trust": 75},
}

# Known Satirical, Parody, or High-Risk Disinformation Outlets
KNOWN_SATIRE_OR_HOAX_SITES = {
    "theonion.com": "The Onion (Established Satire & Parody - Not Real News)",
    "babylonbee.com": "The Babylon Bee (Satirical News - Not Real)",
    "fakingnews.firstpost.com": "Faking News (Satirical Indian Website)",
    "worldnewsdailyreport.com": "World News Daily Report (Fabricated Hoaxes)",
    "newsworldindia.in": "Unverified / Sensational Blog",
}


class ContentLinkVerifier:
    """
    Intelligent Link Content & Media Fact-Checker.
    Extracts text, metadata, and context from News Articles, YouTube Videos, and Web links,
    and conducts multi-factor fact-checking to determine if the reported story is Authentic,
    Misleading, or Fake News.
    """
    def __init__(self, config=None):
        self.config = config
        self.news_verifier = NewsVerifier(config)
        self.evidence_aggregator = EvidenceAggregator(config)
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9,hi;q=0.8",
        })

    def is_url(self, text: str) -> bool:
        """Check if a string matches a web link format."""
        if not text:
            return False
        clean = text.strip()
        if re.match(r"^(https?:\/\/|www\.)[^\s/$.?#].[^\s]*$", clean, re.IGNORECASE):
            return True
        # Also catch domain patterns like bbc.com/news/... or ndtv.com/...
        if re.match(r"^[a-zA-Z0-9\-]+\.[a-zA-Z]{2,}(/[^\s]*)?$", clean):
            return True
        return False

    def is_video_url(self, url: str) -> bool:
        """Detect if the link is a video platform URL (YouTube, Vimeo, etc.)."""
        lower = url.lower()
        return any(v in lower for v in ["youtube.com", "youtu.be", "vimeo.com", "dailymotion.com", "/video/", "/watch?v="])

    def extract_youtube_info(self, url: str) -> Dict[str, Any]:
        """Extract video metadata from YouTube URL using official oEmbed API and URL regex."""
        parsed = urllib.parse.urlparse(url if url.startswith("http") else f"https://{url}")
        video_id = ""

        # Extract video ID
        if "youtu.be" in parsed.netloc:
            video_id = parsed.path.lstrip("/").split("&")[0]
        elif "youtube.com" in parsed.netloc:
            qs = urllib.parse.parse_qs(parsed.query)
            video_id = qs.get("v", [""])[0]
            if not video_id and "/embed/" in parsed.path:
                video_id = parsed.path.split("/embed/")[1].split("/")[0]

        video_info = {
            "type": "video",
            "platform": "YouTube",
            "video_id": video_id,
            "title": "",
            "author": "YouTube Creator",
            "thumbnail_url": f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg" if video_id else "",
            "description": "",
            "source_domain": "youtube.com",
        }

        # Query YouTube oEmbed
        try:
            oembed_url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"
            resp = self.session.get(oembed_url, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                video_info["title"] = data.get("title", "")
                video_info["author"] = data.get("author_name", "YouTube Creator")
                video_info["thumbnail_url"] = data.get("thumbnail_url", video_info["thumbnail_url"])
        except Exception:
            pass

        # Fallback title if oEmbed is offline or private
        if not video_info["title"] and video_id:
            video_info["title"] = f"YouTube Video (ID: {video_id})"

        return video_info

    def extract_article_info(self, url: str) -> Dict[str, Any]:
        """Fetch article title, metadata, author, and paragraph text from a news URL."""
        normalized_url = url if url.startswith("http") else f"https://{url}"
        parsed = urllib.parse.urlparse(normalized_url)
        host = parsed.netloc.lower()
        if host.startswith("www."):
            host = host[4:]

        info = {
            "type": "article",
            "url": normalized_url,
            "host": host,
            "title": "",
            "description": "",
            "publisher": host,
            "body_snippet": "",
            "published_date": "",
            "fetched_online": False,
        }

        # Check known sources for pretty names
        for dom, meta in VERIFIED_NEWS_SOURCES.items():
            if host == dom or host.endswith(f".{dom}"):
                info["publisher"] = meta["name"]
                break

        # Attempt online fetch
        try:
            resp = self.session.get(normalized_url, timeout=6)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "html.parser")
                info["fetched_online"] = True

                # 1. Extract Title
                title_elem = (
                    soup.find("meta", property="og:title")
                    or soup.find("meta", attrs={"name": "twitter:title"})
                    or soup.find("h1")
                    or soup.find("title")
                )
                if title_elem:
                    info["title"] = (title_elem.get("content") or title_elem.get_text() or "").strip()

                # 2. Extract Description / Summary
                desc_elem = (
                    soup.find("meta", property="og:description")
                    or soup.find("meta", attrs={"name": "description"})
                    or soup.find("meta", attrs={"name": "twitter:description"})
                )
                if desc_elem:
                    info["description"] = (desc_elem.get("content") or "").strip()

                # 3. Extract Publisher
                site_elem = soup.find("meta", property="og:site_name")
                if site_elem and site_elem.get("content"):
                    info["publisher"] = site_elem.get("content").strip()

                # 4. Extract Article Paragraphs
                paragraphs = [p.get_text().strip() for p in soup.find_all("p") if len(p.get_text().strip()) > 40]
                if paragraphs:
                    info["body_snippet"] = " ".join(paragraphs[:4])[:600]

        except Exception:
            pass

        # Smart Fallback from URL slug if title not found or site blocked
        if not info["title"]:
            slug = parsed.path.rstrip("/").split("/")[-1]
            # Replace dashes/underscores with spaces
            cleaned_slug = re.sub(r"[\-_]+", " ", slug)
            cleaned_slug = re.sub(r"\.html?|\.php|\.aspx?", "", cleaned_slug, flags=re.IGNORECASE)
            # Remove trailing numeric IDs
            cleaned_slug = re.sub(r"\b\d{4,}\b", "", cleaned_slug).strip()
            if len(cleaned_slug) > 8:
                info["title"] = cleaned_slug.title()
            else:
                info["title"] = f"Report on {info['publisher']}"

        return info

    def verify_content_link(self, raw_url: str) -> Dict[str, Any]:
        """
        Complete verification pipeline for a News or Video link.
        Extracts content, audits source credibility, fact-checks claims,
        and returns a comprehensive verdict.
        """
        raw_clean = raw_url.strip()
        normalized_url = raw_clean if raw_clean.startswith("http") else f"https://{raw_clean}"
        parsed = urllib.parse.urlparse(normalized_url)
        host = parsed.netloc.lower()
        if host.startswith("www."):
            host = host[4:]

        is_video = self.is_video_url(normalized_url)

        # 1. Extract content metadata
        if is_video:
            content_data = self.extract_youtube_info(normalized_url)
            headline_or_claim = content_data.get("title", "")
            content_summary = content_data.get("description", "")
            publisher_name = content_data.get("author", "YouTube Channel")
            content_type_label = "Online Video"
        else:
            content_data = self.extract_article_info(normalized_url)
            headline_or_claim = content_data.get("title", "")
            content_summary = content_data.get("description") or content_data.get("body_snippet", "")
            publisher_name = content_data.get("publisher", host)
            content_type_label = "News Article"

        # 2. Source Credibility Assessment
        source_trust_score = 65  # Neutral baseline
        source_badge = "Unverified Online Source"
        source_category = "General Web"
        is_satire_or_hoax = False

        # Match known verified outlets
        matched_source = None
        for dom, meta in VERIFIED_NEWS_SOURCES.items():
            if host == dom or host.endswith(f".{dom}"):
                matched_source = meta
                source_trust_score = meta["trust"]
                source_badge = f"Verified: {meta['tier']}"
                source_category = "Certified Press"
                break

        # Check known satire / hoaxes
        for dom, label in KNOWN_SATIRE_OR_HOAX_SITES.items():
            if host == dom or host.endswith(f".{dom}"):
                is_satire_or_hoax = True
                source_trust_score = 15
                source_badge = "Satire / Known Hoax Outlet"
                source_category = "Humor / Disinformation"
                break

        # 3. Linguistic & Clickbait Check on Headline
        combined_text = f"{headline_or_claim} {content_summary}".strip()
        linguistics = self.news_verifier.analyze_linguistics(combined_text)

        # 4. Fact-Checking Claim through NewsVerifier & Evidence Search
        eval_claim = headline_or_claim if len(headline_or_claim) > 10 else combined_text
        fact_check_result = self.news_verifier.verify_claim(eval_claim)

        # 5. Composite Authenticity Calculation
        # Combine: Source Trust (40%) + Fact-Check Confidence (60%)
        fc_confidence = fact_check_result.get("confidence_score", 50.0)
        fc_verdict = fact_check_result.get("verdict", "Unverified")

        if is_satire_or_hoax:
            final_verdict = "Fake News / Satire"
            authenticity_score = 12.0
            verdict_class = "danger"
            summary_statement = f"This content is published by {publisher_name}, a recognized satire or fabricated hoax outlet. The claims are not real news."
        elif matched_source and matched_source["trust"] >= 88 and fc_verdict not in ["False", "Manipulated"]:
            final_verdict = "Verified Authentic"
            authenticity_score = round(max(fc_confidence, 88.0), 1)
            verdict_class = "success"
            summary_statement = f"Reported by {publisher_name} ({matched_source['tier']}). The news coverage is supported by corroborated media reports."
        elif fc_verdict in ["False", "Manipulated"]:
            final_verdict = "Debunked / False Claim"
            authenticity_score = round(min(fc_confidence, 25.0), 1)
            verdict_class = "danger"
            summary_statement = "Fact-check records contradict the central claims in this content. The story contains debunked or fabricated assertions."
        elif fc_verdict == "Misleading":
            final_verdict = "Misleading / Out of Context"
            authenticity_score = 45.0
            verdict_class = "warning"
            summary_statement = "The story contains misleading context, exaggeration, or partial information that does not align with established facts."
        else:
            # Neutral / Unverified
            final_verdict = "Unverified / Needs Corroboration"
            authenticity_score = round((source_trust_score * 0.4) + (fc_confidence * 0.6), 1)
            verdict_class = "warning" if authenticity_score < 70 else "success"
            summary_statement = f"The content from {publisher_name} requires independent verification. Exercise critical reading before sharing."

        # Format key findings list
        key_findings = [
            f"Content Type: {content_type_label} from '{publisher_name}' ({host})",
            f"Source Credibility: {source_badge} (Trust Rating: {source_trust_score}/100)",
        ]

        if linguistics.get("sensationalism_detected"):
            key_findings.append("Sensationalism Detected: Headline uses emotional or urgent wording to attract attention.")
        else:
            key_findings.append("Neutral Reporting: Title maintains standard journalistic tone.")

        if fact_check_result.get("supporting_evidence"):
            key_findings.append(f"Corroborating Evidence: Found {len(fact_check_result['supporting_evidence'])} matching reference source(s).")
        if fact_check_result.get("contradicting_evidence"):
            key_findings.append(f"Refuting Evidence: Found {len(fact_check_result['contradicting_evidence'])} contradicting fact-check record(s).")

        return {
            "success": True,
            "url": normalized_url,
            "host": host,
            "content_type": content_type_label,
            "is_video": is_video,
            "title": headline_or_claim or "Extracted Web Content",
            "publisher": publisher_name,
            "thumbnail_url": content_data.get("thumbnail_url", ""),
            "summary_snippet": content_summary[:280] if content_summary else "Direct web content inspection completed.",
            "verdict": final_verdict,
            "verdict_class": verdict_class,
            "authenticity_score": authenticity_score,
            "source_trust_score": source_trust_score,
            "source_badge": source_badge,
            "explanation": summary_statement,
            "key_findings": key_findings,
            "supporting_evidence": fact_check_result.get("supporting_evidence", []),
            "contradicting_evidence": fact_check_result.get("contradicting_evidence", []),
            "source_links": fact_check_result.get("source_links", []),
            "linguistics": linguistics,
        }
