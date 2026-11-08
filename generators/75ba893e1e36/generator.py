"""Input sampler for 59341089: mirror | input | mirror | input.

The canonical Racket rule supplies every authoritative label. Ordinary draws
are LR-asymmetric fields with exactly two or three colors. Even sample indices
anchor the canonical 3x3 profile; odd indices teach width generalization.
Texture and density controls are causal priors, followed by exact constraints.
Deliberately uninformative inputs have a separate make_degenerate API.
"""
from __future__ import annotations

import math

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.textures import fill_texture, apply_bg_density, apply_noise_overlay

GENERATOR_ID = "75ba893e1e36"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "6d59d4b5186a"
SUMMARY = "Teach horizontal mirror|input|mirror|input with canonical anchors and varied-width witnesses."
INVARIANTS = [
    "ordinary inputs are rectangular integer ARC grids, height 1..15 and width 2..7",
    "exactly two or three distinct requested colors occur in every returned input",
    "an unequal horizontally mirrored cell pair makes the reflection observable",
    "default even indices are canonical 3x3; default odd indices have width other than 3",
    "texture/density priors can be adjusted by the exact palette and asymmetry constraints",
]
HELPFUL_TEXTURES = (
    "noise", "sparse", "blob", "stripes", "gradient",
    "checkerboard", "frame", "ring", "plus",
)
# These are names for make_degenerate(), not ordinary texture overrides.
NEGATIVE_FIXTURES = ("lr_symmetric", "monochrome", "single_col")
AXES = {
    "grid_h": {"type": "int", "default": "3 on canonical draws; 1..15 on width witnesses", "valid": "1..15"},
    "grid_w": {"type": "int", "default": "3 on canonical draws; 2|4|5|6|7 on width witnesses", "valid": "2..7"},
    "palette_size": {"type": "int", "default": "2..3, difficulty-weighted and capacity-aware", "valid": "2..3"},
    "palette": {"type": "colors[N]", "default": "distinct subset of 5/7/8", "valid": "2 or 3 distinct literal integer colors 0..9",
                "probe": "diagnostic", "doc": "Variable-length list/tuple; inferred size unless explicitly supplied. Tested by task-local palette regressions."},
    "texture": {"type": "enum", "default": "noise-biased helpful prior", "valid": "|".join(HELPFUL_TEXTURES),
                "doc": "Starting texture, not an exact final shape after constraints."},
    "bg_density": {"type": "float", "default": "0.0", "valid": "0..0.95",
                   "doc": "Per-cell replacement probability for palette[0] before exact constraints."},
    "noise_overlay": {"type": "float", "default": "0.0", "valid": "0..0.3",
                      "doc": "Per-cell random recolor probability before exact constraints."},
    "lr_asymmetric": {"type": "bool", "default": "true (fixed compatibility argument)", "valid": "true",
                      "probe": "diagnostic", "doc": "Only literal True or None accepted; use make_degenerate for symmetric negative fixtures."},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = [
    {"grid_h": 1, "grid_w": 2, "palette_size": 3},
]
EXAMPLES_NEEDED = 3
LESSON_SCHEDULE_PERIOD = 4
SCHEDULE_PROFILES = ("canonical", "width_witness_even", "canonical", "width_witness_odd")
MIN_STRICT_FRAC = 0.40


def _identity(seed, sample_index, difficulty):
    if type(seed) is not int:
        raise ValueError("seed must be a literal integer, not bool/float/string")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative literal integer")
    if difficulty is not None and difficulty not in ("easy", "medium", "hard"):
        raise ValueError("difficulty must be None, easy, medium or hard")


def _integer(value, name, lo, hi):
    if type(value) is not int or not lo <= value <= hi:
        raise ValueError(f"{name} must be a literal integer in {lo}..{hi}")
    return value


def _probability(value, name, hi):
    if type(value) not in (int, float) or not math.isfinite(value) or not 0 <= value <= hi:
        raise ValueError(f"{name} must be a finite number in 0..{hi}")
    return float(value)


def _palette(value):
    if not isinstance(value, (list, tuple)) or not 2 <= len(value) <= 3:
        raise ValueError("palette must be a list/tuple of 2 or 3 distinct integer colors")
    if any(type(v) is not int or not 0 <= v <= 9 for v in value) or len(set(value)) != len(value):
        raise ValueError("palette must contain distinct literal integer ARC colors 0..9")
    return tuple(value)


def _conflict(message, *axes):
    error = ValueError(message)
    error.incompatible_axes = axes
    raise error


def _axis(ctx, name, ordinary_choices, all_choices):
    choices = all_choices if name in ctx.overrides else ordinary_choices
    return ctx.draw_choice(name, choices)


def schedule_profile(seed, sample_index, difficulty=None):
    _identity(seed, sample_index, difficulty)
    return SCHEDULE_PROFILES[sample_index % LESSON_SCHEDULE_PERIOD]


def _is_lr_sym(grid):
    return all(row == row[::-1] for row in grid)


def _enforce_exact_constraints(grid, palette, rng):
    """Protect a randomly located unequal mirror pair, then realize all colors."""
    h, w = len(grid), len(grid[0])
    row = rng.randrange(h)
    left = rng.randrange(w // 2)
    right = w - 1 - left
    a, b = rng.sample(palette, 2)
    grid[row][left], grid[row][right] = a, b
    protected = {(row, left), (row, right)}
    present = {v for values in grid for v in values}
    for color in palette:
        if color not in present:
            # With at most three colors, the protected pair retains the other
            # two. A third requested color has a free cell iff the call is feasible.
            slots = [(r, c) for r in range(h) for c in range(w) if (r, c) not in protected]
            r, c = rng.choice(slots)
            grid[r][c] = color
            present.add(color)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _identity(seed, sample_index, difficulty)
    retired = set(overrides) & {"left_edge_kind", "row_pattern"}
    if retired:
        raise ValueError(f"retired controls {sorted(retired)} had unreliable postconditions; use texture priors or make_degenerate")
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    options = {key: value for key, value in overrides.items() if value is not None}
    for name, lo, hi in (("grid_h", 1, 15), ("grid_w", 2, 7), ("palette_size", 2, 3)):
        if name in options:
            _integer(options[name], name, lo, hi)
    if "lr_asymmetric" in options and options["lr_asymmetric"] is not True:
        raise ValueError("ordinary inputs are LR-asymmetric; use make_degenerate for symmetric negative fixtures")
    if options.get("texture") in NEGATIVE_FIXTURES:
        raise ValueError("negative texture moved to make_degenerate(name, seed=..., sample_index=...)")
    if "texture" in options and options["texture"] not in HELPFUL_TEXTURES:
        raise ValueError("texture must be one of the documented helpful priors")
    density = _probability(options.get("bg_density", 0.0), "bg_density", 0.95)
    noise = _probability(options.get("noise_overlay", 0.0), "noise_overlay", 0.3)
    palette = _palette(options["palette"]) if "palette" in options else None
    if palette is not None:
        if "palette_size" in options and options["palette_size"] != len(palette):
            _conflict("palette length must equal palette_size", "palette", "palette_size")
        options["palette_size"] = len(palette)
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=options)
    profile = schedule_profile(seed, sample_index, difficulty)
    core = profile == "canonical"
    band = difficulty or "medium"
    broad_heights = tuple(range(1, 16)) + ((2, 3, 4) * 4 if band == "easy" else
                     (3, 4, 5, 6) * 4 if band == "medium" else (5, 7, 9, 12, 15) * 4)
    required_count = options.get("palette_size", 2)
    height_choices = (3,) if core else broad_heights
    # Adjacent width witnesses use disjoint shapes. The production sampler's
    # duplicate filter therefore cannot erase the second witness in a lesson.
    width_choices = (3,) if core else ((2, 4, 6) if profile == "width_witness_even" else (5, 7))
    # A caller fixes only supplied axes. Condition free dimensions on palette
    # capacity; a random unbound choice must never create a false incompatibility.
    available_width = options.get("grid_w", max(width_choices))
    height_choices = tuple(value for value in height_choices
                           if value * available_width >= required_count)
    h = _axis(ctx, "grid_h", height_choices, tuple(range(1, 16)))
    width_choices = tuple(value for value in width_choices if h * value >= required_count)
    w = _axis(ctx, "grid_w", width_choices, tuple(range(2, 8)))
    if required_count > h * w:
        count_axis = "palette" if palette is not None and overrides.get("palette_size") is None else "palette_size"
        _conflict("grid_h * grid_w cannot fit the requested distinct colors", "grid_h", "grid_w", count_axis)
    choices = (2, 2, 2, 3) if band == "easy" else ((2, 3, 3, 3) if band == "medium" else (2, 3, 3, 3, 3, 3))
    count = _axis(ctx, "palette_size", tuple(n for n in choices if n <= h*w), (2, 3))
    if palette is None:
        palette = tuple(ctx.draw_rng("palette_order").sample((5, 7, 8), count))
    texture_choices = HELPFUL_TEXTURES + ("noise",) * (12 if band == "easy" else 24)
    texture = ctx.draw_choice("texture", texture_choices)
    grid = fill_texture(texture, h, w, palette, ctx.draw_rng("cells"))
    if density:
        grid = apply_bg_density(grid, palette, ctx.draw_rng("background_density"), density)
    if noise:
        grid = apply_noise_overlay(grid, palette, ctx.draw_rng("noise_overlay_cells"), noise)
    _enforce_exact_constraints(grid, palette, ctx.draw_rng("exact_constraints"))
    return grid


def observe_overrides(grid):
    return {"grid_h": len(grid), "grid_w": len(grid[0]),
            "palette_size": len({v for row in grid for v in row})}


def self_check(grid, *, difficulty=None, meta=None):
    if not isinstance(grid, (list, tuple)) or not grid or not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected a nonempty rectangular grid"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be literal integer ARC colors 0..9"]
    errors = []
    if not 1 <= len(grid) <= 15 or not 2 <= width <= 7:
        errors.append("ordinary dimensions must be height 1..15 and width 2..7")
    if not 2 <= len({v for row in grid for v in row}) <= 3:
        errors.append("ordinary inputs must realize exactly two or three colors")
    if _is_lr_sym(grid):
        errors.append("LR-symmetric input hides the mirror phases; use a negative fixture")
    return errors


