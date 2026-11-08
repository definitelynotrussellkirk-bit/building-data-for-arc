"""Generate terrain-profile reflection scenes for 6d33e42a400d.

A sparse line of paint markers is paired with a parallel source-color
anchor line.  The connected source terrain on the marker line's outer
side is copied, in the paint color, beyond the anchor line.
"""

from __future__ import annotations

from collections import Counter

from puzzle_generators.base import gen_ctx


GENERATOR_ID = "6d33e42a400d"
TASK_ID = "6d33e42a400d"
VERSION = "2.0.0"
RULE_HASH = "d5de5966b074"
SUMMARY = (
    "Copy the connected source terrain across the paired marker/anchor "
    "lines, recoloring the copy with the sparse marker color."
)

INVARIANTS = [
    "one modal background and two unequal non-background color roles",
    "5..8 regularly spaced paint markers lie on one row or column",
    "a parallel source anchor line has exactly the same orthogonal coordinates",
    "one connected source terrain spans the canvas outside the marker line",
    "the terrain copy fits beyond the anchor line and uses the paint color",
]

PUBLIC_PROFILES = (
    "public_h8",
    "public_v8",
    "public_v6",
)
EXTRAPOLATION_PROFILES = (
    "shallow_steps",
    "medium_steps",
    "deep_steps",
)
SCENE_PROFILES = PUBLIC_PROFILES + EXTRAPOLATION_PROFILES

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "weighted rng across all complete profiles",
        "valid": "|".join(SCENE_PROFILES),
    },
    "orientation": {
        "type": "int",
        "default": "rng 0..3; literal public orientation excluded",
        "valid": "0..3",
    },
}

_WEIGHTED_PROFILES = {
    "easy": (
        *PUBLIC_PROFILES,
        *(("shallow_steps",) * 5),
        *(("medium_steps",) * 3),
        "deep_steps",
    ),
    "medium": (
        *PUBLIC_PROFILES,
        *(("shallow_steps",) * 3),
        *(("medium_steps",) * 3),
        *(("deep_steps",) * 3),
    ),
    "hard": (
        *PUBLIC_PROFILES,
        "shallow_steps",
        *(("medium_steps",) * 3),
        *(("deep_steps",) * 5),
    ),
}

# The three normalized public inputs, represented compactly by geometry.
# Role colors are 0=background, 1=source, and 2=paint marker.
_PUBLIC_SPECS = {
    "public_h8": {
        "axis": "horizontal",
        "marker_line": 5,
        "target_line": 11,
        "marker_coords": (0, 3, 6, 9, 12, 15, 18, 21),
        "terrain": (
            (1, 9),
            (1, 10),
            (1, 11),
            (1, 12),
            (2, 9),
            (2, 12),
            (3, 3),
            (3, 4),
            (3, 5),
            (3, 6),
            (3, 9),
            (3, 12),
            (3, 15),
            (3, 16),
            (3, 17),
            (3, 18),
            (4, 0),
            (4, 1),
            (4, 2),
            (4, 3),
            (4, 6),
            (4, 7),
            (4, 8),
            (4, 9),
            (4, 12),
            (4, 13),
            (4, 14),
            (4, 15),
            (4, 18),
            (4, 19),
            (4, 20),
            (4, 21),
        ),
    },
    "public_v8": {
        "axis": "vertical",
        "marker_line": 4,
        "target_line": 10,
        "marker_coords": (0, 3, 6, 9, 12, 15, 18, 21),
        "terrain": (
            (0, 3),
            (1, 3),
            (2, 1),
            (2, 2),
            (2, 3),
            (3, 1),
            (4, 1),
            (4, 2),
            (4, 3),
            (5, 3),
            (6, 2),
            (6, 3),
            (7, 2),
            (7, 3),
            (8, 3),
            (9, 1),
            (9, 2),
            (9, 3),
            (10, 1),
            (11, 1),
            (12, 1),
            (12, 2),
            (12, 3),
            (13, 2),
            (13, 3),
            (14, 2),
            (15, 2),
            (15, 3),
            (16, 3),
            (17, 1),
            (17, 2),
            (17, 3),
            (18, 1),
            (19, 1),
            (19, 2),
            (20, 2),
            (21, 2),
            (21, 3),
        ),
    },
    "public_v6": {
        "axis": "vertical",
        "marker_line": 8,
        "target_line": 14,
        "marker_coords": (0, 4, 8, 12, 16, 20),
        "terrain": (
            (0, 5),
            (0, 6),
            (0, 7),
            (1, 5),
            (2, 4),
            (2, 5),
            (3, 5),
            (4, 5),
            (4, 6),
            (4, 7),
            (5, 7),
            (6, 6),
            (6, 7),
            (7, 6),
            (7, 7),
            (8, 7),
            (9, 7),
            (10, 7),
            (11, 7),
            (12, 2),
            (12, 3),
            (12, 4),
            (12, 5),
            (12, 6),
            (12, 7),
            (13, 2),
            (14, 2),
            (15, 2),
            (16, 2),
            (16, 3),
            (16, 4),
            (16, 5),
            (16, 6),
            (16, 7),
            (17, 7),
            (18, 6),
            (18, 7),
            (19, 6),
            (20, 6),
            (20, 7),
            (21, 7),
        ),
    },
}

