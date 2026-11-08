"""Generator for arc_puzzle_bank_21_set16_bundle:hard_p03 — pair frames to solids by size.

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

GENERATOR_ID = "72c77addd109"
VERSION = "2.0.1"
TASK_ID = "72c77addd109"

SUMMARY = (
    "0-bg grid (h~11-14, w~14-17) with EXACTLY "
    "TWO HOLLOW RECTANGULAR FRAMES and EXACTLY "
    "TWO SOLID FILLED COMPONENTS, all 4 in "
    "DISTINCT non-0 colors: (a) FRAMES — sizes "
    "drawn without replacement from {(4,4), "
    "(5,5), (4,5), (5,4), (4,6)} giving "
    "DISTINCT interior areas; placed at non-"
    "overlapping non-touching positions (1-cell "
    "8-conn padding via _free); (b) SOLIDS — "
    "sizes drawn without replacement from {(2,"
    "2), (2,3), (3,2), (3,3)} giving DISTINCT "
    "cell counts; placed at non-touching "
    "positions disjoint from frames. Each "
    "solid fits inside its potential paired "
    "frame's interior. Rule (SORT FRAMES BY "
    "INTERIOR AREA ASCENDING, SORT SOLIDS BY "
    "SIZE ASCENDING, PAIR IN ORDER, EMIT EACH "
    "FRAME WITH ITS PAIRED SOLID CENTERED "
    "INSIDE): extract every HOLLOW RECTANGULAR "
    "FRAME (compute interior area = (rh-2) * "
    "(rw-2)). SORT frames by interior area "
    "ascending. extract every SOLID FILLED "
    "COMPONENT (count cells). SORT solids by "
    "cell count ascending. PAIR them in "
    "matched order: smallest-interior frame ↔ "
    "smallest solid, etc. PRODUCE a FRESH bg-0 "
    "grid: for each pair, REDRAW the frame at "
    "its ORIGINAL position; PASTE the paired "
    "solid CENTERED inside the frame's "
    "interior (preserving the solid's color). "
    "Original solid positions are dropped. "
    "Net: each frame now contains its size-"
    "matched solid centered in its interior."
)

# Rivals: 'output is input' refuted by demos (solids move into
# frames). 'pair by color' refuted by demos with size order ≠ color
# order. 'no centering' refuted by demos with off-center positioning
# visible. 'output frames only' refuted by demos with solids inside.
# 3 demos with ≥2 frame-solid pairs cover this.
EXAMPLES_NEEDED = 3

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


COMPATIBLE_DIM_PAIRS = (
    ((4, 4), (2, 2)),  # 2x2 interior receives 2x2 solid
    ((4, 5), (2, 3)),  # 2x3 interior receives 2x3 solid
    ((5, 4), (3, 2)),  # 3x2 interior receives 3x2 solid
    ((4, 6), (2, 3)),  # 2x4 interior receives 2x3 solid
    ((5, 5), (3, 3)),  # 3x3 interior receives 3x3 solid
)


def _frame_area(dim):
    fh, fw = dim
    return (fh - 2) * (fw - 2)


def _solid_area(dim):
    sh, sw = dim
    return sh * sw


def _fits(solid_dim, frame_dim):
    sh, sw = solid_dim
    fh, fw = frame_dim
    return sh <= fh - 2 and sw <= fw - 2


def _pick_dim_pairs(rng):
    """Pick two frame/solid pairs with unambiguous size order and fit.

    The rule sorts frames by interior area and solids by cell area before pairing.
    Therefore the selected pairs must have distinct frame areas, distinct solid
    areas, monotone frame/solid order, and each solid must fit in the paired
    frame interior without rotation.
    """
    for _ in range(80):
        pairs = rng.sample(list(COMPATIBLE_DIM_PAIRS), 2)
        by_frame = sorted(pairs, key=lambda p: _frame_area(p[0]))
        frame_areas = [_frame_area(frame) for frame, _ in by_frame]
        solid_areas = [_solid_area(solid) for _, solid in by_frame]
        if len(set(frame_areas)) != len(frame_areas):
            continue
        if len(set(solid_areas)) != len(solid_areas):
            continue
        if solid_areas != sorted(solid_areas):
            continue
        if not all(_fits(solid, frame) for frame, solid in by_frame):
            continue
        # Return in random drawing order; the sortable size relationship remains.
        return pairs
    raise ValueError("could not choose compatible distinct frame/solid sizes")


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
    # Sample frame/solid dimensions as compatible ordered pairs.  The former
    # independent samples could pick tied areas ((4,5) with (5,4), or (2,3)
    # with (3,2)) and could pair a 3x3 solid with a 2-row interior.  That hides
    # or breaks the intended "sort by size then center" rule.
    dim_pairs = _pick_dim_pairs(rng)
    frame_dims = [p[0] for p in dim_pairs]
    solid_dims = [p[1] for p in dim_pairs]

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
        # No frames — no destinations.
        for r in range(2):
            for c in range(2):
                g[3 + r][3 + c] = 1
        for r in range(3):
            for c in range(3):
                g[7 + r][9 + c] = 2
        return g
    if name == "no_solids":
        # Frames present but no solids to pair.
        draw_frame(g, 1, 1, 4, 4, 1)
        draw_frame(g, 6, 8, 10, 13, 2)
        return g
    if name == "tied_sizes":
        # Two frames with identical interior + two solids with identical size.
        draw_frame(g, 1, 1, 4, 4, 1)         # 4x4 → interior 2x2
        draw_frame(g, 1, 9, 4, 12, 2)        # 4x4 → interior 2x2 (same)
        for r in range(2):
            for c in range(2):
                g[7 + r][1 + c] = 3
        for r in range(2):
            for c in range(2):
                g[7 + r][9 + c] = 4
        return g
    return g



def _components(grid):
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
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen
                            and grid[nr][nc] == color):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            out.append((color, cells))
    return out


def _bbox(cells):
    rs = [r for r, _ in cells]
    cs = [c for _, c in cells]
    return min(rs), min(cs), max(rs), max(cs)


def _is_frame_component(cells):
    r1, c1, r2, c2 = _bbox(cells)
    h, w = r2 - r1 + 1, c2 - c1 + 1
    if h < 3 or w < 3:
        return False
    border = {(r, c) for r in range(r1, r2 + 1) for c in range(c1, c2 + 1)
              if r in (r1, r2) or c in (c1, c2)}
    return set(cells) == border


def _is_solid_rect_component(cells):
    if _is_frame_component(cells):
        return False
    r1, c1, r2, c2 = _bbox(cells)
    return set(cells) == {(r, c) for r in range(r1, r2 + 1) for c in range(c1, c2 + 1)}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Executable invariants for the frame/solid size-pairing input."""
    if not grid or not grid[0]:
        return ["empty grid"]
    w = len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    problems = []
    comps = _components(grid)
    frames = []
    solids = []
    for color, cells in comps:
        if _is_frame_component(cells):
            r1, c1, r2, c2 = _bbox(cells)
            frames.append((color, r2 - r1 - 1, c2 - c1 - 1))
        elif _is_solid_rect_component(cells):
            r1, c1, r2, c2 = _bbox(cells)
            solids.append((color, r2 - r1 + 1, c2 - c1 + 1))
        else:
            problems.append("non-frame/non-solid component present")
    if len(frames) != 2:
        problems.append(f"expected 2 hollow frames, found {len(frames)}")
    if len(solids) != 2:
        problems.append(f"expected 2 solid rectangles, found {len(solids)}")
    if len({c for c, _, _ in frames + solids}) != len(frames) + len(solids):
        problems.append("frame/solid colors are not all distinct")
    if len(frames) == 2:
        f_areas = [ih * iw for _, ih, iw in frames]
        if len(set(f_areas)) != 2:
            problems.append("frame interior areas are tied")
    if len(solids) == 2:
        s_areas = [sh * sw for _, sh, sw in solids]
        if len(set(s_areas)) != 2:
            problems.append("solid areas are tied")
    if len(frames) == 2 and len(solids) == 2:
        f_sorted = sorted(frames, key=lambda x: x[1] * x[2])
        s_sorted = sorted(solids, key=lambda x: x[1] * x[2])
        for (_, ih, iw), (_, sh, sw) in zip(f_sorted, s_sorted):
            if sh > ih or sw > iw:
                problems.append(f"sorted solid {sh}x{sw} does not fit sorted frame interior {ih}x{iw}")
    return sorted(set(problems))
