"""Generator for ARC task be94b721.

Rule: `(rule! extract-largest)` — return a crop of the largest connected
non-zero object, by cell count.

Combinatorial axes:
  * grid_h / grid_w        — outer canvas size
  * largest_kind           — shape of the dominant object (rect / L / hollow / blob / cross / line_h / line_v)
  * largest_h / largest_w  — bbox of the dominant object
  * n_distractors          — number of other objects (1..6)
  * distractor_size_dist   — "tiny" (all 1-2 cells), "mixed" (1-4 cells),
                              "close" (one distractor up to ~70% of largest)
  * placement              — where the largest sits (random / center / corner)
  * caller-opt-in degenerates: ties_for_largest, single_object
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_rect, full_grid

GENERATOR_ID = "fea6a4ce763f"
VERSION = "2.2.3"  # canonical-scale canvases; default avoids solid-color crops; +self_check
TASK_ID = "fea6a4ce763f"
SUMMARY = (
    "0-bg grid (canonical-scale h~5-9, w~9-15) with "
    "ONE DOMINANT OBJECT in a "
    "chosen LARGEST_KIND shape "
    "(rect/L_shape/hollow_ring/"
    "random_blob/cross/line_h/"
    "line_v), at bbox size "
    "(largest_h × largest_w) "
    "placed by PLACEMENT (random/"
    "left_half/center/corner). "
    "Plus 1-6 DISTRACTOR OBJECTS "
    "in other colors with bounded "
    "size (tiny/mixed/close — "
    "always < dominant area). "
    "Objects are 4-conn isolated, "
    "with strict size dominance. "
    "Rule (CROP LARGEST OBJECT): "
    "identify all CONNECTED "
    "COMPONENTS in the grid. "
    "Find the one with the "
    "LARGEST CELL COUNT. CROP "
    "to its BBOX. EMIT that "
    "crop as the output. Net: "
    "largest non-bg component "
    "→ output as cropped subgrid."
)

INVARIANTS = [
    "background is zero",
    "there is exactly one object with strictly largest cell count",
    "objects are spatially separated (4-connected components don't merge)",
]

LARGEST_KINDS = (
    "rect", "L_shape", "hollow_ring", "random_blob",
    "cross", "line_h", "line_v",
)
DISTRACTOR_SHAPES = ("rect", "single", "line_h", "line_v", "L_shape")
SIZE_DISTRIBUTIONS = ("tiny", "mixed", "close")
PLACEMENTS = ("random", "left_half", "center", "corner")
# Default/helpful draws should not collapse to a solid-color crop: a solid rectangle/line
# technically exercises extract-largest, but it under-teaches the crop boundary and trips the
# generic all-solid-output defect lint. Keep those shapes as explicit largest_kind overrides.
HELPFUL_TEXTURES = ("L_shape", "hollow_ring", "cross")
DEGENERATE_TEXTURES = ("ties_for_largest", "single_object")

AXES = {
    "grid_h":         {"type": "int", "default": "rng 5..9",  "valid": "5..14"},
    "grid_w":         {"type": "int", "default": "rng 9..15", "valid": "8..18"},
    "largest_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(LARGEST_KINDS)},
    "largest_h":      {"type": "int", "default": "rng 4..lcap (8 easy/12 med/14 hard, ≤h-3)", "valid": "3..14"},
    "largest_w":      {"type": "int", "default": "rng 3..lcap (8 easy/12 med/14 hard, ≤w-3)", "valid": "3..14"},
    "n_distractors":  {"type": "int", "default": "1-3 easy / 2-6 med / 3-8 hard", "valid": "1..8"},
    "distractor_size_dist": {"type": "str", "default": "rng tiny|mixed|close",
                             "valid": "|".join(SIZE_DISTRIBUTIONS)},
    "placement":      {"type": "str", "default": "rng random|left_half|center|corner",
                       "valid": "|".join(PLACEMENTS)},
    "texture":        {"type": "str", "default": "rng helpful (alias for largest_kind)",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)

    if difficulty == "easy":
        h_lo, h_hi, w_lo, w_hi = 5, 6, 9, 11
        lcap, ndist_lo, ndist_hi = 4, 1, 3
    elif difficulty == "hard":
        h_lo, h_hi, w_lo, w_hi = 7, 9, 11, 15
        lcap, ndist_lo, ndist_hi = 6, 2, 5
    else:
        h_lo, h_hi, w_lo, w_hi = 5, 8, 9, 14
        lcap, ndist_lo, ndist_hi = 5, 2, 4

    h = ctx.draw_int("grid_h", h_lo, h_hi)
    w = ctx.draw_int("grid_w", w_lo, w_hi)
    rng = ctx.draw_rng("placement")

    # Caller-opt-in degenerate path.
    texture_override = overrides.get("texture")
    if texture_override in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(texture_override, h, w, ctx, rng)

    # Pick the dominant-object kind. `texture` and `largest_kind` are aliases.
    kind = (texture_override
            or overrides.get("largest_kind")
            or ctx.draw_choice("largest_kind", list(HELPFUL_TEXTURES)))

    # The output is the dominant object's bbox crop, so let it SCALE WITH THE GRID
    # (was artificially capped at 10 and at half the width). Bigger/varied dominants
    # -> bigger/varied output crops. Keep ~3 cells of margin so distractors still fit.
    lh = ctx.draw_int("largest_h", 3, max(3, min(lcap, h - 2)))
    lw = ctx.draw_int("largest_w", 3, max(3, min(lcap, w - 2)))

    # Draw enough colors for one dominant + n_distractors (distinct colors -> up to 9).
    n_dist = int(overrides.get("n_distractors",
                               ctx.draw_int("n_distractors", ndist_lo, ndist_hi)))
    n_colors = max(2, n_dist + 1)
    colors = ctx.draw_distinct_colors("colors", n=min(9, n_colors), exclude={0})

    # Placement of dominant object.
    placement = overrides.get(
        "placement",
        ctx.draw_choice("placement", list(PLACEMENTS)),
    )
    lr, lc = _place_largest(placement, h, w, lh, lw, rng)

    g = full_grid(h, w, 0)
    _paint_object(g, kind, lr, lc, lh, lw, colors[0], rng)
    largest_area = sum(1 for r in range(lr, lr + lh) for c in range(lc, lc + lw)
                       if g[r][c] == colors[0])

    # Distractors. Their sizes are bounded so the dominant remains strictly largest.
    size_dist = overrides.get(
        "distractor_size_dist",
        ctx.draw_choice("distractor_size_dist", list(SIZE_DISTRIBUTIONS)),
    )
    _plant_distractors(g, n_dist, colors[1:], size_dist, largest_area, rng)
    return g


def _place_largest(placement, h, w, lh, lw, rng):
    """Pick (lr, lc) — top-left of the largest object's bbox — given placement."""
    if placement == "left_half":
        return (rng.randint(1, h - lh - 1),
                rng.randint(1, max(1, (w // 2) - lw - 1)))
    if placement == "center":
        return ((h - lh) // 2, (w - lw) // 2)
    if placement == "corner":
        corners = [(1, 1), (1, w - lw - 1),
                   (h - lh - 1, 1), (h - lh - 1, w - lw - 1)]
        return rng.choice(corners)
    # random
    return (rng.randint(1, h - lh - 1),
            rng.randint(1, w - lw - 1))


def _paint_object(g, kind, rr, rc, sh, sw, color, rng):
    """Paint one object of given kind into g[rr:rr+sh, rc:rc+sw]."""
    if kind == "rect":
        for dr in range(sh):
            for dc in range(sw):
                g[rr + dr][rc + dc] = color
    elif kind == "L_shape":
        for dr in range(sh):
            g[rr + dr][rc] = color
        for dc in range(sw):
            g[rr + sh - 1][rc + dc] = color
    elif kind == "hollow_ring":
        for dc in range(sw):
            g[rr][rc + dc] = color
            g[rr + sh - 1][rc + dc] = color
        for dr in range(sh):
            g[rr + dr][rc] = color
            g[rr + dr][rc + sw - 1] = color
    elif kind == "random_blob":
        # CONNECTED random blob grown by random walk within the sh x sw region
        # (the old per-cell sprinkle could leave forced corners isolated, splitting
        # the "dominant" into pieces and breaking strict-largest dominance). The
        # rule crops to the actual bbox, so a sub-bbox connected blob is fine.
        target = max(4, int(round(0.6 * sh * sw)))
        cells = {(rng.randrange(sh), rng.randrange(sw))}
        frontier = list(cells)
        while len(cells) < target and frontier:
            cr, cc = rng.choice(frontier)
            opts = [(cr + dr, cc + dc) for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1))
                    if 0 <= cr + dr < sh and 0 <= cc + dc < sw
                    and (cr + dr, cc + dc) not in cells]
            if not opts:
                frontier.remove((cr, cc))
                continue
            nc = rng.choice(opts)
            cells.add(nc)
            frontier.append(nc)
        for dr, dc in cells:
            g[rr + dr][rc + dc] = color
    elif kind == "cross":
        mr, mc = sh // 2, sw // 2
        for dc in range(sw):
            g[rr + mr][rc + dc] = color
        for dr in range(sh):
            g[rr + dr][rc + mc] = color
    elif kind == "line_h":
        mid = sh // 2
        for dc in range(sw):
            g[rr + mid][rc + dc] = color
    elif kind == "line_v":
        mid = sw // 2
        for dr in range(sh):
            g[rr + dr][rc + mid] = color
    else:
        # Fallback: solid rect.
        for dr in range(sh):
            for dc in range(sw):
                g[rr + dr][rc + dc] = color


def _has_gap(g, rr, rc, dh=1, dw=1):
    """True iff the candidate bbox is empty and one-cell separated from fg."""
    h, w = len(g), len(g[0])
    if rr < 0 or rc < 0 or rr + dh > h or rc + dw > w:
        return False
    for r in range(max(0, rr - 1), min(h, rr + dh + 1)):
        for c in range(max(0, rc - 1), min(w, rc + dw + 1)):
            if g[r][c] != 0:
                return False
    return True


def _has_4conn_sep(g, rr, rc):
    """Weaker fallback for a 1-cell distractor: empty and not 4-adjacent to fg.

    Diagonal contact does not merge 4-connected nonzero components, so this is
    still safe for extract-largest while rescuing very tight canvases where a
    full one-cell halo is impossible.
    """
    h, w = len(g), len(g[0])
    if not (0 <= rr < h and 0 <= rc < w) or g[rr][rc] != 0:
        return False
    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        nr, nc = rr + dr, rc + dc
        if 0 <= nr < h and 0 <= nc < w and g[nr][nc] != 0:
            return False
    return True


def _plant_distractors(g, n, palette, size_dist, largest_area, rng):
    """Place n distractor objects and return how many were actually planted.

    A nondegenerate extract-largest lesson needs at least one smaller object;
    otherwise the demos are compatible with a trivial "crop the only object"
    rule.  The old helper silently gave up after 40 failed attempts for each
    distractor, which produced single-object cases in tight canvases.  Keep the
    randomized placements, but add a deterministic single-cell fallback that
    preserves the one-cell separation invariant.
    """
    h, w = len(g), len(g[0])
    if size_dist == "close":
        max_size = max(2, int(largest_area * 0.7))
    elif size_dist == "tiny":
        max_size = 2
    else:  # mixed
        max_size = max(2, int(largest_area * 0.4))

    placed = 0
    for i in range(n):
        color = palette[i % len(palette)] if palette else 0
        did_place = False
        # Try several placements until one fits and doesn't overlap existing fg.
        for _ in range(40):
            ds = max(1, min(max_size, rng.randint(1, max_size)))
            dh = max(1, min(rng.randint(1, ds), h - 2))
            dw = max(1, min(max(1, ds // max(dh, 1)), w - 2))
            shape = rng.choice(DISTRACTOR_SHAPES)
            rr = rng.randint(1, h - dh - 1)
            rc = rng.randint(1, w - dw - 1)
            # Check non-overlap (4-connected, with 1-cell gap).
            if not _has_gap(g, rr, rc, dh, dw):
                continue
            # Cap distractor area to <= max_size cells.
            _paint_object(g, shape, rr, rc, dh, dw, color, rng)
            # Trim if shape exceeded max_size.
            cells = [(r, c) for r in range(rr, rr + dh)
                              for c in range(rc, rc + dw)
                              if g[r][c] == color]
            if len(cells) > max_size:
                extras = cells[max_size:]
                for r, c in extras:
                    g[r][c] = 0
            placed += 1
            did_place = True
            break
        if did_place:
            continue
        # Fallback: a one-cell distractor is still an object strictly smaller
        # than the dominant.  Shuffle all interior cells to keep seed variation.
        cells = [(r, c) for r in range(1, h - 1) for c in range(1, w - 1)]
        rng.shuffle(cells)
        for rr, rc in cells:
            if _has_gap(g, rr, rc):
                g[rr][rc] = color
                placed += 1
                break
        else:
            # Last resort for very tight canvases: keep 4-connected separation
            # even if diagonal adjacency means the stricter halo is impossible.
            for rr, rc in cells:
                if _has_4conn_sep(g, rr, rc):
                    g[rr][rc] = color
                    placed += 1
                    break
    return placed



def _components(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    comps = []
    for sr in range(h):
        for sc in range(w):
            if grid[sr][sc] == 0 or (sr, sc) in seen:
                continue
            color = grid[sr][sc]
            stack = [(sr, sc)]; seen.add((sr, sc)); cells = []
            while stack:
                r, c = stack.pop(); cells.append((r, c))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if (0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen
                            and grid[nr][nc] == color):
                        seen.add((nr, nc)); stack.append((nr, nc))
            comps.append((color, cells))
    return comps


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Nondegenerate extract-largest input: one strict largest component + distractor."""
    if not grid or not grid[0]:
        return ["empty grid"]
    w = len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    comps = _components(grid)
    if len(comps) < 2:
        return ["expected dominant object plus at least one distractor"]
    sizes = sorted((len(cells) for _color, cells in comps), reverse=True)
    errs = []
    if sizes[0] == sizes[1]:
        errs.append("largest object is not unique by cell count")
    # Default helpful draws should show a shaped crop, not just a solid rectangle/line.
    color, cells = max(comps, key=lambda item: len(item[1]))
    r0 = min(r for r, _ in cells); r1 = max(r for r, _ in cells)
    c0 = min(c for _, c in cells); c1 = max(c for _, c in cells)
    area = (r1 - r0 + 1) * (c1 - c0 + 1)
    if area >= 9 and len(cells) == area:
        errs.append("largest-object crop is a solid single-color rectangle; weak extract-largest signal")
    return errs

def _draw_from_degenerate(name, h, w, ctx, rng):
    """Edge-case where the rule's "largest object" signature is hidden.

    ties_for_largest — two objects of identical cell count exist. The rule
                       returns one of them (Racket's `pick-max` is
                       deterministic), but the demonstration is ambiguous
                       to a model that hasn't internalized the tie-break.
    single_object    — only one foreground object exists, so any "select"
                       rule (largest, smallest, by-color) produces the
                       same output. Demonstration carries less rule signal.
    """
    g = full_grid(h, w, 0)
    colors = ctx.draw_distinct_colors("colors", n=3, exclude={0})
    if name == "ties_for_largest":
        # Place two identical-size 4x4 rectangles plus one smaller distractor.
        size = 4
        draw_rect(g, 1, 1, size, size, colors[0])
        draw_rect(g, 1, w - size - 1, size, size, colors[1])
        draw_rect(g, h - 3, max(1, w // 2 - 1), 2, 2, colors[2])
        return g
    if name == "single_object":
        size = rng.randint(3, max(3, min(6, h - 2, w - 2)))
        draw_rect(g, 1, 1, size, size, colors[0])
        return g
    return g
