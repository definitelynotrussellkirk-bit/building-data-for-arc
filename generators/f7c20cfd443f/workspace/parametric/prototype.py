"""Separate, finite halo-selection family; Python labels are claims until Racket replay.

The first two constructive demonstrations teach morphology and selection jointly.
All settings use identical input streams, including count-stable query prefixes.
"""
from __future__ import annotations

from copy import deepcopy
import random
from pathlib import Path

SELECTIONS = ("all", "largest", "smallest")
CANONICAL = Path(__file__).with_name("canonical.rkt").read_text()
_DILATE = " ".join(CANONICAL.split())[len("(rule! "):-1]


def _integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _selection(settings):
    if type(settings) is not dict or set(settings) != {"selection"}:
        raise ValueError("settings must contain exactly selection")
    value = settings["selection"]
    if type(value) is not str or value not in SELECTIONS:
        raise ValueError("selection must be all, largest, or smallest")
    return value


def validate_grid(grid):
    """Admitted extension grammar: 7..30, black and isolated singleton gray seeds."""
    if (type(grid) is not list or not 7 <= len(grid) <= 30
            or type(grid[0]) is not list or not 7 <= len(grid[0]) <= 30):
        raise ValueError("input dimensions must be 7..30")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width
           or any(type(v) is not int or v not in (0, 5) for v in row) for row in grid):
        raise ValueError("input must be rectangular exact 0/5 integer cells")
    seeds = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 5]
    if not seeds or len(seeds) == len(grid) * width:
        raise ValueError("input needs gray seeds and black background")
    occupied = set(seeds)
    if any((r + dr, c + dc) in occupied for r, c in seeds
           for dr in (-1, 0, 1) for dc in (-1, 0, 1) if dr or dc):
        raise ValueError("gray seeds must be isolated under 8-connectivity")
    return grid


def components(grid, connectivity=4):
    remaining = {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v}
    steps = [(dr, dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1)
             if (dr or dc) and (connectivity == 8 or abs(dr) + abs(dc) == 1)]
    result = []
    while remaining:
        first = min(remaining)
        remaining.remove(first)
        found, stack = {first}, [first]
        while stack:
            r, c = stack.pop()
            for dr, dc in steps:
                cell = r + dr, c + dc
                if cell in remaining:
                    remaining.remove(cell)
                    found.add(cell)
                    stack.append(cell)
        result.append(found)
    return result


