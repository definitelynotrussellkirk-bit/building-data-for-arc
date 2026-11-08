"""Inputs for H155: infer the exact A-to-B transform, apply to C, recolor.

The existing Racket rule is the label authority. Panels are square, separated
by two full body columns of color 8; the first nonzero header cell supplies the
output color. All eight dihedral transforms are supported. Exact color cues,
moving headers, and a four-position teaching schedule refute declared rivals.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "1a2afa3c0d4b"
TASK_ID = GENERATOR_ID
VERSION = "4.0.0"
RULE_HASH = "04089d4dac06"
SUMMARY = (
    "Infer the exact-color dihedral transform mapping square panel A to B, "
    "apply it to C, and recolor its nonzero cells to the first nonzero header "
    "color. Body separator columns have color 8; header position varies."
)
INVARIANTS = [
    "three square panels, side 3..9, separated by exactly two full body columns of 8",
    "the first nonzero header cell determines output color, including lawful color 8",
    "A has eight distinct exact-color orientations, and B is its requested transform",
    "ordinary C has an asymmetric nonempty support so transform choices affect the output",
    "sampled foreground colors occupy connected regions; geometry-mode supports are connected glyphs",
    "default color-witness slots require exact colors, header order rather than color rank, and recoloring",
]

_CODES = ("id", "r1", "r2", "r3", "fh", "fv", "tr", "atr")
_PANEL_COLORS = (1, 2, 3, 4, 5, 6, 7, 9)
_A_MODES = ("geometry", "color")
_HEADER_POSITIONS = ("first", "interior", "last")
AXES = {
    "panel_side": {"type": "int", "default": "4 in canonical slots; varied by band otherwise", "valid": "3..9"},
    "transform": {"type": "enum", "default": "all eight; witness slots favor unshown branches", "valid": "id|r1|r2|r3|fh|fv|tr|atr"},
    "header_color": {"type": "color", "default": "1..9; 2..8 in default header-order witnesses", "valid": "1..9"},
    "header_position": {"type": "enum", "default": "first in canonical slots; shifted in witness slots", "valid": "first|interior|last"},
    "a_mode": {"type": "enum", "default": "geometry, color-witness, broad, color-witness", "valid": "geometry|color"},
}
# Every advertised combination is constructive in every difficulty band.
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []
EXAMPLES_NEEDED = 3
LESSON_SCHEDULE_PERIOD = 4
SCHEDULE_PROFILES = ("canonical", "color_witness", "broad")


def schedule_profile(seed, sample_index, difficulty=None):
    """A semantic schedule, independent of the keyed random content."""
    return ("canonical", "color_witness", "broad", "color_witness")[sample_index % 4]


def _xform_grid(grid, code):
    """The reference's eight transforms; also correct on rectangular arrays."""
    h, w = len(grid), len(grid[0])
    if code == "id":
        return [row[:] for row in grid]
    if code == "r1":
        return [[grid[h - 1 - r][c] for r in range(h)] for c in range(w)]
    if code == "r2":
        return [[grid[h - 1 - r][w - 1 - c] for c in range(w)] for r in range(h)]
    if code == "r3":
        return [[grid[r][c] for r in range(h)] for c in range(w - 1, -1, -1)]
    if code == "fh":
        return [list(reversed(row)) for row in grid]
    if code == "fv":
        return [row[:] for row in reversed(grid)]
    if code == "tr":
        return [[grid[r][c] for r in range(h)] for c in range(w)]
    if code == "atr":
        return [[grid[r][c] for r in range(h - 1, -1, -1)]
                for c in range(w - 1, -1, -1)]
    raise ValueError(f"Unknown transform: {code!r}")


def _as_key(grid):
    return tuple(tuple(row) for row in grid)


def _mask(grid):
    return [[int(v != 0) for v in row] for row in grid]


def _orbit_size(grid):
    return len({_as_key(_xform_grid(grid, code)) for code in _CODES})


def _make_asym_panel(rng, s, colors, *, color_only=False):
    """Grow varied connected glyphs and color regions; never use a fixed fallback.

    Full support makes the color-only A ambiguous by occupancy. Otherwise the
    support itself is asymmetric. Connected color territories avoid the visual
    fragmentation of independent random pixels, while their shapes still vary.
    """
    steps = ((-1, 0), (1, 0), (0, -1), (0, 1))
    for _ in range(128):
        if color_only:
            support = {(r, c) for r in range(s) for c in range(s)}
        else:
            size = rng.randint(max(3, len(colors)), max(3, int(0.6 * s * s)))
            support = {(rng.randrange(s), rng.randrange(s))}
            frontier = set()
            while len(support) < size:
                frontier.update((r + dr, c + dc) for r, c in support for dr, dc in steps
                                if 0 <= r + dr < s and 0 <= c + dc < s)
                frontier.difference_update(support)
                support.add(rng.choice(sorted(frontier)))
        seeds = rng.sample(sorted(support), len(colors))
        labels = {cell: color for cell, color in zip(seeds, colors)}
        frontier = [(r + dr, c + dc, color) for (r, c), color in labels.items()
                    for dr, dc in steps if (r + dr, c + dc) in support]
        while frontier:
            r, c, color = frontier.pop(rng.randrange(len(frontier)))
            if (r, c) in labels:
                continue
            labels[r, c] = color
            frontier.extend((r + dr, c + dc, color) for dr, dc in steps
                            if (r + dr, c + dc) in support and (r + dr, c + dc) not in labels)
        panel = [[labels.get((r, c), 0) for c in range(s)] for r in range(s)]
        if _orbit_size(panel) == 8 and (color_only or _orbit_size(_mask(panel)) == 8):
            return panel
    raise RuntimeError("Could not draw an asymmetric panel in 128 attempts")


