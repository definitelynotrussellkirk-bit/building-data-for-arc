#!/usr/bin/env python3
"""Bounded protected-Racket teaching audit; all retained evidence is private.

Run through review.py from the packet root, with this script's path relative
to WORK/repo. The fixed audit covers seeds 0 and 17, all six settings, two
demonstrations and four queries. It does not change the generator or adapter.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

from arcpuzzles.catalog import Catalog
from arcpuzzles.parametric_worker import _grid, _local_imports, _real_evaluator


TASK = "7fc158ab7b70"
SEEDS = (0, 17)
HOME = Path(__file__).resolve().parent


def sha(value):
    if not isinstance(value, str):
        value = json.dumps(value, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(value.encode()).hexdigest()


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def wrong_rule(setting, *, count=None, mode="replicate"):
    """Materialize independent executable rivals, without changing the adapter."""
    count = count or ("(length nonzero)" if setting["count_basis"] == "cells"
                      else "(length (remove-duplicates nonzero))")
    row_factor = "amount" if setting["scale_axes"] in ("both", "rows") else "1"
    col_factor = "amount" if setting["scale_axes"] in ("both", "columns") else "1"
    source = "g"
    crop = ""
    if mode == "crop":
        crop = """
         (points (filter (lambda (rc)
                           (not (= (list-ref (list-ref g (first rc)) (second rc)) 0)))
                         (for*/list ((r (in-range (length g)))
                                     (c (in-range (length (car g))))) (list r c))))
         (r0 (apply min (map first points)))
         (r1 (apply max (map first points)))
         (c0 (apply min (map second points)))
         (c1 (apply max (map second points)))
         (cropped (for/list ((r (in-range r0 (+ r1 1))))
                    (for/list ((c (in-range c0 (+ c1 1))))
                      (list-ref (list-ref g r) c))))"""
        source = "cropped"
    row_index = (f"(modulo r (length {source}))" if mode == "tile"
                 else "(quotient r row-factor)")
    col_index = (f"(modulo c (length (car {source})))" if mode == "tile"
                 else "(quotient c col-factor)")
    callable_source = f"""(lambda (g)
  (let* ((nonzero (filter (lambda (v) (not (= v 0))) (apply append g)))
         (amount {count})
         (row-factor {row_factor})
         (col-factor {col_factor}){crop})
    (for/list ((r (in-range (* (length {source}) row-factor))))
      (for/list ((c (in-range (* (length (car {source})) col-factor))))
        (list-ref (list-ref {source} {row_index}) {col_index})))))
