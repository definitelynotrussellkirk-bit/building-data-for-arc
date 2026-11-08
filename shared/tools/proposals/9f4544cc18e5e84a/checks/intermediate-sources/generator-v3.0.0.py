"""Rotation-equivalence lessons with shape, reflection and component controls.

The selected Racket program supplies every label. Python relation functions below
are authoring rivals/witnesses and observable-axis diagnostics, never label authority.
The default sampler uses nine demonstrations and one query; see notes.md for its
finite ten-slot schedule, exact controls, generated support and limitations.
"""
from __future__ import annotations

from functools import lru_cache
from itertools import combinations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "5c126cb64bf7"
TASK_ID = GENERATOR_ID
RULE_HASH = "338c27e34ee3"
VERSION = "3.0.0"
SUMMARY = (
    "Three 5-wide panels separated by zero columns; crop and binarize each whole "
    "panel, then compare under the four rotations. Return a symmetric 3x3 matrix "
    "with diagonal 8, equivalent off-diagonal pairs 2, and other pairs 0. Inputs "
    "mix connected shapes and separated satellites, translated and recolored; "
    "chiral equal-count negatives separate rotation from reflection and counting."
)
INVARIANTS = [
    "background and both separator columns (5 and 11) are zero",
    "height is 5..9 and width is exactly 17; panels begin at columns 0, 6 and 12",
    "each panel contains 3..7 cells in one nonzero color; colors may repeat across panels",
    "rotation compares the entire cropped binary panel, including disconnected cells",
]
AXES = {
    "grid_h": {"type": "int", "default": "5 favored; 5..9 supported", "valid": "5..9"},
    "grid_w": {"type": "int", "default": "17 (fixed compatibility parameter)",
               "valid": "17", "probe": "diagnostic"},
    "n_classes": {"type": "int", "default": "ten-slot lesson schedule", "valid": "1..3"},
    "partition": {"type": "str", "default": "scheduled class count; random matching pair",
                  "valid": "all_distinct|all_same|pair_01|pair_02|pair_12"},
    "palette_size": {"type": "int", "default": "seed family: 3,3,3,1,2", "valid": "1..3"},
    "texture": {"type": "str", "default": "scheduled witnesses plus free choices",
                "valid": "connected|scattered"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = [("n_classes", "partition")]
HELPFUL_TEXTURES = ("connected", "scattered")
EXPECTED_OUTPUT_CODOMAIN = 5
EXAMPLES_NEEDED = 9
LESSON_SCHEDULE_PERIOD = 10
SCHEDULE_PROFILES = (
    "all_same_a", "quarter_satellite", "half_connected", "all_distinct_a", "free_pair_a",
    "all_same_b", "quarter_connected", "half_satellite", "all_distinct_b", "free_pair_b",
)
_PARTITIONS = {
    "all_distinct": (0, 1, 2), "all_same": (0, 0, 0),
    "pair_01": (0, 0, 1), "pair_02": (0, 1, 0), "pair_12": (0, 1, 1),
}
_STARTS = (0, 6, 12)
_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))


class IncompatibleOverrides(ValueError):
    """The two individually valid exact controls request different partitions."""
    incompatible_axes = ("n_classes", "partition")


def schedule_profile(seed, sample_index, difficulty=None):
    return SCHEDULE_PROFILES[(seed + sample_index) % LESSON_SCHEDULE_PERIOD]


