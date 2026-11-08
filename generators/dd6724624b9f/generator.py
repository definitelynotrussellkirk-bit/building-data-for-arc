"""Generator for ARC task dd6724624b9f.

The first two cells are a compact instruction strip:

* ``grid[0][0]`` is one of six geometric transform codes;
* ``grid[0][1]`` is the output color.

After clearing the strip, the selected rule crops the sole 4-connected body,
applies the encoded transform, and recolors every body cell to the requested
output color.  The six-code table below is pinned to the selected Racket rule;
the previous generator shipped a stale five-code table and therefore taught a
different task.
"""
from __future__ import annotations

from collections import deque
from copy import deepcopy
from functools import lru_cache
from typing import Any, Callable, Iterable, Sequence

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "dd6724624b9f"
TASK_ID = GENERATOR_ID
VERSION = "3.0.1"
RULE_HASH = "8dd08a5ab5cb"

SUMMARY = (
    "Read transform code grid[0][0] and output color grid[0][1]. Clear those "
    "two controls, crop the single 4-connected monochrome body, apply the "
    "canonical six-code transform table (1 identity, 2 left-right reflection, "
    "3 up-down reflection, 4 clockwise rotation, 5 half-turn, 6 counter-"
    "clockwise rotation), and recolor the transformed body to grid[0][1]."
)

INVARIANTS = [
    "background is color 0",
    "row 0 contains only transform code and output-color controls",
    "row 1 is blank and separates the controls from the body",
    "the body is one 4-connected monochrome 2-D polyomino",
    "body color differs from the requested output color",
    "nonidentity controls are visible on the selected body shape",
]

EXAMPLES_NEEDED = 6
MIN_STRICT_FRAC = 1.0
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

AXES = {
    "grid_h": {
        "type": "int",
        "default": (
            "odd slots use canonical anchors (easy 8, medium 9, hard 10); "
            "even slots cycle 8..16"
        ),
        "valid": "8..16",
    },
    "grid_w": {
        "type": "int",
        "default": (
            "odd slots use canonical anchors (easy 9, medium 10, hard 10); "
            "even slots cycle 9..17"
        ),
        "valid": "9..17",
    },
    "transform_code": {
        "type": "int",
        "default": "six-residue lesson schedule",
        "valid": "1..6",
    },
    "body_cells": {
        "type": "int",
        "default": "difficulty-banded draw: easy 3..4, medium 5..6, hard 7..8",
        "valid": "3..8",
    },
    "color_pair": {
        "type": "int",
        "default": "keyed draw excluding collisions with the transform-code color",
        "valid": "0..7",
    },
}

# Every Cartesian combination of the declared controls is realizable in every
# difficulty band.  Difficulty changes no public override domain.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, Any], ...] = ()

# The first five pairs preserve the public examples' strong color-9 body prior;
# the remaining pairs break that incidental regularity without adding an axis.
_COLOR_PAIRS: tuple[tuple[int, int], ...] = (
    (2, 9),
    (7, 9),
    (4, 9),
    (6, 9),
    (5, 9),
    (8, 3),
    (3, 1),
    (9, 2),
)

# The production curriculum is ordered: every six-demo window covers all six
# codes, but arbitrary query rotations can remove the sole example of a code.
# Do not declare LESSON_SCHEDULE_PERIOD, whose shared receipt contract requires
# rotation-safe lessons.  Task-local tests still exhaust multiple start cycles.
SCHEDULE_PROFILES = tuple(f"transform_code_{code}" for code in range(1, 7))


# ---------------------------------------------------------------------------
# Call validation and schedule
# ---------------------------------------------------------------------------


def _literal_nonnegative_int(name: str, value: Any) -> int:
    if type(value) is not int:
        raise TypeError(f"{name} must be a literal integer (not bool), got {value!r}")
    if value < 0:
        raise ValueError(f"{name} must be nonnegative, got {value}")
    return value


def _band(difficulty: Any) -> str:
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return str(difficulty)
    raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")


