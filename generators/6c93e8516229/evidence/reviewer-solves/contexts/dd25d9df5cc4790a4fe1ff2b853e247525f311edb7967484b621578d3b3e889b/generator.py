"""Input sampler for topology-based recoloring of green components.

The canonical Racket rule finds 4-connected color-3 components.  A component
with at least one degree-3 cell becomes red (2); otherwise a component with
exactly two orthogonal turns becomes magenta (6); every other component becomes
blue (1).  Outputs remain owned by the Racket authority.
"""
from __future__ import annotations

from collections.abc import Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "6c93e8516229"
TASK_ID = GENERATOR_ID
RULE_HASH = "6b0505b049ac"
VERSION = "3.0.1"
SUMMARY = (
    "A 0-background grid contains 3-8 separated green (3) tree components. "
    "Each board includes all three canonical topology classes: degree-3 "
    "T-junctions recolor red (2), exactly-two-corner paths recolor magenta "
    "(6), and all other paths/junctions recolor blue (1). Canonical-sized "
    "profiles and explicit degree-4/three-corner counterexamples prevent "
    "position, generic-junction, and at-least-two-corners shortcuts."
)

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.05

INVARIANTS = [
    "background is color 0 and every source component is color 3",
    "3-8 pairwise 4-disconnected tree components",
    "every generated board contains blue, magenta, and red rule classes",
    "sample-index schedule includes a degree-4 blue and a three-corner blue",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "canonical-profile weighted",
        "valid": "10..19",
    },
    "grid_w": {
        "type": "int",
        "default": "canonical-profile weighted",
        "valid": "11..21",
    },
    "component_count": {
        "type": "int",
        "default": "canonical-profile weighted",
        "valid": "3..8",
    },
}

# (height, width, component count), taken from the four canonical inputs.
_CANONICAL_PROFILES = ((10, 11, 3), (19, 21, 8), (14, 12, 5), (14, 16, 6))
_PROFILE_BY_SHAPE = {(h, w): count for h, w, count in _CANONICAL_PROFILES}
_DIRECTIONS = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _normalize(cells):
    unique = set(cells)
    min_r = min(r for r, _c in unique)
    min_c = min(c for _r, c in unique)
    return tuple(sorted((r - min_r, c - min_c) for r, c in unique))


def _transforms(cells):
    """All distinct D4 transforms, normalized to a zero-based bounding box."""
    source = tuple(cells)
    result = set()
    for reflected in (False, True):
        points = [(r, -c if reflected else c) for r, c in source]
        for turns in range(4):
            current = points
            for _ in range(turns):
                current = [(c, -r) for r, c in current]
            result.add(_normalize(current))
    return tuple(sorted(result))


def _shape_stats(cells):
    points = set(cells)
    corners = 0
    degree3 = 0
    degree4 = 0
    edges = 0
    for r, c in points:
        neighbors = [
            (dr, dc)
            for dr, dc in _DIRECTIONS
            if (r + dr, c + dc) in points
        ]
        edges += len(neighbors)
        if len(neighbors) == 2:
            first, second = neighbors
            if first[0] != second[0] and first[1] != second[1]:
                corners += 1
        elif len(neighbors) == 3:
            degree3 += 1
        elif len(neighbors) == 4:
            degree4 += 1
    color = 2 if degree3 else (6 if corners == 2 else 1)
    return {
        "size": len(points),
        "corners": corners,
        "degree3": degree3,
        "degree4": degree4,
        "edges": edges // 2,
        "color": color,
    }


