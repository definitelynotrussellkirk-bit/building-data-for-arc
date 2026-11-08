"""Generator for c07088fab0f0 — complete the missing symmetric quadrant.

A centered gray cross divides a square grid into four equal quadrants. Three
quadrants contain reflected versions of one connected colored shape and one
quadrant is empty. The output fills only that missing quadrant with the
corresponding reflection.
"""
from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "c07088fab0f0"
TASK_ID = "c07088fab0f0"
VERSION = "3.0.0"
RULE_HASH = "722f434cd224"

SUMMARY = (
    "A centered color-5 cross divides an odd square grid into four equal "
    "quadrants. Exactly three quadrants contain the same connected colored "
    "shape under the horizontal/vertical reflection appropriate to their "
    "position; exactly one quadrant is empty. Fill only the missing quadrant."
)

INVARIANTS = [
    "the grid is an odd square with one centered full color-5 row and column",
    "the cross is the only color-5 content",
    "exactly three quadrants are filled and exactly one is empty",
    "filled quadrants use one non-{0,5} color and equal-size connected shapes",
    "the three shapes are the correct quadrant reflections of one canonical shape",
    "each quadrant-local shape bounding box is anchored at row 0 and column 0",
]

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

_COLORS = (1, 2, 3, 4, 6, 7, 8, 9)
_QUADRANT_NAMES = ("top_left", "top_right", "bottom_left", "bottom_right")
_DIFFICULTY_Q = {
    "easy": (4, 5, 6),
    "medium": (4, 5, 6, 7, 8, 9),
    "hard": (4, 5, 7, 9, 10, 12),
}

AXES = {
    "quad_size": {
        "type": "int",
        "default": "band choice; grid side is 2*quad_size+1",
        "valid": "4..12",
    },
    "missing_quadrant": {
        "type": "str",
        "default": "balanced schedule across sample_index",
        "valid": "|".join(_QUADRANT_NAMES),
    },
    "shape_cells": {
        "type": "int",
        "default": "balanced 3..10-cell schedule",
        "valid": "3..10",
    },
    "foreground_color": {
        "type": "color",
        "default": "rng non-{0,5}",
        "valid": "1|2|3|4|6|7|8|9",
    },
}

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.25

Cell = tuple[int, int]
Shape = tuple[Cell, ...]

# Deterministic asymmetric fallbacks. Every size fits a 4x4 quadrant and has
# four distinct H/V orientations, which prevents orientation-free lessons.
_FALLBACK_SHAPES: dict[int, Shape] = {
    3: ((0, 0), (0, 1), (1, 0)),
    4: ((0, 0), (0, 1), (0, 2), (1, 0)),
    5: ((0, 0), (0, 1), (0, 2), (0, 3), (1, 0)),
    6: ((0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 1)),
    7: ((0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 1), (1, 2)),
    8: ((0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 1), (1, 2), (2, 0)),
    9: (
        (0, 0), (0, 1), (0, 2), (0, 3),
        (1, 0), (1, 1), (1, 2), (1, 3), (2, 0),
    ),
    10: (
        (0, 0), (0, 1), (0, 2), (0, 3),
        (1, 0), (1, 1), (1, 2), (1, 3), (2, 0), (2, 1),
    ),
}


def _is_arc_grid(grid: Any) -> bool:
    return bool(
        isinstance(grid, list)
        and grid
        and isinstance(grid[0], list)
        and grid[0]
        and all(isinstance(row, list) and len(row) == len(grid[0]) for row in grid)
        and all(
            isinstance(value, int)
            and not isinstance(value, bool)
            and 0 <= value <= 9
            for row in grid
            for value in row
        )
    )


def _normalize(cells: Iterable[Cell]) -> Shape:
    seq = tuple(sorted(set(cells)))
    if not seq:
        return ()
    min_r = min(r for r, _ in seq)
    min_c = min(c for _, c in seq)
    return tuple(sorted((r - min_r, c - min_c) for r, c in seq))


