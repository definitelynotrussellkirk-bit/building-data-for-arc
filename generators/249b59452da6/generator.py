"""Input sampler for E82: complete eligible red diagonals simultaneously.

The selected Racket rule is the sole label authority. Diagnostic rivals below
are deliberately wrong rules, never used to label or filter generated examples.

Ordinary draws carry the whole counterexample curriculum on every grid. Exact
overrides also support smaller canvases, two-color inputs, and 9..10 windows;
these constrained draws use a smaller motif family and do not promise that full
curriculum. An incompatible request raises instead of returning a shorter draw.
"""
from __future__ import annotations

from functools import lru_cache

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "249b59452da6"
TASK_ID = GENERATOR_ID
RULE_HASH = "e42ab715e8c9"
VERSION = "3.0.1"
EXAMPLES_NEEDED = 3
SUMMARY = (
    "On a sparse zero-background grid, inspect every input 2x2 window. When "
    "exactly two red (2) cells occupy opposite diagonal corners and both "
    "remaining corners are zero, fill those zeros with green (3). Evaluate "
    "all windows on the original input, including overlapping windows and "
    "boundary windows. Preserve every other cell. Colored distractors, "
    "orthogonal red bars, and occupied opposite corners remain unchanged."
)

INVARIANTS = [
    "rectangular ARC integer grids, dimensions 4..18, with at least half the cells zero",
    "n_pairs counts eligible input 2x2 windows exactly, including windows sharing red cells or zeros",
    "palette_size counts all distinct input colors, including background 0 and fixed target color 2",
    "all draws have 1..10 eligible windows and 2..5 input colors; no identity-only default draws",
    "ordinary draws include both diagonals, an edge window, an overlapping zigzag, a longer red chain, a red bar, and colored foils",
    "overrides preserve requested dimensions, window count, and palette or raise a structured incompatibility",
]

AXES = {
    "grid_h": {"type": "int", "default": "canonical profiles or rng 9..18", "valid": "4..18"},
    "grid_w": {"type": "int", "default": "canonical profiles or rng 9..18", "valid": "4..18"},
    "n_pairs": {"type": "int", "default": "easy 2..5; medium 2..6; hard 2..8", "valid": "1..10"},
    "palette_size": {"type": "int", "default": "canonical profiles or rng 3..5; includes 0", "valid": "2..5"},
}
# Strict policy: only exceptions carrying their actual axes identify refusals.
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []
MIN_STRICT_FRAC = 0.25

_CANONICAL_PROFILES = ((10, 12, 3), (11, 11, 3), (12, 10, 4), (9, 13, 3))
SCHEDULE_PROFILES = ("10x12_palette3", "11x11_palette3", "12x10_palette4", "9x13_palette3", "broad")


class IncompatibleAxes(ValueError):
    """A requested tuple has no placement in the documented sparse sampler."""

    def __init__(self, h, w, n_pairs, palette_size):
        self.incompatible_axes = ("grid_h", "grid_w", "n_pairs", "palette_size")
        super().__init__(
            f"incompatible axes: grid_h={h}, grid_w={w}, n_pairs={n_pairs}, "
            f"palette_size={palette_size}; no exact placement in the supported "
            "separated-patch or compact checkerboard-subset family with at "
            "least half the cells zero and safe space for every distractor color"
        )


def schedule_profile(seed, sample_index, difficulty=None):
    """Four canonical scale/palette profiles plus an independent broad profile."""
    return SCHEDULE_PROFILES[sample_index % len(SCHEDULE_PROFILES)]


