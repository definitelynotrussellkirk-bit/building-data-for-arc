"""Constructive generator for task 3d48e913ef07.

Rule pinned to the selected canonical Racket authority:

* nonzero/non-3 cells in column 0 are a palette, read top to bottom;
* 4-connected color-3 objects are sorted by descending cell area, with
  top-left position as the deterministic tie-break;
* each object is cropped, recolored with the corresponding palette color,
  and the crops are stacked vertically, left aligned, with one blank row.

The sampler constructs the whole grammar directly.  It has no rejection loop,
no fallback that can erase requested controls, and no diagnostic/dead axes.
"""
from __future__ import annotations

from collections import deque
from functools import lru_cache
from itertools import combinations
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "3d48e913ef07"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "4d5171afc86a"

SUMMARY = (
    "Read the distinct first-column colors top to bottom; rank the separated "
    "color-3 components by descending cell area; crop and recolor them in that "
    "palette order; then stack the crops vertically with one blank row."
)

INVARIANTS = [
    "column 0 contains one distinct palette marker per object, read top to bottom",
    "column 1 is blank and color-3 objects occupy columns 2+",
    "there are 3..5 separated color-3 components with distinct areas",
    "generation is constructive for every advertised override combination",
]

AXES = {
    "grid_h": {"type": "int", "default": "linked canonical profile or rng", "valid": "10..18"},
    "grid_w": {"type": "int", "default": "linked canonical profile or rng", "valid": "14..20"},
    "n_objs": {"type": "int", "default": "3 in canonical profiles, 3..5 otherwise", "valid": "3..5"},
}

# Declaring the empty set opts into strict classification: every advertised
# cross-axis tuple is supported, so there are no intentional rejections.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

EXAMPLES_NEEDED = 3
SCHEDULE_PROFILES = (
    "canonical_10x14_6-5-3",
    "canonical_11x15_8-4-3",
    "canonical_12x14_5-4-3",
    "canonical_10x15_8-5-3",
    "broad",
)

_PALETTE_COLORS = (1, 2, 4, 5, 6, 7, 8, 9)
_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))
_CANONICAL_PROFILES = (
    # h, w, descending areas, canonical bbox dimensions by area
    (10, 14, (6, 5, 3), {6: (2, 3), 5: (3, 3), 3: (2, 2)}),
    (11, 15, (8, 4, 3), {8: (3, 3), 4: (2, 3), 3: (2, 2)}),
    (12, 14, (5, 4, 3), {5: (3, 3), 4: (2, 3), 3: (2, 2)}),
    (10, 15, (8, 5, 3), {8: (3, 3), 5: (3, 3), 3: (2, 2)}),
)
_CANONICAL_DIMS = {(h, w) for h, w, _, _ in _CANONICAL_PROFILES}
_MIN_BBOX_AREA = {3: 3, 4: 4, 5: 6, 6: 6, 7: 8, 8: 8}
_MAX_BBOX_AREA = {3: 4, 4: 6, 5: 9, 6: 12, 7: 12, 8: 12}
_AREA_SETS = {
    n: tuple(
        tuple(sorted(values, reverse=True))
        for values in combinations(range(3, 9), n)
        if _MAX_BBOX_AREA[sorted(values, reverse=True)[1]]
        > _MIN_BBOX_AREA[sorted(values, reverse=True)[0]]
    )
    for n in range(3, 6)
}


def schedule_profile(seed: int, sample_index: int, difficulty: Any = None) -> str:
    """Expose the deterministic five-slot teaching schedule to audit tools."""
    del seed, difficulty
    return SCHEDULE_PROFILES[sample_index % len(SCHEDULE_PROFILES)]


def _validate_request(difficulty: Any, overrides: dict[str, Any]) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty {difficulty!r}")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")
    bounds = {"grid_h": (10, 18), "grid_w": (14, 20), "n_objs": (3, 5)}
    for name, value in overrides.items():
        if value is None:
            continue
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError(f"override {name!r} must be an integer, got {value!r}")
        lo, hi = bounds[name]
        if not lo <= value <= hi:
            raise ValueError(f"override {name!r}={value} outside [{lo}, {hi}]")


