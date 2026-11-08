"""Generator for ARC task a5313dff.

Rule: `(rule! (lambda (g) (fill-all-enclosed g 1)))`. Same shape as
00d62c1b but the fill color is 1 (blue) instead of 4.

Combinatorial axes:
  * grid_h / grid_w           — outer canvas size
  * n_frames                  — how many enclosing shapes to plant (1..3)
  * frame_kind                — shape: rect_outline / blob_outline /
                                irregular / U_shape / nested
  * wall_color                — color of the enclosing wall (≠ 0, ≠ 1)
  * size_distribution         — frame size mix
  * inner_marker_prob         — probability of an inner non-bg dot
                                (interrupts the fill, mirrors the canonical
                                ARC examples)
  * decor_density             — extra non-bg, non-1 cells outside frames
  * caller-opt-in degenerates: open_frame, solid_frame, tiny_frame
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, draw_rect_outline

GENERATOR_ID = "7ba2cb1b847b"
VERSION = "2.0.1"
TASK_ID = "7ba2cb1b847b"
SUMMARY = (
    "0-bg grid (h, w~8-15) with 1-2 "
    "CLOSED FRAMES of varied kinds: "
    "rect_outline / blob_outline / "
    "irregular_polygon / U_shape / "
    "nested_rects, drawn in a "
    "WALL_COLOR (random non-{0, 1}) "
    "of varying sizes (3-5 small, "
    "5-h-4 medium, h//2-h-4 large, "
    "or mixed). Each frame is "
    "closed (its interior 0-region "
    "isn't connected to the outer "
    "border). Optional inner "
    "wall-color marker cell with "
    "probability 0..0.7. Optional "
    "0..0.05 density of decoy "
    "non-{0, 1, wall} cells "
    "outside frames. Rule (FILL "
    "ALL ENCLOSED 0 REGIONS WITH "
    "COLOR 1): for EACH 0-CELL, "
    "check if it's ENCLOSED by "
    "non-0 walls (NOT reachable "
    "from the grid border through "
    "0-cells). If enclosed, "
    "RECOLOR to COLOR 1 (blue). "
    "Open frames (interior touches "
    "border) and outer 0-cells "
    "stay 0. Inner markers stay. "
    "Walls stay. Net: closed-"
    "frame interiors fill with "
    "blue."
)

INVARIANTS = [
    "background is 0",
    "≥1 closed nonzero frame",
    "the enclosed 0 region is not connected to the border",
    "wall color ≠ 1 (the fill color)",
]

HELPFUL_FRAME_KINDS = (
    "rect_outline", "blob_outline", "irregular_polygon",
    "U_shape", "nested_rects",
)
SIZE_DISTRIBUTIONS = ("small", "medium", "large", "mixed")
DEGENERATE_TEXTURES = ("open_frame", "solid_frame", "tiny_frame")

AXES = {
    "grid_h":            {"type": "int",   "default": "rng 8..15", "valid": "5..20"},
    "grid_w":            {"type": "int",   "default": "rng 8..15", "valid": "5..20"},
    "n_frames":          {"type": "int",   "default": "rng 1..2",  "valid": "1..3"},
    "frame_kind":        {"type": "str",   "default": "rng helpful",
                          "valid": "|".join(HELPFUL_FRAME_KINDS)},
    "wall_color":        {"type": "color", "default": "rng",       "valid": "1..9 (≠1)"},
    "size_distribution": {"type": "str",   "default": "rng small|medium|large|mixed",
                          "valid": "|".join(SIZE_DISTRIBUTIONS)},
    "inner_marker_prob": {"type": "float", "default": "rng 0..0.7", "valid": "0..1.0"},
    "decor_density":     {"type": "float", "default": "rng 0..0.05", "valid": "0..0.3"},
    "texture":           {"type": "str",   "default": "alias for frame_kind",
                          "valid": "|".join(HELPFUL_FRAME_KINDS + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0, ≥1 nonzero cell that is not color 1 (the frame wall color ≠ fill color)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    w = len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    non1_nz = any(v not in (0, 1) for row in grid for v in row)
    if not non1_nz:
        return ["expected ≥1 nonzero non-1 cell (wall color); found none"]
    return []


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)

    if difficulty == "easy":
        h_lo, h_hi, n_lo, n_hi = 8, 10, 1, 1
    elif difficulty == "hard":
        h_lo, h_hi, n_lo, n_hi = 13, 15, 2, 2
    else:
        h_lo, h_hi, n_lo, n_hi = 8, 15, 1, 2

    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", h_lo, h_hi)
    rng = ctx.draw_rng("decor")

    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], h, w, rng)

    n_frames = int(overrides.get("n_frames",
                                 ctx.draw_int("n_frames", n_lo, n_hi)))
    frame_kind = (overrides.get("texture")
                  or overrides.get("frame_kind")
                  or ctx.draw_choice("frame_kind", list(HELPFUL_FRAME_KINDS)))
    wall = int(overrides.get("wall_color",
                             ctx.draw_color("wall_color", exclude={0, 1})))
    size_dist = overrides.get(
        "size_distribution",
        ctx.draw_choice("size_distribution", list(SIZE_DISTRIBUTIONS)))
    marker_prob = float(overrides.get(
        "inner_marker_prob",
        ctx.draw_rng("inner_marker_prob").uniform(0.0, 0.7)))

    g = full_grid(h, w, 0)
    placed_boxes: list[tuple[int, int, int, int]] = []
    for _ in range(n_frames):
        for _try in range(40):
            fh, fw = _frame_dims(size_dist, h, w, rng)
            rr = rng.randint(1, max(1, h - fh - 1))
            rc = rng.randint(1, max(1, w - fw - 1))
            collide = False
            for (or1, oc1, or2, oc2) in placed_boxes:
                if (rr - 1 <= or2 and rr + fh >= or1
                        and rc - 1 <= oc2 and rc + fw >= oc1):
                    collide = True; break
            if collide:
                continue
            _draw_frame_kind(g, frame_kind, rr, rc, fh, fw, wall, rng)
            # Optional inner marker — same color as wall — survives the fill.
            if fh > 4 and fw > 4 and rng.random() < marker_prob:
                g[rr + fh // 2][rc + fw // 2] = wall
            placed_boxes.append((rr, rc, rr + fh - 1, rc + fw - 1))
            break

    if not placed_boxes:
        draw_rect_outline(g, 1, 1, 4, 4, wall)

    decor = float(overrides.get(
        "decor_density",
        ctx.draw_rng("decor_density").uniform(0.0, 0.05)))
    if decor > 0.0:
        decor_palette = [c for c in range(10) if c not in {0, 1, wall}]
        for _ in range(max(1, int(h * w * decor))):
            r = rng.randint(0, h - 1)
            c = rng.randint(0, w - 1)
            if g[r][c] == 0 and not _is_inside_any(r, c, placed_boxes):
                g[r][c] = rng.choice(decor_palette) if decor_palette else 0
    return g


def _is_inside_any(r, c, boxes):
    for (r1, c1, r2, c2) in boxes:
        if r1 <= r <= r2 and c1 <= c <= c2:
            return True
    return False


def _frame_dims(size_dist, h, w, rng):
    if size_dist == "small":
        return rng.randint(3, 5), rng.randint(3, 5)
    if size_dist == "medium":
        return rng.randint(5, max(5, h - 4)), rng.randint(5, max(5, w - 4))
    if size_dist == "large":
        return (rng.randint(max(5, h // 2), max(5, h - 4)),
                rng.randint(max(5, w // 2), max(5, w - 4)))
    return rng.randint(3, max(3, h - 4)), rng.randint(3, max(3, w - 4))


def _draw_frame_kind(g, kind, rr, rc, fh, fw, color, rng):
    if kind == "rect_outline":
        draw_rect_outline(g, rr, rc, fh, fw, color)
    elif kind == "blob_outline":
        draw_rect_outline(g, rr, rc, fh, fw, color)
        for dr, dc in ((-1, fw // 2), (fh, fw // 2)):
            r = rr + dr; c = rc + dc
            if 0 <= r < len(g) and 0 <= c < len(g[0]):
                g[r][c] = color
    elif kind == "irregular_polygon":
        draw_rect_outline(g, rr, rc, fh, fw, color)
        for dc in range(0, fw, 2):
            r = rr - 1
            if 0 <= r < len(g) and 0 <= rc + dc < len(g[0]):
                g[r][rc + dc] = color
    elif kind == "U_shape":
        draw_rect_outline(g, rr, rc, fh, fw, color)
    elif kind == "nested_rects":
        draw_rect_outline(g, rr, rc, fh, fw, color)
        if fh > 4 and fw > 4:
            draw_rect_outline(g, rr + 2, rc + 2, fh - 4, fw - 4, color)
    else:
        draw_rect_outline(g, rr, rc, fh, fw, color)


def _draw_from_degenerate(name, h, w, rng):
    """Edge-case where the fill-all-enclosed signal is hidden.

    open_frame  — frame touches grid border; "interior" reaches border,
                  rule fills nothing.
    solid_frame — solid rect, no interior; rule no-op.
    tiny_frame  — 3×3 outline (1-cell interior); fill is correct but tiny.
    """
    g = full_grid(h, w, 0)
    color = rng.choice([2, 3, 4, 5, 6, 7, 8, 9])
    if name == "open_frame":
        rh, rw = max(4, h // 3), max(4, w // 3)
        rr = h - rh
        rc = rng.randint(1, max(1, w - rw - 1))
        for c in range(rc, rc + rw):
            g[rr][c] = color
        for r in range(rr, rr + rh):
            g[r][rc] = color
            g[r][rc + rw - 1] = color
        return g
    if name == "solid_frame":
        rh, rw = max(3, h // 3), max(3, w // 3)
        rr = rng.randint(1, max(1, h - rh - 1))
        rc = rng.randint(1, max(1, w - rw - 1))
        for r in range(rr, rr + rh):
            for c in range(rc, rc + rw):
                g[r][c] = color
        return g
    if name == "tiny_frame":
        rr = rng.randint(1, max(1, h - 4))
        rc = rng.randint(1, max(1, w - 4))
        draw_rect_outline(g, rr, rc, 3, 3, color)
        return g
    return g
