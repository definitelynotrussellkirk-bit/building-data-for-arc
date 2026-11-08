"""Generator for ARC task 297e46df4407.

A red cell is a port attached to one blue tetromino.  A green cell marks the
same relative port on a destination.  Translate the complete blue component
by the red-to-green vector and paint the in-bounds copy cyan.  The five public
profiles also demonstrate clear copies, a copy that overwrites one distractor,
and a copy that overwrites the red source port.
"""
from __future__ import annotations

from collections import Counter

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "297e46df4407"
TASK_ID = "297e46df4407"
VERSION = "3.1.0"
RULE_HASH = "47ca0464346f"

SUMMARY = (
    "Copy the one blue tetromino in cyan by the vector from its attached "
    "red port to the green destination port. Preserve the input scene "
    "except where the cyan copy overwrites a demonstrated target cell."
)

INVARIANTS = [
    "the input contains one four-cell blue component and one red/green port pair",
    "the red port has a published relative position on the blue component",
    "all four translated cells are in bounds",
    "structured inert components preserve the published equality-role grammar",
    "clear, one-distractor-overwrite, and red-port-overwrite profiles are covered",
]

SCENE_PROFILES = (
    "t_clear",
    "square_clear",
    "ell_left_clear",
    "ell_overlap_decoy",
    "stair_overlap_red",
)

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "difficulty-weighted over five published profiles",
        "valid": (
            "t_clear|square_clear|ell_left_clear|"
            "ell_overlap_decoy|stair_overlap_red"
        ),
    },
}

HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()

_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))
_SPECIAL_COLORS = {0, 1, 2, 3, 8}
_DECOY_COLORS = (4, 5, 6, 7, 9)

_COMPONENT_SHAPES = {
    "dot": ((0, 0),),
    "domino": ((0, 0), (0, 1)),
    "square2": ((0, 0), (0, 1), (1, 0), (1, 1)),
}

# Each descriptor records a complete linked public profile in its canonical
# orientation.  Distractor coordinates and concrete inert color names are
# nuisance variables; their component morphology and equality roles are not.
_PROFILE_SPECS = {
    "t_clear": {
        "shape": (12, 11),
        "blob": ((0, 0), (1, 0), (1, 1), (2, 0)),
        "anchor": (0, 1),
        "delta": (1, 5),
        "decoy_groups": (
            ("domino", "domino", "dot"),
            ("domino",),
        ),
        "collision": "clear",
        "collision_component": None,
    },
    "square_clear": {
        "shape": (12, 12),
        "blob": ((0, 0), (0, 1), (1, 0), (1, 1)),
        "anchor": (2, 0),
        "delta": (-2, -2),
        "decoy_groups": (
            ("dot",),
            ("square2", "square2"),
        ),
        "collision": "clear",
        "collision_component": None,
    },
    "ell_left_clear": {
        "shape": (13, 14),
        "blob": ((0, 0), (1, 0), (2, 0), (2, 1)),
        "anchor": (1, 1),
        "delta": (1, -6),
        "decoy_groups": (
            ("domino", "domino"),
            ("dot",),
        ),
        "collision": "clear",
        "collision_component": None,
    },
    "ell_overlap_decoy": {
        "shape": (12, 15),
        "blob": ((0, 0), (0, 1), (1, 0), (2, 0)),
        "anchor": (1, 1),
        "delta": (3, 5),
        "decoy_groups": (
            ("domino", "domino"),
            ("square2",),
            ("square2",),
        ),
        "collision": "decoy",
        "collision_component": (1, 0),
    },
    "stair_overlap_red": {
        "shape": (12, 11),
        "blob": ((0, 1), (1, 0), (1, 1), (2, 0)),
        "anchor": (2, 1),
        "delta": (1, 1),
        "decoy_groups": (
            ("domino",),
            ("dot", "domino"),
            ("square2",),
        ),
        "collision": "src_anchor",
        "collision_component": None,
    },
}

_PROFILE_INDEX = {
    profile: index for index, profile in enumerate(SCENE_PROFILES)
}


