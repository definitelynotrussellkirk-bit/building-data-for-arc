"""Generator for ff5ef89054d2 — isolated markers expand to diagonal Xs.

The canonical rule keeps every input cell unchanged and, for each nonzero cell
with an empty eight-neighborhood, paints its in-bounds diagonal neighbors in
the same color. Connected non-singleton components are deliberately included
as negative evidence: they remain unchanged.
"""
from __future__ import annotations

from collections import Counter
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "ff5ef89054d2"
TASK_ID = "ff5ef89054d2"
VERSION = "3.1.0"
RULE_HASH = "d4b2121f30a4"

SUMMARY = (
    "A sparse 9..11 square-or-near-square grid contains two to four isolated "
    "colored singleton markers. Each singleton gains its in-bounds diagonal "
    "neighbors in the same color, forming a full or boundary-clipped X. Some "
    "profiles also contain one separated 2..3-cell connected decoy, which is "
    "not isolated and therefore remains unchanged."
)

INVARIANTS = [
    "background is color 0 and all cells use ARC colors 0..9",
    "there are 2..4 isolated nonzero singleton markers",
    "there are 0..1 separated monochromatic 4-connected decoy blobs of size 2..3",
    "every singleton's in-bounds diagonal arm cells are initially empty",
    "singleton X footprints are pairwise disjoint",
    "at most one singleton is on the outer boundary; all others are interior",
    "decoy colors are drawn from the marker palette and decoys remain unchanged",
]

BOUNDARY_MODES = (
    "interior",
    "left_edge",
    "right_edge",
    "top_edge",
    "bottom_edge",
    "corner",
)

AXES = {
    "grid_h": {
        "type": "int",
        "default": "linked canonical profile",
        "valid": "9..11",
    },
    "grid_w": {
        "type": "int",
        "default": "linked canonical profile",
        "valid": "9..11",
    },
    "n_markers": {
        "type": "int",
        "default": "linked semantic profile",
        "valid": "2..4",
    },
    "n_decoy_blobs": {
        "type": "int",
        "default": "linked semantic profile",
        "valid": "0..1",
    },
    "boundary_mode": {
        "type": "str",
        "default": "linked semantic profile",
        "valid": "|".join(BOUNDARY_MODES),
    },
}

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.30

# Profiles 0 and 1 are deliberately close to the public 9x9/11x11
# three-marker morphology and preserve a 2/6 strict-canonical floor. Profiles
# 2..5 contain decoys. Therefore every cyclic three-demo window contains a
# decoy and every cyclic four-pair lesson contains at least two: holding out any
# one pair as the query still leaves negative evidence against "expand every
# nonzero cell". Every three-demo window also contains a boundary scene.
_PROFILES = (
    {"grid_h": 9, "grid_w": 9, "n_markers": 3,
     "n_decoy_blobs": 0, "boundary_mode": "interior"},
    {"grid_h": 11, "grid_w": 11, "n_markers": 3,
     "n_decoy_blobs": 0, "boundary_mode": "left_edge"},
    {"grid_h": 9, "grid_w": 9, "n_markers": 3,
     "n_decoy_blobs": 1, "boundary_mode": "right_edge"},
    {"grid_h": 11, "grid_w": 11, "n_markers": 4,
     "n_decoy_blobs": 1, "boundary_mode": "top_edge"},
    {"grid_h": 10, "grid_w": 10, "n_markers": 2,
     "n_decoy_blobs": 1, "boundary_mode": "bottom_edge"},
    {"grid_h": 9, "grid_w": 11, "n_markers": 4,
     "n_decoy_blobs": 1, "boundary_mode": "corner"},
)
SCHEDULE_PROFILES = tuple(range(len(_PROFILES)))

_DIAGONALS = ((-1, -1), (-1, 1), (1, -1), (1, 1))
_ORTHOGONALS = ((-1, 0), (1, 0), (0, -1), (0, 1))
_NEIGHBORS_8 = _ORTHOGONALS + _DIAGONALS
_BLOB_SHAPES = (
    ((0, 0), (0, 1)),
    ((0, 0), (1, 0)),
    ((0, 0), (0, 1), (0, 2)),
    ((0, 0), (1, 0), (2, 0)),
    ((0, 0), (0, 1), (1, 0)),
    ((0, 0), (0, 1), (1, 1)),
)


