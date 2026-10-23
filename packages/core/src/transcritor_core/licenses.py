"""Dependency license allowlist (see docs/arquitetura/licencas.md)."""

import re

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
