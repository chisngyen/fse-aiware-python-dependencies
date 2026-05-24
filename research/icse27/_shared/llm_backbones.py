"""Multi-backbone LLM client.

Backbones are config-only — switching from Gemma-2 9B to Qwen2.5-7B is
a single YAML edit, never a code change. Every backbone speaks Ollama's
HTTP API; we keep the abstraction thin to avoid leaking model-specific
quirks into method files.

Token usage is tracked here (not in method files) so it's consistently
reported across methods for G6 efficiency claims.
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from typing import Any

try:
    import requests
except ImportError:  # pragma: no cover
    requests = None  # type: ignore

log = logging.getLogger(__name__)


@dataclass
class BackboneConfig:
    name: str                    # short label for results.csv (e.g. "gemma2-9b")
    ollama_model: str            # model ID for Ollama (e.g. "gemma2:9b")
    base_url: str = "http://localhost:11434"
    temperature: float = 0.0     # deterministic by default for replay
    top_p: float = 1.0
    max_tokens: int = 512
    timeout_sec: int = 120
    supports_json_mode: bool = True
    # Optional: per-backbone prompt prefix (e.g. system message style)
    prompt_prefix: str = ""


@dataclass
class LLMUsage:
    """Cumulative usage counter — surfaced to results for token-cost claims."""

    calls: int = 0
    prompt_chars: int = 0
    response_chars: int = 0
    total_wall_sec: float = 0.0
    errors: int = 0
    by_agent: dict[str, int] = field(default_factory=dict)

    def record(self, agent: str, prompt: str, response: str, dt: float, ok: bool) -> None:
        self.calls += 1
        self.prompt_chars += len(prompt)
        self.response_chars += len(response)
        self.total_wall_sec += dt
        self.by_agent[agent] = self.by_agent.get(agent, 0) + 1
        if not ok:
            self.errors += 1


class LLMBackbone:
    """Thin Ollama HTTP client with deterministic-replay support.

    Methods should call ``generate(prompt, agent_name="...")`` and parse
    the text response themselves. JSON mode is opt-in via ``json_mode=True``.
    """

    def __init__(self, config: BackboneConfig) -> None:
        if requests is None:
            raise RuntimeError("`requests` package is required for LLMBackbone")
        self.config = config
        self.usage = LLMUsage()
        self._session = requests.Session()

    @property
    def name(self) -> str:
        return self.config.name

    def generate(
        self,
        prompt: str,
        agent_name: str = "unknown",
        max_tokens: int | None = None,
        json_mode: bool = False,
        seed: int | None = None,
    ) -> str:
        full_prompt = (self.config.prompt_prefix + prompt) if self.config.prompt_prefix else prompt
        payload: dict[str, Any] = {
            "model": self.config.ollama_model,
            "prompt": full_prompt,
            "stream": False,
            "options": {
                "temperature": self.config.temperature,
                "top_p": self.config.top_p,
                "num_predict": max_tokens or self.config.max_tokens,
            },
        }
        if seed is not None:
            payload["options"]["seed"] = seed
        if json_mode and self.config.supports_json_mode:
            payload["format"] = "json"

        t0 = time.time()
        ok = True
        text = ""
        try:
            r = self._session.post(
                f"{self.config.base_url}/api/generate",
                json=payload,
                timeout=self.config.timeout_sec,
            )
            r.raise_for_status()
            text = r.json().get("response", "")
        except Exception as e:  # noqa: BLE001 — we want to surface and continue
            ok = False
            log.warning("LLM call failed (%s): %s", self.config.name, e)
        finally:
            self.usage.record(agent_name, full_prompt, text, time.time() - t0, ok)
        return text

    def generate_json(
        self,
        prompt: str,
        agent_name: str = "unknown",
        fallback: dict | list | None = None,
        **kwargs: Any,
    ) -> Any:
        text = self.generate(prompt, agent_name=agent_name, json_mode=True, **kwargs)
        text = text.strip()
        if not text:
            return fallback
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Best-effort extraction of the first {...} or [...] block
            for opener, closer in (("{", "}"), ("[", "]")):
                i, j = text.find(opener), text.rfind(closer)
                if 0 <= i < j:
                    try:
                        return json.loads(text[i : j + 1])
                    except json.JSONDecodeError:
                        continue
            return fallback


def load_backbone(config_path: str | "Path") -> LLMBackbone:  # noqa: F821
    """Construct a backbone from a YAML config under configs/backbones/."""
    import yaml
    from pathlib import Path
    p = Path(config_path)
    data = yaml.safe_load(p.read_text(encoding="utf-8"))
    return LLMBackbone(BackboneConfig(**data))