def _validate_call(difficulty, overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(
            "difficulty must be None, 'easy', 'medium', or 'hard'"
        )
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError("unknown override(s): " + ", ".join(unknown))


def _coerce_grid(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        return None, ["grid must be a nonempty rectangular sequence"]
    first_row = grid[0]
    width = len(first_row) if isinstance(first_row, (list, tuple)) else 0
    if width == 0:
        return None, ["grid rows must be nonempty"]
    errors = []
    coerced = []
    for row_index, row in enumerate(grid):
        if not isinstance(row, (list, tuple)) or len(row) != width:
            errors.append(f"row {row_index} must have width {width}")
            continue
        converted = []
        for value in row:
            if (
                not isinstance(value, int)
                or isinstance(value, bool)
                or not 0 <= value <= 9
            ):
                errors.append("all cells must be integer ARC colors 0..9")
                converted.append(0)
            else:
                converted.append(value)
        coerced.append(converted)
    if errors:
        return None, errors
    return coerced, []


def _components(grid, color):
    height = len(grid)
    width = len(grid[0])
    seen = set()
    components = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] != color or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells = []
            while stack:
                cell = stack.pop()
                cells.append(cell)
                for delta_row, delta_col in _CARDINAL:
                    neighbor = (
                        cell[0] + delta_row,
                        cell[1] + delta_col,
                    )
                    if (
                        0 <= neighbor[0] < height
                        and 0 <= neighbor[1] < width
                        and neighbor not in seen
                        and grid[neighbor[0]][neighbor[1]] == color
                    ):
                        seen.add(neighbor)
                        stack.append(neighbor)
            components.append(tuple(sorted(cells)))
    return tuple(components)


def _normalize_cells(cells):
    top = min(row for row, _col in cells)
    left = min(col for _row, col in cells)
    return tuple(sorted(
        (row - top, col - left) for row, col in cells
    ))


def _shape_key(cells):
    """Return a translation/D4-invariant component morphology."""
    variants = []
    original = tuple(cells)
    for reflect in (False, True):
        points = [
            (row, -col if reflect else col)
            for row, col in original
        ]
        for _turn in range(4):
            variants.append(_normalize_cells(points))
            points = [(col, -row) for row, col in points]
    return min(variants)


_ABSTRACT_SHAPES = {
    name: _shape_key(cells)
    for name, cells in _COMPONENT_SHAPES.items()
}


def _decoy_group_signature(grid):
    colors = sorted({
        value
        for row in grid
        for value in row
        if value not in _SPECIAL_COLORS
    })
    groups = []
    for color in colors:
        groups.append(tuple(sorted(
            _shape_key(component)
            for component in _components(grid, color)
        )))
    return tuple(sorted(groups))


def _hit_type(value):
    if value == 1:
        return "source"
    if value == 2:
        return "src_anchor"
    if value == 3:
        return "dst_anchor"
    if value == 0:
        return None
    return "decoy"


def _orientation_signature(grid):
    source_components = _components(grid, 1)
    red = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 2
    ]
    green = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 3
    ]
    if (
        len(source_components) != 1
        or len(source_components[0]) != 4
        or len(red) != 1
        or len(green) != 1
    ):
        return None
    source = source_components[0]
    top = min(row for row, _col in source)
    left = min(col for _row, col in source)
    delta = (
        green[0][0] - red[0][0],
        green[0][1] - red[0][1],
    )
    targets = tuple(
        (row + delta[0], col + delta[1])
        for row, col in source
    )
    height = len(grid)
    width = len(grid[0])
    full = all(
        0 <= row < height and 0 <= col < width
        for row, col in targets
    )
    hits = tuple(sorted(
        hit
        for row, col in targets
        if 0 <= row < height and 0 <= col < width
        for hit in [_hit_type(grid[row][col])]
        if hit is not None
    ))
    return (
        (height, width),
        _normalize_cells(source),
        (red[0][0] - top, red[0][1] - left),
        delta,
        _decoy_group_signature(grid),
        hits,
        full,
    )


def _expected_signature(profile_name):
    spec = _PROFILE_SPECS[profile_name]
    groups = tuple(sorted(
        tuple(sorted(_ABSTRACT_SHAPES[name] for name in group))
        for group in spec["decoy_groups"]
    ))
    collision = spec["collision"]
    hits = () if collision == "clear" else (collision,)
    return (
        spec["shape"],
        tuple(spec["blob"]),
        spec["anchor"],
        spec["delta"],
        groups,
        hits,
        True,
    )


_EXPECTED_SIGNATURES = {
    profile: _expected_signature(profile)
    for profile in SCENE_PROFILES
}


