"""Boolean composition then optional component selection; Racket verifies labels."""
from __future__ import annotations
from functools import lru_cache
from itertools import permutations
import copy
import hashlib
import json
from pathlib import Path
import random

HOME = Path(__file__).resolve().parent
CANONICAL = (HOME / "canonical.rkt").read_text()
POLICIES = ("all", "largest")
CONTROLS = (3, 4, 6)
OPS = {3: "union", 4: "inter", 6: "xor"}


def validate_settings(settings):
    if (type(settings) is not dict or set(settings) != {"component_policy"}
            or type(settings["component_policy"]) is not str
            or settings["component_policy"] not in POLICIES):
        raise ValueError("settings must contain exactly component_policy=all|largest")
    return dict(settings)


def _integer(value, name, lo, hi):
    if type(value) is not int or not lo <= value <= hi:
        raise ValueError(f"{name} must be an exact integer in {lo}..{hi}")
    return value


def _norm(cells):
    if not cells:
        return set()
    r0, c0 = min(r for r, c in cells), min(c for r, c in cells)
    return {(r-r0, c-c0) for r, c in cells}


def _cells(grid, color):
    return {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == color}


def _components(cells, diagonal=False):
    remaining, result = set(cells), []
    deltas = ((-1, 0), (1, 0), (0, -1), (0, 1))
    if diagonal:
        deltas += ((-1, -1), (-1, 1), (1, -1), (1, 1))
    while remaining:
        first = min(remaining)
        remaining.remove(first)
        component, queue = {first}, [first]
        while queue:
            r, c = queue.pop()
            for dr, dc in deltas:
                p = r+dr, c+dc
                if p in remaining:
                    remaining.remove(p)
                    component.add(p)
                    queue.append(p)
        result.append(component)
    return result


def _bbox_key(cells):
    return min(r for r, c in cells), min(c for r, c in cells), min(cells)


def _area(cells):
    return (max(r for r, c in cells)-min(r for r, c in cells)+1) * (
        max(c for r, c in cells)-min(c for r, c in cells)+1)


def _render(cells):
    cells = _norm(cells)
    if not cells:
        return [[0]]
    grid = [[0] * (max(c for r, c in cells)+1) for _ in range(max(r for r, c in cells)+1)]
    for r, c in cells:
        grid[r][c] = 8
    return grid


def intermediate(grid, *, operation=None, absolute=False):
    a, b = _cells(grid, 1), _cells(grid, 2)
    if not absolute:
        a, b = _norm(a), _norm(b)
    if operation is None:
        colors = {v for row in grid for v in row}
        operation = next((OPS[c] for c in CONTROLS if c in colors), "union")
    return {"union": lambda: a | b, "inter": lambda: a & b,
            "xor": lambda: a ^ b}[operation]()


def _reference(grid, selector="all", operation=None, absolute=False, legend=None):
    if legend is not None:
        colors = {v for row in grid for v in row}
        operation = next((op for control,op in zip(CONTROLS,legend) if control in colors), "union")
    result = intermediate(grid, operation=operation, absolute=absolute)
    if selector != "all" and result:
        components = _components(result, diagonal=selector == "diagonal")
        if selector == "first":
            result = components[0]
        elif selector == "smallest":
            result = min(components, key=lambda x: (len(x), *_bbox_key(x)))
        elif selector == "bbox":
            result = min(components, key=lambda x: (-_area(x), *_bbox_key(x)))
        elif selector == "last_tie":
            result = max(components, key=lambda x: (len(x), *_bbox_key(x)))
        else:
            result = min(components, key=lambda x: (-len(x), *_bbox_key(x)))
    return _render(result)


def reference(grid, policy="all"):
    validate_settings({"component_policy": policy})
    return _reference(grid, selector=policy)


