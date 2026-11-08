#!/usr/bin/env python3
"""Independent, source-bound probe for the majority-merge teaching contract.

Run from the repository root with ``PYTHONPATH=shared/runtime``.  The probe
samples the production generator, verifies that each grid crosses both sides of
the >=2-panel threshold, checks every declared rival, exercises two-demo
lessons, and confirms the Python mirror on all labeled canonical pairs.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from collections import Counter
from pathlib import Path
from typing import Any

from reviewer_support import canonical_pairs, find_root


TASK_ID = "8f10b83435aa"


def _load_generator(root: Path):
    path = root / "generators" / TASK_ID / "generator.py"
    spec = importlib.util.spec_from_file_location(f"probe_{TASK_ID}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load generator from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, path


def _counts(grid: list[list[int]]) -> Counter[int]:
    panel_bases = (0, 5, 10)
    result: Counter[int] = Counter()
    for row in range(len(grid)):
        for col in range(4):
            result[sum(grid[row][base + col] != 0 for base in panel_bases)] += 1
    return result


def _record_failure(failures: list[dict[str, Any]], kind: str, **details: Any) -> None:
    if len(failures) < 20:
        failures.append({"kind": kind, **details})


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--per-band", type=int, default=100)
    parser.add_argument("--lesson-starts", type=int, default=30)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    if args.per_band < 1 or args.lesson_starts < 1:
        parser.error("sample counts must be positive")

    root = find_root(__file__)
    gen, source_path = _load_generator(root)
    source_sha = hashlib.sha256(source_path.read_bytes()).hexdigest()
    failures: list[dict[str, Any]] = []
    per_band: dict[str, Any] = {}

    for band in ("easy", "medium", "hard"):
        axes = {name: set() for name in gen.AXES}
        minima = {"one_panel": None, "pair_only": None, "triple": None}
        rival_disagreements = Counter()
        for seed in range(args.per_band):
            sample_index = seed * 13 + 7
            grid = gen.generate(seed, sample_index, difficulty=band)
            replay = gen.generate(seed, sample_index, difficulty=band)
            if grid != replay:
                _record_failure(failures, "nondeterministic", band=band, seed=seed)
            errors = gen.self_check(grid, difficulty=band)
            strict_errors = gen.strict_canonical_like(grid)
            if errors or strict_errors:
                _record_failure(
                    failures,
                    "validator",
                    band=band,
                    seed=seed,
                    self_check=errors,
                    strict=strict_errors,
                )
            counts = _counts(grid)
            for name, value in (
                ("one_panel", counts[1]),
                ("pair_only", counts[2]),
                ("triple", counts[3]),
            ):
                minima[name] = value if minima[name] is None else min(minima[name], value)
            if counts[1] < 3 or counts[2] < 3 or counts[3] < 1:
                _record_failure(
                    failures,
                    "threshold_support",
                    band=band,
                    seed=seed,
                    occupancy=dict(counts),
                )
            truth = gen.rule_mirror(grid)
            for name, rival in gen.LESSON_COMPETITORS.items():
                if rival(grid) != truth:
                    rival_disagreements[name] += 1
                else:
                    _record_failure(
                        failures,
                        "rival_fits_example",
                        band=band,
                        seed=seed,
                        rival=name,
                    )
            observed = gen.observe_overrides(grid)
            for name in axes:
                axes[name].add(observed[name])

        lesson_failures = 0
        for start in range(args.lesson_starts):
            seed = 10000 + start
            demos = []
            for offset in range(gen.EXAMPLES_NEEDED):
                grid = gen.generate(seed, start + offset, difficulty=band)
                demos.append({"input": grid, "output": gen.rule_mirror(grid)})
            query_grid = gen.generate(seed, start + gen.EXAMPLES_NEEDED, difficulty=band)
            query = {"input": query_grid, "output": gen.rule_mirror(query_grid)}
            reasons = gen.lesson_identifiable(demos, query)
            if reasons:
                lesson_failures += 1
                _record_failure(
                    failures,
                    "lesson_ambiguity",
                    band=band,
                    start=start,
                    reasons=reasons,
                )

        per_band[band] = {
            "draws": args.per_band,
            "minimum_occupancy_support": minima,
            "observed_axis_values": {name: sorted(values) for name, values in axes.items()},
            "rival_disagreements": dict(sorted(rival_disagreements.items())),
            "lessons_checked": args.lesson_starts,
            "lesson_failures": lesson_failures,
        }

    canonical = {"pairs": 0, "mirror_mismatches": 0, "validator_failures": 0}
    for pair in canonical_pairs(TASK_ID, root=root, labeled_only=True):
        canonical["pairs"] += 1
        if gen.rule_mirror(pair["input"]) != pair["output"]:
            canonical["mirror_mismatches"] += 1
            _record_failure(failures, "canonical_mirror_mismatch", pair=canonical["pairs"] - 1)
        if gen.self_check(pair["input"]) or gen.strict_canonical_like(pair["input"]):
            canonical["validator_failures"] += 1
            _record_failure(failures, "canonical_validator_failure", pair=canonical["pairs"] - 1)

    report = {
        "schema": "8f10b83435aa-majority-contract-probe-v1",
        "task_id": TASK_ID,
        "generator_sha256": source_sha,
        "per_band": per_band,
        "canonical": canonical,
        "failures": failures,
        "status": "PASS" if not failures else "FAIL",
        "limits": [
            "finite seed schedule",
            "checks declared rivals rather than all possible hypotheses",
            "Python rule mirror; authoritative Racket parity is covered by the battery",
        ],
    }
    raw = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(raw, encoding="utf-8")
    else:
        print(raw, end="")
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
