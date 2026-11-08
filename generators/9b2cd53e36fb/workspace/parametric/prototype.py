"""Deterministic sampler and Python oracle for the edge-hole selector family.

The canonical setting transforms every edge-touching zero component.  The
alternate setting first finds the unique largest edge-touching component,
derives its row/column mirror axis, and transforms every edge hole sharing
that axis.  Sampling is independent of the chosen setting.
"""
from __future__ import annotations

from collections import deque
import hashlib
from pathlib import Path
import random
from typing import Any, Iterable

_TASK_ID = "9b2cd53e36fb"
_HOME = Path(__file__).resolve().parent
_PROGRAMS = {
    "all_holes": (_HOME / "rules" / "all_holes.rkt").read_text(),
    "largest_axis": (_HOME / "rules" / "largest_axis.rkt").read_text(),
}
_SELECTIONS = frozenset(_PROGRAMS)
_RIVAL_PROGRAMS = {
    "fixed_rows": (_HOME / "rules" / "rivals" / "fixed_rows.rkt").read_text(),
    "fixed_cols": (_HOME / "rules" / "rivals" / "fixed_cols.rkt").read_text(),
    "only_largest": (_HOME / "rules" / "rivals" / "only_largest.rkt").read_text(),
}
_VARIANT_PROGRAMS = {**_PROGRAMS, **_RIVAL_PROGRAMS}

# Profiles are (height, width, expected control axis, edge specifications,
# optional floating rectangle).  Each edge specification is
# (edge, span-along-edge, perpendicular-depth).  The first edge rectangle has
# the unique largest area and therefore determines the alternate rule's axis.
_DEMO_PROFILES = (
    (10, 12, "rows", (("top", 4, 3), ("bottom", 3, 2), ("left", 3, 2), ("right", 2, 2)), None),
    (12, 10, "cols", (("left", 4, 3), ("right", 3, 2), ("top", 3, 2), ("bottom", 2, 2)), None),
    (14, 14, "rows", (("bottom", 5, 3), ("top", 3, 2), ("left", 4, 2), ("right", 2, 2)), (1, 2)),
    (16, 12, "cols", (("right", 5, 3), ("left", 3, 2), ("top", 4, 2), ("bottom", 2, 2)), None),
    (12, 16, "rows", (("top", 5, 3), ("bottom", 4, 2), ("left", 3, 2), ("right", 2, 2)), (2, 1)),
    (18, 18, "cols", (("left", 6, 3), ("right", 4, 2), ("top", 5, 2), ("bottom", 3, 2)), None),
)
_QUERY_PROFILES = (
    (18, 14, "rows", (("top", 5, 4), ("bottom", 4, 2), ("left", 4, 3), ("right", 3, 2)), None),
    (14, 18, "cols", (("left", 5, 4), ("right", 4, 2), ("top", 4, 3), ("bottom", 3, 2)), None),
    (24, 30, "rows", (("bottom", 7, 4), ("top", 5, 3), ("bottom", 3, 2), ("left", 5, 3), ("right", 4, 2)), (2, 2)),
    (30, 30, "cols", (("left", 8, 4), ("right", 6, 3), ("left", 4, 2), ("top", 6, 3), ("bottom", 5, 2)), (2, 2)),
)


