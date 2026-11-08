#!/usr/bin/env python3
"""Bounded semantic shortcut and crossed-control probe for vector direction."""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import random
import sys
from typing import Callable, Iterable

_HOME = Path(__file__).resolve().parent
_SPEC = importlib.util.spec_from_file_location("_vector_direction_probe_impl", _HOME / "prototype.py")
if _SPEC is None or _SPEC.loader is None:
    raise ImportError("cannot load task-local prototype")
p = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = p
_SPEC.loader.exec_module(p)

Grid = list[list[int]]
Rival = Callable[[Grid, str], Grid]


def _empty_like(grid: Grid) -> Grid:
    return [[0 for _ in row] for row in grid]


def _paint(grid: Grid, cells) -> Grid:
    output = _empty_like(grid)
    for r, c in cells:
        output[r][c] = 7
    return output


def _marker_vector(grid: Grid) -> tuple[int, int]:
    info = p.analyze_scene(grid)
    if info.get("errors"):
        raise ValueError(info["errors"])
    return tuple(info["vector"])


def _targets(grid: Grid):
    return [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 4]


def _sources(grid: Grid):
    return [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 3]


def _explicit(vector_fn: Callable[[tuple[int, int], str], tuple[int, int]]) -> Rival:
    def apply(grid: Grid, setting: str) -> Grid:
        return p.apply_with_vector(grid, vector_fn(_marker_vector(grid), setting))
    return apply


def _ranked_target(grid: Grid, setting: str, *, reverse: bool = False) -> Grid:
    info = p.analyze_scene(grid)
    anchor = info["marker_9"]
    targets = sorted(_targets(grid), key=lambda q: (abs(q[0] - anchor[0]) + abs(q[1] - anchor[1]), q))
    count = len(info["forward_targets"] if setting == "forward" else info["reverse_targets"])
    selected = targets[-count:] if reverse else targets[:count]
    return _paint(grid, selected)


def _rivals() -> dict[str, Rival]:
    return {
        "opposite_direction": _explicit(lambda v, s: (-v[0], -v[1]) if s == "forward" else v),
        "recolor_every_4": lambda g, s: _paint(g, _targets(g)),
        "paint_every_3": lambda g, s: _paint(g, _sources(g)),
        "first_target_only": lambda g, s: _paint(g, sorted(_targets(g))[:1]),
        "last_target_only": lambda g, s: _paint(g, sorted(_targets(g))[-1:]),
        "absolute_vector": _explicit(lambda v, s: (abs(v[0]), abs(v[1]))),
        "swapped_components": _explicit(lambda v, s: (v[1], v[0])),
        "row_component_only": _explicit(lambda v, s: (v[0], 0)),
        "column_component_only": _explicit(lambda v, s: (0, v[1])),
        "fixed_2_3": _explicit(lambda v, s: (2, 3)),
        "fixed_minus2_3": _explicit(lambda v, s: (-2, 3)),
        "nearest_targets_to_9": lambda g, s: _ranked_target(g, s),
        "farthest_targets_from_9": lambda g, s: _ranked_target(g, s, reverse=True),
        "zero_vector": _explicit(lambda v, s: (0, 0)),
    }


def _relocate_markers(grid: Grid, vector: tuple[int, int]) -> Grid:
    result = [row[:] for row in grid]
    for r, row in enumerate(result):
        for c, value in enumerate(row):
            if value in (8, 9):
                result[r][c] = 0
    height, width = len(result), len(result[0])
    for r in range(height):
        for c in range(width):
            rr, cc = r + vector[0], c + vector[1]
            if 0 <= rr < height and 0 <= cc < width and result[r][c] == result[rr][cc] == 0:
                result[r][c] = 8
                result[rr][cc] = 9
                return result
    raise ValueError("could not relocate markers for crossed control")


