#!/usr/bin/env python3
"""Reproduce the shortcut claims for generator f06d31332595.

This probe is intentionally independent of the battery harness.  It verifies
that every declared canonical shortcut fits every canonical pair, then checks
all cyclic starts of the generator's three-example schedule in every difficulty
band and records a concrete disagreement for each rival.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

TASK_ID = "f06d31332595"
HERE = Path(__file__).resolve()
TASK_DIR = HERE.parents[1]
REPO = HERE.parents[3]
RUNTIME = REPO / "shared/runtime"
CANONICAL = REPO / "shared/data/canonical/puzzles.jsonl"
sys.path.insert(0, str(RUNTIME))


def load_generator():
    path = TASK_DIR / "generator.py"
    spec = importlib.util.spec_from_file_location("shortcut_probe_generator", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, path


def load_pairs() -> list[dict]:
    with CANONICAL.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return list(row["train"]) + list(row["test"])
    raise RuntimeError(f"canonical task {TASK_ID} not found")


def first_difference(left, right):
    for r, (row_l, row_r) in enumerate(zip(left, right)):
        for c, (value_l, value_r) in enumerate(zip(row_l, row_r)):
            if value_l != value_r:
                return {"row": r, "column": c, "intended": value_l, "rival": value_r}
    return None


def main() -> int:
    gen, generator_path = load_generator()
    pairs = load_pairs()
    rivals = dict(gen.CANONICAL_SHORTCUTS)

    canonical_fit = {
        name: sum(rival(pair["input"]) == pair["output"] for pair in pairs)
        for name, rival in rivals.items()
    }

    windows = []
    first_witness = {}
    for band in ("easy", "medium", "hard"):
        for start in range(12):
            demos = [
                gen.generate(7000 + start, start + offset, difficulty=band)
                for offset in range(gen.EXAMPLES_NEEDED)
            ]
            refuted = {}
            for name, rival in rivals.items():
                hits = []
                for offset, grid in enumerate(demos):
                    intended = gen.rule_mirror(grid)
                    rival_output = rival(grid)
                    if intended != rival_output:
                        hit = {
                            "offset": offset,
                            "profile": gen.schedule_profile(
                                7000 + start, start + offset, band
                            ),
                            "input": grid,
                            "intended_output": intended,
                            "rival_output": rival_output,
                            "first_difference": first_difference(
                                intended, rival_output
                            ),
                        }
                        hits.append(hit)
                        first_witness.setdefault(name, {
                            "band": band,
                            "start": start,
                            **hit,
                        })
                refuted[name] = len(hits)
            windows.append({
                "band": band,
                "start": start,
                "profiles": [
                    gen.schedule_profile(7000 + start, start + offset, band)
                    for offset in range(gen.EXAMPLES_NEEDED)
                ],
                "rival_disagreement_examples": refuted,
            })

    failed_fit = {name: count for name, count in canonical_fit.items() if count != len(pairs)}
    failed_windows = [
        window for window in windows
        if any(count == 0 for count in window["rival_disagreement_examples"].values())
    ]
    report = {
        "schema": "f06d31332595-shortcut-probe-v1",
        "task_id": TASK_ID,
        "generator_path": str(generator_path.relative_to(REPO)),
        "generator_sha256": hashlib.sha256(generator_path.read_bytes()).hexdigest(),
        "canonical_pair_count": len(pairs),
        "canonical_fit_counts": canonical_fit,
        "lesson_policy": {
            "examples_needed": gen.EXAMPLES_NEEDED,
            "profiles": list(gen.SCHEDULE_PROFILES),
            "bands": ["easy", "medium", "hard"],
            "cyclic_starts_checked_per_band": 12,
            "windows_checked": len(windows),
        },
        "failed_windows": failed_windows,
        "first_disagreement_witness": first_witness,
        "passed": not failed_fit and not failed_windows,
    }
    print(json.dumps(report, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
