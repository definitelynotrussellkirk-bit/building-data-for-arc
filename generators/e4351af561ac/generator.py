"""Constructive sampler for rotation-matching color-3 components.

The unchanged canonical rule uses the single color-1 component as a template.
It scans only color-3 components, keeps those equal to the template under one
of the four rotations, and paints every kept cell cyan (8) on an otherwise
blank output.  Reflections are not rotations; matching shapes in other colors
are distractors and must be ignored.

The four-step default schedule deliberately teaches those distinctions.  Steps
0 and 2 stay inside the canonical size/palette profile.  Steps 1 and 3 add a
matching non-3 distractor.  Every step contains a nontrivially rotated match and
an equal-area nonmatch; chiral templates make the first nonmatch a reflection.
Thus any single holdout from a four-pair lesson leaves demonstrations against
the declared translation, reflection, all-green, size-only, and color-agnostic
rivals.  Explicit overrides control one draw and do not promise that schedule.
"""
from __future__ import annotations

from functools import lru_cache
from itertools import combinations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "e4351af561ac"
TASK_ID = GENERATOR_ID
RULE_HASH = "f060a0eb09ab"
VERSION = "4.0.0"
SUMMARY = (
    "Use the single blue (1) component as a shape template. Among green (3) "
    "components, keep exactly those matching the template under translation "
    "and any of four rotations, recoloring them cyan (8); drop the template, "
    "green nonmatches, and matching components in other colors. Generated "
    "lessons include rotated positives, equal-area/reflected negatives, and "
    "color-role distractors while retaining frequent canonical-profile inputs."
)

INVARIANTS = [
    "9..16 by 12..18 integer grid with background 0",
    "exactly one color-1 template of 3..5 four-connected cells fitting 3x3",
    "1..2 color-3 rotational matches and 1..2 color-3 nonmatches",
    "0..1 matching component in a non-1/non-3 distractor color",
    "all components are separated even diagonally; every requested count is realized",
]

AXES = {
    "grid_h": {"type": "int", "default": "canonical 9..10; broad band-weighted", "valid": "9..16"},
    "grid_w": {"type": "int", "default": "canonical 12..13; broad band-weighted", "valid": "12..18"},
    "template_size": {"type": "int", "default": "4 canonical; 4..5 broad", "valid": "3..5"},
    "n_match": {"type": "int", "default": "2 canonical; 1..2 broad", "valid": "1..2"},
    "n_nonmatch": {"type": "int", "default": "1 canonical; 1..2 broad", "valid": "1..2"},
    "n_other_match": {"type": "int", "default": "0 canonical; 1 broad", "valid": "0..1"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []
EXAMPLES_NEEDED = 3
LESSON_SCHEDULE_PERIOD = 4
SCHEDULE_PROFILES = (
    "canonical_chiral_a",
    "color_role_a",
    "canonical_chiral_b",
    "color_role_b",
)

_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))
_NEIGHBORS_8 = tuple((dr, dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1)
                     if (dr, dc) != (0, 0))
_OTHER_COLORS = (2, 4, 5, 6, 7, 9)
_BOUNDS = {
    "grid_h": (9, 16),
    "grid_w": (12, 18),
    "template_size": (3, 5),
    "n_match": (1, 2),
    "n_nonmatch": (1, 2),
    "n_other_match": (0, 1),
}


def schedule_profile(seed, sample_index, difficulty=None):
    return SCHEDULE_PROFILES[sample_index % LESSON_SCHEDULE_PERIOD]


def _norm(cells):
    cells = tuple(cells)
    top = min(r for r, _ in cells)
    left = min(c for _, c in cells)
    return tuple(sorted((r - top, c - left) for r, c in cells))


def _rotate(cells, turns=1):
    result = _norm(cells)
    for _ in range(turns % 4):
        result = _norm((c, -r) for r, c in result)
    return result


def _mirror(cells):
    return _norm((r, -c) for r, c in cells)


def _rotations(cells):
    base = _norm(cells)
    return tuple(sorted({_rotate(base, turns) for turns in range(4)}))


def _rotation_key(cells):
    return min(_rotations(cells))


def _connected(cells):
    remaining = set(cells)
    stack = [remaining.pop()]
    while stack:
        r, c = stack.pop()
        for dr, dc in _CARDINAL:
            point = (r + dr, c + dc)
            if point in remaining:
                remaining.remove(point)
                stack.append(point)
    return not remaining


