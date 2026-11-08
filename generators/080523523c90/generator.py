"""Generate full diagonals that determine a three-color stripe tiling."""

from __future__ import annotations

from functools import lru_cache
from itertools import combinations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "080523523c90"
VERSION = "3.1.0"
RULE_HASH = "5f07af88af10"
TASK_ID = "080523523c90"
SUMMARY = (
    "Read the common nonzero color on the complete diagonals belonging to "
    "each (row + column) modulo-three residue, then fill the grid with "
    "those three diagonal stripe colors."
)

INVARIANTS = [
    "background is 0 and all three input colors are nonzero and distinct",
    "the input contains three, four, or six complete constant-(row+column) lines",
    "the selected lines cover residues 0, 1, and 2 at least once",
    "all complete lines in one residue share one uniform residue color",
    "the output fills every cell from its (row+column) modulo-three color",
]

PUBLIC_PROFILES = (
    "public_train_1",
    "public_train_2",
    "public_train_3",
    "public_test_1",
)
EXTRAPOLATION_PROFILES = (
    "contiguous_band",
    "paired_gap",
    "spread_lines",
)
REDUNDANCY_PROFILES = (
    "one_residue_repeated",
    "all_residues_repeated",
)
SCENE_PROFILES = (
    PUBLIC_PROFILES
    + EXTRAPOLATION_PROFILES
    + REDUNDANCY_PROFILES
)

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "weighted curriculum",
        "valid": "|".join(SCENE_PROFILES),
    },
}

# Each public input consists of three complete anti-diagonals. Colors are
# stored by output residue rather than selected-line order.
_PUBLIC_SPECS = {
    "public_train_1": {
        "shape": (7, 7),
        "sums": (8, 9, 10),
        "canonical_residue_colors": (2, 4, 1),
    },
    "public_train_2": {
        "shape": (7, 7),
        "sums": (0, 1, 2),
        "canonical_residue_colors": (2, 8, 3),
    },
    "public_train_3": {
        "shape": (7, 7),
        "sums": (4, 5, 9),
        "canonical_residue_colors": (4, 8, 3),
    },
    "public_test_1": {
        "shape": (7, 7),
        "sums": (1, 6, 11),
        "canonical_residue_colors": (2, 1, 4),
    },
}

# Sixteen public entries out of sixty-four preserve the calibrated 25%
# public prior. The canonical morphology is connected, so contiguous bands
# dominate the unforced curriculum; sparse spacing and repeated-line profiles
# remain reachable by default and are exhaustively available as overrides.
_DEFAULT_PROFILE_POOL = (
    *PUBLIC_PROFILES,
    *PUBLIC_PROFILES,
    *PUBLIC_PROFILES,
    *PUBLIC_PROFILES,
    *(("contiguous_band",) * 40),
    *(("paired_gap",) * 3),
    *(("spread_lines",) * 2),
    *(("one_residue_repeated",) * 2),
    "all_residues_repeated",
)

_CANVASES = {
    "easy": tuple(
        (height, width)
        for height in range(5, 9)
        for width in range(5, 9)
    ),
    "medium": tuple(
        (height, width)
        for height in range(7, 12)
        for width in range(7, 12)
    ),
    "hard": tuple(
        (height, width)
        for height in range(10, 16)
        for width in range(10, 16)
    ),
}


def _normalized_sums(height, width, selected_sums):
    values = tuple(sorted(selected_sums))
    max_sum = height + width - 2
    reflected = tuple(sorted(max_sum - value for value in values))
    return min(values, reflected)


_PUBLIC_SIGNATURES = {
    (
        spec["shape"][0],
        spec["shape"][1],
        _normalized_sums(*spec["shape"], spec["sums"]),
    ): profile
    for profile, spec in _PUBLIC_SPECS.items()
}


def _line_cells(height, width, diagonal_sum):
    return [
        (row, diagonal_sum - row)
        for row in range(height)
        if 0 <= diagonal_sum - row < width
    ]


def _build_scene(height, width, selected_sums, colors_by_residue):
    grid = full_grid(height, width, 0)
    for diagonal_sum in selected_sums:
        color = colors_by_residue[diagonal_sum % 3]
        for row, col in _line_cells(height, width, diagonal_sum):
            grid[row][col] = color
    return grid


