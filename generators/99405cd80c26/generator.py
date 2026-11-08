"""Generator for M140 — infer a panel transform and apply it to a query.

The input is a fixed 4x14 grid containing three 4x4 panels separated by
full-height color-8 columns.  Panel B is panel A under one of the eight D4
transforms.  The selected transform is then applied to panel C to form the
4x4 answer.

Ordinary draws keep the canonical geometry and palette-role structure, use
connected monochrome motifs, schedule all eight transform branches, and make
both A and C D4-asymmetric.  Consequently A->B identifies exactly one
transform and C separates every rival transform output.
"""
from __future__ import annotations

from functools import lru_cache
from itertools import combinations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "99405cd80c26"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "20020b17585c"
EXAMPLES_NEEDED = 5
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "Read the 4x14 input as three 4x4 panels separated by full color-8 "
    "columns. Infer the D4 transform mapping monochrome panel A to panel B, "
    "then apply that same transform to differently colored panel C."
)

INVARIANTS = [
    "input is 4x14 with full color-8 separator columns 4 and 9",
    "A and B are nonempty monochrome panels in the same color",
    "C is nonempty, monochrome, and uses a different color",
    "ordinary A uniquely identifies one of all eight D4 transforms",
    "ordinary A and C are connected and have full eight-image D4 orbits",
]

ALL_TRANSFORMS = (
    "id",
    "rot90",
    "rot180",
    "rot270",
    "flip-h",
    "flip-v",
    "transpose",
    "anti-transpose",
)
SCHEDULE_PROFILES = ALL_TRANSFORMS

AXES = {
    "transform": {
        "type": "str",
        "default": "eight-example schedule",
        "valid": "id|rot90|rot180|rot270|flip-h|flip-v|transpose|anti-transpose",
    },
    "exemplar_cells": {
        "type": "int",
        "default": "difficulty-aware 3..6",
        "valid": "3..6",
    },
    "query_cells": {
        "type": "int",
        "default": "difficulty-aware 3..6",
        "valid": "3..6",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, object], ...] = ()

_PANEL_N = 4
_GRID_W = 3 * _PANEL_N + 2
_SEPARATOR_COLOR = 8
_MOTIF_COLORS = tuple(range(1, 8))
_CELLS = tuple((r, c) for r in range(_PANEL_N) for c in range(_PANEL_N))
_OBSERVED_CANONICAL_FAMILY = ("id", "rot90", "flip-h")


def _freeze(grid):
    return tuple(tuple(row) for row in grid)


def _grid_errors(grid) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                return [f"cell ({r},{c}) is not a literal ARC color 0..9: {value!r}"]
    return []


def _transform(panel, name):
    """Return a fresh square panel under the named D4 transform."""
    if name == "id":
        return [list(row) for row in panel]
    if name == "rot90":
        return [list(row) for row in zip(*panel[::-1])]
    if name == "rot180":
        return [list(reversed(row)) for row in reversed(panel)]
    if name == "rot270":
        return [list(row) for row in zip(*panel)][::-1]
    if name == "flip-h":
        return [list(reversed(row)) for row in panel]
    if name == "flip-v":
        return [list(row) for row in reversed(panel)]
    if name == "transpose":
        return [list(row) for row in zip(*panel)]
    if name == "anti-transpose":
        return _transform(_transform(panel, "transpose"), "rot180")
    raise ValueError(f"unknown transform: {name!r}")


def _panels(grid):
    n = len(grid)
    return (
        [list(row[:n]) for row in grid],
        [list(row[n + 1:2 * n + 1]) for row in grid],
        [list(row[2 * n + 2:3 * n + 2]) for row in grid],
    )


def _support(panel):
    return frozenset(
        (r, c)
        for r, row in enumerate(panel)
        for c, value in enumerate(row)
        if value != 0
    )


def _panel_colors(panel):
    return {value for row in panel for value in row if value != 0}


