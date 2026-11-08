"""Generator for ARC task 26872d42d87a — fill single horizontal gaps.

The selected Racket rule changes a black cell to magenta only when its immediate
left and right neighbours are magenta.  This sampler deliberately includes two
near-misses in every ordinary input:

* a wider horizontal span (``6,0,0,6`` or ``6,0,0,0,6``), which must stay open;
* a vertical ``6,0,6`` pattern, which must also stay open.

Those branches distinguish the authority from two simple rules that fit every
canonical pair: filling an entire row span and applying the local rule vertically
as well as horizontally.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "26872d42d87a"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "bc262329ef0d"
SUMMARY = (
    "A 0-background grid contains three dotted horizontal color-6 segments, "
    "one wider same-row near-miss, one vertical near-miss, and one or two "
    "border color-5 decorations. Fill only a 0 whose immediate horizontal "
    "neighbours are both 6; preserve wider gaps, vertical patterns, and all "
    "decorations."
)
INVARIANTS = [
    "three rows contain at least one horizontal 6,0,6 trigger",
    "one wider horizontal 6...6 span remains unchanged",
    "one vertical 6,0,6 near-miss remains unchanged",
    "one or two color-5 decorations lie on the border",
]

SCENE_PROFILES = (
    "h8_w10",
    "h9_w11",
    "h10_w12",
    "h9_w10",
    "h10_w11",
)
PROFILE_DIMENSIONS = {
    "h8_w10": (8, 10),
    "h9_w11": (9, 11),
    "h10_w12": (10, 12),
    "h9_w10": (9, 10),
    "h10_w11": (10, 11),
}
_PROFILE_BY_DIMENSIONS = {dims: profile for profile, dims in PROFILE_DIMENSIONS.items()}
_PROFILE_DECORATIONS = {
    "h8_w10": 2,
    "h9_w11": 1,
    "h10_w12": 2,
    "h9_w10": 1,
    "h10_w11": 1,
}

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
AXES = {
    "scene_profile": {
        "type": "str",
        "default": "deterministic cycle over all five canonical size/palette profiles",
        "valid": "|".join(SCENE_PROFILES),
    }
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

EXAMPLES_NEEDED = 3
SCHEDULE_PROFILES = SCENE_PROFILES
MIN_STRICT_FRAC = 1.0


def _band(difficulty: str | None) -> str:
    if difficulty is None:
        return "medium"
    if difficulty not in ("easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    return difficulty


def schedule_profile(seed: int, sample_index: int, difficulty: str | None = None) -> str:
    """Cycle profiles independently of Python hash randomization."""
    _band(difficulty)
    return SCENE_PROFILES[sample_index % len(SCENE_PROFILES)]


def _trigger_lengths(band: str, width: int, rng) -> list[int]:
    # All lengths are odd so alternating placements have one or more true gaps.
    pools = {
        "easy": (3, 3, 5),
        "medium": (3, 5, 5),
        "hard": (3, 5, 7),
    }
    lengths = [min(length, 7 if width >= 9 else 5) for length in pools[band]]
    rng.shuffle(lengths)
    return lengths


def _border_cells(height: int, width: int) -> list[tuple[int, int]]:
    cells = [(0, c) for c in range(width)]
    cells.extend((height - 1, c) for c in range(width))
    cells.extend((r, 0) for r in range(1, height - 1))
    cells.extend((r, width - 1) for r in range(1, height - 1))
    return cells


def _build_scene(profile: str, band: str, rng) -> list[list[int]]:
    height, width = PROFILE_DIMENSIONS[profile]
    grid = full_grid(height, width, 0)

    # Reserve two interior rows around a vertical near-miss, leaving at least
    # four other interior rows even in the smallest 8x10 profile.
    vertical_at_top = bool(rng.randrange(2))
    if vertical_at_top:
        endpoint_rows = (0, 2)
        middle_row = 1
        reserved_rows = {1, 2}
    else:
        endpoint_rows = (height - 3, height - 1)
        middle_row = height - 2
        reserved_rows = {height - 3, height - 2}
    vertical_col = rng.choice((0, width - 1))
    for row in endpoint_rows:
        grid[row][vertical_col] = 6

    available_rows = [row for row in range(1, height - 1) if row not in reserved_rows]
    chosen_rows = rng.sample(available_rows, 4)
    wide_row = chosen_rows[0]
    trigger_rows = chosen_rows[1:]

    # A two- or three-cell interior gap distinguishes the selected local rule
    # from "fill everything between the leftmost and rightmost 6".
    separation = rng.choice((3, 4))
    wide_start = rng.randint(1, width - separation - 2)
    grid[wide_row][wide_start] = 6
    grid[wide_row][wide_start + separation] = 6

    for row, length in zip(trigger_rows, _trigger_lengths(band, width, rng)):
        start = rng.randint(1, width - length - 1)
        for offset in range(0, length, 2):
            grid[row][start + offset] = 6

    # Keep the vertical gap cell black so the orientation witness survives.
    excluded = {(middle_row, vertical_col)}
    candidates = [
        cell
        for cell in _border_cells(height, width)
        if grid[cell[0]][cell[1]] == 0 and cell not in excluded
    ]
    for row, col in rng.sample(candidates, _PROFILE_DECORATIONS[profile]):
        grid[row][col] = 5
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axis/axes: {sorted(unknown)}")
    requested = overrides.get("scene_profile")
    if requested is not None and type(requested) is not str:
        raise TypeError("scene_profile override must be a string")
    if requested is not None and requested not in SCENE_PROFILES:
        raise ValueError(
            f"scene_profile must be one of {SCENE_PROFILES}, got {requested!r}"
        )
    band = _band(difficulty)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    scheduled = requested or schedule_profile(seed, sample_index, band)
    profile = ctx.draw_choice("scene_profile", [scheduled])
    return _build_scene(profile, band, ctx.draw_rng("layout"))


def _basic_errors(grid) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty rectangular grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected nonempty rows"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["cells must be integer ARC colors 0..9"]
    return []


def _trigger_positions(grid) -> list[tuple[int, int]]:
    height = len(grid)
    width = len(grid[0])
    return [
        (row, col)
        for row in range(height)
        for col in range(1, width - 1)
        if grid[row][col] == 0
        and grid[row][col - 1] == 6
        and grid[row][col + 1] == 6
    ]


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errors = _basic_errors(grid)
    if errors:
        return errors
    height, width = len(grid), len(grid[0])
    profile = _PROFILE_BY_DIMENSIONS.get((height, width))
    if profile is None:
        errors.append(
            f"dimensions {(height, width)} are outside the five canonical profiles"
        )
    colors = {value for row in grid for value in row}
    if colors != {0, 5, 6}:
        errors.append(f"expected exactly colors [0, 5, 6], got {sorted(colors)}")
    fives = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == 5
    ]
    if not 1 <= len(fives) <= 2:
        errors.append(f"expected one or two color-5 decorations, found {len(fives)}")
    elif any(row not in (0, height - 1) and col not in (0, width - 1) for row, col in fives):
        errors.append("all color-5 decorations must lie on the border")
    triggers = _trigger_positions(grid)
    trigger_rows = {row for row, _ in triggers}
    if len(triggers) < 3:
        errors.append(f"expected at least three horizontal one-cell gaps, found {len(triggers)}")
    if len(trigger_rows) < 2:
        errors.append(f"expected triggers in at least two rows, found {len(trigger_rows)}")
    return errors


def strict_canonical_like(grid) -> list[str]:
    return self_check(grid)


def canonical_profile_signature(grid) -> str | None:
    if self_check(grid):
        return None
    return _PROFILE_BY_DIMENSIONS[(len(grid), len(grid[0]))]


def observe_overrides(grid) -> dict[str, str]:
    profile = canonical_profile_signature(grid)
    if profile is None:
        raise ValueError("grid does not satisfy a declared scene profile")
    return {"scene_profile": profile}


def rule_mirror(grid):
    """Independent Python mirror of the selected Racket authority."""
    output = deepcopy(grid)
    height = len(grid)
    width = len(grid[0])
    for row in range(height):
        for col in range(1, width - 1):
            if (
                grid[row][col] == 0
                and grid[row][col - 1] == 6
                and grid[row][col + 1] == 6
            ):
                output[row][col] = 6
    return output


def _fill_whole_span(grid):
    """Rival: fill every zero between each row's outermost color-6 cells."""
    output = deepcopy(grid)
    for row_index, row in enumerate(grid):
        positions = [col for col, value in enumerate(row) if value == 6]
        if len(positions) >= 2:
            for col in range(min(positions), max(positions) + 1):
                if output[row_index][col] == 0:
                    output[row_index][col] = 6
    return output


