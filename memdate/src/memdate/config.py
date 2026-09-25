"""Configuration: memory root, domain list, and capture discipline.

The domain list is the main decoupling point of the whole package.
Ryan's original skill shipped with his domains (personal, fhk, tribunal,
memory-system, misc). This package ships with neutral defaults and lets
the caller define their own — via constructor, JSON, or a small YAML
subset (top-level keys with scalar or list values only).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field

# Neutral defaults. Nothing Ryan-specific ships here.
DEFAULT_DOMAINS = ("personal", "work", "projects", "reference", "misc")

# Heuristic markers of interpretation inside a capture entry.
# CAPTURE preserves; these phrases suggest the entry is synthesizing.
DEFAULT_INTERPRETATION_MARKERS = (
    "in summary",
    "in conclusion",
    "to summarize",
    "overall,",
    "the takeaway",
    "the bottom line",
    "what this means is",
    "in other words,",
    "therefore we should",
    "we should therefore",
)

DROP_SUBDIRS = ("NEW", "PROCESSED", "PENDING", "QUARANTINE")


class ConfigError(ValueError):
    """Raised for invalid configuration."""


@dataclass
class MemoryConfig:
    """Everything the library needs to find and govern a memory store."""

    root: str
    domains: tuple[str, ...] = DEFAULT_DOMAINS
    interpretation_markers: tuple[str, ...] = DEFAULT_INTERPRETATION_MARKERS
    drop_subdirs: tuple[str, ...] = DROP_SUBDIRS

    def __post_init__(self) -> None:
        if not self.root:
            raise ConfigError("Memory root must not be empty.")
        if not self.domains:
            raise ConfigError("Domain list must not be empty.")
        seen: set[str] = set()
        for d in self.domains:
            name = d.strip()
            if not name:
                raise ConfigError("Domain names must not be blank.")
            if "/" in name or "\\" in name or name in (".", ".."):
                raise ConfigError(f"Invalid domain name: {d!r}.")
            if name.lower() in seen:
                raise ConfigError(f"Duplicate domain: {name!r}.")
            seen.add(name.lower())
        self.domains = tuple(d.strip() for d in self.domains)

    @classmethod
    def from_dict(cls, data: dict) -> "MemoryConfig":
        root = data.get("root")
        if not root:
            raise ConfigError("Config needs a 'root' key.")
        return cls(
            root=root,
            domains=tuple(data.get("domains", DEFAULT_DOMAINS)),
            interpretation_markers=tuple(
                data.get("interpretation_markers", DEFAULT_INTERPRETATION_MARKERS)
            ),
        )

    @classmethod
    def from_json(cls, path: str) -> "MemoryConfig":
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            raise ConfigError(f"{path}: top-level JSON value must be an object.")
        return cls.from_dict(data)

    @classmethod
    def from_yaml(cls, path: str) -> "MemoryConfig":
        """Parse a strict, tiny YAML subset.

        Supported: top-level ``key: value`` pairs and ``key:`` followed by
        ``- item`` list lines. Comments (#) and blank lines ignored.
        Anything else raises ConfigError. This is deliberately not a
        general YAML parser — stdlib has none, and a memory config
        doesn't need one.
        """
        data: dict[str, object] = {}
        current_key: str | None = None
        with open(path, encoding="utf-8") as f:
            for lineno, raw in enumerate(f, 1):
                line = raw.split("#", 1)[0].rstrip()
                if not line.strip():
                    continue
                if line != line.lstrip():
                    stripped = line.strip()
                    if stripped.startswith("- ") and current_key is not None:
                        item = stripped[2:].strip().strip("'\"")
                        lst = data.get(current_key)
                        if not isinstance(lst, list):
                            raise ConfigError(
                                f"{path}:{lineno}: list item without a list key."
                            )
                        lst.append(item)
                        continue
                    raise ConfigError(
                        f"{path}:{lineno}: unsupported indented line: {raw.rstrip()!r}."
                    )
                if ":" not in line:
                    raise ConfigError(
                        f"{path}:{lineno}: expected 'key: value': {raw.rstrip()!r}."
                    )
                key, _, value = line.partition(":")
                key = key.strip()
                value = value.strip().strip("'\"")
                if not key:
                    raise ConfigError(f"{path}:{lineno}: blank key.")
                if value:
                    data[key] = value
                    current_key = None
                else:
                    data[key] = []
                    current_key = key
        return cls.from_dict(data)

    def domain_dir(self, domain: str) -> str:
        """Relative path of a domain's directory inside the root."""
        self.require_domain(domain)
        return domain

    def require_domain(self, domain: str) -> str:
        name = domain.strip()
        known = {d.lower(): d for d in self.domains}
        if name.lower() not in known:
            raise ConfigError(
                f"Unknown domain {domain!r}. Known domains: "
                f"{', '.join(self.domains)}."
            )
        return known[name.lower()]
