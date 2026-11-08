"""Generator for ``bf5bed969a6d`` — stamp the red template into frames.

The unique color-2 object is a shape template.  The oracle removes that
source object, keeps every non-background same-color component, and stamps a
copy of the normalized template at the centered interior position of each
component, recolored to that component's color.  Canonical examples include
both ordinary disjoint hollow frames and an occluded-frame case where one
frame color is split into multiple components, so the distribution exercises
both object topologies.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "bf5bed969a6d"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "39419b6b1cfb"

SUMMARY = (
    "A 0-background grid contains one connected color-2 template and two "
    "colored rectangular frame outlines.  Frames may be disjoint or one may "
    "occlude cells of the other, splitting a frame color into multiple "
    "same-color components.  The output is a fresh 0 canvas containing every "
    "non-2 component plus a centered, frame-colored copy of the normalized "
    "template inside each such component; the source template disappears."
)

INVARIANTS = [
    "background is 0 and all cells are ARC colors 0..9",
    "exactly one connected color-2 template from the supported shape bank",
    "exactly two distinct non-{0,2} frame colors",
    "each frame color reconstructs a hollow rectangle, allowing border cells overwritten by the other frame",
    "the Racket transform is deterministic, input-pure, and non-identity",
]

_PROFILE_KINDS = (
    "canonical_0",
    "canonical_1",
    "canonical_2",
    "canonical_3",
    "generalized",
)
_OVERLAP_KINDS = ("disjoint", "occluded")
_PALETTE_KINDS = ("low", "mid", "high", "split")
_PALETTE_PAIRS = {
    "low": (1, 3),
    "mid": (4, 6),
    "high": (7, 9),
    "split": (5, 8),
}

AXES = {
    "grid_h": {"type": "int", "default": "rng 10..20", "valid": "10..20"},
    "grid_w": {"type": "int", "default": "rng 13..22", "valid": "13..22"},
    "profile_kind": {
        "type": "str",
        "default": "rng canonical_0|canonical_1|canonical_2|canonical_3|generalized",
        "valid": "|".join(_PROFILE_KINDS),
    },
    "overlap_kind": {
        "type": "str",
        "default": "rng disjoint|occluded",
        "valid": "|".join(_OVERLAP_KINDS),
    },
    "palette_kind": {
        "type": "str",
        "default": "rng low|mid|high|split",
        "valid": "|".join(_PALETTE_KINDS),
    },
}

# The four task-linked geometry families.  Frame dimensions are full outline
# dimensions, not interior dimensions.  The first three linked official
# profiles are disjoint; canonical_3 is the occluded profile.
_PROFILE_SPECS = {
    "canonical_0": {
        "template": ((0, 0), (1, 0), (1, 1)),
        "frames": ((5, 5), (4, 4)),
    },
    "canonical_1": {
        "template": ((0, 0), (0, 1), (1, 1), (1, 2)),
        "frames": ((4, 7), (5, 5)),
    },
    "canonical_2": {
        "template": ((0, 1), (1, 0), (1, 1), (1, 2)),
        "frames": ((5, 7), (4, 5)),
    },
    "canonical_3": {
        "template": ((0, 0), (1, 0), (2, 0), (2, 1), (2, 2)),
        "frames": ((5, 5), (7, 7)),
    },
}

_GENERAL_TEMPLATES = (
    ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1)),
    ((0, 0), (1, 0), (2, 0), (2, 1)),
    ((0, 0), (0, 1), (1, 1), (2, 1), (2, 2)),
    ((0, 1), (1, 1), (2, 0), (2, 1), (2, 2)),
)


def _components_4_same_color(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    out = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0 or (r, c) in seen:
                continue
            color = grid[r][c]
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                cr, cc = stack.pop()
                cells.append((cr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = cr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            out.append((color, tuple(cells)))
    return out


def _bbox(cells):
    return (
        min(r for r, _ in cells),
        min(c for _, c in cells),
        max(r for r, _ in cells),
        max(c for _, c in cells),
    )


def _normalize(cells):
    r0, c0, _, _ = _bbox(cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def _transform_cells(cells, transform):
    cells = tuple(cells)
    h = max(r for r, _ in cells) + 1
    w = max(c for _, c in cells) + 1
    if transform == 0:
        raw = cells
    elif transform == 1:  # rotate 90 clockwise
        raw = tuple((c, h - 1 - r) for r, c in cells)
    elif transform == 2:
        raw = tuple((h - 1 - r, w - 1 - c) for r, c in cells)
    elif transform == 3:
        raw = tuple((w - 1 - c, r) for r, c in cells)
    elif transform == 4:  # left-right reflection
        raw = tuple((r, w - 1 - c) for r, c in cells)
    elif transform == 5:
        raw = tuple((c, r) for r, c in cells)
    elif transform == 6:
        raw = tuple((h - 1 - r, c) for r, c in cells)
    elif transform == 7:
        raw = tuple((w - 1 - c, h - 1 - r) for r, c in cells)
    else:
        raise ValueError(f"unknown D4 transform {transform}")
    return _normalize(raw)


def _shape_key(cells):
    return min(_transform_cells(_normalize(cells), k) for k in range(8))


def _grid_transform(grid, transform):
    h, w = len(grid), len(grid[0])
    cells = [(r, c, grid[r][c]) for r in range(h) for c in range(w)]
    if transform == 0:
        nh, nw = h, w
        conv = lambda r, c: (r, c)
    elif transform == 1:
        nh, nw = w, h
        conv = lambda r, c: (c, h - 1 - r)
    elif transform == 2:
        nh, nw = h, w
        conv = lambda r, c: (h - 1 - r, w - 1 - c)
    elif transform == 3:
        nh, nw = w, h
        conv = lambda r, c: (w - 1 - c, r)
    elif transform == 4:
        nh, nw = h, w
        conv = lambda r, c: (r, w - 1 - c)
    elif transform == 5:
        nh, nw = w, h
        conv = lambda r, c: (c, r)
    elif transform == 6:
        nh, nw = h, w
        conv = lambda r, c: (h - 1 - r, c)
    elif transform == 7:
        nh, nw = w, h
        conv = lambda r, c: (w - 1 - c, h - 1 - r)
    else:
        raise ValueError(f"unknown D4 transform {transform}")
    out = full_grid(nh, nw, 0)
    for r, c, value in cells:
        rr, cc = conv(r, c)
        out[rr][cc] = value
    return out


def _crop_nonzero(grid):
    cells = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 0
    ]
    if not cells:
        return [[0]]
    r0, c0, r1, c1 = _bbox(cells)
    return [row[c0 : c1 + 1] for row in grid[r0 : r1 + 1]]


def _draw_frame(grid, r0, c0, fh, fw, color):
    for c in range(c0, c0 + fw):
        grid[r0][c] = color
        grid[r0 + fh - 1][c] = color
    for r in range(r0, r0 + fh):
        grid[r][c0] = color
        grid[r][c0 + fw - 1] = color


def _build_disjoint(template, frame_dims, colors):
    (fh1, fw1), (fh2, fw2) = frame_dims
    th = max(r for r, _ in template) + 1
    tw = max(c for _, c in template) + 1
    top_h = max(fh1, fh2)
    width = fw1 + 1 + fw2
    height = top_h + th
    grid = full_grid(height, max(width, tw), 0)
    _draw_frame(grid, 0, 0, fh1, fw1, colors[0])
    _draw_frame(grid, 0, width - fw2, fh2, fw2, colors[1])
    tr0 = top_h
    tc0 = 0
    for dr, dc in template:
        grid[tr0 + dr][tc0 + dc] = 2
    return _crop_nonzero(grid)


def _build_occluded(template, frame_dims, colors):
    # Canonical-style crossing: frame 2 begins two rows above frame 1's
    # bottom and overwrites exactly part of frame 1's border.  The template
    # stays in the upper-left free corner.
    (fh1, fw1), (fh2, fw2) = frame_dims
    th = max(r for r, _ in template) + 1
    tw = max(c for _, c in template) + 1
    a_r, a_c = 0, max(tw + 1, fw2 - 2)
    b_r, b_c = max(th, fh1 - 4), 0
    height = max(a_r + fh1, b_r + fh2)
    width = max(a_c + fw1, b_c + fw2)
    grid = full_grid(height, width, 0)
    _draw_frame(grid, a_r, a_c, fh1, fw1, colors[0])
    _draw_frame(grid, b_r, b_c, fh2, fw2, colors[1])
    for dr, dc in template:
        grid[dr][dc] = 2
    return _crop_nonzero(grid)


def _general_spec(rng):
    template = rng.choice(_GENERAL_TEMPLATES)
    th = max(r for r, _ in template) + 1
    tw = max(c for _, c in template) + 1
    frames = [
        [min(th + rng.randint(2, 4), 7), min(tw + rng.randint(2, 5), 7)],
        [min(th + rng.randint(2, 5), 7), min(tw + rng.randint(2, 4), 7)],
    ]
    # Keep the disjoint tight motif inside the minimum 10x13 canvas.
    while frames[0][1] + 1 + frames[1][1] > 13:
        idx = 0 if frames[0][1] >= frames[1][1] else 1
        floor = tw + 2
        if frames[idx][1] <= floor:
            idx = 1 - idx
        frames[idx][1] -= 1
    return {"template": template, "frames": tuple(tuple(x) for x in frames)}


def _place_motif(motif, h, w, rng):
    fitting = []
    for transform in range(8):
        candidate = _grid_transform(motif, transform)
        ch, cw = len(candidate), len(candidate[0])
        if ch <= h and cw <= w:
            fitting.append(candidate)
    if not fitting:
        mh, mw = len(motif), len(motif[0])
        raise ValueError(f"motif {mh}x{mw} does not fit requested grid {h}x{w}")
    candidate = rng.choice(fitting)
    ch, cw = len(candidate), len(candidate[0])
    r0 = rng.randint(0, h - ch)
    c0 = rng.randint(0, w - cw)
    out = full_grid(h, w, 0)
    for r in range(ch):
        for c in range(cw):
            if candidate[r][c] != 0:
                out[r0 + r][c0 + c] = candidate[r][c]
    return out


def _recolor_frames(grid, colors):
    old = sorted({value for row in grid for value in row if value not in (0, 2)})
    if len(old) != 2:
        return [row[:] for row in grid]
    mapping = {old[0]: colors[0], old[1]: colors[1]}
    return [
        [mapping.get(value, value) for value in row]
        for row in grid
    ]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    h = ctx.draw_int("grid_h", 10, 20)
    w = ctx.draw_int("grid_w", 13, 22)
    profile_kind = ctx.draw_choice("profile_kind", _PROFILE_KINDS)
    overlap_kind = ctx.draw_choice("overlap_kind", _OVERLAP_KINDS)
    palette_kind = ctx.draw_choice("palette_kind", _PALETTE_KINDS)
    band_salt = difficulty if difficulty in ("easy", "medium", "hard") else "mixed"
    rng = ctx.draw_rng(f"layout:{band_salt}")

    spec = _general_spec(rng) if profile_kind == "generalized" else _PROFILE_SPECS[profile_kind]
    colors = list(_PALETTE_PAIRS[palette_kind])
    if rng.randrange(2):
        colors.reverse()
    if overlap_kind == "disjoint":
        motif = _build_disjoint(spec["template"], spec["frames"], colors)
    else:
        motif = _build_occluded(spec["template"], spec["frames"], colors)
    return _place_motif(motif, h, w, rng)


def _frame_descriptors(grid):
    comps = _components_4_same_color(grid)
    colors = sorted({color for color, _ in comps if color not in (0, 2)})
    descriptors = []
    for color in colors:
        color_cells = [
            (r, c)
            for r, row in enumerate(grid)
            for c, value in enumerate(row)
            if value == color
        ]
        if not color_cells:
            continue
        r0, c0, r1, c1 = _bbox(color_cells)
        border = {
            (r, c)
            for r in range(r0, r1 + 1)
            for c in range(c0, c1 + 1)
            if r in (r0, r1) or c in (c0, c1)
        }
        component_count = sum(1 for comp_color, _ in comps if comp_color == color)
        missing = sum(grid[r][c] != color for r, c in border)
        overwritten = sum(grid[r][c] not in (0, color) for r, c in border)
        descriptors.append(
            {
                "color": color,
                "dims": tuple(sorted((r1 - r0 + 1, c1 - c0 + 1))),
                "bbox": (r0, c0, r1, c1),
                "components": component_count,
                "missing": missing,
                "overwritten": overwritten,
                "cells": tuple(color_cells),
                "border": border,
            }
        )
    return descriptors


def _classify_profile(grid):
    comps = _components_4_same_color(grid)
    templates = [cells for color, cells in comps if color == 2]
    if len(templates) != 1:
        return "generalized"
    shape = _shape_key(templates[0])
    frames = sorted(_frame_descriptors(grid), key=lambda item: item["dims"])
    if len(frames) != 2:
        return "generalized"
    dims = tuple(item["dims"] for item in frames)
    for name, spec in _PROFILE_SPECS.items():
        expected_shape = _shape_key(spec["template"])
        expected_dims = tuple(sorted(tuple(sorted(d)) for d in spec["frames"]))
        if shape == expected_shape and dims == expected_dims:
            return name
    return "generalized"


def _classify_overlap(grid):
    return "occluded" if any(item["missing"] for item in _frame_descriptors(grid)) else "disjoint"


def canonical_profile_signature(grid):
    """Return a complete linked official signature, or ``None``.

    Color, translation, canvas padding, and global D4 orientation are nuisance
    factors.  The linked signature retains the template shape, both frame
    dimensions, each frame-color component count, each overwritten-border
    count, and the disjoint/occluded relation.  This rejects recombinations of
    official marginals that were never demonstrated together.
    """
    profile = _classify_profile(grid)
    overlap = _classify_overlap(grid)
    linked = {
        ("canonical_0", "disjoint"),
        ("canonical_1", "disjoint"),
        ("canonical_2", "disjoint"),
        ("canonical_3", "occluded"),
    }
    if (profile, overlap) not in linked:
        return None
    comps = _components_4_same_color(grid)
    template = next(cells for color, cells in comps if color == 2)
    frame_desc = tuple(
        sorted(
            (
                item["dims"],
                item["components"],
                item["missing"],
                item["overwritten"],
            )
            for item in _frame_descriptors(grid)
        )
    )
    signature = (profile, overlap, _shape_key(template), frame_desc)
    # canonical_3 is specifically the demonstrated one-split/one-intact
    # occlusion topology, not every arbitrary crossing of 5x5 and 7x7 frames.
    if profile == "canonical_3":
        expected = (((5, 5), 2, 2, 2), ((7, 7), 1, 0, 0))
        if frame_desc != expected:
            return None
    return signature


def observe_overrides(grid):
    frames = _frame_descriptors(grid)
    palette = frozenset(item["color"] for item in frames)
    palette_kind = next(
        (name for name, pair in _PALETTE_PAIRS.items() if palette == frozenset(pair)),
        "unknown",
    )
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]) if grid else 0,
        "profile_kind": _classify_profile(grid),
        "overlap_kind": _classify_overlap(grid),
        "palette_kind": palette_kind,
    }


def oracle_output(grid):
    """Python mirror of the selected Racket rule, used only for checks."""
    comps = _components_4_same_color(grid)
    template = next((cells for color, cells in comps if color == 2), None)
    if template is None:
        raise ValueError("missing color-2 template")
    normalized = _normalize(template)
    th = max(r for r, _ in normalized) + 1
    tw = max(c for _, c in normalized) + 1
    out = full_grid(len(grid), len(grid[0]), 0)
    for color, cells in comps:
        if color == 2:
            continue
        r0, c0, r1, c1 = _bbox(cells)
        ih = r1 - r0 - 1
        iw = c1 - c0 - 1
        sr = r0 + 1 + ((ih - th) // 2)
        sc = c0 + 1 + ((iw - tw) // 2)
        for r, c in cells:
            out[r][c] = color
        for dr, dc in normalized:
            rr, cc = sr + dr, sc + dc
            if 0 <= rr < len(out) and 0 <= cc < len(out[0]):
                out[rr][cc] = color
    return out


def self_check(grid, *, difficulty=None, meta=None):
    if not grid or not isinstance(grid, list) or not isinstance(grid[0], list):
        return ["grid is empty or not a 2D list"]
    h, w = len(grid), len(grid[0])
    if any(not isinstance(row, list) or len(row) != w for row in grid):
        return ["grid is ragged"]
    errors = []
    if not (10 <= h <= 20 and 13 <= w <= 22):
        errors.append(f"dims {h}x{w} outside 10..20 x 13..22")
    if any(
        not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        errors.append("grid contains a non-ARC color")

    comps = _components_4_same_color(grid)
    templates = [cells for color, cells in comps if color == 2]
    if len(templates) != 1:
        errors.append(f"expected one connected color-2 template, found {len(templates)}")
        return errors
    allowed_shapes = {_shape_key(spec["template"]) for spec in _PROFILE_SPECS.values()}
    allowed_shapes.update(_shape_key(shape) for shape in _GENERAL_TEMPLATES)
    if _shape_key(templates[0]) not in allowed_shapes:
        errors.append("color-2 component is not a supported template shape")

    frame_desc = _frame_descriptors(grid)
    if len(frame_desc) != 2:
        errors.append(f"expected exactly two frame colors, found {len(frame_desc)}")
    palette = frozenset(item["color"] for item in frame_desc)
    if len(palette) != 2 or any(color in (0, 2) for color in palette):
        errors.append(f"expected two distinct non-{{0,2}} frame colors, found {sorted(palette)}")
    for item in frame_desc:
        r0, c0, r1, c1 = item["bbox"]
        if r1 - r0 + 1 < 3 or c1 - c0 + 1 < 3:
            errors.append(f"color-{item['color']} frame bbox is smaller than 3x3")
        if any((r, c) not in item["border"] for r, c in item["cells"]):
            errors.append(f"color-{item['color']} has a cell inside its frame interior")
        if item["missing"] != item["overwritten"]:
            errors.append(
                f"color-{item['color']} frame has {item['missing'] - item['overwritten']} "
                "unexplained zero holes on its border"
            )
    try:
        transformed = oracle_output(grid)
    except Exception as exc:  # pragma: no cover - diagnostic path
        errors.append(f"oracle mirror failed: {type(exc).__name__}: {exc}")
    else:
        if transformed == grid:
            errors.append("oracle transform is identity")
        if any(value == 2 for row in transformed for value in row):
            errors.append("oracle output retained the source template color")
    return errors
