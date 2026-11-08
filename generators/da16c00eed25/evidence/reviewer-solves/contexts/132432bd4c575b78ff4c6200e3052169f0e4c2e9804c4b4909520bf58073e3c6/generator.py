"""Input sampler for completing a missing axis-aligned rectangle corner.

Every lawful input contains exactly three cells of one nonzero color.  Their
row/column product has four positions, so the absent product position is the
unique fourth corner.  The unchanged Racket authority paints that position.

The sampler intentionally includes adjacent rows/columns, all four missing
corners, and boundary-touching rectangles.  Those cases refute presentation
shortcuts that fit the small canonical set but are not part of the rule.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "da16c00eed25"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "b83881c49fb4"
SUMMARY = (
    "A 0-background 4..14 by 4..14 grid contains exactly three cells of one "
    "nonzero color at three corners of an axis-aligned rectangle. Rows and "
    "columns may be adjacent, and the rectangle may touch any grid boundary. "
    "Complete the unique missing row-column combination with the same color."
)
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0

SCHEDULE_PROFILES = (
    "rival_counterexample",
    "free_1",
    "free_2",
    "free_3",
)


def schedule_profile(seed, sample_index, difficulty=None):
    """Name the four-sample curriculum slot used by ordinary lessons."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]

INVARIANTS = [
    "the grid is rectangular, 4..14 cells high and wide, with background 0",
    "exactly three nonzero cells are present and all share one color",
    "the cells occupy exactly two rows and exactly two columns",
    "exactly one of the four row-column products is background",
]

AXES = {
    "grid_h": {"type": "int", "default": "canonical-weighted 4..14", "valid": "4..14"},
    "grid_w": {"type": "int", "default": "canonical-weighted 4..14", "valid": "4..14"},
    "row_gap": {"type": "int", "default": "weighted 1..h-1", "valid": "1..h-1"},
    "col_gap": {"type": "int", "default": "weighted 1..w-1", "valid": "1..w-1"},
    "missing_corner": {"type": "int", "default": "uniform 0..3", "valid": "0..3"},
    "corner_color": {"type": "color", "default": "uniform nonzero", "valid": "1..9"},
}

# The only incompatible exact combinations are dimension/gap pairs where the
# requested gap cannot fit.  generate() raises a structured ValueError carrying
# the relevant axis names, so the override checker can distinguish this from a
# generator defect.
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []


class _IncompatibleOverrides(ValueError):
    def __init__(self, axes: tuple[str, ...], message: str) -> None:
        super().__init__(message)
        self.incompatible_axes = axes


def _validate_overrides(overrides: dict) -> None:
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")

    bounds = {
        "grid_h": (4, 14),
        "grid_w": (4, 14),
        "row_gap": (1, 13),
        "col_gap": (1, 13),
        "missing_corner": (0, 3),
        "corner_color": (1, 9),
    }
    for name, value in overrides.items():
        if value is None:
            continue
        if type(value) is not int:
            raise ValueError(f"{name} must be an integer, not {type(value).__name__}")
        lo, hi = bounds[name]
        if not lo <= value <= hi:
            raise ValueError(f"{name}={value} outside [{lo}, {hi}]")

    h = overrides.get("grid_h")
    w = overrides.get("grid_w")
    row_gap = overrides.get("row_gap")
    col_gap = overrides.get("col_gap")
    if h is not None and row_gap is not None and row_gap >= h:
        raise _IncompatibleOverrides(
            ("grid_h", "row_gap"),
            f"row_gap={row_gap} cannot fit inside grid_h={h}",
        )
    if w is not None and col_gap is not None and col_gap >= w:
        raise _IncompatibleOverrides(
            ("grid_w", "col_gap"),
            f"col_gap={col_gap} cannot fit inside grid_w={w}",
        )


