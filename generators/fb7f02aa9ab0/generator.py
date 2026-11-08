"""Generator for a legend-controlled Boolean operation on normalized shapes.

The input contains one blue shape (1), one red shape (2), and one control cell:
3 selects union, 4 intersection, and 6 symmetric difference.  Each shape is
normalized independently to its own top-left bounding-box corner before the set
operation; the cropped result is painted cyan (8) by the canonical Racket rule.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx, stable_rng
from puzzle_generators.helpers.grid import full_grid, paint_at

GENERATOR_ID = "fb7f02aa9ab0"
TASK_ID = GENERATOR_ID
RULE_HASH = "27a3cc4c9462"
VERSION = "4.0.0"
SUMMARY = (
    "A blue shape (1) and red shape (2) are placed apart with a control cell "
    "at a varying corner. Control 3/4/6 selects union/intersection/XOR after "
    "each shape is independently normalized to its own top-left bounding-box "
    "corner. Partial-overlap and either-subset relations are generated, and "
    "the shared normalized support may include or omit coordinate (0,0)."
)

EXAMPLES_NEEDED = 3

_CONTROL_COLORS = (3, 4, 6)
_CONTROL_POSITIONS = ("top_left", "top_right", "bottom_left", "bottom_right")
_RELATION_KINDS = ("partial", "a_subset_b", "b_subset_a")
_ORIGIN_KINDS = ("corner", "split")

INVARIANTS = [
    "background is 0 and the only foreground colors are 1,2 and one of 3,4,6",
    "exactly one 4-connected blue shape and one 4-connected red shape",
    "the control cell occupies one of the four corners",
    "normalized masks overlap and are unequal: partial, A-subset-B, or B-subset-A",
    "both normalized masks touch row 0 and column 0; they need not contain (0,0)",
]

AXES = {
    "grid_h": {"type": "int", "default": "canonical-weighted 8..20", "valid": "8..20"},
    "grid_w": {"type": "int", "default": "canonical-weighted 11..24", "valid": "11..24"},
    "control_color": {"type": "int", "default": "scheduled 3|4|6", "valid": "3|4|6"},
    "control_position": {
        "type": "str",
        "default": "scheduled four corners",
        "valid": "top_left|top_right|bottom_left|bottom_right",
    },
    "relation_kind": {
        "type": "str",
        "default": "scheduled partial/subset directions",
        "valid": "partial|a_subset_b|b_subset_a",
    },
    "origin_kind": {
        "type": "str",
        "default": "scheduled corner|split",
        "valid": "corner|split",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []


def _scheduled_choice(ctx, label, options, schedule_salt):
    """Cycle an axis across consecutive samples while preserving exact overrides."""
    if ctx.overrides.get(label) is not None:
        return ctx.draw_choice(label, options)
    offset = stable_rng(ctx.seed, f"{TASK_ID}|{schedule_salt}", VERSION).randrange(len(options))
    scheduled = options[(ctx.sample_index + offset) % len(options)]
    return ctx.draw_choice(label, (scheduled,))


def _weighted_dimension(ctx, label, lo, hi, canonical, favored):
    # Exact overrides remain legal in every band.  Unoverridden core draws use
    # distinct canonical anchors per difficulty, so the knob is observable
    # without sacrificing canonical-sized support in easy/medium/hard.
    if ctx.overrides.get(label) is not None:
        return ctx.draw_choice(label, tuple(range(lo, hi + 1)))
    profile = ctx.draw_choice("curriculum_profile", ("core",) * 11 + ("broad",))
    band_index = {"easy": 0, "medium": 1, "hard": 2}.get(ctx.difficulty)
    if profile == "core" and band_index is not None:
        return ctx.draw_choice(label, (canonical[band_index % len(canonical)],))
    choices = list(range(lo, hi + 1))
    if profile == "core":
        choices += list(canonical) * 40
    else:
        choices += list(favored) * 8
    return ctx.draw_choice(label, choices)


def _neighbors(cell):
    r, c = cell
    return ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1))


def _grow_connected(start, allowed, target_size, rng):
    cells = set(start)
    while len(cells) < target_size:
        frontier = sorted(
            {
                q
                for p in cells
                for q in _neighbors(p)
                if q in allowed and q not in cells
            }
        )
        if not frontier:
            return None
        cells.add(rng.choice(frontier))
    return cells


def _shape_pair(ctx, h, w, relation_kind, origin_kind):
    rng = ctx.draw_rng("normalized_shape_pair")
    max_bh = max(3, min(6, h - 3))
    max_bw = max(3, min(6, (w - 3) // 2 + 1))

    for _ in range(160):
        bh = rng.randint(3, max_bh)
        bw = rng.randint(3, max_bw)
        universe = {(r, c) for r in range(bh) for c in range(bw)}
        if origin_kind == "corner":
            seed = {(0, 0)}
        else:
            universe.remove((0, 0))
            seed = {(0, 1), (1, 1), (1, 0)}

        max_core = max(len(seed), min(len(universe) - 2, (bh * bw) // 2))
        if max_core < len(seed):
            continue
        core_size = rng.randint(len(seed), max_core)
        core = _grow_connected(seed, universe, core_size, rng)
        if core is None:
            continue

        room = len(universe) - len(core)
        if room < 2:
            continue

        if relation_kind == "partial":
            a_extra = rng.randint(1, max(1, min(room - 1, 4)))
            a = _grow_connected(core, universe, len(core) + a_extra, rng)
            if a is None:
                continue
            a_private = a - core
            b_allowed = universe - a_private
            b_room = len(b_allowed) - len(core)
            if b_room < 1:
                continue
            b_extra = rng.randint(1, max(1, min(b_room, 4)))
            b = _grow_connected(core, b_allowed, len(core) + b_extra, rng)
            if b is None or not (a - b) or not (b - a):
                continue
        elif relation_kind == "a_subset_b":
            a_extra = rng.randint(0, max(0, min(room - 1, 4)))
            a = _grow_connected(core, universe, len(core) + a_extra, rng)
            if a is None or len(a) >= len(universe):
                continue
            b_extra = rng.randint(1, max(1, min(len(universe) - len(a), 4)))
            b = _grow_connected(a, universe, len(a) + b_extra, rng)
            if b is None:
                continue
        else:
            b_extra = rng.randint(0, max(0, min(room - 1, 4)))
            b = _grow_connected(core, universe, len(core) + b_extra, rng)
            if b is None or len(b) >= len(universe):
                continue
            a_extra = rng.randint(1, max(1, min(len(universe) - len(b), 4)))
            a = _grow_connected(b, universe, len(b) + a_extra, rng)
            if a is None:
                continue

        # The seed guarantees independent normalization. In split mode (0,0)
        # is absent from the whole universe, not merely from the shared core.
        return sorted(a), sorted(b)

    raise RuntimeError("could not construct normalized shape pair")


def _control_cell(h, w, position):
    return {
        "top_left": (0, 0),
        "top_right": (0, w - 1),
        "bottom_left": (h - 1, 0),
        "bottom_right": (h - 1, w - 1),
    }[position]


def _actual_size(cells):
    return max(r for r, _ in cells) + 1, max(c for _, c in cells) + 1


def _candidate_origins(grid, cells):
    h, w = len(grid), len(grid[0])
    bh, bw = _actual_size(cells)
    out = []
    for r0 in range(h - bh + 1):
        for c0 in range(w - bw + 1):
            clear = True
            for r in range(max(0, r0 - 1), min(h, r0 + bh + 1)):
                for c in range(max(0, c0 - 1), min(w, c0 + bw + 1)):
                    if grid[r][c] != 0:
                        clear = False
                        break
                if not clear:
                    break
            if clear:
                out.append((r0, c0))
    return out


def _place_shape(grid, cells, color, rng):
    origins = _candidate_origins(grid, cells)
    if not origins:
        return False
    r0, c0 = rng.choice(origins)
    paint_at(grid, r0, c0, cells, color)
    return True


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    favored_h = {
        "easy": range(8, 11),
        "medium": range(10, 15),
        "hard": range(14, 21),
    }.get(difficulty, range(8, 21))
    favored_w = {
        "easy": range(11, 15),
        "medium": range(14, 20),
        "hard": range(18, 25),
    }.get(difficulty, range(11, 25))
    h = _weighted_dimension(ctx, "grid_h", 8, 20, (8, 9, 10), favored_h)
    w = _weighted_dimension(ctx, "grid_w", 11, 24, (11, 12, 13), favored_w)
    control_color = _scheduled_choice(ctx, "control_color", _CONTROL_COLORS, "control")
    control_position = _scheduled_choice(
        ctx, "control_position", _CONTROL_POSITIONS, "control-position"
    )
    relation_kind = _scheduled_choice(ctx, "relation_kind", _RELATION_KINDS, "relation")
    origin_kind = _scheduled_choice(ctx, "origin_kind", _ORIGIN_KINDS, "origin")

    placement_rng = ctx.draw_rng("global_placement")
    for _ in range(100):
        grid = full_grid(h, w, 0)
        cr, cc = _control_cell(h, w, control_position)
        grid[cr][cc] = control_color
        a_cells, b_cells = _shape_pair(ctx, h, w, relation_kind, origin_kind)
        if _place_shape(grid, a_cells, 1, placement_rng) and _place_shape(
            grid, b_cells, 2, placement_rng
        ):
            return grid
    raise RuntimeError("could not place both normalized shapes")


def _norm_cells(cells):
    if not cells:
        return set()
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return {(r - r0, c - c0) for r, c in cells}


def _color_cells(grid, color):
    return {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == color}


def _connected(cells):
    if not cells:
        return False
    remaining = set(cells)
    stack = [remaining.pop()]
    while stack:
        for q in _neighbors(stack.pop()):
            if q in remaining:
                remaining.remove(q)
                stack.append(q)
    return not remaining


def _relation(a, b):
    if a < b:
        return "a_subset_b"
    if b < a:
        return "b_subset_a"
    if a & b and a - b and b - a:
        return "partial"
    return "other"


def observe_overrides(grid):
    h, w = len(grid), len(grid[0])
    controls = [(r, c, value) for r, row in enumerate(grid) for c, value in enumerate(row) if value in _CONTROL_COLORS]
    if len(controls) != 1:
        raise ValueError(f"expected one control, found {len(controls)}")
    r, c, color = controls[0]
    positions = {
        (0, 0): "top_left",
        (0, w - 1): "top_right",
        (h - 1, 0): "bottom_left",
        (h - 1, w - 1): "bottom_right",
    }
    if (r, c) not in positions:
        raise ValueError("control is not at a corner")
    a = _norm_cells(_color_cells(grid, 1))
    b = _norm_cells(_color_cells(grid, 2))
    relation = _relation(a, b)
    if relation == "other":
        raise ValueError("normalized relation is outside the advertised domain")
    if (0, 0) in a and (0, 0) in b:
        origin = "corner"
    elif (0, 0) not in a and (0, 0) not in b:
        origin = "split"
    else:
        raise ValueError("mixed origin support is outside the advertised domain")
    return {
        "grid_h": h,
        "grid_w": w,
        "control_color": color,
        "control_position": positions[(r, c)],
        "relation_kind": relation,
        "origin_kind": origin,
    }


def self_check(grid, *, difficulty=None, meta=None):
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty rectangular grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected a nonempty rectangular grid"]
    w = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != w for row in grid):
        return ["expected a nonempty rectangular grid"]
    if any(type(value) is not int or value not in (0, 1, 2, 3, 4, 6) for row in grid for value in row):
        return ["cells must be integer colors from 0,1,2,3,4,6"]

    errors = []
    controls = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value in _CONTROL_COLORS]
    if len(controls) != 1:
        errors.append(f"expected exactly one control cell in {{3,4,6}}, got {len(controls)}")

    a_cells = _color_cells(grid, 1)
    b_cells = _color_cells(grid, 2)
    if not a_cells or not b_cells:
        errors.append("both color-1 and color-2 shapes must be present")
        return errors
    if not _connected(a_cells):
        errors.append("color-1 shape must be 4-connected")
    if not _connected(b_cells):
        errors.append("color-2 shape must be 4-connected")

    a = _norm_cells(a_cells)
    b = _norm_cells(b_cells)
    if not (a & b):
        errors.append("normalized masks must overlap")
    if a == b:
        errors.append("normalized masks must not be identical")
    return errors


def strict_canonical_like(grid):
    """Return errors for instances outside this sampler's teaching manifold."""
    errors = list(self_check(grid))
    if errors:
        return errors
    h, w = len(grid), len(grid[0])
    controls = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value in _CONTROL_COLORS]
    corners = {(0, 0), (0, w - 1), (h - 1, 0), (h - 1, w - 1)}
    if controls[0] not in corners:
        errors.append("control cell must occupy a corner in the generated teaching manifold")
    if not (8 <= h <= 20 and 11 <= w <= 24):
        errors.append("grid dimensions fall outside the generated teaching manifold")
    return errors


