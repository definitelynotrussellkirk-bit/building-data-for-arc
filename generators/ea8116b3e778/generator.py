"""Generate fourfold reflection-completion scenes around a 2x2 pivot."""

from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "ea8116b3e778"
VERSION = "3.0.0"
RULE_HASH = "4e2d4d62614f"
TASK_ID = "ea8116b3e778"
ALLOW_IDENTITY_OUTPUT = True
SUMMARY = (
    "Reflect every red cell across both axes of the green 2x2 pivot, "
    "completing its four-cell orbit while preserving the pivot."
)

INVARIANTS = [
    "background is 0, the reflected motif is red 2, and the pivot is green 3",
    "the green pivot is exactly one filled 2x2 block",
    "every red orbit is fully in bounds around the pivot center",
    "a lesson consistently shows one, two, or all four members per red orbit",
    "the completed output is the union of all four reflections",
]

PUBLIC_PROFILES = (
    "public_train_1",
    "public_train_2",
    "public_train_3",
    "public_test_1",
)
EXTRAPOLATION_PROFILES = (
    "single_quadrant",
    "half_orbit",
    "complete_orbit",
)
SCENE_PROFILES = PUBLIC_PROFILES + EXTRAPOLATION_PROFILES

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "weighted curriculum",
        "valid": "|".join(SCENE_PROFILES),
    },
}

TRANSFORMS = (
    "identity",
    "rotate_90",
    "rotate_180",
    "rotate_270",
    "horizontal_flip",
    "vertical_flip",
    "main_diagonal",
    "anti_diagonal",
)

# Compact, exact reconstructions of all visible public inputs.  The complete
# red bitmap is retained because arbitrary disconnected red submotifs are
# answer-bearing; translation and D4 are the justified nuisance transforms.
_PUBLIC_SPECS = {
    "public_train_1": {
        "shape": (10, 10),
        "green_top_left": (3, 4),
        "red": (
            (0, 1), (0, 2), (1, 1), (1, 3), (2, 2), (2, 3),
        ),
    },
    "public_train_2": {
        "shape": (20, 30),
        "green_top_left": (7, 9),
        "red": (
            (3, 5), (3, 8), (4, 5), (4, 8), (5, 5),
            (5, 8), (6, 5), (6, 6), (6, 7), (6, 8),
        ),
    },
    "public_train_3": {
        "shape": (12, 14),
        "green_top_left": (4, 5),
        "red": (
            (1, 2), (1, 4), (1, 7), (1, 9),
            (2, 2), (2, 9),
            (3, 2), (3, 3), (3, 4), (3, 7), (3, 8), (3, 9),
            (6, 2), (6, 3), (6, 4), (6, 7), (6, 8), (6, 9),
            (7, 2), (7, 9),
            (8, 2), (8, 4), (8, 7), (8, 9),
        ),
    },
    "public_test_1": {
        "shape": (18, 14),
        "green_top_left": (6, 6),
        "red": (
            (2, 2), (2, 3), (2, 4), (2, 5),
            (3, 3), (4, 4), (5, 4), (5, 5),
        ),
    },
}

# Four public entries out of sixteen give a 25% complete-public prior.  The
# complete-orbit state is deliberately lighter because one public profile
# already supplies the important lawful identity case.
_DEFAULT_PROFILE_POOL = (
    *PUBLIC_PROFILES,
    *(("single_quadrant",) * 5),
    *(("half_orbit",) * 5),
    *(("complete_orbit",) * 2),
)

_CANVASES = {
    "easy": (
        (10, 10), (10, 12), (12, 10), (12, 12), (12, 14), (14, 12),
    ),
    "medium": (
        (14, 16), (16, 14), (16, 18), (18, 16),
        (18, 18), (18, 20), (20, 18),
    ),
    "hard": (
        (20, 24), (24, 20), (20, 30), (30, 20),
        (24, 28), (28, 24), (28, 30), (30, 28), (30, 30),
    ),
}


def _build_scene(shape, green_top_left, red):
    height, width = shape
    grid = full_grid(height, width, 0)
    green_row, green_col = green_top_left
    for row in (green_row, green_row + 1):
        for col in (green_col, green_col + 1):
            grid[row][col] = 3
    for row, col in red:
        if not (0 <= row < height and 0 <= col < width):
            raise ValueError("red cell outside canvas")
        if grid[row][col] != 0:
            raise ValueError("red cell overlaps green pivot")
        grid[row][col] = 2
    return grid


