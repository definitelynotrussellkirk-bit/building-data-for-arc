"""Constructive input sampler for ARC task aa378df15340.

Canonical rule
--------------
For every nonzero input cell at ``(row, col)``, copy the same color to
``(col, row)`` while preserving the original cell.  The selected Racket rule is
unchanged; this module generates inputs only.

All canonical sources lie above the main diagonal, so the plausible shortcut
"copy upper-triangle cells only" fits every public pair.  Every ordinary draw
contains sources on both sides of the diagonal and chooses at most one member
of each transpose orbit.  Thus each generated pair refutes that shortcut while
avoiding the unsupported occupied-target collision found by prior audit.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "aa378df15340"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "ba8b31fe9030"
SUMMARY = (
    "Square 5..12 grids with 3..9 colored off-diagonal sources. Distinct "
    "transpose orbits keep every destination empty; positions span multiple "
    "rows and columns and occur on both sides of the main diagonal, so each "
    "lesson teaches bidirectional additive transpose without collision semantics."
)

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0
INCOMPATIBLE_OVERRIDE_COMBINATIONS = [("n_seeds", "n_colors")]
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

AXES = {
    "grid_n": {
        "type": "int",
        "default": "difficulty-weighted draw over the full 5..12 domain",
        "valid": "5..12",
        "doc": "Square input side length; every value is valid in every band.",
    },
    "n_seeds": {
        "type": "int",
        "default": "difficulty-weighted draw over the full 3..9 domain",
        "valid": "3..9",
        "doc": "Exact number of nonzero source cells; one per transpose orbit.",
    },
    "n_colors": {
        "type": "int",
        "default": "weighted draw over 1..4, favoring canonical-like three/four-color scenes",
        "valid": "1..4",
        "doc": "Exact number of distinct nonzero colors used by the sources.",
    },
}

INVARIANTS = [
    "input is square and uses literal ARC colors 0..9",
    "3..9 nonzero sources occupy distinct off-diagonal transpose orbits",
    "every transpose destination is black before the rule executes",
    "source positions span at least two rows and at least two columns",
    "every generated input contains sources above and below the main diagonal",
    "all advertised overrides are exact and observable; n_colors may not exceed n_seeds",
]

_SIZE_OPTIONS = {
    None: (5, 5, 6, 6, 7, 7, 8, 8, 9, 10, 11, 12),
    "easy": (5, 5, 5, 6, 6, 6, 7, 7, 8, 9, 10, 11, 12),
    "medium": (5, 6, 6, 7, 7, 8, 8, 9, 9, 10, 11, 12),
    "hard": (5, 6, 7, 8, 8, 9, 9, 10, 10, 11, 11, 12, 12),
}
_SEED_OPTIONS = {
    None: (3, 3, 4, 4, 5, 6, 7, 8, 9),
    "easy": (3, 3, 3, 4, 4, 5, 6, 7, 8, 9),
    "medium": (3, 4, 4, 5, 5, 6, 6, 7, 8, 9),
    "hard": (3, 4, 5, 6, 6, 7, 7, 8, 8, 9, 9),
}
_COLOR_OPTIONS = {
    None: (1, 2, 3, 3, 4, 4),
    "easy": (1, 2, 2, 3, 3, 4),
    "medium": (1, 2, 3, 3, 4, 4),
    "hard": (1, 2, 3, 3, 4, 4),
}


def _validate_request(difficulty: str | None, overrides: dict[str, Any]) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(
            f"unknown difficulty {difficulty!r}; expected easy, medium, hard, or None"
        )
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")
    for name, lo, hi in (
        ("grid_n", 5, 12),
        ("n_seeds", 3, 9),
        ("n_colors", 1, 4),
    ):
        if name not in overrides:
            continue
        value = overrides[name]
        if type(value) is not int:
            raise TypeError(
                f"{name} override must be an integer, not {type(value).__name__}"
            )
        if not lo <= value <= hi:
            raise ValueError(f"{name} override {value} outside [{lo}, {hi}]")
    if (
        "n_seeds" in overrides
        and "n_colors" in overrides
        and overrides["n_colors"] > overrides["n_seeds"]
    ):
        error = ValueError(
            f"n_colors={overrides['n_colors']} cannot exceed n_seeds={overrides['n_seeds']}"
        )
        error.incompatible_axes = ("n_seeds", "n_colors")
        raise error


def _shape_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a nonempty sequence of rows"]
    if any(not isinstance(row, (list, tuple)) or not row for row in grid):
        return ["every row must be a nonempty sequence"]
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if len(grid) != width:
        return [f"grid must be square, got {len(grid)}x{width}"]
    if any(
        type(value) is not int or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["cells must be integer ARC colors 0..9 (booleans are invalid)"]
    return []


def _marks(grid: list[list[int]] | tuple[tuple[int, ...], ...]) -> list[tuple[int, int, int]]:
    return [
        (row, col, value)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value != 0
    ]


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Pure Python mirror of the selected additive-transpose authority."""
    out = deepcopy(grid)
    for row, col, value in _marks(grid):
        out[col][row] = value
    return out


