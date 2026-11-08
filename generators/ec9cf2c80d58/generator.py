"""Colored bands with holes, bound to the unchanged canonical Racket rule.

Each original hole selects its first nonzero neighbor (up, down, left, right).
Count that color OR ZERO in its complete row and column. If row >= column,
erase matching column cells; otherwise erase matching row cells. All decisions
read the ORIGINAL input. Only Racket supplies production labels; the Python
model below is for source-bound authoring checks and rival comparisons.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "ec9cf2c80d58"
TASK_ID = GENERATOR_ID
VERSION = "4.1.0"
RULE_HASH = "899eb4e6a25d"
SUMMARY = (
    "Two to five distinct color bands with zero holes. Each hole selects its "
    "first nonzero neighbor in up/down/left/right order and compares original "
    "row and column counts of that color or zero. Row >= column clears matching "
    "column cells; otherwise matching row cells. Includes inactive bands, edge "
    "holes, independent canvas aspect ratios, and varied multi-band "
    "extent/tie witnesses that defeat the retained profile-gated shortcut."
)
INVARIANTS = [
    "rectangular integer grid; two to five contiguous, distinct, monochrome bands",
    "each band is at least two cells thick; some bands may have no holes",
    "every row/column along the band axis retains its nonzero band color",
    "at least one hole; its first nonzero neighbor has its latent band color",
    "default lessons include varied original-grid, zero-count, tie, and "
    "profile-gating counterexamples",
]
AXES = {
    "grid_h": {"type": "int", "default": "scheduled or sampled", "valid": "6..24"},
    "grid_w": {"type": "int", "default": "scheduled or sampled", "valid": "6..24"},
    "orientation": {"type": "str", "default": "scheduled or sampled",
                    "valid": "horizontal|vertical"},
    "n_bands": {"type": "int", "default": "2..5", "valid": "2..5"},
}
# These supported legacy spellings both mean n_bands + 1 (including zero).
# They are compatibility aliases, not additional independent distribution axes.
# Their full accepted range 3..6 and conflicts are covered by task-local tests.
COMPATIBILITY_ALIASES = ("palette_size", "n_distinct_colors")
# Rejections carry the actual conflicting caller keys in incompatible_axes.
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.20
LESSON_SCHEDULE_PERIOD = 8
SCHEDULE_PROFILES = ("canonical_horizontal", "teaching", "general_horizontal",
                     "canonical_vertical", "general_vertical")
_DIRECTIONS = ((-1, 0), (1, 0), (0, -1), (0, 1))


def schedule_profile(seed, sample_index, difficulty=None):
    """Odd slots teach every declared rival; even slots vary ordinary bands."""
    _validate_call(seed, sample_index, difficulty)
    slot = sample_index % LESSON_SCHEDULE_PERIOD
    if slot % 2:
        return "teaching"
    return {0: "canonical_horizontal", 2: "general_horizontal",
            4: "canonical_vertical", 6: "general_vertical"}[slot]


def _incompatible(message, overrides, keys):
    error = ValueError(message)
    error.incompatible_axes = tuple(sorted(set(keys) & set(overrides)))
    raise error


def _validate_call(seed, sample_index, difficulty):
    if type(seed) is not int:
        raise TypeError("seed must be an integer, not bool or a coerced value")
    if type(sample_index) is not int:
        raise TypeError("sample_index must be an integer, not bool or a coerced value")
    if sample_index < 0:
        raise ValueError("sample_index must be nonnegative")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be easy, medium, hard, or None")


def _validated_options(overrides):
    unknown = set(overrides) - set(AXES) - set(COMPATIBILITY_ALIASES)
    if unknown:
        raise ValueError(f"unknown override axis: {', '.join(sorted(unknown))}")
    options = {key: value for key, value in overrides.items() if value is not None}
    for key, value in options.items():
        if key == "orientation":
            if value not in ("horizontal", "vertical"):
                raise ValueError("orientation must be horizontal or vertical")
        else:
            if type(value) is not int:
                raise TypeError(f"{key} must be an integer, not bool or a coerced value")
            lo, hi = ((6, 24) if key in ("grid_h", "grid_w") else
                      (2, 5) if key == "n_bands" else (3, 6))
            if not lo <= value <= hi:
                raise ValueError(f"{key} must be in {lo}..{hi}")
    return options


def _general_layout(ctx, options, forced_orientation=None):
    counts = [(name, options[name] - (name != "n_bands"))
              for name in ("n_bands", "palette_size", "n_distinct_colors")
              if name in options]
    if len({value for _, value in counts}) > 1:
        _incompatible("n_bands and palette aliases disagree; palettes include zero",
                      options, [name for name, _ in counts])
    requested_count = counts[0][1] if counts else None
    orientations = [options.get("orientation", forced_orientation)]
    if orientations == [None]:
        orientations = ["horizontal", "vertical"]
    choices = []
    for orientation in orientations:
        band_axis = "grid_h" if orientation == "horizontal" else "grid_w"
        for count in ([requested_count] if requested_count else range(2, 6)):
            if options.get(band_axis, 24) >= 2 * count:
                choices.append((orientation, count))
    if not choices:
        _incompatible("band axis is too short for two cells per requested band",
                      options, ["grid_h", "grid_w", "orientation",
                                "n_bands", "palette_size", "n_distinct_colors"])
    rng = ctx.draw_rng("layout")
    # Difficulty changes preference, never the legal override domain.
    preferred = {"easy": 2, "medium": 3, "hard": 5}.get(ctx.difficulty, 3)
    orientation, count = rng.choice(choices + [x for x in choices if x[1] == preferred] * 2)
    h, w = options.get("grid_h"), options.get("grid_w")
    if h is None:
        h = rng.randint(max(6, 2 * count if orientation == "horizontal" else 6), 24)
    if w is None:
        w = rng.randint(max(6, 2 * count if orientation == "vertical" else 6), 24)
    return orientation, h, w, count


def _partition(total, count, rng):
    sizes = [2] * count
    for _ in range(total - 2 * count):
        sizes[rng.randrange(count)] += 1
    return sizes


def _layout(grid):
    """Recover band geometry from visible nonzero cells, never metadata."""
    for orientation, lines in (("horizontal", grid), ("vertical", list(zip(*grid)))):
        signatures = [{value for value in line if value != 0} for line in lines]
        if any(len(signature) != 1 for signature in signatures):
            continue
        colors = [next(iter(signature)) for signature in signatures]
        bands, start = [], 0
        for index in range(1, len(colors) + 1):
            if index == len(colors) or colors[index] != colors[start]:
                bands.append((start, index, colors[start]))
                start = index
        if (2 <= len(bands) <= 5 and
                len({color for _, _, color in bands}) == len(bands) and
                all(stop - start >= 2 for start, stop, _ in bands)):
            return orientation, bands
    return None


def _neighbor(grid, r, c):
    h, w = len(grid), len(grid[0])
    for dr, dc in _DIRECTIONS:
        nr, nc = r + dr, c + dc
        if 0 <= nr < h and 0 <= nc < w and grid[nr][nc] != 0:
            return grid[nr][nc]
    return None


def self_check(grid, *, difficulty=None, meta=None):
    if not isinstance(grid, list) or not grid or len(grid) > 30:
        return ["expected a nonempty grid with at most 30 rows"]
    if not all(isinstance(row, list) and 1 <= len(row) <= 30 for row in grid):
        return ["expected nonempty list rows with at most 30 columns"]
    if len({len(row) for row in grid}) != 1:
        return ["ragged grid"]
    if any(type(value) is not int or not 0 <= value <= 9
           for row in grid for value in row):
        return ["colors must be integer values 0..9, excluding bool"]
    layout = _layout(grid)
    if layout is None:
        return ["expected two to five distinct contiguous color bands, thickness >= 2"]
    orientation, bands = layout
    holes = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 0]
    if not holes:
        return ["no zero holes"]
    for r, c in holes:
        coordinate = r if orientation == "horizontal" else c
        color = next(color for start, stop, color in bands if start <= coordinate < stop)
        if _neighbor(grid, r, c) != color:
            return ["hole's selected neighbor differs from its latent band color"]
    return []


def _ordinary_grid(ctx, orientation, h, w, count, colors):
    rng = ctx.draw_rng("holes_and_bands")
    sizes = _partition(h if orientation == "horizontal" else w, count, rng)
    grid = full_grid(h, w, 0)
    bands, start = [], 0
    for color, size in zip(colors, sizes):
        stop = start + size
        bands.append((start, stop, color))
        for r in range(h):
            for c in range(w):
                if start <= (r if orientation == "horizontal" else c) < stop:
                    grid[r][c] = color
        start = stop
    # Inactive bands occur canonically. A forced active band prevents identity.
    # Trial counts are not advertised exact hole axes.
    forced = rng.randrange(count)
    for index, (start, stop, color) in enumerate(bands):
        attempts = rng.randint(1 if index == forced else 0, 3)
        candidates = [(r, c) for r in range(h) for c in range(w)
                      if start <= (r if orientation == "horizontal" else c) < stop]
        rng.shuffle(candidates)
        placed = 0
        for r, c in candidates:
            if placed == attempts:
                break
            grid[r][c] = 0
            if self_check(grid):
                grid[r][c] = color
            else:
                placed += 1
    return grid


def _teaching_layout(ctx):
    """Return a varied multi-band carrier for the three-hole extent witness."""
    rng = ctx.draw_rng("profile")
    m = rng.randint(6, 9)
    count = rng.randint(3, 5)
    active = tuple(sorted(rng.sample(range(count), 2)))
    sizes = [m if index in active else 2 for index in range(count)]
    spare = 24 - sum(sizes)
    inactive = [index for index in range(count) if index not in active]
    for _ in range(rng.randint(0, spare)):
        sizes[rng.choice(inactive)] += 1
    return m + 1, sum(sizes), count, sizes, active


def _teaching_grid(ctx, h, sizes, active, colors):
    """Build a non-template witness that refutes every declared shortcut.

    Two active bands have thickness ``h - 1``.  A same-row hole in each makes
    both row extents tie their full columns; an adjacent second hole in the
    first active band makes that row's extent one shorter than its column.
    Extra inactive bands vary the visible profile without changing the proof.
    """
    rng = ctx.draw_rng("holes_and_bands")
    starts = []
    start = 0
    grid = full_grid(h, sum(sizes), 0)
    for color, size in zip(colors, sizes):
        starts.append(start)
        for r in range(h):
            for c in range(start, start + size):
                grid[r][c] = color
        start += size

    primary, secondary = active
    p = rng.randint(1, h - 3)
    q = rng.randint(1, sizes[primary] - 2)
    k = rng.randint(1, sizes[secondary] - 2)
    primary_col = starts[primary] + q
    secondary_col = starts[secondary] + k
    for r, c in ((p, primary_col), (p + 1, primary_col),
                 (p, secondary_col)):
        grid[r][c] = 0
    if rng.choice((False, True)):
        grid = [row[::-1] for row in grid]
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(seed, sample_index, difficulty)
    options = _validated_options(overrides)
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=options)
    profile = schedule_profile(seed, sample_index, difficulty)
    teaching = not options and profile == "teaching"
    if teaching:
        orientation = "vertical"
        h, w, count, teaching_sizes, teaching_active = _teaching_layout(ctx)
    elif not options and profile == "canonical_horizontal":
        rng = ctx.draw_rng("profile")
        h, w, count = rng.choice(((13, 15, 3), (15, 19, 3), (17, 15, 4)))
        orientation = "horizontal"
    elif not options and profile == "canonical_vertical":
        rng = ctx.draw_rng("profile")
        h, w, count = rng.choice(((14, 13, 2), (14, 15, 3)))
        orientation = "vertical"
    else:
        forced = (profile.removeprefix("general_")
                  if not options and profile.startswith("general_") else None)
        orientation, h, w, count = _general_layout(ctx, options, forced)
    # Record FINAL observable values, including aliases, in GenCtx provenance.
    ctx.draw_choice("orientation", [orientation])
    ctx.draw_int_strict("grid_h", h, h)
    ctx.draw_int_strict("grid_w", w, w)
    ctx.draw_int_strict("n_bands", count, count)
    ctx.draw_int_strict("palette_size", count + 1, count + 1)
    ctx.draw_int_strict("n_distinct_colors", count + 1, count + 1)
    colors = ctx.draw_distinct_colors("band_colors", n=count, exclude=(0,))
    if teaching:
        return _teaching_grid(ctx, h, teaching_sizes, teaching_active, colors)
    return _ordinary_grid(ctx, orientation, h, w, count, colors)


def observe_overrides(grid):
    layout = _layout(grid)
    if layout is None:
        raise ValueError("cannot observe band controls in a non-band grid")
    orientation, bands = layout
    palette = len({value for row in grid for value in row})
    return {"grid_h": len(grid), "grid_w": len(grid[0]),
            "orientation": orientation, "n_bands": len(bands),
            "palette_size": palette, "n_distinct_colors": palette}


def _evaluate(grid, *, include_zero=True, sequential=False, forced=None, tie_column=True):
    """Analysis only: production outputs always come from canonical Racket."""
    h, w = len(grid), len(grid[0])
    output = [row[:] for row in grid]
    holes = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 0]
    for r, c in holes:
        source = output if sequential else grid
        color = _neighbor(source, r, c)
        if color is None:
            continue
        row_extent = sum(value == color or (include_zero and value == 0) for value in source[r])
        col_extent = sum(source[nr][c] == color or (include_zero and source[nr][c] == 0)
                         for nr in range(h))
        column = row_extent >= col_extent if tie_column else row_extent > col_extent
        if forced is not None:
            column = forced == "column"
        cells = ((nr, c) for nr in range(h)) if column else ((r, nc) for nc in range(w))
        for nr, nc in cells:
            if source[nr][nc] in (0, color):
                output[nr][nc] = 0
    return output


def rule_model(grid):
    return _evaluate(grid)


def rival_perpendicular(grid):
    layout = _layout(grid)
    if layout is None:
        return [row[:] for row in grid]
    return _evaluate(grid, forced="column" if layout[0] == "horizontal" else "row")


def rival_nonzero_extent(grid):
    return _evaluate(grid, include_zero=False)


def rival_sequential(grid):
    return _evaluate(grid, sequential=True)


def rival_tie_row(grid):
    return _evaluate(grid, tie_column=False)


def rival_always_row(grid):
    return _evaluate(grid, forced="row")


def rival_always_column(grid):
    return _evaluate(grid, forced="column")


def rival_profile_template_gate(grid):
    """Retained audit rival: special-case v4 teaching, else perpendicular."""
    layout = _layout(grid)
    if layout is None:
        return [row[:] for row in grid]
    orientation, bands = layout
    h, w = len(grid), len(grid[0])
    holes = [(r, c) for r, row in enumerate(grid)
             for c, value in enumerate(row) if value == 0]
    old_teaching = (orientation == "vertical" and len(bands) == 2
                    and w == 2 * (h - 1) and len(holes) == 3)
    if not old_teaching:
        return rival_perpendicular(grid)

    output = [row[:] for row in grid]
    for r, c in holes:
        color = _neighbor(grid, r, c)
        if color is None:
            continue
        clear_column = sum(other_r == r for other_r, _ in holes) >= 2
        cells = ((nr, c) for nr in range(h)) if clear_column else ((r, nc) for nc in range(w))
        for nr, nc in cells:
            if grid[nr][nc] in (0, color):
                output[nr][nc] = 0
    return output


CANONICAL_SHORTCUTS = {
    "perpendicular_to_band": rival_perpendicular,
    "exclude_zeros_from_extents": rival_nonzero_extent,
    "sequential_updates": rival_sequential,
    "tie_clears_row": rival_tie_row,
    "profile_template_gate": rival_profile_template_gate,
}
SEMANTIC_RIVALS = {**CANONICAL_SHORTCUTS,
                   "always_row": rival_always_row, "always_column": rival_always_column}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def strict_canonical_like(grid):
    reasons = self_check(grid)
    if reasons:
        return reasons
    return [] if rule_model(grid) == rival_perpendicular(grid) else [
        "lawful extent-interaction extension beyond canonical perpendicular erasure"]


SEMANTIC_WITNESSES = {
    name: (lambda grid, rival=rival: rule_model(grid) != rival(grid))
    for name, rival in SEMANTIC_RIVALS.items()
}
WITNESS_RIVALS = {name: [name] for name in SEMANTIC_RIVALS}


def lesson_identifiable(demos, query):
    """Finite declared-rival ambiguity check, not a universal induction claim."""
    return [f"{name} fits every demonstration but changes the query"
            for name, rival in LESSON_COMPETITORS.items()
            if all(rival(pair["input"]) == pair["output"] for pair in demos)
            and rival(query["input"]) != query["output"]]