"""
    # The native evaluator accepts registered rule! source, while the
    # standalone prototype's direct bridge accepts a callable lambda.
    return "(rule! " + callable_source.rstrip() + ")\n"


MASK = "(map (lambda (row) (map (lambda (v) (if (= v 0) 0 1)) row)) g)"
COUNT_RIVALS = {
    "monochrome_4cc_count": "(length (objects g 0))",
    "monochrome_8cc_count": "(length (objects-8 g 0))",
    "nonzero_4cc_count": f"(length (objects {MASK} 0))",
    "nonzero_8cc_count": f"(length (objects-8 {MASK} 0))",
    "largest_monochrome_4cc_area": "(apply max (map obj-size (objects g 0)))",
    "occupied_rows": """(length (filter (lambda (row)
       (> (length (filter (lambda (v) (not (= v 0))) row)) 0)) g))""",
    "occupied_columns": """(length (filter (lambda (c)
       (> (length (filter (lambda (r)
            (not (= (list-ref (list-ref g r) c) 0)))
            (range 0 (length g)))) 0)) (range 0 (length (car g)))))""",
    "input_side": "(length g)",
}


def rivals(adapter, settings, chosen):
    inventory = [("declared:" + other.name, adapter.program(other.as_dict()))
                 for other in settings if other.as_dict() != chosen]
    inventory += [(f"fixed_scale_{factor}" + ("_copy" if factor == 1 else ""),
                   wrong_rule(chosen, count=str(factor))) for factor in range(1, 7)]
    inventory += [(name, wrong_rule(chosen, count=expression))
                  for name, expression in COUNT_RIVALS.items()]
    inventory += [("whole_grid_tiling", wrong_rule(chosen, mode="tile")),
                  ("foreground_bbox_crop_then_replicate", wrong_rule(chosen, mode="crop"))]
    return inventory


def difference(expected, actual):
    if [len(expected), len(expected[0])] != [len(actual), len(actual[0])]:
        return {"kind": "shape", "expected": [len(expected), len(expected[0])],
                "actual": [len(actual), len(actual[0])]}
    for row in range(len(expected)):
        for col in range(len(expected[0])):
            if expected[row][col] != actual[row][col]:
                return {"kind": "cell", "row": row, "col": col,
                        "expected": expected[row][col], "actual": actual[row][col]}
    return None


class Executor:
    def __init__(self, runtime):
        self.apply, self.identity, self.bridge = _real_evaluator(runtime)
        self.programs, self.cache, self.errors = {}, {}, []
        self.evaluations = 0

    def execute(self, program, grid):
        program_hash, input_hash = sha(program), sha(grid)
        self.programs[program_hash] = program
        key = (program_hash, input_hash)
        if key not in self.cache:
            self.evaluations += 1
            try:
                output = _grid(self.apply(program, deepcopy(grid)))
                result = {"output": output}
            except Exception as exc:
                result = {"error": {"type": type(exc).__name__, "message": str(exc)}}
                self.errors.append({"program_sha256": program_hash,
                                    "input_sha256": input_hash, **result})
            self.cache[key] = result
        return deepcopy(self.cache[key])

    def label(self, program, grid):
        result = self.execute(program, grid)
        if "error" in result:
            raise ValueError("Protected execution failed: " + json.dumps(result["error"]))
        return result["output"]

    def compare(self, program, pair):
        result = self.execute(program, pair["input"])
        if "error" in result:
            return {"status": "error", **result}
        output = result["output"]
        mismatch = difference(pair["output"], output)
        return {"status": "match" if mismatch is None else "different",
                "output_sha256": sha(output), "output_shape": [len(output), len(output[0])],
                "first_difference": mismatch}


def audit_episode(executor, adapter, seed, chosen, settings):
    episode = adapter.generate(seed, chosen, 2, 4)
    program = adapter.program(chosen)
    if episode["program_solution"] != program:
        raise ValueError("Adapter changed its exact program within an episode")
    for split in ("train", "test"):
        for pair in episode[split]:
            actual = executor.label(program, pair["input"])
            if actual != pair["output"]:
                raise ValueError("Python label claim disagrees with protected Racket")
            pair["output"] = actual
    checks, survivors = [], []
    for name, rival in rivals(adapter, settings, chosen):
        demo_checks = []
        for index, pair in enumerate(episode["train"]):
            check = {"demo_index": index, **executor.compare(rival, pair)}
            demo_checks.append(check)
            if check["status"] != "match":
                break
        survives = len(demo_checks) == 2 and all(c["status"] == "match" for c in demo_checks)
        query_checks = []
        if survives:
            survivors.append(name)
            for index, pair in enumerate(episode["test"]):
                query_checks.append({"query_index": index, **executor.compare(rival, pair)})
        checks.append({"name": name, "program_sha256": sha(rival),
                       "survives_both_demos": survives,
                       "demo_checks": demo_checks, "query_checks": query_checks})
    ambiguous = [check["name"] for check in checks if check["survives_both_demos"]
                 and any(query["status"] != "match" for query in check["query_checks"])]
    return {"seed": seed, "settings": chosen, "program_sha256": sha(program),
            "train": episode["train"], "test": episode["test"],
            "python_claims_equal_racket": True, "rivals": checks,
            "demo_survivors": survivors, "ambiguous_rivals": ambiguous}


def historical_probe(executor, adapter, canonical, root):
    old_path = HOME / "evidence/public-id-correction/original/scaling.py"
    if not old_path.is_file():
        return {"status": "not_run", "reason": "Original prototype snapshot is unavailable"}
    old_source_sha256 = hashlib.sha256(old_path.read_bytes()).hexdigest()
    old = load(old_path, "_scaling_original_for_bounded_review")
    chosen = {"count_basis": "cells", "scale_axes": "both"}
    rival = wrong_rule(chosen, count=COUNT_RIVALS["monochrome_4cc_count"])
    results, witness = [], None
    for seed in SEEDS:
        inputs = old.generate_inputs(seed, train=3, test=4)
        demos, demo_checks = [], []
        for index, grid in enumerate(inputs[:3]):
            pair = {"input": grid, "output": executor.label(canonical, grid)}
            demos.append(pair)
            demo_checks.append({"demo_index": index, **executor.compare(rival, pair)})
            if demo_checks[-1]["status"] != "match":
                break
        survives = len(demo_checks) == 3 and all(c["status"] == "match" for c in demo_checks)
        query_checks = []
        if survives:
            for index, grid in enumerate(inputs[3:]):
                pair = {"input": grid, "output": executor.label(canonical, grid)}
                comparison = executor.compare(rival, pair)
                query_checks.append({"query_index": index, **comparison})
                if comparison["status"] == "different":
                    if witness is None:
                        corrected = adapter.generate(seed, chosen, 2, 4)["train"][1]
                        corrected["output"] = executor.label(canonical, corrected["input"])
                        corrected_rival = executor.label(rival, corrected["input"])
                        if corrected_rival == corrected["output"]:
                            raise ValueError("Corrected L-triomino demo did not refute component counting")
                        witness = {
                            "schema": "arcpuzzles-bounded-teaching-repair-v1", "seed": seed,
                            "original_source": str(old_path.relative_to(root)),
                            "original_source_sha256": old_source_sha256,
                            "corrected_source": str((HOME / "scaling.py").relative_to(root)),
                            "corrected_source_sha256": hashlib.sha256((HOME / "scaling.py").read_bytes()).hexdigest(),
                            "settings": chosen, "canonical_program": canonical,
                            "rival_program": rival, "racket": executor.identity,
                            "before": {"train": demos, "query_index": index, "query": pair,
                                       "rival_query_output": executor.label(rival, grid)},
                            "after_distinguishing_demo": {**corrected, "rival_output": corrected_rival},
                            "scope": "Original three demos fit component counting; a recorded original query differs. The new second demo refutes it. No population or universal uniqueness claim.",
                        }
                    break
        results.append({"seed": seed, "survives_three_demos": survives,
                        "demo_checks": demo_checks, "query_checks": query_checks})
    return {"status": "teaching_hole_reproduced" if witness else "no_finding_in_bounded_probe",
            "source": str(old_path.relative_to(root)),
            "source_sha256": old_source_sha256,
            "rival_program_sha256": sha(rival), "checks": results, "witness": witness}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    root = Path.cwd().resolve()
    output = args.out.resolve()
    if output.exists():
        raise ValueError("Choose a fresh audit output directory")
    adapter = load(HOME / "adapter.py", "_native_scaling_adapter_audit")
    catalog = Catalog(root)
    selected = catalog.get(TASK)
    sources = {variant["program_solution"] for variant in selected["variants"]}
    if len(sources) != 1:
        raise ValueError("Selected canonical authority is not exact-text unique")
    canonical = next(iter(sources))
    if adapter.program(adapter.prototype.DEFAULT.as_dict()) != canonical:
        raise ValueError("Native default is not byte-identical to selected canonical authority")
    source_paths = [root / selected["generator"], HOME / "adapter.py", HOME / "scaling.py",
                    HOME / "canonical.rkt", Path(__file__).resolve()]
    historical_source = HOME / "evidence/public-id-correction/original/scaling.py"
    if historical_source.is_file():
        source_paths.append(historical_source)
    source_hashes = {str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
                     for path in source_paths}
    result = {"schema": "arcpuzzles-bounded-scaling-teaching-audit-v1", "task_id": TASK,
              "status": "running", "private": True, "source_hashes": source_hashes,
              "generator_sha256": selected["generator_sha256"],
              "canonical_rule_hash": selected["rule_hash"],
              "canonical_program_sha256": sha(canonical),
              "scope": {"seeds": list(SEEDS), "settings": 6, "demos": 2, "queries": 4,
                        "rivals_per_setting": 21, "query_policy": "Only demo survivors are checked on queries"},
              "episodes": [],
              "limits": "Two seeds and the named finite rivals only. Runtime errors fail the audit; refuted rivals are short-circuited. This does not grant native acceptance or training admission."}
    executor = None
    output.mkdir(parents=True)
    try:
        runtime = root / "shared/runtime"
        with _local_imports(runtime, HOME):
            executor = Executor(runtime)
            result["racket"] = executor.identity
            try:
                for seed in SEEDS:
                    for setting in adapter.prototype.SETTINGS:
                        episode = audit_episode(executor, adapter, seed, setting.as_dict(),
                                                adapter.prototype.SETTINGS)
                        result["episodes"].append(episode)
                        if episode["ambiguous_rivals"]:
                            print(json.dumps({"finding": "surviving_rival_disagrees_on_query",
                                              "seed": seed, "settings": setting.as_dict(),
                                              "rivals": episode["ambiguous_rivals"]}), flush=True)
                result["historical_probe"] = historical_probe(executor, adapter, canonical, root)
            finally:
                executor.bridge.close()
        if any(hashlib.sha256(path.read_bytes()).hexdigest() != source_hashes[str(path.relative_to(root))]
               for path in source_paths):
            raise ValueError("Audited source changed during execution; rerun on frozen source")
        failures = [episode for episode in result["episodes"] if episode["ambiguous_rivals"]]
        result["status"] = "failed" if failures or executor.errors else "passed_finite_rivals"
    except Exception as exc:
        result["status"] = "failed"
        result["fatal_error"] = {"type": type(exc).__name__, "message": str(exc)}
    finally:
        if executor is not None:
            result["actual_racket_evaluations"] = executor.evaluations
            result["execution_errors"] = executor.errors
            result["programs"] = executor.programs
        historical = result.get("historical_probe", {})
        witness = historical.pop("witness", None)
        if witness:
            witness_path = output / "historical-teaching-repair.json"
            witness_path.write_text(json.dumps(witness, separators=(",", ":")) + "\n")
            historical["witness_path"] = witness_path.name
        (output / "audit.json").write_text(json.dumps(result, separators=(",", ":")) + "\n")
    print(json.dumps({"status": result["status"], "episodes": len(result["episodes"]),
                      "racket_evaluations": result.get("actual_racket_evaluations", 0),
                      "execution_errors": len(result.get("execution_errors", [])),
                      "fatal_error": result.get("fatal_error"),
                      "historical_probe": result.get("historical_probe", {}).get("status"),
                      "out": str(output)}, indent=2))
    return 0 if result["status"] == "passed_finite_rivals" else 1


if __name__ == "__main__":
    raise SystemExit(main())
