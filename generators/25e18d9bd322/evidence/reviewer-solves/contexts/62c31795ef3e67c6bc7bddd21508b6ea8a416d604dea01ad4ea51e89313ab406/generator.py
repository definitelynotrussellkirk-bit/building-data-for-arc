"""Generator for ARC task 25e18d9bd322 — crop the object nearest marker 9.

A zero-background grid contains one singleton color-9 control marker and three
or four monochrome 4-connected candidate objects.  Remove the marker, rank each
candidate by the Manhattan distance of its nearest cell to the marker, and break
distance ties by the candidate bounding box's top row and then left column.  The
answer is the selected object cropped to its tight bounding box.

The three-sample default curriculum has one exact linked canonical-profile
anchor, one nearest-cell versus object-origin/centroid counterexample, and one
legal distance-tie example.  Consequently every consecutive three-example
lesson contains canonical support plus a generated counterexample to the
strongest public-demonstration shortcut.
"""
from __future__ import annotations

from collections import deque
from typing import Any, Callable, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "25e18d9bd322"
TASK_ID = GENERATOR_ID
VERSION = "3.1.0"
RULE_HASH = "f275e1e6250c"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.25

SUMMARY = (
    "A 0-background grid contains one color-9 control marker and 3 or 4 "
    "monochrome objects. Ignore the marker. Select the object whose nearest "
    "cell has minimum Manhattan distance to the marker; break distance ties "
    "by bbox top row, then bbox left column. Output that object cropped to its "
    "tight bbox. Every third default draw is a linked canonical-profile anchor, "
    "and the intervening draws explicitly rebut object-origin, centroid, fixed-"
    "shape, reading-order, size, and color-rank shortcuts."
)

INVARIANTS = [
    "background is 0 and all cells are ARC colors 0..9",
    "exactly one color-9 marker exists",
    "there are 3..4 candidate components, each with 2..5 cells",
    "candidate colors are either all shared or all distinct",
    "distance ties are legal and use bbox row/column tie-breaking",
    "every third ordinary sample matches a linked canonical input profile",
    "every sequential three-demo lesson rebuts all declared competitors",
]

_COLOR_MODES = ("shared", "distinct")
AXES = {
    "grid_h": {
        "type": "int",
        "default": "canonical schedule or difficulty band",
        "valid": "8..14",
    },
    "grid_w": {
        "type": "int",
        "default": "canonical schedule or difficulty band",
        "valid": "9..14",
    },
    "n_blobs": {
        "type": "int",
        "default": "3 on anchors, 4 on counterexample scenes",
        "valid": "3..4",
    },
    "color_mode": {
        "type": "str",
        "default": "shared on anchors, distinct on counterexamples",
        "valid": "shared|distinct",
    },
}

_DIRS4 = ((-1, 0), (1, 0), (0, -1), (0, 1))

# Exact canonical-profile geometry, represented as marker + candidate cells.
# Colors are deliberately assigned at generation time.
_ANCHORS = (
    {
        "h": 9,
        "w": 10,
        "marker": (3, 4),
        "blobs": (
            ((1, 1), (1, 2), (2, 1)),
            ((4, 6), (5, 6), (5, 7)),
            ((7, 2), (7, 3)),
        ),
    },
    {
        "h": 8,
        "w": 9,
        "marker": (4, 6),
        "blobs": (
            ((1, 6), (2, 6), (2, 7)),
            ((3, 4), (3, 5)),
            ((5, 1), (6, 1), (6, 2)),
        ),
    },
    {
        "h": 9,
        "w": 9,
        "marker": (5, 7),
        "blobs": (
            ((1, 1), (2, 1), (2, 2)),
            ((3, 7), (4, 7)),
            ((6, 5), (6, 6), (7, 5)),
        ),
    },
)

