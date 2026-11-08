#!/usr/bin/env python3
"""Prepare finite audit inputs, then score the supported arcpuzzles apply receipt."""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
from pathlib import Path
import sys

from reviewer_support import canonical_pairs, canonical_path, find_root, load_selected_generator

TASK = "07dbda8c31c9"


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def write_new(path, value):
    if path.exists():
        raise FileExistsError(f"preserve existing evidence: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def components(grid):
    left = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 2}
    count = 0
    while left:
        count += 1
        stack = [left.pop()]
        while stack:
            r, c = stack.pop()
            for point in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if point in left:
                    left.remove(point)
                    stack.append(point)
    return count


def rival_outputs(grid):
    red = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 2]
    area = (max(r for r, c in red) - min(r for r, c in red) + 1) * (max(c for r, c in red) - min(c for r, c in red) + 1)
    return {
        "count_all_nonzero": [[2] * sum(value != 0 for row in grid for value in row)],
        "count_red_components": [[2] * components(grid)],
        "copy_input_width": [[2] * len(grid[0])],
        "red_bounding_box_area": [[2] * area],
    }


def prepare(directory):
    root = find_root(Path.cwd())
    gen, source, source_hash = load_selected_generator(TASK, root=root)
    canonical = canonical_path(root)
    with canonical.open() as stream:
        authority = next(json.loads(line) for line in stream if json.loads(line).get("task_id") == TASK)
    rule = authority["program_solution"]
    report = {
        "schema": "07dbda8c31c9-audit-inputs-v1", "task_id": TASK,
        "generator_sha256": source_hash, "generator_source": str(source),
        "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "canonical_path": str(canonical),
        "canonical_file_sha256": hashlib.sha256(canonical.read_bytes()).hexdigest(),
        "rule_text": rule, "rule_text_sha256": hashlib.sha256(rule.encode()).hexdigest(),
        "normalized_rule_hash": hashlib.sha256(" ".join(rule.split()).encode()).hexdigest()[:12],
        "declared_rule_hash": gen.RULE_HASH,
        "review_index_exists": (source.parent / "evidence/review_index.json").exists(),
        "semantic_contract_declarations": {name: hasattr(gen, name) for name in (
            "LESSON_COMPETITORS", "SEMANTIC_RIVALS", "SEMANTIC_WITNESSES", "lesson_identifiable", "LESSON_SCHEDULE_PERIOD")},
        "cwd": str(Path.cwd()), "argv": [sys.executable, *sys.argv],
    }
    grids, records, index_by_hash = [], [], {}

    def retain(grid, **metadata):
        sha = digest(grid)
        if sha not in index_by_hash:
            index_by_hash[sha] = len(grids)
            grids.append(grid)
        index = index_by_hash[sha]
        records.append({**metadata, "input_index": index, "input_sha256": sha,
                        "validator_reasons": gen.self_check(grid), "observed": gen.observe_overrides(grid)})
        return index

    canonical_indexes = []
    for pair_index, pair in enumerate(canonical_pairs(TASK, root=root)):
        canonical_indexes.append(retain(pair["input"], kind="canonical", pair_index=pair_index,
                                        canonical_output=pair["output"]))
    scheduled = {}
    for seed, band, index in itertools.product((0, 17), ("easy", "medium", "hard"), range(6)):
        call = dict(seed=seed, sample_index=index, difficulty=band)
        scheduled[seed, band, index] = retain(gen.generate(**call), kind="generated", call=call)

    boundary_cases = [{"grid_h": 4}, {"grid_h": 12}, {"grid_w": 4}, {"grid_w": 30},
                      {"n_red": 2}, {"n_red": 28}, {"texture": "plain"},
                      {"texture": "decoy_colors"}, {"texture": "blob"}]
    boundary_results = []
    for index, overrides in enumerate(boundary_cases):
        call = dict(seed=701, sample_index=index, difficulty="medium", **overrides)
        grid = gen.generate(**call)
        observed = gen.observe_overrides(grid)
        input_index = retain(grid, kind="boundary", call=call)
        boundary_results.append({"call": call, "observed": observed, "input_index": input_index,
                                 "passed": all(observed[key] == value for key, value in overrides.items())})
    report["exact_boundaries"] = boundary_results

    scalar_results, retained_scalar_axes = [], set()
    for band, (axis, values) in itertools.product(
        (None, "easy", "medium", "hard"),
        {"grid_h": (4.0, 4.75, "4"), "grid_w": (4.0, 4.75, "4"), "n_red": (5.0, 5.75, "5")}.items(),
    ):
        for value in values:
            call = dict(seed=991, sample_index=0, difficulty=band)
            call[axis] = value
            result = {"axis": axis, "value_type": type(value).__name__, "call": call}
            try:
                grid = gen.generate(**call)
                result.update(status="accepted_invalid_integer", observed=gen.observe_overrides(grid),
                              validator_reasons=gen.self_check(grid), input_sha256=digest(grid))
                if axis not in retained_scalar_axes:
                    result["input_index"] = retain(grid, kind="invalid_scalar_witness", call=call)
                    retained_scalar_axes.add(axis)
            except Exception as exc:
                result.update(status="rejected", exception_type=type(exc).__name__, message=str(exc))
            scalar_results.append(result)
    report["invalid_integer_overrides"] = scalar_results
    report["records"] = records
    report["canonical_indexes"] = canonical_indexes
    report["lessons"] = [
        {"seed": seed, "difficulty": band, "start": start,
         "sample_indices": list(range(start, start + 4)),
         "input_indexes": [scheduled[seed, band, index] for index in range(start, start + 4)]}
        for seed, band, start in itertools.product((0, 17), ("easy", "medium", "hard"), range(3))
    ]
    report["input_count"] = len(grids)
    report["inputs_digest"] = digest(grids)
    if len(grids) > 64:
        raise AssertionError("supported apply limit exceeded")
    write_new(directory / "inputs.json", grids)
    write_new(directory / "prepared.json", report)
    print(json.dumps({"generator_sha256": source_hash, "input_count": len(grids),
                      "invalid_integer_cases": len(scalar_results),
                      "invalid_integers_accepted": sum(row["status"] == "accepted_invalid_integer" for row in scalar_results),
                      "exact_boundary_passes": sum(row["passed"] for row in boundary_results)}, indent=2))


