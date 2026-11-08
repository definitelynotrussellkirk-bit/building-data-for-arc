#!/usr/bin/env python3
"""Replayable shortcut and lesson probe for ARC task ``61090a45e458``.

The probe discovers rivals from the selected generator rather than duplicating
rival names.  It verifies that each declared canonical shortcut fits every
canonical training demonstration, searches generated inputs for an exact
counterexample, and checks both the ordered production lesson and every query
rotation of its three scheduled examples.

Run from the packet root (or from a copied runtime):

    python3 run_with_racket.py python3 \
      generators/61090a45e458/workspace/shortcut_probe.py \
      --starts 30 --seeds 17 808 5150 \
      --assert-clean --out ../checks/shortcut-probe.json

The intended outputs in this report come from an independent Python
implementation.  Use ``arcpuzzles apply`` on the retained witness input when a
Racket-bound output artifact is required; the task battery separately checks
Python/Racket parity on generated inputs.
"""
from __future__ import annotations

import argparse
from collections import defaultdict, deque
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any, Callable, Iterable

TASK_ID = "61090a45e458"
HERE = Path(__file__).resolve()
TASK_DIR = HERE.parent.parent


def _bootstrap_paths() -> None:
    """Make the source library and isolated-runtime layouts both importable."""
    for candidate in (TASK_DIR, *TASK_DIR.parents):
        runtime = candidate / "shared" / "runtime"
        if (runtime / "reviewer_support.py").is_file():
            sys.path.insert(0, str(runtime))
            return
        if (candidate / "reviewer_support.py").is_file():
            sys.path.insert(0, str(candidate))
            return
    raise RuntimeError(f"cannot locate reviewer_support above {HERE}")


_bootstrap_paths()
from reviewer_support import canonical_pairs, find_root  # noqa: E402

ROOT = find_root(HERE)