def _weighted_dimension(ctx, name: str, minimum: int, difficulty) -> int:
    domain = list(range(minimum, 15))
    if name == "grid_h":
        canonical = [6] * 14
        band = {
            "easy": [4, 5, 6, 7] * 2,
            "medium": [6, 7, 8, 9, 10] * 2,
            "hard": [10, 11, 12, 13, 14] * 2,
        }.get(difficulty, [6, 7, 8, 9, 10])
    else:
        canonical = [7, 8, 9] * 5
        band = {
            "easy": [4, 5, 6, 7, 8] * 2,
            "medium": [7, 8, 9, 10, 11] * 2,
            "hard": [10, 11, 12, 13, 14] * 2,
        }.get(difficulty, [7, 8, 9, 10, 11])
    options = domain + [value for value in canonical + band if value >= minimum]
    return int(ctx.draw_choice(name, options))


def _weighted_gap(ctx, name: str, maximum: int, difficulty) -> int:
    domain = list(range(1, maximum + 1))
    # Adjacent and canonical-looking gaps both remain common in every band.
    favored = [1] * 7 + [3] * 5
    if difficulty == "easy":
        favored += [1, 2] * 3
    elif difficulty == "hard":
        favored += [maximum, max(1, maximum - 1)] * 2
    options = domain + [value for value in favored if value <= maximum]
    return int(ctx.draw_choice(name, options))


