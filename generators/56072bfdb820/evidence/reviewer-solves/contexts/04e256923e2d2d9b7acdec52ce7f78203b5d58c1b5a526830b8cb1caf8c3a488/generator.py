"""Input sampler for ARC task 56072bfdb820, clipped diamond completion.

The unchanged selected rule reads a fixed 3x3 meta-grid.  Exactly two tiles
contain color-2 diamonds.  Their relative placement proposes one color-5 and
one color-8 diamond; proposed positions outside the 3x3 meta-grid are clipped,
so a lawful result may add zero, one, or two diamonds.  If any input symbol is
not color 2, the rule instead returns a 16x16 color-7 grid.

The six-profile schedule is lesson-shaped.  Every five demonstrations drawn
from one six-position block refute the three canonical-fitting shortcuts below,
even when any one of the six labelled pairs is held out as the query.
"""
from __future__ import annotations

from copy import deepcopy
from itertools import combinations
from typing import Callable, Sequence

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "56072bfdb820"
TASK_ID = GENERATOR_ID
RULE_HASH = "5eec51381abd"
VERSION = "5.0.0"
SUMMARY = (
    "An 11x11 color-7 field is divided by color-6 lines into nine 3x3 tiles. "
    "Exactly two tiles hold color-2 diamonds. Their relative placement proposes "
    "one color-5 and one color-8 diamond, with out-of-bounds proposals clipped, "
    "so zero, one, or two diamonds may be added. Any input color-5 or color-8 "
    "diamond is contamination and instead yields a 16x16 color-7 output."
)

INVARIANTS = [
    "the input is exactly 11x11 with color-6 dividers at rows and columns 3 and 7",
    "every non-divider tile is either all color 7 or one exact four-cell diamond",
    "exactly two diamonds are color 2; at most one each are color 5 and color 8",
    "all 36 placements are exact-override lawful; the default lesson schedule excludes identity/no-op placements",
    "bad_mask bit 0 adds one color-5 diamond and bit 1 adds one color-8 diamond",
    "the canonical Racket program remains the sole output authority",
]