def _transform(grid, name):
    if name == "identity":
        return [row[:] for row in grid]
    if name == "rotate_90":
        return [list(row) for row in zip(*reversed(grid))]
    if name == "rotate_180":
        return [list(reversed(row)) for row in reversed(grid)]
    if name == "rotate_270":
        return [list(row) for row in reversed(list(zip(*grid)))]
    if name == "horizontal_flip":
        return [list(reversed(row)) for row in grid]
    if name == "vertical_flip":
        return [row[:] for row in reversed(grid)]
    if name == "main_diagonal":
        return [list(row) for row in zip(*grid)]
    if name == "anti_diagonal":
        return [list(reversed(row)) for row in reversed(list(zip(*grid)))]
    raise ValueError(f"unknown transform: {name}")


def _translate(grid, delta_row, delta_col):
    height, width = len(grid), len(grid[0])
    result = full_grid(height, width, 0)
    for row in range(height):
        for col in range(width):
            value = grid[row][col]
            if value == 0:
                continue
            target_row = row + delta_row
            target_col = col + delta_col
            if not (0 <= target_row < height and 0 <= target_col < width):
                raise ValueError("translation clips a nonzero cell")
            result[target_row][target_col] = value
    return result


def _occupied_bbox(grid):
    cells = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value != 0
    ]
    if not cells:
        raise ValueError("empty occupied bbox")
    return (
        min(row for row, _ in cells),
        min(col for _, col in cells),
        max(row for row, _ in cells),
        max(col for _, col in cells),
    )


def solve_python(grid):
    """Broad input-pure mirror of the authoritative Racket rule."""
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        raise ValueError("empty grid")
    width = len(grid[0])
    if width == 0 or any(
        not isinstance(row, list) or len(row) != width for row in grid
    ):
        raise ValueError("ragged grid")
    height = len(grid)
    greens = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == 3
    ]
    if not greens:
        raise ValueError("missing green pivot")
    sr = min(row for row, _ in greens) + max(row for row, _ in greens)
    sc = min(col for _, col in greens) + max(col for _, col in greens)
    result = [row[:] for row in grid]
    for row in range(height):
        for col in range(width):
            if grid[row][col] != 0:
                continue
            mirrors = (
                (sr - row, col),
                (row, sc - col),
                (sr - row, sc - col),
            )
            if any(
                0 <= other_row < height
                and 0 <= other_col < width
                and grid[other_row][other_col] == 2
                for other_row, other_col in mirrors
            ):
                result[row][col] = 2
    return result


def _role_signature(grid):
    occupied = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value != 0
    ]
    if not occupied:
        return (len(grid), len(grid[0]), ())
    row1 = min(row for row, _ in occupied)
    row2 = max(row for row, _ in occupied)
    col1 = min(col for _, col in occupied)
    col2 = max(col for _, col in occupied)
    crop = tuple(
        tuple(grid[row][col] for col in range(col1, col2 + 1))
        for row in range(row1, row2 + 1)
    )
    return (len(grid), len(grid[0]), crop)


_PUBLIC_INPUTS = {
    profile: _build_scene(
        spec["shape"],
        spec["green_top_left"],
        spec["red"],
    )
    for profile, spec in _PUBLIC_SPECS.items()
}
_PUBLIC_OUTPUTS = {
    profile: solve_python(grid) for profile, grid in _PUBLIC_INPUTS.items()
}
_PUBLIC_LITERALS = {
    tuple(tuple(row) for row in grid) for grid in _PUBLIC_INPUTS.values()
}
_PUBLIC_LOOKUP = {}
for _profile, _grid in _PUBLIC_INPUTS.items():
    for _transform_name in TRANSFORMS:
        _signature = _role_signature(_transform(_grid, _transform_name))
        _previous = _PUBLIC_LOOKUP.setdefault(_signature, _profile)
        if _previous != _profile:
            raise RuntimeError("ambiguous public profile signatures")