def score(directory):
    prepared = json.loads((directory / "prepared.json").read_text())
    inputs = json.loads((directory / "inputs.json").read_text())
    reference_path = directory / "racket.json"
    reference = json.loads(reference_path.read_text())
    if reference["schema"] != "arcpuzzles-apply-v1" or reference["task_id"] != TASK:
        raise ValueError("wrong supported apply receipt")
    if reference["generator_sha256"] != prepared["generator_sha256"]:
        raise ValueError("generator changed between input preparation and Racket execution")
    if reference["executed_rule_hash"] != prepared["normalized_rule_hash"] or not reference["rule_hash_matches_catalog"]:
        raise ValueError("executed canonical authority differs")
    if hashlib.sha256(canonical_path(find_root(Path.cwd())).read_bytes()).hexdigest() != prepared["canonical_file_sha256"]:
        raise ValueError("canonical source file changed")
    if digest(inputs) != prepared["inputs_digest"] or len(reference["results"]) != len(inputs):
        raise ValueError("input population changed")
    outputs = []
    for grid, record in zip(inputs, reference["results"], strict=True):
        if record["input"] != grid or record["output"] is None:
            raise ValueError("reference input mismatch or failed reference execution")
        outputs.append(record["output"])
    names = list(rival_outputs(inputs[0]))
    canonical_fit = {name: {"matches": sum(rival_outputs(inputs[index])[name] == outputs[index] for index in prepared["canonical_indexes"]),
                            "total": len(prepared["canonical_indexes"])} for name in names}
    lessons, counterexamples = [], {}
    for lesson in prepared["lessons"]:
        indexes = lesson["input_indexes"]
        rotations = []
        for query_position in range(4):
            query = indexes[query_position]
            demos = [index for position, index in enumerate(indexes) if position != query_position]
            ambiguous = [name for name in names if all(rival_outputs(inputs[index])[name] == outputs[index] for index in demos)
                         and rival_outputs(inputs[query])[name] != outputs[query]]
            rotations.append({"query_position": query_position, "ambiguous_rivals": ambiguous})
            for name in ambiguous:
                counterexamples.setdefault(name, {**lesson, "query_position": query_position,
                    "demonstration_input_indexes": demos, "query_input_index": query,
                    "input": inputs[query], "actual_racket_output": outputs[query],
                    "rival_output": rival_outputs(inputs[query])[name],
                    "self_check_reasons": next(row["validator_reasons"] for row in prepared["records"] if row["input_index"] == query)})
        lessons.append({**lesson, "unique_inputs": len(set(indexes)),
                        "ordered_ambiguities": rotations[-1]["ambiguous_rivals"], "rotations": rotations})
    result = {
        "schema": "07dbda8c31c9-finite-audit-v1", "task_id": TASK,
        "generator_sha256": prepared["generator_sha256"],
        "executed_rule_hash": reference["executed_rule_hash"],
        "canonical_raw_rule_sha256": prepared["rule_text_sha256"],
        "executed_callable_sha256": reference["rule_text_sha256"],
        "hash_scope_note": "apply.rule_text_sha256 hashes bundle.rule_callable_text, not raw canonical program_solution; both identities are retained separately",
        "preparation_probe_sha256": prepared["probe_sha256"],
        "reference_receipt_sha256": hashlib.sha256(reference_path.read_bytes()).hexdigest(),
        "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "cwd": str(Path.cwd()), "argv": [sys.executable, *sys.argv],
        "input_count": len(inputs),
        "racket_count_red_matches": sum(output == [[2] * sum(value == 2 for row in grid for value in row)] for grid, output in zip(inputs, outputs)),
        "all_retained_inputs_validator_accepted": all(row["validator_reasons"] == [] for row in prepared["records"]),
        "exact_boundary_passes": sum(row["passed"] for row in prepared["exact_boundaries"]),
        "exact_boundary_total": len(prepared["exact_boundaries"]),
        "invalid_integer_accepted": sum(row["status"] == "accepted_invalid_integer" for row in prepared["invalid_integer_overrides"]),
        "invalid_integer_total": len(prepared["invalid_integer_overrides"]),
        "canonical_rival_fit": canonical_fit,
        "lesson_policy": "Three consecutive direct generate demonstrations followed by next query; real Racket labels, no production materializer or all-seed claim",
        "lesson_count": len(lessons), "ordered_ambiguous_lessons": sum(bool(row["ordered_ambiguities"]) for row in lessons),
        "rotation_count": 4 * len(lessons),
        "ambiguous_rotations": sum(bool(rotation["ambiguous_rivals"]) for row in lessons for rotation in row["rotations"]),
        "lessons": lessons, "counterexamples": counterexamples,
        "semantic_contract_declarations": prepared["semantic_contract_declarations"],
        "interpretation": "Integer-override coercion is a reproduced contract defect. Rotation ambiguities limit arbitrary holdouts; they do not refute the stated ordered three-demo policy.",
    }
    write_new(directory / "verdict.json", result)
    print(json.dumps({key: value for key, value in result.items() if key not in ("lessons", "counterexamples")}, indent=2))


