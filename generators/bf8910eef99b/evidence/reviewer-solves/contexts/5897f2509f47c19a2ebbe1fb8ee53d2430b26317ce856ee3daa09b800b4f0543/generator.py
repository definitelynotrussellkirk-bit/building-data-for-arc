"""Input sampler for the canonical opposite-quadrant 2x2 stamping task.

The Racket authority is unchanged.  A solid 2x2 source block contains four
unique colors.  Each source corner paints a 2x2 patch in the diagonally
opposite quadrant at offsets two and three from the source block.  The grid
clips patches naturally; the original source cells remain unchanged.
"""
from __future__ import annotations

from copy import deepcopy

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "bf8910eef99b"
TASK_ID = GENERATOR_ID
RULE_HASH = "f45b7e9216b7"
VERSION = "2.0.0"
EXAMPLES_NEEDED = 3
SUMMARY = (
    "Four distinct colors form a 2x2 source. Each color paints a clipped 2x2 "
    "patch in the diagonally opposite quadrant, measured from the source block."
)

INVARIANTS = [
    "background is color 0 and every cell is an ARC color 0..9",
    "exactly four nonzero cells form one solid 2x2 block",
    "the four source cells have pairwise distinct colors",
    "the source position leaves at least one visible cell from each target patch",
    "production placement profiles clip exactly one grid side and keep the orthogonal axis interior",
]

PLACEMENT_PROFILES = ("top_clip", "right_clip", "bottom_clip", "left_clip")
PALETTES = (
    (1, 2, 3, 4),
    (1, 5, 7, 8),
    (2, 3, 4, 6),
    (2, 5, 8, 9),
    (1, 3, 6, 9),
    (4, 5, 7, 9),
)
_PALETTE_LOOKUP = {frozenset(colors): index for index, colors in enumerate(PALETTES)}

