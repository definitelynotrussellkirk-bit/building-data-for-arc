"""Generator for ``arc_additional_puzzle_bank_volume5:E33``.

The input contains one or more separated green orthogonal paths.  The output
recolors only each path's elbow: a green cell with exactly two green
4-neighbors, one horizontal and one vertical.  Straight degree-two cells are
left green, so ordinary draws directly refute the tempting "recolor every
middle cell" shortcut.
"""
from __future__ import annotations

from collections import deque
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "a0c86a1cb81e"
TASK_ID = "a0c86a1cb81e"
VERSION = "3.0.0"
RULE_HASH = "29ae8ca1668f"

SUMMARY = (
    "A 0-background grid contains separated color-3 simple orthogonal paths "
    "with varied lengths, orientations, and one- or multi-turn geometry. Recolor to 6 exactly the green "
    "cells having two green 4-neighbors split across the horizontal and "
    "vertical axes. Endpoints and straight degree-two cells remain 3."
)

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

INVARIANTS = [
    "the input palette is exactly a subset of {0, 3}",
    "every non-background 4-connected component is one simple orthogonal path",
    "each path has at least one turn and exactly two endpoints",
    "ordinary draws include straight degree-two green cells that remain green",
    "generated paths are separated by at least one background cell",
]

AXES = {
    "grid_h": {"type": "int", "default": "difficulty-aware rng 8..14", "valid": "8..14"},
    "grid_w": {"type": "int", "default": "difficulty-aware rng 8..14", "valid": "8..14"},
    "n_paths": {"type": "int", "default": "difficulty-aware rng 2..4", "valid": "1..4"},
}

_ORIENTATION_ORDER = (0, 3, 1, 2)


def _draw_axis_int(ctx, overrides, label: str, default_lo: int, default_hi: int,
                   full_lo: int, full_hi: int) -> int:
    """Use the full declared domain for overrides and a band range otherwise."""
    if label in overrides and overrides[label] is not None:
        return ctx.draw_int(label, full_lo, full_hi)
    return ctx.draw_int(label, default_lo, default_hi)


def _band_ranges(difficulty) -> tuple[tuple[int, int], tuple[int, int], tuple[int, int]]:
    if difficulty == "easy":
        return (8, 10), (8, 10), (2, 3)
    if difficulty == "hard":
        return (10, 14), (10, 14), (3, 4)
    return (9, 12), (9, 12), (2, 4)


def _slot_intervals(size: int) -> tuple[tuple[int, int], tuple[int, int]]:
    """Two edge regions separated by at least one unused row/column."""
    first_end = (size - 3) // 2
    second_start = first_end + 2
    return (0, first_end), (second_start, size - 1)


def _shape_cells(v_len: int, h_len: int, orientation: int) -> tuple[tuple[int, int], ...]:
    """Normalized L cells; orientation names the elbow's bounding-box corner.

    0=top-left, 1=top-right, 2=bottom-left, 3=bottom-right.
    """
    if orientation == 0:
        cells = {(0, c) for c in range(h_len)} | {(r, 0) for r in range(v_len)}
    elif orientation == 1:
        cells = {(0, c) for c in range(h_len)} | {(r, h_len - 1) for r in range(v_len)}
    elif orientation == 2:
        cells = {(v_len - 1, c) for c in range(h_len)} | {(r, 0) for r in range(v_len)}
    elif orientation == 3:
        cells = {(v_len - 1, c) for c in range(h_len)} | {
            (r, h_len - 1) for r in range(v_len)
        }
    else:  # pragma: no cover - internal invariant
        raise ValueError(f"unknown orientation {orientation}")
    return tuple(sorted(cells))


def _normalize(cells):
    cells = tuple(cells)
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def _d4_variants(cells):
    variants = set()
    current = _normalize(cells)
    for _ in range(4):
        variants.add(current)
        variants.add(_normalize((r, -c) for r, c in current))
        current = _normalize((c, -r) for r, c in current)
    return tuple(sorted(variants))


# Canonical pair 4 contains a two-turn path.  This compact 3x3 template has
# two bends and one straight degree-two cell, so every ordinary draw covers the
# multi-turn branch as well as the shortcut-rebutting straight-cell branch.
_Z5_VARIANTS = _d4_variants(((0, 1), (0, 2), (1, 1), (2, 0), (2, 1)))


