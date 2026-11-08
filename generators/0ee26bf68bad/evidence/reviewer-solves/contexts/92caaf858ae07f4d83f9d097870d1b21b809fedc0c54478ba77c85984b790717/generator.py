"""Largest monochromatic four-connected object's cropped cardinal contour.

The selected Racket rule remains the label authority. The Python mirror is an
independently checked authoring diagnostic, never a replacement label source.
Default lessons alternate source-like rectangles and joint counterexamples.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "0ee26bf68bad"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "d66e3a1b4a29"
SUMMARY = (
    "Select the largest monochromatic 4-connected component by cell count; "
    "retain cells with an absent cardinal neighbor and crop to its bbox."
)
INVARIANTS = [
    "integer colors 0..9; 0 is background",
    "exactly three monochromatic 4-connected components",
    "a unique largest component; smaller components may tie",
    "different colors may touch; separate components may share a color",
    "default draws alternate rectangle and joint counterexample scenes",
]
HELPFUL_TEXTURES = ("rectangle", "joint")
DEGENERATE_TEXTURES = ()
AXES = {
    "grid_h": {"type": "int", "default": "source profiles plus band-sized canvases", "valid": "7..14"},
    "grid_w": {"type": "int", "default": "source profiles plus band-sized canvases", "valid": "9..14"},
    "winner_color": {"type": "int", "default": "keyed 1..9", "valid": "1..9"},
    "texture": {"type": "str", "default": "alternating rectangle|joint", "valid": "rectangle|joint"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []
EXAMPLES_NEEDED = 3
LESSON_SCHEDULE_PERIOD = 2
SCHEDULE_PROFILES = HELPFUL_TEXTURES
MIN_STRICT_FRAC = 1.0
_DIR4 = ((-1, 0), (1, 0), (0, -1), (0, 1))
_DIR8 = tuple((r, c) for r in (-1, 0, 1) for c in (-1, 0, 1) if r or c)
_CANONICAL_PROFILES = ((7, 10), (8, 9), (7, 11), (8, 10))


def schedule_profile(seed, sample_index, difficulty=None):
    """Period of semantic scene families, not random grid bytes."""
    del seed, difficulty
    return HELPFUL_TEXTURES[sample_index % LESSON_SCHEDULE_PERIOD]


def _check_arguments(difficulty, overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override keys: {', '.join(unknown)}")
    for name, lo, hi in (("grid_h", 7, 14), ("grid_w", 9, 14), ("winner_color", 1, 9)):
        value = overrides.get(name)
        if value is not None and (type(value) is not int or not lo <= value <= hi):
            raise ValueError(f"{name} must be an integer in [{lo}, {hi}], not {value!r}")
    texture = overrides.get("texture")
    if texture is not None and (type(texture) is not str or texture not in HELPFUL_TEXTURES):
        raise ValueError(f"texture must be one of {HELPFUL_TEXTURES}, not {texture!r}")


def _canvas(ctx, sample_index, difficulty, overrides):
    # Three of four two-sample blocks use an exact source shape in every band.
    # Rectangle/joint parity varies independently within each such block.
    profile = ctx.draw_choice("canonical_profile", _CANONICAL_PROFILES)
    source_shape = (sample_index // 2) % 4 != 3
    band_bounds = {
        None: ((7, 12), (9, 14)),
        "easy": ((7, 10), (9, 12)),
        "medium": ((7, 12), (9, 14)),
        "hard": ((9, 14), (10, 14)),
    }[difficulty]
    result = []
    for index, (name, lo, hi) in enumerate((("grid_h", 7, 14), ("grid_w", 9, 14))):
        if overrides.get(name) is not None:
            result.append(ctx.draw_int_strict(name, lo, hi))
        elif source_shape:
            result.append(ctx.draw_int_strict(name, profile[index], profile[index]))
        else:
            result.append(ctx.draw_int_strict(name, *band_bounds[index]))
    return tuple(result)


def _rect(height, width):
    return {(r, c) for r in range(height) for c in range(width)}


def _small_shape(rng, height, width):
    """Choose a connected distractor that fits without dropping an object."""
    candidates = [
        {(0, 0)}, {(0, 0), (0, 1)}, {(0, 0), (1, 0)},
        {(0, 0), (0, 1), (0, 2)}, {(0, 0), (1, 0), (1, 1)},
        _rect(2, 2), {(0, 0), (1, 0), (2, 0), (2, 1)},
        {(0, 0), (0, 1), (1, 1), (1, 2), (2, 2)},
    ]
    fitting = [cells for cells in candidates
               if max(r for r, _ in cells) < height and max(c for _, c in cells) < width]
    return rng.choice(fitting)


def _rectangle_scene(rng, h, w, colors):
    rh = rng.randint(3, min(5, h - 2))
    rw = rng.randint(3, min(5, w - 3))
    target = _rect(rh, rw)
    first = _small_shape(rng, h, w - rw - 1)
    second = _small_shape(rng, h - rh - 1, rw)
    return ([(r, c, colors[0]) for r, c in sorted(target)]
            + [(r, c + rw + 1, colors[1]) for r, c in sorted(first)]
            + [(r + rh + 1, c, colors[2]) for r, c in sorted(second)])


def _joint_scene(rng, h, w, colors):
    # Distractors aggregate to a*b+1 cells; winner has a*b-1 or a*b-2.
    # Their only contact is diagonal. The L's bbox area is a*(b+1)>a*b.
    a = rng.randint(4, min(6, (h + 1) // 2))
    b = rng.randint(4, min(6, (w - 1) // 2))
    target = _rect(a, b)
    target.remove((rng.randint(1, a - 2), rng.randint(1, b - 2)))
    if rng.choice((False, True)):
        target.remove(rng.choice(((0, 0), (0, b - 1), (a - 1, 0), (a - 1, b - 1))))
    first = {(0, c) for c in range(b, 2 * b + 1)} | {(r, b) for r in range(1, a)}
    second = {(r, c) for r in range(a, 2 * a - 1) for c in range(1, b)}
    return ([(r, c, colors[0]) for r, c in sorted(target)]
            + [(r, c, colors[1]) for r, c in sorted(first | second)])


def _place_scene(rng, cells, h, w):
    """Translate and reflect; transpose as well whenever the canvas fits."""
    bh = 1 + max(r for r, _, _ in cells)
    bw = 1 + max(c for _, c, _ in cells)
    variants = []
    for transpose in (False, True):
        vh, vw = (bw, bh) if transpose else (bh, bw)
        if vh > h or vw > w:
            continue
        for flip_r in (False, True):
            for flip_c in (False, True):
                placed = []
                for r, c, color in cells:
                    rr, cc = (c, r) if transpose else (r, c)
                    placed.append((vh - 1 - rr if flip_r else rr,
                                   vw - 1 - cc if flip_c else cc, color))
                variants.append((vh, vw, placed))
    vh, vw, selected = rng.choice(variants)
    dr, dc = rng.randint(0, h - vh), rng.randint(0, w - vw)
    grid = full_grid(h, w, 0)
    for r, c, color in selected:
        grid[r + dr][c + dc] = color
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _check_arguments(difficulty, overrides)
    if type(seed) is not int:
        raise ValueError("seed must be an integer, excluding bool")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative integer")
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    h, w = _canvas(ctx, sample_index, difficulty, overrides)
    options = HELPFUL_TEXTURES if overrides.get("texture") is not None else (
        schedule_profile(seed, sample_index, difficulty),)
    texture = ctx.draw_choice("texture", options)
    winner = ctx.draw_int_strict("winner_color", 1, 9)
    remaining = ctx.draw_rng("palette").sample([c for c in range(1, 10) if c != winner], 2)
    colors = (winner, *remaining)
    shape_rng = ctx.draw_rng("shape")
    cells = (_rectangle_scene(shape_rng, h, w, colors) if texture == "rectangle"
             else _joint_scene(shape_rng, h, w, colors))
    return _place_scene(ctx.draw_rng("placement"), cells, h, w)


def _objects(grid, *, diagonal=False, aggregate=False):
    if aggregate:
        groups = {}
        for r, row in enumerate(grid):
            for c, color in enumerate(row):
                if color:
                    groups.setdefault(color, set()).add((r, c))
        return list(groups.items())
    unseen = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value}
    objects = []
    directions = _DIR8 if diagonal else _DIR4
    while unseen:
        start = min(unseen)
        color = grid[start[0]][start[1]]
        unseen.remove(start)
        cells, pending = {start}, [start]
        while pending:
            r, c = pending.pop()
            for dr, dc in directions:
                point = r + dr, c + dc
                if point in unseen and grid[point[0]][point[1]] == color:
                    unseen.remove(point)
                    cells.add(point)
                    pending.append(point)
        objects.append((color, cells))
    return objects


def _bbox(cells):
    return (min(r for r, _ in cells), min(c for _, c in cells),
            max(r for r, _ in cells), max(c for _, c in cells))


def _largest(objects, *, bbox_area=False):
    def key(obj):
        r1, c1, r2, c2 = _bbox(obj[1])
        size = (r2 - r1 + 1) * (c2 - c1 + 1) if bbox_area else len(obj[1])
        return -size, r1, c1
    return min(objects, key=key)


def _render(obj, mode="contour"):
    color, cells = obj
    r1, c1, r2, c2 = _bbox(cells)
    output = full_grid(r2 - r1 + 1, c2 - c1 + 1, 0)
    if mode == "bbox_frame":
        kept = {(r, c) for r in range(r1, r2 + 1) for c in range(c1, c2 + 1)
                if r in (r1, r2) or c in (c1, c2)}
    elif mode == "bbox_strip":
        kept = {(r, c) for r, c in cells if r in (r1, r2) or c in (c1, c2)}
    elif mode == "crop":
        kept = cells
    else:
        directions = _DIR8 if mode == "contour8" else _DIR4
        kept = {(r, c) for r, c in cells
                if any((r + dr, c + dc) not in cells for dr, dc in directions)}
    for r, c in kept:
        output[r - r1][c - c1] = color
    return output


def self_check(grid, *, difficulty=None, meta=None):
    """Rule domain: broader than the generated layout templates."""
    del difficulty, meta
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be nonempty and rectangular"]
    if not all(isinstance(row, (list, tuple)) and row for row in grid):
        return ["every row must be a nonempty sequence"]
    if any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be rectangular"]
    if len(grid) > 30 or len(grid[0]) > 30:
        return ["grid dimensions must be at most 30"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be integer colors 0..9, excluding bool"]
    if not any(value == 0 for row in grid for value in row):
        return ["input must contain background color 0"]
    objects = _objects(grid)
    if len(objects) != 3:
        return [f"need exactly three monochromatic 4-connected objects, got {len(objects)}"]
    sizes = sorted((len(cells) for _, cells in objects), reverse=True)
    if sizes[0] == sizes[1]:
        return ["largest object must be unique by cell count"]
    return []


def strict_canonical_like(grid):
    """Task-domain support; source dimensions are measured separately."""
    return self_check(grid)


def rule_mirror(grid):
    """Diagnostic mirror, not the authority for generated training labels."""
    return _render(_largest(_objects(grid)))


def observe_overrides(grid):
    objects = _objects(grid)
    winner = _largest(objects)[0]
    colors = {color for color, _ in objects}
    return {"grid_h": len(grid), "grid_w": len(grid[0]), "winner_color": winner,
            "texture": "joint" if len(colors) == 2 else "rectangle"}


def _color_frequency(grid):
    return _render(_largest(_objects(grid, aggregate=True)))


def _objects8(grid):
    return _render(_largest(_objects(grid, diagonal=True)))


def _contour8(grid):
    return _render(_largest(_objects(grid)), "contour8")


def _bbox_area(grid):
    return _render(_largest(_objects(grid), bbox_area=True))


def _bbox_frame(grid):
    return _render(_largest(_objects(grid)), "bbox_frame")


def _bbox_strip(grid):
    return _render(_largest(_objects(grid)), "bbox_strip")


def _crop_full_object(grid):
    return _render(_largest(_objects(grid)), "crop")


CANONICAL_SHORTCUTS = {
    "color_frequency": _color_frequency,
    "objects8": _objects8,
    "contour8": _contour8,
    "bbox_area": _bbox_area,
    "bbox_frame": _bbox_frame,
    "bbox_strip": _bbox_strip,
}
SEMANTIC_RIVALS = {**CANONICAL_SHORTCUTS, "crop_full_object": _crop_full_object}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def _refutes(rival):
    def witness(grid):
        return rule_mirror(grid) != rival(grid)
    return witness


SEMANTIC_WITNESSES = {name: _refutes(rival) for name, rival in SEMANTIC_RIVALS.items()}
WITNESS_RIVALS = {name: [name] for name in SEMANTIC_RIVALS}


def lesson_identifiable(demos, query=None):
    """Finite declared-rival diagnostic, not a claim of unique induction."""
    if not isinstance(demos, list) or not demos or not isinstance(query, dict):
        return ["a nonempty demonstration list and a labelled query are required"]
    for index, pair in enumerate([*demos, query]):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            return [f"malformed labelled pair {index}"]
        reasons = self_check(pair["input"])
        if reasons:
            return [f"pair {index}: {reason}" for reason in reasons]
        output = pair["output"]
        if (not isinstance(output, list) or not output
                or not all(isinstance(row, list) and row for row in output)
                or any(len(row) != len(output[0]) for row in output)
                or any(type(value) is not int or not 0 <= value <= 9
                       for row in output for value in row)):
            return [f"pair {index}: output must be a rectangular integer-color grid"]
        if rule_mirror(pair["input"]) != pair["output"]:
            return [f"pair {index}: supplied label disagrees with diagnostic mirror"]
    reasons = []
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            if rival(query["input"]) != query["output"]:
                reasons.append(f"{name} fits demonstrations but changes the query")
    return reasons