def _draw_axis(ctx, overrides: dict[str, Any], name: str, domain: tuple[int, ...], default: tuple[int, ...]) -> int:
    options = domain if overrides.get(name) is not None else default
    return ctx.draw_choice(name, options)


def _bbox(cells: tuple[tuple[int, int], ...]) -> tuple[int, int, int, int]:
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    return min(rows), min(cols), max(rows), max(cols)


def _bbox_dims(cells: tuple[tuple[int, int], ...]) -> tuple[int, int]:
    r0, c0, r1, c1 = _bbox(cells)
    return r1 - r0 + 1, c1 - c0 + 1


@lru_cache(maxsize=None)
def _shape_library(area: int) -> tuple[tuple[tuple[int, int], ...], ...]:
    """All normalized connected subsets of a 4x3 slot with ``area`` cells."""
    board = tuple((r, c) for r in range(4) for c in range(3))
    shapes: set[tuple[tuple[int, int], ...]] = set()
    for candidate in combinations(board, area):
        cells = set(candidate)
        seen = {candidate[0]}
        queue = [candidate[0]]
        while queue:
            r, c = queue.pop()
            for dr, dc in _CARDINAL:
                nxt = (r + dr, c + dc)
                if nxt in cells and nxt not in seen:
                    seen.add(nxt)
                    queue.append(nxt)
        if len(seen) != area:
            continue
        r0 = min(r for r, _ in cells)
        c0 = min(c for _, c in cells)
        shapes.add(tuple(sorted((r - r0, c - c0) for r, c in cells)))
    return tuple(sorted(shapes))


def _choose_shape(rng, area: int, *, bbox_dims: tuple[int, int] | None = None, mode: str = "any"):
    candidates = list(_shape_library(area))
    if bbox_dims is not None:
        candidates = [shape for shape in candidates if _bbox_dims(shape) == bbox_dims]
    elif mode in {"compact", "sparse"}:
        bbox_areas = [h * w for h, w in map(_bbox_dims, candidates)]
        target = min(bbox_areas) if mode == "compact" else max(bbox_areas)
        candidates = [shape for shape in candidates if (lambda d: d[0] * d[1])(_bbox_dims(shape)) == target]
    if not candidates:
        raise RuntimeError(f"no connected area-{area} shape for bbox={bbox_dims!r}, mode={mode!r}")
    return rng.choice(candidates)


def _partition(start: int, stop: int, count: int, gap: int = 1) -> tuple[tuple[int, int], ...]:
    content = stop - start - gap * (count - 1)
    base, extra = divmod(content, count)
    sizes = [base + (index < extra) for index in range(count)]
    bands = []
    cursor = start
    for size in sizes:
        bands.append((cursor, cursor + size))
        cursor += size + gap
    return tuple(bands)


def _slots(h: int, w: int) -> tuple[tuple[int, int, int, int], ...]:
    row_bands = _partition(0, h, 2)
    col_bands = _partition(2, w, 3)
    return tuple((r0, r1, c0, c1) for r0, r1 in row_bands for c0, c1 in col_bands)


