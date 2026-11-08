"""gen3 — GATHER via panel ``overlay``-merge: the two halves of the grid are
superimposed into one half-size panel ``(overlay (left-half g) (right-half g))``
(or top/bottom), collapsing the scattered components of two panels into one
denser merged panel. Optionally composed with a pre-recolor map."""
from __future__ import annotations

from puzzle_generators.base import gen_ctx

BG = 0
VERSION = "0.1.1"



def _dims(g):
    return len(g), len(g[0])


def _colors(g, bg=BG):
    return sorted({v for row in g for v in row if v != bg})


def _recolor(g, src, dst):
    return [[dst if v == src else v for v in row] for row in g]


def _left_half(g):
    w = len(g[0])
    return [row[: w // 2] for row in g]


def _right_half(g):
    w = len(g[0])
    return [row[(w + 1) // 2:] for row in g]


def _top_half(g):
    h = len(g)
    return [row[:] for row in g[: h // 2]]


def _bottom_half(g):
    h = len(g)
    return [row[:] for row in g[(h + 1) // 2:]]


def _overlay(g1, g2, bg=BG):
    """Byte-exact mirror of prelude (overlay g1 g2): g2 wins where non-bg."""
    h, w = _dims(g1)
    return [[(g2[r][c] if g2[r][c] != bg else g1[r][c]) for c in range(w)] for r in range(h)]


def _components(g, bg=BG):
    h, w = _dims(g)
    seen = [[False] * w for _ in range(h)]
    n = 0
    for r in range(h):
        for c in range(w):
            if g[r][c] == bg or seen[r][c]:
                continue
            n += 1
            color = g[r][c]
            stack = [(r, c)]
            seen[r][c] = True
            while stack:
                cr, cc = stack.pop()
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = cr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and not seen[nr][nc] and g[nr][nc] == color:
                        seen[nr][nc] = True
                        stack.append((nr, nc))
    return n


_HALVES = {
    "lr": (_left_half, _right_half, "left-half", "right-half"),
    "ud": (_top_half, _bottom_half, "top-half", "bottom-half"),
}


def _build_input(rng, *, axis, difficulty):
    """Scatter sized so both halves are equal and dense enough to merge.

    For axis 'lr' force EVEN width (so left/right halves match width); for 'ud'
    force EVEN height (so top/bottom halves match height)."""
    if difficulty == "easy":
        base, ncols, density = rng.randint(5, 7), rng.randint(2, 3), 0.24
    elif difficulty == "hard":
        base, ncols, density = rng.randint(11, 15), rng.randint(3, 5), 0.24
    else:
        base, ncols, density = rng.randint(8, 11), rng.randint(2, 4), 0.24
    if axis == "lr":
        h = rng.randint(max(8, base + 4), base + 14)
        w = base * 2  # even
    else:
        h = base * 2  # even
        w = rng.randint(max(8, base + 4), base + 14)
    palette = rng.sample(range(1, 10), ncols)
    g = [[BG] * w for _ in range(h)]
    for r in range(h):
        for c in range(w):
            if rng.random() < density:
                g[r][c] = rng.choice(palette)
    return g, palette


def _apply(g, params):
    base = g
    if params["recolor"] is not None:
        base = _recolor(base, params["recolor"][0], params["recolor"][1])
    fa, fb, _, _ = _HALVES[params["axis"]]
    return _overlay(fa(base), fb(base))


def _program(params):
    inner = "g"
    if params["recolor"] is not None:
        src, dst = params["recolor"]
        inner = f"(recolor g {src} {dst})"
    _, _, ha, hb = _HALVES[params["axis"]]
    return f"(overlay ({ha} {inner}) ({hb} {inner}))"


def generate_task(seed, *, difficulty="medium"):
    ctx = gen_ctx(seed=seed, sample_index=0, version=VERSION,
                  task_id="gather_gen3", difficulty=difficulty, overrides={})
    rng = ctx.draw_rng("gen3")

    axis = rng.choice(["lr", "ud"])
    use_recolor = rng.random() < 0.5
    params = {"axis": axis, "recolor": None}

    n_train = rng.randint(3, 4)
    n_test = rng.randint(1, 2)
    pairs = []
    in_comp = out_comp = 0
    attempts = 0
    while len(pairs) < n_train + n_test and attempts < 300:
        attempts += 1
        g, palette = _build_input(rng, axis=axis, difficulty=difficulty)
        if use_recolor and params["recolor"] is None and len(palette) >= 1:
            src = palette[0]
            dst = next(c for c in range(1, 10) if c != src)
            params["recolor"] = (src, dst)
        out = _apply(g, params)
        if out == g:
            continue
        ci, co = _components(g), _components(out)
        if co >= ci:
            continue
        pairs.append({"input": g, "output": out})
        in_comp += ci
        out_comp += co

    train = pairs[:n_train]
    test = pairs[n_train:n_train + n_test]
    return {
        "train": train,
        "test": test,
        "program": _program(params),
        "chain": (["recolor"] if params["recolor"] else []) + ["overlay-merge"],
        "meta": {"difficulty": difficulty, "version": VERSION, "axis": axis,
                 "avg_in_comp": in_comp / max(1, len(pairs)),
                 "avg_out_comp": out_comp / max(1, len(pairs))},
    }


if __name__ == "__main__":
    from arc_repl.racket_bridge import RacketBridge
    b = RacketBridge()
    n = 30
    ok = 0
    tot_in = tot_out = 0.0
    npairs = 0
    for s in range(n):
        task = generate_task(s, difficulty=["easy", "medium", "hard"][s % 3])
        prog = task["program"]
        for pair in task["train"] + task["test"]:
            b.define_grid("g", pair["input"])
            got = b.eval_text(prog)
            if got == pair["output"]:
                ok += 1
            else:
                print(f"MISMATCH seed={s} prog={prog}")
                print("  in ", pair["input"])
                print("  exp", pair["output"])
                print("  got", got)
            tot_in += _components(pair["input"])
            tot_out += _components(pair["output"])
            npairs += 1
    print(f"PARITY: {ok}/{npairs} exact")
    print(f"avg components in->out: {tot_in/npairs:.1f} -> {tot_out/npairs:.1f}")
