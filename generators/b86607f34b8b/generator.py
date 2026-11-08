"""Input-only sampler for mini-legends selecting per-color closure operations.

Racket remains the sole label authority. Python projections below are explicit
rival/witness diagnostics used to select informative inputs and audit lessons.
"""
from __future__ import annotations

from functools import partial

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "b86607f34b8b"
TASK_ID = GENERATOR_ID
RULE_HASH = "6fa3fd6234a8"
VERSION = "3.0.0"
SUMMARY = (
    "Rows 0/1 map colors to modes above a color-9 divider: 1 closes rows, "
    "2 closes columns, 3 closes rows THEN columns ONCE, and 4 keeps only new "
    "row bridges, erasing its seeds. Rebuild the scene from original color "
    "supports; overlaps prefer mode 1 > 3 > 2 > 4, then the larger color."
)
INVARIANTS = [
    "integer colors 0..9; background 0; unique full color-9 divider at row 2",
    "distinct legend colors 1..8 in row 0 paired with modes 1..4 in row 1",
    "each legend color occurs in the body; no unlisted body colors",
    "teaching draws preserve visible witnesses after all overlap arbitration",
    "outputs are supplied only by the unchanged canonical Racket rule",
]
AXES = {
    "grid_h": {"type": "int", "default": "9 in core; 9..14 broad", "valid": "9..14"},
    "grid_w": {"type": "int", "default": "11 in core; 9..14 broad", "valid": "9..14"},
    "n_colors": {"type": "int", "default": "4 in core; 5 broad; exact override 3..5", "valid": "3..5"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0
SCHEDULE_PROFILES = tuple((core, modes) for core in (False, True) for modes in range(3))


def schedule_profile(seed, sample_index, difficulty=None):
    return sample_index % 2 == 0, sample_index % 3


def _close(cells, axis):
    groups = {}
    for point in cells:
        groups.setdefault(point[axis], []).append(point[1 - axis])
    result = set()
    for fixed, moving in groups.items():
        for value in range(min(moving), max(moving) + 1):
            result.add((fixed, value) if axis == 0 else (value, fixed))
    return result


def _bbox(cells):
    if not cells:
        return set()
    ys, xs = zip(*cells)
    return {(y, x) for y in range(min(ys), max(ys) + 1)
            for x in range(min(xs), max(xs) + 1)}


def _closed(cells, mode, variant):
    rows = _close(cells, 0)
    if variant == "all_bbox" or (variant == "mode3_bbox" and mode == 3):
        return _bbox(cells)
    if variant == "all_double":
        return _close(rows, 1)
    if mode == 1:
        return rows
    if mode == 2:
        return _close(cells, 1)
    if mode == 3:
        if variant == "mode3_reverse":
            return _close(_close(cells, 1), 0)
        if variant == "mode3_union":
            return rows | _close(cells, 1)
        result = _close(rows, 1)
        if variant == "mode3_fixedpoint":
            while True:
                expanded = _close(_close(result, 0), 1)
                if expanded == result:
                    break
                result = expanded
        return result
    if variant == "bridge_keeps_seeds":
        return rows
    if variant == "bridge_blank":
        return set()
    if variant == "bridge_column":
        return _close(cells, 1) - cells
    return rows - cells


def diagnostic_output(grid, variant="reference"):
    """Authoring projection, NOT exported labels. Variants are deliberate rivals."""
    h, w = len(grid), len(grid[0])
    separator = next(r for r, row in enumerate(grid) if all(v == 9 for v in row))
    out = [list(row) if r <= separator else [0] * w for r, row in enumerate(grid)]
    winners = {}
    has_mode1 = any(color and mode == 1 for color, mode in zip(grid[0], grid[1]))
    for column, color in enumerate(grid[0]):
        if not color:
            continue
        mode = grid[1][column]
        cells = {(r, c) for r in range(separator + 1, h) for c in range(w)
                 if grid[r][c] == color}
        priority = {1: 3, 3: 2, 2: 1, 4: 0}[mode]
        key = (priority, color)
        if variant == "color_priority":
            key = (color, priority)
        elif variant == "legend_rightmost_priority":
            key = (column, color)
        elif variant == "lower_color_tie":
            key = (priority, -color)
        elif variant == "legend_rightmost_tie":
            key = (priority, column)
        elif variant == "legend_leftmost_tie":
            key = (priority, -column)
        elif variant in ("mode1_left_else_right_tie", "mode1_right_else_left_tie"):
            left_wins = has_mode1 == (variant == "mode1_left_else_right_tie")
            key = (priority, -column if left_wins else column)
        for point in _closed(cells, mode, variant):
            if point not in winners or key > winners[point]:
                winners[point] = key
                r, c = point
                out[r][c] = color
    return out


_RIVAL_NAMES = (
    "all_double", "all_bbox", "mode3_bbox", "mode3_reverse", "mode3_fixedpoint",
    "mode3_union", "bridge_keeps_seeds", "bridge_blank", "bridge_column",
    "color_priority", "legend_rightmost_priority", "lower_color_tie",
    "legend_rightmost_tie", "legend_leftmost_tie",
    "mode1_left_else_right_tie", "mode1_right_else_left_tie",
)
SEMANTIC_RIVALS = {name: partial(diagnostic_output, variant=name) for name in _RIVAL_NAMES}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
# These thirteen candidates must fit every canonical pair in the retained tests.
CANONICAL_SHORTCUTS = {
    name: SEMANTIC_RIVALS[name] for name in _RIVAL_NAMES
    if name not in ("mode3_union", "color_priority", "legend_rightmost_priority")
}


def _counterexample(grid, variant):
    return diagnostic_output(grid) != diagnostic_output(grid, variant)


def _has_mode(grid, mode):
    return any(color and grid[1][c] == mode for c, color in enumerate(grid[0]))


SEMANTIC_WITNESSES = {name: partial(_counterexample, variant=name) for name in _RIVAL_NAMES}
SEMANTIC_WITNESSES.update({f"mode_{mode}": partial(_has_mode, mode=mode) for mode in range(1, 5)})
WITNESS_RIVALS = {name: [name] for name in _RIVAL_NAMES}
BRANCH_WITNESSES = tuple(f"mode_{mode}" for mode in range(1, 5))


def lesson_identifiable(demos, query):
    """Finite declared-rival test using supplied Racket labels; never a proof."""
    return [f"{name} fits every demonstration but disagrees with the query"
            for name, rival in LESSON_COMPETITORS.items()
            if all(rival(pair["input"]) == pair["output"] for pair in demos)
            and rival(query["input"]) != query["output"]]


def _draw_axis(ctx, name, lo, hi, anchor=None, favored=()):
    if ctx.overrides.get(name) is not None:
        return ctx.draw_int(name, lo, hi)
    if anchor is not None:
        return ctx.draw_choice(name, (anchor,))
    return ctx.draw_choice(name, tuple(range(lo, hi + 1)) + tuple(favored))


def _motif(rng, body_h, width, compact):
    """Same shape family for EVERY mode: no geometry-to-mode cue.

    Core scenes use one sparse three-seed motif. Broad scenes combine two
    disconnected motifs witnessing order and non-idempotence. Monotone
    embeddings vary gaps; flips and extra seeds vary the actual body.
    """
    if compact:
        rs = sorted(rng.sample(range(body_h), 3))
        cs = sorted(rng.sample(range(width), 3))
        templates = (
            {(rs[0], cs[0]), (rs[0], cs[2]), (rs[2], cs[0])},
            {(rs[0], cs[0]), (rs[0], cs[2]), (rs[2], cs[1])},
            {(rs[0], cs[0]), (rs[2], cs[0]), (rs[1], cs[2])},
        )
        points = rng.choice(templates)
    else:
        rs = sorted(rng.sample(range(body_h), 6))
        cs = sorted(rng.sample(range(width), 7))
        points = {(rs[0], cs[0]), (rs[0], cs[2]), (rs[2], cs[1]),
                  (rs[3], cs[4]), (rs[5], cs[4]), (rs[4], cs[6])}
    if rng.randrange(2):
        points = {(body_h - 1 - r, c) for r, c in points}
    if rng.randrange(2):
        points = {(r, width - 1 - c) for r, c in points}
    return {(r + 3, c) for r, c in points}


def _mode_plan(n_colors, phase):
    if n_colors == 3:
        return ((1, 2, 3), (1, 3, 4), (2, 3, 4))[phase]
    if n_colors == 4:
        return ((1, 2, 3, 4), (1, 3, 3, 4), (2, 3, 3, 4))[phase]
    # Three tied colors can simultaneously refute both legend-order rivals.
    # Every default four-pair lesson has two broad boards; any query rotation
    # therefore leaves at least one of these individually teaching boards.
    return (1, 2, 3, 3, 3)


def _required_rivals(modes, compact):
    required = list(_RIVAL_NAMES)
    if compact:
        # Keep canonical-scale sparse scenes. Every default four-pair window
        # also has TWO broad boards individually refuting these alternatives,
        # so every query rotation retains their evidence in a demonstration.
        required = [name for name in required if name not in
                    ("mode3_reverse", "mode3_fixedpoint", "mode3_union")]
    if 4 not in modes:
        required = [name for name in required if not name.startswith("bridge_")]
    if len(set(modes)) == len(modes):
        required.remove("lower_color_tie")
    if max(modes.count(mode) for mode in set(modes)) < 3:
        required = [name for name in required if name not in
                    ("legend_rightmost_tie", "legend_leftmost_tie",
                     "mode1_left_else_right_tie", "mode1_right_else_left_tie")]
    return required


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown or retired override axes: {sorted(unknown)}")
    for name, value in overrides.items():
        if value is not None and type(value) is not int:
            raise ValueError(f"{name} must be an integer")
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    core, phase = schedule_profile(seed, sample_index, difficulty)
    favored = (9, 10) if difficulty == "easy" else ((13, 14) if difficulty == "hard" else ())
    h = _draw_axis(ctx, "grid_h", 9, 14, 9 if core else None, favored)
    w = _draw_axis(ctx, "grid_w", 9, 14, 11 if core else None, favored)
    n = _draw_axis(ctx, "n_colors", 3, 5, 4 if core else 5)
    four_color_curriculum = overrides.get("n_colors") == 4
    tie_left = (sample_index // 2) % 2 == 0
    modes = ((1 if core else 2), 3, 3, 4) if four_color_curriculum else _mode_plan(n, phase)
    required = _required_rivals(modes, core)
    if four_color_curriculum:
        # An exact four-color request cannot use the broad three-way tie.
        # Use left,left,right,right tie witnesses, independently of the
        # alternating mode sets. Any four consecutive draws contain both
        # orientations for each mode set and retain a counterexample to
        # either conditional tie shortcut after any single query holdout.
        required.append("legend_rightmost_tie" if tie_left else "legend_leftmost_tie")
    rng = ctx.draw_rng("scene")
    for attempt in range(512):
        g = full_grid(h, w, 0)
        g[2] = [9] * w
        palette = ([2, 3, 4] if n == 3 else list(range(1, n + 1))) if core else rng.sample(range(1, 9), n)
        rng.shuffle(palette)
        legend_columns = rng.sample(range(w), n)
        if four_color_curriculum:
            high, low = (1, 2) if palette[1] > palette[2] else (2, 1)
            if (legend_columns[high] < legend_columns[low]) != tie_left:
                legend_columns[high], legend_columns[low] = legend_columns[low], legend_columns[high]
        placed = True
        for color, mode, column in zip(palette, modes, legend_columns):
            g[0][column], g[1][column] = color, mode
            for placement in range(128):
                points = _motif(rng, h - 3, w, core)
                if all(g[r][c] == 0 for r, c in points):
                    for r, c in points:
                        g[r][c] = color
                    break
            else:
                placed = False
                break
        if not placed:
            continue
        # Background distractors of an existing color are lawful seeds, never
        # unlabelled noise. More are attempted in hard scenes; acceptance checks
        # whether their interactions preserve the required visible evidence.
        for color in palette:
            if not core and rng.randrange(4) < (2 if difficulty == "hard" else 1):
                empty = [(r, c) for r in range(3, h) for c in range(w) if g[r][c] == 0]
                if empty:
                    r, c = rng.choice(empty)
                    g[r][c] = color
        intended = diagnostic_output(g)
        if all(diagnostic_output(g, name) != intended for name in required):
            return g
    raise RuntimeError(f"could not retain visible teaching witnesses in 512 attempts: {h}x{w}, n_colors={n}, phase={phase}")


def observe_overrides(grid):
    return {"grid_h": len(grid), "grid_w": len(grid[0]),
            "n_colors": len({color for row in grid[3:] for color in row} - {0})}


def self_check(grid, *, difficulty=None, meta=None):
    # This validates the TASK domain, including the sparse canonical examples
    # and one-color diagnostic witnesses, not only our teaching sampler.
    if not isinstance(grid, (list, tuple)) or len(grid) < 4:
        return ["expected at least four rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected nonempty rectangular rows"]
    w = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != w for row in grid):
        return ["ragged grid"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be integer colors 0..9"]
    separators = [r for r, row in enumerate(grid) if all(value == 9 for value in row)]
    if separators != [2]:
        return ["expected exactly one full color-9 divider at row 2"]
    errors = []
    colors = []
    for c, color in enumerate(grid[0]):
        mode = grid[1][c]
        if not color:
            if mode:
                errors.append("mode without a legend color")
        elif not 1 <= color <= 8 or mode not in (1, 2, 3, 4):
            errors.append("legend colors must be 1..8 and modes 1..4")
        else:
            colors.append(color)
    if not colors or len(colors) != len(set(colors)):
        errors.append("legend colors must be nonempty and distinct")
    body_colors = {value for row in grid[3:] for value in row} - {0}
    if body_colors != set(colors):
        errors.append("body colors must equal the legend colors")
    return errors


def strict_canonical_like(grid):
    return self_check(grid)
