"""Fail if an installed dependency has a license outside the allowlist."""

import json
import subprocess
import sys
from pathlib import Path

from transcritor_core.licenses import evaluate, normalize_name, workspace_package_names

# Package name -> reason, for packages verified by hand (needs an ADR).
OVERRIDES: dict[str, str] = {}

ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    result = subprocess.run(
        ["pip-licenses", "--from=mixed", "--format=json"],
        check=True,
        capture_output=True,
        text=True,
    )
    packages: list[dict[str, str]] = json.loads(result.stdout)
    skip = workspace_package_names(ROOT) | {normalize_name(n) for n in OVERRIDES}
    checked, rejected = evaluate(packages, skip)
    for line in rejected:
        print(line)
    if checked == 0:
        print("error: no third-party packages were checked (wrong environment?)")
        return 1
    print(f"{checked} packages checked, {len(rejected)} rejected")
    return 1 if rejected else 0


if __name__ == "__main__":
    sys.exit(main())