def _mirror_h(cells: Iterable[Cell]) -> Shape:
    cells = _normalize(cells)
    if not cells:
        return ()
    max_c = max(c for _, c in cells)
    return _normalize((r, max_c - c) for r, c in cells)


def _mirror_v(cells: Iterable[Cell]) -> Shape:
    cells = _normalize(cells)
    if not cells:
        return ()
    max_r = max(r for r, _ in cells)
    return _normalize((max_r - r, c) for r, c in cells)


def _orient(index: int, cells: Iterable[Cell]) -> Shape:
    cells = _normalize(cells)
    if index == 0:
        return cells
    if index == 1:
        return _mirror_h(cells)
    if index == 2:
        return _mirror_v(cells)
    if index == 3:
        return _mirror_v(_mirror_h(cells))
    raise ValueError(f"invalid quadrant index {index}")


def _orientations(cells: Iterable[Cell]) -> tuple[Shape, ...]:
    return tuple(_orient(index, cells) for index in range(4))


def _connected(cells: Iterable[Cell]) -> bool:
    pending = set(cells)
    if not pending:
        return False
    seen = {next(iter(pending))}
    stack = list(seen)
    while stack:
        r, c = stack.pop()
        for nxt in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
            if nxt in pending and nxt not in seen:
                seen.add(nxt)
                stack.append(nxt)
    return seen == pending


def _quadrant_origins(q: int) -> tuple[Cell, ...]:
    return ((0, 0), (0, q + 1), (q + 1, 0), (q + 1, q + 1))


def _sample_shape(rng, n_cells: int, q: int) -> Shape:
    max_dim = min(q, 5)
    for _ in range(256):
        cells: set[Cell] = {(0, 0)}
        while len(cells) < n_cells:
            frontier: set[Cell] = set()
            for r, c in cells:
                for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                    if (nr, nc) not in cells:
                        frontier.add((nr, nc))
            candidate = rng.choice(sorted(frontier))
            trial = _normalize((*cells, candidate))
            height = max(r for r, _ in trial) + 1
            width = max(c for _, c in trial) + 1
            if height <= max_dim and width <= max_dim:
                cells = set(trial)
        shape = _normalize(cells)
        if len(set(_orientations(shape))) == 4:
            return shape
    return _FALLBACK_SHAPES[n_cells]


def _validate_override_keys(overrides: dict[str, Any]) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")


def _draw_scheduled_choice(ctx, label: str, scheduled: Any, options: tuple[Any, ...]):
    if ctx.overrides.get(label) is not None:
        return ctx.draw_choice(label, options)
    return ctx.draw_choice(label, (scheduled,))


def _draw_scheduled_int(ctx, label: str, scheduled: int, lo: int, hi: int) -> int:
    if ctx.overrides.get(label) is not None:
        return ctx.draw_int(label, lo, hi)
    return ctx.draw_int(label, scheduled, scheduled)