@lru_cache(maxsize=1)
def _shape_classes():
    """Rotation-class representatives for connected 3..5-cell 3x3 shapes."""
    positions = tuple((r, c) for r in range(3) for c in range(3))
    by_size = {size: set() for size in range(3, 6)}
    for size in range(3, 6):
        for cells in combinations(positions, size):
            if _connected(cells):
                by_size[size].add(_rotation_key(cells))
    return {size: tuple(sorted(shapes)) for size, shapes in by_size.items()}


def _is_chiral(shape):
    return _rotation_key(_mirror(shape)) != _rotation_key(shape)


def _bbox(shape):
    return max(r for r, _ in shape) + 1, max(c for _, c in shape) + 1


def _draw_axis(ctx, name, defaults):
    lo, hi = _BOUNDS[name]
    options = tuple(range(lo, hi + 1)) if ctx.overrides.get(name) is not None else tuple(defaults)
    return ctx.draw_choice(name, options)


def _default_axes(ctx, phase, difficulty):
    canonical = phase in (0, 2)
    if canonical:
        return {
            "grid_h": _draw_axis(ctx, "grid_h", (9, 10)),
            "grid_w": _draw_axis(ctx, "grid_w", (12, 13)),
            "template_size": _draw_axis(ctx, "template_size", (4,)),
            "n_match": _draw_axis(ctx, "n_match", (2,)),
            "n_nonmatch": _draw_axis(ctx, "n_nonmatch", (1,)),
            "n_other_match": _draw_axis(ctx, "n_other_match", (0,)),
        }
    heights = range(9, 13) if difficulty == "easy" else range(10, 15) if difficulty != "hard" else range(12, 17)
    widths = range(12, 16) if difficulty == "easy" else range(13, 18) if difficulty != "hard" else range(15, 19)
    return {
        "grid_h": _draw_axis(ctx, "grid_h", heights),
        "grid_w": _draw_axis(ctx, "grid_w", widths),
        "template_size": _draw_axis(ctx, "template_size", (4, 5)),
        "n_match": _draw_axis(ctx, "n_match", (1, 2)),
        "n_nonmatch": _draw_axis(ctx, "n_nonmatch", (1, 2)),
        "n_other_match": _draw_axis(ctx, "n_other_match", (1,)),
    }


def _partition_regions(total, count):
    """Split an axis into `count` regions separated by one-cell gaps."""
    usable = total - (count - 1)
    base, extra = divmod(usable, count)
    widths = [base + (index < extra) for index in range(count)]
    regions = []
    start = 0
    for width in widths:
        regions.append((start, start + width))
        start += width + 1
    return tuple(regions)


def _place_in_region(grid, shape, color, row_region, col_region, rng):
    shape_h, shape_w = _bbox(shape)
    r0, r1 = row_region
    c0, c1 = col_region
    if r1 - r0 < shape_h or c1 - c0 < shape_w:
        raise ValueError("shape does not fit constructive slot")
    top = rng.randint(r0, r1 - shape_h)
    left = rng.randint(c0, c1 - shape_w)
    for dr, dc in shape:
        if grid[top + dr][left + dc] != 0:
            raise RuntimeError("constructive slots overlapped")
        grid[top + dr][left + dc] = color


def _choose_template(rng, size, teaching):
    classes = _shape_classes()[size]
    if teaching:
        chiral = tuple(shape for shape in classes if _is_chiral(shape))
        if chiral:
            return rng.choice(chiral)
    nonsymmetric = tuple(shape for shape in classes if len(_rotations(shape)) > 1)
    return rng.choice(nonsymmetric or classes)


