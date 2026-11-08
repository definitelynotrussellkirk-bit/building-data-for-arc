#!/usr/bin/env python3
"""Audit canonical-fitting shortcuts over every sliding lesson start.

The generic semantic gate samples a bounded set of lessons.  This task-local
probe exhausts a caller-selected schedule period, materializes each three-demo
window plus its query, and verifies that the visible demonstrations refute the
canonical-fitting ``never_complete_color_9`` rival before the query is scored.
It also saves an exact generated counterexample for review and future agents.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
RUNTIME = ROOT / "shared" / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))

TASK_ID = "39574cf4b561"
GENERATOR_PATH = ROOT / "generators" / TASK_ID / "generator.py"
CANONICAL_PATH = ROOT / "shared" / "data" / "canonical" / "puzzles.jsonl"
BANDS = ("easy", "medium", "hard")
DEFAULT_PERIOD = 180  # lcm(4 scene, 5 missing, 4 relation, 9 palette, 3 role)


def _load_generator():
    spec = importlib.util.spec_from_file_location(
        f"lesson_shortcut_generator_{TASK_ID}", GENERATOR_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {GENERATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_pairs() -> list[dict[str, Any]]:
    with CANONICAL_PATH.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return list(row.get("train", [])) + list(row.get("test", []))
    raise RuntimeError(f"canonical task {TASK_ID} not found")


def _grid_key(grid: list[list[int]]) -> str:
    return json.dumps(grid, separators=(",", ":"))


def _pair(generator, grid: list[list[int]]) -> dict[str, list[list[int]]]:
    return {"input": grid, "output": generator.rule_mirror(grid)}


def _counterexample_record(
    generator,
    *,
    shortcut_name: str,
    grid: list[list[int]],
    seed: int,
    sample_index: int,
    difficulty: str,
) -> dict[str, Any]:
    analysis = generator._analyze(grid)
    shortcut = generator.CANONICAL_SHORTCUTS[shortcut_name]
    return {
        "shortcut": shortcut_name,
        "seed": seed,
        "sample_index": sample_index,
        "difficulty": difficulty,
        "active_color_9": 9 in analysis["active_colors"],
        "active_colors": list(analysis["active_colors"]),
        "singleton_color": analysis["singleton_color"],
        "role_assignment": analysis["role_assignment"],
        "input": grid,
        "intended_output": generator.rule_mirror(grid),
        "shortcut_output": shortcut(grid),
    }


def audit(*, period: int = DEFAULT_PERIOD, seed: int = 610_000) -> dict[str, Any]:
    if type(period) is not int or period < 1:
        raise ValueError("period must be a positive integer")
    if type(seed) is not int:
        raise ValueError("seed must be an integer")

    generator = _load_generator()
    generator_sha256 = hashlib.sha256(GENERATOR_PATH.read_bytes()).hexdigest()
    canonical = _canonical_pairs()
    shortcuts = dict(generator.CANONICAL_SHORTCUTS)
    competitors = dict(generator.LESSON_COMPETITORS)

    shortcut_rows: dict[str, Any] = {}
    for name, shortcut in sorted(shortcuts.items()):
        matches = [
            shortcut(pair["input"]) == pair["output"] for pair in canonical
        ]
        shortcut_rows[name] = {
            "canonical_pairs": len(matches),
            "matches": sum(matches),
            "fits_all": bool(matches) and all(matches),
        }

    errors: list[str] = []
    for name, row in shortcut_rows.items():
        if not row["fits_all"]:
            errors.append(
                f"declared canonical shortcut {name!r} fits only "
                f"{row['matches']}/{row['canonical_pairs']} pairs"
            )

    band_rows: dict[str, Any] = {}
    first_counterexample = None
    n_demos = int(generator.EXAMPLES_NEEDED)
    for band_index, band in enumerate(BANDS):
        band_seed = seed + band_index * 10_000
        grids: dict[int, list[list[int]]] = {}
        invalid: list[dict[str, Any]] = []
        for sample_index in range(period + n_demos):
            grid = generator.generate(
                band_seed, sample_index, difficulty=band
            )
            grids[sample_index] = grid
            findings = list(generator.self_check(grid, difficulty=band))
            if findings:
                invalid.append(
                    {"sample_index": sample_index, "findings": findings}
                )

        role_counts = Counter(
            generator._analyze(grid)["role_assignment"]
            for grid in grids.values()
        )
        strict_count = sum(
            not generator.strict_canonical_like(grid) for grid in grids.values()
        )
        unidentifiable: list[dict[str, Any]] = []
        surviving_counts: Counter[str] = Counter()
        role_incomplete: list[dict[str, Any]] = []

        for start in range(period):
            demos = [_pair(generator, grids[start + offset]) for offset in range(n_demos)]
            query = _pair(generator, grids[start + n_demos])
            reasons = list(generator.lesson_identifiable(demos, query))
            if reasons:
                unidentifiable.append({"start": start, "reasons": reasons})

            demo_roles = {
                generator._analyze(pair["input"])["role_assignment"]
                for pair in demos
            }
            if demo_roles != set(generator.ROLE_ASSIGNMENTS):
                role_incomplete.append(
                    {"start": start, "roles": sorted(demo_roles)}
                )

            for name, competitor in competitors.items():
                fits_demos = all(
                    competitor(pair["input"]) == pair["output"]
                    for pair in demos
                )
                query_differs = (
                    competitor(query["input"]) != query["output"]
                )
                if fits_demos and query_differs:
                    surviving_counts[name] += 1

            if first_counterexample is None:
                shortcut = shortcuts["never_complete_color_9"]
                for offset in range(n_demos + 1):
                    sample_index = start + offset
                    grid = grids[sample_index]
                    if shortcut(grid) != generator.rule_mirror(grid):
                        first_counterexample = _counterexample_record(
                            generator,
                            shortcut_name="never_complete_color_9",
                            grid=grid,
                            seed=band_seed,
                            sample_index=sample_index,
                            difficulty=band,
                        )
                        break

        row = {
            "seed": band_seed,
            "period": period,
            "draws": len(grids),
            "windows": period,
            "unique_inputs": len({_grid_key(grid) for grid in grids.values()}),
            "strict_canonical_count": strict_count,
            "strict_canonical_fraction": strict_count / len(grids),
            "role_counts": dict(sorted(role_counts.items())),
            "invalid_draws": invalid,
            "unidentifiable_windows": len(unidentifiable),
            "unidentifiable_examples": unidentifiable[:3],
            "role_incomplete_windows": len(role_incomplete),
            "role_incomplete_examples": role_incomplete[:3],
            "competitor_survivor_counts": dict(sorted(surviving_counts.items())),
            "never_complete_color_9_survivors": surviving_counts.get(
                "never_complete_color_9", 0
            ),
        }
        band_rows[band] = row
        if invalid:
            errors.append(f"{band}: {len(invalid)} generated draws failed self_check")
        if unidentifiable:
            errors.append(
                f"{band}: {len(unidentifiable)}/{period} lesson windows "
                "were unidentifiable"
            )
        if role_incomplete:
            errors.append(
                f"{band}: {len(role_incomplete)}/{period} lesson windows did "
                "not show both color-9 roles"
            )
        if surviving_counts.get("never_complete_color_9", 0):
            errors.append(
                f"{band}: never_complete_color_9 survived "
                f"{surviving_counts['never_complete_color_9']}/{period} windows"
            )

    if first_counterexample is None:
        errors.append("no generated never_complete_color_9 counterexample found")

    return {
        "schema": "task_lesson_shortcut_audit/1",
        "task_id": TASK_ID,
        "generator_version": generator.VERSION,
        "generator_sha256": generator_sha256,
        "rule_hash": generator.RULE_HASH,
        "schedule_period": period,
        "schedule_period_basis": (
            "lcm(scene=4, missing=5, relation=4, palette=9, color_role=3)"
        ),
        "examples_needed": n_demos,
        "canonical_shortcuts": shortcut_rows,
        "bands": band_rows,
        "counterexample": first_counterexample,
        "errors": errors,
        "status": "PASS" if not errors else "FAIL",
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--period", type=int, default=DEFAULT_PERIOD)
    parser.add_argument("--seed", type=int, default=610_000)
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args(argv)
    report = audit(period=args.period, seed=args.seed)
    text = json.dumps(report, indent=2, sort_keys=True)
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
