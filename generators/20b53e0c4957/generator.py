"""Input curriculum for 20b53e0c4957 — replay A→B removals on C.

Two full-height color-5 columns split the input into equal-width panels A, B,
and C.  A is a solid rectangular object.  B is the same object in the same
panel coordinates with selected cells removed.  C has the same bbox dimensions
but is independently translated and contains one pre-existing interior hole.
The unchanged Racket authority transfers only the A-minus-B cells, relative to
A's bbox, onto C's bbox while preserving C's own structure.
"""
from __future__ import annotations

from copy import deepcopy
from functools import partial

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = TASK_ID = "20b53e0c4957"
RULE_HASH = "9217dc891941"
VERSION = "3.0.0"

SUMMARY = (
    "Three equal-width panels A|B|C are separated by full-height color-5 "
    "columns. A is a translated solid rectangle; B is A with 1..6 cells "
    "removed in the same panel coordinates. C has the same bbox dimensions, "
    "a different color, an independently translated bbox, and one independent "
    "interior hole. Transfer the A-minus-B coordinates relative to A's bbox "
    "onto C's bbox, preserving C's existing hole."
)

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0
LESSON_SCHEDULE_PERIOD = 4
SCHEDULE_PROFILES = ("canonical_size", "broad")
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []

INVARIANTS = [
    "two full-height color-5 columns split three equal-width panels",
    "A is one solid rectangle and B is a nonempty strict subset of A at the same coordinates",
    "A and B use one color; C uses one different color",
    "C has the same bbox dimensions as A but an independently translated bbox",
    "ordinary generated C objects contain one interior hole not removed from B",
    "1..6 A-minus-B cells are transferred relative to the A and C bbox origins",
]

# All three pairs occur in the retained canonical task.
_PALETTES = ((2, 7), (4, 6), (3, 7))

AXES = {
    "panel_h": {
        "type": "int",
        "default": "4 on canonical-size schedule; otherwise difficulty-weighted 4..8",
        "valid": "4..8",
    },
    "panel_w": {
        "type": "int",
        "default": "4 on canonical-size schedule; otherwise difficulty-weighted 4..7",
        "valid": "4..7",
    },
    "n_removed": {
        "type": "int",
        "default": "easy 1..3; medium 2..5; hard 3..6; unbanded 1..6",
        "valid": "1..6",
    },
    "palette_id": {
        "type": "int",
        "default": "uniform canonical palette id 0..2",
        "valid": "0..2",
    },
}


def _validate_call(seed, sample_index, difficulty, overrides):
    if type(seed) is not int:
        raise ValueError("seed must be an integer (not bool)")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative integer (not bool)")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be easy, medium, hard, or None")
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")


def schedule_profile(seed, sample_index, difficulty=None):
    """Pin every fourth unoverridden draw to an exact canonical input profile."""
    return "canonical_size" if sample_index % LESSON_SCHEDULE_PERIOD == 0 else "broad"


def _int_axis(ctx, name, global_bounds, preferred_bounds):
    """Difficulty changes defaults, never an exact override's legal domain."""
    bounds = global_bounds if ctx.overrides.get(name) is not None else preferred_bounds
    return ctx.draw_int_strict(name, *bounds)


def _split_panels(grid):
    h, w = len(grid), len(grid[0])
    if (w - 2) % 3:
        raise ValueError("width does not encode three equal panels plus two dividers")
    panel_w = (w - 2) // 3
    return (
        [list(row[:panel_w]) for row in grid],
        [list(row[panel_w + 1 : 2 * panel_w + 1]) for row in grid],
        [list(row[2 * panel_w + 2 :]) for row in grid],
    )


def _cells(panel):
    return {(r, c) for r, row in enumerate(panel) for c, value in enumerate(row) if value != 0}


def _bbox(cells):
    if not cells:
        raise ValueError("cannot take bbox of an empty panel")
    return (
        min(r for r, _ in cells),
        min(c for _, c in cells),
        max(r for r, _ in cells),
        max(c for _, c in cells),
    )


def _foreground_color(panel):
    colors = {value for row in panel for value in row if value != 0}
    if len(colors) != 1:
        raise ValueError(f"expected one nonzero panel color, found {sorted(colors)}")
    return next(iter(colors))


def _paint_rect(panel, top, left, height, width, color):
    for r in range(top, top + height):
        for c in range(left, left + width):
            panel[r][c] = color


def _assemble(a, b, c):
    h, panel_w = len(a), len(a[0])
    grid = full_grid(h, 3 * panel_w + 2, 0)
    for r in range(h):
        grid[r][panel_w] = 5
        grid[r][2 * panel_w + 1] = 5
        grid[r][:panel_w] = a[r]
        grid[r][panel_w + 1 : 2 * panel_w + 1] = b[r]
        grid[r][2 * panel_w + 2 :] = c[r]
    return grid


