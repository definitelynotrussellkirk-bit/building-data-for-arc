"""Rotation-match inputs for ARC task e73c86cb45ad.

The selected Racket authority is unchanged: the top-right cell supplies the
output color; the largest color-1 object is the reference; among the remaining
objects in reading order, select the first binary shape equal to a rotation of
the reference, crop it, and recolor it with the target color.

This sampler constructs four separated zones.  Distractors have the same size
as the reference but a different rotation class, so object size and reading
order cannot replace the intended shape comparison.  The module never creates
labels; ``rule_mirror`` is a diagnostic mirror only.
"""
from __future__ import annotations

from collections import deque
from copy import deepcopy
from functools import lru_cache

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "e73c86cb45ad"
TASK_ID = GENERATOR_ID
RULE_HASH = "a405585a6a23"
VERSION = "3.0.0"
SUMMARY = (
    "Top-right target color, one color-1 reference, and two or three equally "
    "sized candidates; exactly one candidate is a requested rotation match."
)

INVARIANTS = [
    "background is 0 and the top-right target is a unique nonzero color",
    "there is exactly one color-1 reference object",
    "there are two or three other monochrome objects in separated zones",
    "all generated objects have the requested size and exactly one candidate is rotation-equivalent",
    "same-size distractors and scheduled non-first matches teach shape comparison rather than order or size",
]

DIFFICULTIES = (None, "easy", "medium", "hard")
MATCH_ORDERS = ("first", "later")
_BAND_OFFSETS = {None: 0, "easy": 0, "medium": 1, "hard": 2}

