"""Self-check for parse_llm_json — run: python -m app.ai.test_parse_llm_json"""

from app.ai.text_utils import parse_llm_json


def demo():
    # plain JSON
    assert parse_llm_json('{"a": 1}') == {"a": 1}

    # fenced JSON, with and without the json tag
    assert parse_llm_json('```json\n{"a": 1}\n```') == {"a": 1}
    assert parse_llm_json('```\n{"a": 1}\n```') == {"a": 1}

    # the actual 500: a field asked for as a string comes back as an object
    out = parse_llm_json(
        '{"reasoning": {"step1": "weighs risk", "step2": "then decides"}}',
        text_fields=("reasoning",),
    )
    assert isinstance(out["reasoning"], str), out
    assert "step1: weighs risk" in out["reasoning"]

    # lists and scalars flatten too; absent fields are left absent
    assert parse_llm_json('{"s": ["a", "b"]}', text_fields=("s",))["s"] == "a\nb"
    assert parse_llm_json('{"s": 3}', text_fields=("s",))["s"] == "3"
    assert parse_llm_json('{"s": null}', text_fields=("s",))["s"] == ""
    assert "missing" not in parse_llm_json('{"a": 1}', text_fields=("missing",))

    # untouched fields keep their structure
    assert parse_llm_json('{"d": {"k": 1}}', text_fields=("other",))["d"] == {"k": 1}

    # prose wrapped around the object (the real Ollama failure)
    assert parse_llm_json("Here is the JSON:\n{\"a\": 1}\nHope that helps!") == {"a": 1}
    assert parse_llm_json("Sure!\n```json\n{\"a\": 1}\n```\nLet me know.") == {"a": 1}
    # nested braces must not truncate at the first closer
    assert parse_llm_json("note: {\"a\": {\"b\": 2}} done")["a"] == {"b": 2}

    # non-JSON and non-object replies raise, so callers fall back to heuristics
    for bad in ("I think they would say yes.", "[1, 2, 3]", ""):
        try:
            parse_llm_json(bad)
        except ValueError:
            pass
        else:
            raise AssertionError(f"expected ValueError for {bad!r}")

    # the failure message must say WHY, so a fallback is diagnosable from logs
    try:
        parse_llm_json('{"outcomes": [{"a": 1}')
    except ValueError as e:
        assert "truncated" in str(e), e
    try:
        parse_llm_json("")
    except ValueError as e:
        assert "empty" in str(e), e

    print("parse_llm_json: all checks passed")


if __name__ == "__main__":
    demo()
