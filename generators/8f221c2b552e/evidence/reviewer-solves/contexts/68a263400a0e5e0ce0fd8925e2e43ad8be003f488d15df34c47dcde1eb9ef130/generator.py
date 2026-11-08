"""Constructive input sampler for row-local same-color segment bridging.

The selected Racket authority is unchanged: in each row, every nonzero color
that appears at least twice is painted from its leftmost to rightmost occurrence.
This sampler keeps pair rows clean, varies span lengths and row-local color reuse,
and includes a scheduled counterexample to the canonical-fitting shortcut
"only bridge colors that occur exactly twice in the whole grid".
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "8f221c2b552e"
TASK_ID = GENERATOR_ID
RULE_HASH = "df008460a237"
VERSION = "2.0.0"

SUMMARY = (
    "Scan rows independently. Each active row has two separated endpoints of "
    "one color; fill the inclusive segment between them. Singleton distractors "
    "stay unchanged, and the same pair color may be reused in several rows."
)

EXAMPLES_NEEDED = 3
INVARIANTS = [
    "background is 0 and cells are ARC colors 0..9",
    "2..5 active rows each contain exactly two separated endpoints of one color",
    "pair interiors start empty; non-pair cells are at most three unique singleton distractors",
    "pair colors are either all distinct or one shared row-local color",
    "short, long, and mixed span curricula all preserve at least one cell to fill",
]

AXES = {
    "grid_h": {"type": "int", "default": "scheduled 6..10", "valid": "6..10"},
    "grid_w": {"type": "int", "default": "scheduled 8..14", "valid": "8..14"},
    "n_pairs": {"type": "int", "default": "scheduled 2..5", "valid": "2..5"},
    "color_mode": {
        "type": "str",
        "default": "scheduled distinct/shared",
        "valid": "distinct|shared",
    },
    "distractor_count": {
        "type": "int",
        "default": "scheduled 0..3",
        "valid": "0..3",
    },
    "span_style": {
        "type": "str",
        "default": "scheduled short/long/mixed",
        "valid": "short|long|mixed",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

_VALID_DIFFICULTIES = (None, "easy", "medium", "hard")
_INT_DOMAINS = {
    "grid_h": (6, 10),
    "grid_w": (8, 14),
    "n_pairs": (2, 5),
    "distractor_count": (0, 3),
}
_CHOICE_DOMAINS = {
    "color_mode": ("distinct", "shared"),
    "span_style": ("short", "long", "mixed"),
}

_PROFILE_NAMES = (
    "canonical_6x8",
    "shared_7x9",
    "canonical_8x10",
    "shared_6x11",
    "canonical_7x10",
    "broad_shared",
)
SCHEDULE_PROFILES = _PROFILE_NAMES


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Six-slot deterministic curriculum; every 3-demo window has color reuse."""
    del seed, difficulty
    return _PROFILE_NAMES[int(sample_index) % len(_PROFILE_NAMES)]


def _scheduled_defaults(profile: str, difficulty) -> dict[str, Any]:
    fixed = {
        "canonical_6x8": dict(
            grid_h=6, grid_w=8, n_pairs=2, color_mode="distinct",
            distractor_count=0, span_style="short",
        ),
        "shared_7x9": dict(
            grid_h=7, grid_w=9, n_pairs=3, color_mode="shared",
            distractor_count=2, span_style="long",
        ),
        "canonical_8x10": dict(
            grid_h=8, grid_w=10, n_pairs=3, color_mode="distinct",
            distractor_count=0, span_style="mixed",
        ),
        "shared_6x11": dict(
            grid_h=6, grid_w=11, n_pairs=3, color_mode="shared",
            distractor_count=2, span_style="short",
        ),
        "canonical_7x10": dict(
            grid_h=7, grid_w=10, n_pairs=3, color_mode="distinct",
            distractor_count=0, span_style="long",
        ),
    }
    if profile in fixed:
        return fixed[profile]
    if difficulty == "easy":
        return dict(
            grid_h=6, grid_w=8, n_pairs=2, color_mode="shared",
            distractor_count=3, span_style="mixed",
        )
    if difficulty == "hard":
        return dict(
            grid_h=10, grid_w=14, n_pairs=5, color_mode="shared",
            distractor_count=3, span_style="mixed",
        )
    return dict(
        grid_h=9, grid_w=12, n_pairs=4, color_mode="shared",
        distractor_count=3, span_style="mixed",
    )


def _scheduled_int(ctx, label: str, lo: int, hi: int, scheduled: int) -> int:
    if ctx.overrides.get(label) is not None:
        return ctx.draw_int(label, lo, hi)
    return ctx.draw_int(label, scheduled, scheduled)