def _public_variant_parameters():
    variants = {}
    for profile in PUBLIC_PROFILES:
        candidates = []
        for transform_name in TRANSFORMS:
            transformed_input = _transform(
                _PUBLIC_INPUTS[profile],
                transform_name,
            )
            transformed_output = _transform(
                _PUBLIC_OUTPUTS[profile],
                transform_name,
            )
            height, width = len(transformed_output), len(transformed_output[0])
            row1, col1, row2, col2 = _occupied_bbox(transformed_output)
            for delta_row in range(-row1, height - row2):
                for delta_col in range(-col1, width - col2):
                    candidate = _translate(
                        transformed_input,
                        delta_row,
                        delta_col,
                    )
                    key = tuple(tuple(row) for row in candidate)
                    if key not in _PUBLIC_LITERALS:
                        candidates.append(
                            (transform_name, delta_row, delta_col)
                        )
        if not candidates:
            raise RuntimeError(f"no nonliteral variants for {profile}")
        variants[profile] = tuple(candidates)
    return variants


_PUBLIC_VARIANTS = _public_variant_parameters()


def _orbit(row, col, sr, sc):
    return frozenset(
        {
            (row, col),
            (sr - row, col),
            (row, sc - col),
            (sr - row, sc - col),
        }
    )


def _analyze(grid):
    reasons = []
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return {"strict": False, "reasons": ["empty"]}
    width = len(grid[0])
    if width == 0 or any(
        not isinstance(row, list) or len(row) != width for row in grid
    ):
        return {"strict": False, "reasons": ["ragged"]}
    height = len(grid)
    if not (8 <= height <= 30 and 8 <= width <= 30):
        reasons.append("dimension_range")
    values = [value for row in grid for value in row]
    if any(
        isinstance(value, bool)
        or not isinstance(value, int)
        or not 0 <= value <= 9
        for value in values
    ):
        return {"strict": False, "reasons": ["invalid_arc_value"]}
    if set(values) != {0, 2, 3}:
        reasons.append("palette_roles")
    reds = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == 2
    }
    greens = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == 3
    }
    if len(greens) != 4:
        reasons.append("green_count")
        return {
            "strict": False,
            "reasons": reasons,
            "dimensions": f"{height}x{width}",
            "red_count": len(reds),
            "green_count": len(greens),
        }
    row1 = min(row for row, _ in greens)
    row2 = max(row for row, _ in greens)
    col1 = min(col for _, col in greens)
    col2 = max(col for _, col in greens)
    expected_green = {
        (row1, col1),
        (row1, col2),
        (row2, col1),
        (row2, col2),
    }
    if (
        row2 - row1 != 1
        or col2 - col1 != 1
        or greens != expected_green
    ):
        reasons.append("green_not_2x2")
    sr, sc = row1 + row2, col1 + col2
    orbit_counts = {}
    clipped = False
    for row, col in reds:
        orbit = _orbit(row, col, sr, sc)
        if any(
            not (0 <= other_row < height and 0 <= other_col < width)
            for other_row, other_col in orbit
        ):
            clipped = True
        orbit_counts[orbit] = len(reds & orbit)
    if clipped:
        reasons.append("clipped_orbit")
    base_size = len(orbit_counts)
    if not 4 <= base_size <= 14:
        reasons.append("base_size")
    multiplicities = set(orbit_counts.values())
    if len(multiplicities) != 1 or not multiplicities <= {1, 2, 4}:
        state = "mixed"
        reasons.append("mixed_orbit_occupancy")
    else:
        multiplicity = next(iter(multiplicities), 0)
        state = {
            1: "single_quadrant",
            2: "half_orbit",
            4: "complete_orbit",
        }.get(multiplicity, "mixed")
    if state == "single_quadrant":
        quadrants = {
            (
                "top" if 2 * row < sr else "bottom",
                "left" if 2 * col < sc else "right",
            )
            for row, col in reds
        }
        if len(quadrants) != 1:
            reasons.append("single_quadrant_geometry")
    elif state == "half_orbit":
        horizontal = {(sr - row, col) for row, col in reds} == reds
        vertical = {(row, sc - col) for row, col in reds} == reds
        if horizontal == vertical:
            reasons.append("half_orbit_axis")
    answer_profile = _PUBLIC_LOOKUP.get(_role_signature(grid))
    scene_profile = answer_profile or state
    expected = solve_python(grid)
    return {
        "strict": not reasons,
        "reasons": reasons,
        "dimensions": f"{height}x{width}",
        "red_count": len(reds),
        "green_count": len(greens),
        "base_size": base_size,
        "orbit_state": state,
        "scene_profile": scene_profile,
        "answer_profile": answer_profile,
        "identity": expected == grid,
        "output_red_count": sum(
            value == 2 for row in expected for value in row
        ),
    }