def _analyze(grid: Any) -> dict[str, Any]:
    facts: dict[str, Any] = {"errors": []}
    errors: list[str] = facts["errors"]
    if not _is_arc_grid(grid):
        errors.append("grid must be a nonempty rectangular ARC grid")
        return facts

    h, w = len(grid), len(grid[0])
    if h != w or h % 2 != 1:
        errors.append("grid must be an odd square")
        return facts
    q = h // 2
    facts["quad_size"] = q
    if not 4 <= q <= 12:
        errors.append(f"quadrant size {q} outside 4..12")

    full_rows = [r for r in range(h) if all(grid[r][c] == 5 for c in range(w))]
    full_cols = [c for c in range(w) if all(grid[r][c] == 5 for r in range(h))]
    if full_rows != [q]:
        errors.append(f"expected only centered full-5 row {q}; found {full_rows}")
    if full_cols != [q]:
        errors.append(f"expected only centered full-5 column {q}; found {full_cols}")
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            on_cross = r == q or c == q
            if on_cross and value != 5:
                errors.append(f"cross cell ({r},{c}) is {value}, not 5")
            elif not on_cross and value == 5:
                errors.append(f"stray color-5 cell outside cross at ({r},{c})")
    if errors:
        return facts

    quadrant_cells: list[Shape] = []
    quadrant_colors: list[tuple[int, ...]] = []
    for origin_r, origin_c in _quadrant_origins(q):
        local: list[Cell] = []
        colors: list[int] = []
        for local_r in range(q):
            for local_c in range(q):
                value = grid[origin_r + local_r][origin_c + local_c]
                if value != 0:
                    local.append((local_r, local_c))
                    colors.append(value)
        quadrant_cells.append(tuple(local))
        quadrant_colors.append(tuple(colors))

    empty = [index for index, cells in enumerate(quadrant_cells) if not cells]
    filled = [index for index, cells in enumerate(quadrant_cells) if cells]
    if len(empty) != 1 or len(filled) != 3:
        errors.append(
            f"expected exactly one empty and three filled quadrants; "
            f"found {len(empty)} empty and {len(filled)} filled"
        )
        return facts

    missing = empty[0]
    facts["missing_index"] = missing
    facts["missing_quadrant"] = _QUADRANT_NAMES[missing]
    facts["filled_indices"] = tuple(filled)

    all_colors = {value for colors in quadrant_colors for value in colors}
    if len(all_colors) != 1 or next(iter(all_colors), 0) not in _COLORS:
        errors.append(
            "filled quadrants must use exactly one foreground color from "
            f"{_COLORS}; found {sorted(all_colors)}"
        )
        return facts
    foreground = next(iter(all_colors))
    facts["foreground_color"] = foreground

    sizes = {len(quadrant_cells[index]) for index in filled}
    if len(sizes) != 1:
        errors.append(f"filled quadrants have unequal shape sizes {sorted(sizes)}")
        return facts
    shape_cells = next(iter(sizes))
    facts["shape_cells"] = shape_cells
    if not 3 <= shape_cells <= 10:
        errors.append(f"shape cell count {shape_cells} outside 3..10")

    canonical: Shape | None = None
    for index in filled:
        local = quadrant_cells[index]
        if min(r for r, _ in local) != 0 or min(c for _, c in local) != 0:
            errors.append(f"quadrant {_QUADRANT_NAMES[index]} shape is not bbox-anchored")
        if not _connected(local):
            errors.append(f"quadrant {_QUADRANT_NAMES[index]} shape is disconnected")
        candidate = _orient(index, local)
        if canonical is None:
            canonical = candidate
        elif candidate != canonical:
            errors.append(
                f"quadrant {_QUADRANT_NAMES[index]} is not the required reflection"
            )
    if canonical is not None:
        facts["canonical_shape"] = canonical
        facts["quadrant_cells"] = tuple(quadrant_cells)
        facts["orientation_count"] = len(set(_orientations(canonical)))
    return facts


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the complete lawful input grammar."""
    del difficulty, meta
    return list(_analyze(grid)["errors"])


def strict_canonical_like(grid) -> list[str]:
    """Accept the exact canonical size manifold while retaining shape diversity."""
    errors = self_check(grid)
    if errors:
        return errors
    q = _analyze(grid)["quad_size"]
    return [] if q in (4, 5) else [f"quadrant size {q} is outside canonical 4|5"]


def observe_overrides(grid) -> dict[str, int | str]:
    """Recover every declared semantic axis exactly from a returned input."""
    facts = _analyze(grid)
    if facts["errors"]:
        raise ValueError(f"cannot observe invalid grid: {facts['errors']}")
    return {
        "quad_size": facts["quad_size"],
        "missing_quadrant": facts["missing_quadrant"],
        "shape_cells": facts["shape_cells"],
        "foreground_color": facts["foreground_color"],
    }


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_override_keys(overrides)
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty {difficulty!r}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    q_options = _DIFFICULTY_Q.get(difficulty, _DIFFICULTY_Q["medium"])
    q = (
        ctx.draw_int("quad_size", 4, 12)
        if overrides.get("quad_size") is not None
        else ctx.draw_choice("quad_size", q_options)
    )

    scheduled_missing = _QUADRANT_NAMES[sample_index % 4]
    missing_name = _draw_scheduled_choice(
        ctx, "missing_quadrant", scheduled_missing, _QUADRANT_NAMES
    )
    missing_index = _QUADRANT_NAMES.index(missing_name)

    scheduled_cells = 3 + ((sample_index + 2 * (int(seed) % 8)) % 8)
    n_cells = _draw_scheduled_int(ctx, "shape_cells", scheduled_cells, 3, 10)
    color = ctx.draw_choice("foreground_color", _COLORS)
    shape = _sample_shape(ctx.draw_rng("shape_geometry"), n_cells, q)

    side = 2 * q + 1
    grid = full_grid(side, side, 0)
    for c in range(side):
        grid[q][c] = 5
    for r in range(side):
        grid[r][q] = 5

    for index, (origin_r, origin_c) in enumerate(_quadrant_origins(q)):
        if index == missing_index:
            continue
        for local_r, local_c in _orient(index, shape):
            grid[origin_r + local_r][origin_c + local_c] = color

    errors = self_check(grid)
    if errors:
        raise AssertionError(f"generator emitted invalid grid: {errors}")
    observed = observe_overrides(grid)
    expected = {
        "quad_size": q,
        "missing_quadrant": missing_name,
        "shape_cells": n_cells,
        "foreground_color": color,
    }
    if observed != expected:
        raise AssertionError(f"axis observer mismatch: observed={observed}, expected={expected}")
    return grid


def rule_mirror(grid) -> list[list[int]]:
    """Diagnostic Python mirror of the Racket authority; never output authority."""
    if not _is_arc_grid(grid):
        raise ValueError("grid must be a nonempty rectangular ARC grid")
    h, w = len(grid), len(grid[0])
    full_rows = [r for r in range(h) if all(grid[r][c] == 5 for c in range(w))]
    full_cols = [c for c in range(w) if all(grid[r][c] == 5 for r in range(h))]
    if not full_rows or not full_cols:
        raise ValueError("grid has no full color-5 divider row/column")
    div_r, div_c = full_rows[0], full_cols[0]
    origins = ((0, 0), (0, div_c + 1), (div_r + 1, 0), (div_r + 1, div_c + 1))

    source_index: int | None = None
    source_local: Shape = ()
    source_color: int | None = None
    empty_indices: list[int] = []
    for index, (origin_r, origin_c) in enumerate(origins):
        local: list[Cell] = []
        values: list[int] = []
        for r in range(origin_r, div_r if origin_r == 0 else h):
            for c in range(origin_c, div_c if origin_c == 0 else w):
                value = grid[r][c]
                if value not in (0, 5):
                    local.append((r - origin_r, c - origin_c))
                    values.append(value)
        if local and source_index is None:
            source_index = index
            source_local = _normalize(local)
            source_color = values[0]
        if not local:
            empty_indices.append(index)

    if source_index is None or source_color is None:
        raise ValueError("grid has no source shape")
    canonical = _orient(source_index, source_local)
    out = [row[:] for row in grid]
    for index in empty_indices:
        origin_r, origin_c = origins[index]
        for local_r, local_c in _orient(index, canonical):
            out[origin_r + local_r][origin_c + local_c] = source_color
    return out


def _complete_with_shape(grid, cells: Shape) -> list[list[int]]:
    facts = _analyze(grid)
    if facts["errors"]:
        raise ValueError(f"invalid teaching input: {facts['errors']}")
    out = [row[:] for row in grid]
    q = facts["quad_size"]
    missing = facts["missing_index"]
    origin_r, origin_c = _quadrant_origins(q)[missing]
    for local_r, local_c in cells:
        out[origin_r + local_r][origin_c + local_c] = facts["foreground_color"]
    return out


def _fixed_orientation_competitor(index: int) -> Callable[[list[list[int]]], list[list[int]]]:
    def apply(grid):
        facts = _analyze(grid)
        if facts["errors"]:
            return [row[:] for row in grid]
        return _complete_with_shape(grid, _orient(index, facts["canonical_shape"]))

    return apply


def _copy_first_source_competitor(grid) -> list[list[int]]:
    facts = _analyze(grid)
    if facts["errors"]:
        return [row[:] for row in grid]
    first = facts["filled_indices"][0]
    source = _normalize(facts["quadrant_cells"][first])
    return _complete_with_shape(grid, source)


_LESSON_COMPETITORS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "leave the missing quadrant empty": lambda grid: [row[:] for row in grid],
    "always paste canonical orientation": _fixed_orientation_competitor(0),
    "always paste horizontal reflection": _fixed_orientation_competitor(1),
    "always paste vertical reflection": _fixed_orientation_competitor(2),
    "always paste 180-degree reflection": _fixed_orientation_competitor(3),
    "copy the first visible quadrant orientation": _copy_first_source_competitor,
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons where a simple orientation shortcut survives all demos."""
    reasons: list[str] = []
    items = [*demos, query]
    for index, item in enumerate(items):
        label = f"demo {index}" if index < len(demos) else "query"
        input_grid = item.get("input")
        output_grid = item.get("output")
        errors = self_check(input_grid)
        if errors:
            reasons.append(f"{label} input is outside the teaching grammar: {errors}")
            continue
        if rule_mirror(input_grid) != output_grid:
            reasons.append(f"{label} output does not match missing-quadrant reflection")
    if reasons:
        return reasons

    for name, competitor in _LESSON_COMPETITORS.items():
        survives = all(competitor(demo["input"]) == demo["output"] for demo in demos)
        if survives and competitor(query["input"]) != query["output"]:
            reasons.append(
                f"competing rule '{name}' fits every demo but changes the query answer"
            )
    return reasons


