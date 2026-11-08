"""Findings-only audit; canonical labels are obtained separately by public apply.

Run from the packet root, in order:
  python3 review.py run python3 ../checks/audit/8e9c04b8fdfb/probe.py prepare
  python3 review.py run python3 -m arcpuzzles apply 8e9c04b8fdfb --input ../checks/audit/8e9c04b8fdfb/input.json --out ../checks/audit/8e9c04b8fdfb/racket.json
  python3 review.py run python3 ../checks/audit/8e9c04b8fdfb/probe.py compare

The prerequisite canonical_task.json is the public `arcpuzzles show` response.
The probe does not import a private runner or alter any audited source.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys

TASK_ID = "8e9c04b8fdfb"
HERE = Path(__file__).resolve().parent


def read(name):
    return json.loads((HERE / name).read_text())


def write(name, value):
    (HERE / name).write_text(json.dumps(value, indent=2) + "\n")


def find_repo():
    for base in (Path.cwd(), *HERE.parents):
        for candidate in (base, base / "repo"):
            if (candidate / "generators" / TASK_ID / "generator.py").is_file():
                return candidate.resolve()
    raise RuntimeError("Could not locate this packet's repo")


def segments(size, dividers):
    previous = -1
    result = []
    for divider in [*dividers, size]:
        if divider - previous > 1:
            result.append(range(previous + 1, divider))
        previous = divider
    return result


def tiles(grid):
    height, width = len(grid), len(grid[0])
    row_dividers = [r for r in range(height) if all(v == 9 for v in grid[r])]
    col_dividers = [c for c in range(width) if all(grid[r][c] == 9 for r in range(height))]
    row_ranges = segments(height, row_dividers)
    col_ranges = segments(width, col_dividers)
    assert len(row_ranges) == len(col_ranges) == 2
    parts = [[[grid[r][c] for c in cs] for r in rs]
             for rs in row_ranges for cs in col_ranges]
    assert len({(len(t), len(t[0])) for t in parts}) == 1
    return parts


def all_four_xor(grid):
    """Natural rival: parity of occupancy in every tile, including the fourth."""
    parts = tiles(grid)
    return [[8 if sum(t[r][c] != 0 for t in parts) % 2 else 0
             for c in range(len(parts[0][0]))]
            for r in range(len(parts[0]))]


def prepare():
    root = find_repo()
    source_path = root / "generators" / TASK_ID / "generator.py"
    source_hash = hashlib.sha256(source_path.read_bytes()).hexdigest()
    task = read("canonical_task.json")
    assert source_hash == task["generator_sha256"], "Source differs from the inspected authoring record"
    sys.path.insert(0, str(root / "shared" / "runtime"))
    spec = importlib.util.spec_from_file_location("audit_target", source_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    canonical = task["variants"][0]
    source_pairs = [("train", i, pair) for i, pair in enumerate(canonical["train"])]
    test = canonical["test"]
    source_pairs.extend(("test", i, pair) for i, pair in enumerate(test if isinstance(test, list) else [test]))
    cases = []
    for split, index, pair in source_pairs:
        cases.append({
            "name": f"canonical_{split}_{index}",
            "origin": "public canonical task, variant 0",
            "canonical_split": split, "canonical_pair_index": index,
            "seed": None, "sample_index": None, "difficulty": None, "overrides": None,
            "input": pair["input"], "canonical_stored_output": pair["output"],
            "documented_generator_domain": False,
            "domain_reason": "The summary and invariant require a blank bottom-right tile; this canonical input has the center-3 missing-tile marker.",
        })
    for index, difficulty in enumerate((None, "easy", "hard")):
        cases.append({
            "name": f"generated_{difficulty or 'default'}_{index}",
            "origin": "unmodified generator.generate",
            "seed": 20261007, "sample_index": index, "difficulty": difficulty, "overrides": {},
            "input": mod.generate(20261007, index, difficulty=difficulty),
            "documented_generator_domain": True,
            "domain_reason": "Direct unmodified ordinary generate call.",
        })
    marker_removed = [row[:] for row in cases[0]["input"]]
    marker_removed[5][5] = 0
    cases.append({
        "name": "canonical_train_0_marker_removed",
        "origin": "canonical_train_0 with only input[5][5] changed from 3 to 0",
        "seed": None, "sample_index": None, "difficulty": None, "overrides": None,
        "input": marker_removed,
        "documented_generator_domain": True,
        "domain_reason": "3x3 visible masks, color-9 2x2 lattice, blank bottom-right. Still outside actual sampled palette support because all three masks share color 2.",
    })
    for case in cases:
        case["self_check_errors"] = mod.self_check(case["input"], difficulty=case["difficulty"])
        parts = tiles(case["input"])
        case["bottom_right_nonzero_count"] = sum(v != 0 for row in parts[3] for v in row)
        case["rival_name"] = "all_four_tile_occupancy_xor"
        case["rival_output"] = all_four_xor(case["input"])
    write("input.json", [case["input"] for case in cases])
    write("prepared.json", {
        "task_id": TASK_ID,
        "generator_path": str(source_path.relative_to(root)),
        "generator_sha256": source_hash,
        "rule_hash": task["rule_hash"],
        "rule_source_sha256": hashlib.sha256(canonical["program_solution"].encode()).hexdigest(),
        "review_index_present": (source_path.parent / "evidence" / "review_index.json").exists(),
        "payload_argv": sys.argv, "payload_cwd": str(Path.cwd()),
        "cases": cases,
    })
    print(json.dumps({"task_id": TASK_ID, "prepared_cases": len(cases), "generator_sha256": source_hash, "rule_hash": task["rule_hash"]}))


def compare():
    prepared = read("prepared.json")
    receipt = read("racket.json")
    # The public response schema is checked before interpreting any result.
    print(json.dumps({"receipt_keys": list(receipt)}))
    assert receipt["schema"] == "arcpuzzles-apply-v1"
    assert receipt["generator_sha256"] == prepared["generator_sha256"]
    assert receipt["executed_rule_hash"] == prepared["rule_hash"]
    assert receipt["rule_hash_matches_catalog"]
    # The authoring view hashes the (rule! ...) source; apply also hashes its
    # executable callable form. These are separate identities, not equal text.
    assert prepared["rule_source_sha256"].startswith(receipt["executed_rule_hash"])
    prepared["executed_rule_callable_sha256"] = receipt["rule_text_sha256"]
    rows = receipt["results"]
    assert len(rows) == len(prepared["cases"])
    for case, result in zip(prepared["cases"], rows):
        assert result["input"] == case["input"]
        assert result["valid_output"] and result["error"] is None
        actual = result["output"]
        case["actual_racket_output"] = actual
        case["rival_agrees"] = actual == case["rival_output"]
        case["difference_coordinates"] = [[r, c] for r in range(len(actual)) for c in range(len(actual[0]))
                                          if actual[r][c] != case["rival_output"][r][c]]
        if "canonical_stored_output" in case:
            case["racket_matches_canonical_stored_output"] = actual == case["canonical_stored_output"]
    prepared["finding_category"] = "reproduced"
    prepared["finding_id"] = "A8E9C-1"
    prepared["finding"] = "Missing canonical missing-tile-marker support leaves all-four-tile XOR indistinguishable from the canonical three-tile XOR on ordinary generated inputs."
    prepared["scope"] = "Three canonical pairs; three generated inputs at seed 20261007, sample indices 0/default, 1/easy, 2/hard; one marker-removal counterfactual. Not a full battery or a population census."
    prepared["racket_receipt"] = "racket.json"
    prepared["compare_payload_argv"] = sys.argv
    prepared["compare_payload_cwd"] = str(Path.cwd())
    write("evidence.json", prepared)
    summary = [{"name": case["name"], "self_check_errors": case["self_check_errors"],
                "rival_agrees": case["rival_agrees"], "difference_coordinates": case["difference_coordinates"]}
               for case in prepared["cases"]]
    print(json.dumps(summary, indent=2))
    assert all(not case["self_check_errors"] for case in prepared["cases"])
    assert all(case["racket_matches_canonical_stored_output"] for case in prepared["cases"] if case["name"].startswith("canonical_") and "canonical_stored_output" in case)
    assert [case["rival_agrees"] for case in prepared["cases"]] == [False, False, False, True, True, True, True]


if __name__ == "__main__":
    {"prepare": prepare, "compare": compare}[sys.argv[1]]()