def _source_area_order(areas: tuple[int, ...], profile_index: int | None, rng) -> tuple[int, ...]:
    # Moving the second-largest object before the largest gives every draw an
    # explicit counterexample to reading/source order.  Profile 3 also needs
    # this order to break the equal-bbox-area tie (8 cells vs 5 cells).
    if profile_index is not None:
        return (areas[1], areas[0], *areas[2:])
    shift = rng.randint(1, len(areas) - 1)
    return areas[shift:] + areas[:shift]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_request(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    slot = sample_index % len(SCHEDULE_PROFILES)
    profile_index = slot if slot < len(_CANONICAL_PROFILES) else None
    profile = _CANONICAL_PROFILES[profile_index] if profile_index is not None else None

    h_default = (profile[0],) if profile else tuple(range(10, 19))
    w_default = (profile[1],) if profile else tuple(range(14, 21))
    h = _draw_axis(ctx, overrides, "grid_h", tuple(range(10, 19)), h_default)
    w = _draw_axis(ctx, overrides, "grid_w", tuple(range(14, 21)), w_default)

    if profile is not None:
        n_default = (3,)
    else:
        n_default = {
            "easy": (3, 3, 4),
            "medium": (3, 4, 4, 5),
            "hard": (3, 4, 5, 5),
            None: (3, 4, 5),
        }[difficulty]
    n_objs = _draw_axis(ctx, overrides, "n_objs", (3, 4, 5), n_default)

    rng = ctx.draw_rng("constructive_layout")
    active_profile = profile_index if profile is not None and n_objs == 3 else None
    if active_profile is not None:
        areas = profile[2]
        bbox_targets = profile[3]
    else:
        areas = rng.choice(_AREA_SETS[n_objs])
        bbox_targets = {}

    source_areas = _source_area_order(areas, active_profile, rng)
    selected_slots = sorted(rng.sample(_slots(h, w), n_objs), key=lambda box: (box[0], box[2]))

    shape_by_area: dict[int, tuple[tuple[int, int], ...]] = {}
    if active_profile is not None:
        for area in areas:
            shape_by_area[area] = _choose_shape(rng, area, bbox_dims=bbox_targets[area])
    else:
        shape_by_area[areas[0]] = _choose_shape(rng, areas[0], mode="compact")
        shape_by_area[areas[1]] = _choose_shape(rng, areas[1], mode="sparse")
        for area in areas[2:]:
            shape_by_area[area] = _choose_shape(rng, area)

    grid = full_grid(h, w, 0)

    marker_rows = sorted(rng.sample(range(h), n_objs))
    marker_colors = list(rng.sample(_PALETTE_COLORS, n_objs))
    if marker_colors == sorted(marker_colors):
        marker_colors[0], marker_colors[1] = marker_colors[1], marker_colors[0]
    for row, color in zip(marker_rows, marker_colors):
        grid[row][0] = color

    for area, (r0, r1, c0, c1) in zip(source_areas, selected_slots):
        shape = shape_by_area[area]
        shape_h, shape_w = _bbox_dims(shape)
        if shape_h > r1 - r0 or shape_w > c1 - c0:
            raise RuntimeError("constructive slot invariant violated")
        # Top-align within each row band so component reading order is exactly
        # the selected slot order; horizontal jitter remains fully deterministic.
        col = c0 + rng.randint(0, c1 - c0 - shape_w)
        for dr, dc in shape:
            grid[r0 + dr][col + dc] = 3

    errors = self_check(grid)
    if errors:
        raise RuntimeError(f"constructed invalid grid: {errors}")
    return grid


def _coerce_rectangular_grid(grid: Any) -> tuple[list[list[int]] | None, list[str]]:
    if not isinstance(grid, list) or not grid:
        return None, ["grid must be a nonempty list of rows"]
    if not all(isinstance(row, list) and row for row in grid):
        return None, ["every row must be a nonempty list"]
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return None, ["grid is ragged"]
    errors = []
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                errors.append(f"cell ({r},{c}) is not an integer color 0..9")
                return None, errors
    return grid, errors


def _components(grid: list[list[int]], color: int = 3) -> list[tuple[tuple[int, int], ...]]:
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != color or (r, c) in seen:
                continue
            queue = deque([(r, c)])
            seen.add((r, c))
            cells = []
            while queue:
                rr, cc = queue.popleft()
                cells.append((rr, cc))
                for dr, dc in _CARDINAL:
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and grid[nr][nc] == color and (nr, nc) not in seen:
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            result.append(tuple(sorted(cells)))
    return result


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Return concrete structural/semantic diagnostics for the lawful domain."""
    del difficulty, meta
    grid, errors = _coerce_rectangular_grid(grid)
    if errors:
        return errors
    assert grid is not None
    h, w = len(grid), len(grid[0])
    if not 10 <= h <= 18:
        errors.append(f"grid height {h} outside 10..18")
    if not 14 <= w <= 20:
        errors.append(f"grid width {w} outside 14..20")
    if w < 2:
        return errors + ["grid has no reserved column 1"]

    if any(row[1] != 0 for row in grid):
        errors.append("reserved column 1 must be blank")
    if any(row[0] == 3 for row in grid):
        errors.append("color 3 may not occur in palette column 0")
    if any(grid[r][c] not in (0, 3) for r in range(h) for c in range(1, w)):
        errors.append("colors other than 0 and 3 may occur only in column 0")

    markers = [row[0] for row in grid if row[0] not in (0, 3)]
    if not 3 <= len(markers) <= 5:
        errors.append(f"expected 3..5 palette markers, found {len(markers)}")
    if len(markers) != len(set(markers)):
        errors.append("palette marker colors must be distinct")

    comps = _components(grid)
    if len(comps) != len(markers):
        errors.append(f"palette/object count mismatch: {len(markers)} markers vs {len(comps)} objects")
    areas = [len(cells) for cells in comps]
    if len(areas) != len(set(areas)):
        errors.append("object areas must be distinct")
    for index, cells in enumerate(comps):
        if not 3 <= len(cells) <= 8:
            errors.append(f"object {index} area {len(cells)} outside 3..8")
        bh, bw = _bbox_dims(cells)
        if bh > 4 or bw > 3:
            errors.append(f"object {index} bbox {bh}x{bw} exceeds 4x3")
    return errors


def observe_overrides(grid) -> dict[str, int]:
    checked, errors = _coerce_rectangular_grid(grid)
    if errors or checked is None:
        raise ValueError(errors[0] if errors else "invalid grid")
    return {
        "grid_h": len(checked),
        "grid_w": len(checked[0]),
        "n_objs": len(_components(checked)),
    }


def strict_canonical_like(grid) -> list[str]:
    errors = self_check(grid)
    if errors:
        return errors
    assert isinstance(grid, list)
    dims = (len(grid), len(grid[0]))
    areas = tuple(sorted((len(cells) for cells in _components(grid)), reverse=True))
    bboxes = {len(cells): _bbox_dims(cells) for cells in _components(grid)}
    for h, w, expected_areas, expected_bboxes in _CANONICAL_PROFILES:
        if dims == (h, w) and areas == expected_areas and all(bboxes[a] == expected_bboxes[a] for a in expected_areas):
            return []
    return [f"grid profile {(dims, areas, bboxes)!r} is outside the four linked canonical profiles"]


def _crop(cells: tuple[tuple[int, int], ...], color: int) -> list[list[int]]:
    r0, c0, r1, c1 = _bbox(cells)
    result = [[0] * (c1 - c0 + 1) for _ in range(r1 - r0 + 1)]
    for r, c in cells:
        result[r - r0][c - c0] = color
    return result


def _packed(grid, *, object_order: str = "area", palette_order: str = "row") -> list[list[int]]:
    markers = [(r, row[0]) for r, row in enumerate(grid) if row[0] not in (0, 3)]
    colors = [color for _, color in markers]
    if palette_order == "numeric":
        colors = sorted(colors)
    elif palette_order != "row":
        raise ValueError(f"unknown palette order {palette_order!r}")

    comps = _components(grid)
    if object_order == "area":
        comps.sort(key=lambda cells: (-len(cells), _bbox(cells)[0], _bbox(cells)[1]))
    elif object_order == "source":
        comps.sort(key=lambda cells: (_bbox(cells)[0], _bbox(cells)[1]))
    elif object_order == "ascending_area":
        comps.sort(key=lambda cells: (len(cells), _bbox(cells)[0], _bbox(cells)[1]))
    elif object_order == "bbox_area":
        comps.sort(
            key=lambda cells: (
                -((_bbox(cells)[2] - _bbox(cells)[0] + 1) * (_bbox(cells)[3] - _bbox(cells)[1] + 1)),
                _bbox(cells)[0],
                _bbox(cells)[1],
            )
        )
    elif object_order == "bbox_width":
        comps.sort(
            key=lambda cells: (
                -(_bbox(cells)[3] - _bbox(cells)[1] + 1),
                _bbox(cells)[0],
                _bbox(cells)[1],
            )
        )
    else:
        raise ValueError(f"unknown object order {object_order!r}")

    pieces = [_crop(cells, color) for cells, color in zip(comps, colors)]
    if not pieces:
        return [[0]]
    width = max(len(piece[0]) for piece in pieces)
    height = sum(len(piece) for piece in pieces) + len(pieces) - 1
    result = [[0] * width for _ in range(height)]
    top = 0
    for piece in pieces:
        for row_index, row in enumerate(piece):
            result[top + row_index][: len(row)] = row
        top += len(piece) + 1
    return result


def rule_mirror(grid) -> list[list[int]]:
    """Transparent Python mirror used only by validators and audit hooks."""
    return _packed(grid)


def _rival_source_order(grid):
    return _packed(grid, object_order="source")


def _rival_ascending_area(grid):
    return _packed(grid, object_order="ascending_area")


def _rival_bbox_area(grid):
    return _packed(grid, object_order="bbox_area")


def _rival_bbox_width(grid):
    return _packed(grid, object_order="bbox_width")


def _rival_numeric_palette(grid):
    return _packed(grid, palette_order="numeric")


SEMANTIC_RIVALS: dict[str, Callable[[Any], list[list[int]]]] = {
    "source_order": _rival_source_order,
    "ascending_area": _rival_ascending_area,
    "bbox_area": _rival_bbox_area,
    "bbox_width": _rival_bbox_width,
    "numeric_palette": _rival_numeric_palette,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)

# The public components' bbox widths happen to rank exactly like their cell
# areas (ties break by source position), so this plausible wrong rule fits all
# four public pairs.  Generated equal-width reversals explicitly refute it.
CANONICAL_SHORTCUTS: dict[str, Callable[[Any], list[list[int]]]] = {
    "bbox_width": _rival_bbox_width,
}


def _disagrees(name: str, grid: Any) -> bool:
    return not self_check(grid) and SEMANTIC_RIVALS[name](grid) != rule_mirror(grid)


SEMANTIC_WITNESSES = {
    name: (lambda grid, rival_name=name: _disagrees(rival_name, grid))
    for name in SEMANTIC_RIVALS
}
WITNESS_RIVALS = {name: [name] for name in SEMANTIC_RIVALS}


def lesson_identifiable(demos, query) -> list[str]:
    """Check a three-demo lesson against every declared executable rival."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]
    reasons: list[str] = []
    valid_demos = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        structural = self_check(pair["input"])
        if structural:
            reasons.append(f"demo {index} input is outside the teaching grammar: {structural[0]}")
            continue
        if pair["output"] != rule_mirror(pair["input"]):
            reasons.append(f"demo {index} output disagrees with the area/palette packing rule")
            continue
        valid_demos.append(pair)

    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        reasons.append("query must contain input and output grids")
    elif self_check(query["input"]):
        reasons.append("query input is outside the teaching grammar")
    elif query["output"] != rule_mirror(query["input"]):
        reasons.append("query output disagrees with the area/palette packing rule")

    if reasons:
        return reasons
    for name, rival in LESSON_COMPETITORS.items():
        survives = all(rival(pair["input"]) == pair["output"] for pair in valid_demos)
        if survives and rival(query["input"]) != query["output"]:
            reasons.append(f"named competitor survives all demonstrations: {name}")
    return reasons
