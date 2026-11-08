#!/usr/bin/env python3
"""Reproduce two assigned audit-only generator shortcuts without editing targets.

The probe is deliberately independent of each target's declared rival list.  It:
- verifies source hashes from AUDIT_ASSIGNMENT.json;
- checks the rival against every public training pair;
- samples 100 seeds x 20 indices x four difficulty bands;
- checks every cyclic lesson start in that sample;
- validates one lawful counterexample and writes its input for canonical Racket apply.
"""
from __future__ import annotations

from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[2]
REPO = ROOT / "repo"
RUNTIME = REPO / "shared" / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))

BANDS: tuple[str | None, ...] = (None, "easy", "medium", "hard")
SEEDS = range(100)
INDICES = range(20)

TARGETS = {
    "8bc2bc6a9bb8": {
        "base": REPO / "shared/data/base/solutions/banks/22a17f7a0399/H70__8bc2bc6a9bb8.json",
        "expected_hash": "a4628bb6520d8d4805b5a99b699598c00ce1816fc6f4f20fffbeb8b3fb6f01a3",
        "rival": "bbox_area_then_cell_count",
    },
    "7aed1f233b46": {
        "base": REPO / "shared/data/base/solutions/banks/129d068bbf4e/S18_H3__7aed1f233b46.json",
        "expected_hash": "8611cbb884c2babafac47be4e66e6ed1d96f42fee51c2da02143b41e4723d3ea",
        "rival": "largest_non_full_canvas_bbox",
    },
}


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _grid_key(grid: list[list[int]]) -> str:
    raw = json.dumps(grid, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def _load_generator(task_id: str):
    path = REPO / "generators" / task_id / "generator.py"
    name = f"audit_probe_{task_id}"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _components_8(grid: list[list[int]]) -> list[dict[str, Any]]:
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    objects: list[dict[str, Any]] = []
    for row in range(2, h):
        for col in range(w):
            if grid[row][col] != 8 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells: list[tuple[int, int]] = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nxt = (r + dr, c + dc)
                    if (
                        2 <= nxt[0] < h
                        and 0 <= nxt[1] < w
                        and grid[nxt[0]][nxt[1]] == 8
                        and nxt not in seen
                    ):
                        seen.add(nxt)
                        stack.append(nxt)
            r0 = min(r for r, _ in cells)
            c0 = min(c for _, c in cells)
            r1 = max(r for r, _ in cells)
            c1 = max(c for _, c in cells)
            objects.append(
                {
                    "cells": tuple(sorted(cells)),
                    "bbox": (r0, c0, r1, c1),
                    "size": len(cells),
                    "height": r1 - r0 + 1,
                    "width": c1 - c0 + 1,
                    "normalized": tuple(sorted((r - r0, c - c0) for r, c in cells)),
                }
            )
    return objects


def _rival_8(grid: list[list[int]]) -> list[list[int]]:
    """Sort footprint-first, using occupied count only for equal footprints."""
    palette = [value for value in grid[0] if value != 0]
    objects = _components_8(grid)
    objects.sort(
        key=lambda obj: (
            -(obj["height"] * obj["width"]),
            -obj["size"],
            obj["bbox"],
        )
    )
    max_height = max(obj["height"] for obj in objects)
    width = sum(obj["width"] for obj in objects) + max(0, len(objects) - 1)
    output = [[0] * width for _ in range(max_height)]
    left = 0
    for obj, color in zip(objects, palette):
        top = max_height - obj["height"]
        for row, col in obj["normalized"]:
            output[top + row][left + col] = color
        left += obj["width"] + 1
    return output


def _records_7(grid: list[list[int]]) -> list[dict[str, int | tuple[int, int, int, int]]]:
    positions: dict[int, list[tuple[int, int]]] = {}
    for row, values in enumerate(grid):
        for col, color in enumerate(values):
            if color:
                positions.setdefault(color, []).append((row, col))
    records = []
    for color, cells in positions.items():
        r0 = min(r for r, _ in cells)
        c0 = min(c for _, c in cells)
        r1 = max(r for r, _ in cells)
        c1 = max(c for _, c in cells)
        height = r1 - r0 + 1
        width = c1 - c0 + 1
        records.append(
            {
                "color": color,
                "bbox": (r0, c0, r1, c1),
                "height": height,
                "width": width,
                "area": height * width,
            }
        )
    return records


def _rival_7(grid: list[list[int]]) -> list[list[int]]:
    """Choose the largest bbox after discarding any full-canvas candidate."""
    h, w = len(grid), len(grid[0])
    records = _records_7(grid)
    eligible = [obj for obj in records if obj["bbox"] != (0, 0, h - 1, w - 1)]
    if not eligible:
        eligible = records
    chosen = min(eligible, key=lambda obj: (-int(obj["area"]), int(obj["color"])))
    return [[8] * int(chosen["width"]) for _ in range(int(chosen["height"]))]


def _counterexample_8() -> list[list[int]]:
    grid = [[0] * 12 for _ in range(8)]
    for col, color in ((0, 2), (2, 3), (4, 4)):
        grid[0][col] = color
    # Five-cell line: true size rank 1, footprint area 5.
    for col in range(5):
        grid[2][col] = 8
    # Four-cell L: true size rank 2, footprint area 6.
    for row, col in ((4, 7), (5, 7), (6, 7), (6, 8)):
        grid[row][col] = 8
    grid[6][0] = 8
    return grid


def _counterexample_7() -> list[list[int]]:
    grid = [[0] * 12 for _ in range(8)]
    # The unique true winner closes to a 3x3 rectangle.
    for row, col in ((4, 7), (4, 9), (6, 7), (6, 9)):
        grid[row][col] = 2
    # A larger 4x5 nonrectangular closure defeats the bbox shortcut.
    for row, col in ((0, 0), (0, 4), (3, 0)):
        grid[row][col] = 3
    for row, col in ((5, 1), (5, 3), (6, 1)):
        grid[row][col] = 4
    return grid


RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "8bc2bc6a9bb8": _rival_8,
    "7aed1f233b46": _rival_7,
}
COUNTEREXAMPLES = {
    "8bc2bc6a9bb8": _counterexample_8,
    "7aed1f233b46": _counterexample_7,
}


