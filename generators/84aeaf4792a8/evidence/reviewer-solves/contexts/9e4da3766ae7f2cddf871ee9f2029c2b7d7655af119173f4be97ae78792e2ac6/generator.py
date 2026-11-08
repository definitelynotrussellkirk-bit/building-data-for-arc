"""Input sampler for the unchanged rotation-similarity-matrix Racket rule.

Even indices teach rotation versus reflection and coarse shape statistics.
Odd indices broaden counts, partitions and colors. Four consecutive pairs contain
two teaching examples and two non-four-component examples. Any single holdout
retains a refutation of each declared rival. Explicit overrides control individual
inputs; they do not promise the unconstrained lesson schedule.
"""
from __future__ import annotations

from functools import lru_cache
from itertools import combinations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.indices import neighbors_4, neighbors_8
from puzzle_generators.helpers.objects import find_objects
from puzzle_generators.helpers.shape import normalize

GENERATOR_ID = "84aeaf4792a8"
TASK_ID = GENERATOR_ID
RULE_HASH = "f2869336c461"
VERSION = "4.0.0"
SUMMARY = (
    "Compare 2..6 isolated monochromatic components, ordered by bounding-box "
    "top row then left column. Ignore colors and compare occupied cells under "
    "translation and the four rotations, excluding reflection. The N-by-N "
    "matrix has 5 on the diagonal, 8 for matches, and 0 otherwise. Sample all "
    "19 rotation classes of connected 3..5-cell shapes fitting 3x3, including "
    "chiral pairs, repeated colors, and every feasible class count."
)
INVARIANTS = [
    "background 0; integer colors 0..9 on an 8..18 by 12..22 rectangle",
    "2..6 monochromatic four-connected components, separated even diagonally",
    "each component contains 3..5 cells and fits a 3-by-3 bounding box",
    "component count, rotation-class count and foreground-color count are exact controls",
    "unconstrained even draws contain a nontrivial rotational match and a chiral nonmatch",
]
AXES = {
    "grid_h": {"type": "int", "default": "12..13 teaching; band-weighted otherwise", "valid": "8..18"},
    "grid_w": {"type": "int", "default": "14..16 teaching; band-weighted otherwise", "valid": "12..22"},
    "n_components": {"type": "int", "default": "4 even; relation-weighted 2/3/5 and 6 odd", "valid": "2..6"},
    "n_families": {"type": "int", "default": "3 or 2 teaching; 1..n_components otherwise", "valid": "1..6"},
    "n_distinct_colors": {"type": "int", "default": "4 teaching; 1..n_components otherwise", "valid": "1..6"},
}
# Exceptions additionally name the conflicting axes. An unpinned component
# count grows to accommodate a requested family/color count.
INCOMPATIBLE_OVERRIDE_COMBINATIONS = [
    ("n_components", "n_families"),
    ("n_components", "n_distinct_colors"),
]
EXAMPLES_NEEDED = 3
LESSON_SCHEDULE_PERIOD = 4
SCHEDULE_PROFILES = ("teaching_one_pair", "mixed_count", "teaching_two_pairs", "large_count")


def schedule_profile(seed, sample_index, difficulty=None):
    return SCHEDULE_PROFILES[sample_index % LESSON_SCHEDULE_PERIOD]


def _norm(cells):
    return tuple(sorted(normalize(tuple(cells))))


def _turn(cells, turns=1):
    cells = _norm(cells)
    for _ in range(turns % 4):
        cells = _norm((c, -r) for r, c in cells)
    return cells


@lru_cache(maxsize=256)
def _rotation_key(cells):
    return min(_turn(cells, turns) for turns in range(4))


def _mirror(cells):
    return _norm((r, -c) for r, c in cells)


def _connected(cells):
    remaining = set(cells)
    stack = [remaining.pop()]
    while stack:
        for point in neighbors_4(stack.pop()):
            if point in remaining:
                remaining.remove(point)
                stack.append(point)
    return not remaining