def _grid_errors(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty rectangular grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected nonempty rows"]
    if any(not isinstance(row, (list, tuple)) or len(row) != len(grid[0]) for row in grid):
        return ["ragged grid"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be integer ARC colors 0..9; booleans are not colors"]
    return []


def _eligible_windows(grid):
    """Observe the input precondition; this function does not generate labels."""
    windows = []
    for r in range(len(grid) - 1):
        for c in range(len(grid[0]) - 1):
            a, b = grid[r][c], grid[r][c + 1]
            d, e = grid[r + 1][c], grid[r + 1][c + 1]
            if a == e == 2 and b == d == 0:
                windows.append((r, c, "main"))
            elif b == d == 2 and a == e == 0:
                windows.append((r, c, "anti"))
    return windows


def _zero_corners(windows):
    cells = set()
    for r, c, diagonal in windows:
        cells.update(((r, c + 1), (r + 1, c)) if diagonal == "main"
                     else ((r, c), (r + 1, c + 1)))
    return cells


def observe_overrides(grid):
    """Recover every public control from pixels, without generation metadata."""
    errors = _grid_errors(grid)
    if errors:
        raise ValueError("; ".join(errors))
    return {
        "grid_h": len(grid), "grid_w": len(grid[0]),
        "n_pairs": len(_eligible_windows(grid)),
        "palette_size": len({value for row in grid for value in row}),
    }


def self_check(grid, *, difficulty=None, meta=None):
    errors = _grid_errors(grid)
    if errors:
        return errors
    observed = observe_overrides(grid)
    for name, lo, hi in (("grid_h", 4, 18), ("grid_w", 4, 18),
                         ("n_pairs", 1, 10), ("palette_size", 2, 5)):
        if not lo <= observed[name] <= hi:
            errors.append(f"{name}={observed[name]} outside [{lo}, {hi}]")
    if sum(value == 0 for row in grid for value in row) * 2 < len(grid) * len(grid[0]):
        errors.append("sparse zero background requires at least half the cells to be zero")
    return errors


def strict_canonical_like(grid):
    """Canonical scale, sparsity, color roles and active branches, not shape alone.

    The manifold permits the local counterexamples that distinguish the rule;
    it does not require the canonical examples' accidental component isolation.
    """
    errors = self_check(grid)
    if errors:
        return errors
    h, w = len(grid), len(grid[0])
    colors = {value for row in grid for value in row}
    windows = _eligible_windows(grid)
    if not (9 <= h <= 12 and 10 <= w <= 13 and 3 <= len(colors) <= 4):
        errors.append("outside the canonical dimension/palette envelope")
    if len(windows) < 2 or {diagonal for _, _, diagonal in windows} != {"main", "anti"}:
        errors.append("canonical-like scenes need at least two active windows and both diagonals")
    if not colors - {0, 2}:
        errors.append("canonical-like scenes contain unchanged nonred distractors")
    if sum(value != 0 for row in grid for value in row) * 4 > h * w:
        errors.append("canonical-like foreground occupies at most one quarter of the grid")
    return errors


def _spread(total, slots, rng):
    gaps = [0] * slots
    for _ in range(total):
        gaps[rng.randrange(slots)] += 1
    return gaps


def _put(grid, patch, r, c, reserved):
    for dr, row in enumerate(patch):
        for dc, value in enumerate(row):
            grid[r + dr][c + dc] = value
            reserved.add((r + dr, c + dc))


def _turn_square(patch, rng):
    for _ in range(rng.randrange(4)):
        patch = [list(row) for row in zip(*patch[::-1])]
    return patch


def _strip(grid, patches, row, band_height, rng, reserved, *, right_flush=False):
    if not patches:
        return
    spare = len(grid[0]) - sum(len(patch[0]) for patch in patches) - len(patches) + 1
    if spare < 0:
        raise RuntimeError("constructive strip exceeded its proved width")
    gaps = _spread(spare, len(patches) if right_flush else len(patches) + 1, rng)
    c = gaps[0]
    for index, patch in enumerate(patches):
        r = row + rng.randrange(band_height - len(patch) + 1)
        _put(grid, patch, r, c, reserved)
        c += len(patch[0])
        if index + 1 < len(patches):
            c += 1 + gaps[index + 1]


def _finish_curriculum(grid, colors, reserved, rng, transpose):
    """Realize any remaining palette color without occupying a teaching patch."""
    h, w = len(grid), len(grid[0])
    present = {value for row in grid for value in row}
    unused = [color for color in colors if color not in present]
    empty = [(r, c) for r in range(h) for c in range(w)
             if grid[r][c] == 0 and (r, c) not in reserved]
    rng.shuffle(empty)
    if len(empty) < len(unused):
        raise RuntimeError("proved curriculum layout left no room for its palette")
    for (r, c), color in zip(empty, unused):
        grid[r][c] = color
    if rng.choice((False, True)):
        grid.reverse()
    return [list(row) for row in zip(*grid)] if transpose else grid


def _combined_foil(color, rng):
    """A nonred diagonal and two red near misses, with zero eligible windows.

    One red near miss has a nonred occupied corner; the other has a third red
    corner. Its red 4-connected component also has the canonical size four.
    """
    patch = [[0, 0, color, 0], [2, color, 0, 2], [0, 2, 2, 2]]
    if rng.choice((False, True)):
        patch.reverse()
    if rng.choice((False, True)):
        patch = [row[::-1] for row in patch]
    return patch


def _low_count_curriculum(h, w, n_pairs, colors, rng):
    """Two or three windows with the same full rival coverage as larger scenes.

    The T combines an overlapping red zigzag, a connected red chain, a length-3
    orthogonal bar, and untouched component-box zeros. Its five red cells form
    just three 4-connected components. The combined foil adds four more before
    any extra palette markers. Every active window has an attached red endpoint.
    """
    transpose = rng.choice((False, True))
    if transpose:
        h, w = w, h
    grid = full_grid(h, w, 0)
    reserved = set()
    foil = _combined_foil(colors[0], rng)
    combined = [[2, 0, 2], [0, 2, 0], [0, 2, 0], [0, 2, 0]]
    bands = [(4, [foil, combined], True)]
    if n_pairs == 3:
        bands.append((2, [_turn_square([[2, 0], [0, 2]], rng)], False))
    rng.shuffle(bands)
    occupied_height = sum(height for height, _, _ in bands) + len(bands) - 1
    row_gaps = _spread(h - occupied_height, len(bands) + 1, rng)
    r = row_gaps[0]
    for index, (height, patches, flush) in enumerate(bands):
        _strip(grid, patches, r, height, rng, reserved, right_flush=flush)
        r += height
        if index + 1 < len(bands):
            r += 1 + row_gaps[index + 1]
    return _finish_curriculum(grid, colors, reserved, rng, transpose)


def _full_curriculum(h, w, n_pairs, colors, rng):
    """Pack additive, separated patches without placement attempts or clipping."""
    transpose = rng.choice((False, True))
    if transpose:
        h, w = w, h
    grid = full_grid(h, w, 0)
    reserved = set()
    chain = _turn_square([[2, 0, 0], [0, 2, 0], [0, 0, 2]], rng)
    foil = _combined_foil(colors[0], rng)
    chain_patches = [foil, chain]  # Last chain column is a boundary column.

    # A red bar attaches to one zigzag endpoint. Eligibility remains local:
    # both windows still qualify despite this orthogonal red attachment.
    bar_length = rng.randint(3, 4)
    zigzag = [[2, 0] + [2] * bar_length, [0, 2] + [0] * bar_length]
    if rng.choice((False, True)):
        zigzag.reverse()
    if rng.choice((False, True)):
        zigzag = [row[::-1] for row in zigzag]
    has_extra = n_pairs >= 5
    middle_patches = [zigzag]
    if has_extra:
        middle_patches.append(_turn_square([[2, 0], [0, 2]], rng))
    rng.shuffle(middle_patches)
    extra_patches = [_turn_square([[2, 0], [0, 2]], rng)
                     for _ in range(max(0, n_pairs - 5))]
    bands = [(3, chain_patches, True), (2, middle_patches, False),
             (2, extra_patches, False)]
    rng.shuffle(bands)
    row_gaps = _spread(h - 9, 4, rng)
    r = row_gaps[0]
    for index, (height, patches, flush) in enumerate(bands):
        _strip(grid, patches, r, height, rng, reserved, right_flush=flush)
        r += height
        if index < 2:
            r += 1 + row_gaps[index + 1]

    return _finish_curriculum(grid, colors, reserved, rng, transpose)


@lru_cache(maxsize=3)
def _compact_catalog(width):
    """Immutable exact geometry: all subsets of one parity in a 4x4..4x6 box.

    At most 4095 subsets are examined once per box width. This is exhaustive
    over this explicitly limited motif family, not a claim to enumerate all ARC
    grids. Every retained entry records its actual eligible windows.
    """
    positions = tuple((r, c) for r in range(4) for c in range(width) if (r + c) % 2 == 0)
    index = {point: i for i, point in enumerate(positions)}
    edges = []
    for r in range(3):
        for c in range(width - 1):
            points = ((r, c), (r + 1, c + 1)) if (r + c) % 2 == 0 else ((r, c + 1), (r + 1, c))
            edges.append(((1 << index[points[0]]) | (1 << index[points[1]]), r, c))
    catalog = []
    for mask in range(1, 1 << len(positions)):
        active = tuple((r, c) for bits, r, c in edges if mask & bits == bits)
        if not 1 <= len(active) <= 10:
            continue
        red = tuple(point for i, point in enumerate(positions) if mask & (1 << i))
        covered = frozenset((r + dr, c + dc) for r, c in active for dr in (0, 1) for dc in (0, 1))
        catalog.append((len(active), red, covered))
    return tuple(catalog)


@lru_cache(maxsize=900)
def _compact_feasible(h, w, palette_size):
    width = min(6, max(h, w))
    area = h * w
    needed = palette_size - 2
    catalog = _compact_catalog(width)
    candidates = []
    for n_pairs in range(1, 11):
        matching = [index for index, (count, red, covered) in enumerate(catalog)
                    if count == n_pairs and len(red) + needed <= area // 2
                    and area - len(set(red) | covered) >= needed]
        if matching:
            least_red = min(len(catalog[index][1]) for index in matching)
            matching = [index for index in matching if len(catalog[index][1]) <= least_red + 1]
        candidates.append(tuple(matching))
    return tuple(candidates)


def _compact_draw(h, w, n_pairs, colors, rng):
    palette_size = len(colors) + 2
    options = _compact_feasible(h, w, palette_size)[n_pairs - 1]
    if not options:
        raise IncompatibleAxes(h, w, n_pairs, palette_size)
    transpose = h > w
    bh, bw = (w, h) if transpose else (h, w)
    width = min(6, bw)
    _, red, _ = _compact_catalog(width)[rng.choice(options)]
    patch = full_grid(4, width, 0)
    for r, c in red:
        patch[r][c] = 2
    if rng.choice((False, True)):
        patch.reverse()
    if rng.choice((False, True)):
        patch = [row[::-1] for row in patch]
    grid = full_grid(bh, bw, 0)
    _put(grid, patch, rng.randrange(bh - 3), rng.randrange(bw - width + 1), set())
    protected = _zero_corners(_eligible_windows(grid))
    safe = [(r, c) for r in range(bh) for c in range(bw)
            if grid[r][c] == 0 and (r, c) not in protected]
    rng.shuffle(safe)
    for (r, c), color in zip(safe, colors):
        grid[r][c] = color
    return [list(row) for row in zip(*grid)] if transpose else grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axes: {', '.join(unknown)}")
    for name, value in overrides.items():
        if type(value) is not int:
            raise TypeError(f"{name} override must be an integer, not {type(value).__name__}")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be easy, medium, hard, or None")
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    profile_index = sample_index % len(SCHEDULE_PROFILES)
    profile = _CANONICAL_PROFILES[profile_index] if profile_index < 4 else None

    def dimension(name, offset):
        if name in overrides:
            return ctx.draw_int_strict(name, 4, 18)
        if profile is not None:
            return ctx.draw_choice(name, (profile[offset],))
        return ctx.draw_int_strict(name, 9, 18)

    h, w = dimension("grid_h", 0), dimension("grid_w", 1)
    if "palette_size" in overrides:
        palette_size = ctx.draw_int_strict("palette_size", 2, 5)
    elif profile is not None:
        palette_size = ctx.draw_choice("palette_size", (profile[2],))
    else:
        palette_size = ctx.draw_int_strict("palette_size", 3, 5)
    if "n_pairs" in overrides:
        n_pairs = ctx.draw_int_strict("n_pairs", 1, 10)
    else:
        preferred = {"easy": (2, 2, 3, 3, 4, 5), "medium": (2, 3, 4, 5, 6),
                     "hard": (2, 3, 4, 5, 6, 7, 7, 8, 8), None: (2, 3, 4, 5, 6)}[difficulty]
        feasible = _compact_feasible(h, w, palette_size)
        choices = [count for count in preferred if feasible[count - 1]]
        if not choices:
            choices = [count for count in range(1, 11) if feasible[count - 1]]
        if not choices:
            raise IncompatibleAxes(h, w, "any", palette_size)
        n_pairs = ctx.draw_choice("n_pairs", choices)
    colors = ctx.draw_distinct_colors("distractor_colors", n=palette_size - 2, exclude=(0, 2))
    rng = ctx.draw_rng("constructive_placement")
    if min(h, w) >= 9 and 2 <= n_pairs <= 3 and palette_size >= 3:
        grid = _low_count_curriculum(h, w, n_pairs, colors, rng)
    elif min(h, w) >= 9 and 4 <= n_pairs <= 8 and palette_size >= 3:
        grid = _full_curriculum(h, w, n_pairs, colors, rng)
    else:
        grid = _compact_draw(h, w, n_pairs, colors, rng)
    expected = {"grid_h": h, "grid_w": w, "n_pairs": n_pairs, "palette_size": palette_size}
    if observe_overrides(grid) != expected:
        raise RuntimeError("constructive placement violated its exact controls")
    errors = self_check(grid)
    if errors:
        raise RuntimeError("constructed invalid input: " + "; ".join(errors))
    return grid


# Everything below is diagnostic contract code, never a label authority.
def _rival_any_nonzero_diagonal(grid):
    out = [list(row) for row in grid]
    for r in range(len(grid) - 1):
        for c in range(len(grid[0]) - 1):
            a, b, d, e = grid[r][c], grid[r][c + 1], grid[r + 1][c], grid[r + 1][c + 1]
            if a == e != 0 and b == d == 0:
                out[r][c + 1] = out[r + 1][c] = 3
            if b == d != 0 and a == e == 0:
                out[r][c] = out[r + 1][c + 1] = 3
    return out


def _rival_occupied_corners(grid, overwrite):
    out = [list(row) for row in grid]
    for r in range(len(grid) - 1):
        for c in range(len(grid[0]) - 1):
            for ends, missing in ((((r, c), (r + 1, c + 1)), ((r, c + 1), (r + 1, c))),
                                  (((r, c + 1), (r + 1, c)), ((r, c), (r + 1, c + 1)))):
                if all(grid[rr][cc] == 2 for rr, cc in ends):
                    for rr, cc in missing:
                        if overwrite or grid[rr][cc] == 0:
                            out[rr][cc] = 3
    return out


def _rival_ignore_occupied_corner(grid):
    return _rival_occupied_corners(grid, False)


def _rival_overwrite_occupied_corner(grid):
    return _rival_occupied_corners(grid, True)


def _rival_allow_third_red_corner(grid):
    """RIVAL: treat an extra red corner as allowed while rejecting other colors."""
    out = [list(row) for row in grid]
    for r in range(len(grid) - 1):
        for c in range(len(grid[0]) - 1):
            points = ((r, c), (r, c + 1), (r + 1, c), (r + 1, c + 1))
            a, b, d, e = [grid[rr][cc] for rr, cc in points]
            if all(value in (0, 2) for value in (a, b, d, e)) and (a == e == 2 or b == d == 2):
                for rr, cc in points:
                    if grid[rr][cc] == 0:
                        out[rr][cc] = 3
    return out


def _rival_reject_orthogonal_attachment(grid):
    """RIVAL: disqualify a valid diagonal whose red endpoint touches more red."""
    out = [list(row) for row in grid]
    h, w = len(grid), len(grid[0])
    for r, c, diagonal in _eligible_windows(grid):
        ends = ((r, c), (r + 1, c + 1)) if diagonal == "main" else ((r, c + 1), (r + 1, c))
        attached = any(0 <= rr + dr < h and 0 <= cc + dc < w and grid[rr + dr][cc + dc] == 2
                       for rr, cc in ends for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)))
        if not attached:
            for rr, cc in _zero_corners(((r, c, diagonal),)):
                out[rr][cc] = 3
    return out