def schedule_profile(seed, sample_index, difficulty=None):
    """Profile id used by the semantic gate's schedule-coverage audit."""
    del seed
    offset = {None: 0, "easy": 0, "medium": 2, "hard": 4}.get(difficulty)
    if offset is None:
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    return (int(sample_index) + offset) % len(_PROFILES)


def _draw_profile_int(ctx, overrides, label, default, lo, hi):
    if label in overrides and overrides[label] is not None:
        return ctx.draw_int(label, lo, hi)
    return ctx.draw_int(label, default, default)


def _draw_profile_choice(ctx, overrides, label, default, options):
    if label in overrides and overrides[label] is not None:
        return ctx.draw_choice(label, options)
    return ctx.draw_choice(label, (default,))


def _in_bounds(r: int, c: int, h: int, w: int) -> bool:
    return 0 <= r < h and 0 <= c < w


def _guard(cells, h: int, w: int) -> set[tuple[int, int]]:
    return {
        (rr, cc)
        for r, c in cells
        for rr in range(max(0, r - 1), min(h, r + 2))
        for cc in range(max(0, c - 1), min(w, c + 2))
    }


def _boundary_candidates(mode: str, h: int, w: int) -> list[tuple[int, int]]:
    if mode == "left_edge":
        return [(r, 0) for r in range(1, h - 1)]
    if mode == "right_edge":
        return [(r, w - 1) for r in range(1, h - 1)]
    if mode == "top_edge":
        return [(0, c) for c in range(1, w - 1)]
    if mode == "bottom_edge":
        return [(h - 1, c) for c in range(1, w - 1)]
    if mode == "corner":
        return [(0, 0), (0, w - 1), (h - 1, 0), (h - 1, w - 1)]
    if mode == "interior":
        return []
    raise ValueError(f"unknown boundary mode: {mode!r}")


def _blob_options(h: int, w: int):
    for shape in _BLOB_SHAPES:
        sh = max(dr for dr, _ in shape) + 1
        sw = max(dc for _, dc in shape) + 1
        for r0 in range(h - sh + 1):
            for c0 in range(w - sw + 1):
                yield tuple((r0 + dr, c0 + dc) for dr, dc in shape)


def _place_scene(rng, h: int, w: int, n_markers: int,
                 n_decoy_blobs: int, boundary_mode: str):
    interior = [(r, c) for r in range(1, h - 1) for c in range(1, w - 1)]
    rng.shuffle(interior)
    boundary = _boundary_candidates(boundary_mode, h, w)
    rng.shuffle(boundary)
    marker_candidate_lists = (
        [boundary] + [interior] * (n_markers - 1)
        if boundary_mode != "interior"
        else [interior] * n_markers
    )

    blob_candidates = list(_blob_options(h, w))
    rng.shuffle(blob_candidates)
    nodes = 0

    def find_blob(reserved: set[tuple[int, int]]):
        if n_decoy_blobs == 0:
            return []
        for cells in blob_candidates:
            if _guard(cells, h, w).isdisjoint(reserved):
                return [cells]
        return None

    def search(index: int, chosen: list[tuple[int, int]],
               reserved: set[tuple[int, int]]):
        nonlocal nodes
        nodes += 1
        if nodes > 50000:
            return None
        if index == len(marker_candidate_lists):
            blobs = find_blob(reserved)
            if blobs is not None:
                return list(chosen), blobs
            return None
        for cell in marker_candidate_lists[index]:
            cell_guard = _guard((cell,), h, w)
            if not cell_guard.isdisjoint(reserved):
                continue
            result = search(
                index + 1,
                chosen + [cell],
                reserved | cell_guard,
            )
            if result is not None:
                return result
        return None

    placed = search(0, [], set())
    if placed is None:
        raise ValueError(
            "could not place requested markers/decoy without overlap: "
            f"{h}x{w}, markers={n_markers}, decoys={n_decoy_blobs}, "
            f"boundary_mode={boundary_mode}"
        )
    return placed


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)!r}")

    profile_index = schedule_profile(seed, sample_index, difficulty)
    profile = _PROFILES[profile_index]
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    h = _draw_profile_int(ctx, overrides, "grid_h", profile["grid_h"], 9, 11)
    w = _draw_profile_int(ctx, overrides, "grid_w", profile["grid_w"], 9, 11)
    n_markers = _draw_profile_int(
        ctx, overrides, "n_markers", profile["n_markers"], 2, 4
    )
    n_decoys = _draw_profile_int(
        ctx, overrides, "n_decoy_blobs", profile["n_decoy_blobs"], 0, 1
    )
    boundary_mode = _draw_profile_choice(
        ctx,
        overrides,
        "boundary_mode",
        profile["boundary_mode"],
        BOUNDARY_MODES,
    )

    layout_rng = ctx.draw_rng("layout")
    markers, blobs = _place_scene(
        layout_rng, h, w, n_markers, n_decoys, boundary_mode
    )
    color_rng = ctx.draw_rng("colors")
    palette = color_rng.sample(list(range(1, 10)), min(3, n_markers))
    color_rng.shuffle(palette)
    marker_colors = [palette[i % len(palette)] for i in range(n_markers)]
    color_rng.shuffle(marker_colors)

    grid = full_grid(h, w, 0)
    for (r, c), color in zip(markers, marker_colors):
        grid[r][c] = color
    for cells in blobs:
        color = color_rng.choice(palette)
        for r, c in cells:
            grid[r][c] = color

    errors = self_check(grid)
    if errors:
        raise AssertionError("generated invalid isolated-X lesson: " + "; ".join(errors))
    observed = observe_overrides(grid)
    requested = ctx.recorded_draws()
    for axis in AXES:
        if observed.get(axis) != requested.get(axis):
            raise AssertionError(
                f"axis {axis!r} requested {requested.get(axis)!r}, "
                f"observed {observed.get(axis)!r}"
            )
    return grid