def _panels(grid):
    s = len(grid) - 1
    return [[row[k * (s + 1):k * (s + 1) + s] for row in grid[1:]]
            for k in range(3)]


def _infer(a, b, codes=_CODES):
    return next((code for code in codes if _xform_grid(a, code) == b), None)


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Check actual rule preconditions; metadata never exempts malformed input.

    The validator permits an empty C and additional header cells because the
    authority handles them. Ordinary C is nonempty; witness headers have decoys.
    """
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["empty or non-grid input"]
    if any(not isinstance(row, (list, tuple)) or not row for row in grid):
        return ["empty or malformed row"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    if any(type(v) is not int or not 0 <= v <= 9 for row in grid for v in row):
        return ["colors must be integer values 0..9, excluding booleans"]
    s = h - 1
    if not 3 <= s <= 9 or w != 3 * s + 2:
        return ["expected three side-3..9 square panels plus header and two separators"]
    if not any(grid[0]):
        return ["header has no nonzero color"]
    separators = [c for c in range(w) if all(row[c] == 8 for row in grid[1:])]
    if separators != [s, 2 * s + 1]:
        return ["expected exactly the two panel-boundary separator columns"]
    a, b, c = _panels(grid)
    if any(v == 8 for panel in (a, b, c) for row in panel for v in row):
        return ["panel foreground excludes separator color 8"]
    matches = [code for code in _CODES if _xform_grid(a, code) == b]
    if len(matches) != 1:
        return [f"expected one exact-color A-to-B transform, found {len(matches)}"]
    return []


def strict_canonical_like(grid):
    """Task-domain lawfulness, not just canonical shape/palette resemblance."""
    return self_check(grid)


def _choice(ctx, overrides, name, defaults, domain):
    # Restrict defaults without falsely restricting the public override domain.
    return ctx.draw_choice(name, domain if overrides.get(name) is not None else defaults)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"Unknown override axes: {sorted(unknown)}")
    for name in ("panel_side", "header_color"):
        if overrides.get(name) is not None and type(overrides[name]) is not int:
            raise TypeError(f"{name} must be an integer, excluding booleans")
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    profile = schedule_profile(seed, sample_index, difficulty)
    witness = profile == "color_witness"
    core = profile == "canonical"
    favored = {"easy": (3, 4), "medium": (4, 5, 6), "hard": (6, 7, 8, 9)}.get(difficulty, (4, 5, 6))
    s = _choice(ctx, overrides, "panel_side", (4,) if core else favored, tuple(range(3, 10)))
    mode = _choice(ctx, overrides, "a_mode", ("geometry",) if core else (("color",) if witness else _A_MODES), _A_MODES)
    code = _choice(ctx, overrides, "transform", ("r2", "r3", "fv", "atr") if witness else _CODES, _CODES)
    position = _choice(ctx, overrides, "header_position",
                       ("first",) if core else (("interior",) if witness else _HEADER_POSITIONS),
                       _HEADER_POSITIONS)
    target = _choice(ctx, overrides, "header_color",
                     tuple(range(2, 9)) if witness else tuple(range(1, 10)), tuple(range(1, 10)))
    header_rng = ctx.draw_rng("header_decoys")
    tail = []
    if witness and position != "last":
        legal = [color for color in range(1, 10) if color not in (target, 8)]
        if 1 < target < 9:
            # Five distinct colors put the target away from both extremes and
            # the median. Three-color headers accidentally encode the median.
            lower = [color for color in legal if color < target]
            higher = [color for color in legal if color > target]
            splits = [(lo, 4 - lo) for lo in (1, 3)
                      if len(lower) >= lo and len(higher) >= 4 - lo]
            lo, hi = header_rng.choice(splits)
            tail = header_rng.sample(lower, lo) + header_rng.sample(higher, hi)
        else:
            # Exact color-1/9 overrides remain lawful; rank witnesses are
            # impossible at an endpoint, so do not claim them for this case.
            tail = header_rng.sample(legal, 2)
        header_rng.shuffle(tail)
    rng = ctx.draw_rng("panels")
    # Canonical slots use 4 or 5 total colors, including header/panel aliases.
    # Witness C colors exclude the target to require recoloring. Broad slots
    # allow those aliases as well as both A modes and all eight transforms.
    pool = [color for color in _PANEL_COLORS
            if color not in tail and (not witness or color != target)]
    a_colors = rng.sample(pool, 2 if mode == "color" or not core else 1)
    c_pool = [color for color in pool if color not in a_colors]
    c_colors = rng.sample(c_pool, 1 if core else rng.randint(1, min(3, len(c_pool))))
    a = _make_asym_panel(rng, s, a_colors, color_only=mode == "color")
    b = _xform_grid(a, code)
    c = _make_asym_panel(rng, s, c_colors)
    grid = full_grid(s + 1, 3 * s + 2, 0)
    column = 0 if position == "first" else (len(grid[0]) - 1 if position == "last"
             else ctx.draw_rng("header_column").randrange(1, len(grid[0]) - max(1, len(tail))))
    grid[0][column] = target
    for header_column, color in zip(sorted(header_rng.sample(range(column + 1, len(grid[0])), len(tail))), tail):
        grid[0][header_column] = color
    for row in grid[1:]:
        row[s] = row[2 * s + 1] = 8
    for k, panel in enumerate((a, b, c)):
        offset = k * (s + 1)
        for r, row in enumerate(panel):
            grid[r + 1][offset:offset + s] = row
    return grid


def observe_overrides(grid):
    errors = self_check(grid)
    if errors:
        raise ValueError("; ".join(errors))
    a, b, _ = _panels(grid)
    column = next(c for c, color in enumerate(grid[0]) if color)
    position = "first" if column == 0 else ("last" if column == len(grid[0]) - 1 else "interior")
    return {"panel_side": len(a), "transform": _infer(a, b),
            "header_color": grid[0][column], "header_position": position,
            "a_mode": "color" if all(v for row in a for v in row) else "geometry"}


def _prediction(grid, *, binary=False, codes=_CODES, copy_query=False,
                paint_header=True, header_mode="first"):
    """Authoring diagnostic only; the Racket runtime supplies saved labels."""
    a, b, c = _panels(grid)
    if binary:
        a, b = _mask(a), _mask(b)
    code = "id" if copy_query else (_infer(a, b, codes) or "id")
    output = _xform_grid(c, code)
    if not paint_header:
        return output
    colors = [v for v in grid[0] if v]
    if header_mode == "col0":
        color = grid[0][0]
    elif header_mode == "last":
        color = colors[-1]
    elif header_mode == "minimum":
        color = min(colors)
    elif header_mode == "maximum":
        color = max(colors)
    elif header_mode == "median":
        color = sorted(colors)[(len(colors) - 1) // 2]
    else:
        color = colors[0]
    return [[color if v else 0 for v in row] for row in output]


def _binary_transform(grid):
    return _prediction(grid, binary=True)


def _canonical_transform_subset(grid):
    return _prediction(grid, codes=("r1", "fh", "tr"))


def _first_header_cell(grid):
    return _prediction(grid, header_mode="col0")


def _last_header_color(grid):
    return _prediction(grid, header_mode="last")


def _minimum_header_color(grid):
    return _prediction(grid, header_mode="minimum")


def _maximum_header_color(grid):
    return _prediction(grid, header_mode="maximum")


def _median_header_color(grid):
    return _prediction(grid, header_mode="median")


def _identity_query(grid):
    return _prediction(grid, copy_query=True)


def _no_recolor(grid):
    return _prediction(grid, paint_header=False)


def _color_matters(grid):
    return _binary_transform(grid) != _prediction(grid)


def _unshown_transform(grid):
    return _canonical_transform_subset(grid) != _prediction(grid)


def _header_matters(grid):
    return _first_header_cell(grid) != _prediction(grid)


def _recolor_matters(grid):
    return _no_recolor(grid) != _prediction(grid)


def _header_order_matters(grid):
    expected = _prediction(grid)
    return all(rival(grid) != expected for rival in
               (_last_header_color, _minimum_header_color, _maximum_header_color,
                _median_header_color))


SEMANTIC_RIVALS = {
    "binary_transform": _binary_transform,
    "canonical_transform_subset": _canonical_transform_subset,
    "first_header_cell": _first_header_cell,
    "last_header_color": _last_header_color,
    "minimum_header_color": _minimum_header_color,
    "maximum_header_color": _maximum_header_color,
    "median_header_color": _median_header_color,
    "identity_query": _identity_query,
    "no_recolor": _no_recolor,
}
CANONICAL_SHORTCUTS = {name: SEMANTIC_RIVALS[name] for name in
                       ("binary_transform", "canonical_transform_subset", "first_header_cell",
                        "last_header_color", "minimum_header_color", "maximum_header_color",
                        "median_header_color")}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
SEMANTIC_WITNESSES = {
    "exact_colors_matter": _color_matters,
    "unshown_transform": _unshown_transform,
    "shifted_header": _header_matters,
    "recolor_required": _recolor_matters,
    "header_order_and_rank": _header_order_matters,
}
WITNESS_RIVALS = {
    "exact_colors_matter": ["binary_transform"],
    "unshown_transform": ["canonical_transform_subset"],
    "shifted_header": ["first_header_cell"],
    "recolor_required": ["no_recolor"],
    "header_order_and_rank": ["last_header_color", "minimum_header_color", "maximum_header_color",
                              "median_header_color"],
}
