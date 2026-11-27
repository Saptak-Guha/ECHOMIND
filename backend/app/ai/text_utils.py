"""
EchoMind Text Utilities
Shared tokenisation for the keyword-matching heuristics.
"""

import re
from typing import List, Set

# Words carry punctuation in real prose ("motivated," / "confident."). Splitting
# on whitespace alone made every lexicon lookup miss those, silently zeroing the
# emotion, personality and behaviour scores for ordinary sentences.
_WORD_RE = re.compile(r"[a-z0-9']+")


def tokenize(text: str) -> List[str]:
    """Lowercase word tokens with punctuation stripped."""
    return _WORD_RE.findall((text or "").lower())


def token_set(text: str) -> Set[str]:
    """Unique lowercase word tokens, punctuation stripped."""
    return set(tokenize(text))


def demo() -> None:
    """Self-check: punctuation must not hide a keyword."""
    assert tokenize("I am motivated, curious and confident.") == [
        "i", "am", "motivated", "curious", "and", "confident",
    ]
    # The exact regression that zeroed the emotion radar.
    assert "motivated" in token_set("I am motivated, curious and confident.")
    assert "confident" in token_set("Feeling confident!")
    assert "don't" in token_set("I don't know")
    assert tokenize("") == []
    print("text_utils demo ok")


if __name__ == "__main__":
    demo()


# ── LLM JSON parsing ────────────────────────────────────────────────────

import json


def _as_text(value) -> str:
    """Flatten a value into something a Text column will accept."""
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, (int, float, bool)):
        return str(value)
    if isinstance(value, list):
        return "\n".join(_as_text(v) for v in value)
    if isinstance(value, dict):
        # "trait: how it applies" reads better than a raw JSON blob.
        return "\n".join(f"{k}: {_as_text(v)}" for k, v in value.items())
    return str(value)


def _why(text: str, exc: Exception) -> str:
    """Describe an unparseable reply well enough to act on it."""
    if not text:
        return "model returned an empty reply"
    truncated = text.count("{") > text.count("}")
    kind = "reply looks truncated (unbalanced braces)" if truncated else "reply is not JSON"
    return f"{kind}: {exc} | {len(text)} chars, starts {text[:60]!r}, ends {text[-40:]!r}"


def parse_llm_json(response: str, text_fields: tuple = ()) -> dict:
    """Parse a model's JSON reply, tolerating code fences.

    Small local models honour the requested shape only loosely: a field asked
    for as a string comes back as an object often enough that writing it
    straight to a Text column 500s the request. Fields named in `text_fields`
    are flattened to strings so the DB write always succeeds.

    Raises ValueError if the reply is not JSON at all, so callers keep their
    existing fall-back-to-heuristics path.
    """
    text = (response or "").strip()
    if text.startswith("```"):
        parts = text.split("```")
        if len(parts) > 1:
            text = parts[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()

    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        # Small models like to introduce themselves ("Here is the JSON:") or
        # add a closing remark. Retry on the outermost {...} span before
        # giving up and letting the caller fall back to heuristics.
        start, end = text.find("{"), text.rfind("}")
        if start == -1 or end <= start:
            raise ValueError(_why(text, e)) from e
        try:
            data = json.loads(text[start:end + 1])
        except json.JSONDecodeError:
            raise ValueError(_why(text, e)) from e

    if not isinstance(data, dict):
        raise ValueError(f"model returned {type(data).__name__}, expected object")

    for field in text_fields:
        if field in data:
            data[field] = _as_text(data[field])
    return data
