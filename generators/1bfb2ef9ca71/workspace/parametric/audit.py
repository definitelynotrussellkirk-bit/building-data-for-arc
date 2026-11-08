"""Bounded, repeatable self-audit for the 1bfb2ef9ca71 parametric family.

This checks the lawful generator domain and a finite set of plausible shortcuts.
It is authoring evidence, not owner qualification or a proof of uniqueness.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Callable

HERE = Path(__file__).resolve().parent
SEEDS = (0, 17, 97)


def _load(name: str):
    path = HERE / f"{name}.py"
    module_name = f"_1bfb_audit_{name}_{hashlib.sha256(path.read_bytes()).hexdigest()}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


P = _load("prototype")
O = _load("oracle")
Grid = list[list[int]]


def _blank_like(grid: Grid) -> Grid:
    return [[0 for _ in row] for row in grid]


def _fill_selected(grid: Grid, chooser: Callable[[dict[str, object]], tuple]) -> Grid:
    rects = O.rectangles(grid)
    selected = sorted(rects, key=chooser)[0]
    out = O.borders_only(grid)
    for r, c in selected["interior"]:
        out[r][c] = selected["color"]
    return out


def _longest_perimeter(grid: Grid) -> Grid:
    return _fill_selected(
        grid,
        lambda rect: (-int(rect["perimeter"]), rect["bbox"][0], rect["bbox"][1]),
    )


def _largest_bbox(grid: Grid) -> Grid:
    return _fill_selected(
        grid,
        lambda rect: (
            -int(rect["height"]) * int(rect["width"]),
            rect["bbox"][0],
            rect["bbox"][1],
        ),
    )


def _top_left_frame(grid: Grid) -> Grid:
    return _fill_selected(grid, lambda rect: (rect["bbox"][0], rect["bbox"][1]))


def _lowest_color(grid: Grid) -> Grid:
    return _fill_selected(grid, lambda rect: (int(rect["color"]),))


def _fill_all_interiors(grid: Grid) -> Grid:
    out = O.borders_only(grid)
    for rect in O.rectangles(grid):
        for r, c in rect["interior"]:
            out[r][c] = rect["color"]
    return out


RIVALS: dict[str, Callable[[Grid], Grid]] = {
    "longest_perimeter": _longest_perimeter,
    "largest_bbox": _largest_bbox,
    "top_left_frame": _top_left_frame,
    "lowest_color": _lowest_color,
    "fill_all_interiors": _fill_all_interiors,
    "skip_borders": _blank_like,
}


def _inputs(episode: dict[str, object]) -> list[Grid]:
    return [pair["input"] for pair in episode["train"] + episode["test"]]


def run() -> dict[str, object]:
    checks = {
        "deterministic_replays": 0,
        "matched_inputs": 0,
        "stable_prefixes": 0,
        "distinct_input_sets": 0,
        "oracle_labels": 0,
        "privacy_views": 0,
        "stress_cases": 0,
    }
    disagreements = {name: 0 for name in RIVALS}

    for seed in SEEDS:
        small = P.generate(seed, {"finish": "borders_only"}, 3, 1)
        base = P.generate(seed, {"finish": "borders_only"}, 6, 4)
        alt = P.generate(seed, {"finish": "fill_largest_interior"}, 6, 4)
        assert base == P.generate(seed, {"finish": "borders_only"}, 6, 4)
        checks["deterministic_replays"] += 1

        assert small["train"] == base["train"][:3]
        assert small["test"] == base["test"][:1]
        checks["stable_prefixes"] += 1

        base_inputs, alt_inputs = _inputs(base), _inputs(alt)
        assert base_inputs == alt_inputs
        checks["matched_inputs"] += len(base_inputs)
        assert len({json.dumps(grid, separators=(",", ":")) for grid in base_inputs}) == len(base_inputs)
        checks["distinct_input_sets"] += 1

        for finish, episode in (
            ("borders_only", base),
            ("fill_largest_interior", alt),
        ):
            for pair in episode["train"] + episode["test"]:
                assert pair["output"] == O.solve(pair["input"], finish)
                checks["oracle_labels"] += 1

        for query_index in range(4):
            view = P.public_turn(alt, query_index)
            assert set(view) == {"train", "test"}
            assert len(view["train"]) == 6
            assert len(view["test"]) == 1
            assert set(view["test"][0]) == {"input"}
            assert view["test"][0]["input"] == alt["test"][query_index]["input"]
            assert "program_solution" not in view and "settings" not in view
            checks["privacy_views"] += 1

        stress = alt["test"][3]
        info = P.describe(stress["input"], {"finish": "fill_largest_interior"})
        assert info["shape"] == [30, 30]
        assert info["rectangles"] == 4
        assert info["total_border_cells"] >= 100 and info["winner_interior_area"] >= 60
        checks["stress_cases"] += 1

        for name, rival in RIVALS.items():
            for pair in alt["train"][:3]:
                disagreements[name] += int(rival(pair["input"]) != pair["output"])

    if not all(count > 0 for count in disagreements.values()):
        raise AssertionError(f"unrefuted shortcut rivals: {disagreements}")

    return {
        "schema": "arcpuzzles-bounded-parametric-self-audit-v1",
        "task_id": P.TASK_ID,
        "status": "passed",
        "seeds": list(SEEDS),
        "settings": [dict(setting) for setting in P.SETTINGS],
        "count_matrix": {"demos": [3, 6], "queries": [1, 4]},
        "checks": checks,
        "rival_disagreements": disagreements,
        "limitations": (
            "Finite deterministic checks over the declared lawful sampler and named rivals; "
            "not universal rule identification, protected-Racket qualification, owner acceptance, "
            "or training admission."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    report = run()
    raw = json.dumps(report, sort_keys=True, indent=2) + "\n"
    if args.out is None:
        print(raw, end="")
    else:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(raw, encoding="utf-8")
        print(args.out)


if __name__ == "__main__":
    main()