def strict_canonical_like(grid):
    errors = self_check(grid)
    if errors:
        return errors
    if (len(grid), len(grid[0])) != (3, 3):
        errors.append("outside canonical 3x3 profile")
    if not {v for row in grid for v in row} <= {5, 7, 8}:
        errors.append("outside canonical color palette 5/7/8")
    return errors


def make_degenerate(name, *, seed=0, sample_index=0):
    """Deliberate negative fixtures; never sampled by generate()."""
    _identity(seed, sample_index, None)
    if name not in NEGATIVE_FIXTURES:
        raise ValueError("unknown negative fixture")
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=None, overrides={})
    rng = ctx.draw_rng("negative_fixture")
    palette = rng.sample((5, 7, 8), 2)
    if name == "single_col":
        return [[palette[r % 2]] for r in range(3)]
    grid = full_grid(3, 3, palette[0])
    if name == "lr_symmetric":
        for row in grid:
            row[1] = palette[1]
    return grid


# Finite rivals are diagnostics, never sources of authoritative labels.
def _four_copies(grid):
    return [list(row) * 4 for row in grid]


def _input_first(grid):
    return [(list(row) + list(row)[::-1]) * 2 for row in grid]


def _vertical_mirror(grid):
    return [(list(flipped) + list(original)) * 2 for flipped, original in zip(grid[::-1], grid)]


def _fixed_3x3_canvas(grid):
    small = [[grid[r][c] if r < len(grid) and c < len(grid[0]) else 0
              for c in range(3)] for r in range(3)]
    return [(row[::-1] + row) * 2 for row in small]


def _mirror_visible(grid):
    return not _is_lr_sym(grid)


def _width_generalization(grid):
    return len(grid[0]) != 3


SEMANTIC_WITNESSES = {"mirror_visible": _mirror_visible, "width_generalization": _width_generalization}
SEMANTIC_RIVALS = {"four_copies": _four_copies, "input_first": _input_first,
                   "vertical_mirror": _vertical_mirror, "fixed_3x3_canvas": _fixed_3x3_canvas}
WITNESS_RIVALS = {"mirror_visible": ["four_copies", "input_first"],
                 "width_generalization": ["fixed_3x3_canvas"]}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {"fixed_3x3_canvas": _fixed_3x3_canvas}