def _red_components(grid):
    unseen = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 2}
    components = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        component, pending = {start}, [start]
        while pending:
            r, c = pending.pop()
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    point = (r + dr, c + dc)
                    if point in unseen:
                        unseen.remove(point)
                        component.add(point)
                        pending.append(point)
        components.append(component)
    return components


def _rival_isolated_pairs(grid):
    out = [list(row) for row in grid]
    isolated = set().union(*(component for component in _red_components(grid) if len(component) == 2))
    for r, c, diagonal in _eligible_windows(grid):
        ends = ((r, c), (r + 1, c + 1)) if diagonal == "main" else ((r, c + 1), (r + 1, c))
        if all(point in isolated for point in ends):
            for rr, cc in _zero_corners(((r, c, diagonal),)):
                out[rr][cc] = 3
    return out


def _rival_in_place_scan(grid):
    out = [list(row) for row in grid]
    for r in range(len(out) - 1):
        for c in range(len(out[0]) - 1):
            a, b, d, e = out[r][c], out[r][c + 1], out[r + 1][c], out[r + 1][c + 1]
            if a == e == 2 and b == d == 0:
                out[r][c + 1] = out[r + 1][c] = 3
            elif b == d == 2 and a == e == 0:
                out[r][c] = out[r + 1][c + 1] = 3
    return out