def _program(selector="all", operation=None, absolute=False, legend=None):
    if selector == "all" and operation is None and not absolute and legend is None:
        return CANONICAL
    source = CANONICAL
    if operation is not None:
        start, end = source.index("    (define op "), source.index("    (define res0")
        source = source[:start] + f"    (define op '{operation})\n" + source[end:]
    if legend is not None:
        start, end = source.index("    (define op "), source.index("    (define res0")
        branches = " ".join(f"[(not (empty? (find-color g {c}))) '{op}]" for c,op in zip(CONTROLS,legend))
        source = source[:start] + f"    (define op (cond {branches} [else 'union]))\n" + source[end:]
    if absolute:
        old = "(sort (normalize-cells (find-color g color)) cell<?)"
        new = "(for*/list ((r (range (rows g))) (c (range (cols g))) #:when (= (at g r c) color)) (list r c))"
        assert source.count(old) == 1
        source = source.replace(old, new)
    if selector != "all":
        objects = "objects-8" if selector == "diagonal" else "objects"
        choose = {
            "first": "(first pieces)",
            "smallest": "(select-object-by pieces obj-size 'min)",
            "bbox": "(select-object-by pieces (lambda (o) (* (obj-h o) (obj-w o))) 'max)",
            "last_tie": "(pick-max pieces (lambda (o) (+ (* 1000000 (obj-size o)) (* 10000 (obj-r1 o)) (* 100 (obj-c1 o)) (second (first (sort (obj-cells o) cell<?))))))",
        }.get(selector, "(select-object-by pieces obj-size 'max)")
        old = "    (define res (sort (normalize-cells res0) cell<?))"
        new = f"""    (define raw (sort (normalize-cells res0) cell<?))
    (define res
      (if (empty? raw) '()
          (let* ((bb (bbox-of-cells raw))
                 (mask (paint-cells (empty-grid (+ 1 (third bb)) (+ 1 (fourth bb)) 0) raw 8))
                 (pieces ({objects} mask 0))
                 (chosen {choose}))
            (sort (normalize-cells (obj-cells chosen)) cell<?))))"""
        assert source.count(old) == 1
        source = source.replace(old, new)
    return "(rule!\n (lambda (g)\n" + source[len("(rule!"):-1].strip() + "))"


def program(settings):
    return _program(validate_settings(settings)["component_policy"])


def rival_specs(policy):
    validate_settings({"component_policy": policy})
    rivals = {"other_policy": {"selector": "largest" if policy == "all" else "all"}}
    for operation in ("union", "inter", "xor"):
        rivals["fixed_" + operation] = {"selector": policy, "operation": operation}
    rivals["absolute_coordinates"] = {"selector": policy, "absolute": True}
    for mapping in permutations(("union", "inter", "xor")):
        if mapping != ("union", "inter", "xor"):
            rivals["legend_" + "_".join(mapping)] = {"selector":policy, "legend":mapping}
    if policy == "largest":
        for selector in ("smallest", "first", "bbox", "diagonal", "last_tie"):
            rivals[selector] = {"selector": selector}
    return rivals


def rival_programs(policy):
    return {name: _program(**spec) for name, spec in rival_specs(policy).items()}


def _rng(seed, domain, index=0):
    digest = hashlib.sha256(f"fb7f02aa9ab0-parametric-v1:{seed}:{domain}:{index}".encode()).digest()
    return random.Random(int.from_bytes(digest, "big"))


def _grow(start, universe, size, rng):
    result = set(start)
    while len(result) < size:
        frontier = sorted({(r+dr, c+dc) for r, c in result
                           for dr, dc in ((1,0),(-1,0),(0,1),(0,-1))
                           if (r+dr, c+dc) in universe} - result)
        if not frontier:
            break
        result.add(rng.choice(frontier))
    return result


