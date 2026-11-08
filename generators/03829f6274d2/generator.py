"""Generator for arc_puzzle_bank_third21:H16.

Rule: the input contains one connected, single-colour template object and
several colour-9 anchor cells.  The output is a blank grid with an unchanged
copy of the template stamped at every anchor, using each anchor as the
normalised template's top-left corner.  The original template and the colour-9
anchors disappear.

The normal teaching distribution keeps every stamp fully in bounds.  The
``edge_fit`` texture deliberately puts at least one complete stamp exactly
against an outer edge; it does *not* teach clipping beyond the board.
"""
from __future__ import annotations

from collections import deque
from typing import Any, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "03829f6274d2"
TASK_ID = GENERATOR_ID
RULE_HASH = "dac192e5427e"  # sha256(normalized canonical program_solution)[:12]
VERSION = "2.0.0"

SUMMARY = (
    "One connected non-0/non-9 template and 1-8 colour-9 anchors.  Start from "
    "a blank grid and stamp the template, without rotation or recolouring, at "
    "every anchor using the anchor as the template bounding-box top-left.  "
    "Erase the source template and all anchors.  Edge examples fit exactly; "
    "ordinary examples never rely on out-of-bounds clipping."
)

EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 0.35

INVARIANTS = [
    "the grid is rectangular with background colour 0",
    "exactly one 4-connected template object exists, using one colour in 1..8",
    "the template has 2..7 cells and is not a solid rectangle on ordinary draws",
    "there are 1..8 distinct colour-9 anchor cells",
    "every anchor's complete normalised template footprint is in bounds",
    "edge_fit means at least one complete footprint touches an outer grid edge",
]

HELPFUL_TEXTURES = ("plain", "edge_fit")
DEGENERATE_TEXTURES: tuple[str, ...] = ()

AXES = {
    "grid_h": {
        "type": "int",
        "default": "scheduled canonical 8/10 or difficulty-aware 8..17",
        "valid": "8..17",
        "doc": "Grid height; exact overrides are honoured in every band.",
    },
    "grid_w": {
        "type": "int",
        "default": "scheduled canonical 8/10 or difficulty-aware 8..18",
        "valid": "8..18",
        "doc": "Grid width; exact overrides are honoured in every band.",
    },
    "n_markers": {
        "type": "int",
        "default": "scheduled 2,3,4 or difficulty-aware 3..7",
        "valid": "1..8",
        "doc": "Exact number of colour-9 stamp anchors.",
    },
    "template_size": {
        "type": "int",
        "default": "scheduled 3,4,5..7",
        "valid": "2..7",
        "doc": "Exact number of cells in the connected template.",
    },
    "template_color": {
        "type": "color",
        "default": "rng 1..8",
        "valid": "1..8",
        "doc": "The template and output-stamp colour.",
    },
    "texture": {
        "type": "str",
        "default": "scheduled plain|edge_fit",
        "valid": "plain|edge_fit",
        "doc": "Whether no stamp or at least one complete stamp touches an edge.",
    },
}

# Connected, non-solid motifs.  D4 transforms provide orientation diversity
# while retaining exact cell count and 4-connectivity.
_BASE_MOTIFS: dict[int, tuple[tuple[tuple[int, int], ...], ...]] = {
    2: (
        ((0, 0), (0, 1)),
    ),
    3: (
        ((0, 0), (1, 0), (1, 1)),
    ),
    4: (
        ((0, 0), (0, 1), (0, 2), (1, 1)),
        ((0, 0), (1, 0), (2, 0), (2, 1)),
        ((0, 0), (0, 1), (1, 1), (1, 2)),
    ),
    5: (
        ((0, 0), (0, 1), (1, 0), (1, 1), (2, 0)),
        ((0, 0), (0, 2), (1, 0), (1, 1), (1, 2)),
        ((0, 0), (1, 0), (1, 1), (2, 1), (2, 2)),
    ),
    6: (
        ((0, 0), (1, 0), (1, 1), (2, 1), (2, 2), (3, 2)),
        ((0, 0), (0, 1), (0, 2), (1, 0), (2, 0), (2, 1)),
    ),
    7: (
        ((0, 0), (0, 1), (1, 1), (1, 2), (2, 2), (2, 3), (3, 3)),
        ((0, 0), (1, 0), (2, 0), (2, 1), (2, 2), (1, 2), (3, 2)),
    ),
}


