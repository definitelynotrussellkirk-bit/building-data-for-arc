"""Racket-backed question evidence and reusable JSON lesson gate.

Default: run one bounded task-local probe and retain its witness/controls.
--lesson PATH: check {"demos": [...], "query": {"input": ...}} against Racket;
query output is optional and ignored. Exit 0 passes this finite gate, 2 rejects
or blocks a lesson, and 1 means the default probe itself failed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import time

import question_gate as gate

sys.path.insert(0, str(gate.REPO_ROOT / "src"))
from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule


def sha(data):
    return hashlib.sha256(data).hexdigest()


def grid_key(grid):
    return json.dumps(grid, separators=(",", ":"))


def source_hashes():
    paths = [gate.TASK_ROOT / "generator.py", Path(gate.__file__), Path(__file__),
             gate.TASK_ROOT / "tests/test_question_gate.py"]
    return {str(path.relative_to(gate.REPO_ROOT)): sha(path.read_bytes()) for path in paths}


def canonical_row():
    rows = []
    path = gate.REPO_ROOT / "shared/data/canonical/puzzles.jsonl"
    for line in path.read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == "6fde852adb54":
            rows.append(row)
    if len({row["program_solution"] for row in rows}) != 1:
        raise RuntimeError("expected one canonical program for the selected task")
    return next(row for row in rows if row.get("source") == "training")


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lesson", type=Path, help="JSON with demos and one query")
    parser.add_argument("--out", type=Path,
                        default=gate.REPO_ROOT.parent / "checks/questions/probe.json")
    parser.add_argument("--expected-generator-sha", help="fail if selected source changed")
    args = parser.parse_args()
    started = time.monotonic()
    before = source_hashes()
    generator_sha = before["generators/6fde852adb54/generator.py"]
    if args.expected_generator_sha and generator_sha != args.expected_generator_sha:
        raise RuntimeError("selected generator does not match the requested SHA-256")
    row = canonical_row()
    raw_rule = row["program_solution"]
    wrapped_rule = wrap_rule(raw_rule)
    normalized = sha(" ".join(raw_rule.split()).encode())[:12]
    if normalized != gate.GENERATOR.RULE_HASH or normalized != "4a2e9b9f15bf":
        raise RuntimeError("canonical rule identity changed")
    result = {
        "schema": "arcpuzzles-question-probe-v1", "task_id": "6fde852adb54",
        "source_hashes": before,
        "source_scopes": {"generator": "selected source file bytes",
                          "raw_rule": "UTF-8 bytes of canonical row program_solution",
                          "wrapped_rule": "UTF-8 bytes of the callable embedded in the bridge definition",
                          "definition": "UTF-8 bytes of the complete define expression passed to eval_text"},
        "canonical_rule": {"normalized_sha256_prefix": normalized,
                           "raw_program_sha256": sha(raw_rule.encode()),
                           "wrapped_callable_sha256": sha(wrapped_rule.encode()),
                           "definition_sha256": sha(f"(define question-rule {wrapped_rule})".encode()),
                           "canonical_path": "shared/data/canonical/puzzles.jsonl"},
        "command": [sys.executable] + sys.argv, "cwd": os.getcwd(),
        "racket_path": os.environ.get("RACKET_PATH"),
        "reference_calls": [], "scope": gate.SCOPE,
    }
    cache = {}
    with RacketBridge(timeout=30.0) as bridge:
        bridge.eval_text(f"(define question-rule {wrapped_rule})")
        result["racket_version"] = bridge.eval_text("(version)")

        def reference(grid, name="gate_input"):
            key = grid_key(grid)
            if key not in cache:
                binding = f"question-grid-{len(cache)}"
                bridge.define_grid(binding, grid)
                output = bridge.eval_text(f"(question-rule {binding})")
                mirror = gate.GENERATOR.rule_mirror(grid)
                if output != mirror:
                    raise AssertionError(f"Racket/Python disagreement for {name}")
                cache[key] = output
                result["reference_calls"].append({
                    "name": name, "input_sha256": sha(key.encode()),
                    "racket_output_sha256": sha(grid_key(output).encode()),
                    "shape": [len(grid), len(grid[0])],
                    "self_check": gate.GENERATOR.self_check(grid),
                    "python_mirror_matches": True,
                    "rival_difference_cells": gate.difference_cells(output, gate.rival_predict(grid)),
                })
            return [list(row) for row in cache[key]]

        if args.lesson:
            try:
                lesson = json.loads(args.lesson.read_text())
                if not isinstance(lesson, dict):
                    raise ValueError("lesson must be an object")
                report = gate.lesson_gate(lesson.get("demos"), lesson.get("query"),
                                          canonical_predict=reference)
            except (ValueError, OSError) as exc:
                report = {"status": "invalid", "reasons": [str(exc)], "scope": gate.SCOPE}
            result["lesson_path"] = str(args.lesson.resolve())
            result["gate"] = report
            exit_code = 0 if report["status"] == "pass" else 2
        else:
            demos = row["train"]
            for index, pair in enumerate(demos):
                assert reference(pair["input"], f"canonical_demo_{index}") == pair["output"]
                assert gate.rival_predict(pair["input"]) == pair["output"]
            query = row["test"][0]
            assert reference(query["input"], "canonical_query") == query["output"]
            public_results = []
            for profile in range(4):
                for reflected in (False, True):
                    grid = gate.GENERATOR._draw_public(profile, reflected, gate.GENERATOR._EXACT_ROLES)
                    output = reference(grid, f"public_{profile}_reflected_{reflected}")
                    difference = gate.difference_cells(output, gate.rival_predict(grid))
                    assert difference == 0
                    public_results.append({"profile": profile, "reflected": reflected,
                                           "rival_difference_cells": difference})
            control = gate.GENERATOR.generate(17, 0, difficulty="medium", scene_family="generalized")
            reference(control, "generated_control_seed17_index0_medium_generalized")
            witness = gate.make_witness()
            output = reference(witness, "exact_14x14_witness")
            rival_output = gate.rival_predict(witness)
            differences = [{"row": r, "col": c, "canonical": output[r][c], "rival": rival_output[r][c]}
                           for r in range(len(witness)) for c in range(len(witness[0]))
                           if output[r][c] != rival_output[r][c]]
            assert len(differences) == 6
            result["witness"] = {"input": witness, "racket_output": output,
                                 "rival_output": rival_output, "different_cells": differences,
                                 "self_check": gate.GENERATOR.self_check(witness),
                                 "support_scope": "proposed_witness_sampler; not current generate()"}
            ambiguous_lesson = {"demos": demos, "query": {"input": witness}}
            ambiguous = gate.lesson_gate(demos, ambiguous_lesson["query"], canonical_predict=reference)
            assert ambiguous["status"] == "ambiguous"
            poisoned = gate.lesson_gate(demos, {"input": witness, "output": [[False]]},
                                        canonical_predict=reference)
            assert poisoned == ambiguous
            equivalent_lesson = {"demos": demos, "query": {"input": query["input"]}}
            equivalent = gate.lesson_gate(demos, equivalent_lesson["query"], canonical_predict=reference)
            assert equivalent["status"] == "pass" and equivalent["query_difference_cells"] == 0
            fixed_demos = demos + [{"input": witness, "output": output}]
            proposed = []
            seen = {grid_key(d["input"]) for d in fixed_demos}
            for index in range(4):
                grid = gate.sample_witness(17, index)
                key = grid_key(grid)
                assert key not in seen
                seen.add(key)
                target = reference(grid, f"proposed_witness_seed17_index{index}")
                report = gate.lesson_gate(fixed_demos, {"input": grid}, canonical_predict=reference)
                assert report["status"] == "pass" and report["query_difference_cells"] == 6
                assert report["demo_matches"] == [True, True, True, False]
                proposed.append({"seed": 17, "sample_index": index, "input": grid,
                                 "racket_output": target, "gate": report})
            repaired_lesson = {"demos": fixed_demos, "query": {"input": proposed[0]["input"]}}
            result["gate_checks"] = {"ambiguous_witness_query": ambiguous,
                                     "poisoned_query_label_ignored": poisoned == ambiguous,
                                     "answer_equivalent_query": equivalent,
                                     "repaired_four_queries": [p["gate"] for p in proposed]}
            result["proposed_samples"] = proposed
            result["public_catalog_comparison"] = public_results
            result["current_support_conclusion"] = {
                "claim": "no emitted case separates this rival in the selected current generator",
                "basis": "structural source inspection plus complete eight-geometry public catalog comparison",
                "generalized_reason": "distractors exclude all mover columns and cannot join placed components; active bar, L blob and possible attached tip stopper have contiguous obstacle rows within each column",
                "public_reason": "all four public shapes and their reflections agree; semantic role permutations do not change the comparison",
                "sampled_current_controls": 1,
                "not_a_census": True,
            }
            result["artifact_paths"] = {}
            for name, lesson in (("ambiguous_lesson", ambiguous_lesson),
                                 ("answer_equivalent_lesson", equivalent_lesson),
                                 ("repaired_lesson", repaired_lesson)):
                path = args.out.parent / f"{name}.json"
                write_json(path, lesson)
                result["artifact_paths"][name] = str(path.resolve())
            result["status"] = "passed_bounded_probe"
            exit_code = 0
    if before != source_hashes():
        raise RuntimeError("source changed during the probe; result is not source bound")
    result["elapsed_seconds"] = time.monotonic() - started
    result["actual_reference_application_count"] = len(cache)
    result["exit_code"] = exit_code
    result["not_run"] = ["production battery", "large seed census", "model training or Qwen inference",
                         "exhaustive rival search", "automatic production integration or approval"]
    write_json(args.out, result)
    print(json.dumps({"report": str(args.out.resolve()), "exit_code": exit_code,
                      "reference_applications": len(cache),
                      "elapsed_seconds": result["elapsed_seconds"],
                      "status": result.get("status", result.get("gate", {}).get("status"))}))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
