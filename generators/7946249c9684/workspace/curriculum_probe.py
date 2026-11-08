#!/usr/bin/env python3
"""Source-bound cyclic lesson and joint-override probe for 7946249c9684.

This complements the shared Racket-backed lesson census.  The shared census
checks production lesson assembly; this probe rotates every member of a
four-instance schedule window into the query position and exhausts a compact
joint override boundary matrix.  Rival names are read from the generator, not
copied into the probe.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
sys.path.insert(0, str(REPO / "shared" / "runtime"))

from reviewer_support import canonical_pairs, find_root  # noqa: E402


def _load(path: Path):
    spec = importlib.util.spec_from_file_location("generator_under_probe", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import generator from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _grid_hash(grid: Any) -> str:
    payload = json.dumps(grid, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--generator", type=Path, default=HERE.parent / "generator.py")
    parser.add_argument("--blocks-per-band", type=int, default=100)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    generator_path = args.generator.resolve()
    gen = _load(generator_path)
    source_sha = hashlib.sha256(generator_path.read_bytes()).hexdigest()
    profiles = tuple(gen.SCHEDULE_PROFILES)
    n_demos = int(gen.EXAMPLES_NEEDED)
    if n_demos + 1 != 4:
        raise RuntimeError("this probe expects the declared 3-demo schedule")

    rivals = dict(gen.LESSON_COMPETITORS)
    shortcuts = dict(gen.CANONICAL_SHORTCUTS)
    canonical = canonical_pairs(gen.TASK_ID, root=find_root(__file__))
    canonical_fit = {
        name: [rival(pair["input"]) == pair["output"] for pair in canonical]
        for name, rival in shortcuts.items()
    }

    report: dict[str, Any] = {
        "schema": "7946249c9684-curriculum-probe-v1",
        "task_id": gen.TASK_ID,
        "generator_sha256": source_sha,
        "generator_version": gen.VERSION,
        "declared_rule_hash": gen.RULE_HASH,
        "schedule_profiles": list(profiles),
        "examples_needed": n_demos,
        "canonical_shortcut_fit": canonical_fit,
        "cyclic_policy": (
            "Generate four consecutive sample indices. Rotate each of the four "
            "instances into the query position; use the remaining three as demos."
        ),
        "bands": {},
        "joint_override_probe": {},
        "limits": [
            "Uses the generator's independent mirror, not the Racket authority; "
            "pair it with the shared lesson-census report.",
            "Finite declared-rival test, not proof of universal induction.",
        ],
    }

    failures: list[dict[str, Any]] = []
    bases = {"easy": 610_000, "medium": 710_000, "hard": 810_000}
    for band, base in bases.items():
        hashes: set[str] = set()
        start_counts = Counter()
        rotation_counts = Counter()
        rival_refuted = Counter()
        band_failures: list[dict[str, Any]] = []
        generated = 0

        for block in range(args.blocks_per_band):
            seed = base + block
            start = block % len(profiles)
            start_counts[profiles[start]] += 1
            grids = [
                gen.generate(seed, start + offset, difficulty=band)
                for offset in range(n_demos + 1)
            ]
            generated += len(grids)
            hashes.update(_grid_hash(grid) for grid in grids)

            for query_position in range(len(grids)):
                rotation_counts[str(query_position)] += 1
                demos = [
                    {"input": grid, "output": gen._intended_output(grid)}
                    for index, grid in enumerate(grids)
                    if index != query_position
                ]
                query = {"input": grids[query_position]}
                reasons = gen.lesson_identifiable(demos, query)
                surviving = []
                for name, rival in rivals.items():
                    if any(rival(demo["input"]) != demo["output"] for demo in demos):
                        rival_refuted[name] += 1
                    else:
                        surviving.append(name)
                if reasons:
                    row = {
                        "band": band,
                        "block": block,
                        "seed": seed,
                        "start_profile": profiles[start],
                        "query_position": query_position,
                        "surviving_rivals": surviving,
                        "reasons": reasons,
                    }
                    band_failures.append(row)
                    failures.append(row)

        report["bands"][band] = {
            "blocks": args.blocks_per_band,
            "rotated_lessons": args.blocks_per_band * (n_demos + 1),
            "generated_inputs": generated,
            "unique_inputs": len(hashes),
            "cyclic_start_counts": dict(start_counts),
            "query_rotation_counts": dict(rotation_counts),
            "rival_rotations_refuted": {
                name: rival_refuted[name] for name in rivals
            },
            "failures": len(band_failures),
            "first_failures": band_failures[:5],
        }

    # Compact Cartesian boundary/interior matrix across every schedule profile.
    values = {
        "grid_h": (6, 9, 12),
        "grid_w": (7, 9, 12),
        "n_runs": (3, 5, 8),
        "palette_size": (2, 3),
    }
    joint_cases = 0
    joint_failures: list[dict[str, Any]] = []
    for band_index, band in enumerate(("easy", "medium", "hard")):
        for profile_index in range(len(profiles)):
            for h in values["grid_h"]:
                for w in values["grid_w"]:
                    for n_runs in values["n_runs"]:
                        for palette_size in values["palette_size"]:
                            requested = {
                                "grid_h": h,
                                "grid_w": w,
                                "n_runs": n_runs,
                                "palette_size": palette_size,
                            }
                            joint_cases += 1
                            try:
                                grid = gen.generate(
                                    900_000 + band_index * 10_000 + joint_cases,
                                    profile_index,
                                    difficulty=band,
                                    **requested,
                                )
                                observed = gen.observe_overrides(grid)
                                errors = gen.self_check(grid, difficulty=band)
                            except Exception as exc:  # retain concrete repro
                                joint_failures.append(
                                    {
                                        "band": band,
                                        "profile": profiles[profile_index],
                                        "requested": requested,
                                        "exception": repr(exc),
                                    }
                                )
                                continue
                            if observed != requested or errors:
                                joint_failures.append(
                                    {
                                        "band": band,
                                        "profile": profiles[profile_index],
                                        "requested": requested,
                                        "observed": observed,
                                        "self_check": errors,
                                    }
                                )
    report["joint_override_probe"] = {
        "values": {name: list(options) for name, options in values.items()},
        "cases": joint_cases,
        "failures": len(joint_failures),
        "first_failures": joint_failures[:10],
    }

    canonical_ok = all(all(results) for results in canonical_fit.values())
    report["passed"] = canonical_ok and not failures and not joint_failures
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "out": str(args.out),
                "passed": report["passed"],
                "generator_sha256": source_sha,
                "rotated_lessons": sum(
                    row["rotated_lessons"] for row in report["bands"].values()
                ),
                "joint_override_cases": joint_cases,
                "failures": len(failures) + len(joint_failures),
            },
            indent=2,
        )
    )
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