def rule_mirror(grid):
    """Pure Python transcription of the pinned authority, used only for review hooks."""
    a, b, c = _split_panels(grid)
    cells_a = _cells(a)
    cells_b = _cells(b)
    ar0, ac0, _, _ = _bbox(cells_a)
    cr0, cc0, _, _ = _bbox(_cells(c))
    removed = {(r - ar0, col - ac0) for r, col in cells_a - cells_b}
    out = deepcopy(c)
    for rr, cc in removed:
        r, col = cr0 + rr, cc0 + cc
        if 0 <= r < len(out) and 0 <= col < len(out[0]):
            out[r][col] = 0
    return out


def _recolor_b_absolute(grid):
    """Shortcut: ignore A/C geometry and recolor panel B in place."""
    _, b, c = _split_panels(grid)
    color = _foreground_color(c)
    return [[color if value else 0 for value in row] for row in b]


def _copy_b_to_c_bbox(grid):
    """Shortcut: normalize B's occupied bbox and paste it at C's bbox."""
    _, b, c = _split_panels(grid)
    b_cells = _cells(b)
    br0, bc0, _, _ = _bbox(b_cells)
    cr0, cc0, _, _ = _bbox(_cells(c))
    color = _foreground_color(c)
    out = full_grid(len(c), len(c[0]), 0)
    for r, col in b_cells:
        rr, cc = cr0 + (r - br0), cc0 + (col - bc0)
        if 0 <= rr < len(out) and 0 <= cc < len(out[0]):
            out[rr][cc] = color
    return out


def _absolute_removed_positions(grid):
    """Shortcut: apply A-minus-B at raw panel coordinates instead of bbox-relative coordinates."""
    a, b, c = _split_panels(grid)
    out = deepcopy(c)
    for r, col in _cells(a) - _cells(b):
        if 0 <= r < len(out) and 0 <= col < len(out[0]):
            out[r][col] = 0
    return out


