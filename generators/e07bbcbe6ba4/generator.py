"""Generator for e07bbcbe6ba4 (ARC task b7fb29bc).

Rule: the input holds one complete green (3) rectangular frame on a black (0)
background plus one extra green cell strictly inside the frame (the marker).
Every zero cell strictly inside the frame bbox is painted by Chebyshev
distance d from the marker: even d -> red (2), odd d -> yellow (4).  Frame and
marker stay 3; everything outside the frame stays 0.

Combinatorial axes (5): grid_h, grid_w, frame_h, frame_w, marker_edge.
Branches exercised: marker deep in the interior (near-symmetric rings),
marker adjacent to a frame wall (clipped asymmetric rings — the canonical
train[2]/test[0] class), varied frame sizes, frame positions, canvas sizes.
The repaired hard band includes substantially larger frames so the learner
must extrapolate the alternating-distance construction across more rings,
rather than seeing only extra background padding around canonical-sized frames.

Degenerate textures: none.  For this task every degenerate variant (no frame,
no marker, several markers) either crashes the oracle or makes its
reading-order marker pick ambiguous, so no texture axis is declared rather
than declaring modes a structural self_check must reject (KRF-0001).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, draw_rect_outline

GENERATOR_ID = "e07bbcbe6ba4"
VERSION = "4.0.0"
# v4 keeps the canonical rule/hash and linked prior, but makes the call contract
# strict, expands the meaningful frame-size support, and declares an executable
# canonical shortcut plus generated counterexample.
TASK_ID = "e07bbcbe6ba4"
RULE_HASH = "6c9f49f37571"
SUMMARY = "One 3-frame with one interior 3-marker; fill the interior with " \
          "Chebyshev rings from the marker (even=2, odd=4)."

INVARIANTS = [
    "background is color 0; the only nonzero color is 3",
    "exactly one complete rectangular 3-frame, height/width in 7..24",
    "the frame keeps at least a one-cell background margin to the grid edges",
    "exactly one extra 3-cell (the marker) strictly inside the frame, "
    "anywhere in the interior including wall-adjacent cells",
    "no other nonzero cells",
]

# No palette or texture variants: the oracle hard-codes colors 0/2/3/4.
PALETTE_KINDS: tuple = ()
DEGENERATE_TEXTURES: tuple = ()
HELPFUL_TEXTURES: tuple = ()

AXES = {
    "grid_h":      {"type": "int", "default": "band rng 11..30", "valid": "9..30"},
    "grid_w":      {"type": "int", "default": "band rng 11..30", "valid": "9..30"},
    "frame_h":     {"type": "int", "default": "band rng 7..24", "valid": "7..24"},
    "frame_w":     {"type": "int", "default": "band rng 7..24", "valid": "7..24"},
    "marker_edge": {"type": "bool",
                    "default": "band-weighted rng (edge p: easy 0.3, "
                               "medium 0.5, hard 0.7)",
                    "valid": "true|false"},
}

_GRID_LO, _GRID_HI = 9, 30
_FRAME_LO, _FRAME_HI = 7, 24
_ALLOWED_DIFFICULTIES = (None, "easy", "medium", "hard")
_INT_DOMAINS = {
    "grid_h": (_GRID_LO, _GRID_HI),
    "grid_w": (_GRID_LO, _GRID_HI),
    "frame_h": (_FRAME_LO, _FRAME_HI),
    "frame_w": (_FRAME_LO, _FRAME_HI),
}


def _validate_call(seed, sample_index, difficulty, overrides):
    """Reject ambiguous scalar coercions before constructing ``GenCtx``."""
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative integer (not bool)")
    if difficulty not in _ALLOWED_DIFFICULTIES:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")

    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis: {unknown[0]}")

    for name, (lo, hi) in _INT_DOMAINS.items():
        value = overrides.get(name)
        if value is None:
            continue
        if type(value) is not int or not lo <= value <= hi:
            raise ValueError(f"{name} must be an integer in [{lo}, {hi}]")

    marker_edge = overrides.get("marker_edge")
    if marker_edge is not None and not (
        type(marker_edge) is bool
        or (
            type(marker_edge) is str
            and marker_edge.strip().lower() in ("true", "false")
        )
    ):
        raise ValueError(
            "marker_edge must be bool or the string 'true'/'false'"
        )


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Structural invariants of a lawful instance: a rectangular 0..9 grid
    whose only nonzero color is 3, forming one complete rectangular frame
    (every bbox-border cell is 3) with exactly one 3-cell strictly inside the
    bbox (the marker).  Zero markers crash the oracle and several markers make
    its reading-order pick ambiguous, so both are rejected; outputs (which
    contain 2/4) and broken frames are rejected too."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    if h > 30 or w > 30:
        errs.append(f"grid exceeds ARC 30x30 limit: {h}x{w}")
    if any(not 0 <= v <= 9 for row in grid for v in row):
        errs.append("color outside 0..9")
    other = sum(1 for row in grid for v in row if v not in (0, 3))
    if other:
        errs.append(f"{other} cell(s) with color other than 0/3")
    greens = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 3]
    if not greens:
        errs.append("no green (3) frame present")
        return errs
    r1 = min(r for r, _ in greens)
    r2 = max(r for r, _ in greens)
    c1 = min(c for _, c in greens)
    c2 = max(c for _, c in greens)
    fh, fw = r2 - r1 + 1, c2 - c1 + 1
    if fh < 3 or fw < 3:
        errs.append(f"frame {fh}x{fw} has no room for an interior marker")
    # Declared frame envelope and outer margin (AXES/INVARIANTS): frame sides
    # in 7..24 and at least one background cell to every grid edge.
    if not (_FRAME_LO <= fh <= _FRAME_HI and _FRAME_LO <= fw <= _FRAME_HI):
        errs.append(
            f"frame {fh}x{fw} outside the declared "
            f"{_FRAME_LO}..{_FRAME_HI} envelope"
        )
    if r1 == 0 or c1 == 0 or r2 == h - 1 or c2 == w - 1:
        errs.append("frame touches the grid edge; a one-cell background "
                    "margin is required on every side")
    gset = set(greens)
    missing = [(r, c) for r in (r1, r2) for c in range(c1, c2 + 1)
               if (r, c) not in gset]
    missing += [(r, c) for r in range(r1 + 1, r2) for c in (c1, c2)
                if (r, c) not in gset]
    if missing:
        errs.append(f"incomplete frame: {len(missing)} border cell(s) missing")
    interior = [(r, c) for r in range(r1 + 1, r2) for c in range(c1 + 1, c2)
                if grid[r][c] == 3]
    if len(interior) != 1:
        errs.append(
            f"expected exactly one interior 3-marker, found {len(interior)}")
    return errs


def _banded_int(ctx, overrides, label, lo, hi, valid_lo, valid_hi):
    """Band-shaped random draw; overrides validated against the full valid
    range (an override must execute on any band, per the AXES contract)."""
    if label in overrides and overrides[label] is not None:
        return ctx.draw_int_strict(label, valid_lo, valid_hi)
    return ctx.draw_int(label, lo, hi)


def _marker_position(rng, r0, c0, fh, fw, mode):
    """Marker cell strictly inside the frame: deep (>=2 from every wall),
    edge-adjacent (exactly 1 from at least one wall), or anywhere inside."""
    r_lo, r_hi = r0 + 1, r0 + fh - 2
    c_lo, c_hi = c0 + 1, c0 + fw - 2
    if mode == "deep":
        return rng.randint(r_lo + 1, r_hi - 1), rng.randint(c_lo + 1, c_hi - 1)
    if mode == "edge":
        spots = [(r, c) for r in range(r_lo, r_hi + 1)
                 for c in range(c_lo, c_hi + 1)
                 if r in (r_lo, r_hi) or c in (c_lo, c_hi)]
        return spots[rng.randrange(len(spots))]
    return rng.randint(r_lo, r_hi), rng.randint(c_lo, c_hi)


def observe_overrides(grid):
    """Report per-draw realized values of exact semantic axes (KRF-0002),
    derived from the grid itself: frame_h/frame_w are the 3-frame bbox
    dimensions; marker_edge is True when the unique interior marker sits on
    the interior ring (exactly one cell from at least one wall)."""
    h, w = len(grid), len(grid[0])
    greens = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 3]
    if not greens:
        return {"frame_h": 0, "frame_w": 0, "marker_edge": None}
    r1 = min(r for r, _ in greens)
    r2 = max(r for r, _ in greens)
    c1 = min(c for _, c in greens)
    c2 = max(c for _, c in greens)
    interior = [(r, c) for r in range(r1 + 1, r2) for c in range(c1 + 1, c2)
                if grid[r][c] == 3]
    edge = None
    if len(interior) == 1:
        mr, mc = interior[0]
        edge = (mr in (r1 + 1, r2 - 1) or mc in (c1 + 1, c2 - 1))
    return {"frame_h": r2 - r1 + 1, "frame_w": c2 - c1 + 1,
            "marker_edge": edge}


def profile_signature(grid):
    """Complete linked geometry used by the canonical-profile audit."""
    observed = observe_overrides(grid)
    return (
        len(grid),
        len(grid[0]),
        observed["frame_h"],
        observed["frame_w"],
        observed["marker_edge"],
    )


def rule_mirror(grid):
    """Independent Python port used only for parity and regression audits."""
    result = [row[:] for row in grid]
    h, w = len(grid), len(grid[0])
    greens = [(r, c) for r in range(h) for c in range(w)
              if grid[r][c] == 3]
    r1 = min(r for r, _ in greens)
    r2 = max(r for r, _ in greens)
    c1 = min(c for _, c in greens)
    c2 = max(c for _, c in greens)
    markers = [(r, c) for r, c in greens
               if r not in (r1, r2) and c not in (c1, c2)]
    mr, mc = markers[0]
    for r in range(r1 + 1, r2):
        for c in range(c1 + 1, c2):
            if result[r][c] != 0:
                continue
            distance = max(abs(r - mr), abs(c - mc))
            result[r][c] = 2 if distance % 2 == 0 else 4
    return result


def strict_canonical_like(grid):
    """Return ``[]`` for every lawful member of the declared task manifold."""
    return self_check(grid)


def _fixed_canonical_bbox(grid):
    """Plausible WRONG rule: always use the public demonstrations' bbox.

    All canonical inputs are 15x15 with the green frame at rows 2..10 and
    columns 3..11 (zero based).  A learner can therefore fit every public pair
    without learning to detect the frame.  On any input that does not realize
    that exact fixed frame, this total rival conservatively returns the input.
    """
    result = [list(row) for row in grid]
    if not result or not result[0] or any(len(row) != len(result[0]) for row in result):
        return result
    h, w = len(result), len(result[0])
    r1, r2, c1, c2 = 2, 10, 3, 11
    if h <= r2 or w <= c2:
        return result
    border = (
        [(r1, c) for c in range(c1, c2 + 1)]
        + [(r2, c) for c in range(c1, c2 + 1)]
        + [(r, c1) for r in range(r1 + 1, r2)]
        + [(r, c2) for r in range(r1 + 1, r2)]
    )
    if any(result[r][c] != 3 for r, c in border):
        return result
    markers = [
        (r, c)
        for r in range(r1 + 1, r2)
        for c in range(c1 + 1, c2)
        if result[r][c] == 3
    ]
    if len(markers) != 1:
        return result
    mr, mc = markers[0]
    for r in range(r1 + 1, r2):
        for c in range(c1 + 1, c2):
            if result[r][c] == 0:
                distance = max(abs(r - mr), abs(c - mc))
                result[r][c] = 2 if distance % 2 == 0 else 4
    return result


def _variable_geometry_refutes_fixed_bbox(grid):
    if self_check(grid):
        return False
    return _fixed_canonical_bbox(grid) != rule_mirror(grid)


SEMANTIC_RIVALS = {"fixed_canonical_bbox": _fixed_canonical_bbox}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
SEMANTIC_WITNESSES = {
    "variable_geometry_refutes_fixed_bbox": _variable_geometry_refutes_fixed_bbox,
}
WITNESS_RIVALS = {
    "variable_geometry_refutes_fixed_bbox": ["fixed_canonical_bbox"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Validate labels and report declared rivals surviving all demonstrations."""
    reasons: list[str] = []
    if not isinstance(demos, (list, tuple)) or not demos:
        return ["need at least one demonstration"]

    valid_demos = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair:
            reasons.append(f"demo {index} is missing an input")
            continue
        grid = pair["input"]
        errors = self_check(grid)
        if errors:
            reasons.append(f"demo {index} is outside the grammar: {errors[0]}")
            continue
        expected = rule_mirror(grid)
        if pair.get("output") != expected:
            reasons.append(f"demo {index} output does not match Chebyshev rings")
            continue
        valid_demos.append(pair)

    if not isinstance(query, dict) or "input" not in query:
        reasons.append("query is missing an input")
        return reasons
    query_grid = query["input"]
    query_errors = self_check(query_grid)
    if query_errors:
        reasons.append(f"query is outside the grammar: {query_errors[0]}")
        return reasons
    query_answer = rule_mirror(query_grid)
    if query.get("output") is not None and query.get("output") != query_answer:
        reasons.append("query output does not match Chebyshev rings")

    for name, rival in LESSON_COMPETITORS.items():
        if valid_demos and all(
            rival(pair["input"]) == pair["output"] for pair in valid_demos
        ):
            if rival(query_grid) != query_answer:
                reasons.append(f"{name} fits every demo but disagrees on query")
    return reasons