def _crossed_controls() -> dict:
    rng = random.Random(9981)
    base = p._GEN.construct_scene(
        height=16,
        width=18,
        vector=(2, 3),
        matched_pairs=5,
        reverse_pairs=4,
        source_decoys=2,
        target_decoys=2,
        rng=rng,
    )
    fixed_positions = _relocate_markers(base, (-2, 3))
    first = p.apply_rule(base, "forward")
    second = p.apply_rule(fixed_positions, "forward")

    same_vector_a = p._GEN.construct_scene(
        height=16,
        width=18,
        vector=(2, 3),
        matched_pairs=5,
        reverse_pairs=4,
        source_decoys=2,
        target_decoys=2,
        rng=random.Random(77),
    )
    same_vector_b = p._GEN.construct_scene(
        height=16,
        width=18,
        vector=(2, 3),
        matched_pairs=5,
        reverse_pairs=4,
        source_decoys=2,
        target_decoys=2,
        rng=random.Random(78),
    )
    info_a = p.analyze_scene(same_vector_a)
    info_b = p.analyze_scene(same_vector_b)
    passed = (
        base != fixed_positions
        and first != second
        and info_a["vector"] == info_b["vector"] == (2, 3)
        and same_vector_a != same_vector_b
        and len(info_a["forward_targets"]) == len(info_b["forward_targets"]) == 5
        and p.apply_rule(same_vector_a, "forward") != p.apply_rule(same_vector_b, "forward")
    )
    return {
        "passed": passed,
        "intermediate_varied_at_fixed_nonmarker_cells": first != second,
        "nuisance_positions_varied_at_fixed_intermediate": same_vector_a != same_vector_b,
        "fixed_vector": [2, 3],
    }


def run_probe(*, seeds: Iterable[int], demos: int = 2) -> dict:
    seeds = list(seeds)
    if type(demos) is not int or not 2 <= demos <= 6:
        raise ValueError("demos must be an exact integer in 2..6")
    rivals = _rivals()
    survivors = []
    finite_equivalents = []
    checks = 0
    episodes = 0
    first_failures: dict[str, dict] = {}
    for seed in seeds:
        for setting in p.SETTINGS:
            episode = p.generate(seed, {p.PARAMETER: setting}, demos, 4)
            episodes += 1
            for name, rival in rivals.items():
                checks += 1
                demo_predictions = [rival(pair["input"], setting) for pair in episode["train"]]
                demo_match = all(
                    prediction == pair["output"]
                    for prediction, pair in zip(demo_predictions, episode["train"])
                )
                query_predictions = [rival(pair["input"], setting) for pair in episode["test"]]
                query_match = all(
                    prediction == pair["output"]
                    for prediction, pair in zip(query_predictions, episode["test"])
                )
                if demo_match and not query_match:
                    survivors.append({"seed": seed, "setting": setting, "rival": name})
                elif demo_match and query_match:
                    finite_equivalents.append({"seed": seed, "setting": setting, "rival": name})
                elif name not in first_failures:
                    mismatch = next(
                        index
                        for index, (prediction, pair) in enumerate(zip(demo_predictions, episode["train"]))
                        if prediction != pair["output"]
                    )
                    first_failures[name] = {"seed": seed, "setting": setting, "demo_index": mismatch}
    crossed = _crossed_controls()
    return {
        "schema": "arcpuzzles-vector-direction-adversarial-probe-v1",
        "task_id": p.TASK_ID,
        "seeds": seeds,
        "smallest_lesson": demos,
        "episodes": episodes,
        "rivals": sorted(rivals),
        "shortcut_checks": checks,
        "surviving_shortcuts": survivors,
        "finite_equivalents": finite_equivalents,
        "first_refutations": first_failures,
        "crossed_controls": crossed,
        "limitations": (
            "Finite declared rivals and crossed controls only; this is not a proof of "
            "uniqueness against arbitrary programs."
        ),
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=int, default=32)
    parser.add_argument("--demos", type=int, default=2)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.seeds < 1:
        raise ValueError("--seeds must be positive")
    report = run_probe(seeds=range(args.seeds), demos=args.demos)
    if report["surviving_shortcuts"] or report["finite_equivalents"] or not report["crossed_controls"]["passed"]:
        raise SystemExit("adversarial probe found an unresolved shortcut or failed crossed control")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": "passed",
        "episodes": report["episodes"],
        "shortcut_checks": report["shortcut_checks"],
        "rivals": len(report["rivals"]),
        "out": str(args.out.resolve()),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
