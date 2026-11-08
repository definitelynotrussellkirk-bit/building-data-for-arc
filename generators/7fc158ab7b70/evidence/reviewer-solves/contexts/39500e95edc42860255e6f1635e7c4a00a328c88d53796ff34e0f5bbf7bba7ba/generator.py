"""Generator for ARC task ``7fc158ab7b70`` (original ``ac0a08a4``).

The authoritative rule counts nonzero *cells*, then replaces every input cell
with a square block whose side length is that count.  Repeated colors are
therefore essential teaching cases: counting distinct colors is a plausible
shortcut that fits every public demonstration but gives the wrong scale when a
color occurs more than once.
"""
from __future__ import annotations

from typing import Any, Callable, Sequence

from puzzle_generators.base import gen_ctx


GENERATOR_ID = "7fc158ab7b70"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "d959c287782b"
SUMMARY = (
    "Upscale every input cell into an nz×nz block, where nz is the number "
    "of nonzero cells (not the number of distinct colors)."
)

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

INVARIANTS = [
    "background color is 0",
    "input is a square 3..5 grid",
    "input has 2..6 nonzero cells",
    "all cell values are ARC colors 0..9",
    "grid_n * n_cells <= 30, so the output fits the ARC size limit",
    "a monochrome repeated pair is spatially separated; larger monochrome tiny shapes are excluded",
]

AXES = {
    "grid_n": {
        "type": "int",
        "default": "six-step band schedule",
        "valid": "3..5",
    },
    "n_cells": {
        "type": "int",
        "default": "difficulty-aware draw",
        "valid": "2..6",
    },
    "unique_colors": {
        "type": "bool",
        "default": "three-step teaching schedule",
        "valid": "true|false",
    },
    "anchor_origin": {
        "type": "bool",
        "default": "rng true|false",
        "valid": "true|false",
    },
}

_ALLOWED_OVERRIDES = frozenset(AXES)
_SIZE_SCHEDULES = {
    "easy": (3, 3, 4, 3, 5, 4),
    "medium": (3, 4, 5, 3, 4, 5),
    "hard": (3, 5, 4, 5, 3, 4),
}
_LAYOUTS = ("random", "diag", "anti_diag", "row", "col", "cluster")


def _validate_difficulty(difficulty: Any) -> str:
    if difficulty is None:
        return "medium"
    if difficulty not in _SIZE_SCHEDULES:
        raise ValueError(
            "difficulty must be one of 'easy', 'medium', 'hard', or None"
        )
    return str(difficulty)


def _validate_overrides(overrides: dict[str, Any]) -> None:
    unknown = sorted(set(overrides) - _ALLOWED_OVERRIDES)
    if unknown:
        raise ValueError("unknown override axis: " + ", ".join(unknown))

    if "grid_n" in overrides:
        value = overrides["grid_n"]
        if type(value) is not int or not 3 <= value <= 5:
            raise ValueError("grid_n must be an int in 3..5")
    if "n_cells" in overrides:
        value = overrides["n_cells"]
        if type(value) is not int or not 2 <= value <= 6:
            raise ValueError("n_cells must be an int in 2..6")
    for name in ("unique_colors", "anchor_origin"):
        if name in overrides and type(overrides[name]) is not bool:
            raise TypeError(f"{name} must be bool")


