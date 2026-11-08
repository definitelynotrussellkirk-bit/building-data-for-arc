#!/usr/bin/env python3
"""Independent finite teaching audit for seeded blue boxes and post-fill size.

Only demonstrations select survivors. Exact protected-Racket outputs are
compared with independently written coordinate/component semantics.
"""
from __future__ import annotations

import argparse
from collections import Counter
from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve()
HOME = HERE.parent
ROOT = next(parent for parent in HERE.parents if (parent / "shared/runtime").is_dir())
TASK_ID = "486375757aca"
CANONICAL_SHA256 = "a19a4990bac925a40190e810e985b52023a5854b4dcde3769b2251fa35432e8e"
SETTINGS = ({"post": "none"}, {"post": "largest_to_8"})
CARDINAL = ((-1, 0), (0, -1), (0, 1), (1, 0))
EIGHT = tuple((r, c) for r in (-1, 0, 1) for c in (-1, 0, 1) if r or c)
BASE_RIVALS = (
    "first_seed", "column_major", "majority_seed", "min_seed", "max_seed",
    "preserve_blue", "zeros_only", "complete_frames", "updated_seeds",
    "reverse_components", "fill_border", "diagonal_blue", "global_last_seed",
)
POST_RIVALS = (
    "pre_fill_largest", "single_largest", "smallest", "largest_color_total",
    "bbox_area", "include_blue", "filled_only", "each_frame_highlight",
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
    if (type(value) is not list or not 3 <= len(value) <= 30
            or type(value[0]) is not list or not 3 <= len(value[0]) <= 30
            or any(type(row) is not list or len(row) != len(value[0])
                   or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
                   for row in value)):
        raise ValueError("audit grids require rectangular 3..30 exact integer colors 0..9")
    return deepcopy(value)


def _objects(grid, *, diagonal=False):
    remaining = {(r, c) for r, row in enumerate(grid) for c, color in enumerate(row) if color}
    objects = []
    while remaining:
        start = min(remaining)
        color = grid[start[0]][start[1]]
        cells, pending = {start}, [start]
        remaining.remove(start)
        while pending:
            row, col = pending.pop()
            for dr, dc in EIGHT if diagonal else CARDINAL:
                point = row + dr, col + dc
                if point in remaining and grid[point[0]][point[1]] == color:
                    remaining.remove(point)
                    cells.add(point)
                    pending.append(point)
        objects.append({"color": color, "cells": cells})
    return objects


def _bbox(cells):
    return min(r for r, c in cells), min(c for r, c in cells), max(r for r, c in cells), max(c for r, c in cells)


def _interior(box):
    top, left, bottom, right = box
    return [(r, c) for r in range(top + 1, bottom) for c in range(left + 1, right)]


def _seeds(grid, box):
    return [(r, c, grid[r][c]) for r, c in _interior(box) if grid[r][c] not in (0, 1)]


def _parse(value):
    grid = _grid(value)
    blue = [obj for obj in _objects(grid) if obj["color"] == 1]
    if not blue:
        raise ValueError("native input needs at least one blue object")
    boxes = [_bbox(obj["cells"]) for obj in blue]
    if any(not _interior(box) or not _seeds(grid, box) for box in boxes):
        raise ValueError("every blue component needs a nonempty seeded bbox interior")
    return grid, boxes


def _settings(settings):
    if (type(settings) is not dict or set(settings) != {"post"}
            or type(settings["post"]) is not str or settings["post"] not in ("none", "largest_to_8")):
        raise ValueError("settings must be exactly post=none|largest_to_8")
    return settings["post"]


def rivals(settings):
    post = _settings(settings)
    return BASE_RIVALS + ("native_" + ("largest_to_8" if post == "none" else "none"),) + (
        POST_RIVALS if post == "largest_to_8" else ())


def _choice(settings, name):
    post = _settings(settings)
    if name is not None and name not in rivals(settings):
        raise ValueError(f"undeclared rival: {name!r}")
    return name.removeprefix("native_") if name and name.startswith("native_") else post


def _complete_boxes(grid):
    boxes = []
    for top in range(len(grid) - 2):
        for left in range(len(grid[0]) - 2):
            for bottom in range(top + 2, len(grid)):
                for right in range(left + 2, len(grid[0])):
                    box = top, left, bottom, right
                    border = {(r, c) for r in range(top, bottom + 1) for c in range(left, right + 1)
                              if r in (top, bottom) or c in (left, right)}
                    if all(grid[r][c] == 1 for r, c in border) and _seeds(grid, box):
                        boxes.append(box)
    return boxes


def _fill(grid, boxes, name):
    output = deepcopy(grid)
    if name == "complete_frames":
        boxes = _complete_boxes(grid)
    elif name == "diagonal_blue":
        boxes = [_bbox(obj["cells"]) for obj in _objects(grid, diagonal=True) if obj["color"] == 1]
    if name == "reverse_components":
        boxes = list(reversed(boxes))
    for box in boxes:
        seeds = _seeds(output if name == "updated_seeds" else grid, box)
        if not seeds:
            continue
        selected = seeds[-1][2]
        if name == "first_seed":
            selected = seeds[0][2]
        elif name == "column_major":
            selected = max(seeds, key=lambda point: (point[1], point[0]))[2]
        elif name == "majority_seed":
            counts = Counter(color for r, c, color in seeds)
            selected = next(color for r, c, color in reversed(seeds) if counts[color] == max(counts.values()))
        elif name == "min_seed":
            selected = min(color for r, c, color in seeds)
        elif name == "max_seed":
            selected = max(color for r, c, color in seeds)
        elif name == "global_last_seed":
            selected = [color for row in grid for color in row if color not in (0, 1)][-1]
        points = _interior(box)
        if name == "fill_border":
            top, left, bottom, right = box
            points = [(r, c) for r in range(top, bottom + 1) for c in range(left, right + 1)]
        for row, col in points:
            if name == "preserve_blue" and grid[row][col] == 1:
                continue
            if name == "zeros_only" and grid[row][col] != 0:
                continue
            output[row][col] = selected
    return output


def _python_apply(value, settings, name=None):
    post = _choice(settings, name)
    grid, boxes = _parse(value)
    filled = _fill(grid, boxes, name)
    if post == "none":
        return filled
    source = grid if name == "pre_fill_largest" else filled
    groups = [obj for obj in _objects(source) if obj["color"] not in ((0,) if name == "include_blue" else (0, 1))]
    if name == "filled_only":
        inside = set().union(*(set(_interior(box)) for box in boxes))
        groups = [obj for obj in groups if obj["cells"] & inside]
    if not groups:
        return filled
    if name == "each_frame_highlight":
        eligible = set().union(*(set(_interior(box)) for box in boxes))
        points = {point for point in eligible if filled[point[0]][point[1]] not in (0, 1)}
    elif name == "largest_color_total":
        areas = Counter()
        for obj in groups:
            areas[obj["color"]] += len(obj["cells"])
        points = set().union(*(obj["cells"] for obj in groups if areas[obj["color"]] == max(areas.values())))
    else:
        def score(obj):
            if name == "bbox_area":
                top, left, bottom, right = _bbox(obj["cells"])
                return (bottom - top + 1) * (right - left + 1)
            return len(obj["cells"])
        best = (min if name == "smallest" else max)(score(obj) for obj in groups)
        chosen = [obj for obj in groups if score(obj) == best]
        if name == "single_largest":
            chosen = chosen[:1]
        points = set().union(*(obj["cells"] for obj in chosen))
    output = deepcopy(filled)
    for row, col in points:
        output[row][col] = 8
    return output


def python_intended(grid, settings):
    """Independent labels; does not call the native transform or fill helper."""
    return _python_apply(grid, settings)


def python_rival(grid, settings, name):
    return _python_apply(grid, settings, name)


def rival_program(settings, name):
    post = _choice(settings, name)
    if name.startswith("native_"):
        return _load_family().program({"post": post})
    box_source = "(map obj-box blue)"
    if name == "complete_frames":
        box_source = "(complete-boxes)"
    elif name == "diagonal_blue":
        box_source = "(blue-eight-boxes)"
    if name == "reverse_components":
        box_source = "(reverse " + box_source + ")"
    source = "out" if name == "updated_seeds" else "g"
    choose = {
        "first_seed": "(third (first seeds))",
        "column_major": "(third (last (sort seeds (lambda (a b) (or (< (second a) (second b)) (and (= (second a) (second b)) (< (first a) (first b))))))))",
        "majority_seed": "(let* ([colors (map third seeds)] [counts (map (lambda (v) (count (lambda (x) (= x v)) colors)) colors)] [best (apply max counts)]) (third (last (filter (lambda (p) (= (count (lambda (x) (= x (third p))) colors) best)) seeds))))",
        "min_seed": "(apply min (map third seeds))", "max_seed": "(apply max (map third seeds))",
        "global_last_seed": "(last (filter (lambda (v) (not (member v '(0 1)))) (append* g)))",
    }.get(name, "(third (last seeds))")
    fill_points = "(box-all bb)" if name == "fill_border" else "(inside bb)"
    write = {"preserve_blue": "(if (= (at g (first p) (second p)) 1) acc (set-cell acc (first p) (second p) color))",
             "zeros_only": "(if (= (at g (first p) (second p)) 0) (set-cell acc (first p) (second p) color) acc)"}.get(
                 name, "(set-cell acc (first p) (second p) color)")
    group_source = "g" if name == "pre_fill_largest" else "filled"
    eligible = "(not (= (obj-color obj) 0))" if name == "include_blue" else "(not (member (obj-color obj) '(0 1)))"
    groups = f"(filter (lambda (obj) {eligible}) (ordered-objects {group_source}))"
    if name == "filled_only":
        groups = f"(filter (lambda (obj) (ormap (lambda (p) (member p interior-cells)) (obj-cells obj))) {groups})"
    score = "(* (+ 1 (- (obj-r2 obj) (obj-r1 obj))) (+ 1 (- (obj-c2 obj) (obj-c1 obj))))" if name == "bbox_area" else "(length (obj-cells obj))"
    chosen = "(filter (lambda (obj) (= (score obj) best)) groups)"
    if name == "single_largest":
        chosen = "(list (first " + chosen + "))"
    points = f"(append* (map obj-cells {chosen}))"
    if name == "largest_color_total":
        points = "(let* ([colors (remove-duplicates (map obj-color groups))] [area (lambda (color) (apply + (map (lambda (obj) (length (obj-cells obj))) (filter (lambda (obj) (= (obj-color obj) color)) groups))))] [maximum (apply max (map area colors))]) (append* (map obj-cells (filter (lambda (obj) (= (area (obj-color obj)) maximum)) groups))))"
    elif name == "each_frame_highlight":
        points = "(filter (lambda (p) (not (member (at filled (first p) (second p)) '(0 1)))) interior-cells)"
    finish = "filled" if post == "none" else f"""(let* ([interior-cells (remove-duplicates (append* (map inside original-boxes)))]
                 [groups {groups}])
      (if (null? groups) filled
        (let* ([score (lambda (obj) {score})]
               [best (apply {'min' if name == 'smallest' else 'max'} (map score groups))]
               [points {points}])
          (for/fold ([out filled]) ([p points]) (set-cell out (first p) (second p) 8)))))"""
    return f"""(rule! (lambda (g)
 (let ()
  (define (key p) (+ (* (cols g) (first p)) (second p)))
  (define (ordered-objects grid) (sort (objects grid 0) (lambda (a b) (< (apply min (map key (obj-cells a))) (apply min (map key (obj-cells b)))))))
  (define (obj-box obj) (list (obj-r1 obj) (obj-c1 obj) (obj-r2 obj) (obj-c2 obj)))
  (define (inside bb) (for*/list ([r (in-range (+ 1 (first bb)) (third bb))] [c (in-range (+ 1 (second bb)) (fourth bb))]) (list r c)))
  (define (box-all bb) (for*/list ([r (in-range (first bb) (+ 1 (third bb)))] [c (in-range (second bb) (+ 1 (fourth bb)))]) (list r c)))
  (define (seed-cells grid bb) (for/list ([p (inside bb)] #:unless (member (at grid (first p) (second p)) '(0 1))) (list (first p) (second p) (at grid (first p) (second p)))))
  (define blue (filter (lambda (obj) (= (obj-color obj) 1)) (ordered-objects g)))
  (define original-boxes (map obj-box blue))
  (define (complete-boxes)
    (for*/list ([r0 (in-range (- (rows g) 2))] [c0 (in-range (- (cols g) 2))]
                [r1 (in-range (+ r0 2) (rows g))] [c1 (in-range (+ c0 2) (cols g))]
                #:when (and (for/and ([c (in-range c0 (+ c1 1))]) (and (= (at g r0 c) 1) (= (at g r1 c) 1)))
                            (for/and ([r (in-range r0 (+ r1 1))]) (and (= (at g r c0) 1) (= (at g r c1) 1)))
                            (not (null? (seed-cells g (list r0 c0 r1 c1))))))
      (list r0 c0 r1 c1)))
  (define (blue-eight-boxes)
    (let ([seen (make-hash)] [directions '((-1 -1) (-1 0) (-1 1) (0 -1) (0 1) (1 -1) (1 0) (1 1))])
      (for*/fold ([boxes '()]) ([r (in-range (rows g))] [c (in-range (cols g))])
        (if (or (not (= (at g r c) 1)) (hash-has-key? seen (list r c))) boxes
          (let* ([start (list r c)]
                 [cells (let walk ([pending (list start)] [found '()])
                          (if (null? pending) found
                            (let ([p (first pending)])
                              (if (hash-has-key? seen p) (walk (rest pending) found)
                                (begin (hash-set! seen p #t)
                                  (walk (append (rest pending)
                                    (filter (lambda (q) (and (<= 0 (first q)) (< (first q) (rows g))
                                      (<= 0 (second q)) (< (second q) (cols g)) (= (at g (first q) (second q)) 1)))
                                      (map (lambda (d) (list (+ (first p) (first d)) (+ (second p) (second d)))) directions)))
                                    (cons p found)))))))])
            (append boxes (list (bbox-of-cells cells))))))))
  (define boxes {box_source})
  (define filled
    (for/fold ([out g]) ([bb boxes])
      (let ([seeds (seed-cells {source} bb)])
        (if (null? seeds) out
          (let ([color {choose}])
            (for/fold ([acc out]) ([p {fill_points}]) {write}))))))
  {finish})))"""


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
    spec = importlib.util.spec_from_file_location("frames_native_family_for_independent_audit", path)
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
    value, boxes = _parse(grid)
    filled = _fill(value, boxes, None)
    groups = [obj for obj in _objects(filled) if obj["color"] not in (0, 1)]
    largest = max(len(obj["cells"]) for obj in groups)
    return {"shape": [len(value), len(value[0])], "blue_components": len(boxes),
            "blue_cells": sum(cell == 1 for row in value for cell in row),
            "input_seed_cells": sum(cell not in (0, 1) for row in value for cell in row),
            "filled_changed_cells": sum(a != b for row_a, row_b in zip(value, filled) for a, b in zip(row_a, row_b)),
            "post_components": len(groups), "largest_component_area": largest,
            "largest_component_ties": sum(len(obj["cells"]) == largest for obj in groups)}


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
            "inactive_post_rivals": "Post-selection alternatives are inactive when post=none.",
        },
        "limits": [
            "Finite declared-rival audit over two settings and seeds 0,17; no universal identification claim.",
            "All six-demo/four-query bank labels are checked by independent Python and protected Racket.",
            "Only the first two demonstrations decide survival; a rival stops at its first refuting demonstration.",
            "Only demo survivors execute queries; query answers never update the survivor set.",
            "Native grammar includes seeded nonrectangular blue objects, overlapping boxes, freestanding colors and 30x30 grids.",
            "Reviewer evidence does not grant owner acceptance, resolve unrelated audits or admit training data.",
        ],
    }
    executor = None
    try:
        source_binding = _source_binding()
        report["source_files_sha256"] = source_binding
        family = _load_family()
        if {_hash(setting) for setting in family.SETTINGS} != {_hash(setting) for setting in SETTINGS}:
            raise AssertionError("native settings differ from the declared post operations")
        canonical = family.program({"post": "none"})
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
