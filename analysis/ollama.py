# analysis/ollama.py
"""
Sends a small, already-calculated zone summary to a locally running Ollama
model and asks it to produce a short interpretive analysis.

IMPORTANT: Ollama does NOT calculate any numbers here. All counts, trends,
and risk levels come from analysis/zone_statistics.py and analysis/risk.py.
Ollama only explains/interprets those numbers in plain language.

If Ollama is unavailable, this module returns a fallback dict built purely
from the rule-based statistics, so the dashboard keeps working.
"""

import base64
import json
import re

import requests

from config import OLLAMA_CONFIG


def parse_analysis_response(raw_text: str) -> dict:
    """Parse markdown-structured hallucination output into the project’s dict format."""
    cleaned = raw_text.strip()
    if not cleaned:
        raise ValueError("Ollama response is empty.")

    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s*```$", "", cleaned)
        cleaned = cleaned.strip()

    if cleaned.lstrip().startswith("{"):
        parsed = json.loads(cleaned)
        if isinstance(parsed, dict):
            return parsed

    sections = {}
    current_heading = None
    for line in cleaned.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith("## "):
            current_heading = line[3:].strip().lower()
            sections[current_heading] = []
            continue
        if current_heading is not None:
            sections[current_heading].append(line)

    if not sections:
        raise ValueError(f"Ollama response is not in the expected markdown structure: {raw_text!r}")

    mapping = {
        "risk assessment": "risk_assessment",
        "trend explanation": "trend_explanation",
        "dominant debris note": "dominant_debris_note",
        "cleanup recommendation": "cleanup_recommendation",
    }

    parsed = {}
    for heading, canonical in mapping.items():
        if heading in sections:
            value = " ".join(part.strip() for part in sections[heading] if part.strip())
            if value:
                parsed[canonical] = value

    required_keys = {"risk_assessment", "trend_explanation", "dominant_debris_note", "cleanup_recommendation"}
    if not required_keys.issubset(parsed.keys()):
        raise ValueError(f"Ollama response missing expected keys: {parsed}")

    return parsed


def _build_prompt(zone_summary: dict) -> str:
    """Builds a prompt instructing the model to interpret, not invent, numbers."""
    summary_json = json.dumps(zone_summary, indent=2)

    return f"""You are analyzing debris detection statistics for a coastal hotspot zone
in a software prototype. The following JSON contains statistics that have
ALREADY been calculated by rule-based code. Do NOT invent or recalculate
any numbers — only interpret the ones given.

Zone summary:
{summary_json}

Return your answer in Markdown with exactly these sections and no extra text:

## Risk Assessment
<one short sentence confirming or explaining the given risk_level>

## Trend Explanation
<one short sentence explaining what the trend means here>

## Dominant Debris Note
<one short sentence about the dominant debris type>

## Cleanup Recommendation
<one short, practical recommendation>

Rules:
- Use plain prose, not bullet points.
- Do not include JSON, code fences, or preamble.
- Do not invent numbers.
- Stay grounded only in the statistics from the zone summary.
"""


def _fallback_response(zone_summary: dict) -> dict:
    """Used when Ollama is unavailable — built only from rule-based data."""
    return {
        "risk_assessment": f"Rule-based risk level: {zone_summary.get('risk_level', 'UNKNOWN')} "
                            f"(Ollama unavailable — LLM interpretation not generated).",
        "trend_explanation": f"Trend: {zone_summary.get('trend', 'Unknown')} "
                              f"({zone_summary.get('current_count')} vs previous "
                              f"{zone_summary.get('previous_count')}).",
        "dominant_debris_note": f"Most frequent debris type: {zone_summary.get('dominant_debris', 'N/A')}.",
        "cleanup_recommendation": "Ollama is offline — showing rule-based statistics only. "
                                   "Start Ollama locally for a generated recommendation.",
        "source": "fallback_rule_based",
    }


def _ollama_error_detail(error):
    """Return Ollama's JSON/text error instead of hiding it behind HTTPError."""
    response = getattr(error, "response", None)
    if response is not None:
        try:
            detail = response.json().get("error")
        except (ValueError, AttributeError):
            detail = None
        if detail:
            return str(detail)
        if response.text.strip():
            return response.text.strip()
    return str(error)


def get_zone_analysis(zone_summary: dict) -> dict:
    """
    Args:
        zone_summary: dict as produced by analysis/zone_statistics.py, e.g.
            {
              "zone_id": "Z03", "current_count": 147, "previous_count": 105,
              "trend": "Increasing", "dominant_debris": "plastic_bottle",
              "class_breakdown": {...}, "risk_level": "HIGH"
            }

    Returns:
        dict with risk_assessment, trend_explanation, dominant_debris_note,
        cleanup_recommendation, and "source" ("ollama" or "fallback_rule_based").
    """
    prompt = _build_prompt(zone_summary)

    try:
        print("Calling Ollama:", OLLAMA_CONFIG["base_url"], "model=", OLLAMA_CONFIG["model"])
        response = requests.post(
            f"{OLLAMA_CONFIG['base_url']}/api/generate",
            json={
                "model": OLLAMA_CONFIG["model"],
                "prompt": prompt,
                "stream": False,
            },
            timeout=OLLAMA_CONFIG["timeout_seconds"],
        )
        response.raise_for_status()
        raw_text = response.json().get("response", "").strip()
        print("RAW OLLAMA RESPONSE:", repr(raw_text))

        parsed = parse_analysis_response(raw_text)
        parsed["source"] = "ollama"
        return parsed

    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
        print("OLLAMA CONNECTION ERROR:", repr(e))
        return _fallback_response(zone_summary)
    except (json.JSONDecodeError, ValueError, requests.exceptions.HTTPError) as e:
        print("OLLAMA PARSE/HTTP ERROR:", repr(e))
        fallback = _fallback_response(zone_summary)
        fallback["risk_assessment"] += (
            f" (Ollama request failed: {_ollama_error_detail(e)})"
        )
        return fallback


def ask_dashboard_chat(question: str, inspection_context: dict) -> dict:
    """Answer a dashboard question using YOLO facts and optional image input."""
    image_base64 = None
    image_path = inspection_context.get("image_path")
    if image_path:
        try:
            with open(image_path, "rb") as image_file:
                image_base64 = base64.b64encode(image_file.read()).decode("ascii")
        except (OSError, TypeError):
            image_base64 = None

    vision_enabled = bool(image_base64 and OLLAMA_CONFIG.get("vision_model"))
    prompt = f"""You are the marine debris dashboard assistant.
Answer the user's question using only the inspection data below.
Use the YOLO detections as the authoritative object observations. If an image is
attached, inspect it visually, but do not replace or contradict the structured
YOLO data. The pollution_level is a transparent prototype heuristic, not a
scientific environmental or health assessment.
Do not invent measurements, causes, locations, or health effects. Explain
uncertainty when the data is insufficient. Answer directly whether the area is
low, medium, or high according to the supplied heuristic and explain the
evidence from count, nearby zones, composition, and confidence.

Inspection data:
{json.dumps(inspection_context, indent=2)}

User question:
{question}
"""

    try:
        response = requests.post(
            f"{OLLAMA_CONFIG['base_url']}/api/generate",
            json={
                "model": OLLAMA_CONFIG["vision_model"] if vision_enabled else OLLAMA_CONFIG["model"],
                "prompt": prompt,
                "stream": False,
                **({"images": [image_base64]} if vision_enabled else {}),
            },
            timeout=OLLAMA_CONFIG["timeout_seconds"],
        )
        response.raise_for_status()
        answer = response.json().get("response", "").strip()
        if not answer:
            raise ValueError("Ollama returned an empty answer")
        return {"answer": answer, "source": "ollama"}
    except requests.exceptions.HTTPError as error:
        if vision_enabled and OLLAMA_CONFIG["model"] != OLLAMA_CONFIG["vision_model"]:
            try:
                response = requests.post(
                    f"{OLLAMA_CONFIG['base_url']}/api/generate",
                    json={
                        "model": OLLAMA_CONFIG["model"],
                        "prompt": prompt,
                        "stream": False,
                    },
                    timeout=OLLAMA_CONFIG["timeout_seconds"],
                )
                response.raise_for_status()
                answer = response.json().get("response", "").strip()
                if answer:
                    return {"answer": answer, "source": "ollama_text_fallback"}
            except (requests.exceptions.RequestException, ValueError, json.JSONDecodeError):
                pass
        nearby_count = len(inspection_context.get("nearby_zones", []))
        return {
            "answer": (
                f"Ollama rejected the request: {_ollama_error_detail(error)}. "
                "The YOLO result contains "
                f"{inspection_context.get('detection_count', 0)} detected object(s) and "
                f"{nearby_count} nearby zone(s)."
            ),
            "source": "ollama_error_fallback",
        }
    except (requests.exceptions.RequestException, ValueError, json.JSONDecodeError) as error:
        nearby_count = len(inspection_context.get("nearby_zones", []))
        return {
            "answer": (
                f"Rule-based inspection: {inspection_context.get('detection_count', 0)} object(s) "
                f"were detected in the image. {nearby_count} nearby zone(s) are within the "
                f"configured analysis area. Ollama is unavailable, so no additional impact "
                f"claim can be made from this data. ({error})"
            ),
            "source": "fallback_rule_based",
        }