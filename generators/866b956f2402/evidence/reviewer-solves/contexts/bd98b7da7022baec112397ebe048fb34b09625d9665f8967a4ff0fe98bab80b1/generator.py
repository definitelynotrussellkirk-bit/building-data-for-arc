"""Order-preserving gravity in cyan-walled column segments.

The Racket rule, including wall-free columns and bottom tails, is unchanged.
The validator describes a useful teaching subset, not the entire rule domain.
Default lessons use five demonstrations: six consecutive draws repeat each of
three profiles twice. Complementary extension profiles break accidental feature
correlations across seeds while retaining a canonical anchor in every cycle.
"""
from __future__ import annotations

from functools import partial
from puzzle_generators.base import gen_ctx, stable_rng
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = TASK_ID = "866b956f2402"
VERSION = "2.2.0"
RULE_HASH = "7cf1bdb14040"
SUMMARY = "Stable downward gravity in each segment separated by fixed color-8 walls."
INVARIANTS = [
    "0 is background; color 8 alone is an immovable wall.",
    "Columns and wall-separated segments act independently, including bottom tails.",
    "Nonzero pebble order is preserved; useful teaching inputs contain motion.",
]
AXES = {
    "grid_h": {"type": "int", "default": "profile and difficulty", "valid": "8..24"},
    "grid_w": {"type": "int", "default": "profile and difficulty", "valid": "7..24"},
    "texture": {"type": "str", "default": "period-three profile", "valid": "canonical|contrast"},
}
HELPFUL_TEXTURES = ("canonical", "contrast")
DEGENERATE_TEXTURES = ("no_walls", "no_pebbles", "all_at_bottom")
EXAMPLES_NEEDED = 5
LESSON_SCHEDULE_PERIOD = 3
SCHEDULE_PROFILES = ("canonical", "contrast_a", "contrast_b")
MIN_STRICT_FRAC = 0.25
CANONICAL_SHAPES = ((8, 9), (9, 8), (9, 9), (10, 7), (10, 8))
EXTENSIONS = ("wall_free", "color_one", "many_walls", "many_columns", "many_pebbles")


def schedule_profile(seed, sample_index, difficulty=None):
    return SCHEDULE_PROFILES[sample_index % LESSON_SCHEDULE_PERIOD]


def _profile_settings(seed, profile):
    # This RNG deliberately excludes sample_index: paired profiles repeat their
    # semantic failure signatures, while grid geometry still varies per draw.
    rng = stable_rng(seed, "extension-allocation", VERSION)
    assignments = {name: rng.choice((1, 2)) for name in EXTENSIONS}
    counts = {"columns": rng.randint(4, 7), "pebbles": rng.randint(4, 6)}
    flags = {name: profile != 0 and assignments[name] == profile for name in EXTENSIONS}
    return flags, counts


def _segments(column, barriers=(8,)):
    start = 0
    for end in range(len(column) + 1):
        if end == len(column) or column[end] in barriers:
            yield start, end
            start = end + 1


def _has_wall_free_pebbles(grid):
    return any(8 not in col and any(v != 0 for v in col) for col in zip(*grid))


def _gravity(grid, *, mode="down", limit=None):
    """Deterministic local semantic model and explicitly named wrong variants.

    This labels no production data; public generation always uses Racket.
    The model and witness claims are independently checked against Racket.
    """
    out = [list(row) for row in grid]
    if mode == "identity":
        return out
    h, w = len(grid), len(grid[0])
    has_one = any(1 in row for row in grid)
    has_free = _has_wall_free_pebbles(grid)
    active = [c for c in range(w) if any(grid[r][c] != 0 for r in range(h))]
    barriers = (8, 1) if mode == "one_is_wall" or (mode == "one_needs_free_column" and not has_free) else (8,)
    if mode == "wrong_wall_five":
        barriers = (5,)
    if mode == "ignore_walls":
        barriers = ()
    for c in range(w):
        col = [row[c] for row in grid]
        wall_count = col.count(8)
        if mode == "column_cap" and c not in active[:limit]:
            continue
        if mode == "wall_cap" and wall_count > limit:
            continue
        if mode == "interior_only" and c in (0, w - 1):
            continue
        skip_free = mode == "skip_free" or (mode == "free_needs_one" and not has_one)
        skip_free = skip_free or (mode == "free_needs_many_columns" and len(active) <= 3)
        if skip_free and wall_count == 0:
            continue
        for number, (start, end) in enumerate(_segments(col, barriers)):
            if mode == "segment_cap" and number >= limit:
                continue
            if mode == "skip_tail" and end == h:
                continue
            values = [v for v in col[start:end] if v != 0 and v not in barriers]
            if mode == "pebble_cap" and len(values) > limit:
                continue
            if mode == "one_step":
                for r in range(end - 2, start - 1, -1):
                    if out[r][c] != 0 and out[r + 1][c] == 0:
                        out[r + 1][c], out[r][c] = out[r][c], 0
                continue
            if mode == "reverse":
                values.reverse()
            elif mode == "ascending":
                values.sort()
            elif mode == "descending":
                values.sort(reverse=True)
            elif mode == "adaptive_direction_sort" and len(values) >= 2:
                values.sort(reverse=values[0] > values[1])
            for r in range(start, end):
                out[r][c] = 0
            offset = start if mode == "up" else end - len(values)
            for r, value in enumerate(values, offset):
                out[r][c] = value
    return out