def _norm(cells):
    cells = tuple(cells)
    if not cells:
        return ()
    r0 = min(r for r, c in cells)
    c0 = min(c for r, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def _rotate(cells, turns=1):
    cells = _norm(cells)
    for _ in range(turns % 4):
        cells = _norm((c, -r) for r, c in cells)
    return cells


def _mirror(cells):
    return _norm((r, -c) for r, c in cells)


@lru_cache(maxsize=32768)
def _orbit(cells):
    return min(_rotate(cells, k) for k in range(4))


def _components(cells, connectivity=4):
    remaining = set(cells)
    directions = _CARDINAL if connectivity == 4 else tuple(
        (r, c) for r in (-1, 0, 1) for c in (-1, 0, 1) if (r, c) != (0, 0))
    result = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        stack, component = [start], []
        while stack:
            r, c = stack.pop()
            component.append((r, c))
            for dr, dc in directions:
                neighbor = (r + dr, c + dc)
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    stack.append(neighbor)
        result.append(tuple(sorted(component)))
    return tuple(sorted(result, key=lambda part: (-len(part), min(part))))


def _component_bag(cells, connectivity=4):
    return tuple(sorted(_orbit(part) for part in _components(cells, connectivity)))


def _is_satellite_witness(cells):
    reflected = _mirror(cells)
    if _orbit(cells) == _orbit(reflected):
        return False
    for connectivity in (4, 8):
        parts = _components(cells, connectivity)
        if len(parts) < 2 or len(parts[0]) == len(parts[1]):
            return False
        if _component_bag(cells, connectivity) != _component_bag(reflected, connectivity):
            return False
        other = _components(reflected, connectivity)
        if _orbit(parts[0]) != _orbit(other[0]):
            return False
    return True


@lru_cache(maxsize=1)
def _all_shapes():
    """Finite geometry only: 3x3 binary masks plus small cores with satellites.

    This includes every canonical shape orbit (including the centered plus),
    and adds lawful 5x5 arrangements that defeat largest-8-component matching.
    The cache contains immutable templates, not generated grids or RNG state.
    """
    shapes = set()
    for mask in range(1, 1 << 9):
        cells = tuple((i // 3, i % 3) for i in range(9) if mask & (1 << i))
        if 3 <= len(cells) <= 7:
            shapes.add(_orbit(cells))
    cores = (
        ((0, 0), (0, 1)),
        ((0, 0), (0, 1), (0, 2)),
        ((0, 0), (1, 0), (1, 1)),
        ((0, 0), (0, 1), (0, 2), (1, 1)),
        ((0, 0), (0, 1), (1, 0), (1, 1)),
        ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1)),
    )
    for core in cores:
        height = max(r for r, c in core) + 1
        width = max(c for r, c in core) + 1
        for dr in range(6 - height):
            for dc in range(6 - width):
                placed = tuple((r + dr, c + dc) for r, c in core)
                for r in range(5):
                    for c in range(5):
                        if all(max(abs(r - x), abs(c - y)) > 1 for x, y in placed):
                            shapes.add(_orbit(placed + ((r, c),)))
    return tuple(sorted(shapes))


@lru_cache(maxsize=8)
def _bank(texture, chiral=False, satellite=False):
    result = []
    for shape in _all_shapes():
        connected = len(_components(shape)) == 1
        if connected != (texture == "connected"):
            continue
        if chiral and _orbit(shape) == _orbit(_mirror(shape)):
            continue
        if satellite and not _is_satellite_witness(shape):
            continue
        result.append(shape)
    if not result:
        raise RuntimeError("empty constructive shape bank")
    return tuple(result)


def _pick_shape(ctx, label, texture, difficulty, *, chiral=False, satellite=False, excluded=()):
    choices = [shape for shape in _bank(texture, chiral, satellite) if shape not in excluded]
    preferred = {"easy": (3, 4), "medium": (4, 5), "hard": (6, 7)}.get(difficulty, (4, 5))
    weights = [12 if len(shape) in preferred else 1 for shape in choices]
    return ctx.draw_rng(label).choices(choices, weights=weights, k=1)[0]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be easy, medium, hard, or None")
    supplied = {name: value for name, value in overrides.items() if value is not None}
    for name, value in supplied.items():
        kind = AXES[name]["type"]
        if kind == "int" and type(value) is not int:
            raise ValueError(f"{name} must be an integer, not {type(value).__name__}")
        if kind == "str" and not isinstance(value, str):
            raise ValueError(f"{name} must be a string")
    if "partition" in supplied and supplied["partition"] not in _PARTITIONS:
        raise ValueError("unknown partition")
    slot = (seed + sample_index) % LESSON_SCHEDULE_PERIOD
    default_classes = 1 if slot in (0, 5) else 3 if slot in (3, 8) else 2
    if "partition" in supplied:
        requested_classes = len(set(_PARTITIONS[supplied["partition"]]))
        if "n_classes" in supplied and supplied["n_classes"] != requested_classes:
            raise IncompatibleOverrides("n_classes and partition disagree")
        default_classes = requested_classes
    # The schedule is an explicit default, recorded through the same keyed
    # public draw API as caller controls; no declared axis is silently ignored.
    resolved = {"n_classes": default_classes,
                "palette_size": (3, 3, 3, 1, 2)[seed % 5], **supplied}
    if "texture" not in supplied and slot in (1, 2, 6, 7):
        resolved["texture"] = "scattered" if slot in (1, 7) else "connected"
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=resolved)
    height = ctx.draw_choice("grid_h", [5] * 10 + [6, 7, 8, 9])
    width = ctx.draw_int("grid_w", 17, 17)
    n_classes = ctx.draw_int("n_classes", 1, 3)
    palette_size = ctx.draw_int("palette_size", 1, 3)
    texture = ctx.draw_choice("texture", ("connected", "scattered"))
    choices = [name for name, labels in _PARTITIONS.items() if len(set(labels)) == n_classes]
    partition = ctx.draw_choice("partition", choices)
    labels = _PARTITIONS[partition]
    core = n_classes == 2 and slot in (1, 2, 6, 7)
    a = _pick_shape(ctx, "base-a", texture, difficulty, chiral=core,
                    satellite=core and texture == "scattered")
    bases = [a]
    if n_classes > 1:
        b = _orbit(_mirror(a)) if core else _pick_shape(
            ctx, "base-b", texture, difficulty, excluded=bases)
        bases.append(b)
    if n_classes == 3:
        bases.append(_pick_shape(ctx, "base-c", texture, difficulty, excluded=bases))
    rotations = [ctx.draw_rng(f"orientation-{i}").randrange(4) for i in range(3)]
    if core:
        equal = [i for i in range(3) if labels[i] == 0]
        # pair_12 stores its shared class as 1; locate the repeated class by count.
        if len(equal) != 2:
            equal = [i for i in range(3) if labels[i] == 1]
        turns = 1 if slot in (1, 6) else 2
        rotations[equal[1]] = (rotations[equal[0]] + turns) % 4
    palette_rng = ctx.draw_rng("palette")
    palette = palette_rng.sample(range(1, 10), palette_size)
    colors = palette + [palette_rng.choice(palette) for _ in range(3 - palette_size)]
    palette_rng.shuffle(colors)
    grid = full_grid(height, width, 0)
    for i, (start, color, label) in enumerate(zip(_STARTS, colors, labels)):
        cells = _rotate(bases[label], rotations[i])
        shape_h = max(r for r, c in cells) + 1
        shape_w = max(c for r, c in cells) + 1
        position = ctx.draw_rng(f"position-{i}")
        dr, dc = position.randrange(height - shape_h + 1), position.randrange(6 - shape_w)
        for r, c in cells:
            grid[r + dr][start + c + dc] = color
    return grid