def _valid_facts(grid) -> dict[str, Any] | None:
    facts = _analyze(grid)
    return None if facts["errors"] else facts


def _missing_witness(name: str) -> Callable[[list[list[int]]], bool]:
    def witness(grid):
        facts = _valid_facts(grid)
        return bool(facts and facts["missing_quadrant"] == name)

    return witness


def _canonical_scale(grid) -> bool:
    facts = _valid_facts(grid)
    return bool(facts and facts["quad_size"] in (4, 5))


def _expanded_scale(grid) -> bool:
    facts = _valid_facts(grid)
    return bool(facts and facts["quad_size"] >= 6)


def _small_shape(grid) -> bool:
    facts = _valid_facts(grid)
    return bool(facts and facts["shape_cells"] <= 5)


def _large_shape(grid) -> bool:
    facts = _valid_facts(grid)
    return bool(facts and facts["shape_cells"] >= 6)


def _asymmetric_shape(grid) -> bool:
    facts = _valid_facts(grid)
    return bool(facts and facts["orientation_count"] == 4)


def _first_source_top_left(grid) -> bool:
    facts = _valid_facts(grid)
    return bool(facts and facts["missing_index"] != 0)


def _first_source_non_top_left(grid) -> bool:
    facts = _valid_facts(grid)
    return bool(facts and facts["missing_index"] == 0)


SEMANTIC_WITNESSES: dict[str, Callable[[list[list[int]]], bool]] = {
    "missing_top_left": _missing_witness("top_left"),
    "missing_top_right": _missing_witness("top_right"),
    "missing_bottom_left": _missing_witness("bottom_left"),
    "missing_bottom_right": _missing_witness("bottom_right"),
    "canonical_scale": _canonical_scale,
    "expanded_scale": _expanded_scale,
    "small_shape": _small_shape,
    "large_shape": _large_shape,
    "four_distinct_orientations": _asymmetric_shape,
    "first_source_top_left": _first_source_top_left,
    "first_source_non_top_left": _first_source_non_top_left,
}
