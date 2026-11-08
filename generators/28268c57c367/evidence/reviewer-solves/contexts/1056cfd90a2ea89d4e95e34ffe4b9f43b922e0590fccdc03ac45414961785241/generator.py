"""Inputs for row projection to a full-height gray wall.

The unchanged Racket authority processes ORIGINAL sources left-to-right and
fills only zero cells. Consequently, the leftmost non-{0,5} source in a row
owns every originally blank cell to its right before the wall. Other sources,
isolated 5s and right-side distractors are retained. Gray cells are neither
sources nor local ray terminators. Generation never computes output labels.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx, stable_rng
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "28268c57c367"
TASK_ID = GENERATOR_ID
RULE_HASH = "b4fa0726be56"
VERSION = "2.1.0"
SUMMARY = (
    "Project nonzero, non-5 sources rightward to the unique full-height 5 wall. "
    "Only zeros are filled; the first source in each row wins. Off-wall 5s "
    "and right-side objects remain unchanged. Alternate canonical-shaped "
    "examples with multi-source, gray-obstacle counterexamples."
)
INVARIANTS = [
    "rectangular 5..14 by 7..18 grid of integer colors 0..9",
    "one full-height color-5 wall, at column 5..w-2",
    "1..6 left source cells use exactly 1..6 distinct colors excluding 0 and 5",
    "0..3 off-wall gray cells lie left of the wall; 0..3 colored distractors lie right",
    "unrestricted three-demo lessons contain a multi-rival teaching witness",
]
AXES = {
    "grid_h": {"type": "int", "default": "canonical or difficulty-weighted", "valid": "5..14"},
    "grid_w": {"type": "int", "default": "canonical or difficulty-weighted", "valid": "7..18"},
    "wall_col": {"type": "int", "default": "canonical w-3 or varied", "valid": "5..16"},
    "n_cells": {"type": "int", "default": "core 2..3; rich 2..6", "valid": "1..6"},
    "n_distinct_colors": {"type": "int", "default": "core n_cells; rich 2..n_cells", "valid": "1..6"},
    "n_gray": {"type": "int", "default": "core 0..1; rich 2..3", "valid": "0..3"},
    "n_right": {"type": "int", "default": "core 0; rich 0..3", "valid": "0..3"},
}
# Exact incompatible VALUE pairs, not a blanket exemption for whole axes.
INCOMPATIBLE_OVERRIDE_COMBINATIONS = [
    {"n_cells": n, "n_distinct_colors": k}
    for n in range(1, 7) for k in range(n + 1, 7)
] + [
    {"grid_w": w, "wall_col": c}
    for w in range(7, 19) for c in range(5, 17) if c > w - 2
]
_BOUNDS = {name: tuple(map(int, spec["valid"].split(".."))) for name, spec in AXES.items()}
_SOURCE_COLORS = (1, 2, 3, 4, 6, 7, 8, 9)
EXAMPLES_NEEDED = 3
SCHEDULE_PROFILES = ("core", "rich")


def schedule_profile(seed, sample_index, difficulty=None):
    """Both residues are covered by every consecutive pair, for every seed."""
    phase = stable_rng(seed, f"{TASK_ID}:schedule", VERSION).randrange(2)
    return SCHEDULE_PROFILES[(phase + sample_index) % 2]


def _axis(ctx, name, defaults):
    # Pins use the full documented interval, independent of difficulty/profile.
    # Defaults remain truthful keyed draws rather than values overwritten later.
    if ctx.overrides.get(name) is not None:
        return ctx.draw_int_strict(name, *_BOUNDS[name])
    return ctx.draw_choice(name, tuple(defaults))


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown or retired override axes: {sorted(unknown)}")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be easy, medium, hard or None")
    for name, value in overrides.items():
        if value is None:
            continue
        lo, hi = _BOUNDS[name]
        if type(value) is not int or not lo <= value <= hi:
            raise ValueError(f"{name} must be an integer in {lo}..{hi}")
    if (overrides.get("grid_w") is not None and overrides.get("wall_col") is not None
            and overrides["wall_col"] > overrides["grid_w"] - 2):
        raise ValueError("wall_col must be <= grid_w - 2")
    if (overrides.get("n_cells") is not None and overrides.get("n_distinct_colors") is not None
            and overrides["n_distinct_colors"] > overrides["n_cells"]):
        raise ValueError("n_distinct_colors must be <= n_cells")
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    rich = schedule_profile(seed, sample_index, difficulty) == "rich"
    heights = range(5, 10) if difficulty == "easy" else (
        range(9, 15) if difficulty == "hard" else range(5, 15))
    core_heights = ((6, 7, 8, 9, 6, 7) if difficulty == "easy" else
                    ((6, 7, 8, 9, 8, 9) if difficulty == "hard" else (6, 7, 8, 9)))
    h = _axis(ctx, "grid_h", heights if rich else core_heights)
    min_width = max(7, (overrides.get("wall_col") or 5) + 2)
    widths = range(min_width, 19) if rich else (max(min_width, h + 3),)
    w = _axis(ctx, "grid_w", widths)
    wall = _axis(ctx, "wall_col", range(5, w - 1) if rich else (max(5, w - 3),))
    min_cells = max(1, overrides.get("n_distinct_colors") or 1)
    n = _axis(ctx, "n_cells", range(max(2, min_cells), 7) if rich else (max(2, min_cells), max(3, min_cells)))
    n_colors = _axis(ctx, "n_distinct_colors", range(min(2, n), n + 1) if rich else (n,))
    n_gray = _axis(ctx, "n_gray", (2, 3) if rich else (0, 0, 0, 1))
    n_right = _axis(ctx, "n_right", (0, 1, 2, 3) if rich else (0,))
    palette = ctx.draw_rng("source_palette").sample(_SOURCE_COLORS, n_colors)
    g = full_grid(h, w, 0)
    for row in g:
        row[wall] = 5
    rng = ctx.draw_rng("layout")
    source_positions, gray_positions = [], []
    reserved_blanks = set()
    sterile_row = None
    if rich and n >= 2:
        main_row, sterile_row = rng.sample(range(h), 2)
        first = rng.randrange(wall - 3)
        second = rng.randrange(first + 2, wall - 1)
        source_positions = [(main_row, first), (main_row, second)]
        # A zero after the second source distinguishes first-source ownership.
        reserved_blanks.add((main_row, rng.randrange(second + 1, wall)))
        if n_gray:
            gray_positions.append((main_row, rng.randrange(first + 1, second)))
        if n_gray >= 2:
            col = rng.randrange(wall - 1)
            gray_positions.append((sterile_row, col))
            reserved_blanks.add((sterile_row, col + 1))
        candidates = [(r, c) for r in range(h) for c in range(wall)
                      if r not in (main_row, sterile_row)]
        source_positions.extend(rng.sample(candidates, n - 2))
    else:
        # Distinct source rows whenever possible, including all natural core draws.
        if n <= h:
            source_positions = [(r, rng.randrange(wall - 1)) for r in rng.sample(range(h), n)]
        else:
            source_positions = rng.sample([(r, c) for r in range(h) for c in range(wall - 1)], n)
    # The first two rich sources have distinct colors whenever the palette allows.
    colors = palette + [rng.choice(palette) for _ in range(n - n_colors)]
    for (r, c), color in zip(source_positions, colors):
        g[r][c] = color
    occupied = set(source_positions) | set(gray_positions) | reserved_blanks
    candidates = [(r, c) for r in range(h) for c in range(wall) if (r, c) not in occupied]
    # Natural core gray cells are isolated from sources, like the canonical test.
    if not rich:
        unused_rows = set(range(h)) - {r for r, _ in source_positions}
        preferred = [p for p in candidates if p[0] in unused_rows and p[1] < wall - 1]
        if len(preferred) >= n_gray:
            candidates = preferred
    gray_positions.extend(rng.sample(candidates, n_gray - len(gray_positions)))
    for r, c in gray_positions:
        g[r][c] = 5
    for r, c in rng.sample([(r, c) for r in range(h) for c in range(wall + 1, w)], n_right):
        g[r][c] = rng.choice(palette)
    return g


def _wall(grid):
    return next(c for c in range(len(grid[0])) if all(row[c] == 5 for row in grid))


def self_check(grid, *, difficulty=None, meta=None):
    """Validate the supported rule domain; reject malformed input without raising."""
    if not isinstance(grid, list) or not grid or not all(isinstance(row, list) and row for row in grid):
        return ["expected a nonempty list of nonempty rows"]
    h, w = len(grid), len(grid[0])
    if not 1 <= h <= 30 or not 1 <= w <= 30 or any(len(row) != w for row in grid):
        return ["expected a rectangular grid with sides 1..30"]
    if any(type(v) is not int or not 0 <= v <= 9 for row in grid for v in row):
        return ["colors must be integers 0..9, excluding bool"]
    walls = [c for c in range(w) if all(row[c] == 5 for row in grid)]
    if len(walls) != 1:
        return [f"expected exactly one full-height color-5 wall, found {len(walls)}"]
    wall = walls[0]
    if not any(v not in (0, 5) for row in grid for v in row[:wall]):
        return ["expected at least one non-{0,5} source left of the wall"]
    return []


def observe_overrides(grid):
    wall = _wall(grid)
    left = [v for row in grid for v in row[:wall] if v not in (0, 5)]
    return {
        "grid_h": len(grid), "grid_w": len(grid[0]), "wall_col": wall,
        "n_cells": len(left), "n_distinct_colors": len(set(left)),
        "n_gray": sum(v == 5 for row in grid for v in row[:wall]),
        "n_right": sum(v not in (0, 5) for row in grid for v in row[wall + 1:]),
    }


def strict_canonical_like(grid):
    errors = self_check(grid)
    if errors:
        return errors
    h, w, wall = len(grid), len(grid[0]), _wall(grid)
    sources = [(r, c, v) for r, row in enumerate(grid) for c, v in enumerate(row[:wall]) if v not in (0, 5)]
    if not (6 <= h <= 9 and w == h + 3 and wall == w - 3):
        errors.append("outside canonical size/wall profiles")
    if not (2 <= len(sources) <= 3 and len({r for r, c, v in sources}) == len(sources)
            and len({v for r, c, v in sources}) == len(sources)):
        errors.append("canonical core needs 2..3 distinctly colored sources on distinct rows")
    if any(c >= wall - 1 for r, c, v in sources):
        errors.append("canonical source must leave a blank ray gap")
    if any(v for row in grid for v in row[wall + 1:]):
        errors.append("canonical right half is empty")
    gray = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row[:wall]) if v == 5]
    if len(gray) > 1 or any(r in {r for r, c, v in sources} for r, c in gray):
        errors.append("canonical off-wall gray is isolated on a non-source row")
    return errors


def _predict_rival(grid, mode):
    """Diagnostic wrong rules only; Racket remains the output-label authority."""
    wall = _wall(grid)
    out = [row[:] for row in grid]
    for r, row in enumerate(grid):
        if mode == "nearest_source":
            color = None
            for c in range(wall):
                if row[c] not in (0, 5):
                    color = row[c]
                elif row[c] == 0 and color is not None:
                    out[r][c] = color
            continue
        for c in range(wall):
            v = row[c]
            if v == 0 or (v == 5 and mode != "gray_sources"):
                continue
            for cc in range(c + 1, wall):
                if mode == "stop_at_gray" and row[cc] == 5:
                    break
                if mode == "overwrite_obstacles" or out[r][cc] == 0:
                    out[r][cc] = v
    return out


def _gray_sources(grid):
    return _predict_rival(grid, "gray_sources")


def _nearest_source(grid):
    return _predict_rival(grid, "nearest_source")


def _stop_at_gray(grid):
    return _predict_rival(grid, "stop_at_gray")


def _overwrite_obstacles(grid):
    return _predict_rival(grid, "overwrite_obstacles")


def _gray_not_source_witness(grid):
    wall = _wall(grid)
    return any(not any(v not in (0, 5) for v in row[:wall])
               and any(row[c] == 5 and 0 in row[c + 1:wall] for c in range(wall)) for row in grid)


def _shared_ray_witness(grid):
    wall = _wall(grid)
    for row in grid:
        sources = [(c, v) for c, v in enumerate(row[:wall]) if v not in (0, 5)]
        if len(sources) < 2:
            continue
        first, color = sources[0]
        for c, other in sources[1:]:
            # A preserved gray obstacle between distinct sources plus a trailing
            # zero jointly separates all three canonical-fitting rivals.
            if other != color and 5 in row[first + 1:c] and 0 in row[c + 1:wall]:
                return True
    return False


SEMANTIC_WITNESSES = {"gray_is_not_a_source": _gray_not_source_witness,
                      "shared_ray_preserves_and_crosses_obstacles": _shared_ray_witness}
SEMANTIC_RIVALS = {"gray_sources": _gray_sources, "nearest_source": _nearest_source,
                   "stop_at_gray": _stop_at_gray, "overwrite_obstacles": _overwrite_obstacles}
WITNESS_RIVALS = {"gray_is_not_a_source": ["gray_sources"],
                  "shared_ray_preserves_and_crosses_obstacles":
                  ["nearest_source", "stop_at_gray", "overwrite_obstacles"]}
# Gray-as-source fits the three demonstrations but NOT the labeled canonical
# test; do not misrepresent it as fitting every canonical pair.
CANONICAL_SHORTCUTS = {"nearest_source": _nearest_source, "stop_at_gray": _stop_at_gray,
                       "overwrite_obstacles": _overwrite_obstacles}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
