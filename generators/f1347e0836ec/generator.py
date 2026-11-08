"""Generator for ARC task 7ec998c9.

A square input is a solid background with one non-background interior dot.
The selected Racket rule keeps the dot, paints color 1 through the dot's
column, and extends the two boundary endpoints to opposite corners:

* dot on the main diagonal (row == column): top arm -> right, bottom -> left;
* otherwise: top arm -> left, bottom -> right.

The public examples accidentally support several easier rules: the diagonal
example is also centered, on the anti-diagonal, and has an odd background,
while both off-diagonal examples have even backgrounds.  All four examples
also fit the numeric shortcut "use the diagonal branch when dot = background
+ 1".  Ordinary generated lessons use a four-residue schedule containing
explicit counterexamples to all four correlations while retaining canonical
5/7/8 grid-size anchors.
"""
from __future__ import annotations

from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "f1347e0836ec"
TASK_ID = GENERATOR_ID
VERSION = "2.1.0"
RULE_HASH = "39c262fb60b4"

SUMMARY = (
    "Square solid background with one interior dot. Paint color 1 vertically "
    "through the dot column, preserving the dot itself. If row == column, "
    "extend the top endpoint to the top-right corner and the bottom endpoint "
    "to the bottom-left; otherwise extend top-left and bottom-right. Generated "
    "lessons break the canonical anti-diagonal, center-column, and background-"
    "parity and dot-successor correlations."
)

INVARIANTS = [
    "input is a 5..16 square ARC grid",
    "corner color is the background and is not color 1",
    "exactly one cell differs from the background",
    "the unique dot is interior and is not color 1",
    "the semantic branch is exactly whether dot_row == dot_col",
]

EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

AXES = {
    "grid_n": {
        "type": "int",
        "default": "four-residue schedule with canonical 5/7/8 anchors",
        "valid": "5..16",
    },
    "bg_color": {
        "type": "color",
        "default": "scheduled/rng over 2..9; both parities occur in both branches",
        "valid": "2..9",
    },
    "on_diagonal": {
        "type": "bool",
        "default": "alternates by sample_index",
        "valid": "true|false",
    },
}

# Every Cartesian combination of declared axes is valid in every band.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, Any], ...] = ()


SCHEDULE_PROFILES = (
    "diag_not_anti_even_bg",
    "offdiag_on_anti_odd_bg_successor_dot",
    "diag_center_odd_bg",
    "offdiag_center_even_bg",
)


