"""Semantic generator for ARC task 25e78410d5bb.

Color-5 wall cells partition a zero background into rectangular regions.  Two
indicator colors replace selected wall cells.  For every 4-connected zero
region, the oracle counts cardinally adjacent indicators and fills the whole
region with the strict-majority indicator color; walls and indicators remain.

The four canonical 10x10 inputs contain two linked lattice families (2x3 and
3x3 regions).  Default generation places a 1/3 prior on one complete canonical
input profile, then varies only D4 orientation that preserves the declared
row/column band counts and a semantic color renaming.  The remaining draws
construct generalized 2..4 by 2..4 lattices on 10..20 grids with coupled
majority/minority witnesses around every region.
"""
from __future__ import annotations

from collections import Counter
from itertools import permutations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "25e78410d5bb"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "efe95d8efebe"
SUMMARY = (
    "Color-5 walls partition zero cells into a rectangular lattice. Two "
    "indicator colors sit in the walls; each zero region is filled with the "
    "strict-majority adjacent indicator color."
)

INVARIANTS = [
    "input palette is exactly {0, 5, indicator_a, indicator_b}",
    "zero cells form a 2..4 by 2..4 lattice of rectangular 4-connected regions",
    "every zero region has at least one adjacent indicator and a strict majority",
    "both indicator colors win at least one region and at least one region sees both colors",
    "all non-wall nonzero cells are cardinally adjacent to a zero region",
]

SCENE_PROFILES = (
    "canonical_train_1",
    "canonical_train_2",
    "canonical_train_3",
    "canonical_test_1",
    "general_lattice",
)
PALETTE_KINDS = ("canonical", "warm", "cool", "contrast")
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()

AXES = {
    "grid_h": {
        "type": "int",
        "default": "coupled band draw 10..20; canonical profiles pin 10",
        "valid": "10..20",
    },
    "grid_w": {
        "type": "int",
        "default": "coupled band draw 10..20; canonical profiles pin 10",
        "valid": "10..20",
    },
    "row_bands": {
        "type": "int",
        "default": "difficulty-aware 2..4; canonical profiles pin 2 or 3",
        "valid": "2..4",
    },
    "col_bands": {
        "type": "int",
        "default": "difficulty-aware 2..4; canonical profiles pin 3",
        "valid": "2..4",
    },
    "scene_profile": {
        "type": "str",
        "default": "1/3 complete canonical profile, otherwise general_lattice",
        "valid": "|".join(SCENE_PROFILES),
    },
    "palette_kind": {
        "type": "str",
        "default": "uniform semantic two-color renaming",
        "valid": "|".join(PALETTE_KINDS),
    },
}

_DIRS4 = ((-1, 0), (1, 0), (0, -1), (0, 1))
_PALETTES = {
    "canonical": (1, 2),
    "warm": (2, 7),
    "cool": (1, 8),
    "contrast": (3, 9),
}