def _draw_repeated_sums(rng, height, width, profile):
    """Draw answer-equivalent repeated lines with an observable multiplicity."""
    max_sum = height + width - 2
    by_residue = {
        residue: [
            value
            for value in range(max_sum + 1)
            if value % 3 == residue
        ]
        for residue in range(3)
    }
    if profile == "one_residue_repeated":
        repeated = rng.choice((0, 1, 2))
        selected = []
        for residue in range(3):
            count = 2 if residue == repeated else 1
            selected.extend(rng.sample(by_residue[residue], count))
        return tuple(sorted(selected))
    if profile == "all_residues_repeated":
        selected = []
        for residue in range(3):
            selected.extend(rng.sample(by_residue[residue], 2))
        return tuple(sorted(selected))
    raise ValueError(f"not a repeated-line profile: {profile}")


def _public_literal(profile, selected_sums, colors_by_residue):
    spec = _PUBLIC_SPECS[profile]
    return (
        tuple(selected_sums) == tuple(spec["sums"])
        and tuple(colors_by_residue)
        == tuple(spec["canonical_residue_colors"])
    )


@lru_cache(maxsize=None)
def _candidate_sums(height, width, profile):
    max_sum = height + width - 2
    candidates = []
    for values in combinations(range(max_sum + 1), 3):
        if {value % 3 for value in values} != {0, 1, 2}:
            continue
        signature = (
            height,
            width,
            _normalized_sums(height, width, values),
        )
        if signature in _PUBLIC_SIGNATURES:
            continue
        gaps = (values[1] - values[0], values[2] - values[1])
        if profile == "contiguous_band" and gaps != (1, 1):
            continue
        if profile == "paired_gap" and (
            1 not in gaps or gaps == (1, 1)
        ):
            continue
        if profile == "spread_lines" and min(gaps) < 2:
            continue
        candidates.append(values)
    return tuple(candidates)