def _upper_triangle_only(grid: list[list[int]]) -> list[list[int]]:
    """Rival that fits every canonical pair but ignores lower sources."""
    out = deepcopy(grid)
    for row, col, value in _marks(grid):
        if row < col:
            out[col][row] = value
    return out


def _has_lower_triangle_source(grid: list[list[int]]) -> bool:
    return any(row > col for row, col, _ in _marks(grid))


SEMANTIC_WITNESSES: dict[str, Callable[[list[list[int]]], bool]] = {
    "lower_triangle_source": _has_lower_triangle_source,
}
SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "upper_triangle_only": _upper_triangle_only,
}
WITNESS_RIVALS = {"lower_triangle_source": ["upper_triangle_only"]}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def strict_canonical_like(grid: Any) -> list[str]:
    """Recognize the lawful collision-free task manifold and canonical inputs."""
    errors = _shape_errors(grid)
    if errors:
        return errors

    size = len(grid)
    if not 5 <= size <= 12:
        errors.append(f"grid_n={size} outside the supported [5, 12] range")

    marks = _marks(grid)
    if not 3 <= len(marks) <= 9:
        errors.append(f"n_seeds={len(marks)} outside the supported [3, 9] range")

    diagonal = [(row, col) for row, col, _ in marks if row == col]
    if diagonal:
        errors.append(f"sources must be off the main diagonal: {diagonal[:3]}")

    occupied_targets = [
        (row, col)
        for row, col, _ in marks
        if grid[col][row] != 0
    ]
    if occupied_targets:
        errors.append(
            "transpose targets must be empty before the rule executes: "
            f"{occupied_targets[:3]}"
        )

    source_rows = {row for row, _, _ in marks}
    source_cols = {col for _, col, _ in marks}
    if len(source_rows) < 2:
        errors.append("source positions must span at least two rows")
    if len(source_cols) < 2:
        errors.append("source positions must span at least two columns")

    color_count = len({value for _, _, value in marks})
    # Four colors are retained for canonical ownership and are also exercised
    # by ordinary exact/default draws.
    if not 1 <= color_count <= 4:
        errors.append(f"nonzero color count {color_count} outside [1, 4]")

    if 0 not in {value for row in grid for value in row}:
        errors.append("black(0) background is absent")
    return errors


def observe_overrides(grid: list[list[int]]) -> dict[str, int]:
    errors = strict_canonical_like(grid)
    if errors:
        raise ValueError("cannot observe malformed/non-domain grid: " + "; ".join(errors))
    marks = _marks(grid)
    return {
        "grid_n": len(grid),
        "n_seeds": len(marks),
        "n_colors": len({value for _, _, value in marks}),
    }


def self_check(
    grid: Any, *, difficulty: str | None = None, meta: Any = None
) -> list[str]:
    errors = strict_canonical_like(grid)
    if difficulty not in (None, "easy", "medium", "hard"):
        errors.append(f"unknown difficulty {difficulty!r}")
    expected = meta.get("overrides") if isinstance(meta, dict) else None
    if isinstance(expected, dict) and expected and not errors:
        try:
            actual = observe_overrides(grid)
        except ValueError as exc:
            errors.append(str(exc))
        else:
            for name, requested in expected.items():
                if name in AXES and actual.get(name) != requested:
                    errors.append(
                        f"override {name!r} expected {requested!r}, "
                        f"observed {actual.get(name)!r}"
                    )
    return errors


