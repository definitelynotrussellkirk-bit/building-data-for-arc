#!/usr/bin/env python3
"""Independent, replayable curriculum audit for dadeacb21d08.

This source-local probe complements the shared Racket-backed gates.  It checks
all canonical pairs against the Python mirror, verifies declared canonical
shortcuts actually fit those pairs, exhausts every axis-boundary combination,
and measures cyclic four-demo lessons against the generator's *declared*
competitors.  It deliberately imports the declaration dictionaries rather than
copying a rival-name list that could drift.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import itertools
import json
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

TASK_ID = "dadeacb21d08"
HERE = Path(__file__).resolve()
TASK_DIR = HERE.parents[1]
REPO_ROOT = HERE.parents[3]
RUNTIME_ROOT = REPO_ROOT / "shared" / "runtime"
if str(RUNTIME_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNTIME_ROOT))


def _load_generator():
    path = TASK_DIR / "generator.py"
    spec = importlib.util.spec_from_file_location(f"audit_{TASK_ID}_generator", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_pairs() -> list[dict[str, Any]]:
    path = REPO_ROOT / "shared" / "data" / "canonical" / "puzzles.jsonl"
    with path.open() as handle:
        for line in handle:
            if f'"task_id": "{TASK_ID}"' not in line:
                continue
            row = json.loads(line)
            return list(row.get("train", [])) + list(row.get("test", []))
    raise RuntimeError(f"canonical task {TASK_ID} not found in {path}")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _pair(gen, seed: int, sample_index: int, band: str):
    grid = gen.generate(seed, sample_index, difficulty=band)
    return {"input": grid, "output": gen.rule_mirror(grid)}


def run(per_band: int, lessons_per_band: int) -> dict[str, Any]:
    gen = _load_generator()
    canonical = _canonical_pairs()
    failures: list[dict[str, Any]] = []

    canonical_mirror = []
    for index, pair in enumerate(canonical):
        accepted = gen.self_check(pair["input"]) == []
        mirrored = gen.rule_mirror(pair["input"]) == pair["output"]
        canonical_mirror.append({"index": index, "accepted": accepted, "mirrored": mirrored})
        if not accepted or not mirrored:
            failures.append({"kind": "canonical_pair", "index": index, "accepted": accepted, "mirrored": mirrored})

    shortcut_fit = {}
    for name, shortcut in gen.CANONICAL_SHORTCUTS.items():
        fit = sum(shortcut(pair["input"]) == pair["output"] for pair in canonical)
        shortcut_fit[name] = {"fit": fit, "total": len(canonical)}
        if fit != len(canonical):
            failures.append({"kind": "declared_shortcut_not_canonical_fitting", "name": name, "fit": fit})

    axis_values = {
        "grid_h": (10, 16),
        "grid_w": (10, 16),
        "n_target_l": (2, 4),
        "n_red_decoys": (1, 3),
        "n_colored_decoys": (1, 2),
        "hole_mode": ("empty", "occupied", "mixed"),
        "target_position": ("interior", "edge"),
    }
    boundary_total = 0
    boundary_failures = []
    for index, values in enumerate(itertools.product(*axis_values.values())):
        overrides = dict(zip(axis_values, values))
        band = ("easy", "medium", "hard")[index % 3]
        boundary_total += 1
        try:
            grid = gen.generate(9100 + index, 1000 + index, difficulty=band, **overrides)
            observed = gen.observe_overrides(grid)
            errors = gen.self_check(grid, difficulty=band, meta={"overrides": overrides})
            if observed != overrides or errors:
                boundary_failures.append({"index": index, "band": band, "requested": overrides, "observed": observed, "errors": errors})
        except Exception as exc:  # fail-loud evidence, bounded to exact combinations
            boundary_failures.append({"index": index, "band": band, "requested": overrides, "exception": f"{type(exc).__name__}: {exc}"})
    failures.extend({"kind": "axis_boundary", **row} for row in boundary_failures)

    bands: dict[str, Any] = {}
    for band_index, band in enumerate(("easy", "medium", "hard")):
        inputs = []
        strict = 0
        profile_counts: Counter[str] = Counter()
        witness_counts: Counter[str] = Counter()
        self_errors = []
        for index in range(per_band):
            seed = 200_000 + band_index * 10_000 + index
            grid = gen.generate(seed, index, difficulty=band)
            inputs.append(json.dumps(grid, separators=(",", ":")))
            errors = gen.self_check(grid, difficulty=band)
            if errors:
                self_errors.append({"seed": seed, "sample_index": index, "errors": errors})
            strict += not bool(gen.strict_canonical_like(grid))
            profile_counts[str(gen.schedule_profile(seed, index, band))] += 1
            for name, predicate in gen.SEMANTIC_WITNESSES.items():
                if predicate(grid):
                    witness_counts[name] += 1

        lesson_failures = []
        survivor_counts: Counter[str] = Counter()
        dangerous_counts: Counter[str] = Counter()
        unique_lesson_inputs: set[str] = set()
        starts: Counter[str] = Counter()
        for lesson_index in range(lessons_per_band):
            seed = 500_000 + band_index * 100_000 + lesson_index
            start = lesson_index
            starts[str(start % len(gen.SCHEDULE_PROFILES))] += 1
            demos = [_pair(gen, seed, start + offset, band) for offset in range(gen.EXAMPLES_NEEDED)]
            query = _pair(gen, seed, start + gen.EXAMPLES_NEEDED, band)
            for pair in demos + [query]:
                unique_lesson_inputs.add(json.dumps(pair["input"], separators=(",", ":")))
            reasons = gen.lesson_identifiable(demos, query)
            if reasons:
                lesson_failures.append({"lesson_index": lesson_index, "seed": seed, "start": start, "reasons": reasons})
            truth = query["output"]
            for name, competitor in gen.LESSON_COMPETITORS.items():
                if all(competitor(demo["input"]) == demo["output"] for demo in demos):
                    survivor_counts[name] += 1
                    if competitor(query["input"]) != truth:
                        dangerous_counts[name] += 1

        if self_errors:
            failures.append({"kind": "default_self_check", "band": band, "examples": self_errors[:5], "count": len(self_errors)})
        if lesson_failures:
            failures.append({"kind": "lesson_identifiability", "band": band, "examples": lesson_failures[:5], "count": len(lesson_failures)})
        if dangerous_counts:
            failures.append({"kind": "dangerous_competitor", "band": band, "counts": dict(dangerous_counts)})
        missing_witnesses = sorted(set(gen.SEMANTIC_WITNESSES) - set(witness_counts))
        if missing_witnesses:
            failures.append({"kind": "missing_witness", "band": band, "names": missing_witnesses})

        bands[band] = {
            "draws": per_band,
            "unique_inputs": len(set(inputs)),
            "strict": strict,
            "strict_fraction": strict / max(1, per_band),
            "profiles": dict(sorted(profile_counts.items())),
            "witness_counts": dict(sorted(witness_counts.items())),
            "self_check_failures": len(self_errors),
            "lessons": lessons_per_band,
            "lesson_start_residues": dict(sorted(starts.items())),
            "identifiability_failures": len(lesson_failures),
            "competitor_survivors": dict(sorted(survivor_counts.items())),
            "dangerous_competitors": dict(sorted(dangerous_counts.items())),
            "unique_lesson_inputs": len(unique_lesson_inputs),
        }

    return {
        "schema": "dadeacb21d08-independent-audit-v1",
        "task_id": TASK_ID,
        "generator_version": gen.VERSION,
        "generator_sha256": _sha256(TASK_DIR / "generator.py"),
        "rule_hash": gen.RULE_HASH,
        "working_directory": os.getcwd(),
        "command": " ".join(sys.argv),
        "sampler": {
            "draws_per_band": per_band,
            "lessons_per_band": lessons_per_band,
            "lesson_policy": "same seed, every cyclic start, four consecutive demos, next sample as query",
        },
        "canonical_pairs": canonical_mirror,
        "canonical_shortcuts": shortcut_fit,
        "axis_boundary_contract": {
            "total": boundary_total,
            "failures": len(boundary_failures),
            "failure_examples": boundary_failures[:5],
        },
        "bands": bands,
        "failure_count": len(failures),
        "failures": failures,
        "passed": not failures,
        "limits": [
            "The probe uses the task-local Python mirror; shared gates remain the Racket authority check.",
            "Declared-rival elimination is finite evidence, not a proof against every possible learned shortcut.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--per-band", type=int, default=100)
    parser.add_argument("--lessons-per-band", type=int, default=100)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.per_band <= 0 or args.lessons_per_band <= 0:
        parser.error("sample counts must be positive")
    report = run(args.per_band, args.lessons_per_band)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "passed": report["passed"],
        "failure_count": report["failure_count"],
        "axis_boundary_failures": report["axis_boundary_contract"]["failures"],
        "bands": {
            band: {
                "unique_inputs": row["unique_inputs"],
                "strict": f"{row['strict']}/{row['draws']}",
                "lessons_ok": f"{row['lessons']-row['identifiability_failures']}/{row['lessons']}",
                "dangerous": row["dangerous_competitors"],
            }
            for band, row in report["bands"].items()
        },
        "out": str(args.out),
    }, indent=2, sort_keys=True))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
