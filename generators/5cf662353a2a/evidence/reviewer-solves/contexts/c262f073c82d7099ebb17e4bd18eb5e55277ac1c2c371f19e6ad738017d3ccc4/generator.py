"""Generator for 5cf662353a2a: sort objects by cell count into marker bins.

The selected Racket rule finds the non-background, non-marker components, sorts
those objects by *cell count*, normalizes each bounding box, and bottom-aligns
them over the color-1 marker columns from left to right.  This sampler makes the
cell-count key identifiable: every ordinary grid contains a size-4 T tetromino
(bounding-box area 6) and a size-5 line (bounding-box area 5), so the plausible
"sort by bounding-box area" shortcut gives a different labelled answer.
"""
from __future__ import annotations

from collections import deque
from copy import deepcopy

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "5cf662353a2a"
TASK_ID = GENERATOR_ID
RULE_HASH = "da86a7976cec"
VERSION = "3.0.0"

SUMMARY = (
    "Distinct colored objects are scattered above color-1 marker cells. Sort "
    "objects by increasing cell count, normalize their shapes, and bottom-align "
    "smallest-to-largest over the left-to-right markers."
)

INVARIANTS = [
    "background is color 0 and marker cells are color 1 on the bottom row",
    "there is one uniquely colored connected object per marker",
    "object cell counts are distinct and determine the left-to-right order",
    "the normalized objects fit above their assigned markers without clipping",
    "every generated grid refutes sorting by bounding-box area",
]

# Names encode every observable part of the geometry.  Marker locations are
# chosen so all normalized shapes fit after the authoritative drop.
_PROFILE_DATA = {
    "canonical_10x12_3": (10, 12, (1, 5, 9)),
    "canonical_11x13_3": (11, 13, (1, 6, 10)),
    "wide_12x17_3": (12, 17, (1, 7, 14)),
    "wide_13x18_4": (13, 18, (1, 5, 10, 15)),
    "tall_15x14_3": (15, 14, (1, 6, 11)),
    "large_15x20_4": (15, 20, (1, 6, 11, 17)),
}
_PROFILE_NAMES = tuple(_PROFILE_DATA)