AXES = {
    "grid_h": {
        "type": "int",
        "default": "weighted 6..9; every band retains the complete domain",
        "valid": "6..9",
    },
    "grid_w": {
        "type": "int",
        "default": "weighted 6..9; every band retains the complete domain",
        "valid": "6..9",
    },
    "placement_profile": {
        "type": "str",
        "default": "uniform four one-side clipping profiles",
        "valid": "top_clip|right_clip|bottom_clip|left_clip",
    },
    "palette_id": {
        "type": "int",
        "default": "uniform 0..5",
        "valid": "0..5",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []
_VALID_DIFFICULTIES = (None, "easy", "medium", "hard")


def _validate_overrides(overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name in ("grid_h", "grid_w", "palette_id"):
        value = overrides.get(name)
        if value is not None and type(value) is not int:
            raise TypeError(f"{name} must be an integer (not bool)")
    profile = overrides.get("placement_profile")
    if profile is not None and type(profile) is not str:
        raise TypeError("placement_profile must be a string")


def _validate_call(seed, sample_index, difficulty, overrides):
    if type(seed) is not int:
        raise ValueError("seed must be an integer (not bool, float, or string)")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative integer (not bool)")
    if difficulty not in _VALID_DIFFICULTIES:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    _validate_overrides(overrides)


def _dimension_options(difficulty):
    """Keep every override legal in every band while making bands measurably different."""
    base = [6, 7, 8, 9]
    if difficulty == "easy":
        return base + [6] * 10 + [7] * 3
    if difficulty == "medium":
        return base + [6] * 8 + [7] * 5 + [8] * 2
    if difficulty == "hard":
        # Canonical-size support remains substantial enough for the 20-draw profile floor.
        return base + [6] * 7 + [8] * 4 + [9] * 5
    return base + [6] * 8 + [7, 8, 9]


def _profile_options(difficulty):
    base = list(PLACEMENT_PROFILES)
    if difficulty == "easy":
        return base + ["top_clip", "left_clip"] * 2
    if difficulty == "hard":
        return base + ["right_clip", "bottom_clip"] * 2
    return base


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(seed, sample_index, difficulty, overrides)
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    h = ctx.draw_choice("grid_h", _dimension_options(difficulty))
    w = ctx.draw_choice("grid_w", _dimension_options(difficulty))
    profile = ctx.draw_choice("placement_profile", _profile_options(difficulty))
    palette_id = ctx.draw_int_strict("palette_id", 0, len(PALETTES) - 1)

    if profile == "top_clip":
        br = 1
        bc = ctx.draw_rng("interior_column").randint(2, w - 4)
    elif profile == "right_clip":
        br = ctx.draw_rng("interior_row").randint(2, h - 4)
        bc = w - 3
    elif profile == "bottom_clip":
        br = h - 3
        bc = ctx.draw_rng("interior_column").randint(2, w - 4)
    elif profile == "left_clip":
        br = ctx.draw_rng("interior_row").randint(2, h - 4)
        bc = 1
    else:  # draw_choice normally catches this; retain an explicit totality guard.
        raise ValueError(f"unknown placement_profile: {profile!r}")

    colors = list(PALETTES[palette_id])
    ctx.draw_rng("source_color_order").shuffle(colors)
    grid = full_grid(h, w, 0)
    grid[br][bc], grid[br][bc + 1] = colors[0], colors[1]
    grid[br + 1][bc], grid[br + 1][bc + 1] = colors[2], colors[3]
    return grid


def _parse_block(grid):
    cells = [(r, c, value) for r, row in enumerate(grid)
             for c, value in enumerate(row) if value != 0]
    if len(cells) != 4:
        raise ValueError(f"expected exactly four nonzero cells, found {len(cells)}")
    rows = sorted({r for r, _, _ in cells})
    cols = sorted({c for _, c, _ in cells})
    if (len(rows) != 2 or len(cols) != 2 or rows[1] != rows[0] + 1
            or cols[1] != cols[0] + 1):
        raise ValueError("nonzero cells must form a contiguous 2x2 block")
    br, bc = rows[0], cols[0]
    colors = (grid[br][bc], grid[br][bc + 1],
              grid[br + 1][bc], grid[br + 1][bc + 1])
    if any(color == 0 for color in colors):
        raise ValueError("2x2 block must be solid")
    return br, bc, colors


def self_check(grid, *, difficulty=None, meta=None):
    if (not isinstance(grid, (list, tuple)) or not grid
            or not isinstance(grid[0], (list, tuple)) or not grid[0]):
        return ["expected a nonempty rectangular grid"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["ragged grid"]
    errors = []
    h, w = len(grid), width
    if not (6 <= h <= 9 and 6 <= w <= 9):
        errors.append(f"grid dimensions {h}x{w} outside 6..9 by 6..9")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        errors.append("cells must be integer ARC colors 0..9 (bool is not a color)")
        return errors
    try:
        br, bc, colors = _parse_block(grid)
    except ValueError as exc:
        errors.append(str(exc))
        return errors
    if len(set(colors)) != 4:
        errors.append("the four source cells must have distinct colors")
    # These are the exact visibility limits of the canonical clipped rule.  A
    # block may be closer than two cells to an edge, as canonical pair 0 is.
    if not (1 <= br <= h - 3):
        errors.append("source row must leave at least one visible cell in both vertical target directions")
    if not (1 <= bc <= w - 3):
        errors.append("source column must leave at least one visible cell in both horizontal target directions")
    return errors


def strict_canonical_like(grid):
    """The declared lawful manifold; exact 6x6 support is checked separately."""
    return self_check(grid)


def observe_overrides(grid):
    """Recover every advertised control from returned pixels alone."""
    errors = self_check(grid)
    if errors:
        raise ValueError("; ".join(errors))
    h, w = len(grid), len(grid[0])
    br, bc, colors = _parse_block(grid)
    if br == 1 and 2 <= bc <= w - 4:
        profile = "top_clip"
    elif bc == w - 3 and 2 <= br <= h - 4:
        profile = "right_clip"
    elif br == h - 3 and 2 <= bc <= w - 4:
        profile = "bottom_clip"
    elif bc == 1 and 2 <= br <= h - 4:
        profile = "left_clip"
    else:
        raise ValueError("grid is lawful but is not one of the four generated placement profiles")
    palette_id = _PALETTE_LOOKUP.get(frozenset(colors))
    if palette_id is None:
        raise ValueError("source colors do not match an advertised palette_id")
    return {"grid_h": h, "grid_w": w,
            "placement_profile": profile, "palette_id": palette_id}


def _paint(out, rows, cols, color):
    h, w = len(out), len(out[0])
    for r in rows:
        for c in cols:
            if 0 <= r < h and 0 <= c < w and out[r][c] == 0:
                out[r][c] = color


def expected_output(grid):
    br, bc, (tl, tr, bl, brr) = _parse_block(grid)
    out = deepcopy(grid)
    _paint(out, (br + 2, br + 3), (bc + 2, bc + 3), tl)
    _paint(out, (br + 2, br + 3), (bc - 2, bc - 1), tr)
    _paint(out, (br - 2, br - 1), (bc + 2, bc + 3), bl)
    _paint(out, (br - 2, br - 1), (bc - 2, bc - 1), brr)
    return out


def _complete_stamps_only(grid):
    """Rival: incorrectly discard a whole stamp if any part is out of bounds."""
    br, bc, colors = _parse_block(grid)
    h, w = len(grid), len(grid[0])
    out = deepcopy(grid)
    specs = (
        ((br + 2, br + 3), (bc + 2, bc + 3), colors[0]),
        ((br + 2, br + 3), (bc - 2, bc - 1), colors[1]),
        ((br - 2, br - 1), (bc + 2, bc + 3), colors[2]),
        ((br - 2, br - 1), (bc - 2, bc - 1), colors[3]),
    )
    for rows, cols, color in specs:
        if all(0 <= r < h for r in rows) and all(0 <= c < w for c in cols):
            _paint(out, rows, cols, color)
    return out



_CANONICAL_PALETTE_SETS = frozenset({
    frozenset((1, 2, 4, 6)),
    frozenset((3, 7, 8, 9)),
    frozenset((2, 3, 5, 6)),
    frozenset((1, 2, 3, 5)),
})


def _canonical_palette_memorization(grid):
    """Rival: clip correctly only for palettes memorized from canonical data."""
    _, _, colors = _parse_block(grid)
    if frozenset(colors) in _CANONICAL_PALETTE_SETS:
        return expected_output(grid)
    return _complete_stamps_only(grid)


def _single_cell_copies(grid):
    """Rival: copy each source color only once in its opposite quadrant."""
    br, bc, colors = _parse_block(grid)
    out = deepcopy(grid)
    for (r, c), color in zip(((br + 2, bc + 2), (br + 2, bc - 1),
                              (br - 1, bc + 2), (br - 1, bc - 1)), colors):
        _paint(out, (r,), (c,), color)
    return out


def _same_quadrant_stamps(grid):
    """Rival: extend each source corner into its own, rather than opposite, quadrant."""
    br, bc, (tl, tr, bl, brr) = _parse_block(grid)
    out = deepcopy(grid)
    _paint(out, (br - 2, br - 1), (bc - 2, bc - 1), tl)
    _paint(out, (br - 2, br - 1), (bc + 2, bc + 3), tr)
    _paint(out, (br + 2, br + 3), (bc - 2, bc - 1), bl)
    _paint(out, (br + 2, br + 3), (bc + 2, bc + 3), brr)
    return out


def _absolute_corner_stamps(grid):
    """Rival: attach stamps to the four grid corners, ignoring source offsets."""
    _, _, (tl, tr, bl, brr) = _parse_block(grid)
    h, w = len(grid), len(grid[0])
    out = deepcopy(grid)
    _paint(out, (h - 2, h - 1), (w - 2, w - 1), tl)
    _paint(out, (h - 2, h - 1), (0, 1), tr)
    _paint(out, (0, 1), (w - 2, w - 1), bl)
    _paint(out, (0, 1), (0, 1), brr)
    return out


def _clockwise_color_roles(grid):
    """Rival: correct target regions but rotate source-color roles clockwise."""
    br, bc, (tl, tr, bl, brr) = _parse_block(grid)
    out = deepcopy(grid)
    _paint(out, (br + 2, br + 3), (bc + 2, bc + 3), tr)
    _paint(out, (br + 2, br + 3), (bc - 2, bc - 1), brr)
    _paint(out, (br - 2, br - 1), (bc + 2, bc + 3), tl)
    _paint(out, (br - 2, br - 1), (bc - 2, bc - 1), bl)
    return out


SEMANTIC_RIVALS = {
    "complete_stamps_only": _complete_stamps_only,
    "canonical_palette_memorization": _canonical_palette_memorization,
    "single_cell_copies": _single_cell_copies,
    "same_quadrant_stamps": _same_quadrant_stamps,
    "absolute_corner_stamps": _absolute_corner_stamps,
    "clockwise_color_roles": _clockwise_color_roles,
}
LESSON_COMPETITORS = {
    name: rival for name, rival in SEMANTIC_RIVALS.items()
    if name != "canonical_palette_memorization"
}
# This adversarial overfit reproduces every labelled canonical pair by memorizing
# its palette set, then mishandles clipping for every unseen palette.  Production
# palettes are intentionally disjoint from all four canonical palette sets.
CANONICAL_SHORTCUTS = {
    "canonical_palette_memorization": _canonical_palette_memorization,
}
SEMANTIC_WITNESSES = {
    name: (lambda grid, name=name: SEMANTIC_RIVALS[name](grid) != expected_output(grid))
    for name in SEMANTIC_RIVALS
}
WITNESS_RIVALS = {name: [name] for name in SEMANTIC_RIVALS}


def lesson_identifiable(demos, query):
    """Finite-rival check; not a claim of uniqueness over all possible programs."""
    if not isinstance(demos, (list, tuple)) or not demos:
        return ["at least one demonstration is required"]
    if not isinstance(query, dict) or self_check(query.get("input")):
        return ["query is not a lawful task input"]
    errors = []
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or self_check(demo.get("input")):
            errors.append(f"demo {index} is not a lawful task pair")
        elif demo.get("output") != expected_output(demo["input"]):
            errors.append(f"demo {index} output disagrees with the diagnostic oracle")
    if errors:
        return errors
    truth = expected_output(query["input"])
    competitors = dict(LESSON_COMPETITORS)
    competitors.update(CANONICAL_SHORTCUTS)
    for name, rival in competitors.items():
        if (all(rival(demo["input"]) == demo["output"] for demo in demos)
                and rival(query["input"]) != truth):
            errors.append(f"rival {name} matches every demo but changes the query")
    return errors
