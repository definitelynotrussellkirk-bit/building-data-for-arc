#!/usr/bin/env python3
"""Bounded, private Racket self-review of the native aligned-panel family.

Rivals survive solely by fitting the demonstrations. Query answers are consulted
only after that decision. A surviving equivalent rule is harmless on the tested
queries; a survivor that predicts a different query answer makes this command
fail. This is a finite teaching check, not universal identification or approval.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

from arc_repl import racket_bridge
from puzzle_generators import rule_wrap
from reviewer_support import find_root, public_challenge_bytes, public_challenge_id


HOME = Path(__file__).resolve().parent
TASK = "79353e95283d"
OPERATIONS = ("and", "or", "xor", "overlap_components")
SCHEMA = "aligned-panels-native-self-review-v1"


def _hash(value):
    if type(value) is not bytes:
        value = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(value).hexdigest()


def _load_native():
    path = HOME / "native.py"
    if path.is_symlink() or not path.is_file():
        raise ValueError("the adjacent native.py must be a regular source file")
    body = path.read_bytes()
    name = "_panels_audited_native_" + _hash(str(path)) + _hash(body)
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    exec(compile(body, str(path), "exec"), module.__dict__)
    return module


def _callable(program):
    # Reuse the repository's normalization, including rule! and lambda handling.
    source = program if program.lstrip().startswith("(rule!") else "(rule! " + program + ")"
    return rule_wrap.wrap_rule(source)


def _grid(value):
    if (type(value) is not list or not 1 <= len(value) <= 30
            or type(value[0]) is not list or not 1 <= len(value[0]) <= 30
            or any(type(row) is not list or len(row) != len(value[0])
                   or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
                   for row in value)):
        raise ValueError("Racket must return an exact integer rectangular ARC grid")
    return value


def _difference(expected, actual):
    if len(expected) != len(actual) or len(expected[0]) != len(actual[0]):
        return {"kind": "shape", "expected": [len(expected), len(expected[0])],
                "actual": [len(actual), len(actual[0])]}
    for r, (wanted, observed) in enumerate(zip(expected, actual)):
        for c, (a, b) in enumerate(zip(wanted, observed)):
            if a != b:
                return {"kind": "cell", "row": r, "col": c, "expected": a, "actual": b}
    return None


def _pointwise(mask):
    values = " ".join(str(2 * ((mask >> state) & 1)) for state in range(4))
    return f"""(lambda (g)
  (build-grid (rows g) 3 (r c)
    (list-ref '({values}) (+ (* 2 (at g r c)) (at g r (+ c 4))))))"""


SEEDS = """(for*/list ([r (in-range (rows g))] [c (in-range 3)]
                    #:when (and (= 1 (at g r c)) (= 1 (at g r (+ c 4)))))
             (list r c))"""


def _components(*, left=False, diagonal=False, first_seed=False, largest=False, boxes=False,
                exactly_one=False, strict_majority=False):
    panel_cell = "(at g r c)" if left else "(at g r (+ c 4))"
    object_finder = "objects-8" if diagonal else "objects"
    seeds = "(if (null? all-seeds) '() (list (first all-seeds)))" if first_seed else "all-seeds"
    seed_count = "(count (lambda (p) (member p seeds)) (obj-cells o))"
    if largest:
        selected = "(if (null? components) '() (list (pick-max components obj-size)))"
    elif exactly_one:
        selected = f"(filter (lambda (o) (= 1 {seed_count})) components)"
    elif strict_majority:
        selected = f"(filter (lambda (o) (> (* 2 {seed_count}) (obj-size o))) components)"
    else:
        selected = "(filter (lambda (o) (ormap (lambda (p) (member p seeds)) (obj-cells o))) components)"
    cells = ("""(apply append
                    (map (lambda (o)
                      (for*/list ([r (in-range (obj-r1 o) (+ 1 (obj-r2 o)))]
                                  [c (in-range (obj-c1 o) (+ 1 (obj-c2 o)))])
                        (list r c))) selected))""" if boxes
             else "(apply append (map obj-cells selected))")
    return f"""(lambda (g)
  (let* ([panel (build-grid (rows g) 3 (r c) {panel_cell})]
         [all-seeds {SEEDS}]
         [seeds {seeds}]
         [components ({object_finder} panel 0)]
         [selected {selected}]
         [reached {cells}])
    (build-grid (rows g) 3 (r c)
      (if (member (list r c) reached) 2 0))))"""


def _one_hop():
    return f"""(lambda (g)
  (let ([seeds {SEEDS}])
    (build-grid (rows g) 3 (r c)
      (if (and (= 1 (at g r (+ c 4)))
               (ormap (lambda (p)
                 (<= (+ (abs (- r (first p))) (abs (- c (second p)))) 1)) seeds))
          2 0))))"""


def rivals(intended_program):
    """Fixed finite rivals; construction never examines a demonstration label."""
    descriptions = {0: "all zero", 6: "XOR", 8: "AND", 10: "copy right",
                    12: "copy left", 14: "OR", 15: "all two"}
    rows = [{"id": f"truth_table_{mask:02d}",
             "description": descriptions.get(mask, "coordinatewise Boolean truth table"),
             "truth_state_order": ["00", "01", "10", "11"],
             "program": _pointwise(mask)} for mask in range(16)]
    rows.extend([
        {"id": "diagonal_components", "description": "use eight-neighbor right components",
         "program": _components(diagonal=True)},
        {"id": "left_components", "description": "grow overlap seeds in the left panel",
         "program": _components(left=True)},
        {"id": "one_hop", "description": "expand seeds only one cardinal step",
         "program": _one_hop()},
        {"id": "first_seed_only", "description": "use only the row-major first overlap seed",
         "program": _components(first_seed=True)},
        {"id": "largest_component", "description": "paint only the largest right component; ties use row-major order",
         "program": _components(largest=True)},
        {"id": "component_boxes", "description": "fill each selected component's bounding box",
         "program": _components(boxes=True)},
        {"id": "exactly_one_overlap", "description": "select only right components with exactly one overlap seed",
         "program": _components(exactly_one=True)},
        {"id": "strict_majority_overlap", "description": "select right components only when a strict majority of their cells overlap",
         "program": _components(strict_majority=True)},
    ])
    intended = _callable(intended_program)
    rows.extend([
        {"id": "fixed_three_rows", "description": "perform intended rule only in output rows zero through two",
         "program": f"""(lambda (g)
  (let ([answer ({intended} g)])
    (build-grid (rows g) 3 (r c) (if (< r 3) (at answer r c) 0))))"""},
        {"id": "gray_only", "description": "perform intended rule only with separator color five",
         "program": f"""(lambda (g)
  (if (= 5 (at g 0 3)) ({intended} g)
      (build-grid (rows g) 3 (r c) 0)))"""},
    ])
    return rows


def assess_rival(rival, train, test, execute):
    """Freeze demo survival before any query prediction is requested."""
    demo_outputs = [execute(rival["program"], pair["input"]) for pair in train]
    differences = [_difference(pair["output"], output) for pair, output in zip(train, demo_outputs)]
    survivor = all(item is None for item in differences)
    row = {"rival_id": rival["id"], "program_sha256": _hash(rival["program"].encode()),
           "matches_all_demos": survivor,
           "matching_demo_indices": [i for i, item in enumerate(differences) if item is None],
           "demo_prediction_sha256": [_hash(output) for output in demo_outputs],
           "first_demo_difference": next(({"demo_index": i, **item}
                                          for i, item in enumerate(differences) if item is not None), None),
           "query_check": "pending" if survivor else "not_needed_demo_refuted",
           "query_disagreements": []}
    counterexample = None
    if survivor:
        predictions = [execute(rival["program"], pair["input"]) for pair in test]
        disagreements = [i for i, (pair, output) in enumerate(zip(test, predictions))
                         if _difference(pair["output"], output) is not None]
        row.update(query_prediction_sha256=[_hash(output) for output in predictions],
                   query_disagreements=disagreements,
                   query_check="disagrees" if disagreements else "agrees_on_all_queries")
        if disagreements:
            index = disagreements[0]
            counterexample = {"kind": "demo_survivor_query_disagreement", "rival_id": rival["id"],
                              "rival_program_sha256": row["program_sha256"],
                              "train": deepcopy(train), "query_index": index,
                              "input": deepcopy(test[index]["input"]),
                              "intended_output": deepcopy(test[index]["output"]),
                              "rival_output": predictions[index]}
    elif rival["id"] not in {f"truth_table_{mask:02d}" for mask in range(16)}:
        index = next(i for i, item in enumerate(differences) if item is not None)
        counterexample = {"kind": "demonstration_refutes_shortcut", "rival_id": rival["id"],
                          "rival_program_sha256": row["program_sha256"], "demo_index": index,
                          "input": deepcopy(train[index]["input"]),
                          "intended_output": deepcopy(train[index]["output"]),
                          "rival_output": demo_outputs[index]}
    return row, counterexample


def _public_checks(native, episode, seed, settings, demos):
    raw = public_challenge_bytes(episode)
    changed = deepcopy(episode)
    changed.update(seed=seed + 1, settings={"operation": "private sentinel"},
                   program="private sentinel", program_solution="private sentinel",
                   provenance={"hidden": "private sentinel"})
    for pair in changed["train"] + changed["test"]:
        pair["private_note"] = "private sentinel"
    for pair in changed["test"]:
        pair["output"] = [[9] * len(row) for row in pair["input"]]
    invariant = public_challenge_bytes(changed) == raw
    one_query = native.generate(seed, settings, demos=demos, queries=1)
    first_turn = public_challenge_bytes({"train": episode["train"], "test": episode["test"][:1]})
    prefix_equal = first_turn == public_challenge_bytes(one_query)
    parsed = json.loads(first_turn)
    clean = (set(parsed) == {"train", "test"} and len(parsed["test"]) == 1
             and all(set(pair) == {"input", "output"} for pair in parsed["train"])
             and set(parsed["test"][0]) == {"input"})
    return {"passed": invariant and prefix_equal and clean,
            "private_metadata_invariant": invariant,
            "single_query_first_turn_byte_identical": prefix_equal,
            "one_query_no_count_or_future_fields": clean,
            "first_turn_sha256": _hash(first_turn)}, first_turn


def audit(out, *, seed=17, demos=2):
    root = find_root(__file__)
    runtime = root / "shared/runtime"
    for module in (racket_bridge, rule_wrap):
        if not Path(module.__file__).resolve().is_relative_to(runtime):
            raise ValueError("audit requires the reference runtime from this checkout")
    native = _load_native()
    report = {"schema": SCHEMA, "task_id": TASK, "status": "running", "passed": False,
              "seed": seed, "demos": demos, "queries": 4, "settings_requested": len(OPERATIONS),
              "rivals_per_setting": 26, "programs": {}, "episodes": [], "counterexamples": [],
              "failures": [], "source_sha256": {},
              "limits": ["One deterministic minimum-demo episode per setting, not all seeds.",
                         "Only the listed finite rivals are checked; no universal uniqueness claim.",
                         "Public four-query containers are controller data; first-turn files contain only query one.",
                         "This self-review grants neither native acceptance nor training admission."]}
    for name in ("audit_native.py", "native.py", "adapter.py", "prototype.py", "canonical.rkt", "promotion.json"):
        path = HOME / name
        if path.is_file():
            report["source_sha256"][path.relative_to(root).as_posix()] = _hash(path.read_bytes())
    public_rows, baseline_inputs = [], None
    bridge = None
    evaluations = 0
    try:
        bridge = racket_bridge.RacketBridge()
        identity = bridge.runtime_identity
        if identity.get("backend") != "racket" or identity.get("protected") is not True:
            raise ValueError("self-review requires a protected Racket backend")
        report["racket"] = identity
        cache = {}

        def execute(program, grid):
            nonlocal evaluations
            _grid(grid)
            key = (program, _hash(grid))
            if key not in cache:
                literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
                cache[key] = _grid(bridge.eval_text(f"({_callable(program)} {literal})"))
                evaluations += 1
            return deepcopy(cache[key])

        def register(identifier, program, description=None):
            digest = _hash(program.encode())
            item = report["programs"].setdefault(digest, {"program": program, "ids": [], "descriptions": []})
            if identifier not in item["ids"]:
                item["ids"].append(identifier)
            if description and description not in item["descriptions"]:
                item["descriptions"].append(description)
            return digest

        for operation in OPERATIONS:
            settings = {"operation": operation}
            try:
                episode = native.generate(seed, settings, demos=demos, queries=4)
                program = native.program(settings)
                if episode.get("program_solution") != program:
                    raise ValueError("generated program differs from native.program(settings)")
                if len(episode.get("train", [])) != demos or len(episode.get("test", [])) != 4:
                    raise ValueError("native episode did not supply exact requested counts")
                pairs = episode["train"] + episode["test"]
                inputs = [pair["input"] for pair in pairs]
                if len({_hash(grid) for grid in inputs}) != len(inputs):
                    raise ValueError("query/demo input novelty failed")
                if baseline_inputs is None:
                    baseline_inputs = deepcopy(inputs)
                if inputs != baseline_inputs:
                    raise ValueError("matched seed changed input construction across hidden settings")
                for pair in pairs:
                    _grid(pair["output"])
                    if execute(program, pair["input"]) != pair["output"]:
                        raise ValueError("fresh Racket execution disagrees with a generated label")
                intended_digest = register("setting:" + operation, program)
                raw = public_challenge_bytes(episode)
                visible_id = _hash(raw)
                if public_challenge_id(episode) != visible_id:
                    raise ValueError("challenge ID is not the hash of exact public bytes")
                projection, first_turn = _public_checks(native, episode, seed, settings, demos)
                if not projection["passed"]:
                    report["failures"].append({"settings": settings, "kind": "public_projection", **projection})
                private = {"task_id": TASK, "seed": seed, "settings": settings, "episode_id": visible_id,
                           "program": program, "program_sha256": intended_digest,
                           "train": episode["train"], "test": episode["test"]}
                public_rows.append((visible_id, raw, first_turn, private))
                summary = {"settings": settings, "public_id": visible_id, "program_sha256": intended_digest,
                           "counts": {"demos": demos, "queries": 4},
                           "unique_inputs": len(inputs), "input_sizes": [[len(g), len(g[0])] for g in inputs],
                           "matched_inputs_across_settings": True, "public_projection": projection,
                           "rivals": []}
                for rival in rivals(program):
                    register(rival["id"], rival["program"], rival["description"])
                    assessment, counterexample = assess_rival(rival, episode["train"], episode["test"], execute)
                    summary["rivals"].append(assessment)
                    if counterexample and (assessment["query_disagreements"] or operation == "overlap_components"):
                        report["counterexamples"].append({"settings": settings,
                            "intended_program_sha256": intended_digest, **counterexample})
                    if assessment["query_disagreements"]:
                        report["failures"].append({"settings": settings, "rival_id": rival["id"],
                                                    "kind": "demo_survivor_query_disagreement",
                                                    "query_indices": assessment["query_disagreements"]})
                summary["demo_survivors"] = [row["rival_id"] for row in summary["rivals"] if row["matches_all_demos"]]
                summary["passed"] = projection["passed"] and not any(row["query_disagreements"] for row in summary["rivals"])
                report["episodes"].append(summary)
            except Exception as error:
                report["failures"].append({"settings": settings, "kind": "execution_error",
                                           "error": f"{type(error).__name__}: {error}"})

        # This deliberately underidentified lesson is a negative control, never
        # an ordinary emitted episode. Its labels and rival labels are Racket-owned.
        correct = native.program({"operation": "and"})
        weak_inputs = [[[1, 1, 1, 5, 1, 1, 1]], [[1, 0, 1, 5, 0, 1, 1]]]
        weak = [{"input": grid, "output": execute(correct, grid)} for grid in weak_inputs]
        wrong = {"id": "negative_control_copy_right", "program": _pointwise(10)}
        register(wrong["id"], wrong["program"])
        negative, counterexample = assess_rival(wrong, weak[:1], weak[1:], execute)
        detected = negative["matches_all_demos"] and negative["query_disagreements"] == [0]
        report["negative_control"] = {"expected": "copy-right fits equal-panel demo and fails novel query",
                                      "detected": detected, "assessment": negative,
                                      "counterexample": counterexample}
        if not detected:
            report["failures"].append({"kind": "negative_control_not_detected"})
    except Exception as error:
        report["failures"].append({"kind": "audit_error", "error": f"{type(error).__name__}: {error}"})
    finally:
        if bridge is not None:
            bridge.close()

    public_rows.sort(key=lambda row: row[0])
    ids = [row[0] for row in public_rows]
    if len(ids) != len(set(ids)):
        report["failures"].append({"kind": "duplicate_public_challenge_id"})
    (out / "challenges.public.jsonl").write_bytes(b"".join(row[1] for row in public_rows))
    (out / "first-turns.public.jsonl").write_bytes(b"".join(row[2] for row in public_rows))
    (out / "episodes.private.jsonl").write_text("".join(
        json.dumps(row[3], sort_keys=True, separators=(",", ":")) + "\n" for row in public_rows), encoding="utf-8")
    (out / "public-ids.json").write_text(json.dumps(ids, indent=2) + "\n", encoding="utf-8")
    report.update(settings_completed=len(report["episodes"]), protected_racket_evaluations=evaluations,
                  public_ids=ids, public_bytes_sorted_by_id=True,
                  passed=not report["failures"] and len(report["episodes"]) == len(OPERATIONS))
    report["status"] = "passed_finite_self_review" if report["passed"] else "failed"
    (out / "self-review.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--demos", type=int, choices=range(2, 7), default=2)
    args = parser.parse_args(argv)
    if args.out.exists():
        parser.error("output exists; choose a new directory to preserve source-bound evidence")
    if not 0 <= args.seed <= 2**63 - 1:
        parser.error("seed must be in 0..2**63-1")
    args.out.mkdir(parents=True)
    report = audit(args.out, seed=args.seed, demos=args.demos)
    print(json.dumps({key: report[key] for key in
                      ("status", "passed", "settings_completed", "protected_racket_evaluations", "failures")}))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
