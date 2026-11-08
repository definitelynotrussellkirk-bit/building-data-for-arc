#!/usr/bin/env python3
"""Replay the retained failure and a four-demo/four-query protected lesson."""
from pathlib import Path
import hashlib
import importlib.util
import json
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1] / "repo"
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "shared/runtime")]
from arcpuzzles.catalog import Catalog
from arcpuzzles.parametric_worker import _grid, _local_imports, _real_evaluator
from reviewer_support import load_selected_generator


def write(name, value):
    (HERE / name).write_text(json.dumps(value, sort_keys=True, indent=2) + "\n")


def main():
    generator, source, source_sha = load_selected_generator("9fc0b6db96fe", root=ROOT)
    baseline = json.loads((HERE / "generated-counterexample.json").read_text())
    old_source = HERE / "generator-before.py"
    assert hashlib.sha256(old_source.read_bytes()).hexdigest() == baseline["source_binding"]["generator_sha256"]
    spec = importlib.util.spec_from_file_location("peer_baseline_9fc0b6db96fe", old_source)
    previous = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(previous)
    grids = [generator.generate(2, index, difficulty="hard") for index in range(8)]
    assert grids == [previous.generate(2, index, difficulty="hard") for index in range(8)]
    catalog = Catalog(ROOT)
    original = catalog._variants()["9fc0b6db96fe"][0]
    program = original["program_solution"]
    assert program == baseline["program"]
    canonical_identity = program.replace("((= key 4) (flip-lr grid))", "((= key 4) grid)")
    assert canonical_identity != program
    labels = 0
    with _local_imports(ROOT / "shared/runtime", HERE):
        apply, identity, bridge = _real_evaluator(ROOT / "shared/runtime")
        def execute(rule, grid):
            nonlocal labels
            labels += 1
            return _grid(apply(rule, grid))
        try:
            repaired_pairs = [{"input": grid, "output": execute(program, grid)} for grid in grids]
            rival_outputs = [execute(baseline["rival_program"], grid) for grid in grids]
            reasons = [generator.lesson_identifiable(repaired_pairs[:4], pair) for pair in repaired_pairs[4:]]
            assert reasons == [[], [], [], []]
            assert {pair["input"][0][0] for pair in repaired_pairs[:4]} == {1, 2, 3, 4}
            assert any(pair["output"] != value for pair, value in zip(repaired_pairs[:4], rival_outputs[:4]))
            rejected = generator.lesson_identifiable(baseline["train"], baseline["test"][0])
            assert rejected
            tests = original["test"] if isinstance(original["test"], list) else [original["test"]]
            canonical_pairs = original["train"] + tests
            canonical_actual = [execute(program, pair["input"]) for pair in canonical_pairs]
            assert canonical_actual == [pair["output"] for pair in canonical_pairs]
            identity_outputs = [execute(canonical_identity, pair["input"]) for pair in canonical_pairs]
        finally:
            bridge.close()
    binding = {**baseline["source_binding"], "generator_sha256": source_sha,
               "baseline_generator_sha256": baseline["source_binding"]["generator_sha256"]}
    canonical_case = {"source_binding": binding, "racket": identity,
                      "program": program, "rival_program": canonical_identity,
                      "rival_name": "key4_means_identity", "train": original["train"], "test": tests,
                      "canonical_outputs": canonical_actual, "rival_outputs": identity_outputs,
                      "rival_fits_every_demo": identity_outputs[:len(original["train"])] == canonical_actual[:len(original["train"])],
                      "rival_changes_query": identity_outputs[-1] != canonical_actual[-1]}
    write("canonical-key4-identity-counterexample.json", canonical_case)
    write("repaired-lesson.json", {"source_binding": binding, "racket": identity,
          "seed": 2, "difficulty": "hard", "sample_indices": list(range(8)),
          "program": program, "rival_program": baseline["rival_program"],
          "train": repaired_pairs[:4], "test": repaired_pairs[4:],
          "rival_outputs": rival_outputs, "lesson_identifiable_reasons": reasons})
    report = {"schema": "arcpuzzles-bounded-peer-repair-v1", "task_id": "9fc0b6db96fe",
              "status": "pass", "outcome": "repaired", "source_binding": binding,
              "examples_needed_before": previous.EXAMPLES_NEEDED,
              "examples_needed_after": generator.EXAMPLES_NEEDED,
              "input_bytes_unchanged_for_replayed_draws": 8,
              "retained_three_demo_rejection": rejected,
              "four_demo_four_query_reasons": reasons, "racket": identity,
              "racket_evaluations": labels,
              "canonical_identity_rival_fits_demos": canonical_case["rival_fits_every_demo"],
              "canonical_identity_rival_changes_query": canonical_case["rival_changes_query"],
              "limits": "Bounded teaching repair, not exhaustive rival identification. The original canonical visible lesson is unchanged. Current-source owner approval remains pending."}
    write("repair-report.json", report)
    print(json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
