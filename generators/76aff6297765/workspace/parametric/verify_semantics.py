#!/usr/bin/env python3
"""Bounded, source-bound semantic review using the live protected Racket runtime.

Run from the packet repo, preferably through WORK/run_with_racket.py::

    python generators/76aff6297765/workspace/parametric/verify_semantics.py \
      --out generators/76aff6297765/workspace/parametric/evidence/current/self-review.json

This is authoring evidence, not native qualification or acceptance. The seed
census is explicitly a Python diagnostic. Labels, boundary expectations and
independently authored rival programs are actually executed by protected Racket.
No candidate execution error counts as a refutation.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import time


sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
ADAPTER_PATH = HERE / "adapter.py"
CANONICAL_PATH = ROOT / "shared/data/base/solutions/training/0c9aba6e__76aff6297765.json"
DEFAULT_OUT = HERE / "evidence/current/self-review.json"
SETTINGS = ({"selection": "all"}, {"selection": "largest"})
sys.path.insert(0, str(ROOT / "src"))

from arcpuzzles.parametric_worker import _grid, _local_imports, _real_evaluator  # noqa: E402


def digest_bytes(value):
    return hashlib.sha256(value).hexdigest()


def digest_json(value):
    return digest_bytes(json.dumps(value, sort_keys=True, separators=(",", ":")).encode())


def load_adapter():
    """Import this adjacent source by exact path, never a cached generic module."""
    name = "_76aff6297765_semantic_review_" + digest_bytes(str(ADAPTER_PATH).encode())
    spec = importlib.util.spec_from_file_location(name, ADAPTER_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def check(condition, message):
    if not condition:
        raise AssertionError(message)


def mask_expression(predicate):
    return f"(zip-halves g (lambda (a b) (if {predicate} 8 0)) 7)"


JOINT = mask_expression("(and (zero? a) (zero? b))")


def select_expression(expression, mode="largest", *, connectivity=4,
                      one_only=False, bounding_box=False):
    """Independent Racket selector: pick-max supplies the comparison score."""
    if mode == "all":
        return expression
    detector = "objects" if connectivity == 4 else "objects-8"
    score = "(lambda (part) (* (obj-h part) (obj-w part)))" if bounding_box else "obj-size"
    winners = "(list best)" if one_only else "(filter (lambda (part) (= (score part) (score best))) parts)"
    return f"""(let* ([mask {expression}]
        [parts ({detector} mask 0)] [score {score}]
        [blank (empty-grid (rows mask) (cols mask) 0)])
      (if (null? parts) blank
        (let ([best (pick-max parts score)])
          (paint-objects blank {winners} 8))))"""


def as_program(expression):
    return f"(rule! (lambda (g) {expression}))"


def prefix_expression(selected):
    return f"""(let* ([answer {selected}] [n (count-color answer 8)])
      (grid-from-fn (rows answer) (cols answer)
        (lambda (r c) (if (< (+ (* r (cols answer)) c) n) 8 0))))"""


def rival_programs(mode):
    """Executable hypotheses; none delegates label calculation to Python."""
    predicates = (
        "(and (zero? a) (zero? b))",
        "(and (zero? a) (not (zero? b)))",
        "(and (not (zero? a)) (zero? b))",
        "(and (not (zero? a)) (not (zero? b)))",
    )
    result = {}
    for truth in range(16):
        active = [condition for bit, condition in enumerate(predicates) if truth & (1 << bit)]
        condition = "(or " + " ".join(active) + ")" if active else "#f"
        result[f"occupancy_{truth:04b}"] = as_program(select_expression(mask_expression(condition), mode))
    selected = select_expression(JOINT, mode)
    result["other_setting"] = as_program(select_expression(JOINT, "largest" if mode == "all" else "all"))
    result["equal_values"] = as_program(select_expression(mask_expression("(= a b)"), mode))
    result["count_only_prefix"] = as_program(prefix_expression(selected))
    result["profile_gated_count"] = as_program(f"""(let* (
      [panels (split-at-separator g 7)] [top (first panels)] [bottom (second panels)]
      [same (equal? (grid-colors top 0) (grid-colors bottom 0))]
      [canonical (and (= (rows top) 6) (= (cols top) 4)
        (equal? (grid-colors top) '(0 2)) (equal? (grid-colors bottom) '(0 6)))])
      (if (or same canonical) {selected} {prefix_expression(selected)}))""")
    if mode == "largest":
        result["eight_connected"] = as_program(select_expression(JOINT, connectivity=8))
        result["one_largest_only"] = as_program(select_expression(JOINT, one_only=True))
        result["largest_bbox"] = as_program(select_expression(JOINT, bounding_box=True))
        for source, variable in (("top", "a"), ("bottom", "b")):
            prior = select_expression(mask_expression(f"(zero? {variable})"))
            result[f"preselect_{source}"] = as_program(f"""(let ([prior {prior}] [joint {JOINT}])
              (grid-from-fn (rows joint) (cols joint) (lambda (r c)
                (if (and (= (at prior r c) 8) (= (at joint r c) 8)) 8 0))))""")
    return result


def render(h, w, joint, top_extra=(), bottom_extra=(), *, separator=1, colors=(2, 6)):
    joint, top_extra, bottom_extra = set(joint), set(top_extra), set(bottom_extra)
    check(not (top_extra & bottom_extra), "fixture extras must have disjoint zero sets")
    top = [[0 if (r, c) in joint | top_extra else colors[0] for c in range(w)] for r in range(h)]
    bottom = [[0 if (r, c) in joint | bottom_extra else colors[1] for c in range(w)] for r in range(h)]
    return top + [[7] * w for _ in range(separator)] + bottom


def painted(h, w, cells):
    cells = set(cells)
    return [[8 if (r, c) in cells else 0 for c in range(w)] for r in range(h)]


def boundary_cases():
    pair_a = {(0, 0), (0, 1)}
    pair_b = {(2, 3), (2, 4)}
    singleton = {(1, 2)}
    return (
        ("empty_joint_mask", render(2, 3, (), {(0, 0)}, {(1, 2)}),
         {mode: painted(2, 3, ()) for mode in ("all", "largest")}),
        ("single_cell", [[0], [7], [0]],
         {mode: [[8]] for mode in ("all", "largest")}),
        ("full_single_component", render(2, 2, {(0, 0), (0, 1), (1, 0), (1, 1)}, separator=2),
         {mode: [[8, 8], [8, 8]] for mode in ("all", "largest")}),
        ("tied_maxima_with_smaller_component",
         render(3, 5, pair_a | pair_b | singleton, {(0, 4)}, {(2, 0)}, separator=2),
         {"all": painted(3, 5, pair_a | pair_b | singleton),
          "largest": painted(3, 5, pair_a | pair_b)}),
    )


def summarize_grid(grid):
    return {"sha256": digest_json(grid), "shape": [len(grid), len(grid[0])],
            "marked_cells": sum(cell == 8 for row in grid for cell in row)}


def census(adapter):
    """A bounded Python-only generation/teaching diagnostic, not Racket evidence."""
    successful, pair_count = 0, 0
    for seed in range(32):
        for demos in (2, 3, 6):
            matched_inputs = None
            for setting in SETTINGS:
                episode = adapter.generate(seed, deepcopy(setting), demos=demos, queries=4)
                check(len(episode["train"]) == demos and len(episode["test"]) == 4,
                      f"wrong generation counts: seed={seed}, demos={demos}, setting={setting}")
                inputs = [pair["input"] for split in ("train", "test") for pair in episode[split]]
                check(len({digest_json(grid) for grid in inputs}) == len(inputs),
                      f"duplicate input: seed={seed}, demos={demos}, setting={setting}")
                if matched_inputs is None:
                    matched_inputs = inputs
                else:
                    check(inputs == matched_inputs, f"inputs depend on setting: seed={seed}, demos={demos}")
                for split in ("train", "test"):
                    for pair in episode[split]:
                        _grid(pair["input"])
                        _grid(pair["output"])
                check(not adapter.teaching_check(inputs[:2], setting),
                      f"Python rival survives first two demos: seed={seed}, setting={setting}")
                successful += 1
                pair_count += len(inputs)
    return {"backend": "python_diagnostic", "seeds": list(range(32)),
            "demo_counts": [2, 3, 6], "queries": 4, "settings": list(SETTINGS),
            "successful_episodes": successful, "pair_claims": pair_count,
            "matched_inputs_across_settings": True, "distinct_inputs_per_episode": True,
            "first_two_demos_refute_adapter_named_rivals": True}


def run(report):
    adapter = load_adapter()
    canonical = json.loads(CANONICAL_PATH.read_text())["racket_target"]["target_code"]
    check(adapter.program({"selection": "all"}) == canonical, "default canonical program bytes differ")
    report["canonical_default_byte_identical"] = True
    report["python_census"] = census(adapter)
    print("Python census passed: 192 episodes; starting protected Racket checks.", file=sys.stderr, flush=True)

    programs = {setting["selection"]: adapter.program(setting) for setting in SETTINGS}
    rivals = {mode: rival_programs(mode) for mode in programs}
    report["programs"] = {"selected": programs, "independent_rivals": rivals}
    counts = {"selected_labels": 0, "rival_demo_evaluations": 0,
              "literal_boundary_labels": 0, "causal_witness_evaluations": 0}
    report["racket_evaluation_counts"] = counts
    runtime = ROOT / "shared/runtime"
    with _local_imports(runtime, HERE):
        execute_raw, identity, bridge = _real_evaluator(runtime)
        report["racket"] = identity
        check(identity.get("backend") == "racket" and identity.get("protected") is True,
              "a live protected Racket backend is required")

        def execute(program, grid, category):
            counts[category] += 1
            # Any execution error or malformed grid aborts; it never eliminates a rival.
            return _grid(execute_raw(program, deepcopy(grid)))

        try:
            report["demonstration_only_reviews"] = reviews = []
            for seed in (0, 17):
                for setting in SETTINGS:
                    mode = setting["selection"]
                    episode = adapter.generate(seed, deepcopy(setting), demos=2, queries=4)
                    actual_train, label_records = [], []
                    for split in ("train", "test"):
                        for index, pair in enumerate(episode[split]):
                            actual = execute(programs[mode], pair["input"], "selected_labels")
                            check(actual == pair["output"],
                                  f"Racket label mismatch: {mode}, seed={seed}, {split}[{index}]")
                            label_records.append({"split": split, "index": index,
                                                  "input": summarize_grid(pair["input"]),
                                                  "actual_output": summarize_grid(actual)})
                            if split == "train":
                                actual_train.append(actual)
                    check(label_records[-1]["input"]["shape"] == [30, 30],
                          "fourth query must actually exercise 30x30")
                    refutations, controls = {}, []
                    for name, rival in rivals[mode].items():
                        differences, first_output = [], None
                        for index, pair in enumerate(episode["train"]):
                            actual = execute(rival, pair["input"], "rival_demo_evaluations")
                            if actual != actual_train[index]:
                                differences.append(index)
                                if first_output is None:
                                    first_output = summarize_grid(actual)
                        if name == "occupancy_0001":
                            check(not differences, f"independent intended occupancy control disagrees: {mode}, seed={seed}")
                            controls.append(name)
                        else:
                            check(differences, f"Racket rival survives demonstrations: {name}, {mode}, seed={seed}")
                            refutations[name] = {"disagreeing_demo_indices": differences,
                                                "first_actual_rival_output": first_output}
                    reviews.append({"seed": seed, "settings": setting, "demos_used_for_fitting": 2,
                                    "query_labels_used_for_fitting": 0, "labels": label_records,
                                    "fitting_controls": controls, "refuted_rivals": refutations})
                    print(f"Protected review passed: seed={seed}, selection={mode}, {len(refutations)} refuted rivals.",
                          file=sys.stderr, flush=True)

            report["literal_boundary_cases"] = boundaries = []
            for name, grid, expected_by_mode in boundary_cases():
                case = {"name": name, "input": grid, "outputs": {}}
                for mode, expected in expected_by_mode.items():
                    actual = execute(programs[mode], grid, "literal_boundary_labels")
                    check(actual == expected, f"literal boundary mismatch: {name}, {mode}")
                    case["outputs"][mode] = actual
                boundaries.append(case)

            # Independent, small untransformed motif. No adapter fixture or mirror
            # supplies its expected cells. The rival programs are retained above.
            compact = {(r, c) for r in (0, 1) for c in (0, 1, 2)}
            sparse = {(2, 4), (3, 4), (4, 4), (4, 5), (4, 6)}
            joint = compact | sparse | {(0, 6)}
            original = render(5, 7, joint, {(3, 3), (4, 3), (4, 2)},
                              {(2, 5), (2, 6), (3, 6)}, separator=2, colors=(3, 9))
            expected = painted(5, 7, compact)
            actual = execute(programs["largest"], original, "causal_witness_evaluations")
            check(actual == expected, "literal causal base answer differs")
            witness = {"input": original, "program_key": "selected.largest", "output": actual,
                       "joint_component_sizes": [6, 5, 1], "wrong_order": {}, "interventions": []}
            for source in ("top", "bottom"):
                name = f"preselect_{source}"
                wrong = execute(rivals["largest"][name], original, "causal_witness_evaluations")
                check(wrong == painted(5, 7, sparse), f"wrong-order witness changed: {source}")
                check(wrong != actual, f"wrong-order rule survived: {source}")
                witness["wrong_order"][name] = {"program_key": f"independent_rivals.largest.{name}", "output": wrong}
            for changed, answer_cells, sizes in (
                ([(2, 5)], compact | sparse | {(2, 5)}, [6, 6, 1]),
                ([(2, 5), (2, 6)], sparse | {(2, 5), (2, 6)}, [7, 6, 1]),
            ):
                intervened = deepcopy(original)
                for r, c in changed:
                    intervened[r][c] = 0
                after = execute(programs["largest"], intervened, "causal_witness_evaluations")
                check(after == painted(5, 7, answer_cells), "literal causal intervention answer differs")
                witness["interventions"].append({"top_cells_changed_to_zero": [list(p) for p in changed],
                                                  "joint_component_sizes": sizes, "output": after})
            report["causal_and_wrong_order_witness"] = witness
        finally:
            bridge.close()
    report["limits"] = [
        "Finite authoring evidence; not native qualification, acceptance or a training-admission claim.",
        "Protected Racket checks cover seeds 0 and 17, two demos and four queries per setting.",
        "The 192-episode generation census is a Python diagnostic and does not replay all labels through Racket.",
        "Finite named rivals do not prove unique induction against every possible hypothesis.",
        "Boundary labels and the causal intervention expectations were authored independently of adapter.solve.",
    ]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    start = time.monotonic()
    bound_paths = (ADAPTER_PATH, HERE / "promotion.json", Path(__file__).resolve(), CANONICAL_PATH)
    bindings = {str(path.relative_to(ROOT)): digest_bytes(path.read_bytes()) for path in bound_paths}
    report = {"schema": "arcpuzzles-parametric-semantic-self-review-v1", "task_id": "76aff6297765",
              "status": "failed", "sources": bindings, "errors": []}
    try:
        run(report)
        check(all(digest_bytes((ROOT / name).read_bytes()) == value for name, value in bindings.items()),
              "review source bytes changed during execution")
        report["status"] = "passed"
    except Exception as exc:
        report["errors"].append({"type": type(exc).__name__, "message": str(exc)})
    report["elapsed_seconds"] = round(time.monotonic() - start, 3)
    if "racket_evaluation_counts" in report:
        report["total_racket_evaluations"] = sum(report["racket_evaluation_counts"].values())
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": report["status"], "out": str(args.out),
                      "racket_evaluations": report.get("total_racket_evaluations", 0),
                      "elapsed_seconds": report["elapsed_seconds"], "errors": report["errors"]}, sort_keys=True))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
