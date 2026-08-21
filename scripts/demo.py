"""Run the public end-to-end demo against synthetic fixtures."""

import argparse
import subprocess
import sys
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=Path("output/demo"))
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    output = (root / args.output_dir).resolve()
    output.mkdir(parents=True, exist_ok=True)

    baseline = root / "examples/customer-intake-v1.pdf"
    candidate = root / "examples/customer-intake-v2.pdf"
    snapshot = output / "customer-intake-v1.contract.json"
    diff_report = output / "compatibility.json"
    migrated = output / "migrated-values-v2.json"
    filled = output / "customer-intake-v2.filled.pdf"
    fill_report = output / "fill-report.json"

    subprocess.run(
        [sys.executable, "-m", "acrocontract", "snapshot", str(baseline), "-o", str(snapshot)],
        check=True,
    )
    diff_result = subprocess.run(
        [
            sys.executable,
            "-m",
            "acrocontract",
            "diff",
            str(baseline),
            str(candidate),
            "--format",
            "json",
            "-o",
            str(diff_report),
        ],
        check=False,
    )
    if diff_result.returncode != 1:
        raise SystemExit(f"Expected breaking diff exit 1, received {diff_result.returncode}.")
    subprocess.run(
        [
            sys.executable,
            "-m",
            "acrocontract",
            "migrate-values",
            str(root / "examples/values-v1.json"),
            "--plan",
            str(root / "examples/migration.reviewed.json"),
            "-o",
            str(migrated),
        ],
        check=True,
    )
    subprocess.run(
        [
            sys.executable,
            "-m",
            "acrocontract",
            "fill-test",
            str(candidate),
            str(migrated),
            "-o",
            str(filled),
            "--report",
            str(fill_report),
        ],
        check=True,
    )
    print(f"Demo passed. Artifacts: {output}")


if __name__ == "__main__":
    main()