# Compact forms make every exact axis product constructive on a 10x11 canvas.
_BLUE_REGULAR = (
    ((0, 0), (1, 0), (1, 1)),  # 3-cell L: one corner
    ((0, 0), (0, 1), (0, 2)),  # line: zero corners
    ((0, 0), (1, 0), (2, 0), (2, 1), (2, 2)),  # longer L
    ((0, 0), (0, 1), (0, 2), (0, 3), (0, 4)),
)
_BLUE_PLUS = (((0, 1), (1, 0), (1, 1), (1, 2), (2, 1)),)
_BLUE_THREE_CORNERS = (((0, 0), (0, 1), (1, 1), (1, 2), (2, 2)),)
_MAGENTA = (
    ((0, 0), (1, 0), (1, 1), (2, 1)),  # compact S path
    ((0, 0), (1, 0), (1, 1), (1, 2), (0, 2)),  # U, 2 corners
    ((0, 0), (1, 0), (2, 0), (2, 1), (2, 2), (1, 2), (0, 2)),
    ((0, 0), (1, 0), (2, 0), (2, 1), (2, 2), (2, 3), (1, 3)),
)
_RED = (
    ((0, 0), (0, 1), (0, 2), (1, 1)),  # compact T
    ((0, 0), (0, 1), (0, 2), (1, 1), (2, 1)),
    ((0, 0), (1, 0), (2, 0), (1, 1), (1, 2)),
    ((0, 0), (0, 1), (0, 2), (0, 3), (1, 2), (2, 2)),
)

_POOLS = {
    "blue": _BLUE_REGULAR,
    "blue_plus": _BLUE_PLUS,
    "blue_three_corners": _BLUE_THREE_CORNERS,
    "magenta": _MAGENTA,
    "red": _RED,
}
_EXPECTED_COLORS = {
    "blue": 1,
    "blue_plus": 1,
    "blue_three_corners": 1,
    "magenta": 6,
    "red": 2,
}

# Fail at import if an edited prototype ceases to exercise its named branch.
for _name, _prototypes in _POOLS.items():
    for _prototype in _prototypes:
        _stats = _shape_stats(_prototype)
        if _stats["color"] != _EXPECTED_COLORS[_name]:
            raise AssertionError(f"prototype {_name} has wrong topology: {_stats}")


