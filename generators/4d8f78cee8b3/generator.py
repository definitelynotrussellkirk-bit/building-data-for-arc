"""Generator for ``keep_only_colors_that_appear_once_in_a_row``.

The input is a sparse zero-background grid.  The authoritative rule is local
to each row: retain every nonzero cell whose color occurs exactly once in that
row, and erase every cell whose color repeats in that row.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
from typing import Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "4d8f78cee8b3"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "533915230c7f"
EXAMPLES_NEEDED = 3

SUMMARY = (
    "Sparse zero-background grids use seven nonzero colors across 3-4 active "
    "rows.  For each row independently, keep every cell whose color appears "
    "exactly once in that row and erase every cell whose color appears two or "
    "three times.  The curriculum includes singleton-only rows, rows with "
    "multiple singleton colors, repeated pairs and triples, and colors that "
    "change role between rows so global-frequency and one-answer-per-row "
    "shortcuts fail."
)

INVARIANTS = [
    "background is 0 and the grid uses exactly seven nonzero colors",
    "3-4 active rows; every active row has at least one singleton color",
    "at least one color repeats two or three times in a row, so the rule is non-identity",
    "sample_index modulo three cycles canonical, cross-row-role, and dense profiles",
    "the output rule is row-local; a color may be singleton in one row and repeated in another",
]

GRID_PROFILES = ("canonical_6x9", "canonical_5x10", "canonical_7x8")
PALETTE_KINDS = ("low", "high", "split")
SCENE_PROFILES = ("canonical", "cross_row", "dense")

AXES = {
    "grid_profile": {
        "type": "str",
        "default": "rng",
        "valid": "|".join(GRID_PROFILES),
    },
    "palette_kind": {
        "type": "str",
        "default": "rng",
        "valid": "|".join(PALETTE_KINDS),
    },
    "scene_profile": {
        "type": "str",
        "default": "sample_index cycle",
        "valid": "|".join(SCENE_PROFILES),
    },
}

_GRID_DIMS = {
    "canonical_6x9": (6, 9),
    "canonical_5x10": (5, 10),
    "canonical_7x8": (7, 8),
}
_PALETTES = {
    "low": (1, 2, 3, 4, 5, 6, 7),
    "high": (3, 4, 5, 6, 7, 8, 9),
    "split": (1, 2, 3, 5, 7, 8, 9),
}
_PROFILE_SIGNATURES = {
    "canonical": ((1,), (1, 1), (1, 2), (1, 3)),
    "cross_row": ((1, 1), (1, 1, 1), (1, 2), (1, 2)),
    "dense": ((1,), (1, 1, 2), (1, 1, 3)),
}
_CANONICAL_PROFILES = {(6, 9, 8), (5, 10, 8), (7, 8, 8)}


def schedule_profile(seed, sample_index, difficulty=None):
    """Every band has a complete three-sample cycle, with a distinct phase."""
    del seed
    band_offset = {"easy": 0, "medium": 1, "hard": 2}.get(difficulty, 0)
    return SCENE_PROFILES[(sample_index + band_offset) % len(SCENE_PROFILES)]


SCHEDULE_PROFILES = SCENE_PROFILES


def _profile_rows(profile: str, colors: list[int]) -> list[list[int]]:
    """Return ordered row token sequences before sparse column placement."""
    a, b, c, d, e, f, g = colors
    if profile == "canonical":
        # Pair+singleton, triple+singleton, two singletons, singleton-only.
        return [[a, b, a], [c, c, d, c], [e, f], [g]]
    if profile == "cross_row":
        # a and b each reverse role across rows, killing global-count rules.
        return [[a, b, a], [b, b, c], [a, d], [e, f, g]]
    if profile == "dense":
        # Multiple singleton answers share rows with both pair and triple noise.
        return [[a, b, a, c, a], [d, e, f, d], [g]]
    raise ValueError(f"unknown scene_profile {profile!r}")


def _place_row(grid: list[list[int]], row_index: int, tokens: list[int], rng) -> None:
    width = len(grid[0])
    columns = sorted(rng.sample(range(width), len(tokens)))
    # Reverse half the rows to vary left/right placement while preserving the
    # decisive middle-singleton pattern in the first profile row.
    if rng.randrange(2):
        tokens = list(reversed(tokens))
    for column, color in zip(columns, tokens):
        grid[row_index][column] = color


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    grid_profile = ctx.draw_choice("grid_profile", GRID_PROFILES)
    palette_kind = ctx.draw_choice("palette_kind", PALETTE_KINDS)
    if "scene_profile" in overrides:
        scene_profile = ctx.draw_choice("scene_profile", SCENE_PROFILES)
    else:
        scheduled = schedule_profile(seed, sample_index, difficulty)
        scene_profile = ctx.draw_choice("scene_profile", (scheduled,))

    height, width = _GRID_DIMS[grid_profile]
    rng = ctx.draw_rng("layout")
    colors = list(_PALETTES[palette_kind])
    rng.shuffle(colors)
    row_tokens = _profile_rows(scene_profile, colors)
    active_rows = sorted(rng.sample(range(height), len(row_tokens)))

    grid = full_grid(height, width, 0)
    for row_index, tokens in zip(active_rows, row_tokens):
        _place_row(grid, row_index, tokens, rng)
    return grid


def _row_counts(row: list[int]) -> Counter:
    return Counter(value for value in row if value != 0)


def _scene_signature(grid: list[list[int]]) -> tuple[tuple[int, ...], ...]:
    signatures = []
    for row in grid:
        counts = _row_counts(row)
        if counts:
            signatures.append(tuple(sorted(counts.values())))
    return tuple(sorted(signatures))


def observe_overrides(grid) -> dict[str, str]:
    """Recover every declared exact axis from the returned grid."""
    dims = (len(grid), len(grid[0]) if grid else 0)
    grid_profile = next(
        (name for name, value in _GRID_DIMS.items() if value == dims),
        "unclassified",
    )
    colors = frozenset(value for row in grid for value in row if value != 0)
    palette_kind = next(
        (name for name, value in _PALETTES.items() if frozenset(value) == colors),
        "unclassified",
    )
    signature = _scene_signature(grid)
    scene_profile = next(
        (name for name, value in _PROFILE_SIGNATURES.items() if value == signature),
        "unclassified",
    )
    return {
        "grid_profile": grid_profile,
        "palette_kind": palette_kind,
        "scene_profile": scene_profile,
    }


def _solve_grid(grid: list[list[int]]) -> list[list[int]]:
    out = full_grid(len(grid), len(grid[0]) if grid else 0, 0)
    for r, row in enumerate(grid):
        counts = _row_counts(row)
        for c, value in enumerate(row):
            if value != 0 and counts[value] == 1:
                out[r][c] = value
    return out


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Testing mirror only; canonical Racket remains the output authority."""
    return _solve_grid(grid)