# Complete canonical input profiles only.  Outputs are always produced by the
# canonical Racket oracle.  Profiles are nuisance-varied by reflection/180°
# rotation and semantic color renaming before return.
_CANONICAL_GRIDS = {
    "canonical_train_1": (
        (2, 5, 5, 5, 1, 5, 5, 5, 5, 2),
        (0, 0, 5, 0, 0, 0, 0, 5, 0, 0),
        (0, 0, 1, 0, 0, 0, 0, 1, 0, 0),
        (0, 0, 5, 0, 0, 0, 0, 5, 0, 0),
        (0, 0, 5, 0, 0, 0, 0, 5, 0, 0),
        (5, 1, 5, 5, 5, 2, 5, 5, 5, 1),
        (0, 0, 5, 0, 0, 0, 0, 5, 0, 0),
        (0, 0, 5, 0, 0, 0, 0, 2, 0, 0),
        (0, 0, 5, 0, 0, 0, 0, 5, 0, 0),
        (1, 5, 5, 5, 2, 5, 5, 5, 5, 1),
    ),
    "canonical_train_2": (
        (1, 5, 1, 5, 5, 2, 5, 5, 5, 1),
        (0, 0, 0, 5, 0, 0, 0, 5, 0, 0),
        (0, 0, 0, 5, 0, 0, 0, 2, 0, 0),
        (0, 0, 0, 5, 0, 0, 0, 5, 0, 0),
        (5, 2, 5, 5, 5, 5, 5, 5, 2, 5),
        (0, 0, 0, 5, 0, 0, 0, 5, 0, 0),
        (0, 0, 0, 1, 0, 0, 0, 5, 0, 0),
        (0, 0, 0, 5, 0, 0, 0, 5, 0, 0),
        (0, 0, 0, 5, 0, 0, 0, 5, 0, 0),
        (5, 2, 5, 5, 5, 5, 1, 5, 5, 2),
    ),
    "canonical_train_3": (
        (1, 5, 2, 5, 2, 5, 5, 5, 5, 1),
        (0, 0, 0, 5, 0, 0, 2, 0, 0, 0),
        (0, 0, 0, 5, 0, 0, 5, 0, 0, 0),
        (5, 2, 5, 5, 5, 1, 5, 5, 2, 5),
        (0, 0, 0, 5, 0, 0, 2, 0, 0, 0),
        (0, 0, 0, 1, 0, 0, 5, 0, 0, 0),
        (2, 2, 5, 5, 1, 5, 5, 5, 1, 5),
        (0, 0, 0, 5, 0, 0, 1, 0, 0, 0),
        (0, 0, 0, 5, 0, 0, 5, 0, 0, 0),
        (5, 5, 1, 5, 5, 1, 5, 5, 2, 5),
    ),
    "canonical_test_1": (
        (5, 1, 5, 5, 5, 5, 5, 5, 1, 5),
        (0, 0, 5, 0, 0, 5, 0, 0, 0, 0),
        (0, 0, 5, 0, 0, 1, 0, 0, 0, 0),
        (5, 5, 5, 5, 1, 5, 5, 2, 1, 5),
        (0, 0, 2, 0, 0, 2, 0, 0, 0, 0),
        (0, 0, 5, 0, 0, 5, 0, 0, 0, 0),
        (2, 5, 5, 5, 2, 5, 5, 1, 2, 5),
        (0, 0, 1, 0, 0, 2, 0, 0, 0, 0),
        (0, 0, 5, 0, 0, 5, 0, 0, 0, 0),
        (5, 2, 5, 5, 5, 5, 1, 5, 5, 1),
    ),
}
_CANONICAL_BANDS = {
    "canonical_train_1": (2, 3),
    "canonical_train_2": (2, 3),
    "canonical_train_3": (3, 3),
    "canonical_test_1": (3, 3),
}
# Four canonical choices over eight generalized slots = exactly 1/3 prior.
_WEIGHTED_SCENES = tuple(_CANONICAL_GRIDS) + ("general_lattice",) * 8


def _copy_grid(grid):
    return [list(row) for row in grid]


def _flip_lr(grid):
    return [list(reversed(row)) for row in grid]


def _flip_ud(grid):
    return [row[:] for row in reversed(grid)]


def _rotate_180(grid):
    return _flip_ud(_flip_lr(grid))


def _transpose(grid):
    return [list(row) for row in zip(*grid)]


def _rotate_cw(grid):
    return _flip_lr(_transpose(grid))


def _d4(grid):
    base = _copy_grid(grid)
    r1 = _rotate_cw(base)
    r2 = _rotate_cw(r1)
    r3 = _rotate_cw(r2)
    return (
        base,
        r1,
        r2,
        r3,
        _flip_lr(base),
        _flip_lr(r1),
        _flip_lr(r2),
        _flip_lr(r3),
    )


def _axis_preserving_orientations(grid, row_bands, col_bands):
    """D4 nuisance transforms that preserve declared row/column band counts."""
    base = _copy_grid(grid)
    if row_bands == col_bands:
        return _d4(base)
    return (base, _flip_lr(base), _flip_ud(base), _rotate_180(base))


def _recolor(grid, colors):
    a, b = colors
    return [
        [a if value == 1 else b if value == 2 else value for value in row]
        for row in grid
    ]


