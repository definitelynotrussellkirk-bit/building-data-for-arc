"""Generator for arc_puzzle_bank_21_set19_bundle:hard_p03 — pair frames to solids by size.

Rule: detect rectangular hollow frames and other (non-frame) components.
Sort both by ascending size; place each solid centered in the paired frame's
interior.

Combinatorial axes (8): grid_h, grid_w, palette_kind, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_frames (no hollow frames → rule has no destinations);
no_solids (frames present but no solid components → rule has nothing
to pair); tied_sizes (two frames same interior size and two solids
same size → pairing tie-break ambiguous).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_frame, full_grid

GENERATOR_ID = "134c37edbf82"
VERSION = "2.1.0"
TASK_ID = "134c37edbf82"

SUMMARY = (
    "0-bg grid (h~11-14, w~14-17) with: (a) EXACTLY "
    "2 HOLLOW RECTANGULAR FRAMES of DISTINCT "
    "interior sizes drawn from {4×4, 5×5, 4×5, 5×4, "
    "4×6}, each in a distinct color from a 4-color "
    "palette; (b) EXACTLY 2 SOLID FILLED RECTANGLES "
    "in distinct colors and distinct sizes drawn "
    "from {2×2, 2×3, 3×2, 3×3}. Frames and solids "
    "are 4-conn isolated; each solid fits inside one "
    "of the frames' interiors. Rule: SORT the 2 "
    "frames by interior area ASC and SORT the 2 "
    "solids by area ASC. PAIR positionally "
    "(smaller→smaller, larger→larger). For each pair, "
    "PLACE the solid CENTERED inside the paired "
    "frame's interior. The original solid location "
    "is CLEARED. Net: each solid moves to the "
    "size-matched frame center."
)

INVARIANTS = [
    "background is 0",
    "exactly 2 hollow rectangular frames in distinct colors with distinct interior sizes",
    "exactly 2 solid (filled) components in distinct colors with distinct sizes",
    "frames and solids are 4-conn isolated",
    "each solid fits inside its paired frame's interior",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_frames", "no_solids", "tied_sizes")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":            {"type": "int", "default": "rng 11..14", "valid": "10..18"},
    "grid_w":            {"type": "int", "default": "rng 14..17", "valid": "12..20"},
    "palette_kind":      {"type": "str", "default": "rng helpful",
                          "valid": "default|warm|cool|varied"},
    "palette_size":      {"type": "int", "default": "rng 4..4", "valid": "4..4"},
    "position_bias":     {"type": "str", "default": "two_frames_two_solids_distinct_sizes",
                          "valid": "two_frames_two_solids_distinct_sizes"},
    "n_distinct_colors": {"type": "int", "default": "rng 4..4", "valid": "4..4"},
    "density":           {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":           {"type": "str", "default": "alias for palette_kind",
                          "valid": "default|warm|cool|varied|no_frames|no_solids|tied_sizes"},
}


def _free(g, r1, c1, r2, c2):
    h, w = len(g), len(g[0])
    if r1 < 0 or c1 < 0 or r2 >= h or c2 >= w: return False
    for r in range(max(0, r1 - 1), min(h, r2 + 2)):
        for c in range(max(0, c1 - 1), min(w, c2 + 2)):
            if g[r][c] != 0: return False
    return True


def _sample_rule_compatible_dims(rng):
    frame_values = [(4, 4), (5, 5), (4, 5), (5, 4), (4, 6)]
    solid_values = [(2, 2), (2, 3), (3, 2), (3, 3)]
    for _ in range(200):
        frames = _sample_distinct_by(
            rng, frame_values, lambda d: (d[0] - 2) * (d[1] - 2), 2
        )
        solids = _sample_distinct_by(
            rng, solid_values, lambda d: d[0] * d[1], 2
        )
        paired = zip(
            sorted(frames, key=lambda d: (d[0] - 2) * (d[1] - 2)),
            sorted(solids, key=lambda d: d[0] * d[1]),
        )
        if all(sh <= fh - 2 and sw <= fw - 2 for (fh, fw), (sh, sw) in paired):
            return frames, solids
    raise ValueError("could not sample rule-compatible frame/solid dimensions")


def _sample_distinct_by(rng, values, key, n):
    """Sample n values whose rule-sorting keys are distinct.

    The canonical rule pairs frames by *interior area* and loose solids by
    *object area*.  Sampling (4x5, 5x4) frames or (2x3, 3x2) solids together
    creates a tie that hides the intended size-pairing rule behind traversal
    order, so keep the random draw semantically unambiguous.
    """
    picked = []
    used = set()
    pool = list(values)
    rng.shuffle(pool)
    for value in pool:
        k = key(value)
        if k in used:
            continue
        picked.append(value)
        used.add(k)
        if len(picked) == n:
            return picked
    raise ValueError("not enough distinct-key values to sample")


def _components(g):
    h, w = len(g), len(g[0])
    seen = set()
    comps = []
    for sr in range(h):
        for sc in range(w):
            color = g[sr][sc]
            if color == 0 or (sr, sc) in seen:
                continue
            stack = [(sr, sc)]
            seen.add((sr, sc))
            cells = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if (0 <= nr < h and 0 <= nc < w and
                            (nr, nc) not in seen and g[nr][nc] == color):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            comps.append({"color": color, "cells": cells})
    for comp in comps:
        rs = [r for r, _ in comp["cells"]]
        cs = [c for _, c in comp["cells"]]
        comp["bbox"] = (min(rs), min(cs), max(rs), max(cs))
        comp["height"] = comp["bbox"][2] - comp["bbox"][0] + 1
        comp["width"] = comp["bbox"][3] - comp["bbox"][1] + 1
    return comps


def _is_rect_frame(comp):
    r0, c0, r1, c1 = comp["bbox"]
    if comp["height"] < 3 or comp["width"] < 3:
        return False
    expected = {
        (r, c)
        for r in range(r0, r1 + 1)
        for c in range(c0, c1 + 1)
        if r in (r0, r1) or c in (c0, c1)
    }
    return set(comp["cells"]) == expected


def _is_filled_rect(comp):
    r0, c0, r1, c1 = comp["bbox"]
    expected = {
        (r, c)
        for r in range(r0, r1 + 1)
        for c in range(c0, c1 + 1)
    }
    return set(comp["cells"]) == expected


def self_check(grid, *, difficulty=None, meta=None):
    issues = []
    if not isinstance(grid, list) or not grid or not all(isinstance(row, list) for row in grid):
        return ["grid must be a non-empty list of rows"]
    if len({len(row) for row in grid}) != 1:
        return ["grid rows must all have the same width"]
    if any(v == 0 for row in grid for v in row) is False:
        issues.append("background 0 must be present")

    h, w = len(grid), len(grid[0])
    comps = _components(grid)
    frames = [comp for comp in comps if _is_rect_frame(comp)]
    solids = [comp for comp in comps if not _is_rect_frame(comp)]

    if len(frames) != 2:
        issues.append(f"expected exactly 2 hollow frames, got {len(frames)}")
    if len(solids) != 2:
        issues.append(f"expected exactly 2 loose solid components, got {len(solids)}")

    colors = [comp["color"] for comp in comps]
    if len(colors) != len(set(colors)):
        issues.append("frame/solid colors must all be distinct")

    for comp in solids:
        if not _is_filled_rect(comp):
            issues.append(f"loose component color {comp['color']} is not a filled rectangle")

    frame_keys = [(comp["height"] - 2) * (comp["width"] - 2) for comp in frames]
    if len(frame_keys) != len(set(frame_keys)):
        issues.append("frame interior areas must be distinct (rule sort key)")
    solid_keys = [len(comp["cells"]) for comp in solids]
    if len(solid_keys) != len(set(solid_keys)):
        issues.append("solid areas must be distinct (rule sort key)")

    if len(frames) == 2 and len(solids) == 2:
        for fr, solid in zip(sorted(frames, key=lambda c: (c["height"] - 2) * (c["width"] - 2)),
                             sorted(solids, key=lambda c: len(c["cells"]))):
            if solid["height"] > fr["height"] - 2 or solid["width"] > fr["width"] - 2:
                issues.append(
                    f"solid {solid['height']}x{solid['width']} does not fit inside "
                    f"frame interior {fr['height'] - 2}x{fr['width'] - 2}"
                )

    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0:
                continue
            for dr, dc in ((1, 0), (0, 1)):
                nr, nc = r + dr, c + dc
                if 0 <= nr < h and 0 <= nc < w and grid[nr][nc] not in (0, grid[r][c]):
                    issues.append("components must be separated by at least one 0-cell")
                    return issues
    return issues


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 11, 12)
        w = ctx.draw_int("grid_w", 14, 15)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 13, 14)
        w = ctx.draw_int("grid_w", 16, 17)
    else:
        h = ctx.draw_int("grid_h", 11, 14)
        w = ctx.draw_int("grid_w", 14, 17)
    rng = ctx.draw_rng("layout")

    frame_colors = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], 2)
    solid_colors = rng.sample([c for c in [1, 2, 3, 4, 5, 6, 7, 8, 9] if c not in frame_colors], 2)
    frame_dims, solid_dims = _sample_rule_compatible_dims(rng)

    for outer in range(40):
        g = full_grid(h, w, 0)
        ok = True
        for color, (fh, fw) in zip(frame_colors, frame_dims):
            placed = False
            for _ in range(120):
                r0 = rng.randint(0, h - fh)
                c0 = rng.randint(0, w - fw)
                if not _free(g, r0, c0, r0 + fh - 1, c0 + fw - 1):
                    continue
                draw_frame(g, r0, c0, r0 + fh - 1, c0 + fw - 1, color)
                placed = True; break
            if not placed:
                ok = False; break
        if not ok:
            continue
        for color, (sh, sw) in zip(solid_colors, solid_dims):
            placed = False
            for _ in range(120):
                r0 = rng.randint(0, h - sh)
                c0 = rng.randint(0, w - sw)
                if not _free(g, r0, c0, r0 + sh - 1, c0 + sw - 1):
                    continue
                for r in range(sh):
                    for c in range(sw):
                        g[r0 + r][c0 + c] = color
                placed = True; break
            if not placed:
                ok = False; break
        if ok:
            return g
    raise ValueError("could not realize hard_p03 layout")


def _draw_from_degenerate(name, rng):
    h, w = 12, 15
    g = full_grid(h, w, 0)
    if name == "no_frames":
        for r in range(2):
            for c in range(2):
                g[3 + r][3 + c] = 1
        for r in range(3):
            for c in range(3):
                g[7 + r][9 + c] = 2
        return g
    if name == "no_solids":
        draw_frame(g, 1, 1, 4, 4, 1)
        draw_frame(g, 6, 8, 10, 13, 2)
        return g
    if name == "tied_sizes":
        draw_frame(g, 1, 1, 4, 4, 1)
        draw_frame(g, 1, 9, 4, 12, 2)
        for r in range(2):
            for c in range(2):
                g[7 + r][1 + c] = 3
        for r in range(2):
            for c in range(2):
                g[7 + r][9 + c] = 4
        return g
    return g
