#!/usr/bin/env python3
"""Reproduce the c7e852398e08 canonical-domain rejection without editing it.

Preparation imports only the assigned generator and reads its canonical row.
With --racket, the script compares an already retained public apply result.
It does not execute a private reference runner or infer Racket outputs.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

TASK_ID = "c7e852398e08"


def dump(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--racket", type=Path)
    args = parser.parse_args()
    repo, out = args.repo.resolve(), args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(repo / "shared/runtime"))
    sys.path.insert(0, str(repo / "src"))
    from arcpuzzles import Catalog

    source = repo / f"generators/{TASK_ID}/generator.py"
    source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    spec = importlib.util.spec_from_file_location("audited_c7e852398e08", source)
    generator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(generator)
    catalog_row = Catalog(repo).get(TASK_ID)
    assert source_hash == catalog_row["generator_sha256"]
    variants = catalog_row["variants"]
    assert len(variants) == 1
    variant = variants[0]
    pairs = [(f"train[{i}]", pair) for i, pair in enumerate(variant["train"])]
    test = variant["test"]
    if isinstance(test, dict):
        pairs.append(("test[0]", test))
    else:
        pairs.extend((f"test[{i}]", pair) for i, pair in enumerate(test))

    records = []
    for label, pair in pairs:
        grid = [[int(value) for value in row] for row in pair["input"]]
        expected = [[int(value) for value in row] for row in pair["output"]]
        cells = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value]
        top, left = min(r for r, c in cells), min(c for r, c in cells)
        bottom, right = max(r for r, c in cells), max(c for r, c in cells)
        issues = generator.self_check(grid)
        records.append({
            "canonical_pair": label,
            "origin": "unchanged canonical input, not a generated sample",
            "seed": None,
            "sample_index": None,
            "overrides": None,
            "input": grid,
            "expected_output": expected,
            "input_shape": [len(grid), len(grid[0])],
            "output_shape": [len(expected), len(expected[0])],
            "nonzero_colors": sorted({value for row in grid for value in row if value}),
            "output_colors": sorted({value for row in expected for value in row}),
            "zero_padding_on_every_side": top > 0 and left > 0 and bottom < len(grid)-1 and right < len(grid[0])-1,
            "bbox_smaller_than_input": bottom-top+1 < len(grid) and right-left+1 < len(grid[0]),
            "self_check_accepted": not issues,
            "self_check_messages": issues,
            "documented_domain": "canonical example; satisfies both declared INVARIANTS; rejected by the added two-nonzero-color restriction",
        })

    report = {
        "task_id": TASK_ID,
        "version": generator.VERSION,
        "generator_sha256": source_hash,
        "rule_hash": catalog_row["rule_hash"],
        "program_solution": variant["program_solution"],
        "canonical_source": "shared/data/canonical/puzzles.jsonl",
        "canonical_row": variant,
        "finite_scope": "All five canonical pairs from the one selected canonical row; no random sampling or whole-generator battery.",
        "pair_count": len(records),
        "self_check_rejected_count": sum(not record["self_check_accepted"] for record in records),
        "records": records,
    }
    assert len(records) == 5
    assert all(record["zero_padding_on_every_side"] and record["bbox_smaller_than_input"] for record in records)
    assert all(record["self_check_messages"] == ["cropped motif has fewer than 2 visible nonzero colors"] for record in records)
    assert all(len(record["output_colors"]) == 2 for record in records)

    if args.racket is None:
        dump(out / "input.json", {"inputs": [record["input"] for record in records]})
        dump(out / "self_check.json", report)
        print(json.dumps({"task_id": TASK_ID, "generator_sha256": source_hash,
                          "rule_hash": catalog_row["rule_hash"], "canonical_pairs": len(records),
                          "self_check_rejected": report["self_check_rejected_count"]}))
        return

    racket = json.loads(args.racket.read_text())
    assert racket["task_id"] == TASK_ID
    assert racket["generator_sha256"] == source_hash
    assert racket["executed_rule_hash"] == report["rule_hash"]
    assert racket["rule_hash_matches_catalog"]
    assert len(racket["results"]) == len(records)
    for record, actual in zip(records, racket["results"]):
        assert actual["input"] == record["input"]
        assert actual["valid_output"] and actual["error"] is None
        assert actual["output"] == record["expected_output"]
    commands = json.loads((out / "commands.json").read_text())
    apply_command = next(command for command in commands if command["label"] == "racket")
    assert apply_command["exit_code"] == 0
    witness = records[0]
    finding = {
        "finding_id": "C7-A1",
        "classification": "reproduced canonical-domain exclusion / overstrict validator",
        "task_id": TASK_ID,
        "generator_sha256": source_hash,
        "rule_hash": report["rule_hash"],
        "rule_text_sha256": racket["rule_text_sha256"],
        "witness_origin": "canonical train[0], unchanged",
        "seed": None,
        "sample_index": None,
        "overrides": None,
        "input": witness["input"],
        "actual_racket_output": racket["results"][0]["output"],
        "canonical_expected_output": witness["expected_output"],
        "rival_output": None,
        "rival_output_reason": "This finding concerns validator/domain exclusion, not a competing solver prediction.",
        "passes_self_check": False,
        "self_check_messages": witness["self_check_messages"],
        "belongs_to_documented_domain": True,
        "domain_basis": "Unmodified canonical training pair; nonempty interior motif, zero padding on every side, bbox strictly smaller than input. Its crop contains both 0 and 2, so it is not a single-color field. The implementation additionally restricts generated/accepted examples to at least two nonzero colors.",
        "finite_scope": {
            "canonical_rows": 1,
            "canonical_pairs": len(records),
            "unique_canonical_inputs": len({json.dumps(record["input"]) for record in records}),
            "self_check_rejected": report["self_check_rejected_count"],
            "valid_racket_outputs": len(racket["results"]),
            "racket_matches_canonical": len(racket["results"]),
            "random_seed_range": None,
            "sample_index_range": None,
            "generated_samples_checked": 0,
        },
        "source_explanation": "generate draws n_colors_used in 2..3 and injects a second visible color; self_check rejects len(nz_colors) < 2. This is stronger than the separate len(set(crop_vals)) < 2 single-color-output check and excludes every canonical pair.",
        "claim_limit": "No generated/Racket label disagreement, all-seeds claim, or lesson/shortcut identifiability result is claimed.",
        "public_apply_command": apply_command,
        "effective_payload_cwd": racket["cwd"],
        "supporting_files": ["checks/audit/c7e852398e08/self_check.json", "checks/audit/c7e852398e08/racket.json"],
    }
    dump(out / "counterexample.json", finding)
    assert hashlib.sha256(source.read_bytes()).hexdigest() == source_hash
    print(json.dumps({"finding_id": "C7-A1", "canonical_pairs": len(records),
                      "self_check_rejected": report["self_check_rejected_count"],
                      "racket_matches_canonical": len(racket["results"]),
                      "generator_sha256": source_hash, "rule_hash": report["rule_hash"]}))


if __name__ == "__main__":
    main()
