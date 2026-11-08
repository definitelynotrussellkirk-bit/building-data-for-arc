"""Input generator for ``Sort Tiles by Occupancy Count``.

The unchanged Racket authority splits a 3-row strip at full color-9 separator
columns, counts every nonzero payload cell in each 3x3 tile, and reorders the
whole tiles from sparsest to densest.  Canonical tiles are all monochrome red,
so three plausible wrong keys fit every published pair: number of red cells,
modal-color frequency, and raw color sum.  The four-slot curriculum keeps one
canonical-size/palette anchor and three mixed-palette counterexamples in every
consecutive lesson window.
"""
from __future__ import annotations

from collections import Counter
from typing import Any, Callable, Iterable, Sequence

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "88ce0ac7322b"
TASK_ID = GENERATOR_ID
RULE_HASH = "53d8281899b9"
VERSION = "2.0.0"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "A 3-row strip contains three to five 3x3 tiles separated by full color-9 "
    "columns.  Tile occupancies are distinct and initially unsorted; outputs "
    "sort whole tiles from fewest to most nonzero cells.  A five-residue "
    "schedule includes two canonical red anchors and three two-color witness "
    "profiles; every four-pair lesson refutes red-count, modal-frequency, and "
    "raw-sum shortcuts."
)

INVARIANTS = [
    "input is exactly three rows with 3..5 3x3 payload tiles separated by full color-9 columns",
    "payload cells use ARC colors except separator color 9; every tile has 1..8 occupied cells",
    "tile occupancies are pairwise distinct and the input is not already ascending by occupancy",
    "canonical3 uses only payload color 2; every mixed profile refutes all declared canonical shortcuts",
]

PROFILES = ("canonical3", "mixed3", "mixed4", "mixed5")
ORDER_PATTERNS = ("reverse", "rotate", "zigzag")
SCHEDULE_PROFILES = ("canonical3", "mixed3", "canonical3", "mixed4", "mixed5")

AXES = {
    "profile": {
        "type": "str",
        "default": "five-residue schedule: canonical3,mixed3,canonical3,mixed4,mixed5",
        "valid": "canonical3|mixed3|mixed4|mixed5",
    },
    "order_pattern": {
        "type": "str",
        "default": "fifteen-slot schedule over reverse,rotate,zigzag",
        "valid": "reverse|rotate|zigzag",
    },
}

# Every profile/order pair is constructive in every difficulty band.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []

_BANDS = {None, "easy", "medium", "hard"}
_CANONICAL_COUNTS = {
    "easy": ((1, 2, 3), (1, 2, 4)),
    "medium": ((1, 2, 3), (1, 2, 4), (1, 3, 5), (2, 3, 4)),
    "hard": ((1, 4, 8), (2, 5, 8), (1, 5, 7), (2, 4, 7)),
}
_MIXED_ROLES = {
    # The first role is always occupancy four.  The middle role uses a balanced
    # 1/2 palette, so its modal count is three and its color-2 count is 2 or 3.
    # The last role is all color 1.  Thus all three canonical-fitting sort keys
    # are non-monotone while the whole grid stays close to the canonical palette.
    "easy": ((4, 5, 7), (4, 5, 8)),
    "medium": ((4, 5, 7), (4, 6, 7), (4, 5, 8)),
    "hard": ((4, 6, 7), (4, 6, 8), (4, 5, 8)),
}
_EXTRA_COLORS = (1, 2)

Tile = list[list[int]]
Grid = list[list[int]]


def _band(difficulty: str | None) -> str:
    if difficulty not in _BANDS:
        raise ValueError("difficulty must be easy, medium, hard, or None")
    return "medium" if difficulty is None else difficulty


