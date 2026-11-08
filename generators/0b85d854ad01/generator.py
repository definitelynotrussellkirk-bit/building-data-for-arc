"""Generator for arc_puzzle_bank_twelfth21:M82 — crop the largest
key-color blob.

Rule: key = g[0][0]. Among key-colored objects EXCLUDING any
containing (0,0): the LARGEST is raw-bbox-cropped (ties -> first in
scan order; foreign cells inside the bbox appear in the crop). No
candidates -> 1x1 [[key]] (also [[0]] when the corner is 0).

Combinatorial axes: grid_h/w, blob sizes, texture
(plain|size_contest|tie|intrusion|corner_attached).
Degenerates: no_key, no_key_blob, key_only_at_corner (all valid 1x1).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "0b85d854ad01"
VERSION = "3.1.1"  # add executable key-crop invariants
TASK_ID = "0b85d854ad01"
SUMMARY = (
    "Corner key picks the color; the LARGEST non-corner blob of that "
    "color is cropped. size_contest boards carry TWO key blobs "
    "(bigger wins, was never contested); tie boards have equal sizes "
    "(first in scan order wins); intrusion boards put a foreign cell "
    "INSIDE the winner's bbox (raw crop shows it); corner_attached "
    "boards extend a BIG key object from (0,0) (excluded entirely - "
    "a smaller detached blob wins)."
)

# Rivals: 'first blob wins' refuted by size_contest. 'corner object
# counts' refuted by corner_attached. 'crop is the blob mask' refuted
# by intrusion. 'last/biggest tie wins' refuted by tie. 3-4 demos.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "key blobs separated >=2 from the corner and each other",
    "size_contest: strictly different sizes; tie: equal sizes",
    "intrusion: a foreign cell strictly inside the winner's bbox",
]

DEGENERATE_TEXTURES = ("no_key", "no_key_blob", "key_only_at_corner")
HELPFUL_TEXTURES = ("plain", "size_contest", "tie", "intrusion",
                    "corner_attached")

AXES = {
    "grid_h":  {"type": "int", "default": "rng 7..12", "valid": "6..16"},
    "grid_w":  {"type": "int", "default": "rng 8..13", "valid": "7..16"},
    "texture": {"type": "str", "default": "rng helpful",
                "valid": "plain|size_contest|tie|intrusion|"
                         "corner_attached|no_key|no_key_blob|"
                         "key_only_at_corner",
                "doc": "size_contest: two key blobs, bigger wins; tie: "
                       "equal sizes, scan-order first; intrusion: "
                       "foreign cell in the crop; corner_attached: "
                       "big corner-touching key object excluded."},
}

_COLORS = (1, 2, 3, 4, 5, 6, 7, 8, 9)


def _grow(rng, k, max_h=4, max_w=4):
    cells = [(0, 0)]
    seen = {(0, 0)}
    for _ in range(400):
        if len(cells) >= k:
            break
        r, c = cells[rng.randrange(len(cells))]
        dr, dc = ((-1, 0), (1, 0), (0, -1), (0, 1))[rng.randrange(4)]
        p = (r + dr, c + dc)
        if p in seen:
            continue
        rs = [q[0] for q in seen] + [p[0]]
        cs = [q[1] for q in seen] + [p[1]]
        if max(rs) - min(rs) + 1 > max_h or max(cs) - min(cs) + 1 > max_w:
            continue
        cells.append(p)
        seen.add(p)
    mr = min(r for r, _ in cells)
    mc = min(c for _, c in cells)
    return sorted((r - mr, c - mc) for r, c in cells)


def _mirror(g):
    h, w = len(g), len(g[0])
    key = g[0][0]
    seen = set()
    objs = []
    for r in range(h):
        for c in range(w):
            if g[r][c] != key or key == 0 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w \
                            and (nr, nc) not in seen and g[nr][nc] == key:
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            if (0, 0) not in cells:
                objs.append(cells)
    if not objs:
        return [[key]]
    objs.sort(key=len, reverse=True)  # stable: scan order kept on ties
    cells = objs[0]
    r1 = min(r for r, _ in cells)
    r2 = max(r for r, _ in cells)
    c1 = min(c for _, c in cells)
    c2 = max(c for _, c in cells)
    return [row[c1:c2 + 1] for row in g[r1:r2 + 1]]


def _place(g, rng, shape, color, min_gap=2):
    h, w = len(g), len(g[0])
    sh = max(r for r, _ in shape) + 1
    sw = max(c for _, c in shape) + 1
    for _t in range(150):
        r0 = rng.randint(0, h - sh)
        c0 = rng.randint(0, w - sw)
        cells = [(r0 + r, c0 + c) for r, c in shape]
        if any(abs(r) < min_gap and abs(c) < min_gap for r, c in cells):
            continue  # keep clear of (0,0)
        if all(g[r][c] == 0 and
               all(g[ar][ac] == 0
                   for ar, ac in ((r-1, c), (r+1, c), (r, c-1), (r, c+1))
                   if 0 <= ar < h and 0 <= ac < w)
               for r, c in cells):
            for r, c in cells:
                g[r][c] = color
            return cells
    return None


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    texture = overrides.get("texture")
    if texture in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(texture, ctx)
    if texture is None:
        texture = ctx.draw_choice("texture", ("plain", "plain",
                                              "size_contest", "tie",
                                              "intrusion",
                                              "corner_attached"))
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 9)
        w = ctx.draw_int("grid_w", 8, 10)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 10, 12)
        w = ctx.draw_int("grid_w", 11, 13)
    else:
        h = ctx.draw_int("grid_h", 7, 12)
        w = ctx.draw_int("grid_w", 8, 13)
    rng = ctx.draw_rng("layout")

    for _attempt in range(150):
        g = full_grid(h, w, 0)
        key, dec = rng.sample(list(_COLORS), 2)
        g[0][0] = key
        if texture == "corner_attached":
            # big key object growing FROM the corner (excluded)
            arm = rng.randint(4, 6)
            for i in range(arm):
                if rng.random() < 0.5 and i < h:
                    g[i][0] = key
                elif i < w:
                    g[0][i] = key
        win = _place(g, rng, _grow(rng, rng.randint(4, 7), 5, 5), key)
        if win is None:
            continue
        if texture == "size_contest":
            small = _place(g, rng, _grow(rng, rng.randint(2, 3)), key)
            if small is None:
                continue
        elif texture == "tie":
            other = _place(g, rng, _grow(rng, len(win)), key)
            if other is None or len(other) != len(win):
                continue
        if texture == "intrusion":
            r1 = min(r for r, _ in win)
            r2 = max(r for r, _ in win)
            c1 = min(c for _, c in win)
            c2 = max(c for _, c in win)
            holes = [(r, c) for r in range(r1, r2 + 1)
                     for c in range(c1, c2 + 1) if g[r][c] == 0]
            if not holes:
                continue
            rr, cc = rng.choice(holes)
            g[rr][cc] = dec
        else:
            _place(g, rng, _grow(rng, rng.randint(1, 3)), dec)
        out = _mirror(g)
        if out == [[key]]:
            continue
        return g
    raise ValueError("could not realize key-crop board")


def _draw_from_degenerate(name, ctx):
    """All three yield a valid 1x1 output: no_key -> [[0]] (corner is
    0, no key objects); no_key_blob / key_only_at_corner -> [[key]]
    (no non-corner candidates). rng-varied."""
    rng = ctx.draw_rng("degenerate_layout")
    h = ctx.draw_int("grid_h", 7, 10)
    w = ctx.draw_int("grid_w", 8, 11)
    g = full_grid(h, w, 0)
    if name == "no_key":
        _place(g, rng, _grow(rng, 3), rng.choice(_COLORS))
        return g
    key = rng.choice(_COLORS)
    g[0][0] = key
    if name == "no_key_blob":
        _place(g, rng, _grow(rng, 3),
               rng.choice([c for c in _COLORS if c != key]))
    return g

def _key_components(grid, key):
    h, w = len(grid), len(grid[0])
    seen = set()
    comps = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != key or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w and grid[nr][nc] == key
                            and (nr, nc) not in seen):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            comps.append(cells)
    return comps


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errors: list[str] = []
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    if any(v not in range(10) for row in grid for v in row):
        errors.append("grid values must be digits 0..9")
    key = grid[0][0]
    if key == 0:
        errors.append("normal sample must expose a nonzero corner key")
        return errors
    targets = [cells for cells in _key_components(grid, key) if (0, 0) not in cells]
    if not targets:
        errors.append("normal sample must contain at least one non-corner key-color candidate blob")
        return errors
    out = _mirror(grid)
    if out == [[key]]:
        errors.append("normal sample must not collapse to the no-candidate 1x1 fallback")
    winner = max(targets, key=len)
    r0, r1 = min(r for r, _ in winner), max(r for r, _ in winner)
    c0, c1 = min(c for _, c in winner), max(c for _, c in winner)
    if len(out) != r1 - r0 + 1 or len(out[0]) != c1 - c0 + 1:
        errors.append("mirror crop dimensions must equal the largest target blob bbox")
    if len(winner) < 2:
        errors.append("winner blob must be a multi-cell object")
    return errors
