"""Dependency license allowlist (see docs/arquitetura/licencas.md)."""

import re
import tomllib
from pathlib import Path

ALLOWED_LICENSES: frozenset[str] = frozenset(
    {
        "MIT",
        "MIT License",
        "MIT-0",
        "MIT-CMU",
        "BSD License",
        "BSD-2-Clause",
        "BSD-3-Clause",
        "0BSD",
        "Apache-2.0",
        "Apache Software License",
        "ISC",
        "ISC License (ISCL)",
        "Zlib",
        "CC0-1.0",
        "PSF-2.0",
        "Python Software Foundation License",
        "MPL-2.0",
        "Mozilla Public License 2.0 (MPL 2.0)",
    }
)

_SEPARATORS = re.compile(r" AND | OR |;")


def is_allowed(expression: str) -> bool:
    """Return True only if every part of the license expression is allowed.

    Parts are split on " AND ", " OR " and ";". Conservative: an OR still
    requires all alternatives to be allowed. Empty or UNKNOWN is rejected.
    """
    parts = [part.strip() for part in _SEPARATORS.split(expression)]
    return all(part in ALLOWED_LICENSES for part in parts)


def normalize_name(name: str) -> str:
    """PEP 503 normalization: lowercase, runs of -_. collapsed to a single -."""
    return re.sub(r"[-_.]+", "-", name).lower()


def workspace_package_names(root: Path) -> set[str]:
    """Normalized names of the workspace members under ``root/packages/*``."""
    names: set[str] = set()
    for pyproject in sorted(root.glob("packages/*/pyproject.toml")):
        data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
        names.add(normalize_name(data["project"]["name"]))
    return names


def evaluate(packages: list[dict[str, str]], skip: set[str]) -> tuple[int, list[str]]:
    """Check pip-licenses entries; return (checked count, rejected report lines).

    ``skip`` holds normalized names to ignore (workspace members only).
    """
    checked = 0
    rejected: list[str] = []
    for pkg in packages:
        if normalize_name(pkg["Name"]) in skip:
            continue
        checked += 1
        if not is_allowed(pkg["License"]):
            rejected.append(f"{pkg['Name']} {pkg['Version']}: {pkg['License']}")
    return checked, rejected
