#!/usr/bin/env python3
"""Audit canonical shortcuts and generated lesson identifiability.

This is a maintainer-facing reproducer, not part of the selected generator.
It deliberately uses the generator's Python mirror so it can run quickly in a
plain Python environment; the regular battery remains responsible for Racket
parity.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

TASK_ID = "e942ce41cbf5"
REPO = Path(__file__).resolve().parents[3]
for path in (REPO / "shared/runtime", REPO / "src", REPO):
    sys.path.insert(0, str(path))

_SPEC = importlib.util.spec_from_file_location(
    f"shortcut_probe_generator_{TASK_ID}",
    REPO / "generators" / TASK_ID / "generator.py",
)
if _SPEC is None or _SPEC.loader is None:
    raise RuntimeError("could not load selected generator")
GEN = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(GEN)


def _canonical_task() -> dict[str, Any]:
    source = REPO / "shared/data/canonical/puzzles.jsonl"
    with source.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise RuntimeError(f"canonical row {TASK_ID!r} not found in {source}")


def _canonical_shortcut_report(task: dict[str, Any]) -> dict[str, Any]:
    query = task["test"] if isinstance(task["test"], dict) else task["test"][0]
    report: dict[str, Any] = {}
    for name, shortcut in sorted(GEN.CANONICAL_SHORTCUTS.items()):
        rival_output = shortcut(query["input"])
        intended_output = GEN.rule_mirror(query["input"])
        report[name] = {
            "fits_all_demonstrations": all(
                shortcut(pair["input"]) == pair["output"]
                for pair in task["train"]
            ),
            "disagrees_on_query": rival_output != intended_output,
            "query_input": query["input"],
            "intended_output": intended_output,
            "rival_output": rival_output,
        }
    return report


def _generated_lesson_report(*, seeds: int, windows: int) -> dict[str, Any]:
    bands = ("easy", "medium", "hard")
    unidentifiable: list[dict[str, Any]] = []
    surviving: dict[str, list[dict[str, Any]]] = {}
    checked = 0

    for band in bands:
        for seed in range(seeds):
            for start in range(windows):
                pairs = []
                for sample_index in range(start, start + GEN.EXAMPLES_NEEDED + 1):
                    grid = GEN.generate(seed, sample_index, difficulty=band)
                    pairs.append({"input": grid, "output": GEN.rule_mirror(grid)})
                demos, query = pairs[:-1], pairs[-1]
                checked += 1
                reasons = GEN.lesson_identifiable(demos, query)
                if reasons:
                    unidentifiable.append(
                        {
                            "difficulty": band,
                            "seed": seed,
                            "start": start,
                            "reasons": reasons,
                        }
                    )
                for name, rival in sorted(GEN.LESSON_COMPETITORS.items()):
                    if all(rival(pair["input"]) == pair["output"] for pair in demos):
                        surviving.setdefault(name, []).append(
                            {"difficulty": band, "seed": seed, "start": start}
                        )

    return {
        "bands": list(bands),
        "seeds_per_band": seeds,
        "windows_per_seed": windows,
        "lessons_checked": checked,
        "unidentifiable_lessons": unidentifiable,
        "surviving_rivals": surviving,
    }


def build_report(*, seeds: int = 12, windows: int = 6) -> dict[str, Any]:
    if seeds < 1 or windows < 1:
        raise ValueError("seeds and windows must both be positive")
    task = _canonical_task()
    return {
        "task_id": TASK_ID,
        "generator_version": GEN.VERSION,
        "rule_hash": GEN.RULE_HASH,
        "canonical_demonstrations": len(task["train"]),
        "canonical_shortcuts": _canonical_shortcut_report(task),
        "generated_lessons": _generated_lesson_report(
            seeds=seeds,
            windows=windows,
        ),
    }


def _print_text(report: dict[str, Any]) -> None:
    print(f"{report['task_id']} generator {report['generator_version']} rule {report['rule_hash']}")
    for name, result in report["canonical_shortcuts"].items():
        print(
            f"canonical shortcut {name}: "
            f"fits demos={result['fits_all_demonstrations']} "
            f"changes query={result['disagrees_on_query']}"
        )
    lessons = report["generated_lessons"]
    print(
        f"generated lessons: {lessons['lessons_checked']} checked; "
        f"unidentifiable={len(lessons['unidentifiable_lessons'])}; "
        f"surviving rivals={len(lessons['surviving_rivals'])}"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=int, default=12)
    parser.add_argument("--windows", type=int, default=6)
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    args = parser.parse_args(argv)
    report = build_report(seeds=args.seeds, windows=args.windows)
    if args.json:
        print(json.dumps(report, sort_keys=True, separators=(",", ":")))
    else:
        _print_text(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