def _components(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    result = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != 3 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in _DIRECTIONS:
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and grid[nr][nc] == 3
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            result.append(cells)
    return result


def _validate_override_values(overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    bounds = {"grid_h": (10, 19), "grid_w": (11, 21), "component_count": (3, 8)}
    for name, value in overrides.items():
        if value is None:
            continue
        if type(value) is not int:
            raise ValueError(f"{name} must be an integer, not {type(value).__name__}")
        lo, hi = bounds[name]
        if not lo <= value <= hi:
            raise ValueError(f"{name}={value} outside [{lo}, {hi}]")


def _anchor_profile(sample_index, difficulty):
    if difficulty == "easy":
        profiles = (_CANONICAL_PROFILES[0], _CANONICAL_PROFILES[2])
    elif difficulty == "hard":
        profiles = (_CANONICAL_PROFILES[1], _CANONICAL_PROFILES[3])
    else:
        profiles = _CANONICAL_PROFILES
    return profiles[sample_index % len(profiles)]


def _draw_weighted_axis(ctx, name, lo, hi, anchor):
    # All legal values remain selectable and overrideable. Repeating the current
    # canonical anchor makes exact-profile support reliable without replaying a
    # canonical layout.
    options = list(range(lo, hi + 1)) + [anchor] * 128
    return ctx.draw_choice(name, options)


def _partition(total, count, rng):
    """Return count nonempty bands separated by one blank row/column."""
    usable = total - (count - 1)
    if usable < 2 * count:
        raise ValueError("canvas is too small for separated component bands")
    base, remainder = divmod(usable, count)
    sizes = [base + (index < remainder) for index in range(count)]
    rng.shuffle(sizes)
    bands = []
    start = 0
    for size in sizes:
        bands.append((start, size))
        start += size + 1
    return bands


def _slots(h, w, component_count, rng):
    columns = min(3, component_count)
    rows = (component_count + columns - 1) // columns
    row_bands = _partition(h, rows, rng)
    col_bands = _partition(w, columns, rng)
    slots = [(r0, c0, rh, cw) for r0, rh in row_bands for c0, cw in col_bands]
    rng.shuffle(slots)
    return slots


def _class_specs(component_count, sample_index, rng):
    # Alternating the two counterexamples makes every three-of-four query
    # rotation retain at least one witness against each canonical-fitting rival.
    phase = sample_index % 2
    special_blue = "blue_plus" if phase == 0 else "blue_three_corners"
    specs = [special_blue, "magenta", "red"]
    extras = ["blue", "magenta", "red"] * 2
    rng.shuffle(extras)
    specs.extend(extras[: component_count - 3])
    # Keep the special first so it receives a 3x3-capable slot on dense boards;
    # shuffle every other class to remove fixed position/color shortcuts.
    tail = specs[1:]
    rng.shuffle(tail)
    return [specs[0], *tail]


def _shape_options(spec, difficulty, slot_h, slot_w):
    candidates = []
    for prototype in _POOLS[spec]:
        for cells in _transforms(prototype):
            height = max(r for r, _c in cells) + 1
            width = max(c for _r, c in cells) + 1
            if height <= slot_h and width <= slot_w:
                candidates.append((cells, height, width))
    if difficulty == "easy":
        candidates.sort(key=lambda item: (len(item[0]), item[1] * item[2]))
    elif difficulty == "hard":
        candidates.sort(key=lambda item: (-len(item[0]), -(item[1] * item[2])))
    return candidates


def _choose_slot_and_shape(spec, slots, difficulty, rng):
    choices = []
    for slot_index, (_r0, _c0, slot_h, slot_w) in enumerate(slots):
        options = _shape_options(spec, difficulty, slot_h, slot_w)
        if options:
            choices.append((slot_index, options))
    if not choices:
        raise RuntimeError(f"no slot can fit required {spec} component")
    slot_index, options = rng.choice(choices)
    # Easy emphasizes compact forms, hard larger forms, medium uses all. The
    # keyed RNG still varies rotations and alternatives within that ordering.
    if difficulty == "easy":
        cutoff = max(1, len(options) // 2)
        shape = rng.choice(options[:cutoff])
    elif difficulty == "hard":
        cutoff = max(1, len(options) // 2)
        shape = rng.choice(options[:cutoff])
    else:
        shape = rng.choice(options)
    slot = slots.pop(slot_index)
    return slot, shape


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_override_values(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    anchor_h, anchor_w, anchor_count = _anchor_profile(sample_index, difficulty)
    h = _draw_weighted_axis(ctx, "grid_h", 10, 19, anchor_h)
    w = _draw_weighted_axis(ctx, "grid_w", 11, 21, anchor_w)
    component_count = _draw_weighted_axis(
        ctx, "component_count", 3, 8, anchor_count
    )

    grid = full_grid(h, w, 0)
    layout_rng = ctx.draw_rng("layout")
    slots = _slots(h, w, component_count, layout_rng)
    specs = _class_specs(component_count, sample_index, ctx.draw_rng("class_mix"))

    for index, spec in enumerate(specs):
        rng = ctx.draw_rng(f"component_{index}_{spec}")
        slot, (shape, shape_h, shape_w) = _choose_slot_and_shape(
            spec, slots, difficulty, rng
        )
        r0, c0, slot_h, slot_w = slot
        row_offset = rng.randint(0, slot_h - shape_h)
        col_offset = rng.randint(0, slot_w - shape_w)
        for dr, dc in shape:
            grid[r0 + row_offset + dr][c0 + col_offset + dc] = 3

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise RuntimeError(f"constructive generator produced invalid grid: {errors}")
    return grid


def observe_overrides(grid):
    errors = self_check(grid)
    if errors:
        raise ValueError(f"cannot observe malformed task grid: {errors}")
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "component_count": len(_components(grid)),
    }


def self_check(grid, *, difficulty=None, meta=None):
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        return ["grid must be a nonempty list of nonempty rows"]
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        return ["ragged grid"]
    if any(type(value) is not int for row in grid for value in row):
        return ["grid cells must be integers, not booleans or other types"]
    height = len(grid)
    errors = []
    if not (10 <= height <= 19 and 11 <= width <= 21):
        errors.append(f"grid shape {height}x{width} outside 10..19 by 11..21")
    palette = {value for row in grid for value in row}
    if not palette <= {0, 3}:
        errors.append(f"unexpected colors: {sorted(palette - {0, 3})}")
    if 3 not in palette:
        errors.append("no green components")
        return errors

    components = _components(grid)
    if not 3 <= len(components) <= 8:
        errors.append(f"component count {len(components)} outside 3..8")
    classes = set()
    for index, cells in enumerate(components):
        stats = _shape_stats(cells)
        classes.add(stats["color"])
        if not 3 <= stats["size"] <= 12:
            errors.append(f"component {index} size {stats['size']} outside 3..12")
        if stats["edges"] != stats["size"] - 1:
            errors.append(f"component {index} is not a tree")
    missing = {1, 2, 6} - classes
    if missing:
        errors.append(f"missing topology output classes: {sorted(missing)}")
    return errors


def strict_canonical_like(grid):
    errors = self_check(grid)
    if errors:
        return errors
    profile = (len(grid), len(grid[0]), len(_components(grid)))
    if profile not in _CANONICAL_PROFILES:
        return [f"profile {profile} is outside the four canonical profiles"]
    return []


def _solve_with_classifier(grid, classifier: Callable[[dict], int]):
    result = [row[:] for row in grid]
    for cells in _components(grid):
        color = classifier(_shape_stats(cells))
        for r, c in cells:
            result[r][c] = color
    return result


def _canonical_color(stats):
    return 2 if stats["degree3"] else (6 if stats["corners"] == 2 else 1)


def _any_junction_red_color(stats):
    return 2 if stats["degree3"] or stats["degree4"] else (
        6 if stats["corners"] == 2 else 1
    )


def _at_least_two_corners_color(stats):
    return 2 if stats["degree3"] else (6 if stats["corners"] >= 2 else 1)


def _solve_canonical(grid):
    return _solve_with_classifier(grid, _canonical_color)


def _rival_any_junction_red(grid):
    return _solve_with_classifier(grid, _any_junction_red_color)


def _rival_at_least_two_corners_magenta(grid):
    return _solve_with_classifier(grid, _at_least_two_corners_color)


def _has_degree4_blue(grid):
    return any(
        (stats := _shape_stats(cells))["color"] == 1 and stats["degree4"] > 0
        for cells in _components(grid)
    )


def _has_three_corner_blue(grid):
    return any(
        (stats := _shape_stats(cells))["color"] == 1 and stats["corners"] >= 3
        for cells in _components(grid)
    )


SEMANTIC_WITNESSES = {
    "degree4_is_not_tjunction": _has_degree4_blue,
    "three_corners_is_not_exactly_two": _has_three_corner_blue,
}
SEMANTIC_RIVALS = {
    "any_junction_red": _rival_any_junction_red,
    "at_least_two_corners_magenta": _rival_at_least_two_corners_magenta,
}
WITNESS_RIVALS = {
    "degree4_is_not_tjunction": ["any_junction_red"],
    "three_corners_is_not_exactly_two": ["at_least_two_corners_magenta"],
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query):
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    errors = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            errors.append(f"demo {index} must contain input and output")
            continue
        errors.extend(f"demo {index}: {reason}" for reason in self_check(pair["input"]))
    if not isinstance(query, dict) or "input" not in query:
        errors.append("query must contain an input")
    else:
        errors.extend(f"query: {reason}" for reason in self_check(query["input"]))
    if errors:
        return errors
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            errors.append(f"demonstrations do not refute {name}")
    return errors
