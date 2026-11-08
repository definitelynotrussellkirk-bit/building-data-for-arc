"""Template-stamping inputs with complete, non-overlapping stamp footprints.

Background 0 and reference color 3 are semantic constants. Generate only inputs;
Racket remains the label authority. The three-profile default lesson schedule
includes an empty bounding-box corner, an occupied nonrectangular corner, and a
free shape. This distinguishes bounding-box anchoring from first-cell anchoring.

Version 2 removes the old unused palette/position/density/texture knobs. Unknown
keywords now fail rather than pretending to control the distribution. Invalid
examples are exposed by mutation_fixtures(), not as ordinary texture overrides.
"""
from __future__ import annotations

from functools import lru_cache
from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.selfcheck import components

GENERATOR_ID = "28e5fbc279ab"
TASK_ID = "28e5fbc279ab"
VERSION = "2.0.0"
RULE_HASH = "20f1992162e5"
SUMMARY = (
    "Normalize a connected green motif at its bounding-box origin and stamp it "
    "at distinct-color singleton markers; preserve each marker, including when "
    "the motif lacks its top-left corner. All stamps fit and remain disjoint."
)
EXAMPLES_NEEDED = 3
INVARIANTS = [
    "rectangular ARC grid on background 0",
    "exactly one 4-connected color-3 reference with 3-5 cells",
    "1-5 singleton markers in distinct colors from {1,2,4,5,6,7,8,9}",
    "all normalized stamp cells and retained anchors fit inside the canvas",
    "stamp footprints, retained anchors, and reference are pairwise disjoint",
]
AXES = {
    "grid_h": {"type": "int", "default": "canonical mixture / difficulty", "valid": "6..18"},
    "grid_w": {"type": "int", "default": "canonical mixture / difficulty", "valid": "8..20"},
    "n_markers": {"type": "int", "default": "canonical mixture / difficulty", "valid": "1..5"},
    "motif_size": {"type": "int", "default": "3..5; profile 1 prefers 4", "valid": "3..5"},
    "anchor_kind": {"type": "str", "default": "three-profile schedule", "valid": "occupied|empty"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []  # every in-range Cartesian tuple works
SCHEDULE_PROFILES = ("empty_corner", "nonrectangular_corner", "free_shape")
MARKER_COLORS = (1, 2, 4, 5, 6, 7, 8, 9)


def _norm(cells):
    r0 = min(r for r, c in cells)
    c0 = min(c for r, c in cells)
    return tuple(sorted((r-r0, c-c0) for r, c in cells))


@lru_cache(maxsize=5)
def _motifs(size):
    """All translation-normalized fixed polyominoes; no growth-walk bias."""
    if size == 1:
        return (((0, 0),),)
    shapes = set()
    for previous in _motifs(size-1):
        cells = set(previous)
        for r, c in previous:
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                extra = (r+dr, c+dc)
                if extra not in cells:
                    shapes.add(_norm(cells | {extra}))
    return tuple(sorted(shapes))


def schedule_profile(seed, sample_index, difficulty=None):
    del difficulty
    return SCHEDULE_PROFILES[(int(seed)+int(sample_index)) % 3]


def _draw_int(ctx, name, lo, hi, default):
    if name in ctx.overrides and ctx.overrides[name] is not None:
        value = ctx.overrides[name]
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError(f"{name} must be an integer in {lo}..{hi}")
        return ctx.draw_int(name, lo, hi)
    return ctx.draw_int(name, default, default)


def _box(r, c, sh, sw):
    return {(rr, cc) for rr in range(r, r+sh) for cc in range(c, c+sw)}


def _placements(rng, h, w, sh, sw, count):
    """Random full-canvas packing with a finite, count-preserving fallback.

    A first position outside the lower-right quadrant supplies a positional
    counterexample. It becomes a marker, never the reference. Reserve boxes
    (including a possibly empty top-left corner), not just marker pixels.
    """
    anchors = [(r, c) for r in range(h-sh+1) for c in range(w-sw+1)]
    boxes = {p: _box(*p, sh, sw) for p in anchors}
    for _ in range(4):
        rng.shuffle(anchors)
        first = next(p for p in anchors if p[0] < h//2 or p[1] < w//2)
        positions, occupied = [first], set(boxes[first])
        for p in anchors:
            if not occupied.intersection(boxes[p]):
                positions.append(p)
                occupied.update(boxes[p])
                if len(positions) == count:
                    return positions
    # The shape-pool capacity check proves these slots suffice. This is not a
    # retry with fewer markers, a different motif, or silently enlarged canvas.
    rows, cols = h//sh, w//sw
    rphase = rng.randrange(h-rows*sh+1)
    cphase = rng.randrange(w-cols*sw+1)
    slots = [(rphase+i*sh, cphase+j*sw) for i in range(rows) for j in range(cols)]
    first = slots.pop(0)
    rng.shuffle(slots)
    return [first, *slots[:count-1]]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides)-set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    profile = schedule_profile(seed, sample_index, difficulty)
    scale = ctx.draw_rng("scale")
    # Canonical canvas/count support in every difficulty band, without copying
    # canonical grids or constraining the motif, colors, or object positions.
    if scale.random() < 0.5:
        dh, dw, dn = scale.choice(((9, 12, 2), (10, 13, 3)))
    elif difficulty == "easy":
        dh, dw, dn = scale.randint(8, 11), scale.randint(10, 14), scale.randint(1, 3)
    elif difficulty == "hard":
        dh, dw, dn = scale.randint(13, 18), scale.randint(14, 20), scale.randint(3, 5)
    else:
        dh, dw, dn = scale.randint(10, 14), scale.randint(12, 17), scale.randint(2, 4)
    if profile == "empty_corner":
        dn = max(2, dn)  # every default three-demo window teaches all markers
    h = _draw_int(ctx, "grid_h", 6, 18, dh)
    w = _draw_int(ctx, "grid_w", 8, 20, dw)
    n = _draw_int(ctx, "n_markers", 1, 5, dn)
    default_size = 4 if profile == "nonrectangular_corner" else ctx.draw_rng("size").randint(3, 5)
    size = _draw_int(ctx, "motif_size", 3, 5, default_size)
    default_anchor = "empty" if profile == "empty_corner" else "occupied"
    anchor = ctx.draw_choice("anchor_kind", ("occupied", "empty")
                             if overrides.get("anchor_kind") is not None else (default_anchor,))
    choices = []
    for shape in _motifs(size):
        sh, sw = max(r for r, c in shape)+1, max(c for r, c in shape)+1
        if ((0, 0) in shape) != (anchor == "occupied"):
            continue
        if (h//sh)*(w//sw) < n+1:
            continue
        if profile == "nonrectangular_corner" and anchor == "occupied" and len(shape) == sh*sw:
            continue
        choices.append(shape)
    if not choices:
        raise ValueError("grid_h/grid_w/n_markers/motif_size/anchor_kind have no packing")
    shape = ctx.draw_rng("motif").choice(choices)
    sh, sw = max(r for r, c in shape)+1, max(c for r, c in shape)+1
    band = difficulty if difficulty in ("easy", "hard") else "medium"
    rng = ctx.draw_rng(f"layout_{band}")
    positions = _placements(rng, h, w, sh, sw, n+1)
    # Position zero is the positional witness; randomize the reference among
    # all remaining positions and independently randomize marker colors.
    reference_index = rng.randrange(1, len(positions))
    r0, c0 = positions.pop(reference_index)
    g = full_grid(h, w, 0)
    for dr, dc in shape:
        g[r0+dr][c0+dc] = 3
    colors = ctx.draw_rng("colors").sample(MARKER_COLORS, n)
    rng.shuffle(positions)
    for (r, c), color in zip(positions, colors):
        g[r][c] = color
    return g


def _analysis(grid):
    """Normalize row-string canonical grids too; reject malformed data safely."""
    if not isinstance(grid, (list, tuple)) or not grid:
        return None, ["grid must be nonempty and rectangular"]
    g = []
    for row in grid:
        if isinstance(row, str):
            if not row or any(v not in "0123456789" for v in row):
                return None, ["row string must contain ARC digits"]
            row = [int(v) for v in row]
        if not isinstance(row, (list, tuple)) or not row:
            return None, ["grid rows must be nonempty sequences"]
        if any(isinstance(v, bool) or not isinstance(v, int) or not 0 <= v <= 9 for v in row):
            return None, ["cells must be integers 0..9"]
        g.append(list(row))
    if len({len(row) for row in g}) != 1:
        return None, ["grid must be rectangular"]
    h, w = len(g), len(g[0])
    if not (1 <= h <= 30 and 1 <= w <= 30):
        return None, ["ARC canvas must fit 1..30 by 1..30"]
    comps = components(g)
    refs = [c for c in comps if c["color"] == 3]
    markers = [c for c in comps if c["color"] != 3]
    errors = []
    if len(refs) != 1:
        errors.append("expected exactly one color-3 reference component")
    elif not 3 <= len(refs[0]["cells"]) <= 5:
        errors.append("reference component must have 3-5 cells")
    if not 1 <= len(markers) <= 5:
        errors.append("expected 1-5 marker cells")
    if any(len(c["cells"]) != 1 for c in markers):
        errors.append("every non-reference component must be a singleton marker")
    colors = [c["color"] for c in markers]
    if len(colors) != len(set(colors)):
        errors.append("marker colors must be distinct")
    if errors:
        return None, errors
    ref = refs[0]
    shape = ref["norm"]
    occupied = set(ref["cells"])
    for marker in markers:
        r, c = marker["cells"][0]
        footprint = {(r+dr, c+dc) for dr, dc in shape} | {(r, c)}
        if any(not (0 <= rr < h and 0 <= cc < w) for rr, cc in footprint):
            errors.append("stamp extends outside the canvas")
        if occupied.intersection(footprint):
            errors.append("stamp footprint overlaps reference, marker, or another stamp")
        occupied.update(footprint)
    return {"grid": g, "reference": ref, "shape": shape, "markers": markers}, errors


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty, meta
    return _analysis(grid)[1]


def strict_canonical_like(grid):
    analysis, errors = _analysis(grid)
    if errors:
        return errors
    reasons = []
    if (0, 0) not in analysis["shape"]:
        reasons.append("canonical examples have occupied bounding-box corners")
    if len(analysis["shape"]) not in (3, 4):
        reasons.append("canonical motif sizes are 3 or 4")
    if len(analysis["markers"]) not in (2, 3):
        reasons.append("canonical examples have 2 or 3 markers")
    return reasons


def observe_overrides(grid):
    a, errors = _analysis(grid)
    if errors:
        return {}
    return {"grid_h": len(a["grid"]), "grid_w": len(a["grid"][0]),
            "n_markers": len(a["markers"]), "motif_size": len(a["shape"]),
            "anchor_kind": "occupied" if (0, 0) in a["shape"] else "empty"}


def _render_variant(grid, variant):
    """Diagnostic hypotheses only; not called by generate or used for labels."""
    a, errors = _analysis(grid)
    if errors:
        return None
    out = [row[:] for row in a["grid"]]
    shape = a["shape"]
    markers = a["markers"]
    if variant == "identity":
        return out
    if variant == "filled_bbox":
        shape = tuple((r, c) for r in range(max(r for r, c in shape)+1)
                      for c in range(max(c for r, c in shape)+1))
    elif variant == "first_cell_anchor":
        r0, c0 = shape[0]
        shape = tuple((r-r0, c-c0) for r, c in shape)
    elif variant == "first_marker":
        markers = markers[:1]
    for marker in markers:
        r, c = marker["cells"][0]
        if variant == "lower_right_only" and (r < len(out)//2 or c < len(out[0])//2):
            continue
        color = 3 if variant == "green_stamps" else marker["color"]
        for dr, dc in shape:
            rr, cc = r+dr, c+dc
            if 0 <= rr < len(out) and 0 <= cc < len(out[0]):
                out[rr][cc] = color
    return out


def rule_mirror(grid):
    """For counterfactual tests only; every measured match uses Racket labels."""
    return _render_variant(grid, "correct")


def _identity(g): return _render_variant(g, "identity")
def _filled_bbox(g): return _render_variant(g, "filled_bbox")
def _first_cell_anchor(g): return _render_variant(g, "first_cell_anchor")
def _first_marker(g): return _render_variant(g, "first_marker")
def _lower_right_only(g): return _render_variant(g, "lower_right_only")
def _green_stamps(g): return _render_variant(g, "green_stamps")

SEMANTIC_RIVALS = {
    "identity": _identity,
    "filled_bbox": _filled_bbox,
    "first_cell_anchor": _first_cell_anchor,
    "first_marker": _first_marker,
    "lower_right_only": _lower_right_only,
    "green_stamps": _green_stamps,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {"first_cell_anchor": _first_cell_anchor}


def _differs(grid, rival):
    expected = rule_mirror(grid)
    return expected is not None and SEMANTIC_RIVALS[rival](grid) != expected


def _w_empty(g): return _differs(g, "first_cell_anchor")
def _w_nonrect(g): return _differs(g, "filled_bbox")
def _w_multiple(g): return _differs(g, "first_marker")
def _w_position(g): return _differs(g, "lower_right_only")
def _w_color(g): return _differs(g, "green_stamps")
def _w_change(g): return _differs(g, "identity")

SEMANTIC_WITNESSES = {
    "empty_corner_requires_bbox_origin": _w_empty,
    "nonrectangle_refutes_bbox_fill": _w_nonrect,
    "multiple_markers_must_all_be_stamped": _w_multiple,
    "marker_outside_lower_right": _w_position,
    "stamp_uses_marker_color": _w_color,
    "nonidentity": _w_change,
}
WITNESS_RIVALS = {
    "empty_corner_requires_bbox_origin": ["first_cell_anchor"],
    "nonrectangle_refutes_bbox_fill": ["filled_bbox"],
    "multiple_markers_must_all_be_stamped": ["first_marker"],
    "marker_outside_lower_right": ["lower_right_only"],
    "stamp_uses_marker_color": ["green_stamps"],
    "nonidentity": ["identity"],
}


def lesson_identifiable(demos, query):
    """Finite rival screening, not a claim of unique identification among all programs."""
    reasons = []
    if len(demos) < EXAMPLES_NEEDED:
        reasons.append(f"need at least {EXAMPLES_NEEDED} demonstrations")
    for i, pair in enumerate(demos):
        expected = rule_mirror(pair["input"])
        if expected is None or expected != pair.get("output"):
            reasons.append(f"demo {i} is invalid or disagrees with the stamping rule")
    expected = rule_mirror(query["input"])
    if expected is None:
        return reasons + ["query is outside the stamping domain"]
    if query.get("output") is not None and query["output"] != expected:
        reasons.append("query output disagrees with the stamping rule")
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair.get("output") for pair in demos) and rival(query["input"]) != expected:
            reasons.append(f"query-relevant rival survives demonstrations: {name}")
    return reasons


def mutation_fixtures():
    g = full_grid(8, 10, 0)
    g[1][1:4] = [3, 3, 3]
    g[5][2], g[5][6] = 1, 2
    def copy(): return [row[:] for row in g]
    no_ref = copy(); no_ref[1][1:4] = [0, 0, 0]
    no_markers = copy(); no_markers[5][2] = no_markers[5][6] = 0
    overlap = copy(); overlap[5][6] = 0; overlap[5][4] = 2
    clipped = copy(); clipped[5][6] = 0; clipped[7][9] = 2
    reference_hit = copy(); reference_hit[5][6] = 0; reference_hit[1][0] = 2
    duplicate_color = copy(); duplicate_color[5][6] = 1
    ragged = copy(); ragged[-1].pop()
    return [("no_reference", no_ref), ("no_markers", no_markers),
            ("overlapping_stamps", overlap), ("clipped_stamp", clipped),
            ("reference_at_marker", reference_hit), ("duplicate_color", duplicate_color),
            ("ragged", ragged)]
