"""Input sampler for ARC task 3065bdeaa7b0: row-first L connectors.

The unchanged canonical authority connects every color occurring exactly twice.
For each qualifying color it lexicographically orders the endpoints, paints the
horizontal leg from the first endpoint to the second endpoint's column, then
paints the vertical leg to the second endpoint. Pair records are processed in
first-endpoint order, so a later pair owns an intersection. Colors occurring a
non-pair number of times are ignored by the transformation.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "3065bdeaa7b0"
TASK_ID = GENERATOR_ID
RULE_HASH = "1bc66fae4078"
VERSION = "3.1.0"
SUMMARY = (
    "A 9..18 rectangular zero-background grid contains 1..4 distinct colors "
    "that occur exactly twice. The two cells of every such color are offset "
    "in both row and column. The rule lexicographically orders each pair, "
    "draws a horizontal-then-vertical L path in that color, and processes "
    "pairs by their first endpoint so later paths overwrite intersections. "
    "Zero to two additional colors occur exactly three times and are lawful "
    "distractors: because they are not exact pairs, the rule leaves them "
    "unchanged unless a qualifying path crosses them (the sampler avoids that "
    "input ambiguity). A four-position schedule alternates canonical-scale "
    "anchors with explicit witnesses against pair-count, occurrence-count, "
    "endpoint-order, and overlap-priority shortcuts."
)

INVARIANTS = [
    "background is color 0 and every cell is an integer color 0..9",
    "1..4 active colors occur exactly twice; 0..2 other colors occur exactly three times",
    "each exact pair differs in both row and column",
    "no qualifying path passes through a foreign input marker",
    "all advertised override combinations are constructive on every difficulty band",
]

AXES = {
    "grid_h": {"type": "int", "default": "scheduled canonical or difficulty-skewed 9..18", "valid": "9..18"},
    "grid_w": {"type": "int", "default": "scheduled canonical or difficulty-skewed 9..18", "valid": "9..18"},
    "n_pairs": {"type": "int", "default": "scheduled 1..4", "valid": "1..4"},
    "n_decoys": {"type": "int", "default": "scheduled 0..2", "valid": "0..2"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []

EXAMPLES_NEEDED = 3
SCHEDULE_PROFILES = (
    "canonical_anchor",
    "pair_count",
    "one_pair_decoy",
    "combined",
)

_CANONICAL_PROFILES = ((9, 13), (10, 12), (11, 11), (12, 10))
_PAIR_LIMITS = (1, 4)
_DECOY_LIMITS = (0, 2)
_DIM_LIMITS = (9, 18)


def schedule_profile(seed, sample_index, difficulty=None):
    """Name the deterministic curriculum position used by this draw."""
    del seed, difficulty
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative integer")
    return SCHEDULE_PROFILES[sample_index % len(SCHEDULE_PROFILES)]


def _validate_overrides(overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name, value in overrides.items():
        if value is None:
            continue
        if type(value) is not int:
            raise ValueError(f"{name} must be an integer, not {type(value).__name__}")


def _scheduled_int(ctx, name, lo, hi, scheduled):
    """Record an exact axis while preserving its full explicit override range."""
    if name in ctx.overrides and ctx.overrides[name] is not None:
        return ctx.draw_int(name, lo, hi)
    return ctx.draw_int(name, scheduled, scheduled)


def _profile_axes(ctx, profile):
    if profile in {"canonical_anchor", "one_pair_decoy"}:
        shape = ctx.draw_choice("canonical_profile", _CANONICAL_PROFILES)
        h = _scheduled_int(ctx, "grid_h", *_DIM_LIMITS, shape[0])
        w = _scheduled_int(ctx, "grid_w", *_DIM_LIMITS, shape[1])
    else:
        h = ctx.draw_int_diff("grid_h", *_DIM_LIMITS)
        w = ctx.draw_int_diff("grid_w", *_DIM_LIMITS)

    defaults = {
        "canonical_anchor": (2, 0),
        "pair_count": (3, 1),
        "one_pair_decoy": (1, 1),
        "combined": (4, 2),
    }
    default_pairs, default_decoys = defaults[profile]
    n_pairs = _scheduled_int(ctx, "n_pairs", *_PAIR_LIMITS, default_pairs)
    n_decoys = _scheduled_int(ctx, "n_decoys", *_DECOY_LIMITS, default_decoys)
    return h, w, n_pairs, n_decoys


def _base_pairs(h, w):
    """Four constructive endpoint pairs for every h,w >= 9.

    The first/second and first/fourth paths intersect, later records own those
    cells, and alternating endpoint directions prevent a left-to-right shortcut.
    No pair path contains another pair's endpoint.
    """
    return [
        ((1, w - 2), (h - 2, 1)),
        ((2, 0), (h - 3, w - 3)),
        ((3, w - 1), (h - 4, 2)),
        ((4, 0), (h - 1, w - 1)),
    ]


def _reflect_horizontal(point, w):
    return point[0], w - 1 - point[1]


def _ordered_endpoints(a, b):
    return (a, b) if a < b else (b, a)


def _between(a, b):
    step = 1 if a <= b else -1
    return range(a, b + step, step)


def _path_cells(a, b):
    """Canonical row-first cells for already lexicographically ordered points."""
    return (
        [(a[0], c) for c in _between(a[1], b[1])]
        + [(r, b[1]) for r in _between(a[0], b[0])]
    )


def _spread_three(columns):
    """Pick three separated columns from a sorted lawful row domain."""
    values = sorted(columns)
    if len(values) < 3:
        raise RuntimeError("fewer than three lawful decoy cells")
    chosen = [values[0], values[len(values) // 2], values[-1]]
    if len(set(chosen)) != 3:
        raise RuntimeError("could not choose three distinct decoy cells")
    return chosen


def _place_decoys(grid, colors, pair_paths):
    h, w = len(grid), len(grid[0])
    forbidden = set().union(*pair_paths) if pair_paths else set()
    rows = (0, h - 1)
    for color, row in zip(colors, rows):
        lawful = [
            c for c in range(w)
            if (row, c) not in forbidden and grid[row][c] == 0
        ]
        for c in _spread_three(lawful):
            grid[row][c] = color


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_overrides(overrides)
    profile = schedule_profile(seed, sample_index, difficulty)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    h, w, n_pairs, n_decoys = _profile_axes(ctx, profile)
    colors = list(range(1, 10))
    ctx.draw_rng("colors").shuffle(colors)
    pair_colors = colors[:n_pairs]
    decoy_colors = colors[n_pairs:n_pairs + n_decoys]

    reflect = ctx.draw_choice("horizontal_reflection", (False, True))
    pairs = _base_pairs(h, w)[:n_pairs]
    if reflect:
        pairs = [
            (_reflect_horizontal(a, w), _reflect_horizontal(b, w))
            for a, b in pairs
        ]

    grid = full_grid(h, w, 0)
    paths = []
    for color, (a, b) in zip(pair_colors, pairs):
        grid[a[0]][a[1]] = color
        grid[b[0]][b[1]] = color
        first, second = _ordered_endpoints(a, b)
        paths.append(set(_path_cells(first, second)))
    _place_decoys(grid, decoy_colors, paths)

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise RuntimeError(f"constructive sampler violated its contract: {errors}")
    return grid


def _positions(grid):
    by_color = {}
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value:
                by_color.setdefault(value, []).append((r, c))
    return by_color


def observe_overrides(grid):
    counts = Counter(value for row in grid for value in row if value)
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_pairs": sum(count == 2 for count in counts.values()),
        "n_decoys": sum(count == 3 for count in counts.values()),
    }


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty, meta
    if (
        not isinstance(grid, (list, tuple))
        or not grid
        or not isinstance(grid[0], (list, tuple))
        or not grid[0]
    ):
        return ["expected a nonempty rectangular grid"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["ragged grid"]
    h, w = len(grid), width
    errors = []
    if not (_DIM_LIMITS[0] <= h <= _DIM_LIMITS[1] and _DIM_LIMITS[0] <= w <= _DIM_LIMITS[1]):
        errors.append(f"grid dimensions {(h, w)} outside 9..18")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        errors.append("cells must be integer ARC colors 0..9")
        return errors

    by_color = _positions(grid)
    pairs = []
    decoys = []
    for color, points in sorted(by_color.items()):
        if len(points) == 2:
            pairs.append((color, *_ordered_endpoints(points[0], points[1])))
        elif len(points) == 3:
            decoys.append((color, tuple(points)))
        else:
            errors.append(f"color {color} appears {len(points)} times; expected exactly 2 or 3")
    if not _PAIR_LIMITS[0] <= len(pairs) <= _PAIR_LIMITS[1]:
        errors.append(f"n_pairs={len(pairs)} outside 1..4")
    if not _DECOY_LIMITS[0] <= len(decoys) <= _DECOY_LIMITS[1]:
        errors.append(f"n_decoys={len(decoys)} outside 0..2")

    markers = {
        point: color
        for color, points in by_color.items()
        for point in points
    }
    for color, first, second in pairs:
        if first[0] == second[0] or first[1] == second[1]:
            errors.append(f"pair color {color} must differ in both row and column")
            continue
        for point in _path_cells(first, second):
            other = markers.get(point)
            if other is not None and other != color:
                errors.append(
                    f"pair color {color} path passes through foreign marker color {other} at {point}"
                )
                break
    return errors


def strict_canonical_like(grid):
    errors = self_check(grid)
    if errors:
        return errors
    profile = (len(grid), len(grid[0]))
    counts = Counter(value for row in grid for value in row if value)
    reasons = []
    if profile not in _CANONICAL_PROFILES:
        reasons.append(f"shape {profile} is outside canonical profiles {_CANONICAL_PROFILES}")
    if sorted(counts.values()) != [2, 2]:
        reasons.append("canonical-like inputs require exactly two exact-pair colors and no decoys")
    if len({value for row in grid for value in row}) != 3:
        reasons.append("canonical-like palette size must be 3 including background")
    return reasons


def _records(grid, *, at_least_two=False, limit=None, column_first=False):
    records = []
    for color, points in _positions(grid).items():
        eligible = len(points) >= 2 if at_least_two else len(points) == 2
        if not eligible:
            continue
        if column_first:
            first, second = sorted(points, key=lambda p: (p[1], p[0]))[:2]
        else:
            first, second = sorted(points)[:2]
        records.append((first, color, second))
    records.sort(key=lambda record: record[0])
    return records if limit is None else records[:limit]


def _paint(grid, records, *, first_writer_wins=False):
    out = deepcopy(grid)
    painted = set()
    for first, color, second in records:
        for point in _path_cells(first, second):
            if first_writer_wins and point in painted:
                continue
            out[point[0]][point[1]] = color
            painted.add(point)
    return out


def _intended(grid):
    return _paint(grid, _records(grid))


def _first_two_pairs_only(grid):
    return _paint(grid, _records(grid, limit=2))


def _first_two_occurrences_of_every_color(grid):
    return _paint(grid, _records(grid, at_least_two=True))


def _left_to_right_endpoints(grid):
    return _paint(grid, _records(grid, column_first=True))


def _first_writer_wins(grid):
    return _paint(grid, _records(grid), first_writer_wins=True)


def _more_than_two_pairs(grid):
    return observe_overrides(grid)["n_pairs"] > 2


def _ignored_nonpair_color(grid):
    return observe_overrides(grid)["n_decoys"] > 0


def _top_right_first(grid):
    return any(first[1] > second[1] for first, _, second in _records(grid))


def _path_overlap(grid):
    paths = [set(_path_cells(first, second)) for first, _, second in _records(grid)]
    seen = set()
    for path in paths:
        if seen & path:
            return True
        seen.update(path)
    return False


SEMANTIC_RIVALS = {
    "first_two_pairs_only": _first_two_pairs_only,
    "first_two_occurrences_of_every_color": _first_two_occurrences_of_every_color,
    "left_to_right_endpoints": _left_to_right_endpoints,
    "first_writer_wins": _first_writer_wins,
}
CANONICAL_SHORTCUTS = {
    "first_two_pairs_only": _first_two_pairs_only,
    "first_two_occurrences_of_every_color": _first_two_occurrences_of_every_color,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
SEMANTIC_WITNESSES = {
    "more_than_two_pairs": _more_than_two_pairs,
    "ignored_nonpair_color": _ignored_nonpair_color,
    "top_right_first": _top_right_first,
    "path_overlap": _path_overlap,
}
WITNESS_RIVALS = {
    "more_than_two_pairs": ["first_two_pairs_only"],
    "ignored_nonpair_color": ["first_two_occurrences_of_every_color"],
    "top_right_first": ["left_to_right_endpoints"],
    "path_overlap": ["first_writer_wins"],
}


def lesson_identifiable(demos, query):
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        return ["query must contain input and output grids"]
    reasons = []
    for name, rival in LESSON_COMPETITORS.items():
        try:
            fits_demos = all(
                rival(deepcopy(pair["input"])) == pair["output"]
                for pair in demos
            )
            changes_query = rival(deepcopy(query["input"])) != query["output"]
        except Exception as exc:
            reasons.append(f"competitor {name} raised {type(exc).__name__}: {exc}")
            continue
        if fits_demos and changes_query:
            reasons.append(f"competitor {name} fits every demo but changes the query answer")
    return reasons
