"""Generator for arc_additional_puzzles_21_set2:E14 — midpoint marker.

For each row containing exactly two color-8 cells, paint their single-cell
midpoint red (2) only when the endpoint columns have the same parity and the
midpoint is background (0). Rows with an odd-distance pair, three 8s, or an
occupied midpoint are explicit non-firing witnesses.
"""
from __future__ import annotations

from collections import Counter
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "02fcd49e49d6"
TASK_ID = "02fcd49e49d6"
VERSION = "1.3.0"
RULE_HASH = "ad32c1140d6e"

SUMMARY = (
    "In every row with exactly two 8s, paint the empty integer midpoint red(2); "
    "odd-distance pairs, three-8 rows, and occupied midpoints remain unchanged."
)

# Four consecutive default sample indices deliberately cover one positive-only
# scene and all three semantic non-firing branches. This makes a normal lesson
# refute the common shortcuts rather than relying on a lucky random draw.
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "1..5 rows have exactly two 8s with an empty integer midpoint",
    "at most one explicit non-firing row is present: odd_pair, triple_8s, or filled_mid",
    "all other rows are blank and no input cell is red(2)",
]

NEAR_MISSES = ("none", "odd_pair", "triple_8s", "filled_mid")
DISTRACTOR_COLORS = (1, 3, 4, 5, 6, 7, 9)

AXES = {
    "grid_h": {
        "type": "int",
        "default": "easy 5..7; medium 6..8; hard 8..10; linked canonical prior",
        "valid": "4..10",
        "doc": "Grid height.",
    },
    "grid_w": {
        "type": "int",
        "default": "easy 7..9; medium 8..11; hard 10..14; linked canonical prior",
        "valid": "7..14",
        "doc": "Grid width.",
    },
    "n_rows": {
        "type": "int",
        "default": "easy about 2; medium about 3; hard about 4..5",
        "valid": "1..5",
        "doc": "Number of firing rows, recovered exactly from the returned grid.",
    },
    "near_miss": {
        "type": "enum",
        "default": "deterministic four-sample lesson cycle",
        "valid": "none|odd_pair|triple_8s|filled_mid",
        "doc": "Optional single row that the rule must leave unchanged.",
    },
}

_BAND_H = {
    "easy": (5, 7),
    "medium": (6, 8),
    "hard": (8, 10),
}
_BAND_W = {
    "easy": (7, 9),
    "medium": (8, 11),
    "hard": (10, 14),
}
_BAND_ROWS = {
    "easy": (2, 3),
    "medium": (3, 4),
    "hard": (4, 5),
}

# Executably checked against every canonical train and held-out test input by
# tests/test_generator_02fcd49e49d6.py. Horizontal translation is nuisance;
# the linked signature retains the answer-bearing row positions and pair gaps.
_CANONICAL_PROFILES = (
    (6, 8, ((0, 4), (2, 4), (4, 4))),
    (7, 9, ((1, 6), (3, 2), (5, 4))),
    (8, 10, ((0, 6), (2, 4), (4, 6), (6, 4))),
)
_CANONICAL_SIGNATURES = frozenset(_CANONICAL_PROFILES)
_CANONICAL_PRIOR = 0.80


def _normalize_difficulty(difficulty: str | None) -> str:
    if difficulty is None:
        return "medium"
    if difficulty not in _BAND_H:
        raise ValueError("difficulty must be easy, medium, hard, or None")
    return difficulty


def _validate_request(overrides: dict[str, Any]) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown overrides: {', '.join(unknown)}")
    for name, lo, hi in (
        ("grid_h", 4, 10),
        ("grid_w", 7, 14),
        ("n_rows", 1, 5),
    ):
        value = overrides.get(name)
        if value is None:
            continue
        try:
            value = int(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"{name} must be an integer") from exc
        if not lo <= value <= hi:
            raise ValueError(f"{name} must be in {lo}..{hi}")
    near_miss = overrides.get("near_miss")
    if near_miss is not None and near_miss not in NEAR_MISSES:
        raise ValueError(f"near_miss must be one of {NEAR_MISSES}")


def _draw_int_axis(ctx, label: str, default_bounds: tuple[int, int], valid: tuple[int, int]) -> int:
    if ctx.overrides.get(label) is not None:
        return ctx.draw_int(label, *valid)
    return ctx.draw_int(label, *default_bounds)


