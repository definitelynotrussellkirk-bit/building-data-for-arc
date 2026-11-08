#!/usr/bin/env python3
"""Retain one actual selected-generator draw and its public Racket/rival evidence.

Run through WORK/run_with_racket.py. This does not construct, repair, or relabel
the generated input. It calls generate with the exact recorded seed/index/band,
then public arcpuzzles apply for the actual reference output. Python rivals are
diagnostic predictions. The output directory must be new.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import traceback

TASK = "3b1ef21add2f"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True)
    parser.add_argument("--expected-generator-sha", required=True)
    parser.add_argument("--expected-rule-hash", required=True)
    parser.add_argument("--counterexamples", required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--sample-index", type=int, required=True)
    parser.add_argument("--difficulty", required=True, choices=("easy", "medium", "hard"))
    args = parser.parse_args()
    repo = Path.cwd()
    source_path = repo / "generators" / TASK / "generator.py"
    canonical_path = repo / "shared/data/canonical/puzzles.jsonl"
    out = Path(args.out).resolve()
    if out.exists():
        raise SystemExit(f"Refusing to overwrite retained evidence: {out}")
    out.mkdir(parents=True)
    report_path = out / "witness.json"
    record = {
        "schema": "actual-generated-rival-witness-v1", "status": "running",
        "task_id": TASK,
        "invocation": {"argv": [sys.executable, *sys.argv], "cwd": str(repo)},
        "generation": {"api": "selected generator.generate", "seed": args.seed,
                       "sample_index": args.sample_index, "difficulty": args.difficulty,
                       "overrides": {}, "input_edited_after_generation": False},
        "source": {"generator_path": str(source_path.relative_to(repo)),
                   "generator_sha256": sha(source_path), "canonical_file_sha256": sha(canonical_path),
                   "authoring_script_sha256": sha(Path(__file__))},
        "note": "Actual Racket output is authoring evidence, not a replacement training label or approval.",
    }
    save(report_path, record)
    try:
        if record["source"]["generator_sha256"] != args.expected_generator_sha:
            raise ValueError("Selected source hash differs from expected frozen candidate")
        spec = importlib.util.spec_from_file_location("generated_witness_selected", source_path)
        generator = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = generator
        spec.loader.exec_module(generator)
        grid = generator.generate(args.seed, args.sample_index, difficulty=args.difficulty)
        record["input"] = grid
        record["source"]["generator_version"] = generator.VERSION
        record["generation"]["schedule_profile"] = generator.schedule_profile(
            args.seed, args.sample_index, args.difficulty)
        record["self_check_errors"] = generator.self_check(deepcopy(grid))
        record["observed_axes"] = generator.observe_overrides(deepcopy(grid))
        record["semantic_witnesses"] = {name: bool(fn(deepcopy(grid)))
                                         for name, fn in generator.SEMANTIC_WITNESSES.items()}
        record["witness_rivals"] = generator.WITNESS_RIVALS
        if record["self_check_errors"]:
            raise ValueError("Actually generated input failed selected self_check")
        canonical = next(json.loads(line) for line in canonical_path.read_text().splitlines()
                         if json.loads(line).get("task_id") == TASK)
        pairs = [(f"{split}:{index}", pair) for split in ("train", "test")
                 for index, pair in enumerate(canonical[split]) if "output" in pair]
        record["canonical_labelled_pair_count"] = len(pairs)
        record["declared_rivals"] = {}
        predictions = {}
        for namespace in ("CANONICAL_SHORTCUTS", "LESSON_COMPETITORS", "SEMANTIC_RIVALS"):
            declared = getattr(generator, namespace)
            record["declared_rivals"][namespace] = sorted(declared)
            for name, fn in declared.items():
                output = fn(deepcopy(grid))
                fits = [{"pair": pair_id, "fits": fn(deepcopy(pair["input"])) == pair["output"]}
                        for pair_id, pair in pairs]
                if name in predictions:
                    if predictions[name]["output"] != output or predictions[name]["canonical_pairs"] != fits:
                        raise ValueError(f"Conflicting same-name rivals across declarations: {name}")
                    predictions[name]["declarations"].append(namespace)
                else:
                    predictions[name] = {"output": output, "declarations": [namespace],
                                         "callable": fn.__name__, "canonical_pairs": fits,
                                         "canonical_fit_all_labelled_pairs": all(item["fits"] for item in fits)}
        record["rivals"] = predictions
        input_path, output_path = out / "input.json", out / "racket.json"
        save(input_path, {"input": grid})
        argv = [sys.executable, "-m", "arcpuzzles", "apply", TASK,
                "--input", str(input_path), "--out", str(output_path), "--timeout", "180"]
        record["racket_command"] = {"argv": argv, "cwd": str(repo), "exit_code": None,
                                     "input_path": str(input_path), "output_path": str(output_path)}
        save(report_path, record)
        completed = subprocess.run(argv, cwd=repo, capture_output=True, text=True, timeout=240)
        record["racket_command"].update({"exit_code": completed.returncode,
                                         "stdout": completed.stdout, "stderr": completed.stderr})
        if completed.returncode:
            raise RuntimeError(f"Public arcpuzzles apply failed with exit {completed.returncode}")
        receipt = json.loads(output_path.read_text())
        record["racket_command"]["receipt_sha256"] = sha(output_path)
        if receipt["generator_sha256"] != args.expected_generator_sha or sha(source_path) != args.expected_generator_sha:
            raise ValueError("Source changed during materialization or reference execution")
        if receipt["executed_rule_hash"] != args.expected_rule_hash or not receipt["rule_hash_matches_catalog"]:
            raise ValueError("Actual Racket authority differs from the expected rule hash")
        record["source"].update({"executed_rule_hash": receipt["executed_rule_hash"],
                                 "executed_rule_text_sha256": receipt["rule_text_sha256"],
                                 "reference": receipt["reference"]})
        result = receipt["results"][0]
        if result["error"] or not result["valid_output"] or result["input"] != grid:
            raise ValueError(f"Invalid or mismatched actual Racket result: {result}")
        actual = result["output"]
        record["actual_racket_output"] = actual
        record["input_sha256"] = result["input_sha256"]
        record["actual_output_sha256"] = result["output_sha256"]
        for prediction in predictions.values():
            prediction["racket_disagreement_cells"] = [
                [r, c] for r, row in enumerate(actual) for c, value in enumerate(row)
                if prediction["output"][r][c] != value]
            prediction["disagrees_with_actual_racket"] = bool(prediction["racket_disagreement_cells"])
        record["summary"] = {
            "named_rivals": len(predictions),
            "rivals_refuted_on_this_actual_generated_input": sum(
                p["disagrees_with_actual_racket"] for p in predictions.values()),
            "true_semantic_witnesses": sum(record["semantic_witnesses"].values()),
        }
        if not all(p["disagrees_with_actual_racket"] for p in predictions.values()):
            raise ValueError("At least one declared rival survives this requested rich witness")
        record["status"] = "complete"
    except Exception as exc:
        record["status"] = "error"
        record["error"] = repr(exc)
        record["traceback"] = traceback.format_exc()
    save(report_path, record)
    if record["status"] == "complete":
        save(Path(args.counterexamples).resolve(), record)
    print(json.dumps({"status": record["status"], "summary": record.get("summary"),
                      "observed_axes": record.get("observed_axes"), "report": str(report_path)}, indent=2))
    return 0 if record["status"] == "complete" else 1


if __name__ == "__main__":
    raise SystemExit(main())
