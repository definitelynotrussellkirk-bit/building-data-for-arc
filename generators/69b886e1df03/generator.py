"""Generator for ``fill_each_object_s_bounding_box``.

For every 4-connected monochrome nonzero component, the canonical Racket rule
fills that component's tight bounding box with the component's own color.
Generated scenes deliberately mix components that expand with components whose
bounding boxes are already full, and sometimes reuse a color across two distant
components so a per-color (rather than per-component) shortcut is wrong.
"""
from __future__ import annotations

from collections import Counter, deque
from itertools import combinations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "69b886e1df03"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "3cad5a2fcf1f"

SUMMARY = (
    "Place 2-6 separated monochrome components on a zero background.  Every "
    "ordinary draw contains at least one irregular component whose tight "
    "bounding box has holes and at least one singleton or straight component "
    "whose bounding box is already full.  Some scenes reuse one color on two "
    "distant components.  The oracle independently fills each 4-connected "
    "component's tight bounding box with that component's color."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0 and remains the modal color",
    "there are 2-6 separated 4-connected monochrome components in at least two colors",
    "component bounding boxes are pairwise disjoint, so the oracle has no overwrite ambiguity",
    "ordinary generated draws contain both an expanding irregular component and an already-full identity component",
    "repeated-color scenes keep same-colored components disconnected and spatially separated",
]

COUNTER_HYPOTHESES = [
    "copy the input unchanged",
    "fill one bounding box per color instead of per connected component",
    "replace every object by a fixed-size rectangle",
    "fill all background cells or the global nonzero bounding box",
    "use a fixed output color rather than each component's own color",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-aware and compatibility-aware",
        "valid": "4..18",
        "doc": "Exact returned grid height.",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-aware and compatibility-aware",
        "valid": "5..18",
        "doc": "Exact returned grid width.",
    },
    "n_objects": {
        "type": "int",
        "default": "difficulty-aware 2..6",
        "valid": "2..6",
        "doc": "Exact number of 4-connected nonzero components.",
    },
}

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()

# Shapes whose bounding boxes are already full.  Singletons and dominoes are
# canonical branches; the length-three bars add harmless size variation.
_IDENTITY_SHAPES = (
    ((0, 0),),
    ((0, 0), (0, 1)),
    ((0, 0), (1, 0)),
    ((0, 0), (0, 1), (0, 2)),
    ((0, 0), (1, 0), (2, 0)),
)

# Connected shapes with at least one zero inside the tight bounding box.
_EXPANDING_SHAPES = (
    ((0, 0), (0, 1), (1, 0)),
    ((0, 0), (0, 1), (1, 1)),
    ((0, 0), (1, 0), (1, 1)),
    ((0, 1), (1, 0), (1, 1)),
    ((0, 0), (1, 0), (2, 0), (2, 1)),
    ((0, 1), (1, 1), (2, 0), (2, 1)),
    ((0, 0), (0, 1), (0, 2), (1, 1)),
    ((0, 1), (1, 0), (1, 1), (1, 2)),
    ((0, 0), (0, 1), (1, 1), (1, 2)),
    ((0, 1), (1, 0), (1, 1), (2, 0)),
    ((0, 0), (0, 2), (1, 0), (1, 1), (1, 2)),
)


def _shape_extent(shape):
    return max(r for r, _ in shape) + 1, max(c for _, c in shape) + 1


def _normalize_cells(cells):
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


_LEGAL_SHAPES = {
    _normalize_cells(shape) for shape in _IDENTITY_SHAPES + _EXPANDING_SHAPES
}