def dilate(grid, morphology="canonical"):
    h, w = len(grid), len(grid[0])
    seeds = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 5]
    if morphology == "ignore_edge":
        seeds = [(r, c) for r, c in seeds if 0 < r < h - 1 and 0 < c < w - 1]
    if morphology == "ignore_overlap":
        seeds = [s for s in seeds if not any(s != t and max(abs(s[0]-t[0]), abs(s[1]-t[1])) <= 2 for t in seeds)]
    out = [[0] * w for _ in range(h)]
    for r, c in seeds:
        if morphology == "aligned_macrocell":
            cells = [(3*(r//3)+dr, 3*(c//3)+dc) for dr in range(3) for dc in range(3)]
        else:
            cells = [(r+dr, c+dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1)
                     if morphology != "orthogonal" or abs(dr)+abs(dc) <= 1]
        for rr, cc in cells:
            if 0 <= rr < h and 0 <= cc < w:
                out[rr][cc] = 1
    return out


def transform(grid, selection, *, morphology="canonical", connectivity=4,
              metric="area", one_tie=False, preserve_centers=False):
    if selection not in SELECTIONS:
        raise ValueError("unknown selection")
    expanded = dilate(grid, morphology)
    groups = components(expanded, connectivity)
    if selection != "all" and groups:
        def score(cells):
            seed_count = sum(grid[r][c] == 5 for r, c in cells)
            if metric == "seed_count":
                return seed_count
            if metric == "new_cells":
                return len(cells) - seed_count
            if metric == "bbox":
                rs, cs = zip(*cells)
                return (max(rs)-min(rs)+1) * (max(cs)-min(cs)+1)
            return len(cells)
        target = (max if selection == "largest" else min)(map(score, groups))
        selected = [cells for cells in groups if score(cells) == target]
        if one_tie:
            selected = selected[:1]
        expanded = [[0] * len(grid[0]) for _ in grid]
        for cells in selected:
            for r, c in cells:
                expanded[r][c] = 1
    if preserve_centers:
        expanded = [[5 if v and grid[r][c] == 5 else v for c, v in enumerate(row)]
                    for r, row in enumerate(expanded)]
    return expanded


def _select_racket(expression, selection, *, connectivity=4, metric="area", one_tie=False, color=1):
    if selection == "all":
        return expression
    score = {
        "area": "(obj-size obj)",
        "bbox": "(* (+ 1 (- (obj-r2 obj) (obj-r1 obj))) (+ 1 (- (obj-c2 obj) (obj-c1 obj))))",
        "seed_count": "(for/sum ((p (in-list (obj-cells obj)))) (if (= 5 (at g (first p) (second p))) 1 0))",
        "new_cells": "(- (obj-size obj) (for/sum ((p (in-list (obj-cells obj)))) (if (= 5 (at g (first p) (second p))) 1 0)))",
    }[metric]
    aggregate = "max" if selection == "largest" else "min"
    finder = "objects-8" if connectivity == 8 else "objects"
    chosen = "(take winners 1)" if one_tie else "winners"
    return f"""(let* ((expanded {expression}) (groups ({finder} expanded 0)))
      (if (null? groups) expanded
        (let* ((score (lambda (obj) {score}))
               (target (apply {aggregate} (map score groups)))
               (winners (filter (lambda (obj) (= (score obj) target)) groups)))
          (for/fold ((out (grid-from-fn (rows g) (cols g) (lambda (r c) 0))))
                    ((obj (in-list {chosen})))
            (paint-cells out (obj-cells obj) {color})))))"""


def _morph_racket(morphology):
    source = "g"
    if morphology == "ignore_edge":
        source = "(cellmap g (r c v) (if (and (= v 5) (> r 0) (< r (- (rows g) 1)) (> c 0) (< c (- (cols g) 1))) 5 0))"
    if morphology == "ignore_overlap":
        source = """(cellmap g (r c v)
          (if (and (= v 5) (not (for*/or ((dr (in-range -2 3)) (dc (in-range -2 3)))
            (let ((rr (+ r dr)) (cc (+ c dc)))
              (and (or (not (= dr 0)) (not (= dc 0)))
                   (>= rr 0) (< rr (rows g)) (>= cc 0) (< cc (cols g))
                   (= 5 (at g rr cc))))))) 5 0))"""
    if morphology == "aligned_macrocell":
        return """(grid-from-fn (rows g) (cols g) (lambda (r c)
          (if (for*/or ((dr (in-range 3)) (dc (in-range 3)))
            (let ((rr (+ (* 3 (quotient r 3)) dr)) (cc (+ (* 3 (quotient c 3)) dc)))
              (and (< rr (rows g)) (< cc (cols g)) (= 5 (at g rr cc))))) 1 0)))"""
    fn = _DILATE
    if morphology == "orthogonal":
        fn = fn.replace("(and (>= nr 0)", "(and (<= (+ (abs dr) (abs dc)) 1) (>= nr 0)")
    return f"({fn} {source})"


def program(settings):
    selection = _selection(settings)
    if selection == "all":
        return CANONICAL
    return "(rule! (lambda (g) " + _select_racket(_morph_racket("canonical"), selection) + "))"


def rival_names(selection):
    names = ["aligned_macrocell", "ignore_edge", "ignore_overlap", "orthogonal", "preserve_centers"]
    if selection != "all":
        names += ["eight_connected", "bbox", "seed_count", "new_cells", "one_tie", "select_before_dilation"]
    return names


def rival_output(grid, selection, name):
    if name == "select_before_dilation":
        # Every admitted input component is a singleton: all tie before dilation.
        return dilate(grid)
    options = ({"connectivity": 8} if name == "eight_connected" else
               {"metric": name} if name in ("bbox", "seed_count", "new_cells") else
               {"one_tie": True} if name == "one_tie" else
               {"preserve_centers": True} if name == "preserve_centers" else
               {"morphology": name})
    return transform(grid, selection, **options)


def rival_program(selection, name):
    if name not in rival_names(selection):
        raise ValueError("undeclared rival")
    if name == "select_before_dilation":
        before = _select_racket("g", selection, color=5)
        return f"(rule! (lambda (g) ({_DILATE} {before})))"
    expression = _select_racket(
        _morph_racket(name), selection,
        connectivity=8 if name == "eight_connected" else 4,
        metric=name if name in ("bbox", "seed_count", "new_cells") else "area",
        one_tie=name == "one_tie")
    if name == "preserve_centers":
        expression = f"(let ((answer {expression})) (cellmap answer (r c v) (if (and (= v 1) (= 5 (at g r c))) 5 v)))"
    return f"(rule! (lambda (g) {expression}))"


def _grid(h, w, seeds):
    out = [[0] * w for _ in range(h)]
    for r, c in seeds:
        out[r][c] = 5
    return out


def _orient(grid, rng):
    if rng.randrange(2):
        grid = [row[::-1] for row in grid]
    for _ in range(rng.randrange(4)):
        grid = [list(row) for row in zip(*grid[::-1])]
    return grid


def _teaching_input(index, rng):
    if index == 0:
        h, w = rng.randint(18, 21), rng.randint(12, 16)
        # Two irregular 24-cell components touch ONLY diagonally. Their bbox
        # areas are 30, versus a dense four-seed 25-cell component's bbox 25.
        seeds = [(1, 1), (1, 3), (4, 3), (7, 6), (7, 8), (10, 8),
                 (14, 1), (14, 3), (16, 1), (16, 3)]
        dr, dc = rng.randint(0, h - 18), rng.randint(0, w - 10)
        return _orient(_grid(h, w, [(r+dr, c+dc) for r, c in seeds]), rng)
    if index == 1:
        h, w = rng.randint(18, 22), rng.randint(18, 22)
        seeds = [(0, 0), (0, 2), (2, 0), (2, 2),
                 (0, 8), (3, 8), (6, 8), (12, 2), (12, 4), (12, 7),
                 (0, w-3), (0, w-1), (h-1, w-3), (h-1, w-1), (8, w-2)]
        return _orient(_grid(h, w, seeds), rng)
    if index == 2:
        # A source-scale anchor; its meaning is already disambiguated above.
        candidates = [(r, c) for r in (1, 4, 7) for c in (1, 4, 7)]
        return _orient(_grid(9, 9, rng.sample(candidates, rng.choice((3, 4)))), rng)
    return _random_input(rng, rng.randint(10, 18), rng.randint(10, 18), rng.randint(5, 12))


def _random_input(rng, h, w, count):
    # Random sequential packing is constructive at these conservative densities.
    cells = [(r, c) for r in range(h) for c in range(w)]
    rng.shuffle(cells)
    selected, forbidden = [], set()
    for r, c in cells:
        if (r, c) in forbidden:
            continue
        selected.append((r, c))
        forbidden.update((r+dr, c+dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1))
        if len(selected) == count:
            return _grid(h, w, selected)
    raise ValueError(f"could not place {count} isolated seeds in {h}x{w}")


def _query_input(index, rng):
    if index == 0:
        h, w = rng.randint(7, 11), rng.randint(7, 11)
        return _random_input(rng, h, w, rng.randint(3, 7))
    if index == 1:
        return _random_input(rng, rng.randint(12, 18), rng.randint(19, 26), rng.randint(10, 22))
    if index == 2:
        return _random_input(rng, rng.randint(21, 29), rng.randint(21, 29), rng.randint(25, 42))
    return _random_input(rng, 30, 30, rng.randint(55, 75))


def generate(seed, settings, demos=3, queries=4):
    _integer(seed, 0, 2**63-1, "seed")
    _integer(demos, 2, 6, "demos")
    _integer(queries, 1, 4, "queries")
    selection = _selection(settings)
    seen, splits = set(), {}
    for split, count in (("train", demos), ("test", queries)):
        pairs = []
        for index in range(count):
            for retry in range(16):
                # No hidden setting or requested count affects this input RNG.
                rng = random.Random(f"f7c20cfd443f-halos-v1:{seed}:{split}:{index}:{retry}")
                grid = (_teaching_input if split == "train" else _query_input)(index, rng)
                validate_grid(grid)
                if split == "test" and index == 0:
                    # Single-query evaluation must actually require selection.
                    # This input-only condition is identical for every setting.
                    areas = {len(cells) for cells in components(dilate(grid))}
                    if len(areas) < 2:
                        continue
                key = tuple(map(tuple, grid))
                if key not in seen:
                    seen.add(key)
                    pairs.append({"input": grid, "output": transform(grid, selection)})
                    break
            else:
                raise ValueError("distinct-input retry limit exhausted")
        splits[split] = pairs
    return {**splits, "program_solution": program(settings), "settings": dict(settings), "seed": seed}


def public_turn(episode, query_index=0):
    """Pure projection for one turn; history/reveal scheduling belongs to the consumer."""
    _integer(query_index, 0, len(episode["test"])-1, "query_index")
    return deepcopy({"train": [{"input": p["input"], "output": p["output"]} for p in episode["train"]],
                     "test": [{"input": episode["test"][query_index]["input"]}]})


def teaching_check(episode):
    """Finite Python audit; audit_family.py independently executes these rivals in Racket."""
    selection = _selection(episode["settings"])
    survivors, ambiguities, eliminations = [], [], {}
    for name in rival_names(selection):
        rejected = [i for i, p in enumerate(episode["train"])
                    if rival_output(p["input"], selection, name) != p["output"]]
        if rejected:
            eliminations[name] = rejected
        else:
            survivors.append(name)
            for i, p in enumerate(episode["test"]):
                if rival_output(p["input"], selection, name) != p["output"]:
                    ambiguities.append({"rival": name, "query_index": i})
    return {"declared_rivals": rival_names(selection), "surviving_rivals": survivors,
            "query_ambiguities": ambiguities, "eliminated_by_demo": eliminations}
