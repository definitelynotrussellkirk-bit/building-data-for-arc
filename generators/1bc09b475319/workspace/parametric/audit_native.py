#!/usr/bin/env python3
"""Independent, bounded teaching audit for horizontal caps and cap bridges.

The first two demonstrations alone determine rival survival. Query outputs never
teach later queries. Every retained semantic comparison uses exact executable
Racket and a separately written Python oracle; a runtime error is an audit error,
never a refutation. No universal rule-identification claim is made.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from contextlib import contextmanager
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys


HERE = Path(__file__).resolve()
HOME = HERE.parent
ROOT = next(parent for parent in HERE.parents if (parent / "shared/runtime").is_dir())
TASK_ID = "1bc09b475319"
CANONICAL_SHA256 = "15debbc2b09d7b591e587879a201e865beeaa5153cac1d262ca493c6da156cfd"
BASE_RIVALS = (
    "other_mode", "adjacent_any6", "length2_3_only", "minimum3", "minimum4",
    "left_caps_only", "right_caps_only", "interior_caps_only",
    "interior_bars_only", "vertical_caps", "color7", "overwrite_occupied_caps",
    "maximum5",
)
BRIDGE_RIVALS = (
    "all_cyan_anchors", "original_cyan_anchors", "original_six_anchors",
    "extreme_anchors_only", "ignore_blockers", "zeros_through_blockers",
    "allow_cyan_pass", "one_cell_gap_only", "bridge_only", "horizontal_bridges",
    "global_columns", "same_side_only", "equal_length_only",
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
    if (type(value) is not list or not 7 <= len(value) <= 30
            or type(value[0]) is not list or not 7 <= len(value[0]) <= 30
            or any(type(row) is not list or len(row) != len(value[0])
                   or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
                   for row in value)):
        raise ValueError("audit grammar requires rectangular 7..30 exact integer colors 0..9")
    return deepcopy(value)


def _mode(settings):
    if (type(settings) is not dict or set(settings) != {"cap_mode"}
            or type(settings["cap_mode"]) is not str
            or settings["cap_mode"] not in ("caps", "bridge_caps")):
        raise ValueError("cap_mode must be exactly caps or bridge_caps")
    return settings["cap_mode"]


def rivals(settings):
    return BASE_RIVALS + (BRIDGE_RIVALS if _mode(settings) == "bridge_caps" else ())


def _choice(settings, name=None):
    mode = _mode(settings)
    if name is not None and name not in rivals(settings):
        raise ValueError(f"undeclared rival: {name!r}")
    if name == "other_mode":
        mode = "bridge_caps" if mode == "caps" else "caps"
    return mode


def _run_caps(grid, name=None):
    """Independent maximal-run implementation, not local neighbor predicates."""
    height, width = len(grid), len(grid[0])
    vertical = name == "vertical_caps"
    line_count, line_length = (width, height) if vertical else (height, width)
    caps = defaultdict(set)
    minimum = {"adjacent_any6": 1, "minimum3": 3, "minimum4": 4}.get(name, 2)
    for line in range(line_count):
        sequence = [grid[p][line] if vertical else grid[line][p] for p in range(line_length)]
        index = 0
        while index < line_length:
            if sequence[index] != 6:
                index += 1
                continue
            start = index
            while index < line_length and sequence[index] == 6:
                index += 1
            stop, length = index, index - start
            if length < minimum or (name == "length2_3_only" and length not in (2, 3)):
                continue
            if name == "maximum5" and length > 5:
                continue
            if name == "interior_bars_only" and (start == 0 or stop == line_length):
                continue
            for target, side in ((start - 1, "left"), (stop, "right")):
                if not 0 <= target < line_length:
                    continue
                if name == "left_caps_only" and side != "left":
                    continue
                if name == "right_caps_only" and side != "right":
                    continue
                row, col = (target, line) if vertical else (line, target)
                if name == "interior_caps_only" and (row in (0, height - 1) or col in (0, width - 1)):
                    continue
                if grid[row][col] != 0 and name != "overwrite_occupied_caps":
                    continue
                caps[row, col].add((side, length))
    return caps


def _python_apply(grid, settings, name=None):
    original = _grid(grid)
    mode = _choice(settings, name)
    tags = _run_caps(original, name)
    capped = deepcopy(original)
    color = 7 if name == "color7" else 8
    for row, col in tags:
        capped[row][col] = color
    if mode == "caps":
        return capped
    if name == "all_cyan_anchors":
        anchors = {(r, c) for r, row in enumerate(capped) for c, value in enumerate(row) if value == 8}
    elif name in ("original_cyan_anchors", "original_six_anchors"):
        anchor_color = 8 if name == "original_cyan_anchors" else 6
        anchors = {(r, c) for r, row in enumerate(original) for c, value in enumerate(row)
                   if value == anchor_color}
    else:
        anchors = set(tags)
    horizontal = name == "horizontal_bridges"
    groups = defaultdict(set)
    if name == "global_columns":
        positions = {row for row, _ in anchors}
        groups = {col: positions for col in range(len(original[0]))}
    else:
        for row, col in anchors:
            line, position = (row, col) if horizontal else (col, row)
            groups[line].add(position)
    output = deepcopy(original if name == "bridge_only" else capped)
    for line, coordinates in groups.items():
        positions = sorted(coordinates)
        pairs = list(zip(positions, positions[1:]))
        if name == "extreme_anchors_only":
            pairs = [(positions[0], positions[-1])] if len(positions) > 1 else []
        for low, high in pairs:
            start, end = ((line, low), (line, high)) if horizontal else ((low, line), (high, line))
            if name in ("same_side_only", "equal_length_only"):
                tag_index = 0 if name == "same_side_only" else 1
                if not ({tag[tag_index] for tag in tags[start]} & {tag[tag_index] for tag in tags[end]}):
                    continue
            cells = [(line, p) if horizontal else (p, line) for p in range(low + 1, high)]
            if name == "one_cell_gap_only" and len(cells) > 1:
                continue
            if name not in ("ignore_blockers", "zeros_through_blockers"):
                allowed = (0, 8) if name == "allow_cyan_pass" else (0,)
                if any(capped[r][c] not in allowed for r, c in cells):
                    continue
            for row, col in cells:
                if name != "zeros_through_blockers" or capped[row][col] == 0:
                    output[row][col] = color
    return output


def python_intended(grid, settings):
    """Independent intended labels; never calls or imports the native family."""
    return _python_apply(grid, settings)


def python_rival(grid, settings, name):
    return _python_apply(grid, settings, name)


def rival_program(settings, name):
    """Construct exact Racket hypotheses independently of native_family.py."""
    mode = _choice(settings, name)
    vertical_caps = name == "vertical_caps"
    dr, dc = (1, 0) if vertical_caps else (0, 1)
    minimum = {"adjacent_any6": 1, "minimum3": 3, "minimum4": 4}.get(name, 2)
    length_condition = f"(>= n {minimum})"
    if name == "length2_3_only":
        length_condition = "(or (= n 2) (= n 3))"
    elif name == "maximum5":
        length_condition = "(and (>= n 2) (<= n 5))"
    interior_run = "#t"
    if name == "interior_bars_only":
        position, delta, extent = ("r", "dr", "h") if vertical_caps else ("c", "dc", "w")
        interior_run = (f"(and (> (+ {position} {delta}) 0) "
                        f"(< (+ {position} {delta}) (- {extent} 1)) "
                        f"(> (+ {position} (* {delta} n)) 0) "
                        f"(< (+ {position} (* {delta} n)) (- {extent} 1)))")
    neighbor_condition = ("(positive? r c)" if name == "left_caps_only" else
                          "(negative? r c)" if name == "right_caps_only" else
                          "(or (positive? r c) (negative? r c))")
    target_condition = "(not (= (cell-at g r c) 6))" if name == "overwrite_occupied_caps" else "(= (cell-at g r c) 0)"
    interior_target = "(and (> r 0) (< r (- h 1)) (> c 0) (< c (- w 1)))" if name == "interior_caps_only" else "#t"
    color = 7 if name == "color7" else 8
    initial = f"""[h (rows g)] [w (cols g)]
       [inside? (lambda (r c) (and (<= 0 r) (< r h) (<= 0 c) (< c w)))]
       [stretch (lambda (r c dr dc)
          (let loop ([rr (+ r dr)] [cc (+ c dc)] [n 0])
            (if (and (inside? rr cc) (= (cell-at g rr cc) 6))
                (loop (+ rr dr) (+ cc dc) (+ n 1)) n)))]
       [qualifies? (lambda (r c dr dc)
          (let ([n (stretch r c dr dc)]) (and {length_condition} {interior_run})))]
       [positive? (lambda (r c) (qualifies? r c {dr} {dc}))]
       [negative? (lambda (r c) (qualifies? r c {-dr} {-dc}))]
       [new-caps (for*/list ([r (in-range h)] [c (in-range w)]
                    #:when (and {target_condition} {interior_target} {neighbor_condition}))
                   (list r c))]
       [capped (grid-from-fn h w (lambda (r c)
          (if (member (list r c) new-caps) {color} (cell-at g r c))))]"""
    if mode == "caps":
        return f"(rule! (lambda (g)\n  (let* ({initial}) capped)))"
    anchor_expression = {
        "all_cyan_anchors": "(find-color capped 8)",
        "original_cyan_anchors": "(find-color g 8)",
        "original_six_anchors": "(find-color g 6)",
    }.get(name, "new-caps")
    horizontal = name == "horizontal_bridges"
    line_accessor, position_accessor = ("first", "second") if horizontal else ("second", "first")
    point_expression = "(list line p)" if horizontal else "(list p line)"
    line_count = "h" if horizontal else "w"
    selected_anchors = "anchors" if name == "global_columns" else f"(filter (lambda (p) (= ({line_accessor} p) line)) anchors)"
    adjacent_pairs = """(for/list ([a (in-list ps)] [b (in-list (if (null? ps) '() (rest ps)))])
                            (list a b))"""
    if name == "extreme_anchors_only":
        adjacent_pairs = "(if (< (length ps) 2) '() (list (list (first ps) (last ps))))"
    pair_condition = "#t"
    if name == "same_side_only":
        pair_condition = """(or
              (and (positive? (first a) (second a)) (positive? (first b) (second b)))
              (and (negative? (first a) (second a)) (negative? (first b) (second b))))"""
    elif name == "equal_length_only":
        pair_condition = f"""(ormap (lambda (x) (member x
                (filter (lambda (n) (>= n 2))
                  (list (stretch (first b) (second b) {dr} {dc})
                        (stretch (first b) (second b) {-dr} {-dc})))))
              (filter (lambda (n) (>= n 2))
                (list (stretch (first a) (second a) {dr} {dc})
                      (stretch (first a) (second a) {-dr} {-dc}))))"""
    clear_condition = "(andmap (lambda (p) (= (cell-at capped (first p) (second p)) 0)) cells)"
    if name in ("ignore_blockers", "zeros_through_blockers"):
        clear_condition = "#t"
    elif name == "allow_cyan_pass":
        clear_condition = "(andmap (lambda (p) (member (cell-at capped (first p) (second p)) '(0 8))) cells)"
    gap_condition = "(<= (length cells) 1)" if name == "one_cell_gap_only" else "#t"
    selected_cells = ("(filter (lambda (p) (= (cell-at capped (first p) (second p)) 0)) cells)"
                      if name == "zeros_through_blockers" else "cells")
    base = "g" if name == "bridge_only" else "capped"
    return f"""(rule! (lambda (g)
  (let* ({initial}
       [anchors {anchor_expression}]
       [point (lambda (line p) {point_expression})]
       [pairs (append* (for/list ([line (in-range {line_count})])
          (let* ([ps (sort (remove-duplicates (map {position_accessor} {selected_anchors})) <)]
                 [ends {adjacent_pairs}])
            (for/list ([pair (in-list ends)])
              (list line (first pair) (second pair))))))]
       [bridges (append* (for/list ([span (in-list pairs)])
          (let* ([line (first span)] [lo (second span)] [hi (third span)]
                 [a (point line lo)] [b (point line hi)]
                 [cells (for/list ([p (in-range (+ lo 1) hi)]) (point line p))])
            (if (and {pair_condition} {gap_condition} {clear_condition})
                {selected_cells} '()))))])
    (grid-from-fn h w (lambda (r c)
      (if (member (list r c) bridges) {color} (cell-at {base} r c)))))))"""


class ExecutionCache:
    """Execute each exact program/input pair at most once, including failures."""

    def __init__(self, apply, identity, budget=512):
        self.apply = apply
        self.identity = deepcopy(identity)
        self.budget = budget
        self.request_count = 0
        self.execution_count = 0
        self.programs = {}
        self.inputs = {}
        self.records = {}

    def evaluate(self, program, grid):
        grid = _grid(grid)
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
                if (len(output), len(output[0])) != (len(grid), len(grid[0])):
                    raise ValueError("rival output changed grid dimensions")
            except Exception as error:
                row.update(status="error", error_type=type(error).__name__, error=str(error))
            else:
                row.update(status="ok", output=output, output_sha256=_hash(output))
            self.records[key] = row
        return deepcopy(self.records[key])


@contextmanager
def protected_evaluator():
    """Use the current same-checkout native protected executor, never fallback."""
    runtime = ROOT / "shared/runtime"
    before = list(sys.path)
    sys.path[:0] = [str(ROOT / "src"), str(runtime)]
    try:
        from arcpuzzles.parametric_worker import _local_imports, _real_evaluator
        with _local_imports(runtime, HOME):
            apply, identity, bridge = _real_evaluator(runtime)
            try:
                yield ExecutionCache(apply, identity)
            finally:
                bridge.close()
    finally:
        sys.path[:] = before


def assess_program(executor, name, program, train, queries, oracle=None):
    """Assess a single exact rule; errors never count as refuting demonstrations."""
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
            if oracle is not None and row["output"] != oracle(pair["input"]):
                result.update(status="oracle_mismatch", error={"phase": phase, "index": index,
                                                               "racket_output": row["output"]})
                return result
            if row["output"] != intended:
                if phase == "demo":
                    result.update(status="demo_refuted", refuting_demo_index=index)
                    return result
                result["disagreeing_query_indices"].append(index)
                if result["first_teaching_hole"] is None:
                    result["first_teaching_hole"] = {
                        "train": deepcopy(train), "test": [deepcopy(pair)],
                        "query_index": index, "rival_name": name, "rival_program": program,
                        "rival_output": deepcopy(row["output"]),
                        "minimization": "First disagreeing query with the required two demonstrations; cells not minimized.",
                    }
    result["status"] = "teaching_hole" if result["disagreeing_query_indices"] else "query_agreeing_survivor"
    return result


def assess_rival(executor, settings, name, train, queries):
    return assess_program(executor, name, rival_program(settings, name), train, queries,
                          oracle=lambda grid: python_rival(grid, settings, name))


def _load_family():
    path = HOME / "native_family.py"
    spec = importlib.util.spec_from_file_location("caps_native_family_for_independent_audit", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load same-task native family")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _source_binding():
    paths = [HOME / name for name in ("audit_native.py", "native_family.py", "canonical.rkt",
                                      "adapter.py", "promotion.json")]
    paths += [HOME.parents[1] / "tests/test_native_audit.py",
              ROOT / "src/arcpuzzles/parametric_worker.py",
              ROOT / "src/arcpuzzles/catalog.py",
              ROOT / "shared/runtime/arc_repl/racket_bridge.py",
              ROOT / "shared/runtime/puzzle_generators/rule_wrap.py",
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
        source, output = _grid(pair["input"]), _grid(pair["output"])
        if (len(source), len(source[0])) != (len(output), len(output[0])):
            raise ValueError("intended output dimensions differ from input")
        inputs.append(_hash(source))
    if len(inputs) != len(set(inputs)):
        raise ValueError("bank demonstration/query inputs must be distinct")
    return deepcopy(episode)


def run(out):
    out = Path(out).resolve()
    out.mkdir(parents=True, exist_ok=False)
    source_binding = _source_binding()
    family = _load_family()
    report = {
        "schema": "1bc09b475319-native-teaching-audit-v1", "task_id": TASK_ID,
        "status": "running", "source_files_sha256": source_binding,
        "canonical_program_sha256": CANONICAL_SHA256, "seeds": [0, 17],
        "counts": {"teaching_demos": 2, "verified_bank_demos": 6, "queries": 4},
        "episodes": [], "failures": [],
        "excluded_equivalent_hypotheses": {
            "all_pairs_with_strict_zero_paths": "An intervening new cap blocks a nonconsecutive strict-zero interval.",
            "original_grid_for_consecutive_interval_test": "Consecutive new-cap anchors have no intermediate new cap.",
            "sequential_instead_of_frozen_bridge_updates": "Distinct consecutive intervals have disjoint interiors in each column.",
        },
        "limits": [
            "Finite declared-rival audit over two settings and seeds 0,17; no universal identification claim.",
            "All 6-demo/4-query intended banks are checked against independent Python and protected Racket.",
            "Rivals stop at first demonstration refutation; only demonstration survivors execute queries.",
            "A query label never changes the set of demonstration-surviving hypotheses.",
            "This authoring evidence does not grant native acceptance or training admission.",
        ],
    }
    executor = None
    try:
        if tuple(family.SETTINGS) != ({"cap_mode": "caps"}, {"cap_mode": "bridge_caps"}):
            raise AssertionError("native settings differ from the two declared modes")
        canonical = family.program({"cap_mode": "caps"})
        if _digest(canonical.encode()) != CANONICAL_SHA256:
            raise AssertionError("default program differs from pinned canonical Catalog rule")
        with protected_evaluator() as executor:
            report["racket"] = deepcopy(executor.identity)
            for seed in (0, 17):
                shared_inputs = None
                for settings in family.SETTINGS:
                    bank = _bank(family.generate(seed, deepcopy(settings), demos=6, queries=4))
                    minimum = _bank(family.generate(seed, deepcopy(settings), demos=2, queries=4), demos=2)
                    if minimum["train"] != bank["train"][:2] or minimum["test"] != bank["test"]:
                        raise AssertionError("minimum teaching episode differs from full bank prefix")
                    program = family.program(settings)
                    if bank["program_solution"] != program or minimum["program_solution"] != program:
                        raise AssertionError("episode does not bind the selected exact program")
                    input_hashes = [_hash(pair["input"]) for pair in bank["train"] + bank["test"]]
                    if shared_inputs is not None and input_hashes != shared_inputs:
                        raise AssertionError("input bank changes with cap_mode")
                    shared_inputs = input_hashes
                    intended_executions = []
                    for pair in bank["train"] + bank["test"]:
                        row = executor.evaluate(program, pair["input"])
                        intended_executions.append(row["execution_id"])
                        if row["status"] != "ok":
                            raise AssertionError(f"intended Racket execution error: {row}")
                        independent = python_intended(pair["input"], settings)
                        if row["output"] != pair["output"] or row["output"] != independent:
                            raise AssertionError("intended Racket, independent Python and native labels disagree")
                    assessments = []
                    for name in rivals(settings):
                        assessment = assess_rival(executor, settings, name, minimum["train"], bank["test"])
                        assessments.append(assessment)
                        if assessment["status"] in ("teaching_hole", "execution_error", "oracle_mismatch"):
                            report["failures"].append({"seed": seed, "settings": deepcopy(settings), **assessment})
                    episode_row = {
                        "seed": seed, "settings": deepcopy(settings), "program_sha256": _digest(program.encode()),
                        "train": bank["train"], "test": bank["test"], "input_sha256": input_hashes,
                        "intended_executions": intended_executions, "rivals": assessments,
                        "refuted_rivals": [r["name"] for r in assessments if r["status"] == "demo_refuted"],
                        "query_agreeing_survivors": [r["name"] for r in assessments if r["status"] == "query_agreeing_survivor"],
                        "query_disagreeing_survivors": [r["name"] for r in assessments if r["status"] == "teaching_hole"],
                    }
                    report["episodes"].append(episode_row)
                    print(json.dumps({"seed": seed, "settings": settings,
                                      "refuted": len(episode_row["refuted_rivals"]),
                                      "query_agreeing_survivors": episode_row["query_agreeing_survivors"],
                                      "teaching_holes": episode_row["query_disagreeing_survivors"],
                                      "distinct_racket_evaluations": executor.execution_count}), flush=True)
            if _source_binding() != source_binding:
                raise AssertionError("audited source changed during the run")
            report["status"] = "passed" if not report["failures"] else "failed"
    except Exception as error:
        report["status"] = "failed"
        report["failure"] = {"type": type(error).__name__, "message": str(error)}
    finally:
        if executor is not None:
            report["racket_evaluations"] = executor.execution_count
            report["evaluation_requests"] = executor.request_count
            report["cache_hits"] = executor.request_count - executor.execution_count
            evidence = {"schema": "1bc09b475319-exact-racket-executions-v1",
                        "racket": executor.identity, "programs": executor.programs,
                        "inputs": executor.inputs, "executions": list(executor.records.values())}
            _write_json(out / "executions.json", evidence)
            report["executions_file"] = {"path": "executions.json",
                                          "sha256": _digest((out / "executions.json").read_bytes())}
        _write_json(out / "audit.json", report)
    print(json.dumps({"status": report["status"], "episodes": len(report["episodes"]),
                      "failures": len(report["failures"]), "out": str(out)}), flush=True)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True, help="new task-owned evidence directory")
    args = parser.parse_args()
    return 0 if run(args.out)["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
