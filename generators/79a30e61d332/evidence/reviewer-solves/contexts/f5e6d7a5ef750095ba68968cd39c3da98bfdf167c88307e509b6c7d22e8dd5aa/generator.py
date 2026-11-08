"""Canonical-manifold sampler for ARC task 79a30e61d332.

A 17x25 input is a dense 4x6 lattice of 3x3 binary symbol tiles separated by
zero rows and columns.  The unique color-8 tile defines an exact 3x3 occupancy
mask.  Every tile with that exact mask is a key: its nonzero cells become 8.
For every pair of keys aligned in a tile row or column, nonzero cells in the
intervening non-key tiles become 7.

The sampler deliberately teaches the parts that the original two-key generator
left ambiguous: 3--6 keys, horizontal/vertical/mixed bridge layouts, bridges
not involving the visible seed, and a distractor with the same per-row totals
as the key but a different exact mask.
"""
from __future__ import annotations

from itertools import combinations
from typing import Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "79a30e61d332"
TASK_ID = GENERATOR_ID
VERSION = "4.0.0"
RULE_HASH = "0b623466d0bd"
SUMMARY = (
    "Dense canonical 4x6 lattice of 3x3 symbol tiles. The color-8 tile defines "
    "an exact binary mask shared by 3..6 keys; matching keys become 8 and "
    "nonzero tiles between aligned keys become 7. A scheduled horizontal, "
    "vertical, and mixed curriculum includes exact-mask counterexamples."
)

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0
SCHEDULE_PROFILES = ("horizontal", "vertical", "mixed")
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []

INVARIANTS = [
    "input is a 17x25 dense 4x6 lattice of nonempty 3x3 binary tiles",
    "separator rows and columns at multiples of four are all zero",
    "exactly one tile uses color 8 and all other nonzero input cells use color 1",
    "3..6 tiles share the color-8 tile's exact occupancy mask",
    "at least one non-key tile lies between aligned key tiles",
    "every generated input contains a same-row-totals but different-mask distractor",
]

AXES = {
    "layout_profile": {
        "type": "str",
        "default": "three-step schedule",
        "valid": "horizontal|vertical|mixed",
    },
    "n_keys": {
        "type": "int",
        "default": "difficulty band",
        "valid": "3..6",
    },
    "key_cells": {
        "type": "int",
        "default": "difficulty band",
        "valid": "3..8",
    },
}

_TILE_ROWS = 4
_TILE_COLS = 6
_POSITIONS = tuple((tr, tc) for tr in range(_TILE_ROWS) for tc in range(_TILE_COLS))
_AXES = ("horizontal", "vertical")


def _bits(mask_id: int) -> tuple[int, ...]:
    return tuple((mask_id >> shift) & 1 for shift in range(8, -1, -1))


def _row_sums(mask: Iterable[int]) -> tuple[int, int, int]:
    cells = tuple(mask)
    return tuple(sum(cells[3 * row : 3 * row + 3]) for row in range(3))  # type: ignore[return-value]


def _has_full_support(mask: tuple[int, ...]) -> bool:
    return all(sum(mask[3 * row : 3 * row + 3]) for row in range(3)) and all(
        sum(mask[col::3]) for col in range(3)
    )


def _build_key_groups() -> dict[int, tuple[tuple[tuple[int, ...], ...], ...]]:
    by_cells: dict[int, dict[tuple[int, int, int], list[tuple[int, ...]]]] = {
        cells: {} for cells in range(3, 9)
    }
    for mask_id in range(1, 1 << 9):
        mask = _bits(mask_id)
        cells = sum(mask)
        if cells not in by_cells or not _has_full_support(mask):
            continue
        by_cells[cells].setdefault(_row_sums(mask), []).append(mask)
    return {
        cells: tuple(
            tuple(sorted(group))
            for _, group in sorted(groups.items())
            if len(group) >= 2
        )
        for cells, groups in by_cells.items()
    }


