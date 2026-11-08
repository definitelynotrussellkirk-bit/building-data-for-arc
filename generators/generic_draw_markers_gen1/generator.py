"""gen1: recolor base noise (A->B), then draw a FULL CROSS (row+col) in a NEW
color centered on every marker cell -- markers (a distinct color) drive WHERE
each cross is drawn; the cross color is absent from the input.

Transform: (pipe (recolor g A B) -> for each marker (r,c): (draw-cross g r c NEW)).
Composes a color recolor with the draw-from-markers cross step.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.generic.concepts.draw_markers import parity_check

VERSION = "1.1.0"
GENERATOR_ID = "draw_markers.gen1"


def _dims(g):
    return len(g), len(g[0])


def _draw_cross(g, r, c, color):
    """Byte-exact replica of prelude (draw-cross g r c color): paint the whole
    row r and whole column c with color, overwriting existing cells."""
    h, w = _dims(g)
    return [[color if (rr == r or cc == c) else g[rr][cc]
             for cc in range(w)] for rr in range(h)]


def _recolor(g, src, dst):
    return [[dst if v == src else v for v in row] for row in g]


def _apply(g, *, noise_a, noise_b, markers, new_color):
    out = _recolor(g, noise_a, noise_b)
    for (r, c) in markers:  # row-major order, same as Racket pipe sequence
        out = _draw_cross(out, r, c, new_color)
    return out


def _build_input(ctx, sample_index, *, noise_a, marker_color, new_color, bg_color, difficulty):
    rng = ctx.draw_rng(f"input.{sample_index}")
    if difficulty == "easy":
        h, w, nmark, dens = rng.randint(8, 11), rng.randint(8, 11), rng.randint(2, 3), 0.12
    elif difficulty == "hard":
        h, w, nmark, dens = rng.randint(20, 28), rng.randint(20, 28), rng.randint(4, 6), 0.20
    else:
        h, w, nmark, dens = rng.randint(13, 19), rng.randint(13, 19), rng.randint(3, 5), 0.16
    g = [[bg_color] * w for _ in range(h)]
    # scatter base noise (color = noise_a) -- the "core pattern"
    for r in range(h):
        for c in range(w):
            if rng.random() < dens:
                g[r][c] = noise_a
    # place markers at distinct, well-separated cells
    cells = [(r, c) for r in range(h) for c in range(w)]
    rng.shuffle(cells)
    markers = []
    used = set()
    for (r, c) in cells:
        if len(markers) >= nmark:
            break
        if all(abs(r - mr) >= 2 or abs(c - mc) >= 2 for (mr, mc) in markers):
            markers.append((r, c))
            used.add((r, c))
    for (r, c) in markers:
        g[r][c] = marker_color
    markers.sort()  # row-major
    return g, markers


def generate_task(seed, *, difficulty="medium", n_train=3, n_test=1):
    ctx = gen_ctx(seed=seed, sample_index=0, version=VERSION,
                  task_id=GENERATOR_ID, difficulty=difficulty)
    # FIX the transform params for the whole task (all pairs share the rule).
    pal = ctx.draw_rng("palette")
    cols = pal.sample(range(1, 10), 4)
    noise_a, marker_color, new_color, bg_color = cols[0], cols[1], cols[2], cols[3]
    noise_b = pal.choice([c for c in range(1, 10)
                          if c not in (noise_a, marker_color, new_color, bg_color)])

    train, test = [], []
    for i in range(n_train):
        g, markers = _build_input(ctx, i, noise_a=noise_a, marker_color=marker_color,
                                  new_color=new_color, bg_color=bg_color,
                                  difficulty=difficulty)
        out = _apply(g, noise_a=noise_a, noise_b=noise_b, markers=markers,
                     new_color=new_color)
        train.append({"input": g, "output": out})
    for j in range(n_test):
        g, markers = _build_input(ctx, 100 + j, noise_a=noise_a, marker_color=marker_color,
                                  new_color=new_color, bg_color=bg_color,
                                  difficulty=difficulty)
        out = _apply(g, noise_a=noise_a, noise_b=noise_b, markers=markers,
                     new_color=new_color)
        test.append({"input": g, "output": out})

    # Racket program: recolor noise, then draw a cross per marker. We find the
    # markers in-Racket by (find-color g marker_color) BEFORE the recolor so the
    # marker positions are stable, then fold draw-cross over them.
    body = (
        f"(let ([ms (find-color g {marker_color})])"
        f" (foldl (lambda (m acc) (draw-cross acc (first m) (second m) {new_color}))"
        f" (recolor g {noise_a} {noise_b}) ms))"
    )
    program = f"(rule! (lambda (g) {body}))"
    return {"train": train, "test": test, "program": program,
            "chain": ["recolor", "draw_cross_from_markers"],
            "new_color": new_color, "marker_color": marker_color,
            "bg_color": bg_color}


if __name__ == "__main__":
    parity_check(generate_task, n=25, version_label=GENERATOR_ID)