def _draw_axis_choice(ctx, name: str, scheduled: Any, domain: Sequence[Any]) -> Any:
    """Record an exact axis draw while retaining a deterministic schedule.

    Explicit overrides are validated against the complete declared domain.
    Default draws use a singleton containing the scheduled value, which keeps
    GenCtx provenance exact and makes every three-example lesson predictable.
    """
    if name in ctx.overrides:
        return ctx.draw_choice(name, list(domain))
    return ctx.draw_choice(name, [scheduled])


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Generate one lawful input grid with exact, observable overrides."""
    band = _validate_difficulty(difficulty)
    _validate_overrides(overrides)
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative int")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )

    scheduled_n = _SIZE_SCHEDULES[band][sample_index % 6]
    grid_n = int(_draw_axis_choice(ctx, "grid_n", scheduled_n, (3, 4, 5)))
    n_cells = int(ctx.draw_int_diff("n_cells", 2, 6))

    # Any three consecutive sample indices contain repeated-color examples.
    # This makes the canonical-fitting distinct-color shortcut impossible to
    # survive a normal three-demo lesson.
    scheduled_unique = sample_index % EXAMPLES_NEEDED == EXAMPLES_NEEDED - 1
    unique_colors = bool(
        _draw_axis_choice(
            ctx, "unique_colors", scheduled_unique, (False, True)
        )
    )
    anchor_origin = bool(ctx.draw_choice("anchor_origin", (False, True)))

    palette = _palette(ctx, n_cells, unique_colors)
    placement_rng = ctx.draw_rng("placement")
    layout = ctx.draw_choice("layout_profile", _LAYOUTS)
    locations = _pick_cells(
        grid_n,
        n_cells,
        anchor_origin=anchor_origin,
        layout=layout,
        require_spread_pair=(not unique_colors and n_cells == 2),
        rng=placement_rng,
    )

    grid = [[0 for _ in range(grid_n)] for _ in range(grid_n)]
    for (row, col), color in zip(locations, palette):
        grid[row][col] = color

    errors = self_check(grid)
    if errors:  # Constructive generation should make this unreachable.
        raise AssertionError("generated invalid grid: " + "; ".join(errors))
    return grid


def _palette(ctx, n_cells: int, unique_colors: bool) -> list[int]:
    if unique_colors:
        return list(
            ctx.draw_distinct_colors("palette", n=n_cells, exclude={0})
        )

    # Use fewer colors than cells and cycle through the full pool.  This
    # guarantees both a repeated color and an exact observer value of False.
    pool_size = min(3, n_cells - 1)
    pool = list(
        ctx.draw_distinct_colors("palette", n=pool_size, exclude={0})
    )
    return [pool[index % pool_size] for index in range(n_cells)]


def _pick_cells(
    n: int,
    count: int,
    *,
    anchor_origin: bool,
    layout: str,
    require_spread_pair: bool,
    rng,
) -> list[tuple[int, int]]:
    all_cells = [(row, col) for row in range(n) for col in range(n)]
    origin = (0, 0)
    eligible = [cell for cell in all_cells if cell != origin]

    if require_spread_pair:
        if anchor_origin:
            partners = [
                cell
                for cell in eligible
                if abs(cell[0]) + abs(cell[1]) > 1
            ]
            return [origin, rng.choice(partners)]
        pairs = [
            (left, right)
            for index, left in enumerate(eligible)
            for right in eligible[index + 1 :]
            if abs(left[0] - right[0]) + abs(left[1] - right[1]) > 1
        ]
        return list(rng.choice(pairs))

    if layout == "diag":
        preferred = [(i, i) for i in range(n) if (i, i) != origin]
    elif layout == "anti_diag":
        preferred = [(i, n - 1 - i) for i in range(n)]
    elif layout == "row":
        row = rng.randrange(n)
        preferred = [(row, col) for col in range(n) if (row, col) != origin]
    elif layout == "col":
        col = rng.randrange(n)
        preferred = [(row, col) for row in range(n) if (row, col) != origin]
    elif layout == "cluster":
        center = (rng.randrange(n), rng.randrange(n))
        preferred = sorted(
            eligible,
            key=lambda cell: (
                abs(cell[0] - center[0]) + abs(cell[1] - center[1]),
                cell,
            ),
        )
    else:
        preferred = list(eligible)
        rng.shuffle(preferred)

    seen = set()
    ordered: list[tuple[int, int]] = []
    for cell in preferred:
        if cell in eligible and cell not in seen:
            seen.add(cell)
            ordered.append(cell)
    remainder = [cell for cell in eligible if cell not in seen]
    rng.shuffle(remainder)
    ordered.extend(remainder)

    chosen = ([origin] if anchor_origin else []) + ordered[
        : count - int(anchor_origin)
    ]
    if len(chosen) != count or len(set(chosen)) != count:
        raise AssertionError("placement failed to realize the requested count")
    return chosen


def _grid_facts(grid: Any) -> tuple[dict[str, Any] | None, list[str]]:
    if not isinstance(grid, list) or not grid:
        return None, ["grid must be a nonempty list of rows"]
    if not all(isinstance(row, list) for row in grid):
        return None, ["every row must be a list"]
    width = len(grid[0]) if grid[0] else 0
    if width == 0 or any(len(row) != width for row in grid):
        return None, ["grid must be nonempty and rectangular"]

    height = len(grid)
    errors: list[str] = []
    if height != width:
        errors.append(f"expected a square grid; got {height}×{width}")
    if not 3 <= height <= 5:
        errors.append(f"grid side must be in 3..5; got {height}")

    bad_cells = [
        value
        for row in grid
        for value in row
        if type(value) is not int or not 0 <= value <= 9
    ]
    if bad_cells:
        errors.append("all cells must be integer ARC colors in 0..9")

    colors = [
        value
        for row in grid
        for value in row
        if type(value) is int and value != 0
    ]
    n_cells = len(colors)
    if not 2 <= n_cells <= 6:
        errors.append(f"expected 2..6 nonzero cells; found {n_cells}")
    if height * n_cells > 30:
        errors.append(
            f"upscaled side would be {height * n_cells}, exceeding 30"
        )

    distinct_colors = len(set(colors))
    if distinct_colors == 1 and n_cells >= 2:
        locations = [
            (row, col)
            for row, values in enumerate(grid)
            for col, value in enumerate(values)
            if type(value) is int and value != 0
        ]
        if n_cells != 2:
            errors.append(
                "monochrome examples with more than two cells are excluded from the teaching grammar"
            )
        elif (
            abs(locations[0][0] - locations[1][0])
            + abs(locations[0][1] - locations[1][1])
            <= 1
        ):
            errors.append("a monochrome repeated pair must be spatially separated")

    if errors:
        return None, errors
    return {
        "grid_n": height,
        "n_cells": n_cells,
        "unique_colors": len(set(colors)) == n_cells,
        "anchor_origin": grid[0][0] != 0,
        "colors": colors,
    }, []


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the complete public generator domain."""
    del difficulty, meta
    _, errors = _grid_facts(grid)
    return errors


