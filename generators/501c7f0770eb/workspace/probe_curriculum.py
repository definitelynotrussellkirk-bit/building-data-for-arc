#!/usr/bin/env python3
"""Reproducible structural/lesson probe for generator 501c7f0770eb.

This tool deliberately uses the task-local Python mirror only for diagnostics.
Canonical Racket remains label authority; use the source-bound lesson census for
training-admission evidence.
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

TASK_ID = "501c7f0770eb"


def _load_generator(path: Path):
    spec = importlib.util.spec_from_file_location(f"generator_{TASK_ID}_probe", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _grid_hash(grid: list[list[int]]) -> str:
    payload = json.dumps(grid, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def run(*, seeds: int, indices: int) -> dict[str, Any]:
    here = Path(__file__).resolve()
    generator_path = here.parent.parent / "generator.py"
    gen = _load_generator(generator_path)
    root = find_root(__file__)

    counts: Counter[str] = Counter()
    unique_inputs: set[str] = set()
    failures: list[dict[str, Any]] = []
    for band in ("easy", "medium", "hard"):
        for seed in range(seeds):
            for index in range(indices):
                try:
                    grid = gen.generate(seed, index, difficulty=band)
                    duplicate = gen.generate(seed, index, difficulty=band)
                    errors = gen.self_check(grid, difficulty=band)
                    observed = gen.observe_overrides(grid)
                    if duplicate != grid:
                        failures.append({"kind": "nondeterministic", "band": band, "seed": seed, "index": index})
                    if errors:
                        failures.append({"kind": "self_check", "band": band, "seed": seed, "index": index, "errors": errors})
                    unique_inputs.add(_grid_hash(grid))
                    counts[f"band:{band}"] += 1
                    counts[f"layout:{observed['layout_kind']}"] += 1
                    counts[f"blocker:{observed['blocker_style']}"] += 1
                    counts[f"frames:{len(gen._rectangle_frames(grid))}"] += 1
                    counts[f"active:{len(gen._active_frames(grid))}"] += 1
                    counts[f"witness:touching:{bool(gen._has_inactive_touching_pair(grid))}"] += 1
                    counts[f"witness:blocker:{bool(gen._has_observable_axis_blocker(grid))}"] += 1
                    counts[f"rival:all_rectangles_disagrees:{gen._all_rectangles_fire(grid) != gen._component_rule_model(grid)}"] += 1
                    counts[f"rival:ignore_blockers_disagrees:{gen._ignore_blockers(grid) != gen._component_rule_model(grid)}"] += 1
                except Exception as exc:  # keep every exact failure in the report
                    failures.append({"kind": "exception", "band": band, "seed": seed, "index": index, "error": repr(exc)})

    # The production bundle is three demonstrations plus one query.  Enumerate
    # both declared start residues and every possible query rotation.
    schedule_checks: list[dict[str, Any]] = []
    for band in ("easy", "medium", "hard"):
        for start in range(gen.LESSON_SCHEDULE_PERIOD):
            grids = [gen.generate(0, start + offset, difficulty=band) for offset in range(4)]
            for query in range(4):
                demos = [grid for pos, grid in enumerate(grids) if pos != query]
                schedule_checks.append(
                    {
                        "band": band,
                        "start_residue": start,
                        "query_position": query,
                        "demo_has_touching_refutation": any(gen._has_inactive_touching_pair(grid) for grid in demos),
                        "demo_has_blocker_refutation": any(gen._has_observable_axis_blocker(grid) for grid in demos),
                        "query_layout": gen.observe_overrides(grids[query])["layout_kind"],
                    }
                )

    canonical = []
    for pair in canonical_pairs(TASK_ID, root=root, labeled_only=True):
        inp, expected = pair["input"], pair["output"]
        canonical.append(
            {
                "split": pair["split"],
                "pair_index": pair["pair_index"],
                "self_check": gen.self_check(inp),
                "mirror_exact": gen._component_rule_model(inp) == expected,
                "all_rectangles_rival_fits": gen._all_rectangles_fire(inp) == expected,
                "ignore_blockers_rival_fits": gen._ignore_blockers(inp) == expected,
                "layout": gen.observe_overrides(inp)["layout_kind"],
                "frames": len(gen._rectangle_frames(inp)),
                "active_frames": len(gen._active_frames(inp)),
            }
        )

    schedule_ok = all(
        row["demo_has_touching_refutation"] and row["demo_has_blocker_refutation"]
        for row in schedule_checks
    )
    canonical_ok = all(not row["self_check"] and row["mirror_exact"] for row in canonical)
    return {
        "schema": "arc-generator-501c7f0770eb-curriculum-probe-v1",
        "task_id": TASK_ID,
        "generator_path": str(generator_path),
        "generator_sha256": _sha256(generator_path),
        "settings": {"seeds": seeds, "indices_per_seed_band": indices, "bands": ["easy", "medium", "hard"]},
        "generated": {
            "draws": 3 * seeds * indices,
            "unique_inputs": len(unique_inputs),
            "counts": dict(sorted(counts.items())),
            "failures": failures,
        },
        "schedule": {
            "demonstrations": 3,
            "queries": 1,
            "declared_period": gen.LESSON_SCHEDULE_PERIOD,
            "rotations_checked": len(schedule_checks),
            "all_rotations_retain_both_declared_rival_refutations": schedule_ok,
            "checks": schedule_checks,
        },
        "canonical": {
            "pairs": len(canonical),
            "all_self_check_clean_and_mirror_exact": canonical_ok,
            "records": canonical,
        },
        "status": "pass" if not failures and schedule_ok and canonical_ok else "fail",
        "limits": [
            "Python mirror diagnostics are not label authority.",
            "Finite seeds do not exhaust geometry support or undeclared rivals.",
            "Schedule enumeration proves only the declared two-residue profile at seed 0 and these bands.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=int, default=24)
    parser.add_argument("--indices", type=int, default=8)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    if args.seeds <= 0 or args.indices <= 0:
        parser.error("--seeds and --indices must be positive")
    report = run(seeds=args.seeds, indices=args.indices)
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
    else:
        print(text, end="")
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
