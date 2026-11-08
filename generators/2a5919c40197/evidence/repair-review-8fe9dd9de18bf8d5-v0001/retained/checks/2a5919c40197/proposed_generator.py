"""Curriculum generator for uniform-row classification (task 2a5919c40197).

The selected rule classifies each row independently: a row whose cells are all
identical becomes gray (5), and every non-uniform row becomes black (0).

The public canonical examples are all 3x3.  That leaves a strong shortcut:
inspect only the first three cells of every row.  The default two-profile
schedule alternates exact 3x3 anchors with wider examples containing a row that
starts with three equal cells and changes later.  Every three-demonstration
window—and every one-query rotation of its four generated pairs—therefore
contains both a canonical-scale anchor and a counterexample to that shortcut.
Wider examples also include a row that changes only in its final cell, so the
same schedule refutes ignoring the last column in every query rotation.
"""
from __future__ import annotations

from typing import Any

from puzzle_generators.base import gen_ctx


GENERATOR_ID = "2a5919c40197"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
# Preserve this keyed-RNG version: the proposal changes width-extension row
# budgets and adds a witness, while keeping canonical anchors/draw keys stable.
# The candidate source SHA, not VERSION alone, identifies this proposed repair.
RULE_HASH = "bb6a3cb8ba31"

SUMMARY = (
    "Classify each row by full-row uniformity: uniform rows become 5 and mixed "
    "rows become 0. Alternating 3x3 anchors and wider late-change witnesses "
    "teach that cells after the canonical three columns, including the final "
    "column, still matter."
)

INVARIANTS = [
    "rectangular 3..18 by 3..18 ARC-color input",
    "at least one uniform row and at least one non-uniform row",
    "canonical-anchor profile is exactly 3x3 with a 3- or 4-color palette",
    "width-extension profile has width at least 4 and a mixed row whose first three cells agree",
    "every width-extension scene contains a row that changes only in its final cell",
    "generated inputs avoid colors 0 and 5, so the selected rule is never an identity transform",
]