def _teaching_contract_errors(grid: list[list[int]]) -> list[str]:
    errors = strict_canonical_like(grid)
    if errors:
        return errors
    marks = _marks(grid)
    if not any(row < col for row, col, _ in marks):
        errors.append("generated lesson lacks an upper-triangle source")
    if not any(row > col for row, col, _ in marks):
        errors.append("generated lesson lacks a lower-triangle source")
    if _upper_triangle_only(grid) == rule_mirror(grid):
        errors.append("upper-triangle-only shortcut is not answer-changing")
    return errors


def generate(
    seed: int,
    sample_index: int,
    *,
    difficulty: str | None = None,
    **overrides: Any,
) -> list[list[int]]:
    _validate_request(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    size = ctx.draw_choice("grid_n", _SIZE_OPTIONS[difficulty])
    requested_colors = overrides.get("n_colors")
    seed_options = tuple(
        value
        for value in _SEED_OPTIONS[difficulty]
        if requested_colors is None or value >= requested_colors
    )
    n_seeds = ctx.draw_choice("n_seeds", seed_options)
    color_options = tuple(value for value in _COLOR_OPTIONS[difficulty] if value <= n_seeds)
    n_colors = ctx.draw_choice("n_colors", color_options)

    # Choose one representative from each unordered transpose orbit.  This is
    # the root repair for the audited seed: both members can never be occupied.
    layout_rng = ctx.draw_rng("layout")
    orbits = [(row, col) for row in range(size) for col in range(row + 1, size)]
    positions: list[tuple[int, int]] | None = None
    for _attempt in range(128):
        selected = layout_rng.sample(orbits, n_seeds)
        orientations = [True, False] + [
            bool(layout_rng.randrange(2)) for _ in range(n_seeds - 2)
        ]
        layout_rng.shuffle(orientations)
        candidate = [
            (row, col) if upper else (col, row)
            for (row, col), upper in zip(selected, orientations)
        ]
        if (
            len({row for row, _ in candidate}) >= 2
            and len({col for _, col in candidate}) >= 2
        ):
            positions = candidate
            break
    if positions is None:  # pragma: no cover - impossible in the declared domain
        raise AssertionError("could not construct a non-collinear source placement")

    palette_rng = ctx.draw_rng("palette")
    palette = palette_rng.sample(range(1, 10), n_colors)
    values = list(palette)
    values.extend(palette_rng.choice(palette) for _ in range(n_seeds - n_colors))
    palette_rng.shuffle(values)

    grid = full_grid(size, size, 0)
    for (row, col), value in zip(positions, values):
        grid[row][col] = value

    findings = _teaching_contract_errors(grid)
    if findings:
        raise AssertionError(
            "constructive generator violated its teaching contract: "
            + "; ".join(findings)
        )
    return grid


def lesson_identifiable(
    demos: list[dict[str, list[list[int]]]],
    query: dict[str, list[list[int]]],
) -> list[str]:
    """Finite certificate against the declared canonical-fitting shortcut."""
    reasons: list[str] = []
    if not isinstance(demos, list) or len(demos) < EXAMPLES_NEEDED:
        return [f"expected at least {EXAMPLES_NEEDED} demonstrations"]

    labelled: list[dict[str, list[list[int]]]] = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} is not a labelled input/output pair")
            continue
        domain_errors = strict_canonical_like(pair["input"])
        if domain_errors:
            reasons.append(f"demo {index} is outside the task manifold")
            continue
        if rule_mirror(pair["input"]) != pair["output"]:
            reasons.append(f"demo {index} output disagrees with the canonical mirror")
            continue
        labelled.append(pair)
    if reasons:
        return reasons

    survivors = [
        name
        for name, rival in LESSON_COMPETITORS.items()
        if all(rival(pair["input"]) == pair["output"] for pair in labelled)
    ]
    if survivors:
        reasons.append(
            "declared competitors survive all demonstrations: "
            + ", ".join(sorted(survivors))
        )

    if not isinstance(query, dict) or "input" not in query:
        reasons.append("query is missing an input grid")
    else:
        if strict_canonical_like(query["input"]):
            reasons.append("query is outside the task manifold")
        if "output" in query and rule_mirror(query["input"]) != query["output"]:
            reasons.append("query output disagrees with the canonical mirror")
    return reasons
