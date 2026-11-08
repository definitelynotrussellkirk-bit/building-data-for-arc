"""Left-edge row legend: constructive inputs for the unchanged Racket rule.

A row's column-zero header recolors its interior 8s unless that header is 0.
Other cells remain unchanged. Outputs are obtained from Racket, not this sampler.
The core/rich schedule teaches canonical-compatible rivals in ordinary lessons.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "0d5077971eea"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "1130750019d1"
SUMMARY = "Recolor interior 8s by their row's nonzero left header; preserve all other cells."
INVARIANTS = [
    "integer colors 0..9; a nonempty rectangular canvas",
    "0 is the empty-header/background color and 8 is the fixed marker color",
    "at least one row with a non-{0,8} header and an interior 8 changes",
    "zero and 8 headers, foreign spectators, repeated keys and empty rows are lawful",
    "ordinary draws contain two differently keyed transforming rows of opposite parity",
]
AXES = {
    "grid_h": {"type": "int", "default": "core favors 6/7; rich 5..12", "valid": "5..12"},
    "grid_w": {"type": "int", "default": "core favors 9; rich 10..16", "valid": "7..16"},
    "n_distinct_colors": {"type": "int", "default": "core favors 4/5; rich 4..10", "valid": "4..10"},
    "marker_density": {"type": "str", "default": "core low/med/high; rich high", "valid": "low|med|high"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []
EXAMPLES_NEEDED = 3
SCHEDULE_PROFILES = ("core", "rich")
MIN_STRICT_FRAC = 1.0
_KEY_COLORS = (1, 2, 3, 4, 5, 6, 7, 9)


def schedule_profile(seed, sample_index, difficulty=None):
    """Period two, independent of band; no labels depend on schedule position."""
    return SCHEDULE_PROFILES[sample_index % 2]


def _control(ctx, name, allowed, preferred):
    # Curriculum preferences constrain defaults only. Every explicit legal
    # override uses the full declared domain, with truthful GenCtx provenance.
    return ctx.draw_choice(name, allowed if name in ctx.overrides else preferred)


def _put_markers(row, count, rng, spectator=None):
    width = len(row)
    if spectator is None:
        reserved = None
        first = width - 1
        slots = [c for c in range(1, width) if c != first]
    else:
        # Every marker follows the spectator, so the zero-header example
        # actually separates "column zero" from "first nonzero in the row".
        # Restrict the spectator's position constructively, without clipping.
        reserved = rng.randrange(1, width - count)
        row[reserved] = spectator
        first = rng.randrange(reserved + 1, width)
        slots = [c for c in range(reserved + 1, width) if c != first]
    for c in [first] + rng.sample(slots, count - 1):
        row[c] = 8


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name, value in overrides.items():
        kind = AXES[name]["type"]
        if (kind == "int" and type(value) is not int) or (kind == "str" and type(value) is not str):
            raise ValueError(f"{name} requires {kind}")
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    rich = schedule_profile(seed, sample_index, difficulty) == "rich"
    favored_h = (5, 6, 7) if difficulty == "easy" else ((10, 11, 12) if difficulty == "hard" else (7, 8, 9))
    favored_w = (10, 11) if difficulty == "easy" else ((14, 15, 16) if difficulty == "hard" else (11, 12, 13))
    favored_colors = (4, 5) if difficulty == "easy" else ((8, 9, 10) if difficulty == "hard" else (5, 6, 7))
    core_density = ("low", "low", "med", "med", "high") if difficulty == "easy" else (
        ("low", "med", "high", "high") if difficulty == "hard" else ("low", "med", "med", "high"))
    h = _control(ctx, "grid_h", tuple(range(5, 13)),
                 tuple(range(5, 13)) + favored_h * 4 if rich else (6, 7) * 12 + tuple(range(5, 13)))
    w = _control(ctx, "grid_w", tuple(range(7, 17)),
                 tuple(range(10, 17)) + favored_w * 4 if rich else (9,) * 30 + tuple(range(7, 17)))
    n_colors = _control(ctx, "n_distinct_colors", tuple(range(4, 11)),
                        tuple(range(4, 11)) + favored_colors * 4 if rich else (5,) * 25 + (4,) * 12 + tuple(range(4, 11)))
    density = _control(ctx, "marker_density", ("low", "med", "high"),
                       ("high",) if rich else core_density)
    rng = ctx.draw_rng("layout")
    palette = ctx.draw_rng("palette").sample(_KEY_COLORS, n_colors - 2)
    if density == "low":
        peak = 1
    elif density == "med":
        peak = rng.randint(2, (w - 1) // 2)
    else:
        peak = rng.randint((w - 1) // 2 + 1, w - 1)
    grid = full_grid(h, w, 0)
    # Opposite parities break the canonical alternating-row shortcut. Their
    # order and header colors are randomized; neither parity means a color.
    keyed = [rng.choice(list(range(0, h, 2))), rng.choice(list(range(1, h, 2)))]
    rng.shuffle(keyed)
    primary, secondary = keyed
    grid[primary][0], grid[secondary][0] = palette[:2]
    _put_markers(grid[primary], peak, rng)
    _put_markers(grid[secondary], rng.randint(1, min(peak, w - 2)), rng, palette[0])
    free_rows = [r for r in range(h) if r not in keyed]
    rng.shuffle(free_rows)
    empty_header = free_rows.pop()
    _put_markers(grid[empty_header], rng.randint(1, min(3, w - 2)), rng, rng.choice(palette))
    if rich or rng.random() < 0.5:
        inert_header = free_rows.pop()
        grid[inert_header][0] = 8
        _put_markers(grid[inert_header], rng.randint(1, min(3, w - 2)), rng, rng.choice(palette))
    # At least one row remains at h=5. Its >=6 free interior cells provide
    # room for the <=6 palette colors not already used in the two headers.
    # Keeping it markerless also teaches that a header alone changes nothing.
    palette_row = free_rows.pop()
    grid[palette_row][0] = rng.choice(palette)
    for r in free_rows:
        style = rng.choice(("blank", "key_only", "keyed", "keyed"))
        if style != "blank":
            grid[r][0] = rng.choice(palette)
        if style == "keyed":
            count = rng.randint(1, peak)
            _put_markers(grid[r], count, rng)
    # Realize palette cardinality exactly, even at h=5, w=7, colors=10.
    # Extra colors are inert spectators; no marker or header is overwritten.
    present = {v for row in grid for v in row}
    available = [(r, c) for r in range(h) for c in range(1, w) if grid[r][c] == 0]
    rng.shuffle(available)
    for color in palette:
        if color not in present:
            if not available:
                raise RuntimeError("constructive palette capacity exhausted")
            r, c = available.pop()
            grid[r][c] = color
    return grid


def self_check(grid, *, difficulty=None, meta=None):
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be nonempty and rectangular"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be nonempty"]
    if any(not isinstance(row, (list, tuple)) or len(row) != len(grid[0]) for row in grid):
        return ["grid must be rectangular"]
    if len(grid) > 30 or len(grid[0]) > 30:
        return ["grid exceeds the 30 by 30 ARC canvas"]
    if any(type(v) is not int or not 0 <= v <= 9 for row in grid for v in row):
        return ["cells must be integer colors 0..9, excluding booleans"]
    if not any(row[0] not in (0, 8) and 8 in row[1:] for row in grid):
        return ["no productive row with a non-{0,8} header and an interior 8"]
    return []


def strict_canonical_like(grid):
    """Task-domain validity, including canonical headers and inert spectators."""
    return self_check(grid)


def observe_overrides(grid):
    maximum = max((row[1:].count(8) for row in grid if row[0] not in (0, 8)), default=0)
    density = "low" if maximum <= 1 else ("med" if maximum <= (len(grid[0]) - 1) // 2 else "high")
    return {"grid_h": len(grid), "grid_w": len(grid[0]),
            "n_distinct_colors": len({v for row in grid for v in row}), "marker_density": density}


def _rival(grid, mode):
    """Explicit wrong rules for authoring probes; never used to make labels."""
    out = [list(row) for row in grid]
    first_parity = next((r % 2 for r, row in enumerate(grid) if row[0] != 0), 0)
    colored = [r for r, row in enumerate(grid) if row[0] not in (0, 8)]
    for r, row in enumerate(grid):
        key = row[0]
        if mode == "first_nonzero_key":
            key = next((v for v in row if v != 0), 0)
        elif mode == "first_non8_key":
            key = next((v for v in row if v not in (0, 8)), key)
        elif mode == "nearest_colored_header" and key == 0 and colored:
            key = grid[min(colored, key=lambda k: (abs(k - r), k))][0]
        seen = 0
        for c, value in enumerate(row[1:], 1):
            if value == 8:
                seen += 1
            if mode == "erase_zero_key":
                if value == 8:
                    out[r][c] = key
                continue
            if not key or (mode == "alternating_rows" and r % 2 != first_parity):
                continue
            if mode == "recolor_all_nonzero":
                if value != 0:
                    out[r][c] = key
            elif value == 8:
                if mode == "at_most_three" and seen > 3:
                    continue
                if mode == "column_lt9" and c >= 9:
                    continue
                out[r][c] = key
    return out


def _erase_zero_key(grid): return _rival(grid, "erase_zero_key")
def _recolor_all_nonzero(grid): return _rival(grid, "recolor_all_nonzero")
def _first_nonzero_key(grid): return _rival(grid, "first_nonzero_key")
def _first_non8_key(grid): return _rival(grid, "first_non8_key")
def _alternating_rows(grid): return _rival(grid, "alternating_rows")
def _at_most_three(grid): return _rival(grid, "at_most_three")
def _column_lt9(grid): return _rival(grid, "column_lt9")
def _nearest_colored_header(grid): return _rival(grid, "nearest_colored_header")


def _zero_header_marker(grid):
    return any(row[0] == 0 and 8 in row[1:] for row in grid)


def _foreign_spectator(grid):
    return any(row[0] != 0 and any(v not in (0, 8, row[0]) for v in row[1:]) for row in grid)


def _zero_header_spectator(grid):
    return any(row[0] == 0 and 8 in row[1:] and
               next((v for v in row[1:] if v != 0), 8) != 8 for row in grid)


def _both_parities(grid):
    return len({r % 2 for r, row in enumerate(grid) if row[0] not in (0, 8) and 8 in row[1:]}) == 2


def _many_markers(grid):
    return any(row[0] not in (0, 8) and row[1:].count(8) > 3 for row in grid)


def _far_marker(grid):
    return any(row[0] not in (0, 8) and 8 in row[9:] for row in grid)


def _inert_header(grid):
    return any(row[0] == 8 and 8 in row[1:] for row in grid)


def _zero_near_color(grid):
    return _zero_header_marker(grid) and any(row[0] not in (0, 8) for row in grid)


SEMANTIC_WITNESSES = {
    "zero_header_marker": _zero_header_marker,
    "foreign_spectator": _foreign_spectator,
    "zero_header_spectator": _zero_header_spectator,
    "both_row_parities": _both_parities,
    "more_than_three_markers": _many_markers,
    "marker_after_column_eight": _far_marker,
    "zero_header_near_color": _zero_near_color,
    "header_eight_identity": _inert_header,
}
SEMANTIC_RIVALS = {
    "erase_zero_key": _erase_zero_key,
    "recolor_all_nonzero": _recolor_all_nonzero,
    "first_nonzero_key": _first_nonzero_key,
    "first_non8_key": _first_non8_key,
    "alternating_rows": _alternating_rows,
    "at_most_three": _at_most_three,
    "column_lt9": _column_lt9,
    "nearest_colored_header": _nearest_colored_header,
}
WITNESS_RIVALS = {
    "zero_header_marker": ["erase_zero_key"],
    "foreign_spectator": ["recolor_all_nonzero"],
    "zero_header_spectator": ["first_nonzero_key", "first_non8_key"],
    "both_row_parities": ["alternating_rows"],
    "more_than_three_markers": ["at_most_three"],
    "marker_after_column_eight": ["column_lt9"],
    "zero_header_near_color": ["nearest_colored_header"],
}
BRANCH_WITNESSES = {"header_eight_identity"}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query):
    return [f"{name} fits demonstrations but changes the query answer"
            for name, rival in LESSON_COMPETITORS.items()
            if all(rival(pair["input"]) == pair["output"] for pair in demos)
            and rival(query["input"]) != query["output"]]
