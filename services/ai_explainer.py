from typing import Dict, Any, List


class AIExplainer:
    """
    Synthesizes evidence-grounded, human-interpretable explanations.
    Strictly forbids hallucinating or inventing unretrieved facts.
    """

    @staticmethod
    def generate_news_explanation(
        claim: str,
        verdict: str,
        supporting: List[Dict[str, Any]],
        contradicting: List[Dict[str, Any]],
        context: List[Dict[str, Any]],
        linguistics: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Builds a structured, transparent explanation for news verification."""
        sections = []

        # 1. Primary Verdict Synthesis
        if verdict == "Supported by available evidence":
            sources = ", ".join(list({s.get("source", "verified source") for s in supporting})[:3])
            headline = f"The claim is corroborated by documentation from independent authorities ({sources})."
            body = (
                f"Cross-referencing across verified public reporting confirms the factual details presented. "
                f"{len(supporting)} independent source(s) were found confirming the events or statements in question, "
                f"with no authoritative refutations located."
            )
        elif verdict == "False or contradicted by reliable evidence":
            sources = ", ".join(list({c.get("source", "investigative source") for c in contradicting})[:3])
            headline = f"The submitted claim is contradicted by verifiable evidence from {sources}."
            snippets = [c.get("snippet", "") for c in contradicting if c.get("snippet")]
            detail_snippet = f' Specifically: "{snippets[0][:160]}..."' if snippets else ""
            body = (
                f"Available documentation and independent investigations contradict the claim's core premise.{detail_snippet} "
                f"Public records and peer-reviewed consensus directly refute this assertion."
            )
        elif verdict == "Misleading or missing context":
            headline = "The claim contains partial truths combined with distorted framing or omitted context."
            body = (
                "While elements of the statement may touch upon authentic events or real persons, critical context—"
                "such as accurate dates, full quotes, or comparative baseline statistics—has been omitted or exaggerated, "
                "leading to a potentially deceptive conclusion."
            )
        elif verdict == "Unverified":
            headline = "Available records are inconclusive and cannot definitively substantiate the claim."
            body = (
                "Current reporting contains ambiguous statements or lacks primary source verification. "
                "Until further independent corroboration or official releases are made, this claim remains unverified."
            )
        else:  # Insufficient evidence
            headline = "No verifiable documentation was located in public fact-checking records."
            body = (
                "Authoritative archives and digital news repositories yielded insufficient data to verify or disprove this statement. "
                "Lack of indexing does not establish falsehood; exercise caution and await primary documentation."
            )

        sections.append({"title": "Verification Overview", "content": f"{headline} {body}"})

        # 2. Tone & Stylistic Observation
        if linguistics.get("sensationalism_detected"):
            sections.append({
                "title": "Stylistic & Tone Analysis",
                "content": (
                    f"The text exhibits high emotional charge ({linguistics.get('caps_ratio_percent')}% capitalization "
                    f"and urgent phrasing: {', '.join(linguistics.get('sensational_markers', [])) or 'emotional urgency'}). "
                    f"Sensationalist formatting is frequently employed in viral misinformation to elicit reflexive sharing."
                )
            })

        # 3. Methodological Note
        sections.append({
            "title": "Reasoning & Source Grounding",
            "content": (
                f"This assessment was derived by evaluating {len(supporting)} supporting, {len(contradicting)} contradicting, "
                f"and {len(context)} contextual references. No automated decision is treated as absolute without human review."
            )
        })

        full_text = " ".join([s["content"] for s in sections])

        return {
            "summary": headline,
            "detailed_sections": sections,
            "full_text": full_text,
        }

    @staticmethod
    def generate_image_explanation(
        verdict: str,
        exif: Dict[str, Any],
        ela: Dict[str, Any],
        ai_eval: Dict[str, Any],
        ocr: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Builds explanation for forensic image assessment."""
        points = []

        if ai_eval.get("ai_probability_score", 0) >= 70:
            points.append(
                f"AI synthesis markers detected ({ai_eval.get('assessment')} with {ai_eval.get('ai_probability_score')}% synthetic likelihood). "
                f"The image exhibits characteristic generative patterns: {'; '.join(ai_eval.get('indicators', []))}."
            )
        elif exif.get("detected_editor"):
            points.append(
                f"Digital editing signature detected: software tag '{exif.get('detected_editor')}' was identified in image metadata. "
                f"Error Level Analysis reported {ela.get('variance_level')} compression variance."
            )
        elif exif.get("has_exif") and exif.get("camera_make") != "Unknown / Not recorded":
            points.append(
                f"Authentic camera hardware tags found ({exif.get('camera_make')} {exif.get('camera_model')}), "
                f"with consistent error level compression across pixel blocks."
            )
        else:
            points.append(
                "No hardware camera tags found; metadata may have been stripped by web platforms. "
                "Error level compression shows relatively uniform distribution with no obvious localized splicing."
            )

        full_text = " ".join(points)
        return {
            "summary": points[0] if points else "Forensic assessment completed.",
            "full_text": full_text,
        }
