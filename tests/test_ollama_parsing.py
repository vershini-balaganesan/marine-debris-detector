from analysis.ollama import _build_prompt, parse_analysis_response


def test_parse_markdown_response():
    markdown = """
## Risk Assessment
The risk level is HIGH because the zone shows dense debris accumulation.

## Trend Explanation
The count is rising compared with the previous period, indicating worsening accumulation.

## Dominant Debris Note
Plastic bottles are the dominant debris type in this hotspot zone.

## Cleanup Recommendation
Prioritize a targeted cleanup along the eastern edge and remove plastic bottles first.
"""

    parsed = parse_analysis_response(markdown)

    assert parsed["risk_assessment"] == "The risk level is HIGH because the zone shows dense debris accumulation."
    assert parsed["trend_explanation"] == "The count is rising compared with the previous period, indicating worsening accumulation."
    assert parsed["dominant_debris_note"] == "Plastic bottles are the dominant debris type in this hotspot zone."
    assert parsed["cleanup_recommendation"] == "Prioritize a targeted cleanup along the eastern edge and remove plastic bottles first."


def test_prompt_uses_markdown_directive():
    prompt = _build_prompt({"risk_level": "HIGH"})

    assert "markdown" in prompt.lower()
    assert "## Risk Assessment" in prompt
    assert "JSON object" not in prompt
