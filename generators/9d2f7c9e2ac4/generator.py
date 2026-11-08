"""Input sampler for H31: complete a clockwise quadrant analogy.

The color-9 cross separates TL/TR (a worked clockwise example) from BL/BR
(the source and empty target). The unchanged Racket authority rotates the BL
object's bounding box clockwise and retains its row/column offsets in BR.
Labels always come from Racket; the Python predictions below are named rivals
and authoring checks, not a replacement label authority.
"""
from __future__ import annotations

from functools import lru_cache
from itertools import combinations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "9d2f7c9e2ac4"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "3d50e1ec984b"
SUMMARY = (
    "A centered maroon cross separates a visible TL-to-TR clockwise example "
    "from a BL source and empty BR target. Rotate the BL bounding box clockwise, "
    "preserving its offsets and color; generate full-fit shapes on 9..15 grids."
)
INVARIANTS = [
    "one centered full color-9 row and column; all other cells are colors 0..8",
    "TL and TR contain the same monochrome connected shape, rotated clockwise at equal bbox offsets",
    "BL contains one monochrome connected shape; BR is entirely empty",
    "the full BL rotation fits in BR without clipping or dropping cells",
    "default source shapes distinguish all eight square symmetries, and differ from the upper example",
]
AXES = {
    "grid_n": {"type": "int", "default": "9..15, with extra weight on canonical sizes 9 and 11", "valid": "9..15"},
    "shape_variant": {"type": "int", "default": "0..2 = 4, 5, or 6 source cells", "valid": "0..2"},
    "example_color": {"type": "int", "default": "1..8; rank alternates relative to source", "valid": "1..8"},
    "source_color": {"type": "int", "default": "1..8, distinct from example unless explicitly overridden", "valid": "1..8"},
    "source_position": {"type": "str", "default": "origin/down/right/diagonal cycle", "valid": "origin|down|right|diagonal"},
}
# All combinations of the five declared domains are constructive, even n=9/10.
# Explicit equal object colors are lawful; unforced production uses two colors.
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []
EXAMPLES_NEEDED = 3
LESSON_SCHEDULE_PERIOD = 4
SCHEDULE_PROFILES = ("origin", "down", "right", "diagonal")
_POSITIONS = {"origin": (0, 0), "down": (1, 0), "right": (0, 1), "diagonal": (1, 1)}
_DELTAS4 = ((-1, 0), (1, 0), (0, -1), (0, 1))
_TRANSFORMS = ("identity", "cw", "half_turn", "ccw", "flip_lr", "flip_ud", "transpose", "anti_transpose")
MIN_STRICT_FRAC = 0.5


def _normalize(cells):
    cells = tuple(cells)
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def _transform(cells, name):
    operations = {
        "identity": lambda r, c: (r, c),
        "cw": lambda r, c: (c, -r),
        "half_turn": lambda r, c: (-r, -c),
        "ccw": lambda r, c: (-c, r),
        "flip_lr": lambda r, c: (r, -c),
        "flip_ud": lambda r, c: (-r, c),
        "transpose": lambda r, c: (c, r),
        "anti_transpose": lambda r, c: (-c, -r),
    }
    return _normalize(operations[name](r, c) for r, c in cells)


def _connected(cells):
    remaining = set(cells)
    if not remaining:
        return False
    pending = [remaining.pop()]
    while pending:
        r, c = pending.pop()
        for dr, dc in _DELTAS4:
            point = (r + dr, c + dc)
            if point in remaining:
                remaining.remove(point)
                pending.append(point)
    return not remaining


def _asymmetric(cells):
    return len({_transform(cells, name) for name in _TRANSFORMS}) == 8