def _canvas_and_frame(
    ctx,
    overrides,
    *,
    grid_label,
    frame_label,
    grid_lo,
    grid_hi,
    frame_lo,
    frame_hi,
):
    """Draw one canvas/frame dimension with exact, truthful provenance."""
    frame_overridden = (
        frame_label in overrides and overrides[frame_label] is not None
    )
    grid_overridden = (
        grid_label in overrides and overrides[grid_label] is not None
    )
    if frame_overridden:
        frame = _banded_int(
            ctx,
            overrides,
            frame_label,
            frame_lo,
            frame_hi,
            _FRAME_LO,
            _FRAME_HI,
        )
        if grid_overridden:
            grid = _banded_int(
                ctx,
                overrides,
                grid_label,
                grid_lo,
                grid_hi,
                _GRID_LO,
                _GRID_HI,
            )
            if frame + 2 > grid:
                raise ValueError(
                    f"{frame_label}={frame} needs {grid_label} >= "
                    f"{frame + 2}; exact {grid_label}={grid} was requested"
                )
        else:
            fit_lo = max(grid_lo, frame + 2)
            fit_hi = max(grid_hi, fit_lo)
            grid = ctx.draw_int(grid_label, fit_lo, fit_hi)
        return grid, frame

    grid = _banded_int(
        ctx,
        overrides,
        grid_label,
        grid_lo,
        grid_hi,
        _GRID_LO,
        _GRID_HI,
    )
    drawable_hi = min(frame_hi, grid - 2)
    frame = _banded_int(
        ctx,
        overrides,
        frame_label,
        min(frame_lo, drawable_hi),
        drawable_hi,
        _FRAME_LO,
        _FRAME_HI,
    )
    return grid, frame