def _weighted_start(ctx, name: str, maximum: int) -> int:
    options = list(range(maximum + 1))
    if maximum:
        # Boundary witnesses are deliberate curriculum support, not accidents.
        options += [0, maximum] * 5
    return int(ctx.draw_choice(name, options))


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_overrides(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    requested_row_gap = overrides.get("row_gap")
    requested_col_gap = overrides.get("col_gap")
    min_h = 4 if requested_row_gap is None else max(4, requested_row_gap + 1)
    min_w = 4 if requested_col_gap is None else max(4, requested_col_gap + 1)
    h = _weighted_dimension(ctx, "grid_h", min_h, difficulty)
    w = _weighted_dimension(ctx, "grid_w", min_w, difficulty)
    profile = schedule_profile(seed, sample_index, difficulty)
    if profile == "rival_counterexample" and "row_gap" not in overrides:
        row_gap = int(ctx.draw_choice("row_gap", (1,)))
    else:
        row_gap = _weighted_gap(ctx, "row_gap", h - 1, difficulty)
    col_gap = _weighted_gap(ctx, "col_gap", w - 1, difficulty)
    if profile == "rival_counterexample" and "missing_corner" not in overrides:
        missing = int(ctx.draw_choice("missing_corner", (0, 1)))
    else:
        missing = ctx.draw_int("missing_corner", 0, 3)
    color = ctx.draw_color("corner_color", exclude={0})

    if profile == "rival_counterexample":
        r1 = int(ctx.draw_choice("row_start", (0,)))
    else:
        r1 = _weighted_start(ctx, "row_start", h - row_gap - 1)
    c1 = _weighted_start(ctx, "col_start", w - col_gap - 1)
    r2, c2 = r1 + row_gap, c1 + col_gap
    corners = ((r1, c1), (r1, c2), (r2, c1), (r2, c2))

    grid = full_grid(h, w, 0)
    for index, (row, col) in enumerate(corners):
        if index != missing:
            grid[row][col] = color
    return grid


def _extract(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        raise ValueError("expected a nonempty grid")
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        raise ValueError("expected nonempty rows")
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("cells must be integer ARC colors 0..9")

    cells = [(r, c, value) for r, row in enumerate(grid) for c, value in enumerate(row) if value != 0]
    if len(cells) != 3:
        raise ValueError(f"expected exactly three nonzero cells, found {len(cells)}")
    colors = {value for _, _, value in cells}
    if len(colors) != 1:
        raise ValueError("the three cells must share one nonzero color")
    rows = sorted({r for r, _, _ in cells})
    cols = sorted({c for _, c, _ in cells})
    if len(rows) != 2 or len(cols) != 2:
        raise ValueError("the cells must occupy exactly two rows and two columns")

    present = {(r, c) for r, c, _ in cells}
    corners = ((rows[0], cols[0]), (rows[0], cols[1]), (rows[1], cols[0]), (rows[1], cols[1]))
    missing = [index for index, point in enumerate(corners) if point not in present]
    if len(missing) != 1 or any(point not in corners for point in present):
        raise ValueError("the cells must be exactly three of four rectangle corners")
    return {
        "grid_h": len(grid),
        "grid_w": width,
        "row_gap": rows[1] - rows[0],
        "col_gap": cols[1] - cols[0],
        "missing_corner": missing[0],
        "corner_color": next(iter(colors)),
        "rows": rows,
        "cols": cols,
        "corners": corners,
    }


def observe_overrides(grid):
    """Recover every exact public axis from returned pixels."""
    info = _extract(grid)
    return {name: info[name] for name in AXES}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    try:
        info = _extract(grid)
    except ValueError as exc:
        return [str(exc)]
    errors = []
    if not 4 <= info["grid_h"] <= 14:
        errors.append(f"grid_h={info['grid_h']} outside [4, 14]")
    if not 4 <= info["grid_w"] <= 14:
        errors.append(f"grid_w={info['grid_w']} outside [4, 14]")
    return errors


def strict_canonical_like(grid):
    return self_check(grid)


def _copy_grid(grid):
    return [list(row) for row in grid]


def _complete(grid):
    info = _extract(grid)
    out = _copy_grid(grid)
    row, col = info["corners"][info["missing_corner"]]
    out[row][col] = info["corner_color"]
    return out


def _min_gap_two_rival(grid):
    """Wrong shortcut: only complete visibly separated rectangles."""
    info = _extract(grid)
    if info["row_gap"] < 2 or info["col_gap"] < 2:
        return _copy_grid(grid)
    return _complete(grid)


def _bottom_missing_only_rival(grid):
    """Wrong shortcut: canonical examples only require filling the lower row."""
    info = _extract(grid)
    if info["missing_corner"] not in (2, 3):
        return _copy_grid(grid)
    return _complete(grid)


def _interior_only_rival(grid):
    """Wrong shortcut: ignore clues touching the outer frame."""
    info = _extract(grid)
    if (
        info["rows"][0] == 0
        or info["rows"][1] == info["grid_h"] - 1
        or info["cols"][0] == 0
        or info["cols"][1] == info["grid_w"] - 1
    ):
        return _copy_grid(grid)
    return _complete(grid)


def _adjacent_gap(grid):
    info = _extract(grid)
    return info["row_gap"] == 1 or info["col_gap"] == 1


def _top_missing(grid):
    return _extract(grid)["missing_corner"] in (0, 1)


def _edge_touching(grid):
    info = _extract(grid)
    return (
        info["rows"][0] == 0
        or info["rows"][1] == info["grid_h"] - 1
        or info["cols"][0] == 0
        or info["cols"][1] == info["grid_w"] - 1
    )


SEMANTIC_WITNESSES = {
    "adjacent_gap": _adjacent_gap,
    "top_missing": _top_missing,
    "edge_touching": _edge_touching,
}
SEMANTIC_RIVALS = {
    "min_gap_two": _min_gap_two_rival,
    "bottom_missing_only": _bottom_missing_only_rival,
    "interior_only": _interior_only_rival,
}
WITNESS_RIVALS = {
    "adjacent_gap": ["min_gap_two"],
    "top_missing": ["bottom_missing_only"],
    "edge_touching": ["interior_only"],
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query) -> list[str]:
    """Return rivals that still fit every demonstration in a complete lesson."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"expected at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query must contain an input grid"]

    errors = []
    for name, rival in sorted(LESSON_COMPETITORS.items()):
        try:
            survives = all(
                isinstance(demo, dict)
                and "input" in demo
                and "output" in demo
                and rival(demo["input"]) == demo["output"]
                for demo in demos
            )
        except Exception as exc:
            errors.append(f"{name} raised {type(exc).__name__}: {exc}")
            continue
        if survives:
            errors.append(f"{name} fits every demonstration")
    return errors