def _selected_operation(grid):
    colors = {value for row in grid for value in row}
    if 3 in colors:
        return "union"
    if 4 in colors:
        return "intersection"
    if 6 in colors:
        return "xor"
    return "union"


def _render_cells(cells):
    cells = _norm_cells(cells)
    if not cells:
        return [[0]]
    h = max(r for r, _ in cells) + 1
    w = max(c for _, c in cells) + 1
    out = full_grid(h, w, 0)
    for r, c in cells:
        out[r][c] = 8
    return out


def _operation_output(grid, *, forced_operation=None, normalize_operands=True):
    a = _color_cells(grid, 1)
    b = _color_cells(grid, 2)
    if normalize_operands:
        a = _norm_cells(a)
        b = _norm_cells(b)
    operation = forced_operation or _selected_operation(grid)
    if operation == "union":
        result = a | b
    elif operation == "intersection":
        result = a & b
    elif operation == "xor":
        result = a ^ b
    else:
        raise ValueError(f"unknown operation: {operation}")
    return _render_cells(result)


def _reference_output(grid):
    """Independent Python mirror used only for semantic probes and tests."""
    return _operation_output(grid)


def _union_only(grid):
    return _operation_output(grid, forced_operation="union")


def _intersection_only(grid):
    return _operation_output(grid, forced_operation="intersection")


def _xor_only(grid):
    return _operation_output(grid, forced_operation="xor")


def _absolute_coordinates(grid):
    """Plausible shortcut: combine global cells before normalizing the result."""
    return _operation_output(grid, normalize_operands=False)


def _control_is(color):
    def predicate(grid):
        return any(value == color for row in grid for value in row)

    return predicate


def _requires_independent_normalization(grid):
    return _reference_output(grid) != _absolute_coordinates(grid)


SEMANTIC_WITNESSES = {
    "union_control": _control_is(3),
    "intersection_control": _control_is(4),
    "xor_control": _control_is(6),
    "independent_normalization": _requires_independent_normalization,
}
SEMANTIC_RIVALS = {
    "union_only": _union_only,
    "intersection_only": _intersection_only,
    "xor_only": _xor_only,
    "absolute_coordinates": _absolute_coordinates,
}
WITNESS_RIVALS = {
    "union_control": ["intersection_only", "xor_only"],
    "intersection_control": ["union_only", "xor_only"],
    "xor_control": ["union_only", "intersection_only"],
    "independent_normalization": ["absolute_coordinates"],
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
