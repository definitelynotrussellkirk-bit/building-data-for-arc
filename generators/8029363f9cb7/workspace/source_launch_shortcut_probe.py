#!/usr/bin/env python3
"""Measure the canonical source-anchor shortcut and generated rebuttals.

The rival launches horizontally away from the nearest vertical frame.  It is a
plausible canonical shortcut because every public source is adjacent to the left
frame, but it disagrees with the intended always-right launch on right-side
sources.  The probe is independent of the generator's rival implementation so
it can compare historical and repaired source files.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

from reviewer_support import canonical_pairs, find_root


TASK_ID = "8029363f9cb7"
BANDS = ("easy", "medium", "hard")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_generator(path: Path):
    name = f"probe_generator_{_sha256(path)[:16]}"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _source(grid: list[list[int]]) -> tuple[int, int]:
    cells = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 2
    ]
    if len(cells) != 1:
        raise ValueError(f"expected one red source, found {len(cells)}")
    return cells[0]


def _source_side(grid: list[list[int]]) -> str:
    _, col = _source(grid)
    width = len(grid[0])
    left = col
    right = width - 1 - col
    if left < right:
        return "left"
    if right < left:
        return "right"
    return "center"


def _reflect(color: int, dr: int, dc: int) -> tuple[int, int]:
    if color == 3:
        return -dc, -dr
    if color == 4:
        return dc, dr
    raise ValueError(color)


def nearest_frame_launch(grid: list[list[int]]) -> list[list[int]]:
    """Trace the shortcut rule without importing generator rival helpers."""
    output = [list(row) for row in grid]
    height, width = len(grid), len(grid[0])
    row, source_col = _source(grid)
    left = source_col
    right = width - 1 - source_col
    dc = 1 if left <= right else -1
    col = source_col + dc
    dr = 0
    seen: set[tuple[int, int, int, int]] = set()
    for _ in range(max(500, height * width * 8)):
        state = (row, col, dr, dc)
        if state in seen or not (0 <= row < height and 0 <= col < width):
            break
        seen.add(state)
        value = grid[row][col]
        if value == 5:
            break
        if value == 0:
            output[row][col] = 8
        elif value in (3, 4):
            dr, dc = _reflect(value, dr, dc)
        row += dr
        col += dc
    return output


def _grid_hash(grid: list[list[int]]) -> str:
    payload = json.dumps(grid, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def _materialize_call(gen: Any, *, seed: int, sample_index: int, difficulty: str):
    grid = gen.generate(seed, sample_index, difficulty=difficulty)
    intended = gen.rule_mirror(grid)
    rival = nearest_frame_launch(grid)
    return grid, intended, rival


def run_probe(
    generator_path: Path,
    *,
    canonical_root: Path,
    samples_per_band: int,
    window_seeds: int,
    window_starts: int,
) -> dict[str, Any]:
    gen = _load_generator(generator_path)
    canonical = canonical_pairs(TASK_ID, root=canonical_root)
    canonical_rows = []
    for pair in canonical:
        rival = nearest_frame_launch(pair["input"])
        canonical_rows.append(
            {
                "variant": pair["variant"],
                "split": pair["split"],
                "pair_index": pair["pair_index"],
                "matches": rival == pair["output"],
                "input_sha256": _grid_hash(pair["input"]),
            }
        )

    generated: dict[str, Any] = {}
    first_witness = None
    for band in BANDS:
        counts = {
            "requested": samples_per_band,
            "generated": 0,
            "errors": 0,
            "left_sources": 0,
            "right_sources": 0,
            "center_sources": 0,
            "rival_disagreements": 0,
            "unique_inputs": 0,
        }
        unique_inputs: set[str] = set()
        first_error = None
        for ordinal in range(samples_per_band):
            seed = ordinal // 4
            sample_index = ordinal
            try:
                grid, intended, rival = _materialize_call(
                    gen,
                    seed=seed,
                    sample_index=sample_index,
                    difficulty=band,
                )
            except Exception as exc:  # retain exact first generation failure
                counts["errors"] += 1
                if first_error is None:
                    first_error = {
                        "seed": seed,
                        "sample_index": sample_index,
                        "difficulty": band,
                        "error": f"{type(exc).__name__}: {exc}",
                    }
                continue
            counts["generated"] += 1
            side = _source_side(grid)
            counts[f"{side}_sources"] += 1
            unique_inputs.add(_grid_hash(grid))
            if rival != intended:
                counts["rival_disagreements"] += 1
                if first_witness is None:
                    profile = None
                    if hasattr(gen, "observe_overrides"):
                        profile = gen.observe_overrides(grid).get("scene_profile")
                    first_witness = {
                        "generate_call": {
                            "seed": seed,
                            "sample_index": sample_index,
                            "difficulty": band,
                        },
                        "scene_profile": profile,
                        "source": list(_source(grid)),
                        "source_side": side,
                        "input": grid,
                        "intended_output": intended,
                        "rival_output": rival,
                    }
        counts["unique_inputs"] = len(unique_inputs)
        generated[band] = {"counts": counts, "first_error": first_error}

    windows: dict[str, Any] = {}
    for band in BANDS:
        checked = 0
        generation_errors = 0
        missing_side_witness = 0
        rival_survivors = 0
        lesson_failures = 0
        first_failure = None
        for seed in range(window_seeds):
            for start in range(window_starts):
                checked += 1
                try:
                    grids = [
                        gen.generate(seed, start + offset, difficulty=band)
                        for offset in range(int(gen.EXAMPLES_NEEDED))
                    ]
                    query_grid = gen.generate(
                        seed,
                        start + int(gen.EXAMPLES_NEEDED),
                        difficulty=band,
                    )
                except Exception as exc:
                    generation_errors += 1
                    if first_failure is None:
                        first_failure = {
                            "kind": "generation_error",
                            "seed": seed,
                            "start": start,
                            "error": f"{type(exc).__name__}: {exc}",
                        }
                    continue
                sides = {_source_side(grid) for grid in grids}
                if sides != {"left", "right"}:
                    missing_side_witness += 1
                    if first_failure is None:
                        first_failure = {
                            "kind": "missing_side_witness",
                            "seed": seed,
                            "start": start,
                            "sides": sorted(sides),
                        }
                if all(
                    nearest_frame_launch(grid) == gen.rule_mirror(grid)
                    for grid in grids
                ):
                    rival_survivors += 1
                    if first_failure is None:
                        first_failure = {
                            "kind": "rival_survived_all_demos",
                            "seed": seed,
                            "start": start,
                        }
                demos = [
                    {"input": grid, "output": gen.rule_mirror(grid)}
                    for grid in grids
                ]
                query = {
                    "input": query_grid,
                    "output": gen.rule_mirror(query_grid),
                }
                reasons = gen.lesson_identifiable(demos, query)
                if reasons:
                    lesson_failures += 1
                    if first_failure is None:
                        first_failure = {
                            "kind": "lesson_identifiable",
                            "seed": seed,
                            "start": start,
                            "reasons": reasons,
                        }
        windows[band] = {
            "checked": checked,
            "generation_errors": generation_errors,
            "missing_side_witness": missing_side_witness,
            "rival_survived_all_demos": rival_survivors,
            "lesson_failures": lesson_failures,
            "first_failure": first_failure,
        }

    return {
        "schema": "arcpuzzles-source-launch-shortcut-probe-v1",
        "task_id": TASK_ID,
        "generator_path": str(generator_path),
        "generator_sha256": _sha256(generator_path),
        "generator_version": getattr(gen, "VERSION", None),
        "rule_hash": getattr(gen, "RULE_HASH", None),
        "probe_sha256": _sha256(Path(__file__)),
        "rival": "launch horizontally away from the nearest vertical frame",
        "canonical": {
            "pair_count": len(canonical_rows),
            "matched": sum(row["matches"] for row in canonical_rows),
            "rows": canonical_rows,
        },
        "sampling": {
            "samples_per_band": samples_per_band,
            "bands": generated,
            "total_generated": sum(
                row["counts"]["generated"] for row in generated.values()
            ),
            "total_errors": sum(row["counts"]["errors"] for row in generated.values()),
            "total_right_sources": sum(
                row["counts"]["right_sources"] for row in generated.values()
            ),
            "total_rival_disagreements": sum(
                row["counts"]["rival_disagreements"] for row in generated.values()
            ),
        },
        "windows": {
            "seeds": window_seeds,
            "starts_per_seed": window_starts,
            "bands": windows,
            "total_checked": sum(row["checked"] for row in windows.values()),
            "total_generation_errors": sum(
                row["generation_errors"] for row in windows.values()
            ),
            "total_missing_side_witness": sum(
                row["missing_side_witness"] for row in windows.values()
            ),
            "total_rival_survivors": sum(
                row["rival_survived_all_demos"] for row in windows.values()
            ),
            "total_lesson_failures": sum(
                row["lesson_failures"] for row in windows.values()
            ),
        },
        "first_generated_witness": first_witness,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    default_generator = Path(__file__).resolve().parents[1] / "generator.py"
    parser.add_argument("--generator", type=Path, default=default_generator)
    parser.add_argument("--canonical-root", type=Path)
    parser.add_argument("--samples-per-band", type=int, default=400)
    parser.add_argument("--window-seeds", type=int, default=50)
    parser.add_argument("--window-starts", type=int, default=8)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    generator_path = args.generator.resolve()
    canonical_root = (
        args.canonical_root.resolve()
        if args.canonical_root is not None
        else find_root(__file__)
    )
    result = run_probe(
        generator_path,
        canonical_root=canonical_root,
        samples_per_band=args.samples_per_band,
        window_seeds=args.window_seeds,
        window_starts=args.window_starts,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "out": str(args.out),
        "generator_sha256": result["generator_sha256"],
        "canonical": result["canonical"],
        "sampling": {
            key: result["sampling"][key]
            for key in (
                "total_generated",
                "total_errors",
                "total_right_sources",
                "total_rival_disagreements",
            )
        },
        "windows": {
            key: result["windows"][key]
            for key in (
                "total_checked",
                "total_generation_errors",
                "total_missing_side_witness",
                "total_rival_survivors",
                "total_lesson_failures",
            )
        },
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
