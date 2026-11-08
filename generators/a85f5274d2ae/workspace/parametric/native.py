"""Native, independently counted lessons for the marker/target panel puzzle.

The fixed thresholds reuse the retained prototype.  The fourth setting first
selects the target's panel, counts its distractor cells, then uses that count
as the movement threshold.  Input sampling never depends on the setting.
"""
from __future__ import annotations

from copy import deepcopy
from functools import lru_cache
import hashlib
import importlib.util
from pathlib import Path
import random

TASK_ID = "a85f5274d2ae"
SETTINGS = (0, 1, 2, "target_panel_count")
NOISE = (1, 2, 3, 4, 8)
HERE = Path(__file__).resolve().parent


def _load_adjacent(name):
    path = HERE / name
    spec = importlib.util.spec_from_file_location(
        "_a85_" + path.stem + "_" + hashlib.sha256(str(path).encode()).hexdigest()[:12], path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_prototype = _load_adjacent("prototype.py")


@lru_cache(maxsize=1)
def _root():
    from reviewer_support import find_root
    return Path(find_root(__file__))


@lru_cache(maxsize=1)
def _generator():
    from reviewer_support import load_selected_generator
    return load_selected_generator(TASK_ID, root=_root())[0]


@lru_cache(maxsize=1)
def _canonical():
    return _prototype._canonical_program(_root())


def _setting(value):
    if (type(value) is int and value in (0, 1, 2)) or (
            type(value) is str and value == "target_panel_count"):
        return value
    raise ValueError("axis_tolerance must be 0, 1, 2, or 'target_panel_count'")


def _options(settings):
    if type(settings) is not dict or set(settings) != {"axis_tolerance"}:
        raise ValueError("settings must contain exactly axis_tolerance")
    return _setting(settings["axis_tolerance"])


def _integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be a plain integer in {low}..{high}")


def scene_facts(grid):
    errors = _generator().strict_canonical_like(grid)
    if errors:
        raise ValueError("outside panel/ring grammar: " + "; ".join(errors))
    h, w = len(grid), len(grid[0])
    marker = _prototype._positions(grid, 9)[0]
    target = _prototype._positions(grid, 6)[0]
    rows = [r for r in range(h) if all(v == 0 for v in grid[r])]
    cols = [c for c in range(w) if all(grid[r][c] == 0 for r in range(h))]
    rb, cb = [-1, *rows, h], [-1, *cols, w]
    ri, ci = sum(r < target[0] for r in rows), sum(c < target[1] for c in cols)
    bounds = (rb[ri] + 1, cb[ci] + 1, rb[ri + 1] - 1, cb[ci + 1] - 1)
    noise = [(r, c) for r in range(h) for c in range(w) if grid[r][c] in NOISE]
    selected = [(r, c) for r, c in noise
                if bounds[0] <= r <= bounds[2] and bounds[1] <= c <= bounds[3]]
    return {"marker": marker, "target": target, "separator_rows": rows,
            "separator_cols": cols, "panel_bounds": bounds, "noise_cells": noise,
            "panel_noise_cells": selected, "panel_noise_count": len(selected)}


def selected_tolerance(grid, setting):
    setting = _setting(setting)
    return scene_facts(grid)["panel_noise_count"] if setting == "target_panel_count" else setting


def _paint(grid, marker, target, row_threshold, col_threshold, *, global_gate=False):
    dr, dc = target[0] - marker[0], target[1] - marker[1]
    sign = lambda value: (value > 0) - (value < 0)
    if global_gate:
        sr, sc = (0, 0) if max(abs(dr), abs(dc)) <= row_threshold else (sign(dr), sign(dc))
    else:
        sr = 0 if abs(dr) <= row_threshold else sign(dr)
        sc = 0 if abs(dc) <= col_threshold else sign(dc)
    result = deepcopy(grid)
    result[marker[0]][marker[1]] = 5
    result[marker[0] + sr][marker[1] + sc] = 9
    result[target[0]][target[1]] = 9
    return result


def rule_mirror(grid, setting):
    setting = _setting(setting)
    if type(setting) is int:
        return _prototype.rule_mirror(grid, setting)
    facts = scene_facts(grid)
    count = facts["panel_noise_count"]
    return _paint(grid, facts["marker"], facts["target"], count, count)


# All bindings are inside the existing canonical let*, after r6/c6/r9/c9.
# Panel bounds are inferred from full separator lines, not fixed coordinates.
_PANEL_BINDINGS = """
                        (separator-rows (filter (lambda (r)
                          (for/and ((c (range w))) (= (at g r c) 0))) (range h)))
                        (separator-cols (filter (lambda (c)
                          (for/and ((r (range h))) (= (at g r c) 0))) (range w)))
                        (row-low (for/fold ((v -1)) ((r separator-rows))
                          (if (< r r6) (max v r) v)))
                        (row-high (for/fold ((v h)) ((r separator-rows))
                          (if (> r r6) (min v r) v)))
                        (col-low (for/fold ((v -1)) ((c separator-cols))
                          (if (< c c6) (max v c) v)))
                        (col-high (for/fold ((v w)) ((c separator-cols))
                          (if (> c c6) (min v c) v)))
                        (noise? (lambda (v) (or (= v 1) (= v 2) (= v 3) (= v 4) (= v 8))))
                        (panel-count (for*/sum ((r (range (+ row-low 1) row-high))
                                               (c (range (+ col-low 1) col-high)))
                          (if (noise? (at g r c)) 1 0)))"""


def _with_panel_count(canonical):
    anchor = "(c6 (second p6))"
    if canonical.count(anchor) != 1:
        raise ValueError("canonical target binding changed")
    return canonical.replace(anchor, anchor + _PANEL_BINDINGS, 1)


def _axis_program(row_threshold, col_threshold, *, panel=False, global_gate=False):
    result = _with_panel_count(_canonical()) if panel else _canonical()
    if global_gate:
        for axis in ("dr", "dc"):
            old = f"(if (<= (abs {axis}) 1) 0 (if (> {axis} 0) 1 -1))"
            new = (f"(if (<= (max (abs dr) (abs dc)) {row_threshold}) 0 "
                   f"(if (= {axis} 0) 0 (if (> {axis} 0) 1 -1)))")
            if result.count(old) != 1:
                raise ValueError("canonical movement clause changed")
            result = result.replace(old, new, 1)
    else:
        for axis, threshold in (("dr", row_threshold), ("dc", col_threshold)):
            needle = f"(<= (abs {axis}) 1)"
            if result.count(needle) != 1:
                raise ValueError("canonical movement clause changed")
            result = result.replace(needle, f"(<= (abs {axis}) {threshold})", 1)
    return result


def program(settings):
    value = _options(settings)
    if type(value) is int:
        return _prototype.instantiate_program(_canonical(), value)
    return _axis_program("panel-count", "panel-count", panel=True)


def _rng(seed, role):
    material = f"{TASK_ID}:native-v1:{seed}:{role}".encode("ascii")
    return random.Random(int.from_bytes(hashlib.sha256(material).digest(), "big"))


def _transform(grid, index):
    result = deepcopy(grid)
    if index >= 4:
        result = [row[::-1] for row in result]
    for _ in range(index % 4):
        result = [list(row) for row in zip(*result[::-1])]
    return result


def _build_scene(h, w, marker, target, rows, cols, target_count, rng,
                 *, density=0.16, marker_count=None, target_shape=None):
    grid = [[7] * w for _ in range(h)]
    for r in rows:
        grid[r] = [0] * w
    for c in cols:
        for row in grid:
            row[c] = 0
    for r in range(marker[0] - 1, marker[0] + 2):
        for c in range(marker[1] - 1, marker[1] + 2):
            grid[r][c] = 5
    grid[marker[0]][marker[1]] = 9
    grid[target[0]][target[1]] = 6
    band = lambda p: (sum(r < p[0] for r in rows), sum(c < p[1] for c in cols))
    selected, central = band(target), band(marker)
    pools = {(ri, ci): [] for ri in range(3) for ci in range(3)}
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 7:
                pools[band((r, c))].append((r, c))
    for panel, cells in pools.items():
        rng.shuffle(cells)
        # Every nonempty other panel carries real clutter; boundary contacts are
        # retained instead of merely placing a small puzzle in a large canvas.
        boundary = [p for p in cells if p[0] in (0, h - 1) or p[1] in (0, w - 1)]
        if boundary:
            chosen = rng.choice(boundary)
            cells.remove(chosen)
            cells.insert(0, chosen)
        if panel == selected:
            count = target_count
        elif panel == central and marker_count is not None:
            count = marker_count
        else:
            count = max(1, round(len(cells) * density)) if cells else 0
        if count > len(cells):
            raise ValueError("panel lacks room for its required distractor count")
        if panel == selected and target_shape is not None:
            if count != 2:
                raise ValueError("connected/disconnected teaching requires two cells")
            pair = None
            for first in cells:
                candidates = [p for p in cells if p != first and (
                    abs(p[0]-first[0]) + abs(p[1]-first[1]) == 1
                    if target_shape == "connected" else
                    max(abs(p[0]-first[0]), abs(p[1]-first[1])) > 1)]
                if candidates:
                    pair = [first, rng.choice(candidates)]
                    break
            if pair is None:
                raise ValueError("panel cannot realize the required teaching topology")
            cells = pair + [p for p in cells if p not in pair]
        color = rng.choice(NOISE)
        for index, (r, c) in enumerate(cells[:count]):
            # Same-color selected pairs distinguish cell count from color count.
            grid[r][c] = color if panel == selected else NOISE[(index + color) % len(NOISE)]
    facts = scene_facts(grid)
    if facts["panel_noise_count"] != target_count:
        raise AssertionError("constructor lost the selected-panel count")
    return grid


def _scene(h, w, delta, count, rng, *, external=False, density=0.16, target_shape=None):
    mr, mc = rng.randint(3, h - 6), rng.randint(3, w - 6)
    rows = (rng.randint(1, mr - 2), rng.randint(mr + (4 if external else 3), min(h - 2, mr + 5)))
    cols = (rng.randint(1, mc - 2), mc + rng.choice((2, 3)) if external
            else rng.randint(mc + 3, min(w - 2, mc + 5)))
    return _build_scene(h, w, (mr, mc), (mr + delta[0], mc + delta[1]),
                        rows, cols, count, rng, density=density,
                        marker_count=4 if external else None, target_shape=target_shape)


def episode_inputs(seed, demos, queries):
    _integer(seed, 0, 2**63 - 1, "seed")
    _integer(demos, 4, 6, "demos")
    _integer(queries, 4, 4, "queries")
    orient = _rng(seed, "teaching-orientation").randrange(8)
    train = []
    # Each axis has distances 1/2 and moves in both signs beyond 2.
    # The panel counts also teach zero, one, two and independent gating.
    roles = (((1, 4), 0), ((2, 4), 2), ((1, 4), 2), ((2, 4), 1))
    for index, (delta, count) in enumerate(roles):
        rng = _rng(seed, f"teaching-{index}")
        base = 11 + 3 * index
        grid = _scene(rng.randint(base, base + 2), rng.randint(base, base + 2),
                      delta, count, rng, external=True,
                      target_shape="connected" if index == 1 else "disconnected" if index == 2 else None)
        if index == 1:
            grid = [row[::-1] for row in grid]
        elif index >= 2:
            grid = [list(row) for row in zip(*grid)]
            if index == 3:
                grid = grid[::-1]
        train.append(_transform(grid, orient))
    for index in range(4, demos):
        rng = _rng(seed, f"extra-demo-{index}")
        grid = _scene(18 + index, 21 + index, (2, 4), index % 3, rng,
                      external=True, density=0.1 + 0.03 * index)
        train.append(_transform(grid, rng.randrange(8)))
    test = []
    for index in range(queries):
        rng = _rng(seed, f"query-{index}")
        if index == 0:
            grid = _build_scene(8, 8, (3, 3), (7, 7), (1, 5), (1, 5),
                                0, rng, density=0.1)
        elif index == 1:
            grid = _scene(13, 17, (1, 4), 1, rng, external=True, density=0.12)
        elif index == 2:
            grid = _scene(22, 26, (2, 4), 2, rng, external=True, density=0.22)
        else:
            mr, mc = rng.randint(7, 13), rng.randint(7, 15)
            grid = _build_scene(30, 30, (mr, mc), (29, mc + 1),
                                (rng.randint(2, mr - 2), mr + 4),
                                (rng.randint(2, mc - 2), mc + 4),
                                rng.randrange(3), rng, density=0.23)
        test.append(_transform(grid, rng.randrange(8)))
    keys = [tuple(map(tuple, grid)) for grid in [*train, *test]]
    if len(keys) != len(set(keys)):
        raise ValueError("constructive episode unexpectedly repeated an input")
    return {"train": train, "test": test}


def _component_count(grid, points, diagonal=False):
    remaining, count = set(points), 0
    while remaining:
        frontier = [remaining.pop()]
        count += 1
        while frontier:
            r, c = frontier.pop()
            adjacent = {p for p in remaining if grid[p[0]][p[1]] == grid[r][c] and (
                max(abs(p[0]-r), abs(p[1]-c)) == 1 if diagonal else
                abs(p[0]-r) + abs(p[1]-c) == 1)}
            remaining.difference_update(adjacent)
            frontier.extend(adjacent)
    return count


def declared_rivals(grid, setting):
    """Finite plausible shortcuts; surviving equivalents must agree on queries."""
    setting = _setting(setting)
    facts = scene_facts(grid)
    marker, target = facts["marker"], facts["target"]
    tolerance = facts["panel_noise_count"] if setting == "target_panel_count" else setting
    paint = lambda r, c: _paint(grid, marker, target, r, c)
    result = {f"row_{r}_col_{c}": paint(r, c) for r in range(3) for c in range(3)}
    dr, dc = target[0] - marker[0], target[1] - marker[1]
    for r in (-1, 0, 1):
        for c in (-1, 0, 1):
            sr = 0 if abs(dr) <= tolerance else r
            sc = 0 if abs(dc) <= tolerance else c
            answer = deepcopy(grid)
            answer[marker[0]][marker[1]] = 5
            answer[marker[0] + sr][marker[1] + sc] = 9
            answer[target[0]][target[1]] = 9
            result[f"direction_{r}_{c}"] = answer
    result["global_dead_zone"] = _paint(grid, marker, target, tolerance, tolerance, global_gate=True)
    result["panel_direction_only"] = _generator()._panel_direction_only(grid)
    if setting == "target_panel_count":
        bounds = facts["panel_bounds"]
        rows, cols = facts["separator_rows"], facts["separator_cols"]
        panel = lambda p: (sum(r < p[0] for r in rows), sum(c < p[1] for c in cols))
        noise = facts["noise_cells"]
        counts = {
            "global_count": len(noise),
            "marker_panel_count": sum(panel(p) == panel(marker) for p in noise),
            "row_band_count": sum(bounds[0] <= p[0] <= bounds[2] for p in noise),
            "col_band_count": sum(bounds[1] <= p[1] <= bounds[3] for p in noise),
            "distinct_colors": len({grid[r][c] for r, c in facts["panel_noise_cells"]}),
            "include_target": tolerance + 1,
            "nonempty_means_two": 2 if tolerance else 0,
            "cap_at_one": min(tolerance, 1),
            "components_4": _component_count(grid, facts["panel_noise_cells"]),
            "components_8": _component_count(grid, facts["panel_noise_cells"], True),
        }
        result.update({name: paint(count, count) for name, count in counts.items()})
        result["count_rows_only"] = paint(tolerance, 0)
        result["count_cols_only"] = paint(0, tolerance)
    return result


def rival_programs(setting):
    """Executable counterparts used by the reusable protected-Racket audit."""
    setting = _setting(setting)
    dynamic = setting == "target_panel_count"
    threshold = "panel-count" if dynamic else str(setting)
    result = {f"row_{r}_col_{c}": _axis_program(str(r), str(c))
              for r in range(3) for c in range(3)}
    for r in (-1, 0, 1):
        for c in (-1, 0, 1):
            result[f"direction_{r}_{c}"] = program({"axis_tolerance": setting}).replace(
                "(if (> dr 0) 1 -1)", str(r)).replace("(if (> dc 0) 1 -1)", str(c))
    result["global_dead_zone"] = _axis_program(threshold, threshold, panel=dynamic, global_gate=True)
    panel_direction = _with_panel_count(_canonical())
    for axis, coordinate, separators in (("dr", "r6", "separator-rows"), ("dc", "c6", "separator-cols")):
        old = f"(if (<= (abs {axis}) 1) 0 (if (> {axis} 0) 1 -1))"
        new = (f"(if (< {coordinate} (first {separators})) -1 "
               f"(if (> {coordinate} (second {separators})) 1 0))")
        panel_direction = panel_direction.replace(old, new, 1)
    result["panel_direction_only"] = panel_direction
    if dynamic:
        expressions = {
            "global_count": "(for*/sum ((r (range h)) (c (range w))) (if (noise? (at g r c)) 1 0))",
            "row_band_count": "(for*/sum ((r (range (+ row-low 1) row-high)) (c (range w))) (if (noise? (at g r c)) 1 0))",
            "col_band_count": "(for*/sum ((r (range h)) (c (range (+ col-low 1) col-high))) (if (noise? (at g r c)) 1 0))",
            "distinct_colors": "(length (remove-duplicates (for*/list ((r (range (+ row-low 1) row-high)) (c (range (+ col-low 1) col-high)) #:when (noise? (at g r c))) (at g r c))))",
            "include_target": "(+ panel-count 1)",
            "nonempty_means_two": "(if (= panel-count 0) 0 2)",
            "cap_at_one": "(min panel-count 1)",
        }
        result.update({name: _axis_program(expr, expr, panel=True) for name, expr in expressions.items()})
        # Selecting the marker's panel is a source-selection ablation. Only the
        # bound computations change; marker/target displacement stays intact.
        marker_program = program({"axis_tolerance": setting})
        for old, new in (("(< r r6)", "(< r r9)"), ("(> r r6)", "(> r r9)"),
                         ("(< c c6)", "(< c c9)"), ("(> c c6)", "(> c c9)")):
            marker_program = marker_program.replace(old, new)
        result["marker_panel_count"] = marker_program
        result["count_rows_only"] = _axis_program(threshold, "0", panel=True)
        result["count_cols_only"] = _axis_program("0", threshold, panel=True)
        for connectivity, metric in ((4, "+"), (8, "max")):
            bindings = f"""
                        (panel-points (for*/list ((r (range (+ row-low 1) row-high))
                                                 (c (range (+ col-low 1) col-high))
                                                 #:when (noise? (at g r c))) (list r c)))
                        (adjacent? (lambda (a b) (and
                          (= (at g (first a) (second a)) (at g (first b) (second b)))
                          (= ({metric} (abs (- (first a) (first b)))
                                       (abs (- (second a) (second b)))) 1))))
                        (flood (lambda (start remaining)
                          (let loop ((frontier (list start)) (remaining remaining))
                            (if (null? frontier) remaining
                              (let* ((found (filter (lambda (p) (adjacent? (car frontier) p)) remaining))
                                     (rest (filter (lambda (p) (not (member p found))) remaining)))
                                (loop (append (cdr frontier) found) rest))))))
                        (component-count (let loop ((remaining panel-points) (count 0))
                          (if (null? remaining) count
                            (loop (flood (car remaining) (cdr remaining)) (+ count 1)))))"""
            result[f"components_{connectivity}"] = _axis_program(
                "component-count", "component-count", panel=True).replace(
                    _PANEL_BINDINGS, _PANEL_BINDINGS + bindings, 1)
    return result


def generate(seed, settings, demos, queries):
    value = _options(settings)
    inputs = episode_inputs(seed, demos, queries)
    return {**{split: [{"input": grid, "output": rule_mirror(grid, value)} for grid in grids]
               for split, grids in inputs.items()}, "program_solution": program(settings)}


def public_turn(episode, query_index=0):
    """One-query projection; no answers, settings, future inputs, or count hints."""
    _integer(query_index, 0, len(episode["test"]) - 1, "query_index")
    from reviewer_support import public_challenge_bytes
    import json
    return json.loads(public_challenge_bytes({"train": episode["train"],
                                             "test": [episode["test"][query_index]]}))