def observe_overrides(grid) -> dict[str, int | bool]:
    """Recover every declared exact axis from a returned grid."""
    facts, errors = _grid_facts(grid)
    if errors or facts is None:
        raise ValueError("cannot observe invalid grid: " + "; ".join(errors))
    return {
        "grid_n": facts["grid_n"],
        "n_cells": facts["n_cells"],
        "unique_colors": facts["unique_colors"],
        "anchor_origin": facts["anchor_origin"],
    }


def strict_canonical_like(grid) -> list[str]:
    """All generated grids are lawful instances of the canonical rule."""
    return self_check(grid)


def _scale_by(grid: list[list[int]], factor: int) -> list[list[int]]:
    if factor <= 0:
        raise ValueError("scale factor must be positive")
    output: list[list[int]] = []
    for row in grid:
        expanded = [value for value in row for _ in range(factor)]
        for _ in range(factor):
            output.append(list(expanded))
    return output


def rule_mirror(grid) -> list[list[int]]:
    """Independent Python mirror of the selected Racket authority."""
    facts, errors = _grid_facts(grid)
    if errors or facts is None:
        raise ValueError("invalid rule input: " + "; ".join(errors))
    return _scale_by(grid, facts["n_cells"])


def _rival_distinct_nonzero_colors(grid) -> list[list[int]]:
    """Wrong but canonical-fitting rule: scale by distinct nonzero colors."""
    facts, errors = _grid_facts(grid)
    if errors or facts is None:
        raise ValueError("invalid rival input: " + "; ".join(errors))
    return _scale_by(grid, len(set(facts["colors"])))


def _witness_repeated_nonzero_color(grid) -> bool:
    facts, errors = _grid_facts(grid)
    return bool(
        not errors
        and facts is not None
        and not facts["unique_colors"]
    )


SEMANTIC_RIVALS: dict[str, Callable[[Any], list[list[int]]]] = {
    "distinct_nonzero_colors": _rival_distinct_nonzero_colors,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
SEMANTIC_WITNESSES: dict[str, Callable[[Any], bool]] = {
    "repeated_nonzero_color": _witness_repeated_nonzero_color,
}
WITNESS_RIVALS = {
    "repeated_nonzero_color": ["distinct_nonzero_colors"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require the demonstrations to eliminate every declared rival rule."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query must contain an input grid"]

    reasons: list[str] = []
    query_errors = self_check(query["input"])
    if query_errors:
        reasons.append(f"query input is invalid: {query_errors[0]}")
    elif "output" in query and query["output"] != rule_mirror(query["input"]):
        reasons.append("query output disagrees with the endpoint rule")

    refuted = {name: False for name in SEMANTIC_RIVALS}
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or not {"input", "output"} <= set(demo):
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        errors = self_check(demo["input"])
        if errors:
            reasons.append(f"demo {index} input is invalid: {errors[0]}")
            continue
        expected = rule_mirror(demo["input"])
        if demo["output"] != expected:
            reasons.append(f"demo {index} output disagrees with the endpoint rule")
            continue
        for name, rival in SEMANTIC_RIVALS.items():
            if rival(demo["input"]) != expected:
                refuted[name] = True

    for name, was_refuted in refuted.items():
        if not was_refuted:
            reasons.append(f"demonstrations do not refute rival {name}")
    return reasons