def self_check(grid, *, difficulty=None, meta=None):
    """A useful teaching grammar; no-op and wall-free *whole grids* are excluded.

    A populated wall-free column alongside a wall is accepted. Excluded whole
    grids still have perfectly defined Racket outputs and are retained as probes.
    """
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["empty or non-grid input"]
    if not all(isinstance(row, (list, tuple)) and row for row in grid):
        return ["empty or non-row input"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    if not (2 <= h <= 30 and 2 <= w <= 30):
        return ["teaching grids require 2..30 rows and columns"]
    values = [v for row in grid for v in row]
    if any(type(v) is not int or not 0 <= v <= 9 for v in values):
        return ["cells must be integer ARC colors 0..9, not booleans"]
    if 0 not in values:
        return ["no background space"]
    if 8 not in values:
        return ["teaching examples require at least one color-8 wall"]
    if sum(v not in (0, 8) for v in values) < 2:
        return ["teaching examples require at least two pebbles"]
    if _gravity(grid) == [list(row) for row in grid]:
        return ["no observable gravity motion"]
    return []


def strict_canonical_like(grid):
    reasons = self_check(grid)
    if reasons:
        return reasons
    if (len(grid), len(grid[0])) not in CANONICAL_SHAPES:
        return ["outside the observed canonical shape profiles"]
    palette = {v for row in grid for v in row}
    if len(palette) != 8 or 1 in palette:
        return ["canonical anchor has six pebble colors excluding 1, plus 0 and 8"]
    columns = [list(col) for col in zip(*grid) if any(col)]
    if len(columns) != 3:
        return ["canonical anchor has three occupied columns"]
    for col in columns:
        if col.count(8) not in (1, 2) or col[0] == 8 or col[-1] == 8:
            return ["canonical walls are one or two internal cells per occupied column"]
        if any(sum(v != 0 for v in col[start:end]) > 2 for start, end in _segments(col)):
            return ["canonical anchor has at most two pebbles per segment"]
    return []


def _positions(rng, start, end, count, min_drop=1):
    if count <= 0 or end <= start:
        return []
    if end - start <= count:
        return list(range(start, end))
    # At least the first pebble has the requested movement distance.
    latest_first = end - count - min_drop
    first = rng.randint(start, max(start, latest_first))
    rest = rng.sample(range(first + 1, end - 1), count - 1)
    return sorted([first] + rest)


def _standard_walls(rng, h, *, long_top=False):
    lower = 4 if long_top else 3
    if rng.randrange(2) == 0:
        return [rng.randint(lower, h - 3)]
    first = rng.randint(lower, h - 4)
    return [first, rng.randint(first + 2, h - 2)]


def _draw(ctx, h, w, canonical, flags, counts, difficulty):
    rng = ctx.draw_rng("layout")
    n_active = counts["columns"] if flags["many_columns"] else 3
    if canonical:
        # Two neighboring cells must fall independently, and one occupied
        # column touches a border. Repeating this anchor twice closes the
        # measured rigid-object and interior-only lesson shortcuts.
        long_col = rng.choice((0, w - 1))
        free_col = 1 if long_col == 0 else w - 2
        many_col = rng.choice([c for c in range(w) if c not in (long_col, free_col)])
        columns = [long_col, many_col, free_col]
        long_stop = rng.randint(3, h - 4)
        free_stop = rng.randint(long_stop + 2, h - 2)
        shared_row = rng.randint(1, long_stop - 2)
    else:
        columns = rng.sample(range(w), n_active)
        long_col, many_col, free_col = columns[:3]
    wall_map = {}
    for c in columns:
        if canonical and c in (long_col, free_col):
            first = long_stop if c == long_col else free_stop
            walls = [first]
            if first + 2 <= h - 2 and rng.randrange(2):
                walls.append(rng.randint(first + 2, h - 2))
        elif not canonical and c == long_col:
            walls = [h - 1]
        elif flags["many_walls"] and c == many_col:
            walls = [0, 2, 3, h - 3]
        elif flags["wall_free"] and c == free_col:
            walls = []
        else:
            walls = _standard_walls(rng, h, long_top=(c == free_col))
        wall_map[c] = walls

    grid = full_grid(h, w, 0)
    slots = []
    role_pairs = {}
    for c in columns:
        for r in wall_map[c]:
            grid[r][c] = 8
        col = [grid[r][c] for r in range(h)]
        for part, (start, end) in enumerate(_segments(col)):
            length = end - start
            if not length:
                continue
            if c == long_col and part == 0:
                count = counts["pebbles"] if flags["many_pebbles"] else 2
            elif c == free_col and part == 0:
                count = 2
            elif canonical and part == 0:
                count = 2
            else:
                cap = min(2, max(1, length - 1))
                count = rng.randint(1, cap)
            count = min(count, length)
            drop = 2 if c == free_col and part == 0 else 1
            positions = _positions(rng, start, end, count, min_drop=drop)
            if canonical and part == 0 and c == long_col:
                positions = [shared_row - 1, shared_row]
            elif canonical and part == 0 and c == free_col:
                positions = [shared_row, shared_row + 1]
            coordinates = [(r, c) for r in positions]
            slots.extend(coordinates)
            if c in (long_col, free_col) and part == 0:
                role_pairs[c] = coordinates[:3] if c == long_col and flags["many_pebbles"] else coordinates[:2]

    palette_rng = ctx.draw_rng("palette")
    n_colors = 6 if canonical else palette_rng.randint(3, min(8, len(slots) - 2))
    pool = [2, 3, 4, 5, 6, 7, 9]
    if flags["color_one"]:
        palette = [1] + palette_rng.sample(pool, n_colors - 1)
    else:
        n_colors = min(n_colors, len(pool))
        palette = palette_rng.sample(pool, n_colors)
    a, b, c = sorted(palette)[:3]
    # Long stacks preserve a nonmonotone triple in both copies of their profile.
    # This refutes a per-segment sort direction chosen from its first two colors.
    long_prefix = (a, c, b) if flags["many_pebbles"] else (a, b)
    locked = dict(zip(role_pairs[long_col], long_prefix))
    locked.update(zip(role_pairs[free_col], (b, a)))
    # Locked cells use exactly two duplicate colors in either branch, preserving
    # the palette-capacity bound. Color 1 remains in a moving role when enabled.
    remaining = [point for point in slots if point not in locked]
    palette_rng.shuffle(remaining)
    rest_colors = [color for color in palette if color not in locked.values()]
    values = rest_colors + [palette_rng.choice(palette) for _ in range(len(remaining) - len(rest_colors))]
    for (r, c), color in locked.items():
        grid[r][c] = color
    for (r, c), color in zip(remaining, values):
        grid[r][c] = color
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError("unknown or retired override(s): " + ", ".join(sorted(unknown)))
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be easy, medium, hard, or None")
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    profile = sample_index % LESSON_SCHEDULE_PERIOD
    default_texture = "canonical" if profile == 0 else "contrast"
    choices = HELPFUL_TEXTURES + DEGENERATE_TEXTURES if overrides.get("texture") is not None else (default_texture,)
    texture = ctx.draw_choice("texture", choices)
    canonical = texture == "canonical"
    flags, counts = _profile_settings(seed, profile)
    if canonical:
        flags = dict.fromkeys(EXTENSIONS, False)
    elif overrides.get("texture") == "contrast":
        flags = dict.fromkeys(EXTENSIONS, True)
    if canonical:
        wanted_h, wanted_w = ctx.draw_choice("canonical_shape", CANONICAL_SHAPES)
    else:
        ranges = {"easy": (8, 12, 7, 10), "medium": (10, 17, 8, 14),
                  "hard": (12, 24, 9, 19)}
        hlo, hhi, wlo, whi = ranges[difficulty or "medium"]
        size_rng = ctx.draw_rng("shape")
        wanted_h, wanted_w = size_rng.randint(hlo, hhi), size_rng.randint(wlo, whi)
    h = ctx.draw_int_strict("grid_h", 8, 24) if overrides.get("grid_h") is not None else ctx.draw_int_strict("grid_h", wanted_h, wanted_h)
    w = ctx.draw_int_strict("grid_w", 7, 24) if overrides.get("grid_w") is not None else ctx.draw_int_strict("grid_w", wanted_w, wanted_w)
    grid = _draw(ctx, h, w, canonical, flags, counts, difficulty)
    if texture == "no_walls":
        return [[0 if v == 8 else v for v in row] for row in grid]
    if texture == "no_pebbles":
        return [[v if v == 8 else 0 for v in row] for row in grid]
    if texture == "all_at_bottom":
        return _gravity(grid)
    return grid


def _rigid_horizontal_runs(grid):
    h,w = len(grid),len(grid[0])
    walls = {(r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v==8}
    runs = []
    for r,row in enumerate(grid):
        c = 0
        while c < w:
            color = row[c]
            if color in (0,8):
                c += 1
                continue
            end = c+1
            while end < w and row[end] == color:
                end += 1
            runs.append([color,{(r,cc) for cc in range(c,end)}])
            c = end
    moved = True
    while moved:
        moved = False
        runs.sort(key=lambda obj:(-max(r for r,c in obj[1]),min(c for r,c in obj[1])))
        for obj in runs:
            occupied = walls | set().union(*(other[1] for other in runs if other is not obj))
            while all(r+1<h and (r+1,c) not in occupied for r,c in obj[1]):
                obj[1] = {(r+1,c) for r,c in obj[1]}
                moved = True
    out = [[0]*w for _ in range(h)]
    for r,c in walls:
        out[r][c] = 8
    for color,cells in runs:
        for r,c in cells:
            out[r][c] = color
    return out


SEMANTIC_RIVALS = {
    "rigid_horizontal_runs": _rigid_horizontal_runs,
    "adaptive_direction_sort": partial(_gravity, mode="adaptive_direction_sort"),
    "identity": partial(_gravity, mode="identity"),
    "gravity_up": partial(_gravity, mode="up"),
    "one_step_only": partial(_gravity, mode="one_step"),
    "reverse_pebble_order": partial(_gravity, mode="reverse"),
    "sort_colors_ascending": partial(_gravity, mode="ascending"),
    "sort_colors_descending": partial(_gravity, mode="descending"),
    "ignore_walls": partial(_gravity, mode="ignore_walls"),
    "five_is_wall": partial(_gravity, mode="wrong_wall_five"),
    "one_is_wall": partial(_gravity, mode="one_is_wall"),
    "wall_free_passthrough": partial(_gravity, mode="skip_free"),
    "bottom_tail_passthrough": partial(_gravity, mode="skip_tail"),
    "interior_columns_only": partial(_gravity, mode="interior_only"),
    "at_most_two_walls": partial(_gravity, mode="wall_cap", limit=2),
    "at_most_three_segments": partial(_gravity, mode="segment_cap", limit=3),
    "at_most_two_pebbles": partial(_gravity, mode="pebble_cap", limit=2),
    "at_most_three_pebbles": partial(_gravity, mode="pebble_cap", limit=3),
    "first_three_columns": partial(_gravity, mode="column_cap", limit=3),
    "first_four_columns": partial(_gravity, mode="column_cap", limit=4),
    "first_five_columns": partial(_gravity, mode="column_cap", limit=5),
    "first_six_columns": partial(_gravity, mode="column_cap", limit=6),
    "wall_free_requires_one": partial(_gravity, mode="free_needs_one"),
    "one_requires_wall_free": partial(_gravity, mode="one_needs_free_column"),
    "wall_free_requires_many_columns": partial(_gravity, mode="free_needs_many_columns"),
}
_CANONICAL_FITTING_NAMES = (
    "rigid_horizontal_runs", "adaptive_direction_sort",
    "one_is_wall", "wall_free_passthrough", "at_most_two_walls",
    "at_most_three_segments", "at_most_two_pebbles", "at_most_three_pebbles",
    "first_three_columns", "first_four_columns", "first_five_columns",
    "first_six_columns", "wall_free_requires_one", "one_requires_wall_free",
    "wall_free_requires_many_columns",
)
CANONICAL_SHORTCUTS = {name: SEMANTIC_RIVALS[name] for name in _CANONICAL_FITTING_NAMES}
LESSON_COMPETITORS = {name: rival for name, rival in SEMANTIC_RIVALS.items()
                      if name not in CANONICAL_SHORTCUTS}


def _refutes(grid, rival):
    return _gravity(grid) != rival(grid)


SEMANTIC_WITNESSES = {name: partial(_refutes, rival=rival)
                      for name, rival in SEMANTIC_RIVALS.items()}
WITNESS_RIVALS = {name: [name] for name in SEMANTIC_RIVALS}


def lesson_identifiable(demos, query):
    """Finite-bank query agreement, not a universal uniqueness assertion."""
    if not demos:
        return ["no demonstrations"]
    reasons = []
    for name, rival in SEMANTIC_RIVALS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            if rival(query["input"]) != query["output"]:
                reasons.append("demonstrations leave rival " + name + " ambiguous")
    return reasons
