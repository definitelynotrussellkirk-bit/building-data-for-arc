#!/usr/bin/env python3
"""Source-bound qualification probe for generator 3ef5f8be2639.

This complements the shared battery with task-specific exhaustive offset/count
coverage and cyclic query rotations.  It deliberately uses the generator's
public semantic hooks and canonical public pairs; it does not execute or import
private Racket internals.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
from typing import Any, Iterable

TASK_ID = "3ef5f8be2639"
HERE = Path(__file__).resolve().parent
GENERATOR_PATH = HERE.parent / "generator.py"


def _load_generator():
    spec = importlib.util.spec_from_file_location(
        f"qualification_generator_{TASK_ID}", GENERATOR_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {GENERATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _repo_root() -> Path:
    configured = os.environ.get("ARCPUZZLES_HOME")
    if configured:
        return Path(configured).resolve()
    return HERE.parents[2]


def _canonical_pairs(root: Path) -> list[dict[str, Any]]:
    path = root / "shared/data/canonical/puzzles.jsonl"
    with path.open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return [*row["train"], row["test"]]
    raise KeyError(f"canonical task {TASK_ID} not found in {path}")


def _grid_digest(grid: list[list[int]]) -> str:
    payload = json.dumps(grid, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def _first(grid: list[list[int]], color: int) -> tuple[int, int]:
    return next(
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == color
    )


def _difficulty_seed(band: str | None, index: int) -> int:
    base = {None: 31000, "easy": 32000, "medium": 33000, "hard": 34000}[band]
    return base + index


def run_audit(
    *,
    per_band: int = 100,
    bands: Iterable[str | None] = ("easy", "medium", "hard"),
    exact_shapes: Iterable[tuple[int, int]] = ((7, 7), (8, 8)),
) -> dict[str, Any]:
    """Run the finite task-local contract and return a JSON-safe report."""
    if type(per_band) is not int or per_band < 1:
        raise ValueError("per_band must be a positive integer")
    bands = tuple(bands)
    exact_shapes = tuple(exact_shapes)
    gen = _load_generator()
    generator_sha256 = hashlib.sha256(GENERATOR_PATH.read_bytes()).hexdigest()

    canonical_failures: list[str] = []
    accepted = 0
    mirror_matches = 0
    rival_fits = {name: 0 for name in gen.CANONICAL_SHORTCUTS}
    canonical = _canonical_pairs(_repo_root())
    for index, pair in enumerate(canonical):
        errors = gen.self_check(pair["input"])
        if errors:
            canonical_failures.append(f"pair {index}: self_check {errors}")
        else:
            accepted += 1
        actual = gen._first_pair_output(pair["input"])
        if actual == pair["output"]:
            mirror_matches += 1
        else:
            canonical_failures.append(f"pair {index}: Python mirror mismatch")
        for name, rival in gen.CANONICAL_SHORTCUTS.items():
            if rival(pair["input"]) == pair["output"]:
                rival_fits[name] += 1
            else:
                canonical_failures.append(
                    f"pair {index}: declared canonical shortcut {name!r} does not fit"
                )

    exact_failures: list[dict[str, Any]] = []
    exact_cases = 0
    for band_index, band in enumerate(bands):
        for shape_index, (height, width) in enumerate(exact_shapes):
            for offset_id in range(len(gen.OFFSETS)):
                for count_index, (num_2, num_3) in enumerate(
                    ((1, 1), (2, 1), (1, 2), (2, 2))
                ):
                    exact_cases += 1
                    requested = {
                        "grid_h": height,
                        "grid_w": width,
                        "offset_id": offset_id,
                        "num_2_seeds": num_2,
                        "num_3_seeds": num_3,
                    }
                    seed = 41000 + band_index * 10000 + shape_index * 1000 + offset_id * 10 + count_index
                    try:
                        grid = gen.generate(
                            seed,
                            exact_cases,
                            difficulty=band,
                            **requested,
                        )
                        errors = gen.self_check(grid)
                        observed = gen.observe_overrides(grid)
                        replay = gen.generate(
                            seed,
                            exact_cases,
                            difficulty=band,
                            **requested,
                        )
                        if errors or observed != requested or replay != grid:
                            exact_failures.append(
                                {
                                    "band": band,
                                    "requested": requested,
                                    "self_check": errors,
                                    "observed": observed,
                                    "deterministic": replay == grid,
                                }
                            )
                    except Exception as exc:  # report the exact failing tuple
                        exact_failures.append(
                            {
                                "band": band,
                                "requested": requested,
                                "exception": f"{type(exc).__name__}: {exc}",
                            }
                        )

    default_failures: list[dict[str, Any]] = []
    unique_inputs: set[str] = set()
    profiles: dict[str, int] = {}
    distances = {"1": 0, "2": 0}
    effective_distractors = 0
    default_draws = 0
    for band in bands:
        for index in range(per_band):
            default_draws += 1
            seed = _difficulty_seed(band, index)
            try:
                grid = gen.generate(seed, index, difficulty=band)
                replay = gen.generate(seed, index, difficulty=band)
                errors = gen.self_check(grid)
                if errors or replay != grid:
                    default_failures.append(
                        {
                            "band": band,
                            "index": index,
                            "self_check": errors,
                            "deterministic": replay == grid,
                        }
                    )
                    continue
                unique_inputs.add(_grid_digest(grid))
                observed = gen.observe_overrides(grid)
                profile = f"{observed['grid_h']}x{observed['grid_w']}/palette3"
                profiles[profile] = profiles.get(profile, 0) + 1
                two, three = _first(grid, 2), _first(grid, 3)
                distance = max(abs(two[0] - three[0]), abs(two[1] - three[1]))
                distances[str(distance)] = distances.get(str(distance), 0) + 1
                if gen.SEMANTIC_RIVALS["all_pairs"](grid) != gen._first_pair_output(grid):
                    effective_distractors += 1
            except Exception as exc:
                default_failures.append(
                    {
                        "band": band,
                        "index": index,
                        "exception": f"{type(exc).__name__}: {exc}",
                    }
                )

    # A four-item window supports all four possible query positions.  Each
    # rotation leaves three demonstrations, so this catches schedules whose
    # semantic evidence disappears when the informative item is the query.
    lesson_failures: list[dict[str, Any]] = []
    rotations = 0
    for band in bands:
        sequence = []
        for index in range(per_band + 3):
            grid = gen.generate(_difficulty_seed(band, 1000 + index), index, difficulty=band)
            sequence.append({"input": grid, "output": gen._first_pair_output(grid)})
        for start in range(per_band):
            window = sequence[start : start + 4]
            for query_index in range(4):
                rotations += 1
                demos = [item for i, item in enumerate(window) if i != query_index]
                query = {"input": window[query_index]["input"]}
                issues = gen.lesson_identifiable(demos, query)
                if issues:
                    lesson_failures.append(
                        {
                            "band": band,
                            "start": start,
                            "query_index": query_index,
                            "issues": issues,
                        }
                    )

    failures = bool(
        canonical_failures or exact_failures or default_failures or lesson_failures
    )
    return {
        "schema": "3ef5f8be2639-qualification-v1",
        "status": "fail" if failures else "pass",
        "task_id": TASK_ID,
        "generator_version": gen.VERSION,
        "generator_sha256": generator_sha256,
        "canonical": {
            "pairs": len(canonical),
            "accepted": accepted,
            "mirror_matches": mirror_matches,
            "rival_fits": rival_fits,
            "failures": canonical_failures,
        },
        "exact_matrix": {
            "bands": list(bands),
            "shapes": [list(shape) for shape in exact_shapes],
            "offsets": len(gen.OFFSETS),
            "seed_count_combinations": 4,
            "cases": exact_cases,
            "failures": exact_failures,
        },
        "default_schedule": {
            "per_band": per_band,
            "draws": default_draws,
            "unique_inputs": len(unique_inputs),
            "profiles": dict(sorted(profiles.items())),
            "selected_pair_distances": distances,
            "effective_scan_order_distractors": effective_distractors,
            "failures": default_failures,
        },
        "lesson_rotations": {
            "policy": "contiguous four-item windows; each item rotated through query position",
            "windows_per_band": per_band,
            "rotations": rotations,
            "failures": lesson_failures,
        },
        "limits": [
            "Finite source-level audit; it does not prove universal induction.",
            "The shared rule-smoke/authority gates, not this probe, bind outputs to Racket.",
            "Declared rivals are task-specific plausible shortcuts, not an exhaustive hypothesis class.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--per-band", type=int, default=100)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    report = run_audit(per_band=args.per_band)
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
    print(text, end="")
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
