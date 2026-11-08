"""Constructive inputs for counting occupancy across three aligned panels.

The unchanged Racket authority maps each local 5x5 coordinate to 0, 2, 4, or
8 according to whether zero, one, two, or three panels are occupied there.
This sampler keeps the canonical connected-object grammar, exposes only exact
observable controls, and cycles through center and border placements so that a
plausible but wrong "central 3x3 only" rule is refuted inside every lesson.
"""
from __future__ import annotations

from itertools import permutations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "7017b91a367d"
TASK_ID = GENERATOR_ID
RULE_HASH = "aa994ed25e88"
VERSION = "3.0.0"
SUMMARY = (
    "Three 5x5 monochrome connected panels share a local coordinate system. "
    "Their canonical-derived overlap profile contains examples of occupancy "
    "counts one, two, and three; lessons move the motif onto the outer border "
    "to distinguish the full 5x5 count map from a central-only shortcut."
)
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

INVARIANTS = [
    "the input is 5x17 with zero separator columns 5 and 11",
    "each 5x5 panel contains one nonempty 4-connected monochrome object",
    "the three panel colors are distinct but do not affect the rule",
    "all panels share local 5x5 coordinates and realize occupancy counts 1, 2, and 3",
    "the output authority maps counts 0/1/2/3 to colors 0/2/4/8",
]

# Each name records (number of count-1 cells, count-2 cells, count-3 cells).
PROFILE_HISTOGRAMS = {
    "s4_d3_t2": (4, 3, 2),
    "s2_d5_t2": (2, 5, 2),
    "s2_d5_t1": (2, 5, 1),
    "s1_d6_t1": (1, 6, 1),
    "s2_d4_t2": (2, 4, 2),
}
PROFILE_NAMES = tuple(PROFILE_HISTOGRAMS)

# Exact, pixel-observable panel-color tuples. These retain canonical palettes
# without treating color as semantic.
_PALETTES = {
    "default": (4, 2, 7),
    "warm": (7, 3, 9),
    "cool": (2, 4, 3),
    "varied": (9, 1, 8),
}
PALETTE_KINDS = tuple(_PALETTES)
_PALETTE_TO_KIND = {value: key for key, value in _PALETTES.items()}