def generate(seed, sample_index, *, difficulty=None, **overrides):
    overrides = dict(overrides)
    _validate_call(seed, sample_index, difficulty, overrides)
    if overrides.get("marker_edge") is not None:
        raw = overrides["marker_edge"]
        if type(raw) is bool:
            overrides["marker_edge"] = raw
        elif type(raw) is str and raw.strip().lower() in ("true", "false"):
            overrides["marker_edge"] = raw.strip().lower() == "true"
        else:
            raise ValueError(
                "marker_edge must be bool or the string 'true'/'false'"
            )
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    band = difficulty or "medium"
    if band == "easy":
        h_lo, h_hi, f_lo, f_hi, edge_p = 11, 16, 7, 10, 0.3
    elif band == "hard":
        h_lo, h_hi, f_lo, f_hi, edge_p = 21, 30, 14, 24, 0.7
    else:
        h_lo, h_hi, f_lo, f_hi, edge_p = 15, 24, 9, 18, 0.5
    # Canonical-form prior (KRF-0003): every official input is 15x15 with a
    # 9x9 frame. One third of fully-unoverridden draws pin exactly that geometry
    # through keyed draws (marker mode stays band-weighted: both are
    # official); frame position and marker cell stay random.
    if not any(k in overrides for k in ("grid_h", "grid_w", "frame_h", "frame_w")):
        if ctx.draw_rng("canonical_prior").random() < 0.33:
            for label, value in (("grid_h", 15), ("grid_w", 15),
                                 ("frame_h", 9), ("frame_w", 9)):
                overrides[label] = value
                ctx.overrides[label] = value
                ctx.draw_int(label, value, value)
    # Choose a feasible free canvas before recording it. The v3.0 path first
    # recorded a too-small grid and then silently grew it for an overridden
    # frame, so GenCtx provenance disagreed with the returned grid.
    h, fh = _canvas_and_frame(
        ctx,
        overrides,
        grid_label="grid_h",
        frame_label="frame_h",
        grid_lo=h_lo,
        grid_hi=h_hi,
        frame_lo=f_lo,
        frame_hi=f_hi,
    )
    w, fw = _canvas_and_frame(
        ctx,
        overrides,
        grid_label="grid_w",
        frame_label="frame_w",
        grid_lo=h_lo,
        grid_hi=h_hi,
        frame_lo=f_lo,
        frame_hi=f_hi,
    )
    # Marker placement: an override of marker_edge wins over the band's
    # weighted coin; every band keeps positive mass on both modes so both
    # ring-symmetry branches are witnessed in every band.
    if "marker_edge" in overrides and overrides["marker_edge"] is not None:
        edge = ctx.draw_choice("marker_edge", [False, True])
    else:
        edge = ctx.draw_rng("marker_edge").random() < edge_p
        # KRF-0004 provenance: the band-weighted coin's realized outcome is
        # an exact observable axis; record it under its declared label.
        ctx.overrides["marker_edge"] = edge
        ctx.draw_choice("marker_edge", [edge])
    marker_mode = "edge" if edge else "deep"
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    r0 = rng.randint(1, h - fh - 1)
    c0 = rng.randint(1, w - fw - 1)
    draw_rect_outline(g, r0, c0, fh, fw, 3)
    mr, mc = _marker_position(rng, r0, c0, fh, fw, marker_mode)
    g[mr][mc] = 3
    return g
