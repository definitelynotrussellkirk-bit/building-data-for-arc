"""Native, finite marker-lattice family with an object-derived spacing rule.

The canonical program and period-three variant come from the adjacent reviewed
prototype.  The third setting traces east from the marker, measures the first
hit's four-connected gray component, then uses its size plus one as spacing.
All settings share the same bounded input sampler.  Python labels are claims;
native qualification independently executes every retained label in Racket.
"""
from __future__ import annotations

from collections import deque
from copy import deepcopy
from functools import lru_cache
import hashlib
import importlib.util
import json
from pathlib import Path
import random

TASK_ID = "c9034f0626e0"
VERSION = "native-ray-component-v1"
SETTINGS = ("period_2", "period_3", "ray_component")
MAX_ATTEMPTS = 32
QUERY_SHAPES = ((13, 13), (17, 21), (24, 27), (30, 30))


def _adjacent(name):
    path = Path(__file__).resolve().with_name(name + ".py")
    spec = importlib.util.spec_from_file_location(
        "_lattice_" + name + "_" + hashlib.sha256(str(path).encode()).hexdigest(), path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_prototype = _adjacent("prototype")


def _setting(settings):
    if (type(settings) is not dict or set(settings) != {"spacing_rule"}
            or type(settings["spacing_rule"]) is not str
            or settings["spacing_rule"] not in SETTINGS):
        raise ValueError("settings must name exactly one supported spacing_rule")
    return settings["spacing_rule"]


def _racket(period, *, connectivity=4, target=None, hit=None, predicate=None,
            row_phase="mr", col_phase="mc", output_color="color"):
    objects = "objects" if connectivity == 4 else "objects-8"
    hit = hit or "(first (filter (lambda (c) (= (at g mr c) 5)) (range (+ mc 1) w)))"
    target = target or "(first (filter (lambda (o) (member (list mr hit) (obj-cells o))) gray))"
    predicate = predicate or (
        f"(and (= (remainder r period) (remainder {row_phase} period)) "
        f"(= (remainder c period) (remainder {col_phase} period)) (zero? (at g r c)))")
    return f"""(rule! (lambda (g)
  (let* ((h (rows g)) (w (cols g))
         (objs ({objects} g 0))
         (marker (first (filter (lambda (o) (!= (obj-color o) 5)) objs)))
         (mr (first (first (obj-cells marker))))
         (mc (second (first (obj-cells marker))))
         (color (obj-color marker))
         (gray (filter (lambda (o) (= (obj-color o) 5)) objs))
         (hit {hit})
         (target {target})
         (period {period}))
    (build-grid h w (r c) (if {predicate} {output_color} (at g r c))))))"""


def program(settings):
    selected = _setting(settings)
    if selected in ("period_2", "period_3"):
        return _prototype.rule_source(int(selected[-1]))
    return _racket("(+ 1 (obj-size target))")


def _component(grid, start, connectivity=4):
    h, w = len(grid), len(grid[0])
    color = grid[start[0]][start[1]]
    found, queue = {start}, deque([start])
    deltas = ((-1, 0), (1, 0), (0, -1), (0, 1))
    if connectivity == 8:
        deltas += ((-1, -1), (-1, 1), (1, -1), (1, 1))
    while queue:
        r, c = queue.popleft()
        for dr, dc in deltas:
            p = (r + dr, c + dc)
            if (0 <= p[0] < h and 0 <= p[1] < w and p not in found
                    and grid[p[0]][p[1]] == color):
                found.add(p)
                queue.append(p)
    return found


def _gray_components(grid):
    pending = {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 5}
    result = []
    while pending:
        cells = _component(grid, min(pending))
        pending.difference_update(cells)
        result.append(cells)
    return result


def intermediate(grid):
    h, w = _prototype._validate_grid(grid)
    if h > 30 or w > 30:
        raise ValueError("ARC dimensions must not exceed 30")
    mr, mc, color = _prototype._find_marker(grid)
    hits = [(mr, c) for c in range(mc + 1, w) if grid[mr][c] == 5]
    if not hits:
        raise ValueError("admitted input needs a gray hit east of the marker")
    hit = hits[0]
    cells = _component(grid, hit)
    return {"marker": [mr, mc], "marker_color": color, "hit": list(hit),
            "component_cells": [list(p) for p in sorted(cells)],
            "component_size": len(cells), "period": len(cells) + 1}


def _paint(grid, period, *, mode="both", phase=None, color=None):
    mr, mc, marker_color = _prototype._find_marker(grid)
    rp, cp = (mr, mc) if phase is None else phase
    color = marker_color if color is None else color
    result = deepcopy(grid)
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            row_ok, col_ok = r % period == rp % period, c % period == cp % period
            matches = {"both": row_ok and col_ok, "row": row_ok, "column": col_ok,
                       "sum": (r + c) % period == (rp + cp) % period,
                       "all": True, "overwrite": row_ok and col_ok}[mode]
            if matches and (value == 0 or mode == "overwrite"):
                result[r][c] = color
    return result


def solve(grid, spacing_rule):
    if spacing_rule not in SETTINGS:
        raise ValueError("unknown spacing rule")
    if spacing_rule == "ray_component":
        period = intermediate(grid)["period"]
    else:
        _prototype._validate_grid(grid)
        period = int(spacing_rule[-1])
    return _paint(grid, period)


def _rng(seed, stream):
    digest = hashlib.sha256(f"{VERSION}:{seed}:{stream}".encode()).digest()
    return random.Random(int.from_bytes(digest[:16], "big"))


def _scene(rng, shape, target_size, color):
    h, w = shape
    mr = rng.randrange(2, h - 4)
    mc = rng.randrange(1, max(2, w // 3))
    hc = min(mc + rng.randrange(3, 7), w - 6)
    if hc <= mc + 1:
        hc = mc + 2
    shapes = {
        1: [(0, 0)],
        2: [(0, 0), (1, 0)],
        3: rng.choice([[(0, 0), (1, 0), (1, 1)], [(0, 0), (0, 1), (1, 0)]]),
        4: rng.choice([[(0, 0), (1, 0), (1, 1), (2, 0)],
                       [(0, 0), (0, 1), (1, 0), (1, 1)]]),
        # A compact pentomino gives size+1 = 6 but bbox height+width = 5.
        # Every minimum lesson includes it, so bbox semiperimeter cannot replace
        # component cardinality. Both orientations preserve an eastward hit.
        5: rng.choice([[(0, 0), (0, 1), (1, 0), (1, 1), (1, 2)],
                       [(0, 0), (0, 1), (1, 1), (2, 0), (2, 1)]]),
    }
    target = {(mr + r, hc + c) for r, c in shapes[target_size]}
    nearby = {(mr - 1, mc)}
    farther = {(mr, w - 2)}
    # A diagonally touching gray cell separates 4- and 8-connectivity. It may
    # belong to the dense surround, but never to the selected 4-component.
    diagonal = {(max(r for r, _ in target) + 1, max(c for _, c in target) + 1)}
    forced = target | nearby | farther | diagonal
    clear = {(mr, c) for c in range(mc + 1, hc)} | {(mr, w - 1)}
    # Retain a connected open field around the marker and ray, as in the source
    # family; the remainder of the full canvas carries dense gray fragments.
    clear |= {(r, c) for r in range(max(0, mr - 1), min(h, mr + 3))
              for c in range(max(0, mc - 1), min(w, hc + 2))}
    for component in (target, nearby, farther):
        for r, c in component:
            clear |= {(r + dr, c + dc) for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))}
    clear.add((mr, mc))
    clear.difference_update(forced)
    gray = set(forced)
    for point in ((0, 0), (0, w - 1), (h - 1, 0), (h - 1, w - 1)):
        if point not in clear:
            gray.add(point)
    candidates = [(r, c) for r in range(h) for c in range(w)
                  if (r, c) not in gray and (r, c) not in clear]
    rng.shuffle(candidates)
    gray_count = rng.randrange((h * w * 30) // 100, (h * w * 43) // 100)
    gray.update(candidates[:max(0, gray_count - len(gray))])
    grid = [[5 if (r, c) in gray else 0 for c in range(w)] for r in range(h)]
    grid[mr][mc] = color
    observed = intermediate(grid)
    if observed["component_size"] != target_size or observed["hit"] != [mr, hc]:
        raise RuntimeError("constructed ray/component grammar violated")
    return grid


def _rival_specs(grid, selected):
    info = intermediate(grid)
    mr, mc = info["marker"]
    period = info["period"] if selected == "ray_component" else int(selected[-1])
    specs = {f"fixed_{p}": (p, {}) for p in range(1, 7)}
    specs.update({name: (period, {"mode": name}) for name in ("row", "column", "sum", "all", "overwrite")})
    specs.update({"origin": (period, {"phase": (0, 0)}),
                  "swapped_phase": (period, {"phase": (mc, mr)}),
                  "fixed_color_1": (period, {"color": 1}),
                  "fixed_color_5": (period, {"color": 5}),
                  "ray_component": (info["period"], {})})
    if selected == "ray_component":
        cells = [tuple(p) for p in info["component_cells"]]
        rs, cs = zip(*cells)
        components = _gray_components(grid)
        nearest = min(components, key=lambda comp: min(abs(r - mr) + abs(c - mc) for r, c in comp))
        last = max(c for c in range(mc + 1, len(grid[0])) if grid[mr][c] == 5)
        run = 0
        for c in range(info["hit"][1], len(grid[0])):
            if grid[mr][c] != 5:
                break
            run += 1
        specs.update({
            "size_without_one": (len(cells), {}),
            "bbox_area": ((max(rs) - min(rs) + 1) * (max(cs) - min(cs) + 1) + 1, {}),
            "bbox_semiperimeter": (max(rs) - min(rs) + max(cs) - min(cs) + 2, {}),
            "eight_connected": (len(_component(grid, tuple(info["hit"]), 8)) + 1, {}),
            "nearest_component": (len(nearest) + 1, {}),
            "largest_component": (max(map(len, components)) + 1, {}),
            "smallest_component": (min(map(len, components)) + 1, {}),
            "last_hit": (len(_component(grid, (mr, last))) + 1, {}),
            "ray_distance": (info["hit"][1] - mc, {}),
            "row_run": (run + 1, {}),
            "marker_color": (info["marker_color"], {}),
            "all_gray_count": (sum(map(len, components)) + 1, {}),
        })
    return specs


def rivals(grid, selected):
    result = {name: _paint(grid, p, **options)
              for name, (p, options) in _rival_specs(grid, selected).items()}
    result["identity"] = deepcopy(grid)
    return result


def teaching_check(episode):
    selected = _setting(episode.get("settings"))
    train, test = episode.get("train", []), episode.get("test", [])
    if not 2 <= len(train) <= 6 or not 1 <= len(test) <= 4:
        return ["unsupported demonstration/query counts"]
    errors = []
    for pair in train + test:
        if solve(pair["input"], selected) != pair["output"]:
            errors.append("label does not match the selected rule")
    if errors:
        return errors
    demo_rivals = [rivals(pair["input"], selected) for pair in train]
    survivors = [name for name in demo_rivals[0]
                 if all(rows[name] == pair["output"] for rows, pair in zip(demo_rivals, train))]
    # No query answer is used to fit a rival. Queries only determine whether a
    # demonstration survivor would be harmful, including a wrong larger-size rule.
    for pair in test:
        predictions = rivals(pair["input"], selected)
        errors.extend(name + " fits demonstrations but changes a query"
                      for name in survivors if predictions[name] != pair["output"])
    return sorted(set(errors))


@lru_cache(maxsize=64)
def _sample(seed):
    for attempt in range(MAX_ATTEMPTS):
        rng = _rng(seed, "inputs:" + str(attempt))
        first_sizes = [2, 5]
        rng.shuffle(first_sizes)
        demo_sizes = first_sizes + [3, 1, 4, rng.choice([1, 2, 3, 4, 5])]
        query_sizes = [1, 3, 4, 5]
        rng.shuffle(query_sizes)
        palette_low, palette_high = [1, 2, 3, 4], [6, 7, 8, 9]
        rng.shuffle(palette_low)
        rng.shuffle(palette_high)
        colors = [palette_low[0], palette_high[0]]
        rng.shuffle(colors)
        colors += [rng.choice(palette_low + palette_high) for _ in range(8)]
        demo_shapes = [(13, 13), (13, 16), (15, 17), (17, 21), (24, 27), (30, 30)]
        first_shapes = demo_shapes[:2]
        rng.shuffle(first_shapes)
        demo_shapes[:2] = first_shapes
        demo_inputs = [_scene(rng, shape, n, colors[i])
                       for i, (shape, n) in enumerate(zip(demo_shapes, demo_sizes))]
        query_inputs = [_scene(rng, shape, n, colors[i + 6])
                        for i, (shape, n) in enumerate(zip(QUERY_SHAPES, query_sizes))]
        if len({json.dumps(g) for g in demo_inputs + query_inputs}) != 10:
            continue
        valid = True
        for selected in SETTINGS:
            episode = {"settings": {"spacing_rule": selected},
                       "train": [{"input": g, "output": solve(g, selected)} for g in demo_inputs[:2]],
                       "test": [{"input": g, "output": solve(g, selected)} for g in query_inputs]}
            if teaching_check(episode):
                valid = False
                break
        if valid:
            return demo_inputs, query_inputs, attempt + 1
    raise RuntimeError(f"no identifiable lesson in {MAX_ATTEMPTS} bounded attempts for seed {seed}")


def generate(seed, settings, demos=3, queries=4):
    selected = _setting(settings)
    for name, value, low, high in (("seed", seed, 0, 2**63 - 1),
                                    ("demos", demos, 2, 6), ("queries", queries, 1, 4)):
        if type(value) is not int or not low <= value <= high:
            raise ValueError(f"{name} must be a literal integer in [{low}, {high}]")
    demo_inputs, query_inputs, attempts = _sample(seed)
    return {"train": [{"input": deepcopy(g), "output": solve(g, selected)} for g in demo_inputs[:demos]],
            "test": [{"input": deepcopy(g), "output": solve(g, selected)} for g in query_inputs[:queries]],
            "program_solution": program(settings), "settings": dict(settings),
            "seed": seed, "sampling_attempts": attempts}


def public_turn(episode, query_index=0):
    queries = episode["test"]
    if type(query_index) is not int or not 0 <= query_index < len(queries):
        raise ValueError("query_index must select one existing query")
    return {"train": [{"input": deepcopy(pair["input"]), "output": deepcopy(pair["output"])}
                      for pair in episode["train"]],
            "test": [{"input": deepcopy(queries[query_index]["input"])}]}


def rival_program(name, selected):
    """Executable counterparts to the bounded Python self-audit rivals."""
    period = "(+ 1 (obj-size target))" if selected == "ray_component" else selected[-1]
    if name.startswith("fixed_") and name[6:].isdigit():
        return _racket(name[6:])
    if name == "identity":
        return "(rule! (lambda (g) g))"
    if name == "ray_component":
        return program({"spacing_rule": "ray_component"})
    predicates = {
        "row": "(and (zero? (at g r c)) (= (remainder r period) (remainder mr period)))",
        "column": "(and (zero? (at g r c)) (= (remainder c period) (remainder mc period)))",
        "sum": "(and (zero? (at g r c)) (= (remainder (+ r c) period) (remainder (+ mr mc) period)))",
        "all": "(zero? (at g r c))",
        "overwrite": "(and (= (remainder r period) (remainder mr period)) (= (remainder c period) (remainder mc period)))",
    }
    if name in predicates:
        return _racket(period, predicate=predicates[name])
    if name == "origin":
        return _racket(period, row_phase="0", col_phase="0")
    if name == "swapped_phase":
        return _racket(period, row_phase="mc", col_phase="mr")
    if name in ("fixed_color_1", "fixed_color_5"):
        return _racket(period, output_color=name[-1])
    if name == "size_without_one":
        return _racket("(obj-size target)")
    if name == "bbox_area":
        return _racket("(+ 1 (* (+ 1 (- (third (obj-bbox target)) (first (obj-bbox target)))) (+ 1 (- (fourth (obj-bbox target)) (second (obj-bbox target))))))")
    if name == "bbox_semiperimeter":
        return _racket("(+ 2 (- (third (obj-bbox target)) (first (obj-bbox target))) (- (fourth (obj-bbox target)) (second (obj-bbox target))))")
    if name == "eight_connected":
        return _racket(period, connectivity=8)
    if name == "nearest_component":
        distance = "(lambda (o) (apply min (map (lambda (p) (+ (abs (- (first p) mr)) (abs (- (second p) mc)))) (obj-cells o))))"
        return _racket(period, target=f"(first (sort gray (lambda (a b) (< ({distance} a) ({distance} b)))))")
    if name in ("largest_component", "smallest_component"):
        op = ">" if name == "largest_component" else "<"
        return _racket(period, target=f"(first (sort gray (lambda (a b) ({op} (obj-size a) (obj-size b)))))")
    if name == "last_hit":
        return _racket(period, hit="(last (filter (lambda (c) (= (at g mr c) 5)) (range (+ mc 1) w)))")
    if name == "ray_distance":
        return _racket("(- hit mc)")
    if name == "row_run":
        # Count the consecutive gray prefix; later gray cells after a zero do
        # not belong to the run even if they belong to the same component.
        return _racket("(+ 1 (length (takef (range hit w) (lambda (c) (= (at g mr c) 5)))))")
    if name == "marker_color":
        return _racket("color")
    if name == "all_gray_count":
        return _racket("(+ 1 (apply + (map obj-size gray)))")
    raise ValueError("unknown rival: " + name)
