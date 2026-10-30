"""Unit tests for provider.py — all pure-logic paths, no live API calls."""
from backend.app.llm.provider import _cache_key, _strip_think, parse_json


# ── cache key ───────────────────────────────────────────────────────────────

def test_cache_key_differs_by_provider():
    k1 = _cache_key("sarvam", "sarvam-105b", "sys", "user")
    k2 = _cache_key("anthropic", "claude-3", "sys", "user")
    assert k1 != k2


def test_cache_key_differs_by_model():
    k1 = _cache_key("sarvam", "sarvam-105b", "sys", "user")
    k2 = _cache_key("sarvam", "sarvam-105b-conversations", "sys", "user")
    assert k1 != k2


def test_cache_key_same_inputs_deterministic():
    k1 = _cache_key("sarvam", "sarvam-105b", "sys", "user")
    k2 = _cache_key("sarvam", "sarvam-105b", "sys", "user")
    assert k1 == k2


# ── think-block stripping ───────────────────────────────────────────────────

def test_strip_think_removes_block():
    raw = "<think>let me reason about this</think>\n{\"key\": \"value\"}"
    assert _strip_think(raw) == '{"key": "value"}'


def test_strip_think_multiline():
    raw = "<think>\nline1\nline2\n</think>\n{\"a\":1}"
    assert "{" in _strip_think(raw)
    assert "<think>" not in _strip_think(raw)


def test_strip_think_no_block_unchanged():
    raw = '{"decisions": []}'
    assert _strip_think(raw) == raw


def test_strip_think_case_insensitive():
    raw = "<THINK>reasoning</THINK>{\"x\":1}"
    assert "<THINK>" not in _strip_think(raw)


# ── parse_json ──────────────────────────────────────────────────────────────

def test_parse_json_plain():
    assert parse_json('{"a": 1}') == {"a": 1}


def test_parse_json_strips_markdown_fences():
    raw = "```json\n{\"decisions\": []}\n```"
    assert parse_json(raw) == {"decisions": []}


def test_parse_json_with_leading_think():
    raw = "<think>ignore this</think>\n```json\n{\"decisions\": [1]}\n```"
    assert parse_json(raw) == {"decisions": [1]}


def test_parse_json_raises_on_no_object():
    import pytest
    with pytest.raises(ValueError, match="no JSON object"):
        parse_json("this has no json at all")
