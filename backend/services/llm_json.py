import json
import re


class LLMParseError(Exception):
    pass


def get_response_text(response) -> str:
    parts = [block.text for block in response.content if hasattr(block, "text")]
    text = "".join(parts).strip()
    if not text:
        raise LLMParseError("Model returned an empty response")
    return text


def _strip_markdown_fences(text: str) -> str:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*\n?", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\n?```\s*$", "", cleaned)
    return cleaned.strip()


def _extract_json_substring(text: str) -> str:
    for open_ch, close_ch in [("[", "]"), ("{", "}")]:
        start = text.find(open_ch)
        end = text.rfind(close_ch)
        if start != -1 and end > start:
            return text[start : end + 1]
    raise LLMParseError(f"No JSON found in model response: {text[:300]}...")


def parse_llm_json(text: str):
    cleaned = _strip_markdown_fences(text)
    for candidate in (cleaned, _extract_json_substring(cleaned)):
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            continue
    raise LLMParseError(f"Invalid JSON in model response: {text[:300]}...")
