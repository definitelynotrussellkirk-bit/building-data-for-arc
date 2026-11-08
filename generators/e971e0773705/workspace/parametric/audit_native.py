"""Bounded, protected semantic-rival audit for the proposed T-tally family.

Python meanings use independent component traversal. Hypotheses are fitted on
demonstrations before queries; failed execution never counts as a refutation.
The private wrong-order witness is deliberately outside the clean lesson core.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys


HOME = Path(__file__).resolve().parent
TASK = HOME.parents[1]
ROOT = HOME.parents[3]
RUNTIME = ROOT / "shared/runtime"
TASK_ID = "e971e0773705"
sys.path[:0] = [str(ROOT / "src"), str(RUNTIME)]
from arcpuzzles.parametric_worker import _grid, _local_imports, _real_evaluator


SETTINGS = ({"count_mode": "raw"}, {"count_mode": "cancel_opposites"})
JOBS = ((0, 5), (17, 5), (22, 6))
MINIMUM_DEMOS = 5
RIVALS = (
    "cap3", "cap2", "blue_cap3", "green_cap3", "presence_only", "majority_four", "swap_roles",
    "blue_majority_four", "green_majority_four",
    "absolute_difference_blue", "total_on_blue", "tie_preserve",
    "cap_before_cancel", "cancel_one_pair", "parity", "connectivity8",
    "ignore_border", "upper_half_only", "left_half_only", "one_per_anchor_row",
)
TOP = ((0, 0), (0, 1), (0, 2), (1, 1))
BOTTOM = ((0, 1), (1, 0), (1, 1), (1, 2))
BLUE = ((0, 3), (2, 3), (0, 5), (2, 5))
GREEN = ((0, 0), (2, 0), (0, 2), (2, 2))


def packed(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _setting(settings):
    if (type(settings) is not dict or set(settings) != {"count_mode"}
            or type(settings["count_mode"]) is not str
            or settings["count_mode"] not in ("raw", "cancel_opposites")):
        raise ValueError("Expected one exact count_mode setting")
    return settings["count_mode"]


def components(grid, connectivity=4):
    if type(connectivity) is not int or connectivity not in (4, 8):
        raise ValueError("Connectivity must be the exact integer4 or8")
    pending = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 2}
    result = []
    while pending:
        origin = min(pending)
        pending.remove(origin)
        stack, group = [origin], {origin}
        while stack:
            r, c = stack.pop()
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if not (dr or dc) or (connectivity == 4 and abs(dr) + abs(dc) != 1):
                        continue
                    point = r + dr, c + dc
                    if point in pending:
                        pending.remove(point)
                        group.add(point)
                        stack.append(point)
        result.append(tuple(sorted(group)))
    return result


def _kind(cells):
    top = min(r for r, c in cells)
    return 0 if sum(r == top for r, c in cells) >= 3 else 1


def facts(grid):
    grid = _grid(grid)
    if {v for row in grid for v in row} != {0, 2}:
        raise ValueError("T input requires colors0 and2")
    groups = components(grid)
    counts = [0, 0]
    for cells in groups:
        r0, c0 = min(r for r, c in cells), min(c for r, c in cells)
        normalized = tuple(sorted((r-r0, c-c0) for r, c in cells))
        if normalized not in (TOP, BOTTOM):
            raise ValueError("Each red four-component must be an exact vertical T")
        counts[_kind(cells)] += 1
    diagonal = len(components(grid, 8)) < len(groups)
    border = sum(any(r in (0, len(grid)-1) or c in (0, len(grid[0])-1) for r, c in cells) for cells in groups)
    residual = [max(counts[0]-counts[1], 0), max(counts[1]-counts[0], 0)]
    return {"input_shape": [len(grid), len(grid[0])], "orientation_counts": counts,
            "component_count": len(groups), "occupied_cells": 4*len(groups),
            "cancelled_pairs": min(counts), "residual_counts": residual,
            "capped_raw_counts": [min(4, value) for value in counts],
            "capped_residual_counts": [min(4, value) for value in residual],
            "diagonal_contacts": diagonal, "border_component_count": border}


def emblem(top, bottom, cap=4):
    result = [[0]*6 for _ in range(3)]
    for r, c in BLUE[:min(top, cap, 4)]:
        result[r][c] = 1
    for r, c in GREEN[:min(bottom, cap, 4)]:
        result[r][c] = 3
    return result


def _counts(grid, name):
    groups = components(grid, 8 if name == "connectivity8" else 4)
    if name == "ignore_border":
        groups = [cells for cells in groups if all(0 < r < len(grid)-1 and 0 < c < len(grid[0])-1 for r, c in cells)]
    elif name == "upper_half_only":
        groups = [cells for cells in groups if 2*min(r for r, c in cells) < len(grid)]
    elif name == "left_half_only":
        groups = [cells for cells in groups if 2*min(c for r, c in cells) < len(grid[0])]
    if name == "one_per_anchor_row":
        keys = {(min(r for r, c in cells), _kind(cells)) for cells in groups}
        return sum(k == 0 for r, k in keys), sum(k == 1 for r, k in keys)
    return sum(_kind(cells) == 0 for cells in groups), sum(_kind(cells) == 1 for cells in groups)


def rival_reference(grid, settings, name):
    mode = _setting(settings)
    facts(grid)
    if name not in ("reference", *RIVALS):
        raise ValueError("Unknown hypothesis: " + name)
    top, bottom = _counts(grid, name)
    if name == "cap_before_cancel":
        top, bottom = min(top, 4), min(bottom, 4)
    if mode == "cancel_opposites":
        paired = (0 if name == "tie_preserve" and top == bottom else
                  min(top, bottom, 1) if name == "cancel_one_pair" else min(top, bottom))
        top, bottom = top-paired, bottom-paired
    if name == "presence_only":
        top, bottom = int(top > 0), int(bottom > 0)
    elif name == "majority_four":
        top, bottom = (4 if top > bottom else 0), (4 if bottom > top else 0)
    elif name == "blue_majority_four":
        top = 4 if top > bottom else 0
    elif name == "green_majority_four":
        bottom = 4 if bottom > top else 0
    elif name == "swap_roles":
        top, bottom = bottom, top
    elif name == "absolute_difference_blue":
        top, bottom = abs(top-bottom), 0
    elif name == "total_on_blue":
        top, bottom = top+bottom, 0
    elif name == "parity":
        top, bottom = top % 2, bottom % 2
    elif name == "blue_cap3":
        top = min(top, 3)
    elif name == "green_cap3":
        bottom = min(bottom, 3)
    return emblem(top, bottom, 3 if name == "cap3" else 2 if name == "cap2" else 4)


def reference(grid, settings):
    return rival_reference(grid, settings, "reference")


def rival_program(settings, name):
    """Complete independent Racket implementation of each named interpretation."""
    mode = _setting(settings)
    if name not in ("reference", *RIVALS):
        raise ValueError("Unknown hypothesis: " + name)
    discover = "objects-8" if name == "connectivity8" else "objects"
    selection = f"({discover} g 0)"
    if name == "ignore_border":
        selection = f"(filter (lambda (o) (and (> (obj-r1 o) 0) (> (obj-c1 o) 0) (< (obj-r2 o) (- (rows g) 1)) (< (obj-c2 o) (- (cols g) 1)))) {selection})"
    elif name == "upper_half_only":
        selection = f"(filter (lambda (o) (< (* 2 (obj-r1 o)) (rows g))) {selection})"
    elif name == "left_half_only":
        selection = f"(filter (lambda (o) (< (* 2 (obj-c1 o)) (cols g))) {selection})"
    if name == "one_per_anchor_row":
        counts = "(keys (remove-duplicates (map (lambda (o) (list (obj-r1 o) (kind o))) os)))\n           (a (count-if (lambda (k) (= (second k) 0)) keys))\n           (b (count-if (lambda (k) (= (second k) 1)) keys))"
    else:
        counts = "(a (count-if (lambda (o) (= (kind o) 0)) os))\n           (b (count-if (lambda (o) (= (kind o) 1)) os))"
    pre_a, pre_b = ("(min a 4)", "(min b 4)") if name == "cap_before_cancel" else ("a", "b")
    paired = ("0" if mode == "raw" else "(min pa pb 1)" if name == "cancel_one_pair"
              else "(if (= pa pb) 0 (min pa pb))" if name == "tie_preserve"
              else "(min pa pb)")
    final_a, final_b = "ra", "rb"
    if name == "presence_only":
        final_a, final_b = "(if (> ra 0) 1 0)", "(if (> rb 0) 1 0)"
    elif name == "majority_four":
        final_a, final_b = "(if (> ra rb) 4 0)", "(if (> rb ra) 4 0)"
    elif name == "blue_majority_four":
        final_a = "(if (> ra rb) 4 0)"
    elif name == "green_majority_four":
        final_b = "(if (> rb ra) 4 0)"
    elif name == "swap_roles":
        final_a, final_b = "rb", "ra"
    elif name == "absolute_difference_blue":
        final_a, final_b = "(abs (- ra rb))", "0"
    elif name == "total_on_blue":
        final_a, final_b = "(+ ra rb)", "0"
    elif name == "parity":
        final_a, final_b = "(remainder ra 2)", "(remainder rb 2)"
    elif name == "blue_cap3":
        final_a = "(min ra 3)"
    elif name == "green_cap3":
        final_b = "(min rb 3)"
    cap = 3 if name == "cap3" else 2 if name == "cap2" else 4
    return f"""(rule! (lambda (g)
  (define (kind o)
    (if (>= (count-if (lambda (p) (= (first p) (obj-r1 o))) (obj-cells o)) 3) 0 1))
  (let* ((os {selection})
           {counts}
           (pa {pre_a}) (pb {pre_b}) (paired {paired})
           (ra (- pa paired)) (rb (- pb paired))
           (aout (min {cap} {final_a})) (bout (min {cap} {final_b}))
           (blue (take (list (list 0 3) (list 2 3) (list 0 5) (list 2 5)) aout))
           (green (take (list (list 0 0) (list 2 0) (list 0 2) (list 2 2)) bout)))
    (grid-from-fn 3 6 (lambda (r c)
      (cond ((member (list r c) blue) 1)
            ((member (list r c) green) 3)
            (else 0)))))))"""


class CachedEvaluator:
    def __init__(self, apply):
        self.apply, self.cache = apply, {}
        self.requests = self.evaluations = self.cache_hits = 0
        self.last_request = None

    def __call__(self, program, grid):
        self.requests += 1
        key = program, packed(grid)
        if key in self.cache:
            self.cache_hits += 1
            return deepcopy(self.cache[key])
        self.last_request = {"program_sha256": sha(program.encode()), "input_sha256": sha(key[1])}
        self.evaluations += 1
        result = _grid(self.apply(program, deepcopy(grid)))
        self.cache[key] = deepcopy(result)
        return result


def assess(name, program, train, test, execute, *, prefix_count=None):
    if prefix_count is not None and (type(prefix_count) is not int or not 1 <= prefix_count < len(train)):
        raise ValueError("A diagnostic prefix must be shorter than the full demonstration set")
    outputs = [execute(program, pair["input"]) for pair in train]
    rejected = [i for i, (out, pair) in enumerate(zip(outputs, train)) if out != pair["output"]]
    survives = not rejected
    prefix = prefix_count is not None and not any(i < prefix_count for i in rejected)
    checked_for = (["all_demonstrations"] if survives else []) + ([f"first_{prefix_count}_prefix"] if prefix else [])
    queries = [execute(program, pair["input"]) for pair in test] if checked_for else None
    differences = ([i for i, (out, pair) in enumerate(zip(queries, test)) if out != pair["output"]]
                   if queries is not None else None)
    return {"name": name, "program_sha256": sha(program.encode()), "demo_outputs": outputs,
            "rejected_by_demo_indices": rejected, "survives_demonstrations": survives,
            "short_prefix_demo_count": prefix_count, "survives_short_prefix": prefix, "query_checked_for": checked_for,
            "query_outputs": queries, "query_disagreement_indices": differences}


def _load(path):
    name = "_tally_audit_" + sha(str(path).encode())[:16]
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def source_binding():
    paths = list(HOME.glob("*.py")) + list((TASK / "tests").glob("*.py")) + list(HOME.glob("*.rkt"))
    paths += [TASK / "generator.py", HOME / "promotion.json", ROOT / "shared/data/canonical/puzzles.jsonl",
              ROOT / "src/arcpuzzles/parametric_worker.py",
              RUNTIME / "puzzle_generators/rule_wrap.py", RUNTIME / "arc_repl/racket_bridge.py"]
    return {p.relative_to(ROOT).as_posix(): sha(p.read_bytes()) for p in sorted(set(paths)) if p.is_file()}


def literal_scene(top, bottom, *, reverse=False):
    """Independent small lawful layout for the incremental teaching witness."""
    shapes = [TOP] * top + [BOTTOM] * bottom
    if reverse:
        shapes.reverse()
    grid = [[0] * 18 for _ in range(max(8, 3*((len(shapes)+3)//4)+2))]
    for i, shape in enumerate(shapes):
        row, col = 1+3*(i//4), 1+4*(i%4)
        for dr, dc in shape:
            grid[row+dr][col+dc] = 2
    facts(grid)
    return grid


def before_witness(adapter, programs, engine):
    """Declared settings identify cancellation while wrong-order still survives."""
    start = engine.requests, engine.evaluations, engine.cache_hits
    settings = {"count_mode": "cancel_opposites"}
    demos = [literal_scene(5, 0), literal_scene(0, 5, reverse=True),
             literal_scene(3, 1), literal_scene(1, 3, reverse=True), literal_scene(2, 2)]
    query = literal_scene(8, 3, reverse=True)
    candidates = {**programs, "cap_before_cancel": rival_program(settings, "cap_before_cancel")}
    demo_outputs = {name: [engine(program, grid) for grid in demos] for name, program in candidates.items()}
    survivors = [name for name, outputs in demo_outputs.items() if outputs == demo_outputs["cancel_opposites"]]
    if survivors != ["cancel_opposites", "cap_before_cancel"]:
        raise AssertionError("Wrong-order witness does not isolate the intended incremental gap")
    query_outputs = {name: engine(program, query) for name, program in candidates.items()}
    if query_outputs["cancel_opposites"] == query_outputs["cap_before_cancel"]:
        raise AssertionError("Wrong-order witness has no query disagreement")
    episode = adapter.generate(0, settings, MINIMUM_DEMOS, 4)
    repair = next(p for p in episode["train"] if p["input"] not in demos+[query]
                  and facts(p["input"])["orientation_counts"][0] > facts(p["input"])["orientation_counts"][1]
                  and reference(p["input"], settings) != rival_reference(p["input"], settings, "cap_before_cancel"))
    repair_outputs = {name: engine(program, repair["input"]) for name, program in candidates.items()}
    repair_counts = facts(repair["input"])["orientation_counts"]
    replace_index = 0 if repair_counts[0] > repair_counts[1] else 1
    keep = [i for i in range(len(demos)) if i != replace_index]
    repaired_survivors = [name for name in candidates if all(demo_outputs[name][i] == demo_outputs["cancel_opposites"][i]
                          for i in keep)
                          and repair_outputs[name] == repair_outputs["cancel_opposites"]]
    if repaired_survivors != ["cancel_opposites"]:
        raise AssertionError("Distinct repair demonstration does not remove the rival")
    repaired_inputs = [repair["input"] if i == replace_index else grid for i, grid in enumerate(demos)]
    orientations = []
    for grid in repaired_inputs:
        a, b = facts(grid)["orientation_counts"]
        orientations.append((a > b) - (a < b))
    if set(orientations) != {-1, 0, 1} or query in repaired_inputs:
        raise AssertionError("Repair must retain both winners, the tie and query novelty")
    repaired_output_counts = []
    for grid in repaired_inputs:
        output = reference(grid, settings)
        repaired_output_counts.append([sum(v == 1 for row in output for v in row),
                                       sum(v == 3 for row in output for v in row)])
    if {tuple(counts) for counts in repaired_output_counts} != {(4, 0), (0, 4), (2, 0), (0, 2), (0, 0)}:
        raise AssertionError("Repair must retain saturated and sub-cap results for both colors plus a tie")
    for name in candidates:
        for grid, actual in zip(demos+[query, repair["input"]], demo_outputs[name]+[query_outputs[name], repair_outputs[name]]):
            expected = (rival_reference(grid, settings, name) if name == "cap_before_cancel"
                        else reference(grid, {"count_mode": name}))
            if actual != expected:
                raise AssertionError("Wrong-order witness interpretation differs from Racket")
    return {"schema": "e971e0773705-wrong-order-teaching-witness-v1",
            "status": "reproduced_expected_incremental_gate_failure", "visibility": "controller_private",
            "scope": "Constructed five-demo weak lesson outside the clean core. Both colors have saturated and sub-cap examples, and balanced counts teach zero remainder. The declared settings identify cancellation; an extra cap-before-cancellation rule survives all demonstrations and differs on the novel query. This is not a native qualification receipt.",
            "training_admitted": False, "fit_frozen_before_query": True,
            "train": [{"input": g, "output": out} for g, out in zip(demos, demo_outputs["cancel_opposites"])],
            "query": {"input": query}, "programs": candidates, "demo_executed_outputs": demo_outputs,
            "query_executed_outputs": query_outputs, "demo_survivors": survivors,
            "declared_survivors": [name for name in survivors if name in programs],
            "query_difference_cells": sum(a != b for ra, rb in zip(query_outputs["cancel_opposites"], query_outputs["cap_before_cancel"]) for a, b in zip(ra, rb)),
            "facts": {"train": [facts(g) for g in demos], "query": facts(query)},
            "execution": {"requests": engine.requests-start[0], "racket_evaluations": engine.evaluations-start[1], "cache_hits": engine.cache_hits-start[2]},
            "repair": {"action": "replace the weak example with the same winning orientation", "demonstration_count": len(demos),
                       "replaced_demo_index": replace_index, "winner_signs_after_repair": orientations,
                       "output_counts_after_repair": repaired_output_counts,
                       "pair": repair, "candidate_outputs": repair_outputs, "remaining_hypotheses": repaired_survivors,
                       "original_query_retained": True, "query_remains_novel": True}}


def short_prefix_tie_witness(adapter, programs, engine):
    """Explain the supported minimum using the actual first five teaching pairs."""
    settings = {"count_mode": "cancel_opposites"}
    episode = adapter.generate(0, settings, MINIMUM_DEMOS, 4)
    train, query = episode["train"][:-1], episode["train"][-1]
    chosen = programs["cancel_opposites"]
    rival = rival_program(settings, "tie_preserve")
    candidates = {"cancel_opposites": chosen, "tie_preserve": rival}
    demo_outputs = {name: [engine(program, p["input"]) for p in train] for name, program in candidates.items()}
    if demo_outputs["cancel_opposites"] != demo_outputs["tie_preserve"]:
        raise AssertionError("Actual four-demo prefix unexpectedly distinguishes tie behavior")
    query_outputs = {name: engine(program, query["input"]) for name, program in candidates.items()}
    if query_outputs["cancel_opposites"] == query_outputs["tie_preserve"]:
        raise AssertionError("Fifth demonstration does not distinguish tie behavior")
    for name, program in candidates.items():
        for pair, actual in zip(train+[query], demo_outputs[name]+[query_outputs[name]]):
            expected = reference(pair["input"], settings) if name == "cancel_opposites" else rival_reference(pair["input"], settings, name)
            if actual != expected:
                raise AssertionError("Tie-preserve program meaning differs from Racket")
    return {"schema": "e971e0773705-minimum-demo-tie-witness-v1", "status": "reproduced_expected_unsupported_prefix_ambiguity",
            "visibility": "controller_private", "training_admitted": False,
            "scope": "The unsupported four-demo prefix fits both hypotheses. The ordinary fifth demonstration refutes tie-preserve; this motivates minimum5 rather than claiming a supported-episode failure.",
            "settings": settings, "train": train, "query": {"input": query["input"]},
            "programs": candidates, "demo_executed_outputs": demo_outputs,
            "query_executed_outputs": query_outputs, "fit_frozen_before_query": True,
            "held_out_demo_difference_cells": sum(a != b for ra, rb in zip(query_outputs["cancel_opposites"], query_outputs["tie_preserve"]) for a, b in zip(ra, rb)),
            "unsupported_demo_count": len(train), "supported_minimum_demos": MINIMUM_DEMOS,
            "repair": "Keep the existing fifth balanced-count demonstration."}


def run(out):
    out = Path(out).resolve()
    out.mkdir(parents=True, exist_ok=False)
    private = out / "private"
    private.mkdir()
    report = {"schema": "e971e0773705-native-finite-audit-v1", "status": "running",
              "visibility": "controller_private", "training_admitted": False,
              "source_files_sha256": source_binding(), "settings": deepcopy(SETTINGS),
              "jobs": [{"seed": seed, "demos": demos, "queries": 4} for seed, demos in JOBS],
              "extra_rivals": list(RIVALS), "programs": {}, "episodes": [],
              "findings": [], "unsupported_four_demo_prefix_findings": [],
              "limits": "Six supported 5/6-demo episodes and twenty extra finite interpretations. Demonstration fits precede queries; equivalent survivors are allowed. Four-demo prefixes are unsupported and reported diagnostically only. No universal identifiability, owner acceptance or training admission. Size extension remains separate from the production generator's calibrated sampling grammar."}
    bridge, engine, phase = None, None, "setup"
    try:
        with _local_imports(RUNTIME, HOME):
            from arcpuzzles import Catalog
            adapter = _load(HOME / "adapter.py")
            apply, identity, bridge = _real_evaluator(RUNTIME)
            if identity.get("backend") != "racket" or identity.get("protected") is not True:
                raise ValueError("Protected Racket is required")
            report["racket"] = identity
            engine = CachedEvaluator(apply)
            programs = {s["count_mode"]: adapter.program(deepcopy(s)) for s in SETTINGS}
            canonical = {v["program_solution"] for v in Catalog(ROOT).get(TASK_ID)["variants"] if isinstance(v.get("program_solution"), str)}
            if canonical != {programs["raw"]}:
                raise AssertionError("Native default differs from exact canonical source")
            def retain(program):
                identifier = sha(program.encode())
                report["programs"][identifier] = program
                return identifier
            phase = "incremental_wrong_order_teaching_witness"
            witness = before_witness(adapter, programs, engine)
            witness.update({"source_files_sha256": report["source_files_sha256"], "racket": identity})
            (private / "before-witness.json").write_text(json.dumps(witness, indent=2, sort_keys=True)+"\n")
            report["before_witness"] = {"path": "private/before-witness.json", "status": witness["status"],
                                        "query_difference_cells": witness["query_difference_cells"]}
            phase = "unsupported_four_demo_tie_witness"
            tie_witness = short_prefix_tie_witness(adapter, programs, engine)
            tie_witness.update({"source_files_sha256": report["source_files_sha256"], "racket": identity})
            (private / "minimum-demo-witness.json").write_text(json.dumps(tie_witness, indent=2, sort_keys=True)+"\n")
            report["minimum_demo_witness"] = {"path": "private/minimum-demo-witness.json", "status": tie_witness["status"],
                                              "held_out_demo_difference_cells": tie_witness["held_out_demo_difference_cells"]}
            for seed, demos in JOBS:
                shared_inputs = None
                for settings in SETTINGS:
                    mode = settings["count_mode"]
                    phase = f"generate:{seed}:{demos}:{mode}"
                    episode = adapter.generate(seed, deepcopy(settings), demos, 4)
                    if episode["program_solution"] != programs[mode]:
                        raise AssertionError("Episode does not retain exact setting program")
                    pairs = {}
                    for split, count in (("train", demos), ("test", 4)):
                        if type(episode[split]) is not list or len(episode[split]) != count:
                            raise ValueError("Incorrect requested pair count")
                        pairs[split] = [{"input": _grid(p["input"]), "output": _grid(p["output"])} for p in episode[split]]
                    inputs = [p["input"] for p in pairs["train"]+pairs["test"]]
                    if len({packed(g) for g in inputs}) != len(inputs):
                        raise AssertionError("Episode inputs are not distinct")
                    if shared_inputs is not None and shared_inputs != inputs:
                        raise AssertionError("Matched input bank differs across settings")
                    shared_inputs = inputs
                    for pair in pairs["train"]+pairs["test"]:
                        phase = f"reference:{seed}:{demos}:{mode}"
                        actual = engine(programs[mode], pair["input"])
                        if actual != pair["output"] or actual != reference(pair["input"], settings):
                            raise AssertionError("Claim label or independent reference differs from Racket")
                    scene_facts = [facts(g) for g in inputs]
                    record = {"seed": seed, "settings": deepcopy(settings), "demos": demos, "queries": 4,
                              "program_sha256": retain(programs[mode]), **pairs, "hypotheses": [],
                              "scene_facts": {"train": scene_facts[:demos], "test": scene_facts[demos:]}}
                    report["episodes"].append(record)
                    hypotheses = [("declared:"+s["count_mode"], programs[s["count_mode"]], s) for s in SETTINGS]
                    hypotheses += [(name, rival_program(settings, name), None) for name in RIVALS]
                    survivors = []
                    for name, program, declared in hypotheses:
                        phase = f"hypothesis:{seed}:{demos}:{mode}:{name}"
                        retain(program)
                        def execute(source, grid, name=name, declared=declared):
                            actual = engine(source, grid)
                            expected = reference(grid, declared) if declared is not None else rival_reference(grid, settings, name)
                            if actual != expected:
                                raise AssertionError("Racket hypothesis differs from independent meaning: "+name)
                            return actual
                        row = assess(name, program, pairs["train"], pairs["test"], execute, prefix_count=MINIMUM_DEMOS-1)
                        record["hypotheses"].append(row)
                        if declared is not None and row["survives_demonstrations"]:
                            survivors.append(declared["count_mode"])
                        finding = {"episode_index": len(report["episodes"])-1, "seed": seed,
                                   "settings": deepcopy(settings), "rival": name,
                                   "query_indices": row["query_disagreement_indices"]}
                        if row["survives_demonstrations"] and row["query_disagreement_indices"]:
                            report["findings"].append(dict(finding, kind="demo_survivor_query_disagreement"))
                        if row["survives_short_prefix"] and row["query_disagreement_indices"]:
                            report["unsupported_four_demo_prefix_findings"].append(dict(finding, kind="unsupported_prefix_survivor_query_disagreement"))
                    record["declared_survivors"] = survivors
                    record["extra_survivors"] = [r["name"] for r in record["hypotheses"] if not r["name"].startswith("declared:") and r["survives_demonstrations"]]
                    if survivors != [mode]:
                        report["findings"].append({"kind": "declared_setting_not_identified", "episode_index": len(report["episodes"])-1})
                    large = [f for f in scene_facts[demos:] if f["input_shape"] == [30, 30]]
                    stress_ok = bool(large and max(f["component_count"] for f in large) >= 30
                                     and max(f["occupied_cells"] for f in large) >= 120)
                    record["stress_check"] = {"passed": stress_ok, "scope": "30x30 query with at least30 exactTs/120occupiedcells, not a padded small scene."}
                    if not stress_ok:
                        report["findings"].append({"kind": "insufficient_boundary_stress", "episode_index": len(report["episodes"])-1})
                    print(json.dumps({"seed": seed, "demos": demos, "count_mode": mode,
                                      "racket_evaluations": engine.evaluations,
                                      "extra_survivors": record["extra_survivors"],
                                      "findings": len(report["findings"]),
                                      "unsupported_prefix_findings": len(report["unsupported_four_demo_prefix_findings"])}), flush=True)
            if source_binding() != report["source_files_sha256"]:
                raise AssertionError("Source bytes changed during audit")
            report["reference_label_count"] = sum(demos+4 for seed, demos in JOBS)*2
            report["matched_inputs_across_settings"] = True
            report["status"] = "failed" if report["findings"] else "passed"
    except Exception as error:
        report["status"] = "failed"
        report["execution_failure"] = {"phase": phase, "type": type(error).__name__, "message": str(error),
                                       "last_native_request": engine.last_request if engine else None}
    finally:
        if bridge is not None:
            bridge.close()
        if engine is not None:
            report["execution"] = {"requests": engine.requests, "racket_evaluations": engine.evaluations,
                                   "cache_hits": engine.cache_hits, "successful_cached_results": len(engine.cache)}
        (private/"audit.json").write_text(json.dumps(report, indent=2, sort_keys=True)+"\n")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    report = run(args.out)
    print(json.dumps({key: report[key] for key in ("status", "execution", "findings", "unsupported_four_demo_prefix_findings") if key in report}, sort_keys=True))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
