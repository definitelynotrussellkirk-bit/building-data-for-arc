"""Input sampler for the row-key stencil task.

The unchanged Racket authority recolors each cyan (8) cell outside column zero
with that row's nonzero first-column key. A cyan cell in a row whose key is zero
is deliberately preserved. This module samples inputs only; semantic rivals
below exist solely for review and lesson-identifiability checks.
"""
from __future__ import annotations

from itertools import combinations, product
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "a8a8969ab4f1"
TASK_ID = GENERATOR_ID
RULE_HASH = "1130750019d1"
VERSION = "3.0.0"

SUMMARY = (
    "A 6x8, 7x9, or 8x10 zero-background grid has exactly three keyed rows. "
    "Each keyed row begins with a nonzero, non-cyan color and contains one to "
    "three cyan (8) markers. The selected rule recolors only those cyan cells "
    "whose row has a nonzero key; scheduled cyan markers in zero-key rows are "
    "preserved and distinguish the rule from an erase-empty-row shortcut."
)

INVARIANTS = [
    "the grid has one of the three canonical shapes: 6x8, 7x9, or 8x10",
    "exactly three rows have a nonzero, non-cyan key in column zero",
    "every keyed row has one to three cyan markers outside column zero",
    "outside column zero, inputs contain only background 0 and cyan 8",
    "zero-key rows may contain cyan markers, which the authority preserves",
]

_SHAPES = {"6x8": (6, 8), "7x9": (7, 9), "8x10": (8, 10)}
_ROW_PATTERNS = ("alternating", "clustered", "scattered")
_KEY_PATTERNS = ("distinct", "mixed", "repeated")
_MARKER_PROFILES = ("one_each", "two_each", "three_each", "mixed")
_KEY_COLORS = (1, 2, 3, 4, 5, 6, 7, 9)