def _integer(value: Any, name: str, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an integer in {low}..{high}; bool is forbidden")
    return value


def _selection(value: Any) -> str:
    if type(value) is not str or value not in _SELECTIONS:
        raise ValueError("selection must be all_holes or largest_axis")
    return value


def program_for(selection: Any) -> str:
    """Return the exact Racket source for a declared setting."""
    return _PROGRAMS[_selection(selection)]


def variant_names() -> tuple[str, ...]:
    """Return declared settings followed by the bounded adversarial rivals."""
    return tuple(_VARIANT_PROGRAMS)


def _variant(value: Any) -> str:
    if type(value) is not str or value not in _VARIANT_PROGRAMS:
        raise ValueError("variant must name a declared setting or retained finite rival")
    return value


def variant_program(variant: Any) -> str:
    """Return exact Racket text for a setting or finite self-audit rival."""
    return _VARIANT_PROGRAMS[_variant(variant)]


def _validate_grid(grid: Any) -> tuple[int, int]:
    if type(grid) is not list or not grid or any(type(row) is not list for row in grid):
        raise ValueError("grid must be a non-empty list of row lists")
    width = len(grid[0])
    if width == 0 or any(len(row) != width for row in grid):
        raise ValueError("grid must be non-empty and rectangular")
    height = len(grid)
    if not (1 <= height <= 30 and 1 <= width <= 30):
        raise ValueError("grid dimensions must each be in 1..30")
    if any(type(cell) is not int or cell not in {0, 5, 7} for row in grid for cell in row):
        raise ValueError("grid cells must be exact integers from {0,5,7}")
    return height, width


def _zero_components(grid: list[list[int]]) -> list[list[tuple[int, int]]]:
    height, width = _validate_grid(grid)
    unseen = {(r, c) for r in range(height) for c in range(width) if grid[r][c] == 0}
    components: list[list[tuple[int, int]]] = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        queue = deque([start])
        cells: list[tuple[int, int]] = []
        while queue:
            r, c = queue.popleft()
            cells.append((r, c))
            for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if (nr, nc) in unseen:
                    unseen.remove((nr, nc))
                    queue.append((nr, nc))
        components.append(sorted(cells))
    return components


def _hole_fact(cells: list[tuple[int, int]], height: int, width: int) -> dict[str, Any]:
    rows = sorted({r for r, _ in cells})
    cols = sorted({c for _, c in cells})
    r1, r2, c1, c2 = min(rows), max(rows), min(cols), max(cols)
    top, bottom = r1 == 0, r2 == height - 1
    left, right = c1 == 0, c2 == width - 1
    axis = "rows" if top or bottom else "cols" if left or right else "none"
    edges = [name for name, hit in (("top", top), ("bottom", bottom), ("left", left), ("right", right)) if hit]
    return {
        "cells": cells,
        "rows": rows,
        "cols": cols,
        "bbox": [r1, c1, r2, c2],
        "area": len(cells),
        "axis": axis,
        "edges": edges,
        "rectangular": len(cells) == (r2 - r1 + 1) * (c2 - c1 + 1),
    }


def analyze_input(grid: list[list[int]]) -> dict[str, Any]:
    """Return structural facts plus explicit grammar errors for one input."""
    height, width = _validate_grid(grid)
    holes = [_hole_fact(cells, height, width) for cells in _zero_components(grid)]
    edge_holes = [hole for hole in holes if hole["axis"] != "none"]
    floating_holes = [hole for hole in holes if hole["axis"] == "none"]
    errors: list[str] = []
    palette = {cell for row in grid for cell in row}
    if not {5, 7} <= palette:
        errors.append("background must visibly contain both 5 and 7")
    if not edge_holes:
        errors.append("at least one edge hole is required")
    if any(not hole["rectangular"] for hole in holes):
        errors.append("every zero component must be a solid rectangle")
    if {hole["axis"] for hole in edge_holes} != {"rows", "cols"}:
        errors.append("edge holes must exercise both mirror axes")
    control: dict[str, Any] | None = None
    if edge_holes:
        largest = max(hole["area"] for hole in edge_holes)
        controls = [hole for hole in edge_holes if hole["area"] == largest]
        if len(controls) != 1:
            errors.append("the largest edge hole must be unique")
        else:
            control = controls[0]
            if sum(hole["axis"] == control["axis"] for hole in edge_holes) < 2:
                errors.append("the selected axis needs a secondary edge hole")
    if len(floating_holes) > 1:
        errors.append("at most one floating distractor is allowed")
    return {
        "height": height,
        "width": width,
        "holes": holes,
        "edge_holes": edge_holes,
        "floating_holes": floating_holes,
        "control": control,
        "errors": errors,
    }


def _selected_holes(facts: dict[str, Any], selection: str) -> list[dict[str, Any]]:
    if selection == "all_holes":
        return list(facts["edge_holes"])
    control = facts["control"]
    if control is None:
        raise ValueError("largest_axis needs a unique largest edge hole")
    return [hole for hole in facts["edge_holes"] if hole["axis"] == control["axis"]]


def _render_holes(
    grid: list[list[int]],
    facts: dict[str, Any],
    holes: Iterable[dict[str, Any]],
) -> list[list[int]]:
    height, width = facts["height"], facts["width"]
    mirrored: set[tuple[int, int]] = set()
    swept: set[tuple[int, int]] = set()
    for hole in holes:
        if hole["axis"] == "rows":
            mirrored.update((height - 1 - r, c) for r, c in hole["cells"])
            swept.update((r, c) for r in range(height) for c in hole["cols"])
        else:
            mirrored.update((r, width - 1 - c) for r, c in hole["cells"])
            swept.update((r, c) for r in hole["rows"] for c in range(width))
    return [
        [0 if (r, c) in mirrored else 7 if (r, c) in swept else grid[r][c] for c in range(width)]
        for r in range(height)
    ]


def apply_rule(grid: list[list[int]], selection: Any) -> list[list[int]]:
    """Apply one declared family rule in Python for diagnostics."""
    selection = _selection(selection)
    facts = analyze_input(grid)
    if facts["errors"]:
        raise ValueError("invalid family input: " + "; ".join(facts["errors"]))
    return _render_holes(grid, facts, _selected_holes(facts, selection))


def apply_variant(grid: list[list[int]], variant: Any) -> list[list[int]]:
    """Apply a declared rule or finite plausible shortcut in Python."""
    variant = _variant(variant)
    if variant in _SELECTIONS:
        return apply_rule(grid, variant)
    facts = analyze_input(grid)
    if facts["errors"] or facts["control"] is None:
        raise ValueError("rival audit requires a valid family input")
    if variant == "fixed_rows":
        holes = [hole for hole in facts["edge_holes"] if hole["axis"] == "rows"]
    elif variant == "fixed_cols":
        holes = [hole for hole in facts["edge_holes"] if hole["axis"] == "cols"]
    else:
        holes = [facts["control"]]
    return _render_holes(grid, facts, holes)


def sequential_trace(grid: list[list[int]]) -> dict[str, Any]:
    """Expose the real input-dependent intermediate used by largest_axis."""
    facts = analyze_input(grid)
    if facts["errors"] or facts["control"] is None:
        raise ValueError("trace requires a valid family input")
    control = facts["control"]
    return {
        "step_a": "find the unique largest edge-touching zero component and derive its mirror axis",
        "intermediate_value": {
            "axis": control["axis"],
            "area": control["area"],
            "bbox": list(control["bbox"]),
            "edges": list(control["edges"]),
        },
        "step_b": "mirror and sweep every edge hole whose mirror axis matches that derived axis",
        "output": apply_rule(grid, "largest_axis"),
    }


def _rng(seed: int, split: str, profile_index: int, attempt: int) -> random.Random:
    payload = f"{_TASK_ID}-largest-axis-v1:{seed}:{split}:{profile_index}:{attempt}".encode()
    return random.Random(int.from_bytes(hashlib.sha256(payload).digest(), "big"))


def _edge_candidates(
    height: int,
    width: int,
    edge: str,
    span: int,
    depth: int,
) -> list[set[tuple[int, int]]]:
    if edge in {"top", "bottom"}:
        if depth >= height or span > width - 2:
            return []
        row0 = 0 if edge == "top" else height - depth
        return [
            {(r, c) for r in range(row0, row0 + depth) for c in range(start, start + span)}
            for start in range(1, width - span)
        ]
    if edge in {"left", "right"}:
        if depth >= width or span > height - 2:
            return []
        col0 = 0 if edge == "left" else width - depth
        return [
            {(r, c) for r in range(start, start + span) for c in range(col0, col0 + depth)}
            for start in range(1, height - span)
        ]
    raise ValueError(f"unknown edge: {edge}")


def _clear_of_occupied(cells: set[tuple[int, int]], occupied: set[tuple[int, int]]) -> bool:
    return all(
        (r + dr, c + dc) not in occupied
        for r, c in cells
        for dr in (-1, 0, 1)
        for dc in (-1, 0, 1)
    )


def _place_edges(
    height: int,
    width: int,
    specs: tuple[tuple[str, int, int], ...],
    rng: random.Random,
) -> list[set[tuple[int, int]]] | None:
    candidates = [_edge_candidates(height, width, *spec) for spec in specs]
    for pool in candidates:
        rng.shuffle(pool)

    placed: list[set[tuple[int, int]]] = []
    occupied: set[tuple[int, int]] = set()

    def visit(index: int) -> bool:
        if index == len(candidates):
            return True
        for cells in candidates[index]:
            if not _clear_of_occupied(cells, occupied):
                continue
            placed.append(cells)
            occupied.update(cells)
            if visit(index + 1):
                return True
            placed.pop()
            occupied.difference_update(cells)
        return False

    return placed.copy() if visit(0) else None


def _floating_candidates(
    height: int,
    width: int,
    shape: tuple[int, int],
) -> list[set[tuple[int, int]]]:
    hole_h, hole_w = shape
    return [
        {(r, c) for r in range(top, top + hole_h) for c in range(left, left + hole_w)}
        for top in range(2, height - hole_h - 1)
        for left in range(2, width - hole_w - 1)
    ]


def _paint_texture(height: int, width: int, holes: Iterable[set[tuple[int, int]]], rng: random.Random) -> list[list[int]]:
    grid = [[5 if rng.getrandbits(1) == 0 else 7 for _ in range(width)] for _ in range(height)]
    occupied = set().union(*holes)
    for r, c in occupied:
        grid[r][c] = 0
    nonzero = [(r, c) for r in range(height) for c in range(width) if grid[r][c] != 0]
    if len(nonzero) < 2:
        raise RuntimeError("profile leaves too little visible background")
    grid[nonzero[0][0]][nonzero[0][1]] = 5
    grid[nonzero[1][0]][nonzero[1][1]] = 7
    return grid


def _profile_for(seed: int, split: str, index: int):
    if split == "demo":
        _integer(index, "index", 0, len(_DEMO_PROFILES) - 1)
        return _DEMO_PROFILES[(seed + index) % len(_DEMO_PROFILES)]
    if split == "query":
        _integer(index, "index", 0, len(_QUERY_PROFILES) - 1)
        return _QUERY_PROFILES[index]
    raise ValueError("split must be demo or query")


def sample_input(seed: int, split: str, index: int) -> list[list[int]]:
    """Create one deterministic input without consulting the chosen setting."""
    _integer(seed, "seed", 0, 2**63 - 1)
    profile = _profile_for(seed, split, index)
    height, width, control_axis, specs, floating_shape = profile
    for attempt in range(128):
        rng = _rng(seed, split, index, attempt)
        edge_holes = _place_edges(height, width, specs, rng)
        if edge_holes is None:
            continue
        holes = list(edge_holes)
        if floating_shape is not None:
            candidates = _floating_candidates(height, width, floating_shape)
            rng.shuffle(candidates)
            floating = next(
                (cells for cells in candidates if _clear_of_occupied(cells, set().union(*holes))),
                None,
            )
            if floating is None:
                continue
            holes.append(floating)
        grid = _paint_texture(height, width, holes, rng)
        facts = analyze_input(grid)
        if facts["errors"]:
            continue
        if facts["control"]["axis"] != control_axis:
            continue
        if apply_rule(grid, "all_holes") == apply_rule(grid, "largest_axis"):
            continue
        return grid
    raise RuntimeError(f"could not realize {split} profile {index} for seed {seed}")


def generate_episode(seed: Any, selection: Any, demos: Any = 3, queries: Any = 4) -> dict[str, Any]:
    """Return deterministic private labels for a native qualification episode."""
    seed = _integer(seed, "seed", 0, 2**63 - 1)
    selection = _selection(selection)
    demos = _integer(demos, "demos", 2, 6)
    queries = _integer(queries, "queries", 4, 4)
    demonstration_inputs = [sample_input(seed, "demo", index) for index in range(demos)]
    query_inputs = [sample_input(seed, "query", index) for index in range(queries)]
    all_inputs = demonstration_inputs + query_inputs
    pairs = [{"input": grid, "output": apply_rule(grid, selection)} for grid in all_inputs]
    return {
        "train": pairs[:demos],
        "test": pairs[demos:],
        "program_solution": program_for(selection),
    }