def schedule_profile(seed: int, sample_index: int, difficulty: str | None = None) -> str:
    """Every four-pair window has at least two mixed shortcut witnesses."""
    del seed
    _band(difficulty)
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def _scheduled_order(sample_index: int) -> str:
    return ORDER_PATTERNS[(int(sample_index) // len(SCHEDULE_PROFILES)) % len(ORDER_PATTERNS)]


def _draw_scheduled_choice(ctx, name: str, options: Sequence[str], scheduled: str) -> str:
    if ctx.overrides.get(name) is not None:
        return str(ctx.draw_choice(name, options))
    return str(ctx.draw_choice(name, (scheduled,)))


def _tile(count: int, values: Iterable[int], rng) -> Tile:
    values = list(values)
    if len(values) != count:
        raise ValueError(f"tile color list length {len(values)} != occupancy {count}")
    if not 1 <= count <= 8:
        raise ValueError(f"tile occupancy {count} outside 1..8")
    if any(type(value) is not int or value in (0, 9) or not 0 <= value <= 9 for value in values):
        raise ValueError("tile payload colors must be literal nonzero ARC colors other than 9")

    positions = rng.sample(range(9), count)
    rng.shuffle(values)
    tile = full_grid(3, 3, 0)
    for position, value in zip(positions, values):
        row, col = divmod(position, 3)
        tile[row][col] = value
    return tile


def _assemble(tiles: Sequence[Tile]) -> Grid:
    if not tiles:
        raise ValueError("cannot assemble an empty tile strip")
    width = len(tiles) * 3 + len(tiles) - 1
    grid = full_grid(3, width, 9)
    for index, tile in enumerate(tiles):
        start = index * 4
        for row in range(3):
            for col in range(3):
                grid[row][start + col] = tile[row][col]
    return grid


def _split_tiles(grid: Sequence[Sequence[int]]) -> list[Tile]:
    width = len(grid[0])
    return [
        [list(row[start : start + 3]) for row in grid]
        for start in range(0, width, 4)
    ]


def _flat(tile: Sequence[Sequence[int]]) -> list[int]:
    return [value for row in tile for value in row]


def _occupancy(tile: Sequence[Sequence[int]]) -> int:
    return sum(value != 0 for value in _flat(tile))


def _dominant_count(tile: Sequence[Sequence[int]]) -> int:
    counts = Counter(value for value in _flat(tile) if value != 0)
    return max(counts.values(), default=0)


def _color_2_count(tile: Sequence[Sequence[int]]) -> int:
    return sum(value == 2 for value in _flat(tile))


def _raw_color_sum(tile: Sequence[Sequence[int]]) -> int:
    return sum(_flat(tile))


def _sort_tiles_by_key(grid: Sequence[Sequence[int]], key: Callable[[Tile], int]) -> Grid:
    # Python's stable sort is an intentionally plausible tie policy for rivals.
    tiles = _split_tiles(grid)
    return _assemble(sorted(tiles, key=key))


def rule_mirror(grid: Sequence[Sequence[int]]) -> Grid:
    """Independent Python mirror for tests; the selected Racket rule is authority."""
    return _sort_tiles_by_key(grid, _occupancy)


def _sort_by_color_2_count(grid: Sequence[Sequence[int]]) -> Grid:
    return _sort_tiles_by_key(grid, _color_2_count)


def _sort_by_dominant_count(grid: Sequence[Sequence[int]]) -> Grid:
    return _sort_tiles_by_key(grid, _dominant_count)


def _sort_by_raw_color_sum(grid: Sequence[Sequence[int]]) -> Grid:
    return _sort_tiles_by_key(grid, _raw_color_sum)


def _order_indices(count: int, pattern: str) -> tuple[int, ...]:
    if pattern == "reverse":
        return tuple(range(count - 1, -1, -1))
    if pattern == "rotate":
        return tuple(range(1, count)) + (0,)
    if pattern == "zigzag":
        result: list[int] = []
        low, high = 0, count - 1
        while low <= high:
            result.append(high)
            high -= 1
            if low <= high:
                result.append(low)
                low += 1
        return tuple(result)
    raise ValueError(f"unknown order pattern {pattern!r}")


def _canonical_tiles(ctx, band: str) -> list[tuple[int, Tile]]:
    counts = ctx.draw_rng("canonical_counts").choice(_CANONICAL_COUNTS[band])
    result = []
    for index, count in enumerate(counts):
        rng = ctx.draw_rng(f"canonical_tile_{index}_{count}")
        result.append((count, _tile(count, [2] * count, rng)))
    return result


def _mixed_tiles(ctx, band: str, tile_count: int) -> list[tuple[int, Tile]]:
    small, middle, large = ctx.draw_rng("mixed_role_counts").choice(_MIXED_ROLES[band])
    occupied_counts = {small, middle, large}
    available = [count for count in range(1, 9) if count not in occupied_counts]
    extras_needed = tile_count - 3
    extras = ctx.draw_rng("extra_counts").sample(available, extras_needed)

    middle_values = [1] * ((middle + 1) // 2) + [2] * (middle // 2)
    specs: list[tuple[int, list[int], str]] = [
        # Occupancy four but four red cells: red-count and modal-count both start at 4.
        (small, [2] * small, "small_red"),
        # Balanced 1/2 colors: modal count 3, red count 2 or 3, raw sum 7 or 9.
        (middle, middle_values, "middle_balanced"),
        # Larger all-color-1 tile: zero red cells and raw sum equal to occupancy.
        (large, [1] * large, "large_low_value"),
    ]
    for slot, count in enumerate(extras):
        color = ctx.draw_rng(f"extra_color_{slot}").choice(_EXTRA_COLORS)
        specs.append((count, [color] * count, f"extra_{slot}"))

    result: list[tuple[int, Tile]] = []
    for count, values, label in specs:
        result.append((count, _tile(count, values, ctx.draw_rng(f"tile_{label}_{count}"))))
    return sorted(result, key=lambda item: item[0])


def generate(seed, sample_index, *, difficulty=None, **overrides):
    band = _band(difficulty)
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError("unknown override axis/axes: " + ", ".join(unknown))

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = _draw_scheduled_choice(
        ctx,
        "profile",
        PROFILES,
        schedule_profile(seed, sample_index, difficulty),
    )
    order_pattern = _draw_scheduled_choice(
        ctx,
        "order_pattern",
        ORDER_PATTERNS,
        _scheduled_order(sample_index),
    )

    if profile == "canonical3":
        ordered = sorted(_canonical_tiles(ctx, band), key=lambda item: item[0])
    else:
        tile_count = int(profile[-1])
        ordered = _mixed_tiles(ctx, band, tile_count)

    indices = _order_indices(len(ordered), order_pattern)
    grid = _assemble([ordered[index][1] for index in indices])
    errors = self_check(grid)
    if errors:
        raise RuntimeError("generator constructed an invalid grid: " + "; ".join(errors))
    return grid


def _shape_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a nonempty sequence of rows"]
    if any(not isinstance(row, (list, tuple)) for row in grid):
        return ["every row must be a sequence"]
    if len(grid) != 3:
        return [f"tile strip must have exactly 3 rows, found {len(grid)}"]
    width = len(grid[0])
    if width == 0 or any(len(row) != width for row in grid):
        return ["grid must be nonempty and rectangular"]
    if (width + 1) % 4 != 0:
        return [f"tile strip width {width} is not 3n+(n-1)"]
    tile_count = (width + 1) // 4
    if not 3 <= tile_count <= 5:
        return [f"tile strip must contain 3..5 tiles, found {tile_count}"]
    for row in grid:
        for value in row:
            if type(value) is not int or not 0 <= value <= 9:
                return ["cells must be literal ARC color integers 0 through 9"]
    return []


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the lawful tile-strip grammar without requiring one curriculum profile."""
    del difficulty, meta
    errors = _shape_errors(grid)
    if errors:
        return errors

    width = len(grid[0])
    tile_count = (width + 1) // 4
    problems: list[str] = []
    for separator in range(3, width, 4):
        if any(grid[row][separator] != 9 for row in range(3)):
            problems.append(f"separator column {separator} must be all color 9")

    occupancies: list[int] = []
    for index in range(tile_count):
        start = index * 4
        values = [grid[row][col] for row in range(3) for col in range(start, start + 3)]
        if 9 in values:
            problems.append(f"tile {index} payload must not contain separator color 9")
        count = sum(value != 0 for value in values)
        occupancies.append(count)
        if not 1 <= count <= 8:
            problems.append(f"tile {index} occupancy {count} must be in 1..8")

    if len(set(occupancies)) != len(occupancies):
        problems.append(f"tile occupancies must be pairwise distinct, found {occupancies}")
    if occupancies == sorted(occupancies):
        problems.append(f"input is already sorted by occupancy count: {occupancies}")
    return sorted(set(problems))


def strict_canonical_like(grid) -> list[str]:
    """All ordinary draws stay on the reviewed 3x3-tile task grammar."""
    return self_check(grid)


def _profile_from_grid(grid: Sequence[Sequence[int]]) -> str | None:
    tile_count = (len(grid[0]) + 1) // 4
    payload_colors = {
        value
        for tile in _split_tiles(grid)
        for value in _flat(tile)
        if value != 0
    }
    if tile_count == 3 and payload_colors == {2}:
        return "canonical3"
    if tile_count in (3, 4, 5):
        return f"mixed{tile_count}"
    return None


def _order_from_grid(grid: Sequence[Sequence[int]]) -> str | None:
    counts = [_occupancy(tile) for tile in _split_tiles(grid)]
    ranks = {count: rank for rank, count in enumerate(sorted(counts))}
    pattern = tuple(ranks[count] for count in counts)
    for name in ORDER_PATTERNS:
        if pattern == _order_indices(len(counts), name):
            return name
    return None


def observe_overrides(grid) -> dict[str, str | None]:
    """Recover both exact controls from returned pixels, not RNG bookkeeping."""
    if self_check(grid):
        return {}
    return {
        "profile": _profile_from_grid(grid),
        "order_pattern": _order_from_grid(grid),
    }


def _mixed_palette_refutes_shortcuts(grid) -> bool:
    if self_check(grid) or _profile_from_grid(grid) == "canonical3":
        return False
    expected = rule_mirror(grid)
    return all(rival(grid) != expected for rival in SEMANTIC_RIVALS.values())


SEMANTIC_RIVALS = {
    "color_2_count": _sort_by_color_2_count,
    "dominant_color_count": _sort_by_dominant_count,
    "raw_color_sum": _sort_by_raw_color_sum,
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
SEMANTIC_WITNESSES = {
    "mixed_palette_refutes_shortcuts": _mixed_palette_refutes_shortcuts,
}
WITNESS_RIVALS = {
    "mixed_palette_refutes_shortcuts": tuple(SEMANTIC_RIVALS),
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject malformed labels and any lesson whose demos leave a named rival live."""
    reasons: list[str] = []
    if not isinstance(demos, (list, tuple)) or len(demos) < 2:
        reasons.append("lesson needs at least two labeled demonstrations")
        demos = [] if not isinstance(demos, (list, tuple)) else list(demos)

    valid_demos: list[dict[str, Any]] = []
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        errors = self_check(demo["input"])
        if errors:
            reasons.append(f"demo {index} input invalid: {'; '.join(errors)}")
            continue
        expected = rule_mirror(demo["input"])
        if demo["output"] != expected:
            reasons.append(f"demo {index} output is not the authoritative occupancy sort")
            continue
        valid_demos.append(demo)

    if not isinstance(query, dict) or "input" not in query:
        reasons.append("query must contain an input grid")
        return reasons
    query_errors = self_check(query["input"])
    if query_errors:
        reasons.append("query input invalid: " + "; ".join(query_errors))
        return reasons
    expected_query = rule_mirror(query["input"])
    if "output" in query and query["output"] != expected_query:
        reasons.append("query output is not the authoritative occupancy sort")

    for name, rival in LESSON_COMPETITORS.items():
        if valid_demos and all(rival(demo["input"]) == demo["output"] for demo in valid_demos):
            if rival(query["input"]) != expected_query:
                reasons.append(
                    f"named shortcut {name!r} survives every demonstration and changes the query answer"
                )
    return reasons