def _selected_slots(sample_index: int, n_paths: int) -> tuple[int, ...]:
    # Opposite quadrants come first; rotating the order moves single-path
    # overrides around the whole grid rather than pinning them to one corner.
    shift = sample_index % 4
    order = _ORIENTATION_ORDER[shift:] + _ORIENTATION_ORDER[:shift]
    return tuple(order[:n_paths])


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(k for k, value in overrides.items() if value is not None and k not in AXES)
    if unknown:
        raise ValueError(f"unknown override axis/axes: {unknown}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    h_band, w_band, n_band = _band_ranges(difficulty)
    h = _draw_axis_int(ctx, overrides, "grid_h", *h_band, 8, 14)
    w = _draw_axis_int(ctx, overrides, "grid_w", *w_band, 8, 14)
    n_paths = _draw_axis_int(ctx, overrides, "n_paths", *n_band, 1, 4)

    row_regions = _slot_intervals(h)
    col_regions = _slot_intervals(w)
    slots = (
        (row_regions[0], col_regions[0]),
        (row_regions[0], col_regions[1]),
        (row_regions[1], col_regions[0]),
        (row_regions[1], col_regions[1]),
    )
    rng = ctx.draw_rng("path_geometry")
    grid = full_grid(h, w, 0)

    for index, slot_index in enumerate(_selected_slots(sample_index, n_paths)):
        (r0, r1), (c0, c1) = slots[slot_index]
        slot_h, slot_w = r1 - r0 + 1, c1 - c0 + 1

        if index == 0:
            # A two-turn canonical branch, transformed through its full D4 orbit.
            cells = _Z5_VARIANTS[(sample_index + rng.randrange(len(_Z5_VARIANTS))) % len(_Z5_VARIANTS)]
        else:
            max_v = min(4, slot_h)
            max_h = min(4, slot_w)
            if index == 1:
                # Keep a one-turn component with a different extent from Z5.
                v_len, h_len = ((3, 2) if sample_index % 2 == 0 else (2, 3))
            else:
                v_len = rng.randint(2, max_v)
                h_len = rng.randint(2, max_h)
                if v_len == 2 and h_len == 2:
                    v_len = 3
            orientation = _ORIENTATION_ORDER[(sample_index + index) % 4]
            cells = _shape_cells(v_len, h_len, orientation)

        shape_h = max(r for r, _ in cells) + 1
        shape_w = max(c for _, c in cells) + 1
        anchor_r = rng.randint(r0, r1 - shape_h + 1)
        anchor_c = rng.randint(c0, c1 - shape_w + 1)
        for dr, dc in cells:
            grid[anchor_r + dr][anchor_c + dc] = 3

    observed = observe_overrides(grid)
    expected = {"grid_h": h, "grid_w": w, "n_paths": n_paths}
    if observed != expected:  # pragma: no cover - fail-loud internal contract
        raise RuntimeError(f"generated scene lost keyed axes: expected {expected}, observed {observed}")
    errors = self_check(grid)
    if errors:  # pragma: no cover - fail-loud internal contract
        raise RuntimeError("generated invalid orthogonal-path scene: " + "; ".join(errors))
    return grid


def _neighbors(r: int, c: int, h: int, w: int):
    for dr, dc, name in ((-1, 0, "up"), (1, 0, "down"), (0, -1, "left"), (0, 1, "right")):
        nr, nc = r + dr, c + dc
        if 0 <= nr < h and 0 <= nc < w:
            yield nr, nc, name


def _components(grid) -> list[set[tuple[int, int]]]:
    h, w = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == 3}
    components: list[set[tuple[int, int]]] = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        comp = {start}
        queue = deque([start])
        while queue:
            r, c = queue.popleft()
            for nr, nc, _ in _neighbors(r, c, h, w):
                if (nr, nc) in unseen:
                    unseen.remove((nr, nc))
                    comp.add((nr, nc))
                    queue.append((nr, nc))
        components.append(comp)
    return components