SEMANTIC_RIVALS = {
    "recolor_b_absolute": _recolor_b_absolute,
    "copy_b_to_c_bbox": _copy_b_to_c_bbox,
    "absolute_removed_positions": _absolute_removed_positions,
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def _refutes(grid, *, rival):
    return rule_mirror(grid) != SEMANTIC_RIVALS[rival](grid)


SEMANTIC_WITNESSES = {name: partial(_refutes, rival=name) for name in SEMANTIC_RIVALS}
WITNESS_RIVALS = {name: [name] for name in SEMANTIC_RIVALS}


def _candidate_grid(ctx, panel_h, panel_w, n_removed, palette_id, attempt):
    rng = ctx.draw_rng(f"layout:{attempt}")
    color_a, color_c = _PALETTES[palette_id]

    # Leave at least one row and column of translation freedom.  A 3x3 minimum
    # also guarantees an interior C-only hole and six removable non-hole cells.
    object_h = rng.randint(3, min(5, panel_h - 1))
    object_w = rng.randint(3, min(5, panel_w - 1))
    positions = [
        (top, left)
        for top in range(panel_h - object_h + 1)
        for left in range(panel_w - object_w + 1)
    ]
    a_top, a_left = rng.choice(positions)
    c_top, c_left = rng.choice([position for position in positions if position != (a_top, a_left)])

    interior = [
        (r, c)
        for r in range(1, object_h - 1)
        for c in range(1, object_w - 1)
    ]
    query_hole = rng.choice(interior)
    local_cells = [(r, c) for r in range(object_h) for c in range(object_w)]
    removal_candidates = [cell for cell in local_cells if cell != query_hole]
    removed = set(rng.sample(removal_candidates, n_removed))

    a = full_grid(panel_h, panel_w, 0)
    b = full_grid(panel_h, panel_w, 0)
    c = full_grid(panel_h, panel_w, 0)
    _paint_rect(a, a_top, a_left, object_h, object_w, color_a)
    _paint_rect(b, a_top, a_left, object_h, object_w, color_a)
    _paint_rect(c, c_top, c_left, object_h, object_w, color_c)
    for rr, cc in removed:
        b[a_top + rr][a_left + cc] = 0
    c[c_top + query_hole[0]][c_left + query_hole[1]] = 0
    return _assemble(a, b, c)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(seed, sample_index, difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    pinned = any(value is not None for value in overrides.values())
    core = not pinned and schedule_profile(seed, sample_index, difficulty) == "canonical_size"
    if core:
        h_bounds, w_bounds = (4, 4), (4, 4)
    elif difficulty == "easy":
        h_bounds, w_bounds = (4, 6), (4, 5)
    elif difficulty == "hard":
        h_bounds, w_bounds = (6, 8), (5, 7)
    else:
        h_bounds, w_bounds = (4, 8), (4, 7)

    removed_bounds = {
        "easy": (1, 3),
        "medium": (2, 5),
        "hard": (3, 6),
        None: (1, 6),
    }[difficulty]
    panel_h = _int_axis(ctx, "panel_h", (4, 8), h_bounds)
    panel_w = _int_axis(ctx, "panel_w", (4, 7), w_bounds)
    n_removed = _int_axis(ctx, "n_removed", (1, 6), removed_bounds)
    palette_id = _int_axis(ctx, "palette_id", (0, 2), (0, 2))

    # Qualification is deterministic and input-only.  It protects the teaching
    # contract from accidental equality with canonical-fitting shortcuts.
    for attempt in range(256):
        grid = _candidate_grid(ctx, panel_h, panel_w, n_removed, palette_id, attempt)
        truth = rule_mirror(grid)
        if all(rival(grid) != truth for rival in SEMANTIC_RIVALS.values()):
            return grid
    raise RuntimeError("could not construct a shortcut-refuting bbox-transfer instance")


def observe_overrides(grid):
    a, b, c = _split_panels(grid)
    palette = (_foreground_color(a), _foreground_color(c))
    try:
        palette_id = _PALETTES.index(palette)
    except ValueError as exc:
        raise ValueError(f"unrecognized generated palette {palette}") from exc
    return {
        "panel_h": len(grid),
        "panel_w": len(a[0]),
        "n_removed": len(_cells(a) - _cells(b)),
        "palette_id": palette_id,
    }


def self_check(grid, *, difficulty=None, meta=None):
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty rectangular grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected nonempty rows"]
    h, w = len(grid), len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != w for row in grid):
        return ["ragged grid"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be integer ARC colors 0..9"]
    if h > 30 or w > 30:
        return [f"grid too large: {h}x{w}"]
    if (w - 2) % 3:
        return ["width must be 3*panel_w+2"]
    panel_w = (w - 2) // 3
    if not (3 <= h <= 8 and 3 <= panel_w <= 7):
        return [f"panel dimensions outside supported canonical/generator range: {h}x{panel_w}"]

    d1, d2 = panel_w, 2 * panel_w + 1
    errors = []
    for r, row in enumerate(grid):
        if row[d1] != 5 or row[d2] != 5:
            errors.append(f"row {r} lacks the two color-5 divider cells")
            break
    extra_fives = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 5 and c not in (d1, d2)
    ]
    if extra_fives:
        errors.append(f"color 5 appears outside divider columns at {extra_fives[0]}")

    a, b, c = _split_panels(grid)
    panels = (("A", a), ("B", b), ("C", c))
    panel_cells = {}
    panel_colors = {}
    for name, panel in panels:
        cells = _cells(panel)
        if not cells:
            errors.append(f"panel {name} is empty")
            continue
        colors = {value for row in panel for value in row if value != 0}
        if len(colors) != 1:
            errors.append(f"panel {name} must contain one foreground color, found {sorted(colors)}")
            continue
        panel_cells[name] = cells
        panel_colors[name] = next(iter(colors))

    if set(panel_cells) != {"A", "B", "C"}:
        return errors
    if panel_colors["A"] != panel_colors["B"]:
        errors.append("A and B must use the same foreground color")
    if panel_colors["C"] == panel_colors["A"]:
        errors.append("C must use a different foreground color")

    cells_a, cells_b, cells_c = panel_cells["A"], panel_cells["B"], panel_cells["C"]
    ar0, ac0, ar1, ac1 = _bbox(cells_a)
    solid_a = {(r, col) for r in range(ar0, ar1 + 1) for col in range(ac0, ac1 + 1)}
    if cells_a != solid_a:
        errors.append("A must be a solid rectangle")
    if not cells_b < cells_a:
        errors.append("B must be a nonempty strict subset of A at the same coordinates")
    removed = cells_a - cells_b
    if not 1 <= len(removed) <= 6:
        errors.append(f"A-minus-B removal count must be 1..6, found {len(removed)}")

    cr0, cc0, cr1, cc1 = _bbox(cells_c)
    a_shape = (ar1 - ar0 + 1, ac1 - ac0 + 1)
    c_shape = (cr1 - cr0 + 1, cc1 - cc0 + 1)
    if c_shape != a_shape:
        errors.append(f"C bbox dimensions {c_shape} must equal A bbox dimensions {a_shape}")
    c_bbox_cells = {(r, col) for r in range(cr0, cr1 + 1) for col in range(cc0, cc1 + 1)}
    query_holes = c_bbox_cells - cells_c
    if len(query_holes) > 2:
        errors.append(f"C may contain at most two pre-existing bbox holes, found {len(query_holes)}")
    return errors


def strict_canonical_like(grid):
    return self_check(grid)


def lesson_identifiable(demos, query):
    """Finite declared-rival check; not a universal uniqueness proof."""
    return [
        name + " fits every demonstration but changes the query"
        for name, rival in LESSON_COMPETITORS.items()
        if all(rival(pair["input"]) == pair["output"] for pair in demos)
        and rival(query["input"]) != query["output"]
    ]