def _scheduled_near_miss(sample_index: int) -> str:
    return ("none", "odd_pair", "triple_8s", "filled_mid")[sample_index % 4]


def _draw_near_miss(ctx, sample_index: int) -> str:
    if ctx.overrides.get("near_miss") is not None:
        return ctx.draw_choice("near_miss", NEAR_MISSES)
    return ctx.draw_choice("near_miss", (_scheduled_near_miss(sample_index),))


def _canonical_profile(ctx, difficulty: str, overrides: dict[str, Any], near_miss: str):
    if overrides or near_miss != "none":
        return None
    rng = ctx.draw_rng("linked_canonical_profile")
    if rng.random() >= _CANONICAL_PRIOR:
        return None
    h, w, rows_and_gaps = rng.choice(_CANONICAL_PROFILES)
    # Every declared exact axis is still recorded through a keyed draw.
    ctx.draw_int("grid_h", h, h)
    ctx.draw_int("grid_w", w, w)
    ctx.draw_int("n_rows", len(rows_and_gaps), len(rows_and_gaps))
    return h, w, rows_and_gaps


def _draw_axes(ctx, difficulty: str, overrides: dict[str, Any], near_miss: str):
    profile = _canonical_profile(ctx, difficulty, overrides, near_miss)
    if profile is not None:
        return (*profile[:2], len(profile[2]), profile[2])

    extra_row = int(near_miss != "none")
    requested_rows = overrides.get("n_rows")
    requested_rows = int(requested_rows) if requested_rows is not None else None

    if overrides.get("grid_h") is not None:
        h = ctx.draw_int("grid_h", 4, 10)
    else:
        lo, hi = _BAND_H[difficulty]
        if requested_rows is not None:
            lo = max(lo, requested_rows + extra_row)
            hi = max(hi, lo)
        if hi > 10:
            raise ValueError("n_rows plus near_miss cannot fit within grid_h<=10")
        h = ctx.draw_int("grid_h", lo, hi)

    w = _draw_int_axis(ctx, "grid_w", _BAND_W[difficulty], (7, 14))
    capacity = h - extra_row
    if requested_rows is not None:
        n_rows = ctx.draw_int("n_rows", 1, 5)
        if n_rows > capacity:
            raise ValueError(
                f"n_rows={n_rows} with near_miss={near_miss!r} requires "
                f"grid_h>={n_rows + extra_row}, got {h}"
            )
    else:
        lo, hi = _BAND_ROWS[difficulty]
        hi = min(hi, capacity, 5)
        lo = min(lo, hi)
        n_rows = ctx.draw_int("n_rows", max(1, lo), max(1, hi))
    return h, w, n_rows, None


def _even_pair(width: int, rng, *, gap: int | None = None) -> tuple[int, int]:
    gaps = list(range(2, width, 2))
    if gap is None:
        gap = rng.choice(gaps)
    if gap not in gaps:
        raise ValueError(f"even pair gap {gap} is invalid for width {width}")
    c1 = rng.randint(0, width - 1 - gap)
    return c1, c1 + gap


def _odd_pair(width: int, rng) -> tuple[int, int]:
    gap = rng.choice(list(range(1, width, 2)))
    c1 = rng.randint(0, width - 1 - gap)
    return c1, c1 + gap


def _paint_firing_row(grid, row: int, width: int, rng, *, gap: int | None = None) -> None:
    c1, c2 = _even_pair(width, rng, gap=gap)
    grid[row][c1] = 8
    grid[row][c2] = 8


