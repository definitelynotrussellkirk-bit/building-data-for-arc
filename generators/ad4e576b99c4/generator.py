"""Input sampler for opposite-side diagonal shearing of a color-5 patch.

The unchanged Racket authority reads the color-5 bounding box, moves that
rectangular source patch to the opposite side of the color-1 field, and shifts
rows after the first three one column inward per row.  On the first color-6
row it paints color 9 between the sheared patch's final foot and the opposite
edge.  This module samples inputs only; Racket remains the label authority.

The canonical demonstrations all reuse one five-column comb mask.  Generated
sample indices cycle through that mask and two connected alternatives so every
three-pair lesson (two demos plus one query) refutes the plausible but wrong
"always use the public comb" shortcut under every query rotation.
"""
from __future__ import annotations

from copy import deepcopy

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "ad4e576b99c4"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "6de9bdaa4c45"
EXAMPLES_NEEDED = 2
MIN_STRICT_FRAC = 1.0
LESSON_SCHEDULE_PERIOD = 3
SCHEDULE_PROFILES = ("canonical_comb", "odd_teeth", "alternating_bands")

SUMMARY = (
    "A square 16-22 grid has a color-1 upper field and color-6 lower field. "
    "A connected color-5 rectangular-mask patch is flush with the left or "
    "right edge and ends immediately above the split. Move the entire source "
    "rectangle to the opposite edge, preserve its mask, and shear rows after "
    "the first three one column inward per row; paint the exposed part of the "
    "first color-6 row color 9."
)

INVARIANTS = [
    "the input palette is exactly colors 1, 5, and 6",
    "all rows from the horizontal split downward are solid color 6",
    "the color-5 bounding box is flush with exactly one side and ends one row above the split",
    "the source mask is 4-connected, has a full top row, and occupies every bounding-box row",
    "the patch dimensions leave room for the authority's one-column-per-row shear",
]

