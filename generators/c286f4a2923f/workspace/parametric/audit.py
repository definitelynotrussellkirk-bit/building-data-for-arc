"""Bounded, repeatable self-audit for the c286f4a2923f parametric family.

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
    module_name = f"_c286_audit_{name}_{hashlib.sha256(path.read_bytes()).hexdigest()}"
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


def _source_geometry(grid: Grid) -> tuple[list[tuple[int, int]], tuple[int, int, int, int], tuple[int, int, int, int]]:
    source = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 2]
    target = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 3]
    if not source or not target:
        raise AssertionError("lawful scene lost a source or target")
    sr = [r for r, _ in source]
    sc = [c for _, c in source]
    tr = [r for r, _ in target]
    tc = [c for _, c in target]
    source_bbox = min(sr), min(sc), max(sr), max(sc)
    target_bbox = min(tr), min(tc), max(tr), max(tc)
    offsets = [(r - source_bbox[0], c - source_bbox[1]) for r, c in source]
    return offsets, source_bbox, target_bbox


def _place(grid: Grid, row: int, col: int, offsets: list[tuple[int, int]], *, mirror: bool = False) -> Grid:
    out = _blank_like(grid)
    width = max(c for _, c in offsets) + 1
    for dr, dc in offsets:
        cc = width - 1 - dc if mirror else dc
        out[row + dr][col + cc] = 8
    return out


def _center_alignment(grid: Grid) -> Grid:
    offsets, source, target = _source_geometry(grid)
    sh, sw = source[2] - source[0] + 1, source[3] - source[1] + 1
    th, tw = target[2] - target[0] + 1, target[3] - target[1] + 1
    return _place(grid, target[0] + (th - sh) // 2, target[1] + (tw - sw) // 2, offsets)


def _bottom_right_alignment(grid: Grid) -> Grid:
    offsets, source, target = _source_geometry(grid)
    sh, sw = source[2] - source[0] + 1, source[3] - source[1] + 1
    return _place(grid, target[2] - sh + 1, target[3] - sw + 1, offsets)


def _horizontal_mirror(grid: Grid) -> Grid:
    offsets, _, target = _source_geometry(grid)
    return _place(grid, target[0], target[1], offsets, mirror=True)


def _fill_first_hole(grid: Grid) -> Grid:
    out = O.transfer_only(grid)
    regions = O.enclosed_regions(out)
    if regions:
        for r, c in regions[0]:
            out[r][c] = 4
    return out


def _fill_entire_target(grid: Grid) -> Grid:
    out = O.transfer_only(grid)
    _, _, target = _source_geometry(grid)
    for r in range(target[0], target[2] + 1):
        for c in range(target[1], target[3] + 1):
            if out[r][c] == 0:
                out[r][c] = 4
    return out


RIVALS: dict[str, tuple[str, Callable[[Grid], Grid]]] = {
    "center_alignment": ("transfer_only", _center_alignment),
    "bottom_right_alignment": ("transfer_only", _bottom_right_alignment),
    "horizontal_mirror": ("transfer_only", _horizontal_mirror),
    "fill_first_hole_only": ("fill_transferred_holes", _fill_first_hole),
    "fill_entire_target": ("fill_transferred_holes", _fill_entire_target),
    "skip_transfer": ("fill_transferred_holes", _blank_like),
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
        small = P.generate(seed, {"finish": "transfer_only"}, 3, 1)
        base = P.generate(seed, {"finish": "transfer_only"}, 6, 4)
        alt = P.generate(seed, {"finish": "fill_transferred_holes"}, 6, 4)
        assert base == P.generate(seed, {"finish": "transfer_only"}, 6, 4)
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
            ("transfer_only", base),
            ("fill_transferred_holes", alt),
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
        info = P.describe(stress["input"], {"finish": "fill_transferred_holes"})
        assert info["shape"] == [30, 30]
        assert info["source_cells"] >= 35 and info["enclosed_regions"] >= 2
        checks["stress_cases"] += 1

        visible = {
            "transfer_only": base["train"][:3],
            "fill_transferred_holes": alt["train"][:3],
        }
        for name, (finish, rival) in RIVALS.items():
            for pair in visible[finish]:
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
