"""Generator for ARC task ebd08d719ed6, "Recolor the Densest Tile".

Color-9 lines divide the input into a lattice of 3x3 tiles.  Exactly one tile
has more occupied (nonzero) cells than every other tile.  The output preserves
the lattice and recolors only the occupied cells of that unique densest tile
to color 8.

The three-example default curriculum deliberately contains one canonical
2x2/count-{2,3,4,5} anchor and two counterexamples to the canonical-fitting
shortcut "recolor the five-cell tile".
"""
from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.lattice import assemble_tiles, blank_tile

GENERATOR_ID = "ebd08d719ed6"
TASK_ID = GENERATOR_ID
RULE_HASH = "f5f6e2df9282"
VERSION = "3.0.0"
SUMMARY = (
    "Color-9 divider lines form a 2x2..4x4 lattice of 3x3 tiles. Count each "
    "tile's nonzero cells, find the unique maximum, and recolor only that "
    "tile's occupied cells to color 8. Every default three-example lesson "
    "contains a canonical {2,3,4,5} anchor, a unique maximum of 4 with no "
    "five-cell tile, and a unique maximum of 7 with a five-cell distractor."
)

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.30

INVARIANTS = [
    "color 9 occurs exactly on one-cell divider rows and columns",
    "the divider lattice contains 2..4 rows and 2..4 columns of 3x3 tiles",
    "every tile is nonempty and exactly one tile has maximal occupancy",
    "tile foreground colors are either shared color 2 or shared colors 2 and 3",
    "the count profile is one of the three declared semantic profiles",
]

COUNT_PROFILES = (
    "canonical_2345",
    "max4_no5",
    "max7_with5_distractor",
)
PALETTE_PROFILES = ("canonical_single", "mixed_shared")

