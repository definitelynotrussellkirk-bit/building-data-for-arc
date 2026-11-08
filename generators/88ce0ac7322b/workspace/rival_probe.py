#!/usr/bin/env python3
"""Retained source-bound curriculum and shortcut probe for task 88ce0ac7322b.

The probe deliberately does not copy rival names from the review.  It imports
``CANONICAL_SHORTCUTS`` and ``LESSON_COMPETITORS`` from the selected generator,
checks that every declared canonical shortcut really fits every labeled
canonical pair, exhausts the legal joint exact-axis matrix, and tests every
cyclic start of the 12-slot schedule with every one-of-four query rotation.

Outputs are computed by a small independent Python implementation.  That mirror
is supplementary semantic evidence; the repository battery remains the Racket
authority check.  A finite declared-rival pass is not a proof of unique ARC
induction, but it is a cheap regression tool for future edits to this task.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path
import sys
from typing import Any, Sequence

TASK_ID = "88ce0ac7322b"
BANDS = ("easy", "medium", "hard")

# Make the script work both in the source tree and in a portable task runtime.
_SOURCE_GUESS = Path(__file__).resolve().parents[3]
_SHARED_RUNTIME = _SOURCE_GUESS / "shared" / "runtime"
if _SHARED_RUNTIME.is_dir():
    sys.path.insert(0, str(_SHARED_RUNTIME))
if str(_SOURCE_GUESS) not in sys.path:
    sys.path.insert(0, str(_SOURCE_GUESS))

from reviewer_support import canonical_pairs, find_root  # noqa: E402

ROOT = Path(find_root(__file__))
GENERATOR_PATH = ROOT / "generators" / TASK_ID / "generator.py"


def generator_sha256() -> str:
    return hashlib.sha256(GENERATOR_PATH.read_bytes()).hexdigest()


def load_generator():
    """Load the selected bytes from this probe's own source/runtime tree."""
    spec = importlib.util.spec_from_file_location(
        f"{TASK_ID}_retained_rival_probe_generator", GENERATOR_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator at {GENERATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _split(grid: Sequence[Sequence[int]]) -> list[list[list[int]]]:
    width = len(grid[0])
    return [
        [list(row[start : start + 3]) for row in grid]
        for start in range(0, width, 4)
    ]


def _assemble(tiles: Sequence[Sequence[Sequence[int]]]) -> list[list[int]]:
    result = [[], [], []]
    for index, tile in enumerate(tiles):
        if index:
            for row in result:
                row.append(9)
        for row_index, row in enumerate(tile):
            result[row_index].extend(row)
    return result


def independent_output(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    """Sort complete 3x3 tiles by nonzero occupancy, without generator helpers."""
    tiles = _split(grid)
    ranked = sorted(
        tiles,
        key=lambda tile: sum(value != 0 for row in tile for value in row),
    )
    return _assemble(ranked)


def _grid_hash(grid: Sequence[Sequence[int]]) -> str:
    payload = json.dumps(grid, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def _axis_values(module, axis: str) -> tuple[str, ...]:
    meta = module.AXES[axis]
    raw = meta.get("valid") if isinstance(meta, dict) else None
    if not isinstance(raw, str):
        raise ValueError(f"axis {axis!r} does not expose a pipe-delimited valid domain")
    values = tuple(part.strip() for part in raw.split("|") if part.strip())
    if not values:
        raise ValueError(f"axis {axis!r} has an empty exact domain")
    return values


def _failure(kind: str, **detail: Any) -> dict[str, Any]:
    return {"kind": kind, **detail}


def run_probe(*, starts_per_band: int = 15) -> dict[str, Any]:
    if type(starts_per_band) is not int or starts_per_band < 1:
        raise ValueError("starts_per_band must be a positive integer")

    module = load_generator()
    failures: list[dict[str, Any]] = []
    canonical = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    shortcuts = dict(getattr(module, "CANONICAL_SHORTCUTS", {}) or {})
    competitors = dict(getattr(module, "LESSON_COMPETITORS", {}) or {})
    if not shortcuts:
        failures.append(_failure("no_canonical_shortcuts_declared"))
    if not competitors:
        failures.append(_failure("no_lesson_competitors_declared"))

    canonical_rows: dict[str, dict[str, Any]] = {}
    for name, rival in sorted(shortcuts.items()):
        matches = 0
        errors: list[str] = []
        for pair_index, pair in enumerate(canonical):
            try:
                matches += int(rival(pair["input"]) == pair["output"])
            except Exception as exc:  # retained evidence should report, not hide
                errors.append(f"pair {pair_index}: {type(exc).__name__}: {exc}")
        fits_all = matches == len(canonical) and not errors
        canonical_rows[name] = {
            "matching_pairs": matches,
            "denominator": len(canonical),
            "fits_all": fits_all,
            "errors": errors,
        }
        if not fits_all:
            failures.append(
                _failure(
                    "declared_shortcut_does_not_fit_canonical",
                    competitor=name,
                    matches=matches,
                    denominator=len(canonical),
                    errors=errors,
                )
            )

    profile_values = _axis_values(module, "profile")
    order_values = _axis_values(module, "order_pattern")
    override_cases = 0
    override_failures = 0
    mixed_refutations = Counter()
    for band_index, band in enumerate(BANDS):
        for case_index, (profile, order_pattern) in enumerate(
            itertools.product(profile_values, order_values)
        ):
            override_cases += 1
            seed = 610_000 + band_index * 10_000 + case_index
            try:
                grid = module.generate(
                    seed,
                    case_index,
                    difficulty=band,
                    profile=profile,
                    order_pattern=order_pattern,
                )
                errors = list(module.self_check(grid) or [])
                observed = module.observe_overrides(grid)
                expected = independent_output(grid)
                mirror = module.rule_mirror(grid)
                case_problems: list[str] = []
                if errors:
                    case_problems.append("self_check: " + "; ".join(errors))
                if observed != {
                    "profile": profile,
                    "order_pattern": order_pattern,
                }:
                    case_problems.append(f"observed overrides {observed!r}")
                if mirror != expected:
                    case_problems.append("generator mirror disagrees with independent output")
                if profile != "canonical3":
                    for name, rival in sorted(competitors.items()):
                        disagrees = rival(grid) != expected
                        mixed_refutations[name] += int(disagrees)
                        if not disagrees:
                            case_problems.append(f"mixed profile fails to refute {name}")
                if case_problems:
                    override_failures += 1
                    failures.append(
                        _failure(
                            "override_case",
                            band=band,
                            profile=profile,
                            order_pattern=order_pattern,
                            problems=case_problems,
                        )
                    )
            except Exception as exc:
                override_failures += 1
                failures.append(
                    _failure(
                        "override_exception",
                        band=band,
                        profile=profile,
                        order_pattern=order_pattern,
                        error=f"{type(exc).__name__}: {exc}",
                    )
                )

    demos = int(module.EXAMPLES_NEEDED)
    rows_per_window = demos + 1
    production_windows = 0
    rotated_queries = 0
    unidentifiable = 0
    unique_inputs: set[str] = set()
    profile_counts = Counter()
    production_survivors = Counter()
    rotation_survivors = Counter()
    by_band: dict[str, dict[str, int]] = {}

    for band_index, band in enumerate(BANDS):
        band_counts = Counter()
        for start in range(starts_per_band):
            seed = 880_000 + band_index * 100_000 + start
            pairs: list[dict[str, Any]] = []
            for offset in range(rows_per_window):
                grid = module.generate(seed, start + offset, difficulty=band)
                output = independent_output(grid)
                unique_inputs.add(_grid_hash(grid))
                observed = module.observe_overrides(grid)
                profile_counts[str(observed.get("profile"))] += 1
                if module.rule_mirror(grid) != output:
                    failures.append(
                        _failure(
                            "schedule_mirror_mismatch",
                            band=band,
                            start=start,
                            offset=offset,
                        )
                    )
                pairs.append({"input": grid, "output": output})

            production_windows += 1
            band_counts["production_windows"] += 1
            production_demos = pairs[:demos]
            production_query = pairs[demos]
            reasons = list(
                module.lesson_identifiable(production_demos, production_query) or []
            )
            if reasons:
                unidentifiable += 1
                band_counts["unidentifiable"] += 1
                failures.append(
                    _failure(
                        "production_lesson_unidentifiable",
                        band=band,
                        start=start,
                        reasons=reasons,
                    )
                )
            for name, rival in sorted(competitors.items()):
                survives = all(
                    rival(pair["input"]) == pair["output"]
                    for pair in production_demos
                )
                production_survivors[name] += int(survives)
                if survives and rival(production_query["input"]) != production_query["output"]:
                    failures.append(
                        _failure(
                            "production_rival_survives",
                            band=band,
                            start=start,
                            competitor=name,
                        )
                    )

            for query_index in range(rows_per_window):
                rotated_queries += 1
                band_counts["rotated_queries"] += 1
                query = pairs[query_index]
                rotated_demos = [
                    pair for index, pair in enumerate(pairs) if index != query_index
                ]
                reasons = list(module.lesson_identifiable(rotated_demos, query) or [])
                if reasons:
                    unidentifiable += 1
                    band_counts["unidentifiable"] += 1
                    failures.append(
                        _failure(
                            "rotated_lesson_unidentifiable",
                            band=band,
                            start=start,
                            query_index=query_index,
                            reasons=reasons,
                        )
                    )
                for name, rival in sorted(competitors.items()):
                    survives = all(
                        rival(pair["input"]) == pair["output"]
                        for pair in rotated_demos
                    )
                    rotation_survivors[name] += int(survives)
                    if survives and rival(query["input"]) != query["output"]:
                        failures.append(
                            _failure(
                                "rotation_rival_survives",
                                band=band,
                                start=start,
                                query_index=query_index,
                                competitor=name,
                            )
                        )
        by_band[band] = dict(band_counts)

    return {
        "schema": "88ce0ac7322b-rival-probe-v1",
        "task_id": TASK_ID,
        "generator_sha256": generator_sha256(),
        "generator_version": str(module.VERSION),
        "rule_hash": str(module.RULE_HASH),
        "declared_competitors": sorted(competitors),
        "declared_canonical_shortcuts": sorted(shortcuts),
        "canonical": {
            "pair_count": len(canonical),
            "shortcuts": canonical_rows,
        },
        "override_matrix": {
            "bands": list(BANDS),
            "profiles": list(profile_values),
            "order_patterns": list(order_values),
            "cases": override_cases,
            "failures": override_failures,
            "mixed_refutations": dict(sorted(mixed_refutations.items())),
        },
        "lessons": {
            "examples_needed": demos,
            "rows_per_window": rows_per_window,
            "starts_per_band": starts_per_band,
            "start_indices": list(range(starts_per_band)),
            "production_windows": production_windows,
            "rotated_queries": rotated_queries,
            "unidentifiable": unidentifiable,
            "unique_inputs": len(unique_inputs),
            "profile_counts": dict(sorted(profile_counts.items())),
            "production_surviving_competitors": dict(
                sorted(production_survivors.items())
            ),
            "rotation_surviving_competitors": dict(
                sorted(rotation_survivors.items())
            ),
            "by_band": by_band,
        },
        "domain_limits": {
            "grid_height": 3,
            "tile_shape": "3x3",
            "tile_count": "3..5",
            "separator_color": 9,
            "payload_occupancy": "1..8 distinct per strip",
            "scope": (
                "all legal exact profile/order combinations and finite declared-rival "
                "lesson windows; not universal ARC-rule uniqueness"
            ),
        },
        "failures": failures,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--starts-per-band", type=int, default=15)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    report = run_probe(starts_per_band=args.starts_per_band)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "task_id": TASK_ID,
                "generator_sha256": report["generator_sha256"],
                "override_cases": report["override_matrix"]["cases"],
                "production_windows": report["lessons"]["production_windows"],
                "rotated_queries": report["lessons"]["rotated_queries"],
                "failures": len(report["failures"]),
                "out": str(args.out),
            },
            sort_keys=True,
        )
    )
    return 1 if report["failures"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
