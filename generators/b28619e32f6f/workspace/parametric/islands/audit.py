"""Replay the bounded teaching, count, grammar, Racket and projection audit.

Run through review.py run, from the packet root; see adjacent README.md.
The tool refuses an existing output directory and grants no acceptance.
"""
from __future__ import annotations

import argparse
from collections import Counter
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
TASK = "b28619e32f6f"


def load():
    spec = importlib.util.spec_from_file_location("_b286_audit_adapter", HERE / "adapter.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def raw(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def sha(value):
    return hashlib.sha256(raw(value)).hexdigest()


def rival_programs(p, policy):
    fill = p.FILL_LAMBDA
    def wrap(body):
        return p._compose(body, policy)
    programs = {
        "other_setting": p.program({"island_policy": "absorb" if policy == "keep" else "keep"}),
        "strict_both": wrap(fill.replace("(<= size 8)", "(< size 8)").replace("(<= size 24)", "(< size 24)")),
        "strict_8": wrap(fill.replace("(<= size 8)", "(< size 8)")),
        "strict_24": wrap(fill.replace("(<= size 24)", "(< size 24)")),
        "exact_8_24": wrap(fill.replace("(<= size 8)", "(= size 8)").replace("(<= size 24)", "(= size 24)")),
        "bbox_area": wrap(fill.replace("(size (length region))", """(box (bbox-of-cells region))
             (size (* (+ 1 (- (third box) (first box)))
                      (+ 1 (- (fourth box) (second box)))))""")),
        "fill_exterior": wrap(fill.replace("(if (enclosed? grid (first cell) (second cell))", "(if #t")),
        "identity": "(rule! (lambda (grid) grid))",
        "singleton_connectivity_8": p._compose(fill, policy, 8),
    }
    for color, name in ((8, "all_cyan"), (4, "all_yellow"), (3, "all_green")):
        programs[name] = wrap(fill.replace("(recolor-cells out region fill-color)", f"(recolor-cells out region {color})"))
    connected8 = fill.replace("(find-0-regions grid)", "(map obj-cells (objects-8 grid 2))")
    connected8 = connected8.replace("(enclosed? grid (first cell) (second cell))", """(not
           (ormap (lambda (p) (or (= (first p) 0) (= (second p) 0)
                 (= (first p) (- (rows grid) 1)) (= (second p) (- (cols grid) 1)))) region))""")
    programs["zero_connectivity_8"] = wrap(connected8)
    frame_measure = """(owners
              (filter (lambda (obj)
                (let ((b (bbox-of-cells (obj-cells obj))))
                  (and (< (first b) (first cell)) (< (first cell) (third b))
                       (< (second b) (second cell)) (< (second cell) (fourth b)))))
                (objects grid 0)))
             (size (if (empty? owners) (length region)
               (let ((b (bbox-of-cells (obj-cells (first owners)))))
                 (length (filter (lambda (p)
                   (and (< (first b) (first p)) (< (first p) (third b))
                        (< (second b) (second p)) (< (second p) (fourth b))))
                   (find-color grid 0))))))"""
    programs["per_frame_total"] = wrap(fill.replace("(size (length region))", frame_measure))
    singleton_expr = """(filter (lambda (cell)
        (andmap (lambda (v) (= v 0))
          (neighbors-4 grid (first cell) (second cell) 2))) (find-color grid 2))"""
    programs["reuse_original_regions"] = p.CANONICAL if policy == "keep" else f"""(rule!
      (lambda (grid)
        (let ((old ({fill} grid)))
          (reduce (lambda (out cell)
            (set-cell out (first cell) (second cell)
              (at old (- (first cell) 1) (second cell)))) old {singleton_expr}))))"""
    programs["erase_dominoes_too"] = p.CANONICAL if policy == "keep" else f"""(rule!
      (lambda (grid)
        ({fill} (recolor-cells grid
          (flatmap obj-cells (filter (lambda (obj) (<= (obj-size obj) 6)) (objects grid 0))) 0))))"""
    return programs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        raise SystemExit("Refusing existing audit output; select a new --out")
    args.out.mkdir(parents=True)
    a = load()
    p = a.prototype
    from reviewer_support import load_selected_generator, public_challenge_bytes, public_challenge_id
    from arcpuzzles.parametric_worker import _local_imports, _real_evaluator
    canonical, source, source_hash = load_selected_generator(TASK, root=ROOT)
    start = time.monotonic()
    report = {"schema": "b28619e32f6f-parametric-audit-v1", "task_id": TASK,
              "generator_sha256": source_hash, "canonical_program_sha256": hashlib.sha256(p.CANONICAL.encode()).hexdigest(),
              "status": "running", "training_admitted": False,
              "limits": "Finite declared rivals and sampled seeds; no universal uniqueness or learning-benefit claim.",
              "sampler": {"attempted": 0, "succeeded": 0, "failures": []},
              "racket_labels": [], "racket_teaching": [], "public_projection": {}}
    dimensions, before_areas, after_areas = Counter(), Counter(), Counter()
    for seed in range(12):
        for demos in (2, 3, 6):
            for queries in (1, 4):
                paired = []
                for policy in p.POLICIES:
                    report["sampler"]["attempted"] += 1
                    try:
                        ep = a.generate(seed, {"island_policy": policy}, demos, queries)
                        assert not p.teaching_failures(ep["train"], ep["test"], policy)
                        for pair in ep["train"] + ep["test"]:
                            assert not canonical.self_check(pair["input"])
                            mid = p.intermediate(pair["input"], policy)
                            assert not canonical.self_check(mid)
                            dimensions[f'{len(mid)}x{len(mid[0])}'] += 1
                            before_areas.update(len(r) for r in p.regions(pair["input"]) if not p.exterior(pair["input"], r))
                            after_areas.update(len(r) for r in p.regions(mid) if not p.exterior(mid, r))
                        one = a.generate(seed, {"island_policy": policy}, demos, 1)
                        assert one["train"] == ep["train"] and one["test"] == ep["test"][:1]
                        paired.append([pair["input"] for pair in ep["train"] + ep["test"]])
                        report["sampler"]["succeeded"] += 1
                    except Exception as exc:
                        report["sampler"]["failures"].append({"seed": seed, "demos": demos, "queries": queries,
                            "policy": policy, "error": str(exc)})
                assert len(paired) != 2 or paired[0] == paired[1]
    report["sampler"].update({"seeds": list(range(12)), "demo_counts": [2, 3, 6], "query_counts": [1, 4],
                             "dimensions": dict(dimensions), "before_area_counts": dict(sorted(before_areas.items())),
                             "after_area_counts": dict(sorted(after_areas.items()))})
    examples = []
    runtime = ROOT / "shared/runtime"
    with _local_imports(runtime, HERE):
        apply, identity, bridge = _real_evaluator(runtime)
        report["racket"] = identity
        try:
            for policy in p.POLICIES:
                for seed, demos in ((0, 2), (17, 6)):
                    ep = a.generate(seed, {"island_policy": policy}, demos, 4)
                    for split in ("train", "test"):
                        for index, pair in enumerate(ep[split]):
                            actual = apply(ep["program_solution"], pair["input"])
                            assert actual == pair["output"], ("Racket label mismatch", policy, seed, split, index)
                            report["racket_labels"].append({"policy": policy, "seed": seed, "demos": demos,
                                "split": split, "pair_index": index, "input_sha256": sha(pair["input"]),
                                "output_sha256": sha(actual)})
                    if seed != 0:
                        continue
                    examples.append({"settings": {"island_policy": policy}, "seed": seed, **ep})
                    for name, program in rival_programs(p, policy).items():
                        result = {"policy": policy, "rival": name, "program": program,
                                  "defeated_by_demo": None, "query_disagreements": []}
                        for index, pair in enumerate(ep["train"]):
                            predicted = apply(program, pair["input"])
                            expected = p.rival_outputs(pair["input"], policy)[name]
                            assert predicted == expected, ("Racket/Python rival mismatch", policy, name, index)
                            if predicted != pair["output"]:
                                result.update({"defeated_by_demo": index, "rival_output_sha256": sha(predicted),
                                    "different_cells": sum(x != y for row, out in zip(predicted, pair["output"])
                                                           for x, y in zip(row, out))})
                                break
                        if result["defeated_by_demo"] is None:
                            for index, pair in enumerate(ep["test"]):
                                predicted = apply(program, pair["input"])
                                assert predicted == p.rival_outputs(pair["input"], policy)[name]
                                if predicted != pair["output"]:
                                    result["query_disagreements"].append(index)
                        assert not result["query_disagreements"], result
                        report["racket_teaching"].append(result)
        finally:
            bridge.close()
    (args.out / "examples.private.json").write_bytes(raw({"episodes": examples, "training_admitted": False}))
    public = args.out / "public"
    public.mkdir()
    for ep in examples:
        first = {"train": ep["train"], "test": ep["test"][:1]}
        visible = public_challenge_bytes(first)
        key = public_challenge_id(first)
        assert key == hashlib.sha256(visible).hexdigest()
        hidden = copy.deepcopy(first)
        hidden.update({"settings": {"island_policy": "different"}, "seed": 999, "program": "private"})
        hidden["test"][0]["output"] = [[9]]
        assert public_challenge_bytes(hidden) == visible
        assert public_challenge_id(hidden) == key
        single = a.generate(ep["seed"], ep["settings"], len(ep["train"]), 1)
        assert public_challenge_bytes(single) == visible
        (public / (key + ".json")).write_bytes(visible)
        parsed = json.loads(visible)
        assert set(parsed) == {"train", "test"} and len(parsed["test"]) == 1
        assert set(parsed["test"][0]) == {"input"}
    rejected = []
    for name, bad in (("bool_cell", [[True]]), ("float_cell", [[1.0]]),
                      ("oversized_grid", [[0] * 31]), ("ragged_grid", [[0, 0], [0]])):
        invalid = {"train": [{"input": [[0]], "output": [[0]]}], "test": [{"input": bad}]}
        try:
            public_challenge_bytes(invalid)
        except ValueError:
            rejected.append(name)
        else:
            raise AssertionError("Projection accepted " + name)
    report["public_projection"] = {"first_turn_files": len(examples), "visible_queries_per_file": 1,
        "four_queries_retained_privately_per_setting": True, "first_turn_equal_to_single_query": True,
        "private_field_invariance": True, "hash_exact_public_bytes": True, "rejected_inputs": rejected,
        "delivery_contract": "Controller retains private four-query episode; reveal only next query after prior answer, without total-count/final-turn hints."}
    report["elapsed_seconds"] = round(time.monotonic() - start, 3)
    report["status"] = "passed" if not report["sampler"]["failures"] else "failed"
    (args.out / "audit.json").write_bytes(raw(report))
    print(json.dumps({"status": report["status"], "sampler": {k: report["sampler"][k] for k in ("attempted", "succeeded", "failures")},
                      "racket_labels": len(report["racket_labels"]), "racket_teaching_cases": len(report["racket_teaching"]),
                      "elapsed_seconds": report["elapsed_seconds"]}, indent=2))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