def _components(cells: set[tuple[int, int]], directions):
    remaining = set(cells)
    result: list[set[tuple[int, int]]] = []
    while remaining:
        start = remaining.pop()
        comp = {start}
        stack = [start]
        while stack:
            r, c = stack.pop()
            for dr, dc in directions:
                nxt = (r + dr, c + dc)
                if nxt in remaining:
                    remaining.remove(nxt)
                    comp.add(nxt)
                    stack.append(nxt)
        result.append(comp)
    return result


def _classify_boundary(marker: tuple[int, int], h: int, w: int) -> str:
    r, c = marker
    if r in (0, h - 1) and c in (0, w - 1):
        return "corner"
    if c == 0:
        return "left_edge"
    if c == w - 1:
        return "right_edge"
    if r == 0:
        return "top_edge"
    if r == h - 1:
        return "bottom_edge"
    return "interior"


def _analyze(grid: Any) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return {"errors": ["grid must be a non-empty list of rows"]}
    h, w = len(grid), len(grid[0])
    if w == 0 or any(not isinstance(row, list) or len(row) != w for row in grid):
        return {"errors": ["grid rows must be non-empty and rectangular"]}
    if not 9 <= h <= 11:
        errors.append(f"grid height {h} outside 9..11")
    if not 9 <= w <= 11:
        errors.append(f"grid width {w} outside 9..11")

    nonzero: set[tuple[int, int]] = set()
    values: dict[tuple[int, int], int] = {}
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                errors.append(f"cell ({r},{c}) has invalid ARC color {value!r}")
                continue
            if value:
                nonzero.add((r, c))
                values[(r, c)] = value
    if any("invalid ARC color" in error for error in errors):
        return {"errors": errors}

    comps8 = _components(nonzero, _NEIGHBORS_8)
    markers = sorted(next(iter(comp)) for comp in comps8 if len(comp) == 1)
    decoys = [comp for comp in comps8 if len(comp) > 1]
    if not 2 <= len(markers) <= 4:
        errors.append(f"expected 2..4 isolated singleton markers, got {len(markers)}")
    if not 0 <= len(decoys) <= 1:
        errors.append(f"expected 0..1 decoy blobs, got {len(decoys)}")

    for index, comp in enumerate(decoys):
        if not 2 <= len(comp) <= 3:
            errors.append(f"decoy {index} has size {len(comp)}, expected 2..3")
        if len(_components(set(comp), _ORTHOGONALS)) != 1:
            errors.append(f"decoy {index} must be 4-connected")
        colors = {values[p] for p in comp}
        if len(colors) != 1:
            errors.append(f"decoy {index} must be monochromatic")

    marker_palette = {values[p] for p in markers}
    expected_colors = min(3, len(markers))
    if markers and len(marker_palette) != expected_colors:
        errors.append(
            f"marker palette has {len(marker_palette)} colors, expected {expected_colors}"
        )
    decoy_palette = {values[p] for comp in decoys for p in comp}
    if decoy_palette - marker_palette:
        errors.append("decoy colors must be drawn from the marker palette")

    boundary_markers = [p for p in markers if _classify_boundary(p, h, w) != "interior"]
    if len(boundary_markers) > 1:
        errors.append(f"expected at most one boundary marker, got {len(boundary_markers)}")
    boundary_mode = (
        _classify_boundary(boundary_markers[0], h, w)
        if len(boundary_markers) == 1
        else "interior"
    )

    arm_owner: dict[tuple[int, int], tuple[int, int]] = {}
    arms_by_marker: dict[tuple[int, int], tuple[tuple[int, int], ...]] = {}
    for marker in markers:
        r, c = marker
        arms = tuple(
            (r + dr, c + dc)
            for dr, dc in _DIAGONALS
            if _in_bounds(r + dr, c + dc, h, w)
        )
        arms_by_marker[marker] = arms
        for arm in arms:
            if arm in nonzero:
                errors.append(f"marker {marker} has occupied diagonal arm {arm}")
            if arm in arm_owner:
                errors.append(
                    f"markers {arm_owner[arm]} and {marker} share diagonal arm {arm}"
                )
            arm_owner[arm] = marker

    changed_cells = len(arm_owner)
    if changed_cells == 0:
        errors.append("the rule must visibly add at least one diagonal arm")

    return {
        "errors": errors,
        "grid_h": h,
        "grid_w": w,
        "n_markers": len(markers),
        "n_decoy_blobs": len(decoys),
        "boundary_mode": boundary_mode,
        "markers": markers,
        "decoys": decoys,
        "values": values,
        "marker_palette": marker_palette,
        "arms_by_marker": arms_by_marker,
        "changed_cells": changed_cells,
    }