def load_generator():
    path = TASK_DIR / "generator.py"
    spec = importlib.util.spec_from_file_location(f"shortcut_probe_{TASK_ID}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def source_sha256() -> str:
    return hashlib.sha256((TASK_DIR / "generator.py").read_bytes()).hexdigest()


def grid_sha256(grid: list[list[int]]) -> str:
    payload = json.dumps(grid, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def different_cells(
    left: list[list[int]], right: list[list[int]]
) -> list[list[int]]:
    if len(left) != len(right) or any(
        len(a) != len(b) for a, b in zip(left, right)
    ):
        raise ValueError("grid shapes differ")
    return [
        [row, column]
        for row, (left_row, right_row) in enumerate(zip(left, right))
        for column, (a, b) in enumerate(zip(left_row, right_row))
        if a != b
    ]


def _color_components(grid: list[list[int]]) -> list[tuple[int, set[tuple[int, int]]]]:
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    components: list[tuple[int, set[tuple[int, int]]]] = []
    for row in range(height):
        for column in range(width):
            color = grid[row][column]
            if color == 0 or (row, column) in seen:
                continue
            cells = {(row, column)}
            seen.add((row, column))
            queue = deque([(row, column)])
            while queue:
                r, c = queue.popleft()
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    rr, cc = r + dr, c + dc
                    if (
                        0 <= rr < height
                        and 0 <= cc < width
                        and (rr, cc) not in seen
                        and grid[rr][cc] == color
                    ):
                        seen.add((rr, cc))
                        cells.add((rr, cc))
                        queue.append((rr, cc))
            components.append((color, cells))
    return components


def _frame_boxes(grid: list[list[int]]) -> list[tuple[int, int, int, int]]:
    frames = []
    for _color, cells in _color_components(grid):
        rows = [row for row, _ in cells]
        columns = [column for _, column in cells]
        r1, r2 = min(rows), max(rows)
        c1, c2 = min(columns), max(columns)
        height, width = r2 - r1 + 1, c2 - c1 + 1
        expected = {
            (row, column)
            for row in range(r1, r2 + 1)
            for column in range(c1, c2 + 1)
            if row in (r1, r2) or column in (c1, c2)
        }
        if height >= 3 and width >= 3 and cells == expected:
            frames.append((r1, c1, r2, c2))
    return sorted(frames)


def intended_output(grid: list[list[int]]) -> list[list[int]]:
    """Independent implementation of the selected rule on lawful task inputs."""
    out = deepcopy(grid)
    frames = _frame_boxes(grid)
    if not frames:
        raise ValueError("no rectangular frame found")
    for r1, c1, r2, c2 in frames:
        interior: dict[int, list[tuple[int, int]]] = defaultdict(list)
        for row in range(r1 + 1, r2):
            for column in range(c1 + 1, c2):
                color = grid[row][column]
                if color:
                    interior[color].append((row, column))
        seeds = [color for color, cells in interior.items() if len(cells) == 1]
        if len(seeds) != 1 or len(interior) != 2:
            raise ValueError(
                f"frame {(r1, c1, r2, c2)} lacks one seed and one target"
            )
        seed = seeds[0]
        for color, cells in interior.items():
            if color == seed:
                continue
            for row, column in cells:
                out[row][column] = seed
    return out


def _fired_witnesses(generator, grid: list[list[int]]) -> list[str]:
    fired = []
    for name, predicate in dict(getattr(generator, "SEMANTIC_WITNESSES", {})).items():
        try:
            if predicate(deepcopy(grid)):
                fired.append(name)
        except Exception:
            continue
    return sorted(fired)


def _rival_status(
    rival: Callable[[list[list[int]]], list[list[int]]],
    demos: list[dict[str, list[list[int]]]],
    query: dict[str, list[list[int]]],
) -> str:
    survives = all(rival(deepcopy(pair["input"])) == pair["output"] for pair in demos)
    query_differs = rival(deepcopy(query["input"])) != query["output"]
    if survives and query_differs:
        return "ambiguous"
    if survives:
        return "survives_same_query"
    return "refuted_by_demo"


def _generated_pair(generator, seed: int, sample_index: int, band: str) -> dict[str, Any]:
    grid = generator.generate(seed, sample_index, difficulty=band)
    errors = generator.self_check(grid, difficulty=band)
    if errors:
        raise ValueError(
            f"generated invalid grid at {band}/{seed}/{sample_index}: {errors}"
        )
    return {
        "input": grid,
        "output": intended_output(grid),
        "seed": seed,
        "sample_index": sample_index,
        "difficulty": band,
        "profile": generator.schedule_profile(seed, sample_index, band),
    }


def _find_witnesses(
    generator,
    rivals: dict[str, Callable],
    *,
    starts: int,
    seeds: list[int],
    bands: Iterable[str],
) -> dict[str, dict[str, Any]]:
    found: dict[str, dict[str, Any]] = {}
    horizon = max(12, starts + generator.EXAMPLES_NEEDED + 1)
    for band in bands:
        for seed in seeds:
            for sample_index in range(horizon):
                pair = _generated_pair(generator, seed, sample_index, band)
                for name, rival in rivals.items():
                    if name in found:
                        continue
                    rival_output = rival(deepcopy(pair["input"]))
                    diff = different_cells(pair["output"], rival_output)
                    if not diff:
                        continue
                    found[name] = {
                        "difficulty": band,
                        "seed": seed,
                        "sample_index": sample_index,
                        "profile": pair["profile"],
                        "input_sha256": grid_sha256(pair["input"]),
                        "input": pair["input"],
                        "intended_output": pair["output"],
                        "rival_output": rival_output,
                        "different_cells": diff,
                        "semantic_witnesses": _fired_witnesses(
                            generator, pair["input"]
                        ),
                        "self_check": generator.self_check(pair["input"]),
                        "observed_axes": generator.observe_overrides(pair["input"]),
                    }
                if len(found) == len(rivals):
                    return found
    return found


def run_probe(
    starts: int = 16,
    seeds: list[int] | None = None,
    bands: Iterable[str] = ("easy", "medium", "hard"),
) -> dict[str, Any]:
    if type(starts) is not int or starts < 1:
        raise ValueError("starts must be a positive integer")
    seeds = [17, 808, 5150] if seeds is None else list(seeds)
    if not seeds or any(type(seed) is not int for seed in seeds):
        raise ValueError("seeds must be a nonempty list of integers")
    bands = tuple(bands)
    if not bands:
        raise ValueError("at least one difficulty band is required")

    generator = load_generator()
    shortcuts: dict[str, Callable] = dict(generator.CANONICAL_SHORTCUTS)
    competitors: dict[str, Callable] = dict(generator.LESSON_COMPETITORS)
    canonical = [
        pair
        for pair in canonical_pairs(
            TASK_ID, root=ROOT, variant=0, labeled_only=True
        )
        if pair["split"] == "train"
    ]

    canonical_fit: dict[str, dict[str, Any]] = {}
    for name, rival in shortcuts.items():
        mismatches = [
            index
            for index, pair in enumerate(canonical)
            if rival(deepcopy(pair["input"])) != pair["output"]
        ]
        canonical_fit[name] = {
            "pairs": len(canonical),
            "fits": len(canonical) - len(mismatches),
            "mismatch_indices": mismatches,
        }

    witnesses = _find_witnesses(
        generator,
        shortcuts,
        starts=starts,
        seeds=seeds,
        bands=bands,
    )

    production_ambiguities: list[dict[str, Any]] = []
    production_hook_failures: list[dict[str, Any]] = []
    rotation_ambiguities: list[dict[str, Any]] = []
    rotation_hook_failures: list[dict[str, Any]] = []
    rival_status_counts: dict[str, dict[str, int]] = {
        "production": defaultdict(int),
        "rotations": defaultdict(int),
    }
    unique_inputs: set[str] = set()
    lessons = 0
    rotation_queries = 0

    for band in bands:
        for seed in seeds:
            for start in range(starts):
                scheduled = [
                    _generated_pair(generator, seed, index, band)
                    for index in range(
                        start, start + generator.EXAMPLES_NEEDED
                    )
                ]
                production_query = _generated_pair(
                    generator,
                    seed,
                    start + generator.EXAMPLES_NEEDED,
                    band,
                )
                lessons += 1
                for pair in (*scheduled, production_query):
                    unique_inputs.add(grid_sha256(pair["input"]))

                demos = [
                    {"input": pair["input"], "output": pair["output"]}
                    for pair in scheduled
                ]
                query = {
                    "input": production_query["input"],
                    "output": production_query["output"],
                }
                hook = generator.lesson_identifiable(demos, query)
                if hook:
                    production_hook_failures.append(
                        {
                            "difficulty": band,
                            "seed": seed,
                            "start": start,
                            "profiles": [pair["profile"] for pair in scheduled],
                            "reasons": hook,
                        }
                    )
                for name, rival in competitors.items():
                    status = _rival_status(rival, demos, query)
                    rival_status_counts["production"][f"{name}:{status}"] += 1
                    if status == "ambiguous":
                        production_ambiguities.append(
                            {
                                "rival": name,
                                "difficulty": band,
                                "seed": seed,
                                "start": start,
                                "query_sample_index": production_query["sample_index"],
                            }
                        )

                for query_index, held_out in enumerate(scheduled):
                    rotation_queries += 1
                    rotated_demos = [
                        {"input": pair["input"], "output": pair["output"]}
                        for index, pair in enumerate(scheduled)
                        if index != query_index
                    ]
                    rotated_query = {
                        "input": held_out["input"],
                        "output": held_out["output"],
                    }
                    hook = generator.lesson_identifiable(
                        rotated_demos, rotated_query
                    )
                    if hook:
                        rotation_hook_failures.append(
                            {
                                "difficulty": band,
                                "seed": seed,
                                "start": start,
                                "query_offset": query_index,
                                "query_sample_index": held_out["sample_index"],
                                "reasons": hook,
                            }
                        )
                    for name, rival in competitors.items():
                        status = _rival_status(
                            rival, rotated_demos, rotated_query
                        )
                        rival_status_counts["rotations"][f"{name}:{status}"] += 1
                        if status == "ambiguous":
                            rotation_ambiguities.append(
                                {
                                    "rival": name,
                                    "difficulty": band,
                                    "seed": seed,
                                    "start": start,
                                    "query_offset": query_index,
                                    "query_sample_index": held_out["sample_index"],
                                }
                            )

    shortcut_fit_failures = sorted(
        name
        for name, record in canonical_fit.items()
        if record["mismatch_indices"]
    )
    missing_witnesses = sorted(set(shortcuts) - set(witnesses))
    status = "pass"
    if (
        shortcut_fit_failures
        or missing_witnesses
        or production_ambiguities
        or production_hook_failures
        or rotation_ambiguities
        or rotation_hook_failures
    ):
        status = "fail"

    return {
        "schema": "61090a45e458-shortcut-probe-v1",
        "task_id": TASK_ID,
        "status": status,
        "generator_version": generator.VERSION,
        "generator_sha256": source_sha256(),
        "rule_hash": generator.RULE_HASH,
        "canonical_demonstrations": len(canonical),
        "canonical_shortcut_fit": canonical_fit,
        "witness_by_rival": witnesses,
        "missing_witnesses": missing_witnesses,
        "shortcut_fit_failures": shortcut_fit_failures,
        "sampler": {
            "bands": list(bands),
            "seeds": seeds,
            "starts_per_seed_band": starts,
            "examples_needed": generator.EXAMPLES_NEEDED,
            "production_policy": (
                "three consecutive demonstrations followed by the next "
                "sample as query"
            ),
            "rotation_policy": (
                "hold out each of the three scheduled demonstrations once; "
                "use the other two as demonstrations"
            ),
        },
        "production": {
            "lessons": lessons,
            "ambiguities": len(production_ambiguities),
            "hook_failures": len(production_hook_failures),
            "rival_status_counts": dict(rival_status_counts["production"]),
            "ambiguity_records": production_ambiguities,
            "hook_failure_records": production_hook_failures,
        },
        "rotations": {
            "queries": rotation_queries,
            "ambiguities": len(rotation_ambiguities),
            "hook_failures": len(rotation_hook_failures),
            "rival_status_counts": dict(rival_status_counts["rotations"]),
            "ambiguity_records": rotation_ambiguities,
            "hook_failure_records": rotation_hook_failures,
        },
        "unique_materialized_inputs": len(unique_inputs),
        "limits": [
            "Finite check against declared rivals only; not a proof of unique induction.",
            "The independent Python intended-output implementation is Racket-bound separately by rule_smoke and authority_sync.",
            "The local rotation probe rotates the three scheduled examples; the shared lesson census checks the production sampler independently.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--starts", type=int, default=16)
    parser.add_argument("--seeds", type=int, nargs="+", default=[17, 808, 5150])
    parser.add_argument("--bands", nargs="+", default=["easy", "medium", "hard"])
    parser.add_argument("--out", type=Path)
    parser.add_argument("--assert-clean", action="store_true")
    args = parser.parse_args()

    report = run_probe(args.starts, args.seeds, args.bands)
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(rendered, encoding="utf-8")
    print(
        json.dumps(
            {
                "task_id": TASK_ID,
                "status": report["status"],
                "lessons": report["production"]["lessons"],
                "production_ambiguities": report["production"]["ambiguities"],
                "rotation_queries": report["rotations"]["queries"],
                "rotation_ambiguities": report["rotations"]["ambiguities"],
                "generator_sha256": report["generator_sha256"],
                "out": str(args.out) if args.out else None,
            },
            sort_keys=True,
        )
    )
    return 1 if args.assert_clean and report["status"] != "pass" else 0


if __name__ == "__main__":
    raise SystemExit(main())