def _fill_horizontal_or_vertical(grid):
    """Rival: apply the one-cell local rule in both orientations."""
    output = rule_mirror(grid)
    height = len(grid)
    width = len(grid[0])
    for row in range(1, height - 1):
        for col in range(width):
            if (
                grid[row][col] == 0
                and grid[row - 1][col] == 6
                and grid[row + 1][col] == 6
            ):
                output[row][col] = 6
    return output


def _wide_horizontal_near_miss(grid) -> bool:
    return _fill_whole_span(grid) != rule_mirror(grid)


def _vertical_near_miss(grid) -> bool:
    return _fill_horizontal_or_vertical(grid) != rule_mirror(grid)


SEMANTIC_WITNESSES = {
    "wide_horizontal_near_miss": _wide_horizontal_near_miss,
    "vertical_near_miss": _vertical_near_miss,
}
SEMANTIC_RIVALS = {
    "fill_whole_span": _fill_whole_span,
    "fill_horizontal_or_vertical": _fill_horizontal_or_vertical,
}
WITNESS_RIVALS = {
    "wide_horizontal_near_miss": ["fill_whole_span"],
    "vertical_near_miss": ["fill_horizontal_or_vertical"],
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query) -> list[str]:
    reasons: list[str] = []
    for name, rival in LESSON_COMPETITORS.items():
        fits_demos = all(rival(pair["input"]) == pair["output"] for pair in demos)
        changes_query = rival(query["input"]) != query["output"]
        if fits_demos and changes_query:
            reasons.append(f"{name} fits every demonstration but changes the query")
    return reasons