AXES = {
    "layout_profile": {
        "type": "str",
        "default": "deterministic six-profile schedule with canonical profiles in every band",
        "valid": "canonical_10x12_3|canonical_11x13_3|wide_12x17_3|wide_13x18_4|tall_15x14_3|large_15x20_4",
    },
    "palette_start": {
        "type": "int",
        "default": "keyed uniform 2..5",
        "valid": "2..5",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []

# Each six-position cycle contains both canonical (height,width,palette) profiles.
# Difficulty changes the order and therefore the sampled geometry without
# withdrawing any legal exact override from any band.
_SCHEDULES = {
    None: (
        "canonical_10x12_3", "wide_12x17_3", "canonical_11x13_3",
        "wide_13x18_4", "tall_15x14_3", "large_15x20_4",
    ),
    "easy": (
        "canonical_10x12_3", "canonical_11x13_3", "wide_12x17_3",
        "canonical_10x12_3", "tall_15x14_3", "canonical_11x13_3",
    ),
    "medium": (
        "canonical_11x13_3", "wide_12x17_3", "canonical_10x12_3",
        "large_15x20_4", "tall_15x14_3", "canonical_11x13_3",
    ),
    "hard": (
        "canonical_10x12_3", "large_15x20_4", "canonical_11x13_3",
        "wide_13x18_4", "wide_12x17_3", "canonical_10x12_3",
    ),
}
SCHEDULE_PROFILES = _PROFILE_NAMES

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0


def schedule_profile(seed, sample_index, difficulty=None):
    """Declared default schedule; seed is intentionally nuisance-only here."""
    del seed
    if difficulty not in _SCHEDULES:
        raise ValueError("difficulty must be one of None, easy, medium, hard")
    schedule = _SCHEDULES[difficulty]
    return schedule[int(sample_index) % len(schedule)]


def _normalize_shape(cells):
    cells = tuple(cells)
    top = min(r for r, _ in cells)
    left = min(c for _, c in cells)
    return tuple(sorted((r - top, c - left) for r, c in cells))


def _rotate(shape):
    return _normalize_shape((c, -r) for r, c in shape)


def _reflect(shape):
    return _normalize_shape((r, -c) for r, c in shape)


def _dihedral_variants(shape):
    current = _normalize_shape(shape)
    variants = set()
    for _ in range(4):
        variants.add(current)
        variants.add(_reflect(current))
        current = _rotate(current)
    return tuple(sorted(variants))


_DOMINO = _dihedral_variants(((0, 0), (1, 0)))
_TRIOMINO = tuple(sorted(set(
    _dihedral_variants(((0, 0), (1, 0), (2, 0)))
    + _dihedral_variants(((0, 0), (1, 0), (1, 1)))
)))
_T_TETROMINO = _dihedral_variants(((0, 0), (0, 1), (0, 2), (1, 1)))
_VERTICAL_FIVE = (((0, 0), (1, 0), (2, 0), (3, 0), (4, 0)),)


def _shape_family(size):
    return {
        2: _DOMINO,
        3: _TRIOMINO,
        4: _T_TETROMINO,
        # Keeping the five-cell line vertical guarantees it fits at the
        # rightmost canonical marker while preserving bounding-box area 5.
        5: _VERTICAL_FIVE,
    }[size]


def _shape_for(ctx, size, difficulty):
    options = _shape_family(size)
    return ctx.draw_rng(f"shape_{difficulty or 'none'}_{size}").choice(options)


def _candidate_origins(h, w, shape):
    sh = max(r for r, _ in shape) + 1
    sw = max(c for _, c in shape) + 1
    # Reserve row h-2 as a moat above the bottom-row markers.
    return [(r, c) for r in range(0, h - sh - 1) for c in range(0, w - sw + 1)]


def _fits_with_moat(shape, origin, occupied, h, w):
    r0, c0 = origin
    cells = {(r0 + r, c0 + c) for r, c in shape}
    if any(not (0 <= r < h - 1 and 0 <= c < w) for r, c in cells):
        return False
    for r, c in cells:
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if (r + dr, c + dc) in occupied:
                    return False
    return True


def _place_all(ctx, grid, colored_shapes, difficulty):
    """Finite exhaustive backtracking; no capped random retry or silent shrink."""
    h, w = len(grid), len(grid[0])
    occupied = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value}
    ordered = sorted(colored_shapes, key=lambda item: (-len(item[1]), item[0]))
    candidate_lists = []
    for color, shape in ordered:
        candidates = _candidate_origins(h, w, shape)
        ctx.draw_rng(f"place_{difficulty or 'none'}_{color}").shuffle(candidates)
        candidate_lists.append((color, shape, candidates))

    placements = {}

    def search(index):
        if index == len(candidate_lists):
            return True
        color, shape, candidates = candidate_lists[index]
        for origin in candidates:
            if not _fits_with_moat(shape, origin, occupied, h, w):
                continue
            cells = {(origin[0] + r, origin[1] + c) for r, c in shape}
            occupied.update(cells)
            placements[color] = cells
            if search(index + 1):
                return True
            del placements[color]
            occupied.difference_update(cells)
        return False

    if not search(0):
        raise ValueError("declared profile cannot place all objects with a one-cell moat")
    for color, cells in placements.items():
        for r, c in cells:
            grid[r][c] = color


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    if difficulty not in _SCHEDULES:
        raise ValueError("difficulty must be one of None, easy, medium, hard")
    if "layout_profile" in overrides and overrides["layout_profile"] is not None:
        if not isinstance(overrides["layout_profile"], str):
            raise TypeError("layout_profile must be a string")
    if "palette_start" in overrides and overrides["palette_start"] is not None:
        if type(overrides["palette_start"]) is not int:
            raise TypeError("palette_start must be an integer (not bool)")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    if overrides.get("layout_profile") is None:
        scheduled = schedule_profile(seed, sample_index, difficulty)
        layout_profile = ctx.draw_choice("layout_profile", (scheduled,))
    else:
        layout_profile = ctx.draw_choice("layout_profile", _PROFILE_NAMES)
    palette_start = ctx.draw_int_strict("palette_start", 2, 5)

    h, w, marker_cols = _PROFILE_DATA[layout_profile]
    n_objects = len(marker_cols)
    sizes = (3, 4, 5) if n_objects == 3 else (2, 3, 4, 5)
    colors = list(range(palette_start, palette_start + n_objects))
    ctx.draw_rng(f"color_assignment_{difficulty or 'none'}").shuffle(colors)
    colored_shapes = [
        (color, _shape_for(ctx, size, difficulty))
        for color, size in zip(colors, sizes)
    ]

    grid = full_grid(h, w, 0)
    for col in marker_cols:
        grid[h - 1][col] = 1
    _place_all(ctx, grid, colored_shapes, difficulty)
    return grid


def _components4(grid, *, include_markers=True):
    h, w = len(grid), len(grid[0])
    seen = set()
    result = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (not include_markers and color == 1) or (r, c) in seen:
                continue
            queue = deque([(r, c)])
            seen.add((r, c))
            cells = []
            while queue:
                rr, cc = queue.popleft()
                cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen
                            and grid[nr][nc] == color):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            result.append({"color": color, "cells": tuple(sorted(cells))})
    return result


def _bbox_area(component):
    rows = [r for r, _ in component["cells"]]
    cols = [c for _, c in component["cells"]]
    return (max(rows) - min(rows) + 1) * (max(cols) - min(cols) + 1)


def _normalized_component(component):
    return _normalize_shape(component["cells"])


