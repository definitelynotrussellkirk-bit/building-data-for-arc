#!/usr/bin/env python3
"""Audit exact-vector support and sliding-window shortcut survival.

This task-local tool is intentionally independent of the repository's generic
morphology gates.  It asks the rule-level question that exposed the defect in
v3.0.0: can a solver ignore the exact red-to-green distance, snap every vector
to signed/oriented 2x3 magnitudes, and still fit the generated curriculum?

Run from anywhere inside the review packet, for example:

    python3 generators/a4f0ea66fd65/workspace/vector_shortcut_audit.py \
        --seeds 20 --out checks/a4f0ea66fd65_vector_shortcut_audit.json

Use ``--generator`` to compare another revision of the task generator.
"""
from __future__ import annotations

import argparse
import copy
import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Callable

TOOL = Path(__file__).resolve()
TASK_DIR = TOOL.parents[1]
REPO = TOOL.parents[3]
RUNTIME = REPO / "shared/runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))

BANDS = ("easy", "medium", "hard")
WINDOW = 4


def _load_generator(path: Path):
    path = path.resolve()
    spec = importlib.util.spec_from_file_location(
        f"vector_shortcut_audit_{abs(hash(str(path)))}", path
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import generator from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sign(value: int) -> int:
    return -1 if value < 0 else (1 if value > 0 else 0)


def marker_vector(grid: list[list[int]]) -> tuple[int, int]:
    red = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 2]
    green = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 3]
    if len(red) != 1 or len(green) != 1:
        raise ValueError(f"expected one red and one green marker, got {len(red)}/{len(green)}")
    return green[0][0] - red[0][0], green[0][1] - red[0][1]


def quantized_2x3_vector(vector: tuple[int, int]) -> tuple[int, int]:
    """Snap direction/orientation to the canonical 2x3 displacement family."""
    dr, dc = vector
    sr, sc = _sign(dr), _sign(dc)
    if dr == 0:
        return 0, 3 * sc
    if dc == 0:
        return 3 * sr, 0
    if abs(dr) <= abs(dc):
        return 2 * sr, 3 * sc
    return 3 * sr, 2 * sc


def copy_by_vector(grid: list[list[int]], vector: tuple[int, int]) -> list[list[int]]:
    out = copy.deepcopy(grid)
    h, w = len(grid), len(grid[0])
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 8:
                continue
            nr, nc = r + vector[0], c + vector[1]
            if 0 <= nr < h and 0 <= nc < w:
                out[nr][nc] = 1
    return out


def quantized_2x3_solver(grid: list[list[int]]) -> list[list[int]]:
    return copy_by_vector(grid, quantized_2x3_vector(marker_vector(grid)))


def _grid_key(grid: Any) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(int(value) for value in row) for row in grid)


def _declared_rivals(module: Any) -> dict[str, Callable[[Any], Any]]:
    raw = getattr(module, "LESSON_COMPETITORS", None)
    if not isinstance(raw, dict):
        raw = getattr(module, "SEMANTIC_RIVALS", None)
    if not isinstance(raw, dict):
        return {}
    return {str(name): fn for name, fn in raw.items() if callable(fn)}


