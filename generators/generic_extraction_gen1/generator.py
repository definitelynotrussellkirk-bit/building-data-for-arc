"""gen1: keep-only ONE target color, then crop-to-content.

Transform: `(crop-to-content (keep-only g TARGET))` — from a large
multi-color noisy field, erase every color except TARGET (filter), then
crop to the tight bounding box of the surviving TARGET cells
(extraction). Output is the small TARGET-shaped patch; distractor
colors are scattered everywhere else and vanish.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.generic.concepts.extraction import parity_check

VERSION = "1.1.0"
TASK_ID = "generic_extraction_gen1"


def _dims_for(difficulty):
    if difficulty == "easy":
        return (12, 16), (3, 6)
    if difficulty == "hard":
        return (22, 30), (5, 9)
    return (16, 24), (4, 7)          # medium


def _keep_only(g, target):
    return [[v if v == target else 0 for v in row] for row in g]


def _crop_to_content(g):
    h, w = len(g), len(g[0])
    rs = [r for r in range(h) if any(g[r][c] != 0 for c in range(w))]
    cs = [c for c in range(w) if any(g[r][c] != 0 for r in range(h))]
    if not rs or not cs:
        return [[]]                  # mirrors Racket '(())
    r1, r2, c1, c2 = rs[0], rs[-1], cs[0], cs[-1]
    return [[g[r][c] for c in range(c1, c2 + 1)] for r in range(r1, r2 + 1)]


def _apply(g, target):
    return _crop_to_content(_keep_only(g, target))


def _build_input(ctx, idx, target, distractors, gh, gw):
    """Large field: TARGET forms a compact blob in a random window; the
    rest is sparse scatter of distractor colors (never TARGET, so they
    cannot extend the kept bbox)."""
    rng = ctx.draw_rng(f"input_{idx}")
    g = [[0] * gw for _ in range(gh)]
    # distractor scatter
    for r in range(gh):
        for c in range(gw):
            if rng.random() < 0.22:
                g[r][c] = rng.choice(distractors)
    # TARGET blob inside a random window. Require an interior cell so we can
    # force a zero hole below; otherwise small 2x2 windows can become a solid
    # single-color crop and teach only "return a rectangle of TARGET".
    bh = rng.randint(3, max(3, gh // 2))
    bw = rng.randint(3, max(3, gw // 2))
    br = rng.randint(0, gh - bh)
    bc = rng.randint(0, gw - bw)
    # ensure the blob spans its full window on at least the extreme rows/cols
    # so crop dims are deterministic: fill corners, then random interior.
    for r in range(br, br + bh):
        for c in range(bc, bc + bw):
            if rng.random() < 0.6:
                g[r][c] = target
            elif g[r][c] == target:
                g[r][c] = 0
    # force the 4 window edges to contain target so the bbox == window
    for c in range(bc, bc + bw):
        g[br][c] = target if rng.random() < 0.7 else g[br][c]
        g[br + bh - 1][c] = target if rng.random() < 0.7 else g[br + bh - 1][c]
    for r in range(br, br + bh):
        g[r][bc] = target if rng.random() < 0.7 else g[r][bc]
        g[r][bc + bw - 1] = target if rng.random() < 0.7 else g[r][bc + bw - 1]
    # guarantee each extreme edge has >=1 target (so window is the true bbox)
    g[br][bc] = target
    g[br][bc + bw - 1] = target
    g[br + bh - 1][bc] = target
    g[br + bh - 1][bc + bw - 1] = target
    # Force an interior zero so the cropped keep-only output is never a uniform
    # TARGET block. This preserves the same crop bbox while making the extraction
    # task about the target *shape*, not just its bounding rectangle.
    g[br + bh // 2][bc + bw // 2] = 0
    # clear any stray TARGET that leaked into the distractor scatter OUTSIDE
    # the window (would corrupt the bbox)
    for r in range(gh):
        for c in range(gw):
            if g[r][c] == target and not (br <= r < br + bh and bc <= c < bc + bw):
                g[r][c] = 0
    return g


def generate_task(seed, *, difficulty="medium"):
    ctx = gen_ctx(seed=seed, sample_index=0, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty)
    (glo, ghi), (blo, bhi) = _dims_for(difficulty)

    target = ctx.draw_color("target", exclude=[0])
    distractors = list(ctx.draw_distinct_colors("distractors", n=4,
                                                exclude=[0, target]))
    n_train = ctx.draw_int("n_train", 3, 4)
    n_test = ctx.draw_int("n_test", 1, 2)

    program = (f"(rule! (lambda (g) "
               f"(crop-to-content (keep-only g {target}))))")

    pairs = []
    for idx in range(n_train + n_test):
        gh = ctx.draw_int(f"gh_{idx}", glo, ghi)
        gw = ctx.draw_int(f"gw_{idx}", glo, ghi)
        gin = _build_input(ctx, idx, target, distractors, gh, gw)
        gout = _apply(gin, target)
        pairs.append({"input": gin, "output": gout})

    return {
        "train": pairs[:n_train],
        "test": pairs[n_train:],
        "program": program,
        "chain": ["keep_only", "crop_to_content"],
        "meta": {"difficulty": difficulty, "target": target,
                 "distractors": distractors, "version": VERSION},
    }


if __name__ == "__main__":
    parity_check(generate_task, n=25, version_label=VERSION)