def _arrange(grid, *, key):
    """Python mirror used only for task-local rivals and diagnostics."""
    h, w = len(grid), len(grid[0])
    marker_cols = [c for c, value in enumerate(grid[h - 1]) if value == 1]
    motifs = _components4(grid, include_markers=False)
    if len(motifs) != len(marker_cols):
        raise ValueError("one object is required per marker")
    motifs = sorted(motifs, key=key)

    out = full_grid(h, w, 0)
    for col in marker_cols:
        out[h - 1][col] = 1
    for marker_col, component in zip(marker_cols, motifs):
        shape = _normalized_component(component)
        shape_h = max(r for r, _ in shape) + 1
        top = h - 1 - shape_h
        for dr, dc in shape:
            r, c = top + dr, marker_col + dc
            if not (0 <= r < h - 1 and 0 <= c < w):
                raise ValueError("normalized object clips outside the output grid")
            if out[r][c] != 0:
                raise ValueError("normalized objects collide in the output grid")
            out[r][c] = component["color"]
    return out


def _cell_count_output(grid):
    return _arrange(grid, key=lambda obj: (len(obj["cells"]), obj["color"]))


def _bbox_area_sort(grid):
    """Plausible wrong rule: sort normalized objects by bounding-box area."""
    return _arrange(
        grid,
        key=lambda obj: (_bbox_area(obj), len(obj["cells"]), obj["color"]),
    )


def _has_size_bbox_order_conflict(grid):
    try:
        motifs = _components4(grid, include_markers=False)
        by_size = [obj["color"] for obj in sorted(
            motifs, key=lambda obj: (len(obj["cells"]), obj["color"]))]
        by_box = [obj["color"] for obj in sorted(
            motifs,
            key=lambda obj: (_bbox_area(obj), len(obj["cells"]), obj["color"]),
        )]
        return by_size != by_box
    except Exception:
        return False


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty, meta
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty rectangular grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected a nonempty rectangular grid"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be integer ARC colors 0..9"]

    h = len(grid)
    errors = []
    marker_cells = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row)
                    if value == 1]
    if any(r != h - 1 for r, _ in marker_cells):
        errors.append("all color-1 markers must lie on the bottom row")
    marker_cols = sorted(c for r, c in marker_cells if r == h - 1)
    if not 2 <= len(marker_cols) <= 5:
        errors.append(f"expected 2-5 bottom markers, found {len(marker_cols)}")
    if any(b - a <= 1 for a, b in zip(marker_cols, marker_cols[1:])):
        errors.append("bottom markers must be separated")

    motifs = _components4(grid, include_markers=False)
    if len(motifs) != len(marker_cols):
        errors.append(
            f"expected one colored object per marker, found objects={len(motifs)} "
            f"markers={len(marker_cols)}"
        )
    colors = [obj["color"] for obj in motifs]
    if len(colors) != len(set(colors)):
        errors.append("each object must have a distinct color")
    if any(any(r == h - 1 for r, _ in obj["cells"]) for obj in motifs):
        errors.append("non-marker objects must stay above the marker row")
    sizes = [len(obj["cells"]) for obj in motifs]
    if len(sizes) != len(set(sizes)):
        errors.append(f"object cell counts must be distinct: {sorted(sizes)}")

    if not errors:
        try:
            out = _cell_count_output(grid)
        except ValueError as exc:
            errors.append(str(exc))
        else:
            input_counts = sorted((obj["color"], len(obj["cells"])) for obj in motifs)
            output_objects = _components4(out, include_markers=False)
            output_counts = sorted(
                (obj["color"], len(obj["cells"])) for obj in output_objects
            )
            if input_counts != output_counts:
                errors.append("drop must preserve every object's color and cell count")
    return errors


def strict_canonical_like(grid):
    return self_check(grid)


def observe_overrides(grid):
    errors = self_check(grid)
    if errors:
        raise ValueError("cannot observe malformed grid: " + "; ".join(errors))
    marker_count = sum(value == 1 for value in grid[-1])
    signature = (len(grid), len(grid[0]), marker_count)
    matches = [name for name, (h, w, cols) in _PROFILE_DATA.items()
               if signature == (h, w, len(cols))]
    if len(matches) != 1:
        raise ValueError(f"grid does not identify one layout profile: {signature}")
    object_colors = [obj["color"] for obj in _components4(grid, include_markers=False)]
    return {
        "layout_profile": matches[0],
        "palette_start": min(object_colors),
    }


SEMANTIC_WITNESSES = {
    "cell_count_vs_bbox_area": _has_size_bbox_order_conflict,
}
SEMANTIC_RIVALS = {
    "bbox_area_sort": _bbox_area_sort,
}
WITNESS_RIVALS = {
    "cell_count_vs_bbox_area": ["bbox_area_sort"],
}
CANONICAL_SHORTCUTS = {
    "bbox_area_sort": _bbox_area_sort,
}
LESSON_COMPETITORS = {
    "bbox_area_sort": _bbox_area_sort,
}


def lesson_identifiable(demos, query):
    """Check identifiability against every declared task-local competitor."""
    reasons = []
    for name, rival in LESSON_COMPETITORS.items():
        try:
            survives_demos = all(
                rival(pair["input"]) == pair["output"] for pair in demos
            )
            changes_query = rival(query["input"]) != query["output"]
        except Exception as exc:
            reasons.append(f"competitor {name!r} raised {type(exc).__name__}: {exc}")
            continue
        if survives_demos and changes_query:
            reasons.append(
                f"competitor {name!r} fits every demonstration but changes the query"
            )
    return reasons