def _validate_call(difficulty, overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")
    for name, lo, hi in (
        ("grid_h", 4, 18),
        ("grid_w", 5, 18),
        ("n_objects", 2, 6),
    ):
        value = overrides.get(name)
        if value is not None and (
            type(value) is not int or not lo <= value <= hi
        ):
            raise ValueError(f"{name} must be an integer in [{lo}, {hi}]")


def _components(grid):
    """Return monochrome 4-connected nonzero components."""
    h, w = len(grid), len(grid[0])
    seen = set()
    out = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            todo = deque([(r, c)])
            seen.add((r, c))
            cells = []
            while todo:
                rr, cc = todo.popleft()
                cells.append((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        todo.append((nr, nc))
            out.append({"color": color, "cells": tuple(sorted(cells))})
    return out


def _bbox(cells):
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    return min(rows), min(cols), max(rows), max(cols)


def _rect_cells(box):
    r1, c1, r2, c2 = box
    return {(r, c) for r in range(r1, r2 + 1) for c in range(c1, c2 + 1)}


def semantic_observables(grid):
    """Recover task-linked facts from a returned input grid."""
    comps = _components(grid)
    boxes = [_bbox(comp["cells"]) for comp in comps]
    expanding = 0
    identity = 0
    edge = 0
    for comp, box in zip(comps, boxes):
        area = len(_rect_cells(box))
        if area > len(comp["cells"]):
            expanding += 1
        else:
            identity += 1
        r1, c1, r2, c2 = box
        if r1 == 0 or c1 == 0 or r2 == len(grid) - 1 or c2 == len(grid[0]) - 1:
            edge += 1
    color_counts = Counter(comp["color"] for comp in comps)
    repeated_colors = sum(count > 1 for count in color_counts.values())
    per_color_bbox_traps = 0
    for color, count in color_counts.items():
        if count < 2:
            continue
        color_comps = [comp for comp in comps if comp["color"] == color]
        all_cells = [cell for comp in color_comps for cell in comp["cells"]]
        union_area = len(_rect_cells(_bbox(all_cells)))
        component_bbox_area = sum(
            len(_rect_cells(_bbox(comp["cells"]))) for comp in color_comps
        )
        if union_area > component_bbox_area:
            per_color_bbox_traps += 1
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_objects": len(comps),
        "n_colors": len(color_counts),
        "expanding_objects": expanding,
        "identity_objects": identity,
        "edge_objects": edge,
        "repeated_colors": repeated_colors,
        "per_color_bbox_traps": per_color_bbox_traps,
    }


def observe_overrides(grid):
    facts = semantic_observables(grid)
    return {name: facts[name] for name in AXES}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the canonical-linked input grammar, not the output itself."""
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["empty grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["empty row"]
    h, w = len(grid), len(grid[0])
    errs = []
    if any(not isinstance(row, (list, tuple)) or len(row) != w for row in grid):
        return ["ragged grid"]
    if any(
        type(value) is not int or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["cells must be integer colors in 0..9"]
    counts = Counter(value for row in grid for value in row)
    if counts[0] <= max((count for color, count in counts.items() if color != 0), default=0):
        errs.append("0 must be the modal background")

    comps = _components(grid)
    if not 2 <= len(comps) <= 6:
        errs.append(f"expected 2-6 nonzero components, got {len(comps)}")
        return errs
    colors = {comp["color"] for comp in comps}
    if len(colors) < 2:
        errs.append("expected at least two nonzero colors")

    boxes = []
    identity_count = 0
    for index, comp in enumerate(comps):
        normalized = _normalize_cells(comp["cells"])
        if normalized not in _LEGAL_SHAPES:
            errs.append(f"component {index} has unsupported shape {normalized}")
        box = _bbox(comp["cells"])
        boxes.append(box)
        if len(_rect_cells(box)) == len(comp["cells"]):
            identity_count += 1
    if identity_count == 0:
        errs.append("expected at least one already-full identity component")

    for (left_i, left), (right_i, right) in combinations(enumerate(boxes), 2):
        if _rect_cells(left) & _rect_cells(right):
            errs.append(
                f"component bounding boxes {left_i} and {right_i} overlap"
            )
    return errs


def _draw_axis(ctx, overrides, name, random_lo, random_hi, valid_lo, valid_hi):
    """Use full declared bounds for explicit overrides, band bounds otherwise."""
    if name in overrides and overrides[name] is not None:
        return ctx.draw_int(name, valid_lo, valid_hi)
    return ctx.draw_int(name, random_lo, random_hi)


def _orthogonal_halo(cells):
    halo = set(cells)
    for r, c in tuple(cells):
        halo.update(((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)))
    return halo


def _place_shapes(h, w, shapes, rng, edge_first):
    occupied = set()
    reserved_boxes = set()
    placements = []
    for index, shape in enumerate(shapes):
        sh, sw = _shape_extent(shape)
        candidates = [
            (r0, c0)
            for r0 in range(h - sh + 1)
            for c0 in range(w - sw + 1)
        ]
        if index == 0 and edge_first:
            edge_candidates = [
                (r0, c0)
                for r0, c0 in candidates
                if r0 == 0 or c0 == 0 or r0 + sh == h or c0 + sw == w
            ]
            if edge_candidates:
                candidates = edge_candidates
        rng.shuffle(candidates)
        chosen = None
        for r0, c0 in candidates:
            cells = {(r0 + r, c0 + c) for r, c in shape}
            box_cells = {
                (r, c)
                for r in range(r0, r0 + sh)
                for c in range(c0, c0 + sw)
            }
            if box_cells & reserved_boxes:
                continue
            if cells & _orthogonal_halo(occupied):
                continue
            chosen = (cells, box_cells)
            break
        if chosen is None:
            return None
        cells, box_cells = chosen
        occupied.update(cells)
        reserved_boxes.update(box_cells)
        placements.append(tuple(sorted(cells)))
    return placements


def _choose_shapes(n_objects, h, w, sample_index, rng):
    expanding = [shape for shape in _EXPANDING_SHAPES if _shape_extent(shape)[0] <= h and _shape_extent(shape)[1] <= w]
    identity = [shape for shape in _IDENTITY_SHAPES if _shape_extent(shape)[0] <= h and _shape_extent(shape)[1] <= w]
    if not expanding or not identity:
        raise ValueError("grid too small for the required mixed component grammar")
    shapes = [rng.choice(expanding), rng.choice(identity)]
    for index in range(2, n_objects):
        bank = expanding if (sample_index + index) % 3 != 1 else identity
        shapes.append(rng.choice(bank))
    # Put larger footprints first after preserving the mandatory branch pair.
    tail = sorted(
        shapes[2:],
        key=lambda shape: _shape_extent(shape)[0] * _shape_extent(shape)[1],
        reverse=True,
    )
    return shapes[:2] + tail


def _assign_colors(placements, sample_index, rng):
    n_objects = len(placements)
    if n_objects >= 3 and sample_index % 3 == 1:
        palette = rng.sample(range(1, 10), n_objects - 1)
        centers = []
        for cells in placements:
            box = _bbox(cells)
            centers.append(((box[0] + box[2]) / 2, (box[1] + box[3]) / 2))
        pair = max(
            combinations(range(n_objects), 2),
            key=lambda ij: abs(centers[ij[0]][0] - centers[ij[1]][0])
            + abs(centers[ij[0]][1] - centers[ij[1]][1]),
        )
        colors = [None] * n_objects
        colors[pair[0]] = colors[pair[1]] = palette[0]
        remaining = iter(palette[1:])
        for index in range(n_objects):
            if colors[index] is None:
                colors[index] = next(remaining)
        return colors
    return rng.sample(range(1, 10), n_objects)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Build one deterministic lawful input; Racket remains output authority."""
    _validate_call(difficulty, overrides)
    requested_n = overrides.get("n_objects")
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    if difficulty == "easy":
        h_lo, h_hi = 4, 7
        w_lo, w_hi = 5, 8
    elif difficulty == "hard":
        h_lo, h_hi = 8, 14
        w_lo, w_hi = 9, 15
    else:
        h_lo, h_hi = 5, 10
        w_lo, w_hi = 6, 11

    # A single n_objects boundary override must work in every band.  Raise the
    # default canvas floor before drawing rather than drawing and clamping later.
    if requested_n is not None and requested_n >= 5:
        h_lo = max(h_lo, 9)
        w_lo = max(w_lo, 9)
        h_hi = max(h_hi, h_lo)
        w_hi = max(w_hi, w_lo)
    if requested_n is None and sample_index % 3 == 1:
        # The repeated-color lesson lane needs at least three components.
        h_lo = max(h_lo, 5)
        w_lo = max(w_lo, 6)
    h = _draw_axis(ctx, overrides, "grid_h", h_lo, h_hi, 4, 18)
    w = _draw_axis(ctx, overrides, "grid_w", w_lo, w_hi, 5, 18)

    if requested_n is not None:
        n_objects = ctx.draw_int("n_objects", 2, 6)
    else:
        rough_cap = max(2, min(6, (h * w) // 10))
        if difficulty == "easy":
            n_lo, n_hi = 2, min(3, rough_cap)
        elif difficulty == "hard":
            n_lo, n_hi = min(4, rough_cap), rough_cap
        else:
            n_lo, n_hi = min(3, rough_cap), min(5, rough_cap)
        if sample_index % 3 == 1:
            # EXAMPLES_NEEDED=3 uses consecutive sample indices.  Reserve the
            # middle lane for a repeated-color counterexample so every ordinary
            # three-demo lesson refutes the tempting per-color bbox shortcut.
            n_lo = max(n_lo, 3)
        n_lo = min(n_lo, n_hi)
        n_objects = ctx.draw_int("n_objects", n_lo, n_hi)

    layout_rng = ctx.draw_rng("layout")
    placements = None
    for attempt in range(240):
        shapes = _choose_shapes(
            n_objects,
            h,
            w,
            sample_index + attempt,
            layout_rng,
        )
        placements = _place_shapes(
            h,
            w,
            shapes,
            layout_rng,
            edge_first=(sample_index % 4 == 0),
        )
        if placements is not None:
            break
    if placements is None:
        raise ValueError(
            f"incompatible grid/object overrides: cannot place {n_objects} "
            f"separated components in {h}x{w}"
        )

    colors = _assign_colors(placements, sample_index, ctx.draw_rng("colors"))
    grid = full_grid(h, w, 0)
    for color, cells in zip(colors, placements):
        for r, c in cells:
            grid[r][c] = color

    errors = self_check(grid, difficulty=difficulty, meta={"overrides": overrides})
    if errors:
        raise AssertionError(f"internal generator invariant failed: {errors}")
    facts = semantic_observables(grid)
    if facts["expanding_objects"] < 1 or facts["identity_objects"] < 1:
        raise AssertionError("ordinary draw did not expose both rule branches")
    return grid
