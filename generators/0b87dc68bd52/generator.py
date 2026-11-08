"""Generator for arc_puzzle_bank_21_more:hard_b02 — center shapes
into same-colored frames.

Rule: exact rectangular frame objects (perimeter-only, >=3x3) are
kept; for EACH frame, the first non-frame object of the SAME COLOR is
center-pasted into the frame interior (floor-half centering). All
loose shapes are erased (output = frames + inserted copies). A frame
with NO same-colored loose shape CRASHES ((first '())) — never
generated. (Old generator was wrong-task: 'vertical gallery pack' of
random motifs - 9th template copy found; unique_out was 8.)

Combinatorial axes: grid_h/w, frame sizes, shapes, texture
(plain|two_pairs|odd_center|extra_shape).
Degenerates: no_frames (everything erased -> blank-ish output).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "0b87dc68bd52"
VERSION = "3.0.1"
TASK_ID = "0b87dc68bd52"

SUMMARY = (
    "Each color-matched loose shape teleports to the CENTER of its "
    "frame (floor-half offsets); loose shapes are erased from their "
    "original spots. two_pairs boards run two frame+shape colors; "
    "odd_center boards use even-size interiors with odd-size shapes "
    "(floor-half biases up-left); extra_shape boards add a second "
    "same-colored loose shape (only the FIRST in scan order is "
    "used, but both are erased)."
)

# Rivals: 'shapes stay where they are' refuted by every demo (loose
# shapes erased). 'paste at top-left' refuted by centered placement.
# 'all same-color shapes insert' refuted by extra_shape (first only,
# both erased). 3-4 demos.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "every frame has >=1 same-colored loose shape (missing crashes)",
    "shapes fit strictly inside their frame interiors",
    "frames are exact perimeter rectangles >=3x3",
]

DEGENERATE_TEXTURES = ("no_frames",)
HELPFUL_TEXTURES = ("plain", "two_pairs", "odd_center", "extra_shape")

AXES = {
    "grid_h":  {"type": "int", "default": "rng 11..15", "valid": "10..18"},
    "grid_w":  {"type": "int", "default": "rng 12..17", "valid": "11..20"},
    "texture": {"type": "str", "default": "rng helpful",
                "valid": "plain|two_pairs|odd_center|extra_shape|"
                         "no_frames",
                "doc": "two_pairs: two frame+shape colors; odd_center: "
                       "floor-half centering bias visible; extra_shape: "
                       "spare same-color shape erased unused."},
}

_COLORS = (1, 2, 3, 4, 5, 6, 7, 8, 9)


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """>=1 perimeter-frame >=3x3 exists (rule crashes on missing same-color shape)."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    # find 4-connected components, check if any is a perimeter rect >=3x3
    seen = set()
    found_frame = False
    for sr in range(h):
        for sc in range(w):
            v = grid[sr][sc]
            if v == 0 or (sr, sc) in seen:
                continue
            stack = [(sr, sc)]
            seen.add((sr, sc))
            comp = []
            while stack:
                r, c = stack.pop()
                comp.append((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < h and 0 <= nc < w and grid[nr][nc] == v and (nr, nc) not in seen:
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            rs = [r for r, _ in comp]; cs = [c for _, c in comp]
            r1, r2, c1, c2 = min(rs), max(rs), min(cs), max(cs)
            fh, fw = r2 - r1 + 1, c2 - c1 + 1
            perimeter = fh * fw - max(0, fh - 2) * max(0, fw - 2)
            if fh >= 3 and fw >= 3 and len(comp) == perimeter and \
                    all(r in (r1, r2) or c in (c1, c2) for r, c in comp):
                found_frame = True
                break
        if found_frame:
            break
    if not found_frame:
        return ["no perimeter-only frame >=3x3 found"]
    return []


def _grow(rng, k, max_h, max_w):
    cells = [(0, 0)]
    seen = {(0, 0)}
    for _ in range(300):
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


def _floor_half(x):
    return x // 2 if x >= 0 else -((-x + 1) // 2)


def _mirror(g):
    h, w = len(g), len(g[0])
    seen = set()
    comps = []
    for r in range(h):
        for c in range(w):
            v = g[r][c]
            if v == 0 or (r, c) in seen:
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
                            and (nr, nc) not in seen and g[nr][nc] == v:
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            comps.append((v, cells))
    frames, shapes = [], []
    for v, cells in comps:
        r1 = min(r for r, _ in cells)
        r2 = max(r for r, _ in cells)
        c1 = min(c for _, c in cells)
        c2 = max(c for _, c in cells)
        fh, fw = r2 - r1 + 1, c2 - c1 + 1
        border = fh * fw - max(0, fh - 2) * max(0, fw - 2)
        is_frame = fh >= 3 and fw >= 3 and len(cells) == border and \
            all(r in (r1, r2) or c in (c1, c2) for r, c in cells)
        (frames if is_frame else shapes).append((v, cells, r1, c1, r2, c2))
    out = [[0] * w for _ in range(h)]
    for v, cells, *_ in frames:
        for r, c in cells:
            out[r][c] = v
    for v, cells, fr1, fc1, fr2, fc2 in frames:
        cand = next((s for s in shapes if s[0] == v), None)
        if cand is None:
            return None  # rule would crash
        _, scells, sr1, sc1, sr2, sc2 = cand
        crop = [row[sc1:sc2 + 1] for row in g[sr1:sr2 + 1]]
        ch, cw = len(crop), len(crop[0])
        top = fr1 + 1 + _floor_half((fr2 - fr1 - 1) - ch)
        left = fc1 + 1 + _floor_half((fc2 - fc1 - 1) - cw)
        for r in range(ch):
            for c in range(cw):
                if crop[r][c] != 0:
                    out[top + r][left + c] = crop[r][c]
    return out


def _place_frame(g, rng, ih, iw, color):
    h, w = len(g), len(g[0])
    fh, fw = ih + 2, iw + 2
    for _t in range(150):
        r0 = rng.randint(0, h - fh)
        c0 = rng.randint(0, w - fw)
        if not all(g[r][c] == 0
                   for r in range(max(0, r0 - 1), min(h, r0 + fh + 1))
                   for c in range(max(0, c0 - 1), min(w, c0 + fw + 1))):
            continue
        for c in range(c0, c0 + fw):
            g[r0][c] = color
            g[r0 + fh - 1][c] = color
        for r in range(r0, r0 + fh):
            g[r][c0] = color
            g[r][c0 + fw - 1] = color
        return True
    return False


def _place_shape(g, rng, shape, color):
    h, w = len(g), len(g[0])
    sh = max(r for r, _ in shape) + 1
    sw = max(c for _, c in shape) + 1
    for _t in range(150):
        r0 = rng.randint(0, h - sh)
        c0 = rng.randint(0, w - sw)
        cells = [(r0 + r, c0 + c) for r, c in shape]
        if all(g[r][c] == 0 and
               all(g[ar][ac] == 0
                   for ar, ac in ((r-1, c), (r+1, c), (r, c-1), (r, c+1))
                   if 0 <= ar < h and 0 <= ac < w)
               for r, c in cells):
            for r, c in cells:
                g[r][c] = color
            return True
    return False


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    texture = overrides.get("texture")
    if texture in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(texture, ctx)
    if texture is None:
        texture = ctx.draw_choice("texture", ("plain", "plain", "two_pairs",
                                              "odd_center", "extra_shape"))
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 11, 13)
        w = ctx.draw_int("grid_w", 12, 14)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 14, 15)
        w = ctx.draw_int("grid_w", 15, 17)
    else:
        h = ctx.draw_int("grid_h", 11, 15)
        w = ctx.draw_int("grid_w", 12, 17)
    rng = ctx.draw_rng("layout")

    for _attempt in range(150):
        g = full_grid(h, w, 0)
        n_pairs = 2 if texture == "two_pairs" else 1
        colors = rng.sample(_COLORS, n_pairs)
        ok = True
        for color in colors:
            if texture == "odd_center":
                ih, iw = rng.choice([4, 6]), rng.choice([4, 6])
                shape = _grow(rng, rng.randint(3, 5),
                              ih - 1 if ih % 2 == 0 else ih,
                              iw - 1 if iw % 2 == 0 else iw)
                # odd-size shape in even interior -> floor-half bias
                sh = max(r for r, _ in shape) + 1
                sw = max(c for _, c in shape) + 1
                if sh % 2 == 0 and sw % 2 == 0:
                    ok = False
                    break
            else:
                ih, iw = rng.randint(3, 5), rng.randint(3, 5)
                shape = _grow(rng, rng.randint(3, 5), ih - 1, iw - 1)
            sh = max(r for r, _ in shape) + 1
            sw = max(c for _, c in shape) + 1
            if sh > ih or sw > iw:
                ok = False
                break
            if not _place_frame(g, rng, ih, iw, color):
                ok = False
                break
            if not _place_shape(g, rng, shape, color):
                ok = False
                break
            if texture == "extra_shape":
                _place_shape(g, rng, _grow(rng, rng.randint(2, 3), 2, 2),
                             color)
        if not ok:
            continue
        out = _mirror(g)
        if out is None or out == g:
            continue
        return g
    raise ValueError("could not realize frame-centering board")


def _draw_from_degenerate(name, ctx):
    """no_frames — loose shapes only: every loose shape is erased,
    output is blank. rng-varied."""
    rng = ctx.draw_rng("degenerate_layout")
    h = ctx.draw_int("grid_h", 11, 14)
    w = ctx.draw_int("grid_w", 12, 15)
    g = full_grid(h, w, 0)
    for color in rng.sample(_COLORS, rng.randint(2, 3)):
        _place_shape(g, rng, _grow(rng, rng.randint(3, 5), 3, 3), color)
    return g
