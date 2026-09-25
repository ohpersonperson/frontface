"""Frontmatter: parse, render, validate.

Derived artifacts (distilled.md, INDEX-cross-domain.md) carry provenance
frontmatter. raw.md deliberately does not — CAPTURE is an append-only
evidence log, and per-entry protocol metadata would pollute source
fidelity. The protocol stamp lives on the derived representation, never
on the raw record.
"""

from __future__ import annotations


class FrontmatterError(ValueError):
    """Raised when frontmatter is missing or malformed."""


def render(fields: dict[str, object]) -> str:
    """Render a frontmatter block from an ordered field mapping.

    Lists render as one ``- item`` per line; dicts as ``key: value``
    sub-lines; scalars inline. ``None`` values are skipped.
    """
    lines = ["---"]
    for key, value in fields.items():
        if value is None:
            continue
        if isinstance(value, list):
            lines.append(f"{key}:")
            for item in value:
                lines.append(f"  - {item}")
        elif isinstance(value, dict):
            lines.append(f"{key}:")
            for sub, subval in value.items():
                lines.append(f"  {sub}: {subval}")
        else:
            lines.append(f"{key}: {value}")
    lines.append("---")
    return "\n".join(lines) + "\n"


def split(text: str) -> tuple[dict[str, object], str]:
    """Split ``(frontmatter dict, body)``. Raises if the block is absent."""
    if not text.startswith("---"):
        raise FrontmatterError("Document has no frontmatter block (must start with '---').")
    lines = text.splitlines()
    try:
        end = lines.index("---", 1)
    except ValueError:
        raise FrontmatterError("Frontmatter block never closes (missing second '---').")
    fields: dict[str, object] = {}
    current: str | None = None
    for lineno, line in enumerate(lines[1:end], 2):
        stripped = line.strip()
        if not stripped:
            continue
        if line[0] in (" ", "\t"):
            if current is None:
                raise FrontmatterError(f"Line {lineno}: indented line outside a list/dict.")
            container = fields[current]
            if stripped.startswith("- "):
                if not isinstance(container, list):
                    raise FrontmatterError(f"Line {lineno}: list item under scalar key {current!r}.")
                container.append(_scalar(stripped[2:].strip()))
            elif ":" in stripped:
                if isinstance(container, list):
                    if container:
                        raise FrontmatterError(
                            f"Line {lineno}: sub-key under list key {current!r}."
                        )
                    container = {}
                    fields[current] = container
                if not isinstance(container, dict):
                    raise FrontmatterError(f"Line {lineno}: sub-key under non-dict key {current!r}.")
                sub, _, subval = stripped.partition(":")
                container[sub.strip()] = _scalar(subval.strip())
            else:
                raise FrontmatterError(f"Line {lineno}: cannot parse {line!r}.")
            continue
        if ":" not in stripped:
            raise FrontmatterError(f"Line {lineno}: expected 'key: value'.")
        key, _, value = stripped.partition(":")
        key, value = key.strip(), value.strip()
        if not key:
            raise FrontmatterError(f"Line {lineno}: blank key.")
        if value:
            fields[key] = _scalar(value)
            current = None
        else:
            # Could be a list or a dict; decide on first child line.
            fields[key] = []
            current = key
    body = "\n".join(lines[end + 1:])
    return fields, body


def _scalar(value: str) -> object:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
        return value[1:-1]
    return value


def require(fields: dict[str, object], *keys: str, what: str = "document") -> None:
    """Assert required keys are present and non-blank."""
    missing = [k for k in keys if not fields.get(k)]
    if missing:
        raise FrontmatterError(
            f"{what} frontmatter missing required keys: {', '.join(missing)}."
        )
