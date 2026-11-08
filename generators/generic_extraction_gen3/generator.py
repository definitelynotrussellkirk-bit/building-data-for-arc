"""gen3: remove a pervasive noise color, recolor-map two colors, crop-to-content.

Transform:
  `(crop-to-content (recolor-map (remove-color g NOISE) (hash A B C D)))`
A large grid is flooded with a pervasive NOISE color (scattered far beyond
the meaningful shape's bounding box). remove-color erases NOISE to bg, a
recolor-map swaps the shape's two structural colors (A->B, C->D), and
crop-to-content extracts the tight bounding box of the surviving shape.
Output is the small, recolored shape pulled out of the noisy field.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.generic.concepts.extraction import parity_check

VERSION = "1.0.0"
TASK_ID = "generic_extraction_gen3"


def _dims_for(difficulty):
    if difficulty == "easy":
        return (12, 16), (3, 6)
    if difficulty == "hard":
        return (22, 30), (5, 9)
    return (16, 24), (4, 7)          # medium


def _remove_color(g, noise):
    return [[0 if v == noise else v for v in row] for row in g]


def _recolor_map(g, mapping):
    return [[mapping.get(v, v) for v in row] for row in g]


def _crop_to_content(g):
    h, w = len(g), len(g[0])
    rs = [r for r in range(h) if any(g[r][c] != 0 for c in range(w))]
    cs = [c for c in range(w) if any(g[r][c] != 0 for r in range(h))]
    if not rs or not cs:
        return [[]]
    r1, r2, c1, c2 = rs[0], rs[-1], cs[0], cs[-1]
    return [[g[r][c] for c in range(c1, c2 + 1)] for r in range(r1, r2 + 1)]


def _apply(g, noise, mapping):
    return _crop_to_content(_recolor_map(_remove_color(g, noise), mapping))


def _build_input(ctx, idx, noise, ca, cb, gh, gw, slo, shi):
    """A compact 2-color shape (colors ca, cb) inside a window, embedded in
    a large field flooded with NOISE everywhere else. NOISE may appear
    inside the window's bg cells too — remove-color erases it all. The
    window's extreme edges are guaranteed to carry ca/cb so the crop bbox
    is the window (deterministic)."""
    rng = ctx.draw_rng(f"input_{idx}")
    g = [[0] * gw for _ in range(gh)]

    # pervasive noise flood (high density, spans whole grid)
    for r in range(gh):
        for c in range(gw):
            if rng.random() < 0.5:
                g[r][c] = noise

    sh = rng.randint(slo, min(shi, gh - 2))
    sw = rng.randint(slo, min(shi, gw - 2))
    sr = rng.randint(0, gh - sh)
    sc = rng.randint(0, gw - sw)

    # fill window with ca/cb/noise mix (noise inside the window is fine —
    # it is removed). Clear first so we control the shape.
    for r in range(sr, sr + sh):
        for c in range(sc, sc + sw):
            roll = rng.random()
            if roll < 0.4:
                g[r][c] = ca
            elif roll < 0.7:
                g[r][c] = cb
            else:
                g[r][c] = noise        # interior gaps (become bg)

    # force the 4 window corners + edges to carry non-noise so bbox == window
    for c in range(sc, sc + sw):
        if rng.random() < 0.6:
            g[sr][c] = rng.choice([ca, cb])
        if rng.random() < 0.6:
            g[sr + sh - 1][c] = rng.choice([ca, cb])
    for r in range(sr, sr + sh):
        if rng.random() < 0.6:
            g[r][sc] = rng.choice([ca, cb])
        if rng.random() < 0.6:
            g[r][sc + sw - 1] = rng.choice([ca, cb])
    g[sr][sc] = ca
    g[sr][sc + sw - 1] = cb
    g[sr + sh - 1][sc] = cb
    g[sr + sh - 1][sc + sw - 1] = ca

    # CRITICAL: outside the window, the only non-noise must be bg, else the
    # crop bbox grows. Noise outside is fine (removed). But ca/cb must NOT
    # leak outside — we only ever placed ca/cb inside the window, so we are
    # safe. Nothing to clean.
    return g


def generate_task(seed, *, difficulty="medium"):
    ctx = gen_ctx(seed=seed, sample_index=0, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty)
    (glo, ghi), (slo, shi) = _dims_for(difficulty)

    noise, ca, cb, db, dd = ctx.draw_distinct_colors("colors", n=5, exclude=[0])
    # recolor-map: ca->db, cb->dd. db/dd distinct from each other and from
    # noise/ca/cb so the swap is real and bg(0) is never a key/value.
    mapping = {ca: db, cb: dd}
    n_train = ctx.draw_int("n_train", 3, 4)
    n_test = ctx.draw_int("n_test", 1, 2)

    program = (f"(rule! (lambda (g) (crop-to-content "
               f"(recolor-map (remove-color g {noise}) "
               f"(hash {ca} {db} {cb} {dd})))))")

    pairs = []
    for idx in range(n_train + n_test):
        gh = ctx.draw_int(f"gh_{idx}", glo, ghi)
        gw = ctx.draw_int(f"gw_{idx}", glo, ghi)
        gin = _build_input(ctx, idx, noise, ca, cb, gh, gw, slo, shi)
        gout = _apply(gin, noise, mapping)
        pairs.append({"input": gin, "output": gout})

    return {
        "train": pairs[:n_train],
        "test": pairs[n_train:],
        "program": program,
        "chain": ["remove_color", "recolor_map", "crop_to_content"],
        "meta": {"difficulty": difficulty, "noise": noise,
                 "mapping": mapping, "version": VERSION},
    }


if __name__ == "__main__":
    parity_check(generate_task, n=25, version_label=VERSION)
