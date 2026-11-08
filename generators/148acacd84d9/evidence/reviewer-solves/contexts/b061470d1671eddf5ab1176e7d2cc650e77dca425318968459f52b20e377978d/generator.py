"""Sparse, multicolor inputs for the canonical clockwise square rotation.

Default lessons alternate canonical-size squares and larger squares. Explicit
dimension overrides also support rectangles; that extension is not taught by
the default square lessons. Racket remains the label authority.
"""
from __future__ import annotations

from functools import partial

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "148acacd84d9"
TASK_ID = "148acacd84d9"
VERSION = "2.0.1"
RULE_HASH = "2f0ece3d3c8f"
SUMMARY = "Rotate a sparse multicolor square grid 90 degrees clockwise."

INVARIANTS = [
    "normal grids have dimensions 4..12, zero background and integer colors 0..9",
    "normal grids contain exactly 3..12 foreground cells and 3..10 total colors",
    "default grids are square; independent exact dimension overrides permit rectangles",
    "default lessons alternate canonical-size and larger squares in every difficulty",
    "normal draws distinguish clockwise rotation from the other seven D4 maps",
    "default larger squares distinguish canvas rotation from cropping and repadding the foreground",
]
AXES = {
    "grid_h": {"type": "int", "default": "4..6 on even indices; 7..12 on odd indices, band weighted", "valid": "4..12"},
    "grid_w": {"type": "int", "default": "same as grid_h unless explicitly overridden", "valid": "4..12"},
    "mark_count": {"type": "int", "default": "3..5 in canonical profiles; 3..12 otherwise", "valid": "3..12"},
    "palette_size": {"type": "int", "default": "4..5 in canonical profiles; 3..min(10, mark_count+1) otherwise, including zero", "valid": "3..10"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = [("mark_count", "palette_size")]

# Explicit diagnostic fixtures, outside the normal AXES domain. They are lawful
# inputs to Racket's rotation, but fail the sparse multicolor teaching-input
# validator and are never sampled into normal lessons.
DEGENERATE_TEXTURES = ("empty_grid", "single_mark", "full_grid")

EXAMPLES_NEEDED = 3
LESSON_SCHEDULE_PERIOD = 2
SCHEDULE_PROFILES = ("canonical_size", "larger_square")


def schedule_profile(seed, sample_index, difficulty=None):
    return SCHEDULE_PROFILES[sample_index % LESSON_SCHEDULE_PERIOD]


def _incompatible(axes, message):
    error = ValueError(message)
    error.incompatible_axes = tuple(axes)
    raise error


def _validate_overrides(overrides):
    unknown = set(overrides) - set(AXES) - {"texture"}
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(sorted(unknown))}")
    for name, value in overrides.items():
        if name == "texture":
            continue
        if type(value) is not int:
            raise ValueError(f"{name} must be an integer, not {type(value).__name__}")
        lo, hi = {"grid_h": (4, 12), "grid_w": (4, 12),
                  "mark_count": (3, 12), "palette_size": (3, 10)}[name]
        if not lo <= value <= hi:
            raise ValueError(f"{name} must be in {lo}..{hi}")


def _diagnostic_texture(name):
    if name not in DEGENERATE_TEXTURES:
        raise ValueError(f"unknown diagnostic texture: {name!r}")
    grid = full_grid(5, 5, 3 if name == "full_grid" else 0)
    if name == "single_mark":
        grid[2][2] = 3
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_overrides(overrides)
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be easy, medium, hard, or None")
    if "texture" in overrides:
        if len(overrides) != 1:
            _incompatible(overrides, "diagnostic textures cannot be combined with exact normal controls")
        return _diagnostic_texture(overrides["texture"])

    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    core = schedule_profile(seed, sample_index, difficulty) == "canonical_size"
    if "grid_h" in overrides:
        height = ctx.draw_int_strict("grid_h", 4, 12)
    else:
        if core:
            sizes = (4, 5, 6)
        else:
            # Bands change weights, never the accepted exact-override domain.
            favored = {"easy": (7, 8), "medium": (8, 9, 10),
                       "hard": (10, 11, 12)}.get(difficulty, (8, 9, 10))
            sizes = tuple(range(7, 13)) + favored * 3
        height = ctx.draw_choice("grid_h", sizes)
    width = (ctx.draw_int_strict("grid_w", 4, 12) if "grid_w" in overrides
             else ctx.draw_choice("grid_w", (height,)))

    # Canonical (size, marks, TOTAL palette) profiles, with newly drawn positions
    # and color identities: 4x4/3/4, 5x5/4/4, 6x6/5/5.
    core_marks, core_palette = {4: (3, 4), 5: (4, 4), 6: (5, 5)}.get(height, (4, 4))
    required_marks = max(3, overrides.get("palette_size", 3) - 1)
    if "mark_count" in overrides:
        count = ctx.draw_int_strict("mark_count", 3, 12)
    elif core:
        count = ctx.draw_choice("mark_count", (max(core_marks, required_marks),))
    else:
        favored = {"easy": (3, 4, 5), "medium": (5, 6, 7, 8),
                   "hard": (8, 9, 10, 11, 12)}.get(difficulty, (5, 6, 7, 8))
        counts = tuple(range(required_marks, 13))
        counts += tuple(n for n in favored if n >= required_marks) * 3
        count = ctx.draw_choice("mark_count", counts)
    if "palette_size" in overrides:
        palette_size = ctx.draw_int_strict("palette_size", 3, 10)
    else:
        if core and height == 5:
            palettes = (min(4, count + 1), min(5, count + 1))
        else:
            palettes = ((min(core_palette, count + 1),) if core
                        else tuple(range(3, min(10, count + 1) + 1)))
        palette_size = ctx.draw_choice("palette_size", palettes)
    if palette_size > count + 1:
        _incompatible(("mark_count", "palette_size"),
                      "palette_size includes zero and cannot exceed mark_count + 1")

    colors = ctx.draw_distinct_colors("foreground_colors", n=palette_size - 1, exclude=(0,))
    rng = ctx.draw_rng("layout")
    cells = [(r, c) for r in range(height) for c in range(width)]
    teach_canvas = not core and not overrides
    # Teaching margins are confined to default larger squares. Applying this
    # condition blindly to dense 4x4 overrides would break feasible requests.
    for _attempt in range(128):
        if teach_canvas:
            top, bottom, left, right = rng.choice(
                ((1, 3, 1, 1), (3, 1, 1, 1), (1, 1, 1, 3), (1, 1, 3, 1)))
            interior = [(r, c) for r in range(top, height - bottom)
                        for c in range(left, width - right)]
            # Keep the shorter margin exactly one, with the opposite margin
            # at least three. The near-edge mark has a random location/color.
            if bottom == 3:
                edge = [cell for cell in interior if cell[0] == top]
            elif top == 3:
                edge = [cell for cell in interior if cell[0] == height - bottom - 1]
            elif right == 3:
                edge = [cell for cell in interior if cell[1] == left]
            else:
                edge = [cell for cell in interior if cell[1] == width - right - 1]
            anchor = rng.choice(edge)
            positions = [anchor] + rng.sample([cell for cell in interior if cell != anchor], count - 1)
        else:
            positions = rng.sample(cells, count)
        values = list(colors) + [rng.choice(colors) for _ in range(count - len(colors))]
        rng.shuffle(values)
        grid = full_grid(height, width, 0)
        for (r, c), color in zip(positions, values):
            grid[r][c] = color
        rotated = _rot_cw(grid)
        if (all(rival(grid) != rotated for rival in _GEOMETRIC_RIVALS.values())
                and (not teach_canvas or all(rival(grid) != rotated for rival in _CROP_RIVALS.values()))):
            return grid
    raise RuntimeError("could not draw an orientation-distinguishing layout in 128 attempts")


def observe_overrides(grid):
    """Recover exact controls from pixels, including zero in palette_size."""
    colors = [value for row in grid for value in row]
    return {"grid_h": len(grid), "grid_w": len(grid[0]),
            "mark_count": sum(value != 0 for value in colors),
            "palette_size": len(set(colors))}


def _rot_cw(grid):
    return [list(row) for row in zip(*grid[::-1])]


def _identity(grid):
    return [list(row) for row in grid]


def _rot_ccw(grid):
    return [list(row) for row in zip(*grid)][::-1]


def _rot180(grid):
    return [list(reversed(row)) for row in reversed(grid)]


def _flip_lr(grid):
    return [list(reversed(row)) for row in grid]


def _flip_ud(grid):
    return [list(row) for row in reversed(grid)]


def _transpose(grid):
    return [list(row) for row in zip(*grid)]


def _antitranspose(grid):
    return _rot180(_transpose(grid))


def _canonical_sizes_only(grid):
    """Canonical-fitting rival: refuse rotation outside the original sizes."""
    if len(grid) == len(grid[0]) and 4 <= len(grid) <= 6:
        return _rot_cw(grid)
    return _identity(grid)


def _alignment_offset(gap, placement):
    return {"start": 0, "center": gap // 2,
            "center_ceil": (gap + 1) // 2, "end": gap}[placement]


def _crop_repad(grid, *, vertical, horizontal):
    """Rival: rotate only the foreground bbox, then align it on a zero canvas."""
    height, width = len(grid), len(grid[0])
    output = full_grid(width, height, 0)
    marks = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value != 0]
    if not marks:
        return output
    r0, r1 = min(r for r, _ in marks), max(r for r, _ in marks)
    c0, c1 = min(c for _, c in marks), max(c for _, c in marks)
    crop = _rot_cw([list(row[c0:c1 + 1]) for row in grid[r0:r1 + 1]])
    row_offset = _alignment_offset(width - len(crop), vertical)
    col_offset = _alignment_offset(height - len(crop[0]), horizontal)
    for r, row in enumerate(crop):
        for c, color in enumerate(row):
            output[r + row_offset][c + col_offset] = color
    return output


_CROP_PLACEMENTS = ("start", "center", "center_ceil", "end")
_CROP_RIVALS = {
    f"crop_{vertical}_{horizontal}": partial(_crop_repad, vertical=vertical, horizontal=horizontal)
    for vertical in _CROP_PLACEMENTS for horizontal in _CROP_PLACEMENTS
}
_GEOMETRIC_RIVALS = {
    "identity": _identity, "counterclockwise": _rot_ccw, "halfturn": _rot180,
    "flip_lr": _flip_lr, "flip_ud": _flip_ud, "transpose": _transpose,
    "antitranspose": _antitranspose,
}
SEMANTIC_RIVALS = {**_GEOMETRIC_RIVALS, **_CROP_RIVALS, "canonical_sizes_only": _canonical_sizes_only}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    "canonical_sizes_only": _canonical_sizes_only,
    **{f"crop_{vertical}_{horizontal}": _CROP_RIVALS[f"crop_{vertical}_{horizontal}"]
       for vertical in ("start", "center") for horizontal in _CROP_PLACEMENTS},
}