def _validate_overrides(overrides: dict[str, Any]) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")
    bounds = {
        "grid_h": (8, 16),
        "grid_w": (9, 17),
        "transform_code": (1, 6),
        "body_cells": (3, 8),
        "color_pair": (0, len(_COLOR_PAIRS) - 1),
    }
    for name, value in overrides.items():
        if value is None:
            continue
        if type(value) is not int:
            raise TypeError(f"override {name!r} must be a literal integer, got {value!r}")
        lo, hi = bounds[name]
        if not lo <= value <= hi:
            raise ValueError(f"override {name!r} must be in [{lo}, {hi}], got {value}")


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Return the public six-residue transform curriculum profile."""
    _literal_nonnegative_int("seed", seed)
    index = _literal_nonnegative_int("sample_index", sample_index)
    _band(difficulty)
    return SCHEDULE_PROFILES[index % len(SCHEDULE_PROFILES)]


# ---------------------------------------------------------------------------
# Polyomino and transform helpers
# ---------------------------------------------------------------------------


def _norm_cells(cells: Iterable[tuple[int, int]]) -> list[tuple[int, int]]:
    cells = list(cells)
    if not cells:
        raise ValueError("cannot normalize an empty cell set")
    row0 = min(row for row, _ in cells)
    col0 = min(col for _, col in cells)
    return sorted((row - row0, col - col0) for row, col in cells)


def _shape_dims(cells: Iterable[tuple[int, int]]) -> tuple[int, int]:
    cells = list(cells)
    return max(row for row, _ in cells) + 1, max(col for _, col in cells) + 1


def _transform(cells: Iterable[tuple[int, int]], code: int) -> list[tuple[int, int]]:
    """Apply the exact transform table selected by the Racket authority."""
    cells = _norm_cells(cells)
    height, width = _shape_dims(cells)
    operations: dict[int, Callable[[int, int], tuple[int, int]]] = {
        1: lambda row, col: (row, col),
        2: lambda row, col: (row, width - 1 - col),
        3: lambda row, col: (height - 1 - row, col),
        4: lambda row, col: (col, height - 1 - row),
        5: lambda row, col: (height - 1 - row, width - 1 - col),
        6: lambda row, col: (width - 1 - col, row),
    }
    if code not in operations:
        raise ValueError(f"unsupported transform code {code!r}")
    operation = operations[code]
    return _norm_cells(operation(row, col) for row, col in cells)


def _legacy_transform(
    cells: Iterable[tuple[int, int]], code: int
) -> list[tuple[int, int]]:
    """The stale table from generator v2.1.0, retained only as a named rival."""
    cells = _norm_cells(cells)
    height, width = _shape_dims(cells)
    operations: dict[int, Callable[[int, int], tuple[int, int]]] = {
        1: lambda row, col: (row, col),
        2: lambda row, col: (col, height - 1 - row),
        3: lambda row, col: (height - 1 - row, width - 1 - col),
        4: lambda row, col: (width - 1 - col, row),
        5: lambda row, col: (row, width - 1 - col),
        6: lambda row, col: (row, col),
    }
    if code not in operations:
        raise ValueError(f"unsupported legacy transform code {code!r}")
    operation = operations[code]
    return _norm_cells(operation(row, col) for row, col in cells)


_NEIGHBORS = ((-1, 0), (1, 0), (0, -1), (0, 1))


@lru_cache(maxsize=None)
def _fixed_polyominoes(size: int) -> tuple[tuple[tuple[int, int], ...], ...]:
    """Enumerate translation-normalized fixed polyominoes up to eight cells."""
    if size < 1:
        raise ValueError("polyomino size must be positive")
    if size == 1:
        return (((0, 0),),)
    expanded: set[tuple[tuple[int, int], ...]] = set()
    for shape in _fixed_polyominoes(size - 1):
        occupied = set(shape)
        for row, col in shape:
            for drow, dcol in _NEIGHBORS:
                candidate = (row + drow, col + dcol)
                if candidate in occupied:
                    continue
                normalized = tuple(_norm_cells(occupied | {candidate}))
                expanded.add(normalized)
    return tuple(sorted(expanded))


@lru_cache(maxsize=None)
def _semantic_shapes(
    body_cells: int, code: int
) -> tuple[tuple[tuple[int, int], ...], ...]:
    """Cache the expensive semantic filtering independently of canvas size."""
    candidates: list[tuple[tuple[int, int], ...]] = []
    for shape in _fixed_polyominoes(body_cells):
        if len({row for row, _ in shape}) < 2:
            continue
        if len({col for _, col in shape}) < 2:
            continue
        transformed = _transform(shape, code)
        if code != 1 and transformed == list(shape):
            continue
        # Every generated nonidentity example is also a direct counterexample
        # to the stale transform table that motivated this repair.
        if code != 1 and transformed == _legacy_transform(shape, code):
            continue
        candidates.append(shape)
    return tuple(candidates)


@lru_cache(maxsize=None)
def _candidate_shapes(
    body_cells: int, code: int, grid_h: int, grid_w: int
) -> tuple[tuple[tuple[int, int], ...], ...]:
    return tuple(
        shape
        for shape in _semantic_shapes(body_cells, code)
        if _shape_dims(shape)[0] <= grid_h - 2
        and _shape_dims(shape)[1] <= grid_w
    )


# ---------------------------------------------------------------------------
# Grid analysis, self-check, and observable controls
# ---------------------------------------------------------------------------


def _components4(grid: Sequence[Sequence[int]]) -> list[list[tuple[int, int]]]:
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[list[tuple[int, int]]] = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] == 0 or (row, col) in seen:
                continue
            queue = deque([(row, col)])
            seen.add((row, col))
            component: list[tuple[int, int]] = []
            while queue:
                rr, cc = queue.popleft()
                component.append((rr, cc))
                for drow, dcol in _NEIGHBORS:
                    nr, nc = rr + drow, cc + dcol
                    if not (0 <= nr < height and 0 <= nc < width):
                        continue
                    if grid[nr][nc] == 0 or (nr, nc) in seen:
                        continue
                    seen.add((nr, nc))
                    queue.append((nr, nc))
            result.append(component)
    return result


def _analyze(grid: Any) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(grid, (list, tuple)) or not grid:
        return {"errors": ["grid must be a nonempty row sequence"]}
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return {"errors": ["grid rows must be nonempty sequences"]}
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return {"errors": ["grid must be rectangular"]}
    height = len(grid)
    if not 8 <= height <= 16:
        errors.append(f"grid height must be in 8..16, got {height}")
    if not 9 <= width <= 17:
        errors.append(f"grid width must be in 9..17, got {width}")
    if any(
        type(value) is not int or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        errors.append("cells must be literal ARC integers in 0..9")
        return {"errors": errors, "height": height, "width": width}
    if width < 2:
        errors.append("grid must expose two control cells")
        return {"errors": errors, "height": height, "width": width}

    code = int(grid[0][0])
    out_color = int(grid[0][1])
    if code not in range(1, 7):
        errors.append(f"transform code must be in 1..6, got {code}")
    if not 1 <= out_color <= 9:
        errors.append(f"output color must be nonzero, got {out_color}")
    if any(value != 0 for value in grid[0][2:]):
        errors.append("row 0 may contain only the two control cells")
    if height > 1 and any(value != 0 for value in grid[1]):
        errors.append("row 1 must be a blank separator")

    work = [list(row) for row in grid]
    work[0][0] = 0
    work[0][1] = 0
    components = _components4(work)
    if len(components) != 1:
        errors.append(f"expected exactly one body component, got {len(components)}")
        return {
            "errors": errors,
            "height": height,
            "width": width,
            "code": code,
            "out_color": out_color,
        }

    absolute_cells = components[0]
    cells = _norm_cells(absolute_cells)
    body_colors = {int(grid[row][col]) for row, col in absolute_cells}
    if len(body_colors) != 1:
        errors.append(f"body must be monochrome, got colors {sorted(body_colors)}")
        body_color = None
    else:
        body_color = next(iter(body_colors))
        if body_color == out_color:
            errors.append("body color must differ from output color")
    body_cells = len(cells)
    if not 3 <= body_cells <= 8:
        errors.append(f"body must contain 3..8 cells, got {body_cells}")
    if len({row for row, _ in cells}) < 2 or len({col for _, col in cells}) < 2:
        errors.append("body must occupy at least two rows and two columns")
    if code in range(2, 7) and _transform(cells, code) == cells:
        errors.append("nonidentity transform is invisible on the body shape")

    color_pair = None
    if body_color is not None:
        try:
            color_pair = _COLOR_PAIRS.index((out_color, body_color))
        except ValueError:
            errors.append(
                f"output/body color pair {(out_color, body_color)} is outside the generator palette"
            )

    return {
        "errors": errors,
        "height": height,
        "width": width,
        "code": code,
        "out_color": out_color,
        "body_color": body_color,
        "body_cells": body_cells,
        "cells": cells,
        "absolute_cells": absolute_cells,
        "color_pair": color_pair,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del meta
    if difficulty is not None:
        try:
            _band(difficulty)
        except ValueError as exc:
            return [str(exc)]
    return list(_analyze(grid)["errors"])


def strict_canonical_like(grid) -> list[str]:
    return self_check(grid)


def observe_overrides(grid) -> dict[str, int]:
    facts = _analyze(grid)
    if facts["errors"]:
        raise ValueError("cannot observe invalid grid: " + "; ".join(facts["errors"]))
    return {
        "grid_h": int(facts["height"]),
        "grid_w": int(facts["width"]),
        "transform_code": int(facts["code"]),
        "body_cells": int(facts["body_cells"]),
        "color_pair": int(facts["color_pair"]),
    }


# ---------------------------------------------------------------------------
# Rule mirror and explicit rivals
# ---------------------------------------------------------------------------


def _render_shape(cells: Iterable[tuple[int, int]], color: int) -> list[list[int]]:
    cells = _norm_cells(cells)
    height, width = _shape_dims(cells)
    output = full_grid(height, width, 0)
    for row, col in cells:
        output[row][col] = color
    return output


def rule_mirror(grid) -> list[list[int]]:
    """Independent Python mirror for diagnostics; Racket remains authority."""
    facts = _analyze(grid)
    if facts["errors"]:
        raise ValueError("invalid input: " + "; ".join(facts["errors"]))
    return _render_shape(_transform(facts["cells"], facts["code"]), facts["out_color"])


def _rival_stale_transform_table(grid) -> list[list[int]]:
    facts = _analyze(grid)
    if facts["errors"]:
        raise ValueError("invalid input: " + "; ".join(facts["errors"]))
    return _render_shape(
        _legacy_transform(facts["cells"], facts["code"]), facts["out_color"]
    )


def _rival_five_codes_only(grid) -> list[list[int]]:
    facts = _analyze(grid)
    if facts["errors"]:
        raise ValueError("invalid input: " + "; ".join(facts["errors"]))
    code = 1 if facts["code"] == 6 else facts["code"]
    return _render_shape(_transform(facts["cells"], code), facts["out_color"])


def _rival_preserve_body_color(grid) -> list[list[int]]:
    facts = _analyze(grid)
    if facts["errors"]:
        raise ValueError("invalid input: " + "; ".join(facts["errors"]))
    return _render_shape(
        _transform(facts["cells"], facts["code"]), facts["body_color"]
    )


SEMANTIC_RIVALS = {
    "stale_transform_table": _rival_stale_transform_table,
    "five_codes_only": _rival_five_codes_only,
    "preserve_body_color": _rival_preserve_body_color,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
# Public labeled examples use codes 1..4 only, so treating unseen code 6 as
# identity fits every canonical label.  Generated six-example windows refute it.
CANONICAL_SHORTCUTS = {"five_codes_only": _rival_five_codes_only}


def _valid_facts(grid) -> dict[str, Any] | None:
    facts = _analyze(grid)
    return None if facts["errors"] else facts


def _witness_stale_transform_table(grid) -> bool:
    facts = _valid_facts(grid)
    return bool(
        facts
        and facts["code"] != 1
        and _transform(facts["cells"], facts["code"])
        != _legacy_transform(facts["cells"], facts["code"])
    )


def _witness_code_six(grid) -> bool:
    facts = _valid_facts(grid)
    return bool(facts and facts["code"] == 6)


def _witness_recolor(grid) -> bool:
    facts = _valid_facts(grid)
    return bool(facts and facts["body_color"] != facts["out_color"])


SEMANTIC_WITNESSES = {
    "legacy_transform_table": _witness_stale_transform_table,
    "code_six_branch": _witness_code_six,
    "recolor_body": _witness_recolor,
}
WITNESS_RIVALS = {
    "legacy_transform_table": ["stale_transform_table"],
    "code_six_branch": ["five_codes_only"],
    "recolor_body": ["preserve_body_color"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Check that a lesson both labels the rule and eliminates named rivals."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"expected at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        return ["query must contain input and output grids"]

    reasons: list[str] = []
    codes: set[int] = set()
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} must contain input and output")
            continue
        facts = _analyze(pair["input"])
        if facts["errors"]:
            reasons.append(f"demo {index} input is outside the task grammar")
            continue
        codes.add(int(facts["code"]))
        if rule_mirror(pair["input"]) != pair["output"]:
            reasons.append(f"demo {index} output disagrees with the selected rule")

    query_facts = _analyze(query["input"])
    if query_facts["errors"]:
        reasons.append("query input is outside the task grammar")
    elif rule_mirror(query["input"]) != query["output"]:
        reasons.append("query output disagrees with the selected rule")

    if reasons:
        return reasons
    if codes != set(range(1, 7)):
        reasons.append(f"demonstrations cover transform codes {sorted(codes)}, not all 1..6")
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(deepcopy(pair["input"])) == pair["output"] for pair in demos):
            reasons.append(f"demonstrations do not refute rival {name}")
    return reasons


# ---------------------------------------------------------------------------
# Deterministic generation
# ---------------------------------------------------------------------------


def _draw_scheduled_code(ctx, scheduled: int) -> int:
    if "transform_code" in ctx.overrides and ctx.overrides["transform_code"] is not None:
        return ctx.draw_int_strict("transform_code", 1, 6)
    return ctx.draw_int_strict("transform_code", scheduled, scheduled)


def _draw_banded_int(
    ctx, label: str, full_lo: int, full_hi: int, bands: dict[str, tuple[int, int]]
) -> int:
    """Use a live difficulty default while keeping every explicit override lawful."""
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_int_strict(label, full_lo, full_hi)
    lo, hi = bands[str(ctx.difficulty)]
    return ctx.draw_int_strict(label, lo, hi)


def _draw_profiled_dimension(
    ctx,
    label: str,
    full_lo: int,
    full_hi: int,
    canonical_anchor: dict[str, int],
) -> int:
    """Interleave exact canonical profiles with complete size-domain support.

    Odd sample slots are stable profile-floor anchors.  Even slots walk every
    declared dimension exactly once per 18-slot cycle, so the ordinary
    curriculum—not only explicit overrides—uses the complete public domain.
    """
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_int_strict(label, full_lo, full_hi)
    if ctx.sample_index % 2:
        scheduled = canonical_anchor[str(ctx.difficulty)]
    else:
        scheduled = full_lo + (ctx.sample_index // 2) % (full_hi - full_lo + 1)
    return ctx.draw_int_strict(label, scheduled, scheduled)


def _draw_color_pair(ctx, code: int) -> int:
    if "color_pair" in ctx.overrides and ctx.overrides["color_pair"] is not None:
        return ctx.draw_int_strict("color_pair", 0, len(_COLOR_PAIRS) - 1)
    safe = tuple(
        index
        for index, (out_color, body_color) in enumerate(_COLOR_PAIRS)
        if code not in (out_color, body_color)
    )
    scheduled = ctx.draw_rng("color_pair_default").choice(safe)
    return ctx.draw_int_strict("color_pair", scheduled, scheduled)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    seed = _literal_nonnegative_int("seed", seed)
    sample_index = _literal_nonnegative_int("sample_index", sample_index)
    band = _band(difficulty)
    _validate_overrides(overrides)

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    grid_h = _draw_profiled_dimension(
        ctx, "grid_h", 8, 16,
        {"easy": 8, "medium": 9, "hard": 10},
    )
    grid_w = _draw_profiled_dimension(
        ctx, "grid_w", 9, 17,
        {"easy": 9, "medium": 10, "hard": 10},
    )
    scheduled_code = sample_index % 6 + 1
    code = _draw_scheduled_code(ctx, scheduled_code)
    body_cells = _draw_banded_int(
        ctx, "body_cells", 3, 8,
        {"easy": (3, 4), "medium": (5, 6), "hard": (7, 8)},
    )
    color_pair = _draw_color_pair(ctx, code)
    out_color, body_color = _COLOR_PAIRS[color_pair]

    candidates = _candidate_shapes(body_cells, code, grid_h, grid_w)
    if not candidates:
        raise ValueError(
            "no lawful polyomino for "
            f"body_cells={body_cells}, code={code}, grid={grid_h}x{grid_w}"
        )
    shape = ctx.draw_rng("body_shape").choice(candidates)
    shape_h, shape_w = _shape_dims(shape)
    row0 = ctx.draw_rng("body_row").randint(2, grid_h - shape_h)
    col0 = ctx.draw_rng("body_col").randint(0, grid_w - shape_w)

    grid = full_grid(grid_h, grid_w, 0)
    grid[0][0] = code
    grid[0][1] = out_color
    for drow, dcol in shape:
        grid[row0 + drow][col0 + dcol] = body_color

    errors = self_check(grid, difficulty=band, meta={"overrides": overrides})
    if errors:
        raise AssertionError("generated invalid grid: " + "; ".join(errors))
    return grid
