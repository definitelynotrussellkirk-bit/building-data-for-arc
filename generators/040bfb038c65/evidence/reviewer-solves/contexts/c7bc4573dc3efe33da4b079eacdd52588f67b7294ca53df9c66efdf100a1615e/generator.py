"""Constructive generator for ``Recolor the symmetry outsider``.

Every lawful input contains one D4-shape class repeated two or three times and
one different yellow object.  The canonical rule recolors the unique class to
cyan.  A three-phase lesson schedule deliberately breaks the canonical-fitting
"recolor the largest object" shortcut in every three-demonstration window.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "040bfb038c65"
TASK_ID = GENERATOR_ID
RULE_HASH = "80d289c11e33"
VERSION = "3.0.0"
SUMMARY = (
    "Three or four separated yellow objects occupy independent corner regions. "
    "All but one share a D4-canonical polyomino shape; recolor the unique shape "
    "to cyan. A deterministic three-phase size schedule refutes the plausible "
    "largest-object shortcut in every ordinary lesson."
)

EXAMPLES_NEEDED = 3
LESSON_SCHEDULE_PERIOD = 3
SCHEDULE_PROFILES = ("smaller_odd", "same_size_odd", "larger_odd")

INVARIANTS = [
    "input uses exactly background 0 and yellow 4",
    "three or four 4-connected yellow objects are separated by a blank moat",
    "one D4-canonical shape occurs once and the other occurs two or three times",
    "ordinary three-example windows include smaller- and equal-size counterexamples to the largest-object shortcut",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "canonical 7",
        "valid": "7..14",
        "doc": "Grid height.",
    },
    "grid_w": {
        "type": "int",
        "default": "canonical 9 or 10",
        "valid": "9..16",
        "doc": "Grid width.",
    },
    "n_majority": {
        "type": "int",
        "default": "2 (easy), 2..3 (medium), 3 (hard)",
        "valid": "2..3",
        "doc": "Copies of the majority D4-shape class (plus one oddball).",
    },
    "texture": {
        "type": "str",
        "default": "3-phase lesson schedule",
        "valid": "smaller_odd|same_size_odd|larger_odd",
        "doc": "Cell-count relation between the oddball and majority objects.",
    },
}
# Four independent 3x3 regions fit on the minimum 7x9 canvas, so every
# advertised cross-product is constructive in every difficulty band.
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []


def _norm(cells):
    """Translate cells to the origin and return a stable immutable form."""
    top = min(row for row, _ in cells)
    left = min(col for _, col in cells)
    return tuple(sorted((row - top, col - left) for row, col in cells))


def _transforms(cells):
    """Return the distinct D4 transforms of a polyomino."""
    original = list(_norm(cells))
    variants = set()
    for reflected in (False, True):
        current = (
            [(row, -col) for row, col in original]
            if reflected
            else list(original)
        )
        for _ in range(4):
            variants.add(_norm(current))
            current = [(col, -row) for row, col in current]
    return tuple(sorted(variants))


def _d4(cells):
    """Canonical D4 signature."""
    return min(_transforms(cells))


def _bbox(cells):
    normalized = _norm(cells)
    return (
        max(row for row, _ in normalized) + 1,
        max(col for _, col in normalized) + 1,
    )


def _free_polyominoes(size):
    """Enumerate free polyominoes of ``size`` cells, deterministically."""
    shapes = {((0, 0),)}
    for _ in range(1, size):
        grown = set()
        for shape in shapes:
            occupied = set(shape)
            for row, col in shape:
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    neighbor = row + dr, col + dc
                    if neighbor not in occupied:
                        grown.add(_d4((*shape, neighbor)))
        shapes = grown
    return tuple(sorted(shapes))


# Every listed shape fits one of the four independent 3x3 placement regions.
_SHAPES_BY_SIZE = {
    size: tuple(shape for shape in _free_polyominoes(size) if max(_bbox(shape)) <= 3)
    for size in (3, 4, 5)
}
_ASYMMETRIC_BY_SIZE = {
    size: tuple(shape for shape in shapes if len(_transforms(shape)) >= 2)
    for size, shapes in _SHAPES_BY_SIZE.items()
}


def schedule_profile(seed, sample_index, difficulty=None):
    """Return the seed-independent semantic slot used by lesson assembly."""
    del seed, difficulty
    return SCHEDULE_PROFILES[sample_index % LESSON_SCHEDULE_PERIOD]


def _validate_call(seed, sample_index, difficulty, overrides):
    if type(seed) is not int:
        raise TypeError("seed must be a literal integer")
    if type(sample_index) is not int:
        raise TypeError("sample_index must be a literal integer")
    if sample_index < 0:
        raise ValueError("sample_index must be nonnegative")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, easy, medium or hard")
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")


def _draw_int_axis(ctx, name, lo, hi, defaults):
    """Honor exact overrides over the entire advertised domain."""
    if ctx.overrides.get(name) is not None:
        return ctx.draw_int_strict(name, lo, hi)
    return ctx.draw_choice(name, tuple(defaults))


def _draw_texture(ctx, sample_index):
    if ctx.overrides.get("texture") is not None:
        value = ctx.overrides["texture"]
        if type(value) is not str:
            raise TypeError("texture must be a string")
        return ctx.draw_choice("texture", SCHEDULE_PROFILES)
    scheduled = SCHEDULE_PROFILES[sample_index % LESSON_SCHEDULE_PERIOD]
    return ctx.draw_choice("texture", (scheduled,))


def _size_pairs(texture, difficulty):
    """Lawful majority/odd cell-count pairs, with difficulty-only weighting."""
    if texture == "same_size_odd":
        if difficulty == "easy":
            return ((3, 3), (3, 3), (4, 4))
        if difficulty == "hard":
            return ((4, 4), (5, 5), (5, 5))
        return ((3, 3), (4, 4), (5, 5))
    if texture == "smaller_odd":
        if difficulty == "easy":
            return ((4, 3), (4, 3), (5, 3))
        if difficulty == "hard":
            return ((5, 3), (5, 4), (5, 4))
        return ((4, 3), (5, 3), (5, 4))
    if difficulty == "easy":
        return ((3, 4), (3, 4), (3, 5))
    if difficulty == "hard":
        return ((3, 5), (4, 5), (4, 5))
    return ((3, 4), (3, 5), (4, 5))


def _choose_shapes(ctx, texture, difficulty):
    rng = ctx.draw_rng("shape_classes")
    majority_size, odd_size = rng.choice(_size_pairs(texture, difficulty))
    majority = rng.choice(_ASYMMETRIC_BY_SIZE[majority_size])
    odd_candidates = [
        shape
        for shape in _SHAPES_BY_SIZE[odd_size]
        if _d4(shape) != _d4(majority)
    ]
    if not odd_candidates:  # Defensive: the finite catalog currently always has one.
        raise RuntimeError("no distinct oddball shape for requested size relation")
    return majority, rng.choice(odd_candidates)


def _slot_origins(height, width):
    """Four disjoint 3x3 boxes with at least one blank row/column between."""
    return ((0, 0), (0, width - 3), (height - 3, 0), (height - 3, width - 3))


def _paint_in_slot(grid, shape, origin, rng):
    shape_h, shape_w = _bbox(shape)
    row0 = origin[0] + rng.randint(0, 3 - shape_h)
    col0 = origin[1] + rng.randint(0, 3 - shape_w)
    for row, col in shape:
        target = row0 + row, col0 + col
        if grid[target[0]][target[1]] != 0:
            raise RuntimeError("constructive slot placement collided")
        grid[target[0]][target[1]] = 4


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(seed, sample_index, difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    # Ordinary production stays exactly on the canonical size/palette profiles;
    # explicit controls expose a broader, still constructive geometric domain.
    height_defaults = (7,) * 32 + tuple(range(8, 15))
    width_defaults = (9, 10) * 16 + tuple(range(11, 17))
    height = _draw_int_axis(ctx, "grid_h", 7, 14, height_defaults)
    width = _draw_int_axis(ctx, "grid_w", 9, 16, width_defaults)
    default_majorities = {
        "easy": (2,),
        "medium": (2, 3),
        "hard": (3,),
        None: (2, 3),
    }[difficulty]
    n_majority = _draw_int_axis(ctx, "n_majority", 2, 3, default_majorities)
    texture = _draw_texture(ctx, sample_index)

    majority, odd = _choose_shapes(ctx, texture, difficulty)
    majority_variants = list(_transforms(majority))
    orientation_rng = ctx.draw_rng("orientations")
    orientation_rng.shuffle(majority_variants)
    majority_shapes = [
        majority_variants[index % len(majority_variants)]
        for index in range(n_majority)
    ]
    odd_shape = orientation_rng.choice(_transforms(odd))

    slot_rng = ctx.draw_rng("object_slots")
    selected_slots = sorted(slot_rng.sample(range(4), n_majority + 1))
    # Equal-size inputs use the last selected region for the oddball, ensuring
    # the row-major largest-object tie-break selects an earlier majority object.
    odd_slot = (
        selected_slots[-1]
        if texture == "same_size_odd"
        else slot_rng.choice(selected_slots)
    )

    grid = full_grid(height, width, 0)
    origins = _slot_origins(height, width)
    majority_iter = iter(majority_shapes)
    placement_rng = ctx.draw_rng("placement_offsets")
    for slot in selected_slots:
        shape = odd_shape if slot == odd_slot else next(majority_iter)
        _paint_in_slot(grid, shape, origins[slot], placement_rng)
    return grid


def _grid_error(grid):
    if not isinstance(grid, list) or not grid:
        return "grid must be a non-empty list of rows"
    if not all(isinstance(row, list) and row for row in grid):
        return "every row must be a non-empty list"
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return "grid must be rectangular"
    if any(type(value) is not int for row in grid for value in row):
        return "grid cells must be literal integers"
    return None


def _components(grid, color=4):
    height, width = len(grid), len(grid[0])
    seen = set()
    result = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] != color or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells = []
            while stack:
                current = stack.pop()
                cells.append(current)
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    neighbor = current[0] + dr, current[1] + dc
                    if (
                        0 <= neighbor[0] < height
                        and 0 <= neighbor[1] < width
                        and grid[neighbor[0]][neighbor[1]] == color
                        and neighbor not in seen
                    ):
                        seen.add(neighbor)
                        stack.append(neighbor)
            result.append(tuple(sorted(cells)))
    return sorted(result, key=min)


def self_check(grid, *, difficulty=None, meta=None):
    """Validate the exact two-class odd-one-out input grammar."""
    del difficulty, meta
    malformed = _grid_error(grid)
    if malformed:
        return [malformed]

    messages = []
    colors = {value for row in grid for value in row}
    if colors != {0, 4}:
        messages.append(f"expected exactly colors [0, 4], got {sorted(colors)}")
        return messages

    blobs = _components(grid)
    if not 3 <= len(blobs) <= 4:
        messages.append(f"expected 3-4 yellow(4) objects, got {len(blobs)}")
        return messages

    signatures = [_d4(blob) for blob in blobs]
    counts = Counter(signatures)
    class_counts = sorted(counts.values())
    if len(counts) != 2 or class_counts[0] != 1 or class_counts[1] != len(blobs) - 1:
        messages.append(
            "expected exactly one singleton D4 class and one repeated class; "
            f"got class counts {class_counts}"
        )
    return messages


def strict_canonical_like(grid):
    """The task manifold is exactly the grammar checked above."""
    return self_check(grid)


def _class_roles(grid):
    blobs = _components(grid)
    counts = Counter(_d4(blob) for blob in blobs)
    oddballs = [blob for blob in blobs if counts[_d4(blob)] == 1]
    majorities = [blob for blob in blobs if counts[_d4(blob)] > 1]
    if len(oddballs) != 1 or not majorities:
        raise ValueError("grid does not contain one singleton and one repeated D4 class")
    return majorities, oddballs[0]


def observe_overrides(grid):
    """Recover every advertised exact control from a lawful generated grid."""
    findings = self_check(grid)
    if findings:
        raise ValueError("cannot observe controls on invalid grid: " + "; ".join(findings))
    majorities, oddball = _class_roles(grid)
    majority_size = len(majorities[0])
    odd_size = len(oddball)
    texture = (
        "smaller_odd"
        if odd_size < majority_size
        else ("larger_odd" if odd_size > majority_size else "same_size_odd")
    )
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_majority": len(majorities),
        "texture": texture,
    }


def rule_mirror(grid):
    """Independent Python mirror of the selected canonical Racket rule."""
    findings = self_check(grid)
    if findings:
        raise ValueError("rule_mirror requires a lawful input: " + "; ".join(findings))
    _, oddball = _class_roles(grid)
    output = deepcopy(grid)
    for row, col in oddball:
        output[row][col] = 8
    return output


def _largest_yellow_blob(grid):
    """Plausible wrong rule: recolor the largest, row-major on size ties."""
    blobs = _components(grid)
    if not blobs:
        return deepcopy(grid)
    largest_size = max(map(len, blobs))
    winner = next(blob for blob in blobs if len(blob) == largest_size)
    output = deepcopy(grid)
    for row, col in winner:
        output[row][col] = 8
    return output


def _oddball_not_largest(grid):
    try:
        return _largest_yellow_blob(grid) != rule_mirror(grid)
    except (TypeError, ValueError):
        return False


SEMANTIC_RIVALS = {"largest_yellow_blob": _largest_yellow_blob}
SEMANTIC_WITNESSES = {"oddball_not_largest": _oddball_not_largest}
WITNESS_RIVALS = {"oddball_not_largest": ["largest_yellow_blob"]}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query):
    """Report declared wrong rules that fit all demos but alter the query."""
    reasons = []
    for name, rival in LESSON_COMPETITORS.items():
        fits_demos = all(rival(pair["input"]) == pair["output"] for pair in demos)
        changes_query = rival(query["input"]) != query["output"]
        if fits_demos and changes_query:
            reasons.append(f"{name} fits every demonstration but changes the query")
    return reasons