def observe_overrides(grid):
    analysis = _analyze(grid)
    if analysis["errors"]:
        return {}
    return {
        "grid_h": analysis["grid_h"],
        "grid_w": analysis["grid_w"],
        "n_markers": analysis["n_markers"],
        "n_decoy_blobs": analysis["n_decoy_blobs"],
        "boundary_mode": analysis["boundary_mode"],
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty, meta
    return list(_analyze(grid)["errors"])


def _apply_rule(grid, *, require_isolation: bool = True,
                directions=_DIAGONALS, keep_centers: bool = True,
                ignore_boundary: bool = False):
    h, w = len(grid), len(grid[0])
    out = [list(row) for row in grid]
    for r in range(h):
        for c in range(w):
            value = grid[r][c]
            if value == 0:
                continue
            isolated = all(
                not _in_bounds(r + dr, c + dc, h, w)
                or grid[r + dr][c + dc] == 0
                for dr, dc in _NEIGHBORS_8
            )
            if require_isolation and not isolated:
                continue
            if ignore_boundary and _classify_boundary((r, c), h, w) != "interior":
                continue
            if not keep_centers:
                out[r][c] = 0
            for dr, dc in directions:
                rr, cc = r + dr, c + dc
                if _in_bounds(rr, cc, h, w) and out[rr][cc] == 0:
                    out[rr][cc] = value
    return out


def rule_mirror(grid):
    errors = self_check(grid)
    if errors:
        raise ValueError("; ".join(errors))
    return _apply_rule(grid)


def semantic_observables(grid) -> dict[str, Any]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        return {"errors": list(analysis["errors"])}
    arm_counts = Counter(len(arms) for arms in analysis["arms_by_marker"].values())
    return {
        **observe_overrides(grid),
        "marker_colors": len(analysis["marker_palette"]),
        "full_x_markers": arm_counts.get(4, 0),
        "edge_clipped_markers": arm_counts.get(2, 0),
        "corner_clipped_markers": arm_counts.get(1, 0),
        "changed_cells": analysis["changed_cells"],
        "has_decoy": bool(analysis["decoys"]),
        "has_boundary_marker": analysis["boundary_mode"] != "interior",
        "has_repeated_marker_color": (
            analysis["n_markers"] > len(analysis["marker_palette"])
        ),
    }


def strict_canonical_like(grid) -> list[str]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        return list(analysis["errors"])
    reasons: list[str] = []
    if (analysis["grid_h"], analysis["grid_w"]) not in ((9, 9), (11, 11)):
        reasons.append("canonical grids are 9x9 or 11x11")
    if analysis["n_markers"] != 3:
        reasons.append("canonical inputs contain exactly three singleton markers")
    if analysis["n_decoy_blobs"] != 0:
        reasons.append("canonical inputs contain no non-singleton decoy")
    if analysis["boundary_mode"] not in ("interior", "left_edge", "right_edge"):
        reasons.append("canonical clipping is absent or on a vertical side edge")
    return reasons


def _witness(grid, predicate: Callable[[dict[str, Any]], bool]) -> bool:
    obs = semantic_observables(grid)
    return not obs.get("errors") and bool(predicate(obs))


SEMANTIC_WITNESSES = {
    "interior_full_x": lambda grid: _witness(grid, lambda o: o["full_x_markers"] > 0),
    "left_edge_clip": lambda grid: _witness(grid, lambda o: o["boundary_mode"] == "left_edge"),
    "right_edge_clip": lambda grid: _witness(grid, lambda o: o["boundary_mode"] == "right_edge"),
    "top_edge_clip": lambda grid: _witness(grid, lambda o: o["boundary_mode"] == "top_edge"),
    "bottom_edge_clip": lambda grid: _witness(grid, lambda o: o["boundary_mode"] == "bottom_edge"),
    "corner_clip": lambda grid: _witness(grid, lambda o: o["boundary_mode"] == "corner"),
    "decoy_blob_unchanged": lambda grid: _witness(grid, lambda o: o["has_decoy"]),
    "centers_retained": lambda grid: _witness(grid, lambda o: o["n_markers"] >= 2),
}


def _rival_expand_all_nonzero(grid):
    return _apply_rule(grid, require_isolation=False)


def _rival_ignore_boundary_markers(grid):
    return _apply_rule(grid, ignore_boundary=True)


def _rival_orthogonal_plus(grid):
    return _apply_rule(grid, directions=_ORTHOGONALS)


def _rival_remove_centers(grid):
    return _apply_rule(grid, keep_centers=False)


SEMANTIC_RIVALS = {
    "expand_all_nonzero": _rival_expand_all_nonzero,
    "ignore_boundary_markers": _rival_ignore_boundary_markers,
    "orthogonal_plus": _rival_orthogonal_plus,
    "remove_marker_centers": _rival_remove_centers,
}
WITNESS_RIVALS = {
    "decoy_blob_unchanged": ["expand_all_nonzero"],
    "left_edge_clip": ["ignore_boundary_markers"],
    "right_edge_clip": ["ignore_boundary_markers"],
    "top_edge_clip": ["ignore_boundary_markers"],
    "bottom_edge_clip": ["ignore_boundary_markers"],
    "corner_clip": ["ignore_boundary_markers"],
    "interior_full_x": ["orthogonal_plus"],
    "centers_retained": ["remove_marker_centers"],
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    # All public inputs contain only isolated nonzero cells, so this wrong rule
    # is answer-equivalent on canonical data and needs generated decoys.
    "expand_all_nonzero": _rival_expand_all_nonzero,
}


def lesson_identifiable(demos, query) -> list[str]:
    reasons: list[str] = []
    query_input = query.get("input") if isinstance(query, dict) else None
    query_errors = self_check(query_input)
    if query_errors:
        return ["query input is not a lawful isolated-X scene: " + "; ".join(query_errors)]
    query_truth = rule_mirror(query_input)

    for index, demo in enumerate(demos):
        demo_input = demo.get("input") if isinstance(demo, dict) else None
        errors = self_check(demo_input)
        if errors:
            reasons.append(f"demo {index} input is unlawful: {'; '.join(errors)}")
            continue
        if demo.get("output") != rule_mirror(demo_input):
            reasons.append(f"demo {index} output disagrees with the isolated-X rule")
    if reasons:
        return reasons

    for name, competitor in LESSON_COMPETITORS.items():
        if all(competitor(demo["input"]) == demo["output"] for demo in demos):
            if competitor(query_input) != query_truth:
                reasons.append(
                    f"demos remain compatible with competitor {name!r}, "
                    "which changes the query answer"
                )
    return reasons