_KEY_GROUPS = _build_key_groups()
_DISTRACTOR_MASKS = tuple(_bits(mask_id) for mask_id in range(1, 1 << 9))


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Cycle the three bridge branches independently of seed and difficulty."""
    del seed, difficulty
    return SCHEDULE_PROFILES[sample_index % len(SCHEDULE_PROFILES)]


def _controls(overrides: dict[str, object]) -> dict[str, object]:
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    active = {name: value for name, value in overrides.items() if value is not None}

    if "layout_profile" in active:
        value = active["layout_profile"]
        if type(value) is not str:
            raise TypeError("layout_profile must be a string")
        if value not in SCHEDULE_PROFILES:
            raise ValueError(f"layout_profile must be one of {SCHEDULE_PROFILES}")
    for name, bounds in (("n_keys", (3, 6)), ("key_cells", (3, 8))):
        if name not in active:
            continue
        value = active[name]
        if type(value) is not int:
            raise TypeError(f"{name} must be an integer (not bool)")
        lo, hi = bounds
        if not lo <= value <= hi:
            raise ValueError(f"{name} must be in {lo}..{hi}")
    return active


def _difficulty_options(difficulty, easy, medium, hard, default):
    if difficulty == "easy":
        return easy
    if difficulty == "medium":
        return medium
    if difficulty == "hard":
        return hard
    return default


def _draw_axis(ctx, active, name, default_options, full_options):
    options = full_options if name in active else default_options
    return ctx.draw_choice(name, tuple(options))


def _paint_tile(grid, tr: int, tc: int, color: int, mask: Iterable[int]) -> None:
    for index, occupied in enumerate(mask):
        if not occupied:
            continue
        dr, dc = divmod(index, 3)
        grid[1 + 4 * tr + dr][1 + 4 * tc + dc] = color


def _clear_tile(grid, tr: int, tc: int) -> None:
    for dr in range(3):
        for dc in range(3):
            grid[1 + 4 * tr + dr][1 + 4 * tc + dc] = 0


def _tile_mask(grid, tr: int, tc: int) -> tuple[int, ...]:
    return tuple(
        int(grid[1 + 4 * tr + dr][1 + 4 * tc + dc] != 0)
        for dr in range(3)
        for dc in range(3)
    )


def _tile_values(grid, tr: int, tc: int) -> tuple[int, ...]:
    return tuple(
        grid[1 + 4 * tr + dr][1 + 4 * tc + dc]
        for dr in range(3)
        for dc in range(3)
    )


def _aligned_pairs(keys: Iterable[tuple[int, int]]):
    for a, b in combinations(sorted(keys), 2):
        if a[0] == b[0]:
            yield a, b, "horizontal"
        if a[1] == b[1]:
            yield a, b, "vertical"


def _bridge_positions(
    keys: Iterable[tuple[int, int]],
    allowed_axes: Iterable[str] = _AXES,
) -> set[tuple[int, int]]:
    key_set = set(keys)
    allowed = set(allowed_axes)
    result: set[tuple[int, int]] = set()
    for a, b, axis in _aligned_pairs(key_set):
        if axis not in allowed:
            continue
        if axis == "horizontal":
            result.update(
                (a[0], col)
                for col in range(min(a[1], b[1]) + 1, max(a[1], b[1]))
            )
        else:
            result.update(
                (row, a[1])
                for row in range(min(a[0], b[0]) + 1, max(a[0], b[0]))
            )
    return result - key_set


def _seed_bridge_positions(
    keys: Iterable[tuple[int, int]], seed: tuple[int, int]
) -> set[tuple[int, int]]:
    key_set = set(keys)
    result: set[tuple[int, int]] = set()
    for other in key_set - {seed}:
        if other[0] == seed[0]:
            result.update(
                (seed[0], col)
                for col in range(min(seed[1], other[1]) + 1, max(seed[1], other[1]))
            )
        if other[1] == seed[1]:
            result.update(
                (row, seed[1])
                for row in range(min(seed[0], other[0]) + 1, max(seed[0], other[0]))
            )
    return result - key_set


def _profile_from_keys(keys: Iterable[tuple[int, int]]) -> str:
    horizontal = _bridge_positions(keys, ("horizontal",))
    vertical = _bridge_positions(keys, ("vertical",))
    if horizontal and not vertical:
        return "horizontal"
    if vertical and not horizontal:
        return "vertical"
    # A mixed lesson must make each axis independently observable.  Merely
    # having a vertical pair whose bridge is already covered by a horizontal
    # pair does not refute the horizontal-only rival (and vice versa).
    if horizontal - vertical and vertical - horizontal:
        return "mixed"
    return "none"


def _layout_candidate(
    keys: Iterable[tuple[int, int]], profile: str
) -> tuple[tuple[tuple[int, int], ...], tuple[tuple[int, int], ...]] | None:
    key_tuple = tuple(sorted(keys))
    if _profile_from_keys(key_tuple) != profile:
        return None
    bridges = _bridge_positions(key_tuple)
    valid_seeds = tuple(
        seed
        for seed in key_tuple
        if bridges - _seed_bridge_positions(key_tuple, seed)
    )
    if not valid_seeds:
        return None
    return key_tuple, valid_seeds


def _draw_key_layout(rng, profile: str, n_keys: int):
    # Rejection sampling has comfortable support even in the narrowest case
    # (vertical, six keys).  The deterministic exhaustive fallback makes the
    # constructive contract total rather than probabilistic.
    for _ in range(4096):
        candidate = _layout_candidate(rng.sample(_POSITIONS, n_keys), profile)
        if candidate is not None:
            keys, valid_seeds = candidate
            return keys, rng.choice(valid_seeds)
    for keys in combinations(_POSITIONS, n_keys):
        candidate = _layout_candidate(keys, profile)
        if candidate is not None:
            key_tuple, valid_seeds = candidate
            return key_tuple, valid_seeds[0]
    raise RuntimeError(f"no constructive {profile!r} layout for n_keys={n_keys}")


def _draw_key_and_collision_masks(rng, key_cells: int):
    groups = _KEY_GROUPS[key_cells]
    group = rng.choice(groups)
    key_mask = rng.choice(group)
    collision_mask = rng.choice([mask for mask in group if mask != key_mask])
    return key_mask, collision_mask


def generate(seed, sample_index, *, difficulty=None, **overrides):
    active = _controls(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=active,
    )

    profile = _draw_axis(
        ctx,
        active,
        "layout_profile",
        (schedule_profile(seed, sample_index, difficulty),),
        SCHEDULE_PROFILES,
    )
    n_keys = _draw_axis(
        ctx,
        active,
        "n_keys",
        _difficulty_options(
            difficulty,
            easy=(3, 4),
            medium=(4, 5),
            hard=(5, 6),
            default=(3, 4, 5, 6),
        ),
        range(3, 7),
    )
    key_cells = _draw_axis(
        ctx,
        active,
        "key_cells",
        _difficulty_options(
            difficulty,
            easy=(3, 4),
            medium=(5, 6),
            hard=(7, 8),
            default=(3, 4, 5, 6, 7, 8),
        ),
        range(3, 9),
    )

    layout_rng = ctx.draw_rng("key_layout")
    key_tiles, seed_tile = _draw_key_layout(layout_rng, profile, n_keys)
    key_set = set(key_tiles)

    mask_rng = ctx.draw_rng("tile_masks")
    key_mask, collision_mask = _draw_key_and_collision_masks(mask_rng, key_cells)
    distractor_pool = [mask for mask in _DISTRACTOR_MASKS if mask != key_mask]
    nonkeys = [position for position in _POSITIONS if position not in key_set]
    collision_position = mask_rng.choice(nonkeys)

    grid = full_grid(17, 25, 0)
    for position in nonkeys:
        mask = collision_mask if position == collision_position else mask_rng.choice(distractor_pool)
        _paint_tile(grid, *position, 1, mask)
    for position in key_tiles:
        _paint_tile(grid, *position, 8 if position == seed_tile else 1, key_mask)
    return grid


def _rectangular_error(grid):
    if (
        not isinstance(grid, (list, tuple))
        or not grid
        or not isinstance(grid[0], (list, tuple))
        or not grid[0]
    ):
        return "expected a nonempty rectangular grid"
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return "expected a nonempty rectangular grid"
    return None


def _seed_and_keys(grid):
    seed_tiles = [position for position in _POSITIONS if 8 in _tile_values(grid, *position)]
    if len(seed_tiles) != 1:
        raise ValueError(f"expected exactly one color-8 seed tile; got {len(seed_tiles)}")
    seed = seed_tiles[0]
    key_mask = _tile_mask(grid, *seed)
    keys = [position for position in _POSITIONS if _tile_mask(grid, *position) == key_mask]
    return seed, key_mask, keys


def self_check(grid, *, difficulty=None, meta=None):
    """Validate the canonical dense symbol-lattice input domain."""
    del difficulty, meta
    rectangular = _rectangular_error(grid)
    if rectangular:
        return [rectangular]
    h, w = len(grid), len(grid[0])
    errors: list[str] = []
    if (h, w) != (17, 25):
        errors.append(f"expected canonical 17x25 tile lattice; got {h}x{w}")
        return errors
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        errors.append("cells must be integer colors 0..9 (booleans are not colors)")
        return errors
    illegal = sorted({value for row in grid for value in row} - {0, 1, 8})
    if illegal:
        errors.append(f"input colors must be a subset of {{0,1,8}}; got {illegal}")

    for row in range(0, h, 4):
        if any(grid[row][col] != 0 for col in range(w)):
            errors.append(f"separator row {row} is not all zero")
            break
    for col in range(0, w, 4):
        if any(grid[row][col] != 0 for row in range(h)):
            errors.append(f"separator column {col} is not all zero")
            break

    empty_tiles = [position for position in _POSITIONS if not any(_tile_mask(grid, *position))]
    if empty_tiles:
        errors.append(f"expected all 24 symbol tiles to be nonempty; empty={empty_tiles[:4]}")

    seed_tiles = [position for position in _POSITIONS if 8 in _tile_values(grid, *position)]
    if len(seed_tiles) != 1:
        errors.append(f"expected exactly one color-8 seed tile; got {len(seed_tiles)}")
        return errors
    seed = seed_tiles[0]
    seed_nonzero = {value for value in _tile_values(grid, *seed) if value != 0}
    if seed_nonzero != {8}:
        errors.append("every nonzero cell of the seed tile must be color 8")
    for position in _POSITIONS:
        if position == seed:
            continue
        nonzero = {value for value in _tile_values(grid, *position) if value != 0}
        if nonzero and nonzero != {1}:
            errors.append(f"non-seed tile {position} must use only color 1")
            break

    key_mask = _tile_mask(grid, *seed)
    key_cells = sum(key_mask)
    if not 3 <= key_cells <= 8:
        errors.append(f"key mask must contain 3..8 cells; got {key_cells}")
    if not _has_full_support(key_mask):
        errors.append("key mask must occupy every local row and column")
    keys = [position for position in _POSITIONS if _tile_mask(grid, *position) == key_mask]
    if not 3 <= len(keys) <= 6:
        errors.append(f"expected 3..6 exact key-mask matches; got {len(keys)}")
    if not _bridge_positions(keys):
        errors.append("expected a non-key bridge tile between aligned key tiles")
    return errors


def strict_canonical_like(grid):
    return self_check(grid)


def observe_overrides(grid):
    errors = self_check(grid)
    if errors:
        raise ValueError("; ".join(errors))
    _, key_mask, keys = _seed_and_keys(grid)
    return {
        "layout_profile": _profile_from_keys(keys),
        "n_keys": len(keys),
        "key_cells": sum(key_mask),
    }


def _solve_with_keys(grid, keys, allowed_axes=_AXES):
    out = [list(row) for row in grid]
    key_set = set(keys)
    bridges = _bridge_positions(key_set, allowed_axes)
    for tr, tc in _POSITIONS:
        color = 8 if (tr, tc) in key_set else 7 if (tr, tc) in bridges else None
        if color is None:
            continue
        for dr in range(3):
            for dc in range(3):
                row, col = 1 + 4 * tr + dr, 1 + 4 * tc + dc
                if out[row][col] != 0:
                    out[row][col] = color
    return out


def _exact_keys(grid):
    _, _, keys = _seed_and_keys(grid)
    return keys


def _reference_output(grid):
    return _solve_with_keys(grid, _exact_keys(grid))


rule_mirror = _reference_output


def _row_sums_only(grid):
    seed, key_mask, _ = _seed_and_keys(grid)
    del seed
    signature = _row_sums(key_mask)
    keys = [position for position in _POSITIONS if _row_sums(_tile_mask(grid, *position)) == signature]
    return _solve_with_keys(grid, keys)


def _horizontal_only(grid):
    return _solve_with_keys(grid, _exact_keys(grid), ("horizontal",))


def _vertical_only(grid):
    return _solve_with_keys(grid, _exact_keys(grid), ("vertical",))


def _seed_lines_only(grid):
    seed, _, keys = _seed_and_keys(grid)
    out = [list(row) for row in grid]
    key_set = set(keys)
    bridges = _seed_bridge_positions(key_set, seed)
    for tr, tc in _POSITIONS:
        color = 8 if (tr, tc) in key_set else 7 if (tr, tc) in bridges else None
        if color is None:
            continue
        for dr in range(3):
            for dc in range(3):
                row, col = 1 + 4 * tr + dr, 1 + 4 * tc + dc
                if out[row][col] != 0:
                    out[row][col] = color
    return out


def _first_two_keys(grid):
    seed, _, keys = _seed_and_keys(grid)
    other = next(position for position in keys if position != seed)
    return _solve_with_keys(grid, (seed, other))


def _keys_only(grid):
    return _solve_with_keys(grid, _exact_keys(grid), ())


def _has_row_sum_collision(grid) -> bool:
    _, key_mask, _ = _seed_and_keys(grid)
    signature = _row_sums(key_mask)
    return any(
        _tile_mask(grid, *position) != key_mask
        and _row_sums(_tile_mask(grid, *position)) == signature
        for position in _POSITIONS
    )


def _has_horizontal_bridge(grid) -> bool:
    keys = _exact_keys(grid)
    horizontal = _bridge_positions(keys, ("horizontal",))
    vertical = _bridge_positions(keys, ("vertical",))
    return bool(horizontal - vertical)


def _has_vertical_bridge(grid) -> bool:
    keys = _exact_keys(grid)
    horizontal = _bridge_positions(keys, ("horizontal",))
    vertical = _bridge_positions(keys, ("vertical",))
    return bool(vertical - horizontal)


def _has_nonseed_pair_bridge(grid) -> bool:
    seed, _, keys = _seed_and_keys(grid)
    return bool(_bridge_positions(keys) - _seed_bridge_positions(keys, seed))


def _has_more_than_two_keys(grid) -> bool:
    return len(_exact_keys(grid)) > 2


def _has_bridge_recoloring(grid) -> bool:
    return bool(_bridge_positions(_exact_keys(grid)))


SEMANTIC_WITNESSES = {
    "exact_mask_not_row_totals": _has_row_sum_collision,
    "horizontal_bridge": _has_horizontal_bridge,
    "vertical_bridge": _has_vertical_bridge,
    "nonseed_pair_bridge": _has_nonseed_pair_bridge,
    "more_than_two_keys": _has_more_than_two_keys,
    "bridge_recoloring": _has_bridge_recoloring,
}
SEMANTIC_RIVALS = {
    "row_sums_only": _row_sums_only,
    "horizontal_only": _horizontal_only,
    "vertical_only": _vertical_only,
    "seed_lines_only": _seed_lines_only,
    "first_two_keys": _first_two_keys,
    "keys_only": _keys_only,
}
WITNESS_RIVALS = {
    "exact_mask_not_row_totals": ["row_sums_only"],
    "horizontal_bridge": ["vertical_only"],
    "vertical_bridge": ["horizontal_only"],
    "nonseed_pair_bridge": ["seed_lines_only"],
    "more_than_two_keys": ["first_two_keys"],
    "bridge_recoloring": ["keys_only"],
}
CANONICAL_SHORTCUTS = {"row_sums_only": _row_sums_only}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query):
    """Require the demonstrations to refute every declared plausible rival."""
    del query
    reasons = []
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            reasons.append(f"demonstrations do not distinguish declared rival {name}")
    return reasons