AXES = {
    "shape": {
        "type": "str",
        "default": "difficulty-weighted canonical shape",
        "valid": "6x8|7x9|8x10",
    },
    "row_pattern": {
        "type": "str",
        "default": "difficulty-weighted",
        "valid": "alternating|clustered|scattered",
    },
    "key_color_pattern": {
        "type": "str",
        "default": "mostly distinct; mixed and repeated retained",
        "valid": "distinct|mixed|repeated",
    },
    "marker_profile": {
        "type": "str",
        "default": "difficulty-weighted",
        "valid": "one_each|two_each|three_each|mixed",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.15
SCHEDULE_PROFILES = ("canonical_anchor", "unkeyed_marker_witness")


def schedule_profile(seed, sample_index, difficulty=None):
    """Expose the deterministic semantic branch, independent of random draws."""
    del seed, difficulty
    return "canonical_anchor" if sample_index % 3 == 0 else "unkeyed_marker_witness"


def _weighted_options(name: str, difficulty: Any) -> tuple[str, ...]:
    """Return full-support weights; exact overrides still use the full domain."""
    if name == "shape":
        if difficulty == "easy":
            return ("6x8",) * 6 + ("7x9",) * 3 + ("8x10",)
        if difficulty == "hard":
            return ("6x8",) + ("7x9",) * 3 + ("8x10",) * 6
        if difficulty == "medium":
            return ("6x8",) * 2 + ("7x9",) * 6 + ("8x10",) * 2
        return tuple(_SHAPES) * 3
    if name == "row_pattern":
        if difficulty == "easy":
            return ("alternating",) * 5 + ("clustered",) * 3 + ("scattered",) * 2
        if difficulty == "hard":
            return ("alternating",) * 2 + ("clustered",) * 3 + ("scattered",) * 5
        return _ROW_PATTERNS * 3
    if name == "key_color_pattern":
        return ("distinct",) * 8 + ("mixed",) + ("repeated",)
    if name == "marker_profile":
        if difficulty == "easy":
            return ("one_each",) * 5 + ("two_each",) * 3 + ("three_each",) + ("mixed",)
        if difficulty == "hard":
            return ("one_each",) + ("two_each",) * 2 + ("three_each",) * 4 + ("mixed",) * 3
        return _MARKER_PROFILES * 3
    raise KeyError(name)


def _draw_axis(ctx, name: str, domain: tuple[str, ...], difficulty: Any) -> str:
    # Explicit overrides are checked against the literal advertised domain.
    # Defaults use duplicate-weighted sequences while retaining full support.
    options = (
        domain
        if name in ctx.overrides and ctx.overrides[name] is not None
        else _weighted_options(name, difficulty)
    )
    return ctx.draw_choice(name, options)


def _classify_rows(rows: tuple[int, int, int] | list[int]) -> str:
    a, b, c = rows
    if b - a == 1 and c - b == 1:
        return "clustered"
    if b - a == 2 and c - b == 2:
        return "alternating"
    return "scattered"


def _active_rows(ctx, h: int, pattern: str) -> tuple[int, int, int]:
    candidates = [rows for rows in combinations(range(h), 3) if _classify_rows(rows) == pattern]
    if not candidates:
        raise RuntimeError(f"no {pattern!r} three-row placement for height {h}")
    return ctx.draw_rng("active_rows").choice(candidates)


def _key_sequence(ctx, pattern: str) -> tuple[int, int, int]:
    rng = ctx.draw_rng("key_colors")
    if pattern == "distinct":
        return tuple(rng.sample(_KEY_COLORS, 3))
    if pattern == "repeated":
        color = rng.choice(_KEY_COLORS)
        return (color, color, color)
    first, second = rng.sample(_KEY_COLORS, 2)
    values = [first, first, second]
    rng.shuffle(values)
    return tuple(values)


def _marker_counts(ctx, profile: str) -> tuple[int, int, int]:
    if profile == "one_each":
        return (1, 1, 1)
    if profile == "two_each":
        return (2, 2, 2)
    if profile == "three_each":
        return (3, 3, 3)
    choices = [counts for counts in product((1, 2, 3), repeat=3) if len(set(counts)) > 1]
    return ctx.draw_rng("mixed_marker_counts").choice(choices)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    shape = _draw_axis(ctx, "shape", tuple(_SHAPES), difficulty)
    row_pattern = _draw_axis(ctx, "row_pattern", _ROW_PATTERNS, difficulty)
    key_pattern = _draw_axis(ctx, "key_color_pattern", _KEY_PATTERNS, difficulty)
    marker_profile = _draw_axis(ctx, "marker_profile", _MARKER_PROFILES, difficulty)

    h, w = _SHAPES[shape]
    rows = _active_rows(ctx, h, row_pattern)
    keys = _key_sequence(ctx, key_pattern)
    counts = _marker_counts(ctx, marker_profile)
    grid = full_grid(h, w, 0)

    for row, key, count in zip(rows, keys, counts):
        grid[row][0] = key
        columns = ctx.draw_rng(f"keyed_markers_row_{row}").sample(range(1, w), count)
        for column in columns:
            grid[row][column] = 8

    # Two of every three consecutive samples exercise the authority's otherwise
    # hidden key=0 branch. This cadence guarantees every four-pair lesson keeps
    # a counterexample after any single query rotation.
    if schedule_profile(seed, sample_index, difficulty) == "unkeyed_marker_witness":
        blank_rows = [row for row in range(h) if row not in rows]
        candidates = [(row, column) for row in blank_rows for column in range(1, w)]
        witness_count = 1 if sample_index % 3 == 1 else 2
        for row, column in ctx.draw_rng("unkeyed_markers").sample(candidates, witness_count):
            grid[row][column] = 8

    return grid


def _basic_grid_errors(grid) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty rectangular grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected a nonempty rectangular grid"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["expected a rectangular grid"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be integer ARC colors in 0..9 (bool is not accepted)"]
    shape = f"{len(grid)}x{width}"
    if shape not in _SHAPES:
        return [f"shape {shape} is outside the canonical 6x8|7x9|8x10 profiles"]
    return []


def _facts(grid) -> dict[str, Any]:
    errors = _basic_grid_errors(grid)
    if errors:
        raise ValueError("; ".join(errors))
    h, w = len(grid), len(grid[0])
    active_rows = tuple(row for row in range(h) if grid[row][0] != 0)
    blank_rows = tuple(row for row in range(h) if grid[row][0] == 0)
    key_colors = tuple(grid[row][0] for row in active_rows)
    marker_counts = tuple(sum(value == 8 for value in grid[row][1:]) for row in active_rows)
    unkeyed_markers = tuple(
        (row, column)
        for row in blank_rows
        for column in range(1, w)
        if grid[row][column] == 8
    )
    return {
        "shape": f"{h}x{w}",
        "active_rows": active_rows,
        "blank_rows": blank_rows,
        "key_colors": key_colors,
        "marker_counts": marker_counts,
        "unkeyed_markers": unkeyed_markers,
    }


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty, meta
    errors = _basic_grid_errors(grid)
    if errors:
        return errors
    w = len(grid[0])
    active_rows: list[int] = []
    for row_index, row in enumerate(grid):
        key = row[0]
        if key == 8:
            errors.append(f"row {row_index} has cyan 8 in the key column")
        elif key not in (0,) + _KEY_COLORS:
            errors.append(f"row {row_index} key must be 0 or one of {_KEY_COLORS}, saw {key}")
        elif key != 0:
            active_rows.append(row_index)

        bad = [
            (column, value)
            for column, value in enumerate(row[1:], start=1)
            if value not in (0, 8)
        ]
        if bad:
            errors.append(
                f"row {row_index} has non-background/non-cyan cells outside column zero: {bad[:3]}"
            )

    if len(active_rows) != 3:
        errors.append(f"expected exactly three keyed rows, found {len(active_rows)}")
    for row_index in active_rows:
        marker_count = sum(value == 8 for value in grid[row_index][1:w])
        if not 1 <= marker_count <= 3:
            errors.append(
                f"keyed row {row_index} must contain one to three cyan markers, found {marker_count}"
            )
    return errors


def observe_overrides(grid):
    """Recover every declared exact axis from returned pixels alone."""
    errors = self_check(grid)
    if errors:
        raise ValueError("cannot observe invalid grid: " + "; ".join(errors))
    facts = _facts(grid)
    rows = facts["active_rows"]
    keys = facts["key_colors"]
    counts = facts["marker_counts"]
    if len(set(keys)) == 3:
        key_pattern = "distinct"
    elif len(set(keys)) == 1:
        key_pattern = "repeated"
    else:
        key_pattern = "mixed"
    if counts == (1, 1, 1):
        marker_profile = "one_each"
    elif counts == (2, 2, 2):
        marker_profile = "two_each"
    elif counts == (3, 3, 3):
        marker_profile = "three_each"
    else:
        marker_profile = "mixed"
    return {
        "shape": facts["shape"],
        "row_pattern": _classify_rows(rows),
        "key_color_pattern": key_pattern,
        "marker_profile": marker_profile,
    }


def strict_canonical_like(grid):
    """Canonical manifold: lawful grid, three distinct keys, no zero-key marker."""
    errors = self_check(grid)
    if errors:
        return errors
    facts = _facts(grid)
    reasons: list[str] = []
    if len(set(facts["key_colors"])) != 3:
        reasons.append("canonical examples use three distinct row-key colors")
    if facts["unkeyed_markers"]:
        reasons.append("canonical examples contain no cyan markers in zero-key rows")
    return reasons


def _authority_equivalent_output(grid):
    """Local helper for semantic hooks; the Racket program remains authority."""
    out = [list(row) for row in grid]
    for row_index, row in enumerate(grid):
        key = row[0]
        if key == 0:
            continue
        for column in range(1, len(row)):
            if row[column] == 8:
                out[row_index][column] = key
    return out


def _erase_unkeyed_markers(grid):
    """RIVAL: correctly recolors keyed rows but erases cyan in zero-key rows."""
    out = _authority_equivalent_output(grid)
    for row_index, row in enumerate(grid):
        if row[0] == 0:
            for column in range(1, len(row)):
                if row[column] == 8:
                    out[row_index][column] = 0
    return out


def _has_unkeyed_marker(grid) -> bool:
    try:
        return bool(_facts(grid)["unkeyed_markers"])
    except (TypeError, ValueError, IndexError):
        return False


def lesson_identifiable(demos, query):
    """Reject only if the erase-empty-row rival fits demos and changes query."""
    try:
        rival_fits = all(
            _erase_unkeyed_markers(pair["input"]) == pair["output"] for pair in demos
        )
        if rival_fits and _erase_unkeyed_markers(query["input"]) != query["output"]:
            return [
                "demonstrations do not show that cyan markers in zero-key rows are preserved"
            ]
        return []
    except (KeyError, TypeError, ValueError, IndexError) as exc:
        return [f"malformed labeled lesson: {exc}"]


SEMANTIC_WITNESSES = {"unkeyed_marker_preservation": _has_unkeyed_marker}
SEMANTIC_RIVALS = {"erase_unkeyed_markers": _erase_unkeyed_markers}
WITNESS_RIVALS = {"unkeyed_marker_preservation": ["erase_unkeyed_markers"]}
CANONICAL_SHORTCUTS = {"erase_unkeyed_markers": _erase_unkeyed_markers}
LESSON_COMPETITORS = {"erase_unkeyed_markers": _erase_unkeyed_markers}