def _band(difficulty: Any) -> str:
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return str(difficulty)
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Name the four-residue lesson schedule; seed intentionally does not matter."""
    del seed
    _band(difficulty)
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def _validate_overrides(overrides: dict[str, Any]) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {unknown}")
    if "grid_n" in overrides and overrides["grid_n"] is not None:
        value = overrides["grid_n"]
        if isinstance(value, bool) or not isinstance(value, int):
            raise TypeError(f"override 'grid_n' must be an integer, got {value!r}")
    if "bg_color" in overrides and overrides["bg_color"] is not None:
        value = overrides["bg_color"]
        if isinstance(value, bool) or not isinstance(value, int):
            raise TypeError(f"override 'bg_color' must be an integer, got {value!r}")
    if "on_diagonal" in overrides and overrides["on_diagonal"] is not None:
        if not isinstance(overrides["on_diagonal"], bool):
            raise TypeError(
                "override 'on_diagonal' must be a bool, "
                f"got {overrides['on_diagonal']!r}"
            )


def _validate_call_arguments(seed: Any, sample_index: Any) -> None:
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool, float, or string)")
    if type(sample_index) is not int:
        raise TypeError(
            "sample_index must be an integer (not bool, float, or string)"
        )
    if sample_index < 0:
        raise ValueError("sample_index must be nonnegative")


def _draw_scheduled_int(ctx, label: str, scheduled: int, lo: int, hi: int) -> int:
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_int(label, lo, hi)
    return ctx.draw_int(label, scheduled, scheduled)


def _draw_scheduled_choice(ctx, label: str, scheduled: Any, options) -> Any:
    options = tuple(options)
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_choice(label, options)
    return ctx.draw_choice(label, (scheduled,))


def _scheduled_size(profile_index: int, band: str) -> int:
    # Every band has at least one canonical 5/7/8 profile in each period.
    return {
        "easy": (5, 6, 7, 8),
        "medium": (7, 9, 8, 10),
        "hard": (8, 12, 14, 16),
    }[band][profile_index]


def _scheduled_bg(ctx, profile_index: int) -> int:
    # Profile 1 must admit the exact successor color used to refute the
    # canonical-fitting dot/background shortcut, so exclude background 9.
    if profile_index == 1:
        parity_pool = (3, 5, 7)
    else:
        parity_pool = (2, 4, 6, 8) if profile_index in (0, 3) else (3, 5, 7, 9)
    return ctx.draw_rng("scheduled_bg").choice(parity_pool)


def _internal_dot_color(ctx, bg: int, profile_index: int) -> int:
    # Profile 1 is off the main diagonal but uses dot = background + 1, an
    # explicit counterexample to a shortcut that fits all canonical pairs.
    if profile_index == 1 and bg < 9:
        return bg + 1
    legal = [color for color in range(2, 10) if color != bg]
    return ctx.draw_rng("dot_color_internal").choice(legal)


def _profile_position(profile_index: int, n: int) -> tuple[int, int]:
    if profile_index == 0:
        # Main diagonal, deliberately not anti-diagonal or centered.
        return 1, 1
    if profile_index == 1:
        # Anti-diagonal, deliberately not main diagonal.
        return 1, n - 2
    if profile_index == 2:
        # Canonical-like centered/main-diagonal example.
        center = n // 2
        return center, center
    # Center-column but off the main diagonal.
    col = n // 2
    row = 1 if col != 1 else 2
    return row, col


def _fallback_position(on_diagonal: bool, n: int, rng) -> tuple[int, int]:
    if on_diagonal:
        choices = [(i, i) for i in range(1, n - 1)]
    else:
        choices = [
            (r, c)
            for r in range(1, n - 1)
            for c in range(1, n - 1)
            if r != c
        ]
    return rng.choice(choices)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call_arguments(seed, sample_index)
    _validate_overrides(overrides)
    band = _band(difficulty)
    profile_index = int(sample_index) % len(SCHEDULE_PROFILES)
    scheduled_on_diagonal = profile_index in (0, 2)

    ctx = gen_ctx(
        seed=int(seed),
        sample_index=int(sample_index),
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )

    n = _draw_scheduled_int(
        ctx, "grid_n", _scheduled_size(profile_index, band), 5, 16
    )
    on_diagonal = bool(
        _draw_scheduled_choice(
            ctx, "on_diagonal", scheduled_on_diagonal, (False, True)
        )
    )

    bg_scheduled = _scheduled_bg(ctx, profile_index)
    bg = int(_draw_scheduled_choice(ctx, "bg_color", bg_scheduled, range(2, 10)))
    dot_color = _internal_dot_color(ctx, bg, profile_index)

    # Preserve the adversarial profile on ordinary draws.  An explicit branch
    # override is exact and wins over the schedule; position itself is not a
    # declared axis, so a deterministic fallback may choose any lawful witness.
    if "on_diagonal" not in overrides or overrides.get("on_diagonal") is None:
        row, col = _profile_position(profile_index, n)
        if (row == col) != on_diagonal:
            raise AssertionError("scheduled position disagrees with branch draw")
    else:
        row, col = _fallback_position(
            on_diagonal, n, ctx.draw_rng("override_dot_position")
        )

    grid = full_grid(n, n, bg)
    grid[row][col] = dot_color
    errors = self_check(grid, difficulty=band, meta={"overrides": overrides})
    if errors:
        raise ValueError("generated invalid grid: " + "; ".join(errors))
    return grid


def _grid_analysis(grid: Any) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(grid, (list, tuple)) or not grid:
        return {"errors": ["grid must be a nonempty row sequence"]}
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return {"errors": ["grid rows must be nonempty sequences"]}
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return {"errors": ["grid must be rectangular"]}
    height = len(grid)
    if height != width:
        errors.append(f"grid must be square, got {height}x{width}")
    if not 5 <= height <= 16 or not 5 <= width <= 16:
        errors.append(f"grid dimensions must be in 5..16, got {height}x{width}")
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        errors.append("cells must be literal ARC integers 0..9")
        return {"errors": errors, "height": height, "width": width}

    bg = int(grid[0][0])
    if bg == 1:
        errors.append("background may not be 1 because the rule paints color 1")
    if not 2 <= bg <= 9:
        errors.append(f"background must be one of 2..9, got {bg}")
    dots = [
        (row, col, int(grid[row][col]))
        for row in range(height)
        for col in range(width)
        if grid[row][col] != bg
    ]
    if len(dots) != 1:
        errors.append(f"expected exactly one non-background dot, got {len(dots)}")
        return {
            "errors": errors,
            "height": height,
            "width": width,
            "grid_n": height if height == width else None,
            "bg_color": bg,
            "dots": dots,
        }
    row, col, dot_color = dots[0]
    if not (1 <= row <= height - 2 and 1 <= col <= width - 2):
        errors.append("dot must be strictly interior")
    if dot_color == 1:
        errors.append("dot color may not be 1 because 1 is the paint color")
    if not 2 <= dot_color <= 9:
        errors.append(f"dot color must be one of 2..9, got {dot_color}")
    return {
        "errors": errors,
        "height": height,
        "width": width,
        "grid_n": height if height == width else None,
        "bg_color": bg,
        "dot_color": dot_color,
        "dot_row": row,
        "dot_col": col,
        "on_diagonal": row == col,
        "on_anti_diagonal": row + col == width - 1,
        "center_column": col == width // 2,
    }


def observe_overrides(grid: Any) -> dict[str, Any]:
    analysis = _grid_analysis(grid)
    if analysis["errors"]:
        return {}
    return {
        "grid_n": analysis["grid_n"],
        "bg_color": analysis["bg_color"],
        "on_diagonal": analysis["on_diagonal"],
    }


def _meta_overrides(meta: Any) -> dict[str, Any]:
    if not isinstance(meta, dict):
        return {}
    nested = meta.get("overrides")
    return nested if isinstance(nested, dict) else meta


def self_check(grid: Any, *, difficulty=None, meta=None) -> list[str]:
    """Recognize the authority-valid one-dot input grammar, not curriculum slots."""
    errors: list[str] = []
    try:
        _band(difficulty)
    except ValueError as exc:
        errors.append(str(exc))
    analysis = _grid_analysis(grid)
    errors.extend(analysis["errors"])
    if analysis["errors"]:
        return errors
    observed = observe_overrides(grid)
    for name, requested in _meta_overrides(meta).items():
        if name in AXES and requested is not None and observed.get(name) != requested:
            errors.append(
                f"override {name}={requested!r} realized as {observed.get(name)!r}"
            )
    return errors


def strict_canonical_like(grid: Any) -> list[str]:
    return self_check(grid)


def _paint_orientation(grid: Any, *, diagonal_orientation: bool) -> list[list[int]]:
    analysis = _grid_analysis(grid)
    if analysis["errors"]:
        raise ValueError("invalid one-dot grid: " + "; ".join(analysis["errors"]))
    n = analysis["grid_n"]
    bg = analysis["bg_color"]
    dot_row = analysis["dot_row"]
    dot_col = analysis["dot_col"]
    out = [list(row) for row in grid]
    for row in range(n):
        if row != dot_row:
            out[row][dot_col] = 1
    top_corner = n - 1 if diagonal_orientation else 0
    bottom_corner = 0 if diagonal_orientation else n - 1
    for col in range(min(dot_col, top_corner), max(dot_col, top_corner) + 1):
        if out[0][col] == bg:
            out[0][col] = 1
    for col in range(min(dot_col, bottom_corner), max(dot_col, bottom_corner) + 1):
        if out[n - 1][col] == bg:
            out[n - 1][col] = 1
    return out


def rule_mirror(grid: Any) -> list[list[int]]:
    """Python test mirror only; the selected Racket program remains output authority."""
    analysis = _grid_analysis(grid)
    if analysis["errors"]:
        raise ValueError("invalid one-dot grid: " + "; ".join(analysis["errors"]))
    return _paint_orientation(grid, diagonal_orientation=analysis["on_diagonal"])


def _rival_always_off(grid: Any) -> list[list[int]]:
    return _paint_orientation(grid, diagonal_orientation=False)


def _rival_always_diag(grid: Any) -> list[list[int]]:
    return _paint_orientation(grid, diagonal_orientation=True)


def _rival_anti_diagonal(grid: Any) -> list[list[int]]:
    analysis = _grid_analysis(grid)
    if analysis["errors"]:
        raise ValueError("invalid grid for anti-diagonal rival")
    return _paint_orientation(
        grid, diagonal_orientation=analysis["on_anti_diagonal"]
    )


def _rival_center_column(grid: Any) -> list[list[int]]:
    analysis = _grid_analysis(grid)
    if analysis["errors"]:
        raise ValueError("invalid grid for center-column rival")
    return _paint_orientation(grid, diagonal_orientation=analysis["center_column"])


def _rival_background_odd(grid: Any) -> list[list[int]]:
    analysis = _grid_analysis(grid)
    if analysis["errors"]:
        raise ValueError("invalid grid for background-parity rival")
    return _paint_orientation(
        grid, diagonal_orientation=bool(analysis["bg_color"] % 2)
    )


def _rival_dot_successor(grid: Any) -> list[list[int]]:
    analysis = _grid_analysis(grid)
    if analysis["errors"]:
        raise ValueError("invalid grid for dot-successor rival")
    return _paint_orientation(
        grid,
        diagonal_orientation=(
            analysis["dot_color"] == analysis["bg_color"] + 1
        ),
    )


SEMANTIC_RIVALS: dict[str, Callable[[Any], list[list[int]]]] = {
    "always_off_diagonal_orientation": _rival_always_off,
    "always_diagonal_orientation": _rival_always_diag,
    "anti_diagonal_predicate": _rival_anti_diagonal,
    "center_column_predicate": _rival_center_column,
    "background_odd_predicate": _rival_background_odd,
    "dot_successor_predicate": _rival_dot_successor,
}
LESSON_COMPETITORS = SEMANTIC_RIVALS
CANONICAL_SHORTCUTS = {
    "anti_diagonal_predicate": _rival_anti_diagonal,
    "center_column_predicate": _rival_center_column,
    "background_odd_predicate": _rival_background_odd,
    "dot_successor_predicate": _rival_dot_successor,
}


def _witness_on_main(grid: Any) -> bool:
    analysis = _grid_analysis(grid)
    return not analysis["errors"] and analysis["on_diagonal"]


def _witness_off_main(grid: Any) -> bool:
    analysis = _grid_analysis(grid)
    return not analysis["errors"] and not analysis["on_diagonal"]


def _witness_diag_not_anti_even_bg(grid: Any) -> bool:
    analysis = _grid_analysis(grid)
    return (
        not analysis["errors"]
        and analysis["on_diagonal"]
        and not analysis["on_anti_diagonal"]
        and not analysis["center_column"]
        and analysis["bg_color"] % 2 == 0
    )


def _witness_offdiag_on_anti_odd_successor_dot(grid: Any) -> bool:
    analysis = _grid_analysis(grid)
    return (
        not analysis["errors"]
        and not analysis["on_diagonal"]
        and analysis["on_anti_diagonal"]
        and analysis["bg_color"] % 2 == 1
        and analysis["dot_color"] == analysis["bg_color"] + 1
    )


def _witness_offdiag_center(grid: Any) -> bool:
    analysis = _grid_analysis(grid)
    return (
        not analysis["errors"]
        and not analysis["on_diagonal"]
        and analysis["center_column"]
    )


SEMANTIC_WITNESSES = {
    "on_main_diagonal_branch": _witness_on_main,
    "off_main_diagonal_branch": _witness_off_main,
    "diag_not_anti_even_bg": _witness_diag_not_anti_even_bg,
    "offdiag_on_anti_odd_successor_dot": _witness_offdiag_on_anti_odd_successor_dot,
    "offdiag_center_column": _witness_offdiag_center,
}
BRANCH_WITNESSES = {
    "on_main_diagonal_branch",
    "off_main_diagonal_branch",
}
WITNESS_RIVALS = {
    "diag_not_anti_even_bg": [
        "always_off_diagonal_orientation",
        "anti_diagonal_predicate",
        "center_column_predicate",
        "background_odd_predicate",
    ],
    "offdiag_on_anti_odd_successor_dot": [
        "always_diagonal_orientation",
        "anti_diagonal_predicate",
        "background_odd_predicate",
        "dot_successor_predicate",
    ],
    "offdiag_center_column": [
        "always_diagonal_orientation",
        "center_column_predicate",
    ],
}


def lesson_identifiable(demos: Any, query: Any) -> list[str]:
    """Require every four-demo window to eliminate the named plausible rivals."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]
    reasons: list[str] = []
    if not isinstance(query, dict) or "input" not in query:
        reasons.append("query must contain an input grid")
    elif self_check(query["input"]):
        reasons.append("query input is outside the teaching grammar")

    valid_demos: list[dict[str, Any]] = []
    branch_values: set[bool] = set()
    bg_colors: set[int] = set()
    sizes: set[int] = set()
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        analysis = _grid_analysis(demo["input"])
        if analysis["errors"]:
            reasons.append(f"demo {index} input is outside the teaching grammar")
            continue
        expected = rule_mirror(demo["input"])
        if demo["output"] != expected:
            reasons.append(f"demo {index} output disagrees with the selected rule")
            continue
        branch_values.add(bool(analysis["on_diagonal"]))
        bg_colors.add(int(analysis["bg_color"]))
        sizes.add(int(analysis["grid_n"]))
        valid_demos.append(demo)

    if branch_values != {False, True}:
        reasons.append("demonstrations must contain both diagonal branches")
    if len(bg_colors) < 2:
        reasons.append("demonstrations must vary background color")
    if len(sizes) < 2:
        reasons.append("demonstrations must vary grid size")
    for name, rival in LESSON_COMPETITORS.items():
        if valid_demos and all(
            rival(demo["input"]) == demo["output"] for demo in valid_demos
        ):
            reasons.append(f"demonstrations do not refute rival {name}")
    return reasons
