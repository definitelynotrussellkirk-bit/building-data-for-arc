"""Input sampler for horizontal reflection at a marker, S15_E3.

The unchanged Racket rule normalizes the color-2 template to its bounding box,
mirrors it left/right, and paints cyan at the color-1 marker on a fresh grid.
Overflow is clipped, never translated back inside. This module returns inputs;
the Python grid-producing functions below are explicitly competing rules.
"""
from __future__ import annotations

from functools import partial

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "f1668de79fa1"
TASK_ID = GENERATOR_ID
RULE_HASH = "6fbd99546842"
VERSION = "2.0.0"
SUMMARY = (
    "One connected 4..9-cell color-2 template and one color-1 marker on zero. "
    "Mirror the template inside its tight bbox, then stamp it in color 8 with "
    "the bbox top-left at the marker on a fresh zero grid. Clip overflow. "
    "Sample symmetric and asymmetric shapes, canonical and larger canvases, "
    "and both complete and partial stamps. No palette relabeling is valid: "
    "the reference uses literal colors 0, 1, 2 and 8."
)

INVARIANTS = [
    "rectangular integer grid with input colors exactly 0, 1 and 2",
    "exactly one 4-connected color-2 template containing 4..9 cells",
    "exactly one color-1 marker, on a cell outside the template",
    "at least one horizontally mirrored template cell lands in bounds",
    "symmetry and partial clipping are lawful; they are not validation errors",
]
AXES = {
    "grid_h": {"type": "int", "default": "6..18; core favors 8 and 9", "valid": "6..18"},
    "grid_w": {"type": "int", "default": "8..22; core favors 13 and 14", "valid": "8..22"},
    "template_cells": {"type": "int", "default": "4..9; wide lessons use 7..9", "valid": "4..9"},
    "marker_mode": {"type": "str", "default": "scheduled full or clipped", "valid": "full|clipped"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []

# Every consecutive three unoverridden draws include a full wide-shape witness
# and a clipping witness. Six distinct accepted pairs give two of each, so a
# leave-one-out query still leaves both kinds of demonstration. The production
# sampler can reject duplicates; retained census evidence records actual indices.
EXAMPLES_NEEDED = 5
SCHEDULE_PROFILES = ("core", "wide", "clipped")
MIN_STRICT_FRAC = 1.0


def schedule_profile(seed, sample_index, difficulty=None):
    return SCHEDULE_PROFILES[(int(seed) + int(sample_index)) % 3]


def _size(shape):
    return max(r for r, _ in shape) + 1, max(c for _, c in shape) + 1


def _normalize(cells):
    top = min(r for r, _ in cells)
    left = min(c for _, c in cells)
    return tuple(sorted((r - top, c - left) for r, c in cells))


def _transformed(shape, operation):
    h, w = _size(shape)
    if operation == "identity":
        result = shape
    elif operation == "flip_lr":
        result = [(r, w - 1 - c) for r, c in shape]
    elif operation == "flip_ud":
        result = [(h - 1 - r, c) for r, c in shape]
    elif operation == "rotate_cw":
        result = [(c, h - 1 - r) for r, c in shape]
    elif operation == "rotate_ccw":
        result = [(w - 1 - c, r) for r, c in shape]
    elif operation == "rotate_180":
        result = [(h - 1 - r, w - 1 - c) for r, c in shape]
    elif operation == "transpose":
        result = [(c, r) for r, c in shape]
    elif operation == "anti_transpose":
        result = [(w - 1 - c, h - 1 - r) for r, c in shape]
    elif operation == "swap_edge_columns":
        result = [(r, w - 1 if c == 0 else 0 if c == w - 1 else c) for r, c in shape]
    else:
        raise ValueError(f"unknown rival operation: {operation}")
    return tuple(sorted(result))


_D4 = ("identity", "flip_lr", "flip_ud", "rotate_cw", "rotate_ccw",
       "rotate_180", "transpose", "anti_transpose")


def _wide_shape(shape):
    """Interior-column contrast and no D4 stabilizer, measured on pixels."""
    return (_size(shape)[1] >= 4
            and len({_transformed(shape, op) for op in _D4}) == 8
            and _transformed(shape, "flip_lr") != _transformed(shape, "swap_edge_columns"))


def _has_interior(shape):
    cells = set(shape)
    return any(all(p in cells for p in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)))
               for r, c in cells)


