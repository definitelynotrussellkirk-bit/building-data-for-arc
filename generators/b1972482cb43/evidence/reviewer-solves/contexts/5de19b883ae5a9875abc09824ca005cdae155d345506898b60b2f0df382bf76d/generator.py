"""Input generator for M132: preserve a shape and reflect it through its 9-anchor.

The Racket rule remains the only label authority. The Python transforms below
are explicit teaching rivals and a small geometry oracle used to select inputs;
they never supply exported labels. A five-slot schedule puts two interior and
two clipped witnesses around one broad sample, retaining the original easy shapes.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "b1972482cb43"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "add600b28dfb"
SUMMARY = (
    "One 9-anchor and one connected monochromatic 2-5-cell shape on background 0. "
    "Keep the original and add its point reflection through the anchor, clipping "
    "individual out-of-bounds cells. Mix copied-interior plus witnesses, "
    "partially clipped asymmetric witnesses, and broad complete or symmetric shapes; retain canonical-size support "
    "in every difficulty band."
)
EXAMPLES_NEEDED = 4
LESSON_SCHEDULE_PERIOD = 5
SCHEDULE_PROFILES = ("interior", "clipped_asymmetric", "broad")
_SCHEDULE = ("interior", "clipped_asymmetric", "interior", "clipped_asymmetric", "broad")
MIN_STRICT_FRAC = 0.05
INVARIANTS = [
    "rectangular 1..30 integer grids with colors 0..9 and background 0",
    "exactly one anchor of fixed color 9",
    "one 4-connected monochromatic shape of 2..5 cells, color 1..8",
    "original and point-reflected shape are disjoint",
    "at least one reflected cell is in bounds and changes the output",
]
PALETTE_KINDS = ("default", "warm", "cool", "varied")
HELPFUL_TEXTURES = PALETTE_KINDS
DEGENERATE_TEXTURES = ("no_anchor", "no_shape", "reflection_oob")
_PALETTES = {"default": tuple(range(1, 9)), "warm": (2, 4, 7),
             "cool": (1, 3, 8), "varied": (5, 6)}
AXES = {
    "grid_h": {"type": "int", "default": "4..12, canonical mixture favors 5", "valid": "4..12"},
    "grid_w": {"type": "int", "default": "5..14, canonical mixture favors 7 and 8", "valid": "5..14"},
    "palette_kind": {"type": "str", "default": "seed-stable family; color cycles within a lesson", "valid": "default|warm|cool|varied"},
    "texture": {"type": "str", "default": "alias of palette_kind", "valid": "default|warm|cool|varied"},
    "palette_size": {"type": "int", "default": "2 foreground colors", "valid": "2..2", "probe": "diagnostic"},
    "n_distinct_colors": {"type": "int", "default": "3 including background", "valid": "3..3", "probe": "diagnostic"},
    "position_bias": {"type": "str", "default": "shape_then_anchor_offset", "valid": "shape_then_anchor_offset", "probe": "diagnostic"},
    "density": {"type": "str", "default": "sparse", "valid": "sparse", "probe": "diagnostic"},
}
# Only disagreeing values of the two explicit aliases are incompatible.
INCOMPATIBLE_OVERRIDE_COMBINATIONS = [
    {"palette_kind": a, "texture": b}
    for a in PALETTE_KINDS for b in PALETTE_KINDS if a != b
]
_PLUS = ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1))
_ASYMMETRIC = (
    ((0, 0), (0, 1), (1, 0)),
    ((0, 0), (1, 0), (1, 1)),
    ((0, 1), (1, 0), (1, 1)),
    ((0, 0), (0, 1), (1, 1)),
    ((0, 0), (0, 1), (1, 0), (2, 0)),
    ((0, 0), (1, 0), (2, 0), (2, 1)),
    ((0, 0), (0, 1), (0, 2), (1, 0)),
    ((0, 0), (0, 1), (0, 2), (1, 2)),
    ((0, 0), (1, 0), (1, 1), (1, 2)),
    ((0, 0), (0, 1), (1, 0), (1, 1), (2, 0)),
    ((0, 0), (0, 1), (1, 0), (1, 1), (0, 2)),
    ((0, 0), (0, 1), (0, 2), (1, 1)),
    ((0, 1), (1, 0), (1, 1), (1, 2)),
    ((0, 0), (1, 0), (1, 1), (2, 0)),
    ((0, 1), (1, 0), (1, 1), (2, 1)),
)
_SYMMETRIC = (
    ((0, 0), (0, 1)), ((0, 0), (1, 0)),
    ((0, 0), (0, 1), (0, 2)), ((0, 0), (1, 0), (2, 0)),
    ((0, 0), (0, 1), (1, 0), (1, 1)),
    ((0, 0), (0, 1), (1, 1), (1, 2)),
    ((0, 1), (1, 0), (1, 1), (2, 0)),
)


def _parts(grid):
    anchor = next((r, c) for r, row in enumerate(grid)
                  for c, value in enumerate(row) if value == 9)
    cells = [(r, c) for r, row in enumerate(grid)
             for c, value in enumerate(row) if value not in (0, 9)]
    return anchor, cells


def _targets(cells, anchor):
    ar, ac = anchor
    return {(2 * ar - r, 2 * ac - c) for r, c in cells}


def _inside(point, h, w):
    return 0 <= point[0] < h and 0 <= point[1] < w


def self_check(grid, *, difficulty=None, meta=None):
    """Validate task assumptions without guessing through malformed inputs."""
    if not isinstance(grid, list) or not grid:
        return ["expected a nonempty grid list"]
    if any(not isinstance(row, list) or not row for row in grid):
        return ["expected nonempty row lists"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["grid must be rectangular"]
    if not (1 <= h <= 30 and 1 <= w <= 30):
        return ["grid dimensions must be 1..30"]
    if any(type(v) is not int or not 0 <= v <= 9 for row in grid for v in row):
        return ["cells must be integers 0..9, not bool or coerced scalars"]
    anchors = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 9]
    if len(anchors) != 1:
        return [f"expected exactly one 9-anchor; found {len(anchors)}"]
    shape = {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v not in (0, 9)}
    if not 2 <= len(shape) <= 5:
        return [f"expected 2..5 shape cells; found {len(shape)}"]
    if len({grid[r][c] for r, c in shape}) != 1:
        return ["shape must have one nonzero, non-9 color"]
    reached = {min(shape)}
    frontier = list(reached)
    while frontier:
        r, c = frontier.pop()
        for p in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
            if p in shape and p not in reached:
                reached.add(p)
                frontier.append(p)
    errors = []
    if reached != shape:
        errors.append("shape must be 4-connected")
    reflected = _targets(shape, anchors[0])
    if shape & reflected:
        errors.append("shape overlaps its point reflection")
    if not any(_inside(p, h, w) for p in reflected):
        errors.append("all reflected cells are out of bounds")
    return errors


def _copy(grid, *, center=None, mode="point", keep=True, color=None, outline=False, whole=False):
    """Geometry for teaching checks, never an exported label source."""
    anchor, cells = _parts(grid)
    ar, ac = anchor if center is None else center
    h, w = len(grid), len(grid[0])
    output = [row[:] for row in grid] if keep else full_grid(h, w, 0)
    if not keep:
        output[anchor[0]][anchor[1]] = 9
    selected = set(cells)
    if outline:
        cells = [(r, c) for r, c in cells if any(p not in selected for p in
                 ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)))]
    rsum = min(r for r, c in selected) + max(r for r, c in selected)
    csum = min(c for r, c in selected) + max(c for r, c in selected)
    placed = []
    for r, c in cells:
        if mode == "horizontal":
            target = (2 * ar - r, c)
        elif mode == "vertical":
            target = (r, 2 * ac - c)
        elif mode == "translate":
            target = (r + 2 * ar - rsum, c + 2 * ac - csum)
        else:
            target = (2 * ar - r, 2 * ac - c)
        placed.append((target, grid[r][c] if color is None else color))
    if whole and any(not _inside(p, h, w) for p, v in placed):
        return output
    for (r, c), v in placed:
        if _inside((r, c), h, w):
            output[r][c] = v
    return output


def _identity(grid):
    return [row[:] for row in grid]


def _fixed_anchor(grid):
    return _copy(grid, center=(2, 3))


def _grid_center(grid):
    return _copy(grid, center=(len(grid) // 2, (len(grid[0]) - 1) // 2))


def _all_or_nothing(grid):
    return _copy(grid, whole=True)


def _outline_only(grid):
    return _copy(grid, outline=True)


def _left_of_anchor_only(grid):
    """Preserve input, but copy only source cells at or left of the 9-axis."""
    (ar, ac), cells = _parts(grid)
    output = [row[:] for row in grid]
    h, w = len(grid), len(grid[0])
    for r, c in cells:
        target = (2 * ar - r, 2 * ac - c)
        if c <= ac and _inside(target, h, w):
            output[target[0]][target[1]] = grid[r][c]
    return output


def _horizontal_axis(grid):
    return _copy(grid, mode="horizontal")


def _vertical_axis(grid):
    return _copy(grid, mode="vertical")


def _reflection_only(grid):
    return _copy(grid, keep=False)


def _anchor_color_copy(grid):
    return _copy(grid, color=9)


def _translate_only(grid):
    return _copy(grid, mode="translate")


CANONICAL_SHORTCUTS = {"fixed_anchor": _fixed_anchor, "grid_center": _grid_center,
                      "all_or_nothing": _all_or_nothing, "outline_only": _outline_only,
                      "left_of_anchor_only": _left_of_anchor_only}
SEMANTIC_RIVALS = dict(CANONICAL_SHORTCUTS)
LESSON_COMPETITORS = {**CANONICAL_SHORTCUTS, "identity": _identity,
    "horizontal_axis": _horizontal_axis, "vertical_axis": _vertical_axis,
    "reflection_only": _reflection_only, "anchor_color_copy": _anchor_color_copy,
    "translate_only": _translate_only}


def _visible_interior(grid):
    anchor, cells = _parts(grid)
    points = set(cells)
    return any(all(p in points for p in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)))
               and _inside((2 * anchor[0] - r, 2 * anchor[1] - c), len(grid), len(grid[0]))
               for r, c in cells)


def _partial_clipping(grid):
    anchor, cells = _parts(grid)
    count = sum(_inside(p, len(grid), len(grid[0])) for p in _targets(cells, anchor))
    return 0 < count < len(cells)


def _off_fixed_anchor(grid):
    return _copy(grid) != _fixed_anchor(grid)


def _off_grid_center(grid):
    return _copy(grid) != _grid_center(grid)


def _right_source_copied(grid):
    return _copy(grid) != _left_of_anchor_only(grid)


SEMANTIC_WITNESSES = {"visible_interior": _visible_interior, "partial_clipping": _partial_clipping,
    "off_fixed_anchor": _off_fixed_anchor, "off_grid_center": _off_grid_center,
    "right_source_copied": _right_source_copied}
WITNESS_RIVALS = {"visible_interior": ["outline_only"], "partial_clipping": ["all_or_nothing"],
    "off_fixed_anchor": ["fixed_anchor"], "off_grid_center": ["grid_center"],
    "right_source_copied": ["left_of_anchor_only"]}


def strict_canonical_like(grid):
    errors = self_check(grid)
    if not errors and (len(grid) != 5 or len(grid[0]) not in (7, 8)):
        errors.append("outside canonical height/width/color profile (5 by 7 or 8, three colors)")
    return errors


def lesson_identifiable(demos, query):
    """Finite rival test only; an agreeing rival need not be eliminated."""
    reasons = []
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            if rival(query["input"]) != query["output"]:
                reasons.append(f"{name} fits all demonstrations and changes the query")
    return reasons


def schedule_profile(seed, sample_index, difficulty=None):
    return _SCHEDULE[sample_index % LESSON_SCHEDULE_PERIOD]


def _controls(seed, sample_index, difficulty, overrides):
    if type(seed) is not int:
        raise ValueError("seed must be an integer, not bool")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative integer")
    if difficulty is not None and (type(difficulty) is not str or difficulty not in ("easy", "medium", "hard")):
        raise ValueError("difficulty must be None, easy, medium, or hard")
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name, value in overrides.items():
        if value is None:
            continue
        expected = int if AXES[name]["type"] == "int" else str
        if type(value) is not expected:
            raise ValueError(f"{name} must be {expected.__name__}, not {type(value).__name__}")
    fixed = {"palette_size": 2, "n_distinct_colors": 3,
             "position_bias": "shape_then_anchor_offset", "density": "sparse"}
    for name, value in fixed.items():
        if overrides.get(name) is not None and overrides[name] != value:
            raise ValueError(f"{name} is fixed at {value!r}")
    for name in ("palette_kind", "texture"):
        allowed = PALETTE_KINDS + (DEGENERATE_TEXTURES if name == "texture" else ())
        if overrides.get(name) is not None and overrides[name] not in allowed:
            raise ValueError(f"unknown {name}: {overrides[name]!r}")
    kind, texture = overrides.get("palette_kind"), overrides.get("texture")
    if kind is not None and texture in PALETTE_KINDS and kind != texture:
        raise ValueError("palette_kind and texture are aliases and must agree")


def _dimension(ctx, name, lo, hi, *, core, favored):
    if ctx.overrides.get(name) is not None:
        return ctx.draw_int_strict(name, lo, hi)
    choices = list(range(lo, hi + 1))
    choices += list(favored) * (60 if core else 3)
    return ctx.draw_choice(name, choices)


def _layout_ok(grid, profile):
    if self_check(grid):
        return False
    if profile == "interior":
        return _visible_interior(grid)
    if profile == "broad":
        anchor, cells = _parts(grid)
        rsum = min(r for r, c in cells) + max(r for r, c in cells)
        csum = min(c for r, c in cells) + max(c for r, c in cells)
        symmetric = set(cells) == {(rsum - r, csum - c) for r, c in cells}
        # Preserve full asymmetric copies and optionally clipped symmetric
        # motifs, while keeping this class distinct from the clipped witnesses.
        return symmetric or not _partial_clipping(grid)
    if not _partial_clipping(grid):
        return False
    intended = _copy(grid)
    return all(rival(grid) != intended for name, rival in LESSON_COMPETITORS.items()
               if name != "outline_only")


def _paint(h, w, cells, anchor, color):
    grid = full_grid(h, w, 0)
    for r, c in cells:
        grid[r][c] = color
    grid[anchor[0]][anchor[1]] = 9
    return grid


def _draw_from_degenerate(name, rng=None, h=7, w=9):
    if name == "no_shape":
        return _paint(h, w, (), (h // 2, w // 2), 3)
    if name == "no_anchor":
        grid = full_grid(h, w, 0)
        grid[1][1] = grid[1][2] = 3
        return grid
    if name == "reflection_oob":
        return _paint(h, w, ((2, 2), (2, 3)), (0, 0), 4)
    raise ValueError(f"unknown negative fixture {name!r}")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _controls(seed, sample_index, difficulty, overrides)
    normalized = dict(overrides)
    if overrides.get("texture") in PALETTE_KINDS:
        normalized["palette_kind"] = overrides["texture"]
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=normalized)
    core = ctx.draw_choice("scale_profile", ("canonical", "broad")) == "canonical"
    height_bias = (5,) if core else ((4, 5, 6) if difficulty == "easy" else (10, 11, 12) if difficulty == "hard" else (6, 7, 8))
    width_bias = (7, 8) if core else ((5, 6, 7) if difficulty == "easy" else (12, 13, 14) if difficulty == "hard" else (7, 8, 9))
    h = _dimension(ctx, "grid_h", 4, 12, core=core, favored=height_bias)
    w = _dimension(ctx, "grid_w", 5, 14, core=core, favored=width_bias)
    ctx.draw_int_strict("palette_size", 2, 2)
    ctx.draw_int_strict("n_distinct_colors", 3, 3)
    ctx.draw_choice("position_bias", ("shape_then_anchor_offset",))
    ctx.draw_choice("density", ("sparse",))
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], h=h, w=w)
    # Family is constant for one seed and constant overrides. The two instances
    # of each witness profile in any five slots receive consecutive colors.
    # The three shape classes cannot coincide. All five inputs are therefore
    # distinct, so deduplication cannot remove a needed witness before a query.
    families = PALETTE_KINDS if normalized.get("palette_kind") is not None else (PALETTE_KINDS[seed % len(PALETTE_KINDS)],)
    kind = ctx.draw_choice("palette_kind", families)
    ctx.draw_choice("texture", (kind,))
    palette = _PALETTES[kind]
    ordinal = 2 * (sample_index // LESSON_SCHEDULE_PERIOD) + (sample_index % LESSON_SCHEDULE_PERIOD) // 2
    color = ctx.draw_choice("shape_color", (palette[(seed + ordinal) % len(palette)],))
    profile = schedule_profile(seed, sample_index, difficulty)
    shapes = (_PLUS,) if profile == "interior" else (_SYMMETRIC + _ASYMMETRIC) if profile == "broad" else _ASYMMETRIC
    rng = ctx.draw_rng("layout")
    for _ in range(256):
        shape = rng.choice(shapes)
        sh = max(r for r, c in shape) + 1
        sw = max(c for r, c in shape) + 1
        sr, sc = rng.randrange(h - sh + 1), rng.randrange(w - sw + 1)
        cells = tuple((sr + r, sc + c) for r, c in shape)
        anchor = (rng.randrange(h), rng.randrange(w))
        if anchor in cells:
            continue
        grid = _paint(h, w, cells, anchor, color)
        if _layout_ok(grid, profile):
            return grid
    # Constructive witnesses valid for every advertised size, never an invalid
    # fallback. Both satisfy the same semantic schedule, including 4x5 corners.
    if profile == "interior":
        cells, anchor = ((2, 1), (1, 1), (3, 1), (2, 0), (2, 2)), (1, 2)
    elif profile == "broad":
        cells, anchor = ((0, 0), (0, 1)), (1, 1)
    else:
        cells, anchor = ((0, 2), (0, 3), (1, 3)), (1, 1)
    grid = _paint(h, w, cells, anchor, color)
    if not _layout_ok(grid, profile):
        raise RuntimeError("constructive witness does not meet the declared lesson contract")
    return grid
