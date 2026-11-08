"""Generator for puzzle 516b51b7.

Rule: solid blue rectangles; rule fills each with concentric red/green
rings (center=blue, dist 1=red, dist 2=green, alternating).

Combinatorial axes (8): grid_h/w, n_rects, rect_size_kind,
position_bias, palette_size, decoy_density, inter_rect_margin,
asymmetry_force.
Degenerates: no_rects, single_small, all_overlap.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, draw_rect

GENERATOR_ID = "2587fd13e366"
VERSION = "1.2.0"  # normal samples now show 2+ rectangles and canonical 3x3 small rectangles
TASK_ID = "2587fd13e366"
SUMMARY = "Solid blue rectangles; rule fills with concentric red/green rings."

INVARIANTS = [
    "background is 0",
    ">=2 solid blue(1) rectangles in the normal path",
    "blue rectangles are solid, bbox-filled, and at least 3×3",
    "rectangles non-overlapping with margin >=1",
    "no colors 2 or 3 in input (rule writes them for output)",
]

RECT_SIZE_KINDS = ("small", "medium", "large", "wide", "tall")
DEGENERATE_TEXTURES = ("no_rects", "single_small", "all_overlap")
HELPFUL_TEXTURES = RECT_SIZE_KINDS

AXES = {
    "grid_h":             {"type": "int", "default": "rng 12..18", "valid": "10..22"},
    "grid_w":             {"type": "int", "default": "rng 12..18", "valid": "10..22"},
    "n_rects":            {"type": "int", "default": "rng 2..3", "valid": "1..5"},
    "rect_size_kind":     {"type": "str", "default": "rng helpful",
                           "valid": "|".join(RECT_SIZE_KINDS)},
    "position_bias":      {"type": "str", "default": "rng spread|center|edge",
                           "valid": "spread|center|edge"},
    "palette_size":       {"type": "int", "default": "1", "valid": "1..3"},
    "inter_rect_margin":  {"type": "int", "default": "1", "valid": "1..3"},
    "asymmetry_force":    {"type": "bool", "default": "false",
                           "valid": "true|false"},
    "texture":            {"type": "str", "default": "alias for rect_size_kind",
                           "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _blue_components(grid):
    h, w = len(grid), len(grid[0])
    seen = set(); comps = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != 1 or (r, c) in seen:
                continue
            stack = [(r, c)]; seen.add((r, c)); cells = []
            while stack:
                rr, cc = stack.pop(); cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and grid[nr][nc] == 1 and (nr, nc) not in seen:
                        seen.add((nr, nc)); stack.append((nr, nc))
            comps.append(cells)
    return comps


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify normal concentric-ring inputs: multiple solid blue rectangles, no output colors."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errors = []
    for bad in (2, 3):
        if any(grid[r][c] == bad for r in range(h) for c in range(w)):
            errors.append(f"color {bad} in input — rule writes it, not the generator")
    comps = _blue_components(grid)
    if len(comps) < 2:
        errors.append(f"normal path should show at least 2 blue rectangles, found {len(comps)}")
    for cells in comps:
        rs = [r for r, _ in cells]; cs = [c for _, c in cells]
        r1, r2, c1, c2 = min(rs), max(rs), min(cs), max(cs)
        rh, rw = r2 - r1 + 1, c2 - c1 + 1
        if rh < 3 or rw < 3:
            errors.append(f"blue rectangle too small: {rh}x{rw}")
        if len(cells) != rh * rw:
            errors.append(f"blue component is not a solid filled rectangle: bbox {rh}x{rw}, cells={len(cells)}")
    return errors


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if difficulty == "easy":
        h_lo, h_hi = 10, 13
    elif difficulty == "hard":
        h_lo, h_hi = 17, 22
    else:
        h_lo, h_hi = 12, 18
    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", h_lo, h_hi)
    rng = ctx.draw_rng("placement")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], h, w, rng)
    if "n_rects" in overrides:
        n_rects = int(overrides["n_rects"])
    elif difficulty == "easy":
        n_rects = ctx.draw_int("n_rects", 2, 2)
    elif difficulty == "hard":
        n_rects = ctx.draw_int("n_rects", 2, 4)
    else:
        n_rects = ctx.draw_int("n_rects", 2, 3)
    n_rects = max(1, min(5, n_rects))
    min_required = 1 if "n_rects" in overrides and n_rects == 1 else 2
    size_kind = (overrides.get("texture") or
                 overrides.get("rect_size_kind")
                 or ctx.draw_choice("rect_size_kind",
                                    list(RECT_SIZE_KINDS)))
    # Multiple rectangles are the normal lesson; center/edge placement is too often
    # impossible for >1 separated rectangles, so keep those as explicit overrides.
    bias = overrides.get("position_bias", "spread")
    margin = int(overrides.get("inter_rect_margin", 1))

    best = None; best_count = -1
    for _outer in range(30):
        g = full_grid(h, w, 0)
        placed = 0
        placed_boxes = []
        for _ in range(n_rects * 30):
            if placed >= n_rects:
                break
            rh, rw = _rect_dims(size_kind, h, w, rng)
            for _try in range(20):
                r0, c0 = _pick_pos(bias, h, w, rh, rw, rng)
                if r0 < 1 or c0 < 1 or r0 + rh > h - 1 or c0 + rw > w - 1:
                    continue
                ok = all(not (r0 - margin <= obr2 and r0 + rh + margin >= obr1
                              and c0 - margin <= obc2 and c0 + rw + margin >= obc1)
                         for (obr1, obc1, obr2, obc2) in placed_boxes)
                if not ok:
                    continue
                draw_rect(g, r0, c0, rh, rw, 1)
                placed_boxes.append((r0, c0, r0 + rh - 1, c0 + rw - 1))
                placed += 1
                break
        if placed > best_count:
            best, best_count = g, placed
        if placed >= min_required:
            return g

    # Last-resort non-crashing fallback: still emit two canonical-small rectangles when the
    # requested overrides make random placement too tight.
    g = full_grid(h, w, 0)
    if h >= 8 and w >= 8:
        draw_rect(g, 1, 1, 3, 3, 1)
        draw_rect(g, h - 4, w - 4, 3, 3, 1)
        return g
    return best if best is not None else g


def _rect_dims(kind, h, w, rng):
    max_h = max(4, h // 2)
    max_w = max(4, w // 2)
    if kind == "small":
        return rng.choice([(3, 3), (3, 4), (4, 3), (4, 4)])
    if kind == "medium":
        return rng.randint(4, 5), rng.randint(4, 5)
    if kind == "large":
        return rng.randint(5, 7), rng.randint(5, 7)
    if kind == "wide":
        return 4, rng.randint(5, max_w)
    if kind == "tall":
        return rng.randint(5, max_h), 4
    return rng.randint(4, max_h), rng.randint(4, max_w)


def _pick_pos(bias, h, w, rh, rw, rng):
    if bias == "center":
        return max(1, (h - rh) // 2), max(1, (w - rw) // 2)
    if bias == "edge":
        return 1, 1
    return rng.randint(1, h - rh - 1), rng.randint(1, w - rw - 1)


def _draw_from_degenerate(name, h, w, rng):
    g = full_grid(h, w, 0)
    if name == "no_rects":
        return g
    if name == "single_small":
        if h >= 4 and w >= 4:
            draw_rect(g, 1, 1, 3, 3, 1)
        return g
    if name == "all_overlap":
        if h >= 6 and w >= 6:
            draw_rect(g, 1, 1, 4, 4, 1)
            draw_rect(g, 2, 2, 4, 4, 1)
        return g
    return g
