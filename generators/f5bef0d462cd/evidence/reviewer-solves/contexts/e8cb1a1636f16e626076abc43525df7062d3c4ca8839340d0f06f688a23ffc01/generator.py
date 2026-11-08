"""Input generator for the three-panel geometric-transform analogy.

Each input contains three 4x4 panels separated by full color-9 columns.  The
first two panels expose exactly one transform from the canonical seven-name
order; the unchanged Racket authority applies that transform to the third panel.

The default 20-step sample-index schedule covers all seven transforms.  Every
four consecutive pairs contain four different transforms, including both
quarter-turn directions, which prevents fixed-transform and inverse-direction
rules from fitting all three demonstrations while changing the held-out query.
Explicit controls remain exact and independent of that teaching schedule.
"""
from __future__ import annotations

from functools import lru_cache
from itertools import combinations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "f5bef0d462cd"
TASK_ID = GENERATOR_ID
VERSION = "4.0.0"
RULE_HASH = "9a215441e24b"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0
LESSON_SCHEDULE_PERIOD = 20

SUMMARY = (
    "Three sparse 4x4 panels separated by full color-9 columns. Panel 1 is the "
    "unique canonical transform of panel 0, and panel 2 is an independently "
    "placed motif in a different color. Infer the panel-0→panel-1 transform "
    "and apply it to panel 2. Defaults cycle through all seven transforms."
)

INVARIANTS = [
    "the input is exactly three 4x4 panels separated by full color-9 columns",
    "panel0 and panel1 use one shared non-9 color; panel2 uses one different color",
    "panel0 has exactly one matching transform in the canonical seven-name order",
    "generated panel0 and panel2 motifs are connected and transform-asymmetric",
    "output = the inferred panel0-to-panel1 transform applied to panel2",
]

_TRANSFORM_NAMES = (
    "id",
    "rot90",
    "rot180",
    "rot270",
    "flip-h",
    "flip-v",
    "transpose",
)

# Binary pattern NNSS repeated: every cyclic four-pair window contains both
# non-self-inverse rotations plus two different self-inverse transforms.  This
# refutes both fixed-transform and wrong-direction rivals under every holdout.
_SCHEDULE_TRANSFORMS = (
    "rot90", "rot270", "id", "rot180",
    "rot90", "rot270", "flip-h", "flip-v",
    "rot90", "rot270", "transpose", "id",
    "rot90", "rot270", "rot180", "flip-h",
    "rot90", "rot270", "flip-v", "transpose",
)
assert len(_SCHEDULE_TRANSFORMS) == LESSON_SCHEDULE_PERIOD