AXES = {
    "profile": {
        "type": "str",
        "default": "difficulty-weighted canonical occupancy profile",
        "valid": "s4_d3_t2|s2_d5_t2|s2_d5_t1|s1_d6_t1|s2_d4_t2",
    },
    "palette_kind": {
        "type": "str",
        "default": "uniform exact palette",
        "valid": "default|warm|cool|varied",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []

SCHEDULE_PROFILES = ("center", "top_left", "bottom_right")
_WINDOW_ORIGINS = {
    "center": (1, 1),
    "top_left": (0, 0),
    "bottom_right": (2, 2),
}

# A local cell stores a three-bit panel-occupancy mask. These five abstract
# motifs reproduce the canonical occupancy profiles; dihedral transforms and
# panel permutations create the sampler's variants without replaying full grids.
_PROFILE_PATTERNS = {
    "s4_d3_t2": (
        (6, 7, 2),
        (5, 3, 1),
        (4, 7, 4),
    ),
    "s2_d5_t2": (
        (7, 6, 6),
        (7, 1, 4),
        (5, 5, 5),
    ),
    "s2_d5_t1": (
        (3, 7, 3),
        (5, 6, 6),
        (0, 4, 2),
    ),
    "s1_d6_t1": (
        (4, 7, 5),
        (6, 3, 6),
        (5, 3, 0),
    ),
    "s2_d4_t2": (
        (3, 7, 3),
        (4, 5, 6),
        (0, 7, 2),
    ),
}
_PANEL_PERMUTATIONS = tuple(permutations(range(3)))


def schedule_profile(seed, sample_index, difficulty=None):
    """Cycle placement evidence; seed and band never hide a schedule branch."""
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def _rotate90(pattern):
    return tuple(tuple(row) for row in zip(*pattern[::-1]))


def _dihedral(pattern, index):
    result = tuple(tuple(row) for row in pattern)
    if index >= 4:
        result = tuple(tuple(reversed(row)) for row in result)
        index -= 4
    for _ in range(index):
        result = _rotate90(result)
    return result


def _permute_mask(mask, permutation):
    result = 0
    for new_panel, old_panel in enumerate(permutation):
        if mask & (1 << old_panel):
            result |= 1 << new_panel
    return result


def _permute_pattern(pattern, permutation):
    return tuple(
        tuple(_permute_mask(mask, permutation) for mask in row)
        for row in pattern
    )


def _pattern_variants(pattern):
    return {
        _permute_pattern(_dihedral(pattern, transform), permutation)
        for transform in range(8)
        for permutation in _PANEL_PERMUTATIONS
    }


_VARIANT_TO_PROFILE = {}
for _profile_name, _profile_pattern in _PROFILE_PATTERNS.items():
    for _variant in _pattern_variants(_profile_pattern):
        previous = _VARIANT_TO_PROFILE.setdefault(_variant, _profile_name)
        if previous != _profile_name:  # pragma: no cover - import-time invariant
            raise RuntimeError(f"profile variants collide: {previous} and {_profile_name}")


def _profile_choices(difficulty):
    base = list(PROFILE_NAMES)
    if difficulty == "easy":
        return base + ["s4_d3_t2", "s2_d4_t2"] * 3
    if difficulty == "medium":
        return base + ["s2_d5_t2", "s2_d4_t2"] * 3
    if difficulty == "hard":
        return base + ["s1_d6_t1", "s2_d5_t1"] * 3
    return base


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axes: {unknown}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = ctx.draw_choice("profile", _profile_choices(difficulty))
    palette_kind = ctx.draw_choice("palette_kind", PALETTE_KINDS)

    rng = ctx.draw_rng(f"layout:{difficulty or 'all'}")
    pattern = _dihedral(_PROFILE_PATTERNS[profile], rng.randrange(8))
    pattern = _permute_pattern(pattern, rng.choice(_PANEL_PERMUTATIONS))
    row0, col0 = _WINDOW_ORIGINS[schedule_profile(seed, sample_index, difficulty)]
    colors = _PALETTES[palette_kind]

    grid = full_grid(5, 17, 0)
    for rr, row in enumerate(pattern):
        for cc, mask in enumerate(row):
            for panel, color in enumerate(colors):
                if mask & (1 << panel):
                    grid[row0 + rr][6 * panel + col0 + cc] = color
    return grid


def _connected(cells):
    if not cells:
        return False
    seen = {next(iter(cells))}
    pending = list(seen)
    while pending:
        r, c = pending.pop()
        for point in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
            if point in cells and point not in seen:
                seen.add(point)
                pending.append(point)
    return seen == cells


def _occupancy_masks(grid):
    return tuple(
        tuple(
            sum((grid[r][c + 6 * panel] != 0) << panel for panel in range(3))
            for c in range(5)
        )
        for r in range(5)
    )


def _extract_pattern(grid):
    masks = _occupancy_masks(grid)
    occupied = [(r, c) for r in range(5) for c in range(5) if masks[r][c]]
    if not occupied:
        raise ValueError("no occupied local coordinate")
    rows, cols = zip(*occupied)
    r0, c0, r1, c1 = min(rows), min(cols), max(rows), max(cols)
    if (r1 - r0 + 1, c1 - c0 + 1) != (3, 3):
        raise ValueError("combined motif must have a 3x3 bounding box")
    if (r0, c0) not in _WINDOW_ORIGINS.values():
        raise ValueError("motif must occupy the center, top-left, or bottom-right 3x3 window")
    pattern = tuple(tuple(masks[r0 + r][c0 + c] for c in range(3)) for r in range(3))
    profile = _VARIANT_TO_PROFILE.get(pattern)
    if profile is None:
        raise ValueError("occupancy pattern is outside the declared canonical-derived profiles")
    return profile, (r0, c0), pattern


def self_check(grid, *, difficulty=None, meta=None):
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty rectangular grid"]
    if any(not isinstance(row, (list, tuple)) for row in grid):
        return ["expected row sequences"]
    if any(len(row) != 17 for row in grid) or len(grid) != 5:
        return ["expected exactly 5 rows and 17 columns"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be integer ARC colors 0..9 (booleans are not colors)"]

    errors = []
    for separator in (5, 11):
        if any(grid[r][separator] != 0 for r in range(5)):
            errors.append(f"separator column {separator} must be zero")

    panel_colors = []
    for panel in range(3):
        left = 6 * panel
        cells = {(r, c) for r in range(5) for c in range(5) if grid[r][left + c] != 0}
        colors = {grid[r][left + c] for r, c in cells}
        if not cells:
            errors.append(f"panel {panel} must be nonempty")
        elif len(colors) != 1:
            errors.append(f"panel {panel} must be monochrome")
        elif not _connected(cells):
            errors.append(f"panel {panel} must be 4-connected")
        if len(colors) == 1:
            panel_colors.append(next(iter(colors)))
    if len(panel_colors) == 3 and len(set(panel_colors)) != 3:
        errors.append("the three panel colors must be distinct")
    if errors:
        return errors

    try:
        _extract_pattern(grid)
    except ValueError as exc:
        errors.append(str(exc))
    return errors


def strict_canonical_like(grid):
    """The connected three-panel overlap manifold, not literal grid replay."""
    return self_check(grid)


def observe_overrides(grid):
    """Recover every advertised exact control from returned pixels."""
    reasons = self_check(grid)
    if reasons:
        raise ValueError("; ".join(reasons))
    profile, _, _ = _extract_pattern(grid)
    colors = []
    for panel in range(3):
        left = 6 * panel
        colors.append(next(grid[r][left + c] for r in range(5) for c in range(5) if grid[r][left + c]))
    palette = tuple(colors)
    if palette not in _PALETTE_TO_KIND:
        raise ValueError(f"panel palette {palette!r} is lawful but outside the exact advertised palettes")
    return {"profile": profile, "palette_kind": _PALETTE_TO_KIND[palette]}


def _count_map(grid, *, central_only=False):
    """Input-only helper for the declared wrong rival; Racket remains authority."""
    output = full_grid(5, 5, 0)
    colors = (0, 2, 4, 8)
    for r in range(5):
        for c in range(5):
            if central_only and not (1 <= r <= 3 and 1 <= c <= 3):
                continue
            count = sum(grid[r][c + 6 * panel] != 0 for panel in range(3))
            output[r][c] = colors[count]
    return output


def _central_3x3_only(grid):
    """WRONG rival: ignores all local coordinates on the outer 5x5 border."""
    return _count_map(grid, central_only=True)


def _has_border_occupancy(grid):
    return any(
        grid[r][c + 6 * panel] != 0
        for panel in range(3)
        for r in range(5)
        for c in range(5)
        if r in (0, 4) or c in (0, 4)
    )


def _has_all_count_levels(grid):
    masks = _occupancy_masks(grid)
    counts = {mask.bit_count() for row in masks for mask in row if mask}
    return {1, 2, 3} <= counts


SEMANTIC_WITNESSES = {
    "border_occupancy": _has_border_occupancy,
    "all_count_levels": _has_all_count_levels,
}
SEMANTIC_RIVALS = {"central_3x3_only": _central_3x3_only}
WITNESS_RIVALS = {"border_occupancy": ["central_3x3_only"]}
BRANCH_WITNESSES = ("all_count_levels",)
CANONICAL_SHORTCUTS = {"central_3x3_only": _central_3x3_only}
LESSON_COMPETITORS = {"central_3x3_only": _central_3x3_only}


def lesson_identifiable(demos, query):
    """Reject lessons whose labels leave the declared shortcut query-ambiguous."""
    reasons = []
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        return ["query must be a labeled pair"]
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demonstration {index} is not a labeled pair")
    if reasons:
        return reasons

    taught_colors = {value for demo in demos for row in demo["output"] for value in row}
    missing = {2, 4, 8} - taught_colors
    if missing:
        reasons.append(f"demonstrations do not teach output colors {sorted(missing)}")

    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(demo["input"]) == demo["output"] for demo in demos):
            if rival(query["input"]) != query["output"]:
                reasons.append(f"{name} fits every demonstration but changes the query")
    return reasons