def _normalise(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(cells)
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def _transform(cells: Iterable[tuple[int, int]], index: int) -> tuple[tuple[int, int], ...]:
    def one(r: int, c: int) -> tuple[int, int]:
        return (
            (r, c),
            (c, -r),
            (-r, -c),
            (-c, r),
            (r, -c),
            (-c, -r),
            (-r, c),
            (c, r),
        )[index]

    return _normalise(one(r, c) for r, c in cells)


def _orbit_size(cells: Iterable[tuple[int, int]]) -> int:
    return len({_transform(cells, i) for i in range(8)})


def _shape(rng: Any, size: int) -> tuple[tuple[int, int], ...]:
    choices = _BASE_MOTIFS[size]
    base = rng.choice(choices)
    return _transform(base, rng.randrange(8))


def _bbox(cells: Iterable[tuple[int, int]]) -> tuple[int, int, int, int]:
    cells = tuple(cells)
    rs = [r for r, _ in cells]
    cs = [c for _, c in cells]
    return min(rs), min(cs), max(rs), max(cs)


def _is_connected(cells: set[tuple[int, int]]) -> bool:
    if not cells:
        return False
    seen = {next(iter(cells))}
    queue = deque(seen)
    while queue:
        r, c = queue.popleft()
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            q = (r + dr, c + dc)
            if q in cells and q not in seen:
                seen.add(q)
                queue.append(q)
    return seen == cells


def _has_override(ctx: Any, label: str) -> bool:
    return label in ctx.overrides and ctx.overrides[label] is not None


def _draw_int(
    ctx: Any,
    label: str,
    default_bounds: tuple[int, int],
    valid_bounds: tuple[int, int],
) -> int:
    return ctx.draw_int(
        label,
        *(valid_bounds if _has_override(ctx, label) else default_bounds),
    )


def _draw_choice(
    ctx: Any,
    label: str,
    default_options: tuple[str, ...],
    valid_options: tuple[str, ...],
) -> str:
    return ctx.draw_choice(
        label,
        valid_options if _has_override(ctx, label) else default_options,
    )


def _scheduled_defaults(sample_index: int, difficulty: Any) -> dict[str, Any]:
    """Four-slot lesson schedule.

    Slots 0/1 anchor the exact canonical scale.  Slots 2/3 force shape-size,
    marker-count, and edge-role contrasts so four consecutive demonstrations
    identify stamping rather than marker painting, bounding-box filling, or a
    fixed-size/fixed-position shortcut.
    """
    slot = sample_index % 4
    if slot == 0:
        return {
            "grid_h": (8, 8), "grid_w": (8, 8),
            "n_markers": (2, 2), "template_size": (4, 4),
            "texture": ("edge_fit",),
        }
    if slot == 1:
        return {
            "grid_h": (10, 10), "grid_w": (10, 10),
            "n_markers": (3, 3), "template_size": (4, 4),
            "texture": ("edge_fit",),
        }

    if difficulty == "easy":
        h_bounds, w_bounds = (8, 11), (8, 12)
        late_size, late_markers = 5, 3
    elif difficulty == "hard":
        h_bounds, w_bounds = (13, 17), (14, 18)
        late_size, late_markers = 7, 7
    else:
        h_bounds, w_bounds = (10, 14), (10, 15)
        late_size, late_markers = 6, 5

    if slot == 2:
        return {
            "grid_h": h_bounds, "grid_w": w_bounds,
            "n_markers": (4, 4), "template_size": (3, 3),
            "texture": ("plain",),
        }
    return {
        "grid_h": h_bounds, "grid_w": w_bounds,
        "n_markers": (late_markers, late_markers),
        "template_size": (late_size, late_size),
        "texture": ("edge_fit",),
    }


def _touches_edge(anchor: tuple[int, int], sh: int, sw: int, h: int, w: int) -> bool:
    r, c = anchor
    return r == 0 or c == 0 or r + sh == h or c + sw == w


def _choose_spread(
    rng: Any,
    candidates: list[tuple[int, int]],
    count: int,
    initial: list[tuple[int, int]] | None = None,
) -> list[tuple[int, int]]:
    chosen = list(initial or [])
    remaining = [p for p in candidates if p not in chosen]
    rng.shuffle(remaining)
    while len(chosen) < count and remaining:
        if not chosen:
            chosen.append(remaining.pop())
            continue
        best_i = max(
            range(len(remaining)),
            key=lambda i: (
                min(abs(remaining[i][0] - q[0]) + abs(remaining[i][1] - q[1]) for q in chosen),
                rng.random(),
            ),
        )
        chosen.append(remaining.pop(best_i))
    return chosen


def _construct(
    rng: Any,
    h: int,
    w: int,
    size: int,
    n_markers: int,
    template_color: int,
    texture: str,
    canonical_slot: bool,
) -> list[list[int]]:
    for _shape_attempt in range(80):
        motif = _shape(rng, size)
        _, _, r1, c1 = _bbox(motif)
        sh, sw = r1 + 1, c1 + 1
        if sh > h or sw > w:
            continue

        placements = [(r, c) for r in range(h - sh + 1) for c in range(w - sw + 1)]
        rng.shuffle(placements)
        if canonical_slot:
            placements.sort(
                key=lambda p: (
                    p[0] in (0, h - sh) or p[1] in (0, w - sw),
                    abs((p[0] + sh / 2) - h / 2) + abs((p[1] + sw / 2) - w / 2),
                )
            )
        else:
            # Trying edge/corner source placements first leaves the interior
            # anchor codomain large enough for the n_markers=8 boundary.
            placements.sort(
                key=lambda p: not (
                    p[0] in (0, h - sh) or p[1] in (0, w - sw)
                )
            )

        for tr, tc in placements:
            template_abs = {(tr + r, tc + c) for r, c in motif}
            full = [
                (r, c)
                for r in range(h - sh + 1)
                for c in range(w - sw + 1)
                if (r, c) not in template_abs
            ]
            edge = [p for p in full if _touches_edge(p, sh, sw, h, w)]
            interior = [p for p in full if not _touches_edge(p, sh, sw, h, w)]

            if texture == "plain":
                if len(interior) < n_markers:
                    continue
                anchors = _choose_spread(rng, interior, n_markers)
            else:
                if not edge or len(full) < n_markers:
                    continue
                first = rng.choice(edge)
                initial = [first]
                if n_markers >= 2 and interior:
                    initial.append(rng.choice(interior))
                anchors = _choose_spread(rng, full, n_markers, initial)
            if len(anchors) != n_markers:
                continue

            g = full_grid(h, w, 0)
            for r, c in template_abs:
                g[r][c] = template_color
            for r, c in anchors:
                # The anchor cell itself must stay visibly colour 9; placements
                # whose anchor overlaps a source-template cell were excluded.
                g[r][c] = 9
            return g

    raise ValueError(
        "incompatible axis combination: could not place one template and the "
        f"requested {n_markers} {texture} anchors on {h}x{w}"
    )


def generate(seed: int, sample_index: int, *, difficulty: Any = None, **overrides: Any):
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    defaults = _scheduled_defaults(sample_index, difficulty)
    h = _draw_int(ctx, "grid_h", defaults["grid_h"], (8, 17))
    w = _draw_int(ctx, "grid_w", defaults["grid_w"], (8, 18))
    n_markers = _draw_int(ctx, "n_markers", defaults["n_markers"], (1, 8))
    template_size = _draw_int(ctx, "template_size", defaults["template_size"], (2, 7))
    template_color = ctx.draw_color("template_color", exclude=(0, 9))
    texture = _draw_choice(ctx, "texture", defaults["texture"], HELPFUL_TEXTURES)
    rng = ctx.draw_rng("layout")
    return _construct(
        rng,
        h,
        w,
        template_size,
        n_markers,
        template_color,
        texture,
        canonical_slot=sample_index % 4 in (0, 1),
    )


def _analyse(grid: Any) -> tuple[dict[str, Any], list[str]]:
    reasons: list[str] = []
    if not isinstance(grid, (list, tuple)) or not grid:
        return {}, ["grid must be a nonempty row sequence"]
    if not all(isinstance(row, (list, tuple)) for row in grid):
        return {}, ["every grid row must be a sequence"]
    widths = {len(row) for row in grid}
    if len(widths) != 1 or not widths or next(iter(widths)) == 0:
        return {}, ["grid must be a nonempty rectangle"]
    h, w = len(grid), len(grid[0])

    invalid = [
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 9
    ]
    if invalid:
        reasons.append(f"grid contains invalid ARC values, first={invalid[0]}")

    template_cells = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value not in (0, 9)
    }
    template_colors = {
        grid[r][c] for r, c in template_cells
    }
    markers = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 9
    ]
    if not template_cells:
        reasons.append("missing non-0/non-9 template")
        return {
            "grid_h": h, "grid_w": w, "n_markers": len(markers),
        }, reasons
    if len(template_colors) != 1:
        reasons.append(f"template must use one colour, found {sorted(template_colors)}")
    if not _is_connected(template_cells):
        reasons.append("template cells are not one 4-connected object")

    r0, c0, r1, c1 = _bbox(template_cells)
    norm = _normalise(template_cells)
    sh, sw = r1 - r0 + 1, c1 - c0 + 1
    out_of_bounds = [
        marker
        for marker in markers
        if marker[0] + sh > h or marker[1] + sw > w
    ]
    if out_of_bounds:
        reasons.append(
            "anchor footprints must be fully in bounds; first bad anchor="
            f"{out_of_bounds[0]} for template {sh}x{sw}"
        )
    edge_fit = any(_touches_edge(m, sh, sw, h, w) for m in markers)
    info = {
        "grid_h": h,
        "grid_w": w,
        "n_markers": len(markers),
        "template_size": len(template_cells),
        "template_color": next(iter(template_colors)) if len(template_colors) == 1 else None,
        "texture": "edge_fit" if edge_fit else "plain",
        "template_cells": template_cells,
        "template_norm": norm,
        "template_bbox": (r0, c0, r1, c1),
        "template_h": sh,
        "template_w": sw,
        "markers": tuple(markers),
        "edge_fit": edge_fit,
        "interior_anchor": any(not _touches_edge(m, sh, sw, h, w) for m in markers),
        "orbit_size": _orbit_size(norm),
    }
    return info, reasons