AXES = {
    "transform": {
        "type": "str",
        "default": "sample-index seven-transform cycle",
        "valid": "|".join(_TRANSFORM_NAMES),
    },
    "motif_cells": {
        "type": "int",
        "default": "difficulty: easy=3, medium=4, hard=5; otherwise 3..5",
        "valid": "3..5",
    },
    "query_cells": {
        "type": "int",
        "default": "difficulty-weighted 3..5 value fixed within each seed's lesson",
        "valid": "3..5",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []


def _copy(grid):
    return [list(row) for row in grid]


def _rot_cw(grid):
    return [list(row) for row in zip(*grid[::-1])]


def _rot_ccw(grid):
    return [list(row) for row in zip(*grid)][::-1]


def _rot180(grid):
    return [list(reversed(row)) for row in reversed(grid)]


def _flip_lr(grid):
    return [list(reversed(row)) for row in grid]


def _flip_ud(grid):
    return [list(row) for row in reversed(grid)]


def _transpose(grid):
    return [list(row) for row in zip(*grid)]


_TRANSFORMS = {
    "id": _copy,
    "rot90": _rot_cw,
    "rot180": _rot180,
    "rot270": _rot_ccw,
    "flip-h": _flip_lr,
    "flip-v": _flip_ud,
    "transpose": _transpose,
}
_INVERSE = {
    "id": "id",
    "rot90": "rot270",
    "rot180": "rot180",
    "rot270": "rot90",
    "flip-h": "flip-h",
    "flip-v": "flip-v",
    "transpose": "transpose",
}


def _tuplize(grid):
    return tuple(tuple(row) for row in grid)


def _support_connected(cells):
    cells = set(cells)
    if not cells:
        return False
    seen = {next(iter(cells))}
    todo = list(seen)
    while todo:
        r, c = todo.pop()
        for point in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
            if point in cells and point not in seen:
                seen.add(point)
                todo.append(point)
    return seen == cells


def _paint(cells, color):
    panel = full_grid(4, 4, 0)
    for r, c in cells:
        panel[r][c] = color
    return panel


def _transform_orbit(panel):
    return {_tuplize(_TRANSFORMS[name](panel)) for name in _TRANSFORM_NAMES}


@lru_cache(maxsize=3)
def _shape_pool(cell_count):
    """All connected 4x4 supports whose seven authority transforms differ."""
    if type(cell_count) is not int or not 3 <= cell_count <= 5:
        raise ValueError("cell_count must be an integer in [3, 5]")
    points = tuple((r, c) for r in range(4) for c in range(4))
    result = []
    for cells in combinations(points, cell_count):
        if not _support_connected(cells):
            continue
        if len(_transform_orbit(_paint(cells, 1))) != len(_TRANSFORM_NAMES):
            continue
        result.append(tuple(cells))
    if not result:
        raise RuntimeError(f"no transform-asymmetric connected shapes for {cell_count} cells")
    return tuple(result)


def schedule_profile(seed, sample_index, difficulty=None):
    """Return the default transform from the exact 20-step lesson schedule."""
    del difficulty
    return _SCHEDULE_TRANSFORMS[(int(seed) + int(sample_index)) % LESSON_SCHEDULE_PERIOD]


def _validate_request(difficulty, overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be one of None, easy, medium, hard")
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")

    if "transform" in overrides and overrides["transform"] is not None:
        value = overrides["transform"]
        if type(value) is not str or value not in _TRANSFORM_NAMES:
            raise ValueError(f"transform must be one of {_TRANSFORM_NAMES}, not {value!r}")

    for name in ("motif_cells", "query_cells"):
        if name not in overrides or overrides[name] is None:
            continue
        value = overrides[name]
        if type(value) is not int:
            raise TypeError(f"{name} must be an integer, not {type(value).__name__}")
        if not 3 <= value <= 5:
            raise ValueError(f"{name}={value} outside [3, 5]")


def _count(ctx, name, difficulty):
    if name in ctx.overrides and ctx.overrides[name] is not None:
        return ctx.draw_int_strict(name, 3, 5)
    scheduled = None
    if name == "motif_cells":
        if difficulty == "easy":
            scheduled = 3
        elif difficulty == "medium":
            scheduled = 4
        elif difficulty == "hard":
            scheduled = 5
    elif name == "query_cells":
        # Keep this observable size constant inside a lesson.  The previous
        # sample-index parity schedule perfectly encoded rot90 versus rot270.
        # Varying by seed preserves support without leaking transform direction.
        variant = int(ctx.seed) % 3
        if difficulty == "easy":
            scheduled = (4, 3, 5)[variant]
        elif difficulty == "medium":
            scheduled = (3, 5, 4)[variant]
        elif difficulty == "hard":
            scheduled = (5, 4, 3)[variant]
        else:
            scheduled = (3, 4, 5)[variant]
    if scheduled is not None:
        # Single-option draws preserve exact default provenance for the shared
        # override checker without changing the deterministic lesson schedule.
        return int(ctx.draw_choice(name, (scheduled,)))
    return ctx.draw_int_strict(name, 3, 5)


def _transform_name(ctx, seed, sample_index, difficulty):
    if "transform" in ctx.overrides and ctx.overrides["transform"] is not None:
        return ctx.draw_choice("transform", _TRANSFORM_NAMES)
    scheduled = schedule_profile(seed, sample_index, difficulty)
    return str(ctx.draw_choice("transform", (scheduled,)))


def _assemble(panel0, panel1, panel2):
    grid = full_grid(4, 14, 0)
    for panel_index, panel in enumerate((panel0, panel1, panel2)):
        left = panel_index * 5
        for r in range(4):
            for c in range(4):
                grid[r][left + c] = panel[r][c]
    for r in range(4):
        grid[r][4] = 9
        grid[r][9] = 9
    return grid


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
    name = _transform_name(ctx, seed, sample_index, difficulty)
    motif_cells = _count(ctx, "motif_cells", difficulty)
    query_cells = _count(ctx, "query_cells", difficulty)
    source_color, query_color = ctx.draw_distinct_colors("colors", n=2, exclude={0, 9})

    panel0 = _paint(ctx.draw_rng("motif_shape").choice(_shape_pool(motif_cells)), source_color)
    panel1 = _TRANSFORMS[name](panel0)
    panel2 = _paint(ctx.draw_rng("query_shape").choice(_shape_pool(query_cells)), query_color)
    grid = _assemble(panel0, panel1, panel2)
    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise RuntimeError("constructive generator produced invalid input: " + "; ".join(errors))
    return grid


def _grid_error(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        return "expected a nonempty rectangular grid"
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return "expected nonempty rows"
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return "grid must be rectangular"
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return "cells must be integer ARC colors 0..9, excluding booleans"
    return None


def _split_panels(grid):
    if len(grid) != 4 or len(grid[0]) != 14:
        raise ValueError("expected a 4x14 input")
    if any(row[4] != 9 or row[9] != 9 for row in grid):
        raise ValueError("expected full color-9 dividers at columns 4 and 9")
    return (
        [list(row[0:4]) for row in grid],
        [list(row[5:9]) for row in grid],
        [list(row[10:14]) for row in grid],
    )


def _panel_support(panel):
    return {(r, c) for r, row in enumerate(panel) for c, value in enumerate(row) if value != 0}


def _panel_colors(panel):
    return {value for row in panel for value in row if value != 0}


def _matching_transforms(panel0, panel1):
    return [name for name in _TRANSFORM_NAMES if _TRANSFORMS[name](panel0) == panel1]


def _infer_transform(grid):
    panel0, panel1, _ = _split_panels(grid)
    matches = _matching_transforms(panel0, panel1)
    if len(matches) != 1:
        raise ValueError(f"expected exactly one transform from panel0 to panel1, got {matches}")
    return matches[0]


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty, meta
    first = _grid_error(grid)
    if first:
        return [first]
    errors = []
    if len(grid) != 4 or len(grid[0]) != 14:
        return [f"expected fixed canonical input shape 4x14, got {len(grid)}x{len(grid[0])}"]
    if any(row[4] != 9 or row[9] != 9 for row in grid):
        errors.append("expected full color-9 dividers at columns 4 and 9")
    if any(value == 9 for row in grid for c, value in enumerate(row) if c not in (4, 9)):
        errors.append("separator color 9 must not appear inside a panel")
    if errors:
        return errors

    panel0, panel1, panel2 = _split_panels(grid)
    panels = (panel0, panel1, panel2)
    for index, panel in enumerate(panels):
        count = len(_panel_support(panel))
        colors = _panel_colors(panel)
        if not 3 <= count <= 5:
            errors.append(f"panel {index} must have 3..5 motif cells, got {count}")
        if len(colors) != 1:
            errors.append(f"panel {index} must use exactly one nonzero color, got {sorted(colors)}")
        if count and not _support_connected(_panel_support(panel)):
            errors.append(f"panel {index} motif must be 4-connected")

    colors0 = _panel_colors(panel0)
    colors1 = _panel_colors(panel1)
    colors2 = _panel_colors(panel2)
    if colors0 != colors1:
        errors.append("panel0 and panel1 must use the same motif color")
    if colors0 & colors2:
        errors.append("panel2 must use a different motif color")
    matches = _matching_transforms(panel0, panel1)
    if len(matches) != 1:
        errors.append(f"expected exactly one transform mapping panel0 to panel1, got {matches}")
    return errors


def strict_canonical_like(grid):
    """The generated manifold is the canonical 4x14 sparse-panel domain."""
    return self_check(grid)


def observe_overrides(grid):
    errors = self_check(grid)
    if errors:
        raise ValueError("cannot observe controls on invalid input: " + "; ".join(errors))
    panel0, _, panel2 = _split_panels(grid)
    return {
        "transform": _infer_transform(grid),
        "motif_cells": len(_panel_support(panel0)),
        "query_cells": len(_panel_support(panel2)),
    }


def _intended_output(grid):
    _, _, panel2 = _split_panels(grid)
    return _TRANSFORMS[_infer_transform(grid)](panel2)


def _fixed(grid, name):
    _, _, panel2 = _split_panels(grid)
    return _TRANSFORMS[name](panel2)


def _fixed_id(grid):
    return _fixed(grid, "id")


def _fixed_rot90(grid):
    return _fixed(grid, "rot90")


def _fixed_rot180(grid):
    return _fixed(grid, "rot180")


def _fixed_rot270(grid):
    return _fixed(grid, "rot270")


def _fixed_flip_h(grid):
    return _fixed(grid, "flip-h")


def _fixed_flip_v(grid):
    return _fixed(grid, "flip-v")


def _fixed_transpose(grid):
    return _fixed(grid, "transpose")


def _inverse_transform(grid):
    _, _, panel2 = _split_panels(grid)
    return _TRANSFORMS[_INVERSE[_infer_transform(grid)]](panel2)


def _return_panel1(grid):
    _, panel1, _ = _split_panels(grid)
    return _copy(panel1)


SEMANTIC_RIVALS = {
    "fixed_id": _fixed_id,
    "fixed_rot90": _fixed_rot90,
    "fixed_rot180": _fixed_rot180,
    "fixed_rot270": _fixed_rot270,
    "fixed_flip-h": _fixed_flip_h,
    "fixed_flip-v": _fixed_flip_v,
    "fixed_transpose": _fixed_transpose,
    "inverse_transform": _inverse_transform,
    "return_panel1": _return_panel1,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)


def _rival_differs(name, grid):
    return SEMANTIC_RIVALS[name](grid) != _intended_output(grid)


SEMANTIC_WITNESSES = {
    name: (lambda grid, name=name: _rival_differs(name, grid))
    for name in SEMANTIC_RIVALS
}
WITNESS_RIVALS = {name: [name] for name in SEMANTIC_RIVALS}


def lesson_identifiable(demos, query):
    """Return declared rivals that fit every demo but alter the query label."""
    return [
        f"{name} fits every demonstration but changes the query"
        for name, rival in LESSON_COMPETITORS.items()
        if all(rival(pair["input"]) == pair["output"] for pair in demos)
        and rival(query["input"]) != query["output"]
    ]