def _rival_skip_bottom_right(grid):
    out = [list(row) for row in grid]
    windows = [window for window in _eligible_windows(grid)
               if window[0] < len(grid) - 2 and window[1] < len(grid[0]) - 2]
    for r, c in _zero_corners(windows):
        out[r][c] = 3
    return out


def _rival_component_boxes(grid):
    out = [list(row) for row in grid]
    for component in _red_components(grid):
        if len(component) < 2:
            continue
        rows, cols = zip(*component)
        for r in range(min(rows), max(rows) + 1):
            for c in range(min(cols), max(cols) + 1):
                if grid[r][c] == 0:
                    out[r][c] = 3
    return out


def _rival_one_diagonal(grid, diagonal):
    out = [list(row) for row in grid]
    for r, c in _zero_corners(window for window in _eligible_windows(grid) if window[2] == diagonal):
        out[r][c] = 3
    return out


def _rival_main_only(grid):
    return _rival_one_diagonal(grid, "main")


def _rival_anti_only(grid):
    return _rival_one_diagonal(grid, "anti")


def _rival_orthogonal_completion(grid):
    out = [list(row) for row in grid]
    for r in range(len(grid) - 1):
        for c in range(len(grid[0]) - 1):
            points = ((r, c), (r, c + 1), (r + 1, c), (r + 1, c + 1))
            values = [grid[rr][cc] for rr, cc in points]
            if values.count(2) == 2 and values.count(0) == 2:
                for rr, cc in points:
                    if grid[rr][cc] == 0:
                        out[rr][cc] = 3
    return out


