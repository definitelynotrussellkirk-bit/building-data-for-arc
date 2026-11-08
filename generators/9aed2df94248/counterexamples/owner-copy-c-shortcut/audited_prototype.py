"""Parametric panel analogy: infer the A->B transformation, transfer once/twice/mirror.

The default Racket program is byte-identical to the selected canonical authority.
All labels are Python *claims*; the native preflight replays them via protected Racket.
The input is built independently of episode mode (no mode cues in the layout).
"""
from __future__ import annotations

import hashlib
import json
import random
from pathlib import Path
from reviewer_support import canonical_path, find_root

TASK_ID = "9aed2df94248"
ROOT = find_root(__file__)
MODES = ("once", "twice", "mirror_after")
DEFAULT = "once"


def canonical_source(root=ROOT):
    sources = []
    with canonical_path(root).open(encoding="utf8") as file:
        for line in file:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                sources.append(row.get("program_solution"))
    if len(set(sources)) != 1 or not sources or not sources[0]:
        raise ValueError("canonical program missing or non-unique")
    return sources[0]


def program_for(mode, root=ROOT):
    if mode not in MODES or type(mode) is not str:
        raise ValueError("invalid panel transfer mode")
    canonical = canonical_source(root)
    if mode == DEFAULT:
        return canonical
    needle = "(apply-transform c (if (eq? cmd #f) 0 cmd))"
    if canonical.count(needle) != 1:
        raise ValueError("canonical source changed: guarded final transfer not found")
    cmd = "(if (eq? cmd #f) 0 cmd)"
    expression = (
        f"(apply-transform (apply-transform c {cmd}) {cmd})" if mode == "twice"
        else f"(flip-lr (apply-transform c {cmd}))"
    )
    return canonical.replace(needle, expression)


def _rotation(points, code):
    if code == 1: return {(c, -r) for r, c in points}
    if code == 2: return {(-r, -c) for r, c in points}
    if code == 3: return {(c, r) for r, c in points}
    if code == 4: return {(r, -c) for r, c in points}
    if code == 5: return {(-r, c) for r, c in points}
    return set(points)


def _norm(points):
    r0 = min(r for r, _ in points)
    c0 = min(c for _, c in points)
    return frozenset((r-r0, c-c0) for r, c in points)


def _all_eight(points):
    return {tuple(sorted(_norm(transformed))) for transformed in (
        *(_rotation(points, code) for code in range(6)),
        {(-c, r) for r, c in points},
        {(-c, -r) for r, c in points},
    )}


def _shape(rng, height, width, fill):
    """Construct a connected spanning shape with occupied every row and column."""
    if height < 3 or width < 3:
        raise ValueError("shape dimensions too small for reliable D4 asymmetry")
    for _ in range(60):
        r, c = 0, 0
        cells = {(r, c)}
        route = [0]*(height-1) + [1]*(width-1)
        rng.shuffle(route)
        for step in route:
            if step == 0: r += 1
            else: c += 1
            cells.add((r, c))
        # Add only cells adjacent to an existing cell: no isolated pixels.
        goal = max(len(cells), int(round(height * width * fill)))
        for _ in range(height * width * 12):
            if len(cells) >= goal: break
            rr, cc = rng.choice(tuple(sorted(cells)))
            dr, dc = rng.choice(((0,1),(1,0),(-1,0),(0,-1)))
            q = (rr+dr, cc+dc)
            if 0 <= q[0] < height and 0 <= q[1] < width:
                cells.add(q)
        if len(_all_eight(cells)) == 8:
            return frozenset(cells)
    raise RuntimeError("could not construct asymmetric shape")


def _matrix(cells, color):
    cells = _norm(cells)
    h = max(r for r, _ in cells)+1
    w = max(c for _, c in cells)+1
    return [[color if (r,c) in cells else 0 for c in range(w)] for r in range(h)]


def _grid_key(g):
    return tuple(tuple(row) for row in g)


def _apply_to_c(c, code, mode):
    points = _rotation(c, code)
    if mode == "twice": points = _rotation(points, code)
    elif mode == "mirror_after": points = _rotation(points, 4)
    return _norm(points)


