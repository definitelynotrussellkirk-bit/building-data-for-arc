"""Portable, source-bound border semantics probe with public Racket labels.

From WORK, use review.py run with the selected Python interpreter:
  ... generators/9b37d4bbfb7e/workspace/probe_border_semantics.py prepare
      --out ../checks/final/border-probe --baseline-source ../checks/baseline-generator.py
  ... -m arcpuzzles apply 9b37d4bbfb7e --check-generator-domain
      --input ../checks/final/border-probe/input.json --out ../checks/final/border-probe/racket.json
  ... generators/9b37d4bbfb7e/workspace/probe_border_semantics.py analyze
      --out ../checks/final/border-probe

The baseline source is optional and used only to verify the retained negative
pixels; it is never a runtime dependency. Authoritative outputs come only from
public apply. expected_output from test_generator_contract.py is separately
assessed as a Python mirror, never substituted for the authority.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK = "9b37d4bbfb7e"
HOME = Path(__file__).resolve().parent.parent
FIXTURES = HOME / "counterexamples/border-semantics-fixtures.json"


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def file_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def import_source(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def setup():
    root = find_root(__file__)
    generator, source, source_sha = load_selected_generator(TASK, root=root)
    return root, generator, source, source_sha


def prepare(output, baseline_source=None):
    root, generator, source, source_sha = setup()
    fixtures = json.loads(FIXTURES.read_text())
    cases = [{"kind": record["kind"], "name": record["name"], "input": record["input"],
              "recipe": record.get("baseline_recipe"),
              "origin": record["origin"]} for record in fixtures["fixtures"]]
    baseline = None
    if baseline_source is not None:
        old = import_source(baseline_source, "border_probe_baseline")
        checks = []
        for record in fixtures["fixtures"]:
            if record["kind"] != "negative":
                continue
            assert file_hash(baseline_source) == record["baseline_generator_sha256"]
            recipe = record["baseline_recipe"]
            pixels = old.generate(recipe["seed"], recipe["sample_index"],
                                  difficulty=recipe["difficulty"], **recipe["overrides"])
            assert pixels == record["input"], record["name"]
            checks.append({"name": record["name"], "pixels_equal": True,
                           "baseline_self_check": old.self_check(pixels)})
        baseline = {"source_sha256": file_hash(baseline_source), "negative_fixtures": checks,
                    "scope": "Original texture requests generated these exact pixels; current production requests must reject them."}
    canonical = canonical_pairs(TASK, root=root)
    cases += [{"kind": "canonical", "name": f"canonical-{index}", "input": pair["input"],
               "canonical_output_sha256": digest(pair["output"])}
              for index, pair in enumerate(canonical)]
    for band in ("easy", "medium", "hard"):
        for seed in range(8):
            index = seed % 4
            grid = generator.generate(seed, index, difficulty=band)
            cases.append({"kind": "default", "name": f"{band}-s{seed}-i{index}", "input": grid,
                          "recipe": {"seed": seed, "sample_index": index,
                                     "difficulty": band, "overrides": {}},
                          "schedule_profile": generator.schedule_profile(seed, index, band)})
    assert len(cases) == 36
    for index, record in enumerate(cases):
        record["case_index"] = index
        record["input_sha256"] = digest(record["input"])
        record["self_check_errors"] = generator.self_check(record["input"])
        record["observed_axes"] = generator.observe_overrides(record["input"])
        assert bool(record["self_check_errors"]) == (record["kind"] == "negative"), record
    negative_requests = []
    for record in fixtures["fixtures"]:
        if record["kind"] != "negative":
            continue
        try:
            generator.generate(0, 0, difficulty="medium", texture=record["name"])
        except ValueError as error:
            negative_requests.append({"texture": record["name"], "rejected": True, "error": str(error)})
        else:
            raise AssertionError(f"Negative texture admitted: {record['name']}")
    metadata = {
        "schema": "border-semantics-population-v1", "task_id": TASK,
        "generator_sha256": source_sha, "generator_version": generator.VERSION,
        "generator_source": str(source.relative_to(root)), "declared_rule_hash": generator.RULE_HASH,
        "canonical_shortcuts": sorted(generator.CANONICAL_SHORTCUTS),
        "lesson_competitors": sorted(generator.LESSON_COMPETITORS),
        "case_count": len(cases), "canonical_count": len(canonical),
        "default_policy": {"seeds": [0, 7], "sample_index": "seed % 4",
                           "bands": ["easy", "medium", "hard"], "draw_count": 24,
                           "overrides": {}, "selection": "direct generation; no filtering or rejection"},
        "baseline_negative_preservation": baseline, "negative_texture_requests": negative_requests,
        "cases": [{k: v for k, v in record.items() if k != "input"} for record in cases],
    }
    write(output / "input.json", [record["input"] for record in cases])
    write(output / "population.json", metadata)
    print(json.dumps({"prepared_cases": len(cases), "positives": 5, "negatives": 3,
                      "canonical": len(canonical), "defaults": 24, "source_sha256": source_sha}))


def differing_cells(expected, actual):
    assert len(expected) == len(actual) and all(len(a) == len(b) for a, b in zip(expected, actual))
    return [{"row": r, "column": c, "racket": value, "rival": actual[r][c]}
            for r, row in enumerate(expected) for c, value in enumerate(row) if value != actual[r][c]]


def validate_receipt(grids, metadata, racket, expected_source_sha, expected_rule_hash):
    """Validate a public apply receipt before using any of its labels."""
    assert expected_source_sha == metadata["generator_sha256"] == racket["generator_sha256"]
    assert expected_rule_hash == racket["executed_rule_hash"]
    assert racket["rule_hash_matches_catalog"]
    assert "--check-generator-domain" in racket["command"]
    results = racket["results"]
    assert len(results) == len(grids) == len(metadata["cases"])
    assert all(row["valid_output"] and not row["error"] for row in results)
    for index, (grid, record, result) in enumerate(zip(grids, metadata["cases"], results)):
        assert record["case_index"] == index, f"Population order differs at case {index}"
        assert result["index"] == index, f"Receipt order differs at case {index}"
        input_hash = digest(grid)
        assert record["input_sha256"] == input_hash, f"Population input hash differs at case {index}"
        assert result["input"] == grid, f"Receipt input payload differs at case {index}"
        assert result["input_sha256"] == input_hash, f"Receipt input hash differs at case {index}"
        assert result["input_sha256"] == digest(result["input"]), f"Receipt input payload hash differs at case {index}"
        assert result["output_sha256"] == digest(result["output"]), f"Receipt output payload hash differs at case {index}"


def analyze(output):
    root, generator, source, source_sha = setup()
    metadata = json.loads((output / "population.json").read_text())
    grids = json.loads((output / "input.json").read_text())
    racket = json.loads((output / "racket.json").read_text())
    validate_receipt(grids, metadata, racket, source_sha, generator.RULE_HASH)
    results = racket["results"]
    assert len(results) == len(grids) == 36
    outputs = [row["output"] for row in results]
    records = metadata["cases"]
    for record, result in zip(records, results):
        expected_status = "invalid" if record["kind"] == "negative" else "valid"
        assert result["generator_domain"]["status"] == expected_status
        assert result["generator_domain"]["errors"] == record["self_check_errors"]
    groups = {kind: [i for i, row in enumerate(records) if row["kind"] == kind]
              for kind in ("positive", "negative", "canonical", "default")}
    canonical = canonical_pairs(TASK, root=root)
    assert outputs[8:12] == [pair["output"] for pair in canonical]
    contract_path = HOME / "tests/test_generator_contract.py"
    contract = import_source(contract_path, "border_probe_contract_tests")
    assert contract.SOURCE_SHA256 == source_sha
    mirror_matches = [contract.expected_output(grid) == expected for grid, expected in zip(grids, outputs)]
    predictions = {}
    before = digest(grids)
    for name, rival in generator.LESSON_COMPETITORS.items():
        predictions[name] = [rival(grid) for grid in grids]
    for name, rival in generator.CANONICAL_SHORTCUTS.items():
        if name not in predictions:
            predictions[name] = [rival(grid) for grid in grids]
    assert digest(grids) == before, "A rival mutated an input"
    rival_counts = {}
    for name, guesses in predictions.items():
        rival_counts[name] = {kind: {"matched": sum(guesses[i] == outputs[i] for i in indices),
                                    "total": len(indices),
                                    "refuting_case_indices": [i for i in indices if guesses[i] != outputs[i]]}
                              for kind, indices in groups.items()}
    failures = []
    for name in generator.CANONICAL_SHORTCUTS:
        if rival_counts[name]["canonical"]["matched"] != len(canonical):
            failures.append({"kind": "canonical_shortcut_does_not_fit", "rival": name})
        if not rival_counts[name]["positive"]["refuting_case_indices"]:
            failures.append({"kind": "positive_fixture_does_not_refute", "rival": name})
    if not all(mirror_matches):
        failures.append({"kind": "python_test_oracle_differs_from_racket",
                         "case_indices": [i for i, matches in enumerate(mirror_matches) if not matches]})
    frequencies = {}
    for name, predicate in generator.SEMANTIC_WITNESSES.items():
        indices = [i for i in groups["default"] if predicate(grids[i])]
        linked = generator.WITNESS_RIVALS.get(name, [])
        frequencies[name] = {"predicate_hits": len(indices), "default_draws": len(groups["default"]),
                             "case_indices": indices,
                             "racket_refuting_counts": {rival: sum(predictions[rival][i] != outputs[i] for i in indices)
                                                         for rival in linked},
                             "first_recipe": records[indices[0]]["recipe"] if indices else None,
                             "first_case_index": indices[0] if indices else None}
        if not indices:
            failures.append({"kind": "declared_witness_absent_in_bounded_defaults", "witness": name})
    binding = {"generator_sha256": source_sha, "executed_rule_hash": racket["executed_rule_hash"],
               "rule_text_sha256": racket["rule_text_sha256"],
               "probe_sha256": file_hash(__file__),
               "racket_response_sha256": file_hash(output / "racket.json")}
    fixtures = json.loads(FIXTURES.read_text())
    fixtures.update({"label_status": "public_racket_verified", **binding,
                     "racket_command": racket["command"], "racket_cwd": racket["cwd"]})
    for index, fixture in enumerate(fixtures["fixtures"]):
        assert fixture["input"] == grids[index]
        fixture.update({"racket_output": outputs[index], "authority_case_index": index,
                        "input_sha256": results[index]["input_sha256"],
                        "output_sha256": results[index]["output_sha256"],
                        "self_check_errors": records[index]["self_check_errors"],
                        "refuted_canonical_shortcuts": [name for name in generator.CANONICAL_SHORTCUTS
                                                       if predictions[name][index] != outputs[index]]})
    write(FIXTURES, fixtures)
    repeated = next(i for i in groups["positive"] if records[i]["name"] == "repeated_color")
    strong = "border_colors"
    generated_witnesses = rival_counts[strong]["default"]["refuting_case_indices"]
    first = generated_witnesses[0] if generated_witnesses else None
    question = {
        "schema": "border-color-question-counterexample-v1", "task_id": TASK, **binding,
        "purpose": "Contrastive reviewer witness; not a blind solve record or training-label artifact",
        "question": "Does a disconnected interior component survive when its color also occurs on the border?",
        "rival_name": strong, "rival_description": "Erase every pixel whose color occurs in a border-touching object",
        "canonical_fit": rival_counts[strong]["canonical"],
        "input": grids[repeated], "actual_racket_output": outputs[repeated],
        "rival_output": predictions[strong][repeated],
        "differing_cells": differing_cells(outputs[repeated], predictions[strong][repeated]),
        "self_check_errors": records[repeated]["self_check_errors"],
        "in_documented_generator_domain": True, "origin": "explicit minimal 6x7 fixture",
        "generated_refuting_draws": len(generated_witnesses), "generated_draws": 24,
        "generated_first_witness": None if first is None else {
            "case_index": first, "recipe": records[first]["recipe"], "input": grids[first],
            "actual_racket_output": outputs[first], "rival_output": predictions[strong][first]},
        "racket_command": racket["command"], "racket_cwd": racket["cwd"],
        "exact_commands": "checks/final/border-probe/commands.json",
    }
    write(HOME / "counterexamples/border-colors-question.json", question)
    report = {
        "schema": "border-semantics-analysis-v1", "task_id": TASK, **binding,
        "status": "PASS" if not failures else "FAIL", "failures": failures,
        "authority": "public arcpuzzles apply --check-generator-domain; all outputs are from Racket",
        "receipt_validation": {"cases_checked": len(results), "input_order": "matched",
                               "input_payloads": "matched", "input_and_population_hashes": "matched",
                               "output_payload_hashes": "matched"},
        "case_count": len(grids), "unique_inputs": len({digest(grid) for grid in grids}),
        "counts_by_kind": {kind: {"draws": len(indices), "unique_inputs": len({digest(grids[i]) for i in indices}),
                                 "self_check_accepted": sum(not records[i]["self_check_errors"] for i in indices),
                                 "self_check_rejected": sum(bool(records[i]["self_check_errors"]) for i in indices)}
                           for kind, indices in groups.items()},
        "public_domain_evidence": [{"case_index": i, **{k: v for k, v in row.items()
                                    if k not in ("input", "output", "input_sha256", "output_sha256")}}
                                   for i, row in enumerate(results)],
        "canonical_shortcut_count": len(generator.CANONICAL_SHORTCUTS),
        "canonical_shortcuts_fitting_every_pair": sum(rival_counts[name]["canonical"]["matched"] == len(canonical)
                                                     for name in generator.CANONICAL_SHORTCUTS),
        "lesson_competitor_count": len(generator.LESSON_COMPETITORS),
        "rival_fit_counts": rival_counts,
        "generated_witness_frequencies": frequencies,
        "python_test_oracle": {"path": str(contract_path.relative_to(root)), "source_sha256": file_hash(contract_path),
                               "function": "expected_output", "matched": sum(mirror_matches), "total": len(grids),
                               "scope": "Python mirror independently cross-checked against retained authoritative Racket labels"},
        "baseline_negative_preservation": metadata["baseline_negative_preservation"],
        "negative_texture_requests": metadata["negative_texture_requests"],
        "source_unchanged": source_sha == file_hash(source),
        "scope": "Per-grid semantic witnesses only; these 24 direct draws are not a lesson identifiability census.",
        "racket_command": racket["command"], "racket_cwd": racket["cwd"],
        "exact_commands": "checks/final/border-probe/commands.json",
    }
    assert report["source_unchanged"]
    write(output / "analysis.json", report)
    print(json.dumps({"status": report["status"], "racket_cases": len(grids), "unique_inputs": report["unique_inputs"],
                      "canonical_shortcuts": report["canonical_shortcuts_fitting_every_pair"],
                      "canonical_pairs": len(canonical), "python_mirror_matches": sum(mirror_matches),
                      "border_colors_generated_refutations": len(generated_witnesses),
                      "generated_first_recipe": records[first]["recipe"] if first is not None else None,
                      "witness_frequencies": {name: row["predicate_hits"] for name, row in frequencies.items()}}))
    return int(bool(failures))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("prepare", "analyze"))
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--baseline-source", type=Path)
    args = parser.parse_args()
    if args.mode == "prepare":
        prepare(args.out, args.baseline_source)
    else:
        raise SystemExit(analyze(args.out))