CANONICAL_SHORTCUTS = {
    "any_nonzero_diagonal": _rival_any_nonzero_diagonal,
    "ignore_occupied_corner": _rival_ignore_occupied_corner,
    "overwrite_occupied_corner": _rival_overwrite_occupied_corner,
    "allow_third_red_corner": _rival_allow_third_red_corner,
    "reject_orthogonal_red_attachment": _rival_reject_orthogonal_attachment,
    "isolated_red_pairs_only": _rival_isolated_pairs,
    "in_place_scan": _rival_in_place_scan,
    "skip_bottom_right": _rival_skip_bottom_right,
    "red_component_bounding_boxes": _rival_component_boxes,
}
SEMANTIC_RIVALS = {
    **CANONICAL_SHORTCUTS,
    "main_diagonal_only": _rival_main_only,
    "anti_diagonal_only": _rival_anti_only,
    "orthogonal_completion": _rival_orthogonal_completion,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def _rival_has_counterexample(grid, rival):
    """Input feature predicate: identify a rival's missing or extra local edit.

    This compares changed-cell sets with the observed local preconditions. It
    returns only a boolean. The semantic gate checks every claim against Racket.
    """
    expected_cells = _zero_corners(_eligible_windows(grid))
    prediction = rival(grid)
    return any(prediction[r][c] != (3 if (r, c) in expected_cells else value)
               for r, row in enumerate(grid) for c, value in enumerate(row))


def _witness_nonred(grid):
    return _rival_has_counterexample(grid, _rival_any_nonzero_diagonal)


def _witness_blocked(grid):
    return _rival_has_counterexample(grid, _rival_ignore_occupied_corner)


def _witness_third_red(grid):
    return _rival_has_counterexample(grid, _rival_allow_third_red_corner)


def _witness_attachment(grid):
    return _rival_has_counterexample(grid, _rival_reject_orthogonal_attachment)


def _witness_chain(grid):
    return _rival_has_counterexample(grid, _rival_isolated_pairs)


def _witness_overlap(grid):
    return _rival_has_counterexample(grid, _rival_in_place_scan)


def _witness_edge(grid):
    return _rival_has_counterexample(grid, _rival_skip_bottom_right)


def _witness_box_gap(grid):
    return _rival_has_counterexample(grid, _rival_component_boxes)


def _witness_main(grid):
    return _rival_has_counterexample(grid, _rival_anti_only)


def _witness_anti(grid):
    return _rival_has_counterexample(grid, _rival_main_only)


def _witness_bar(grid):
    return _rival_has_counterexample(grid, _rival_orthogonal_completion)


SEMANTIC_WITNESSES = {
    "nonred_diagonal_unchanged": _witness_nonred,
    "occupied_corner_blocks_completion": _witness_blocked,
    "third_red_corner_blocks_completion": _witness_third_red,
    "orthogonally_attached_red_pair": _witness_attachment,
    "connected_red_chain": _witness_chain,
    "overlapping_windows_require_simultaneity": _witness_overlap,
    "bottom_or_right_edge": _witness_edge,
    "chain_bounding_box_has_untouched_zeros": _witness_box_gap,
    "main_diagonal": _witness_main,
    "anti_diagonal": _witness_anti,
    "orthogonal_red_bar_unchanged": _witness_bar,
}
WITNESS_RIVALS = {
    "nonred_diagonal_unchanged": ["any_nonzero_diagonal"],
    "occupied_corner_blocks_completion": ["ignore_occupied_corner", "overwrite_occupied_corner"],
    "third_red_corner_blocks_completion": ["allow_third_red_corner"],
    "orthogonally_attached_red_pair": ["reject_orthogonal_red_attachment"],
    "connected_red_chain": ["isolated_red_pairs_only"],
    "overlapping_windows_require_simultaneity": ["in_place_scan"],
    "bottom_or_right_edge": ["skip_bottom_right"],
    "chain_bounding_box_has_untouched_zeros": ["red_component_bounding_boxes"],
    "main_diagonal": ["anti_diagonal_only"],
    "anti_diagonal": ["main_diagonal_only"],
    "orthogonal_red_bar_unchanged": ["orthogonal_completion"],
}


def lesson_identifiable(demos, query):
    """Finite rival screen using supplied authoritative labels, not a proof."""
    reasons = []
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            if rival(query["input"]) != query["output"]:
                reasons.append(f"{name} fits every demonstration but changes the query answer")
    return reasons