_PROFILE_PARAMETERS = {
    "shallow_steps": {
        "max_depth": 3,
        "period": 3,
        "gap": 5,
        "sizes": {"easy": 20, "medium": 21, "hard": 22},
    },
    "medium_steps": {
        "max_depth": 4,
        "period": 3,
        "gap": 6,
        "sizes": {"easy": 21, "medium": 22, "hard": 23},
    },
    "deep_steps": {
        "max_depth": 6,
        "period": 4,
        "gap": 6,
        "sizes": {"easy": 22, "medium": 23, "hard": 24},
    },
}


def _empty_grid(height, width, value=0):
    return [[value for _ in range(width)] for _ in range(height)]


def _rotate90(grid):
    return [
        [grid[len(grid) - 1 - row][col] for row in range(len(grid))]
        for col in range(len(grid[0]))
    ]


def _rotations(grid):
    transformed = []
    current = [row[:] for row in grid]
    for _ in range(4):
        transformed.append([row[:] for row in current])
        current = _rotate90(current)
    return tuple(transformed)


def _reflect(grid):
    return [list(reversed(row)) for row in grid]


def _d4(grid):
    transformed = []
    current = [row[:] for row in grid]
    for _ in range(4):
        transformed.append([row[:] for row in current])
        transformed.append(_reflect(current))
        current = _rotate90(current)
    return tuple(transformed)


def _grid_key(grid):
    return tuple(tuple(row) for row in grid)


def _rotation_canonical(grid):
    return min(_rotations(grid), key=_grid_key)


def _build_public_roles(profile):
    spec = _PUBLIC_SPECS[profile]
    grid = _empty_grid(22, 22)
    for row, col in spec["terrain"]:
        grid[row][col] = 1
    marker_line = spec["marker_line"]
    target_line = spec["target_line"]
    for coordinate in spec["marker_coords"]:
        if spec["axis"] == "horizontal":
            grid[marker_line][coordinate] = 2
            grid[target_line][coordinate] = 1
        else:
            grid[coordinate][marker_line] = 2
            grid[coordinate][target_line] = 1
    return grid


_PUBLIC_ROLE_GRIDS = {
    profile: _build_public_roles(profile) for profile in PUBLIC_PROFILES
}
_PUBLIC_PROFILE_LOOKUP = {}
for _profile, _grid in _PUBLIC_ROLE_GRIDS.items():
    for _transformed in _d4(_grid):
        _PUBLIC_PROFILE_LOOKUP[_grid_key(_transformed)] = _profile


def _role_info(grid):
    counts = Counter(value for row in grid for value in row)
    if len(counts) != 3:
        return None
    ranked = counts.most_common()
    if ranked[0][1] == ranked[1][1]:
        return None
    background = ranked[0][0]
    colors = [value for value in counts if value != background]
    if counts[colors[0]] == counts[colors[1]]:
        return None
    source = max(colors, key=counts.get)
    paint = min(colors, key=counts.get)
    return background, source, paint, counts


def _normalize_roles(grid):
    info = _role_info(grid)
    if info is None:
        return None
    background, source, paint, _ = info
    role = {background: 0, source: 1, paint: 2}
    return [[role[value] for value in row] for row in grid]


def _canonical_answer_profile(grid):
    normalized = _normalize_roles(grid)
    if normalized is None:
        return None
    return _PUBLIC_PROFILE_LOOKUP.get(_grid_key(normalized))


