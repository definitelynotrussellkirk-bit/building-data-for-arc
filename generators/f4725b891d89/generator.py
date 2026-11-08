"""Generator for f4725b891d89 — fill matching row/column intersections.

A color-5 rectangle frames two sparse headers: row labels live in the left
interior column and column labels live in the top interior row.  The selected
Racket authority fills an interior crossing exactly when its two labels have
the same color.  This module generates inputs only; ``rule_mirror`` is a tested
Python mirror used for review contracts and never replaces the Racket label
authority.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "f4725b891d89"
TASK_ID = GENERATOR_ID
RULE_HASH = "d0cb884b1dae"
VERSION = "3.0.0"
SUMMARY = (
    "A hollow color-5 frame contains a sparse top header and left header. "
    "Every interior crossing whose two header colors match is filled with that "
    "shared color; nonmatching crossings remain background."
)

EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0

INVARIANTS = [
    "grid is 8..18 by 8..18 with a complete color-5 outer frame",
    "top and left headers each contain 3..5 markers and at least one gap or boundary slot",
    "both headers use the same 2..3 nonzero non-frame colors",
    "each header repeats at least one color, exposing cross-product rather than one-to-one matching",
    "all non-header interior cells start as background 0",
]

# Every Cartesian combination is constructive: an 8x8 frame has exactly five
# legal slots in either header, enough for the largest advertised marker count.
AXES = {
    "frame_h": {
        "type": "int",
        "default": "weighted 8..18; every band retains an 8x8 canonical anchor",
        "valid": "8..18",
    },
    "frame_w": {
        "type": "int",
        "default": "weighted 8..18; every band retains an 8x8 canonical anchor",
        "valid": "8..18",
    },
    "n_top_markers": {
        "type": "int",
        "default": "profile-weighted 3..5",
        "valid": "3..5",
    },
    "n_left_markers": {
        "type": "int",
        "default": "profile-weighted 3..5",
        "valid": "3..5",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

SCHEDULE_PROFILES = (
    "canonical_anchor",
    "top_heavy",
    "left_heavy",
    "balanced_crossed",
)

# Profile-specific color sets cover both canonical palette cardinalities:
# two marker colors (four total ARC colors with 0 and 5) and three marker
# colors (five total).  If an exact marker-count override leaves only three
# slots, generation safely uses the first two colors so duplicate evidence is
# never sacrificed.
_PROFILE_PALETTES = {
    "canonical_anchor": (2, 7),
    "top_heavy": (3, 6, 8),
    "left_heavy": (2, 4, 6),
    "balanced_crossed": (1, 4, 9),
}

_PROFILE_COUNTS = {
    "canonical_anchor": (4, 3),
    "top_heavy": (5, 4),
    "left_heavy": (4, 5),
    "balanced_crossed": (4, 4),
}

_PROFILE_DIMENSIONS = {
    "easy": {
        "canonical_anchor": (8, 8),
        "top_heavy": (8, 9),
        "left_heavy": (9, 8),
        "balanced_crossed": (9, 9),
    },
    "medium": {
        "canonical_anchor": (8, 8),
        "top_heavy": (9, 10),
        "left_heavy": (10, 9),
        "balanced_crossed": (10, 10),
    },
    "hard": {
        "canonical_anchor": (8, 8),
        "top_heavy": (14, 18),
        "left_heavy": (18, 14),
        "balanced_crossed": (18, 18),
    },
}


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Cycle four teaching profiles; every four consecutive examples cover all."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def _validate_request(difficulty, overrides: dict[str, Any]) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    bounds = {
        "frame_h": (8, 18),
        "frame_w": (8, 18),
        "n_top_markers": (3, 5),
        "n_left_markers": (3, 5),
    }
    for name, value in overrides.items():
        if value is None:
            continue
        if type(value) is not int:
            raise TypeError(f"{name} must be an integer (not {type(value).__name__})")
        lo, hi = bounds[name]
        if not lo <= value <= hi:
            raise ValueError(f"{name}={value} outside [{lo}, {hi}]")


def _weighted_axis(ctx, name: str, lo: int, hi: int, preferred: int) -> int:
    """Draw over the full override domain while strongly favoring a profile anchor."""
    options = tuple(range(lo, hi + 1)) + (preferred,) * 256
    return int(ctx.draw_choice(name, options))


def _header_entries(grid) -> tuple[list[tuple[int, int]], list[tuple[int, int]]]:
    h, w = len(grid), len(grid[0])
    top = [
        (c, grid[1][c])
        for c in range(2, w - 1)
        if grid[1][c] not in (0, 5)
    ]
    left = [
        (r, grid[r][1])
        for r in range(2, h - 1)
        if grid[r][1] not in (0, 5)
    ]
    return top, left


def _color_sequence(colors: tuple[int, ...], count: int, *, profile: str, side: str) -> list[int]:
    """Use every selected color and force a duplicate in each 3..5-marker header."""
    if len(colors) == 2:
        a, b = colors
        start_with_a = {
            ("canonical_anchor", "top"): True,
            ("canonical_anchor", "left"): False,
            ("top_heavy", "top"): True,
            ("top_heavy", "left"): True,
            ("left_heavy", "top"): False,
            ("left_heavy", "left"): True,
            ("balanced_crossed", "top"): True,
            ("balanced_crossed", "left"): False,
        }[(profile, side)]
        first, second = (a, b) if start_with_a else (b, a)
        if profile in ("top_heavy", "left_heavy") and (
            (profile == "top_heavy" and side == "top")
            or (profile == "left_heavy" and side == "left")
        ):
            base = [first, first, second, first, second]
        else:
            base = [first, second, first, second, first]
        return base[:count]

    if len(colors) != 3 or count < 4:
        raise ValueError("three-color headers require at least four markers")
    a, b, c = colors
    patterns = {
        ("top_heavy", "top"): [a, a, b, c, a],
        ("top_heavy", "left"): [b, c, a, b, c],
        ("left_heavy", "top"): [c, a, b, c, a],
        ("left_heavy", "left"): [a, b, c, a, a],
        ("balanced_crossed", "top"): [a, b, c, a, b],
        ("balanced_crossed", "left"): [c, a, b, c, a],
    }
    return patterns[(profile, side)][:count]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_request(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    profile = schedule_profile(seed, sample_index, difficulty)
    band = difficulty if difficulty in ("easy", "medium", "hard") else "medium"
    preferred_h, preferred_w = _PROFILE_DIMENSIONS[band][profile]
    preferred_top, preferred_left = _PROFILE_COUNTS[profile]

    h = _weighted_axis(ctx, "frame_h", 8, 18, preferred_h)
    w = _weighted_axis(ctx, "frame_w", 8, 18, preferred_w)
    n_top = _weighted_axis(ctx, "n_top_markers", 3, 5, preferred_top)
    n_left = _weighted_axis(ctx, "n_left_markers", 3, 5, preferred_left)

    grid = full_grid(h, w, 0)
    for c in range(w):
        grid[0][c] = 5
        grid[h - 1][c] = 5
    for r in range(h):
        grid[r][0] = 5
        grid[r][w - 1] = 5

    top_positions = sorted(ctx.draw_rng("top_positions").sample(range(2, w - 1), n_top))
    left_positions = sorted(ctx.draw_rng("left_positions").sample(range(2, h - 1), n_left))
    palette = _PROFILE_PALETTES[profile]
    if len(palette) == 3 and (n_top < 4 or n_left < 4):
        palette = palette[:2]
    top_colors = _color_sequence(palette, n_top, profile=profile, side="top")
    left_colors = _color_sequence(palette, n_left, profile=profile, side="left")

    for col, color in zip(top_positions, top_colors, strict=True):
        grid[1][col] = color
    for row, color in zip(left_positions, left_colors, strict=True):
        grid[row][1] = color
    return grid


def observe_overrides(grid) -> dict[str, int]:
    """Recover every advertised exact control from returned pixels."""
    findings = self_check(grid)
    if findings:
        raise ValueError("cannot observe malformed grid: " + "; ".join(findings[:3]))
    top, left = _header_entries(grid)
    return {
        "frame_h": len(grid),
        "frame_w": len(grid[0]),
        "n_top_markers": len(top),
        "n_left_markers": len(left),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the complete input grammar, including canonical public examples."""
    del difficulty, meta
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty rectangular grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected nonempty rows"]
    w = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != w for row in grid):
        return ["ragged grid"]
    h = len(grid)
    errors: list[str] = []
    if not (8 <= h <= 18 and 8 <= w <= 18):
        errors.append(f"frame dimensions {h}x{w} outside 8..18")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        errors.append("cells must be integer ARC colors 0..9")
        return errors

    if any(grid[0][c] != 5 or grid[h - 1][c] != 5 for c in range(w)):
        errors.append("top and bottom borders must be color 5")
    if any(grid[r][0] != 5 or grid[r][w - 1] != 5 for r in range(h)):
        errors.append("left and right borders must be color 5")

    interior_bad = []
    for r in range(1, h - 1):
        for c in range(1, w - 1):
            header = (r == 1 and c >= 2) or (c == 1 and r >= 2)
            if not header and grid[r][c] != 0:
                interior_bad.append((r, c, grid[r][c]))
    if interior_bad:
        errors.append(f"non-header interior cells must be 0; first={interior_bad[0]}")

    top, left = _header_entries(grid)
    if not 3 <= len(top) <= 5:
        errors.append(f"top header must contain 3..5 markers, found {len(top)}")
    if not 3 <= len(left) <= 5:
        errors.append(f"left header must contain 3..5 markers, found {len(left)}")

    top_colors = [color for _position, color in top]
    left_colors = [color for _position, color in left]
    if any(color in (0, 5) for color in top_colors + left_colors):
        errors.append("header markers may not use background 0 or frame color 5")
    top_set, left_set = set(top_colors), set(left_colors)
    if top_set != left_set:
        errors.append(f"header color sets must match, found top={sorted(top_set)} left={sorted(left_set)}")
    if not 2 <= len(top_set) <= 3:
        errors.append(f"headers must use 2..3 shared colors, found {len(top_set)}")
    if top_colors and max(Counter(top_colors).values()) < 2:
        errors.append("top header must repeat at least one color")
    if left_colors and max(Counter(left_colors).values()) < 2:
        errors.append("left header must repeat at least one color")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """The strict sampler manifold; all public canonical inputs belong to it."""
    return self_check(grid)


