"""gen2: recolor one distractor color, then extract-largest.

Transform: `(extract-largest (recolor g SRC DST))` — first recolor every
SRC cell to DST (a global color swap on the scattered distractors), then
crop to the bounding box of the largest 4-connected object (extraction).

The input is a large field of many small distractor components plus ONE
strictly-largest solid rectangle (a unique color, untouched by the
recolor, so it stays the unique argmax). Output = that rectangle's bbox
patch, recolored. SRC/DST are chosen so the swap never creates a
component larger than the rectangle and never touches the rectangle's
color, keeping the Racket `argmax obj-size` deterministic.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.generic.concepts.extraction import parity_check

VERSION = "1.1.0"
TASK_ID = "generic_extraction_gen2"


def _dims_for(difficulty):
    if difficulty == "easy":
        return (12, 16)
    if difficulty == "hard":
        return (22, 30)
    return (16, 24)                  # medium


def _recolor(g, src, dst):
    return [[dst if v == src else v for v in row] for row in g]


def _components(g, bg=0):
    """4-connected components, row-major discovery order (matches prelude
    find-objects). Returns list of (size, cells, bbox)."""
    h, w = len(g), len(g[0])
    seen = [[False] * w for _ in range(h)]
    comps = []
    for r in range(h):
        for c in range(w):
            if g[r][c] == bg or seen[r][c]:
                continue
            color = g[r][c]
            stack = [(r, c)]
            seen[r][c] = True
            cells = []
            while stack:
                cr, cc = stack.pop()
                cells.append((cr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = cr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w and not seen[nr][nc]
                            and g[nr][nc] == color):
                        seen[nr][nc] = True
                        stack.append((nr, nc))
            rs = [p[0] for p in cells]
            cs = [p[1] for p in cells]
            comps.append((len(cells), cells,
                          (min(rs), min(cs), max(rs), max(cs))))
    return comps


def _extract_largest(g, bg=0):
    comps = _components(g, bg)
    if not comps:
        return [row[:] for row in g]
    # argmax obj-size: FIRST (earliest row-major) component with max size.
    best = comps[0]
    for comp in comps[1:]:
        if comp[0] > best[0]:        # strict > keeps the FIRST on ties
            best = comp
    r1, c1, r2, c2 = best[2]
    return [[g[r][c] for c in range(c1, c2 + 1)] for r in range(r1, r2 + 1)]


def _apply(g, src, dst):
    return _extract_largest(_recolor(g, src, dst))


def _build_input(ctx, idx, rect_color, src, dst, others, gh, gw):
    """Many small distractor specks + one unique solid rectangle whose
    area strictly dominates. SRC scatter is kept to single cells / 1-wide
    so post-recolor it can never out-grow the rectangle."""
    rng = ctx.draw_rng(f"input_{idx}")
    g = [[0] * gw for _ in range(gh)]

    # Solid rectangle: area must dominate. Make it at least 4x4 and big.
    rh = rng.randint(4, max(4, gh // 2))
    rw = rng.randint(4, max(4, gw // 2))
    rr = rng.randint(0, gh - rh)
    rc = rng.randint(0, gw - rw)
    rect_area = rh * rw
    for r in range(rr, rr + rh):
        for c in range(rc, rc + rw):
            g[r][c] = rect_color

    # Punch isolated SRC dots into the rectangle INTERIOR (never the border,
    # never adjacent to each other) so the recolor SRC->DST is VISIBLE in the
    # extracted output. Interior single-cell holes on a 2-lattice can't
    # disconnect a solid rectangle nor merge into a component, so the
    # rect_color region stays one connected blob and strictly largest.
    for r in range(rr + 1, rr + rh - 1, 2):
        for c in range(rc + 1, rc + rw - 1, 2):
            if rng.random() < 0.4:
                g[r][c] = src
    # Force at least one visible recolor inside the extracted rectangle. Without
    # this, many seeds contain no SRC cells in the rectangle and the output is a
    # solid single-color patch despite the advertised recolor+extract chain.
    g[rr + 1][rc + 1] = src

    # Distractor specks: isolated single cells of `others`, src, dst — each
    # surrounded by bg so no component exceeds size 1. Place sparsely on the
    # 2-spaced lattice and never adjacent to the rectangle's color region.
    speck_cells = []
    for r in range(0, gh, 2):
        for c in range(0, gw, 2):
            if rr - 1 <= r <= rr + rh and rc - 1 <= c <= rc + rw:
                continue              # keep clear margin around rectangle
            if rng.random() < 0.45:
                speck_cells.append((r, c))
    palette = list(others) + [src, dst]
    for (r, c) in speck_cells:
        g[r][c] = rng.choice(palette)

    # Safety: rectangle color must be unique to the rectangle (no specks of it).
    # palette excludes rect_color by construction. Rect strictly largest:
    # every speck is size 1 << rect_area. After recolor SRC->DST, adjacent
    # src/dst specks could merge — but specks sit on a 2-lattice (never
    # 4-adjacent), so merging is impossible. Assert the invariant cheaply.
    assert rect_area >= 16
    return g


def generate_task(seed, *, difficulty="medium"):
    ctx = gen_ctx(seed=seed, sample_index=0, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty)
    glo, ghi = _dims_for(difficulty)

    # rect_color, src, dst, plus 3 other distractor colors — all distinct.
    cols = list(ctx.draw_distinct_colors("colors", n=6, exclude=[0]))
    rect_color, src, dst, o1, o2, o3 = cols
    others = [o1, o2, o3]
    n_train = ctx.draw_int("n_train", 3, 4)
    n_test = ctx.draw_int("n_test", 1, 2)

    program = (f"(rule! (lambda (g) "
               f"(extract-largest (recolor g {src} {dst}))))")

    pairs = []
    for idx in range(n_train + n_test):
        gh = ctx.draw_int(f"gh_{idx}", glo, ghi)
        gw = ctx.draw_int(f"gw_{idx}", glo, ghi)
        gin = _build_input(ctx, idx, rect_color, src, dst, others, gh, gw)
        gout = _apply(gin, src, dst)
        pairs.append({"input": gin, "output": gout})

    return {
        "train": pairs[:n_train],
        "test": pairs[n_train:],
        "program": program,
        "chain": ["recolor", "extract_largest"],
        "meta": {"difficulty": difficulty, "rect_color": rect_color,
                 "src": src, "dst": dst, "others": others, "version": VERSION},
    }


if __name__ == "__main__":
    parity_check(generate_task, n=25, version_label=VERSION)