def _zero_components(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    components = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != 0 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                cr, cc = stack.pop()
                cells.append((cr, cc))
                for dr, dc in _DIRS4:
                    nr, nc = cr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and grid[nr][nc] == 0
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            components.append(cells)
    return components


def _component_votes(grid, cells):
    h, w = len(grid), len(grid[0])
    votes = []
    for r, c in cells:
        for dr, dc in _DIRS4:
            nr, nc = r + dr, c + dc
            if 0 <= nr < h and 0 <= nc < w:
                value = grid[nr][nc]
                if value not in (0, 5):
                    votes.append(value)
    return Counter(votes)


def _band_shape(grid):
    components = _zero_components(grid)
    if not components:
        return None
    row_ranges = set()
    col_ranges = set()
    for cells in components:
        r0 = min(r for r, _ in cells)
        r1 = max(r for r, _ in cells)
        c0 = min(c for _, c in cells)
        c1 = max(c for _, c in cells)
        expected = {
            (r, c)
            for r in range(r0, r1 + 1)
            for c in range(c0, c1 + 1)
        }
        if set(cells) != expected:
            return None
        row_ranges.add((r0, r1))
        col_ranges.add((c0, c1))
    if len(components) != len(row_ranges) * len(col_ranges):
        return None
    return len(row_ranges), len(col_ranges)


def observe_overrides(grid):
    """Expose exact returned semantic axes for override-contract v6."""
    shape = _band_shape(grid)
    if shape is None:
        return {}
    row_bands, col_bands = shape
    return {"row_bands": row_bands, "col_bands": col_bands}


def _normalized_profile(grid):
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        return None
    colors = sorted({value for row in grid for value in row if value not in (0, 5)})
    if len(colors) != 2:
        return None
    candidates = []
    for transformed in _d4(grid):
        for mapped in permutations((1, 2)):
            color_map = dict(zip(colors, mapped))
            normalized = tuple(
                tuple(color_map.get(value, value) for value in row)
                for row in transformed
            )
            candidates.append(normalized)
    return min(candidates)


def canonical_profile_signature(grid):
    """Return the complete linked canonical input signature, or ``None``."""
    signature = _normalized_profile(grid)
    if signature in _CANONICAL_SIGNATURES:
        return signature
    return None


_CANONICAL_SIGNATURES = frozenset(
    _normalized_profile(_copy_grid(grid)) for grid in _CANONICAL_GRIDS.values()
)


def _resolve_size_and_bands(ctx, overrides, size_name, band_name):
    size_given = size_name in overrides and overrides[size_name] is not None
    bands_given = band_name in overrides and overrides[band_name] is not None

    if size_given and bands_given:
        size = ctx.draw_int(size_name, 10, 20)
        bands = ctx.draw_int(band_name, 2, 4)
        if size < 3 * bands - 1:
            raise ValueError(
                f"{size_name}={size} cannot realize {band_name}={bands} "
                "with two-cell regions"
            )
        return size, bands

    if size_given:
        size = ctx.draw_int(size_name, 10, 20)
        max_bands = min(4, (size + 1) // 3)
        bands = ctx.draw_int_diff(band_name, 2, max_bands)
        return size, bands

    if bands_given:
        bands = ctx.draw_int(band_name, 2, 4)
        size = ctx.draw_int_diff(size_name, max(10, 3 * bands - 1), 20)
        return size, bands

    bands = ctx.draw_int_diff(band_name, 2, 4)
    size = ctx.draw_int_diff(size_name, max(10, 3 * bands - 1), 20)
    return size, bands


def _partition_intervals(total, bands, rng):
    """Positive intervals of width >=2 separated by one-cell wall lines."""
    free = total - (bands - 1) - 2 * bands
    if free < 0:
        raise ValueError(f"cannot partition {total} cells into {bands} bands")
    sizes = [2] * bands
    for _ in range(free):
        sizes[rng.randrange(bands)] += 1
    intervals = []
    cursor = 0
    for index, size in enumerate(sizes):
        intervals.append((cursor, cursor + size - 1))
        cursor += size
        if index + 1 < bands:
            cursor += 1
    separators = [intervals[index][1] + 1 for index in range(bands - 1)]
    return intervals, separators


def _draw_general_lattice(ctx, overrides, colors):
    h, row_bands = _resolve_size_and_bands(
        ctx, overrides, "grid_h", "row_bands"
    )
    w, col_bands = _resolve_size_and_bands(
        ctx, overrides, "grid_w", "col_bands"
    )
    rng = ctx.draw_rng("general_lattice")
    row_intervals, sep_rows = _partition_intervals(h, row_bands, rng)
    col_intervals, sep_cols = _partition_intervals(w, col_bands, rng)

    grid = full_grid(h, w, 0)
    for row in sep_rows:
        for col in range(w):
            grid[row][col] = 5
    for col in sep_cols:
        for row in range(h):
            grid[row][col] = 5

    # Row-band winners alternate so both colors necessarily win somewhere.
    winners = [colors[index % 2] for index in range(row_bands)]

    # Every vertical separator contributes two winner votes to each adjacent
    # region in the same row band.  This guarantees a stable majority even
    # after the minority witnesses below are added.
    for band_index, (r0, r1) in enumerate(row_intervals):
        rows = list(range(r0, r1 + 1))
        for sep_index, col in enumerate(sep_cols):
            local = rows[:]
            rng.shuffle(local)
            chosen = local[:2]
            for row in chosen:
                grid[row][col] = winners[band_index]

    # On each horizontal separator, each column band gets one marker of the
    # upper winner and one of the lower winner.  Thus both neighboring regions
    # see both colors, but their two vertical winner votes keep the result
    # unambiguous (3-vs-1 on edge columns, 5-vs-1 on interior columns).
    for sep_index, row in enumerate(sep_rows):
        upper = winners[sep_index]
        lower = winners[sep_index + 1]
        for c0, c1 in col_intervals:
            cols = list(range(c0, c1 + 1))
            rng.shuffle(cols)
            grid[row][cols[0]] = upper
            grid[row][cols[1]] = lower

    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    palette_kind = ctx.draw_choice("palette_kind", PALETTE_KINDS)
    colors = _PALETTES[palette_kind]

    numeric_axes = ("grid_h", "grid_w", "row_bands", "col_bands")
    numeric_override = any(
        name in overrides and overrides[name] is not None for name in numeric_axes
    )
    explicit_scene = "scene_profile" in overrides and overrides["scene_profile"] is not None
    scene_options = (
        _WEIGHTED_SCENES
        if explicit_scene or not numeric_override
        else ("general_lattice",)
    )
    scene_profile = ctx.draw_choice("scene_profile", scene_options)

    if scene_profile == "general_lattice":
        return _draw_general_lattice(ctx, overrides, colors)

    template = _copy_grid(_CANONICAL_GRIDS[scene_profile])
    expected_rows, expected_cols = _CANONICAL_BANDS[scene_profile]
    h = ctx.draw_int("grid_h", 10, 10)
    w = ctx.draw_int("grid_w", 10, 10)
    row_bands = ctx.draw_int("row_bands", expected_rows, expected_rows)
    col_bands = ctx.draw_int("col_bands", expected_cols, expected_cols)
    if (h, w) != (10, 10):  # defensive; draw_int already enforces this
        raise ValueError("canonical profiles require a 10x10 grid")
    orient_rng = ctx.draw_rng("canonical_orientation")
    orientations = _axis_preserving_orientations(template, row_bands, col_bands)
    oriented = orientations[orient_rng.randrange(len(orientations))]
    return _recolor(oriented, colors)


def self_check(grid, *, difficulty=None, meta=None):
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return ["grid must be a non-empty list of rows"]
    width = len(grid[0])
    if width == 0 or any(not isinstance(row, list) or len(row) != width for row in grid):
        return ["grid must be rectangular"]

    h, w = len(grid), width
    errors = []
    if not (10 <= h <= 20 and 10 <= w <= 20):
        errors.append(f"dimensions {h}x{w} outside 10..20")
    invalid = {
        value
        for row in grid
        for value in row
        if not isinstance(value, int)
        or isinstance(value, bool)
        or not 0 <= value <= 9
    }
    if invalid:
        errors.append(f"invalid ARC cell values: {sorted(invalid, key=repr)}")
        return errors

    marker_colors = sorted(
        {value for row in grid for value in row if value not in (0, 5)}
    )
    if len(marker_colors) != 2:
        errors.append(
            f"expected exactly two indicator colors besides 0/5, got {marker_colors}"
        )

    shape = _band_shape(grid)
    if shape is None:
        errors.append("zero regions must form a complete rectangular lattice")
        return errors
    row_bands, col_bands = shape
    if not (2 <= row_bands <= 4 and 2 <= col_bands <= 4):
        errors.append(
            f"lattice must be 2..4 by 2..4, got {row_bands}x{col_bands}"
        )

    components = _zero_components(grid)
    winners = set()
    mixed_region = False
    for index, cells in enumerate(components):
        counts = _component_votes(grid, cells)
        if not counts:
            errors.append(f"zero region {index} has no adjacent indicator")
            continue
        ranked = counts.most_common()
        if len(ranked) > 1 and ranked[0][1] == ranked[1][1]:
            errors.append(f"zero region {index} has a tied indicator vote {dict(counts)}")
            continue
        winners.add(ranked[0][0])
        mixed_region = mixed_region or len(counts) >= 2

    if len(marker_colors) == 2 and winners != set(marker_colors):
        errors.append(
            f"both indicator colors must win at least one region; winners={sorted(winners)}"
        )
    if not mixed_region:
        errors.append("at least one region must see both indicator colors")

    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value in (0, 5):
                continue
            if not any(
                0 <= r + dr < h
                and 0 <= c + dc < w
                and grid[r + dr][c + dc] == 0
                for dr, dc in _DIRS4
            ):
                errors.append(f"indicator at {(r, c)} is not adjacent to any zero region")

    return errors
