"""Generator for ARC task 67504673cd7c — stamp a gray template at markers.

The input contains one connected color-5 template and 2..5 distinct one-cell
markers.  Each marker is the bounding-box origin of an output copy of the
normalized template, painted in the marker color.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = TASK_ID = "67504673cd7c"
VERSION = "2.1.0"
RULE_HASH = "35ef1014dd1e"
SUMMARY = (
    "One connected color-5 template (3-6 cells) and 2-5 distinct one-cell "
    "markers; stamp the normalized template at every marker in its color."
)

INVARIANTS = [
    "background is 0",
    "exactly one 4-connected color-5 template of size 3..6",
    "2..5 single-cell markers with distinct non-{0,5} colors",
    "all marker-origin stamps are in bounds, pairwise disjoint, and separate from the template",
]

AXES = {
    "grid_h": {"type": "int", "default": "difficulty-aware with canonical-profile anchors", "valid": "8..22"},
    "grid_w": {"type": "int", "default": "difficulty-aware with canonical-profile anchors", "valid": "10..24"},
    "num_anchors": {"type": "int", "default": "difficulty-aware 2..5", "valid": "2..5"},
    "template_size": {"type": "int", "default": "difficulty-aware 3..6", "valid": "3..6"},
}

EXAMPLES_NEEDED = 2
_CANONICAL_PROFILES = ((10, 12, 3, 2), (9, 11, 4, 2), (10, 10, 3, 2), (8, 12, 3, 2))
_MARKER_COLORS = (1, 2, 3, 4, 6, 7, 8, 9)
_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _validate_request(seed, sample_index, difficulty, overrides):
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    if type(sample_index) is not int or sample_index < 0:
        raise TypeError("sample_index must be a nonnegative integer (not bool)")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, easy, medium, or hard")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {unknown}")
    for name in AXES:
        if name in overrides and overrides[name] is not None and type(overrides[name]) is not int:
            raise TypeError(f"{name} must be an integer (not bool)")


def _normalise(cells):
    cells = set(cells)
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def _shape_variants(size):
    bases = {
        3: ((0, 0), (1, 0), (1, 1)),
        4: ((0, 1), (1, 0), (1, 1), (2, 1)),
        5: ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1)),
        6: ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2)),
    }
    result = set()
    for reflect in (False, True):
        for rotations in range(4):
            transformed = []
            for r, c in bases[size]:
                if reflect:
                    c = -c
                for _ in range(rotations):
                    r, c = c, -r
                transformed.append((r, c))
            result.add(_normalise(transformed))
    return tuple(sorted(result))


def _connected(cells):
    cells = set(cells)
    if not cells:
        return False
    seen = {next(iter(cells))}
    stack = list(seen)
    while stack:
        r, c = stack.pop()
        for dr, dc in _CARDINAL:
            point = (r + dr, c + dc)
            if point in cells and point not in seen:
                seen.add(point)
                stack.append(point)
    return seen == cells


def _analyse(grid):
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        raise ValueError("grid is empty or not a 2D list")
    h, w = len(grid), len(grid[0])
    if any(type(row) is not list or len(row) != w for row in grid):
        raise ValueError("ragged grid")
    if not (8 <= h <= 22 and 10 <= w <= 24):
        raise ValueError(f"grid dimensions must be within 8..22 by 10..24, got {h}x{w}")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("grid cells must be exact integers 0..9")

    template = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 5}
    if not 3 <= len(template) <= 6:
        raise ValueError(f"template size must be 3..6, got {len(template)}")
    if not _connected(template):
        raise ValueError("color-5 template must be one 4-connected component")
    shape = _normalise(template)

    anchors = [(r, c, value) for r, row in enumerate(grid) for c, value in enumerate(row) if value not in (0, 5)]
    if not 2 <= len(anchors) <= 5:
        raise ValueError(f"anchor count must be 2..5, got {len(anchors)}")
    colors = [value for _, _, value in anchors]
    if len(set(colors)) != len(colors):
        raise ValueError("marker colors must be distinct singletons")

    footprints = []
    for r, c, _ in anchors:
        footprint = {(r + dr, c + dc) for dr, dc in shape}
        if any(not (0 <= rr < h and 0 <= cc < w) for rr, cc in footprint):
            raise ValueError(f"marker at {(r, c)} stamps out of bounds")
        if footprint & template:
            raise ValueError(f"marker at {(r, c)} overlaps the input template footprint")
        if any(footprint & prior for prior in footprints):
            raise ValueError("marker stamp footprints overlap")
        footprints.append(footprint)
    return {"h": h, "w": w, "template": template, "shape": shape, "anchors": anchors}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    try:
        _analyse(grid)
    except (TypeError, ValueError) as exc:
        return [str(exc)]
    return []


def observe_overrides(grid):
    info = _analyse(grid)
    return {
        "grid_h": info["h"],
        "grid_w": info["w"],
        "num_anchors": len(info["anchors"]),
        "template_size": len(info["template"]),
    }


def _draw_axis(ctx, name, full_bounds, band_bounds):
    if name in ctx.overrides and ctx.overrides[name] is not None:
        return ctx.draw_int_strict(name, *full_bounds)
    return ctx.draw_int_strict(name, *band_bounds)


def _lattice_origins(shape, h, w, needed, rng):
    sh = max(r for r, _ in shape) + 1
    sw = max(c for _, c in shape) + 1
    choices = []
    for ro in range(sh):
        for co in range(sw):
            positions = [(r, c) for r in range(ro, h - sh + 1, sh) for c in range(co, w - sw + 1, sw)]
            if len(positions) >= needed:
                choices.append(positions)
    if not choices:
        raise ValueError(f"cannot place {needed} disjoint {sh}x{sw} template boxes in {h}x{w}")
    positions = list(rng.choice(choices))
    rng.shuffle(positions)
    return positions[:needed]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_request(seed, sample_index, difficulty, overrides)
    effective = dict(overrides)
    # A source-independent periodic prior gives every band exact support for a
    # public (height, width, palette-size) profile without making all draws tiny.
    if sample_index % 2 == 0:
        profile = _CANONICAL_PROFILES[(sample_index // 2) % len(_CANONICAL_PROFILES)]
        for name, value in zip(("grid_h", "grid_w", "template_size", "num_anchors"), profile):
            effective.setdefault(name, value)

    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=effective)
    bands = {
        None: ((8, 22), (10, 24), (2, 5), (3, 6)),
        "easy": ((8, 12), (10, 14), (2, 3), (3, 4)),
        "medium": ((10, 17), (12, 19), (2, 4), (3, 5)),
        "hard": ((14, 22), (16, 24), (3, 5), (4, 6)),
    }
    hb, wb, ab, sb = bands[difficulty]
    h = _draw_axis(ctx, "grid_h", (8, 22), hb)
    w = _draw_axis(ctx, "grid_w", (10, 24), wb)
    num_anchors = _draw_axis(ctx, "num_anchors", (2, 5), ab)
    template_size = _draw_axis(ctx, "template_size", (3, 6), sb)

    shape_rng = ctx.draw_rng("template-shape")
    shape = shape_rng.choice(_shape_variants(template_size))
    origins = _lattice_origins(shape, h, w, num_anchors + 1, ctx.draw_rng("placements"))
    template_origin, marker_origins = origins[0], origins[1:]

    grid = full_grid(h, w, 0)
    for dr, dc in shape:
        grid[template_origin[0] + dr][template_origin[1] + dc] = 5
    colors = list(_MARKER_COLORS)
    ctx.draw_rng("marker-colors").shuffle(colors)
    for (r, c), color in zip(marker_origins, colors[:num_anchors]):
        grid[r][c] = color

    findings = self_check(grid)
    if findings:
        raise AssertionError("constructed invalid instance: " + "; ".join(findings))
    return grid


def rule_mirror(grid):
    info = _analyse(grid)
    output = full_grid(info["h"], info["w"], 0)
    for r, c, color in info["anchors"]:
        for dr, dc in info["shape"]:
            output[r + dr][c + dc] = color
    return output


def _anchors_only(grid):
    info = _analyse(grid)
    output = full_grid(info["h"], info["w"], 0)
    for r, c, color in info["anchors"]:
        output[r][c] = color
    return output


def _multi_cell_template(grid):
    try:
        return len(_analyse(grid)["template"]) > 1
    except (TypeError, ValueError):
        return False


strict_canonical_like = self_check
SEMANTIC_WITNESSES = {"multi_cell_template": _multi_cell_template}
SEMANTIC_RIVALS = {"anchors_only": _anchors_only}
WITNESS_RIVALS = {"multi_cell_template": ["anchors_only"]}
LESSON_COMPETITORS = SEMANTIC_RIVALS