# Base 8x9 nearest-cell counterexamples.  Every target below either has a
# strictly closer cell than the distractors or wins a legal nearest-distance
# tie by bbox row/column.  In all cases, object-origin and centroid distance
# select the compact top distractor instead.  Multiple target masks prevent a
# model from replacing the selection rule with a memorized output silhouette.
_DISTANCE_TARGETS = (
    ((0, 1), (1, 1), (2, 1), (2, 2)),
    ((0, 1), (1, 1), (2, 1), (3, 1)),
    ((1, 1), (2, 1), (2, 2), (3, 2)),
    ((2, 0), (2, 1), (2, 2), (3, 2)),
    ((2, 0), (2, 1), (3, 1), (3, 2)),
    ((2, 0), (3, 0), (3, 1), (3, 2)),
    ((0, 0), (0, 1), (1, 1), (2, 1), (2, 2)),
    ((0, 0), (0, 1), (1, 1), (2, 1), (3, 1)),
    ((0, 0), (1, 0), (1, 1), (2, 1), (2, 2)),
    ((0, 0), (1, 0), (1, 1), (2, 1), (3, 1)),
    ((0, 0), (1, 0), (2, 0), (2, 1), (2, 2)),
    ((0, 0), (1, 0), (2, 0), (2, 1), (3, 1)),
    ((0, 0), (1, 0), (2, 0), (3, 0), (3, 1)),
    ((0, 1), (1, 0), (1, 1), (2, 1), (2, 2)),
    ((0, 1), (1, 0), (1, 1), (2, 1), (3, 1)),
    ((0, 1), (1, 1), (2, 0), (2, 1), (2, 2)),
    ((0, 1), (1, 1), (2, 0), (2, 1), (3, 1)),
    ((0, 1), (1, 1), (2, 1), (2, 2), (3, 1)),
    ((0, 1), (1, 1), (2, 1), (3, 0), (3, 1)),
    ((1, 0), (1, 1), (2, 1), (2, 2), (3, 2)),
    ((1, 0), (2, 0), (2, 1), (2, 2), (3, 2)),
    ((1, 1), (2, 0), (2, 1), (2, 2), (3, 2)),
    ((1, 1), (2, 1), (2, 2), (3, 1), (3, 2)),
    ((2, 0), (2, 1), (2, 2), (3, 0), (3, 2)),
    ((2, 0), (2, 1), (2, 2), (3, 1), (3, 2)),
    ((2, 0), (2, 1), (3, 0), (3, 1), (3, 2)),
    ((2, 0), (2, 2), (3, 0), (3, 1), (3, 2)),
)
_DISTANCE_DISTRACTORS = (
    ((0, 3), (0, 4), (1, 3)),
    ((6, 7), (6, 8), (7, 7)),
    ((6, 0), (7, 0)),
)
_DISTANCE_MARKER = (4, 4)
_DISTANCE_FLIPS = tuple(((False, False),) for _ in _DISTANCE_TARGETS)

# Base 8x9 scene with a legal nearest-distance tie.  Objects 0 and 1 are both
# distance two from the marker; object 0 wins because its bbox starts higher.
_TIE_SCENE = {
    "marker": (4, 4),
    "blobs": (
        ((1, 4), (2, 4)),
        ((4, 1), (4, 2)),
        ((6, 7), (7, 7), (7, 8)),
        ((0, 0), (0, 1), (1, 0)),
    ),
}