def _components4(cells):
    cells = set(cells)
    seen = set()
    components = []
    for start in sorted(cells):
        if start in seen:
            continue
        stack = [start]
        seen.add(start)
        component = set()
        while stack:
            row, col = stack.pop()
            component.add((row, col))
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                neighbor = (row + dr, col + dc)
                if neighbor in cells and neighbor not in seen:
                    seen.add(neighbor)
                    stack.append(neighbor)
        components.append(component)
    return components


def _find_geometry(grid, source, paint):
    height, width = len(grid), len(grid[0])
    markers = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == paint
    ]
    if not markers:
        return None
    marker_rows = {row for row, _ in markers}
    marker_cols = {col for _, col in markers}
    if len(marker_rows) == 1:
        axis = "horizontal"
        marker_line = next(iter(marker_rows))
        marker_coords = tuple(sorted(col for _, col in markers))
        candidates = [
            row
            for row in range(height)
            if row != marker_line
            and tuple(
                col for col in range(width) if grid[row][col] == source
            )
            == marker_coords
        ]
    elif len(marker_cols) == 1:
        axis = "vertical"
        marker_line = next(iter(marker_cols))
        marker_coords = tuple(sorted(row for row, _ in markers))
        candidates = [
            col
            for col in range(width)
            if col != marker_line
            and tuple(
                row for row in range(height) if grid[row][col] == source
            )
            == marker_coords
        ]
    else:
        return None
    return {
        "axis": axis,
        "marker_line": marker_line,
        "marker_coords": marker_coords,
        "target_candidates": tuple(candidates),
        "markers": tuple(markers),
    }


def _analyze(grid):
    reasons = []
    if (
        not isinstance(grid, list)
        or not grid
        or not isinstance(grid[0], list)
        or not grid[0]
    ):
        return {"strict": False, "reasons": ["empty_or_non_grid"]}
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        return {"strict": False, "reasons": ["ragged"]}
    if any(
        isinstance(value, bool)
        or not isinstance(value, int)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return {"strict": False, "reasons": ["invalid_arc_value"]}

    height = len(grid)
    if not (20 <= height <= 24 and height == width):
        reasons.append("dimension_range_or_square")
    info = _role_info(grid)
    if info is None:
        reasons.append("role_color_counts")
        return {"strict": False, "reasons": reasons}
    background, source, paint, counts = info
    if counts[background] <= height * width * 3 // 4:
        reasons.append("background_not_dominant")
    geometry = _find_geometry(grid, source, paint)
    if geometry is None:
        reasons.append("paint_markers_not_aligned")
        return {"strict": False, "reasons": reasons}

    marker_coords = geometry["marker_coords"]
    marker_count = len(marker_coords)
    if not 5 <= marker_count <= 8:
        reasons.append("marker_count")
    steps = tuple(
        second - first
        for first, second in zip(marker_coords, marker_coords[1:])
    )
    marker_period = steps[0] if steps and len(set(steps)) == 1 else None
    if marker_period not in (3, 4):
        reasons.append("marker_period")
    orth_size = width if geometry["axis"] == "horizontal" else height
    if marker_coords and not (
        marker_coords[0] == 0 or marker_coords[-1] == orth_size - 1
    ):
        reasons.append("marker_boundary_attachment")
    if len(geometry["target_candidates"]) != 1:
        reasons.append("target_line_count")
        return {
            "strict": False,
            "reasons": reasons,
            "axis": geometry["axis"],
            "marker_count": marker_count,
            "marker_period": marker_period,
        }

    marker_line = geometry["marker_line"]
    target_line = geometry["target_candidates"][0]
    line_gap = abs(target_line - marker_line)
    if not 5 <= line_gap <= 7:
        reasons.append("line_gap")
    source_cells = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == source
    }
    anchors = (
        {(target_line, coordinate) for coordinate in marker_coords}
        if geometry["axis"] == "horizontal"
        else {(coordinate, target_line) for coordinate in marker_coords}
    )
    if geometry["axis"] == "horizontal":
        terrain = {
            (row, col)
            for row, col in source_cells
            if (
                row < marker_line
                if target_line > marker_line
                else row > marker_line
            )
        }
        orth_values = {col for _, col in terrain}
        depths = {abs(row - marker_line) for row, _ in terrain}
        destinations = {
            (target_line + marker_line - row, col)
            for row, col in terrain
        }
    else:
        terrain = {
            (row, col)
            for row, col in source_cells
            if (
                col < marker_line
                if target_line > marker_line
                else col > marker_line
            )
        }
        orth_values = {row for row, _ in terrain}
        depths = {abs(col - marker_line) for _, col in terrain}
        destinations = {
            (row, target_line + marker_line - col)
            for row, col in terrain
        }
    if source_cells != terrain | anchors:
        reasons.append("unexpected_source_cells")
    terrain_components = _components4(terrain)
    if len(terrain_components) != 1:
        reasons.append("terrain_component_count")
    if orth_values != set(range(orth_size)):
        reasons.append("terrain_not_full_span")
    max_depth = max(depths, default=0)
    if not 3 <= max_depth <= 6:
        reasons.append("terrain_depth")
    terrain_size = len(terrain)
    change_fraction = terrain_size / (height * width)
    if not 0.05 <= change_fraction <= 0.13:
        reasons.append("terrain_density")
    if len(destinations) != terrain_size or any(
        not (0 <= row < height and 0 <= col < width)
        for row, col in destinations
    ):
        reasons.append("copy_out_of_bounds_or_collapsed")
    elif any(grid[row][col] != background for row, col in destinations):
        reasons.append("copy_destination_occupied")

    answer_profile = _canonical_answer_profile(grid)
    if answer_profile is not None:
        scene_profile = answer_profile
    elif max_depth <= 3:
        scene_profile = "shallow_steps"
    elif max_depth <= 4:
        scene_profile = "medium_steps"
    else:
        scene_profile = "deep_steps"
    return {
        "strict": not reasons,
        "reasons": reasons,
        "height": height,
        "width": width,
        "background": background,
        "source": source,
        "paint": paint,
        "palette": tuple(sorted(counts)),
        "axis": geometry["axis"],
        "marker_line": marker_line,
        "target_line": target_line,
        "line_gap": line_gap,
        "marker_count": marker_count,
        "marker_period": marker_period,
        "terrain_size": terrain_size,
        "max_depth": max_depth,
        "change_fraction": change_fraction,
        "source_component_count": len(_components4(source_cells)),
        "paint_component_count": len(_components4(geometry["markers"])),
        "canonical_answer_profile": answer_profile,
        "scene_profile": scene_profile,
    }