def _transform_grid(grid, transform):
    transformed = [row[:] for row in grid]
    if transform >= 4:
        transformed = [
            list(reversed(row)) for row in transformed
        ]
    for _turn in range(transform % 4):
        transformed = [
            list(row) for row in zip(*reversed(transformed))
        ]
    return transformed


def _scene_analysis(grid):
    coerced, errors = _coerce_grid(grid)
    if coerced is None:
        return None, {}, errors
    counts = Counter(value for row in coerced for value in row)
    if 0 not in counts or counts[0] != max(counts.values()):
        errors.append("zero must be a modal background")
    if counts.get(8, 0):
        errors.append("input must not contain prepainted cyan cells")
    foreign = sorted(set(counts) - _SPECIAL_COLORS - set(_DECOY_COLORS))
    if foreign:
        errors.append(f"unsupported input colors: {foreign}")

    source_components = _components(coerced, 1)
    if len(source_components) != 1 or len(source_components[0]) != 4:
        errors.append(
            "input must contain one four-cell blue component"
        )
    if counts.get(2, 0) != 1 or counts.get(3, 0) != 1:
        errors.append(
            "input must contain exactly one red and one green anchor"
        )

    profile_name = None
    if not errors:
        for transform in range(8):
            signature = _orientation_signature(
                _transform_grid(coerced, transform)
            )
            for candidate in SCENE_PROFILES:
                if signature == _EXPECTED_SIGNATURES[candidate]:
                    profile_name = candidate
                    break
            if profile_name is not None:
                break
    if profile_name is None:
        errors.append(
            "returned scene must match a complete published port profile"
        )
    return coerced, {"scene_profile": profile_name}, errors


def self_check(grid, *, difficulty=None, meta=None):
    """Validate the complete returned-grid curriculum profile."""
    _coerced, _features, errors = _scene_analysis(grid)
    return errors


def observe_overrides(grid):
    """Recover every exact control from the returned grid."""
    _coerced, features, errors = _scene_analysis(grid)
    if errors:
        return {}
    return {"scene_profile": features["scene_profile"]}


def canonical_profile_index(grid):
    _coerced, features, errors = _scene_analysis(grid)
    if errors:
        return None
    return _PROFILE_INDEX[features["scene_profile"]]


def rule_mirror(grid):
    """Execute the broad semantic rule beyond the strict curriculum."""
    coerced, errors = _coerce_grid(grid)
    if coerced is None:
        raise ValueError("; ".join(errors))
    output = [row[:] for row in coerced]
    source_components = _components(coerced, 1)
    red = [
        (row, col)
        for row, values in enumerate(coerced)
        for col, value in enumerate(values)
        if value == 2
    ]
    green = [
        (row, col)
        for row, values in enumerate(coerced)
        for col, value in enumerate(values)
        if value == 3
    ]
    if not source_components or not red or not green:
        return output
    delta = (
        green[0][0] - red[0][0],
        green[0][1] - red[0][1],
    )
    height = len(coerced)
    width = len(coerced[0])
    for row, col in source_components[0]:
        target_row = row + delta[0]
        target_col = col + delta[1]
        if (
            0 <= target_row < height
            and 0 <= target_col < width
        ):
            output[target_row][target_col] = 8
    return output


def _in_bounds(cell, height, width):
    return 0 <= cell[0] < height and 0 <= cell[1] < width


def _core_candidates(spec):
    height, width = spec["shape"]
    candidates = []
    for top in range(height):
        for left in range(width):
            source = {
                (top + row, left + col)
                for row, col in spec["blob"]
            }
            red = (
                top + spec["anchor"][0],
                left + spec["anchor"][1],
            )
            green = (
                red[0] + spec["delta"][0],
                red[1] + spec["delta"][1],
            )
            targets = {
                (
                    row + spec["delta"][0],
                    col + spec["delta"][1],
                )
                for row, col in source
            }
            all_cells = source | {red, green} | targets
            if not all(
                _in_bounds(cell, height, width)
                for cell in all_cells
            ):
                continue
            if red in source or green in source or red == green:
                continue
            core_hits = []
            for cell in targets:
                if cell in source:
                    core_hits.append("source")
                elif cell == red:
                    core_hits.append("src_anchor")
                elif cell == green:
                    core_hits.append("dst_anchor")
            expected_hits = (
                ["src_anchor"]
                if spec["collision"] == "src_anchor"
                else []
            )
            if sorted(core_hits) != expected_hits:
                continue
            candidates.append((top, left, source, red, green, targets))
    return candidates


