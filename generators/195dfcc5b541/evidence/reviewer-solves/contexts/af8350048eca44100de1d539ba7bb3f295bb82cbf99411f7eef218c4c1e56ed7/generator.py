"""Constructive input sampler for task 195dfcc5b541.

A compact color-8 object is a stencil.  Every color-3 occurrence of that
stencil under a rotation *or reflection* is recolored to 8 by the unchanged
canonical Racket authority.  This module samples dense canonical-style inputs;
it does not generate labels.

The sampler deliberately plants both an orientation-preserving copy and a
reflection-only copy of a chiral stencil.  That makes every generated example a
counterexample to the strongest shortcut supported by the canonical training
pairs: "match rotations, but ignore reflections".
"""
from __future__ import annotations

from copy import deepcopy

from puzzle_generators.base import gen_ctx

GENERATOR_ID = "195dfcc5b541"
TASK_ID = GENERATOR_ID
RULE_HASH = "22e420574f26"
VERSION = "3.0.0"
SUMMARY = (
    "Dense 0/2/3/4/7 noise contains one color-8 chiral stencil and two to "
    "four isolated color-3 dihedral copies.  At least one copy is a true "
    "reflection, so rotations-only rules fail; the selected Racket rule "
    "recolors all matching copy cells to 8."
)

INVARIANTS = [
    "exactly one 8-connected color-8 stencil of four or five cells",
    "two to four isolated color-3 copies, including a rotation and a reflection-only copy",
    "all other color-3 cells are isolated singletons, preventing accidental composite matches",
    "the full canonical palette 0/2/3/4/7/8 appears in a dense noisy field",
    "the canonical rule changes the input and disagrees with the rotations-only rival",
]