def _global_unique_rival(grid):
    counts = Counter(value for row in grid for value in row if value != 0)
    return [
        [value if value != 0 and counts[value] == 1 else 0 for value in row]
        for row in grid
    ]


def _one_singleton_per_row_rival(grid):
    out = full_grid(len(grid), len(grid[0]), 0)
    for r, row in enumerate(grid):
        counts = _row_counts(row)
        candidates = [c for c, value in enumerate(row) if value and counts[value] == 1]
        if candidates:
            c = candidates[0]
            out[r][c] = row[c]
    return out


def _keep_rightmost_nonzero_rival(grid):
    out = full_grid(len(grid), len(grid[0]), 0)
    for r, row in enumerate(grid):
        candidates = [c for c, value in enumerate(row) if value != 0]
        if candidates:
            c = candidates[-1]
            out[r][c] = row[c]
    return out


def _erase_pairs_only_rival(grid):
    out = deepcopy(grid)
    for r, row in enumerate(grid):
        counts = _row_counts(row)
        for c, value in enumerate(row):
            if value != 0 and counts[value] == 2:
                out[r][c] = 0
    return out


def _lowest_singleton_only_rival(grid):
    out = full_grid(len(grid), len(grid[0]), 0)
    for r, row in enumerate(grid):
        counts = _row_counts(row)
        singleton_colors = [color for color, count in counts.items() if count == 1]
        if singleton_colors:
            chosen = min(singleton_colors)
            for c, value in enumerate(row):
                if value == chosen:
                    out[r][c] = value
    return out


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "keep globally unique colors": _global_unique_rival,
    "keep only one singleton per row": _one_singleton_per_row_rival,
    "keep the rightmost nonzero cell per row": _keep_rightmost_nonzero_rival,
    "erase repeated pairs but retain triples": _erase_pairs_only_rival,
    "keep only the lowest singleton color per row": _lowest_singleton_only_rival,
}
LESSON_COMPETITORS = SEMANTIC_RIVALS
CANONICAL_SHORTCUTS = SEMANTIC_RIVALS


