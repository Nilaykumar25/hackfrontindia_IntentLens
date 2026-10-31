"""LLM + embedding abstraction. Swap providers via LLM_PROVIDER in .env.

Sarvam notes (verified against docs 2025-10):
  - Endpoint: POST /v1/chat/completions
  - Auth:     api-subscription-key header  (Bearer also accepted but we prefer the key header)
  - Models:   sarvam-105b, sarvam-105b-conversations  (sarvam-m is legacy)
  - response_format: {"type": "json_object"} is supported and guarantees valid JSON output
  - reasoning_effort: "low" | "high" | "max" (default "medium" on v1)
  - Response shape: OpenAI-compatible; usage dict has completion_tokens/prompt_tokens/total_tokens
  - sarvam-105b on v1 does NOT return reasoning_content, but we defensively strip <think> blocks
    in case of future model changes or if the caller switches to a reasoning variant
  - Rate limit: 429; transient errors: 5xx.  We retry with exponential backoff on both.
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import time
from abc import ABC, abstractmethod
from functools import lru_cache

import httpx

from ..config import settings

log = logging.getLogger(__name__)

CACHE_DIR = os.path.join(settings.cache_dir, "llm")

# ──────────────────────────────────────────────────────────────────────────────
# JSON helpers
# ──────────────────────────────────────────────────────────────────────────────

_THINK_RE = re.compile(r"<think>.*?</think>", re.DOTALL | re.IGNORECASE)


def _strip_think(raw: str) -> str:
    """Remove any <think>…</think> reasoning block before JSON parsing."""
    return _THINK_RE.sub("", raw).strip()


def parse_json(raw: str) -> dict:
    raw = _strip_think(raw)
    raw = re.sub(r"^```(?:json)?|```$", "", raw, flags=re.MULTILINE).strip()
    start, end = raw.find("{"), raw.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("no JSON object found in LLM output")
    return json.loads(raw[start : end + 1])


# ──────────────────────────────────────────────────────────────────────────────
# Cache key helpers
# ──────────────────────────────────────────────────────────────────────────────

def _cache_key(provider: str, model: str, system: str, user: str) -> str:
    """Cache key includes provider + model so switching providers/models busts the cache."""
    blob = f"{provider}|{model}|{system}|{user}"
    return hashlib.sha256(blob.encode()).hexdigest()


# ──────────────────────────────────────────────────────────────────────────────
# Base class
# ──────────────────────────────────────────────────────────────────────────────

class LLM(ABC):
    provider: str = "unknown"
    model: str = "unknown"

    @abstractmethod
    def _complete(self, system: str, user: str, max_tokens: int) -> str: ...

    def complete(self, system: str, user: str, max_tokens: int = 1500, cache: bool = True) -> str:
        key = _cache_key(self.provider, self.model, system, user)
        path = os.path.join(CACHE_DIR, key + ".txt")
        if cache and os.path.exists(path):
            return open(path, encoding="utf-8").read()
        out = self._complete(system, user, max_tokens)
        if cache:
            os.makedirs(CACHE_DIR, exist_ok=True)
            open(path, "w", encoding="utf-8").write(out)
        return out

    def complete_json(self, system: str, user: str, max_tokens: int = 1500) -> dict:
        sys2 = system + "\nRespond with a single JSON object only. No prose, no markdown fences."
        raw = self.complete(sys2, user, max_tokens)
        try:
            return parse_json(raw)
        except Exception:
            repair = self.complete(
                sys2,
                user + "\n\nYour previous reply was not valid JSON. Reply with valid JSON only.",
                max_tokens,
                cache=False,
            )
            return parse_json(repair)


# ──────────────────────────────────────────────────────────────────────────────
# Anthropic (kept but unused when LLM_PROVIDER=sarvam)
# ──────────────────────────────────────────────────────────────────────────────

class AnthropicLLM(LLM):
    provider = "anthropic"

    def __init__(self) -> None:
        import anthropic
        self.client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        self.model = settings.llm_model

    def _complete(self, system: str, user: str, max_tokens: int) -> str:
        msg = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return "".join(b.text for b in msg.content if getattr(b, "type", "") == "text")


# ──────────────────────────────────────────────────────────────────────────────
# Sarvam
# ──────────────────────────────────────────────────────────────────────────────

_RETRY_STATUSES = {429, 500, 502, 503, 504}
_SARVAM_V1_URL = "https://api.sarvam.ai/v1/chat/completions"


def _sarvam_post(client: httpx.Client, payload: dict) -> dict:
    """POST to Sarvam with exponential backoff on 429/5xx.  Returns the parsed JSON body."""
    for attempt in range(5):
        r = client.post(_SARVAM_V1_URL, json=payload)
        if r.status_code not in _RETRY_STATUSES:
            r.raise_for_status()
            return r.json()
        wait = (2 ** attempt) + 1
        if r.status_code == 429:
            # Honour Retry-After if present, else back off
            retry_after = r.headers.get("Retry-After")
            wait = int(retry_after) if retry_after and retry_after.isdigit() else wait
            log.warning("Sarvam 429 rate-limited; sleeping %ds (attempt %d/5)", wait, attempt + 1)
        else:
            log.warning("Sarvam %d transient error; sleeping %ds (attempt %d/5)", r.status_code, wait, attempt + 1)
        time.sleep(wait)
    r.raise_for_status()
    return r.json()  # unreachable but keeps type checker happy


def _log_usage(data: dict, model: str) -> None:
    usage = data.get("usage")
    if usage:
        rt = (usage.get("completion_tokens_details") or {}).get("reasoning_tokens", 0)
        ct = usage.get("completion_tokens", 0)
        log.info(
            "Sarvam usage model=%s prompt=%d completion=%d (reasoning=%d content=%d) total=%d",
            model,
            usage.get("prompt_tokens", 0),
            ct,
            rt,
            ct - rt,
            usage.get("total_tokens", 0),
        )


class SarvamLLM(LLM):
    """Sarvam /v1/chat/completions.

    Docs: https://docs.sarvam.ai/api-reference/chat/chat-completions-v1
    Auth: api-subscription-key header.
    JSON mode: response_format={"type":"json_object"} guarantees valid JSON output,
    eliminating most parse failures without a retry.
    """
    provider = "sarvam"

    def __init__(self) -> None:
        self.model = settings.sarvam_model
        self._headers = {
            "api-subscription-key": settings.sarvam_api_key,
            "Content-Type": "application/json",
        }

    def _build_payload(self, system: str, user: str, max_tokens: int, json_mode: bool = False) -> dict:
        payload: dict = {
            "model": self.model,
            "max_tokens": max_tokens,
            "temperature": 0.2,
            # Disable reasoning (reasoning_effort=None) — the model otherwise
            # burns ~3000+ tokens on internal reasoning and returns empty content.
            "reasoning_effort": None,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}
        return payload

    def _complete(self, system: str, user: str, max_tokens: int) -> str:
        with httpx.Client(headers=self._headers, timeout=120) as client:
            data = _sarvam_post(client, self._build_payload(system, user, max_tokens))
        _log_usage(data, self.model)
        content = data["choices"][0]["message"]["content"] or ""
        return _strip_think(content)

    def complete_json(self, system: str, user: str, max_tokens: int = 1500) -> dict:
        """Use response_format=json_object for a cleaner first-pass; fall back to repair if needed."""
        sys2 = system + "\nRespond with a single JSON object only. No prose, no markdown fences."
        key = _cache_key(self.provider, self.model, sys2, user)
        path = os.path.join(CACHE_DIR, key + ".txt")
        if os.path.exists(path):
            raw = open(path, encoding="utf-8").read()
        else:
            with httpx.Client(headers=self._headers, timeout=120) as client:
                data = _sarvam_post(client, self._build_payload(sys2, user, max_tokens, json_mode=True))
            _log_usage(data, self.model)
            raw = _strip_think(data["choices"][0]["message"]["content"] or "")
            os.makedirs(CACHE_DIR, exist_ok=True)
            open(path, "w", encoding="utf-8").write(raw)

        try:
            return parse_json(raw)
        except Exception:
            log.warning("Sarvam JSON parse failed on first attempt; retrying with repair prompt")
            with httpx.Client(headers=self._headers, timeout=120) as client:
                repair_data = _sarvam_post(
                    client,
                    self._build_payload(
                        sys2,
                        user + "\n\nYour previous reply was not valid JSON. Reply with valid JSON only.",
                        max_tokens,
                        json_mode=True,
                    ),
                )
            _log_usage(repair_data, self.model)
            repair_raw = _strip_think(repair_data["choices"][0]["message"]["content"] or "")
            return parse_json(repair_raw)


# ──────────────────────────────────────────────────────────────────────────────
# Factory
# ──────────────────────────────────────────────────────────────────────────────

@lru_cache
def get_llm() -> LLM:
    return SarvamLLM() if settings.llm_provider == "sarvam" else AnthropicLLM()


def get_sarvam() -> LLM:
    return SarvamLLM()


# ──────────────────────────────────────────────────────────────────────────────
# Embeddings (local sentence-transformers, no API key needed)
# ──────────────────────────────────────────────────────────────────────────────

@lru_cache
def _embedder():
    try:
        from sentence_transformers import SentenceTransformer
        return SentenceTransformer(settings.embedding_model)
    except Exception:
        return None


def embed(texts: list[str]) -> list[list[float]]:
    model = _embedder()
    if model is None:
        # Fallback: return zero vectors — vector search will be skipped gracefully
        return [[0.0] * settings.embedding_dim for _ in texts]
    return model.encode(texts, normalize_embeddings=True, show_progress_bar=False).tolist()


def cosine(a: list[float], b: list[float]) -> float:
    return float(sum(x * y for x, y in zip(a, b)))  # vectors are already L2-normalised