@lru_cache(maxsize=3)
def _shape_bank(count):
    """Enumerate finite geometry, not cached examples: 8/16/32 oriented shapes.

    Every shape is connected, fully D4-asymmetric and fits a 3x3 box. This
    constructive bank replaces rejection/fallback that could silently reduce
    an exact requested cell count. Positions, sizes and colors remain draws.
    """
    points = tuple((r, c) for r in range(3) for c in range(3))
    shapes = {_normalize(cells) for cells in combinations(points, count)
              if _connected(cells) and _asymmetric(cells)}
    if not shapes:
        raise ValueError(f"no asymmetric shape with {count} cells")
    return tuple(sorted(shapes))


def _paint(grid, origin, cells, color):
    r0, c0 = origin
    for r, c in cells:
        grid[r0 + r][c0 + c] = color


def schedule_profile(seed, sample_index, difficulty=None):
    """Semantic schedule only; keyed random geometry need not repeat."""
    return SCHEDULE_PROFILES[sample_index % LESSON_SCHEDULE_PERIOD]


def _checked_overrides(overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    controls = {key: value for key, value in overrides.items() if value is not None}
    ranges = {"grid_n": (9, 15), "shape_variant": (0, 2),
              "example_color": (1, 8), "source_color": (1, 8)}
    for key, value in controls.items():
        if key in ranges:
            low, high = ranges[key]
            if type(value) is not int or not low <= value <= high:
                raise ValueError(f"{key} must be an integer in {low}..{high} (not bool)")
        elif not isinstance(value, str) or value not in _POSITIONS:
            raise ValueError("source_position must be origin, down, right, or diagonal")
    return controls


def generate(seed, sample_index, *, difficulty=None, **overrides):
    controls = _checked_overrides(overrides)
    controls.setdefault("source_position", schedule_profile(seed, sample_index, difficulty))
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=controls)
    sizes = list(range(9, 16)) + [9, 11] * 8
    if difficulty == "easy":
        sizes += [9] * 4
    elif difficulty == "hard":
        sizes += [13, 15] * 2
    n = ctx.draw_choice("grid_n", sizes)
    variant = ctx.draw_int_strict("shape_variant", 0, 2)
    position = ctx.draw_choice("source_position", SCHEDULE_PROFILES)
    row_offset, col_offset = _POSITIONS[position]

    # In each four-draw window, two sources are numerically below their upper
    # example and two are above. Caller-specified colors remain exact, including
    # equal colors. A forced extreme example color may override the rank hint.
    source_lower = sample_index % 2 == 0
    example_options = list(range(2, 9) if source_lower else range(1, 8))
    if "example_color" in controls:
        example_options = list(range(1, 9))
    elif "source_color" in controls:
        example_options = [c for c in example_options if c != controls["source_color"]]
    example_color = ctx.draw_choice("example_color", example_options)
    source_options = list(range(1, example_color) if source_lower else range(example_color + 1, 9))
    if not source_options:
        source_options = [c for c in range(1, 9) if c != example_color]
    if "source_color" in controls:
        source_options = list(range(1, 9))
    source_color = ctx.draw_choice("source_color", source_options)

    source = ctx.draw_rng("source_shape").choice(_shape_bank(4 + variant))
    examples = tuple(shape for shape in _shape_bank(4) if shape != source)
    example = ctx.draw_rng("example_shape").choice(examples)
    example_rng = ctx.draw_rng("example_position")
    if sample_index % 4 in (1, 2):
        # At least two of every four scenes distinguish the example's offset
        # from the source's. Other positions remain independently randomized.
        er, ec = 1 - row_offset, 1 - col_offset
    else:
        er, ec = example_rng.randrange(2), example_rng.randrange(2)
    middle = n // 2
    grid = full_grid(n, n, 0)
    for i in range(n):
        grid[middle][i] = grid[i][middle] = 9
    _paint(grid, (er, ec), example, example_color)
    _paint(grid, (er, middle + 1 + ec), _transform(example, "cw"), example_color)
    _paint(grid, (middle + 1 + row_offset, col_offset), source, source_color)
    return grid