def _masks(rng, sh, sw, kind):
    universe = {(r, c) for r in range(sh) for c in range(sw)}
    if kind == "growth":
        start = {(0,0)}
        if rng.randrange(2):
            universe.remove((0,0))
            start = {(0,1),(1,0),(1,1)}
        core = _grow(start, universe, rng.randint(len(start), max(len(start), len(universe)//3)), rng)
        a = _grow(core, universe, rng.randint(len(core)+1, max(len(core)+1, len(universe)*3//4)), rng)
        b = _grow(core, universe, rng.randint(len(core)+1, max(len(core)+1, len(universe)*3//4)), rng)
        relation = rng.randrange(5)
        if relation == 0:
            b |= a
        elif relation == 1:
            a |= b
        if a == b:
            a = _grow(a, universe, min(len(universe), len(a)+1), rng)
        return _norm(a), _norm(b)
    # Each operand connects shared rails with a different end corridor. Their
    # intersection can split into irregular components and diagonal contacts.
    left = {(r,0) for r in range(sh)}
    right = {(r,sw-1) for r in range(sh)}
    for r in range(1, sh-1):
        if rng.randrange(3):
            left |= {(r,c) for c in range(1, rng.randint(1, max(1, (sw-1)//2))+1)}
        if rng.randrange(3):
            right |= {(r,c) for c in range(sw-rng.randint(1, max(1, (sw-1)//2))-1,sw-1)}
    common = left | right
    a = common | {(0,c) for c in range(sw)}
    b = common | {(sh-1,c) for c in range(sw)}
    for c in range(1, sw-1):
        if rng.randrange(2):
            a |= {(r,c) for r in range(1, rng.randint(1,max(1,(sh-1)//3))+1)}
        if rng.randrange(2):
            b |= {(r,c) for r in range(sh-rng.randint(1,max(1,(sh-1)//3))-1,sh-1)}
    return a, b


def _orient(cells, sh, sw, flip_r, flip_c):
    return {(sh-1-r if flip_r else r, sw-1-c if flip_c else c) for r,c in cells}


def make_input(seed, index, control, *, height=None, width=None, kind=None):
    """Deterministic lawful inputs; 30x30 uses full-height operand structure."""
    rng = _rng(seed, "input", index)
    h = height if height is not None else rng.randint(8, 22)
    w = width if width is not None else rng.randint(11, 26)
    _integer(h, "height", 8, 30)
    _integer(w, "width", 11, 30)
    transpose = h >= 11 and bool(rng.randrange(2))
    if transpose:
        h, w = w, h
    if type(control) is not int or control not in CONTROLS:
        raise ValueError("control must be 3,4,6")
    kind = kind or ("growth" if index % 3 == 0 else "rails")
    if kind not in {"growth", "rails"}:
        raise ValueError("kind must be growth or rails")
    sh, sw = h-2, (w-3)//2
    if h != 30 or w != 30:
        sh = rng.randint(4, sh)
        sw = rng.randint(3, sw)
    a, b = _masks(rng, sh, sw, kind)
    fr, fc = bool(rng.randrange(2)), bool(rng.randrange(2))
    a = _norm(_orient(a, sh, sw, fr, fc))
    b = _norm(_orient(b, sh, sw, fr, fc))
    grid = [[0]*w for _ in range(h)]
    if rng.randrange(2):
        a, b = b, a
    for color, cells, left, right in ((1,a,0,(w-3)//2), (2,b,(w+1)//2,w)):
        bh, bw = max(r for r,c in cells)+1, max(c for r,c in cells)+1
        r0 = rng.randrange(h-bh+1)
        c0 = rng.randint(left, right-bw)
        for r,c in cells:
            grid[r+r0][c+c0] = color
    corners = [(0,0),(0,w-1),(h-1,0),(h-1,w-1)]
    rng.shuffle(corners)
    for r,c in corners:
        if grid[r][c] == 0:
            grid[r][c] = control
            return [list(row) for row in zip(*grid)] if transpose else grid
    raise RuntimeError("no free control corner")


def _fingerprint(grid):
    return json.dumps(grid, separators=(",", ":"))


def _survivors(train, policy):
    return {name: spec for name,spec in rival_specs(policy).items()
            if all(_reference(g, **spec) == reference(g,policy) for g in train)}


@lru_cache(maxsize=64)
def _inputs(seed, demos):
    # Select against both settings; private settings cannot leak through inputs.
    # No query is read during this demonstration-only teaching selection.
    controls = list(CONTROLS)
    _rng(seed, "control-order").shuffle(controls)
    best = None
    for attempt in range(8):
        train, seen = [], set()
        alive = {p: rival_specs(p) for p in POLICIES}
        for slot in range(demos):
            control = controls[slot % 3]
            candidates = []
            for candidate in range(48):
                g = make_input(seed, attempt*10000+slot*100+candidate, control)
                if _fingerprint(g) in seen:
                    continue
                expected = {p: reference(g,p) for p in POLICIES}
                killed = {p: {name for name,spec in alive[p].items()
                              if _reference(g, **spec) != expected[p]} for p in POLICIES}
                score = sum(len(v) for v in killed.values())
                fragments = min(4, len(_components(intermediate(g))))
                candidates.append(((score, fragments), g, killed))
            if not candidates:
                raise RuntimeError("no distinct teaching candidate")
            _, chosen, killed = max(candidates, key=lambda row: row[0])
            train.append(chosen)
            seen.add(_fingerprint(chosen))
            for p in POLICIES:
                for name in killed[p]:
                    alive[p].pop(name)
        residual = sum(len(v) for v in alive.values())
        if best is None or residual < best[0]:
            best = residual, train, alive
        if residual == 0:
            break
    if best[0]:
        raise RuntimeError(f"bounded teaching construction failed: {best[2]}")
    train = best[1]
    seen = {_fingerprint(g) for g in train}
    queries = []
    for index in range(4):
        control = controls[index % 3] if index < 3 else (4,6)[seed % 2]
        for retry in range(32):
            number = 100000+100*index+retry
            kwargs = {"height":30, "width":30, "kind":"rails"} if index == 3 else {}
            g = make_input(seed, number, control, **kwargs)
            if _fingerprint(g) not in seen:
                queries.append(g)
                seen.add(_fingerprint(g))
                break
        else:
            raise RuntimeError("bounded novel-query construction failed")
    return train, queries


def generate(seed, settings, demos=3, queries=4):
    policy = validate_settings(settings)["component_policy"]
    _integer(seed, "seed", 0, 2**63-1)
    _integer(demos, "demos", 3, 6)
    _integer(queries, "queries", 1, 4)
    train, test = _inputs(seed, demos)
    def pairs(grids):
        return [{"input":copy.deepcopy(g), "output":reference(g,policy)} for g in grids]
    return {"train":pairs(train), "test":pairs(test[:queries]), "program_solution":program(settings)}
