#!/usr/bin/env python3
"""Emit generated witnesses and verify a separately obtained canonical receipt.

No intended Python labels are generated. The current rival registry is evaluated
from source, so a newly added rival cannot silently disappear from verification.
Use a new output directory to preserve previous successes and failures.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

TASK = "49754d8fa42e"
ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "generators" / TASK / "generator.py"


def _load():
    sys.path.insert(0, str(ROOT / "shared/runtime"))
    spec = importlib.util.spec_from_file_location("counterexample_generator", SOURCE)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    exec(compile(SOURCE.read_bytes(), str(SOURCE), "exec"), module.__dict__)
    return module


def _hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _predictions(module, grid):
    _require(bool(module.CANONICAL_SHORTCUTS), "current shortcut registry is empty")
    result = {}
    for name, rival in module.CANONICAL_SHORTCUTS.items():
        candidate = copy.deepcopy(grid)
        result[name] = rival(candidate)
        _require(candidate == grid, f"rival {name} mutated its input")
    return result


def _record(module, seed, index, pins, kind):
    grid = module.generate(seed, index, difficulty="medium", **pins)
    _require(module.self_check(grid) == [], "generated witness fails self_check")
    observed = module.observe_overrides(grid)
    values = [v for row in grid for v in row if v]
    mode = observed["mode_color"]
    endpoints = int(values[0] == mode) + int(values[-1] == mode)
    return {"seed": seed, "sample_index": index, "difficulty": "medium",
            "overrides": dict(pins), "kind": kind,
            "mode_at_endpoint_count": endpoints,
            "profile": module.schedule_profile(seed, index, "medium"),
            "observed": observed, "input": grid,
            "rival_outputs": _predictions(module, grid)}


def emit(directory):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    for name in ("input.json", "generated.json", "racket.json", "verified.json"):
        if (directory / name).exists():
            raise FileExistsError(f"refusing to overwrite retained evidence: {directory / name}")
    source_hash = _hash(SOURCE)
    module = _load()
    pins = {"grid_h": 5, "grid_w": 5, "mode_color": 2,
            "mode_count": 5, "palette_size": 4}
    controlled = {}
    for index in range(30):
        row = _record(module, 17, index, pins, "controlled_endpoint")
        count = row["mode_at_endpoint_count"]
        if count in (0, 1):
            controlled.setdefault(count, row)
        if len(controlled) == 2:
            break
    _require(len(controlled) == 2, "could not realize both controlled endpoint kinds in indices 0..29")
    spatial = {}
    for seed in range(17, 33):
        for index in range(12):
            if not module.schedule_spatial_witness(seed, index):
                continue
            row = _record(module, seed, index, {}, "default_spatial")
            grid = row["input"]
            _require(module.SEMANTIC_WITNESSES["component_size_decoy"](grid),
                     "scheduled spatial example lacks a strict component witness")
            _require(module.SEMANTIC_WITNESSES["bbox_area_decoy"](grid),
                     "scheduled spatial example lacks a strict bbox witness")
            count = row["mode_at_endpoint_count"]
            _require(count in (0, 1), "unexpected spatial endpoint condition")
            spatial.setdefault(count, row)
            if len(spatial) == 2:
                break
        if len(spatial) == 2:
            break
    _require(len(spatial) == 2, "bounded search did not realize both spatial endpoint conditions")
    rows = [controlled[0], controlled[1], spatial[0], spatial[1]]
    _require(_hash(SOURCE) == source_hash, "generator source changed during emission")
    _write(directory / "input.json", [row["input"] for row in rows])
    _write(directory / "generated.json", {
        "schema": "arcpuzzles-task-counterexamples-v2", "task_id": TASK,
        "generator_sha256": source_hash, "probe_sha256": _hash(Path(__file__)),
        "rule_hash": module.RULE_HASH,
        "sampler": "actual generate calls; two controlled endpoint cases plus two unpinned spatial cases",
        "domain": "All four inputs pass self_check. This is a witness set, not a complete teaching lesson.",
        "examples": rows})
    print(json.dumps({"emitted": len(rows), "directory": str(directory)}))


def verify(directory):
    directory = Path(directory)
    generated = json.loads((directory / "generated.json").read_text())
    inputs = json.loads((directory / "input.json").read_text())
    reference = json.loads((directory / "racket.json").read_text())
    source_hash = _hash(SOURCE)
    module = _load()
    _require(generated.get("task_id") == reference.get("task_id") == TASK, "task identity mismatch")
    _require(reference.get("schema") == "arcpuzzles-apply-v1", "unsupported reference receipt")
    _require(reference.get("reference") == "canonical", "canonical reference required")
    _require(generated["generator_sha256"] == reference.get("generator_sha256") == source_hash,
             "generator source identity mismatch")
    _require(reference.get("rule_hash_matches_catalog") is True, "unbound reference rule")
    _require(reference.get("executed_rule_hash") == generated["rule_hash"] == module.RULE_HASH,
             "executed rule identity mismatch")
    results = reference["results"]
    examples = generated["examples"]
    _require(0 < len(results) == len(examples) <= 64, "reference/example count mismatch")
    _require(inputs == [e["input"] for e in examples], "input.json and generated metadata disagree")
    refuted = {name: [] for name in module.CANONICAL_SHORTCUTS}
    for index, (example, actual) in enumerate(zip(examples, results)):
        grid = example["input"]
        _require(actual.get("input") == grid, f"input mismatch at {index}")
        _require(actual.get("error") is None and actual.get("valid_output") is True
                 and actual.get("output") is not None, f"reference execution failed at {index}")
        _require(module.self_check(grid) == [], f"witness {index} is outside the task domain")
        replay = module.generate(example["seed"], example["sample_index"],
                                 difficulty=example["difficulty"], **example["overrides"])
        _require(replay == grid, f"generator replay mismatch at {index}")
        predictions = _predictions(module, grid)
        _require(predictions == example["rival_outputs"], f"stale or altered rival predictions at {index}")
        for name, prediction in predictions.items():
            if prediction != actual["output"]:
                refuted[name].append(index)
    _require(_hash(SOURCE) == source_hash, "generator changed during verification")
    report = {"task_id": TASK, "generator_sha256": source_hash,
              "probe_sha256": _hash(Path(__file__)),
              "reference_receipt_sha256": _hash(directory / "racket.json"),
              "rule_hash": reference["executed_rule_hash"], "inputs_verified": len(results),
              "rival_refuted_on_input_indices": refuted, "passed": all(refuted.values())}
    _write(directory / "verified.json", report)
    print(json.dumps(report))
    if not report["passed"]:
        raise SystemExit(1)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("emit", "verify"))
    parser.add_argument("--out-dir", type=Path, required=True)
    options = parser.parse_args()
    {"emit": emit, "verify": verify}[options.mode](options.out_dir)


if __name__ == "__main__":
    main()
