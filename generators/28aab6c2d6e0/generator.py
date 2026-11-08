"""Generator for ``Fill each object's bounding box``.

The selected Racket authority treats every 4-connected monochrome nonzero
component independently: it paints that component's tight bounding rectangle
with the component's own color on a fresh zero canvas.

Ordinary draws stay on the public task's 7-8 by 7-9 scale, include at least one
non-L irregular component, and schedule a repeated-color scene in every three
consecutive examples.  The latter is a generated counterexample to the tempting
but wrong shortcut "fill one bounding box per color".
"""
from __future__ import annotations

from collections import Counter, deque
from itertools import combinations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "28aab6c2d6e0"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "c86a6d30fc9f"

SUMMARY = (
    "Place 2-4 separated monochrome irregular components on a zero background. "
    "Every component has at least one hole in its tight bounding box, and every "
    "draw includes a non-L component, so the task is not reducible to completing "
    "2x2 L-trominoes. Exactly two nonzero colors are used; scenes with three or "
    "four components reuse colors across disconnected components. The oracle "
    "independently fills each component's tight bounding box with that component's "
    "color."
)

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

INVARIANTS = [
    "background is modal color 0",
    "there are exactly 2-4 pairwise-separated 4-connected monochrome components",
    "exactly two nonzero colors are present",
    "every component is irregular and expands under the selected rule",
    "at least one component is not a three-cell L in a 2x2 box",
    "component bounding boxes are pairwise disjoint",
]

COUNTER_HYPOTHESES = [
    "complete only 2x2 L-trominoes",
    "fill one bounding box per color rather than per connected component",
    "fill only the first component",
    "copy the input unchanged",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "scheduled canonical-scale profile",
        "valid": "7..8",
        "doc": "Exact returned grid height.",
    },
    "grid_w": {
        "type": "int",
        "default": "scheduled canonical-scale profile",
        "valid": "7..9",
        "doc": "Exact returned grid width.",
    },
    "n_objects": {
        "type": "int",
        "default": "difficulty- and lesson-lane-aware 2..4",
        "valid": "2..4",
        "doc": "Exact number of disconnected nonzero components.",
    },
}

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()

SCHEDULE_PROFILES = (
    "canonical_scale_a",
    "repeated_color_trap",
    "canonical_scale_b",
)
_CANONICAL_DIMENSIONS = ((7, 7), (7, 8), (8, 9))

# All shapes fit inside a 3x3 placement slot and have a non-full tight bbox.
_L_TROMINOES = (
    ((0, 0), (0, 1), (1, 0)),
    ((0, 0), (0, 1), (1, 1)),
    ((0, 0), (1, 0), (1, 1)),
    ((0, 1), (1, 0), (1, 1)),
)
_NON_L_EXPANDING_SHAPES = (
    ((0, 0), (1, 0), (1, 1), (1, 2)),
    ((0, 0), (0, 1), (0, 2), (1, 2)),
    ((0, 2), (1, 0), (1, 1), (1, 2)),
    ((0, 0), (0, 1), (0, 2), (1, 0)),
    ((0, 0), (1, 0), (1, 1), (2, 1)),
    ((0, 1), (1, 0), (1, 1), (2, 0)),
    ((0, 0), (0, 1), (1, 1), (2, 1)),
    ((0, 0), (1, 0), (2, 0), (2, 1)),
    ((0, 0), (0, 1), (0, 2), (1, 1)),
    ((0, 1), (1, 0), (1, 1), (1, 2)),
    ((0, 0), (0, 2), (1, 0), (1, 1), (1, 2)),
)
_ALL_EXPANDING_SHAPES = _L_TROMINOES + _NON_L_EXPANDING_SHAPES


def schedule_profile(seed, sample_index, difficulty=None):
    """Return the stable three-lane lesson profile name."""
    del seed, difficulty
    return SCHEDULE_PROFILES[sample_index % len(SCHEDULE_PROFILES)]


