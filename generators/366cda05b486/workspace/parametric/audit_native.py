#!/usr/bin/env python3
"""Independent finite teaching audit of blue contact clusters and hop frontiers.

Only demonstrations select survivors. Exact protected-Racket outputs are
compared with an independent component/coordinate oracle; errors never refute.
"""
from __future__ import annotations

import argparse
from collections import deque
from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve()
HOME = HERE.parent
ROOT = next(parent for parent in HERE.parents if (parent / "shared/runtime").is_dir())
TASK_ID = "366cda05b486"
CANONICAL_SHA256 = "f50313901f961bd1d105eedf9f91e943a0e52d1e0ea092fceb6e500c7eb77db4"
SETTINGS = ({"scope": "cluster"}, {"scope": "farthest"})
CARDINAL = ((-1, 0), (0, -1), (0, 1), (1, 0))
EIGHT = tuple((dr, dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1) if dr or dc)
BASE_RIVALS = (
    "seed_only", "one_hop_ball", "one_hop_layer", "all_foreground", "eight_contact",
    "largest_cluster", "most_objects_cluster", "noncyan_cluster", "largest_object",
    "solid_bbox", "preserve_colors",
)
FAR_RIVALS = (
    "cell_distance_objects", "manhattan_gap", "centroid_l1", "single_farthest",
    "graph_leaves", "dfs_depth", "color_graph",
)


def _digest(body):
    return hashlib.sha256(body).hexdigest()


