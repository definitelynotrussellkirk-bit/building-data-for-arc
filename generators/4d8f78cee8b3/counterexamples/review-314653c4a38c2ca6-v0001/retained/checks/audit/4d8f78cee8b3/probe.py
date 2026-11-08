"""Source-bound, bounded audit; public Racket apply supplies all fresh labels."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import itertools
import json
from pathlib import Path

from reviewer_support import canonical_pairs, find_root, load_selected_generator


TASK_ID = "4d8f78cee8b3"
EXPECTED_SOURCE = "b4effd60c55c9e79aeb4f3726da33265c13d6eead9efb4b252a13f9dea9ceb95"
HERE = Path(__file__).resolve().parent


def endpoint_repeat_rival(grid):
    """Only inspect the first/last nonzero colors for repetition in each row."""
    result = []
    for row in grid:
        nonzero = [value for value in row if value]
        counts = Counter(nonzero)
        endpoints = {nonzero[0], nonzero[-1]} if nonzero else set()
        erased = {color for color in endpoints if counts[color] > 1}
        result.append([0 if value in erased else value for value in row])
    return result


def singleton_mirror(grid):
    result = []
    for row in grid:
        counts = Counter(value for value in row if value)
        result.append([value if value and counts[value] == 1 else 0 for value in row])
    return result


def write_json(name, data):
    (HERE / name).write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def prepare():
    root = find_root(__file__)
    module, source_path, source_sha = load_selected_generator(TASK_ID, root=root)
    assert source_sha == EXPECTED_SOURCE, (source_path, source_sha)
    canon = canonical_pairs(TASK_ID, root=root, labeled_only=True)
    cases = []
    for pair in canon:
        cases.append({
            "kind": "canonical",
            "identity": {key: pair[key] for key in ("variant", "split", "pair_index")},
            "input": pair["input"],
            "canonical_output": pair["output"],
        })
    # All declared axis values, once each combination. This is a finite probe,
    # not a census over seeds, lesson windows, or generator random support.
    axes = (module.GRID_PROFILES, module.PALETTE_KINDS, module.SCENE_PROFILES)
    for index, (grid_profile, palette_kind, scene_profile) in enumerate(itertools.product(*axes)):
        call = {
            "seed": 23,
            "sample_index": index,
            "difficulty": ("easy", "medium", "hard")[index % 3],
            "grid_profile": grid_profile,
            "palette_kind": palette_kind,
            "scene_profile": scene_profile,
        }
        cases.append({"kind": "generated", "generate_call": call, "input": module.generate(**call)})
    # Three active rows, seven colors, a pair and two singleton colors in the
    # first row. Moving repeats inside the row violates no stated invariant.
    witness = [
        [1, 2, 0, 2, 0, 3, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [4, 0, 5, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 6, 0, 0, 0, 7, 0, 0, 0, 0],
    ]
    cases.append({
        "kind": "counterexample",
        "construction": "Hand-built lawful counterfactual; pair color 2 is not a first/last nonzero color.",
        "generate_call": None,
        "in_documented_domain": True,
        "in_current_generator_support": False,
        "input": witness,
    })
    for index, case in enumerate(cases):
        case["batch_index"] = index
        case["self_check"] = module.self_check(case["input"])
        case["strict_canonical_like"] = module.strict_canonical_like(case["input"])
        case["mirror_output"] = singleton_mirror(case["input"])
        case["rival_output"] = endpoint_repeat_rival(case["input"])
    # Read actual declarations rather than guessing the named rival inventory.
    declarations = {}
    for attr in ("CANONICAL_SHORTCUTS", "LESSON_COMPETITORS"):
        declarations[attr] = []
        for name, rival in getattr(module, attr).items():
            mismatches = [
                {key: pair[key] for key in ("variant", "split", "pair_index")}
                for pair in canon if rival(pair["input"]) != pair["output"]
            ]
            declarations[attr].append({
                "name": name,
                "canonical_pairs": len(canon),
                "canonical_agreements": len(canon) - len(mismatches),
                "canonical_mismatches": mismatches,
            })
    assert len(cases) <= 64
    data = {
        "task_id": TASK_ID,
        "generator_sha256": source_sha,
        "generator_path": str(source_path.relative_to(root)),
        "seed_range": [23, 23],
        "sample_index_range": [0, 26],
        "canonical_count": len(canon),
        "generated_count": 27,
        "counterexample_count": 1,
        "declared_rivals": declarations,
        "cases": cases,
    }
    write_json("preparation.json", data)
    write_json("input.json", [case["input"] for case in cases])
    print(json.dumps({
        "generator_sha256": source_sha,
        "canonical_count": len(canon),
        "total_inputs": len(cases),
        "canonical_rival_agreements": sum(case["canonical_output"] == case["rival_output"] for case in cases if case["kind"] == "canonical"),
        "generated_mirror_rival_agreements": sum(case["mirror_output"] == case["rival_output"] for case in cases if case["kind"] == "generated"),
        "validator_rejections": sum(bool(case["self_check"]) for case in cases),
        "counterexample_separates_mirror": cases[-1]["mirror_output"] != cases[-1]["rival_output"],
        "declared_rivals": declarations,
    }, indent=2))


def permutation():
    module, _, source_sha = load_selected_generator(TASK_ID, root=find_root(__file__))
    assert source_sha == EXPECTED_SOURCE
    preparation = json.loads((HERE / "preparation.json").read_text())
    source_case = next(case for case in preparation["cases"]
                       if case["kind"] == "generated"
                       and case["generate_call"]["grid_profile"] == "canonical_5x10"
                       and case["generate_call"]["palette_kind"] == "low"
                       and case["generate_call"]["scene_profile"] == "dense")
    grid = [row[:] for row in source_case["input"]]
    row_index = next(index for index, row in enumerate(grid)
                     if sorted(Counter(value for value in row if value).values()) == [1, 1, 2])
    row = grid[row_index]
    columns = [index for index, value in enumerate(row) if value]
    counts = Counter(value for value in row if value)
    repeated = next(color for color, count in counts.items() if count == 2)
    singles = [color for color, count in counts.items() if count == 1]
    old_tokens = [row[column] for column in columns]
    new_tokens = [singles[0], repeated, repeated, singles[1]]
    for column, value in zip(columns, new_tokens):
        row[column] = value
    data = {
        "task_id": TASK_ID,
        "generator_sha256": source_sha,
        "generate_call": source_case["generate_call"],
        "source_batch_index": source_case["batch_index"],
        "source_input": source_case["input"],
        "mutation": {"row_index": row_index, "columns": columns,
                     "original_tokens": old_tokens, "new_tokens": new_tokens},
        "input": grid,
        "self_check": module.self_check(grid),
        "strict_canonical_like": module.strict_canonical_like(grid),
        "original_observed_axes": module.observe_overrides(source_case["input"]),
        "mutated_observed_axes": module.observe_overrides(grid),
        "in_documented_domain": True,
        "in_current_generator_support": False,
        "domain_explanation": "Only permutes colors within the same occupied row positions; dimensions, palette, multiplicities, active rows and every observable axis are unchanged.",
        "mirror_output": singleton_mirror(grid),
        "rival_output": endpoint_repeat_rival(grid),
    }
    assert not data["self_check"] and not data["strict_canonical_like"]
    assert data["original_observed_axes"] == data["mutated_observed_axes"]
    assert data["mirror_output"] != data["rival_output"]
    write_json("permutation.json", data)
    write_json("permutation-input.json", grid)
    print(json.dumps({key: data[key] for key in ("generate_call", "mutation", "self_check", "strict_canonical_like", "mutated_observed_axes")}, indent=2))


def summarize():
    _, _, source_sha = load_selected_generator(TASK_ID, root=find_root(__file__))
    assert source_sha == EXPECTED_SOURCE
    preparation = json.loads((HERE / "preparation.json").read_text())
    reference = json.loads((HERE / "racket.json").read_text())
    perm = json.loads((HERE / "permutation.json").read_text())
    perm_ref = json.loads((HERE / "permutation-racket.json").read_text())
    for receipt in (reference, perm_ref):
        assert receipt["generator_sha256"] == source_sha
        assert receipt["rule_hash_matches_catalog"]
        assert receipt["executed_rule_hash"] == "533915230c7f"
        assert all(result["valid_output"] and result["error"] is None for result in receipt["results"])
    assert reference["rule_text_sha256"] == perm_ref["rule_text_sha256"]
    checks = []
    assert len(preparation["cases"]) == len(reference["results"]) == 32
    for case, result in zip(preparation["cases"], reference["results"]):
        assert case["batch_index"] == result["index"]
        assert case["input"] == result["input"]
        assert case["mirror_output"] == result["output"]
        if case["kind"] == "canonical":
            assert case["canonical_output"] == result["output"]
        checks.append({"index": result["index"], "kind": case["kind"],
                       "input_sha256": result["input_sha256"],
                       "rival_agrees_with_racket": case["rival_output"] == result["output"],
                       "validator_accepted": not case["self_check"]})
    perm_result = perm_ref["results"][0]
    assert len(perm_ref["results"]) == 1 and perm_result["input"] == perm["input"]
    assert perm["mirror_output"] == perm_result["output"]
    assert perm["rival_output"] != perm_result["output"]
    witnesses = [case for case in preparation["cases"] if case["kind"] == "counterexample"]
    assert all(case["rival_output"] != reference["results"][case["batch_index"]]["output"] for case in witnesses)
    assert all(check["rival_agrees_with_racket"] for check in checks if check["kind"] in {"canonical", "generated"})
    mismatch_cells = [[r, c] for r, row in enumerate(perm_result["output"])
                      for c, value in enumerate(row) if value != perm["rival_output"][r][c]]
    witness = {
        **perm,
        "rule_hash": perm_ref["executed_rule_hash"],
        "rule_text_sha256": perm_ref["rule_text_sha256"],
        "actual_racket_output": perm_result["output"],
        "input_sha256": perm_result["input_sha256"],
        "output_sha256": perm_result["output_sha256"],
        "mismatch_cells": mismatch_cells,
        "racket_command": perm_ref["command"],
        "racket_cwd": perm_ref["cwd"],
        "racket_evidence_path": "checks/audit/4d8f78cee8b3/permutation-racket.json",
    }
    write_json("witness.json", witness)
    all_inputs = [case["input"] for case in preparation["cases"]] + [perm["input"]]
    summary = {
        "task_id": TASK_ID,
        "generator_sha256": source_sha,
        "rule_hash": reference["executed_rule_hash"],
        "rule_text_sha256": reference["rule_text_sha256"],
        "status": "confirmed_shortcut_and_canonical_shortcut_declaration_mismatch",
        "scope": "Four labeled canonical pairs; 27 axis combinations at seed 23/sample_index 0..26; two lawful counterfactuals. Not a full battery or an all-seed empirical census.",
        "racket_inputs": len(all_inputs),
        "unique_racket_inputs": len({json.dumps(grid, separators=(",", ":")) for grid in all_inputs}),
        "racket_valid_outputs": 33,
        "canonical_racket_label_matches": 4,
        "generated_rival_agreements": 27,
        "canonical_rival_agreements": 4,
        "lawful_counterexamples": 2,
        "mutated_observed_axes": perm["mutated_observed_axes"],
        "primary_witness_mismatch_cells": mismatch_cells,
        "declared_rivals": preparation["declared_rivals"],
        "case_checks": checks,
        "evidence_sha256": {name: hashlib.sha256((HERE / name).read_bytes()).hexdigest()
                            for name in ("probe.py", "preparation.json", "input.json", "racket.json", "permutation.json", "permutation-input.json", "permutation-racket.json", "witness.json")},
    }
    write_json("summary.json", summary)
    print(json.dumps({key: summary[key] for key in ("status", "generator_sha256", "rule_hash", "racket_inputs", "unique_racket_inputs", "canonical_rival_agreements", "generated_rival_agreements", "lawful_counterexamples", "primary_witness_mismatch_cells")}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=["prepare", "permutation", "summarize"])
    args = parser.parse_args()
    {"prepare": prepare, "permutation": permutation, "summarize": summarize}[args.phase]()
