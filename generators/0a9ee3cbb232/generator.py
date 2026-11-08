"""Generator for ARC task 5289ad53 / 0a9ee3cbb232.

Count maximal horizontal runs of color 3 and color 2 independently.  Write the
counts into a 2x3 row-major tally: all 3 cells first, then 2 cells, then zero
padding.  The six output cells naturally truncate an overfull tally.

The curriculum deliberately separates this rule from three shortcuts that fit
all public examples: counting 4-connected components, counting occupied rows,
and discarding color-2 runs when the six-cell tally overflows.
"""
from __future__ import annotations

from collections import deque
from copy import deepcopy

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "0a9ee3cbb232"
TASK_ID = GENERATOR_ID
VERSION = "4.0.1"
RULE_HASH = "54a0bdf9c500"
SUMMARY = (
    "Count maximal horizontal runs of 3 and 2 into a 2x3 row-major tally. "
    "Canonical-profile canvases vary the background; every default draw "
    "contains a multi-row connected run object and two same-color runs in one "
    "row, while alternating draws overflow the six-cell tally."
)
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0
EXPECTED_OUTPUT_CODOMAIN = 10

_CANVAS_PROFILES = ((10, 14), (10, 10), (13, 15), (10, 19), (15, 10))
_BACKGROUNDS = (0, 1, 4, 5, 6, 7, 8, 9)
_BOUNDED_COUNTS = (
    (1, 4), (1, 5), (2, 2), (2, 3), (2, 4),
    (3, 2), (3, 3), (4, 1), (4, 2), (5, 1),
)
_OVERFLOW_COUNTS = (
    (4, 3), (5, 2), (4, 4), (5, 3), (4, 5), (5, 4),
)

SCHEDULE_PROFILES = ("bounded", "overflow")
_DIFFICULTIES = {None, "easy", "medium", "hard"}

AXES = {
    "canvas_profile": {
        "type": "int",
        "default": "scheduled canonical profile",
        "valid": "0..4",
        "doc": "0:10x14, 1:10x10, 2:13x15, 3:10x19, 4:15x10",
    },
    "n_3": {
        "type": "int",
        "default": "scheduled 2..5",
        "valid": "1..6",
        "doc": "exact number of maximal horizontal color-3 runs",
    },
    "n_2": {
        "type": "int",
        "default": "scheduled 2..5",
        "valid": "1..6",
        "doc": "exact number of maximal horizontal color-2 runs",
    },
    "background": {
        "type": "int",
        "default": "scheduled non-2/non-3 ARC color",
        "valid": "0|1|4|5|6|7|8|9",
        "doc": "exact modal background color",
    },
}

# Every advertised Cartesian combination is constructive.
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []

INVARIANTS = [
    "input dimensions equal one canonical (height,width) profile",
    "input palette is exactly {background,2,3}",
    "every counted horizontal run has length at least two",
    "n_3 and n_2 are exact and each lie in 1..6",
    "default lessons refute component-counting and occupied-row shortcuts",
]


def schedule_profile(seed, sample_index, difficulty=None):
    """Alternating schedule; every three consecutive examples include overflow."""
    del seed, difficulty
    return SCHEDULE_PROFILES[sample_index % len(SCHEDULE_PROFILES)]


