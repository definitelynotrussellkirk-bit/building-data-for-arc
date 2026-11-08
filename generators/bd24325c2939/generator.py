"""Generator for ARC task bd24325c2939 — mirror the largest component.

A single cyan cell (8) is the reflection pivot.  Ignore that marker, choose the
unique largest 4-connected nonzero component, and copy every one of its colored
cells into all four positions obtained by reflecting across the pivot row and
pivot column.  Smaller disconnected components are distractors and disappear.

The ordinary lesson schedule includes canonical-scale/morphology anchors, a
novel-color distractor witness, and source components in non-canonical
quadrants so fixed-position, all-nonzero, count-only, and modal-color shortcuts
cannot explain the demonstrations.
"""
from __future__ import annotations

from collections import deque
from typing import Any, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "bd24325c2939"
TASK_ID = "bd24325c2939"
VERSION = "3.0.0"
RULE_HASH = "3833f9c0e35d"  # sha256[:12] of whitespace-normalized canonical rule
EXAMPLES_NEEDED = 3

SUMMARY = (
    "Find the single color-8 pivot. After temporarily removing it, select the "
    "unique largest 4-connected nonzero component. Preserve each source cell's "
    "color and paint that component in all four reflection-related positions "
    "around the pivot: original, left/right mirror, up/down mirror, and both. "
    "Return a fresh background-0 grid with the pivot restored; smaller "
    "disconnected components are distractors and are omitted."
)

INVARIANTS = [
    "background is color 0 and there is exactly one color-8 pivot",
    "the unique largest non-pivot 4-connected component has 3..6 cells",
    "the selected component uses 2..4 colors, so per-cell color preservation is visible",
    "the selected component lies strictly in one pivot quadrant",
    "all four reflected copies are in-bounds and pairwise disjoint",
    "0..2 smaller disconnected distractor components may appear but never occupy an answer-orbit cell",
]

QUADRANTS = ("upper_left", "upper_right", "lower_left", "lower_right")
AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-banded with canonical prior",
        "valid": "9..15",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-banded with canonical prior",
        "valid": "9..15",
    },
    "component_size": {
        "type": "int",
        "default": "difficulty-banded 3..6",
        "valid": "3..6",
    },
    "component_palette_size": {
        "type": "int",
        "default": "2..min(4, component_size)",
        "valid": "2..4",
    },
    "distractor_count": {
        "type": "int",
        "default": "scheduled/banded 0..2",
        "valid": "0..2",
    },
    "source_quadrant": {
        "type": "str",
        "default": "scheduled then varied",
        "valid": "|".join(QUADRANTS),
    },
}

_H_RANGE = (9, 15)
_W_RANGE = (9, 15)
_COMPONENT_RANGE = (3, 6)
_PALETTE_RANGE = (2, 4)
_DISTRACTOR_RANGE = (0, 2)
_DIRS4 = ((1, 0), (-1, 0), (0, 1), (0, -1))

# Free polyominoes are transformed at draw time, so this compact bank yields a
# much larger orientation/morphology support while keeping every shape small
# enough for the 9x9 boundary override.
_SHAPES_BY_SIZE: dict[int, tuple[tuple[tuple[int, int], ...], ...]] = {
    3: (
        ((0, 0), (1, 0), (1, 1)),
        ((0, 0), (0, 1), (0, 2)),
    ),
    4: (
        ((0, 0), (0, 1), (1, 0), (1, 1)),
        ((0, 0), (1, 0), (2, 0), (2, 1)),
        ((0, 0), (0, 1), (0, 2), (1, 1)),
        ((0, 0), (1, 0), (1, 1), (2, 1)),
        ((0, 0), (0, 1), (1, 1), (1, 2)),
    ),
    5: (
        ((0, 0), (0, 2), (1, 0), (1, 1), (1, 2)),
        ((0, 0), (1, 0), (1, 1), (2, 1), (2, 2)),
        ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1)),
        ((0, 0), (0, 1), (1, 0), (1, 1), (2, 0)),
        ((0, 0), (1, 0), (2, 0), (3, 0), (3, 1)),
    ),
    6: (
        ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2)),
        ((0, 0), (1, 0), (1, 1), (2, 1), (2, 2), (3, 2)),
        ((0, 0), (1, 0), (2, 0), (3, 0), (3, 1), (3, 2)),
        ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1), (3, 1)),
    ),
}