def _validate_call(difficulty, overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")
    for name, lo, hi in (
        ("grid_h", 7, 8),
        ("grid_w", 7, 9),
        ("n_objects", 2, 4),
    ):
        value = overrides.get(name)
        if value is not None and (type(value) is not int or not lo <= value <= hi):
            raise ValueError(f"{name} must be an integer in [{lo}, {hi}]")


def _components(grid):
    """Return monochrome 4-connected nonzero components in reading order."""
    h, w = len(grid), len(grid[0])
    seen = set()
    out = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            todo = deque([(r, c)])
            seen.add((r, c))
            cells = []
            while todo:
                rr, cc = todo.popleft()
                cells.append((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        todo.append((nr, nc))
            out.append({"color": color, "cells": tuple(sorted(cells))})
    return out


def _bbox(cells):
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    return min(rows), min(cols), max(rows), max(cols)


def _rect_cells(box):
    r1, c1, r2, c2 = box
    return {(r, c) for r in range(r1, r2 + 1) for c in range(c1, c2 + 1)}


def _bbox_area(box):
    r1, c1, r2, c2 = box
    return (r2 - r1 + 1) * (c2 - c1 + 1)


def _is_l_tromino(cells):
    box = _bbox(cells)
    return len(cells) == 3 and _bbox_area(box) == 4


def _copy_grid(grid):
    return [list(row) for row in grid]


def _canonical_rule(grid):
    """Pure-Python mirror used only for tests and semantic rival checks."""
    h, w = len(grid), len(grid[0])
    out = full_grid(h, w, 0)
    for component in _components(grid):
        for r, c in _rect_cells(_bbox(component["cells"])):
            out[r][c] = component["color"]
    return out


def _rival_per_color_bbox(grid):
    """Wrong shortcut: merge disconnected same-colored components first."""
    h, w = len(grid), len(grid[0])
    out = full_grid(h, w, 0)
    by_color = {}
    for component in _components(grid):
        by_color.setdefault(component["color"], []).extend(component["cells"])
    for color in sorted(by_color):
        for r, c in _rect_cells(_bbox(by_color[color])):
            out[r][c] = color
    return out


def _rival_l_tromino_only(grid):
    """Wrong legacy rule: complete only three-cell 2x2 L objects."""
    out = _copy_grid(grid)
    for component in _components(grid):
        if _is_l_tromino(component["cells"]):
            for r, c in _rect_cells(_bbox(component["cells"])):
                out[r][c] = component["color"]
    return out


def _rival_first_object_only(grid):
    """Wrong quantifier: fill only the first component in reading order."""
    out = _copy_grid(grid)
    components = _components(grid)
    if components:
        component = components[0]
        for r, c in _rect_cells(_bbox(component["cells"])):
            out[r][c] = component["color"]
    return out


def semantic_observables(grid):
    """Recover exact controls and task-linked semantic branches from a grid."""
    components = _components(grid)
    boxes = [_bbox(component["cells"]) for component in components]
    expanding = sum(
        _bbox_area(box) > len(component["cells"])
        for component, box in zip(components, boxes)
    )
    non_l_expanding = sum(
        _bbox_area(box) > len(component["cells"])
        and not _is_l_tromino(component["cells"])
        for component, box in zip(components, boxes)
    )
    color_counts = Counter(component["color"] for component in components)
    per_color_bbox_traps = 0
    for color, count in color_counts.items():
        if count < 2:
            continue
        matching = [component for component in components if component["color"] == color]
        all_cells = [cell for component in matching for cell in component["cells"]]
        union_area = _bbox_area(_bbox(all_cells))
        independent_area = sum(_bbox_area(_bbox(component["cells"])) for component in matching)
        if union_area > independent_area:
            per_color_bbox_traps += 1
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_objects": len(components),
        "n_colors": len(color_counts),
        "expanding_objects": expanding,
        "non_l_expanding_objects": non_l_expanding,
        "l_tromino_objects": sum(_is_l_tromino(component["cells"]) for component in components),
        "repeated_colors": sum(count > 1 for count in color_counts.values()),
        "per_color_bbox_traps": per_color_bbox_traps,
        "cells_added_by_rule": sum(
            _bbox_area(box) - len(component["cells"])
            for component, box in zip(components, boxes)
        ),
    }


def observe_overrides(grid):
    facts = semantic_observables(grid)
    return {name: facts[name] for name in AXES}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the task-specific teaching grammar, including canonical inputs."""
    del difficulty, meta
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["empty grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["empty row"]
    h, w = len(grid), len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != w for row in grid):
        return ["ragged grid"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be integer colors in 0..9"]

    errors = []
    if not 7 <= h <= 8:
        errors.append(f"grid height {h} outside 7..8")
    if not 7 <= w <= 9:
        errors.append(f"grid width {w} outside 7..9")

    counts = Counter(value for row in grid for value in row)
    largest_nonzero = max((count for color, count in counts.items() if color != 0), default=0)
    if counts[0] <= largest_nonzero:
        errors.append("0 must be the modal background")

    components = _components(grid)
    if not 2 <= len(components) <= 4:
        errors.append(f"expected 2-4 nonzero components, got {len(components)}")
        return errors
    colors = {component["color"] for component in components}
    if len(colors) != 2:
        errors.append(f"expected exactly two nonzero colors, got {len(colors)}")

    boxes = []
    non_l = 0
    for index, component in enumerate(components):
        cells = component["cells"]
        box = _bbox(cells)
        boxes.append(box)
        r1, c1, r2, c2 = box
        bh, bw = r2 - r1 + 1, c2 - c1 + 1
        if not 3 <= len(cells) <= 5:
            errors.append(f"component {index} size {len(cells)} outside 3..5")
        if not 2 <= bh <= 3 or not 2 <= bw <= 3:
            errors.append(f"component {index} bbox {bh}x{bw} outside 2..3 by 2..3")
        if _bbox_area(box) <= len(cells):
            errors.append(f"component {index} already fills its bounding box")
        if not _is_l_tromino(cells):
            non_l += 1
    if non_l == 0:
        errors.append("expected at least one expanding non-L component")

    for (left_i, left), (right_i, right) in combinations(enumerate(boxes), 2):
        if _rect_cells(left) & _rect_cells(right):
            errors.append(f"component bounding boxes {left_i} and {right_i} overlap")
        left_cells = set(components[left_i]["cells"])
        right_cells = set(components[right_i]["cells"])
        if any(
            abs(lr - rr) + abs(lc - rc) == 1
            for lr, lc in left_cells
            for rr, rc in right_cells
        ):
            errors.append(f"components {left_i} and {right_i} touch orthogonally")
    return errors


def strict_canonical_like(grid):
    return self_check(grid)


def _draw_axis(ctx, overrides, name, default, lo, hi):
    if name in overrides:
        return ctx.draw_int(name, lo, hi)
    return ctx.draw_int(name, default, default)


def _shape_extent(shape):
    return max(r for r, _ in shape) + 1, max(c for _, c in shape) + 1


def _choose_shapes(n_objects, rng):
    shapes = [rng.choice(_NON_L_EXPANDING_SHAPES)]
    for _ in range(1, n_objects):
        shapes.append(rng.choice(_ALL_EXPANDING_SHAPES))
    rng.shuffle(shapes)
    return shapes


def _place_shapes(h, w, shapes, rng):
    """Place at most four shapes in separated 3x3 corner slots."""
    slots = [(0, 0), (0, w - 3), (h - 3, 0), (h - 3, w - 3)]
    rng.shuffle(slots)
    placements = []
    for shape, (slot_r, slot_c) in zip(shapes, slots):
        sh, sw = _shape_extent(shape)
        r0 = slot_r + rng.randint(0, 3 - sh)
        c0 = slot_c + rng.randint(0, 3 - sw)
        placements.append(tuple(sorted((r0 + r, c0 + c) for r, c in shape)))
    return placements


def _assign_colors(n_objects, rng):
    first, second = rng.sample(range(1, 10), 2)
    return [first if index % 2 == 0 else second for index in range(n_objects)]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Build one deterministic lawful input; Racket remains output authority."""
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    lane = sample_index % 3
    default_h, default_w = _CANONICAL_DIMENSIONS[lane]
    h = _draw_axis(ctx, overrides, "grid_h", default_h, 7, 8)
    w = _draw_axis(ctx, overrides, "grid_w", default_w, 7, 9)

    if difficulty == "easy":
        default_n = (2, 3, 2)[lane]
    elif difficulty == "hard":
        default_n = (3, 4, 4)[lane]
    else:
        default_n = (2, 3, 4)[lane]
    n_objects = _draw_axis(ctx, overrides, "n_objects", default_n, 2, 4)

    shapes = _choose_shapes(n_objects, ctx.draw_rng("shapes"))
    placements = _place_shapes(h, w, shapes, ctx.draw_rng("layout"))
    colors = _assign_colors(n_objects, ctx.draw_rng("colors"))

    grid = full_grid(h, w, 0)
    for color, cells in zip(colors, placements):
        for r, c in cells:
            grid[r][c] = color

    errors = self_check(grid)
    if errors:
        raise AssertionError(f"internal generator invariant failed: {errors}")
    return grid


def _witness_repeated_color_components(grid):
    return semantic_observables(grid)["per_color_bbox_traps"] >= 1


def _witness_non_l_expanding_component(grid):
    return semantic_observables(grid)["non_l_expanding_objects"] >= 1


def _witness_multiple_expanding_components(grid):
    return semantic_observables(grid)["expanding_objects"] >= 2


SEMANTIC_RIVALS = {
    "per_color_bbox": _rival_per_color_bbox,
    "l_tromino_only": _rival_l_tromino_only,
    "first_object_only": _rival_first_object_only,
}

LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {"per_color_bbox": _rival_per_color_bbox}

SEMANTIC_WITNESSES = {
    "repeated_color_components": _witness_repeated_color_components,
    "non_l_expanding_component": _witness_non_l_expanding_component,
    "multiple_expanding_components": _witness_multiple_expanding_components,
}

WITNESS_RIVALS = {
    "repeated_color_components": ["per_color_bbox"],
    "non_l_expanding_component": ["l_tromino_only"],
    "multiple_expanding_components": ["first_object_only"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Report any declared wrong rule that still fits every demonstration."""
    del query
    survivors = []
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(demo["input"]) == demo["output"] for demo in demos):
            survivors.append(name)
    if survivors:
        return ["declared competitors fit every demo: " + ", ".join(sorted(survivors))]
    return []
