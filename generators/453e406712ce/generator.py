"""Generate binary periodic fields with one boundary-attached square hole.

The input is a 4x4, 5x5, or 7x7 crop of a minimal period-2 or period-3
two-color pattern.  One solid square at the boundary is erased to black.  The
rule detects the smallest period and returns the values missing from the
erased square.
"""

from __future__ import annotations

from typing import NamedTuple

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "453e406712ce"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "6dd0a63a27c0"
SUMMARY = (
    "A binary minimal-period field has one square boundary hole; recover the "
    "periodic values inside the hole's bounding box."
)
INVARIANTS = [
    "the canvas is square with side 4, 5, or 7",
    "the intact field uses exactly two nonzero colors and minimal period 2 or 3",
    "all zeros form one solid 1x1, 2x2, or 3x3 square touching the boundary",
    "the top-left period tile stays intact and every multi-cell answer is non-solid",
]
EXPECTED_OUTPUT_CODOMAIN = 18_873


class SceneSpec(NamedTuple):
    size: int
    period: int
    hole_size: int
    touched_sides: int
    template: str | None


SCENE_SPECS = {
    # The first four modes retain every linked public dimension, minimal
    # period, hole size, edge relation, and toroidal/D4 tile morphology.
    "p2_n4_h1_edge": SceneSpec(4, 2, 1, 1, "checker"),
    "p2_n5_h2_corner": SceneSpec(5, 2, 2, 2, "one_minority"),
    "p3_n7_h2_corner": SceneSpec(7, 3, 2, 2, "block_cross"),
    "p3_n7_h3_corner": SceneSpec(7, 3, 3, 2, "three_marks"),
    # Linked extrapolations recombine only demonstrated sizes, periods, hole
    # sizes, and edge relations.
    "p2_n5_h3_edge": SceneSpec(5, 2, 3, 1, None),
    "p2_n4_h2_corner": SceneSpec(4, 2, 2, 2, None),
    "p3_n7_h2_edge": SceneSpec(7, 3, 2, 1, None),
    "p3_n7_h3_edge": SceneSpec(7, 3, 3, 1, None),
}
SCENE_PROFILES = tuple(SCENE_SPECS)
PUBLIC_PROFILES = SCENE_PROFILES[:4]

_TEMPLATE_BITS = {
    "checker": [[0, 1], [1, 0]],
    "one_minority": [[0, 1], [1, 1]],
    "block_cross": [
        [0, 0, 1],
        [0, 0, 1],
        [1, 1, 1],
    ],
    "three_marks": [
        [0, 1, 0],
        [1, 0, 0],
        [0, 0, 1],
    ],
}

_PROFILE_WEIGHTS = {
    "easy": PUBLIC_PROFILES + SCENE_PROFILES[4:] * 2,
    "medium": PUBLIC_PROFILES + SCENE_PROFILES[4:] * 2,
    "hard": PUBLIC_PROFILES + SCENE_PROFILES[4:] * 3,
    "all": PUBLIC_PROFILES + SCENE_PROFILES[4:] * 2,
}

# Preserve the full ARC palette across the generator while keeping exact public
# inputs out of the training stream.  Each public-linked profile excludes only
# its own demonstrated unordered pair; the extrapolation profiles still realize
# those pairs.
_PUBLIC_PALETTES = {
    "p2_n4_h1_edge": frozenset((6, 8)),
    "p2_n5_h2_corner": frozenset((1, 2)),
    "p3_n7_h2_corner": frozenset((2, 5)),
    "p3_n7_h3_corner": frozenset((1, 8)),
}

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "difficulty-weighted periodic-hole profile",
        "valid": (
            "p2_n4_h1_edge|p2_n5_h2_corner|p3_n7_h2_corner|"
            "p3_n7_h3_corner|p2_n5_h3_edge|p2_n4_h2_corner|"
            "p3_n7_h2_edge|p3_n7_h3_edge"
        ),
    },
}

