#!/usr/bin/env python3
"""Deterministic adversarial-distribution census for this review packet.

This is retained as executable evidence: it samples both assigned audit targets,
measures whether their generated curricula exercise the branch used by the
proposed shortcut, and asks the exact canonical Racket programs for the
counterexample outputs.
"""
from __future__ import annotations

from collections import Counter, deque
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
REPO = ROOT / "repo"
sys.path.insert(0, str(REPO / "shared" / "runtime"))
sys.path.insert(0, str(REPO / "shared" / "tools"))

from arc_repl.racket_bridge import RacketBridge

# rule_wrap imports the repository tool as ``scripts.comment_solutions`` in the
# installed/runtime layout.  The review packet keeps it under shared/tools, so
# register the same module name explicitly for this standalone evidence script.
import types
_scripts = types.ModuleType("scripts")
_scripts.__path__ = []
sys.modules.setdefault("scripts", _scripts)
_comment_spec = importlib.util.spec_from_file_location(
    "scripts.comment_solutions", REPO / "shared" / "tools" / "comment_solutions.py"
)
if _comment_spec is None or _comment_spec.loader is None:
    raise RuntimeError("cannot load scripts.comment_solutions")
_comment_module = importlib.util.module_from_spec(_comment_spec)
sys.modules["scripts.comment_solutions"] = _comment_module
_comment_spec.loader.exec_module(_comment_module)

from puzzle_generators.rule_wrap import wrap_rule

TARGETS = ("36bf1fb8975c", "0d655a5e1a2d")
BANDS = ("easy", "medium", "hard")
DRAWS_PER_BAND = 200


def load_generator(task_id: str):
    path = REPO / "generators" / task_id / "generator.py"
    spec = importlib.util.spec_from_file_location(f"audit_{task_id}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_rows() -> dict[str, dict[str, Any]]:
    found: dict[str, dict[str, Any]] = {}
    path = REPO / "shared" / "data" / "canonical" / "puzzles.jsonl"
    for line in path.read_text().splitlines():
        row = json.loads(line)
        task_id = row.get("task_id")
        if task_id in TARGETS:
            found[task_id] = row
    if set(found) != set(TARGETS):
        raise RuntimeError(f"missing canonical rows: {set(TARGETS) - set(found)}")
    return found


def grid_literal(grid: list[list[int]]) -> str:
    return "'(" + " ".join(
        "(" + " ".join(map(str, row)) + ")" for row in grid
    ) + ")"


def apply_exact(bridge: RacketBridge, source: str, grid: list[list[int]]):
    return bridge.eval_text(f"({wrap_rule(source)} {grid_literal(grid)})")


def components(grid: list[list[int]]) -> list[set[tuple[int, int]]]:
    h, w = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0}
    result: list[set[tuple[int, int]]] = []
    while unseen:
        start = unseen.pop()
        value = grid[start[0]][start[1]]
        comp = {start}
        todo = deque([start])
        while todo:
            r, c = todo.popleft()
            for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if (nr, nc) in unseen and grid[nr][nc] == value:
                    unseen.remove((nr, nc))
                    comp.add((nr, nc))
                    todo.append((nr, nc))
        result.append(comp)
    return result


def l_windows(grid: list[list[int]]) -> list[dict[str, Any]]:
    hits = []
    for r in range(len(grid) - 1):
        for c in range(len(grid[0]) - 1):
            cells = ((r, c), (r, c + 1), (r + 1, c), (r + 1, c + 1))
            values = [grid[rr][cc] for rr, cc in cells]
            nonzero = [v for v in values if v != 0]
            if len(nonzero) == 3 and len(set(nonzero)) == 1:
                hits.append({"top_left": [r, c], "color": nonzero[0]})
    return hits


def audit_header_generator(module) -> dict[str, Any]:
    body_under_zero_header = 0
    unused_active_headers = 0
    body_cells = 0
    draws = 0
    per_band: dict[str, dict[str, int]] = {}
    for band_index, band in enumerate(BANDS):
        band_counts = Counter()
        for seed in range(DRAWS_PER_BAND):
            index = band_index * DRAWS_PER_BAND + seed
            grid = module.generate(80_000 + seed, index, difficulty=band)
            draws += 1
            active = {c for c, v in enumerate(grid[0]) if v != 0}
            used = {c for row in grid[1:] for c, v in enumerate(row) if v != 0}
            bad = used - active
            body_under_zero_header += sum(
                1 for row in grid[1:] for c, v in enumerate(row)
                if v != 0 and grid[0][c] == 0
            )
            unused_active_headers += len(active - used)
            body_cells += sum(v != 0 for row in grid[1:] for v in row)
            band_counts["draws"] += 1
            band_counts["body_under_zero_header"] += len(bad)
            band_counts["unused_active_headers"] += len(active - used)
        per_band[band] = dict(band_counts)
    return {
        "draws": draws,
        "body_cells": body_cells,
        "body_cells_under_zero_header": body_under_zero_header,
        "unused_active_headers": unused_active_headers,
        "per_band": per_band,
    }


