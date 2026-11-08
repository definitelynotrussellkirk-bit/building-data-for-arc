#!/usr/bin/env python3
"""Source-bound lesson census for c782972f840b.

The probe deliberately uses an independent Python implementation of the
rotation-only relation matrix.  It checks that every declared canonical
shortcut fits every usable canonical pair, then assembles non-overlapping
3-demo + 1-query lessons from the generator's real default sampler and measures
whether each declared lesson competitor survives the demonstrations.

Example from the packet repository::

    python3 generators/c782972f840b/workspace/lesson_probe.py \
      --lessons-per-band 100 --out ../checks/c782972f840b_lesson_probe.json
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from types import ModuleType
from typing import Any, Callable

TASK_ID = "c782972f840b"
BANDS = ("easy", "medium", "hard")
REPO = Path(__file__).resolve().parents[3]
DEFAULT_GENERATOR = REPO / "generators" / TASK_ID / "generator.py"
DEFAULT_CANONICAL = REPO / "shared" / "data" / "canonical" / "puzzles.jsonl"


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _grid_hash(grid: list[list[int]]) -> str:
    return _sha256(json.dumps(grid, separators=(",", ":")).encode())


def _load_generator(path: Path) -> ModuleType:
    runtime = REPO / "shared" / "runtime"
    if runtime.is_dir() and str(runtime) not in sys.path:
        sys.path.insert(0, str(runtime))
    source = path.read_bytes()
    name = f"c782972f840b_lesson_probe_{_sha256(source)[:16]}"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ValueError(f"cannot import generator {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    exec(compile(source, str(path), "exec"), module.__dict__)
    return module


def _components(grid: list[list[int]]) -> list[dict[str, Any]]:
    """Independent 4-connected nonzero component extraction."""
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[dict[str, Any]] = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] == 0 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells: list[tuple[int, int]] = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    rr, cc = r + dr, c + dc
                    if (
                        0 <= rr < height
                        and 0 <= cc < width
                        and grid[rr][cc] != 0
                        and (rr, cc) not in seen
                    ):
                        seen.add((rr, cc))
                        stack.append((rr, cc))
            colors = {grid[r][c] for r, c in cells}
            if len(colors) != 1:
                raise ValueError("independent oracle found a multicolor component")
            result.append(
                {
                    "cells": tuple(sorted(cells)),
                    "top_left": (min(r for r, _ in cells), min(c for _, c in cells)),
                    "color": next(iter(colors)),
                }
            )
    return sorted(result, key=lambda item: item["top_left"])


def _normalize(points) -> tuple[tuple[int, int], ...]:
    points = tuple(points)
    if not points:
        return ()
    top = min(row for row, _ in points)
    left = min(col for _, col in points)
    return tuple(sorted((row - top, col - left) for row, col in points))


def _rotate(shape) -> tuple[tuple[int, int], ...]:
    return _normalize((col, -row) for row, col in shape)


def _rotation_key(shape) -> tuple[tuple[int, int], ...]:
    current = _normalize(shape)
    variants = []
    for _ in range(4):
        variants.append(current)
        current = _rotate(current)
    return min(variants)


def independent_output(grid: list[list[int]]) -> list[list[int]]:
    """Implement the selected rule without importing generator helpers."""
    items = _components(grid)
    for item in items:
        item["rotation"] = _rotation_key(item["cells"])
    size = len(items)
    output = [[0] * size for _ in range(size)]
    for row, left in enumerate(items):
        for col, right in enumerate(items):
            if row == col:
                output[row][col] = 9
                continue
            same_shape = left["rotation"] == right["rotation"]
            same_color = left["color"] == right["color"]
            output[row][col] = (
                6
                if same_shape and same_color
                else 4
                if same_shape
                else 2
                if same_color
                else 0
            )
    return output


def _canonical_pairs(path: Path = DEFAULT_CANONICAL) -> list[dict[str, Any]]:
    pairs: list[dict[str, Any]] = []
    for line in path.read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") != TASK_ID:
            continue
        for split in ("train", "test"):
            section = row.get(split) or []
            if isinstance(section, dict):
                section = [section]
            for index, pair in enumerate(section):
                pairs.append({"split": split, "index": index, **pair})
    if not pairs:
        raise ValueError(f"no canonical pairs for {TASK_ID}")
    return pairs


def _declarations(module: ModuleType, name: str) -> dict[str, Callable]:
    value = getattr(module, name, None)
    if not isinstance(value, dict):
        raise ValueError(f"{name} must be a dict")
    if any(not isinstance(key, str) or not callable(function) for key, function in value.items()):
        raise ValueError(f"{name} must be dict[str, callable]")
    return dict(value)


def _evaluate(function: Callable, grid: list[list[int]]) -> tuple[Any, str | None]:
    try:
        return function([row[:] for row in grid]), None
    except Exception as exc:  # diagnostic output, not silent fallback
        return None, f"{type(exc).__name__}: {exc}"


def _canonical_shortcut_checks(
    shortcuts: dict[str, Callable], pairs: list[dict[str, Any]]
) -> dict[str, Any]:
    checks: dict[str, Any] = {}
    for name, function in shortcuts.items():
        rows = []
        for pair in pairs:
            predicted, error = _evaluate(function, pair["input"])
            rows.append(
                {
                    "split": pair["split"],
                    "index": pair["index"],
                    "fits": error is None and predicted == pair["output"],
                    "error": error,
                }
            )
        checks[name] = {
            "fits_all": all(row["fits"] for row in rows),
            "matching_pairs": sum(row["fits"] for row in rows),
            "denominator": len(rows),
            "pairs": rows,
        }
    return checks


def audit_lessons(module: ModuleType, lessons_per_band: int = 100) -> dict[str, Any]:
    if lessons_per_band < 1:
        raise ValueError("lessons_per_band must be positive")
    examples = int(getattr(module, "EXAMPLES_NEEDED", 3))
    if examples < 1:
        raise ValueError("EXAMPLES_NEEDED must be positive")

    competitors = _declarations(module, "LESSON_COMPETITORS")
    shortcuts = _declarations(module, "CANONICAL_SHORTCUTS")
    witnesses = _declarations(module, "SEMANTIC_WITNESSES")
    witness_rivals = getattr(module, "WITNESS_RIVALS", {})
    if not isinstance(witness_rivals, dict):
        raise ValueError("WITNESS_RIVALS must be a dict")

    canonical = _canonical_pairs()
    canonical_authority = [
        {
            "split": pair["split"],
            "index": pair["index"],
            "fits": independent_output(pair["input"]) == pair["output"],
        }
        for pair in canonical
    ]
    shortcut_checks = _canonical_shortcut_checks(shortcuts, canonical)

    totals = Counter()
    global_inputs: set[str] = set()
    global_outputs: set[str] = set()
    first_counterexample: dict[str, Any] = {}
    by_band: dict[str, Any] = {}
    all_heights: list[int] = []
    all_widths: list[int] = []
    all_palette_sizes: list[int] = []
    all_object_counts: list[int] = []
    all_canvas_profiles: set[str] = set()
    all_relation_profiles: set[str] = set()

    for band_index, band in enumerate(BANDS):
        band_counts = Counter(lessons=lessons_per_band)
        band_inputs: set[str] = set()
        band_outputs: set[str] = set()
        profiles = Counter()
        relation_profiles = Counter()
        object_counts = Counter()
        competitor_stats = {
            name: Counter(
                lessons=0,
                survives_all_demos=0,
                demo_disagreements=0,
                query_disagreements=0,
                query_disagreeing_survivors=0,
                errors=0,
            )
            for name in competitors
        }
        witness_stats = {
            name: Counter(rows=0, fires=0, lessons_with_demo_witness=0)
            for name in witnesses
        }

        for lesson_index in range(lessons_per_band):
            seed = 910_000 + band_index * 100_000 + lesson_index
            start = lesson_index * (examples + 1)
            rows = []
            for offset in range(examples + 1):
                sample_index = start + offset
                grid = module.generate(seed, sample_index, difficulty=band)
                repeat = module.generate(seed, sample_index, difficulty=band)
                if repeat != grid:
                    band_counts["nondeterministic_rows"] += 1
                errors = module.self_check(grid)
                if errors:
                    band_counts["self_check_failures"] += 1
                authority = independent_output(grid)
                observed = module.observe_overrides(grid)
                predictions = {}
                for name, function in competitors.items():
                    predictions[name] = _evaluate(function, grid)
                witness_values = {}
                for name, function in witnesses.items():
                    value, error = _evaluate(function, grid)
                    witness_values[name] = bool(value) if error is None else False
                    witness_stats[name]["rows"] += 1
                    witness_stats[name]["fires"] += int(witness_values[name])

                input_hash = _grid_hash(grid)
                output_hash = _grid_hash(authority)
                band_inputs.add(input_hash)
                band_outputs.add(output_hash)
                global_inputs.add(input_hash)
                global_outputs.add(output_hash)
                palette_size = len({value for row in grid for value in row})
                object_count = len(_components(grid))
                profiles[str(observed["canvas_profile"])] += 1
                relation_profiles[str(observed["relation_profile"])] += 1
                object_counts[str(object_count)] += 1
                all_heights.append(len(grid))
                all_widths.append(len(grid[0]))
                all_palette_sizes.append(palette_size)
                all_object_counts.append(object_count)
                all_canvas_profiles.add(str(observed["canvas_profile"]))
                all_relation_profiles.add(str(observed["relation_profile"]))
                rows.append(
                    {
                        "seed": seed,
                        "sample_index": sample_index,
                        "grid": grid,
                        "authority": authority,
                        "predictions": predictions,
                        "witness_values": witness_values,
                    }
                )
                band_counts["rows"] += 1

            for witness_name in witnesses:
                if any(row["witness_values"][witness_name] for row in rows[:examples]):
                    witness_stats[witness_name]["lessons_with_demo_witness"] += 1
                else:
                    band_counts["lessons_missing_demo_witness"] += 1

            for name in competitors:
                stats = competitor_stats[name]
                stats["lessons"] += 1
                demo_disagreements = 0
                demo_error = False
                for row in rows[:examples]:
                    predicted, error = row["predictions"][name]
                    if error is not None:
                        stats["errors"] += 1
                        demo_error = True
                    if error is not None or predicted != row["authority"]:
                        demo_disagreements += 1
                        if name not in first_counterexample:
                            first_counterexample[name] = {
                                "difficulty": band,
                                "seed": row["seed"],
                                "sample_index": row["sample_index"],
                                "input": row["grid"],
                                "authority_output": row["authority"],
                                "rival_output": predicted,
                                "rival_error": error,
                            }
                survives = demo_disagreements == 0 and not demo_error
                query_prediction, query_error = rows[examples]["predictions"][name]
                query_disagrees = (
                    query_error is not None
                    or query_prediction != rows[examples]["authority"]
                )
                stats["demo_disagreements"] += demo_disagreements
                stats["survives_all_demos"] += int(survives)
                stats["query_disagreements"] += int(query_disagrees)
                stats["query_disagreeing_survivors"] += int(
                    survives and query_disagrees
                )
                band_counts["surviving_competitor_lessons"] += int(survives)

        band_counts["unique_inputs"] = len(band_inputs)
        band_counts["unique_outputs"] = len(band_outputs)
        totals.update(band_counts)
        by_band[band] = {
            **dict(band_counts),
            "canvas_profiles": dict(sorted(profiles.items())),
            "relation_profiles": dict(sorted(relation_profiles.items())),
            "object_counts": dict(sorted(object_counts.items())),
            "competitors": {
                name: dict(stats)
                for name, stats in sorted(competitor_stats.items())
            },
            "witnesses": {
                name: dict(stats) for name, stats in sorted(witness_stats.items())
            },
        }

    # Counter.update sums per-band unique counts; replace with true global counts.
    totals["unique_inputs"] = len(global_inputs)
    totals["unique_outputs"] = len(global_outputs)
    for key in (
        "self_check_failures",
        "nondeterministic_rows",
        "surviving_competitor_lessons",
        "lessons_missing_demo_witness",
    ):
        totals.setdefault(key, 0)

    return {
        "schema": "c782972f840b-lesson-probe-v1",
        "task_id": TASK_ID,
        "lessons_per_band": lessons_per_band,
        "examples_per_lesson": examples,
        "queries_per_lesson": 1,
        "bands": list(BANDS),
        "sampling": {
            "generator_entrypoint": "generate(seed, sample_index, difficulty=band)",
            "seed_formula": "910000 + band_index*100000 + lesson_index",
            "lesson_start_sample_index": f"lesson_index*{examples + 1}",
            "rows_per_lesson": examples + 1,
            "overlap": "none",
            "schedule_cycle": "not applicable; generator declares no deterministic lesson schedule",
            "sampler": "actual default generator sampler; no overrides",
        },
        "declared": {
            "canonical_shortcuts": sorted(shortcuts),
            "lesson_competitors": sorted(competitors),
            "semantic_witnesses": sorted(witnesses),
            "witness_rivals": witness_rivals,
        },
        "canonical_pair_count": len(canonical),
        "canonical_independent_authority_fit": {
            "fits_all": all(row["fits"] for row in canonical_authority),
            "matching_pairs": sum(row["fits"] for row in canonical_authority),
            "denominator": len(canonical_authority),
            "pairs": canonical_authority,
        },
        "canonical_shortcut_fit": shortcut_checks,
        "totals": dict(totals),
        "by_band": by_band,
        "first_competitor_counterexample": first_counterexample,
        "observed_domain": {
            "height": [min(all_heights), max(all_heights)],
            "width": [min(all_widths), max(all_widths)],
            "palette_size_including_background": [
                min(all_palette_sizes),
                max(all_palette_sizes),
            ],
            "object_count": [min(all_object_counts), max(all_object_counts)],
            "canvas_profiles": sorted(all_canvas_profiles),
            "relation_profiles": sorted(all_relation_profiles),
            "shape_bbox_limit": "generator self_check enforces <=3x3",
            "scope": "finite declared rivals over sampled lawful lessons; not universal induction",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generator", type=Path, default=DEFAULT_GENERATOR)
    parser.add_argument("--lessons-per-band", type=int, default=100)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    generator_path = args.generator.resolve()
    module = _load_generator(generator_path)
    report = audit_lessons(module, lessons_per_band=args.lessons_per_band)
    canonical_path = DEFAULT_CANONICAL.resolve()
    report["source"] = {
        "generator_path": str(generator_path.relative_to(REPO)),
        "generator_sha256": _sha256(generator_path.read_bytes()),
        "probe_path": str(Path(__file__).resolve().relative_to(REPO)),
        "probe_sha256": _sha256(Path(__file__).read_bytes()),
        "canonical_path": str(canonical_path.relative_to(REPO)),
        "canonical_sha256": _sha256(canonical_path.read_bytes()),
        "declared_rule_hash": getattr(module, "RULE_HASH", None),
    }

    failures = []
    if not report["canonical_independent_authority_fit"]["fits_all"]:
        failures.append("independent authority does not fit every canonical pair")
    failures.extend(
        f"canonical shortcut {name!r} does not fit all canonical pairs"
        for name, row in report["canonical_shortcut_fit"].items()
        if not row["fits_all"]
    )
    for key in (
        "self_check_failures",
        "nondeterministic_rows",
        "surviving_competitor_lessons",
        "lessons_missing_demo_witness",
    ):
        if report["totals"].get(key, 0):
            failures.append(f"{key}={report['totals'][key]}")
    report["status"] = "PASS" if not failures else "FAIL"
    report["failures"] = failures

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "status": report["status"],
                "task_id": TASK_ID,
                "generator_sha256": report["source"]["generator_sha256"],
                "lessons_per_band": args.lessons_per_band,
                "totals": report["totals"],
                "failures": failures,
            },
            indent=2,
        )
    )
    return int(bool(failures))


if __name__ == "__main__":
    raise SystemExit(main())