def _analyze_component(comp: set[tuple[int, int]]) -> dict[str, Any]:
    directions: dict[tuple[int, int], tuple[str, ...]] = {}
    for r, c in comp:
        dirs = []
        for dr, dc, name in ((-1, 0, "up"), (1, 0, "down"), (0, -1, "left"), (0, 1, "right")):
            if (r + dr, c + dc) in comp:
                dirs.append(name)
        directions[(r, c)] = tuple(dirs)

    endpoints = [cell for cell, dirs in directions.items() if len(dirs) == 1]
    overfull = [cell for cell, dirs in directions.items() if len(dirs) > 2]
    isolated = [cell for cell, dirs in directions.items() if len(dirs) == 0]
    bends = []
    straight = []
    for cell, dirs in directions.items():
        if len(dirs) != 2:
            continue
        horizontal = any(d in {"left", "right"} for d in dirs)
        vertical = any(d in {"up", "down"} for d in dirs)
        if horizontal and vertical:
            bends.append(cell)
        else:
            straight.append(cell)

    orientation = None
    if len(bends) == 1:
        bend_r, bend_c = bends[0]
        r0, r1 = min(r for r, _ in comp), max(r for r, _ in comp)
        c0, c1 = min(c for _, c in comp), max(c for _, c in comp)
        orientation = {
            (r0, c0): "top_left",
            (r0, c1): "top_right",
            (r1, c0): "bottom_left",
            (r1, c1): "bottom_right",
        }.get((bend_r, bend_c))

    return {
        "size": len(comp),
        "endpoints": endpoints,
        "overfull": overfull,
        "isolated": isolated,
        "bends": bends,
        "straight": straight,
        "orientation": orientation,
    }