AXES = {
    "grid_h": {"type": "int", "default": "weighted 16..22; favors canonical 16..18", "valid": "16..22"},
    "grid_w": {"type": "int", "default": "weighted 16..22; usually equals grid_h", "valid": "16..22"},
    "bottom_rows": {"type": "int", "default": "difficulty-weighted 3..6", "valid": "3..6"},
    "patch_width": {"type": "int", "default": "weighted 3..7; favors canonical 5", "valid": "3..7"},
    "patch_height": {"type": "int", "default": "difficulty-weighted 4..10", "valid": "4..10"},
    "side": {"type": "str", "default": "uniform left|right", "valid": "left|right"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []

_INT_BOUNDS = {
    "grid_h": (16, 22),
    "grid_w": (16, 22),
    "bottom_rows": (3, 6),
    "patch_width": (3, 7),
    "patch_height": (4, 10),
}
_SIDES = ("left", "right")
_STEPS = ((-1, 0), (1, 0), (0, -1), (0, 1))


def schedule_profile(seed, sample_index, difficulty=None):
    """Cycle masks so any three consecutive pairs contain all three profiles."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % LESSON_SCHEDULE_PERIOD]


def _validate_request(difficulty, overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be one of None, easy, medium, hard")
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name, (lo, hi) in _INT_BOUNDS.items():
        if name not in overrides or overrides[name] is None:
            continue
        value = overrides[name]
        if type(value) is not int:
            raise ValueError(f"{name} must be an integer, not {type(value).__name__}")
        if not lo <= value <= hi:
            raise ValueError(f"{name}={value} outside [{lo}, {hi}]")
    if "side" in overrides and overrides["side"] is not None:
        value = overrides["side"]
        if type(value) is not str or value not in _SIDES:
            raise ValueError(f"side must be one of {_SIDES}, not {value!r}")


def _weighted_int(ctx, name, lo, hi, favored):
    # Every call retains the entire advertised exact-control domain.  Repeated
    # values weight defaults only; explicit overrides still pass the same gate.
    options = tuple(range(lo, hi + 1)) + tuple(favored)
    return ctx.draw_choice(name, options)


def _mask(profile, height, width, rng=None):
    if profile == "canonical_comb":
        return {
            (r, c)
            for r in range(height)
            for c in range(width)
            if r < 2 or c % 2 == 0
        }
    if profile == "odd_teeth":
        # A keyed spine gives many masks while keeping every lower tooth tied
        # to the full second row.  It can never equal the public even-tooth comb.
        spine = (rng.randrange(width) if rng is not None else width // 2)
        return {
            (r, c)
            for r in range(height)
            for c in range(width)
            if r < 2 or c % 2 == 1 or c == spine
        }
    if profile == "alternating_bands":
        # Full even rows connect the object; keyed spines vary the sparse rows.
        spines = {
            r: (rng.randrange(width) if rng is not None else width // 2)
            for r in range(1, height, 2)
        }
        return {
            (r, c)
            for r in range(height)
            for c in range(width)
            if r == 0 or r % 2 == 0 or c in (0, width - 1, spines[r])
        }
    raise ValueError(f"unknown schedule profile {profile!r}")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_request(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    h = _weighted_int(ctx, "grid_h", 16, 22, (16, 17, 18) * 30)
    # A strong square bias gives every pinned 20-draw band abundant exact
    # canonical dimension/palette hits while preserving every rectangular
    # override and occasional broad default rectangle.
    w = _weighted_int(ctx, "grid_w", 16, 22, (h,) * 100)

    if difficulty == "easy":
        bottom_favored = (5, 6) * 8
        height_favored = (4, 5, 6) * 6
    elif difficulty == "hard":
        bottom_favored = (3, 4) * 8
        height_favored = (8, 9, 10) * 6
    else:
        bottom_favored = (4, 5, 6) * 4
        height_favored = tuple(range(4, 11)) * 2

    bottom_rows = _weighted_int(ctx, "bottom_rows", 3, 6, bottom_favored)
    patch_width = _weighted_int(ctx, "patch_width", 3, 7, (5,) * 20)
    patch_height = _weighted_int(ctx, "patch_height", 4, 10, height_favored)
    side = ctx.draw_choice("side", _SIDES)

    boundary = h - bottom_rows
    # The declared Cartesian product is constructive: boundary >= 10,
    # patch_height <= 10, and max shear patch_height-3 <= 7 <= w-patch_width.
    if patch_height > boundary or patch_height - 3 > w - patch_width:
        raise RuntimeError("advertised axis combination unexpectedly infeasible")

    grid = full_grid(h, w, 1)
    for r in range(boundary, h):
        grid[r] = [6] * w

    r0 = boundary - patch_height
    c0 = 0 if side == "left" else w - patch_width
    profile = schedule_profile(seed, sample_index, difficulty)
    mask_rng = ctx.draw_rng("mask_variation")
    for dr, dc in _mask(profile, patch_height, patch_width, mask_rng):
        grid[r0 + dr][c0 + dc] = 5

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise RuntimeError("constructive generator produced invalid grid: " + "; ".join(errors))
    return grid


def _shape(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        raise ValueError("expected a nonempty rectangular grid")
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        raise ValueError("expected a nonempty rectangular grid")
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        raise ValueError("ragged grid")
    if any(type(value) is not int for row in grid for value in row):
        raise ValueError("all cells must be integer ARC colors")
    return len(grid), width


def _geometry(grid):
    h, w = _shape(grid)
    fives = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 5]
    sixes = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 6]
    if not fives:
        raise ValueError("no color-5 source patch")
    if not sixes:
        raise ValueError("no color-6 field")
    r0 = min(r for r, _ in fives)
    c0 = min(c for _, c in fives)
    r1 = max(r for r, _ in fives)
    c1 = max(c for _, c in fives)
    boundary = min(r for r, _ in sixes)
    side = "left" if c0 == 0 and c1 < w - 1 else "right" if c1 == w - 1 and c0 > 0 else None
    if side is None:
        raise ValueError("color-5 bounding box must touch exactly one horizontal edge")
    return {
        "h": h,
        "w": w,
        "r0": r0,
        "c0": c0,
        "r1": r1,
        "c1": c1,
        "boundary": boundary,
        "patch_height": r1 - r0 + 1,
        "patch_width": c1 - c0 + 1,
        "side": side,
    }


def observe_overrides(grid):
    g = _geometry(grid)
    return {
        "grid_h": g["h"],
        "grid_w": g["w"],
        "bottom_rows": g["h"] - g["boundary"],
        "patch_width": g["patch_width"],
        "patch_height": g["patch_height"],
        "side": g["side"],
    }


def _connected(cells):
    cells = set(cells)
    if not cells:
        return False
    reached = {min(cells)}
    todo = list(reached)
    for r, c in todo:
        for dr, dc in _STEPS:
            point = r + dr, c + dc
            if point in cells and point not in reached:
                reached.add(point)
                todo.append(point)
    return reached == cells


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty, meta
    try:
        h, w = _shape(grid)
    except ValueError as exc:
        return [str(exc)]
    errors = []
    palette = {value for row in grid for value in row}
    if not palette <= {1, 5, 6}:
        errors.append(f"input colors must be a subset of 1,5,6; found {sorted(palette)}")
    if palette != {1, 5, 6}:
        errors.append(f"input must contain colors 1,5,6; found {sorted(palette)}")
    try:
        g = _geometry(grid)
    except ValueError as exc:
        return errors + [str(exc)]

    br = g["boundary"]
    if not 1 <= br < h:
        errors.append("color-6 split must have nonempty fields above and below")
    for r in range(br):
        for c, value in enumerate(grid[r]):
            if value not in (1, 5):
                errors.append(f"cell ({r},{c}) above split must be color 1 or 5")
                break
    for r in range(br, h):
        if any(value != 6 for value in grid[r]):
            errors.append(f"row {r} at/below split must be solid color 6")
            break

    if g["r1"] != br - 1:
        errors.append("color-5 bounding box must end immediately above the color-6 split")
    if g["patch_height"] < 4 or g["patch_width"] < 3:
        errors.append("color-5 patch must be at least 4x3")
    if g["patch_height"] - 3 > w - g["patch_width"]:
        errors.append("color-5 patch is too tall to shear within the grid")

    local = {
        (r - g["r0"], c - g["c0"])
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 5
    }
    if any((0, c) not in local for c in range(g["patch_width"])):
        errors.append("top row of the color-5 bounding box must be full")
    for r in range(g["patch_height"]):
        if not any((r, c) in local for c in range(g["patch_width"])):
            errors.append(f"color-5 bounding-box row {r} is empty")
            break
    if not _connected(local):
        errors.append("color-5 cells must form one 4-connected patch")

    return errors


def strict_canonical_like(grid):
    """Accept the task-lawful split-field manifold, including all canonical inputs."""
    return self_check(grid)


def _source_mask(grid, geometry=None):
    g = geometry or _geometry(grid)
    return {
        (r - g["r0"], c - g["c0"])
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 5
    }


def _render(grid, mask):
    """Independent Python mirror of the selected Racket geometry for probes/tests."""
    g = _geometry(grid)
    h, w = g["h"], g["w"]
    ph, pw = g["patch_height"], g["patch_width"]
    move_right = g["c0"] < w // 2
    max_shift = max(0, ph - 3)
    final_start = w - pw - max_shift if move_right else max_shift

    out = [[1 if r < g["boundary"] else 6 for _ in range(w)] for r in range(h)]
    for c in range(w):
        if (move_right and c < final_start + pw - 1) or (
            not move_right and c > final_start
        ):
            out[g["boundary"]][c] = 9

    for dr, dc in mask:
        shift = max(0, dr - 2)
        start = w - pw - shift if move_right else shift
        out[g["r0"] + dr][start + dc] = 5
    return out


def rule_mirror(grid):
    """Supplementary Python oracle; the repository's Racket rule is authoritative."""
    return _render(grid, _source_mask(grid))


def _fixed_public_comb(grid):
    """RIVAL: infer geometry but always substitute the public five-mask family."""
    g = _geometry(grid)
    return _render(grid, _mask("canonical_comb", g["patch_height"], g["patch_width"]))


def _noncanonical_mask(grid):
    try:
        g = _geometry(grid)
        return _source_mask(grid, g) != _mask("canonical_comb", g["patch_height"], g["patch_width"])
    except Exception:
        return False


def lesson_identifiable(demos, query):
    """Check the declared canonical-fitting rival, not universal induction."""
    del query
    if any(_fixed_public_comb(pair["input"]) != pair["output"] for pair in demos):
        return []
    return ["the fixed-public-comb rival still fits every demonstration"]


SEMANTIC_WITNESSES = {"noncanonical_source_mask": _noncanonical_mask}
SEMANTIC_RIVALS = {"fixed_public_comb": _fixed_public_comb}
WITNESS_RIVALS = {"noncanonical_source_mask": ["fixed_public_comb"]}
CANONICAL_SHORTCUTS = {"fixed_public_comb": _fixed_public_comb}
LESSON_COMPETITORS = {"fixed_public_comb": _fixed_public_comb}
