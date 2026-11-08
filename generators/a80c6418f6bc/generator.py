"""Generator for e14e4b5836bc:H96 — transfer an added shape delta.

A color-9 row and column split the input into four equal quadrants.  The
upper-left panel A and upper-right panel B demonstrate an edit: after aligning
their nonzero bounding boxes, B contains every cell of A plus one or more new
relative cells.  The lower-left panel C is the query object.  The canonical
Racket rule copies C into the empty lower-right panel and adds the same relative
B-minus-A cells in C's color.

The sequential sample-index schedule deliberately breaks common shortcuts:
within-bbox and bbox-expanding edits, aligned and offset placements, delta
counts 1/2/3, and both same-shape and different-shape query objects appear in
each ordinary four-pair lesson.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "a80c6418f6bc"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "88309ffec80e"

SUMMARY = (
    "A color-9 cross forms demonstration panels A and B, query panel C, and an "
    "empty answer panel.  B is a strict bbox-aligned superset of A.  Copy C to "
    "the answer panel and stamp exactly the relative B-minus-A cells in C's "
    "color.  Ordinary four-pair lessons schedule within-bbox, right-expanding, "
    "down-expanding, and two-axis-expanding edits; they also include query "
    "shapes that differ from A so copying B's silhouette is not a valid shortcut."
)

INVARIANTS = [
    "one full color-9 row and column split the grid into four equal quadrants",
    "A and B are monochrome in the same color; B is a strict bbox-aligned superset of A",
    "C is monochrome in a different color and has A's bbox dimensions",
    "the answer quadrant is empty and every B-minus-A cell is absent from C",
    "the Racket oracle copies C and stamps the relative B-minus-A cells in C's color",
]

_DELTA_MODES = ("within_bbox", "expand_right", "expand_down", "expand_both")
_PLACEMENT_MODES = ("aligned", "offset")
_QUERY_RELATIONS = ("same_shape", "different_shape")
_COLORS = tuple(range(1, 9))

AXES = {
    "quad_size": {
        "type": "int",
        "default": "difficulty-aware 4..8",
        "valid": "4..8",
    },
    "delta_count": {
        "type": "int",
        "default": "sample_index schedule 1,2,3",
        "valid": "1..3",
    },
    "delta_mode": {
        "type": "str",
        "default": "sample_index schedule",
        "valid": "within_bbox|expand_right|expand_down|expand_both",
    },
    "placement_mode": {
        "type": "str",
        "default": "sample_index schedule aligned|offset",
        "valid": "aligned|offset",
    },
    "query_relation": {
        "type": "str",
        "default": "same_shape once, then different_shape",
        "valid": "same_shape|different_shape",
    },
}


def _scheduled_int(ctx, name, lo, hi, scheduled):
    if name in ctx.overrides and ctx.overrides[name] is not None:
        return ctx.draw_int(name, lo, hi)
    return ctx.draw_int(name, scheduled, scheduled)


def _scheduled_choice(ctx, name, options, scheduled):
    if name in ctx.overrides and ctx.overrides[name] is not None:
        return ctx.draw_choice(name, options)
    return ctx.draw_choice(name, (scheduled,))


def _neighbors4(cell, h, w):
    r, c = cell
    for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        nr, nc = r + dr, c + dc
        if 0 <= nr < h and 0 <= nc < w:
            yield nr, nc


def _monotone_path(h, w, rng, forbidden=frozenset()):
    """Random connected path touching all four bbox sides, or None."""
    steps = [(1, 0)] * (h - 1) + [(0, 1)] * (w - 1)
    for _ in range(80):
        rng.shuffle(steps)
        r = c = 0
        cells = {(0, 0)}
        if (0, 0) in forbidden:
            return None
        valid = True
        for dr, dc in steps:
            r += dr
            c += dc
            if (r, c) in forbidden:
                valid = False
                break
            cells.add((r, c))
        if valid:
            return cells
    return None


def _grow_shape(
    h,
    w,
    rng,
    *,
    forbidden=frozenset(),
    reserve_holes=0,
    force_right_edge=False,
    force_bottom_edge=False,
    avoid=None,
):
    """Build a connected, bbox-spanning shape with bounded random density."""
    usable = {(r, c) for r in range(h) for c in range(w)} - set(forbidden)
    max_cells = len(usable) - reserve_holes
    if max_cells < h + w - 1:
        raise ValueError("shape domain leaves too few cells for a bbox-spanning path")

    for _ in range(160):
        cells = _monotone_path(h, w, rng, forbidden)
        if cells is None:
            continue
        if force_right_edge:
            cells.update((r, w - 1) for r in range(h))
        if force_bottom_edge:
            cells.update((h - 1, c) for c in range(w))
        if cells & set(forbidden) or len(cells) > max_cells:
            continue

        room = max_cells - len(cells)
        extra_target = rng.randint(0, room) if room else 0
        for _add in range(extra_target):
            frontier = sorted(
                cell
                for cell in usable - cells
                if any(nb in cells for nb in _neighbors4(cell, h, w))
            )
            if not frontier:
                break
            cells.add(rng.choice(frontier))

        if avoid is not None and cells == set(avoid):
            continue
        return cells

    # The query-shape call always supplies an already-valid bbox-spanning
    # ``avoid`` shape plus at least one non-delta interior hole.  Random
    # monotone paths can nevertheless miss the tiny feasible set on 3x3
    # domains.  Deterministically perturb the valid shape by adding an allowed
    # boundary-adjacent hole instead of turning a legal declared/default
    # override into a seed-specific rejection.
    if avoid is not None:
        base = set(avoid)
        additions = sorted(
            cell
            for cell in usable - base
            if any(nb in base for nb in _neighbors4(cell, h, w))
        )
        if additions and len(base) + 1 <= max_cells:
            return base | {rng.choice(additions)}
    raise ValueError("unable to construct a distinct valid shape")


def _shape_dimensions(q, delta_mode, delta_count, placement_mode, difficulty, rng):
    expansion_h = delta_mode in {"expand_down", "expand_both"}
    expansion_w = delta_mode in {"expand_right", "expand_both"}
    band_cap = {"easy": 3, "medium": 4, "hard": 5}.get(difficulty, 5)
    h_max = min(band_cap, q - int(expansion_h))
    w_max = min(band_cap, q - int(expansion_w))
    if placement_mode == "offset" and not (expansion_h or expansion_w):
        # With no bbox expansion, at least one panel origin must have slack.
        h_max = min(h_max, q - 1)
    h_min = 3 if delta_mode == "within_bbox" else 2
    w_min = 3 if delta_mode == "within_bbox" else 2
    if delta_mode == "expand_right":
        h_min = max(h_min, delta_count)
    if delta_mode == "expand_down":
        w_min = max(w_min, delta_count)
    if h_min > h_max or w_min > w_max:
        raise ValueError(
            f"infeasible shape domain q={q} mode={delta_mode} count={delta_count}"
        )
    return rng.randint(h_min, h_max), rng.randint(w_min, w_max)


def _choose_delta(source, h, w, mode, count, rng):
    protected_query_hole = None
    if mode == "within_bbox":
        candidates = sorted({(r, c) for r in range(h) for c in range(w)} - source)
        # Keep one source-adjacent hole outside the edit.  It is a guaranteed
        # legal one-cell perturbation for a different query shape, even on the
        # tiny 3x3 domains exercised by the exact override matrix.
        adjacent_holes = [
            cell
            for cell in candidates
            if any(nb in source for nb in _neighbors4(cell, h, w))
        ]
        if not adjacent_holes:
            raise ValueError("within-bbox source leaves no query perturbation hole")
        protected_query_hole = rng.choice(adjacent_holes)
        candidates = [cell for cell in candidates if cell != protected_query_hole]
    elif mode == "expand_right":
        candidates = [(r, w) for r in range(h)]
    elif mode == "expand_down":
        candidates = [(h, c) for c in range(w)]
    else:
        # The corner alone expands both bbox dimensions, so count=1 remains valid.
        corner = (h, w)
        border = [(r, w) for r in range(h)] + [(h, c) for c in range(w)]
        candidates = [corner] + border
    if len(candidates) < count:
        raise ValueError(f"delta mode {mode} has only {len(candidates)} candidates")
    if mode == "expand_both":
        rest = candidates[1:]
        return {candidates[0], *rng.sample(rest, count - 1)}
    return set(rng.sample(candidates, count))


def _bbox(cells):
    if not cells:
        return None
    rs = [r for r, _ in cells]
    cs = [c for _, c in cells]
    return min(rs), min(cs), max(rs), max(cs)


def _random_position(rng, q, h, w):
    return rng.randint(0, q - h), rng.randint(0, q - w)


def _positions(q, ah, aw, bh, bw, mode, rng):
    if mode == "aligned":
        top = rng.randint(0, q - max(ah, bh))
        left = rng.randint(0, q - max(aw, bw))
        return (top, left), (top, left), (top, left)

    b_pos = _random_position(rng, q, bh, bw)
    # Force the source demonstration origin away from B.  Merely requiring
    # "not all equal" leaves an absolute-position shortcut alive in some
    # four-pair lessons.  A is always smaller in at least one dimension when
    # B fills the panel, and non-expanding offset shapes are capped below q.
    a_candidates = [
        (r, c)
        for r in range(q - ah + 1)
        for c in range(q - aw + 1)
        if (r, c) != b_pos
    ]
    if not a_candidates:
        raise ValueError("offset placement has no A origin distinct from B")
    a_pos = rng.choice(a_candidates)
    # C's source bbox is ah x aw, but it must leave room for every delta cell.
    c_pos = _random_position(rng, q, bh, bw)
    return a_pos, b_pos, c_pos


def _panel(q, cells, origin, color):
    out = [[0] * q for _ in range(q)]
    top, left = origin
    for r, c in cells:
        out[top + r][left + c] = color
    return out


def _assemble(a, b, c, q):
    n = 2 * q + 1
    grid = full_grid(n, n, 0)
    for r in range(q):
        for col in range(q):
            grid[r][col] = a[r][col]
            grid[r][q + 1 + col] = b[r][col]
            grid[q + 1 + r][col] = c[r][col]
    for col in range(n):
        grid[q][col] = 9
    for r in range(n):
        grid[r][q] = 9
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    q = ctx.draw_int_diff("quad_size", 4, 8)
    delta_count = _scheduled_int(
        ctx, "delta_count", 1, 3, 1 + (sample_index % 3)
    )
    delta_mode = _scheduled_choice(
        ctx, "delta_mode", _DELTA_MODES, _DELTA_MODES[sample_index % 4]
    )
    placement_mode = _scheduled_choice(
        ctx,
        "placement_mode",
        _PLACEMENT_MODES,
        _PLACEMENT_MODES[sample_index % 2],
    )
    query_relation = _scheduled_choice(
        ctx,
        "query_relation",
        _QUERY_RELATIONS,
        "same_shape" if sample_index % 4 == 0 else "different_shape",
    )

    dims_rng = ctx.draw_rng("shape_dimensions")
    h, w = _shape_dimensions(
        q, delta_mode, delta_count, placement_mode, difficulty, dims_rng
    )
    source_rng = ctx.draw_rng("source_shape")
    source = _grow_shape(
        h,
        w,
        source_rng,
        reserve_holes=(delta_count + 1) if delta_mode == "within_bbox" else 0,
        force_right_edge=delta_mode == "expand_right",
        force_bottom_edge=delta_mode == "expand_down",
    )
    delta = _choose_delta(
        source, h, w, delta_mode, delta_count, ctx.draw_rng("delta_cells")
    )
    target = source | delta
    target_bbox = _bbox(target)
    assert target_bbox is not None
    bh, bw = target_bbox[2] + 1, target_bbox[3] + 1

    if query_relation == "same_shape":
        query = set(source)
    else:
        query = _grow_shape(
            h,
            w,
            ctx.draw_rng("query_shape"),
            forbidden=frozenset(cell for cell in delta if cell[0] < h and cell[1] < w),
            avoid=source,
        )

    demo_color, query_color = ctx.draw_rng("colors").sample(_COLORS, 2)
    placement_rng = ctx.draw_rng("placement")
    for _attempt in range(80):
        a_pos, b_pos, c_pos = _positions(
            q, h, w, bh, bw, placement_mode, placement_rng
        )
        a = _panel(q, source, a_pos, demo_color)
        b = _panel(q, target, b_pos, demo_color)
        c = _panel(q, query, c_pos, query_color)
        grid = _assemble(a, b, c, q)
        # An offset demonstration must visibly disprove treating B-minus-A as
        # absolute panel coordinates instead of bbox-relative coordinates.
        if (
            placement_mode == "offset"
            and _absolute_position_shortcut_output(grid) == _mirror_output(grid)
        ):
            continue
        errors = self_check(grid, difficulty=difficulty)
        if not errors:
            return grid
    raise ValueError("unable to place a shortcut-rebutting valid instance")


def _split_quadrants(grid):
    h, w = len(grid), len(grid[0])
    sep_rows = [r for r in range(h) if all(grid[r][c] == 9 for c in range(w))]
    sep_cols = [c for c in range(w) if all(grid[r][c] == 9 for r in range(h))]
    if len(sep_rows) != 1 or len(sep_cols) != 1:
        raise ValueError(f"expected one full color-9 row/col, got {sep_rows}/{sep_cols}")
    qh, qw = sep_rows[0], sep_cols[0]
    if qh != qw or h != w or h != 2 * qh + 1:
        raise ValueError(f"separator does not form four equal square quadrants: {h}x{w} at {qh},{qw}")
    q = qh
    return (
        q,
        [row[:q] for row in grid[:q]],
        [row[q + 1 :] for row in grid[:q]],
        [row[:q] for row in grid[q + 1 :]],
        [row[q + 1 :] for row in grid[q + 1 :]],
    )


def _panel_info(panel):
    cells = [(r, c) for r, row in enumerate(panel) for c, value in enumerate(row) if value != 0]
    if not cells:
        return None
    r0, c0, r1, c1 = _bbox(cells)
    rel = {(r - r0, c - c0) for r, c in cells}
    colors = {panel[r][c] for r, c in cells}
    return {
        "origin": (r0, c0),
        "height": r1 - r0 + 1,
        "width": c1 - c0 + 1,
        "cells": set(cells),
        "relative": rel,
        "colors": colors,
    }


def _analysis(grid):
    q, a, b, c, answer = _split_quadrants(grid)
    ai, bi, ci = (_panel_info(panel) for panel in (a, b, c))
    if any(info is None for info in (ai, bi, ci)):
        raise ValueError("A, B, and C must be nonempty")
    delta = bi["relative"] - ai["relative"]
    if bi["height"] == ai["height"] and bi["width"] == ai["width"]:
        delta_mode = "within_bbox"
    elif bi["height"] == ai["height"] and bi["width"] == ai["width"] + 1:
        delta_mode = "expand_right"
    elif bi["height"] == ai["height"] + 1 and bi["width"] == ai["width"]:
        delta_mode = "expand_down"
    elif bi["height"] == ai["height"] + 1 and bi["width"] == ai["width"] + 1:
        delta_mode = "expand_both"
    else:
        delta_mode = "other"
    return {
        "q": q,
        "a": a,
        "b": b,
        "c": c,
        "answer": answer,
        "ai": ai,
        "bi": bi,
        "ci": ci,
        "delta": delta,
        "delta_mode": delta_mode,
    }


def observe_overrides(grid):
    info = _analysis(grid)
    origins = {info[name]["origin"] for name in ("ai", "bi", "ci")}
    return {
        "quad_size": info["q"],
        "delta_count": len(info["delta"]),
        "delta_mode": info["delta_mode"],
        "placement_mode": "aligned" if len(origins) == 1 else "offset",
        "query_relation": (
            "same_shape"
            if info["ai"]["relative"] == info["ci"]["relative"]
            else "different_shape"
        ),
    }


def _mirror_output(grid):
    """Python mirror for tests only; the Racket program remains authoritative."""
    info = _analysis(grid)
    q = info["q"]
    out = [row[:] for row in grid]
    cr0, cc0 = info["ci"]["origin"]
    query_color = next(iter(info["ci"]["colors"]))
    for r in range(q):
        for c in range(q):
            out[q + 1 + r][q + 1 + c] = info["c"][r][c]
    for dr, dc in info["delta"]:
        out[q + 1 + cr0 + dr][q + 1 + cc0 + dc] = query_color
    return out


def _absolute_position_shortcut_output(grid):
    """Wrong-answer probe: use panel-absolute B-minus-A coordinates."""
    info = _analysis(grid)
    q = info["q"]
    out = [row[:] for row in grid]
    query_color = next(iter(info["ci"]["colors"]))
    for r in range(q):
        for c in range(q):
            out[q + 1 + r][q + 1 + c] = info["c"][r][c]
    for r, c in info["bi"]["cells"] - info["ai"]["cells"]:
        out[q + 1 + r][q + 1 + c] = query_color
    return out


def self_check(grid, *, difficulty=None, meta=None):
    """Structural gate accepting canonical inputs and rejecting edit impostors."""
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return ["grid is not a nonempty list of rows"]
    width = len(grid[0])
    if width == 0 or any(not isinstance(row, list) or len(row) != width for row in grid):
        return ["grid is empty or ragged"]
    if any(
        not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["grid contains a non-integer or ARC color outside 0..9"]

    try:
        info = _analysis(grid)
    except ValueError as exc:
        return [str(exc)]

    errors = []
    q = info["q"]
    ai, bi, ci = info["ai"], info["bi"], info["ci"]
    if any(value != 0 for row in info["answer"] for value in row):
        errors.append("answer quadrant must be empty in the input")
    if any(9 in panel_info["colors"] for panel_info in (ai, bi, ci)):
        errors.append("color 9 is reserved for the separator")
    for name, panel_info in (("A", ai), ("B", bi), ("C", ci)):
        if len(panel_info["colors"]) != 1:
            errors.append(f"{name} must be monochrome, found {sorted(panel_info['colors'])}")
    if len(ai["colors"]) == len(bi["colors"]) == 1 and ai["colors"] != bi["colors"]:
        errors.append("A and B must use the same demonstration color")
    if len(ci["colors"]) == 1 and ci["colors"] == ai["colors"]:
        errors.append("C must use a different query color from A/B")

    if (ai["height"], ai["width"]) != (ci["height"], ci["width"]):
        errors.append(
            "A and C bbox dimensions differ: "
            f"{ai['height']}x{ai['width']} vs {ci['height']}x{ci['width']}"
        )
    if not ai["relative"] <= bi["relative"]:
        errors.append("B removes or shifts one or more A cells after bbox alignment")
    delta = info["delta"]
    if not delta:
        errors.append("B has no added delta cells")
    if info["delta_mode"] == "other":
        errors.append(
            "B bbox may only match A or expand by one row and/or one column"
        )
    hidden = delta & ci["relative"]
    if hidden:
        errors.append(f"C already contains delta cells, hiding the edit: {sorted(hidden)}")

    cr0, cc0 = ci["origin"]
    clipped = [(r, c) for r, c in delta if cr0 + r >= q or cc0 + c >= q]
    if clipped:
        errors.append(f"delta would be clipped when applied to C: {sorted(clipped)}")
    if not errors and _mirror_output(grid) == grid:
        errors.append("oracle is identity: the answer panel would not change")
    return errors