def run(task_id: str) -> dict[str, Any]:
    config = TARGETS[task_id]
    generator_path = REPO / "generators" / task_id / "generator.py"
    source_hash = _sha(generator_path)
    if source_hash != config["expected_hash"]:
        raise RuntimeError(
            f"source hash changed for {task_id}: {source_hash} != {config['expected_hash']}"
        )
    generator = _load_generator(task_id)
    rival = RIVALS[task_id]
    public = json.loads(Path(config["base"]).read_text())["visible_context"]["train"]
    public_results = [
        {
            "index": index,
            "matches": rival(pair["input"]) == pair["output"],
            "input_hash": _grid_key(pair["input"]),
            "output_hash": _grid_key(pair["output"]),
        }
        for index, pair in enumerate(public)
    ]

    generated: dict[tuple[str | None, int, int], tuple[list[list[int]], list[list[int]]]] = {}
    unique_inputs: set[str] = set()
    profile_counts: Counter[str] = Counter()
    mismatch_cases: list[dict[str, Any]] = []
    generation_failures: list[dict[str, Any]] = []
    for band in BANDS:
        for seed in SEEDS:
            for sample_index in INDICES:
                key = (band, seed, sample_index)
                try:
                    grid = generator.generate(seed, sample_index, difficulty=band)
                    truth = generator.rule_mirror(grid)
                    prediction = rival(grid)
                    generated[key] = (truth, prediction)
                    unique_inputs.add(_grid_key(grid))
                    observables = generator.semantic_observables(grid)
                    profile = observables.get("scene_profile")
                    if profile is None:
                        profile = generator.schedule_profile(seed, sample_index, band)
                    profile_counts[str(profile)] += 1
                    if prediction != truth:
                        mismatch_cases.append(
                            {
                                "band": band,
                                "seed": seed,
                                "sample_index": sample_index,
                                "truth": truth,
                                "rival": prediction,
                            }
                        )
                except Exception as exc:
                    generation_failures.append(
                        {
                            "band": band,
                            "seed": seed,
                            "sample_index": sample_index,
                            "exception": f"{type(exc).__name__}: {exc}",
                        }
                    )

    window_size = int(generator.EXAMPLES_NEEDED)
    cyclic_windows = 0
    surviving_windows = 0
    changed_query_windows = 0
    for band in BANDS:
        for seed in SEEDS:
            for start in INDICES:
                keys = [
                    (band, seed, (start + offset) % len(INDICES))
                    for offset in range(window_size + 1)
                ]
                if not all(key in generated for key in keys):
                    continue
                cyclic_windows += 1
                demos = keys[:window_size]
                query = keys[-1]
                if all(generated[key][0] == generated[key][1] for key in demos):
                    surviving_windows += 1
                    if generated[query][0] != generated[query][1]:
                        changed_query_windows += 1

    counterexample = COUNTEREXAMPLES[task_id]()
    self_errors = list(generator.self_check(counterexample))
    strict_errors = list(generator.strict_canonical_like(counterexample))
    truth = generator.rule_mirror(counterexample)
    rival_output = rival(counterexample)

    out_dir = ROOT / "checks" / "audit" / task_id
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "input.json").write_text(json.dumps(counterexample, indent=2) + "\n")
    (out_dir / "rival_output.json").write_text(json.dumps(rival_output, indent=2) + "\n")
    report = {
        "schema": "arcpuzzles-assigned-audit-shortcut-v1",
        "task_id": task_id,
        "generator_sha256": source_hash,
        "rule_hash": generator.RULE_HASH,
        "rival_name": config["rival"],
        "rival_definition": (
            "Sort components by bounding-box area descending, use occupied-cell count "
            "only as an equal-footprint tie-break, then perform the documented packing."
            if task_id == "8bc2bc6a9bb8"
            else "Discard any candidate whose bbox is the entire input canvas, then output "
            "the largest remaining bbox as a cyan rectangle."
        ),
        "public_training_pairs": {
            "checked": len(public_results),
            "matched": sum(result["matches"] for result in public_results),
            "cases": public_results,
        },
        "generated_sample": {
            "bands": ["default" if band is None else band for band in BANDS],
            "seed_range": "0..99",
            "sample_index_range": "0..19",
            "requests": len(BANDS) * len(SEEDS) * len(INDICES),
            "successful_draws": len(generated),
            "unique_inputs": len(unique_inputs),
            "rival_matches": len(generated) - len(mismatch_cases),
            "mismatches": len(mismatch_cases),
            "generation_failures": generation_failures,
            "profile_counts": dict(sorted(profile_counts.items())),
            "first_mismatches": mismatch_cases[:5],
        },
        "cyclic_lesson_sample": {
            "assembly": (
                f"for each band/seed/start in 0..19, {window_size} demos followed by one "
                "query, indices wrapped modulo 20"
            ),
            "lesson_window_size": window_size,
            "windows_checked": cyclic_windows,
            "windows_where_rival_fits_all_demos": surviving_windows,
            "windows_where_fitting_rival_changes_generated_query": changed_query_windows,
        },
        "counterexample": {
            "input_path": f"checks/audit/{task_id}/input.json",
            "input_hash": _grid_key(counterexample),
            "self_check_errors": self_errors,
            "strict_canonical_like_errors": strict_errors,
            "intended_output": truth,
            "rival_output": rival_output,
            "outputs_differ": truth != rival_output,
            "belongs_to_documented_validator_domain": not self_errors,
            "belongs_to_strict_canonical_profile": not strict_errors,
        },
        "command": "python3 checks/audit/adversarial_shortcut_probe.py",
        "working_directory": str(ROOT),
        "limitations": [
            "The 8,000-draw census is finite; the zero-mismatch claim outside that sample follows from inspection of the target's finite shape/profile constructors, not exhaustive seed enumeration.",
            "A surviving rival demonstrates under-identification of the generated distribution; it does not imply the canonical Racket rule is wrong.",
        ],
    }
    (out_dir / "probe.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return report


def main() -> int:
    summaries = []
    for task_id in TARGETS:
        report = run(task_id)
        summaries.append(
            {
                "task_id": task_id,
                "public": report["public_training_pairs"],
                "generated_sample": report["generated_sample"],
                "cyclic_lesson_sample": report["cyclic_lesson_sample"],
                "counterexample": report["counterexample"],
            }
        )
    print(json.dumps(summaries, indent=2, sort_keys=True))
    failures = [
        report
        for report in summaries
        if report["public"]["matched"] != report["public"]["checked"]
        or report["generated_sample"]["mismatches"]
        or report["generated_sample"]["generation_failures"]
        or not report["counterexample"]["outputs_differ"]
        or report["counterexample"]["self_check_errors"]
    ]
    return int(bool(failures))


if __name__ == "__main__":
    raise SystemExit(main())
