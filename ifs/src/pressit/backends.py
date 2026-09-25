"""Swappable LLM backends for the engine.

- StubBackend: deterministic canned JSON for tests and demos. No network.
- OpenRouterBackend: OpenRouter chat completions (documented endpoint
  https://openrouter.ai/api/v1/chat/completions). Key comes from the
  OPENROUTER_API_KEY environment variable at call time — never stored in
  files, never logged. Free-tier friendly.
- OllamaBackend: a local Ollama server (default http://localhost:11434),
  for fully offline runs on Ryan-style local setups.

Only the backend you choose is used. No credentials are exchanged in chat
or files.
"""

from __future__ import annotations

import json
import os
import urllib.request


class StubBackend:
    """Deterministic backend for tests and offline demos."""

    name = "stub"

    def __init__(self, artifact_json: dict) -> None:
        self._artifact_json = artifact_json

    def complete(self, system: str, user: str) -> str:
        return json.dumps(self._artifact_json)


class OpenRouterBackend:
    """OpenRouter chat completions backend.

    Reads OPENROUTER_API_KEY from the environment at call time. Optional
    OPENROUTER_MODEL selects the model (defaults to a free-tier model).
    """

    name = "openrouter"
    ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"

    def __init__(self, model: str | None = None, endpoint: str | None = None) -> None:
        self.model = model or os.environ.get("OPENROUTER_MODEL", "")
        self.endpoint = endpoint or os.environ.get("OPENROUTER_ENDPOINT") or self.ENDPOINT
        if not self.model:
            raise RuntimeError(
                "No model selected: pass model= or set OPENROUTER_MODEL."
            )

    def complete(self, system: str, user: str) -> str:
        key = os.environ.get("OPENROUTER_API_KEY")
        if not key:
            raise RuntimeError(
                "OPENROUTER_API_KEY is not set. Export it before running."
            )
        payload = json.dumps({
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": 0.2,
            "response_format": {"type": "json_object"},
        }).encode()
        req = urllib.request.Request(
            self.endpoint, data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {key}",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                body = json.loads(resp.read().decode())
        except Exception as exc:
            raise RuntimeError(f"OpenRouter request failed: {exc}") from exc
        try:
            return body["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as exc:
            raise RuntimeError(f"Unexpected OpenRouter response shape: {body!r}") from exc


class OllamaBackend:
    """Local Ollama backend (http://localhost:11434 by default)."""

    name = "ollama"

    def __init__(self, model: str = "llama3.1",
                 base_url: str = "http://localhost:11434") -> None:
        self.model = model
        self.base_url = base_url.rstrip("/")

    def complete(self, system: str, user: str) -> str:
        payload = json.dumps({
            "model": self.model,
            "system": system,
            "prompt": user,
            "stream": False,
            "format": "json",
            "options": {"temperature": 0.2},
        }).encode()
        req = urllib.request.Request(
            f"{self.base_url}/api/generate", data=payload,
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=300) as resp:
                body = json.loads(resp.read().decode())
        except Exception as exc:
            raise RuntimeError(f"Ollama request failed: {exc}") from exc
        return body.get("response", "")