def solve_python(grid):
    """Input-pure Python mirror of the broad authoritative Racket rule."""
    if not isinstance(grid, list) or not grid:
        raise ValueError("empty grid")
    if not all(isinstance(row, list) for row in grid):
        raise ValueError("rows must be lists")
    width = len(grid[0])
    if width == 0 or any(len(row) != width for row in grid):
        raise ValueError("ragged grid")
    if any(
        isinstance(value, bool)
        or not isinstance(value, int)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        raise ValueError("invalid ARC value")

    colors = {}
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            residue = (row + col) % 3
            if value != 0 and residue not in colors:
                colors[residue] = value
    if set(colors) != {0, 1, 2}:
        raise ValueError("missing nonzero seed for a residue")
    return [
        [colors[(row + col) % 3] for col in range(width)]
        for row in range(len(grid))
    ]


def _analyze(grid):
    reasons = []
    if not isinstance(grid, list) or not grid:
        return {"reasons": ["empty"], "scene_profile": "invalid"}
    if not all(isinstance(row, list) for row in grid):
        return {"reasons": ["row_type"], "scene_profile": "invalid"}
    width = len(grid[0])
    if width == 0 or any(len(row) != width for row in grid):
        return {"reasons": ["ragged"], "scene_profile": "invalid"}
    if any(
        isinstance(value, bool)
        or not isinstance(value, int)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return {
            "reasons": ["invalid_arc_value"],
            "scene_profile": "invalid",
        }

    height = len(grid)
    selected_sums = sorted({
        row + col
        for row in range(height)
        for col in range(width)
        if grid[row][col] != 0
    })
    if len(selected_sums) not in (3, 4, 6):
        reasons.append("line_count")

    colors = {}
    for diagonal_sum in selected_sums:
        values = [
            grid[row][col]
            for row, col in _line_cells(height, width, diagonal_sum)
        ]
        if any(value == 0 for value in values):
            reasons.append("incomplete_line")
        nonzero = {value for value in values if value != 0}
        if len(nonzero) != 1:
            reasons.append("nonuniform_line")
        elif values and all(value != 0 for value in values):
            colors[diagonal_sum] = next(iter(nonzero))

    residue_line_counts = {
        residue: sum(value % 3 == residue for value in selected_sums)
        for residue in range(3)
    }
    if set(
        value % 3 for value in selected_sums
    ) != {0, 1, 2}:
        reasons.append("residue_coverage")

    residue_colors = {}
    for residue in range(3):
        values = {
            colors[diagonal_sum]
            for diagonal_sum in selected_sums
            if diagonal_sum in colors and diagonal_sum % 3 == residue
        }
        if len(values) > 1:
            reasons.append("residue_color_conflict")
        elif len(values) == 1:
            residue_colors[residue] = next(iter(values))
    if len(residue_colors) == 3 and len(set(residue_colors.values())) != 3:
        reasons.append("color_alias")

    multiplicities = sorted(residue_line_counts.values())
    expected_multiplicities = {
        3: [1, 1, 1],
        4: [1, 1, 2],
        6: [2, 2, 2],
    }
    if (
        len(selected_sums) in expected_multiplicities
        and multiplicities != expected_multiplicities[len(selected_sums)]
    ):
        reasons.append("line_multiplicity")
    reasons = sorted(set(reasons))

    if len(selected_sums) == 4:
        structural_profile = "one_residue_repeated"
    elif len(selected_sums) == 6:
        structural_profile = "all_residues_repeated"
    else:
        gaps = tuple(
            right - left
            for left, right in zip(selected_sums, selected_sums[1:])
        )
        if gaps == (1, 1):
            structural_profile = "contiguous_band"
        elif 1 in gaps:
            structural_profile = "paired_gap"
        else:
            structural_profile = "spread_lines"
    if len(selected_sums) == 3:
        signature = (
            height,
            width,
            _normalized_sums(height, width, selected_sums),
        )
        scene_profile = _PUBLIC_SIGNATURES.get(
            signature, structural_profile
        )
    else:
        scene_profile = structural_profile
    if reasons:
        scene_profile = "invalid"
    return {
        "reasons": reasons,
        "scene_profile": scene_profile,
        "height": height,
        "width": width,
        "selected_sums": selected_sums,
        "residue_line_counts": residue_line_counts,
        "residue_colors": residue_colors,
        "line_lengths": [
            len(_line_cells(height, width, value))
            for value in selected_sums
        ],
        "seed_count": sum(
            value != 0 for row in grid for value in row
        ),
    }


def self_check(grid, *, difficulty=None, meta=None):
    """Validate the demonstrated full-line training grammar from final pixels."""
    del difficulty, meta
    return _analyze(grid)["reasons"]


def semantic_observables(grid):
    """Return task-linked coverage facts recoverable from the final pixels."""
    info = _analyze(grid)
    return {
        "scene_profile": info["scene_profile"],
        "shape": (info.get("height"), info.get("width")),
        "selected_sums": tuple(info.get("selected_sums", ())),
        "residue_line_counts": tuple(
            info.get("residue_line_counts", {}).get(residue, 0)
            for residue in range(3)
        ),
        "residue_colors": tuple(
            info.get("residue_colors", {}).get(residue)
            for residue in range(3)
        ),
        "seed_count": info.get("seed_count", 0),
    }


def observe_overrides(grid):
    """Recover the only declared axis from the returned grid."""
    info = _analyze(grid)
    return {"scene_profile": info["scene_profile"]}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown overrides: {unknown}")
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = ctx.draw_choice(
        "scene_profile", list(_DEFAULT_PROFILE_POOL)
    )
    rng = ctx.draw_rng("scene")
    # Keep palette sampling on the scene RNG so existing seed-to-geometry
    # trajectories remain stable; the sample is already distinct/nonzero.
    colors_by_residue = rng.sample(range(1, 10), 3)

    if profile in PUBLIC_PROFILES:
        spec = _PUBLIC_SPECS[profile]
        height, width = spec["shape"]
        selected_sums = tuple(spec["sums"])
        if rng.choice((False, True)):
            max_sum = height + width - 2
            selected_sums = tuple(
                sorted(max_sum - value for value in selected_sums)
            )
        if _public_literal(
            profile, selected_sums, colors_by_residue
        ):
            colors_by_residue[0], colors_by_residue[1] = (
                colors_by_residue[1],
                colors_by_residue[0],
            )
    else:
        band = (
            difficulty
            if difficulty in ("easy", "hard")
            else "medium"
        )
        height, width = rng.choice(_CANVASES[band])
        if profile in REDUNDANCY_PROFILES:
            selected_sums = _draw_repeated_sums(
                rng, height, width, profile
            )
        else:
            candidates = _candidate_sums(height, width, profile)
            if not candidates:
                raise ValueError(
                    f"no {profile} line sets for {height}x{width}"
                )
            selected_sums = rng.choice(candidates)

    grid = _build_scene(
        height,
        width,
        selected_sums,
        colors_by_residue,
    )
    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise ValueError(f"constructed invalid scene: {errors}")
    return grid