def _paint_near_miss(grid, row: int, width: int, kind: str, rng) -> None:
    if kind == "odd_pair":
        c1, c2 = _odd_pair(width, rng)
        grid[row][c1] = 8
        grid[row][c2] = 8
        return
    if kind == "triple_8s":
        for col in sorted(rng.sample(range(width), 3)):
            grid[row][col] = 8
        return
    if kind == "filled_mid":
        c1, c2 = _even_pair(width, rng)
        grid[row][c1] = 8
        grid[row][c2] = 8
        grid[row][(c1 + c2) // 2] = rng.choice(DISTRACTOR_COLORS)
        return
    raise ValueError(f"unsupported near_miss {kind!r}")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_request(overrides)
    band = _normalize_difficulty(difficulty)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    near_miss = _draw_near_miss(ctx, sample_index)
    h, w, n_rows, canonical_rows = _draw_axes(ctx, band, overrides, near_miss)
    grid = full_grid(h, w, 0)
    rng = ctx.draw_rng("layout")

    if canonical_rows is not None:
        for row, gap in canonical_rows:
            _paint_firing_row(grid, row, w, rng, gap=gap)
        return grid

    row_slots = rng.sample(range(h), n_rows + int(near_miss != "none"))
    firing_rows = sorted(row_slots[:n_rows])
    for row in firing_rows:
        _paint_firing_row(grid, row, w, rng)
    if near_miss != "none":
        _paint_near_miss(grid, row_slots[-1], w, near_miss, rng)
    return grid


def _classify_row(row: list[int]) -> tuple[str, int | None]:
    eights = [index for index, value in enumerate(row) if value == 8]
    nonzero = [index for index, value in enumerate(row) if value != 0]
    if not nonzero:
        return "blank", None
    if len(eights) == 2:
        c1, c2 = eights
        if (c1 + c2) % 2:
            if len(nonzero) == 2:
                return "odd_pair", c2 - c1
            return "invalid", None
        midpoint = (c1 + c2) // 2
        if row[midpoint] == 0 and len(nonzero) == 2:
            return "firing", c2 - c1
        if (
            row[midpoint] in DISTRACTOR_COLORS
            and len(nonzero) == 3
            and set(nonzero) == {c1, midpoint, c2}
        ):
            return "filled_mid", c2 - c1
        return "invalid", None
    if len(eights) == 3 and len(nonzero) == 3:
        return "triple_8s", None
    return "invalid", None


def analyze_grid(grid) -> tuple[list[str], dict[str, Any]]:
    errors: list[str] = []
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return ["grid must be a nonempty list of rows"], {}
    width = len(grid[0])
    if width == 0 or any(not isinstance(row, list) or len(row) != width for row in grid):
        return ["grid must be rectangular and nonempty"], {}
    height = len(grid)
    if not 4 <= height <= 10:
        errors.append(f"grid_h must be 4..10, found {height}")
    if not 7 <= width <= 14:
        errors.append(f"grid_w must be 7..14, found {width}")
    if any(
        not isinstance(value, int)
        or isinstance(value, bool)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        errors.append("grid cells must be integer ARC colors 0..9")
    if any(value == 2 for row in grid for value in row):
        errors.append("input must not contain answer color 2")

    row_kinds: list[str] = []
    firing_rows: list[tuple[int, int]] = []
    near_misses: list[str] = []
    for row_index, row in enumerate(grid):
        kind, gap = _classify_row(row)
        row_kinds.append(kind)
        if kind == "invalid":
            errors.append(f"row {row_index} is outside the teaching grammar")
        elif kind == "firing":
            firing_rows.append((row_index, int(gap)))
        elif kind != "blank":
            near_misses.append(kind)

    if not 1 <= len(firing_rows) <= 5:
        errors.append(f"firing-row count must be 1..5, found {len(firing_rows)}")
    if len(near_misses) > 1:
        errors.append(f"at most one near-miss row is allowed, found {len(near_misses)}")
    if len(set(near_misses)) != len(near_misses):
        errors.append("duplicate near-miss rows are not allowed")

    features = {
        "grid_h": height,
        "grid_w": width,
        "n_rows": len(firing_rows),
        "near_miss": near_misses[0] if near_misses else "none",
        "firing_rows": tuple(firing_rows),
        "row_kind_counts": dict(Counter(row_kinds)),
    }
    return errors, features


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the complete task-specific input grammar without mutation."""
    errors, _ = analyze_grid(grid)
    return errors


def observe_overrides(grid) -> dict[str, int | str]:
    """Recover every declared exact axis solely from the returned grid."""
    errors, features = analyze_grid(grid)
    if errors:
        raise ValueError("cannot observe overrides on invalid grid: " + "; ".join(errors))
    return {
        "grid_h": features["grid_h"],
        "grid_w": features["grid_w"],
        "n_rows": features["n_rows"],
        "near_miss": features["near_miss"],
    }


def canonical_profile_signature(grid):
    """Strict linked canonical signature, or ``None`` outside that manifold."""
    errors, features = analyze_grid(grid)
    if errors or features["near_miss"] != "none":
        return None
    signature = (
        features["grid_h"],
        features["grid_w"],
        features["firing_rows"],
    )
    return signature if signature in _CANONICAL_SIGNATURES else None