def audit(generator_path: Path, seeds: int) -> dict[str, Any]:
    if seeds < 1:
        raise ValueError("--seeds must be positive")
    module = _load_generator(generator_path)
    profiles = tuple(getattr(module, "SCENE_PROFILES", ()))
    cycle = len(profiles) or 6
    rivals = _declared_rivals(module)

    vectors: dict[str, Counter[tuple[int, int]]] = {band: Counter() for band in BANDS}
    profile_counts: dict[str, Counter[str]] = {band: Counter() for band in BANDS}
    declared_matches = Counter()
    quantized_matches = 0
    total_scenes = 0
    axis_aligned = 0
    exact_distance_counterexamples = 0
    generation_failures: list[dict[str, Any]] = []

    for band in BANDS:
        for seed_offset in range(seeds):
            seed = 700_000 + seed_offset
            for sample_index in range(cycle * 2):
                try:
                    grid = module.generate(seed, sample_index, difficulty=band)
                    official = module.rule_mirror(grid)
                    vector = marker_vector(grid)
                except Exception as exc:  # counted and serialized, never hidden
                    generation_failures.append({
                        "band": band,
                        "seed": seed,
                        "sample_index": sample_index,
                        "error": f"{type(exc).__name__}: {exc}",
                    })
                    continue
                total_scenes += 1
                vectors[band][vector] += 1
                if vector[0] == 0 or vector[1] == 0:
                    axis_aligned += 1
                facts = module.semantic_observables(grid)
                profile_counts[band][str(facts.get("scene_profile"))] += 1
                if _grid_key(quantized_2x3_solver(grid)) == _grid_key(official):
                    quantized_matches += 1
                else:
                    exact_distance_counterexamples += 1
                for name, rival in rivals.items():
                    if _grid_key(rival(copy.deepcopy(grid))) == _grid_key(official):
                        declared_matches[name] += 1

    quantized_survivor_windows: list[dict[str, Any]] = []
    declared_survivor_counts = Counter()
    declared_survivor_examples: list[dict[str, Any]] = []
    windows = 0
    for band in BANDS:
        for seed_offset in range(seeds):
            seed = 800_000 + seed_offset
            for start in range(cycle):
                try:
                    demos = [
                        module.generate(seed, start + offset, difficulty=band)
                        for offset in range(WINDOW)
                    ]
                    official = [module.rule_mirror(grid) for grid in demos]
                except Exception as exc:
                    generation_failures.append({
                        "band": band,
                        "seed": seed,
                        "sample_index": start,
                        "window": True,
                        "error": f"{type(exc).__name__}: {exc}",
                    })
                    continue
                windows += 1
                if all(
                    _grid_key(quantized_2x3_solver(grid)) == _grid_key(expected)
                    for grid, expected in zip(demos, official)
                ):
                    quantized_survivor_windows.append({
                        "band": band,
                        "seed": seed,
                        "start": start,
                        "vectors": [list(marker_vector(grid)) for grid in demos],
                    })
                for name, rival in rivals.items():
                    if all(
                        _grid_key(rival(copy.deepcopy(grid))) == _grid_key(expected)
                        for grid, expected in zip(demos, official)
                    ):
                        declared_survivor_counts[name] += 1
                        if len(declared_survivor_examples) < 20:
                            declared_survivor_examples.append({
                                "name": name,
                                "band": band,
                                "seed": seed,
                                "start": start,
                                "vectors": [list(marker_vector(grid)) for grid in demos],
                            })

    vector_json = {
        band: {f"{dr},{dc}": count for (dr, dc), count in sorted(counter.items())}
        for band, counter in vectors.items()
    }
    profiles_json = {
        band: dict(sorted(counter.items())) for band, counter in profile_counts.items()
    }
    status = "PASS"
    reasons: list[str] = []
    if generation_failures:
        status = "FAIL"
        reasons.append(f"{len(generation_failures)} generation failures")
    if exact_distance_counterexamples == 0:
        status = "FAIL"
        reasons.append("no generated scene refutes signed/oriented 2x3 quantization")
    if axis_aligned == 0:
        status = "FAIL"
        reasons.append("no axis-aligned marker vectors generated")
    if quantized_survivor_windows:
        status = "FAIL"
        reasons.append(
            f"quantized_2x3 survives {len(quantized_survivor_windows)}/{windows} four-demo windows"
        )
    if declared_survivor_counts:
        status = "FAIL"
        reasons.append(
            "declared rivals survive windows: "
            + ", ".join(f"{name}={count}" for name, count in sorted(declared_survivor_counts.items()))
        )

    return {
        "schema": "a4f0ea66fd65-vector-shortcut-audit-v1",
        "generator": str(generator_path.resolve()),
        "generator_version": getattr(module, "VERSION", None),
        "seeds": seeds,
        "bands": list(BANDS),
        "cycle_length": cycle,
        "four_demo_windows": windows,
        "total_scenes": total_scenes,
        "status": status,
        "reasons": reasons,
        "vector_histogram": vector_json,
        "profile_counts": profiles_json,
        "axis_aligned_scenes": axis_aligned,
        "exact_distance_counterexamples": exact_distance_counterexamples,
        "quantized_2x3": {
            "matches": quantized_matches,
            "disagrees": exact_distance_counterexamples,
            "match_rate": (quantized_matches / total_scenes if total_scenes else None),
            "surviving_windows": len(quantized_survivor_windows),
            "survivor_examples": quantized_survivor_windows[:20],
        },
        "declared_rivals": {
            "names": sorted(rivals),
            "single_scene_match_counts": dict(sorted(declared_matches.items())),
            "surviving_window_counts": dict(sorted(declared_survivor_counts.items())),
            "survivor_examples": declared_survivor_examples,
        },
        "generation_failures": generation_failures[:50],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--generator", type=Path, default=TASK_DIR / "generator.py",
        help="generator.py revision to audit (default: current task generator)",
    )
    parser.add_argument("--seeds", type=int, default=20)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)

    result = audit(args.generator, args.seeds)
    payload = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.out is not None:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(payload)
    print(
        f"{result['status']} scenes={result['total_scenes']} "
        f"windows={result['four_demo_windows']} "
        f"quantized_match={result['quantized_2x3']['matches']}/"
        f"{result['total_scenes']} "
        f"quantized_surviving_windows={result['quantized_2x3']['surviving_windows']} "
        f"axis_aligned={result['axis_aligned_scenes']}"
    )
    for reason in result["reasons"]:
        print(f"  {reason}")
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
