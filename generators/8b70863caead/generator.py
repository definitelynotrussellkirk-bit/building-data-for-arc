"""Generator for v1_e_m_h_keys:H7 — intersection of first two objects.

REAL rule (the "gallery pack" docstring was WRONG): take the first two
objects in scan order, normalize each to its bbox, and output the bbox of
their normalized-cell INTERSECTION painted color 8.

The old generator scattered random motifs, so the first-two intersection was
uncontrolled (often empty -> 1x1, or tiny) -> low diversity / dups. This
builds two shapes that share a chosen target T (the intersection) plus
disjoint extras, so the output is exactly T and varies freely.

Combinatorial axes: the intersection target T, the two shapes' extras, grid.
Degenerates: no_motifs, single_motif, all_same_color.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "8b70863caead"
VERSION = "3.0.0"  # WRONG-TASK + distinct=32: rule outputs the normalized-cell INTERSECTION of the first 2 objects (painted 8); generator scattered random motifs so the intersection was uncontrolled (often empty/tiny). Build 2 shapes sharing a chosen target T (the output) + disjoint extras.
TASK_ID = "8b70863caead"

SUMMARY = (
    "0-bg grid with exactly two ISOLATED connected objects that share a common "
    "normalized sub-shape T (a random polyomino) plus disjoint extra cells. "
    "Rule: take the first two objects, normalize each, output the bbox of their "
    "cell intersection painted 8 -- which equals T. The target T, the two "
    "shapes' extras, colors and grid size all vary."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "exactly two connected objects in distinct colors",
    "their normalized cell-sets intersect in exactly the target sub-shape T",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_motifs", "single_motif", "all_same_color")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 9..11", "valid": "7..16"},
    "grid_w":         {"type": "int", "default": "rng 11..13", "valid": "9..18"},
    "n":              {"type": "int", "default": "rng 3..4", "valid": "2..5"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "palette_size":   {"type": "int", "default": "rng 3..4", "valid": "2..5"},
    "position_bias":  {"type": "str", "default": "scattered_colored_motifs",
                       "valid": "scattered_colored_motifs"},
    "n_distinct_colors": {"type": "int", "default": "rng 3..4", "valid": "2..5"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _free(g, r1, c1, r2, c2):
    h, w = len(g), len(g[0])
    if r1 < 0 or c1 < 0 or r2 >= h or c2 >= w: return False
    for r in range(max(0, r1 - 1), min(h, r2 + 2)):
        for c in range(max(0, c1 - 1), min(w, c2 + 2)):
            if g[r][c] != 0: return False
    return True


def _build_motif(rng, k):
    cells = [(0, 0)]; seen = {(0, 0)}
    while len(cells) < k:
        r, c = rng.choice(cells)
        dr, dc = rng.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        if (r + dr, c + dc) not in seen:
            cells.append((r + dr, c + dc)); seen.add((r + dr, c + dc))
    rmin = min(r for r, _ in cells); cmin = min(c for _, c in cells)
    return [(r - rmin, c - cmin) for r, c in cells]


def _grow_extra(rng, base, forbidden, k):
    """Add k cells adjacent to `base`, all with row>=0 and col>=0 (so the
    bbox anchor stays at base's min) and not in `forbidden`.

    The previous random-probe version could return zero cells for the second
    object when the first object's extras happened to occupy the sampled
    frontier.  That made one object equal the target intersection, hiding the
    "extra cells are discarded" branch.  Maintain an explicit frontier instead.
    """
    cells = set(base)
    added = []
    while len(added) < k:
        candidates = []
        for r, c in cells:
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nr, nc = r + dr, c + dc
                if nr < 0 or nc < 0 or (nr, nc) in cells or (nr, nc) in forbidden:
                    continue
                candidates.append((nr, nc))
        if not candidates:
            break
        nr, nc = rng.choice(sorted(set(candidates)))
        cells.add((nr, nc))
        added.append((nr, nc))
    return added


def _place(g, rng, cells, color):
    h, w = len(g), len(g[0])
    sh = max(r for r, _ in cells) + 1; sw = max(c for _, c in cells) + 1
    for _ in range(80):
        r0 = rng.randint(0, h - sh); c0 = rng.randint(0, w - sw)
        if _free(g, r0, c0, r0 + sh - 1, c0 + sw - 1):
            for r, c in cells:
                g[r0 + r][c0 + c] = color
            return True
    return False


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 9, 10); w = ctx.draw_int("grid_w", 11, 13)
        t_lo, t_hi = 2, 4
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 12, 16); w = ctx.draw_int("grid_w", 14, 18)
        t_lo, t_hi = 4, 7
    else:
        h = ctx.draw_int("grid_h", 10, 13); w = ctx.draw_int("grid_w", 12, 15)
        t_lo, t_hi = 3, 6
    rng = ctx.draw_rng("layout")
    for _outer in range(40):
        g = full_grid(h, w, 0)
        target = _build_motif(rng, rng.randint(t_lo, t_hi))     # the intersection T
        tset = set(target)
        ea = _grow_extra(rng, target, tset, rng.randint(1, 3))
        eb = _grow_extra(rng, target, tset | set(ea), rng.randint(1, 3))
        if not ea or not eb:
            # Both objects need visible extras; otherwise one object is exactly
            # the intersection T and the learner never has to discard cells.
            continue
        a = target + ea
        b = target + eb
        col_a, col_b = rng.sample([2, 3, 4, 5, 6, 7, 8, 9], 2)
        if _place(g, rng, a, col_a) and _place(g, rng, b, col_b):
            return g
    raise ValueError("could not realize intersection layout")


def _draw_from_degenerate(name, rng):
    h, w = 10, 12
    g = full_grid(h, w, 0)
    if name == "no_motifs":
        # Empty grid — rule has no motifs to gather.
        return g
    if name == "single_motif":
        # Only 1 motif — rule's gallery is trivial.
        for r, c in [(2, 2), (2, 3), (3, 3), (3, 4)]: g[r][c] = 4
        return g
    if name == "all_same_color":
        # All motifs share a color — rule's per-color gather
        # treats them as one big component.
        for r, c in [(1, 1), (1, 2), (2, 2)]: g[r][c] = 4
        for r, c in [(5, 6), (5, 7), (6, 7)]: g[r][c] = 4
        for r, c in [(8, 1), (8, 2), (9, 2)]: g[r][c] = 4
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
            q = [(r, c)]
            seen.add((r, c))
            cells = []
            for rr, cc in q:
                cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen
                            and grid[nr][nc] != 0):
                        seen.add((nr, nc))
                        q.append((nr, nc))
            out.append((color, cells))
    return out


def _normalized(cells):
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return {(r - r0, c - c0) for r, c in cells}


def self_check(grid, *, difficulty=None, meta=None):
    """Executable invariants for the first-two-object normalized intersection task."""
    issues = []
    if not grid or not isinstance(grid, list) or not isinstance(grid[0], list):
        return ["grid must be a non-empty 2D list"]
    w = len(grid[0])
    if any(len(row) != w for row in grid):
        return ["grid rows must be rectangular"]
    comps = _components(grid)
    if len(comps) != 2:
        issues.append(f"expected exactly two isolated nonzero objects, got {len(comps)}")
        return issues
    if len({color for color, _ in comps}) != 2:
        issues.append("the two objects must have distinct colors")
    norm = [_normalized(cells) for _, cells in comps]
    inter = norm[0] & norm[1]
    if not inter:
        issues.append("normalized intersection of first two objects must be non-empty")
    if inter and (len(inter) == len(norm[0]) or len(inter) == len(norm[1])):
        issues.append("each object must contain at least one visible extra cell outside the intersection")
    return issues
