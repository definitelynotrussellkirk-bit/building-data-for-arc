"""Input sampler for E160: recolor each row by its column-0 header.

The selected Racket rule owns labels.  This module emits only inputs.  Every
ordinary draw is deliberately self-teaching: multiple header colors distinguish
per-row recoloring from a global color rule, every header row contains a visible
mismatch, and a payload in a headerless row demonstrates that header 0 means
"preserve" rather than "erase".
"""
from __future__ import annotations

from copy import deepcopy

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = TASK_ID = "019445e9b5a1"
RULE_HASH = "f0e910e5b6d0"
VERSION = "2.0.0"
SUMMARY = (
    "Column 0 supplies an independent color header for each row. Nonzero "
    "payload cells in a headered row take that header color; payload in a "
    "headerless row keeps its own color. Default draws contain visible "
    "mismatches in every header row plus a retained headerless payload."
)
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0
LESSON_SCHEDULE_PERIOD = 3
SCHEDULE_PROFILES = ("canonical_core", "broad", "contrast")

INVARIANTS = [
    "rectangular 4..8 by 6..12 grid with integer colors 0..9 and background 0",
    "1..3 distinct nonzero row headers in column 0 and 4..12 payload cells elsewhere",
    "every generated header row has a differently colored payload, so the rule visibly changes",
    "every generated input has a nonzero payload in a headerless row, which must remain unchanged",
]
AXES = {
    "grid_h": {"type": "int", "default": "scheduled/difficulty-weighted", "valid": "4..8"},
    "grid_w": {"type": "int", "default": "scheduled/difficulty-weighted", "valid": "6..12"},
    "n_headers": {"type": "int", "default": "2..3 (canonical core 3)", "valid": "1..3"},
    "n_payload": {"type": "int", "default": "5..10 (canonical core 7)", "valid": "4..12"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []

_HEIGHTS = tuple(range(4, 9))
_WIDTHS = tuple(range(6, 13))
_DIFFICULTIES = {None, "easy", "medium", "hard"}


def schedule_profile(seed, sample_index, difficulty=None):
    """Three-period production schedule; explicit axes still take precedence."""
    return SCHEDULE_PROFILES[sample_index % LESSON_SCHEDULE_PERIOD]


def _validate_request(difficulty, overrides):
    if difficulty not in _DIFFICULTIES:
        raise ValueError(f"difficulty must be one of easy/medium/hard/None, not {difficulty!r}")
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    bounds = {
        "grid_h": (4, 8),
        "grid_w": (6, 12),
        "n_headers": (1, 3),
        "n_payload": (4, 12),
    }
    for name, value in overrides.items():
        if value is None:
            continue
        if type(value) is not int:
            raise TypeError(f"{name} must be an integer (not bool)")
        lo, hi = bounds[name]
        if not lo <= value <= hi:
            raise ValueError(f"{name} must be in {lo}..{hi}")


def _draw_axis(ctx, overrides, name, lo, hi, default_options):
    if overrides.get(name) is not None:
        return ctx.draw_int_strict(name, lo, hi)
    return ctx.draw_choice(name, tuple(default_options))


def _shape_options(profile, difficulty):
    if profile == "canonical_core":
        return (4,), (8,)
    heights = {
        "easy": (4, 4, 5, 5, 6),
        "medium": (4, 5, 6, 6, 7),
        "hard": (4, 6, 7, 8, 8),
        None: _HEIGHTS,
    }[difficulty]
    widths = {
        "easy": (6, 7, 7, 8, 8),
        "medium": (6, 7, 8, 9, 10),
        "hard": (7, 8, 9, 10, 11, 12),
        None: _WIDTHS,
    }[difficulty]
    return heights, widths


def _count_options(profile, difficulty):
    if profile == "canonical_core":
        return (3,), (7,)
    headers = (2, 3, 3) if profile == "contrast" else (2, 2, 3)
    payload = {
        "easy": (5, 5, 6, 7),
        "medium": (5, 6, 7, 8, 9),
        "hard": (6, 7, 8, 9, 10),
        None: tuple(range(5, 11)),
    }[difficulty]
    return headers, payload


def _place_payloads(grid, header, palette, count, ctx):
    """Place exactly count payload cells while realizing all teaching witnesses."""
    h, w = len(grid), len(grid[0])
    rng = ctx.draw_rng("payload_layout")
    header_rows = sorted(header)
    headerless_rows = [row for row in range(h) if row not in header]
    non_header_colors = [color for color in palette if color not in set(header.values())]
    if not headerless_rows or not non_header_colors:
        raise RuntimeError("constructive palette/row contract unexpectedly failed")

    assignments: list[tuple[int, int, int]] = []
    used_positions: set[tuple[int, int]] = set()

    # One guaranteed visible mismatch in every header row.
    for index, row in enumerate(header_rows):
        choices = [(row, col) for col in range(1, w) if (row, col) not in used_positions]
        position = rng.choice(choices)
        used_positions.add(position)
        assignments.append((*position, non_header_colors[index % len(non_header_colors)]))

    # Header 0 is semantically meaningful: this payload must survive unchanged.
    headerless_row = rng.choice(headerless_rows)
    choices = [(headerless_row, col) for col in range(1, w)
               if (headerless_row, col) not in used_positions]
    position = rng.choice(choices)
    used_positions.add(position)
    assignments.append((*position, non_header_colors[-1]))

    used_colors = set(header.values()) | {color for _, _, color in assignments}
    missing_colors = [color for color in palette if color not in used_colors]
    slots_left = count - len(assignments)
    if slots_left < len(missing_colors):
        raise RuntimeError("payload count cannot realize the selected palette")

    # When capacity permits, include a payload already equal to its header.
    if slots_left > len(missing_colors):
        row = header_rows[0]
        choices = [(row, col) for col in range(1, w) if (row, col) not in used_positions]
        position = rng.choice(choices)
        used_positions.add(position)
        assignments.append((*position, header[row]))
        slots_left -= 1

    candidates = [(row, col) for row in range(h) for col in range(1, w)
                  if (row, col) not in used_positions]
    remaining_positions = rng.sample(candidates, slots_left)
    remaining_colors = list(missing_colors)
    color_rng = ctx.draw_rng("payload_colors")
    remaining_colors.extend(color_rng.choice(palette)
                            for _ in range(slots_left - len(remaining_colors)))
    color_rng.shuffle(remaining_colors)
    assignments.extend((row, col, color)
                       for (row, col), color in zip(remaining_positions, remaining_colors))

    if len(assignments) != count:
        raise RuntimeError("constructive payload placement produced the wrong count")
    for row, col, color in assignments:
        grid[row][col] = color


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_request(difficulty, overrides)
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    profile = schedule_profile(seed, sample_index, difficulty)
    height_options, width_options = _shape_options(profile, difficulty)
    header_options, payload_options = _count_options(profile, difficulty)

    h = _draw_axis(ctx, overrides, "grid_h", 4, 8, height_options)
    w = _draw_axis(ctx, overrides, "grid_w", 6, 12, width_options)
    n_headers = _draw_axis(ctx, overrides, "n_headers", 1, 3, header_options)
    n_payload = _draw_axis(ctx, overrides, "n_payload", 4, 12, payload_options)

    # A core draw exactly matches canonical profile (4, 8, palette-size 6).
    if profile == "canonical_core" and not any(
            overrides.get(name) is not None for name in ("grid_h", "grid_w", "n_headers", "n_payload")):
        palette_size = 5
    else:
        min_palette = max(n_headers + 1, 4)
        max_palette = min(8, n_headers + n_payload, 9)
        preferred = {
            "easy": (min_palette, min(min_palette + 1, max_palette)),
            "medium": tuple(range(min_palette, max_palette + 1)),
            "hard": tuple(range(min_palette, max_palette + 1)) + (max_palette, max_palette),
            None: tuple(range(min_palette, max_palette + 1)),
        }[difficulty]
        palette_size = ctx.draw_choice("palette_size", preferred)

    palette = ctx.draw_rng("palette").sample(list(range(1, 10)), palette_size)
    row_rng = ctx.draw_rng("header_rows")
    header_rows = row_rng.sample(range(h), n_headers)
    header_colors = ctx.draw_rng("header_colors").sample(palette, n_headers)
    header = dict(zip(header_rows, header_colors))

    grid = full_grid(h, w, 0)
    for row, color in header.items():
        grid[row][0] = color
    _place_payloads(grid, header, palette, n_payload, ctx)
    return grid


def observe_overrides(grid):
    headers = sum(row[0] != 0 for row in grid)
    payload = sum(value != 0 for row in grid for value in row[1:])
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_headers": headers,
        "n_payload": payload,
    }


def self_check(grid, *, difficulty=None, meta=None):
    if (not isinstance(grid, (list, tuple)) or not grid
            or not isinstance(grid[0], (list, tuple)) or not grid[0]):
        return ["grid must be nonempty and rectangular"]
    if any(not isinstance(row, (list, tuple)) or len(row) != len(grid[0]) for row in grid):
        return ["grid must be rectangular"]
    if any(type(value) is not int or not 0 <= value <= 9
           for row in grid for value in row):
        return ["cells must be integer colors 0..9 (not booleans)"]

    h, w = len(grid), len(grid[0])
    errors = []
    if not 4 <= h <= 8 or not 6 <= w <= 12:
        errors.append("canvas must be 4..8 rows by 6..12 columns")
    headers = {row: grid[row][0] for row in range(h) if grid[row][0] != 0}
    payload = [(row, col, grid[row][col]) for row in range(h)
               for col in range(1, w) if grid[row][col] != 0]
    if not 1 <= len(headers) <= 3:
        errors.append(f"expected 1..3 nonzero headers, found {len(headers)}")
    if not 4 <= len(payload) <= 12:
        errors.append(f"expected 4..12 payload cells, found {len(payload)}")
    if headers and not any(row in headers and value != headers[row]
                           for row, _, value in payload):
        errors.append("no payload differs from its row header; rule would be identity")
    return errors


def strict_canonical_like(grid):
    """Lawful task-domain input; teaching witnesses are checked separately."""
    return self_check(grid)


def _identity(grid):
    return deepcopy(grid)


def _global_first_header(grid):
    output = deepcopy(grid)
    first = next((row[0] for row in grid if row[0] != 0), 0)
    for row_index, row in enumerate(grid):
        for col_index, value in enumerate(row[1:], start=1):
            if value != 0:
                output[row_index][col_index] = first
    return output


def _erase_headerless_payloads(grid):
    output = deepcopy(grid)
    for row_index, row in enumerate(grid):
        header = row[0]
        for col_index, value in enumerate(row[1:], start=1):
            if value != 0:
                output[row_index][col_index] = header
    return output


def _visible_recolor(grid):
    return any(row[0] and value and value != row[0]
               for row in grid for value in row[1:])


def _multiple_headers(grid):
    return len({row[0] for row in grid if row[0]}) >= 2


def _headerless_payload(grid):
    return any(row[0] == 0 and any(value != 0 for value in row[1:]) for row in grid)


SEMANTIC_WITNESSES = {
    "visible_recolor": _visible_recolor,
    "multiple_header_colors": _multiple_headers,
    "headerless_payload_kept": _headerless_payload,
}
SEMANTIC_RIVALS = {
    "identity": _identity,
    "global_first_header": _global_first_header,
    "erase_headerless_payloads": _erase_headerless_payloads,
}
WITNESS_RIVALS = {
    "visible_recolor": ["identity"],
    "multiple_header_colors": ["global_first_header"],
    "headerless_payload_kept": ["erase_headerless_payloads"],
}
CANONICAL_SHORTCUTS = {
    "erase_headerless_payloads": _erase_headerless_payloads,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query):
    """Finite declared-rival check against the supplied demonstration labels."""
    return [
        f"demonstrations do not distinguish declared rival {name}"
        for name, rival in LESSON_COMPETITORS.items()
        if all(rival(pair["input"]) == pair["output"] for pair in demos)
    ]