def _choose_nonmatches(rng, template, count):
    accepted = set(_rotations(template))
    candidates = [shape for shape in _shape_classes()[len(template)]
                  if _rotation_key(shape) != _rotation_key(template)]
    preferred = _mirror(template)
    result = []
    if _norm(preferred) not in accepted:
        result.append(_norm(preferred))
    remaining = [shape for shape in candidates if _norm(shape) not in result]
    rng.shuffle(remaining)
    while len(result) < count:
        if not remaining:
            remaining = list(candidates)
            rng.shuffle(remaining)
        result.append(_rotate(remaining.pop(), rng.randrange(4)))
    return result[:count]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if type(seed) is not int:
        raise TypeError("seed must be an integer")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative integer")
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise TypeError(f"unknown override(s): {sorted(unknown)}")
    for name, value in overrides.items():
        if value is None:
            continue
        if type(value) is not int:
            raise TypeError(f"{name} must be an integer")
        lo, hi = _BOUNDS[name]
        if not lo <= value <= hi:
            raise ValueError(f"{name} must be in {lo}..{hi}")

    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    phase = sample_index % LESSON_SCHEDULE_PERIOD
    axes = _default_axes(ctx, phase, difficulty)
    height, width = axes["grid_h"], axes["grid_w"]
    template_size = axes["template_size"]
    n_match, n_nonmatch = axes["n_match"], axes["n_nonmatch"]
    n_other = axes["n_other_match"]

    rng = ctx.draw_rng("shape_assignment_and_layout")
    teaching = phase in (0, 1, 2, 3) and template_size in (4, 5)
    template = _choose_template(rng, template_size, teaching)
    rotations = list(_rotations(template))
    nontrivial = [shape for shape in rotations if shape != _norm(template)]
    matches = [rng.choice(nontrivial or rotations)]
    while len(matches) < n_match:
        matches.append(rng.choice(rotations))
    nonmatches = _choose_nonmatches(rng, template, n_nonmatch)
    other_matches = [rng.choice(rotations) for _ in range(n_other)]

    pieces = [(1, template)]
    pieces.extend((3, shape) for shape in matches)
    pieces.extend((3, shape) for shape in nonmatches)
    if other_matches:
        colors = list(_OTHER_COLORS)
        rng.shuffle(colors)
        pieces.extend((colors[index], shape) for index, shape in enumerate(other_matches))
    rng.shuffle(pieces)

    grid = full_grid(height, width, 0)
    row_regions = _partition_regions(height, 2)
    col_regions = _partition_regions(width, 3)
    region_slots = [(rr, cc) for rr in row_regions for cc in col_regions]
    rng.shuffle(region_slots)
    for (color, shape), (row_region, col_region) in zip(pieces, region_slots):
        _place_in_region(grid, shape, color, row_region, col_region, rng)
    return grid


def _components(grid):
    height, width = len(grid), len(grid[0])
    seen = set()
    result = []
    for r in range(height):
        for c in range(width):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in _CARDINAL:
                    point = (rr + dr, cc + dc)
                    if (0 <= point[0] < height and 0 <= point[1] < width
                            and point not in seen
                            and grid[point[0]][point[1]] == color):
                        seen.add(point)
                        stack.append(point)
            result.append((color, tuple(sorted(cells))))
    return result


def observe_overrides(grid):
    comps = _components(grid)
    templates = [cells for color, cells in comps if color == 1]
    if len(templates) != 1:
        raise ValueError("expected exactly one color-1 template")
    template = templates[0]
    accepted = set(_rotations(template))
    threes = [cells for color, cells in comps if color == 3]
    others = [cells for color, cells in comps if color not in (1, 3)]
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "template_size": len(template),
        "n_match": sum(_norm(cells) in accepted for cells in threes),
        "n_nonmatch": sum(_norm(cells) not in accepted for cells in threes),
        "n_other_match": sum(_norm(cells) in accepted for cells in others),
    }


