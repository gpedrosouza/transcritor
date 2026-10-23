"""Fail if an installed dependency has a license outside the allowlist."""

import json
import subprocess
import sys

from transcritor_core.licenses import is_allowed

# Package name -> reason, for packages verified by hand (needs an ADR).
OVERRIDES: dict[str, str] = {}

WORKSPACE_PREFIXES = ("transcritor-", "transcritor_")


def main() -> int:
    result = subprocess.run(
        ["pip-licenses", "--from=mixed", "--format=json"],
        check=True,
        capture_output=True,
        text=True,
    )
    packages: list[dict[str, str]] = json.loads(result.stdout)
    rejected = 0
    checked = 0
    for pkg in packages:
        name = pkg["Name"]
        if name.lower().startswith(WORKSPACE_PREFIXES) or name in OVERRIDES:
            continue
        checked += 1
        license_name = pkg["License"]
        if not is_allowed(license_name):
            rejected += 1
            print(f"{name} {pkg['Version']}: {license_name}")
    print(f"{checked} packages checked, {rejected} rejected")
    return 1 if rejected else 0


if __name__ == "__main__":
    sys.exit(main())