def _grow_shape(rng, count, max_h, max_w, *, wide, interior):
    # Grow through a finite frontier; no unbounded random walk or silent
    # shortfall. Sorting makes draws independent of set iteration order.
    for _ in range(128):
        cells = {(0, 0)}
        for _step in range(count - 1):
            frontier = set()
            for r, c in sorted(cells):
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    candidate = (r + dr, c + dc)
                    if candidate in cells:
                        continue
                    normalized = _normalize(cells | {candidate})
                    sh, sw = _size(normalized)
                    if sh <= max_h and sw <= max_w:
                        frontier.add(candidate)
            if not frontier:
                break
            cells.add(rng.choice(sorted(frontier)))
        shape = _normalize(cells)
        if (len(shape) == count and (not wide or _wide_shape(shape))
                and (not interior or _has_interior(shape))):
            return shape
    # A connected asymmetric four-wide T with an off-center stem works for
    # every wide count 5..9 and fits even the minimum 6x8 canvas.
    if interior:
        base = [(0, 1), (0, 2), (1, 0), (1, 1), (1, 2), (1, 3), (2, 1)]
        shape = tuple(sorted(base + [(2, 0), (3, 0)][:count - 7]))
    elif wide:
        shape = tuple(sorted([(0, c) for c in range(4)]
                             + [(r, 1) for r in range(1, count - 3)]))
    else:
        shape = tuple([(0, c) for c in range(count - 1)] + [(1, 0)])
    sh, sw = _size(shape)
    if (len(shape) != count or sh > max_h or sw > max_w
            or (wide and not _wide_shape(shape)) or (interior and not _has_interior(shape))):
        raise RuntimeError("constructive shape fallback violated its contract")
    return shape


def _retained(shape, marker, h, w):
    return {(marker[0] + r, marker[1] + c) for r, c in shape
            if 0 <= marker[0] + r < h and 0 <= marker[1] + c < w}


def _validate_overrides(overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for key, lo, hi in (("grid_h", 6, 18), ("grid_w", 8, 22), ("template_cells", 4, 9)):
        if key in overrides and (type(overrides[key]) is not int or not lo <= overrides[key] <= hi):
            raise ValueError(f"{key} must be an integer in {lo}..{hi}")
    if "marker_mode" in overrides:
        value = overrides["marker_mode"]
        if not isinstance(value, str) or value not in ("full", "clipped"):
            raise ValueError("marker_mode must be full or clipped")


def _dimension(ctx, name, lo, hi, favorites, core):
    choices = list(range(lo, hi + 1))
    choices += list(favorites) * (60 if core else 2)
    return ctx.draw_choice(name, choices)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_overrides(overrides)
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    profile = schedule_profile(seed, sample_index, difficulty)
    core = profile == "core"
    h = _dimension(ctx, "grid_h", 6, 18, (8, 9), core)
    w = _dimension(ctx, "grid_w", 8, 22, (13, 14), core)
    if "template_cells" in overrides:
        count = ctx.draw_int("template_cells", 4, 9)
    else:
        sizes = list(range(7 if profile == "wide" else 4, 10))
        if difficulty == "easy" or core:
            sizes += [7] * 6 if profile == "wide" else [4, 5] * 6
        elif difficulty == "hard":
            sizes += [7, 8, 9] * 3
        count = ctx.draw_choice("template_cells", sizes)
    default_mode = "clipped" if profile == "clipped" else "full"
    modes = ("full", "clipped") if "marker_mode" in overrides else (default_mode,)
    mode = ctx.draw_choice("marker_mode", modes)
    # Small exact overrides remain lawful and exact but can disable the
    # scheduled width/interior witnesses. The default curriculum has no pins.
    wide = profile == "wide" and count >= 5
    interior = profile == "wide" and count >= 7
    shape = _grow_shape(ctx.draw_rng("template"), count, min(h, 6), min(w, 8),
                        wide=wide, interior=interior)
    sh, sw = _size(shape)
    position_rng = ctx.draw_rng("source_position")
    source_r = position_rng.randint(0, h - sh)
    source_c = position_rng.randint(0, w - sw)
    grid = full_grid(h, w, 0)
    for r, c in shape:
        grid[source_r + r][source_c + c] = 2
    mirrored = _transformed(shape, "flip_lr")
    markers = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != 0:
                continue
            if wide and mode == "full" and (r, c) == (source_r, source_c):
                continue
            retained = len(_retained(mirrored, (r, c), h, w))
            if retained and ((retained == count) == (mode == "full")):
                markers.append((r, c))
    if not markers:
        raise RuntimeError("no lawful marker position for an advertised exact combination")
    r, c = ctx.draw_rng("marker_position").choice(markers)
    grid[r][c] = 1
    return grid


def _scene(grid):
    cells = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 2]
    marker = next((r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 1)
    return _normalize(cells), marker, (min(r for r, _ in cells), min(c for _, c in cells))


def observe_overrides(grid):
    """Recover advertised controls from returned pixels, without RNG state."""
    shape, marker, _ = _scene(grid)
    visible = _retained(_transformed(shape, "flip_lr"), marker, len(grid), len(grid[0]))
    return {"grid_h": len(grid), "grid_w": len(grid[0]), "template_cells": len(shape),
            "marker_mode": "full" if len(visible) == len(shape) else "clipped"}


def self_check(grid, *, difficulty=None, meta=None):
    if (not isinstance(grid, (list, tuple)) or not grid
            or not isinstance(grid[0], (list, tuple)) or not grid[0]):
        return ["expected a nonempty rectangular grid"]
    if any(not isinstance(row, (list, tuple)) or len(row) != len(grid[0]) for row in grid):
        return ["expected a rectangular grid"]
    if any(type(value) is not int or value not in (0, 1, 2) for row in grid for value in row):
        return ["input cells must be integer colors 0, 1 or 2"]
    source = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 2}
    markers = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 1]
    errors = []
    if not 4 <= len(source) <= 9:
        errors.append(f"expected 4..9 template cells, found {len(source)}")
    if len(markers) != 1:
        errors.append(f"expected exactly one marker, found {len(markers)}")
    if not source:
        return errors
    reached = {min(source)}
    stack = list(reached)
    while stack:
        r, c = stack.pop()
        for point in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)):
            if point in source and point not in reached:
                reached.add(point)
                stack.append(point)
    if reached != source:
        errors.append("template must be one 4-connected component")
    if len(markers) == 1:
        mirrored = _transformed(_normalize(source), "flip_lr")
        if not _retained(mirrored, markers[0], len(grid), len(grid[0])):
            errors.append("mirrored stamp must retain at least one in-bounds cell")
    return errors