def verify_production(directory):
    """Bind the one materialized witness to the independently applied inputs."""
    path = directory / "production-witness.jsonl"
    lines = path.read_text().splitlines()
    assert len(lines) == 1
    episode = json.loads(lines[0])
    reference = json.loads((directory / "racket.json").read_text())
    verdict_path = directory / "verdict.json"
    verdict = json.loads(verdict_path.read_text())
    assert episode["provenance"]["generator_sha256"] == verdict["generator_sha256"]
    assert episode["executed_rule_hash"] == verdict["executed_rule_hash"]
    indexes = next(row["input_indexes"] for row in verdict["lessons"]
                   if row["seed"] == 17 and row["difficulty"] == "easy" and row["start"] == 0)
    pairs = episode["train"] + episode["test"]
    assert len(episode["train"]) == 3 and len(episode["test"]) == 1
    assert [row["sample_index"] for row in episode["sampling"]["accepted_pairs"]] == [0, 1, 2, 3]
    assert episode["sampling"]["rejections"] == []
    for pair, index in zip(pairs, indexes, strict=True):
        assert pair["input"] == reference["results"][index]["input"]
        assert pair["output"] == reference["results"][index]["output"]
        assert reference["results"][index]["generator_domain"]["status"] == "valid"
    predictions = [rival_outputs(pair["input"])["copy_input_width"] for pair in pairs]
    assert all(pair["output"] == rival for pair, rival in zip(episode["train"], predictions[:3]))
    assert episode["test"][0]["output"] != predictions[3]
    summary = {
        "receipt": str(path), "receipt_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "source_and_reference_bound": True, "all_four_pairs_match_apply_receipt": True,
        "seed": 17, "difficulty": "easy", "accepted_sample_indices": [0, 1, 2, 3], "rejections": 0,
        "demo_input_widths": [len(pair["input"][0]) for pair in episode["train"]],
        "demo_output_widths": [len(pair["output"][0]) for pair in episode["train"]],
        "query_input_sha256": digest(episode["test"][0]["input"]),
        "query_input": episode["test"][0]["input"], "actual_racket_output": episode["test"][0]["output"],
        "width_rival_output": predictions[3], "lesson_check": episode["lesson_check"],
        "cwd": str(Path.cwd()), "argv": [sys.executable, *sys.argv],
    }
    if "production_witness" in verdict:
        raise FileExistsError("production witness already verified; preserve existing receipt")
    verdict["production_witness"] = summary
    verdict["interpretation"] = "Reproduced integer-override coercion and one production lesson ambiguous under the width-copy rival. Query-rotation findings remain a separate limitation."
    verdict_path.write_text(json.dumps(verdict, indent=2, sort_keys=True) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("prepare", "score", "production"))
    parser.add_argument("--dir", type=Path, default=Path("../checks/audit") / TASK)
    arguments = parser.parse_args()
    {"prepare": prepare, "score": score, "production": verify_production}[arguments.mode](arguments.dir)