def self_check(grid, *, difficulty=None, meta=None):
    """Validate the calibrated lesson from the returned grid alone."""
    return _analyze(grid)["reasons"]


def solve_python(grid):
    """Input-pure Python mirror of the canonical marker/terrain rule."""
    if (
        not isinstance(grid, list)
        or not grid
        or not isinstance(grid[0], list)
        or not grid[0]
    ):
        raise ValueError("grid must be nonempty")
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    info = _role_info(grid)
    if info is None:
        raise ValueError("grid must have one modal and two unequal role colors")
    _, source, paint, _ = info
    geometry = _find_geometry(grid, source, paint)
    if geometry is None or not geometry["target_candidates"]:
        raise ValueError("marker and target lines not found")
    marker_line = geometry["marker_line"]
    target_line = geometry["target_candidates"][0]
    source_cells = [
        (row, col)
        for row in range(len(grid))
        for col in range(width)
        if grid[row][col] == source
    ]
    output = [row[:] for row in grid]
    if geometry["axis"] == "horizontal":
        direction = -1 if target_line > marker_line else 1
        for row, col in source_cells:
            sign = -1 if row < marker_line else 1 if row > marker_line else 0
            if sign != direction:
                continue
            new_row = target_line + marker_line - row
            if 0 <= new_row < len(grid):
                output[new_row][col] = paint
    else:
        direction = -1 if target_line > marker_line else 1
        for row, col in source_cells:
            sign = -1 if col < marker_line else 1 if col > marker_line else 0
            if sign != direction:
                continue
            new_col = target_line + marker_line - col
            if 0 <= new_col < width:
                output[row][new_col] = paint
    return output


def _terrain_polyline(size, marker_coords, max_depth, rng):
    for _ in range(120):
        segment_depths = [
            rng.randint(1, max_depth) for _ in marker_coords
        ]
        eligible_max = list(range(max(1, len(segment_depths) - 1)))
        max_index = rng.choice(eligible_max)
        segment_depths[max_index] = max_depth
        one_choices = [
            index
            for index in range(len(segment_depths))
            if index != max_index
        ]
        segment_depths[rng.choice(one_choices)] = 1
        if marker_coords[-1] == size - 1:
            segment_depths[-1] = 1

        terrain = set()
        marker_index = 0
        previous_depth = 1
        for coordinate in range(size):
            while (
                marker_index + 1 < len(marker_coords)
                and coordinate >= marker_coords[marker_index + 1]
            ):
                marker_index += 1
            current_depth = segment_depths[marker_index]
            for depth in range(
                min(previous_depth, current_depth),
                max(previous_depth, current_depth) + 1,
            ):
                terrain.add((depth, coordinate))
            previous_depth = current_depth
        depths = {depth for depth, _ in terrain}
        density = len(terrain) / (size * size)
        if max(depths, default=0) == max_depth and 0.05 <= density <= 0.13:
            return terrain
    raise RuntimeError("unable to construct calibrated connected terrain")