# Canonical rule-relevant signatures.  Exact colors and distractor coordinates
# are nuisance variables; dimensions, pivot-centered offsets, component
# morphology/color-count, and distractor-size multiset are preserved.
_CANONICAL_PROFILES = (
    {
        "name": "train0",
        "h": 9,
        "w": 9,
        "offsets": ((-3, -3), (-2, -3), (-2, -2)),
        "component_palette_size": 3,
        "distractor_count": 0,
    },
    {
        "name": "train1",
        "h": 11,
        "w": 11,
        "offsets": ((-3, -3), (-3, -1), (-2, -3), (-2, -2), (-2, -1)),
        "component_palette_size": 2,
        "distractor_count": 0,
    },
    {
        "name": "train2",
        "h": 9,
        "w": 11,
        "offsets": ((-3, -3), (-2, -3), (-2, -2), (-1, -2), (-1, -1)),
        "component_palette_size": 2,
        "distractor_count": 0,
    },
    {
        "name": "train3",
        "h": 13,
        "w": 13,
        "offsets": ((-3, -3), (-3, -2), (-2, -2)),
        "component_palette_size": 2,
        "distractor_count": 1,
    },
    {
        "name": "test0",
        "h": 9,
        "w": 9,
        "offsets": ((-3, -3), (-3, -2), (-2, -2), (-2, -1)),
        "component_palette_size": 3,
        "distractor_count": 0,
    },
)


def _is_arc_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and 0 <= value <= 9


def _components(
    grid: list[list[int]], *, ignore: Iterable[tuple[int, int]] = ()
) -> list[list[tuple[int, int]]]:
    """4-connected nonzero components after treating ``ignore`` as background."""
    h, w = len(grid), len(grid[0])
    ignored = set(ignore)
    unseen = {
        (r, c)
        for r in range(h)
        for c in range(w)
        if grid[r][c] != 0 and (r, c) not in ignored
    }
    out: list[list[tuple[int, int]]] = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        queue = deque([start])
        cells: list[tuple[int, int]] = []
        while queue:
            cell = queue.popleft()
            cells.append(cell)
            for dr, dc in _DIRS4:
                neighbor = (cell[0] + dr, cell[1] + dc)
                if neighbor in unseen:
                    unseen.remove(neighbor)
                    queue.append(neighbor)
        out.append(sorted(cells))
    return out


def _quadrant(cells: Iterable[tuple[int, int]], pivot: tuple[int, int]) -> str | None:
    pr, pc = pivot
    signs = {
        (-1 if r < pr else 1 if r > pr else 0,
         -1 if c < pc else 1 if c > pc else 0)
        for r, c in cells
    }
    mapping = {
        (-1, -1): "upper_left",
        (-1, 1): "upper_right",
        (1, -1): "lower_left",
        (1, 1): "lower_right",
    }
    if len(signs) != 1:
        return None
    return mapping.get(next(iter(signs)))


def _orbit(
    cells: Iterable[tuple[int, int]], pivot: tuple[int, int]
) -> set[tuple[int, int]]:
    pr, pc = pivot
    return {
        reflected
        for r, c in cells
        for reflected in (
            (r, c),
            (r, 2 * pc - c),
            (2 * pr - r, c),
            (2 * pr - r, 2 * pc - c),
        )
    }


