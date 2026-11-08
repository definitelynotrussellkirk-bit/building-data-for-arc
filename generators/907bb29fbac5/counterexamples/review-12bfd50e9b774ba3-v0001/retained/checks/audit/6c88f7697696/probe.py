"""Findings-only audit; invented rivals are distinguished from declarations.

Run from WORK/repo with PYTHONPATH=src:shared/runtime and the packet interpreter.
This script never modifies a generator or changes approval/training state.
"""
from __future__ import annotations

from collections import Counter
import copy
import hashlib
import json
from pathlib import Path
import random
import re
import sys

from reviewer_support import canonical_pairs, canonical_path, find_root, load_selected_generator


TASK = "6c88f7697696"
EXPECTED = {
    "17a429a40b62": "ed4067e90712fe2df759fe0a8a57c9f29ee5e961b99811e71ac5cb4e34d35ff6",
    "6c88f7697696": "bf56a4bbe13feb934341436cca2cb6d8e2cf896b9d8cdb54459fa9106d18b745",
}
BANDS = ("easy", "medium", "hard")
SEEDS = (0, 17, 20261019)
SCHEDULE_SEED = 20261019
OUT = Path(__file__).resolve().parent
ROOT = find_root(__file__)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def write(name, value):
    (OUT / name).write_text(json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n")


def selected():
    gen, source, sha = load_selected_generator(TASK, root=ROOT)
    assert sha == EXPECTED[TASK], (sha, EXPECTED[TASK])
    return gen, source, sha


def observe(gen, grid):
    return {"grid_h": len(grid), "grid_w": len(grid[0]), **gen.observe_overrides(grid)}


def named_rivals(gen):
    rivals = {}
    declarations = {}
    for attribute in ("CANONICAL_SHORTCUTS", "LESSON_COMPETITORS"):
        declared = getattr(gen, attribute, {})
        declarations[attribute] = list(declared)
        for name, function in declared.items():
            rivals[name] = function
    if TASK == "17a429a40b62":
        def remap(grid, fixed=False, bidirectional=False):
            out = copy.deepcopy(grid)
            columns = (0, 2, 4) if fixed else range(len(grid[0]))
            mapping = {grid[0][c]: grid[1][c] for c in columns if c < len(grid[0]) and grid[0][c] and grid[1][c]}
            if bidirectional:
                mapping.update({value: key for key, value in list(mapping.items())})
            for r in range(2, len(grid)):
                for c, value in enumerate(grid[r]):
                    out[r][c] = mapping.get(value, value)
            return out
        rivals["auditor: fixed legend columns 0/2/4"] = lambda grid: remap(grid, fixed=True)
        rivals["auditor: bidirectional source/destination swap"] = lambda grid: remap(grid, bidirectional=True)
    return rivals, declarations


def prepare():
    gen, source, sha = selected()
    canonical = canonical_pairs(TASK, root=ROOT, labeled_only=True)
    rows = []
    with canonical_path(ROOT).open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK:
                rows.append(row)
    rules = sorted({row["program_solution"] for row in rows})
    assert len(rules) == 1
    rule = rules[0]
    rule_hash = hashlib.sha256(" ".join(rule.split()).encode()).hexdigest()[:12]
    assert gen.RULE_HASH == rule_hash
    rivals, declarations = named_rivals(gen)
    report = {
        "schema": "findings-only-generator-audit-v1", "task_id": TASK,
        "generator_sha256": sha, "generator_path": str(source),
        "rule_hash": rule_hash, "rule_source_sha256": hashlib.sha256(rule.encode()).hexdigest(),
        "canonical_rows": len(rows), "canonical_pairs": len(canonical),
        "notes_path": str(source.parent / "notes.md"),
        "review_index_present": (source.parent / "evidence/review_index.json").exists(),
        "declared_axes": gen.AXES, "rival_declarations": declarations,
        "auditor_rivals": [name for name in rivals if name.startswith("auditor:")],
        "examples_needed": gen.EXAMPLES_NEEDED,
        "canonical_self_check": [gen.self_check(pair["input"]) for pair in canonical],
        "canonical_rival_predictions_unconfirmed": {
            name: [function(pair["input"]) for pair in canonical]
            for name, function in rivals.items()
        },
        "command": {"cwd": "repo", "argv": [sys.executable, "-B", *sys.argv],
                    "env": {"PYTHONPATH": "src:shared/runtime"}, "exit_code": 0},
    }
    frequencies = {band: {} for band in BANDS}
    unique = set()
    failures = []
    draws = 0
    for band in BANDS:
        for seed in SEEDS:
            for index in range(28):
                draws += 1
                try:
                    grid = gen.generate(seed, index, difficulty=band)
                    errors = gen.self_check(grid)
                    if errors:
                        failures.append({"seed": seed, "sample_index": index, "difficulty": band, "self_check": errors, "input": grid})
                    unique.add(digest(grid))
                    for key, value in observe(gen, grid).items():
                        frequencies[band].setdefault(key, Counter())[str(value)] += 1
                except Exception as error:
                    failures.append({"seed": seed, "sample_index": index, "difficulty": band, "exception": type(error).__name__, "message": str(error)})
    report["ordinary_census"] = {"seeds": SEEDS, "sample_indices": [0, 27], "bands": BANDS,
                                  "calls": draws, "unique_inputs": len(unique), "failures": failures,
                                  "observable_counts_by_band": frequencies}
    axis_cases = []
    for axis, spec in gen.AXES.items():
        valid = spec["valid"]
        if spec["type"] == "int":
            lo, hi = map(int, re.fullmatch(r"(\d+)\.\.(\d+)", valid).groups())
            values = range(lo, hi + 1)
        else:
            values = valid
        for band in BANDS:
            for value in values:
                record = {"axis": axis, "requested": value, "difficulty": band}
                try:
                    grid = gen.generate(SCHEDULE_SEED, 5, difficulty=band, **{axis: value})
                    record.update({"observed": observe(gen, grid)[axis], "self_check": gen.self_check(grid),
                                   "exact": observe(gen, grid)[axis] == value})
                except Exception as error:
                    record.update({"exception": type(error).__name__, "message": str(error)})
                axis_cases.append(record)
    report["declared_axis_sweep"] = {"seed": SCHEDULE_SEED, "sample_index": 5, "calls": len(axis_cases), "cases": axis_cases}
    if TASK == "17a429a40b62":
        invalid = [{"n_pairs": 2.75}, {"n_pairs": "2"}, {"grid_h": 5.75},
                   {"unchanged_body_colors": True}, {"ignored_control": 123}, {"difficulty": "impossible"}]
    else:
        invalid = [{"source_color_count": True}, {"source_color_count": 1.75}, {"source_color_count": "2"},
                   {"a_cells": 3.75}, {"c_cells": "7"}, {"a_cells": False},
                   {"transform": "id"}, {"unexpected_control": 123}, {"difficulty": "impossible"}]
    invalid_results = []
    for supplied in invalid:
        record = {"seed": SCHEDULE_SEED, "sample_index": 5, "supplied": supplied}
        try:
            grid = gen.generate(SCHEDULE_SEED, 5, **supplied)
            record.update({"accepted": True, "observed": observe(gen, grid), "input": grid,
                           "self_check": gen.self_check(grid),
                           "self_check_with_supplied_meta": gen.self_check(grid, meta={"overrides": supplied})})
        except Exception as error:
            record.update({"accepted": False, "exception": type(error).__name__, "message": str(error)})
        invalid_results.append(record)
    report["invalid_control_probes"] = invalid_results
    base = gen.generate(SCHEDULE_SEED, 0)
    malformed = {"empty": [], "ragged": copy.deepcopy(base), "boolean_cell": copy.deepcopy(base),
                 "fractional_cell": copy.deepcopy(base), "out_of_palette": copy.deepcopy(base)}
    malformed["ragged"][0].pop()
    malformed["boolean_cell"][0][0] = True
    malformed["fractional_cell"][0][0] = 0.5
    malformed["out_of_palette"][0][0] = 10
    report["malformed_validator_probes"] = {name: gen.self_check(grid) for name, grid in malformed.items()}
    state = random.getstate()
    first = gen.generate(SCHEDULE_SEED, 5)
    second = gen.generate(SCHEDULE_SEED, 5)
    report["replay"] = {"seed": SCHEDULE_SEED, "sample_index": 5, "calls": 2,
                        "equal": first == second, "fresh_rows": all(a is not b for a, b in zip(first, second)),
                        "global_rng_unchanged": state == random.getstate()}
    period = 4 if TASK == "17a429a40b62" else 14
    demo_count = gen.EXAMPLES_NEEDED
    inputs = []
    ordering = []
    for pair in canonical:
        ordering.append({"kind": "canonical", "variant": pair["variant"], "split": pair["split"], "pair_index": pair["pair_index"]})
        inputs.append(pair["input"])
    for band in BANDS:
        for index in range(period + demo_count):
            ordering.append({"kind": "scheduled", "seed": SCHEDULE_SEED, "sample_index": index, "difficulty": band})
            inputs.append(gen.generate(SCHEDULE_SEED, index, difficulty=band))
    assert len(inputs) <= 64
    report["authority_input_order"] = ordering
    report["lesson_policy"] = {"schedule_period_derived_from_source": period, "schedule_seed": SCHEDULE_SEED,
                                "demonstrations": demo_count, "query_policy": "next consecutive sample",
                                "cyclic_starts": [0, period - 1], "bands": BANDS,
                                "distinct_materialized_inputs": len({digest(grid) for grid in inputs}),
                                "materialized_inputs": len(inputs)}
    write("input.json", inputs)
    write("probe.json", report)
    print(json.dumps({"task_id": TASK, "ordinary_calls": draws, "ordinary_failures": len(failures),
                      "axis_calls": len(axis_cases), "axis_failures": sum(not case.get("exact", False) or bool(case.get("self_check")) for case in axis_cases),
                      "invalid_controls_accepted": sum(case["accepted"] for case in invalid_results),
                      "invalid_controls_tested": len(invalid_results), "authority_inputs": len(inputs)}))


if __name__ == "__main__":
    if sys.argv[1:] != ["prepare"]:
        raise SystemExit("usage: probe.py prepare")
    prepare()
