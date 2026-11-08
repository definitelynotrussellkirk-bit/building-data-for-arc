"""Compact, teachable inputs for the fixed `(rule! rotate-ccw)` authority."""
from __future__ import annotations

from collections import Counter
import math

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.objects import find_objects
from puzzle_generators.helpers.textures import (
    fill_texture, apply_bg_density, apply_noise_overlay, apply_border,
)

GENERATOR_ID = "864eaaac6503"
VERSION = "2.0.0"
TASK_ID = "864eaaac6503"
RULE_HASH = "56583247080a"
SUMMARY = "Rotate a compact multicolor grid 90 degrees counterclockwise."
INVARIANTS = [
    "nonempty rectangular ARC integer grid, with dimensions at most 30",
    "at least two realized colors, with exact requested dimensions and palette size",
    "default lessons alternate canonical profiles and informative size generalizations",
]
HELPFUL_TEXTURES = (
    "noise", "sparse", "blob", "stripes", "gradient", "checkerboard", "frame", "ring", "plus",
)
# Texture and overlay controls describe a sampling procedure, not an exact
# recoverable image statistic. Dimensions and realized palette count are exact.
AXES = {
    "grid_h": {"type": "int", "default": "canonical 3; extended 4..13", "valid": "2..30"},
    "grid_w": {"type": "int", "default": "canonical 3; extended 4..13", "valid": "2..30"},
    "palette_size": {"type": "int", "default": "canonical 2; extended 2..4", "valid": "2..10"},
    "texture": {"type": "str", "default": "noise|sparse|blob", "valid": "|".join(HELPFUL_TEXTURES),
                "exact": False},
    "bg_density": {"type": "float", "default": 0.0, "valid": "0..0.95", "exact": False},
    "noise_overlay": {"type": "float", "default": 0.0, "valid": "0..0.5", "exact": False},
    "border_mode": {"type": "str", "default": "free", "valid": "free|always_bg|always_fg", "exact": False},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []  # Actual conflicts carry incompatible_axes.
EXAMPLES_NEEDED = 3
LESSON_SCHEDULE_PERIOD = 4
SCHEDULE_PROFILES = ("canonical", "extended_even", "extended_odd")
MIN_STRICT_FRAC = 0.25


def _identity(grid):
    return [list(row) for row in grid]


def _ccw(grid):
    return [list(row) for row in zip(*grid)][::-1]


def _cw(grid):
    return [list(row) for row in zip(*grid[::-1])]


def _half_turn(grid):
    return [list(reversed(row)) for row in reversed(grid)]


def _flip_lr(grid):
    return [list(reversed(row)) for row in grid]


def _flip_ud(grid):
    return [list(row) for row in reversed(grid)]


def _transpose(grid):
    return [list(row) for row in zip(*grid)]


def _anti_transpose(grid):
    return _half_turn(_transpose(grid))


def _only_three_by_three(grid):
    return _ccw(grid) if len(grid) == 3 and len(grid[0]) == 3 else _identity(grid)


def _foreground_components(grid):
    return sorted((sorted(cell for _, cell in obj)
                   for obj in find_objects(grid, univalued=True, bg=0)), key=lambda cells: cells[0])


def _first_component_rotation(grid):
    components = _foreground_components(grid)
    masked = [[0 for _ in row] for row in grid]
    if components:
        for r, c in components[0]:
            masked[r][c] = grid[r][c]
    return _ccw(masked)


def _nearest_component_changes(grid, reverse_ties=False):
    # Independent input-only version of a searched partial-construction rival:
    # apply only changes spatially attributed to the first nonblack component.
    # On rectangles the corresponding partial-object rotation is used.
    if len(grid) != len(grid[0]):
        return _first_component_rotation(grid)
    output = _ccw(grid)
    components = _foreground_components(grid)
    if not components:
        return output
    for r, row in enumerate(output):
        for c, value in enumerate(row):
            if value == grid[r][c]:
                continue
            distances = [min(abs(r - rr) + abs(c - cc) for rr, cc in cells)
                         for cells in components]
            tied = [i for i, distance in enumerate(distances) if distance == min(distances)]
            owner = tied[-1] if reverse_ties else tied[0]
            if owner != 0:
                output[r][c] = grid[r][c]
    return output


def _reverse_tie_component_changes(grid):
    return _nearest_component_changes(grid, reverse_ties=True)


DIHEDRAL_RIVALS = ("identity", "clockwise", "half_turn", "flip_lr", "flip_ud", "transpose", "anti_transpose")
FOREGROUND_RIVALS = ("first_component_rotation", "nearest_component_changes", "reverse_tie_component_changes")
SEMANTIC_RIVALS = {
    "identity": _identity, "clockwise": _cw, "half_turn": _half_turn,
    "flip_lr": _flip_lr, "flip_ud": _flip_ud, "transpose": _transpose,
    "anti_transpose": _anti_transpose, "only_three_by_three": _only_three_by_three,
    "first_component_rotation": _first_component_rotation,
    "nearest_component_changes": _nearest_component_changes,
    "reverse_tie_component_changes": _reverse_tie_component_changes,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {"only_three_by_three": _only_three_by_three}


def _all_dihedral_rivals_refuted(grid):
    expected = _ccw(grid)
    return all(SEMANTIC_RIVALS[name](grid) != expected for name in DIHEDRAL_RIVALS)


def _whole_foreground_distinguished(grid):
    expected = _ccw(grid)
    return all(SEMANTIC_RIVALS[name](grid) != expected for name in FOREGROUND_RIVALS)


SEMANTIC_WITNESSES = {
    "orientation_distinguished": _all_dihedral_rivals_refuted,
    "size_generalization": lambda grid: (len(grid), len(grid[0])) != (3, 3)
        and _ccw(grid) != grid,
    "whole_foreground": _whole_foreground_distinguished,
}
WITNESS_RIVALS = {
    "orientation_distinguished": ["identity", "clockwise", "half_turn", "flip_lr",
                                   "flip_ud", "transpose", "anti_transpose"],
    "size_generalization": ["only_three_by_three"],
    "whole_foreground": list(FOREGROUND_RIVALS),
}


def schedule_profile(seed, sample_index, difficulty=None):
    if sample_index % 2 == 0:
        return "canonical"
    return "extended_even" if (sample_index // 2) % 2 == 0 else "extended_odd"


def _integer(name, value, lo, hi=None):
    if type(value) is not int:
        raise TypeError(f"{name} must be an integer, not {type(value).__name__}")
    if value < lo or (hi is not None and value > hi):
        raise ValueError(f"{name} outside [{lo}, {hi if hi is not None else 'unbounded'}]")


def _conflict(message, overrides):
    error = ValueError(message + "; overrides=" + repr(overrides))
    error.incompatible_axes = tuple(sorted(overrides))
    raise error


def _fit_capacity(h, w, n_colors, border, overrides):
    if border != "free":
        for key, size in (("grid_h", h), ("grid_w", w)):
            if key in overrides and size < 3:
                _conflict("A uniform border and two colors require both dimensions >=3", overrides)
        h, w = max(h, 3), max(w, 3)
    capacity = lambda: h * w if border == "free" else (h - 2) * (w - 2) + 1
    while capacity() < n_colors:
        adjustable = [(h, "grid_h"), (w, "grid_w")]
        adjustable = [(size, key) for size, key in adjustable if key not in overrides and size < 30]
        if not adjustable:
            _conflict("palette_size exceeds available cells after grid_h/grid_w/border_mode constraints", overrides)
        _, key = min(adjustable)
        if key == "grid_h":
            h += 1
        else:
            w += 1
    return h, w


def _realize_palette(grid, palette, rng, border):
    counts = Counter(value for row in grid for value in row)
    cells = [(r, c) for r in range(len(grid)) for c in range(len(grid[0]))
             if border == "free" or (0 < r < len(grid) - 1 and 0 < c < len(grid[0]) - 1)]
    rng.shuffle(cells)
    for color in palette:
        if counts[color]:
            continue
        for r, c in cells:
            old = grid[r][c]
            if counts[old] > 1:
                grid[r][c] = color
                counts[old] -= 1
                counts[color] += 1
                break
        else:
            raise RuntimeError("No color-preserving capacity after validated constraints")
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _integer("seed", seed, 0)
    _integer("sample_index", sample_index, 0)
    if difficulty is not None and (type(difficulty) is not str or difficulty not in {"easy", "medium", "hard"}):
        raise ValueError("difficulty must be None, easy, medium, or hard")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError("Unknown override axes: " + ", ".join(unknown))
    overrides = {key: value for key, value in overrides.items() if value is not None}
    for key, lo, hi in (("grid_h", 2, 30), ("grid_w", 2, 30), ("palette_size", 2, 10)):
        if key in overrides:
            _integer(key, overrides[key], lo, hi)
    for key, hi in (("bg_density", 0.95), ("noise_overlay", 0.5)):
        if key in overrides:
            value = overrides[key]
            if type(value) not in (int, float) or not math.isfinite(value) or not 0 <= value <= hi:
                raise ValueError(f"{key} must be a finite number in [0, {hi}]")
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    profile = schedule_profile(seed, sample_index, difficulty)
    # The indexed C,E cycle gives every three consecutive demos an E witness;
    # each four-pair window has two E witnesses. Their minimum dimensions have
    # alternating parity, so production deduplication cannot discard either.
    # Difficulty controls extension size, not override legality.
    if profile == "canonical":
        h = w = 3
        c_hi = 2
    else:
        lo, hi, c_hi = {"easy": (4, 5, 2), "medium": (4, 8, 3),
                        "hard": (5, 12, 4), None: (4, 8, 3)}[difficulty]
        extent_parity = (sample_index // 2) % 2
        h = ctx.draw_choice("extended_size", [n for n in range(lo, hi + 1) if n % 2 == extent_parity])
        w = h
        geometry = ctx.draw_int_strict("geometry", 0, 9)
        if geometry == 0:
            w += 1
        elif geometry == 1:
            h += 1
    colors = ctx.draw_int_strict("palette_size", 2, 10 if "palette_size" in overrides else c_hi)
    h, w = overrides.get("grid_h", h), overrides.get("grid_w", w)
    border = ctx.draw_choice("border_mode", ["free", "always_bg", "always_fg"]) if "border_mode" in overrides else "free"
    h, w = _fit_capacity(h, w, colors, border, overrides)
    # Record exactly the dimensions that will be realized, including any
    # automatic expansion of dimensions the caller did not pin.
    h = ctx.draw_int_strict("grid_h", 2, 30) if "grid_h" in overrides else ctx.draw_int_strict("grid_h", h, h)
    w = ctx.draw_int_strict("grid_w", 2, 30) if "grid_w" in overrides else ctx.draw_int_strict("grid_w", w, w)
    palette = (0,) + ctx.draw_distinct_colors("nonzero_palette", n=colors - 1, exclude={0})
    texture = ctx.draw_choice("texture", list(HELPFUL_TEXTURES) if "texture" in overrides else ["noise", "sparse", "blob"])
    background_density = float(overrides.get("bg_density", 0.0))
    noise = float(overrides.get("noise_overlay", 0.0))
    rng = ctx.draw_rng("cells")
    for attempt in range(256):
        # Fixed texture overrides are sampling controls. Palette realization
        # and border constraints may alter their motif; no exact texture claim.
        selected = texture if attempt < 64 else "noise"
        grid = fill_texture(selected, h, w, palette, rng)
        if background_density:
            grid = apply_bg_density(grid, palette, rng, background_density)
        if noise:
            grid = apply_noise_overlay(grid, palette, rng, noise)
        grid = apply_border(grid, palette, rng, border)
        grid = _realize_palette(grid, palette, rng, border)
        if overrides:
            return grid
        if profile == "canonical" and _ccw(grid) != grid:
            return grid
        if profile != "canonical" and _all_dihedral_rivals_refuted(grid) and _whole_foreground_distinguished(grid):
            return grid
    raise RuntimeError("Could not sample an informative default rotation example in 256 attempts")


def self_check(grid, *, difficulty=None, meta=None):
    """Validate lawful rotation inputs without inventing foreground grammar."""
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must contain rows"]
    if not all(isinstance(row, (list, tuple)) for row in grid) or not grid[0]:
        return ["grid must contain nonempty rows"]
    h, w = len(grid), len(grid[0])
    if not (1 <= h <= 30 and 1 <= w <= 30) or any(len(row) != w for row in grid):
        return ["grid must be rectangular with dimensions in 1..30"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["every cell must be a Python integer in 0..9"]
    if len({value for row in grid for value in row}) < 2:
        return ["need at least two realized colors"]
    return []


def strict_canonical_like(grid):
    errors = self_check(grid)
    if errors:
        return errors
    colors = {value for row in grid for value in row}
    return [] if len(grid) == len(grid[0]) == 3 and len(colors) == 2 and 0 in colors else [
        "canonical profile is a 3x3 grid with black plus one nonzero color"]


def observe_overrides(grid):
    return {"grid_h": len(grid), "grid_w": len(grid[0]),
            "palette_size": len({value for row in grid for value in row})}


def lesson_identifiable(demos, query):
    """Finite declared-rival check; never a universal induction claim."""
    return ["rival " + name + " fits demonstrations but changes the query"
            for name, rival in LESSON_COMPETITORS.items()
            if all(rival(pair["input"]) == pair["output"] for pair in demos)
            and rival(query["input"]) != query["output"]]


def mutation_fixtures():
    return [("ragged", [[0, 1], [0]]), ("boolean_cell", [[0, True], [1, 0]]),
            ("out_of_palette", [[0, 10], [1, 0]]), ("monochrome", [[0, 0], [0, 0]])]