def semantic_observables(grid) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        return {"errors": ["empty or non-list grid"]}
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        return {"errors": ["grid is not rectangular"]}
    bad = sorted({value for row in grid for value in row if value not in {0, 3}})
    if bad:
        errors.append(f"unexpected colors {bad}; only 0 and 3 are lawful inputs")

    components = _components(grid)
    analyses = [_analyze_component(comp) for comp in components]
    if not components:
        errors.append("no green path component")
    for index, analysis in enumerate(analyses):
        if analysis["size"] < 3:
            errors.append(f"component {index} has size {analysis['size']} < 3")
        if analysis["isolated"]:
            errors.append(f"component {index} contains isolated green cells")
        if analysis["overfull"]:
            errors.append(f"component {index} branches at {analysis['overfull']}")
        if len(analysis["endpoints"]) != 2:
            errors.append(
                f"component {index} has {len(analysis['endpoints'])} endpoints, expected 2"
            )
        if len(analysis["bends"]) < 1:
            errors.append(f"component {index} has no turn cells")

    return {
        "errors": errors,
        "grid_h": len(grid),
        "grid_w": width,
        "n_paths": len(components),
        "components": analyses,
        "bend_count": sum(len(a["bends"]) for a in analyses),
        "straight_degree2_count": sum(len(a["straight"]) for a in analyses),
        "endpoint_count": sum(len(a["endpoints"]) for a in analyses),
        "orientations": sorted({a["orientation"] for a in analyses if a["orientation"]}),
        "component_sizes": [a["size"] for a in analyses],
        "one_turn_paths": sum(len(a["bends"]) == 1 for a in analyses),
        "multi_turn_paths": sum(len(a["bends"]) >= 2 for a in analyses),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the authority-level input grammar, not curriculum scheduling."""
    return list(semantic_observables(grid).get("errors", []))


def strict_canonical_like(grid) -> list[str]:
    return self_check(grid)


def observe_overrides(grid) -> dict[str, int]:
    obs = semantic_observables(grid)
    if obs.get("errors"):
        raise ValueError("cannot observe axes from invalid scene: " + "; ".join(obs["errors"]))
    return {"grid_h": obs["grid_h"], "grid_w": obs["grid_w"], "n_paths": obs["n_paths"]}


def _green_neighbor_directions(grid, r: int, c: int) -> tuple[str, ...]:
    h, w = len(grid), len(grid[0])
    return tuple(name for nr, nc, name in _neighbors(r, c, h, w) if grid[nr][nc] == 3)


def rule_mirror(grid):
    """Test-only Python mirror; the canonical Racket remains output authority."""
    if self_check(grid):
        raise ValueError("rule_mirror requires a lawful input")
    out = [row[:] for row in grid]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 3:
                continue
            dirs = _green_neighbor_directions(grid, r, c)
            horizontal = any(d in {"left", "right"} for d in dirs)
            vertical = any(d in {"up", "down"} for d in dirs)
            if len(dirs) == 2 and horizontal and vertical:
                out[r][c] = 6
    return out


def _identity(grid):
    return [row[:] for row in grid]


def _recolor_every_degree_two(grid):
    out = [row[:] for row in grid]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value == 3 and len(_green_neighbor_directions(grid, r, c)) == 2:
                out[r][c] = 6
    return out


def _recolor_all_bbox_corners(grid):
    out = [row[:] for row in grid]
    for comp in _components(grid):
        r0, r1 = min(r for r, _ in comp), max(r for r, _ in comp)
        c0, c1 = min(c for _, c in comp), max(c for _, c in comp)
        for cell in ((r0, c0), (r0, c1), (r1, c0), (r1, c1)):
            if cell in comp:
                out[cell[0]][cell[1]] = 6
    return out


def _recolor_top_left_green_bbox_corner(grid):
    out = [row[:] for row in grid]
    for comp in _components(grid):
        r0, c0 = min(r for r, _ in comp), min(c for _, c in comp)
        candidates = sorted(cell for cell in comp if cell[0] == r0 or cell[1] == c0)
        if candidates:
            r, c = candidates[0]
            out[r][c] = 6
    return out


SEMANTIC_RIVALS: dict[str, Callable] = {
    "identity": _identity,
    "recolor every degree-two green cell": _recolor_every_degree_two,
    "recolor every green bounding-box corner": _recolor_all_bbox_corners,
    "recolor a fixed top-left component cell": _recolor_top_left_green_bbox_corner,
}
LESSON_COMPETITORS = SEMANTIC_RIVALS
CANONICAL_SHORTCUTS = SEMANTIC_RIVALS


def _witness(grid, predicate) -> bool:
    obs = semantic_observables(grid)
    return not obs.get("errors") and bool(predicate(obs))


SEMANTIC_WITNESSES = {
    "elbow_recoloring_fires": lambda grid: _witness(grid, lambda o: o["bend_count"] >= 1),
    "straight_degree_two_control": lambda grid: _witness(
        grid, lambda o: o["straight_degree2_count"] >= 1
    ),
    "multi_turn_path": lambda grid: _witness(grid, lambda o: o["multi_turn_paths"] >= 1),
    "bbox_corner_shortcut_rebuttal": lambda grid: (
        not self_check(grid) and _recolor_all_bbox_corners(grid) != rule_mirror(grid)
    ),
    "fixed_position_shortcut_rebuttal": lambda grid: (
        not self_check(grid) and _recolor_top_left_green_bbox_corner(grid) != rule_mirror(grid)
    ),
}
WITNESS_RIVALS = {
    "elbow_recoloring_fires": ["identity"],
    "straight_degree_two_control": ["recolor every degree-two green cell"],
    "multi_turn_path": ["recolor a fixed top-left component cell"],
    "bbox_corner_shortcut_rebuttal": ["recolor every green bounding-box corner"],
    "fixed_position_shortcut_rebuttal": ["recolor a fixed top-left component cell"],
}


def lesson_identifiable(demos, query) -> list[str]:
    errors: list[str] = []
    query_input = query.get("input") if isinstance(query, dict) else None
    if self_check(query_input):
        return ["query input is not a lawful collection of orthogonal paths"]
    truth = rule_mirror(query_input)

    for index, demo in enumerate(demos):
        demo_input = demo.get("input") if isinstance(demo, dict) else None
        if self_check(demo_input):
            errors.append(f"demo {index} input is not a lawful collection of orthogonal paths")
            continue
        if demo.get("output") != rule_mirror(demo_input):
            errors.append(f"demo {index} output disagrees with the elbow rule")
    if errors:
        return errors

    for name, competitor in LESSON_COMPETITORS.items():
        if all(competitor(demo["input"]) == demo["output"] for demo in demos):
            if competitor(query_input) != truth:
                errors.append(
                    f"demos remain compatible with competitor '{name}', which changes the query answer"
                )
    return errors