def rule_mirror(grid) -> list[list[int]]:
    """Python mirror of the selected equality-cross-product authority."""
    out = deepcopy(grid)
    top, left = _header_entries(grid)
    for row, row_color in left:
        for col, col_color in top:
            if row_color == col_color:
                out[row][col] = row_color
    return out


# --- Explicit plausible wrong rules used by semantic and lesson gates. ---

def _all_crossings_row_color(grid):
    out = deepcopy(grid)
    top, left = _header_entries(grid)
    for row, row_color in left:
        for col, _col_color in top:
            out[row][col] = row_color
    return out


def _first_top_match_only(grid):
    out = deepcopy(grid)
    top, left = _header_entries(grid)
    for row, row_color in left:
        match = next((col for col, col_color in top if col_color == row_color), None)
        if match is not None:
            out[row][match] = row_color
    return out


def _first_left_match_only(grid):
    out = deepcopy(grid)
    top, left = _header_entries(grid)
    for col, col_color in top:
        match = next((row for row, row_color in left if row_color == col_color), None)
        if match is not None:
            out[match][col] = col_color
    return out


def _same_rank_only(grid):
    out = deepcopy(grid)
    top, left = _header_entries(grid)
    for (row, row_color), (col, col_color) in zip(left, top):
        if row_color == col_color:
            out[row][col] = row_color
    return out