def _oriented_component(shape_name, rng):
    if shape_name == "domino" and rng.randrange(2):
        return ((0, 0), (1, 0))
    return _COMPONENT_SHAPES[shape_name]


def _absolute_shape(shape, top, left):
    return {
        (top + row, left + col) for row, col in shape
    }


def _touches_same_color(cells, color, grid):
    height = len(grid)
    width = len(grid[0])
    for row, col in cells:
        for delta_row, delta_col in _CARDINAL:
            neighbor = (row + delta_row, col + delta_col)
            if (
                neighbor not in cells
                and _in_bounds(neighbor, height, width)
                and grid[neighbor[0]][neighbor[1]] == color
            ):
                return True
    return False


def _place_component(
    grid,
    occupied,
    targets,
    shape,
    color,
    rng,
    *,
    collide=False,
):
    height = len(grid)
    width = len(grid[0])
    shape_height = max(row for row, _col in shape) + 1
    shape_width = max(col for _row, col in shape) + 1
    candidates = [
        (top, left)
        for top in range(height - shape_height + 1)
        for left in range(width - shape_width + 1)
    ]
    rng.shuffle(candidates)
    for top, left in candidates:
        cells = _absolute_shape(shape, top, left)
        target_overlap = cells & targets
        if collide:
            if len(target_overlap) != 1:
                continue
        elif target_overlap:
            continue
        if cells & occupied:
            continue
        if _touches_same_color(cells, color, grid):
            continue
        for row, col in cells:
            grid[row][col] = color
        occupied.update(cells)
        return True
    return False


def _build_scene(profile_name, rng):
    spec = _PROFILE_SPECS[profile_name]
    height, width = spec["shape"]
    core_candidates = _core_candidates(spec)
    if not core_candidates:
        return None
    _top, _left, source, red, green, targets = rng.choice(
        core_candidates
    )
    grid = full_grid(height, width, 0)
    for row, col in source:
        grid[row][col] = 1
    grid[red[0]][red[1]] = 2
    grid[green[0]][green[1]] = 3
    occupied = set(source) | {red, green}

    groups = spec["decoy_groups"]
    colors = rng.sample(list(_DECOY_COLORS), len(groups))
    requests = [
        (group_index, component_index, shape_name)
        for group_index, group in enumerate(groups)
        for component_index, shape_name in enumerate(group)
    ]
    collision_component = spec["collision_component"]
    if collision_component is not None:
        requests.sort(
            key=lambda item: (
                (item[0], item[1]) != collision_component,
                item[0],
                item[1],
            )
        )
    for group_index, component_index, shape_name in requests:
        shape = _oriented_component(shape_name, rng)
        if not _place_component(
            grid,
            occupied,
            targets,
            shape,
            colors[group_index],
            rng,
            collide=(
                (group_index, component_index)
                == collision_component
            ),
        ):
            return None
    return _transform_grid(grid, rng.randrange(8))


def _draw_scene(profile_name, rng):
    for _attempt in range(240):
        grid = _build_scene(profile_name, rng)
        if grid is None:
            continue
        _coerced, features, errors = _scene_analysis(grid)
        if (
            not errors
            and features["scene_profile"] == profile_name
        ):
            return grid
    raise ValueError(
        f"could not realize strict scene profile {profile_name!r}"
    )


def _profile_options(difficulty):
    if difficulty == "easy":
        return (
            "t_clear",
            "t_clear",
            "square_clear",
            "square_clear",
            "ell_left_clear",
            "ell_overlap_decoy",
            "stair_overlap_red",
        )
    if difficulty == "hard":
        return (
            "t_clear",
            "square_clear",
            "ell_left_clear",
            "ell_overlap_decoy",
            "ell_overlap_decoy",
            "stair_overlap_red",
            "stair_overlap_red",
        )
    return SCENE_PROFILES


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Generate a deterministic fresh input with an observed exact profile."""
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile_name = ctx.draw_choice(
        "scene_profile",
        _profile_options(difficulty),
    )
    grid = _draw_scene(profile_name, ctx.draw_rng("scene"))
    observed = observe_overrides(grid)
    if observed != {"scene_profile": profile_name}:
        raise AssertionError(
            "returned profile does not match the requested profile"
        )
    return grid