SCHEDULE_PROFILES = ("canonical_anchor", "width_extension")
AXES = {
    "scene_profile": {
        "type": "enum",
        "default": "alternates canonical_anchor / width_extension by sample_index",
        "valid": ["canonical_anchor", "width_extension"],
        "doc": "Choose an exact 3x3 anchor or a wider shortcut-counterexample scene.",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.45

_ALLOWED_DIFFICULTIES = {None, "easy", "medium", "hard"}
_INPUT_COLORS = (1, 2, 3, 4, 6, 7, 8, 9)
_SHORTCUT_NAME = "inspect only the first three cells of each row"
_FINAL_COLUMN_RIVAL_NAME = "ignore the final column of each row"

# These index templates preserve the canonical task's small-scale morphology
# without copying any canonical grid.  Each template uses every listed color,
# has at least one uniform row, and has at least one mixed row.
_CANONICAL_TEMPLATES: tuple[tuple[tuple[int, ...], ...], ...] = (
    ((0, 1, 0), (2, 2, 2), (1, 1, 1)),
    ((0, 1, 1), (2, 2, 2), (1, 0, 0)),
    ((0, 0, 1), (0, 0, 1), (2, 2, 2)),
    ((0, 0, 0), (1, 2, 1), (1, 2, 2)),
    ((0, 0, 0), (1, 2, 1), (3, 3, 3)),
    ((0, 1, 0), (2, 2, 2), (3, 3, 3)),
)


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Return the linked two-profile curriculum slot.

    The schedule deliberately ignores seed and difficulty: consecutive accepted
    sample indices alternate profiles in every band.
    """
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def _draw_scene_profile(ctx, overrides: dict[str, Any]) -> str:
    default = schedule_profile(ctx.seed, ctx.sample_index, ctx.difficulty)
    options = SCHEDULE_PROFILES if overrides.get("scene_profile") is not None else (default,)
    return ctx.draw_choice("scene_profile", options)


def _canonical_grid(ctx) -> list[list[int]]:
    template = ctx.draw_rng("canonical_template").choice(_CANONICAL_TEMPLATES)
    n_colors = 1 + max(value for row in template for value in row)
    palette = ctx.draw_distinct_colors(
        "canonical_palette", n=n_colors, exclude=(0, 5)
    )
    return [[palette[index] for index in row] for row in template]


def _broad_dimensions(ctx) -> tuple[int, int]:
    """Difficulty-aware defaults with full broad variation; not public axes."""
    heights = list(range(3, 19))
    widths = list(range(4, 19))
    if ctx.difficulty == "easy":
        heights += list(range(3, 8)) * 4
        widths += list(range(4, 9)) * 4
    elif ctx.difficulty == "hard":
        heights += list(range(12, 19)) * 4
        widths += list(range(12, 19)) * 4
    else:
        heights += list(range(6, 14)) * 3
        widths += list(range(7, 15)) * 3
    return (
        ctx.draw_rng("broad_height").choice(heights),
        ctx.draw_rng("broad_width").choice(widths),
    )


def _late_change_row(width: int, palette: tuple[int, ...], rng) -> list[int]:
    base, other = palette[0], palette[1]
    row = [base] * width
    # Keep the canonical-width prefix perfectly uniform while changing a later
    # cell.  Prefer an interior late cell when one exists so first/last-only
    # heuristics also receive useful counterevidence.
    candidates = list(range(3, width - 1)) or [width - 1]
    row[rng.choice(candidates)] = other
    return row


def _non_uniform_row(
    pattern: str, width: int, palette: tuple[int, ...], rng
) -> list[int]:
    a, b = palette[0], palette[1]
    if pattern == "alternating":
        row = [a if index % 2 == 0 else b for index in range(width)]
    elif pattern == "split":
        cut = max(1, min(width - 1, rng.randint(1, width - 1)))
        row = [a] * cut + [b] * (width - cut)
    elif pattern == "same_ends":
        row = [a] * width
        row[rng.randint(1, width - 2)] = b
    elif pattern == "one_minority":
        base = rng.choice(palette)
        other = next(color for color in palette if color != base)
        row = [base] * width
        row[rng.randrange(width)] = other
    else:  # random, repaired deterministically if it accidentally collapses
        row = [rng.choice(palette) for _ in range(width)]
        if len(set(row)) == 1:
            row[rng.randrange(width)] = next(color for color in palette if color != row[0])
    return row


def _width_extension_grid(ctx) -> list[list[int]]:
    height, width = _broad_dimensions(ctx)
    palette_size_options = {
        "easy": (3, 3, 4),
        "medium": (3, 4, 4, 5),
        "hard": (4, 5, 5, 6),
        None: (3, 4, 5),
    }[ctx.difficulty]
    n_colors = ctx.draw_rng("broad_palette_size").choice(palette_size_options)
    palette = ctx.draw_distinct_colors(
        "broad_palette", n=n_colors, exclude=(0, 5)
    )

    count_rng = ctx.draw_rng("uniform_count")
    # At width four one mandatory row refutes both rivals. At larger widths,
    # retain the interior change and reserve a second row for the final change.
    n_required_mixed = 1 if width == 4 else 2
    n_uniform = count_rng.randint(1, height - n_required_mixed)
    rows: list[list[int]] = []

    # This first mixed row is the executable counterexample to the strongest
    # canonical-fitting shortcut.
    rows.append(_late_change_row(width, palette, ctx.draw_rng("late_change")))
    if width >= 5:
        rows.append([palette[0]] * (width - 1) + [palette[1]])

    patterns = ("alternating", "split", "same_ends", "one_minority", "random")
    remaining_non_uniform = height - n_uniform - n_required_mixed
    for index in range(remaining_non_uniform):
        pattern = patterns[index % len(patterns)]
        rows.append(
            _non_uniform_row(
                pattern,
                width,
                palette,
                ctx.draw_rng(f"non_uniform_row_{index}"),
            )
        )

    for index in range(n_uniform):
        # palette[0:2] already occur in the mandatory late-change row.  Start
        # uniform rows at palette[2] so every generated scene has at least
        # three visible colors, matching the public task's ordinary grammar.
        color = palette[(index + 2) % len(palette)]
        rows.append([color] * width)

    ctx.draw_rng("row_order").shuffle(rows)
    return rows


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    if difficulty not in _ALLOWED_DIFFICULTIES:
        raise ValueError(
            f"difficulty must be one of easy, medium, hard, or None; got {difficulty!r}"
        )
    if "scene_profile" in overrides and overrides["scene_profile"] is not None:
        value = overrides["scene_profile"]
        if type(value) is not str or value not in SCHEDULE_PROFILES:
            raise ValueError(
                f"scene_profile must be one of {list(SCHEDULE_PROFILES)}, got {value!r}"
            )

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = _draw_scene_profile(ctx, overrides)
    if profile == "canonical_anchor":
        return _canonical_grid(ctx)
    return _width_extension_grid(ctx)


def _grid_shape_errors(grid) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty rectangular grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected nonempty rows"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["expected a rectangular grid"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be integer ARC colors 0..9"]
    return []


def self_check(grid, *, difficulty=None, meta=None):
    """Validate the lawful row-classification domain and non-degenerate signal."""
    del difficulty, meta
    errors = _grid_shape_errors(grid)
    if errors:
        return errors
    height, width = len(grid), len(grid[0])
    if not 3 <= height <= 18:
        errors.append(f"grid height {height} outside [3, 18]")
    if not 3 <= width <= 18:
        errors.append(f"grid width {width} outside [3, 18]")
    palette_size = len({value for row in grid for value in row})
    if palette_size < 3:
        errors.append("expected at least three input colors")
    if not any(len(set(row)) == 1 for row in grid):
        errors.append("no uniform row (output would contain no 5)")
    if not any(len(set(row)) > 1 for row in grid):
        errors.append("no non-uniform row (output would contain no 0)")
    return errors


def strict_canonical_like(grid):
    """Accept the public task's exact 3x3, 3/4-color input profile."""
    errors = self_check(grid)
    if errors:
        return errors
    reasons: list[str] = []
    if (len(grid), len(grid[0])) != (3, 3):
        reasons.append("canonical profile is exactly 3x3")
    palette_size = len({value for row in grid for value in row})
    if palette_size not in (3, 4):
        reasons.append("canonical profile uses exactly 3 or 4 input colors")
    return reasons


def observe_overrides(grid) -> dict[str, str]:
    """Recover the exact public profile from returned pixels."""
    profile = "canonical_anchor" if strict_canonical_like(grid) == [] else "width_extension"
    return {"scene_profile": profile}


def rule_mirror(grid) -> list[list[int]]:
    """Independent Python mirror used only for tests and semantic probes."""
    return [
        [5 if len(set(row)) == 1 else 0] * len(row)
        for row in grid
    ]


def _first_three_only(grid) -> list[list[int]]:
    """Rival: incorrectly ignores every cell after the canonical width."""
    return [
        [5 if len(set(row[:3])) == 1 else 0] * len(row)
        for row in grid
    ]


def _has_late_change_after_three(grid) -> bool:
    if _grid_shape_errors(grid):
        return False
    return any(
        len(row) >= 4 and len(set(row[:3])) == 1 and len(set(row)) > 1
        for row in grid
    )


def _ignore_final_column(grid) -> list[list[int]]:
    """Lesson rival already refuted by the full canonical demonstration set."""
    return [
        [5 if len(set(row[:-1])) == 1 else 0] * len(row)
        for row in grid
    ]


SEMANTIC_WITNESSES = {"late_change_after_three": _has_late_change_after_three}
SEMANTIC_RIVALS = {_SHORTCUT_NAME: _first_three_only}
WITNESS_RIVALS = {"late_change_after_three": [_SHORTCUT_NAME]}
CANONICAL_SHORTCUTS = {_SHORTCUT_NAME: _first_three_only}
LESSON_COMPETITORS = {
    _SHORTCUT_NAME: _first_three_only,
    _FINAL_COLUMN_RIVAL_NAME: _ignore_final_column,
}


def lesson_identifiable(demos, query):
    """Require both a canonical anchor and a direct refutation in the demos."""
    del query
    reasons: list[str] = []
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]

    valid_pairs = [
        pair
        for pair in demos
        if isinstance(pair, dict) and "input" in pair and "output" in pair
    ]
    if len(valid_pairs) != len(demos):
        return ["every demonstration must be a labeled input/output pair"]

    if not any(strict_canonical_like(pair["input"]) == [] for pair in valid_pairs):
        reasons.append("demonstrations omit a canonical 3x3 anchor")
    if not any(_has_late_change_after_three(pair["input"]) for pair in valid_pairs):
        reasons.append("demonstrations omit a post-column-three change witness")

    for name, competitor in LESSON_COMPETITORS.items():
        try:
            survives = all(
                competitor(copy_grid := [list(row) for row in pair["input"]])
                == pair["output"]
                for pair in valid_pairs
            )
        except Exception as exc:
            reasons.append(f"competitor {name!r} could not be scored: {type(exc).__name__}: {exc}")
            continue
        if survives:
            reasons.append(f"competitor {name!r} fits every demonstration")
    return reasons