def _is_connected(cells) -> bool:
    cells = set(cells)
    if not cells:
        return False
    pending = [next(iter(cells))]
    seen = set(pending)
    while pending:
        r, c = pending.pop()
        for neighbor in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
            if neighbor in cells and neighbor not in seen:
                seen.add(neighbor)
                pending.append(neighbor)
    return seen == cells


def _matching_transforms(panel_a, panel_b):
    target = _freeze(panel_b)
    return [name for name in ALL_TRANSFORMS if _freeze(_transform(panel_a, name)) == target]


def _infer_transform(grid):
    panel_a, panel_b, _ = _panels(grid)
    matches = _matching_transforms(panel_a, panel_b)
    if not matches:
        raise ValueError("no D4 transform maps panel A to panel B")
    # This exactly mirrors the canonical Racket rule's priority order.
    return matches[0]


def _apply_rule(grid):
    """Pure Python mirror for semantic checks; Racket remains authoritative."""
    _, _, panel_c = _panels(grid)
    return _transform(panel_c, _infer_transform(grid))


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the authority-compatible three-panel input grammar."""
    del difficulty, meta
    errors = _grid_errors(grid)
    if errors:
        return errors

    n = len(grid)
    width = len(grid[0])
    if width != 3 * n + 2:
        return [f"expected n x (3n+2) grid, got {n}x{width}"]

    separator_columns = (n, 2 * n + 1)
    for column in separator_columns:
        bad_rows = [r for r in range(n) if grid[r][column] != _SEPARATOR_COLOR]
        if bad_rows:
            errors.append(
                f"column {column} must be full color-{_SEPARATOR_COLOR}; "
                f"bad rows {bad_rows[:3]}"
            )

    panel_a, panel_b, panel_c = _panels(grid)
    for index, panel in enumerate((panel_a, panel_b, panel_c), start=1):
        if any(value == _SEPARATOR_COLOR for row in panel for value in row):
            errors.append(f"panel {index} contains reserved separator color {_SEPARATOR_COLOR}")
        colors = _panel_colors(panel)
        if not colors:
            errors.append(f"panel {index} must contain a nonzero motif")
        elif len(colors) != 1:
            errors.append(f"panel {index} must be monochrome, found {sorted(colors)}")

    if errors:
        return errors

    color_a = next(iter(_panel_colors(panel_a)))
    color_b = next(iter(_panel_colors(panel_b)))
    color_c = next(iter(_panel_colors(panel_c)))
    if color_a != color_b:
        errors.append(f"panels A and B must share one color, got {color_a} and {color_b}")
    if color_c == color_a:
        errors.append("panel C must use a color distinct from panels A/B")

    matches = _matching_transforms(panel_a, panel_b)
    if not matches:
        errors.append("no D4 transform maps panel A to panel B")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Require the morphology shared by canonical inputs and ordinary draws."""
    errors = self_check(grid)
    if errors:
        return errors
    if len(grid) != _PANEL_N or len(grid[0]) != _GRID_W:
        errors.append(f"canonical profile is {_PANEL_N}x{_GRID_W}")
        return errors

    palette = {value for row in grid for value in row}
    if len(palette) != 4:
        errors.append(f"canonical profile has exactly four colors, found {sorted(palette)}")

    for label, panel in zip("ABC", _panels(grid)):
        cells = _support(panel)
        if not 3 <= len(cells) <= 6:
            errors.append(f"panel {label} must contain 3..6 motif cells, found {len(cells)}")
        if not _is_connected(cells):
            errors.append(f"panel {label} motif must be 4-connected")
    return errors


