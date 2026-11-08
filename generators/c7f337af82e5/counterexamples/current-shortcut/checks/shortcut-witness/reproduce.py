#!/usr/bin/env python3
"""Reproduce two final-source default witnesses; then compare public Racket labels."""
from __future__ import annotations
import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
PACKET = HERE.parents[1]
REPO = PACKET / "repo"
TASK = "c7f337af82e5"

def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    sys.modules[name] = result
    spec.loader.exec_module(result)
    return result

def sha(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("build", "verify"))
    args = parser.parse_args()
    source = REPO / "generators" / TASK / "generator.py"
    gen = module("shortcut_witness_generator", source)
    probe = module("shortcut_witness_probe", source.parent / "workspace/probe_distribution.py")
    cases = []
    for sample_index in (2, 28):
        grid = gen.generate(0, sample_index, difficulty="easy")
        expected, objects = probe.oracle(grid)
        rival = gen.CANONICAL_SHORTCUTS["not_smallest_perimeter"](deepcopy(grid))
        reasons = gen.self_check(grid)
        assert not reasons
        assert sorted(x["pixels"] for x in objects) == [8, 15]
        cases.append({"seed": 0, "sample_index": sample_index, "difficulty": "easy", "overrides": {},
                      "input": grid, "input_sha256": sha(grid),
                      "validator_reasons": reasons, "domain": "exact frame and filled rectangle",
                      "objects": objects, "python_expected": expected, "rival_output": rival})
    report = {"task_id": TASK, "generator_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
              "rule_hash": gen.RULE_HASH, "rival": "not_smallest_perimeter", "cases": cases}
    if args.mode == "build":
        (HERE / "input.json").write_text(json.dumps([x["input"] for x in cases], indent=2) + "\n")
        (HERE / "expected.json").write_text(json.dumps(report, indent=2) + "\n")
    else:
        receipt = json.loads((HERE / "racket.json").read_text())
        results = receipt["results"]
        for case, result in zip(cases, results, strict=True):
            actual = result["output"]
            assert actual == case["python_expected"]
            assert actual != case["rival_output"]
            case["actual_racket_output"] = actual
            case["differing_cells"] = [
                {"row": r, "col": c, "racket": actual[r][c], "rival": case["rival_output"][r][c]}
                for r in range(len(actual)) for c in range(len(actual[0]))
                if actual[r][c] != case["rival_output"][r][c]]
        report["public_apply_receipt"] = "checks/shortcut-witness/racket.json"
        report["receipt_sha256"] = hashlib.sha256((HERE / "racket.json").read_bytes()).hexdigest()
        report["status"] = "verified"
        (HERE / "counterexample.json").write_text(json.dumps(report, indent=2) + "\n")
        print(json.dumps({"status": "verified", "generator_sha256": report["generator_sha256"],
                          "rule_hash": report["rule_hash"],
                          "differing_cells": [len(x["differing_cells"]) for x in cases]}))

if __name__ == "__main__":
    main()

