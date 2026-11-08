"""Generator for arc_additional_puzzles_21_set14_bundle:H94 — transform analogy transfer.

Rule: full-column color-1 dividers split into 3 panels. Each panel is cropped
to content (after dropping the divider). Transform t in {1..6} maps A→B
(1=id, 2=cw, 3=180, 4=transpose, 5=flip-lr, 6=flip-ud). Output = t(C).

Public axes: panel_n, transform, shape_k, and texture.
Degenerate textures preserve the three-panel grammar but intentionally hide
transform evidence; incompatible transform/shape overrides fail closed.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "027805c8ff0f"
VERSION = "2.1.2"
TASK_ID = "027805c8ff0f"
RULE_HASH = "2d205350180d"

SUMMARY = (
    "0-bg N x (3N+2) grid: three square N x N panels A | B | C split "
    "by two full-height blue(1) divider columns. B = t(A) for t in "
    "{1=id 2=cw 3=180 4=transpose 5=flip-lr 6=flip-ud}; C holds an "
    "independent shape. Rule: crop each panel to content, find the "
    "FIRST t (in 1..6 order) with t(crop A) == crop B, and output "
    "t(crop C) — a small cropped grid, NOT the 3-panel layout."
)

# Rivals: 'output = C unchanged' refuted by non-identity transforms.
# 'output keeps the panel layout' refuted (output is the small crop).
# 'transform read at panel coords' refuted by off-center placements
# that only match at crop level. 'any matching t' — the FIRST match
# wins, enforced at generation. 4 demos spanning >=3 transforms.
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "background is 0",
    "two full-height color-1 dividers split three equal NxN panels",
    "the intended t is the FIRST crop-level match in the rule's 1..6 order "
    "(verified by a Python mirror — symmetric shapes are resampled)",
    "C is non-empty (crop-to-content of an empty panel crashes the rule)",
]

DEGENERATE_TEXTURES = ("identity_transform", "ambiguous_symmetric")
HELPFUL_TEXTURES = ("plain",)

AXES = {
    "panel_n":   {"type": "int", "default": "rng 4..5", "valid": "3..6",
                  "doc": "Panel side length."},
    "transform": {"type": "int", "default": "rng 2..6", "valid": "1..6",
                  "doc": "Intended A->B transform."},
    "shape_k":   {"type": "int", "default": "rng 3..n*n//2", "valid": "3..12",
                  "doc": "Cells in the A shape."},
    "texture":   {"type": "str", "default": "plain",
                  "valid": "plain|identity_transform|ambiguous_symmetric",
                  "doc": "Set to a degenerate name to build a rule-hiding input."},
}


def _crop(cells):
    mr = min(r for r, _ in cells)
    mc = min(c for _, c in cells)
    return sorted((r - mr, c - mc) for r, c in cells)


def _first_match(cells_a, cells_b, n):
    """Mirror of the rule's inference: first t in 1..6 whose transform
    of crop(A) equals crop(B)."""
    matches = _matching_transforms(cells_a, cells_b)
    return matches[0] if matches else 1


def _matching_transforms(cells_a, cells_b):
    """Return every transform code whose cropped A image equals cropped B."""
    ca, cb = _crop(cells_a), _crop(cells_b)
    ah = max(r for r, _ in ca) + 1
    aw = max(c for _, c in ca) + 1
    matches = []
    for t in range(1, 7):
        if t == 1:
            tc = ca
        elif t == 2:
            tc = sorted((c, ah - 1 - r) for r, c in ca)
        elif t == 3:
            tc = sorted((ah - 1 - r, aw - 1 - c) for r, c in ca)
        elif t == 4:
            tc = sorted((c, r) for r, c in ca)
        elif t == 5:
            tc = sorted((r, aw - 1 - c) for r, c in ca)
        else:
            tc = sorted((ah - 1 - r, c) for r, c in ca)
        if _crop(tc) == cb:
            matches.append(t)
    return matches


def _xform(cells, t, n):
    if t == 1: return list(cells)
    if t == 2: return [(c, n - 1 - r) for r, c in cells]
    if t == 3: return [(n - 1 - r, n - 1 - c) for r, c in cells]
    if t == 4: return [(c, r) for r, c in cells]
    if t == 5: return [(r, n - 1 - c) for r, c in cells]
    return [(n - 1 - r, c) for r, c in cells]


def _rand_cells(rng, n, k):
    cells = [(rng.randint(0, n - 1), rng.randint(0, n - 1))]
    seen = set(cells)
    while len(cells) < k:
        r, c = rng.choice(cells)
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        nr, nc = r + dr, c + dc
        if 0 <= nr < n and 0 <= nc < n and (nr, nc) not in seen:
            cells.append((nr, nc)); seen.add((nr, nc))
    return cells


def _validate_overrides(overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)}")
    for name, lo, hi in (
        ("panel_n", 3, 6),
        ("transform", 1, 6),
        ("shape_k", 3, 12),
    ):
        if name not in overrides or overrides[name] is None:
            continue
        value = overrides[name]
        if type(value) is not int:
            raise TypeError(f"override {name!r} must be an integer (not bool)")
        if not lo <= value <= hi:
            raise ValueError(f"override {name!r}={value} outside [{lo}, {hi}]")
    if "texture" in overrides and overrides["texture"] is not None:
        texture = overrides["texture"]
        if type(texture) is not str:
            raise TypeError("override 'texture' must be a string")
        allowed = set(HELPFUL_TEXTURES) | set(DEGENERATE_TEXTURES)
        if texture not in allowed:
            raise ValueError(f"override 'texture'={texture!r} not in {sorted(allowed)}")
        if texture in DEGENERATE_TEXTURES:
            incompatible = [
                name for name in ("transform", "shape_k")
                if name in overrides and overrides[name] is not None
            ]
            if incompatible:
                raise ValueError(
                    f"incompatible degenerate texture {texture!r} and override(s): {incompatible}"
                )


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_overrides(overrides)
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a non-negative integer")
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    texture = overrides.get("texture", "plain")
    if texture in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(texture, ctx)
    if "panel_n" in overrides and overrides["panel_n"] is not None:
        n = ctx.draw_int_strict("panel_n", 3, 6)
    elif difficulty == "easy":
        n = ctx.draw_int_strict("panel_n", 4, 4)
    elif difficulty == "hard":
        n = ctx.draw_int_strict("panel_n", 5, 6)
    else:
        n = ctx.draw_int_strict("panel_n", 4, 5)
    t = ctx.draw_int_strict(
        "transform",
        1 if "transform" in overrides and overrides["transform"] is not None else 2,
        6,
    )
    shape_hi = min(12, n * n // 2)
    ka = ctx.draw_int_strict("shape_k", 3, shape_hi)
    rng = ctx.draw_rng("layout")
    h = n
    w = n * 3 + 2
    d1, d2 = n, 2 * n + 1
    color_a, color_c = rng.sample([2, 3, 4, 5, 6, 7, 8, 9], 2)

    for _outer in range(80):
        g = full_grid(h, w, 0)
        for r in range(h):
            g[r][d1] = 1
            g[r][d2] = 1
        cells_a = _rand_cells(rng, n, ka)
        cells_b = _xform(cells_a, t, n)
        # the rule compares CROPPED panels and takes the FIRST matching
        # t — a symmetric shape lets an earlier code win; resample
        if _first_match(cells_a, cells_b, n) != t:
            continue
        kc = rng.randint(3, max(3, min(8, n * n // 2)))
        cells_c = _rand_cells(rng, n, kc)
        for r, c in cells_a:
            g[r][c] = color_a
        for r, c in cells_b:
            g[r][d1 + 1 + c] = color_a
        for r, c in cells_c:
            g[r][d2 + 1 + c] = color_c
        return g
    raise ValueError("could not realize 3-panel analogy")


def _draw_from_degenerate(name, ctx):
    """Rule-hiding inputs — rng-varied, rule-safe (3 panels, all
    non-empty; no_dividers and no_C_content were dropped: both CRASH
    the rule at (second panels) / crop-to-content of empty).

    identity_transform  — A == B: code falls back to 1, output = crop C.
    ambiguous_symmetric — A symmetric: several codes match; the FIRST
                          in 1..6 order silently wins.
    """
    n = ctx.draw_int_strict(
        "panel_n",
        3 if "panel_n" in ctx.overrides and ctx.overrides["panel_n"] is not None else 4,
        6 if "panel_n" in ctx.overrides and ctx.overrides["panel_n"] is not None else 5,
    )
    rng = ctx.draw_rng("degenerate_layout")
    h, w = n, n * 3 + 2
    g = full_grid(h, w, 0)
    for r in range(h):
        g[r][n] = 1
        g[r][2 * n + 1] = 1
    color_a, color_c = rng.sample([2, 3, 4, 5, 6, 7, 8, 9], 2)
    if name == "identity_transform":
        cells = _rand_cells(rng, n, rng.randint(3, n))
        for r, c in cells:
            g[r][c] = color_a
            g[r][n + 1 + c] = color_a
    else:
        # ambiguous_symmetric: a 2x2 block matches every transform
        r0 = rng.randint(0, n - 2)
        c0 = rng.randint(0, n - 2)
        for dr in range(2):
            for dc in range(2):
                g[r0 + dr][c0 + dc] = color_a
                g[r0 + dr][n + 1 + c0 + dc] = color_a
    cells_c = _rand_cells(rng, n, rng.randint(3, n))
    for r, c in cells_c:
        g[r][2 * n + 2 + c] = color_c
    return g


def self_check(grid, *, difficulty=None, meta=None):
    """Verify the complete three-panel transform-analogy contract."""
    msgs = []
    if not isinstance(grid, list) or not grid or not all(isinstance(row, list) for row in grid):
        return ["expected a non-empty rectangular ARC grid"]
    if not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        return ["expected a non-empty rectangular ARC grid"]
    h, w = len(grid), len(grid[0])
    if h > 30 or w > 30:
        msgs.append("grid exceeds ARC 30x30 bounds")
    if w != 3 * h + 2:
        msgs.append(f"expected width 3*h+2, got h={h}, w={w}")
    div_cols = [c for c in range(w) if all(grid[r][c] == 1 for r in range(h))]
    if len(div_cols) != 2:
        msgs.append(f"expected exactly 2 full-height color-1 dividers, found {len(div_cols)}")
        return msgs
    # Three panels must be equal-width: panel_n = (w-2)/3
    n = h
    if div_cols[0] != n or div_cols[1] != 2 * n + 1:
        msgs.append(
            f"dividers at {div_cols} don't match equal-panel layout "
            f"(expected at {n} and {2 * n + 1} for w={w})"
        )
    a_cells = [(r, c) for r in range(h) for c in range(n) if grid[r][c] not in (0, 1)]
    b_cells = [
        (r, c - (n + 1))
        for r in range(h)
        for c in range(n + 1, 2 * n + 1)
        if grid[r][c] not in (0, 1)
    ]
    c_start = 2 * n + 2
    c_cells = [
        (r, c - c_start)
        for r in range(h)
        for c in range(c_start, w)
        if grid[r][c] not in (0, 1)
    ]
    if not a_cells:
        msgs.append("panel A (leftmost) has no non-{0,1} cells")
    if not b_cells:
        msgs.append("panel B (middle) has no non-{0,1} cells")
    if not c_cells:
        msgs.append("panel C (rightmost) has no non-{0,1} cells")
    a_colors = {grid[r][c] for r in range(h) for c in range(n) if grid[r][c] not in (0, 1)}
    b_colors = {
        grid[r][c]
        for r in range(h)
        for c in range(n + 1, 2 * n + 1)
        if grid[r][c] not in (0, 1)
    }
    if a_colors and b_colors and (len(a_colors) != 1 or a_colors != b_colors):
        msgs.append("A/B transform panels must use the same single color")
    if a_cells and b_cells and not _matching_transforms(a_cells, b_cells):
        msgs.append("panel B has no valid cropped transform match from panel A")
    return msgs