def observe_overrides(grid: Any) -> dict[str, int | str | None]:
    info, _ = _analyse(grid)
    return {
        axis: info[axis]
        for axis in (
            "grid_h", "grid_w", "n_markers", "template_size",
            "template_color", "texture",
        )
        if axis in info
    }


def self_check(grid: Any, *, difficulty: Any = None, meta: Any = None) -> list[str]:
    info, reasons = _analyse(grid)
    if reasons:
        return reasons
    if not (8 <= info["grid_h"] <= 17):
        reasons.append(f"grid_h outside 8..17: {info['grid_h']}")
    if not (8 <= info["grid_w"] <= 18):
        reasons.append(f"grid_w outside 8..18: {info['grid_w']}")
    if not (1 <= info["n_markers"] <= 8):
        reasons.append(f"expected 1..8 colour-9 anchors, found {info['n_markers']}")
    if not (2 <= info["template_size"] <= 7):
        reasons.append(f"expected template size 2..7, found {info['template_size']}")
    if info["template_color"] not in range(1, 9):
        reasons.append(f"template colour must be 1..8, found {info['template_color']}")
    return reasons


def strict_canonical_like(grid: Any) -> list[str]:
    info, reasons = _analyse(grid)
    if reasons:
        return reasons
    strict: list[str] = []
    if (info["grid_h"], info["grid_w"]) not in {(8, 8), (10, 10)}:
        strict.append("canonical grids are 8x8 or 10x10")
    if info["template_size"] != 4:
        strict.append("canonical template size is 4")
    if info["n_markers"] not in (2, 3):
        strict.append("canonical examples use 2 or 3 anchors")
    if not info["edge_fit"]:
        strict.append("canonical examples include an exactly edge-fitted stamp")
    r0, c0, r1, c1 = info["template_bbox"]
    if (r1 - r0 + 1) * (c1 - c0 + 1) == info["template_size"]:
        strict.append("canonical template is non-rectangular")
    return strict


