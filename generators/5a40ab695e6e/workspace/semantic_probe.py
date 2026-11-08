#!/usr/bin/env python3
"""Source-bound coverage probe for generator 5a40ab695e6e.

The shared lesson census exercises the production materializer and Racket rule.
This complementary task-local probe checks two areas that are easy to miss:

* all four choices of masked query within a four-pair lesson; and
* every legal joint combination of the three exact override axes.

It also records an exact grid on which the canonical-fitting bounding-box/area
shortcut disagrees with the symmetry rule, making the review claim replayable.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

TASK_ID = "5a40ab695e6e"
TASK_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]
GENERATOR_PATH = TASK_DIR / "generator.py"
CANONICAL_PATH = REPO_ROOT / "shared/data/canonical/puzzles.jsonl"


def _load_generator():
    spec = importlib.util.spec_from_file_location(
        f"semantic_probe_generator_{TASK_ID}", GENERATOR_PATH
    )
    module = importlib.util.module_from_spec(spec)
    if spec.loader is None:  # pragma: no cover - importlib defensive branch
        raise RuntimeError(f"could not load {GENERATOR_PATH}")
    spec.loader.exec_module(module)
    return module


def _canonical_pairs() -> list[dict[str, Any]]:
    with CANONICAL_PATH.open() as source:
        for line in source:
            row = json.loads(line)
            if row.get("task_id") != TASK_ID:
                continue
            tests = row["test"] if isinstance(row["test"], list) else [row["test"]]
            return [*row["train"], *tests]
    raise RuntimeError(f"canonical task {TASK_ID} not found in {CANONICAL_PATH}")


def _grid_hash(grid) -> str:
    payload = json.dumps(grid, separators=(",", ":"), sort_keys=False).encode()
    return hashlib.sha256(payload).hexdigest()


def _surviving_rivals(gen, demos) -> list[str]:
    return sorted(
        name
        for name, rival in gen.LESSON_COMPETITORS.items()
        if all(rival(pair["input"]) == pair["output"] for pair in demos)
    )


def run_probe(*, lessons_per_band: int = 100) -> dict[str, Any]:
    if type(lessons_per_band) is not int or lessons_per_band < 1:
        raise ValueError("lessons_per_band must be a positive integer")

    gen = _load_generator()
    canonical = _canonical_pairs()
    shortcut_name, shortcut = next(iter(gen.CANONICAL_SHORTCUTS.items()))
    canonical_fit = sum(shortcut(pair["input"]) == pair["output"] for pair in canonical)

    override_failures: list[dict[str, Any]] = []
    override_accepted = 0
    for band_index, band in enumerate(("easy", "medium", "hard")):
        case_index = 0
        for grid_h in range(9, 15):
            for grid_w in range(10, 17):
                for n_objects in (3, 4):
                    requested = {
                        "grid_h": grid_h,
                        "grid_w": grid_w,
                        "n_objects": n_objects,
                    }
                    try:
                        grid = gen.generate(
                            910_000 + band_index,
                            case_index,
                            difficulty=band,
                            **requested,
                        )
                        observed = gen.observe_overrides(grid)
                        errors = gen.self_check(
                            grid,
                            difficulty=band,
                            meta={"overrides": requested},
                        )
                    except Exception as exc:  # retained as evidence, not hidden
                        override_failures.append(
                            {
                                "band": band,
                                "case": requested,
                                "error": f"{type(exc).__name__}: {exc}",
                            }
                        )
                    else:
                        if observed != requested or errors:
                            override_failures.append(
                                {
                                    "band": band,
                                    "case": requested,
                                    "observed": observed,
                                    "self_check": errors,
                                }
                            )
                        else:
                            override_accepted += 1
                    case_index += 1

    per_band: dict[str, Any] = {}
    first_counterexample = None
    for band_index, band in enumerate(("easy", "medium", "hard")):
        production_failures = []
        cyclic_failures = []
        unique_inputs: set[str] = set()
        profile_counts: dict[str, int] = {}
        witness_hits = 0
        replay_rows = []

        for lesson_index in range(lessons_per_band):
            seed = 820_000 + band_index * 100_000 + lesson_index
            start = lesson_index * 4
            pairs = []
            profiles = []
            for offset in range(4):
                sample_index = start + offset
                grid = gen.generate(seed, sample_index, difficulty=band)
                errors = gen.self_check(grid, difficulty=band)
                if errors:
                    production_failures.append(
                        {
                            "seed": seed,
                            "sample_index": sample_index,
                            "errors": errors,
                        }
                    )
                output = gen.rule_mirror(grid)
                pairs.append({"input": grid, "output": output})
                profile = gen.schedule_profile(seed, sample_index, band)
                profiles.append(profile)
                profile_counts[profile] = profile_counts.get(profile, 0) + 1
                unique_inputs.add(_grid_hash(grid))
                if gen.SEMANTIC_WITNESSES[
                    "bbox_area_shortcut_counterexample"
                ](grid):
                    witness_hits += 1
                    if first_counterexample is None:
                        rival_output = shortcut(grid)
                        first_counterexample = {
                            "replay": {
                                "seed": seed,
                                "sample_index": sample_index,
                                "difficulty": band,
                            },
                            "profile": profile,
                            "input": grid,
                            "authority_output": output,
                            "rival_output": rival_output,
                            "input_sha256": _grid_hash(grid),
                        }

            production_errors = gen.lesson_identifiable(pairs[:3], pairs[3])
            if production_errors:
                production_failures.append(
                    {
                        "seed": seed,
                        "start": start,
                        "profiles": profiles,
                        "errors": production_errors,
                        "survivors": _surviving_rivals(gen, pairs[:3]),
                    }
                )

            for query_index in range(4):
                demos = [pair for index, pair in enumerate(pairs) if index != query_index]
                rotation_errors = gen.lesson_identifiable(demos, pairs[query_index])
                if rotation_errors:
                    cyclic_failures.append(
                        {
                            "seed": seed,
                            "start": start,
                            "query_index": query_index,
                            "profiles": profiles,
                            "errors": rotation_errors,
                            "survivors": _surviving_rivals(gen, demos),
                        }
                    )

            replay_rows.append(
                {
                    "seed": seed,
                    "start": start,
                    "profiles": profiles,
                    "input_sha256": [_grid_hash(pair["input"]) for pair in pairs],
                }
            )

        per_band[band] = {
            "production_lessons": lessons_per_band,
            "production_unidentifiable": production_failures,
            "cyclic_rotations": lessons_per_band * 4,
            "cyclic_unidentifiable": cyclic_failures,
            "materialized_pairs": lessons_per_band * 4,
            "unique_inputs": len(unique_inputs),
            "profile_counts": dict(sorted(profile_counts.items())),
            "witness_hits": witness_hits,
            "replays": replay_rows,
        }

    failures = (
        override_failures
        or canonical_fit != len(canonical)
        or first_counterexample is None
        or any(
            cell["production_unidentifiable"] or cell["cyclic_unidentifiable"]
            for cell in per_band.values()
        )
    )
    return {
        "schema": "5a40ab695e6e-semantic-probe-v1",
        "task_id": TASK_ID,
        "generator_version": gen.VERSION,
        "generator_sha256": hashlib.sha256(GENERATOR_PATH.read_bytes()).hexdigest(),
        "lessons_per_band": lessons_per_band,
        "canonical_shortcut": {
            "name": shortcut_name,
            "canonical_pairs": len(canonical),
            "canonical_pairs_fit": canonical_fit,
        },
        "exact_overrides": {
            "attempted": 6 * 7 * 2 * 3,
            "accepted": override_accepted,
            "failures": override_failures,
        },
        "per_band": per_band,
        "first_counterexample": first_counterexample,
        "limitations": [
            "Python source-bound probe; Racket equivalence is established separately by the official semantic gate and lesson census.",
            "Finite deterministic census over the declared generated manifold, not proof of universal rule induction.",
        ],
        "status": "FAIL" if failures else "PASS",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lessons-per-band", type=int, default=100)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    report = run_probe(lessons_per_band=args.lessons_per_band)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    print(
        json.dumps(
            {
                "task_id": TASK_ID,
                "status": report["status"],
                "out": str(args.out),
                "lessons_per_band": args.lessons_per_band,
            }
        )
    )
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
