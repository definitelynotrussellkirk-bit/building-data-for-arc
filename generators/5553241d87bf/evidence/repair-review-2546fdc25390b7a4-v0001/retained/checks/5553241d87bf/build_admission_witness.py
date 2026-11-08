#!/usr/bin/env python3
"""Upgrade the task-local causal audit into the native admission witness schema.

This tool intentionally does not invent labels. It binds an already-qualified
setting program and an already-protected raw counterfactual receipt, then emits
exactly the source-bound witness consumed by ARCpuzzles owner replay.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def load_module(path: Path):
    runtime = path.resolve().parents[4] / "shared" / "runtime"
    sys.path.insert(0, str(runtime))
    spec = importlib.util.spec_from_file_location("marker_count_rotation_witness_source", path)
    if spec is None or spec.loader is None:
        raise ValueError(f"cannot load prototype: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_settings_key(settings: dict[str, Any]) -> str:
    return json.dumps(settings, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--qualification", type=Path, required=True)
    parser.add_argument("--raw-witness", type=Path, required=True)
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--prototype", type=Path, required=True)
    parser.add_argument("--task-id", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    qualification = read_json(args.qualification)
    raw = read_json(args.raw_witness)
    results = read_json(args.results)
    if qualification.get("status") != "qualified" or qualification.get("task_id") != args.task_id:
        raise ValueError("qualification is not the requested qualified task")
    target = next(
        (row for row in results.get("repair_targets", []) if row.get("task_id") == args.task_id),
        None,
    )
    if not isinstance(target, dict):
        raise ValueError("results do not contain the requested task")
    dependency = target.get("parametric_work", {}).get("sequential_dependency")
    if not isinstance(dependency, dict):
        raise ValueError("results lack sequential_dependency")

    prototype = load_module(args.prototype)
    programs = prototype.rival_programs()
    settings = raw.get("setting")
    if not isinstance(settings, dict):
        raise ValueError("raw witness lacks setting")
    setting_key = canonical_settings_key(settings)
    program = programs.get("marker_count_rotation")
    counterfactual = programs.get("always_quarter_turn")
    if not isinstance(program, str) or not isinstance(counterfactual, str):
        raise ValueError("prototype lacks required correct/counterfactual programs")
    expected_hash = qualification.get("programs", {}).get(setting_key)
    actual_hash = hashlib.sha256(program.encode("utf-8")).hexdigest()
    if actual_hash != expected_hash:
        raise ValueError("correct witness program is not the exact qualified setting program")
    if raw.get("programs", {}).get("correct", {}).get("sha256") != actual_hash:
        raise ValueError("raw witness correct-program hash differs")
    counterfactual_hash = hashlib.sha256(counterfactual.encode("utf-8")).hexdigest()
    if raw.get("programs", {}).get("wrong_intermediate", {}).get("sha256") != counterfactual_hash:
        raise ValueError("raw witness counterfactual-program hash differs")

    required_raw = ("input", "correct_output", "wrong_intermediate_output", "intermediate")
    if any(key not in raw for key in required_raw):
        raise ValueError("raw witness lacks causal case fields")
    named = {key: dependency.get(key) for key in (
        "step_a", "intermediate", "step_b", "why_b_depends_on_a"
    )}
    if any(not isinstance(value, str) or not value.strip() for value in named.values()):
        raise ValueError("sequential dependency descriptions must be nonempty strings")

    witness = {
        "schema": "arcpuzzles-sequential-dependency-witness-v1",
        "source_binding": qualification["source_binding"],
        "racket": {"backend": "racket", "protected": True},
        **named,
        "cases": [
            {
                "input": raw["input"],
                "settings": settings,
                "intermediate_value": raw["intermediate"],
                "output": raw["correct_output"],
                "counterfactual_output": raw["wrong_intermediate_output"],
                "ablation": "wrong_intermediate",
                "program": program,
                "counterfactual_program": counterfactual,
                "changed_cells": raw.get("changed_cells"),
            }
        ],
        "provenance": {
            "qualification_sha256": hashlib.sha256(args.qualification.read_bytes()).hexdigest(),
            "raw_witness_sha256": hashlib.sha256(args.raw_witness.read_bytes()).hexdigest(),
            "training_admitted": False,
        },
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(witness, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": "built",
        "cases": 1,
        "out": str(args.out),
        "sha256": hashlib.sha256(args.out.read_bytes()).hexdigest(),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
