"""Curriculum generator for ARC task ``68a312813b77``.

For each 8-connected nonzero object, the selected rule fills background cells
inside that object's bounding box with color 7 while preserving object cells.

Version 2.1.0 clamped every object one cell away from the canvas boundary, so a
wrong rule that skipped edge-touching objects solved every generated example.
Version 2.3.0 places exact, separated object bboxes with both a boundary object
and an interior object in every default scene, using cached constructive layouts
so every valid single-axis control remains realizable without exponential search.
"""
from __future__ import annotations

from collections.abc import Callable, Sequence
from copy import deepcopy
from functools import lru_cache
from itertools import permutations
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

Grid = list[list[int]]
Cell = tuple[int, int]
Box = tuple[int, int, int, int]

GENERATOR_ID = "68a312813b77"
TASK_ID = GENERATOR_ID
VERSION = "2.3.0"
RULE_HASH = "0515ffa9320e"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0
SUMMARY = (
    "Generate separated, non-rectangular 8-connected objects, including both "
    "an edge-touching and an interior object in every default scene. Fill each "
    "object's bounding-box background cells with color 7."
)

INVARIANTS = [
    "background is 0 and input objects never use color 7",
    "every nonzero component is 8-connected and has a background hole in its bbox",
    "component bboxes are separated by at least one blank row or column",
    "default draws contain both boundary-touching and interior components",
]

OBJECT_KINDS = (
    "diagonal",
    "L_shape",
    "cross",
    "Z_shape",
    "random_blob",
    "hollow_ring",
    "staircase",
)
SIZE_DISTRIBUTIONS = ("small", "medium", "large", "mixed")
PLACEMENTS = ("random", "corners", "row", "column")