def audit_l_generator(module) -> dict[str, Any]:
    component_sizes = Counter()
    qualifying_windows = 0
    embedded_in_larger_component = 0
    draws_with_fewer_than_two_l = 0
    draws = 0
    per_band: dict[str, dict[str, Any]] = {}
    for band_index, band in enumerate(BANDS):
        band_counts = Counter()
        for seed in range(DRAWS_PER_BAND):
            index = band_index * DRAWS_PER_BAND + seed
            grid = module.generate(90_000 + seed, index, difficulty=band)
            draws += 1
            comps = components(grid)
            lookup = {cell: len(comp) for comp in comps for cell in comp}
            for comp in comps:
                component_sizes[len(comp)] += 1
            hits = l_windows(grid)
            qualifying_windows += len(hits)
            if len(hits) < 2:
                draws_with_fewer_than_two_l += 1
            for hit in hits:
                r, c = hit["top_left"]
                occupied = [
                    (rr, cc)
                    for rr, cc in ((r, c), (r, c + 1), (r + 1, c), (r + 1, c + 1))
                    if grid[rr][cc] != 0
                ]
                if occupied and lookup[occupied[0]] > 3:
                    embedded_in_larger_component += 1
            band_counts["draws"] += 1
            band_counts["qualifying_windows"] += len(hits)
            band_counts["draws_with_fewer_than_two_l"] += int(len(hits) < 2)
        per_band[band] = dict(band_counts)
    return {
        "draws": draws,
        "qualifying_l_windows": qualifying_windows,
        "component_sizes": {str(k): v for k, v in sorted(component_sizes.items())},
        "qualifying_l_windows_embedded_in_component_larger_than_3": embedded_in_larger_component,
        "draws_with_fewer_than_two_l_windows": draws_with_fewer_than_two_l,
        "per_band": per_band,
    }


def main() -> int:
    rows = canonical_rows()
    modules = {task: load_generator(task) for task in TARGETS}
    header_input = [[2, 0, 4], [0, 1, 1], [0, 0, 0]]
    header_shortcut = [[2, 0, 4], [0, 1, 4], [0, 0, 0]]
    l_input = [[2, 2, 0], [2, 0, 0], [2, 0, 0]]
    l_shortcut = [row[:] for row in l_input]

    bridge = RacketBridge()
    try:
        header_output = apply_exact(
            bridge, rows["36bf1fb8975c"]["program_solution"], header_input
        )
        l_output = apply_exact(
            bridge, rows["0d655a5e1a2d"]["program_solution"], l_input
        )
    finally:
        bridge.close()

    report = {
        "schema": "arcpuzzles-adversarial-census-v1",
        "sampling": {
            "bands": list(BANDS),
            "draws_per_band": DRAWS_PER_BAND,
            "seed_formulas": {
                "36bf1fb8975c": "seed=80000+i, sample_index=band_index*200+i",
                "0d655a5e1a2d": "seed=90000+i, sample_index=band_index*200+i",
            },
        },
        "36bf1fb8975c": {
            "census": audit_header_generator(modules["36bf1fb8975c"]),
            "rival": (
                "For nonzero body cells, use the header color only when the header "
                "is nonzero; otherwise preserve the body cell."
            ),
            "counterexample": {
                "input": header_input,
                "authority_output": header_output,
                "rival_output": header_shortcut,
                "checked_with": "exact canonical Racket program_solution via RacketBridge",
            },
        },
        "0d655a5e1a2d": {
            "census": audit_l_generator(modules["0d655a5e1a2d"]),
            "rival": (
                "Complete a missing corner only when the entire connected colored "
                "component is exactly a three-cell L."
            ),
            "counterexample": {
                "input": l_input,
                "authority_output": l_output,
                "rival_output": l_shortcut,
                "checked_with": "exact canonical Racket program_solution via RacketBridge",
            },
        },
    }

    assert report["36bf1fb8975c"]["census"]["body_cells_under_zero_header"] == 0
    assert report["36bf1fb8975c"]["census"]["unused_active_headers"] == 0
    assert report["36bf1fb8975c"]["counterexample"]["authority_output"] != header_shortcut
    assert report["0d655a5e1a2d"]["census"][
        "qualifying_l_windows_embedded_in_component_larger_than_3"
    ] == 0
    assert report["0d655a5e1a2d"]["counterexample"]["authority_output"] != l_shortcut

    output = Path(__file__).with_name("adversarial_census.json")
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