AXES = {
    "pair_index": {
        "type": "int",
        "default": "six-profile lesson schedule, difficulty-stratified within profile",
        "valid": "0..35",
        "doc": "Lexicographic index of the two occupied color-2 tiles among C(9,2).",
    },
    "bad_mask": {
        "type": "int",
        "default": "schedule 0,0,3,1,2,0",
        "valid": "0..3",
        "doc": "Bit mask: 1 adds color 5 and 2 adds color 8; either triggers the bad-symbol branch.",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict] = []
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
MIN_STRICT_FRAC = 1.0
ALLOW_IDENTITY_OUTPUT = True
EXPECTED_OUTPUT_CODOMAIN = 17  # 16 transformed pair outputs plus one shared bad-symbol output
EXAMPLES_NEEDED = 5

SCHEDULE_PROFILES = (
    "full_completion",
    "clipped_completion_a",
    "both_bad_5_8",
    "single_bad_5",
    "single_bad_8",
    "clipped_completion_b",
)
_PROFILE_BAD_MASK = {
    "full_completion": 0,
    "clipped_completion_a": 0,
    "both_bad_5_8": 3,
    "single_bad_5": 1,
    "single_bad_8": 2,
    "clipped_completion_b": 0,
}

_DIAMOND = ((0, 1), (1, 0), (1, 2), (2, 1))
_TILES = tuple((row, col) for row in range(3) for col in range(3))
_PAIRS = tuple(combinations(_TILES, 2))
_PAIR_TO_INDEX = {pair: index for index, pair in enumerate(_PAIRS)}
_CANONICAL_VALID_PAIR_INDICES = frozenset({16, 26, 28})


def _raw_extras(pair: Sequence[tuple[int, int]]) -> tuple[tuple[int, int, int], ...]:
    """Return the two un-clipped proposals made by the selected authority."""
    (r1, c1), (r2, c2) = pair
    if c1 == c2:
        row, col = min(r1, r2) - 1, c1
        return ((row, col - 1, 5), (row, col + 1, 8))
    if r1 == r2:
        row, col = r1, min(c1, c2) - 1
        return ((row - 1, col, 8), (row + 1, col, 5))
    if c2 < c1:
        return ((r2, c2 - 1, 8), (r2 + 1, c2, 5))
    return ((r2, c2 + 1, 8), (r2 + 1, c2, 5))


def _clipped_extras(pair: Sequence[tuple[int, int]]) -> tuple[tuple[int, int, int], ...]:
    return tuple(
        item for item in _raw_extras(pair)
        if 0 <= item[0] < 3 and 0 <= item[1] < 3
    )


_PAIR_CLASSES = {
    count: tuple(index for index, pair in enumerate(_PAIRS) if len(_clipped_extras(pair)) == count)
    for count in (0, 1, 2)
}
_DISTANCE_CLASSES = {
    distance: tuple(
        index for index, pair in enumerate(_PAIRS)
        if abs(pair[0][0] - pair[1][0]) + abs(pair[0][1] - pair[1][1]) == distance
    )
    for distance in (1, 2, 3, 4)
}
_CLIPPED_BY_BAND = {
    None: _PAIR_CLASSES[1],
    "easy": tuple(index for index in _PAIR_CLASSES[1] if index in _DISTANCE_CLASSES[1]),
    "medium": tuple(index for index in _PAIR_CLASSES[1] if index in _DISTANCE_CLASSES[2]),
    "hard": tuple(index for index in _PAIR_CLASSES[1] if index in _DISTANCE_CLASSES[3] + _DISTANCE_CLASSES[4]),
}
_IDENTITY_BY_BAND = {
    None: _PAIR_CLASSES[0],
    "easy": tuple(index for index in _PAIR_CLASSES[0] if index in _DISTANCE_CLASSES[1]),
    "medium": tuple(index for index in _PAIR_CLASSES[0] if index in _DISTANCE_CLASSES[2]),
    "hard": tuple(index for index in _PAIR_CLASSES[0] if index in _DISTANCE_CLASSES[3] + _DISTANCE_CLASSES[4]),
}
_ALL_BY_BAND = {
    None: tuple(range(36)),
    "easy": _DISTANCE_CLASSES[1],
    "medium": _DISTANCE_CLASSES[2],
    "hard": _DISTANCE_CLASSES[3] + _DISTANCE_CLASSES[4],
}


def _validate_call_scalars(seed, sample_index) -> None:
    if type(seed) is not int:
        raise ValueError("seed must be an integer")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative integer")


def schedule_profile(seed, sample_index, difficulty=None) -> str:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    _validate_call_scalars(seed, sample_index)
    seed_value = seed & ((1 << 64) - 1)
    seed_shift = (
        (seed_value * 0x9E3779B1) ^ (seed_value >> 3)
    ) % len(SCHEDULE_PROFILES)
    return SCHEDULE_PROFILES[(sample_index + seed_shift) % len(SCHEDULE_PROFILES)]


def _validate_overrides(overrides: dict) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axes: {unknown}")
    for name, value in overrides.items():
        if value is not None and type(value) is not int:
            raise ValueError(f"{name} must be an integer, not {type(value).__name__}")
    if overrides.get("pair_index") is not None and not 0 <= overrides["pair_index"] <= 35:
        raise ValueError("pair_index must be in 0..35")
    if overrides.get("bad_mask") is not None and not 0 <= overrides["bad_mask"] <= 3:
        raise ValueError("bad_mask must be in 0..3")


def _draw_int_axis(ctx, overrides: dict, name: str, default: int, lo: int, hi: int) -> int:
    if name in overrides and overrides[name] is not None:
        return ctx.draw_int(name, lo, hi)
    return ctx.draw_int(name, default, default)


def _scheduled_pair(ctx, profile: str, difficulty) -> int:
    if profile == "full_completion":
        candidates = _PAIR_CLASSES[2]
    elif profile in ("clipped_completion_a", "clipped_completion_b"):
        candidates = _CLIPPED_BY_BAND[difficulty]
    else:
        candidates = _ALL_BY_BAND[difficulty]
    if not candidates:
        # The finite classes above are asserted by task-local tests; keep a
        # deterministic fallback rather than silently changing profile meaning.
        raise ValueError(f"no pair candidates for profile={profile!r}, difficulty={difficulty!r}")
    # This linked finite schedule deliberately mixes both lesson identity and
    # position, avoiding collisions in the seed==sample_index cohort used by
    # the shared defect gate while retaining exact six-profile blocks.
    seed_value = int(ctx.seed) & ((1 << 64) - 1)
    sample_value = int(ctx.sample_index) & ((1 << 64) - 1)
    seed_gray = seed_value ^ (seed_value >> 1)
    sample_mix = sample_value ^ (sample_value >> 2)
    offset = SCHEDULE_PROFILES.index(profile)
    slot = seed_gray * 5 + sample_mix * 3 + offset
    return tuple(candidates)[slot % len(candidates)]


def _base_grid() -> list[list[int]]:
    grid = full_grid(11, 11, 7)
    for row in (3, 7):
        grid[row] = [6] * 11
    for col in (3, 7):
        for row in range(11):
            grid[row][col] = 6
    return grid


def _put_diamond(grid: list[list[int]], tile: tuple[int, int], color: int) -> None:
    row0, col0 = tile[0] * 4, tile[1] * 4
    for dr, dc in _DIAMOND:
        grid[row0 + dr][col0 + dc] = color


def _bad_tiles(pair_index: int, bad_mask: int) -> dict[int, tuple[int, int]]:
    """Choose deterministic, distinct empty tiles for requested bad colors."""
    occupied = set(_PAIRS[pair_index])
    available = [tile for tile in _TILES if tile not in occupied]
    result: dict[int, tuple[int, int]] = {}
    for color, bit in ((5, 1), (8, 2)):
        if not bad_mask & bit:
            continue
        # Prefer a proposed extra slot of the opposite authority color.  This
        # reproduces the canonical invalid fixture for pair 3 while remaining
        # deterministic for every exact joint override.
        proposed = [
            (row, col)
            for row, col, proposal_color in _raw_extras(_PAIRS[pair_index])
            if proposal_color != color and (row, col) in available
        ]
        if proposed:
            tile = proposed[0]
        else:
            tile = available[(pair_index * 5 + color) % len(available)]
        available.remove(tile)
        result[color] = tile
    return result


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Construct one lawful input.  Outputs remain owned by the Racket rule."""
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    _validate_call_scalars(seed, sample_index)
    _validate_overrides(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = schedule_profile(seed, sample_index, difficulty)
    default_pair = _scheduled_pair(ctx, profile, difficulty)
    pair_index = _draw_int_axis(ctx, overrides, "pair_index", default_pair, 0, 35)
    bad_mask = _draw_int_axis(
        ctx,
        overrides,
        "bad_mask",
        _PROFILE_BAD_MASK[profile],
        0,
        3,
    )

    grid = _base_grid()
    for tile in _PAIRS[pair_index]:
        _put_diamond(grid, tile, 2)
    for color, tile in _bad_tiles(pair_index, bad_mask).items():
        _put_diamond(grid, tile, color)

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise ValueError(f"constructed invalid instance: {errors}")
    observed = observe_overrides(grid)
    expected = {"pair_index": pair_index, "bad_mask": bad_mask}
    if observed != expected:
        raise ValueError(f"constructed instance did not realize axes: {observed!r} != {expected!r}")
    return grid


def _grid_shape_errors(grid) -> list[str]:
    if not isinstance(grid, (list, tuple)) or len(grid) != 11:
        return ["grid must have exactly 11 rows"]
    if any(not isinstance(row, (list, tuple)) or len(row) != 11 for row in grid):
        return ["grid must be rectangular with exactly 11 columns"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["every cell must be a literal ARC integer color 0..9"]
    return []


def _analyze(grid) -> tuple[list[str], list[tuple[int, int, int]]]:
    errors = _grid_shape_errors(grid)
    if errors:
        return errors, []

    symbols: list[tuple[int, int, int]] = []
    for row in range(11):
        for col in range(11):
            if row in (3, 7) or col in (3, 7):
                if grid[row][col] != 6:
                    errors.append("divider rows and columns must be entirely color 6")
                    return errors, []
            elif grid[row][col] not in (2, 5, 7, 8):
                errors.append("non-divider cells may use only colors 2, 5, 7, and 8")
                return errors, []

    for tile_row, tile_col in _TILES:
        row0, col0 = tile_row * 4, tile_col * 4
        diamond_values = [grid[row0 + dr][col0 + dc] for dr, dc in _DIAMOND]
        other_values = [
            grid[row0 + dr][col0 + dc]
            for dr in range(3)
            for dc in range(3)
            if (dr, dc) not in _DIAMOND
        ]
        if all(value == 7 for value in diamond_values + other_values):
            continue
        if len(set(diamond_values)) != 1 or diamond_values[0] not in (2, 5, 8):
            errors.append(f"tile {(tile_row, tile_col)} must contain one exact monochrome diamond")
            continue
        if any(value != 7 for value in other_values):
            errors.append(f"tile {(tile_row, tile_col)} has stray non-background cells")
            continue
        symbols.append((tile_row, tile_col, diamond_values[0]))

    twos = [(row, col) for row, col, color in symbols if color == 2]
    fives = [(row, col) for row, col, color in symbols if color == 5]
    eights = [(row, col) for row, col, color in symbols if color == 8]
    if len(twos) != 2:
        errors.append(f"expected exactly two color-2 diamonds, got {len(twos)}")
    if len(fives) > 1:
        errors.append(f"expected at most one color-5 diamond, got {len(fives)}")
    if len(eights) > 1:
        errors.append(f"expected at most one color-8 diamond, got {len(eights)}")
    return errors, symbols


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty
    errors, symbols = _analyze(grid)
    if errors:
        return errors
    if meta and isinstance(meta, dict) and isinstance(meta.get("overrides"), dict):
        observed = observe_overrides(grid)
        for name, requested in meta["overrides"].items():
            if name in AXES and requested is not None and observed[name] != requested:
                errors.append(
                    f"override {name}={requested!r} was not realized; observed {observed[name]!r}"
                )
    return errors


def strict_canonical_like(grid):
    return self_check(grid)


def observe_overrides(grid) -> dict[str, int]:
    errors, symbols = _analyze(grid)
    if errors:
        raise ValueError(f"cannot observe axes from malformed input: {errors[0]}")
    pair = tuple((row, col) for row, col, color in symbols if color == 2)
    pair = tuple(sorted(pair))
    bad_mask = 0
    if any(color == 5 for _, _, color in symbols):
        bad_mask |= 1
    if any(color == 8 for _, _, color in symbols):
        bad_mask |= 2
    return {"pair_index": _PAIR_TO_INDEX[pair], "bad_mask": bad_mask}


def _render_symbols(symbols: Sequence[tuple[int, int, int]], *, wrap=False) -> list[list[int]]:
    """Render the authority's completion branch from row-major symbols."""
    twos = [(row, col) for row, col, color in symbols if color == 2]
    if len(twos) < 2:
        raise ValueError("completion branch needs at least two color-2 symbols")
    extras = _raw_extras(twos[:2])
    if wrap:
        extras = tuple((row % 3, col % 3, color) for row, col, color in extras)
    else:
        extras = tuple(
            item for item in extras
            if 0 <= item[0] < 3 and 0 <= item[1] < 3
        )
    # Racket append + find-first gives every observed symbol precedence.
    items = list(symbols) + list(extras)
    lookup: dict[tuple[int, int], int] = {}
    for row, col, color in items:
        lookup.setdefault((row, col), color)

    output = _base_grid()
    for tile, color in lookup.items():
        _put_diamond(output, tile, color)
    return output


def rule_mirror(grid) -> list[list[int]]:
    """Supplemental Python mirror of the pinned selected Racket authority."""
    errors, symbols = _analyze(grid)
    if errors:
        raise ValueError(f"rule_mirror requires a lawful generator input: {errors[0]}")
    if any(color != 2 for _, _, color in symbols):
        return full_grid(16, 16, 7)
    return _render_symbols(symbols)


def _canonical_pairs_only(grid):
    """Rival: memorize canonical valid pair placements; identity elsewhere."""
    observed = observe_overrides(grid)
    if observed["bad_mask"] or observed["pair_index"] in _CANONICAL_VALID_PAIR_INDICES:
        return rule_mirror(grid)
    return deepcopy(grid)


def _wrap_clipped_extras(grid):
    """Rival: wrap proposed meta-positions modulo 3 instead of clipping them."""
    errors, symbols = _analyze(grid)
    if errors:
        raise ValueError(errors[0])
    if any(color != 2 for _, _, color in symbols):
        return full_grid(16, 16, 7)
    return _render_symbols(symbols, wrap=True)


def _reject_only_both_bad_colors(grid):
    """Rival: reject only when both bad colors occur; treat a singleton as 2."""
    errors, symbols = _analyze(grid)
    if errors:
        raise ValueError(errors[0])
    colors = {color for _, _, color in symbols}
    if 5 in colors and 8 in colors:
        return full_grid(16, 16, 7)
    coerced = [(row, col, 2 if color in (5, 8) else color) for row, col, color in symbols]
    return _render_symbols(coerced)


def _noncanonical_completion_witness(grid) -> bool:
    observed = observe_overrides(grid)
    return (
        observed["bad_mask"] == 0
        and observed["pair_index"] not in _CANONICAL_VALID_PAIR_INDICES
        and rule_mirror(grid) != grid
    )


def _clipped_completion_witness(grid) -> bool:
    observed = observe_overrides(grid)
    return observed["bad_mask"] == 0 and len(_clipped_extras(_PAIRS[observed["pair_index"]])) == 1


def _single_bad_color_witness(grid) -> bool:
    return observe_overrides(grid)["bad_mask"] in (1, 2)


SEMANTIC_RIVALS: dict[str, Callable[[Sequence[Sequence[int]]], list[list[int]]]] = {
    "canonical_pairs_only": _canonical_pairs_only,
    "wrap_clipped_extras": _wrap_clipped_extras,
    "reject_only_both_bad_colors": _reject_only_both_bad_colors,
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
SEMANTIC_WITNESSES = {
    "noncanonical_completion": _noncanonical_completion_witness,
    "clipped_completion": _clipped_completion_witness,
    "single_bad_color": _single_bad_color_witness,
}
WITNESS_RIVALS = {
    "noncanonical_completion": ["canonical_pairs_only"],
    "clipped_completion": ["canonical_pairs_only", "wrap_clipped_extras"],
    "single_bad_color": ["reject_only_both_bad_colors"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Return reasons a declared wrong rule can still change the query answer."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query must contain an input grid"]

    reasons: list[str] = []
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        errors = self_check(demo["input"])
        if errors:
            reasons.append(f"demo {index} input is not lawful: {errors[0]}")
            continue
        if demo["output"] != rule_mirror(demo["input"]):
            reasons.append(f"demo {index} output disagrees with the selected rule")
    query_errors = self_check(query["input"])
    if query_errors:
        reasons.append(f"query input is not lawful: {query_errors[0]}")
    elif "output" in query and query["output"] != rule_mirror(query["input"]):
        reasons.append("query output disagrees with the selected rule")
    if reasons:
        return reasons

    query_truth = rule_mirror(query["input"])
    for name, competitor in LESSON_COMPETITORS.items():
        if all(competitor(demo["input"]) == demo["output"] for demo in demos):
            if competitor(query["input"]) != query_truth:
                reasons.append(
                    f"competitor {name!r} fits every demonstration and changes the query answer"
                )
    return reasons