def _has_pair(grid) -> bool:
    return any(2 in _row_counts(row).values() for row in grid)


def _has_triple(grid) -> bool:
    return any(3 in _row_counts(row).values() for row in grid)


def _has_singleton_only_row(grid) -> bool:
    return any(counts and all(count == 1 for count in counts.values())
               for counts in map(_row_counts, grid))


def _has_multi_singleton_row(grid) -> bool:
    return any(sum(count == 1 for count in _row_counts(row).values()) >= 2
               for row in grid)


def _has_cross_row_role_reversal(grid) -> bool:
    roles: dict[int, set[str]] = {}
    for row in grid:
        for color, count in _row_counts(row).items():
            roles.setdefault(color, set()).add("singleton" if count == 1 else "repeated")
    return any(value == {"singleton", "repeated"} for value in roles.values())


def _rightmost_shortcut_fails(grid) -> bool:
    return _solve_grid(grid) != _keep_rightmost_nonzero_rival(grid)


SEMANTIC_WITNESSES = {
    "repeated_pair": _has_pair,
    "repeated_triple": _has_triple,
    "singleton_only_row": _has_singleton_only_row,
    "multiple_singletons_same_row": _has_multi_singleton_row,
    "cross_row_role_reversal": _has_cross_row_role_reversal,
    "rightmost_position_rebuttal": _rightmost_shortcut_fails,
}
WITNESS_RIVALS = {
    "repeated_pair": ["keep the rightmost nonzero cell per row"],
    "repeated_triple": ["erase repeated pairs but retain triples"],
    "singleton_only_row": ["keep the rightmost nonzero cell per row"],
    "multiple_singletons_same_row": [
        "keep only one singleton per row",
        "keep only the lowest singleton color per row",
    ],
    "cross_row_role_reversal": ["keep globally unique colors"],
    "rightmost_position_rebuttal": ["keep the rightmost nonzero cell per row"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject a lesson when a named rival survives demos but changes query."""
    if not isinstance(demos, list) or not demos:
        return ["at least one demonstration is required"]
    reasons: list[str] = []
    for index, pair in enumerate([*demos, query]):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"pair {index} is missing input/output")
        elif pair["output"] != _solve_grid(pair["input"]):
            reasons.append(f"pair {index} output disagrees with row-local singleton rule")
    if reasons:
        return reasons
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            if rival(query["input"]) != query["output"]:
                reasons.append(f"demonstrations do not refute rival: {name}")
    return reasons


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Structural checker for canonical inputs and the trainable grammar."""
    del difficulty, meta
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        return ["grid must be a non-empty list of non-empty rows"]
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        return ["grid must be rectangular"]

    errors: list[str] = []
    height = len(grid)
    if not (5 <= height <= 7 and 8 <= width <= 10):
        errors.append(f"dimensions {height}x{width} outside canonical 5..7 by 8..10 envelope")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        errors.append("grid values must be integer ARC colors 0..9")
        return errors

    colors = {value for row in grid for value in row if value != 0}
    if len(colors) != 7:
        errors.append(f"expected exactly seven nonzero colors, got {len(colors)}")

    active_rows = 0
    repeated_rows = 0
    singleton_cells = 0
    for r, row in enumerate(grid):
        counts = _row_counts(row)
        if not counts:
            continue
        active_rows += 1
        multiplicities = list(counts.values())
        if any(count > 3 for count in multiplicities):
            errors.append(f"row {r} has a color occurring more than three times")
        singletons = sum(count == 1 for count in multiplicities)
        if singletons == 0:
            errors.append(f"row {r} has no singleton color and would hide the keep branch")
        singleton_cells += singletons
        if any(count >= 2 for count in multiplicities):
            repeated_rows += 1
        if not 1 <= sum(multiplicities) <= 5:
            errors.append(f"row {r} has {sum(multiplicities)} nonzero cells outside 1..5")

    if not 3 <= active_rows <= 4:
        errors.append(f"expected 3..4 active rows, got {active_rows}")
    if repeated_rows == 0:
        errors.append("at least one row must contain a repeated color")
    if singleton_cells < 3:
        errors.append(f"expected at least three singleton answer cells, got {singleton_cells}")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Exact canonical (height, width, palette-size) profile plus grammar."""
    errors = self_check(grid)
    if errors:
        return errors
    profile = (len(grid), len(grid[0]), len({value for row in grid for value in row}))
    if profile not in _CANONICAL_PROFILES:
        return [f"profile {profile} is not canonical"]
    return []


MIN_STRICT_FRAC = 1.0