AXES = {
    "grid_h": {
        "type": "int",
        "default": "canonical-profile schedule plus full-domain draws",
        "valid": "10..16",
    },
    "grid_w": {
        "type": "int",
        "default": "canonical-profile schedule plus full-domain draws",
        "valid": "11..16",
    },
    "shape_size": {
        "type": "int",
        "default": "teaching cycle over 4..7",
        "valid": "4..7",
    },
    "match_rotation": {
        "type": "int",
        "default": "teaching cycle over 0..3 clockwise turns",
        "valid": "0..3",
    },
    "match_order": {
        "type": "str",
        "default": "teaching cycle with a non-first match in every three examples",
        "valid": "first|later",
    },
    "n_distractors": {
        "type": "int",
        "default": "canonical-profile prefix then cycle over 1..2",
        "valid": "1..2",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []
EXAMPLES_NEEDED = 3

# The five public dimensions are deliberately retained at the start of every
# default stream.  With two distractors these also reproduce the public six-
# color input profiles.  Remaining residues cover the full declared domain.
_CANONICAL_SIZES = ((12, 13), (13, 14), (12, 12), (14, 14), (13, 13))
_SIZE_SCHEDULE = _CANONICAL_SIZES + (
    (10, 11),
    (10, 16),
    (11, 12),
    (11, 15),
    (12, 16),
    (13, 11),
    (14, 12),
    (14, 16),
    (15, 13),
    (15, 15),
    (16, 11),
    (16, 14),
    (16, 16),
    None,
)
# Every contiguous three samples contain at least one non-first match.
_ORDER_SCHEDULE = ("first", "later", "later")


def _validate_request(difficulty, overrides):
    if difficulty not in DIFFICULTIES:
        raise ValueError(
            f"difficulty must be one of easy|medium|hard|None, got {difficulty!r}"
        )
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")

    integer_bounds = {
        "grid_h": (10, 16),
        "grid_w": (11, 16),
        "shape_size": (4, 7),
        "match_rotation": (0, 3),
        "n_distractors": (1, 2),
    }
    for name, (lo, hi) in integer_bounds.items():
        if name not in overrides:
            continue
        value = overrides[name]
        if type(value) is not int:
            raise TypeError(f"{name} must be an integer, not {type(value).__name__}")
        if not lo <= value <= hi:
            raise ValueError(f"{name} must be in {lo}..{hi}, got {value!r}")

    if "match_order" in overrides:
        value = overrides["match_order"]
        if type(value) is not str:
            raise TypeError(
                f"match_order must be a string, not {type(value).__name__}"
            )
        if value not in MATCH_ORDERS:
            raise ValueError(
                f"match_order must be one of {MATCH_ORDERS}, got {value!r}"
            )


def _effective_axes(seed, sample_index, difficulty, overrides):
    """Resolve defaults, then send every exact axis through the final GenCtx."""
    effective = dict(overrides)
    scheduled_size = _SIZE_SCHEDULE[sample_index % len(_SIZE_SCHEDULE)]
    if scheduled_size is not None:
        effective.setdefault("grid_h", scheduled_size[0])
        effective.setdefault("grid_w", scheduled_size[1])

    # A planning context is created only for unscheduled defaults.  The final
    # context is created afterwards and records every exact effective value.
    if len(effective) < len(AXES):
        planner = gen_ctx(
            seed=seed,
            sample_index=sample_index,
            version=VERSION,
            task_id=TASK_ID,
            difficulty=difficulty,
            overrides={},
        )
        if "grid_h" not in effective:
            effective["grid_h"] = planner.draw_rng("planned_grid_h").randint(10, 16)
        if "grid_w" not in effective:
            effective["grid_w"] = planner.draw_rng("planned_grid_w").randint(11, 16)

    band_offset = _BAND_OFFSETS[difficulty]
    effective.setdefault("shape_size", 4 + ((sample_index + band_offset) % 4))
    effective.setdefault(
        "match_rotation", ((sample_index % 4) + (sample_index // 4)) % 4
    )
    effective.setdefault(
        "match_order", _ORDER_SCHEDULE[sample_index % len(_ORDER_SCHEDULE)]
    )
    # Preserve six-color canonical profiles for the five scheduled public sizes,
    # then alternate one and two distractors throughout the remaining stream.
    default_distractors = 2 if sample_index % len(_SIZE_SCHEDULE) < 5 else 1 + (sample_index % 2)
    effective.setdefault("n_distractors", default_distractors)
    return effective


def _norm(cells):
    cells = tuple(cells)
    if not cells:
        raise ValueError("shape must contain at least one cell")
    min_r = min(r for r, _ in cells)
    min_c = min(c for _, c in cells)
    return tuple(sorted((r - min_r, c - min_c) for r, c in cells))


def _rotate_cw(shape):
    shape = _norm(shape)
    height = max(r for r, _ in shape) + 1
    return _norm((c, height - 1 - r) for r, c in shape)


def _rotations(shape):
    values = []
    current = _norm(shape)
    for _ in range(4):
        values.append(current)
        current = _rotate_cw(current)
    return tuple(values)


def _rotation_class(shape):
    return frozenset(_rotations(shape))


@lru_cache(maxsize=None)
def _polyominoes(size):
    """Enumerate fixed connected polyominoes of ``size`` fitting a 4x4 slot."""
    shapes = {((0, 0),)}
    for _ in range(1, size):
        expanded = set()
        for shape in shapes:
            occupied = set(shape)
            for r, c in shape:
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    cell = (r + dr, c + dc)
                    if cell in occupied:
                        continue
                    candidate = _norm(occupied | {cell})
                    if max(r for r, _ in candidate) < 4 and max(c for _, c in candidate) < 4:
                        expanded.add(candidate)
        shapes = expanded
    return tuple(sorted(shapes))


@lru_cache(maxsize=None)
def _reference_shapes(size):
    shapes = tuple(
        shape for shape in _polyominoes(size) if len(set(_rotations(shape))) == 4
    )
    if not shapes:
        raise RuntimeError(f"no four-orientation reference shape for size {size}")
    return shapes


def _bbox(cells):
    return (
        min(r for r, _ in cells),
        min(c for _, c in cells),
        max(r for r, _ in cells),
        max(c for _, c in cells),
    )


def _place_in_slot(grid, shape, color, slot, rng):
    """Place a normalized shape with a random legal offset inside a 4x4 slot."""
    row0, col0 = slot
    shape = _norm(shape)
    shape_h = max(r for r, _ in shape) + 1
    shape_w = max(c for _, c in shape) + 1
    off_r = rng.randint(0, 4 - shape_h)
    off_c = rng.randint(0, 4 - shape_w)
    cells = []
    for dr, dc in shape:
        r, c = row0 + off_r + dr, col0 + off_c + dc
        if grid[r][c] != 0:
            raise RuntimeError("constructive placement collision")
        grid[r][c] = color
        cells.append((r, c))
    return tuple(sorted(cells))


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_request(difficulty, overrides)
    effective = _effective_axes(seed, sample_index, difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=effective,
    )
    h = ctx.draw_int_strict("grid_h", 10, 16)
    w = ctx.draw_int_strict("grid_w", 11, 16)
    shape_size = ctx.draw_int_strict("shape_size", 4, 7)
    rotation = ctx.draw_int_strict("match_rotation", 0, 3)
    match_order = ctx.draw_choice("match_order", MATCH_ORDERS)
    n_distractors = ctx.draw_int_strict("n_distractors", 1, 2)

    shape_rng = ctx.draw_rng("shape_selection")
    references = _reference_shapes(shape_size)
    reference = shape_rng.choice(list(references))
    reference_class = _rotation_class(reference)
    distractor_pool = [
        shape for shape in _polyominoes(shape_size) if shape not in reference_class
    ]
    if len(distractor_pool) < n_distractors:
        raise RuntimeError("insufficient non-equivalent same-size distractors")
    distractors = shape_rng.sample(distractor_pool, n_distractors)
    distractors = [
        _rotations(shape)[shape_rng.randrange(4)] for shape in distractors
    ]
    match = _rotations(reference)[rotation]

    target_color, match_color, *distractor_colors = ctx.draw_distinct_colors(
        "object_colors", n=n_distractors + 2, exclude={0, 1}
    )
    grid = full_grid(h, w, 0)
    grid[0][w - 1] = target_color

    slots = {
        "reference": (1, 0),
        "top_right": (1, w - 4),
        "bottom_left": (h - 4, 0),
        "bottom_right": (h - 4, w - 4),
    }
    layout_rng = ctx.draw_rng("slot_offsets")
    _place_in_slot(grid, reference, 1, slots["reference"], layout_rng)

    candidate_slots = [
        slots["top_right"],
        slots["bottom_left"],
        slots["bottom_right"],
    ][: n_distractors + 1]
    if match_order == "first":
        candidate_shapes = [match, *distractors]
        candidate_colors = [match_color, *distractor_colors]
    else:
        # The first reading-order candidate is a same-size distractor; the
        # actual match follows in the bottom-left zone.
        candidate_shapes = [distractors[0], match, *distractors[1:]]
        candidate_colors = [distractor_colors[0], match_color, *distractor_colors[1:]]
    for shape, color, slot in zip(candidate_shapes, candidate_colors, candidate_slots):
        _place_in_slot(grid, shape, color, slot, layout_rng)
    return grid


def _components_by_color(grid):
    h = len(grid)
    w = len(grid[0]) if h else 0
    seen = set()
    components = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            queue = deque([(r, c)])
            seen.add((r, c))
            cells = []
            while queue:
                rr, cc = queue.popleft()
                cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            components.append((color, tuple(sorted(cells))))
    return components


def _analyze(grid):
    h = len(grid)
    w = len(grid[0])
    target = grid[0][w - 1]
    marker = (0, w - 1)
    scene_components = [
        (color, cells)
        for color, cells in _components_by_color(grid)
        if not (len(cells) == 1 and cells[0] == marker)
    ]
    references = [
        (color, cells) for color, cells in scene_components if color == 1
    ]
    if not references:
        raise ValueError("no color-1 reference object")
    reference = sorted(
        references,
        key=lambda item: (-len(item[1]), _bbox(item[1])[0], _bbox(item[1])[1]),
    )[0]
    candidates = sorted(
        [item for item in scene_components if item != reference],
        key=lambda item: (_bbox(item[1])[0], _bbox(item[1])[1]),
    )
    reference_class = _rotation_class(reference[1])
    matches = [item for item in candidates if _norm(item[1]) in reference_class]
    return {
        "height": h,
        "width": w,
        "target": target,
        "reference": reference,
        "references": references,
        "candidates": candidates,
        "matches": matches,
    }


def _crop_recolor(cells, color):
    r1, c1, r2, c2 = _bbox(cells)
    occupied = set(cells)
    return [
        [color if (r, c) in occupied else 0 for c in range(c1, c2 + 1)]
        for r in range(r1, r2 + 1)
    ]


def observe_overrides(grid):
    """Recover every exact advertised axis from returned pixels."""
    info = _analyze(grid)
    if len(info["matches"]) != 1:
        raise ValueError(f"expected one match, found {len(info['matches'])}")
    reference_shape = _norm(info["reference"][1])
    match_shape = _norm(info["matches"][0][1])
    turns = [
        index
        for index, rotated in enumerate(_rotations(reference_shape))
        if rotated == match_shape
    ]
    if len(turns) != 1:
        raise ValueError(f"match rotation is not uniquely recoverable: {turns}")
    match_index = info["candidates"].index(info["matches"][0])
    return {
        "grid_h": info["height"],
        "grid_w": info["width"],
        "shape_size": len(info["reference"][1]),
        "match_rotation": turns[0],
        "match_order": "first" if match_index == 0 else "later",
        "n_distractors": len(info["candidates"]) - 1,
    }


def self_check(grid, *, difficulty=None, meta=None):
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty rectangular grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected a nonempty rectangular grid"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["ragged grid"]
    if any(
        type(value) is not int or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["cells must be integer ARC colors 0..9"]

    height = len(grid)
    errors = []
    if not 10 <= height <= 16:
        errors.append(f"grid height {height} outside 10..16")
    if not 11 <= width <= 16:
        errors.append(f"grid width {width} outside 11..16")
    if 0 not in {value for row in grid for value in row}:
        errors.append("expected background color 0")

    target = grid[0][width - 1]
    if target == 0:
        errors.append("top-right target color must be nonzero")
    target_cells = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == target
    ]
    if target != 0 and target_cells != [(0, width - 1)]:
        errors.append("top-right target color must occur exactly once in the input")

    try:
        info = _analyze(grid)
    except Exception as exc:
        errors.append(f"could not analyze objects: {type(exc).__name__}: {exc}")
        return errors

    if len(info["references"]) != 1:
        errors.append(
            f"expected exactly one color-1 reference object, found {len(info['references'])}"
        )
    if len(info["candidates"]) not in (2, 3):
        errors.append(
            f"expected two or three candidate objects, found {len(info['candidates'])}"
        )
    if len(info["matches"]) != 1:
        errors.append(
            f"expected exactly one rotation-equivalent candidate, found {len(info['matches'])}"
        )
    if info["candidates"] and len(info["matches"]) == len(info["candidates"]):
        errors.append("expected at least one non-matching distractor")

    object_colors = [info["reference"][0], *[color for color, _ in info["candidates"]]]
    if len(object_colors) != len(set(object_colors)):
        errors.append("reference and candidate objects must use distinct colors")
    if target in object_colors:
        errors.append("target color must be distinct from all object colors")
    return errors


def strict_canonical_like(grid):
    return self_check(grid)


def rule_mirror(grid):
    """Diagnostic Python mirror; the selected Racket program remains authority."""
    info = _analyze(deepcopy(grid))
    if not info["matches"]:
        raise ValueError("no rotation-equivalent candidate")
    return _crop_recolor(info["matches"][0][1], info["target"])


def _first_candidate(grid):
    """Wrong canonical-fitting rival: return the first object after the reference."""
    info = _analyze(deepcopy(grid))
    if not info["candidates"]:
        raise ValueError("no candidate object")
    return _crop_recolor(info["candidates"][0][1], info["target"])


def _match_not_first(grid):
    try:
        return observe_overrides(grid)["match_order"] == "later"
    except Exception:
        return False


SEMANTIC_WITNESSES = {"match_not_first": _match_not_first}
SEMANTIC_RIVALS = {"first_candidate": _first_candidate}
WITNESS_RIVALS = {"match_not_first": ["first_candidate"]}
CANONICAL_SHORTCUTS = {"first_candidate": _first_candidate}
LESSON_COMPETITORS = {"first_candidate": _first_candidate}


def lesson_identifiable(demos, query):
    """Return named wrong rules still consistent with every demonstration."""
    problems = []
    for name, rival in LESSON_COMPETITORS.items():
        try:
            survives = all(
                rival(deepcopy(pair["input"])) == pair["output"] for pair in demos
            )
        except Exception as exc:
            problems.append(f"{name} raised {type(exc).__name__}: {exc}")
            continue
        if survives:
            problems.append(f"{name} fits every demonstration")
    return problems
