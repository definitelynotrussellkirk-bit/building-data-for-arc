"""Generator for 20_bundle:m140 — select object touching 2 borders, crop.

Rule: components merge ALL adjacent non-zero cells (color-blind);
border count = how many of the 4 grid edges hold >=1 cell. The FIRST
component (scan order) touching EXACTLY 2 borders is cropped to its
bbox (its own cells keep their colors; other content in the bbox
becomes 0).

Combinatorial axes: grid_h/w, target_kind (corner|span_v|span_h),
texture (plain|one_border|three_border|multicolor).
Degenerates: no_two_border (CRASHES the rule - never generated; kept
out), multiple_two_border (first in scan order wins, rng-varied),
target_only.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "076ce2aa4e8c"
VERSION = "3.0.1"
TASK_ID = "076ce2aa4e8c"
SUMMARY = (
    "One blob touches exactly TWO grid borders - a corner blob (any "
    "of the 4 corners, random grown shape) or a bar spanning top+"
    "bottom / left+right - and gets cropped to its bbox. Decoys touch "
    "0, 1, or 3 borders and are ignored; components are color-blind "
    "so multicolor targets crop with both colors. (Was: the same "
    "3-cell L at the top-left corner every board - outputs were one "
    "2x2 shape in 8 colors; the 'intrinsic-low' flag was wrong.)"
)

# Rivals: 'pick the corner object' refuted by span boards (top+bottom
# counts as 2 borders, no corner involved). 'pick by color/size'
# refuted by varied decoys. 'one border is enough' refuted by
# one_border decoys staying. '3+ borders counts' refuted by
# three_border decoys. 'per-color objects' refuted by multicolor
# targets. 4 demos incl. >=1 span + >=1 three_border.
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "exactly one component touches exactly 2 borders (mirror-verified), except multiple_two_border",
    ">=1 component ALWAYS with exactly 2 borders (none would crash the rule)",
    "decoys touch 0/1/3 borders, never 2",
]

DEGENERATE_TEXTURES = ("target_only", "multiple_two_border")
HELPFUL_TEXTURES = ("plain", "one_border", "three_border", "multicolor")

AXES = {
    "grid_h":      {"type": "int", "default": "rng 7..12", "valid": "6..16"},
    "grid_w":      {"type": "int", "default": "rng 8..14", "valid": "7..16"},
    "target_kind": {"type": "str", "default": "rng",
                    "valid": "corner|span_v|span_h"},
    "texture":     {"type": "str", "default": "rng helpful",
                    "valid": "plain|one_border|three_border|multicolor|"
                             "target_only|multiple_two_border",
                    "doc": "one_border/three_border: decoys with the wrong "
                           "border count; multicolor: target in 2 colors "
                           "(components are color-blind)."},
}


def _comps(g):
    h, w = len(g), len(g[0])
    seen = [[False] * w for _ in range(h)]
    out = []
    for r0 in range(h):
        for c0 in range(w):
            if g[r0][c0] == 0 or seen[r0][c0]:
                continue
            stack = [(r0, c0)]
            seen[r0][c0] = True
            cells = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    rr, cc = r + dr, c + dc
                    if 0 <= rr < h and 0 <= cc < w and not seen[rr][cc] \
                            and g[rr][cc] != 0:
                        seen[rr][cc] = True
                        stack.append((rr, cc))
            out.append(sorted(cells))
    return out


def _borders(cells, h, w):
    return sum((any(r == 0 for r, _ in cells),
                any(r == h - 1 for r, _ in cells),
                any(c == 0 for _, c in cells),
                any(c == w - 1 for _, c in cells)))


def _mirror(g):
    h, w = len(g), len(g[0])
    hit = None
    for cells in _comps(g):
        if _borders(cells, h, w) == 2:
            hit = cells
            break
    if hit is None:
        return None
    r1 = min(r for r, _ in hit)
    r2 = max(r for r, _ in hit)
    c1 = min(c for _, c in hit)
    c2 = max(c for _, c in hit)
    out = [[0] * (c2 - c1 + 1) for _ in range(r2 - r1 + 1)]
    for r, c in hit:
        out[r - r1][c - c1] = g[r][c]
    return out


def _grow_from(rng, seeds, allowed, k):
    cells = list(seeds)
    seen = set(cells)
    for _ in range(200):
        if len(cells) >= k:
            break
        r, c = cells[rng.randrange(len(cells))]
        dr, dc = ((-1, 0), (1, 0), (0, -1), (0, 1))[rng.randrange(4)]
        p = (r + dr, c + dc)
        if p in seen or p not in allowed:
            continue
        cells.append(p)
        seen.add(p)
    return cells


def _make_target(rng, h, w, kind):
    if kind == "corner":
        corner = rng.choice(((0, 0), (0, w - 1), (h - 1, 0), (h - 1, w - 1)))
        rzone = range(0, h - 2) if corner[0] == 0 else range(2, h)
        czone = range(0, w - 2) if corner[1] == 0 else range(2, w)
        allowed = {(r, c) for r in rzone for c in czone}
        return _grow_from(rng, [corner], allowed, rng.randint(3, 7))
    if kind == "span_v":
        c = rng.randint(1, w - 2)
        cells = [(r, c) for r in range(h)]
        allowed = {(r, cc) for r in range(h) for cc in range(1, w - 1)}
        return _grow_from(rng, cells, allowed, h + rng.randint(0, 3))
    c0 = rng.randint(1, h - 2)
    cells = [(c0, c) for c in range(w)]
    allowed = {(r, cc) for r in range(1, h - 1) for cc in range(w)}
    return _grow_from(rng, cells, allowed, w + rng.randint(0, 3))


def _place_decoy(g, rng, n_borders, taken):
    """A blob touching exactly n_borders edges, away from taken cells."""
    h, w = len(g), len(g[0])
    for _try in range(120):
        if n_borders == 0:
            seed = (rng.randint(2, h - 3), rng.randint(2, w - 3))
            allowed = {(r, c) for r in range(1, h - 1) for c in range(1, w - 1)}
        elif n_borders == 1:
            side = rng.randrange(4)
            if side == 0:
                seed = (0, rng.randint(2, w - 3))
                allowed = {(r, c) for r in range(0, h - 2)
                           for c in range(1, w - 1)}
            elif side == 1:
                seed = (h - 1, rng.randint(2, w - 3))
                allowed = {(r, c) for r in range(2, h)
                           for c in range(1, w - 1)}
            elif side == 2:
                seed = (rng.randint(2, h - 3), 0)
                allowed = {(r, c) for r in range(1, h - 1)
                           for c in range(0, w - 2)}
            else:
                seed = (rng.randint(2, h - 3), w - 1)
                allowed = {(r, c) for r in range(1, h - 1)
                           for c in range(2, w)}
        else:  # 3 borders: a U along top+left+bottom or top+right+bottom
            left = rng.random() < 0.5
            cc = 0 if left else w - 1
            cells = [(r, cc) for r in range(h)]
            cells += [(0, cc + (1 if left else -1)),
                      (h - 1, cc + (1 if left else -1))]
            blob = cells
            halo = {(r + dr, c + dc) for r, c in blob
                    for dr in (-1, 0, 1) for dc in (-1, 0, 1)}
            if any(p in taken for p in halo):
                continue
            color = rng.choice([1, 2, 3, 4, 5, 6, 7, 8, 9])
            for r, c in blob:
                g[r][c] = color
            return set(blob)
        if seed in taken:
            continue
        blob = _grow_from(rng, [seed], allowed, rng.randint(2, 5))
        halo = {(r + dr, c + dc) for r, c in blob
                for dr in (-1, 0, 1) for dc in (-1, 0, 1)}
        if any(p in taken for p in halo):
            continue
        if _borders(blob, h, w) != n_borders:
            continue
        color = rng.choice([1, 2, 3, 4, 5, 6, 7, 8, 9])
        for r, c in blob:
            g[r][c] = color
        return set(blob)
    return set()


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    texture = overrides.get("texture")
    if texture in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(texture, ctx)
    if texture is None:
        texture = ctx.draw_choice(
            "texture", ("plain", "plain", "one_border", "three_border",
                        "multicolor"))
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 9)
        w = ctx.draw_int("grid_w", 8, 10)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 10, 12)
        w = ctx.draw_int("grid_w", 12, 14)
    else:
        h = ctx.draw_int("grid_h", 7, 12)
        w = ctx.draw_int("grid_w", 8, 14)
    kind = overrides.get("target_kind") or \
        ctx.draw_choice("target_kind", ("corner", "corner", "span_v", "span_h"))
    rng = ctx.draw_rng("layout")

    for _attempt in range(80):
        g = full_grid(h, w, 0)
        target = _make_target(rng, h, w, kind)
        if _borders(target, h, w) != 2:
            continue
        colors = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], 2)
        for i, (r, c) in enumerate(target):
            if texture == "multicolor":
                g[r][c] = colors[i % 2]
            else:
                g[r][c] = colors[0]
        taken = {(r + dr, c + dc) for r, c in target
                 for dr in (-1, 0, 1) for dc in (-1, 0, 1)}

        # decoys: interior always; wrong-border-count per texture
        for _ in range(rng.randint(1, 2)):
            taken |= {(r + dr, c + dc) for r, c in
                      _place_decoy(g, rng, 0, taken)
                      for dr in (-1, 0, 1) for dc in (-1, 0, 1)}
        if texture == "one_border":
            taken |= {(r + dr, c + dc) for r, c in
                      _place_decoy(g, rng, 1, taken)
                      for dr in (-1, 0, 1) for dc in (-1, 0, 1)}
        elif texture == "three_border":
            taken |= {(r + dr, c + dc) for r, c in
                      _place_decoy(g, rng, 3, taken)
                      for dr in (-1, 0, 1) for dc in (-1, 0, 1)}

        # the intended target must be the unique 2-border component
        comps = _comps(g)
        hits = [c for c in comps if _borders(c, h, w) == 2]
        if len(hits) != 1 or hits[0] != sorted(target):
            continue
        return g
    raise ValueError("could not realize 2-border board")


def _draw_from_degenerate(name, ctx):
    """Rule-hiding inputs — rng-varied, always rule-safe.

    target_only         — just the 2-border blob: crop is the whole story.
    multiple_two_border — TWO 2-border blobs: the FIRST in scan order
                          (row-major by topmost-leftmost cell) wins.
    (A board with NO 2-border component crashes the rule and is never
    generated.)
    """
    rng = ctx.draw_rng("degenerate_layout")
    h = ctx.draw_int("grid_h", 8, 11)
    w = ctx.draw_int("grid_w", 9, 13)
    g = full_grid(h, w, 0)
    if name == "target_only":
        target = _make_target(rng, h, w, "corner")
        color = rng.randint(1, 9)
        for r, c in target:
            g[r][c] = color
        return g
    # multiple_two_border: top-left corner blob + bottom-right corner blob
    a = _grow_from(rng, [(0, 0)],
                   {(r, c) for r in range(0, h - 2) for c in range(0, w - 2)},
                   rng.randint(3, 5))
    b = _grow_from(rng, [(h - 1, w - 1)],
                   {(r, c) for r in range(2, h) for c in range(2, w)},
                   rng.randint(3, 5))
    ca, cb = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], 2)
    for r, c in a:
        g[r][c] = ca
    for r, c in b:
        g[r][c] = cb
    return g


def self_check(grid, *, difficulty=None, meta=None):
    """Verify: at least one color-blind 4-connected component touches
    exactly 2 grid borders (otherwise the rule crashes)."""
    msgs = []
    h, w = len(grid), len(grid[0])
    seen = [[False] * w for _ in range(h)]
    comps = []
    for r0 in range(h):
        for c0 in range(w):
            if grid[r0][c0] == 0 or seen[r0][c0]:
                continue
            stack = [(r0, c0)]
            seen[r0][c0] = True
            cells = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < h and 0 <= nc < w and not seen[nr][nc] and grid[nr][nc] != 0:
                        seen[nr][nc] = True
                        stack.append((nr, nc))
            comps.append(cells)
    def borders(cells):
        b = set()
        for r, c in cells:
            if r == 0: b.add('T')
            if r == h - 1: b.add('B')
            if c == 0: b.add('L')
            if c == w - 1: b.add('R')
        return len(b)
    two_border = [c for c in comps if borders(c) == 2]
    if not two_border:
        msgs.append(
            "no component touches exactly 2 borders "
            "(a board with none crashes the rule)"
        )
    return msgs