def _has_nonmatching_crossing(grid) -> bool:
    top, left = _header_entries(grid)
    return any(row_color != col_color for _r, row_color in left for _c, col_color in top)


def _has_repeated_top(grid) -> bool:
    top, _left = _header_entries(grid)
    counts = Counter(color for _c, color in top)
    return bool(counts) and max(counts.values()) >= 2


def _has_repeated_left(grid) -> bool:
    _top, left = _header_entries(grid)
    counts = Counter(color for _r, color in left)
    return bool(counts) and max(counts.values()) >= 2


def _has_off_rank_match(grid) -> bool:
    top, left = _header_entries(grid)
    return any(i != j and row_color == col_color
               for i, (_r, row_color) in enumerate(left)
               for j, (_c, col_color) in enumerate(top))


SEMANTIC_RIVALS: dict[str, Callable] = {
    "fill_all_crossings": _all_crossings_row_color,
    "first_top_match_only": _first_top_match_only,
    "first_left_match_only": _first_left_match_only,
    "same_rank_only": _same_rank_only,
}
SEMANTIC_WITNESSES = {
    "nonmatching_crossing": _has_nonmatching_crossing,
    "repeated_top_color": _has_repeated_top,
    "repeated_left_color": _has_repeated_left,
    "off_rank_match": _has_off_rank_match,
}
WITNESS_RIVALS = {
    "nonmatching_crossing": ["fill_all_crossings"],
    "repeated_top_color": ["first_top_match_only"],
    "repeated_left_color": ["first_left_match_only"],
    "off_rank_match": ["same_rank_only"],
}
CANONICAL_SHORTCUTS: dict[str, Callable] = {}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query) -> list[str]:
    """Report competitors that fit every demonstration but change the query."""
    reasons: list[str] = []
    if not isinstance(demos, list) or len(demos) < EXAMPLES_NEEDED:
        reasons.append(f"expected at least {EXAMPLES_NEEDED} demonstrations")
        return reasons

    normalized_demos = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} is not a labeled pair")
            continue
        findings = strict_canonical_like(pair["input"])
        if findings:
            reasons.append(f"demo {index} is outside the strict manifold: {findings[0]}")
            continue
        truth = rule_mirror(pair["input"])
        if pair["output"] != truth:
            reasons.append(f"demo {index} label disagrees with the rule mirror")
            continue
        normalized_demos.append(pair)
    if reasons:
        return reasons

    if not isinstance(query, dict) or "input" not in query:
        return ["query is missing an input grid"]
    query_findings = strict_canonical_like(query["input"])
    if query_findings:
        return [f"query is outside the strict manifold: {query_findings[0]}"]
    query_truth = query.get("output", rule_mirror(query["input"]))
    if query_truth != rule_mirror(query["input"]):
        return ["query label disagrees with the rule mirror"]

    for name, rival in LESSON_COMPETITORS.items():
        try:
            fits_demos = all(rival(pair["input"]) == pair["output"] for pair in normalized_demos)
            changes_query = rival(query["input"]) != query_truth
        except Exception as exc:  # defensive diagnostics for future rival edits
            reasons.append(f"competitor {name} crashed: {exc!r}")
            continue
        if fits_demos and changes_query:
            reasons.append(f"competitor {name} fits every demo but changes the query")
    return reasons