def _json_bytes(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def _hash(value):
    return _digest(_json_bytes(value))


def _write_json(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _grid(value):
    if (type(value) is not list or not 1 <= len(value) <= 30
            or type(value[0]) is not list or not 1 <= len(value[0]) <= 30
            or any(type(row) is not list or len(row) != len(value[0])
                   or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
                   for row in value)):
        raise ValueError("audit grids require rectangular 1..30 exact integer colors 0..9")
    return deepcopy(value)


def _parse(value):
    grid = _grid(value)
    remaining = {(r, c) for r, row in enumerate(grid) for c, cell in enumerate(row) if cell}
    objects, owner = [], {}
    while remaining:
        start = min(remaining)
        color = grid[start[0]][start[1]]
        cells, frontier = {start}, [start]
        remaining.remove(start)
        while frontier:
            row, col = frontier.pop()
            for dr, dc in CARDINAL:
                neighbor = row + dr, col + dc
                if neighbor in remaining and grid[neighbor[0]][neighbor[1]] == color:
                    remaining.remove(neighbor)
                    cells.add(neighbor)
                    frontier.append(neighbor)
        index = len(objects)
        for point in cells:
            owner[point] = index
        objects.append({"color": color, "cells": cells})
    seeds = [index for index, obj in enumerate(objects) if obj["color"] == 1]
    if len(seeds) != 1:
        raise ValueError("input needs exactly one monochromatic cardinal blue object")
    adjacency = _adjacency(objects, owner, CARDINAL)
    return grid, objects, owner, adjacency, seeds[0]


def _adjacency(objects, owner, directions):
    adjacency = [set() for _ in objects]
    for point, index in owner.items():
        for dr, dc in directions:
            other = owner.get((point[0] + dr, point[1] + dc))
            if other is not None and other != index:
                adjacency[index].add(other)
    return adjacency


def _distances(adjacency, seed):
    distance, queue = {seed: 0}, deque([seed])
    while queue:
        index = queue.popleft()
        for other in sorted(adjacency[index]):
            if other not in distance:
                distance[other] = distance[index] + 1
                queue.append(other)
    return distance


def _settings(settings):
    if (type(settings) is not dict or set(settings) != {"scope"}
            or type(settings["scope"]) is not str or settings["scope"] not in ("cluster", "farthest")):
        raise ValueError("settings must be exactly scope=cluster|farthest")
    return settings["scope"]


def rivals(settings):
    scope = _settings(settings)
    return BASE_RIVALS + ("native_" + ("farthest" if scope == "cluster" else "cluster"),) + (
        FAR_RIVALS if scope == "farthest" else ("exclude_blue",))


def _choice(settings, name):
    scope = _settings(settings)
    if name is not None and name not in rivals(settings):
        raise ValueError(f"undeclared rival: {name!r}")
    return name.removeprefix("native_") if name and name.startswith("native_") else scope


def _crop(grid, objects, selected, *, solid=False, colors=False):
    cells = set().union(*(objects[index]["cells"] for index in selected))
    row0, row1 = min(r for r, _ in cells), max(r for r, _ in cells)
    col0, col1 = min(c for _, c in cells), max(c for _, c in cells)
    return [[(grid[r][c] if colors else 8) if solid or (r, c) in cells else 0
             for c in range(col0, col1 + 1)] for r in range(row0, row1 + 1)]


def _python_apply(value, settings, name=None):
    scope = _choice(settings, name)
    grid, objects, owner, adjacency, seed = _parse(value)
    distance = _distances(adjacency, seed)
    reachable = sorted(distance)
    max_depth = max(distance.values())
    selected = reachable if scope == "cluster" else [i for i in reachable if distance[i] == max_depth]
    if name == "seed_only":
        selected = [seed]
    elif name == "one_hop_ball":
        selected = [i for i in reachable if distance[i] <= 1]
    elif name == "one_hop_layer":
        selected = sorted(adjacency[seed]) or [seed]
    elif name == "exclude_blue":
        selected = [i for i in reachable if i != seed] or [seed]
    elif name == "all_foreground":
        selected = list(range(len(objects)))
    elif name == "largest_object":
        selected = [max(range(len(objects)), key=lambda i: (len(objects[i]["cells"]), -i))]
    elif name == "eight_contact":
        alternate = _distances(_adjacency(objects, owner, EIGHT), seed)
        selected = sorted(alternate) if scope == "cluster" else [i for i in sorted(alternate) if alternate[i] == max(alternate.values())]
    elif name in ("largest_cluster", "most_objects_cluster", "noncyan_cluster"):
        unseen, groups = set(range(len(objects))), []
        while unseen:
            group = set(_distances(adjacency, min(unseen)))
            groups.append(group)
            unseen -= group
        choices = [group for group in groups if all(objects[i]["color"] != 8 for i in group)] if name == "noncyan_cluster" else groups
        selected = max(choices or groups, key=lambda group: (
            len(group) if name == "most_objects_cluster" else sum(len(objects[i]["cells"]) for i in group),
            seed in group, -min(group)))
    elif name == "single_farthest":
        selected = [min(selected)]
    elif name == "graph_leaves":
        selected = [i for i in reachable if i != seed and len(adjacency[i]) == 1] or [seed]
    elif name == "dfs_depth":
        depths = {}
        def visit(index, depth):
            if index not in depths:
                depths[index] = depth
                for other in sorted(adjacency[index]):
                    visit(other, depth + 1)
        visit(seed, 0)
        selected = [i for i in reachable if depths[i] == max(depths.values())]
    elif name == "color_graph":
        color_adjacency = [set() for _ in range(10)]
        for index, adjacent in enumerate(adjacency):
            color_adjacency[objects[index]["color"]].update(objects[j]["color"] for j in adjacent)
        depths = _distances(color_adjacency, 1)
        selected = [i for i, obj in enumerate(objects) if depths.get(obj["color"], -1) == max(depths.values())]
    elif name in ("cell_distance_objects", "manhattan_gap", "centroid_l1"):
        blue = objects[seed]["cells"]
        if name == "cell_distance_objects":
            cell_depths, queue = {point: 0 for point in blue}, deque(sorted(blue))
            while queue:
                r, c = queue.popleft()
                for dr, dc in CARDINAL:
                    neighbor = r + dr, c + dc
                    if neighbor in owner and neighbor not in cell_depths:
                        cell_depths[neighbor] = cell_depths[(r, c)] + 1
                        queue.append(neighbor)
            scores = {i: max(cell_depths[p] for p in objects[i]["cells"]) for i in reachable}
        elif name == "manhattan_gap":
            scores = {i: min(abs(r - br) + abs(c - bc) for r, c in objects[i]["cells"] for br, bc in blue) for i in reachable}
        else:
            br, bc = (Fraction(sum(p[axis] for p in blue), len(blue)) for axis in (0, 1))
            scores = {i: abs(Fraction(sum(r for r, c in objects[i]["cells"]), len(objects[i]["cells"])) - br)
                      + abs(Fraction(sum(c for r, c in objects[i]["cells"]), len(objects[i]["cells"])) - bc) for i in reachable}
        selected = [i for i in reachable if scores[i] == max(scores.values())]
    return _crop(grid, objects, selected, solid=name == "solid_bbox", colors=name == "preserve_colors")


def python_intended(grid, settings):
    """Independent output labels; never calls native_family.transform."""
    return _python_apply(grid, settings)


def python_rival(grid, settings, name):
    return _python_apply(grid, settings, name)


def rival_program(settings, name):
    scope = _choice(settings, name)
    if name.startswith("native_"):
        return _load_family().program({"scope": scope})
    selection = "reachable" if scope == "cluster" else "(max-ids reachable (lambda (i) (hash-ref distances i)))"
    choices = {
        "seed_only": "(list seed)",
        "one_hop_ball": "(filter (lambda (i) (<= (hash-ref distances i) 1)) reachable)",
        "one_hop_layer": "(or-seed (list-ref adj seed))",
        "exclude_blue": "(or-seed (filter (lambda (i) (not (= i seed))) reachable))",
        "all_foreground": "ids",
        "largest_object": "(list (first (max-ids ids (lambda (i) (length (cells i))))))",
        "eight_contact": "(let* ([d (walk (make-adj eight-deltas) seed)] [rs (filter (lambda (i) (hash-has-key? d i)) ids)]) " + ("rs)" if scope == "cluster" else "(max-ids rs (lambda (i) (hash-ref d i))))"),
        "largest_cluster": "(best-group groups #f)",
        "most_objects_cluster": "(best-group groups #t)",
        "noncyan_cluster": "(let ([good (filter (lambda (group) (andmap (lambda (i) (not (= (obj-color (list-ref objs i)) 8))) group)) groups)]) (best-group (if (null? good) groups good) #f))",
        "single_farthest": "(list (first (max-ids reachable (lambda (i) (hash-ref distances i)))))",
        "graph_leaves": "(or-seed (filter (lambda (i) (and (not (= i seed)) (= (length (list-ref adj i)) 1))) reachable))",
        "dfs_depth": "(let ([depths (make-hash)]) (letrec ([visit (lambda (i depth) (unless (hash-has-key? depths i) (hash-set! depths i depth) (for ([j (list-ref adj i)]) (visit j (+ depth 1)))))]) (visit seed 0)) (max-ids reachable (lambda (i) (hash-ref depths i))))",
        "color_graph": "(let* ([ca (for/list ([color (in-range 10)]) (sort (remove-duplicates (append* (for/list ([i ids] #:when (= (obj-color (list-ref objs i)) color)) (map (lambda (j) (obj-color (list-ref objs j))) (list-ref adj i))))) <))] [depths (walk ca 1)] [best (apply max (hash-values depths))]) (filter (lambda (i) (= (hash-ref depths (obj-color (list-ref objs i)) -1) best)) ids))",
        "cell_distance_objects": "(let ([depths (cell-walk (cells seed))]) (max-ids reachable (lambda (i) (apply max (map (lambda (p) (hash-ref depths p)) (cells i))))))",
        "manhattan_gap": "(max-ids reachable (lambda (i) (apply min (for*/list ([p (cells i)] [b (cells seed)]) (+ (abs (- (first p) (first b))) (abs (- (second p) (second b))))))))",
        "centroid_l1": "(let* ([ratios (map centroid-score reachable)] [best (for/fold ([best (first ratios)]) ([rat (rest ratios)]) (if (> (* (first rat) (second best)) (* (first best) (second rat))) rat best))]) (filter (lambda (i) (let ([rat (centroid-score i)]) (= (* (first rat) (second best)) (* (first best) (second rat))))) reachable))",
    }
    selected = choices.get(name, selection)
    fill = "8" if name == "solid_bbox" else ("(if (member p chosen-cells) (cell-at g (first p) (second p)) 0)" if name == "preserve_colors" else "(if (member p chosen-cells) 8 0)")
    return f"""(rule! (lambda (g)
 (let ()
  (define (point-key p) (+ (* (cols g) (first p)) (second p)))
  (define objs (sort (objects g 0) (lambda (a b) (< (apply min (map point-key (obj-cells a))) (apply min (map point-key (obj-cells b)))))))
  (define ids (range 0 (length objs)))
  (define (cells i) (obj-cells (list-ref objs i)))
  (define seed (first (filter (lambda (i) (= (obj-color (list-ref objs i)) 1)) ids)))
  (define eight-deltas '((-1 -1) (-1 0) (-1 1) (0 -1) (0 1) (1 -1) (1 0) (1 1)))
  (define (make-adj directions)
    (for/list ([i ids])
      (filter (lambda (j) (and (not (= i j))
        (ormap (lambda (p) (ormap (lambda (d)
          (member (list (+ (first p) (first d)) (+ (second p) (second d))) (cells j))) directions)) (cells i)))) ids)))
  (define adj (make-adj cardinal-deltas))
  (define (walk graph start)
    (let ([seen (make-hash)])
      (hash-set! seen start 0)
      (let loop ([queue (list start)])
        (if (null? queue) seen
          (let* ([i (first queue)] [fresh (filter (lambda (j) (not (hash-has-key? seen j))) (list-ref graph i))])
            (for ([j fresh]) (hash-set! seen j (+ 1 (hash-ref seen i))))
            (loop (append (rest queue) fresh)))))))
  (define distances (walk adj seed))
  (define reachable (filter (lambda (i) (hash-has-key? distances i)) ids))
  (define (or-seed xs) (if (null? xs) (list seed) xs))
  (define (max-ids xs score)
    (let ([best (apply max (map score xs))]) (filter (lambda (i) (= (score i) best)) xs)))
  (define groups
    (let loop ([left ids] [out '()])
      (if (null? left) (reverse out)
        (let* ([seen (walk adj (first left))] [group (filter (lambda (i) (hash-has-key? seen i)) ids)])
          (loop (filter (lambda (i) (not (member i group))) left) (cons group out))))))
  (define (best-group choices by-count)
    (define (score group) (if by-count (length group) (apply + (map (lambda (i) (length (cells i))) group))))
    (for/fold ([best (first choices)]) ([group (rest choices)])
      (if (or (> (score group) (score best))
              (and (= (score group) (score best)) (member seed group) (not (member seed best)))) group best)))
  (define (cell-walk starts)
    (let ([seen (make-hash)])
      (for ([p starts]) (hash-set! seen p 0))
      (let loop ([queue starts])
        (if (null? queue) seen
          (let* ([p (first queue)]
                 [near (map (lambda (d) (list (+ (first p) (first d)) (+ (second p) (second d)))) cardinal-deltas)]
                 [fresh (filter (lambda (q)
                   (and (<= 0 (first q)) (< (first q) (rows g)) (<= 0 (second q)) (< (second q) (cols g))
                        (not (= (cell-at g (first q) (second q)) 0)) (not (hash-has-key? seen q)))) near)])
            (for ([q fresh]) (hash-set! seen q (+ 1 (hash-ref seen p))))
            (loop (append (rest queue) fresh)))))))
  (define (centroid-score i)
    (let* ([ps (cells i)] [bs (cells seed)] [pn (length ps)] [bn (length bs)]
           [sr (apply + (map first ps))] [sc (apply + (map second ps))]
           [br (apply + (map first bs))] [bc (apply + (map second bs))])
      (list (+ (abs (- (* sr bn) (* br pn))) (abs (- (* sc bn) (* bc pn)))) (* pn bn))))
  (define chosen {selected})
  (define chosen-cells (append* (map cells chosen)))
  (define bb (bbox-of-cells chosen-cells))
  (grid-from-fn (+ 1 (- (third bb) (first bb))) (+ 1 (- (fourth bb) (second bb)))
    (lambda (r c) (let ([p (list (+ r (first bb)) (+ c (second bb)))]) {fill}))))))"""


class ExecutionCache:
    """Retain each exact program/input/output evaluation once, including errors."""

    def __init__(self, apply, identity, budget=512):
        self.apply = apply
        self.identity = deepcopy(identity)
        self.identity_after = None
        self.budget = budget
        self.request_count = 0
        self.execution_count = 0
        self.programs = {}
        self.inputs = {}
        self.records = {}

    def evaluate(self, program, grid):
        grid = _parse(grid)[0]
        if type(program) is not str or not program.strip():
            raise ValueError("program must be nonempty text")
        self.request_count += 1
        program_hash, input_hash = _digest(program.encode()), _hash(grid)
        key = program_hash + ":" + input_hash
        if key not in self.records:
            if self.execution_count >= self.budget:
                raise RuntimeError(f"bounded audit execution budget exceeded ({self.budget})")
            self.programs[program_hash] = program
            self.inputs[input_hash] = deepcopy(grid)
            row = {"execution_id": key, "program_sha256": program_hash, "input_sha256": input_hash}
            self.execution_count += 1
            try:
                output = _grid(self.apply(program, deepcopy(grid)))
            except Exception as error:
                row.update(status="error", error_type=type(error).__name__, error=str(error))
            else:
                row.update(status="ok", output=output, output_sha256=_hash(output))
            self.records[key] = row
        return deepcopy(self.records[key])


@contextmanager
def protected_evaluator():
    """Use the current same-checkout protected runtime and bind it before/after."""
    runtime = ROOT / "shared/runtime"
    before = list(sys.path)
    sys.path[:0] = [str(ROOT / "src"), str(runtime)]
    try:
        from arcpuzzles.parametric_worker import _local_imports, _real_evaluator
        with _local_imports(runtime, HOME):
            apply, identity, bridge = _real_evaluator(runtime)
            executor = ExecutionCache(apply, identity)
            try:
                yield executor
            finally:
                try:
                    current = bridge.runtime_identity
                    executor.identity_after = {key: current[key] for key in identity}
                finally:
                    bridge.close()
    finally:
        sys.path[:] = before


def assess_program(executor, name, program, train, queries, oracle=None):
    """Stop on first demo refutation; assess every query of a surviving rule."""
    if not train or not queries:
        raise ValueError("a lesson needs demonstrations and independent queries")
    result = {
        "name": name, "program_sha256": _digest(program.encode()), "status": "running",
        "demo_indices_checked": [], "query_indices_checked": [],
        "demo_executions": [], "query_executions": [], "refuting_demo_index": None,
        "disagreeing_query_indices": [], "first_teaching_hole": None,
    }
    for phase, pairs in (("demo", train), ("query", queries)):
        for index, pair in enumerate(pairs):
            intended = _grid(pair["output"])
            row = executor.evaluate(program, pair["input"])
            result[f"{phase}_indices_checked"].append(index)
            result[f"{phase}_executions"].append(row["execution_id"])
            if row["status"] != "ok":
                result.update(status="execution_error", error=row)
                return result
            independent = oracle(pair["input"]) if oracle is not None else None
            if oracle is not None and row["output"] != independent:
                result.update(status="oracle_mismatch", error={
                    "phase": phase, "index": index, "racket_output": row["output"],
                    "independent_output": independent,
                })
                return result
            if row["output"] != intended:
                if phase == "demo":
                    result.update(status="demo_refuted", refuting_demo_index=index)
                    return result
                result["disagreeing_query_indices"].append(index)
                if result["first_teaching_hole"] is None:
                    result["first_teaching_hole"] = {
                        "train": deepcopy(train), "test": [deepcopy(pair)], "query_index": index,
                        "rival_name": name, "rival_program": program, "rival_output": row["output"],
                        "minimization": "First disagreeing query with the required two demos; cells not minimized.",
                    }
    result["status"] = "teaching_hole" if result["disagreeing_query_indices"] else "query_agreeing_survivor"
    return result


def assess_rival(executor, settings, name, train, queries):
    return assess_program(executor, name, rival_program(settings, name), train, queries,
                          oracle=lambda grid: python_rival(grid, settings, name))


def _load_family():
    path = HOME / "native_family.py"
    spec = importlib.util.spec_from_file_location("cluster_native_family_for_independent_audit", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load same-task native family")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _source_binding():
    paths = [HOME / name for name in ("audit_native.py", "native_family.py", "canonical.rkt",
                                      "adapter.py", "promotion.json", "README.md")]
    paths += [HOME.parents[1] / "generator.py", HOME.parents[1] / "tests/test_native_audit.py",
              HOME.parents[1] / "tests/test_native_family.py",
              ROOT / "src/arcpuzzles/parametric_worker.py", ROOT / "src/arcpuzzles/catalog.py",
              ROOT / "shared/runtime/arc_repl/racket_bridge.py",
              ROOT / "shared/runtime/arc_repl/security.py",
              ROOT / "shared/runtime/puzzle_generators/rule_wrap.py",
              ROOT / "shared/tools/comment_solutions.py",
              ROOT / "shared/runtime/arc_repl/racket_prelude/arc-prelude.rkt"]
    return {str(path.relative_to(ROOT)): _digest(path.read_bytes()) for path in paths}


def _bank(episode, demos=6, queries=4):
    if (type(episode) is not dict or type(episode.get("train")) is not list
            or type(episode.get("test")) is not list
            or len(episode["train"]) != demos or len(episode["test"]) != queries):
        raise ValueError("native family returned incorrect bank counts")
    inputs = []
    for pair in episode["train"] + episode["test"]:
        if type(pair) is not dict or not {"input", "output"} <= set(pair):
            raise ValueError("bank pair needs input and output")
        source, output = _parse(pair["input"])[0], _grid(pair["output"])
        inputs.append(_hash(source))
    if len(inputs) != len(set(inputs)):
        raise ValueError("bank demonstration/query inputs must be distinct")
    return deepcopy(episode)


def _features(grid):
    value, objects, owner, adjacency, seed = _parse(grid)
    depths = _distances(adjacency, seed)
    maximum = max(depths.values())
    farthest = [index for index in depths if depths[index] == maximum]
    return {"shape": [len(value), len(value[0])], "object_count": len(objects),
            "foreground_cells": len(owner), "blue_cells": len(objects[seed]["cells"]),
            "reachable_objects": len(depths), "max_shortest_object_hops": maximum,
            "farthest_objects": len(farthest),
            "farthest_cells": sum(len(objects[index]["cells"]) for index in farthest),
            "reachable_cells": sum(len(objects[index]["cells"]) for index in depths),
            "depth_histogram": {str(depth): sum(value == depth for value in depths.values())
                                for depth in range(maximum + 1)}}


def run(out):
    out = Path(out).resolve()
    out.mkdir(parents=True, exist_ok=False)
    report = {
        "schema": TASK_ID + "-native-teaching-audit-v1", "task_id": TASK_ID,
        "status": "running", "started_utc": datetime.now(timezone.utc).isoformat(),
        "canonical_program_sha256": CANONICAL_SHA256, "seeds": [0, 17],
        "counts": {"teaching_demos": 2, "verified_bank_demos": 6, "queries": 4,
                   "settings": 2, "intended_labels_expected": 40},
        "episodes": [], "failures": [], "intended_labels_verified": 0,
        "excluded_equivalent_hypotheses": {
            "foreground_flood_for_cluster": "Foreground four-way flood from the blue object equals closure of the cardinal object-contact graph.",
            "farthest_exclude_blue": "For nontrivial connected graphs, farthest already excludes the seed; isolated seed remains explicit.",
        },
        "limits": [
            "Finite declared-rival audit over two settings and seeds 0,17; no universal identification claim.",
            "All six-demo/four-query bank labels are checked by independent Python and protected Racket.",
            "Only the first two demonstrations decide survival; a rival stops at its first refuting demonstration.",
            "Only demo survivors execute queries; query answers never update the survivor set.",
            "Centroid L1 comparisons use exact cross-products, avoiding this DSL's truncated integer division.",
            "Native grammar extends production to cycles, repeated colors, arbitrary connected object shapes and 30x30 grids.",
            "Reviewer evidence does not grant owner acceptance, resolve unrelated audits or admit training data.",
        ],
    }
    executor = None
    try:
        source_binding = _source_binding()
        report["source_files_sha256"] = source_binding
        family = _load_family()
        if {_hash(setting) for setting in family.SETTINGS} != {_hash(setting) for setting in SETTINGS}:
            raise AssertionError("native settings differ from the declared scopes")
        canonical = family.program({"scope": "cluster"})
        if _digest(canonical.encode()) != CANONICAL_SHA256 or canonical != (HOME / "canonical.rkt").read_text():
            raise AssertionError("default differs from the pinned exact canonical source")
        with protected_evaluator() as executor:
            report["racket"] = deepcopy(executor.identity)
            for seed in (0, 17):
                shared_inputs = None
                for settings in SETTINGS:
                    bank = _bank(family.generate(seed, deepcopy(settings), demos=6, queries=4))
                    minimum = _bank(family.generate(seed, deepcopy(settings), demos=2, queries=4), demos=2)
                    if minimum["train"] != bank["train"][:2] or minimum["test"] != bank["test"]:
                        raise AssertionError("minimum episode differs from the full bank prefix")
                    program = family.program(settings)
                    if bank["program_solution"] != program or minimum["program_solution"] != program:
                        raise AssertionError("episode program differs from the selected exact source")
                    pairs = bank["train"] + bank["test"]
                    input_hashes = [_hash(pair["input"]) for pair in pairs]
                    if shared_inputs is not None and input_hashes != shared_inputs:
                        raise AssertionError("input bank changes with private settings")
                    shared_inputs = input_hashes
                    intended_executions = []
                    for pair in pairs:
                        evaluation = executor.evaluate(program, pair["input"])
                        intended_executions.append(evaluation["execution_id"])
                        if evaluation["status"] != "ok":
                            raise AssertionError(f"intended Racket execution failed: {evaluation}")
                        if evaluation["output"] != pair["output"] or evaluation["output"] != python_intended(pair["input"], settings):
                            raise AssertionError("native claims, independent Python and exact Racket disagree")
                        report["intended_labels_verified"] += 1
                    assessments = []
                    for name in rivals(settings):
                        assessment = assess_rival(executor, settings, name, minimum["train"], bank["test"])
                        assessments.append(assessment)
                        if assessment["status"] in ("teaching_hole", "execution_error", "oracle_mismatch"):
                            report["failures"].append({"seed": seed, "settings": deepcopy(settings), **assessment})
                    report["episodes"].append({
                        "seed": seed, "settings": deepcopy(settings), "program_sha256": _digest(program.encode()),
                        "train": bank["train"], "test": bank["test"], "input_sha256": input_hashes,
                        "features": [_features(pair["input"]) for pair in pairs],
                        "intended_executions": intended_executions, "rivals": assessments,
                        "refuted_rivals": [row["name"] for row in assessments if row["status"] == "demo_refuted"],
                        "query_agreeing_survivors": [row["name"] for row in assessments if row["status"] == "query_agreeing_survivor"],
                        "query_disagreeing_survivors": [row["name"] for row in assessments if row["status"] == "teaching_hole"],
                    })
                    print(json.dumps({"seed": seed, "settings": settings,
                                      "refuted": sum(row["status"] == "demo_refuted" for row in assessments),
                                      "rivals": len(assessments)}), flush=True)
        report["racket_after"] = deepcopy(executor.identity_after)
        report["runtime_stable"] = executor.identity_after == executor.identity
        report["source_files_sha256_after"] = _source_binding()
        report["source_stable"] = report["source_files_sha256_after"] == source_binding
        if not report["source_stable"] or not report["runtime_stable"]:
            raise AssertionError("audited source or runtime changed during the run")
        report["status"] = "passed" if not report["failures"] else "failed"
    except Exception as error:
        report["status"] = "failed"
        report["failures"].append({"error_type": type(error).__name__, "error": str(error)})
    finally:
        if executor is not None:
            executions = {"schema": TASK_ID + "-exact-racket-executions-v1",
                          "programs": executor.programs, "inputs": executor.inputs,
                          "executions": list(executor.records.values())}
            execution_path = out / "executions.json"
            _write_json(execution_path, executions)
            report["executions_file"] = {"path": execution_path.name, "sha256": _digest(execution_path.read_bytes())}
            report["evaluation_requests"] = executor.request_count
            report["racket_evaluations"] = executor.execution_count
            report["cache_hits"] = executor.request_count - executor.execution_count
        holes = [failure for failure in report["failures"] if failure.get("status") == "teaching_hole"]
        if holes:
            hole = holes[0]
            hole_path = out / "minimal-teaching-hole.json"
            _write_json(hole_path, {"task_id": TASK_ID, "seed": hole["seed"], "settings": hole["settings"],
                                   **hole["first_teaching_hole"]})
            report["minimal_teaching_hole_file"] = {"path": hole_path.name, "sha256": _digest(hole_path.read_bytes())}
        report["finished_utc"] = datetime.now(timezone.utc).isoformat()
        _write_json(out / "audit.json", report)
    print(json.dumps({"status": report["status"], "episodes": len(report["episodes"]),
                      "failures": len(report["failures"]), "out": str(out)}), flush=True)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    arguments = parser.parse_args()
    return 0 if run(arguments.out)["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