AXES = {
    "grid_h": {"type": "int", "default": "difficulty-aware 9..20", "valid": "6..20"},
    "grid_w": {"type": "int", "default": "difficulty-aware 9..20", "valid": "6..20"},
    "n_objects": {"type": "int", "default": "difficulty-aware 2..5", "valid": "1..5"},
    "object_kind": {"type": "str", "default": "rng", "valid": "|".join(OBJECT_KINDS)},
    "fg_color": {"type": "color", "default": "rng", "valid": "1|2|3|4|5|6|8|9"},
    "size_distribution": {
        "type": "str",
        "default": "difficulty-aware",
        "valid": "|".join(SIZE_DISTRIBUTIONS),
    },
    "placement": {"type": "str", "default": "rng", "valid": "|".join(PLACEMENTS)},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

_DIFFICULTY_BANDS = {
    None: ((10, 16), (10, 16), (2, 4), ("small", "medium")),
    "easy": ((9, 12), (9, 12), (2, 3), ("small",)),
    "medium": ((12, 16), (12, 16), (3, 4), ("small", "medium")),
    "hard": ((16, 20), (16, 20), (4, 5), ("medium", "large")),
}


def _validate_public_controls(
    seed: int,
    sample_index: int,
    difficulty: str | None,
    overrides: dict[str, Any],
) -> None:
    if type(seed) is not int or seed < 0:
        raise TypeError("seed must be a nonnegative integer (not bool)")
    if type(sample_index) is not int or sample_index < 0:
        raise TypeError("sample_index must be a nonnegative integer (not bool)")
    if difficulty not in _DIFFICULTY_BANDS:
        raise ValueError("difficulty must be one of None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")
    for name in ("grid_h", "grid_w", "n_objects", "fg_color"):
        value = overrides.get(name)
        if value is not None and type(value) is not int:
            raise TypeError(f"{name} must be an integer (not bool)")
    for name in ("object_kind", "size_distribution", "placement"):
        value = overrides.get(name)
        if value is not None and type(value) is not str:
            raise TypeError(f"{name} must be a string")


def _draw_int_axis(ctx, label, *, default, legal, overrides):
    if label in overrides and overrides[label] is not None:
        return ctx.draw_int_strict(label, legal[0], legal[1])
    return ctx.draw_int_strict(label, default[0], default[1])


def _draw_choice_axis(ctx, label, *, default_options, legal_options, overrides):
    options = legal_options if overrides.get(label) is not None else default_options
    return ctx.draw_choice(label, tuple(options))


def _draw_fg(ctx, overrides):
    if overrides.get("fg_color") is not None:
        return ctx.draw_color_strict("fg_color", exclude={0, 7})
    return ctx.draw_color_strict("fg_color", exclude={0, 7})


def _size_for(distribution: str, index: int) -> tuple[int, int]:
    if distribution == "small":
        side = 3
    elif distribution == "medium":
        side = 4
    elif distribution == "large":
        side = 5
    else:
        side = (3, 4, 5)[index % 3]
    return side, side


def _touches_boundary(box: Box, h: int, w: int) -> bool:
    r0, c0, r1, c1 = box
    return r0 == 0 or c0 == 0 or r1 == h - 1 or c1 == w - 1


def _separated(a: Box, b: Box) -> bool:
    """True when bboxes cannot be 8-connected, including diagonally."""
    ar0, ac0, ar1, ac1 = a
    br0, bc0, br1, bc1 = b
    return ar1 + 1 < br0 or br1 + 1 < ar0 or ac1 + 1 < bc0 or bc1 + 1 < ac0


def _row_groups(order: tuple[int, ...], mask: int) -> list[tuple[int, ...]]:
    groups: list[tuple[int, ...]] = []
    start = 0
    for index in range(len(order) - 1):
        if mask & (1 << index):
            groups.append(order[start : index + 1])
            start = index + 1
    groups.append(order[start:])
    return groups


def _layout_has_teaching_roles(layout: Sequence[Box], h: int, w: int) -> bool:
    if not layout:
        return False
    boundary = any(_touches_boundary(box, h, w) for box in layout)
    if len(layout) == 1:
        return boundary
    interior = any(not _touches_boundary(box, h, w) for box in layout)
    return boundary and interior


def _row_layouts(
    h: int,
    w: int,
    shapes: tuple[tuple[int, int], ...],
    *,
    limit: int = 64,
) -> tuple[tuple[Box, ...], ...]:
    """Construct shelf layouts with explicit boundary/interior witnesses.

    This replaces the former 200,000-node rectangle search.  With at most five
    objects, enumerating object orders and row breaks is tiny (at most 1,920
    partitions) and gives an exact, deterministic feasibility test.
    """
    n = len(shapes)
    if n == 0:
        return ()
    if n == 1:
        sh, sw = shapes[0]
        if sh <= h and sw <= w:
            return (((0, 0, sh - 1, sw - 1),),)
        return ()

    layouts: list[tuple[Box, ...]] = []
    seen: set[tuple[Box, ...]] = set()
    for order in permutations(range(n)):
        for mask in range(1 << (n - 1)):
            groups = _row_groups(order, mask)
            heights = [max(shapes[index][0] for index in group) for group in groups]
            widths = [
                sum(shapes[index][1] for index in group) + len(group) - 1
                for group in groups
            ]
            total_h = sum(heights) + len(groups) - 1

            # Left-boundary shelf: all rows have top/bottom margins.  The first
            # object touches the left canvas edge; every later object has room
            # on all four sides and is therefore an interior witness.
            if total_h + 2 <= h:
                boxes: list[Box | None] = [None] * n
                row = 1
                valid = True
                for group_index, group in enumerate(groups):
                    col = 0 if group_index == 0 else 1
                    width_limit = w - 1 if group_index == 0 else w - 2
                    if widths[group_index] > width_limit:
                        valid = False
                        break
                    for index in group:
                        sh, sw = shapes[index]
                        boxes[index] = (row, col, row + sh - 1, col + sw - 1)
                        col += sw + 1
                    row += heights[group_index] + 1
                if valid:
                    layout = tuple(box for box in boxes if box is not None)
                    if (
                        len(layout) == n
                        and _layout_has_teaching_roles(layout, h, w)
                        and layout not in seen
                    ):
                        seen.add(layout)
                        layouts.append(layout)

            # Top-boundary shelf: the first row touches the top edge; lower
            # rows have side and bottom margins, supplying an interior witness.
            if len(groups) >= 2 and total_h + 1 <= h:
                boxes = [None] * n
                row = 0
                valid = True
                for group_index, group in enumerate(groups):
                    col = 0 if group_index == 0 else 1
                    width_limit = w if group_index == 0 else w - 2
                    if widths[group_index] > width_limit:
                        valid = False
                        break
                    for index in group:
                        sh, sw = shapes[index]
                        boxes[index] = (row, col, row + sh - 1, col + sw - 1)
                        col += sw + 1
                    row += heights[group_index] + 1
                if valid:
                    layout = tuple(box for box in boxes if box is not None)
                    if (
                        len(layout) == n
                        and _layout_has_teaching_roles(layout, h, w)
                        and layout not in seen
                    ):
                        seen.add(layout)
                        layouts.append(layout)

            if len(layouts) >= limit:
                return tuple(layouts)
    return tuple(layouts)


def _transpose_layout(layout: Sequence[Box]) -> tuple[Box, ...]:
    return tuple((c0, r0, c1, r1) for r0, c0, r1, c1 in layout)


def _mirror_rows(layout: Sequence[Box], h: int) -> tuple[Box, ...]:
    return tuple((h - 1 - r1, c0, h - 1 - r0, c1) for r0, c0, r1, c1 in layout)


def _mirror_cols(layout: Sequence[Box], w: int) -> tuple[Box, ...]:
    return tuple((r0, w - 1 - c1, r1, w - 1 - c0) for r0, c0, r1, c1 in layout)


@lru_cache(maxsize=None)
def _layout_templates(
    h: int,
    w: int,
    shapes: tuple[tuple[int, int], ...],
) -> tuple[tuple[Box, ...], ...]:
    """Return cached constructive layouts, or an empty tuple if impossible."""
    candidates = list(_row_layouts(h, w, shapes))
    transposed_shapes = tuple((sw, sh) for sh, sw in shapes)
    candidates.extend(
        _transpose_layout(layout)
        for layout in _row_layouts(w, h, transposed_shapes)
    )

    layouts: list[tuple[Box, ...]] = []
    seen: set[tuple[Box, ...]] = set()
    for candidate in candidates:
        variants = (
            candidate,
            _mirror_rows(candidate, h),
            _mirror_cols(candidate, w),
            _mirror_cols(_mirror_rows(candidate, h), w),
        )
        for layout in variants:
            if layout in seen or not _layout_has_teaching_roles(layout, h, w):
                continue
            seen.add(layout)
            layouts.append(layout)
            if len(layouts) >= 256:
                return tuple(layouts)
    return tuple(layouts)


def _placement_score(layout: Sequence[Box], placement: str, h: int, w: int):
    row_bands = len({(r0, r1) for r0, _, r1, _ in layout})
    col_bands = len({(c0, c1) for _, c0, _, c1 in layout})
    vertical_span = max(box[2] for box in layout) - min(box[0] for box in layout)
    horizontal_span = max(box[3] for box in layout) - min(box[1] for box in layout)
    boundary_sides = sum(
        (r0 == 0) + (c0 == 0) + (r1 == h - 1) + (c1 == w - 1)
        for r0, c0, r1, c1 in layout
    )
    centers = [((r0 + r1) / 2, (c0 + c1) / 2) for r0, c0, r1, c1 in layout]
    spread = sum(
        abs(r1 - r2) + abs(c1 - c2)
        for index, (r1, c1) in enumerate(centers)
        for r2, c2 in centers[index + 1 :]
    )
    if placement == "row":
        return (row_bands, vertical_span, -horizontal_span, -boundary_sides)
    if placement == "column":
        return (col_bands, horizontal_span, -vertical_span, -boundary_sides)
    return (-boundary_sides, -spread, row_bands + col_bands)


def _place_boxes(
    h: int,
    w: int,
    shapes: Sequence[tuple[int, int]],
    placement: str,
    rng,
) -> list[Box]:
    templates = _layout_templates(h, w, tuple(shapes))
    if not templates:
        raise ValueError(
            f"cannot place {len(shapes)} separated objects in {h}x{w} "
            f"with sizes {list(shapes)}"
        )
    if placement == "random":
        return list(rng.choice(templates))
    return list(min(templates, key=lambda layout: _placement_score(layout, placement, h, w)))


@lru_cache(maxsize=None)
def _structural_candidates(
    difficulty: str | None,
    grid_h: int | None,
    grid_w: int | None,
    n_objects: int | None,
    size_distribution: str | None,
) -> tuple[tuple[int, int, int, str], ...]:
    h_band, w_band, n_band, size_options = _DIFFICULTY_BANDS[difficulty]
    heights = (grid_h,) if grid_h is not None else tuple(range(h_band[0], h_band[1] + 1))
    widths = (grid_w,) if grid_w is not None else tuple(range(w_band[0], w_band[1] + 1))
    counts = (n_objects,) if n_objects is not None else tuple(range(n_band[0], n_band[1] + 1))
    sizes = (size_distribution,) if size_distribution is not None else tuple(size_options)

    feasible: list[tuple[int, int, int, str]] = []
    for h in heights:
        for w in widths:
            for n in counts:
                for distribution in sizes:
                    if type(h) is not int or type(w) is not int or type(n) is not int:
                        continue
                    if not 6 <= h <= 20 or not 6 <= w <= 20 or not 1 <= n <= 5:
                        continue
                    if distribution not in SIZE_DISTRIBUTIONS:
                        continue
                    shapes = tuple(_size_for(distribution, index) for index in range(n))
                    if _layout_templates(h, w, shapes):
                        feasible.append((h, w, n, distribution))
    return tuple(feasible)


def _select_structural_axes(ctx, difficulty, overrides):
    supplied = {
        name: overrides.get(name)
        for name in ("grid_h", "grid_w", "n_objects", "size_distribution")
        if overrides.get(name) is not None
    }
    candidates = list(
        _structural_candidates(
            difficulty,
            supplied.get("grid_h"),
            supplied.get("grid_w"),
            supplied.get("n_objects"),
            supplied.get("size_distribution"),
        )
    )
    if not candidates:
        exc = ValueError(
            "cannot fit a feasible separated-object layout for the requested grid_h, "
            "grid_w, n_objects, and size_distribution controls"
        )
        if len(supplied) >= 2:
            exc.incompatible_axes = tuple(supplied)
        raise exc

    selected: list[Any] = []
    specs = (
        ("grid_h", 0, (6, 20)),
        ("grid_w", 1, (6, 20)),
        ("n_objects", 2, (1, 5)),
        ("size_distribution", 3, SIZE_DISTRIBUTIONS),
    )
    for name, index, legal in specs:
        if name in supplied:
            if name == "size_distribution":
                value = ctx.draw_choice(name, tuple(legal))
            else:
                value = ctx.draw_int_strict(name, legal[0], legal[1])
        else:
            values = tuple(sorted({candidate[index] for candidate in candidates}))
            value = ctx.draw_choice(name, values)
        selected.append(value)
        candidates = [candidate for candidate in candidates if candidate[index] == value]
    return tuple(selected)

def _neighbors8(cell: Cell):
    r, c = cell
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            if dr or dc:
                yield r + dr, c + dc


def _is_fillable(cells: Sequence[Cell], sh: int | None = None, sw: int | None = None) -> bool:
    cs = set(cells)
    if not cs:
        return False
    seen = {next(iter(cs))}
    stack = list(seen)
    while stack:
        cell = stack.pop()
        for neighbor in _neighbors8(cell):
            if neighbor in cs and neighbor not in seen:
                seen.add(neighbor)
                stack.append(neighbor)
    if seen != cs:
        return False
    r0 = min(r for r, _ in cs)
    c0 = min(c for _, c in cs)
    r1 = max(r for r, _ in cs)
    c1 = max(c for _, c in cs)
    if sh is not None and (r0, c0, r1, c1) != (0, 0, sh - 1, sw - 1):
        return False
    return any((r, c) not in cs for r in range(r0, r1 + 1) for c in range(c0, c1 + 1))


def _fallback_cells(sh: int, sw: int) -> list[Cell]:
    # Three sides of a frame: connected, exact bbox, and always leaves holes.
    cells = {(0, c) for c in range(sw)}
    cells.update((r, 0) for r in range(sh))
    cells.update((r, sw - 1) for r in range(sh))
    return sorted(cells)


def _shape_cells(kind: str, sh: int, sw: int, rng) -> list[Cell]:
    if kind == "diagonal":
        cells = [(i, i) for i in range(min(sh, sw))]
    elif kind == "L_shape":
        cells = [(r, 0) for r in range(sh)] + [(sh - 1, c) for c in range(1, sw)]
    elif kind == "cross":
        mr, mc = sh // 2, sw // 2
        cells = [(mr, c) for c in range(sw)] + [(r, mc) for r in range(sh)]
    elif kind == "Z_shape":
        cells = [(0, c) for c in range(sw)] + [(sh - 1, c) for c in range(sw)]
        for r in range(1, sh - 1):
            c = round((sw - 1) * (sh - 1 - r) / max(1, sh - 1))
            cells.append((r, c))
    elif kind == "hollow_ring":
        cells = [(0, c) for c in range(sw)] + [(sh - 1, c) for c in range(sw)]
        cells += [(r, 0) for r in range(1, sh - 1)]
        cells += [(r, sw - 1) for r in range(1, sh - 1)]
    elif kind == "staircase":
        cells = [(i, i) for i in range(min(sh, sw))]
        cells += [(i, min(sw - 1, i + 1)) for i in range(max(0, min(sh, sw) - 1))]
    else:  # random_blob: begin with a U and add a few non-central cells.
        cells = _fallback_cells(sh, sw)
        additions = [
            (r, c)
            for r in range(1, sh - 1)
            for c in range(1, sw - 1)
            if (r, c) != (sh // 2, sw // 2)
        ]
        rng.shuffle(additions)
        cells += additions[: max(0, len(additions) // 3)]

    cells = sorted(set(cells))
    return cells if _is_fillable(cells, sh, sw) else _fallback_cells(sh, sw)


def generate(seed, sample_index, *, difficulty=None, **overrides) -> Grid:
    _validate_public_controls(seed, sample_index, difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    h, w, n, size_distribution = _select_structural_axes(ctx, difficulty, overrides)
    kind = _draw_choice_axis(
        ctx,
        "object_kind",
        default_options=OBJECT_KINDS,
        legal_options=OBJECT_KINDS,
        overrides=overrides,
    )
    placement = _draw_choice_axis(
        ctx,
        "placement",
        default_options=PLACEMENTS,
        legal_options=PLACEMENTS,
        overrides=overrides,
    )
    fg = _draw_fg(ctx, overrides)

    shapes = [_size_for(size_distribution, index) for index in range(n)]
    boxes = _place_boxes(h, w, shapes, placement, ctx.draw_rng("layout"))
    grid = full_grid(h, w, 0)
    shape_rng = ctx.draw_rng("shape_details")
    for box, (sh, sw) in zip(boxes, shapes, strict=True):
        r0, c0, _, _ = box
        for dr, dc in _shape_cells(kind, sh, sw, shape_rng):
            grid[r0 + dr][c0 + dc] = fg
    return grid


def _grid_shape_errors(grid) -> list[str]:
    if not isinstance(grid, list) or not grid:
        return ["grid must be a nonempty list of rows"]
    if not all(isinstance(row, list) for row in grid):
        return ["every row must be a list"]
    if not grid[0]:
        return ["grid rows must be nonempty"]
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return ["grid must be rectangular"]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if type(value) is not int or not 0 <= value <= 9:
                return [f"cell ({r},{c}) must be an integer color in 0..9"]
    return []


def _components8(grid: Grid) -> list[list[Cell]]:
    h, w = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0}
    components: list[list[Cell]] = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        component = [start]
        stack = [start]
        while stack:
            cell = stack.pop()
            for neighbor in _neighbors8(cell):
                if neighbor in unseen:
                    unseen.remove(neighbor)
                    component.append(neighbor)
                    stack.append(neighbor)
        components.append(sorted(component))
    return components


def _bbox(component: Sequence[Cell]) -> Box:
    return (
        min(r for r, _ in component),
        min(c for _, c in component),
        max(r for r, _ in component),
        max(c for _, c in component),
    )


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate that every component gives the rule a visible bbox fill."""
    del difficulty, meta
    errors = _grid_shape_errors(grid)
    if errors:
        return errors
    if any(value == 7 for row in grid for value in row):
        errors.append("input objects may not use fill color 7")

    components = _components8(grid)
    if not components:
        errors.append("blank grid: no object to fill")
        return errors
    if len(components) > 5:
        errors.append(f"scene has {len(components)} objects; maximum is 5")

    boxes = []
    for index, component in enumerate(components):
        colors = {grid[r][c] for r, c in component}
        if len(colors) != 1:
            errors.append(f"object {index} mixes foreground colors")
        box = _bbox(component)
        boxes.append(box)
        r0, c0, r1, c1 = box
        occupied = set(component)
        if not any(
            (r, c) not in occupied
            for r in range(r0, r1 + 1)
            for c in range(c0, c1 + 1)
        ):
            errors.append(f"object {index} is a solid rectangle with nothing to fill")
    for i, box in enumerate(boxes):
        for other in boxes[i + 1 :]:
            if not _separated(box, other):
                errors.append("object bboxes are not separated by a blank gap")
                break
    return sorted(set(errors))


def _fill_selected(grid: Grid, predicate: Callable[[Box, int, int], bool]) -> Grid:
    if _grid_shape_errors(grid):
        raise ValueError("bbox filling requires a nonempty rectangular ARC grid")
    out = deepcopy(grid)
    h, w = len(grid), len(grid[0])
    for component in _components8(grid):
        box = _bbox(component)
        if not predicate(box, h, w):
            continue
        r0, c0, r1, c1 = box
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                if out[r][c] == 0:
                    out[r][c] = 7
    return out


def rule_mirror(grid: Grid) -> Grid:
    return _fill_selected(grid, lambda box, h, w: True)


def _skip_boundary(grid: Grid) -> Grid:
    return _fill_selected(grid, lambda box, h, w: not _touches_boundary(box, h, w))


def _boundary_only(grid: Grid) -> Grid:
    return _fill_selected(grid, lambda box, h, w: _touches_boundary(box, h, w))


def _global_bbox(grid: Grid) -> Grid:
    if _grid_shape_errors(grid):
        raise ValueError("global bbox rival requires a valid grid")
    cells = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value]
    if not cells:
        return deepcopy(grid)
    out = deepcopy(grid)
    r0, c0, r1, c1 = _bbox(cells)
    for r in range(r0, r1 + 1):
        for c in range(c0, c1 + 1):
            if out[r][c] == 0:
                out[r][c] = 7
    return out


SEMANTIC_RIVALS = {
    "skip_boundary": _skip_boundary,
    "boundary_only": _boundary_only,
    "global_bbox": _global_bbox,
}
CANONICAL_SHORTCUTS: dict[str, object] = {}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query) -> list[str]:
    reasons: list[str] = []
    if not demos:
        return ["lesson has no demonstrations"]
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} is not an input/output pair")
            continue
        structural = self_check(pair["input"])
        if structural:
            reasons.append(f"demo {index} is structurally invalid: {structural[0]}")
        elif rule_mirror(pair["input"]) != pair["output"]:
            reasons.append(f"demo {index} output disagrees with the canonical rule")
    for name, rival in LESSON_COMPETITORS.items():
        if all(
            isinstance(pair, dict)
            and "input" in pair
            and "output" in pair
            and rival(pair["input"]) == pair["output"]
            for pair in demos
        ):
            reasons.append(f"rival {name!r} survives every demonstration")
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        reasons.append("query is not an input/output pair")
    else:
        structural = self_check(query["input"])
        if structural:
            reasons.append(f"query is structurally invalid: {structural[0]}")
        elif rule_mirror(query["input"]) != query["output"]:
            reasons.append("query output disagrees with the canonical rule")
    return reasons


def observe_overrides(grid: Grid) -> dict[str, Any]:
    if _grid_shape_errors(grid):
        return {}
    colors = {value for row in grid for value in row if value}
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_objects": len(_components8(grid)),
        "fg_color": next(iter(colors)) if len(colors) == 1 else None,
    }
