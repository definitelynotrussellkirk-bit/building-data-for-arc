#!/usr/bin/env python3
"""Replay a declared rival on a deliberately constructed authoring lesson.
Reads retained JSON/gzip labels; never generates examples or calls the authority.
Exit 0 means completed: inspect constructed_ambiguity for the diagnostic finding.
"""
import argparse
from copy import deepcopy
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

from arcpuzzles import Catalog
from reviewer_support import normalize_grid

def sha(data):
    return hashlib.sha256(data).hexdigest()

def digest(value):
    return sha(json.dumps(value, sort_keys=True, separators=(",", ":")).encode())

def read_report(path):
    stored = path.read_bytes()
    raw = gzip.decompress(stored) if path.suffix == ".gz" else stored
    return json.loads(raw), {"path": str(path), "stored_sha256": sha(stored), "json_sha256": sha(raw)}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("census", "query-receipt", "out"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--rival", required=True)
    parser.add_argument("--lesson-index", type=int, default=0)
    parser.add_argument("--query-index", type=int, default=0)
    args = parser.parse_args()
    census, census_file = read_report(args.census)
    receipt, query_file = read_report(args.query_receipt)
    assert 0 <= args.lesson_index < len(census["lessons"]), "Invalid lesson index"
    assert 0 <= args.query_index < len(receipt["results"]), "Invalid query index"
    lesson, query = census["lessons"][args.lesson_index], receipt["results"][args.query_index]
    catalog = Catalog()
    row = catalog.get(census["task_id"])
    source = catalog.root / row["generator"]
    source_bytes = source.read_bytes()
    spec = importlib.util.spec_from_file_location("conditional_probe_generator", source)
    generator = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = generator
    spec.loader.exec_module(generator)
    rival = generator.SEMANTIC_RIVALS[args.rival]
    assert callable(rival), "Selected declaration is not callable"
    assert row["id"] == receipt["task_id"] == generator.TASK_ID, "Task mismatch"
    assert census["declared_rule_hash"] == receipt["executed_rule_hash"] == row["rule_hash"] == generator.RULE_HASH
    assert receipt["reference"] == "canonical" and receipt["rule_hash_matches_catalog"]
    assert census["rule_callable_sha256"] == receipt["rule_text_sha256"], "Executable rule mismatch"
    assert {sha(v["program_solution"].encode()) for v in row["variants"]} == {census["rule_source_sha256"]}
    assert digest(lesson["instance"]) == lesson["instance_sha256"], "Retained instance hash mismatch"
    assert query["valid_output"] and query["error"] is None, "Query lacks a successful authority result"
    assert digest(query["input"]) == query["input_sha256"] and digest(query["output"]) == query["output_sha256"]
    def score(pair):
        grid, expected = normalize_grid(pair["input"]), normalize_grid(pair["output"])
        assert not generator.self_check(grid), "Input is outside the current documented domain"
        predicted = normalize_grid(rival(deepcopy(grid)))
        differences = []
        for r in range(max(len(expected), len(predicted))):
            a, b = expected[r] if r < len(expected) else [], predicted[r] if r < len(predicted) else []
            for c in range(max(len(a), len(b))):
                actual, wanted = b[c] if c < len(b) else None, a[c] if c < len(a) else None
                if actual != wanted:
                    differences.append({"row": r, "column": c, "expected": wanted, "rival": actual})
        observer = getattr(generator, "observe_overrides", None)
        return {"input_sha256": digest(grid), "expected_sha256": digest(expected),
                "prediction_sha256": digest(predicted), "fits": not differences,
                "context": observer(deepcopy(grid)) if callable(observer) else None,
                "difference_count": len(differences), "differences": differences}
    demos = [score(pair) for pair in lesson["instance"]["train"]]
    scored_query = score(query)
    assert sha(source.read_bytes()) == sha(source_bytes), "Generator changed during the probe"
    result = {"schema": "arcpuzzles-conditional-context-probe-v1", "task_id": row["id"],
              "intent": "intentionally_constructed_diagnostic_not_production_failure_or_model_solve",
              "census_file": census_file, "query_receipt_file": query_file,
              "demo_generator_sha256": census["generator_sha256"], "query_generator_sha256": receipt["generator_sha256"],
              "rival_generator_sha256": sha(source_bytes), "rival": args.rival,
              "rule_hash": row["rule_hash"], "rule_source_sha256": census["rule_source_sha256"],
              "rule_callable_sha256": census["rule_callable_sha256"], "lesson_index": args.lesson_index,
              "query_index": args.query_index, "lesson_instance_sha256": lesson["instance_sha256"],
              "demo_origin": {key: lesson[key] for key in ("band", "seed", "sample_index")},
              "demonstrations": demos, "query": scored_query, "demonstrations_fit": sum(p["fits"] for p in demos),
              "demonstration_count": len(demos), "constructed_ambiguity": all(p["fits"] for p in demos) and not scored_query["fits"],
              "new_generated_inputs": 0, "new_reference_executions": 0, "rival_evaluations": len(demos) + 1,
              "label_basis": "Retained actual Racket labels, hash-checked and reused without relabeling.",
              "script_sha256": sha(Path(__file__).read_bytes()), "argv": sys.argv, "cwd": str(Path.cwd())}
    with args.out.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2)
        stream.write("\n")
    print(json.dumps({"result": str(args.out), "demo_fit": f"{result['demonstrations_fit']}/{len(demos)}",
                      "query_differences": scored_query["difference_count"], "constructed_ambiguity": result["constructed_ambiguity"]}))

if __name__ == "__main__":
    main()