Grid = list[list[int]]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic periodic field with a recoverable hole."""
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {unknown}")
    if (
        isinstance(difficulty, str)
        and difficulty not in {"easy", "medium", "hard"}
    ):
        raise ValueError(f"invalid difficulty: {difficulty!r}")
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    band = (
        difficulty
        if difficulty in {"easy", "medium", "hard"}
        else "all"
    )
    profile = ctx.draw_choice(
        "scene_profile", _PROFILE_WEIGHTS[band]
    )
    spec = SCENE_SPECS[profile]
    layout_rng = ctx.draw_rng(f"periodic_layout_{band}")
    color_rng = ctx.draw_rng(f"periodic_palette_{band}")
    colors = _choose_colors(profile, color_rng)
    origins = _legal_hole_origins(spec)
    if not origins:
        raise RuntimeError(f"no legal hole origin for {profile!r}")

    for _ in range(512):
        if spec.template is None:
            bits = _random_binary_tile(spec.period, layout_rng)
        else:
            bits = _variant_tile(_TEMPLATE_BITS[spec.template], layout_rng)
        tile = [
            [colors[bits[row][col]] for col in range(spec.period)]
            for row in range(spec.period)
        ]
        hole_row, hole_col = layout_rng.choice(origins)
        output = _periodic_patch(
            tile,
            hole_row,
            hole_col,
            spec.hole_size,
        )
        if (
            spec.hole_size > 1
            and len({value for row in output for value in row}) < 2
        ):
            continue
        grid = full_grid(spec.size, spec.size, 0)
        for row in range(spec.size):
            for col in range(spec.size):
                grid[row][col] = tile[
                    row % spec.period
                ][col % spec.period]
        for row in range(hole_row, hole_row + spec.hole_size):
            for col in range(hole_col, hole_col + spec.hole_size):
                grid[row][col] = 0
        analysis = _analyze(grid)
        if (
            analysis["profile"] == profile
            and _profile_tile_matches(analysis)
            and _profile_output_matches(analysis)
        ):
            return grid
    raise RuntimeError(
        f"unable to construct {profile!r} after 512 deterministic attempts"
    )


def solve_python(grid: Grid) -> Grid:
    """Independent Python mirror of the canonical minimal-period rule."""
    height, width = _validate_rectangular_grid(grid)
    zeros = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == 0
    ]
    if not zeros:
        raise ValueError("grid has no zero cells")
    r1 = min(row for row, _ in zeros)
    c1 = min(col for _, col in zeros)
    r2 = max(row for row, _ in zeros)
    c2 = max(col for _, col in zeros)
    period = _find_period(grid)
    if period is None:
        raise ValueError("grid has no canonical period")
    return [
        [
            grid[(r1 + row) % period][(c1 + col) % period]
            for col in range(c2 - c1 + 1)
        ]
        for row in range(r2 - r1 + 1)
    ]


def self_check(grid, *, difficulty=None, meta=None):
    """Recognize the complete returned-grid training grammar."""
    try:
        analysis = _analyze(grid)
    except (TypeError, ValueError) as exc:
        return [str(exc)]
    errors = []
    if analysis["profile"] is None:
        errors.append(
            "dimension/period/hole/boundary tuple is outside the profile set"
        )
    if len(analysis["colors"]) != 2:
        errors.append(
            f"expected exactly two nonzero colors, got {analysis['colors']}"
        )
    if not analysis["solid_square_hole"]:
        errors.append("zeros do not form one solid square hole")
    if analysis["period"] not in {2, 3}:
        errors.append(
            f"expected minimal period 2 or 3, got {analysis['period']}"
        )
    if analysis["reference_tile_erased"]:
        errors.append("top-left period reference tile is erased")
    if any(
        value == 0
        for row in analysis["output"]
        for value in row
    ):
        errors.append("recovered output still contains zero")
    if (
        analysis["hole_size"] > 1
        and len(
            {
                value
                for row in analysis["output"]
                for value in row
            }
        )
        < 2
    ):
        errors.append("multi-cell output collapses to one color")
    if not _profile_tile_matches(analysis):
        errors.append("public-linked profile has the wrong tile morphology")
    if not _profile_output_matches(analysis):
        errors.append("public-linked profile has the wrong output morphology")
    return errors


def observe_overrides(grid):
    """Recover the exact declared scene profile from the returned grid."""
    if self_check(grid):
        return {}
    analysis = _analyze(grid)
    return {"scene_profile": analysis["profile"]}


def canonical_profile_index(grid):
    """Return the linked public-profile index, or ``None``."""
    if self_check(grid):
        return None
    profile = _analyze(grid)["profile"]
    return (
        PUBLIC_PROFILES.index(profile)
        if profile in PUBLIC_PROFILES
        else None
    )


def _analyze(grid: Grid) -> dict:
    height, width = _validate_rectangular_grid(grid)
    colors = sorted({value for row in grid for value in row if value})
    zeros = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == 0
    ]
    if not zeros:
        raise ValueError("grid has no zero cells")
    r1 = min(row for row, _ in zeros)
    c1 = min(col for _, col in zeros)
    r2 = max(row for row, _ in zeros)
    c2 = max(col for _, col in zeros)
    hole_h = r2 - r1 + 1
    hole_w = c2 - c1 + 1
    solid_hole = set(zeros) == {
        (row, col)
        for row in range(r1, r2 + 1)
        for col in range(c1, c2 + 1)
    }
    touched = tuple(
        side
        for side, yes in (
            ("top", r1 == 0),
            ("bottom", r2 == height - 1),
            ("left", c1 == 0),
            ("right", c2 == width - 1),
        )
        if yes
    )
    period = _find_period(grid)
    reference_erased = (
        period is None
        or any(
            grid[row][col] == 0
            for row in range(min(period, height))
            for col in range(min(period, width))
        )
    )
    profile = None
    if (
        height == width
        and hole_h == hole_w
        and period is not None
    ):
        signature = (height, period, hole_h, len(touched))
        profile = _PROFILE_BY_SIGNATURE.get(signature)
    output = solve_python(grid) if period is not None else []
    tile = (
        [
            [grid[row][col] for col in range(period)]
            for row in range(period)
        ]
        if period is not None
        and period <= height
        and period <= width
        else []
    )
    return {
        "height": height,
        "width": width,
        "colors": colors,
        "period": period,
        "hole_origin": (r1, c1),
        "hole_height": hole_h,
        "hole_width": hole_w,
        "hole_size": hole_h if hole_h == hole_w else 0,
        "solid_square_hole": (
            solid_hole
            and hole_h == hole_w
            and hole_h in {1, 2, 3}
        ),
        "boundary_sides": touched,
        "reference_tile_erased": reference_erased,
        "profile": profile,
        "tile_class": _tile_class(tile) if tile else "",
        "output": output,
    }


def _profile_tile_matches(analysis: dict) -> bool:
    profile = analysis["profile"]
    if profile is None:
        return False
    expected = _PUBLIC_TILE_CLASSES.get(profile)
    return expected is None or analysis["tile_class"] == expected


def _profile_output_matches(analysis: dict) -> bool:
    profile = analysis["profile"]
    if profile is None:
        return False
    expected = _PUBLIC_OUTPUT_CLASSES.get(profile)
    return (
        expected is None
        or _tile_class(analysis["output"]) == expected
    )


def _find_period(grid: Grid) -> int | None:
    height, width = _validate_rectangular_grid(grid)
    for period in range(2, height + 1):
        if all(
            grid[row][col] == 0
            or grid[row][col]
            == grid[row % period][col % period]
            for row in range(height)
            for col in range(width)
        ):
            return period
    return None


def _validate_rectangular_grid(grid: Grid) -> tuple[int, int]:
    if not isinstance(grid, list) or not grid:
        raise ValueError("grid must be a non-empty list")
    if not all(isinstance(row, list) and row for row in grid):
        raise ValueError("grid rows must be non-empty lists")
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    for row in grid:
        for value in row:
            if (
                not isinstance(value, int)
                or isinstance(value, bool)
                or not 0 <= value <= 9
            ):
                raise ValueError("grid values must be ARC integers 0..9")
    return len(grid), width


def _legal_hole_origins(spec: SceneSpec) -> tuple[tuple[int, int], ...]:
    origins = []
    limit = spec.size - spec.hole_size
    for row in range(limit + 1):
        for col in range(limit + 1):
            touched = sum(
                (
                    row == 0,
                    row + spec.hole_size == spec.size,
                    col == 0,
                    col + spec.hole_size == spec.size,
                )
            )
            if touched != spec.touched_sides:
                continue
            if row < spec.period and col < spec.period:
                continue
            origins.append((row, col))
    return tuple(origins)


def _periodic_patch(
    tile: Grid,
    row_start: int,
    col_start: int,
    size: int,
) -> Grid:
    period = len(tile)
    return [
        [
            tile[(row_start + row) % period][
                (col_start + col) % period
            ]
            for col in range(size)
        ]
        for row in range(size)
    ]


def _random_binary_tile(period: int, rng) -> list[list[int]]:
    while True:
        tile = [
            [rng.randrange(2) for _ in range(period)]
            for _ in range(period)
        ]
        if len({value for row in tile for value in row}) == 2:
            return tile


def _choose_colors(profile: str, rng) -> list[int]:
    forbidden = _PUBLIC_PALETTES.get(profile)
    pairs = [
        (first, second)
        for first in range(1, 10)
        for second in range(first + 1, 10)
        if frozenset((first, second)) != forbidden
    ]
    colors = list(rng.choice(pairs))
    if rng.randrange(2):
        colors.reverse()
    return colors


def _variant_tile(tile: list[list[int]], rng) -> list[list[int]]:
    result = [row[:] for row in tile]
    for _ in range(rng.randrange(4)):
        result = _rotate_clockwise(result)
    if rng.randrange(2):
        result = [row[::-1] for row in result]
    period = len(result)
    row_shift = rng.randrange(period)
    col_shift = rng.randrange(period)
    return [
        [
            result[(row + row_shift) % period][
                (col + col_shift) % period
            ]
            for col in range(period)
        ]
        for row in range(period)
    ]


def _rotate_clockwise(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*grid[::-1])]


def _tile_class(tile: Grid) -> str:
    if not tile or any(len(row) != len(tile) for row in tile):
        return ""
    colors = sorted({value for row in tile for value in row})
    if len(colors) != 2:
        return ""
    bits = [
        [int(value == colors[1]) for value in row]
        for row in tile
    ]
    period = len(bits)
    candidates = []
    oriented = bits
    for _ in range(4):
        for candidate in (oriented, [row[::-1] for row in oriented]):
            for row_shift in range(period):
                for col_shift in range(period):
                    shifted = [
                        [
                            candidate[
                                (row + row_shift) % period
                            ][(col + col_shift) % period]
                            for col in range(period)
                        ]
                        for row in range(period)
                    ]
                    flattened = "".join(
                        str(value)
                        for row in shifted
                        for value in row
                    )
                    inverse = "".join(
                        str(1 - value)
                        for row in shifted
                        for value in row
                    )
                    candidates.extend((flattened, inverse))
        oriented = _rotate_clockwise(oriented)
    return min(candidates)


_PROFILE_BY_SIGNATURE = {
    (
        spec.size,
        spec.period,
        spec.hole_size,
        spec.touched_sides,
    ): profile
    for profile, spec in SCENE_SPECS.items()
}
_PUBLIC_TILE_CLASSES = {
    profile: _tile_class(_TEMPLATE_BITS[SCENE_SPECS[profile].template])
    for profile in PUBLIC_PROFILES
}
_PUBLIC_OUTPUT_CLASSES = {
    "p2_n4_h1_edge": None,
    "p2_n5_h2_corner": _tile_class([[0, 0], [1, 0]]),
    "p3_n7_h2_corner": _tile_class([[0, 0], [0, 1]]),
    "p3_n7_h3_corner": _tile_class(
        [
            [0, 1, 1],
            [1, 1, 0],
            [1, 0, 1],
        ]
    ),
}
