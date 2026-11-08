"""gen2 — GATHER via two-axis corner pack ``(gravity (gravity g d1 bg) d2 bg)``: a first
gravity packs to one edge, a second (perpendicular) gravity packs that into a
corner, collapsing a scattered field into one dense corner mass. Optionally
composed with a pre-recolor map.  The generator deliberately uses a sampled
nonzero modal background; ARC-AGI-2 eval often does, and keeping every gather
task on black-background fields was a systematic distribution shortcut."""
from __future__ import annotations

import re

from puzzle_generators.base import gen_ctx

DEFAULT_BG = 0
VERSION = "0.2.1"



def _dims(g):
    return len(g), len(g[0])


def _colors(g, bg=DEFAULT_BG):
    return sorted({v for row in g for v in row if v != bg})


def _recolor(g, src, dst):
    return [[dst if v == src else v for v in row] for row in g]


def _gravity(g, direction, bg=DEFAULT_BG):
    """Byte-exact mirror of prelude (gravity g direction)."""
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
    else:
        for r in range(h):
            non_bg = [v for v in g[r] if v != bg]
            pad = w - len(non_bg)
            packed = ([bg] * pad + non_bg) if direction == "right" else (non_bg + [bg] * pad)
            out[r] = packed
    return out


def _components(g, bg=DEFAULT_BG):
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


def _build_input(rng, *, difficulty, bg):
    """Few colors + medium density so the corner pack merges into a solid block."""
    if difficulty == "easy":
        h, w, ncols, density = rng.randint(10, 14), rng.randint(10, 14), rng.randint(2, 3), 0.20
    elif difficulty == "hard":
        h, w, ncols, density = rng.randint(22, 30), rng.randint(22, 30), rng.randint(3, 5), 0.22
    else:
        h, w, ncols, density = rng.randint(16, 22), rng.randint(16, 22), rng.randint(2, 4), 0.22
    palette = rng.sample([c for c in range(10) if c != bg], ncols)
    g = [[bg] * w for _ in range(h)]
    for r in range(h):
        for c in range(w):
            if rng.random() < density:
                g[r][c] = rng.choice(palette)
    return g, palette


def _apply(g, params):
    out = g
    if params["recolor"] is not None:
        out = _recolor(out, params["recolor"][0], params["recolor"][1])
    out = _gravity(out, params["dir1"], params["bg"])
    out = _gravity(out, params["dir2"], params["bg"])
    return out


def _program(params):
    inner = "g"
    if params["recolor"] is not None:
        src, dst = params["recolor"]
        inner = f"(recolor g {src} {dst})"
    return f'(gravity (gravity {inner} "{params["dir1"]}" {params["bg"]}) "{params["dir2"]}" {params["bg"]})'


def generate_task(seed, *, difficulty="medium"):
    ctx = gen_ctx(seed=seed, sample_index=0, version=VERSION,
                  task_id="gather_gen2", difficulty=difficulty, overrides={})
    rng = ctx.draw_rng("gen2")

    # Pick a vertical then a horizontal axis (perpendicular -> a true corner).
    dir1 = rng.choice(["down", "up"])
    dir2 = rng.choice(["left", "right"])
    if rng.random() < 0.5:
        dir1, dir2 = dir2, dir1  # sometimes horizontal-then-vertical
    use_recolor = rng.random() < 0.5
    bg = rng.choice(range(1, 10))
    params = {"dir1": dir1, "dir2": dir2, "recolor": None, "bg": bg}

    n_train = rng.randint(3, 4)
    n_test = rng.randint(1, 2)
    pairs = []
    in_comp = out_comp = 0
    attempts = 0
    while len(pairs) < n_train + n_test and attempts < 200:
        attempts += 1
        g, palette = _build_input(rng, difficulty=difficulty, bg=bg)
        if use_recolor and params["recolor"] is None and len(palette) >= 1:
            src = palette[0]
            dst = next(c for c in range(10) if c not in (src, bg))
            params["recolor"] = (src, dst)
        out = _apply(g, params)
        if out == g:
            continue
        ci, co = _components(g, bg), _components(out, bg)
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
        "chain": (["recolor"] if params["recolor"] else []) + ["gravity", "gravity", "nonzero_background"],
        "meta": {"difficulty": difficulty, "version": VERSION, "dir1": dir1, "dir2": dir2,
                 "bg_color": params["bg"],
                 "avg_in_comp": in_comp / max(1, len(pairs)),
                 "avg_out_comp": out_comp / max(1, len(pairs))},
    }