def _tally(n3, n2):
    out = [[0] * 3 for _ in range(2)]
    for index in range(6):
        if index < n3:
            out[index // 3][index % 3] = 3
        elif index < n3 + n2:
            out[index // 3][index % 3] = 2
    return out


def _horizontal_run_lengths(grid, color):
    lengths = []
    for row in grid:
        length = 0
        for value in row:
            if value == color:
                length += 1
            elif length:
                lengths.append(length)
                length = 0
        if length:
            lengths.append(length)
    return lengths


def _run_counts(grid):
    return tuple(len(_horizontal_run_lengths(grid, color)) for color in (3, 2))


def _mirror(grid):
    """Independent Python mirror of the pinned Racket authority."""
    return _tally(*_run_counts(grid))


def _draw_scheduled(ctx, label, default, domain):
    """Record a deterministic scheduled default while keeping all overrides exact."""
    overridden = label in ctx.overrides and ctx.overrides[label] is not None
    return ctx.draw_choice(label, domain if overridden else (default,))


def _validate_overrides(overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    domains = {
        "canvas_profile": set(range(len(_CANVAS_PROFILES))),
        "n_3": set(range(1, 7)),
        "n_2": set(range(1, 7)),
        "background": set(_BACKGROUNDS),
    }
    for name, value in overrides.items():
        if value is None:
            continue
        if type(value) is not int:
            raise TypeError(f"{name} must be an integer, not {type(value).__name__}")
        if value not in domains[name]:
            raise ValueError(
                f"{name}={value!r} outside declared domain {sorted(domains[name])}"
            )


def _validate_request(seed, sample_index, difficulty, overrides):
    """Reject coercible or out-of-domain public controls before drawing."""
    if type(seed) is not int:
        raise TypeError(f"seed must be an integer, not {type(seed).__name__}")
    if type(sample_index) is not int:
        raise TypeError(
            f"sample_index must be an integer, not {type(sample_index).__name__}"
        )
    if sample_index < 0:
        raise ValueError("sample_index must be nonnegative")
    if difficulty not in _DIFFICULTIES:
        raise ValueError(
            "difficulty must be None, 'easy', 'medium', or 'hard'"
        )
    _validate_overrides(overrides)


def _run_length(difficulty, zone_width, rng):
    requested = {"easy": 2, "medium": 3, "hard": 4}.get(difficulty)
    if requested is None:
        requested = rng.randint(2, min(4, zone_width))
    return min(requested, zone_width)


def _put_run(grid, row, zone, color, difficulty, rng):
    lo, hi = zone
    length = _run_length(difficulty, hi - lo + 1, rng)
    start = rng.randint(lo, hi - length + 1)
    for column in range(start, start + length):
        grid[row][column] = color
    return start, length


def _put_rectangle(grid, rows, zone, color, difficulty, rng):
    lo, hi = zone
    length = _run_length(difficulty, hi - lo + 1, rng)
    start = rng.randint(lo, hi - length + 1)
    for row in rows:
        for column in range(start, start + length):
            grid[row][column] = color
    return start, length


def _construct_grid(h, w, background, n3, n2, difficulty, rng):
    """Construct exact run counts without rejection or lossy fallback.

    Two horizontally separated slots per row give at least 20 run slots on the
    smallest 10x10 canvas.  A two-row rectangle supplies the component-count
    counterexample; two slots of one row supply the occupied-row counterexample.
    Remaining runs use at most one slot per color per row.
    """
    grid = full_grid(h, w, background)
    split = w // 2
    zones = ((0, split - 1), (split + 1, w - 1))
    if min(hi - lo + 1 for lo, hi in zones) < 2:
        raise RuntimeError("canvas profile cannot hold two separated run slots")

    totals = {3: n3, 2: n2}
    remaining = dict(totals)
    used_rows = {3: set(), 2: set()}
    occupied = set()

    # Prefer color 3 for the multi-row object.  Low-count exact overrides may
    # move it to color 2 or lawfully omit this optional teaching structure.
    object_color = 3 if remaining[3] >= 2 else (2 if remaining[2] >= 2 else None)
    if object_color is not None:
        start_row = rng.randint(0, h - 2)
        rows = (start_row, start_row + 1)
        _put_rectangle(grid, rows, zones[0], object_color, difficulty, rng)
        for row in rows:
            occupied.add((row, 0))
            used_rows[object_color].add(row)
        remaining[object_color] -= 2

    # Prefer the other color for the same-row split.  If an exact override has
    # only one viable color, use that color only when two unallocated runs remain.
    preferred = 2 if object_color == 3 else 3
    same_color = None
    # When the tally overflows, a lower color-2 count can be hidden behind the
    # already-filled prefix.  Put both structural counterexamples on color 3
    # whenever it has four runs, so each wrong shortcut changes a visible cell.
    if n3 + n2 > 6 and object_color == 3 and remaining[3] >= 2:
        same_color = 3
    elif remaining[preferred] >= 2:
        same_color = preferred
    elif object_color is not None and remaining[object_color] >= 2:
        same_color = object_color
    elif remaining[3] >= 2:
        same_color = 3
    elif remaining[2] >= 2:
        same_color = 2
    if same_color is not None:
        rows = [
            row for row in range(h)
            if row not in used_rows[same_color]
            and (row, 0) not in occupied
            and (row, 1) not in occupied
        ]
        if not rows:
            raise RuntimeError("no row available for same-row witness")
        row = rng.choice(rows)
        _put_run(grid, row, zones[0], same_color, difficulty, rng)
        _put_run(grid, row, zones[1], same_color, difficulty, rng)
        occupied.update(((row, 0), (row, 1)))
        used_rows[same_color].add(row)
        remaining[same_color] -= 2

    # Each ordinary run uses a new row for its own color.  Different colors may
    # share a row in opposite slots, which broadens layouts without changing
    # either exact horizontal count.
    for color in (3, 2):
        for _ in range(remaining[color]):
            candidates = []
            for row in range(h):
                if row in used_rows[color]:
                    continue
                free = [zone_index for zone_index in (0, 1)
                        if (row, zone_index) not in occupied]
                if free:
                    candidates.append((row, free))
            if not candidates:
                raise RuntimeError(
                    f"constructive slot exhaustion for color {color}: "
                    f"target={totals[color]}"
                )
            row, free = rng.choice(candidates)
            zone_index = rng.choice(free)
            _put_run(grid, row, zones[zone_index], color, difficulty, rng)
            occupied.add((row, zone_index))
            used_rows[color].add(row)

    actual = _run_counts(grid)
    if actual != (n3, n2):
        raise RuntimeError(
            f"constructive run mismatch: requested {(n3, n2)}, realized {actual}"
        )
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_request(seed, sample_index, difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    profile_default = sample_index % len(_CANVAS_PROFILES)
    profile = _draw_scheduled(
        ctx, "canvas_profile", profile_default, tuple(range(len(_CANVAS_PROFILES)))
    )
    h, w = _CANVAS_PROFILES[profile]

    curriculum = schedule_profile(seed, sample_index, difficulty)
    pairs = _OVERFLOW_COUNTS if curriculum == "overflow" else _BOUNDED_COUNTS
    pair_default = pairs[ctx.draw_rng("count_schedule").randrange(len(pairs))]
    n3 = _draw_scheduled(ctx, "n_3", pair_default[0], tuple(range(1, 7)))
    n2 = _draw_scheduled(ctx, "n_2", pair_default[1], tuple(range(1, 7)))
    background_default = _BACKGROUNDS[sample_index % len(_BACKGROUNDS)]
    background = _draw_scheduled(
        ctx, "background", background_default, _BACKGROUNDS
    )

    grid = _construct_grid(
        h, w, background, n3, n2, difficulty, ctx.draw_rng("layout")
    )
    issues = self_check(grid, difficulty=difficulty)
    if issues:
        raise RuntimeError("constructive self-check failed: " + "; ".join(issues))
    return grid


def self_check(grid, *, difficulty=None, meta=None):
    """Validate the declared sampler manifold; return diagnostics, never raise."""
    del difficulty, meta
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty rectangular grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected nonempty rows"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["ragged grid"]
    if any(type(value) is not int or not 0 <= value <= 9
           for row in grid for value in row):
        return ["cells must be integer ARC colors 0..9 (bool is not a color)"]

    issues = []
    shape = (len(grid), width)
    if shape not in _CANVAS_PROFILES:
        issues.append(f"canvas {shape} is not one of {_CANVAS_PROFILES}")

    palette = {value for row in grid for value in row}
    background_colors = palette - {2, 3}
    if len(background_colors) != 1 or 2 not in palette or 3 not in palette:
        issues.append("palette must be exactly one background plus colors 2 and 3")
        return issues
    background = next(iter(background_colors))
    counts = {value: sum(cell == value for row in grid for cell in row)
              for value in palette}
    if not all(counts[background] > counts[color] for color in (2, 3)):
        issues.append("the unique non-2/non-3 color must be the strict modal background")

    for color in (3, 2):
        lengths = _horizontal_run_lengths(grid, color)
        if not 1 <= len(lengths) <= 6:
            issues.append(f"color {color} has {len(lengths)} runs, expected 1..6")
        if any(length < 2 for length in lengths):
            issues.append(f"color {color} contains a singleton horizontal run")
    return issues


def strict_canonical_like(grid):
    return self_check(grid)


def observe_overrides(grid):
    issues = self_check(grid)
    if issues:
        raise ValueError("cannot observe malformed grid: " + "; ".join(issues))
    palette = {value for row in grid for value in row}
    background = next(iter(palette - {2, 3}))
    n3, n2 = _run_counts(grid)
    return {
        "canvas_profile": _CANVAS_PROFILES.index((len(grid), len(grid[0]))),
        "n_3": n3,
        "n_2": n2,
        "background": background,
    }


def _component_count(grid, color):
    h, w = len(grid), len(grid[0])
    remaining = {
        (row, column)
        for row, values in enumerate(grid)
        for column, value in enumerate(values)
        if value == color
    }
    count = 0
    while remaining:
        count += 1
        queue = deque([remaining.pop()])
        while queue:
            row, column = queue.popleft()
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                point = (row + dr, column + dc)
                if 0 <= point[0] < h and 0 <= point[1] < w and point in remaining:
                    remaining.remove(point)
                    queue.append(point)
    return count


def _connected_components_rival(grid):
    """Wrong shortcut: count 4-connected objects instead of horizontal runs."""
    return _tally(_component_count(grid, 3), _component_count(grid, 2))


def _occupied_rows_rival(grid):
    """Wrong shortcut: at most one count per color per occupied row."""
    return _tally(
        sum(any(value == 3 for value in row) for row in grid),
        sum(any(value == 2 for value in row) for row in grid),
    )


def _drop_twos_on_overflow_rival(grid):
    """Wrong shortcut: discard color-2 counts rather than truncate sequentially."""
    n3, n2 = _run_counts(grid)
    return _tally(n3, 0 if n3 + n2 > 6 else n2)


def _refutes(rule):
    def witness(grid):
        try:
            return rule(deepcopy(grid)) != _mirror(grid)
        except Exception:
            return False
    return witness


SEMANTIC_RIVALS = {
    "connected_components": _connected_components_rival,
    "occupied_rows": _occupied_rows_rival,
    "drop_twos_on_overflow": _drop_twos_on_overflow_rival,
}
SEMANTIC_WITNESSES = {
    "multirow_component": _refutes(_connected_components_rival),
    "multiple_runs_same_row": _refutes(_occupied_rows_rival),
    "overflow_truncation": _refutes(_drop_twos_on_overflow_rival),
}
WITNESS_RIVALS = {
    "multirow_component": ["connected_components"],
    "multiple_runs_same_row": ["occupied_rows"],
    "overflow_truncation": ["drop_twos_on_overflow"],
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query):
    """Name any declared rival that fits all demos but changes the query."""
    reasons = []
    for name, rival in sorted(LESSON_COMPETITORS.items()):
        try:
            fits = all(rival(demo["input"]) == demo["output"] for demo in demos)
            changes_query = rival(query["input"]) != query["output"]
        except Exception as exc:
            reasons.append(f"{name} could not be evaluated: {type(exc).__name__}: {exc}")
            continue
        if fits and changes_query:
            reasons.append(f"{name} fits every demonstration but changes the query")
    return reasons