def _witness_multiple_markers(grid: Any) -> bool:
    info, reasons = _analyse(grid)
    return not reasons and info["n_markers"] >= 2


def _witness_three_markers(grid: Any) -> bool:
    info, reasons = _analyse(grid)
    return not reasons and info["n_markers"] >= 3


def _witness_edge_fit(grid: Any) -> bool:
    info, reasons = _analyse(grid)
    return not reasons and info["edge_fit"]


def _witness_interior_anchor(grid: Any) -> bool:
    info, reasons = _analyse(grid)
    return not reasons and info["interior_anchor"]


def _witness_non_rectangular(grid: Any) -> bool:
    info, reasons = _analyse(grid)
    if reasons:
        return False
    r0, c0, r1, c1 = info["template_bbox"]
    return (r1 - r0 + 1) * (c1 - c0 + 1) > info["template_size"]


def _witness_orientation_sensitive(grid: Any) -> bool:
    info, reasons = _analyse(grid)
    return not reasons and info["orbit_size"] >= 4


SEMANTIC_WITNESSES = {
    "multiple_markers": _witness_multiple_markers,
    "three_or_more_markers": _witness_three_markers,
    "edge_aligned_complete_stamp": _witness_edge_fit,
    "interior_complete_stamp": _witness_interior_anchor,
    "non_rectangular_template": _witness_non_rectangular,
    "orientation_sensitive_template": _witness_orientation_sensitive,
}


