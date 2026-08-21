"""Run the local release gate used by contributors and CI."""

import subprocess
import sys
from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    commands = [
        ["uv", "lock", "--check"],
        ["uv", "run", "ruff", "format", "--check", "."],
        ["uv", "run", "ruff", "check", "."],
        ["uv", "run", "mypy", "src"],
        [
            "uv",
            "run",
            "pytest",
            "--cov=acrocontract",
            "--cov-report=term-missing",
            "--cov-fail-under=85",
        ],
        ["uv", "run", sys.executable, "-m", "build"],
    ]
    for command in commands:
        subprocess.run(command, cwd=root, check=True)
    artifacts = [
        str(path)
        for pattern in ("*.whl", "*.tar.gz")
        for path in sorted((root / "dist").glob(pattern))
    ]
    subprocess.run(["uv", "run", "twine", "check", *artifacts], cwd=root, check=True)


if __name__ == "__main__":
    main()
