#!/usr/bin/env python3
"""Per-function CRAP score for Python code, from radon complexity and coverage data.

    CRAP = complexity^2 * (1 - coverage)^3 + complexity

Inputs:
  * a coverage JSON report (``coverage json`` or ``pytest --cov --cov-report=json``);
  * radon complexity, either a saved ``radon cc -j`` report (``--radon FILE``) or
    computed on the fly for the given paths if radon is installed.

The score is an indicator, not proof of quality. A high score says "look here":
add behavior tests first, simplify only if the function is genuinely tangled.
The exit code is 0 unless ``--strict`` is given and a function exceeds the threshold.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys


def crap(complexity: int, coverage: float) -> float:
    return complexity**2 * (1 - coverage) ** 3 + complexity


def norm(path: str) -> str:
    return os.path.normcase(os.path.realpath(path))


def load_radon(report: str | None, paths: list[str]) -> dict:
    if report:
        with open(report, encoding="utf-8") as fh:
            return json.load(fh)
    try:
        result = subprocess.run(
            [sys.executable, "-m", "radon", "cc", "-j", *paths],
            capture_output=True, text=True, check=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        detail = getattr(exc, "stderr", "") or str(exc)
        sys.exit(f"error: could not run radon (is it installed in this environment?)\n{detail.strip()}")
    return json.loads(result.stdout)


def function_blocks(blocks: list[dict]):
    """Yield functions and methods, including those nested in classes and closures."""
    for block in blocks:
        if block.get("type") == "class":
            yield from function_blocks(block.get("methods", []))
        elif block.get("type") in ("function", "method"):
            yield block
            yield from function_blocks(block.get("closures", []))


def line_coverage(file_cov: dict | None, first: int, last: int) -> float | None:
    """Share of executable lines in [first, last] that were executed."""
    if file_cov is None:
        return None
    executed = sum(1 for n in file_cov.get("executed_lines", []) if first <= n <= last)
    missing = sum(1 for n in file_cov.get("missing_lines", []) if first <= n <= last)
    total = executed + missing
    return executed / total if total else 1.0


def collect(radon: dict, coverage: dict) -> list[dict]:
    cov_by_file = {norm(path): data for path, data in coverage.get("files", {}).items()}
    rows = []
    seen = set()
    for path, blocks in radon.items():
        if not isinstance(blocks, list):  # radon reports {"error": ...} for unparsable files
            continue
        file_cov = cov_by_file.get(norm(path))
        for block in function_blocks(blocks):
            name = f"{block['classname']}.{block['name']}" if block.get("classname") else block["name"]
            key = (path, name, block["lineno"])
            if key in seen:
                continue
            seen.add(key)
            cov = line_coverage(file_cov, block["lineno"], block["endline"])
            rows.append({
                "file": path,
                "line": block["lineno"],
                "name": name,
                "complexity": block["complexity"],
                "coverage": cov,
                "crap": crap(block["complexity"], 0.0 if cov is None else cov),
            })
    return sorted(rows, key=lambda r: r["crap"], reverse=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Per-function CRAP score (radon + coverage).")
    parser.add_argument("paths", nargs="*", default=["."], help="source paths for radon (default: .)")
    parser.add_argument("--coverage", default="coverage.json", help="coverage JSON report (default: coverage.json)")
    parser.add_argument("--radon", help="saved output of `radon cc -j` instead of running radon")
    parser.add_argument("--threshold", type=float, default=10.0, help="target CRAP score (default: 10)")
    parser.add_argument("--top", type=int, default=20, help="how many functions to print (default: 20; 0 = all)")
    parser.add_argument("--strict", action="store_true", help="exit with 1 if any function exceeds the threshold")
    args = parser.parse_args(argv)

    try:
        with open(args.coverage, encoding="utf-8") as fh:
            coverage = json.load(fh)
    except FileNotFoundError:
        sys.exit(f"error: {args.coverage} not found; create it with `pytest --cov --cov-report=json`")

    rows = collect(load_radon(args.radon, args.paths), coverage)
    over = [r for r in rows if r["crap"] > args.threshold]
    shown = rows if args.top == 0 else rows[: args.top]

    print(f"{'CRAP':>8} {'CC':>4} {'cov':>6}  location")
    for r in shown:
        cov = "n/a" if r["coverage"] is None else f"{r['coverage']:.0%}"
        flag = " !" if r["crap"] > args.threshold else ""
        print(f"{r['crap']:>8.1f} {r['complexity']:>4} {cov:>6}  {r['file']}:{r['line']} {r['name']}{flag}")
    print(f"\n{len(rows)} functions, {len(over)} above the target of {args.threshold:g}.")
    if any(r["coverage"] is None for r in rows):
        print("'n/a' = file absent from the coverage report; it is counted as 0% covered.")
    print("Indicator only: add behavior tests first; do not split functions just to lower the score.")
    return 1 if args.strict and over else 0


if __name__ == "__main__":
    sys.exit(main())
