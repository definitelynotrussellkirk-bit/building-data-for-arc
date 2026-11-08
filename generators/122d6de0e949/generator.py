"""Generator for arc_puzzle_bank_21_set14_s:S14_H4.

The color-1 anchor contributes a column-count profile. The target object is
the first non-anchor component whose row profile is the reversed anchor column
profile.

Combinatorial axes (8): grid_h, grid_w, palette_kind, profile_variant,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_anchor, no_target_match, multiple_matches.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "122d6de0e949"
VERSION = "2.0.1"  # diversity: random anchor col-profile (varied len/counts) + random connected target shape matching the reversed row-profile (was 3 fixed 10x12 boards, 3 outputs); varied grid/positions/distractors
TASK_ID = "122d6de0e949"
SUMMARY = "Find the object whose row profile reverses the anchor column profile."

INVARIANTS = [
    "one color-1 anchor object has a nonuniform column profile",
    "exactly one non-anchor object has the reversed profile as its row profile",
    "distractors have different row profiles",
    "the selected object is cropped and recolored to 8",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_anchor", "no_target_match", "multiple_matches")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 9..14", "valid": "8..18"},
    "grid_w":         {"type": "int", "default": "rng 12..18", "valid": "10..22"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "profile_len":    {"type": "int", "default": "rng 3..4", "valid": "2..5"},
    "palette_size":   {"type": "int", "default": "3", "valid": "3..3"},
    "position_bias":  {"type": "str", "default": "anchor_plus_target_plus_distractor",
                       "valid": "anchor_plus_target_plus_distractor"},
    "n_distinct_colors": {"type": "int", "default": "3", "valid": "3..3"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _paint_cols(g, top, left, profile, color):
    """Paint a column-profile shape (column c has `count` cells from top)."""
    for c, count in enumerate(profile):
        for r in range(count):
            g[top + r][left + c] = color


def _shape_from_row_profile(rng, profile):
    """Build a 4-connected shape whose row r has exactly profile[r] cells.
    Each row is a contiguous horizontal run placed so consecutive rows
    overlap in >=1 column (keeps it 4-connected). Returns (cells, h, w)
    with cells normalized to (0,0)."""
    for _ in range(80):
        rows = []  # (start, length) per row
        prev_lo, prev_hi = None, None
        ok = True
        for cnt in profile:
            if cnt <= 0:
                ok = False
                break
            if prev_lo is None:
                start = rng.randint(0, 3)
            else:
                # overlap previous row's span by >=1 column
                lo = prev_lo - (cnt - 1)
                hi = prev_hi
                start = rng.randint(max(0, lo), max(0, hi))
            rows.append((start, cnt))
            prev_lo, prev_hi = start, start + cnt - 1
        if not ok:
            continue
        cells = [(r, start + i) for r, (start, cnt) in enumerate(rows)
                 for i in range(cnt)]
        mc = min(c for _, c in cells)
        cells = [(r, c - mc) for r, c in cells]
        h = len(profile)
        w = max(c for _, c in cells) + 1
        # verify 4-connected
        cs = set(cells)
        stack = [cells[0]]
        seen = {cells[0]}
        while stack:
            r, c = stack.pop()
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                p = (r + dr, c + dc)
                if p in cs and p not in seen:
                    seen.add(p)
                    stack.append(p)
        if len(seen) == len(cs):
            return cells, h, w
    # fallback: left-aligned bars (always connected if each row >=1)
    cells = [(r, c) for r, cnt in enumerate(profile) for c in range(cnt)]
    return cells, len(profile), max(profile)


def _place_shape(g, occ, rng, cells, h, w, color, gh, gw):
    for _t in range(120):
        top = rng.randint(0, gh - h)
        left = rng.randint(0, gw - w)
        abs_cells = [(top + r, left + c) for r, c in cells]
        clear = all(
            0 <= rr < gh and 0 <= cc < gw and (rr, cc) not in occ
            for r, c in abs_cells
            for rr, cc in ((top + r + dr, left + c + dc)
                           for dr in (-1, 0, 1) for dc in (-1, 0, 1)))
        if not clear:
            continue
        for r, c in abs_cells:
            g[r][c] = color
            occ.add((r, c))
        return True
    return False


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: rectangular grid; has a color-1 anchor; background is 0."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errors = []
    ones = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 1]
    if not ones:
        return errors  # degenerate (no_anchor) — allowed
    # Grid dimensions in valid range
    if h < 8 or h > 18:
        errors.append(f"grid_h={h} out of valid range 8..18")
    if w < 10 or w > 22:
        errors.append(f"grid_w={w} out of valid range 10..22")
    return errors


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        gh = ctx.draw_int("grid_h", 9, 11)
        gw = ctx.draw_int("grid_w", 12, 14)
        plen = ctx.draw_int("profile_len", 3, 3)
    elif difficulty == "hard":
        gh = ctx.draw_int("grid_h", 12, 14)
        gw = ctx.draw_int("grid_w", 16, 18)
        plen = ctx.draw_int("profile_len", 4, 5)
    else:
        gh = ctx.draw_int("grid_h", 9, 14)
        gw = ctx.draw_int("grid_w", 12, 18)
        plen = ctx.draw_int("profile_len", 3, 4)

    # Placement congestion (esp. hard band: longer profiles + 2 distractors on a
    # tight board) exhausts the 120-try placement loop for ~8% of seeds. Retrying
    # the same size doesn't help, so GROW the canvas every 150 failed attempts --
    # the rule is size-agnostic, so a slightly larger board guarantees room.
    for _attempt in range(900):
        if _attempt and _attempt % 150 == 0:
            gh += 1; gw += 1
        # anchor column-profile: each column has 1..4 cells, not all equal
        anchor_profile = [rng.randint(1, 4) for _ in range(plen)]
        if len(set(anchor_profile)) < 2:
            continue
        target_profile = list(reversed(anchor_profile))
        # distractor row-profiles must differ from target_profile
        cols = rng.sample([3, 4, 5, 6, 7, 9], 2)
        target_color, distractor_color = cols[0], cols[1]

        g = full_grid(gh, gw, 0)
        occ = set()

        # anchor (color 1): column profile, place as a unit
        ah = max(anchor_profile)
        aw = len(anchor_profile)
        anchor_cells = [(r, c) for c, cnt in enumerate(anchor_profile)
                        for r in range(cnt)]
        if not _place_shape(g, occ, rng, anchor_cells, ah, aw, 1, gh, gw):
            continue

        # target: connected shape with row-profile == reversed anchor
        tcells, th, tw = _shape_from_row_profile(rng, target_profile)
        if not _place_shape(g, occ, rng, tcells, th, tw, target_color,
                            gh, gw):
            continue

        # 1-2 distractors with DIFFERENT row-profiles
        n_dist = rng.randint(1, 2)
        for _ in range(n_dist):
            for _t in range(20):
                dp = [rng.randint(1, 4) for _ in range(rng.randint(2, 4))]
                if dp != target_profile:
                    break
            else:
                continue
            dcells, dh, dw = _shape_from_row_profile(rng, dp)
            _place_shape(g, occ, rng, dcells, dh, dw, distractor_color,
                         gh, gw)

        # Final gate: the board must reproduce the rule's selection
        # cleanly (one connected anchor, exactly one matching target).
        if _selectable(g, target_profile):
            return g
    raise ValueError("could not realize profile-match board")


def _per_color_components(g):
    h, w = len(g), len(g[0])
    seen = set()
    out = []
    for r in range(h):
        for c in range(w):
            if g[r][c] != 0 and (r, c) not in seen:
                col = g[r][c]
                stack = [(r, c)]
                seen.add((r, c))
                cells = []
                while stack:
                    rr, cc = stack.pop()
                    cells.append((rr, cc))
                    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        nr, nc = rr + dr, cc + dc
                        if (0 <= nr < h and 0 <= nc < w
                                and g[nr][nc] == col
                                and (nr, nc) not in seen):
                            seen.add((nr, nc))
                            stack.append((nr, nc))
                out.append((col, cells))
    return out


def _row_profile(cells):
    r1 = min(r for r, _ in cells)
    r2 = max(r for r, _ in cells)
    return [sum(1 for r, _ in cells if r == rr) for rr in range(r1, r2 + 1)]


def _col_profile(cells):
    c1 = min(c for _, c in cells)
    c2 = max(c for _, c in cells)
    return [sum(1 for _, c in cells if c == cc) for cc in range(c1, c2 + 1)]


def _selectable(g, target_profile):
    """Mirror the rule's discriminator: exactly one color-1 component,
    its reversed col-profile == target_profile, and exactly one
    non-anchor component whose row-profile == target_profile."""
    comps = _per_color_components(g)
    anchors = [c for col, c in comps if col == 1]
    if len(anchors) != 1:
        return False
    if list(reversed(_col_profile(anchors[0]))) != target_profile:
        return False
    matches = sum(1 for col, c in comps if col != 1
                  and _row_profile(c) == target_profile)
    return matches == 1


def _draw_from_degenerate(name, rng):
    g = full_grid(10, 12, 0)
    if name == "no_anchor":
        # no color-1 anchor → no profile to compute, no selection
        _paint_rows(g, 5, 6, [2, 1, 3], 4)
        _paint_rows(g, 6, 1, [1, 2, 1], 6)
        return g
    if name == "no_target_match":
        # anchor present but no candidate has the reversed profile → no selection
        _paint_cols(g, 1, 1, [1, 3, 2], 1)
        _paint_rows(g, 5, 6, [1, 2, 1], 4)
        _paint_rows(g, 6, 1, [3, 1, 2], 6)
        return g
    if name == "multiple_matches":
        # multiple non-anchor objects share the reversed profile → ambiguous
        _paint_cols(g, 1, 1, [1, 3, 2], 1)
        _paint_rows(g, 5, 6, [2, 3, 1], 4)
        _paint_rows(g, 7, 1, [2, 3, 1], 6)
        return g
    return g