def _small_shapes():
    # Enumerate geometry once; never cache draws, palettes, layouts or labels.
    positions = tuple((r, c) for r in range(3) for c in range(3))
    return tuple(sorted({
        _rotation_key(_norm(cells))
        for size in range(3, 6)
        for cells in combinations(positions, size)
        if _connected(cells)
    }))


_SHAPES = _small_shapes()
_CHIRAL = tuple(shape for shape in _SHAPES if _rotation_key(_mirror(shape)) != shape)


def _components(grid):
    result = []
    for obj in find_objects(grid, univalued=True, diagonal=False, bg=0):
        cells = tuple(point for _, point in obj)
        top = min(r for r, c in cells)
        left = min(c for r, c in cells)
        result.append((top, left, next(iter(obj))[0], _norm(cells), cells))
    return sorted(result, key=lambda obj: obj[:2])


def self_check(grid, *, difficulty=None, meta=None):
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty rectangular grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected nonempty rows"]
    if any(not isinstance(row, (list, tuple)) or len(row) != len(grid[0]) for row in grid):
        return ["ragged grid"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be integer colors 0..9, excluding booleans"]
    errors = []
    if not (8 <= len(grid) <= 18 and 12 <= len(grid[0]) <= 22):
        errors.append("canvas must be 8..18 rows by 12..22 columns")
    components = _components(grid)
    if not 2 <= len(components) <= 6:
        errors.append(f"expected 2..6 components; found {len(components)}")
    owners = {}
    for index, obj in enumerate(components):
        shape = obj[3]
        if not 3 <= len(shape) <= 5:
            errors.append(f"component {index} must contain 3..5 cells")
        if max(r for r, c in shape) >= 3 or max(c for r, c in shape) >= 3:
            errors.append(f"component {index} must fit a 3-by-3 bounding box")
        for point in obj[4]:
            owners[point] = index
    if any(neighbor in owners and owners[neighbor] != owner
           for point, owner in owners.items() for neighbor in neighbors_8(point)):
        errors.append("components must be separated by background, including diagonally")
    return errors


def strict_canonical_like(grid):
    errors = self_check(grid)
    if errors:
        return errors
    observed = observe_overrides(grid)
    if not (12 <= len(grid) <= 13 and 14 <= len(grid[0]) <= 16):
        errors.append("outside canonical canvas envelope")
    if observed["n_components"] != 4 or observed["n_distinct_colors"] != 4:
        errors.append("canonical inputs have four components in four colors")
    if {value for row in grid for value in row} != {0, 2, 3, 4, 5}:
        errors.append("outside canonical palette")
    return errors


def observe_overrides(grid):
    components = _components(grid)
    return {
        "grid_h": len(grid), "grid_w": len(grid[0]),
        "n_components": len(components),
        "n_families": len({_rotation_key(obj[3]) for obj in components}),
        "n_distinct_colors": len({obj[2] for obj in components}),
    }


def _draw_int(ctx, name, low, high, defaults):
    # Explicit controls share one legal domain across difficulties. Both
    # defaults and overrides retain the values recorded by the public GenCtx.
    choices = tuple(range(low, high + 1)) if name in ctx.overrides else tuple(defaults)
    return ctx.draw_choice(name, choices)


@lru_cache(maxsize=48)
def _partitions(count, families):
    """Restricted-growth strings enumerate each unlabeled relation once."""
    sequences = [(0,)]
    for _ in range(1, count):
        sequences = [seq + (label,) for seq in sequences
                     for label in range(min(families - 1, max(seq) + 1) + 1)]
    return tuple(seq for seq in sequences if max(seq) + 1 == families)


def _shape_list(rng, count, families, teaching, difficulty):
    pool = list(_SHAPES)
    if teaching and 2 <= families < count:
        preferred = [s for s in _CHIRAL if len(s) == (4 if difficulty == "easy" else 5)]
        base = rng.choice(preferred)
        mirror = _rotation_key(_mirror(base))
        angle = rng.randrange(4)
        shapes = [_turn(base, angle), _turn(base, angle + 1), _turn(mirror, rng.randrange(4))]
        used = [base, mirror]
        for shape in rng.sample([s for s in pool if s not in used], families - 2):
            shapes.append(_turn(shape, rng.randrange(4)))
            used.append(shape)
        if count == 4 and families == 2:
            shapes.append(_turn(mirror, rng.randrange(4)))
        while len(shapes) < count:
            shapes.append(_turn(rng.choice(used), rng.randrange(4)))
        rng.shuffle(shapes)
        # Canonical examples always match components 0/1. Teaching cases refute
        # that position rule; supplemental draws remain unrestricted.
        if _rotation_key(shapes[0]) == _rotation_key(shapes[1]):
            other = next(i for i in range(2, count)
                         if _rotation_key(shapes[i]) != _rotation_key(shapes[0]))
            shapes[1], shapes[other] = shapes[other], shapes[1]
        return shapes
    selected = rng.sample(pool, families)
    assignment = rng.choice(_partitions(count, families))
    return [_turn(selected[label], rng.randrange(4)) for label in assignment]


def _matrix(keys):
    return [[5 if r == c else 8 if keys[r] == keys[c] else 0
             for c in range(len(keys))] for r in range(len(keys))]


def _color_sequence(rng, count, n_colors, keys, teaching):
    palette = [2, 3, 4, 5] if teaching and count == n_colors == 4 else rng.sample(range(1, 10), n_colors)
    colors = list(palette) + [rng.choice(palette) for _ in range(count - n_colors)]
    rng.shuffle(colors)
    if teaching and n_colors == count and 1 < len(set(keys)) < count:
        intended = _matrix(keys)

        def wrong_order(candidate):
            order = sorted(range(count), key=lambda i: candidate[i])
            return _matrix([keys[i] for i in order]) != intended

        if not wrong_order(colors):
            for a, b in combinations(range(count), 2):
                candidate = list(colors)
                candidate[a], candidate[b] = candidate[b], candidate[a]
                if wrong_order(candidate):
                    colors = candidate
                    break
            else:
                raise RuntimeError("no distinguishing color ordering for a nontrivial partition")
    return colors


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise TypeError(f"unknown override(s): {sorted(unknown)}")
    bounds = {"grid_h": (8, 18), "grid_w": (12, 22), "n_components": (2, 6),
              "n_families": (1, 6), "n_distinct_colors": (1, 6)}
    for name, value in overrides.items():
        if type(value) is not int:
            raise TypeError(f"{name} must be an integer")
        low, high = bounds[name]
        if not low <= value <= high:
            raise ValueError(f"{name} must be in {low}..{high}")
    if "n_components" in overrides:
        for name in ("n_families", "n_distinct_colors"):
            if overrides.get(name, 1) > overrides["n_components"]:
                error = ValueError(f"{name} cannot exceed n_components")
                error.incompatible_axes = ("n_components", name)
                raise error
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    phase = sample_index % LESSON_SCHEDULE_PERIOD
    teaching = phase % 2 == 0
    required = max(2, overrides.get("n_families", 1), overrides.get("n_distinct_colors", 1))
    # Weight supplemental sizes/classes by their number of relation matrices.
    # This avoids overproducing the same all-equal/all-distinct small outputs.
    count_options = ((4,) if teaching else
                     tuple(n for n in (2, 3, 5)
                           for _ in range(sum(len(_partitions(n, f)) for f in range(1, n + 1))))
                     if phase == 1 else (6,))
    count_options = tuple(v for v in count_options if v >= required) or (required,)
    count = _draw_int(ctx, "n_components", 2, 6, count_options)
    family_defaults = ((count - 1,) if phase == 0 else (min(2, count),) if teaching else
                       tuple(f for f in range(1, count + 1) for _ in _partitions(count, f)))
    families = _draw_int(ctx, "n_families", 1, count, family_defaults)
    n_colors = _draw_int(ctx, "n_distinct_colors", 1, count, (count,) if teaching else range(1, count + 1))
    if teaching:
        profile = ctx.draw_choice("canonical_profile", ((12, 14), (13, 15), (12, 16), (13, 16)))
        heights, widths = (profile[0],), (profile[1],)
    else:
        heights = range(8, 14) if difficulty == "easy" else range(10, 17) if difficulty != "hard" else range(12, 19)
        widths = range(12, 18) if difficulty == "easy" else range(13, 21) if difficulty != "hard" else range(15, 23)
    height = _draw_int(ctx, "grid_h", 8, 18, heights)
    width = _draw_int(ctx, "grid_w", 12, 22, widths)
    rng = ctx.draw_rng("shape_assignment_and_layout")
    shapes = _shape_list(rng, count, families, teaching, difficulty)
    keys = [_rotation_key(shape) for shape in shapes]
    colors = _color_sequence(rng, count, n_colors, keys, teaching)
    grid = full_grid(height, width, 0)
    slots = sorted(rng.sample([(r, c) for r in range(2) for c in range(3)], count))
    row_edges, col_edges = (0, height // 2, height), (0, width // 3, 2 * width // 3, width)
    # Reserve each slot's last row/column as background. All six 3x3 motifs
    # fit on the 8x12 boundary without failed or silently dropped placements.
    tier_offsets = [rng.randrange(row_edges[t + 1] - row_edges[t] - 3) for t in range(2)]
    for shape, color, (tier, column) in zip(shapes, colors, slots):
        shape_h = max(r for r, c in shape) + 1
        shape_w = max(c for r, c in shape) + 1
        row = row_edges[tier] + (tier_offsets[tier] if teaching else
              rng.randrange(row_edges[tier + 1] - row_edges[tier] - shape_h))
        col = col_edges[column] + rng.randrange(col_edges[column + 1] - col_edges[column] - shape_w)
        for dr, dc in shape:
            grid[row + dr][col + dc] = color
    return grid


# Pure diagnostics below never supply generation labels. Public lessons and
# witness checks obtain all labels from the selected Racket authority.
def _rotation_matrix(grid):
    return _matrix([_rotation_key(obj[3]) for obj in _components(grid)])


def _area_bbox(grid):
    return _matrix([(len(obj[3]), tuple(sorted((max(r for r, c in obj[3]) + 1,
                                               max(c for r, c in obj[3]) + 1))))
                    for obj in _components(grid)])


def _reflections(grid):
    return _matrix([min(_rotation_key(obj[3]), _rotation_key(_mirror(obj[3])))
                    for obj in _components(grid)])


def _translation_only(grid):
    return _matrix([obj[3] for obj in _components(grid)])


def _color_order(grid):
    return _matrix([_rotation_key(obj[3]) for obj in sorted(_components(grid), key=lambda obj: (obj[2], obj[0], obj[1]))])


def _fixed_four(grid):
    actual = _rotation_matrix(grid)
    return [[5 if r == c else actual[r][c] if r < len(actual) and c < len(actual) else 0
             for c in range(4)] for r in range(4)]


def _first_pair(grid):
    result = _rotation_matrix(grid)
    if len(result) >= 2:
        result[0][1] = result[1][0] = 8
    return result


SEMANTIC_RIVALS = {
    "area_bbox": _area_bbox, "reflections": _reflections,
    "translation_only": _translation_only, "color_order": _color_order,
    "fixed_four": _fixed_four, "first_pair": _first_pair,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {name: rival for name, rival in SEMANTIC_RIVALS.items()
                      if name != "translation_only"}


def _refutes(name, grid):
    return SEMANTIC_RIVALS[name](grid) != _rotation_matrix(grid)


SEMANTIC_WITNESSES = {name: (lambda grid, name=name: _refutes(name, grid))
                      for name in SEMANTIC_RIVALS}
WITNESS_RIVALS = {name: [name] for name in SEMANTIC_RIVALS}


def lesson_identifiable(demos, query):
    """Finite declared-rival ambiguity check using supplied reference labels."""
    return [f"{name} fits every demonstration but changes the query"
            for name, rival in LESSON_COMPETITORS.items()
            if all(rival(pair["input"]) == pair["output"] for pair in demos)
            and rival(query["input"]) != query["output"]]