def self_check(grid, *, difficulty=None, meta=None):
    """Return strict final-grid curriculum violations."""
    return _analyze(grid)["reasons"]


def observe_overrides(grid):
    """Recover the exact declared profile from returned pixels."""
    analysis = _analyze(grid)
    if not analysis["strict"]:
        raise ValueError(
            "cannot observe scene_profile on invalid grid: "
            + ",".join(analysis["reasons"])
        )
    return {"scene_profile": analysis["scene_profile"]}


def _generate_bitmap(rng, size, max_rows, max_cols):
    candidates = [
        (row, col)
        for row in range(1, max_rows + 1)
        for col in range(1, max_cols + 1)
    ]
    if len(candidates) < size:
        raise ValueError("motif box too small")
    for _ in range(50):
        chosen = set(rng.sample(candidates, size))
        if (
            len({row for row, _ in chosen}) >= 2
            and len({col for _, col in chosen}) >= 2
        ):
            return chosen
    raise ValueError("could not generate a two-dimensional motif")


def _generate_control(rng, profile, difficulty):
    band = difficulty if difficulty in _CANVASES else "medium"
    height, width = rng.choice(_CANVASES[band])
    size_ranges = {
        "easy": (4, 6),
        "medium": (6, 10),
        "hard": (8, 14),
    }
    size = rng.randint(*size_ranges[band])
    max_fit_rows = min(6, (height - 2) // 2)
    max_fit_cols = min(6, (width - 2) // 2)
    boxes = [
        (rows, cols)
        for rows in range(2, max_fit_rows + 1)
        for cols in range(2, max_fit_cols + 1)
        if rows * cols >= size
    ]
    box_rows, box_cols = rng.choice(boxes)
    offsets = _generate_bitmap(rng, size, box_rows, box_cols)
    pivot_row = rng.randint(box_rows, height - 2 - box_rows)
    pivot_col = rng.randint(box_cols, width - 2 - box_cols)
    base = {
        (pivot_row - delta_row, pivot_col - delta_col)
        for delta_row, delta_col in offsets
    }
    sr, sc = 2 * pivot_row + 1, 2 * pivot_col + 1
    if profile == "single_quadrant":
        reds = set(base)
    elif profile == "half_orbit":
        if rng.choice((False, True)):
            reds = base | {(sr - row, col) for row, col in base}
        else:
            reds = base | {(row, sc - col) for row, col in base}
    elif profile == "complete_orbit":
        reds = set().union(
            *(_orbit(row, col, sr, sc) for row, col in base)
        )
    else:
        raise ValueError(f"unknown control profile: {profile}")
    grid = _build_scene(
        (height, width),
        (pivot_row, pivot_col),
        reds,
    )
    return _transform(grid, rng.choice(TRANSFORMS))


def _generate_public(rng, profile):
    transform_name, delta_row, delta_col = rng.choice(
        _PUBLIC_VARIANTS[profile]
    )
    transformed = _transform(_PUBLIC_INPUTS[profile], transform_name)
    return _translate(transformed, delta_row, delta_col)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic fourfold-completion lesson."""
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = ctx.draw_choice("scene_profile", _DEFAULT_PROFILE_POOL)
    rng = ctx.draw_rng("layout")
    if profile in PUBLIC_PROFILES:
        grid = _generate_public(rng, profile)
        if _analyze(grid)["scene_profile"] != profile:
            raise RuntimeError("public profile lost during nuisance transform")
        return grid
    for _ in range(30):
        grid = _generate_control(rng, profile, difficulty)
        analysis = _analyze(grid)
        if analysis["strict"] and analysis["scene_profile"] == profile:
            return grid
    raise ValueError(f"could not construct profile {profile!r}")
