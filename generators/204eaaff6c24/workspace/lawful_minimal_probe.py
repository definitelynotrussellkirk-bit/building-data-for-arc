#!/usr/bin/env python3
"""Execute current task semantics on minimal shapes flagged by generic lint.

This is evidence, not an exemption.  It binds the current selected generator,
canonical Racket program, expected count-rule outputs, and exact probe grids.
"""
from __future__ import annotations

import argparse
from contextlib import nullcontext
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

from arc_repl.racket_bridge import RacketBridge, racket_runtime_status
from puzzle_generators.rule_wrap import strip_rule_wrapper
from reviewer_support import canonical_path, find_root, normalize_grid

TASK_ID = "204eaaff6c24"
PROBES: dict[str, dict[str, list[list[int]]]] = {
    "singleton": {
        "input": [[4, 0, 0], [0, 0, 0], [0, 0, 0]],
        "expected": [[4]],
    },
    "short_line": {
        "input": [[0, 0, 0, 0, 0], [4, 4, 4, 4, 0], [0, 0, 0, 0, 0]],
        "expected": [[4, 4, 4, 4]],
    },
    "solid_2x2": {
        "input": [[4, 4, 0], [4, 4, 0], [0, 0, 0]],
        "expected": [[4, 4, 4, 4]],
    },
}


def _root(root=None) -> Path:
    return Path(root).resolve() if root is not None else find_root(__file__)


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_text(text: str) -> str:
    return _sha256_bytes(text.encode("utf-8"))


def _canonical_record(root: Path) -> dict[str, Any]:
    matches = []
    with canonical_path(root).open(encoding="utf-8") as stream:
        for line in stream:
            if line.strip():
                record = json.loads(line)
                if record.get("task_id") == TASK_ID:
                    matches.append(record)
    if len(matches) != 1:
        raise ValueError(f"expected one canonical record for {TASK_ID}, found {len(matches)}")
    return matches[0]


def _load_generator(root: Path):
    source = root / "generators" / TASK_ID / "generator.py"
    spec = importlib.util.spec_from_file_location(f"generator_{TASK_ID}_minimal_probe", source)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, source


def _execute(bridge: RacketBridge, program: str, grid) -> list[list[int]]:
    body = strip_rule_wrapper(program)
    if not body.lstrip().startswith(("(lambda", "(λ")):
        raise ValueError("canonical program must contain a lambda-bodied rule")
    bridge.define_grid("__lawful_minimal_input__", normalize_grid(grid))
    return normalize_grid(bridge.eval_text(f"({body} __lawful_minimal_input__)"))


def build_report(*, root=None, bridge=None) -> dict[str, Any]:
    repo = _root(root)
    generator, generator_source = _load_generator(repo)
    canonical = _canonical_record(repo)
    program = canonical["program_solution"]
    results = []

    context = nullcontext(bridge) if bridge is not None else RacketBridge(timeout=10, startup_timeout=60)
    with context as active:
        for name, probe in PROBES.items():
            grid = normalize_grid(probe["input"])
            expected = normalize_grid(probe["expected"])
            errors = list(generator.self_check(grid))
            actual = _execute(active, program, grid)
            results.append(
                {
                    "name": name,
                    "input": grid,
                    "expected": expected,
                    "canonical_output": actual,
                    "self_check_errors": errors,
                    "canonical_matches_expected": actual == expected,
                    "passed": not errors and actual == expected,
                }
            )

    passed = sum(bool(item["passed"]) for item in results)
    source = Path(__file__).resolve()
    return {
        "schema": "arcpuzzles-lawful-minimal-probe-v1",
        "status": "pass" if passed == len(results) else "fail",
        "task_id": TASK_ID,
        "rule_hash": generator.RULE_HASH,
        "summary": {"checked": len(results), "passed": passed},
        "probes": results,
        "source_binding": {
            "generator_path": str(generator_source.relative_to(repo)),
            "generator_sha256": _sha256_bytes(generator_source.read_bytes()),
            "canonical_program_sha256": _sha256_text(program),
            "probe_path": str(source.relative_to(repo)),
            "probe_sha256": _sha256_bytes(source.read_bytes()),
        },
        "runtime": racket_runtime_status(),
        "interpretation": (
            "These exact inputs are lawful under the selected count-all-foreground-cells rule. "
            "The report justifies retaining their support; it does not waive other defect-lint findings."
        ),
        "limitations": [
            "Only the three named exact grids are checked.",
            "Successful Racket execution is not a universal proof of domain membership.",
            "Any generator or canonical-program change requires a fresh report.",
        ],
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    out = Path(args.out)
    if out.exists():
        raise FileExistsError(f"refusing to overwrite existing report: {out}")
    report = build_report()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], **report["summary"], "out": str(out)}, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