def _analyze_scene(grid: Any) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(grid, list) or not grid:
        return {"errors": ["grid must be a non-empty list of rows"]}
    if not isinstance(grid[0], list) or not grid[0]:
        return {"errors": ["grid rows must be non-empty lists"]}
    h, w = len(grid), len(grid[0])
    if any(not isinstance(row, list) or len(row) != w for row in grid):
        return {"errors": ["grid must be rectangular"]}
    if any(not _is_arc_int(value) for row in grid for value in row):
        return {"errors": ["all cells must be literal ARC integers 0..9"]}
    if not (_H_RANGE[0] <= h <= _H_RANGE[1]):
        errors.append(f"height {h} outside {_H_RANGE[0]}..{_H_RANGE[1]}")
    if not (_W_RANGE[0] <= w <= _W_RANGE[1]):
        errors.append(f"width {w} outside {_W_RANGE[0]}..{_W_RANGE[1]}")

    pivots = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 8]
    if len(pivots) != 1:
        errors.append(f"expected exactly one color-8 pivot, found {len(pivots)}")
        return {"errors": errors, "grid_h": h, "grid_w": w, "pivots": pivots}
    pivot = pivots[0]
    pr, pc = pivot
    if any(
        0 <= pr + dr < h
        and 0 <= pc + dc < w
        and grid[pr + dr][pc + dc] != 0
        for dr, dc in _DIRS4
    ):
        errors.append("pivot must be orthogonally isolated")

    components = _components(grid, ignore={pivot})
    if not components:
        errors.append("expected at least one non-pivot component")
        return {
            "errors": errors,
            "grid_h": h,
            "grid_w": w,
            "pivot": pivot,
            "components": components,
        }
    sizes = sorted((len(component) for component in components), reverse=True)
    if len(sizes) > 1 and sizes[0] == sizes[1]:
        errors.append("largest non-pivot component must be unique")
    main = max(components, key=lambda component: (len(component), tuple(component)))
    distractors = [component for component in components if component is not main]
    main_size = len(main)
    if not (_COMPONENT_RANGE[0] <= main_size <= _COMPONENT_RANGE[1]):
        errors.append(
            f"largest component size {main_size} outside "
            f"{_COMPONENT_RANGE[0]}..{_COMPONENT_RANGE[1]}"
        )
    main_colors = {grid[r][c] for r, c in main}
    if not (_PALETTE_RANGE[0] <= len(main_colors) <= _PALETTE_RANGE[1]):
        errors.append(
            f"largest component uses {len(main_colors)} colors; expected "
            f"{_PALETTE_RANGE[0]}..{_PALETTE_RANGE[1]}"
        )
    quadrant = _quadrant(main, pivot)
    if quadrant is None:
        errors.append("largest component must lie strictly in one pivot quadrant")

    orbit = _orbit(main, pivot)
    if any(not (0 <= r < h and 0 <= c < w) for r, c in orbit):
        errors.append("a reflected component cell leaves the grid")
    if len(orbit) != 4 * main_size:
        errors.append("the four reflected copies must be pairwise disjoint")

    if not (_DISTRACTOR_RANGE[0] <= len(distractors) <= _DISTRACTOR_RANGE[1]):
        errors.append(
            f"distractor count {len(distractors)} outside "
            f"{_DISTRACTOR_RANGE[0]}..{_DISTRACTOR_RANGE[1]}"
        )
    for index, component in enumerate(distractors):
        if len(component) >= main_size:
            errors.append(f"distractor {index} is not smaller than the selected component")
        overlap = set(component) & orbit
        if overlap:
            errors.append(
                f"distractor {index} occupies answer-orbit cell(s) {sorted(overlap)[:3]}"
            )

    return {
        "errors": errors,
        "grid_h": h,
        "grid_w": w,
        "pivot": pivot,
        "components": components,
        "main": main,
        "distractors": distractors,
        "main_colors": main_colors,
        "source_quadrant": quadrant,
        "orbit": orbit,
        "component_size": main_size,
        "component_palette_size": len(main_colors),
        "distractor_count": len(distractors),
        "distractor_sizes": tuple(sorted(len(component) for component in distractors)),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed or ambiguous lessons; accept all canonical inputs."""
    return _analyze_scene(grid)["errors"]


def observe_overrides(grid) -> dict[str, int | str]:
    """Recover every declared exact axis from the returned input grid."""
    facts = _analyze_scene(grid)
    if facts["errors"]:
        return {}
    return {
        "grid_h": facts["grid_h"],
        "grid_w": facts["grid_w"],
        "component_size": facts["component_size"],
        "component_palette_size": facts["component_palette_size"],
        "distractor_count": facts["distractor_count"],
        "source_quadrant": facts["source_quadrant"],
    }


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Small Python test mirror of the canonical oracle; never an output authority."""
    h, w = len(grid), len(grid[0])
    pivot = next((r, c) for r in range(h) for c in range(w) if grid[r][c] == 8)
    components = _components(grid, ignore={pivot})
    main = max(components, key=lambda component: (len(component), tuple(component)))
    pr, pc = pivot
    out = full_grid(h, w, 0)
    out[pr][pc] = 8
    for r, c in main:
        value = grid[r][c]
        for rr, cc in (
            (r, c),
            (r, 2 * pc - c),
            (2 * pr - r, c),
            (2 * pr - r, 2 * pc - c),
        ):
            if 0 <= rr < h and 0 <= cc < w:
                out[rr][cc] = value
    return out


def _normalize(shape: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(shape)
    min_r = min(r for r, _ in cells)
    min_c = min(c for _, c in cells)
    return tuple(sorted((r - min_r, c - min_c) for r, c in cells))


def _dihedral_shapes(
    shape: tuple[tuple[int, int], ...]
) -> tuple[tuple[tuple[int, int], ...], ...]:
    variants: set[tuple[tuple[int, int], ...]] = set()
    current = tuple(shape)
    for _ in range(4):
        variants.add(_normalize(current))
        variants.add(_normalize((r, -c) for r, c in current))
        current = tuple((c, -r) for r, c in current)
    return tuple(sorted(variants))


def _draw_axis_int(ctx, overrides, label, default_lo, default_hi, valid_lo, valid_hi):
    if overrides.get(label) is not None:
        return ctx.draw_int(label, valid_lo, valid_hi)
    return ctx.draw_int(label, default_lo, default_hi)


def _source_cells(
    h: int,
    w: int,
    shape: tuple[tuple[int, int], ...],
    quadrant: str,
    rng,
    *,
    force_center: bool = False,
) -> tuple[tuple[int, int], list[tuple[int, int]]]:
    sh = max(r for r, _ in shape) + 1
    sw = max(c for _, c in shape) + 1
    pivot_rows = [r for r in range(h) if min(r, h - 1 - r) >= sh]
    pivot_cols = [c for c in range(w) if min(c, w - 1 - c) >= sw]
    if not pivot_rows or not pivot_cols:
        raise ValueError(f"{h}x{w} cannot host a {sh}x{sw} component orbit")
    if force_center:
        pr, pc = h // 2, w // 2
        if pr not in pivot_rows or pc not in pivot_cols:
            raise ValueError("canonical centered pivot cannot host selected component")
    else:
        pr, pc = rng.choice(pivot_rows), rng.choice(pivot_cols)

    row_room = min(pr, h - 1 - pr)
    col_room = min(pc, w - 1 - pc)
    row_gap = rng.randint(1, row_room - sh + 1)
    col_gap = rng.randint(1, col_room - sw + 1)
    upper = quadrant.startswith("upper")
    left = quadrant.endswith("left")
    r0 = pr - row_gap - sh + 1 if upper else pr + row_gap
    c0 = pc - col_gap - sw + 1 if left else pc + col_gap
    cells = [(r0 + r, c0 + c) for r, c in shape]
    return (pr, pc), cells


def _assign_component_colors(
    grid: list[list[int]],
    cells: list[tuple[int, int]],
    palette: tuple[int, ...],
    rng,
) -> None:
    order = list(cells)
    rng.shuffle(order)
    colors = list(palette)
    rng.shuffle(colors)
    plan = colors[:]
    while len(plan) < len(order):
        plan.append(rng.choice(colors))
    rng.shuffle(plan)
    # Reassert one occurrence of each color after shuffling the repeated tail.
    for index, color in enumerate(colors):
        plan[index] = color
    rng.shuffle(plan)
    for (r, c), color in zip(order, plan, strict=True):
        grid[r][c] = color


def _place_distractors(
    grid: list[list[int]],
    *,
    count: int,
    colors: tuple[int, ...],
    forbidden: set[tuple[int, int]],
    rng,
) -> None:
    h, w = len(grid), len(grid[0])
    occupied = {(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0}
    for index in range(count):
        candidates = []
        for r in range(h):
            for c in range(w):
                cell = (r, c)
                if cell in occupied or cell in forbidden:
                    continue
                if any((r + dr, c + dc) in occupied for dr, dc in _DIRS4):
                    continue
                candidates.append(cell)
        if not candidates:
            raise ValueError("not enough separated cells for requested distractors")
        cell = rng.choice(candidates)
        grid[cell[0]][cell[1]] = colors[index]
        occupied.add(cell)


def _band_ranges(band: str) -> tuple[tuple[int, int], tuple[int, int], tuple[int, int], tuple[int, int]]:
    if band == "easy":
        return (9, 11), (9, 11), (3, 4), (0, 1)
    if band == "hard":
        return (11, 15), (11, 15), (4, 6), (1, 2)
    return (9, 13), (9, 13), (3, 5), (0, 2)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unsupported difficulty {difficulty!r}")
    unknown = sorted(
        key for key, value in overrides.items()
        if value is not None and key not in AXES
    )
    if unknown:
        raise TypeError(f"unknown override axis/axes: {', '.join(unknown)}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    band = difficulty or "medium"
    explicit = {key for key, value in overrides.items() if value is not None}
    layout_rng = ctx.draw_rng("layout")
    schedule_slot = int(sample_index) % (EXAMPLES_NEEDED + 1)

    profile = None
    if not explicit and schedule_slot == 0:
        profile = _CANONICAL_PROFILES[(int(sample_index) // 4) % len(_CANONICAL_PROFILES)]
    elif not explicit and schedule_slot == 3 and layout_rng.random() < 0.30:
        profile = ctx.draw_choice("canonical_profile", _CANONICAL_PROFILES)

    if profile is not None:
        h = ctx.draw_int("grid_h", profile["h"], profile["h"])
        w = ctx.draw_int("grid_w", profile["w"], profile["w"])
        component_size = ctx.draw_int(
            "component_size", len(profile["offsets"]), len(profile["offsets"])
        )
        component_palette_size = ctx.draw_int(
            "component_palette_size",
            profile["component_palette_size"],
            profile["component_palette_size"],
        )
        distractor_count = ctx.draw_int(
            "distractor_count",
            profile["distractor_count"],
            profile["distractor_count"],
        )
        source_quadrant = ctx.draw_choice("source_quadrant", ("upper_left",))
        pivot = (h // 2, w // 2)
        source_cells = [
            (pivot[0] + dr, pivot[1] + dc) for dr, dc in profile["offsets"]
        ]
    else:
        h_band, w_band, size_band, distractor_band = _band_ranges(band)
        h = _draw_axis_int(ctx, overrides, "grid_h", *h_band, *_H_RANGE)
        w = _draw_axis_int(ctx, overrides, "grid_w", *w_band, *_W_RANGE)

        requested_palette = (
            int(overrides["component_palette_size"])
            if overrides.get("component_palette_size") is not None
            else None
        )
        if overrides.get("component_size") is not None:
            component_size = ctx.draw_int("component_size", *_COMPONENT_RANGE)
        else:
            size_lo, size_hi = size_band
            if requested_palette is not None:
                size_lo = max(size_lo, requested_palette)
            component_size = ctx.draw_int("component_size", size_lo, size_hi)

        if overrides.get("component_palette_size") is not None:
            component_palette_size = ctx.draw_int(
                "component_palette_size", *_PALETTE_RANGE
            )
        else:
            component_palette_size = ctx.draw_int(
                "component_palette_size", 2, min(_PALETTE_RANGE[1], component_size)
            )
        if component_palette_size > component_size:
            raise ValueError(
                f"component_palette_size={component_palette_size} exceeds "
                f"component_size={component_size}"
            )

        if overrides.get("distractor_count") is not None:
            distractor_count = ctx.draw_int("distractor_count", *_DISTRACTOR_RANGE)
        elif schedule_slot == 1:
            distractor_count = ctx.draw_int("distractor_count", 1, 2)
        else:
            distractor_count = ctx.draw_int("distractor_count", *distractor_band)

        if overrides.get("source_quadrant") is not None:
            source_quadrant = ctx.draw_choice("source_quadrant", QUADRANTS)
        elif schedule_slot == 2:
            source_quadrant = ctx.draw_choice(
                "source_quadrant", ("upper_right", "lower_left", "lower_right")
            )
        else:
            source_quadrant = ctx.draw_choice("source_quadrant", QUADRANTS)

        base_shape = ctx.draw_choice("shape", _SHAPES_BY_SIZE[component_size])
        shape = layout_rng.choice(_dihedral_shapes(base_shape))
        pivot, source_cells = _source_cells(
            h, w, shape, source_quadrant, layout_rng
        )

    scene_colors = ctx.draw_distinct_colors(
        "scene_colors",
        n=component_palette_size + distractor_count,
        exclude={0, 8},
    )
    component_colors = scene_colors[:component_palette_size]
    distractor_colors = scene_colors[component_palette_size:]

    grid = full_grid(h, w, 0)
    grid[pivot[0]][pivot[1]] = 8
    _assign_component_colors(
        grid,
        source_cells,
        component_colors,
        ctx.draw_rng("component_colors"),
    )
    orbit = _orbit(source_cells, pivot)
    _place_distractors(
        grid,
        count=distractor_count,
        colors=distractor_colors,
        forbidden=orbit,
        rng=ctx.draw_rng("distractors"),
    )

    findings = self_check(grid, difficulty=difficulty)
    if findings:
        raise RuntimeError(f"generator built an invalid lesson: {findings}")
    observed = observe_overrides(grid)
    expected = {
        "grid_h": h,
        "grid_w": w,
        "component_size": component_size,
        "component_palette_size": component_palette_size,
        "distractor_count": distractor_count,
        "source_quadrant": source_quadrant,
    }
    if observed != expected:
        raise RuntimeError(f"axis realization mismatch: expected {expected}, observed {observed}")
    return grid