def _panels(grid):
    return tuple(tuple((r, c) for r, row in enumerate(grid)
                       for c, value in enumerate(row[start:start + 5]) if value != 0)
                 for start in _STARTS)


def _relation(keys):
    return [[8 if i == j else 2 if keys[i] == keys[j] else 0
             for j in range(len(keys))] for i in range(len(keys))]


def _rotation_matrix(grid):
    """Python diagnostic mirror; selected Racket remains the label authority."""
    return _relation([_orbit(cells) for cells in _panels(grid)])


def observe_overrides(grid):
    panels = _panels(grid)
    keys = [_orbit(cells) for cells in panels]
    classes, labels = [], []
    for key in keys:
        if key not in classes:
            classes.append(key)
        labels.append(classes.index(key))
    connectivity = [len(_components(cells)) == 1 for cells in panels]
    return {
        "grid_h": len(grid), "grid_w": len(grid[0]), "n_classes": len(classes),
        "partition": next(name for name, values in _PARTITIONS.items() if values == tuple(labels)),
        "palette_size": len({value for row in grid for value in row if value != 0}),
        "texture": "connected" if all(connectivity) else "scattered" if not any(connectivity) else "mixed",
    }


def self_check(grid, *, difficulty=None, meta=None):
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty rectangular grid"]
    if any(not isinstance(row, (list, tuple)) or len(row) != 17 for row in grid):
        return ["every row must have exactly 17 cells"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be integer colors 0..9, excluding bool"]
    reasons = []
    if not 5 <= len(grid) <= 9:
        reasons.append("height must be 5..9")
    if any(row[5] != 0 or row[11] != 0 for row in grid):
        reasons.append("separator columns 5 and 11 must be zero")
    for start, cells in zip(_STARTS, _panels(grid)):
        if not 3 <= len(cells) <= 7:
            reasons.append(f"panel at column {start} must contain 3..7 cells")
        colors = {grid[r][start + c] for r, c in cells}
        if len(colors) != 1:
            reasons.append(f"panel at column {start} must use one nonzero color")
    return reasons


def strict_canonical_like(grid):
    reasons = self_check(grid)
    if not reasons and len(grid) != 5:
        reasons.append("canonical-height profile uses exactly 5 rows")
    return reasons


def _d4(grid):
    return _relation([min(_orbit(p), _orbit(_mirror(p))) for p in _panels(grid)])


def _largest(grid, connectivity):
    return _relation([_orbit(_components(p, connectivity)[0]) for p in _panels(grid)])


def _bag(grid, connectivity):
    return _relation([_component_bag(p, connectivity) for p in _panels(grid)])


def _degrees(cells):
    points = set(cells)
    return tuple(sorted(sum((r + dr, c + dc) in points for dr, dc in _CARDINAL)
                        for r, c in cells))


def _box_degrees(cells):
    points = _norm(cells)
    return (len(points), tuple(sorted((max(r for r, c in points) + 1,
                                      max(c for r, c in points) + 1))), _degrees(points))


def _distances(cells):
    return tuple(sorted((r - x) ** 2 + (c - y) ** 2
                        for (r, c), (x, y) in combinations(cells, 2)))


def _global_colors(grid):
    groups = {}
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value:
                groups.setdefault(value, []).append((r, c))
    ordered = sorted(groups.values(), key=lambda cells: min(c for r, c in cells))
    return _relation([_orbit(tuple(cells)) for cells in ordered])


def _partial_rotations(grid, turns):
    panels = [_norm(cells) for cells in _panels(grid)]
    return [[8 if i == j else 2 if any(_rotate(panels[i], k) == panels[j] for k in turns) else 0
             for j in range(3)] for i in range(3)]


def _uncropped(grid):
    panels = [tuple(tuple(int(value != 0) for value in row[start:start + 5]) for row in grid)
              for start in _STARTS]
    keys = []
    for panel in panels:
        rotations = []
        for _ in range(4):
            rotations.append(panel)
            panel = tuple(zip(*panel[::-1]))
        keys.append(min(rotations))
    return _relation(keys)


def _first_match(grid):
    actual = _rotation_matrix(grid)
    output = _relation([0, 1, 2])
    for i, j in combinations(range(3), 2):
        if actual[i][j] == 2:
            output[i][j] = output[j][i] = 2
            break
    return output


def _force_pair(grid):
    output = _first_match(grid)
    if not any(2 in row for row in output):
        output[0][1] = output[1][0] = 2
    return output


SEMANTIC_RIVALS = {
    "rotation_or_reflection": _d4,
    "largest_4_component": lambda grid: _largest(grid, 4),
    "largest_8_component": lambda grid: _largest(grid, 8),
    "component_bag_4": lambda grid: _bag(grid, 4),
    "component_bag_8": lambda grid: _bag(grid, 8),
    "degree_histogram": lambda grid: _relation([_degrees(p) for p in _panels(grid)]),
    "count_bbox_degree": lambda grid: _relation([_box_degrees(p) for p in _panels(grid)]),
    "distance_histogram": lambda grid: _relation([_distances(p) for p in _panels(grid)]),
    "global_color_groups": _global_colors,
    "first_match_only": _first_match,
    "force_one_pair": _force_pair,
    "cell_count": lambda grid: _relation([len(p) for p in _panels(grid)]),
    "no_rotation": lambda grid: _partial_rotations(grid, (0,)),
    "halfturn_only": lambda grid: _partial_rotations(grid, (0, 2)),
    "no_halfturn": lambda grid: _partial_rotations(grid, (0, 1, 3)),
    "uncropped_rotation": _uncropped,
}
# These assertions are separately executed on all five labelled canonical pairs.
# Cell count and restricted rotations are intentionally not claimed canonical-fitting.
CANONICAL_SHORTCUTS = {name: SEMANTIC_RIVALS[name] for name in (
    "rotation_or_reflection", "largest_4_component", "largest_8_component",
    "component_bag_4", "component_bag_8", "degree_histogram", "count_bbox_degree",
    "distance_histogram", "global_color_groups", "first_match_only", "force_one_pair",
)}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def _refuter(rival):
    return lambda grid: rival(grid) != _rotation_matrix(grid)


SEMANTIC_WITNESSES = {"refute_" + name: _refuter(rival) for name, rival in SEMANTIC_RIVALS.items()}
WITNESS_RIVALS = {"refute_" + name: [name] for name in SEMANTIC_RIVALS}


def lesson_identifiable(demos, query):
    """Finite authoring check against declared pure-grid rivals, using supplied labels."""
    return [name for name, rival in LESSON_COMPETITORS.items()
            if all(rival(pair["input"]) == pair["output"] for pair in demos)
            and rival(query["input"]) != query["output"]]
