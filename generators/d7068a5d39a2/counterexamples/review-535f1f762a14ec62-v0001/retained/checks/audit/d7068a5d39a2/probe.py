"""Findings-only support audit; no private runner or solve imports.

Run from packet root:
  python3 run_with_racket.py python3 ../checks/audit/d7068a5d39a2/probe.py
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys


HERE = Path(__file__).resolve().parent
PACKET = HERE.parents[2]
REPO = PACKET / "repo"
TASK = "d7068a5d39a2"
GENERATOR = REPO / "generators" / TASK / "generator.py"


def digest(value):
    return hashlib.sha256(value).hexdigest()


def grid_digest(grid):
    return digest(json.dumps(grid, separators=(",", ":")).encode())


def support(grid):
    half = len(grid[0]) // 2
    result = {"left_only": 0, "right_only": 0, "both": 0, "zero": 0}
    for row in grid:
        for c in range(half):
            left, right = row[c] != 0, row[c + half] != 0
            key = "both" if left and right else "left_only" if left else "right_only" if right else "zero"
            result[key] += 1
    return result


def intended_or(grid):
    half = len(grid[0]) // 2
    return [[6 if row[c] or row[c + half] else 0 for c in range(half)] for row in grid]


def overlap_gated_or(grid):
    """Diagnostic rival, NOT claimed to fit all canonical pairs."""
    if support(grid)["both"]:
        return intended_or(grid)
    return [[0] * (len(grid[0]) // 2) for _ in grid]


def main():
    spec = importlib.util.spec_from_file_location("audit_d7068_generator", GENERATOR)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    rows = [json.loads(line) for line in (REPO / "shared/data/canonical/puzzles.jsonl").open()
            if json.loads(line).get("task_id") == TASK]
    assert len(rows) == 1
    row = rows[0]
    canonical = []
    for split in ("train", "test"):
        for index, pair in enumerate(row[split]):
            grid, expected = pair["input"], pair["output"]
            canonical.append({
                "split": split, "pair_index": index,
                "support": support(grid),
                "validator_errors": module.self_check(grid),
                "written_or_matches_saved_output": intended_or(grid) == expected,
                "diagnostic_rival_matches_saved_output": overlap_gated_or(grid) == expected,
                "input_sha256": grid_digest(grid),
            })
    generated = []
    for band in ("easy", "medium", "hard"):
        for sample_index in range(20):
            grid = module.generate(0, sample_index, difficulty=band)
            generated.append({
                "seed": 0, "sample_index": sample_index, "difficulty": band, "overrides": {},
                "shape": [len(grid), len(grid[0])], "support": support(grid),
                "validator_errors": module.self_check(grid, difficulty=band),
                "diagnostic_rival_matches_written_or": overlap_gated_or(grid) == intended_or(grid),
                "input_sha256": grid_digest(grid),
            })
    control_probes = []
    for overrides in (
        {"grid_h": 1},
        {"half_w": 1},
        {"grid_h": 3, "half_w": 3, "or_target": 9},
    ):
        item = {"seed": 0, "sample_index": 0, "difficulty": None, "overrides": overrides}
        try:
            grid = module.generate(0, 0, **overrides)
            item.update(input=grid, validator_errors=module.self_check(grid))
        except Exception as exc:
            item["exception"] = f"{type(exc).__name__}: {exc}"
        control_probes.append(item)

    witness_pair = row["train"][2]
    witness = {
        "task_id": TASK,
        "source": "canonical variant 0, train[2] (zero-based index)",
        "authority_result_index": 0,
        "seed": None, "sample_index": None, "difficulty": None, "overrides": None,
        "input": witness_pair["input"],
        "saved_canonical_output": witness_pair["output"],
        "actual_racket_output": "See racket.json; authoritative command run separately.",
        "rival_name": "overlap_gated_or",
        "rival_definition": "Return OR-to-6 when any paired coordinate is nonzero in both halves; otherwise return all zeros.",
        "rival_output": overlap_gated_or(witness_pair["input"]),
        "rival_status": "Diagnostic blind spot only: fits all sampled ordinary generated grids, but fails this canonical pair. Not a canonical-fitting rival or measured model error.",
        "validator_errors": module.self_check(witness_pair["input"]),
        "domain_status": {
            "rectangular_arc_grid": True,
            "written_rule_domain": True,
            "listed_invariants": True,
            "canonical_member": True,
            "ordinary_generated_support": False,
            "reason": "Contains no overlap; every ordinary generated input reserves one overlap, and self_check rejects no-overlap inputs.",
        },
    }
    subset_pair = row["train"][4]
    subset_witness = {
        "task_id": TASK,
        "source": "canonical variant 0, train[4] (zero-based index)",
        "authority_result_index": 1,
        "seed": None, "sample_index": None, "difficulty": None, "overrides": None,
        "input": subset_pair["input"],
        "saved_canonical_output": subset_pair["output"],
        "actual_racket_output": "See racket.json; authoritative command run separately.",
        "rival_name": "left_only_gated_or",
        "rival_definition": "Return OR-to-6 when any paired coordinate is nonzero only in the left half; otherwise return all zeros.",
        "rival_output": intended_or(subset_pair["input"]) if support(subset_pair["input"])["left_only"] else [[0] * 3 for _ in range(3)],
        "rival_status": "Intentional diagnostic blind spot, not a canonical-fitting rival or measured model error; the generator forces left-only support in ordinary grids.",
        "validator_errors": module.self_check(subset_pair["input"]),
        "domain_status": {
            "rectangular_arc_grid": True,
            "written_rule_domain": True,
            "listed_invariants": True,
            "canonical_member": True,
            "ordinary_generated_support": False,
            "reason": "Left support is contained in right support; every ordinary generated input reserves one left-only coordinate, and self_check rejects inputs without it.",
        },
    }
    report = {
        "task_id": TASK,
        "generator_version": module.VERSION,
        "generator_sha256": digest(GENERATOR.read_bytes()),
        "rule_text_sha256": digest(row["program_solution"].encode()),
        "canonical_row_json_sha256": digest(json.dumps(row, sort_keys=True, separators=(",", ":")).encode()),
        "probe_execution": {"cwd": str(Path.cwd()), "argv": sys.argv},
        "canonical": canonical,
        "ordinary_generated_probe": {
            "sampling": "seed 0; sample_index 0..19 inclusive separately for easy, medium, hard; no overrides",
            "count": len(generated),
            "unique_inputs": len({x["input_sha256"] for x in generated}),
            "validator_pass_count": sum(not x["validator_errors"] for x in generated),
            "overlap_present_count": sum(x["support"]["both"] > 0 for x in generated),
            "diagnostic_rival_fit_count": sum(x["diagnostic_rival_matches_written_or"] for x in generated),
            "authority_status": "This sample probe uses the written OR formula; only the retained canonical witness is executed through the separate supported Racket apply command.",
            "samples": generated,
        },
        "advertised_control_probes": control_probes,
        "witnesses": [witness, subset_witness],
        "limitations": [
            "Findings-only audit; target generator, reference rule, and shared files are unchanged.",
            "No complete battery or production lesson census was run.",
            "The rival is an intentional diagnostic and does not fit all canonical pairs.",
            "Default sample counts do not prove semantic correctness or unique inductive identification.",
        ],
    }
    (HERE / "input.json").write_text(json.dumps([witness["input"], subset_witness["input"]], indent=2) + "\n")
    (HERE / "rival.json").write_text(json.dumps([
        {"rival_name": item["rival_name"], "output": item["rival_output"]}
        for item in (witness, subset_witness)
    ], indent=2) + "\n")
    (HERE / "probe.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({
        "canonical_validator_pass": sum(not x["validator_errors"] for x in canonical),
        "canonical_count": len(canonical),
        "canonical_failures": [x for x in canonical if x["validator_errors"]],
        "ordinary_samples": report["ordinary_generated_probe"]["count"],
        "ordinary_validator_pass": report["ordinary_generated_probe"]["validator_pass_count"],
        "advertised_control_probes": control_probes,
        "generator_sha256": report["generator_sha256"],
        "rule_text_sha256": report["rule_text_sha256"],
    }, indent=2))


if __name__ == "__main__":
    main()