def _scheduled_choice(ctx, label: str, options: tuple[str, ...], scheduled: str) -> str:
    if ctx.overrides.get(label) is not None:
        return str(ctx.draw_choice(label, options))
    return str(ctx.draw_choice(label, (scheduled,)))


def _validate_call(difficulty, overrides: dict[str, Any]) -> None:
    if difficulty not in _VALID_DIFFICULTIES:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {unknown}")
    for name, value in overrides.items():
        if value is None:
            continue
        if name in _INT_DOMAINS:
            lo, hi = _INT_DOMAINS[name]
            if type(value) is not int:
                raise ValueError(f"{name} must be an integer, not {type(value).__name__}")
            if not lo <= value <= hi:
                raise ValueError(f"{name}={value} outside [{lo}, {hi}]")
        else:
            options = _CHOICE_DOMAINS[name]
            if type(value) is not str or value not in options:
                raise ValueError(f"{name} must be one of {options}, not {value!r}")


def _span_candidates(width: int, kind: str) -> list[tuple[int, int]]:
    candidates = []
    for left in range(width):
        for right in range(left + 2, width):
            gap = right - left - 1
            if left == 0 and right == width - 1:
                continue  # generated rows retain an outside background witness
            if kind == "short" and gap <= 2:
                candidates.append((left, right))
            elif kind == "long" and gap >= 3:
                candidates.append((left, right))
    if not candidates:
        raise ValueError(f"grid_w={width} cannot realize {kind!r} spans")
    return candidates


def _span_kinds(style: str, count: int, rng) -> list[str]:
    if style == "short":
        return ["short"] * count
    if style == "long":
        return ["long"] * count
    kinds = ["short", "long"]
    kinds.extend(rng.choice(("short", "long")) for _ in range(count - 2))
    rng.shuffle(kinds)
    return kinds


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = schedule_profile(seed, sample_index, difficulty)
    defaults = _scheduled_defaults(profile, difficulty)

    h = _scheduled_int(ctx, "grid_h", 6, 10, int(defaults["grid_h"]))
    w = _scheduled_int(ctx, "grid_w", 8, 14, int(defaults["grid_w"]))
    n_pairs = _scheduled_int(ctx, "n_pairs", 2, 5, int(defaults["n_pairs"]))
    color_mode = _scheduled_choice(
        ctx, "color_mode", ("distinct", "shared"), str(defaults["color_mode"])
    )
    distractor_count = _scheduled_int(
        ctx, "distractor_count", 0, 3, int(defaults["distractor_count"])
    )
    span_style = _scheduled_choice(
        ctx, "span_style", ("short", "long", "mixed"), str(defaults["span_style"])
    )

    grid = full_grid(h, w, 0)
    layout_rng = ctx.draw_rng("layout")
    pair_rows = sorted(layout_rng.sample(range(h), n_pairs))
    inactive_rows = [row for row in range(h) if row not in set(pair_rows)]

    pair_color_count = n_pairs if color_mode == "distinct" else 1
    palette = ctx.draw_rng("palette").sample(
        list(range(1, 10)), pair_color_count + distractor_count
    )
    if color_mode == "distinct":
        pair_colors = palette[:n_pairs]
        distractor_colors = palette[n_pairs:]
    else:
        pair_colors = [palette[0]] * n_pairs
        distractor_colors = palette[1:]

    kinds = _span_kinds(span_style, n_pairs, ctx.draw_rng("span_kind_order"))
    short_candidates = _span_candidates(w, "short")
    long_candidates = _span_candidates(w, "long")
    endpoint_rng = ctx.draw_rng("endpoints")
    for row, color, kind in zip(pair_rows, pair_colors, kinds):
        left, right = endpoint_rng.choice(
            short_candidates if kind == "short" else long_candidates
        )
        grid[row][left] = color
        grid[row][right] = color

    if distractor_count:
        cells = [(row, col) for row in inactive_rows for col in range(w)]
        chosen = ctx.draw_rng("distractor_positions").sample(cells, distractor_count)
        for (row, col), color in zip(chosen, distractor_colors):
            grid[row][col] = color
    return grid


