"""Generator for arc_puzzle_bank_21_set9_e:easy_i01.

Canonical rule: replace every horizontal same-color run by its endpoints.
The ordinary sampler constructs the requested number of separated runs exactly;
degenerate textures are explicit probes and never leak into ordinary draws.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "8a761b80b11b"
VERSION = "2.1.0"
TASK_ID = "8a761b80b11b"

SUMMARY = (
    "0-background grid with an exact requested count of horizontal same-color "
    "runs. Each ordinary run is a contiguous nonzero segment in one row, has "
    "length 2-5, and no row contains two abutting runs. At least one run has "
    "length at least 3, so endpoint reduction is observable. The canonical rule "
    "creates a fresh empty grid and paints only each run's first and last cells "
    "in its original color; all run interiors become 0. Explicit degenerate "
    "textures (blank, vertical-only, singleton-only) are dimension-honoring "
    "negative probes rather than ordinary samples."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "ordinary nonzero cells form horizontal same-color runs",
    "ordinary generation places exactly n_runs",
    "at least one ordinary run has length >=3",
]

PALETTES = {
    "default": (1, 2, 3, 4, 5, 6, 7, 8, 9),
    "warm": (2, 4, 6, 7),
    "cool": (1, 5, 8, 9),
    "varied": (1, 2, 4, 5, 6, 8, 9),
}
PALETTE_KINDS = tuple(PALETTES)
DEGENERATE_TEXTURES = ("no_runs", "vertical_only", "all_singletons")
HELPFUL_TEXTURES = PALETTE_KINDS
_ALLOWED_OVERRIDES = {"grid_h", "grid_w", "n_runs", "palette_kind", "texture"}

AXES = {
    "grid_h": {"type": "int", "default": "difficulty-aware 5..7", "valid": "3..12"},
    "grid_w": {"type": "int", "default": "difficulty-aware 8..11", "valid": "5..18"},
    "palette_kind": {"type": "str", "default": "rng helpful", "valid": "|".join(PALETTE_KINDS)},
    "n_runs": {"type": "int", "default": "difficulty-aware 3..5", "valid": "1..min(12,grid_h)"},
    "texture": {"type": "str", "default": "ordinary", "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _row_runs(row):
    runs = []
    c = 0
    while c < len(row):
        if row[c] == 0:
            c += 1
            continue
        start, color = c, row[c]
        while c < len(row) and row[c] == color:
            c += 1
        runs.append((start, c - 1, color))
    return runs


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify an ordinary sample's horizontal runs and observable reduction."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if h > 30 or w > 30 or any(len(row) != w for row in grid):
        return ["grid must be rectangular and at most 30x30"]
    errs = []
    has_long = False
    for r, row in enumerate(grid):
        c = 0
        while c < w:
            value = row[c]
            if value == 0:
                c += 1
                continue
            start = c
            while c < w and row[c] == value:
                c += 1
            if c - start >= 3:
                has_long = True
            if c < w and row[c] != 0:
                errs.append(f"row {r} col {c}: adjacent non-bg color change without gap")
    if not has_long:
        errs.append("no horizontal run of length >=3")
    return errs


def _dimension(ctx, label, *, difficulty, easy, medium, hard, full):
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_int_strict(label, *full)
    bounds = easy if difficulty == "easy" else hard if difficulty == "hard" else medium
    return ctx.draw_int_strict(label, *bounds)


def _draw_from_degenerate(name, height, width):
    grid = full_grid(height, width, 0)
    if name == "no_runs":
        return grid
    if name == "vertical_only":
        columns = sorted({1, max(1, width - 2)})
        colors = (4, 6)
        for index, column in enumerate(columns):
            start = index % 2
            stop = min(height, start + max(2, height - 2))
            for row in range(start, stop):
                grid[row][column] = colors[index]
        return grid
    if name == "all_singletons":
        colors = (4, 6, 7, 2, 8)
        positions = []
        for row in range(0, height, 2):
            column = (2 * row + 1) % width
            if positions and abs(column - positions[-1][1]) <= 1 and row == positions[-1][0]:
                column = (column + 2) % width
            positions.append((row, column))
            if len(positions) == len(colors):
                break
        for (row, column), color in zip(positions, colors):
            grid[row][column] = color
        return grid
    raise ValueError(f"unknown degenerate texture: {name}")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be easy, medium, hard, or None")
    unknown = sorted(set(overrides) - _ALLOWED_OVERRIDES)
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")

    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    height = _dimension(ctx, "grid_h", difficulty=difficulty,
                        easy=(5, 5), medium=(5, 7), hard=(6, 7), full=(3, 12))
    width = _dimension(ctx, "grid_w", difficulty=difficulty,
                       easy=(8, 9), medium=(8, 11), hard=(10, 11), full=(5, 18))

    texture = overrides.get("texture", "ordinary")
    if type(texture) is not str or texture not in HELPFUL_TEXTURES + DEGENERATE_TEXTURES + ("ordinary",):
        raise ValueError("texture must be ordinary, a palette alias, or a declared degenerate")
    explicit_palette = overrides.get("palette_kind")
    if texture in DEGENERATE_TEXTURES:
        if explicit_palette is not None or overrides.get("n_runs") is not None:
            raise ValueError("degenerate texture conflicts with palette_kind or n_runs")
        return _draw_from_degenerate(texture, height, width)
    if texture in PALETTE_KINDS and explicit_palette is not None and texture != explicit_palette:
        raise ValueError("texture alias and palette_kind conflict")

    if texture in PALETTE_KINDS:
        palette_kind = texture
    else:
        palette_kind = ctx.draw_choice("palette_kind", PALETTE_KINDS)
    palette = PALETTES[palette_kind]

    max_runs = min(12, height)
    if "n_runs" in overrides and overrides["n_runs"] is not None:
        target = ctx.draw_int_strict("n_runs", 1, max_runs)
    elif difficulty == "easy":
        target = ctx.draw_int_strict("n_runs", min(3, max_runs), min(3, max_runs))
    elif difficulty == "hard":
        target = ctx.draw_int_strict("n_runs", min(4, max_runs), min(5, max_runs))
    else:
        target = ctx.draw_int_strict("n_runs", min(3, max_runs), min(5, max_runs))

    rng = ctx.draw_rng("layout")
    rows = sorted(rng.sample(range(height), target))
    long_row = rng.choice(rows)
    grid = full_grid(height, width, 0)
    for row in rows:
        minimum = 3 if row == long_row else 2
        length = rng.randint(minimum, min(5, width))
        start = rng.randint(0, width - length)
        color = rng.choice(palette)
        for column in range(start, start + length):
            grid[row][column] = color
    return grid