def _band(difficulty: Any) -> str:
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return difficulty
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def _validate_grid(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a nonempty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["rows must be nonempty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["cells must be integer ARC colors 0..9"]
    return []


def _components(grid: list[list[int]]) -> list[dict[str, Any]]:
    """Monochrome 4-connected components, matching the selected Racket prelude."""
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    components: list[dict[str, Any]] = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color in (0, 9) or (r, c) in seen:
                continue
            queue = deque([(r, c)])
            seen.add((r, c))
            cells: list[tuple[int, int]] = []
            while queue:
                rr, cc = queue.popleft()
                cells.append((rr, cc))
                for dr, dc in _DIRS4:
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            cells.sort()
            rows = [rr for rr, _ in cells]
            cols = [cc for _, cc in cells]
            components.append(
                {
                    "color": color,
                    "cells": tuple(cells),
                    "bbox": (min(rows), min(cols), max(rows), max(cols)),
                    "size": len(cells),
                    "key": cells[0],
                }
            )
    components.sort(key=lambda obj: obj["key"])
    return components


def _distance(marker: tuple[int, int], obj: dict[str, Any]) -> int:
    mr, mc = marker
    return min(abs(mr - r) + abs(mc - c) for r, c in obj["cells"])


def _mean_distance(marker: tuple[int, int], obj: dict[str, Any]) -> float:
    mr, mc = marker
    return sum(abs(mr - r) + abs(mc - c) for r, c in obj["cells"]) / obj["size"]


def _winner_key(marker: tuple[int, int], obj: dict[str, Any]) -> tuple[int, int, int]:
    r1, c1, _r2, _c2 = obj["bbox"]
    return (_distance(marker, obj), r1, c1)


def _crop(grid: list[list[int]], obj: dict[str, Any]) -> list[list[int]]:
    r1, c1, r2, c2 = obj["bbox"]
    out = full_grid(r2 - r1 + 1, c2 - c1 + 1, 0)
    for r, c in obj["cells"]:
        out[r - r1][c - c1] = grid[r][c]
    return out


def _analyze(grid: Any) -> dict[str, Any]:
    errors = _validate_grid(grid)
    if errors:
        return {"errors": errors}
    normalized = [list(row) for row in grid]
    h, w = len(normalized), len(normalized[0])
    markers = [
        (r, c)
        for r, row in enumerate(normalized)
        for c, value in enumerate(row)
        if value == 9
    ]
    candidates = _components(normalized)

    if not (8 <= h <= 14 and 9 <= w <= 14):
        errors.append(f"dims {h}x{w} outside declared envelope 8..14 x 9..14")
    if len(markers) != 1:
        errors.append(f"expected exactly one marker-9, found {len(markers)}")
    if not (3 <= len(candidates) <= 4):
        errors.append(f"expected 3..4 candidate blobs, found {len(candidates)}")
    for obj in candidates:
        if not (2 <= obj["size"] <= 5):
            errors.append(f"candidate size {obj['size']} outside 2..5")

    colors = [obj["color"] for obj in candidates]
    color_mode = None
    if candidates:
        if len(set(colors)) == 1:
            color_mode = "shared"
        elif len(set(colors)) == len(colors):
            color_mode = "distinct"
        else:
            errors.append("candidate colors must be all shared or all distinct")

    marker = markers[0] if len(markers) == 1 else None
    best = min(candidates, key=lambda obj: _winner_key(marker, obj)) if marker and candidates else None
    return {
        "errors": errors,
        "grid": normalized,
        "height": h,
        "width": w,
        "marker": marker,
        "candidates": candidates,
        "best": best,
        "color_mode": color_mode,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the intended rule domain; legal marker contact and ties remain valid."""
    return list(_analyze(grid)["errors"])


def strict_canonical_like(grid) -> list[str]:
    """Linked canonical manifold, allowing a shared-color relabeling."""
    analysis = _analyze(grid)
    reasons = list(analysis["errors"])
    if reasons:
        return reasons
    candidates = analysis["candidates"]
    sizes = tuple(sorted(obj["size"] for obj in candidates))
    bbox_dims = tuple(
        sorted(
            (
                obj["bbox"][2] - obj["bbox"][0] + 1,
                obj["bbox"][3] - obj["bbox"][1] + 1,
            )
            for obj in candidates
        )
    )
    profile = (
        analysis["height"],
        analysis["width"],
        len(candidates),
        analysis["color_mode"],
        sizes,
        bbox_dims,
    )
    lawful = {
        (8, 9, 3, "shared", (2, 3, 3), ((1, 2), (2, 2), (2, 2))),
        (9, 9, 3, "shared", (2, 3, 3), ((2, 1), (2, 2), (2, 2))),
        (9, 10, 3, "shared", (2, 3, 3), ((1, 2), (2, 2), (2, 2))),
    }
    if profile not in lawful:
        reasons.append(
            "linked dimensions/count/color/sizes/bboxes do not match a canonical train/test profile"
        )
    return reasons


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Small test-only mirror of the selected Racket rule; not output authority."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return _crop(analysis["grid"], analysis["best"])


def observe_overrides(grid) -> dict[str, Any]:
    """Recover every advertised exact control from the realized input."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return {
        "grid_h": analysis["height"],
        "grid_w": analysis["width"],
        "n_blobs": len(analysis["candidates"]),
        "color_mode": analysis["color_mode"],
    }


def _draw_axis_int(ctx, label: str, lo: int, hi: int, default_lo: int, default_hi: int) -> int:
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_int(label, lo, hi)
    return ctx.draw_int(label, default_lo, default_hi)


def _draw_axis_choice(ctx, label: str, options: tuple[str, ...], default: str) -> str:
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_choice(label, options)
    return ctx.draw_choice(label, (default,))


def _translate_cells(
    cells: Iterable[tuple[int, int]], row_offset: int, col_offset: int
) -> tuple[tuple[int, int], ...]:
    return tuple((r + row_offset, c + col_offset) for r, c in cells)


def _transform_scene(
    marker: tuple[int, int],
    blobs: tuple[tuple[tuple[int, int], ...], ...],
    h: int,
    w: int,
    *,
    flip_rows: bool,
    flip_cols: bool,
) -> tuple[tuple[int, int], tuple[tuple[tuple[int, int], ...], ...]]:
    def transform(cell: tuple[int, int]) -> tuple[int, int]:
        r, c = cell
        if flip_rows:
            r = h - 1 - r
        if flip_cols:
            c = w - 1 - c
        return r, c

    return transform(marker), tuple(
        tuple(transform(cell) for cell in cells) for cells in blobs
    )


def _winner_blob_index(
    marker: tuple[int, int], blobs: tuple[tuple[tuple[int, int], ...], ...]
) -> int:
    mr, mc = marker

    def key(index: int) -> tuple[int, int, int]:
        cells = blobs[index]
        return (
            min(abs(mr - r) + abs(mc - c) for r, c in cells),
            min(r for r, _ in cells),
            min(c for _, c in cells),
        )

    return min(range(len(blobs)), key=key)


def _paint_scene(
    h: int,
    w: int,
    marker: tuple[int, int],
    blobs: tuple[tuple[tuple[int, int], ...], ...],
    colors: list[int],
) -> list[list[int]]:
    grid = full_grid(h, w, 0)
    grid[marker[0]][marker[1]] = 9
    for cells, color in zip(blobs, colors):
        for r, c in cells:
            if grid[r][c] != 0:
                raise AssertionError(f"scene overlap at {(r, c)}")
            grid[r][c] = color
    return grid


def _candidate_colors(
    n: int, color_mode: str, role: str, rng, *, target_index: int = 0
) -> list[int]:
    if color_mode == "shared":
        return [rng.choice(tuple(range(1, 9)))] * n

    # Keep the intended winner at an extreme color so each lesson refutes one
    # color-rank shortcut, but draw that extreme uniformly from every feasible
    # ARC color instead of using the heavily skewed min/max of a random sample.
    # This preserves the semantic witness while avoiding accidental output-
    # color collapse (for four blobs, sample maxima are usually 7 or 8).
    if role == "distance":
        target = rng.choice(tuple(range(n, 9)))
        rest = rng.sample(tuple(range(1, target)), n - 1)
    else:
        target = rng.choice(tuple(range(1, 10 - n)))
        rest = rng.sample(tuple(range(target + 1, 9)), n - 1)
    rng.shuffle(rest)
    assigned: list[int | None] = [None] * n
    assigned[target_index] = target
    remaining = iter(rest)
    for index in range(n):
        if assigned[index] is None:
            assigned[index] = next(remaining)
    return [int(color) for color in assigned]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)}")

    band = _band(difficulty)
    phase = int(seed) + int(sample_index)
    anchor = not overrides and phase % 3 == 0
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    layout_rng = ctx.draw_rng("layout")
    palette_rng = ctx.draw_rng("palette")

    if anchor:
        template = _ANCHORS[(phase // 3) % len(_ANCHORS)]
        h = _draw_axis_int(ctx, "grid_h", 8, 14, template["h"], template["h"])
        w = _draw_axis_int(ctx, "grid_w", 9, 14, template["w"], template["w"])
        n_blobs = _draw_axis_int(ctx, "n_blobs", 3, 4, 3, 3)
        color_mode = _draw_axis_choice(ctx, "color_mode", _COLOR_MODES, "shared")
        marker, blobs = _transform_scene(
            template["marker"],
            template["blobs"],
            h,
            w,
            flip_rows=bool(layout_rng.randrange(2)),
            flip_cols=bool(layout_rng.randrange(2)),
        )
        colors = _candidate_colors(n_blobs, color_mode, "anchor", palette_rng)
    else:
        defaults = {
            "easy": (8, 9, 9, 10),
            "medium": (9, 12, 10, 13),
            "hard": (12, 14, 12, 14),
        }[band]
        h = _draw_axis_int(ctx, "grid_h", 8, 14, defaults[0], defaults[1])
        w = _draw_axis_int(ctx, "grid_w", 9, 14, defaults[2], defaults[3])
        role = "distance" if phase % 3 in (0, 1) else "tie"
        default_n = 4
        n_blobs = _draw_axis_int(ctx, "n_blobs", 3, 4, default_n, default_n)
        color_mode = _draw_axis_choice(ctx, "color_mode", _COLOR_MODES, "distinct")
        if role == "distance":
            target_index_in_catalog = layout_rng.randrange(len(_DISTANCE_TARGETS))
            target_cells = _DISTANCE_TARGETS[target_index_in_catalog]
            source_blobs = (target_cells, *_DISTANCE_DISTRACTORS[: n_blobs - 1])
            variants = _DISTANCE_FLIPS[target_index_in_catalog]
            source_marker = _DISTANCE_MARKER
        else:
            source_blobs = _TIE_SCENE["blobs"][:n_blobs]
            variants = ((False, False), (False, True), (True, False), (True, True))
            source_marker = _TIE_SCENE["marker"]
        flip_rows, flip_cols = layout_rng.choice(variants)
        base_marker, base_blobs = _transform_scene(
            source_marker,
            source_blobs,
            8,
            9,
            flip_rows=flip_rows,
            flip_cols=flip_cols,
        )
        row_offset = layout_rng.randint(0, h - 8)
        col_offset = layout_rng.randint(0, w - 9)
        marker = (base_marker[0] + row_offset, base_marker[1] + col_offset)
        blobs = tuple(
            _translate_cells(cells, row_offset, col_offset) for cells in base_blobs
        )
        target_index = _winner_blob_index(marker, blobs)
        colors = _candidate_colors(
            n_blobs, color_mode, role, palette_rng, target_index=target_index
        )

    grid = _paint_scene(h, w, marker, blobs, colors)
    errors = self_check(grid, difficulty=band)
    if errors:
        raise AssertionError("generated invalid nearest-marker lesson: " + "; ".join(errors))
    expected = {
        "grid_h": h,
        "grid_w": w,
        "n_blobs": n_blobs,
        "color_mode": color_mode,
    }
    observed = observe_overrides(grid)
    if observed != expected:
        raise AssertionError(f"axis realization drift: expected {expected}, observed {observed}")
    return grid


def _valid_analysis(grid) -> dict[str, Any] | None:
    analysis = _analyze(grid)
    return None if analysis["errors"] else analysis


def _crop_choice(grid, chooser: Callable[[dict[str, Any]], dict[str, Any] | None]):
    analysis = _valid_analysis(grid)
    if analysis is None:
        return None
    chosen = chooser(analysis)
    return None if chosen is None else _crop(analysis["grid"], chosen)


def _rival_first_candidate(grid):
    return _crop_choice(grid, lambda a: min(a["candidates"], key=lambda obj: obj["key"]))


def _rival_last_candidate(grid):
    return _crop_choice(grid, lambda a: max(a["candidates"], key=lambda obj: obj["key"]))


def _rival_smallest_candidate(grid):
    return _crop_choice(
        grid, lambda a: min(a["candidates"], key=lambda obj: (obj["size"], obj["key"]))
    )


def _rival_largest_candidate(grid):
    return _crop_choice(
        grid, lambda a: min(a["candidates"], key=lambda obj: (-obj["size"], obj["key"]))
    )


def _rival_lowest_color(grid):
    return _crop_choice(
        grid, lambda a: min(a["candidates"], key=lambda obj: (obj["color"], obj["key"]))
    )


def _rival_highest_color(grid):
    return _crop_choice(
        grid, lambda a: min(a["candidates"], key=lambda obj: (-obj["color"], obj["key"]))
    )


def _rival_bbox_origin_distance(grid):
    return _crop_choice(
        grid,
        lambda a: min(
            a["candidates"],
            key=lambda obj: (
                abs(a["marker"][0] - obj["bbox"][0])
                + abs(a["marker"][1] - obj["bbox"][1]),
                obj["bbox"][0],
                obj["bbox"][1],
            ),
        ),
    )


def _rival_centroid_distance(grid):
    return _crop_choice(
        grid,
        lambda a: min(
            a["candidates"],
            key=lambda obj: (
                _mean_distance(a["marker"], obj),
                obj["bbox"][0],
                obj["bbox"][1],
            ),
        ),
    )


def _rival_fixed_l_tromino(grid):
    analysis = _valid_analysis(grid)
    if analysis is None:
        return None
    color = analysis["best"]["color"]
    return [[color, 0], [color, color]]


def _disagrees(grid, rival: Callable) -> bool:
    analysis = _valid_analysis(grid)
    return bool(analysis and rival(grid) != _crop(analysis["grid"], analysis["best"]))


FEATURE_WITNESSES = {
    "canonical_profile_anchor": lambda grid: strict_canonical_like(grid) == [],
    "legal_distance_tie": lambda grid: bool(
        (analysis := _valid_analysis(grid))
        and sum(
            _distance(analysis["marker"], obj)
            == _distance(analysis["marker"], analysis["best"])
            for obj in analysis["candidates"]
        )
        >= 2
    ),
}

# This registry is deliberately limited to executable disagreements with named
# rivals.  Feature-presence checks live in FEATURE_WITNESSES so the semantic
# gate never mistakes "this case exists" for "this rival is refuted here."
SEMANTIC_WITNESSES = {
    "reading_order_first_rebutted": lambda grid: _disagrees(grid, _rival_first_candidate),
    "reading_order_last_rebutted": lambda grid: _disagrees(grid, _rival_last_candidate),
    "smallest_candidate_rebutted": lambda grid: _disagrees(grid, _rival_smallest_candidate),
    "largest_candidate_rebutted": lambda grid: _disagrees(grid, _rival_largest_candidate),
    "lowest_color_rebutted": lambda grid: _disagrees(grid, _rival_lowest_color),
    "highest_color_rebutted": lambda grid: _disagrees(grid, _rival_highest_color),
    "bbox_origin_distance_rebutted": lambda grid: _disagrees(grid, _rival_bbox_origin_distance),
    "centroid_distance_rebutted": lambda grid: _disagrees(grid, _rival_centroid_distance),
    "fixed_l_tromino_rebutted": lambda grid: _disagrees(grid, _rival_fixed_l_tromino),
}

SEMANTIC_RIVALS = {
    "first_candidate": _rival_first_candidate,
    "last_candidate": _rival_last_candidate,
    "smallest_candidate": _rival_smallest_candidate,
    "largest_candidate": _rival_largest_candidate,
    "lowest_color": _rival_lowest_color,
    "highest_color": _rival_highest_color,
    "bbox_origin_distance": _rival_bbox_origin_distance,
    "centroid_distance": _rival_centroid_distance,
    "fixed_l_tromino": _rival_fixed_l_tromino,
}

WITNESS_RIVALS = {
    "reading_order_first_rebutted": ["first_candidate"],
    "reading_order_last_rebutted": ["last_candidate"],
    "smallest_candidate_rebutted": ["smallest_candidate"],
    "largest_candidate_rebutted": ["largest_candidate"],
    "lowest_color_rebutted": ["lowest_color"],
    "highest_color_rebutted": ["highest_color"],
    "bbox_origin_distance_rebutted": ["bbox_origin_distance"],
    "centroid_distance_rebutted": ["centroid_distance"],
    "fixed_l_tromino_rebutted": ["fixed_l_tromino"],
}

LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    "bbox_origin_distance": _rival_bbox_origin_distance,
    "fixed_l_tromino": _rival_fixed_l_tromino,
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject a lesson if a declared plausible rival survives all demos."""
    reasons: list[str] = []
    for index, demo in enumerate(demos):
        try:
            expected = rule_mirror(demo["input"])
        except (KeyError, ValueError) as exc:
            reasons.append(f"demo {index} is outside the rule domain: {exc}")
            continue
        if demo.get("output") != expected:
            reasons.append(f"demo {index} output disagrees with nearest-cell crop rule")
    try:
        query_answer = rule_mirror(query["input"])
    except (KeyError, ValueError) as exc:
        reasons.append(f"query is outside the rule domain: {exc}")
        return reasons

    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(competitor(demo["input"]) == demo.get("output") for demo in demos)
        if survives and competitor(query["input"]) != query_answer:
            reasons.append(
                f"competing rule '{name}' fits every demo but answers the query differently"
            )
    return reasons