def _teaching_reasons(grid) -> list[str]:
    """Curriculum-only constraints that need not hold for every canonical row."""
    reasons = strict_canonical_like(grid)
    if reasons:
        return reasons
    panel_a, panel_b, panel_c = _panels(grid)
    matches = _matching_transforms(panel_a, panel_b)
    if len(matches) != 1:
        reasons.append(f"A->B transform must be unique, got {matches}")
    if len({_freeze(_transform(panel_a, name)) for name in ALL_TRANSFORMS}) != 8:
        reasons.append("panel A must have a full eight-image D4 orbit")
    if len({_freeze(_transform(panel_c, name)) for name in ALL_TRANSFORMS}) != 8:
        reasons.append("panel C must have a full eight-image D4 orbit")
    return reasons


def _transform_cells(cells, name):
    panel = full_grid(_PANEL_N, _PANEL_N, 0)
    for r, c in cells:
        panel[r][c] = 1
    transformed = _transform(panel, name)
    return frozenset(
        (r, c)
        for r, row in enumerate(transformed)
        for c, value in enumerate(row)
        if value
    )


def _full_d4_orbit(cells) -> bool:
    return len({_transform_cells(cells, name) for name in ALL_TRANSFORMS}) == 8


@lru_cache(maxsize=None)
def _connected_asymmetric_masks(cell_count: int):
    masks = []
    for cells in combinations(_CELLS, cell_count):
        frozen = frozenset(cells)
        if _is_connected(frozen) and _full_d4_orbit(frozen):
            masks.append(tuple(sorted(frozen)))
    if not masks:
        raise ValueError(f"no connected D4-asymmetric 4x4 mask with {cell_count} cells")
    return tuple(masks)


def _paint_panel(cells, color: int):
    panel = full_grid(_PANEL_N, _PANEL_N, 0)
    for r, c in cells:
        panel[r][c] = color
    return panel


def _paste_panel(grid, panel, left: int) -> None:
    for r, row in enumerate(panel):
        for c, value in enumerate(row):
            grid[r][left + c] = value


def schedule_profile(seed, sample_index, difficulty=None):
    """Every sliding eight-example window contains all D4 branches once."""
    del difficulty
    return ALL_TRANSFORMS[(int(seed) + int(sample_index)) % len(ALL_TRANSFORMS)]


def _cell_bounds(difficulty):
    if difficulty == "easy":
        return 3, 4
    if difficulty == "hard":
        return 4, 6
    return 3, 5


