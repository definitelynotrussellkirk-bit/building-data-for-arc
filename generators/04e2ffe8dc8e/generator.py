"""Generator for arc_puzzle_bank_21_set2:S2_E2.

Rule: the uniquely smallest green component is recolored magenta.

Combinatorial axes (8): grid_h, grid_w, palette_kind, small_size, n_large,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_components, tied_smallest, all_same_size.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.place import place_no_overlap

GENERATOR_ID = "04e2ffe8dc8e"
VERSION = "1.3.0"
TASK_ID = "04e2ffe8dc8e"
RULE_HASH = "c67640298f12"

SUMMARY = (
    "The uniquely smallest GREEN component is recolored magenta; "
    "decoy boards also carry an even-smaller NON-green object the "
    "rule must ignore (only greens compete)."
)

# Rivals: 'recolor the smallest object of any color' refuted by decoy
# boards where a tinier non-green object stays. 'recolor all small
# greens' refuted by the unique-min guarantee. 3 demos incl. >=1
# decoy board.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "exactly one green component has the smallest size among GREENS",
    "decoy boards: a smaller non-green object is ignored by the rule",
]

DEGENERATE_TEXTURES = ("tied_smallest", "all_same_size")
HELPFUL_TEXTURES = ("plain", "decoy")
_VALID_DIFFICULTIES = (None, "easy", "medium", "hard")

AXES = {
    "grid_h":     {"type": "int", "default": "rng 9..11", "valid": "6..14"},
    "grid_w":     {"type": "int", "default": "rng 9..12", "valid": "6..16"},
    "small_size": {"type": "choice", "default": "rng 1|2", "valid": "1|2"},
    "n_large":    {"type": "int", "default": "rng 2..3 (hard 3..4)",
                   "valid": "1..4"},
    "texture":    {"type": "str", "default": "rng (decoy ~30%)",
                   "valid": "plain|decoy|tied_smallest|all_same_size",
                   "doc": "decoy adds a 1-cell non-green object smaller "
                          "than the smallest green."},
}

_SMALL = {
    1: [(0, 0)],
    2: [(0, 0), (0, 1)],
}

_LARGE = [
    [(0, 0), (0, 1), (0, 2)],
    [(0, 0), (0, 1), (1, 1)],
    [(0, 0), (0, 1), (1, 0), (1, 1)],
    [(0, 0), (1, 0), (2, 0), (2, 1)],
]


def _draw_int(ctx, overrides, name, full_bounds, default_bounds):
    bounds = full_bounds if overrides.get(name) is not None else default_bounds
    return ctx.draw_int(name, *bounds)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in _VALID_DIFFICULTIES:
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unsupported override(s): {sorted(unknown)}")
    texture = overrides.get("texture")
    if texture is not None and texture not in HELPFUL_TEXTURES + DEGENERATE_TEXTURES:
        raise ValueError(
            f"unknown texture {texture!r}; valid values are "
            f"{HELPFUL_TEXTURES + DEGENERATE_TEXTURES}"
        )
    if texture == "decoy" and overrides.get("small_size") == 1:
        raise ValueError("decoy is impossible with small_size=1; no smaller component exists")
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if texture in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(texture, ctx)
    if texture is None:
        # Every three-sample window carries one real decoy, so the documented
        # any-color shortcut cannot survive the ordinary teaching stream.
        scheduled = "decoy" if (int(seed) + int(sample_index)) % 3 == 2 else "plain"
        texture = ctx.draw_choice("texture", (scheduled,))
    else:
        texture = ctx.draw_choice("texture", HELPFUL_TEXTURES)
    if difficulty == "easy":
        defaults = ((9, 10), (9, 10), (2, 2))
    elif difficulty == "hard":
        defaults = ((10, 11), (11, 12), (3, 4))
    else:
        defaults = ((9, 11), (9, 12), (2, 3))
    h = _draw_int(ctx, overrides, "grid_h", (6, 14), defaults[0])
    w = _draw_int(ctx, overrides, "grid_w", (6, 16), defaults[1])
    n_large = _draw_int(ctx, overrides, "n_large", (1, 4), defaults[2])
    small_size = ctx.draw_choice("small_size", [2] if texture == "decoy" else [1, 2])
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    if place_no_overlap(rng, g, _SMALL[small_size], 3, padding=1, max_tries=400) is None:
        raise ValueError("could not place smallest component")
    for _ in range(n_large):
        if place_no_overlap(rng, g, rng.choice(_LARGE), 3, padding=1, max_tries=400) is None:
            raise ValueError("could not place requested larger green component")
    if texture == "decoy":
        # a 1-cell NON-green object, smaller than the smallest green —
        # the rule must ignore it (only greens compete)
        placed = place_no_overlap(
            rng,
            g,
            [(0, 0)],
            rng.choice([1, 2, 4, 5, 7, 8, 9]),
            padding=1,
            max_tries=200,
        )
        if placed is None:
            raise ValueError("could not place required non-green decoy")
    return g


def _draw_from_degenerate(name, ctx):
    """Rule-hiding inputs — rng-varied, rule-safe (>=1 green always;
    no_components was dropped — an empty board crashes the rule at
    (first (sort '() ...))).

    tied_smallest — two greens share the min: the cell< tie-break
                    silently picks the topmost-leftmost.
    all_same_size — every green ties.
    """
    rng = ctx.draw_rng("degenerate_layout")
    h = ctx.draw_int("grid_h", 9, 11)
    w = ctx.draw_int("grid_w", 9, 12)
    g = full_grid(h, w, 0)
    if name == "tied_smallest":
        place_no_overlap(rng, g, [(0, 0)], 3, padding=1, max_tries=200)
        place_no_overlap(rng, g, [(0, 0)], 3, padding=1, max_tries=200)
        place_no_overlap(rng, g, _LARGE[rng.randrange(len(_LARGE))], 3,
                         padding=1, max_tries=200)
        return g
    # all_same_size
    for _ in range(3):
        place_no_overlap(rng, g, [(0, 0), (0, 1)], 3, padding=1, max_tries=200)
    return g

def _components_of_color(grid, color):
    h, w = len(grid), len(grid[0])
    seen = set(); comps = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != color or (r, c) in seen:
                continue
            stack = [(r, c)]; seen.add((r, c)); cells = []
            while stack:
                rr, cc = stack.pop(); cells.append((rr, cc))
                for nr, nc in ((rr - 1, cc), (rr + 1, cc), (rr, cc - 1), (rr, cc + 1)):
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and grid[nr][nc] == color:
                        seen.add((nr, nc)); stack.append((nr, nc))
            comps.append(cells)
    return comps


def _rule_mirror(grid):
    """Input-pure Python mirror of the canonical Racket transformation."""
    greens = _components_of_color(grid, 3)
    if not greens:
        raise ValueError("canonical rule requires at least one green component")
    target = min(greens, key=lambda cells: (len(cells), min(cells)))
    output = [list(row) for row in grid]
    for row, col in target:
        output[row][col] = 6
    return output


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty
    errors = []
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be non-empty and rectangular"]
    if any(type(value) is not int or value < 0 or value > 9 for row in grid for value in row):
        errors.append("color outside 0..9")
        return errors

    greens = _components_of_color(grid, 3)
    sizes = sorted(len(component) for component in greens)
    if len(greens) < 2:
        errors.append(
            f"expected smallest green plus at least one larger green, got {len(greens)}"
        )
    if not sizes or sizes.count(sizes[0]) != 1:
        errors.append("green components do not have a unique smallest size")
    elif any(size <= sizes[0] for size in sizes[1:]):
        errors.append("every non-target green component must be larger than the target")

    if isinstance(meta, dict):
        requested = meta.get("overrides") if isinstance(meta.get("overrides"), dict) else meta
        try:
            observed = observe_overrides(grid)
        except ValueError:
            observed = {}
        for axis, expected in requested.items():
            if axis in AXES and observed.get(axis) != expected:
                errors.append(
                    f"meta {axis} requested {expected!r}, observed {observed.get(axis)!r}"
                )
    return errors


def observe_overrides(grid) -> dict[str, int | str]:
    """Recover every public axis from a valid generated scene."""
    errors = self_check(grid)
    if errors:
        raise ValueError("cannot observe overrides: " + "; ".join(errors))
    greens = _components_of_color(grid, 3)
    non_green_foreground = [
        value
        for row in grid
        for value in row
        if value not in (0, 3)
    ]
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "small_size": min(len(component) for component in greens),
        "n_large": len(greens) - 1,
        "texture": "decoy" if non_green_foreground else "plain",
    }