AXES = {
    "grid_h": {"type": "int", "default": "weighted 11..18", "valid": "11..18"},
    "grid_w": {"type": "int", "default": "weighted 17..18", "valid": "17..18"},
    "shape_variant": {"type": "int", "default": "uniform 0..1", "valid": "0..1"},
    "copy_count": {"type": "int", "default": "weighted 2..4", "valid": "2..4"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

# Variant 0 is the chiral tetromino from canonical train[1].  Variant 1 is a
# compact chiral pentomino, extending support to the canonical stencil-size
# range while retaining a reflection branch that rotations cannot mimic.
_SHAPES = (
    ((0, 0), (0, 2), (1, 1), (1, 2)),
    ((0, 0), (0, 1), (1, 0), (1, 1), (2, 0)),
)
_ALLOWED_COLORS = frozenset((0, 2, 3, 4, 7, 8))
_NOISE_PALETTE = (0, 0, 0, 2, 2, 4, 4, 7, 7, 7)
_NEIGHBORS_8 = tuple(
    (dr, dc)
    for dr in (-1, 0, 1)
    for dc in (-1, 0, 1)
    if dr or dc
)


def _norm(cells):
    cells = tuple(cells)
    if not cells:
        raise ValueError("cannot normalize an empty shape")
    min_row = min(row for row, _ in cells)
    min_col = min(col for _, col in cells)
    return tuple(sorted((row - min_row, col - min_col) for row, col in cells))


def _rotate(cells):
    return _norm((col, -row) for row, col in cells)


def _reflect(cells):
    return _norm((row, -col) for row, col in cells)


def _rotations(cells):
    result = []
    shape = _norm(cells)
    for _ in range(4):
        result.append(shape)
        shape = _rotate(shape)
    return tuple(result)


def _dihedral(cells):
    rotations = _rotations(cells)
    return rotations + tuple(_reflect(shape) for shape in rotations)


def _bbox(cells):
    shape = _norm(cells)
    return max(row for row, _ in shape) + 1, max(col for _, col in shape) + 1


def _at(shape, row0, col0):
    return frozenset((row0 + row, col0 + col) for row, col in shape)


def _halo(cells, height, width):
    return frozenset(
        (row + dr, col + dc)
        for row, col in cells
        for dr in (-1, 0, 1)
        for dc in (-1, 0, 1)
        if 0 <= row + dr < height and 0 <= col + dc < width
    )


def _components_8(grid, color):
    height, width = len(grid), len(grid[0])
    seen = set()
    components = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] != color or (row, col) in seen:
                continue
            component = []
            stack = [(row, col)]
            seen.add((row, col))
            while stack:
                point = stack.pop()
                component.append(point)
                for dr, dc in _NEIGHBORS_8:
                    nxt = point[0] + dr, point[1] + dc
                    if not (0 <= nxt[0] < height and 0 <= nxt[1] < width):
                        continue
                    if nxt in seen or grid[nxt[0]][nxt[1]] != color:
                        continue
                    seen.add(nxt)
                    stack.append(nxt)
            components.append(component)
    return components


def _rule_output(grid, *, include_reflections=True):
    """Independent geometry implementation matching the selected Racket rule.

    This is used only for sampler validation, observability, and declared rival
    probes.  Authoritative labels are still produced by the Racket program.
    """
    height, width = len(grid), len(grid[0])
    matches = []
    for component in _components_8(grid, 8):
        base = _norm(component)
        rotations = _rotations(base)
        variants = [(0, shape) for shape in rotations]
        if include_reflections:
            variants.extend((1, _reflect(shape)) for shape in rotations)
        # The Racket program prepends each candidate and then stably sorts only
        # by (flip-rank,row,column).  insert(0, ...) preserves that tie order.
        for flip_rank, shape in variants:
            shape_h, shape_w = _bbox(shape)
            for row0 in range(height - shape_h + 1):
                for col0 in range(width - shape_w + 1):
                    cells = tuple((row0 + row, col0 + col) for row, col in shape)
                    if all(grid[row][col] == 3 for row, col in cells):
                        matches.insert(0, (flip_rank, row0, col0, cells))
    matches.sort(key=lambda item: item[:3])
    output = deepcopy(grid)
    used = set()
    for _, _, _, cells in matches:
        if used.intersection(cells):
            continue
        used.update(cells)
        for row, col in cells:
            output[row][col] = 8
    return output


def _intended_rule(grid):
    return _rule_output(grid, include_reflections=True)


def _rotation_only(grid):
    """Plausible rival: match rotations of the stencil, but not reflections."""
    return _rule_output(grid, include_reflections=False)


def _weighted_choice(ctx, label, values, favored=()):
    # Keep the complete declared domain available in every difficulty band.
    # Repetition changes only sampling weight; exact overrides remain legal.
    options = list(values) + list(favored) * 4
    return ctx.draw_choice(label, options)


def _draw_axes(ctx, difficulty):
    if difficulty == "easy":
        height_favored = (11, 12, 13)
        width_favored = (17,)
        count_favored = (2,)
    elif difficulty == "hard":
        height_favored = (16, 17, 18)
        width_favored = (18,)
        count_favored = (4,)
    elif difficulty == "medium":
        height_favored = (13, 14, 15, 16)
        width_favored = (17, 18)
        count_favored = (3,)
    else:
        height_favored = ()
        width_favored = ()
        count_favored = ()
    height = _weighted_choice(ctx, "grid_h", range(11, 19), height_favored)
    width = _weighted_choice(ctx, "grid_w", range(17, 19), width_favored)
    shape_variant = ctx.draw_choice("shape_variant", (0, 1))
    copy_count = _weighted_choice(ctx, "copy_count", range(2, 5), count_favored)
    return height, width, shape_variant, copy_count


def _stencil_candidates(height, width, shape, region):
    shape_h, shape_w = _bbox(shape)
    rows = range(height - shape_h + 1)
    cols = range(width - shape_w + 1)
    candidates = []
    for row in rows:
        for col in cols:
            on_top = row == 0
            on_bottom = row + shape_h == height
            on_left = col == 0
            on_right = col + shape_w == width
            interior = not (on_top or on_bottom or on_left or on_right)
            if region == "top" and on_top:
                candidates.append((row, col))
            elif region == "bottom" and on_bottom:
                candidates.append((row, col))
            elif region == "left" and on_left:
                candidates.append((row, col))
            elif region == "right" and on_right:
                candidates.append((row, col))
            elif region == "interior" and interior:
                candidates.append((row, col))
    return candidates


def _copy_candidates(height, width, shape):
    shape_h, shape_w = _bbox(shape)
    return [
        _at(shape, row, col)
        for row in range(height - shape_h + 1)
        for col in range(width - shape_w + 1)
    ]


def _place_isolated_shapes(height, width, shapes, initial_blocked, rng):
    """Backtrack to place shapes with one-cell Chebyshev separation."""
    candidate_lists = []
    for shape in shapes:
        candidates = _copy_candidates(height, width, shape)
        rng.shuffle(candidates)
        candidate_lists.append(candidates)

    def search(index, blocked, placed):
        if index == len(candidate_lists):
            return tuple(placed)
        for cells in candidate_lists[index]:
            if cells.intersection(blocked):
                continue
            result = search(
                index + 1,
                blocked.union(_halo(cells, height, width)),
                placed + [cells],
            )
            if result is not None:
                return result
        return None

    placements = search(0, frozenset(initial_blocked), [])
    if placements is None:
        raise RuntimeError("constructive placement failed for a documented axis combination")
    return placements


def _paint(grid, cells, color):
    for row, col in cells:
        grid[row][col] = color


def _shape_family(cells):
    normalized = _norm(cells)
    for index, shape in enumerate(_SHAPES):
        if normalized in set(_dihedral(shape)):
            return index
    raise ValueError(f"stencil shape {normalized!r} is not a generated shape family")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name, value in overrides.items():
        if value is not None and type(value) is not int:
            raise ValueError(f"{name} must be an integer, not {type(value).__name__}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    height, width, shape_variant, copy_count = _draw_axes(ctx, difficulty)

    orientation = ctx.draw_int("stencil_orientation", 0, 7)
    stencil_shape = _dihedral(_SHAPES[shape_variant])[orientation]
    region = ctx.draw_choice("stencil_region", ("top", "bottom", "left", "right", "interior"))
    stencil_positions = _stencil_candidates(height, width, stencil_shape, region)
    if not stencil_positions:
        raise RuntimeError(f"no {region} stencil position for {height}x{width}")
    stencil_row, stencil_col = ctx.draw_rng("stencil_position").choice(stencil_positions)
    stencil_cells = _at(stencil_shape, stencil_row, stencil_col)

    rotations = _rotations(stencil_shape)
    reflected = tuple(_reflect(shape) for shape in rotations)
    variant_rng = ctx.draw_rng("copy_variants")
    copy_shapes = [variant_rng.choice(rotations), variant_rng.choice(reflected)]
    all_variants = rotations + reflected
    copy_shapes.extend(variant_rng.choice(all_variants) for _ in range(copy_count - 2))

    placements = _place_isolated_shapes(
        height,
        width,
        copy_shapes,
        _halo(stencil_cells, height, width),
        ctx.draw_rng("copy_positions"),
    )

    background_rng = ctx.draw_rng("background")
    grid = [
        [background_rng.choice(_NOISE_PALETTE) for _ in range(width)]
        for _ in range(height)
    ]
    _paint(grid, stencil_cells, 8)
    copy_cells = frozenset().union(*placements)
    for cells in placements:
        _paint(grid, cells, 3)

    # Add isolated color-3 noise without joining any planted copy component.
    blocked_3 = set()
    for cells in placements:
        blocked_3.update(_halo(cells, height, width))
    distractor_candidates = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if (row, col) not in stencil_cells and (row, col) not in blocked_3
    ]
    distractor_rng = ctx.draw_rng("isolated_three_noise")
    distractor_rng.shuffle(distractor_candidates)
    target_distractors = min(10, max(6, height * width // 24))
    distractors = []
    for point in distractor_candidates:
        if point in blocked_3:
            continue
        distractors.append(point)
        blocked_3.update(_halo((point,), height, width))
        if len(distractors) == target_distractors:
            break
    _paint(grid, distractors, 3)

    # Pin the complete canonical palette on cells outside semantic objects.
    palette_slots = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if (row, col) not in stencil_cells and (row, col) not in copy_cells and (row, col) not in distractors
    ]
    if len(palette_slots) < 4:
        raise RuntimeError("not enough background cells to realize the canonical palette")
    for point, color in zip(palette_slots[:4], (0, 2, 4, 7)):
        grid[point[0]][point[1]] = color

    # Construction itself guarantees the semantic branches.  Keep generate()
    # independent of any solver oracle: the retained tests and semantic gate
    # compare these inputs with the authoritative Racket rule.
    if len(placements) != copy_count:
        raise RuntimeError("constructive placement returned the wrong copy count")
    if _reflect(stencil_shape) in set(rotations):
        raise RuntimeError("selected stencil unexpectedly lost chirality")
    return grid


def _matching_copy_components(grid, stencil):
    """Return isolated color-3 components in the stencil's dihedral orbit."""
    variants = set(_dihedral(_norm(stencil)))
    size = len(stencil)
    return [
        component
        for component in _components_8(grid, 3)
        if len(component) == size and _norm(component) in variants
    ]


def observe_overrides(grid):
    """Recover every advertised exact axis directly from input structure."""
    components = _components_8(grid, 8)
    if len(components) != 1:
        raise ValueError(f"expected one color-8 stencil, found {len(components)}")
    stencil = components[0]
    copy_count = len(_matching_copy_components(grid, stencil))
    if not copy_count:
        raise ValueError("no isolated color-3 stencil copies were observed")
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "shape_variant": _shape_family(stencil),
        "copy_count": copy_count,
    }


def self_check(grid, *, difficulty=None, meta=None):
    """Validate canonical-like structure and actual rule firing."""
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty rectangular grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected a nonempty rectangular grid"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["ragged grid"]
    if any(type(value) is not int for row in grid for value in row):
        return ["cells must be integer ARC colors"]

    height = len(grid)
    errors = []
    if not (11 <= height <= 18 and 17 <= width <= 18):
        errors.append(f"expected canonical noisy size 11..18 x 17..18; got {height}x{width}")

    colors = {value for row in grid for value in row}
    unknown = colors - _ALLOWED_COLORS
    if unknown:
        errors.append(f"unexpected colors {sorted(unknown)}; expected only {sorted(_ALLOWED_COLORS)}")
    missing = _ALLOWED_COLORS - colors
    if missing:
        errors.append(f"missing canonical palette colors {sorted(missing)}")
    if errors:
        return errors

    stencil_components = _components_8(grid, 8)
    if len(stencil_components) != 1:
        errors.append(f"expected exactly one 8-connected color-8 stencil; found {len(stencil_components)}")
    else:
        stencil_size = len(stencil_components[0])
        if stencil_size not in (4, 5):
            errors.append(f"expected a four- or five-cell stencil; got {stencil_size}")

    flat = [value for row in grid for value in row]
    if sum(value != 0 for value in flat) < 0.60 * len(flat):
        errors.append("background is too sparse for the canonical noisy regime")
    if flat.count(3) < 4:
        errors.append("too few color-3 cells to contain a stencil copy")
    if errors:
        return errors

    output = _intended_rule(grid)
    changed = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] != output[row][col]
    ]
    if not changed:
        errors.append("canonical rule is identity: no color-3 stencil copy is present")
    elif any(grid[row][col] != 3 or output[row][col] != 8 for row, col in changed):
        errors.append("canonical rule changes cells other than 3-to-8 stencil matches")
    elif stencil_components and len(changed) % len(stencil_components[0]):
        errors.append("changed-cell count is not a multiple of stencil size")
    return errors


def strict_canonical_like(grid):
    """Accept lawful inputs on the canonical noisy stencil/copy manifold."""
    return self_check(grid)


def _reflection_required(grid):
    return _rotation_only(grid) != _intended_rule(grid)


def lesson_identifiable(demos, query):
    """Reject a lesson when a declared wrong rule fits demos but changes query."""
    reasons = []
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            if rival(query["input"]) != query["output"]:
                reasons.append(f"{name} fits all demonstrations but changes the query answer")
    return reasons


SEMANTIC_WITNESSES = {"reflection_required": _reflection_required}
SEMANTIC_RIVALS = {"rotations_only": _rotation_only}
WITNESS_RIVALS = {"reflection_required": ["rotations_only"]}
CANONICAL_SHORTCUTS = {"rotations_only": _rotation_only}
LESSON_COMPETITORS = {"rotations_only": _rotation_only}