def _construct_extrapolation(profile, difficulty, rng):
    band = difficulty if difficulty in _WEIGHTED_PROFILES else "medium"
    parameters = _PROFILE_PARAMETERS[profile]
    size = parameters["sizes"][band]
    max_depth = parameters["max_depth"]
    marker_coords = tuple(range(0, size, parameters["period"]))
    gap = parameters["gap"]
    low = max_depth
    high = size - 1 - gap - max_depth
    if low > high:
        raise RuntimeError("profile geometry cannot fit its canvas")

    for _ in range(80):
        marker_line = rng.randint(low, high)
        target_line = marker_line + gap
        terrain_depths = _terrain_polyline(
            size,
            marker_coords,
            max_depth,
            rng,
        )
        grid = _empty_grid(size, size)
        for depth, col in terrain_depths:
            grid[marker_line - depth][col] = 1
        for col in marker_coords:
            grid[marker_line][col] = 2
            grid[target_line][col] = 1
        if not self_check(grid):
            return grid
    raise RuntimeError(
        f"unable to construct complete {profile!r} scene after 80 attempts"
    )


def _draw_palette(rng):
    background = rng.choice((3, 4, 8, 3, 4, 8, 0, 1, 2, 5, 6, 7, 9))
    remaining = [color for color in range(10) if color != background]
    source = rng.choice(remaining)
    paint = rng.choice([color for color in remaining if color != source])
    return background, source, paint


def _recolor_roles(grid, palette):
    background, source, paint = palette
    colors = {0: background, 1: source, 2: paint}
    return [[colors[value] for value in row] for row in grid]


def observe_overrides(grid):
    """Recover both exact declared controls from the returned grid."""
    analysis = _analyze(grid)
    if not analysis["strict"]:
        raise ValueError(f"cannot observe invalid grid: {analysis['reasons']}")
    normalized = _normalize_roles(grid)
    canonical = _rotation_canonical(normalized)
    orientation = next(
        index
        for index, candidate in enumerate(_rotations(canonical))
        if candidate == normalized
    )
    return {
        "scene_profile": analysis["scene_profile"],
        "orientation": orientation,
    }


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")
    if (
        "orientation" in overrides
        and overrides["orientation"] is not None
        and (
            isinstance(overrides["orientation"], bool)
            or not isinstance(overrides["orientation"], int)
        )
    ):
        raise ValueError("orientation override must be an integer in 0..3")
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    band = difficulty if difficulty in _WEIGHTED_PROFILES else "medium"
    profile = ctx.draw_choice(
        "scene_profile",
        _WEIGHTED_PROFILES[band],
    )
    scene_rng = ctx.draw_rng("scene")
    palette_rng = ctx.draw_rng("palette")

    if profile in PUBLIC_PROFILES:
        roles = [
            row[:] for row in _PUBLIC_ROLE_GRIDS[profile]
        ]
    else:
        roles = _construct_extrapolation(
            profile,
            difficulty,
            scene_rng,
        )
    canonical = _rotation_canonical(roles)
    if "orientation" in overrides and overrides["orientation"] is not None:
        orientation = ctx.draw_choice("orientation", tuple(range(4)))
    elif profile in PUBLIC_PROFILES:
        original = _PUBLIC_ROLE_GRIDS[profile]
        literal_orientation = next(
            index
            for index, candidate in enumerate(_rotations(canonical))
            if candidate == original
        )
        orientation = ctx.draw_choice(
            "orientation",
            tuple(
                index
                for index in range(4)
                if index != literal_orientation
            ),
        )
    else:
        orientation = ctx.draw_choice("orientation", tuple(range(4)))
    roles = _rotations(canonical)[orientation]
    grid = _recolor_roles(roles, _draw_palette(palette_rng))

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise RuntimeError(
            f"constructed invalid {profile!r} scene: {errors}"
        )
    return [row[:] for row in grid]