def _orientation_witness(grid):
    rotated = _rot_cw(grid)
    return all(rival(grid) != rotated for rival in _GEOMETRIC_RIVALS.values())


def _larger_square_witness(grid):
    return (len(grid) == len(grid[0]) and len(grid) > 6
            and _canonical_sizes_only(grid) != _rot_cw(grid))


def _canvas_origin_witness(grid):
    rotated = _rot_cw(grid)
    return all(rival(grid) != rotated for rival in _CROP_RIVALS.values())


SEMANTIC_WITNESSES = {
    "orientation_distinguished": _orientation_witness,
    "larger_square": _larger_square_witness,
    "canvas_origin": _canvas_origin_witness,
}
WITNESS_RIVALS = {
    "orientation_distinguished": list(_GEOMETRIC_RIVALS),
    "larger_square": ["canonical_sizes_only"],
    "canvas_origin": list(_CROP_RIVALS),
}


def self_check(grid, *, difficulty=None, meta=None):
    """Validate the normal sparse multicolor domain, not all Racket inputs."""
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a nonempty sequence of rows"]
    if any(not isinstance(row, (list, tuple)) or not row for row in grid):
        return ["rows must be nonempty sequences"]
    if any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be rectangular"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["grid values must be integer ARC colors 0..9, excluding booleans"]
    errors = []
    observed = observe_overrides(grid)
    if not (4 <= observed["grid_h"] <= 12 and 4 <= observed["grid_w"] <= 12):
        errors.append("normal grid dimensions must be in 4..12")
    if not 3 <= observed["mark_count"] <= 12:
        errors.append("normal samples must contain 3..12 nonzero marks")
    if not any(value == 0 for row in grid for value in row):
        errors.append("normal samples must have zero background")
    if not 3 <= observed["palette_size"] <= 10:
        errors.append("normal samples need at least two foreground colors")
    if _rot_cw(grid) == [list(row) for row in grid]:
        errors.append("normal samples must show a nonidentity clockwise rotation")
    return errors


def strict_canonical_like(grid):
    errors = self_check(grid)
    if not errors and len(grid) != len(grid[0]):
        errors.append("rectangles are an explicit extension outside the default square curriculum")
    return errors


def lesson_identifiable(demos, query):
    """Check only declared rivals; answer-equivalent survivors are harmless."""
    reasons = []
    for name, rival in LESSON_COMPETITORS.items():
        if (all(rival(pair["input"]) == pair["output"] for pair in demos)
                and rival(query["input"]) != query["output"]):
            reasons.append(f"{name} fits every demonstration but changes the query answer")
    return reasons