def _inspect(grid) -> tuple[dict[str, Any] | None, list[str]]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return None, ["expected a nonempty rectangular grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return None, ["expected nonempty rows"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return None, ["ragged grid"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return None, ["cells must be integer ARC colors 0..9"]

    height = len(grid)
    errors: list[str] = []
    if not 6 <= height <= 10:
        errors.append(f"grid_h={height} outside [6,10]")
    if not 8 <= width <= 14:
        errors.append(f"grid_w={width} outside [8,14]")

    pair_colors: list[int] = []
    gaps: list[int] = []
    distractor_colors: list[int] = []
    for row_index, row in enumerate(grid):
        positions: dict[int, list[int]] = {}
        for col, value in enumerate(row):
            if value:
                positions.setdefault(value, []).append(col)
        repeated = [(color, cols) for color, cols in positions.items() if len(cols) >= 2]
        if repeated:
            if len(repeated) != 1 or len(positions) != 1:
                errors.append(f"row {row_index} mixes a pair with other markers")
                continue
            color, columns = repeated[0]
            if len(columns) != 2:
                errors.append(f"row {row_index} must have exactly two endpoints")
                continue
            gap = columns[1] - columns[0] - 1
            if gap < 1:
                errors.append(f"row {row_index} endpoints must have an empty interior")
                continue
            if any(row[col] != 0 for col in range(columns[0] + 1, columns[1])):
                errors.append(f"row {row_index} pair interior must start empty")
                continue
            pair_colors.append(color)
            gaps.append(gap)
        else:
            if any(len(columns) != 1 for columns in positions.values()):
                errors.append(f"row {row_index} contains a malformed repeated color")
            distractor_colors.extend(positions)

    if not 2 <= len(pair_colors) <= 5:
        errors.append(f"n_pairs={len(pair_colors)} outside [2,5]")
    if len(distractor_colors) > 3:
        errors.append(f"distractor_count={len(distractor_colors)} outside [0,3]")
    if len(distractor_colors) != len(set(distractor_colors)):
        errors.append("distractor colors must be globally unique singletons")
    if set(distractor_colors) & set(pair_colors):
        errors.append("distractor colors must be distinct from pair colors")

    color_mode = None
    if pair_colors:
        if len(set(pair_colors)) == 1:
            color_mode = "shared"
        elif len(set(pair_colors)) == len(pair_colors):
            color_mode = "distinct"
        else:
            errors.append("pair colors must be all shared or all distinct")

    span_style = None
    if gaps:
        has_short = any(gap <= 2 for gap in gaps)
        has_long = any(gap >= 3 for gap in gaps)
        span_style = "mixed" if has_short and has_long else ("short" if has_short else "long")

    observed = {
        "grid_h": height,
        "grid_w": width,
        "n_pairs": len(pair_colors),
        "color_mode": color_mode,
        "distractor_count": len(distractor_colors),
        "span_style": span_style,
    }
    return observed, errors


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty, meta
    _, errors = _inspect(grid)
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Lawful row-pair instances in the declared sampler manifold."""
    return self_check(grid)


def observe_overrides(grid) -> dict[str, Any]:
    """Recover every advertised exact control from returned pixels."""
    observed, errors = _inspect(grid)
    if errors:
        raise ValueError("; ".join(errors))
    return observed


def rule_mirror(grid):
    """Pure Python mirror used only for task-local tests and rival definitions."""
    out = deepcopy(grid)
    for row_index, row in enumerate(grid):
        by_color: dict[int, list[int]] = {}
        for col, value in enumerate(row):
            if value:
                by_color.setdefault(value, []).append(col)
        for color, columns in by_color.items():
            if len(columns) >= 2:
                for col in range(min(columns), max(columns) + 1):
                    out[row_index][col] = color
    return out


def _global_exactly_two(grid):
    """Rival: bridges a color only when it occurs exactly twice globally."""
    totals = Counter(value for row in grid for value in row if value)
    out = deepcopy(grid)
    for row_index, row in enumerate(grid):
        by_color: dict[int, list[int]] = {}
        for col, value in enumerate(row):
            if value:
                by_color.setdefault(value, []).append(col)
        for color, columns in by_color.items():
            if totals[color] == 2 and len(columns) >= 2:
                for col in range(min(columns), max(columns) + 1):
                    out[row_index][col] = color
    return out


def _reused_pair_color(grid) -> bool:
    observed, errors = _inspect(grid)
    return not errors and observed["color_mode"] == "shared"


SEMANTIC_WITNESSES = {"reused_pair_color": _reused_pair_color}
SEMANTIC_RIVALS = {"global_exactly_two": _global_exactly_two}
WITNESS_RIVALS = {"reused_pair_color": ["global_exactly_two"]}
CANONICAL_SHORTCUTS = {"global_exactly_two": _global_exactly_two}
LESSON_COMPETITORS = {"global_exactly_two": _global_exactly_two}


def lesson_identifiable(demos, query) -> list[str]:
    """A lesson is sufficient when every declared canonical shortcut is refuted."""
    del query
    reasons = []
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            reasons.append(f"competitor {name!r} fits every demonstration")
    return reasons