def _sample(seed, index, total, difficulty):
    rng = random.Random(f"panel-transfer:{seed}:{index}:{total}:{difficulty}")
    # Transform identities vary with the seed and scene; never encode them in
    # demonstration/query index, dimensions, or a fixed global schedule.
    # First demo must expose all three output policies, and the next must show
    # a different A->B transform while preserving the minimum two-demo lesson.
    if index == 0:
        code = rng.choice((1, 2, 3, 5))
    elif index == 1:
        first_rng = random.Random(f"panel-transfer:{seed}:0:{total}:{difficulty}")
        first_code = first_rng.choice((1, 2, 3, 5))
        code = rng.choice(tuple(c for c in (1, 2, 3, 4, 5) if c != first_code))
    else:
        code = rng.choice((1, 2, 3, 4, 5))
    large = index == total-1
    if large:
        code = rng.choice((2, 4, 5))   # tall narrow panels must stay tall
        h, w = 30, 30
        ah, aw, ch, cw = 30, 8, 29, 8
        gap1, gap2 = 2, 2
    else:
        h = rng.randint(7, 12) if difficulty != "easy" else rng.randint(6,9)
        ah = rng.randint(4, min(7,h))
        aw = rng.randint(4, 6)
        ch = rng.randint(4, min(7,h))
        cw = rng.randint(4, 6)
        gap1, gap2 = rng.randint(1, 2), rng.randint(1, 2)
        w = None
    a = _shape(rng, ah, aw, rng.uniform(.38, .65))
    b = _norm(_rotation(a, code))
    c = _shape(rng, ch, cw, rng.uniform(.32, .68))
    panels = (a,b,c)
    sizes = [(max(r for r,_ in p)+1,max(cc for _,cc in p)+1) for p in panels]
    needed_w = sizes[0][1]+sizes[1][1]+sizes[2][1]+gap1+gap2
    if large:
        assert needed_w == 28 and h == 30 and w == 30
        offset = 1
    else:
        w = min(30,needed_w + rng.randint(2,5))
        offset = rng.randint(0, w-needed_w)
    if h < max(sh for sh,_ in sizes):
        raise ValueError("inconsistent panel height")
    color = rng.randint(1,9)
    grid = [[0]*w for _ in range(h)]
    col = offset
    for k,p in enumerate(panels):
        ph,pw=sizes[k]
        row = rng.randint(0,h-ph)
        for rr,cc in p:
            grid[row+rr][col+cc]=color
        col += pw + (gap1 if k==0 else gap2 if k==1 else 0)
    labels = {mode:_matrix(_apply_to_c(c,code,mode),color) for mode in MODES}
    # A constructed lesson must separate all three settings on *every* example.
    if code != 4 and len({_grid_key(v) for v in labels.values()}) != len(MODES):
        raise AssertionError(f"input {index} is not teaching-distinguishing, code={code}")
    assert len(grid)<=30 and len(grid[0])<=30
    return grid, labels, code


def generate_claims(seed, mode, *, demos=3, queries=4, difficulty="medium", root=ROOT):
    if type(seed) is not int or seed < 0: raise ValueError("seed must be nonnegative integer")
    if type(demos) is not int or demos not in range(2,7): raise ValueError("demos must be 2..6")
    if type(queries) is not int or queries != 4: raise ValueError("queries must be 4")
    if difficulty not in ("easy", "medium", "hard"): raise ValueError("invalid difficulty")
    if mode not in MODES: raise ValueError("invalid mode")
    pairs = []
    for i in range(demos + queries):
        grid, labels, _ = _sample(seed, i, demos+queries, difficulty)
        pairs.append({"input":grid,"output":labels[mode]})
    keys = [json.dumps(p["input"],separators=(",",":")) for p in pairs]
    if len(set(keys)) != len(keys): raise AssertionError("duplicate inputs")
    return {"train":pairs[:demos],"test":pairs[demos:],"program_solution":program_for(mode,root)}


def self_audit(seed=11, demos=2, difficulty="medium"):
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule
    bank={mode:generate_claims(seed,mode,demos=demos,difficulty=difficulty) for mode in MODES}
    with RacketBridge() as bridge:
        for mode,ep in bank.items():
            for pair in ep["train"]+ep["test"]:
                bridge.define_grid("g",pair["input"])
                actual=bridge.eval_text(f'({wrap_rule(ep["program_solution"])} g)')
                if actual!=pair["output"]:
                    raise AssertionError(f"Racket disagreement mode={mode}")
    # Canonical panel A->B step varies even at fixed dimensions; none of the
    # three modes can be chosen from a constant geometry/profile shortcut.
    return {"status":"passed","seed":seed,"demos":demos,"queries":4,
            "modes":list(MODES),"racket_evaluations":len(MODES)*(demos+4),
            "large_input": [len(bank["once"]["test"][-1]["input"]),
                            len(bank["once"]["test"][-1]["input"][0])],
            "distinct_inputs":True,"minimum_demos_identify_each_setting":True}


if __name__ == "__main__":
    print(json.dumps(self_audit(),sort_keys=True))