def _draw_axis_int(ctx, overrides, label: str, difficulty) -> int:
    if label in overrides:
        return ctx.draw_int(label, 3, 6)
    lo, hi = _cell_bounds(difficulty)
    return ctx.draw_int(label, lo, hi)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic, canonical-profile, transform-identifying input."""
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError("unknown override axis(es): " + ", ".join(unknown))

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    scheduled = schedule_profile(seed, sample_index, difficulty)
    if "transform" in overrides:
        transform = ctx.draw_choice("transform", list(ALL_TRANSFORMS))
    else:
        transform = ctx.draw_choice("transform", [scheduled])

    exemplar_cells = _draw_axis_int(ctx, overrides, "exemplar_cells", difficulty)
    query_cells = _draw_axis_int(ctx, overrides, "query_cells", difficulty)

    exemplar_rng = ctx.draw_rng("exemplar_mask")
    query_rng = ctx.draw_rng("query_mask")
    palette_rng = ctx.draw_rng("palette")

    exemplar_support = exemplar_rng.choice(_connected_asymmetric_masks(exemplar_cells))
    query_candidates = [
        mask
        for mask in _connected_asymmetric_masks(query_cells)
        if frozenset(mask) != frozenset(exemplar_support)
    ]
    query_support = query_rng.choice(query_candidates or _connected_asymmetric_masks(query_cells))
    exemplar_color, query_color = palette_rng.sample(list(_MOTIF_COLORS), 2)

    panel_a = _paint_panel(exemplar_support, exemplar_color)
    panel_b = _transform(panel_a, transform)
    panel_c = _paint_panel(query_support, query_color)

    grid = full_grid(_PANEL_N, _GRID_W, 0)
    for r in range(_PANEL_N):
        grid[r][_PANEL_N] = _SEPARATOR_COLOR
        grid[r][2 * _PANEL_N + 1] = _SEPARATOR_COLOR
    _paste_panel(grid, panel_a, 0)
    _paste_panel(grid, panel_b, _PANEL_N + 1)
    _paste_panel(grid, panel_c, 2 * _PANEL_N + 2)
    return grid


def observe_overrides(grid):
    panel_a, _, panel_c = _panels(grid)
    return {
        "transform": _infer_transform(grid),
        "exemplar_cells": len(_support(panel_a)),
        "query_cells": len(_support(panel_c)),
    }


def _rival_fixed(name):
    def rival(grid):
        return _transform(_panels(grid)[2], name)
    return rival


def _rival_copy_panel_b(grid):
    return [list(row) for row in _panels(grid)[1]]


def _rival_observed_transform_family_only(grid):
    panel_a, panel_b, panel_c = _panels(grid)
    target = _freeze(panel_b)
    for name in _OBSERVED_CANONICAL_FAMILY:
        if _freeze(_transform(panel_a, name)) == target:
            return _transform(panel_c, name)
    # A solver that learned only the observed family has no rule for any other
    # branch; the most conservative shortcut is to copy C unchanged.
    return _transform(panel_c, "id")


def _transform_witness(expected):
    def witness(grid):
        return not _teaching_reasons(grid) and _infer_transform(grid) == expected
    return witness


def _safe_name(name: str) -> str:
    return name.replace("-", "_")


SEMANTIC_RIVALS = {
    f"fixed_{_safe_name(name)}": _rival_fixed(name)
    for name in ALL_TRANSFORMS
}
SEMANTIC_RIVALS.update({
    "copy_panel_b": _rival_copy_panel_b,
    "observed_transform_family_only": _rival_observed_transform_family_only,
})

SEMANTIC_WITNESSES = {
    f"transform_{_safe_name(name)}_unique": _transform_witness(name)
    for name in ALL_TRANSFORMS
}

WITNESS_RIVALS = {}
for name in ALL_TRANSFORMS:
    witness_name = f"transform_{_safe_name(name)}_unique"
    rivals = [
        f"fixed_{_safe_name(other)}"
        for other in ALL_TRANSFORMS
        if other != name
    ]
    rivals.append("copy_panel_b")
    if name not in _OBSERVED_CANONICAL_FAMILY:
        rivals.append("observed_transform_family_only")
    WITNESS_RIVALS[witness_name] = rivals

LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    "observed_transform_family_only": _rival_observed_transform_family_only,
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require a worker-serializable lesson that refutes every declared rival."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"lesson needs at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query must contain an input grid"]

    errors: list[str] = []
    profiles = set()
    survivors = set(LESSON_COMPETITORS)

    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            errors.append(f"demo {index} must contain input and output grids")
            continue
        grid = demo["input"]
        teaching_errors = _teaching_reasons(grid)
        if teaching_errors:
            errors.append(f"demo {index} is outside the teaching grammar: {teaching_errors[0]}")
            continue
        authoritative = _apply_rule(grid)
        if demo["output"] != authoritative:
            errors.append(f"demo {index} output disagrees with the selected rule")
            continue
        profiles.add(_infer_transform(grid))
        for name, competitor in LESSON_COMPETITORS.items():
            if competitor(grid) != authoritative:
                survivors.discard(name)

    if len(profiles) < 2:
        errors.append("demonstrations need at least two distinct transform branches")

    query_grid = query["input"]
    query_errors = _teaching_reasons(query_grid)
    if query_errors:
        errors.append(f"query is outside the teaching grammar: {query_errors[0]}")
    else:
        if "output" in query and query["output"] != _apply_rule(query_grid):
            errors.append("query output disagrees with the selected rule")

    if survivors:
        errors.append("demonstrations leave rival rule(s) alive: " + ", ".join(sorted(survivors)))
    return errors