def _full_split(grid):
    rows = [r for r, row in enumerate(grid) if all(value == 9 for value in row)]
    cols = [c for c in range(len(grid[0])) if all(row[c] == 9 for row in grid)]
    if len(rows) != 1 or len(cols) != 1:
        return None
    return rows[0], cols[0]


def _bounds(grid, panel):
    split = _full_split(grid)
    if split is None:
        raise ValueError("expected one full color-9 row and column")
    gr, gc = split
    return {"TL": (0, gr, 0, gc), "TR": (0, gr, gc + 1, len(grid[0])),
            "BL": (gr + 1, len(grid), 0, gc),
            "BR": (gr + 1, len(grid), gc + 1, len(grid[0]))}[panel]


def _panel(grid, panel):
    r0, r1, c0, c1 = _bounds(grid, panel)
    return {(r - r0, c - c0): grid[r][c]
            for r in range(r0, r1) for c in range(c0, c1)
            if grid[r][c] not in (0, 9)}


def _offset(cells):
    return min(r for r, _ in cells), min(c for _, c in cells)


def _rotated_panel(cells):
    ro, co = _offset(cells)
    color = next(iter(cells.values()))
    return {(ro + r, co + c): color for r, c in _transform(cells, "cw")}


def self_check(grid, *, difficulty=None, meta=None):
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty grid"]
    if any(not isinstance(row, (list, tuple)) or not row for row in grid):
        return ["expected nonempty grid rows"]
    if len({len(row) for row in grid}) != 1:
        return ["ragged grid"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be integer colors 0..9 (not bool)"]
    n = len(grid)
    if len(grid[0]) != n or not 9 <= n <= 15:
        return ["expected a square grid of size 9..15"]
    split = _full_split(grid)
    if split != (n // 2, n // 2):
        return ["expected exactly one centered full color-9 row and column"]
    middle = n // 2
    if any(grid[r][c] == 9 for r in range(n) for c in range(n) if r != middle and c != middle):
        return ["color 9 may occur only on the separator cross"]
    reasons = []
    panels = {name: _panel(grid, name) for name in ("TL", "TR", "BL")}
    for name, cells in panels.items():
        if not cells:
            reasons.append(f"{name} has no shape")
        elif len(set(cells.values())) != 1 or not _connected(cells):
            reasons.append(f"{name} must be one single-color connected shape")
    if any(grid[r][c] != 0 for r in range(middle + 1, n) for c in range(middle + 1, n)):
        reasons.append("bottom-right quadrant is not empty")
    if panels["TL"] and panels["TR"] != _rotated_panel(panels["TL"]):
        reasons.append("top-right must show the full clockwise example with matching bbox offsets and color")
    if panels["BL"]:
        rotated = _rotated_panel(panels["BL"])
        capacity = n - middle - 1
        if any(not (0 <= r < capacity and 0 <= c < capacity) for r, c in rotated):
            reasons.append("rotated bottom-left shape would be clipped in bottom-right")
    return reasons


def strict_canonical_like(grid):
    reasons = self_check(grid)
    if reasons:
        return reasons
    if len(grid) not in (9, 11):
        reasons.append("outside canonical sizes 9 and 11")
    if len({value for row in grid for value in row}) != 4:
        reasons.append("canonical scenes have two distinct object colors, background, and separator")
    # Symmetric canonical sources are legitimate: asymmetry is a teaching
    # preference of generate(), never a condition for canonical acceptance.
    return reasons


def observe_overrides(grid):
    top, source = _panel(grid, "TL"), _panel(grid, "BL")
    offset = _offset(source)
    names = {value: key for key, value in _POSITIONS.items()}
    return {"grid_n": len(grid), "shape_variant": len(source) - 4,
            "example_color": next(iter(top.values())),
            "source_color": next(iter(source.values())),
            "source_position": names[offset]}


def _rival(grid, *, transform="cw", placement="source", color_choice="source", copy_example=False):
    """Pure alternative prediction; used only by the authoring semantic checks."""
    source = _panel(grid, "BL")
    if not source:
        return [list(row) for row in grid]
    ro, co = _offset(source)
    top = _panel(grid, "TL")
    positions = {"source": (ro, co), "origin": (0, 0), "swapped": (co, ro),
                 "drop_row": (0, co), "drop_column": (ro, 0),
                 "repeat_row": (ro, ro), "repeat_column": (co, co),
                 "template_row": (_offset(top)[0] if top else 0, co)}
    ro, co = positions[placement]
    color = next(iter(source.values()))
    if color_choice == "maximum":
        color = max(v for row in grid for v in row if v not in (0, 9))
    elif color_choice == "minimum":
        color = min(v for row in grid for v in row if v not in (0, 9))
    shape = _transform(top if copy_example and top else source, transform)
    r0, r1, c0, c1 = _bounds(grid, "BR")
    output = [list(row) for row in grid]
    for r, c in shape:
        rr, cc = r0 + ro + r, c0 + co + c
        if r0 <= rr < r1 and c0 <= cc < c1:
            output[rr][cc] = color
    return output


CANONICAL_SHORTCUTS = {
    "origin_anchor": lambda g: _rival(g, placement="origin"),
    "swap_offsets": lambda g: _rival(g, placement="swapped"),
    "drop_row_offset": lambda g: _rival(g, placement="drop_row"),
    "drop_column_offset": lambda g: _rival(g, placement="drop_column"),
    "duplicate_row_offset": lambda g: _rival(g, placement="repeat_row"),
    "duplicate_column_offset": lambda g: _rival(g, placement="repeat_column"),
    "template_row_offset": lambda g: _rival(g, placement="template_row"),
    "max_foreground_color": lambda g: _rival(g, color_choice="maximum"),
}
SEMANTIC_RIVALS = {
    **CANONICAL_SHORTCUTS,
    "no_rotation": lambda g: _rival(g, transform="identity"),
    "counterclockwise": lambda g: _rival(g, transform="ccw"),
    "half_turn": lambda g: _rival(g, transform="half_turn"),
    "flip_lr": lambda g: _rival(g, transform="flip_lr"),
    "flip_ud": lambda g: _rival(g, transform="flip_ud"),
    "transpose": lambda g: _rival(g, transform="transpose"),
    "anti_transpose": lambda g: _rival(g, transform="anti_transpose"),
    "copy_upper_shape": lambda g: _rival(g, copy_example=True),
    "min_foreground_color": lambda g: _rival(g, color_choice="minimum"),
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def _row_offset(g):
    return _offset(_panel(g, "BL"))[0]


def _column_offset(g):
    return _offset(_panel(g, "BL"))[1]


SEMANTIC_WITNESSES = {
    "origin_anchor": lambda g: _offset(_panel(g, "BL")) != (0, 0),
    "swap_offsets": lambda g: _row_offset(g) != _column_offset(g),
    "drop_row_offset": lambda g: _row_offset(g) > 0,
    "drop_column_offset": lambda g: _column_offset(g) > 0,
    "duplicate_row_offset": lambda g: _row_offset(g) != _column_offset(g),
    "duplicate_column_offset": lambda g: _row_offset(g) != _column_offset(g),
    "template_row_offset": lambda g: _offset(_panel(g, "TL"))[0] != _row_offset(g),
    "max_foreground_color": lambda g: next(iter(_panel(g, "BL").values())) < next(iter(_panel(g, "TL").values())),
    "asymmetric_source": lambda g: _asymmetric(_panel(g, "BL")),
}
WITNESS_RIVALS = {name: [name] for name in CANONICAL_SHORTCUTS}
WITNESS_RIVALS["asymmetric_source"] = ["no_rotation", "counterclockwise", "transpose"]


def lesson_identifiable(demos, query):
    """Finite declared-rival check, not a claim of universal rule identification."""
    reasons = []
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            if rival(query["input"]) != query["output"]:
                reasons.append(f"{name} fits every demonstration but changes the query")
    return reasons