def strict_canonical_like(grid):
    """The task's lawful scene domain; symmetry and clipping remain valid."""
    return self_check(grid)


def _rival(grid, *, operation):
    """Competing hypotheses only; production labels always come from Racket."""
    shape, marker, source = _scene(grid)
    h, w = len(grid), len(grid[0])
    if operation == "boundary_only":
        cells = set(shape)
        boundary = [(r, c) for r, c in shape
                    if any(p not in cells for p in ((r-1, c), (r+1, c), (r, c-1), (r, c+1)))]
        offsets = _transformed(boundary, "flip_lr")
    elif operation in ("fit_inside", "copy_at_source", "keep_original"):
        offsets = _transformed(shape, "flip_lr")
    else:
        offsets = _transformed(shape, operation)
    if operation == "fit_inside":
        sh, sw = _size(shape)
        marker = (min(marker[0], h - sh), min(marker[1], w - sw))
    elif operation == "copy_at_source":
        marker = source
    out = [list(row) for row in grid] if operation == "keep_original" else full_grid(h, w, 0)
    for r, c in _retained(offsets, marker, h, w):
        out[r][c] = 8
    return out


def _wide_witness(grid):
    shape, _, _ = _scene(grid)
    return _wide_shape(shape) and observe_overrides(grid)["marker_mode"] == "full"


def _clip_witness(grid):
    return observe_overrides(grid)["marker_mode"] == "clipped"


def _interior_witness(grid):
    shape, _, _ = _scene(grid)
    return _has_interior(shape) and observe_overrides(grid)["marker_mode"] == "full"


SEMANTIC_RIVALS = {
    name: partial(_rival, operation=name)
    for name in ("identity", "flip_ud", "rotate_cw", "rotate_ccw", "rotate_180",
                 "transpose", "anti_transpose", "swap_edge_columns", "fit_inside",
                 "copy_at_source", "keep_original", "boundary_only")
}
CANONICAL_SHORTCUTS = {name: SEMANTIC_RIVALS[name]
                      for name in ("swap_edge_columns", "fit_inside", "boundary_only")}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
SEMANTIC_WITNESSES = {"wide_interior_reflection": _wide_witness, "partial_stamp": _clip_witness,
                      "interior_source_cells": _interior_witness}
WITNESS_RIVALS = {
    "wide_interior_reflection": ["identity", "flip_ud", "rotate_cw", "rotate_ccw",
                                "rotate_180", "transpose", "anti_transpose", "swap_edge_columns"],
    "partial_stamp": ["fit_inside"],
    "interior_source_cells": ["boundary_only"],
}


def lesson_identifiable(demos, query):
    """Report query ambiguity only against the declared finite rival family."""
    reasons = []
    for name, rival in LESSON_COMPETITORS.items():
        if (all(rival(pair["input"]) == pair["output"] for pair in demos)
                and rival(query["input"]) != query["output"]):
            reasons.append(f"{name} fits every demonstration but disagrees on the query")
    return reasons