def _solve_python(grid: Any) -> list[list[int]]:
    info, reasons = _analyse(grid)
    if reasons:
        raise ValueError("; ".join(reasons))
    h, w = info["grid_h"], info["grid_w"]
    out = full_grid(h, w, 0)
    color = info["template_color"]
    for mr, mc in info["markers"]:
        for dr, dc in info["template_norm"]:
            out[mr + dr][mc + dc] = color
    return out


def lesson_identifiable(demos: list[dict[str, Any]], query: dict[str, Any]) -> list[str]:
    reasons: list[str] = []
    if len(demos) < EXAMPLES_NEEDED:
        reasons.append(f"need at least {EXAMPLES_NEEDED} demonstrations")
        return reasons

    infos: list[dict[str, Any]] = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} is not an input/output pair")
            continue
        info, bad = _analyse(pair["input"])
        if bad:
            reasons.append(f"demo {index} malformed: {bad[0]}")
            continue
        try:
            expected = _solve_python(pair["input"])
        except ValueError as exc:
            reasons.append(f"demo {index} cannot be solved structurally: {exc}")
            continue
        if pair["output"] != expected:
            reasons.append(f"demo {index} output does not stamp the exact template at every anchor")
        infos.append(info)

    if len(infos) != len(demos):
        return reasons
    marker_counts = {info["n_markers"] for info in infos}
    shapes = {info["template_norm"] for info in infos}
    sizes = {info["template_size"] for info in infos}
    textures = {info["texture"] for info in infos}
    dimensions = {(info["grid_h"], info["grid_w"]) for info in infos}
    if max(marker_counts) < 3:
        reasons.append("demonstrations never require stamping three or more anchors")
    if len(marker_counts) < 2:
        reasons.append("marker count is fixed across demonstrations")
    if len(shapes) < 2 or len(sizes) < 2:
        reasons.append("template geometry/size does not vary across demonstrations")
    if textures != {"plain", "edge_fit"}:
        reasons.append("demonstrations do not contrast interior and exact edge-fit anchors")
    if len(dimensions) < 3:
        reasons.append("grid size is too fixed across demonstrations")
    if not all(_witness_non_rectangular(pair["input"]) for pair in demos):
        reasons.append("a solid bounding-box template admits a fill-the-box shortcut")

    if not isinstance(query, dict) or "input" not in query:
        reasons.append("query is not an input/output pair")
    else:
        qinfo, qbad = _analyse(query["input"])
        if qbad:
            reasons.append(f"query malformed: {qbad[0]}")
        elif qinfo["n_markers"] < 1:
            reasons.append("query has no anchor to apply the learned operation")
    return reasons
