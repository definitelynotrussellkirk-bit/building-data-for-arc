"""gen1 — GATHER via single-axis ``gravity`` pack (packs all non-bg cells to one
edge, collapsing a scattered field into a dense bar), optionally composed with a
pre-recolor map (recolor one source color before the pack)."""
from __future__ import annotations

from puzzle_generators.base import gen_ctx

BG = 0
VERSION = "0.1.1"



# --------------------------------------------------------------------------
# Python reference ops (must be byte-exact with the Racket prelude heads)
def _dims(g):
    return len(g), len(g[0])


def _colors(g, bg=BG):
    return sorted({v for row in g for v in row if v != bg})


def _recolor(g, src, dst):
    """Mirror of prelude (recolor g from to)."""
    return [[dst if v == src else v for v in row] for row in g]


def _gravity(g, direction, bg=BG):
    """Byte-exact mirror of prelude (gravity g direction).

    down/right pack non-bg to the high index (append after bg pad);
    up/left pack to the low index (bg pad after).
    """
    h, w = _dims(g)
    out = [[bg] * w for _ in range(h)]
    if direction in ("down", "up"):
        for c in range(w):
            col = [g[r][c] for r in range(h)]
            non_bg = [v for v in col if v != bg]
            pad = h - len(non_bg)
            packed = ([bg] * pad + non_bg) if direction == "down" else (non_bg + [bg] * pad)
            for r in range(h):
                out[r][c] = packed[r]
    else:  # left / right
        for r in range(h):
            row = g[r]
            non_bg = [v for v in row if v != bg]
            pad = w - len(non_bg)
            packed = ([bg] * pad + non_bg) if direction == "right" else (non_bg + [bg] * pad)
            out[r] = packed
    return out


def _components(g, bg=BG):
    """4-connected components, like prelude (objects g)."""
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


# --------------------------------------------------------------------------
def _build_input(rng, *, difficulty):
    """Sparse scatter of many tiny components so the gravity pack is dramatic."""
    if difficulty == "easy":
        h, w, ncols, density = rng.randint(10, 14), rng.randint(10, 14), rng.randint(2, 3), 0.14
    elif difficulty == "hard":
        h, w, ncols, density = rng.randint(22, 30), rng.randint(22, 30), rng.randint(5, 8), 0.16
    else:
        h, w, ncols, density = rng.randint(16, 22), rng.randint(16, 22), rng.randint(3, 5), 0.15
    palette = rng.sample(range(1, 10), ncols)
    g = [[BG] * w for _ in range(h)]
    for r in range(h):
        for c in range(w):
            if rng.random() < density:
                g[r][c] = rng.choice(palette)
    return g, palette


def _apply(g, params):
    out = g
    if params["recolor"] is not None:
        out = _recolor(out, params["recolor"][0], params["recolor"][1])
    out = _gravity(out, params["dir"])
    return out


def _program(params):
    inner = "g"
    if params["recolor"] is not None:
        src, dst = params["recolor"]
        inner = f"(recolor g {src} {dst})"
    return f'(gravity {inner} "{params["dir"]}")'


def generate_task(seed, *, difficulty="medium"):
    ctx = gen_ctx(seed=seed, sample_index=0, version=VERSION,
                  task_id="gather_gen1", difficulty=difficulty, overrides={})
    rng = ctx.draw_rng("gen1")

    # FIX one transform + params for the whole task.
    direction = rng.choice(["down", "up", "left", "right"])
    use_recolor = rng.random() < 0.5
    params = {"dir": direction, "recolor": None}

    n_train = rng.randint(3, 4)
    n_test = rng.randint(1, 2)
    pairs = []
    in_comp = out_comp = 0
    attempts = 0
    while len(pairs) < n_train + n_test and attempts < 200:
        attempts += 1
        g, palette = _build_input(rng, difficulty=difficulty)
        # Lock the recolor pair once, using this task's palette, to a present color.
        if use_recolor and params["recolor"] is None and len(palette) >= 1:
            src = palette[0]
            dst = next(c for c in range(1, 10) if c != src)
            params["recolor"] = (src, dst)
        out = _apply(g, params)
        if out == g:
            continue  # require output != input
        ci, co = _components(g), _components(out)
        if co >= ci:
            continue  # require an actual collapse
        pairs.append({"input": g, "output": out})
        in_comp += ci
        out_comp += co

    train = pairs[:n_train]
    test = pairs[n_train:n_train + n_test]
    return {
        "train": train,
        "test": test,
        "program": _program(params),
        "chain": (["recolor"] if params["recolor"] else []) + ["gravity"],
        "meta": {"difficulty": difficulty, "version": VERSION, "dir": direction,
                 "avg_in_comp": in_comp / max(1, len(pairs)),
                 "avg_out_comp": out_comp / max(1, len(pairs))},
    }



def self_check_task(task):
    """Executable invariants for generated gather tasks."""
    errs = []
    if not isinstance(task, dict):
        return ["task is not a dict"]
    train = task.get("train") or []
    test = task.get("test") or []
    pairs = train + test
    if len(train) < 3:
        errs.append("expected at least three training pairs")
    if len(test) < 1:
        errs.append("expected at least one test pair")
    if task.get("chain", [])[-1:] != ["gravity"]:
        errs.append("program chain must end in gravity")
    program = task.get("program", "")
    if "(gravity " not in program:
        errs.append("program must contain a gravity call")

    for i, pair in enumerate(pairs):
        g = pair.get("input")
        out = pair.get("output")
        if not g or not out or not g[0] or not out[0]:
            errs.append(f"pair {i} has an empty grid")
            continue
        if any(len(row) != len(g[0]) for row in g) or any(len(row) != len(out[0]) for row in out):
            errs.append(f"pair {i} has a ragged grid")
            continue
        if (len(g), len(g[0])) != (len(out), len(out[0])):
            errs.append(f"pair {i} changes grid shape")
        if out == g:
            errs.append(f"pair {i} output equals input")
        if _components(out) >= _components(g):
            errs.append(f"pair {i} does not reduce component count")
    meta = task.get("meta", {})
    if meta.get("avg_out_comp", 10**9) >= meta.get("avg_in_comp", -1):
        errs.append("meta component averages do not show collapse")
    return errs


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
            tot_in += _components(pair["input"])
            tot_out += _components(pair["output"])
            npairs += 1
    print(f"PARITY: {ok}/{npairs} exact")
    print(f"avg components in->out: {tot_in/npairs:.1f} -> {tot_out/npairs:.1f}")