AXES = {
    "tile_rows": {
        "type": "int",
        "default": "scheduled 2..4; every third example is the canonical value 2",
        "valid": "2..4",
    },
    "tile_cols": {
        "type": "int",
        "default": "scheduled 2..4; every third example is the canonical value 2",
        "valid": "2..4",
    },
    "count_profile": {
        "type": "str",
        "default": "sample_index cycle across all three semantic profiles",
        "valid": "|".join(COUNT_PROFILES),
    },
    "palette_profile": {
        "type": "str",
        "default": "canonical_single anchor then mixed_shared counterexamples",
        "valid": "|".join(PALETTE_PROFILES),
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()


def _validate_call(overrides: dict[str, Any]) -> None:
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")

    for name in ("tile_rows", "tile_cols"):
        if name not in overrides or overrides[name] is None:
            continue
        value = overrides[name]
        if type(value) is not int:
            raise TypeError(f"{name} must be an integer, not {type(value).__name__}")
        if not 2 <= value <= 4:
            raise ValueError(f"{name}={value} outside [2, 4]")

    domains = {
        "count_profile": COUNT_PROFILES,
        "palette_profile": PALETTE_PROFILES,
    }
    for name, domain in domains.items():
        if name not in overrides or overrides[name] is None:
            continue
        value = overrides[name]
        if type(value) is not str:
            raise TypeError(f"{name} must be a string, not {type(value).__name__}")
        if value not in domain:
            raise ValueError(f"{name}={value!r} not in {list(domain)}")


def _scheduled_choice(ctx, label: str, domain: Sequence[Any], scheduled: Any) -> Any:
    """Record a full-domain choice while selecting an exact scheduled default."""
    if scheduled not in domain:
        raise ValueError(f"scheduled {label} value {scheduled!r} is outside domain")
    options = list(domain) * 4
    selected_index = ctx.draw_rng(label).randrange(len(options))
    options[selected_index] = scheduled
    return ctx.draw_choice(label, options)


def _scheduled_dimensions(sample_index: int, difficulty: Any) -> tuple[int, int]:
    slot = int(sample_index) % EXAMPLES_NEEDED
    if slot == 0:
        return 2, 2
    cycle = int(sample_index) // EXAMPLES_NEEDED
    offset = {"easy": 0, "medium": 1, "hard": 2}.get(difficulty, 0)
    values = (2, 3, 4)
    rows = values[(cycle + slot + offset) % len(values)]
    cols = values[(2 * cycle + 2 * slot + offset) % len(values)]
    return rows, cols


def _profile_counts(profile: str, tile_count: int) -> list[int]:
    if tile_count < 4:
        raise ValueError("at least four tiles are required")
    if profile == "canonical_2345":
        base = [2, 3, 4, 5]
        extras = (1, 2, 3, 4)
    elif profile == "max4_no5":
        base = [1, 2, 3, 4]
        extras = (1, 2, 3)
    elif profile == "max7_with5_distractor":
        base = [2, 3, 5, 7]
        extras = (1, 2, 3, 4)
    else:  # guarded by the public validation and draw domain
        raise ValueError(f"unknown count profile: {profile!r}")
    return base + [extras[index % len(extras)] for index in range(tile_count - 4)]


def _tile(rng, count: int, color: int) -> list[list[int]]:
    tile = blank_tile(3, 3)
    cells = [(row, col) for row in range(3) for col in range(3)]
    rng.shuffle(cells)
    for row, col in cells[:count]:
        tile[row][col] = color
    return tile


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    slot = int(sample_index) % EXAMPLES_NEEDED
    scheduled_rows, scheduled_cols = _scheduled_dimensions(sample_index, difficulty)
    rows = _scheduled_choice(ctx, "tile_rows", (2, 3, 4), scheduled_rows)
    cols = _scheduled_choice(ctx, "tile_cols", (2, 3, 4), scheduled_cols)
    count_profile = _scheduled_choice(
        ctx,
        "count_profile",
        COUNT_PROFILES,
        COUNT_PROFILES[slot],
    )
    palette_profile = _scheduled_choice(
        ctx,
        "palette_profile",
        PALETTE_PROFILES,
        "canonical_single" if slot == 0 else "mixed_shared",
    )

    counts = _profile_counts(count_profile, rows * cols)
    ctx.draw_rng("tile_count_positions").shuffle(counts)

    if palette_profile == "canonical_single":
        colors = [2] * (rows * cols)
    else:
        colors = [2 if index % 2 == 0 else 3 for index in range(rows * cols)]
        ctx.draw_rng("tile_color_positions").shuffle(colors)

    shape_rng = ctx.draw_rng("tile_shapes")
    tiles: list[list[list[list[int]]]] = []
    for row in range(rows):
        tile_row = []
        for col in range(cols):
            index = row * cols + col
            tile_row.append(_tile(shape_rng, counts[index], colors[index]))
        tiles.append(tile_row)
    return assemble_tiles(tiles)


def _spans(size: int, separators: Sequence[int]) -> list[tuple[int, int]]:
    previous = -1
    spans: list[tuple[int, int]] = []
    for separator in [*separators, size]:
        if separator - previous - 1 > 0:
            spans.append((previous + 1, separator))
        previous = separator
    return spans


def _classify_count_profile(counts: Sequence[int]) -> str | None:
    if not counts:
        return None
    maximum = max(counts)
    if counts.count(maximum) != 1:
        return None
    if maximum == 5 and all(1 <= count <= 5 for count in counts):
        if {2, 3, 4, 5} <= set(counts) and counts.count(5) == 1:
            return "canonical_2345"
    if maximum == 4 and all(1 <= count <= 4 for count in counts):
        if {1, 2, 3, 4} <= set(counts) and 5 not in counts:
            return "max4_no5"
    if maximum == 7 and all(1 <= count <= 7 for count in counts):
        if counts.count(7) == 1 and counts.count(5) == 1:
            return "max7_with5_distractor"
    return None


def _parse_grid(grid) -> dict[str, Any]:
    if not isinstance(grid, (list, tuple)) or not grid:
        raise ValueError("grid must be a nonempty list of rows")
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        raise ValueError("grid must be a nonempty rectangular grid")
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    for row_index, row in enumerate(grid):
        for col_index, value in enumerate(row):
            if type(value) is not int or not 0 <= value <= 9:
                raise ValueError(
                    f"cell ({row_index},{col_index}) is not an ARC color: {value!r}"
                )

    height = len(grid)
    if (height + 1) % 4 or (width + 1) % 4:
        raise ValueError(
            "grid dimensions must encode 3x3 tiles separated by one-cell dividers"
        )
    tile_rows = (height + 1) // 4
    tile_cols = (width + 1) // 4
    if not 2 <= tile_rows <= 4 or not 2 <= tile_cols <= 4:
        raise ValueError(
            f"tile lattice must be 2..4 by 2..4, got {tile_rows}x{tile_cols}"
        )

    separator_rows = tuple(range(3, height, 4))
    separator_cols = tuple(range(3, width, 4))
    separator_row_set = set(separator_rows)
    separator_col_set = set(separator_cols)
    for row in range(height):
        for col in range(width):
            expected_separator = row in separator_row_set or col in separator_col_set
            value = grid[row][col]
            if expected_separator and value != 9:
                raise ValueError(f"divider cell ({row},{col}) must be color 9")
            if not expected_separator and value == 9:
                raise ValueError(f"stray color 9 inside tile at ({row},{col})")

    row_spans = _spans(height, separator_rows)
    col_spans = _spans(width, separator_cols)
    tiles: list[list[tuple[int, int]]] = []
    counts: list[int] = []
    foreground_colors: set[int] = set()
    for row_start, row_end in row_spans:
        for col_start, col_end in col_spans:
            if (row_end - row_start, col_end - col_start) != (3, 3):
                raise ValueError("every lattice tile must be 3x3")
            cells = [
                (row, col)
                for row in range(row_start, row_end)
                for col in range(col_start, col_end)
            ]
            colors = {grid[row][col] for row, col in cells if grid[row][col] != 0}
            if not colors:
                raise ValueError("every tile must contain at least one occupied cell")
            if not colors <= {2, 3}:
                raise ValueError(
                    f"tile foreground colors must be shared colors 2/3, found {sorted(colors)}"
                )
            if len(colors) != 1:
                raise ValueError("each tile must use exactly one foreground color")
            foreground_colors.update(colors)
            tiles.append(cells)
            counts.append(sum(grid[row][col] != 0 for row, col in cells))

    count_profile = _classify_count_profile(counts)
    if count_profile is None:
        raise ValueError(f"tile occupancies do not match a declared count profile: {counts}")
    if foreground_colors == {2}:
        palette_profile = "canonical_single"
    elif foreground_colors == {2, 3}:
        palette_profile = "mixed_shared"
    else:
        raise ValueError(
            f"foreground palette does not match a declared profile: {sorted(foreground_colors)}"
        )

    return {
        "tile_rows": tile_rows,
        "tile_cols": tile_cols,
        "tiles": tiles,
        "counts": counts,
        "count_profile": count_profile,
        "palette_profile": palette_profile,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty, meta
    try:
        _parse_grid(grid)
    except (TypeError, ValueError) as exc:
        return [str(exc)]
    return []


def strict_canonical_like(grid) -> list[str]:
    try:
        analysis = _parse_grid(grid)
    except (TypeError, ValueError) as exc:
        return [str(exc)]
    reasons: list[str] = []
    if (analysis["tile_rows"], analysis["tile_cols"]) != (2, 2):
        reasons.append("canonical-like lattice must be exactly 2x2")
    if analysis["count_profile"] != "canonical_2345":
        reasons.append("canonical-like occupancies must be exactly {2,3,4,5}")
    if analysis["palette_profile"] != "canonical_single":
        reasons.append("canonical-like foreground palette must be exactly color 2")
    return reasons


def observe_overrides(grid) -> dict[str, int | str]:
    analysis = _parse_grid(grid)
    return {
        "tile_rows": analysis["tile_rows"],
        "tile_cols": analysis["tile_cols"],
        "count_profile": analysis["count_profile"],
        "palette_profile": analysis["palette_profile"],
    }


def _recolor_tile(grid, analysis: dict[str, Any], tile_index: int | None) -> list[list[int]]:
    output = [list(row) for row in grid]
    if tile_index is None:
        return output
    for row, col in analysis["tiles"][tile_index]:
        if output[row][col] != 0:
            output[row][col] = 8
    return output


def rule_mirror(grid) -> list[list[int]]:
    """Independent Python mirror; the pinned Racket program remains authoritative."""
    analysis = _parse_grid(grid)
    target = analysis["counts"].index(max(analysis["counts"]))
    return _recolor_tile(grid, analysis, target)


def _fixed_five(grid) -> list[list[int]]:
    """Canonical-fitting rival that recolors a five-cell tile regardless of rank."""
    analysis = _parse_grid(grid)
    target = next(
        (index for index, count in enumerate(analysis["counts"]) if count == 5),
        None,
    )
    return _recolor_tile(grid, analysis, target)


def _fixed_five_counterexample(grid) -> bool:
    try:
        return _fixed_five(grid) != rule_mirror(grid)
    except (TypeError, ValueError):
        return False


SEMANTIC_WITNESSES = {
    "fixed_five_counterexample": _fixed_five_counterexample,
}
SEMANTIC_RIVALS = {
    "fixed_five": _fixed_five,
}
WITNESS_RIVALS = {
    "fixed_five_counterexample": ["fixed_five"],
}
CANONICAL_SHORTCUTS = {
    "fixed_five": _fixed_five,
}
LESSON_COMPETITORS = {
    "fixed_five": _fixed_five,
}
