"""Generator for arc_puzzle_bank_sixth_21_bundle:hard_39_local_object_gravity_in_frames.

Rule: color-5 EXACT rectangular frames (>=3x3) are gravity chambers.
Inside each, the multicolor 4-conn components fall as WHOLE units:
sorted deepest-bottom-edge first (ties: top row, then left col), each
drops until its floor or a previously-dropped component blocks it.
Content outside frames is untouched; a broken (non-rect) 5-outline is
NOT a frame and its contents stay frozen. (Old generator was
wrong-task: 'symmetry completion with key markers' - 11/24 outputs
were identity because scattered cells were already settled.)

Combinatorial axes: grid_h/w, frames, blobs, texture
(plain|stack|settled|multicolor_blob|outside_decoy|broken_frame).
Degenerates: empty_frame, no_frames (both identity).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "0af2b70671c6"
RULE_HASH = "01815bc8eeee"  # canonical rule this generator was written against
VERSION = "2.0.1"
TASK_ID = "0af2b70671c6"

SUMMARY = (
    "Components inside 5-frames fall as whole units (deepest-first, "
    "stacking on earlier-dropped ones). stack boards drop two blobs "
    "in shared columns (the upper lands ON the lower); settled boards "
    "mix an already-grounded blob with a floating one; "
    "multicolor_blob boards fall as ONE unit (components are "
    "color-blind); outside_decoy content never moves; broken_frame "
    "outlines (one gap) are NOT chambers - their contents stay "
    "frozen."
)

# Rivals: 'cells fall individually' refuted by blobs keeping shape.
# 'everything falls' refuted by outside_decoy + broken_frame. 'color
# = component' refuted by multicolor_blob falling as one. 3-4 demos
# incl. >=1 stacking.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    ">=1 floating component per board (output != input)",
    "frames are exact 5-rectangles >=3x3; interiors hold the blobs",
    "broken_frame boards also carry one REAL frame with content",
]

DEGENERATE_TEXTURES = ("empty_frame", "no_frames")
HELPFUL_TEXTURES = ("plain", "stack", "settled", "multicolor_blob",
                    "outside_decoy", "broken_frame")

AXES = {
    "grid_h":  {"type": "int", "default": "rng 12..16", "valid": "10..20"},
    "grid_w":  {"type": "int", "default": "rng 14..20", "valid": "12..26"},
    "texture": {"type": "str", "default": "rng helpful",
                "valid": "plain|stack|settled|multicolor_blob|"
                         "outside_decoy|broken_frame|empty_frame|"
                         "no_frames",
                "doc": "stack: blobs share columns and pile up; "
                       "settled: grounded blob stays put; "
                       "broken_frame: gapped outline is not a "
                       "chamber."},
}

_COLORS = (1, 2, 3, 4, 6, 7, 8, 9)


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


def _components(sub):
    sh, sw = len(sub), len(sub[0])
    seen = set()
    comps = []
    for r in range(sh):
        for c in range(sw):
            if sub[r][c] == 0 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < sh and 0 <= nc < sw \
                            and (nr, nc) not in seen and sub[nr][nc] != 0:
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            comps.append(cells)
    return comps


def _mirror(g):
    h, w = len(g), len(g[0])
    seen = set()
    frames = []
    for r in range(h):
        for c in range(w):
            if g[r][c] != 5 or (r, c) in seen:
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
                            and (nr, nc) not in seen and g[nr][nc] == 5:
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            r1 = min(rr for rr, _ in cells)
            r2 = max(rr for rr, _ in cells)
            c1 = min(cc for _, cc in cells)
            c2 = max(cc for _, cc in cells)
            fh, fw = r2 - r1 + 1, c2 - c1 + 1
            border = {(rr, cc) for rr in range(r1, r2 + 1)
                      for cc in range(c1, c2 + 1)
                      if rr in (r1, r2) or cc in (c1, c2)}
            if fh >= 3 and fw >= 3 and set(cells) == border:
                frames.append((r1, c1, r2, c2))
    frames.sort()
    out = [row[:] for row in g]
    for fr1, fc1, fr2, fc2 in frames:
        ir1, ic1, ir2, ic2 = fr1 + 1, fc1 + 1, fr2 - 1, fc2 - 1
        sub = [row[ic1:ic2 + 1] for row in g[ir1:ir2 + 1]]
        sh = len(sub)
        comps = _components(sub)
        comps.sort(key=lambda cs: (-max(r for r, _ in cs),
                                   min(r for r, _ in cs),
                                   min(c for _, c in cs)))
        dropped = [[0] * len(sub[0]) for _ in range(sh)]
        for cs in comps:
            s = 0
            while all(r + s + 1 < sh and dropped[r + s + 1][c] == 0
                      for r, c in cs):
                s += 1
            for r, c in cs:
                dropped[r + s][c] = sub[r][c]
        for r in range(ir1, ir2 + 1):
            for c in range(ic1, ic2 + 1):
                out[r][c] = dropped[r - ir1][c - ic1]
    return out


def _place_frame(g, rng, fh, fw, broken=False):
    h, w = len(g), len(g[0])
    for _t in range(150):
        r0 = rng.randint(0, h - fh)
        c0 = rng.randint(0, w - fw)
        if not all(g[r][c] == 0
                   for r in range(max(0, r0 - 1), min(h, r0 + fh + 1))
                   for c in range(max(0, c0 - 1), min(w, c0 + fw + 1))):
            continue
        for c in range(c0, c0 + fw):
            g[r0][c] = 5
            g[r0 + fh - 1][c] = 5
        for r in range(r0, r0 + fh):
            g[r][c0] = 5
            g[r][c0 + fw - 1] = 5
        if broken:
            side = rng.choice(["t", "b", "l", "r"])
            if side == "t":
                g[r0][rng.randint(c0 + 1, c0 + fw - 2)] = 0
            elif side == "b":
                g[r0 + fh - 1][rng.randint(c0 + 1, c0 + fw - 2)] = 0
            elif side == "l":
                g[rng.randint(r0 + 1, r0 + fh - 2)][c0] = 0
            else:
                g[rng.randint(r0 + 1, r0 + fh - 2)][c0 + fw - 1] = 0
        return r0, c0
    return None


def _fill_interior(g, rng, r0, c0, fh, fw, texture):
    """Place floating blobs in the frame interior."""
    ir1, ic1 = r0 + 1, c0 + 1
    ih, iw = fh - 2, fw - 2
    blobs = []
    n = 2 if texture in ("stack", "settled") else rng.randint(1, 2)
    for i in range(n):
        colors = rng.sample(_COLORS, 2) if texture == "multicolor_blob" \
            else [rng.choice(_COLORS)]
        shape = _grow(rng, rng.randint(2, 4), max(1, ih - 2),
                      max(1, iw - 1))
        sh = max(r for r, _ in shape) + 1
        sw = max(c for _, c in shape) + 1
        for _t in range(120):
            if texture == "settled" and i == 0:
                br = ih - sh  # grounded
            else:
                if ih - sh - 1 < 0:
                    continue
                br = rng.randint(0, max(0, ih - sh - 1))  # floating
            if texture == "stack" and blobs:
                pc = blobs[0]
                lo = min(max(0, pc - 1), iw - sw)
                hi = max(lo, min(iw - sw, pc + 1))
                bc = rng.randint(lo, hi)
            else:
                bc = rng.randint(0, iw - sw)
            cells = [(ir1 + br + r, ic1 + bc + c) for r, c in shape]
            if all(g[rr][cc] == 0 and
                   all(g[ar][ac] == 0 or g[ar][ac] == 5
                       for ar, ac in ((rr - 1, cc), (rr + 1, cc),
                                      (rr, cc - 1), (rr, cc + 1)))
                   for rr, cc in cells):
                for rr, cc in cells:
                    g[rr][cc] = rng.choice(colors)
                blobs.append(bc)
                break
    return bool(blobs)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    texture = overrides.get("texture")
    if texture in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(texture, ctx)
    if texture is None:
        texture = ctx.draw_choice("texture", ("plain", "plain", "stack",
                                              "settled", "multicolor_blob",
                                              "outside_decoy",
                                              "broken_frame"))
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 12, 14)
        w = ctx.draw_int("grid_w", 14, 16)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 15, 16)
        w = ctx.draw_int("grid_w", 18, 20)
    else:
        h = ctx.draw_int("grid_h", 12, 16)
        w = ctx.draw_int("grid_w", 14, 20)
    rng = ctx.draw_rng("layout")

    for _attempt in range(120):
        g = full_grid(h, w, 0)
        fh = rng.randint(6, min(9, h - 1))
        fw = rng.randint(6, min(9, w - 8))
        pos = _place_frame(g, rng, fh, fw)
        if pos is None:
            continue
        if not _fill_interior(g, rng, pos[0], pos[1], fh, fw, texture):
            continue
        if texture == "broken_frame":
            fh2 = rng.randint(5, min(7, h - 1))
            fw2 = rng.randint(5, min(7, w - 1))
            pos2 = _place_frame(g, rng, fh2, fw2, broken=True)
            if pos2 is None:
                continue
            # floating content inside the broken outline (stays frozen)
            _fill_interior(g, rng, pos2[0], pos2[1], fh2, fw2, "plain")
        elif rng.random() < 0.5:
            fh2 = rng.randint(5, min(8, h - 1))
            fw2 = rng.randint(5, min(8, w - 1))
            pos2 = _place_frame(g, rng, fh2, fw2)
            if pos2 is not None:
                _fill_interior(g, rng, pos2[0], pos2[1], fh2, fw2,
                               "plain")
        if texture == "outside_decoy":
            for _d in range(rng.randint(2, 4)):
                for _t in range(60):
                    r = rng.randint(0, h - 1)
                    c = rng.randint(0, w - 1)
                    if g[r][c] == 0 and \
                       all(g[ar][ac] == 0
                           for ar, ac in ((r-1, c), (r+1, c),
                                          (r, c-1), (r, c+1))
                           if 0 <= ar < h and 0 <= ac < w):
                        g[r][c] = rng.choice(_COLORS)
                        break
        out = _mirror(g)
        if out == g:
            continue
        return g
    raise ValueError("could not realize gravity-frame board")


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """>=1 color-5 rectangular frame (>=3x3 border) with >=1 non-{0,5} cell inside."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    seen: set = set()
    has_valid_frame = False
    for r0 in range(h):
        for c0 in range(w):
            if grid[r0][c0] != 5 or (r0, c0) in seen:
                continue
            # BFS to find this color-5 component
            stack = [(r0, c0)]; seen.add((r0, c0)); cells = []
            while stack:
                r, c = stack.pop(); cells.append((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and grid[nr][nc] == 5:
                        seen.add((nr, nc)); stack.append((nr, nc))
            r1 = min(r for r, _ in cells); r2 = max(r for r, _ in cells)
            c1 = min(c for _, c in cells); c2 = max(c for _, c in cells)
            fh, fw = r2 - r1 + 1, c2 - c1 + 1
            if fh < 3 or fw < 3:
                continue
            # must be exactly the border cells
            border = {(r, c) for r in range(r1, r2 + 1)
                      for c in range(c1, c2 + 1)
                      if r in (r1, r2) or c in (c1, c2)}
            if set(cells) != border:
                continue
            # at least one non-{0,5} inside
            interior = any(grid[r][c] not in (0, 5)
                           for r in range(r1 + 1, r2) for c in range(c1 + 1, c2))
            if interior:
                has_valid_frame = True
                break
        if has_valid_frame:
            break
    errors = []
    if not has_valid_frame:
        errors.append("no color-5 rectangular frame (>=3x3) with a non-bg blob inside")
    return errors


def _draw_from_degenerate(name, ctx):
    """empty_frame — frames with empty interiors: identity. no_frames
    — loose blobs, no chambers: identity. rng-varied."""
    rng = ctx.draw_rng("degenerate_layout")
    h = ctx.draw_int("grid_h", 12, 15)
    w = ctx.draw_int("grid_w", 14, 18)
    g = full_grid(h, w, 0)
    if name == "no_frames":
        for _ in range(rng.randint(2, 3)):
            shape = _grow(rng, rng.randint(2, 4), 3, 3)
            sh = max(r for r, _ in shape) + 1
            sw = max(c for _, c in shape) + 1
            r0 = rng.randint(0, h - sh)
            c0 = rng.randint(0, w - sw)
            if all(g[r0 + r][c0 + c] == 0 for r, c in shape):
                color = rng.choice(_COLORS)
                for r, c in shape:
                    g[r0 + r][c0 + c] = color
        return g
    _place_frame(g, rng, rng.randint(5, 8), rng.randint(5, 8))
    _place_frame(g, rng, rng.randint(5, 7), rng.randint(5, 7))
    return g