_PROGRAM_RE = re.compile(
    r'^\(gravity \(gravity (?P<inner>g|\(recolor g (?P<src>\d+) (?P<dst>\d+)\)) '
    r'"(?P<dir1>down|up|left|right)" (?P<bg1>\d+)\) '
    r'"(?P<dir2>down|up|left|right)" (?P<bg2>\d+)\)$'
)


def _params_from_program(program):
    m = _PROGRAM_RE.match(program)
    if not m:
        return None
    bg1 = int(m.group("bg1"))
    bg2 = int(m.group("bg2"))
    if bg1 != bg2:
        return None
    recolor = None
    if m.group("src") is not None:
        recolor = (int(m.group("src")), int(m.group("dst")))
    return {
        "dir1": m.group("dir1"),
        "dir2": m.group("dir2"),
        "bg": bg1,
        "recolor": recolor,
    }


def _rectangular(g):
    return isinstance(g, list) and g and isinstance(g[0], list) and all(len(row) == len(g[0]) for row in g)


def self_check_task(task):
    """Executable invariants for the two-axis gather concept task.

    The examples must be reproducible from the emitted program, use one nonzero
    modal background, gather along perpendicular axes into a corner, and reduce
    same-color component count on every pair.  This catches the common generic
    concept failure modes where a sampled task is internally inconsistent or
    degenerates to a no-op gather.
    """
    errs = []
    if not isinstance(task, dict):
        return ["task must be a dict"]
    train = task.get("train") or []
    test = task.get("test") or []
    pairs = train + test
    if len(train) < 3:
        errs.append(f"need at least 3 train pairs, got {len(train)}")
    if len(test) < 1:
        errs.append(f"need at least 1 test pair, got {len(test)}")
    params = _params_from_program(task.get("program", ""))
    if params is None:
        errs.append("program must be the closed form two-gravity gather expression")
        return errs
    vertical = {"up", "down"}
    horizontal = {"left", "right"}
    dirs = {params["dir1"], params["dir2"]}
    if not (dirs & vertical and dirs & horizontal):
        errs.append(f"gather axes must be perpendicular, got {params['dir1']} then {params['dir2']}")
    if params["bg"] == DEFAULT_BG:
        errs.append("normal gather_gen2 tasks should exercise a nonzero modal background")
    if params["recolor"] is not None:
        src, dst = params["recolor"]
        if src == dst or src == params["bg"] or dst == params["bg"]:
            errs.append(f"invalid recolor under bg={params['bg']}: {src}->{dst}")
    for i, pair in enumerate(pairs):
        g = pair.get("input") if isinstance(pair, dict) else None
        out = pair.get("output") if isinstance(pair, dict) else None
        if not (_rectangular(g) and _rectangular(out)):
            errs.append(f"pair {i} must contain rectangular input/output grids")
            continue
        if _dims(g) != _dims(out):
            errs.append(f"pair {i} output dims {_dims(out)} differ from input dims {_dims(g)}")
            continue
        got = _apply(g, params)
        if got != out:
            errs.append(f"pair {i} output does not match emitted program")
        if out == g:
            errs.append(f"pair {i} is a gather no-op")
        ci, co = _components(g, params["bg"]), _components(out, params["bg"])
        if co >= ci:
            errs.append(f"pair {i} does not reduce component count: {ci}->{co}")
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