def self_check(grid, *, difficulty=None, meta=None):
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty rectangular grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected nonempty rows"]
    if any(not isinstance(row, (list, tuple)) or len(row) != len(grid[0]) for row in grid):
        return ["ragged grid"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be integer colors 0..9, excluding booleans"]
    height, width = len(grid), len(grid[0])
    errors = []
    if not (9 <= height <= 16 and 12 <= width <= 18):
        errors.append("canvas must be 9..16 rows by 12..18 columns")
    comps = _components(grid)
    templates = [cells for color, cells in comps if color == 1]
    if len(templates) != 1:
        errors.append(f"expected exactly one color-1 template, found {len(templates)}")
        return errors
    template = templates[0]
    if not 3 <= len(template) <= 5 or max(_bbox(_norm(template))) > 3:
        errors.append("template must contain 3..5 cells and fit 3x3")
    owners = {}
    for index, (color, cells) in enumerate(comps):
        shape = _norm(cells)
        if not 3 <= len(cells) <= 5:
            errors.append(f"component {index} must contain 3..5 cells")
        if max(_bbox(shape)) > 3:
            errors.append(f"component {index} must fit 3x3")
        for point in cells:
            owners[point] = index
    if any((r + dr, c + dc) in owners and owners[(r + dr, c + dc)] != owner
           for (r, c), owner in owners.items() for dr, dc in _NEIGHBORS_8):
        errors.append("components must be separated by background, including diagonally")
    accepted = set(_rotations(template))
    threes = [cells for color, cells in comps if color == 3]
    matches = sum(_norm(cells) in accepted for cells in threes)
    nonmatches = sum(_norm(cells) not in accepted for cells in threes)
    if not 1 <= matches <= 2:
        errors.append(f"expected 1..2 matching color-3 components, found {matches}")
    if not 1 <= nonmatches <= 2:
        errors.append(f"expected 1..2 nonmatching color-3 components, found {nonmatches}")
    others = [(color, cells) for color, cells in comps if color not in (1, 3)]
    if len(others) > 1:
        errors.append(f"expected at most one other-color component, found {len(others)}")
    if any(color not in _OTHER_COLORS or _norm(cells) not in accepted for color, cells in others):
        errors.append("other-color component must be a rotational template match in an allowed distractor color")
    return errors


def strict_canonical_like(grid):
    errors = self_check(grid)
    if errors:
        return errors
    observed = observe_overrides(grid)
    palette = {value for row in grid for value in row}
    if not (9 <= len(grid) <= 10 and 12 <= len(grid[0]) <= 13):
        errors.append("outside canonical canvas envelope")
    if palette != {0, 1, 3}:
        errors.append("outside canonical palette {0,1,3}")
    if observed["template_size"] not in (3, 4):
        errors.append("canonical template contains 3 or 4 cells")
    if (observed["n_match"], observed["n_nonmatch"], observed["n_other_match"]) != (2, 1, 0):
        errors.append("canonical profile has two matches, one nonmatch, and no other-color component")
    return errors


# Pure diagnostics below do not supply labels to generation.
def _blank_like(grid):
    return [[0 for _ in row] for row in grid]


def _paint(out, cells, color=8):
    for r, c in cells:
        out[r][c] = color
    return out


def _official_output(grid):
    comps = _components(grid)
    template = next(cells for color, cells in comps if color == 1)
    accepted = set(_rotations(template))
    out = _blank_like(grid)
    for color, cells in comps:
        if color == 3 and _norm(cells) in accepted:
            _paint(out, cells)
    return out


def _translation_only(grid):
    comps = _components(grid)
    template = _norm(next(cells for color, cells in comps if color == 1))
    out = _blank_like(grid)
    for color, cells in comps:
        if color == 3 and _norm(cells) == template:
            _paint(out, cells)
    return out


def _reflection_allowed(grid):
    comps = _components(grid)
    template = next(cells for color, cells in comps if color == 1)
    accepted = set(_rotations(template)) | set(_rotations(_mirror(template)))
    out = _blank_like(grid)
    for color, cells in comps:
        if color == 3 and _norm(cells) in accepted:
            _paint(out, cells)
    return out


def _all_green(grid):
    out = _blank_like(grid)
    for color, cells in _components(grid):
        if color == 3:
            _paint(out, cells)
    return out


def _color_agnostic(grid):
    comps = _components(grid)
    template = next(cells for color, cells in comps if color == 1)
    accepted = set(_rotations(template))
    out = _blank_like(grid)
    for color, cells in comps:
        if color != 1 and _norm(cells) in accepted:
            _paint(out, cells)
    return out


def _size_only(grid):
    comps = _components(grid)
    template = next(cells for color, cells in comps if color == 1)
    out = _blank_like(grid)
    for color, cells in comps:
        if color == 3 and len(cells) == len(template):
            _paint(out, cells)
    return out


SEMANTIC_RIVALS = {
    "translation_only": _translation_only,
    "reflection_allowed": _reflection_allowed,
    "all_green": _all_green,
    "color_agnostic": _color_agnostic,
    "size_only": _size_only,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {"color_agnostic": _color_agnostic}


def _refutes(name, grid):
    return SEMANTIC_RIVALS[name](grid) != _official_output(grid)


SEMANTIC_WITNESSES = {
    name: (lambda grid, name=name: _refutes(name, grid))
    for name in SEMANTIC_RIVALS
}
WITNESS_RIVALS = {name: [name] for name in SEMANTIC_RIVALS}


def lesson_identifiable(demos, query):
    """Finite declared-rival ambiguity check using supplied reference labels."""
    return [f"{name} fits every demonstration but changes the query"
            for name, rival in LESSON_COMPETITORS.items()
            if all(rival(pair["input"]) == pair["output"] for pair in demos)
            and rival(query["input"]) != query["output"]]
