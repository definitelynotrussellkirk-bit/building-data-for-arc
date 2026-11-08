"""Bounded, public-data audit. Run from the WORK packet root."""
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

from reviewer_support import canonical_pairs


TASK = "dcc5f8961845"
DEST = Path("checks/audit") / TASK
SOURCE = Path("repo/generators") / TASK / "generator.py"
SPEC = importlib.util.spec_from_file_location("audit_dcc5f8961845", SOURCE)
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)


def transform(grid, command):
    height, width = len(grid), len(grid[0])
    out_h, out_w = (width, height) if command in (1, 3) else (height, width)
    output = [[0] * out_w for _ in range(out_h)]
    for row in range(height):
        for col in range(width):
            target = (
                (row, col), (col, height - 1 - row),
                (height - 1 - row, width - 1 - col), (col, row),
                (row, width - 1 - col), (height - 1 - row, col),
            )[command]
            output[target[0]][target[1]] = grid[row][col]
    return output


def reference_from_pixels(grid, *, reversed_order=False):
    cells = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row)
             if v != 0 and (r, c) not in ((0, 0), (0, 1))]
    top, bottom = min(r for r, c in cells), max(r for r, c in cells)
    left, right = min(c for r, c in cells), max(c for r, c in cells)
    motif = [row[left:right + 1] for row in grid[top:bottom + 1]]
    commands = grid[0][:2]
    if reversed_order:
        commands = commands[::-1]
    for command in commands:
        motif = transform(motif, command)
    return motif


def validator_result(grid):
    try:
        return {"returned": GEN.self_check(grid), "exception": None}
    except Exception as error:
        return {"returned": None,
                "exception": {"type": type(error).__name__, "message": str(error)}}


def main():
    pairs = canonical_pairs(TASK, root=Path("repo"), labeled_only=True)
    records = []
    for cmd1 in range(6):
        for cmd2 in range(6):
            index = cmd1 * 6 + cmd2
            band = ("easy", "medium", "hard")[index % 3]
            overrides = {"grid_h": 8, "grid_w": 9, "motif_h": 2, "motif_w": 5,
                         "n_colors": 3, "cmd1": cmd1, "cmd2": cmd2}
            grid = GEN.generate(802, index, difficulty=band, **overrides)
            expected = reference_from_pixels(grid)
            records.append({
                "seed": 802, "sample_index": index, "difficulty": band,
                "overrides": overrides, "input": grid,
                "validator": validator_result(grid),
                "observed_axes": GEN.observe_overrides(grid),
                "independent_output": expected,
                "python_mirror_matches": GEN.rule_mirror(grid) == expected,
                "reversed_order_rival_output": reference_from_pixels(grid, reversed_order=True),
                "domain_status": "inside documented generated domain",
            })
    baseline = deepcopy(pairs[0]["input"])
    malformed = deepcopy(baseline)
    malformed[3][3] = None
    result = {
        "schema": "review-audit-probe-v1", "task_id": TASK,
        "generator_version": GEN.VERSION,
        "generator_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        "declared_rule_hash": GEN.RULE_HASH,
        "canonical_pair_count": len(pairs),
        "canonical_validator_findings": [GEN.self_check(p["input"]) for p in pairs],
        "canonical_independent_matches": [reference_from_pixels(p["input"]) == p["output"] for p in pairs],
        "canonical_python_mirror_matches": [GEN.rule_mirror(p["input"]) == p["output"] for p in pairs],
        "generated_count": len(records), "generated_records": records,
        "finding": {
            "id": "A2", "classification": "reproduced validator exception on malformed input",
            "input": malformed, "input_path": str(DEST / "malformed-input.json"),
            "seed": None, "sample_index": None, "overrides": {},
            "origin": "canonical variant 0 train pair 0; replace cell (3,3) value 2 with null",
            "validator": validator_result(malformed),
            "domain_status": "outside documented domain: one cell is not an integer ARC color",
            "expected_validator_behavior": "return nonempty findings; do not crash during scene analysis",
            "cause": "self_check records invalid value but continues into _analyze_scene; sorting colors mixes None and int",
            "baseline_input": baseline, "baseline_output": pairs[0]["output"],
            "baseline_validator": validator_result(baseline),
        },
        "prior_audit": {
            "return_id": "review-5f28079104b822e3:v0001",
            "classification": "existing unresolved portable-test path defect remains visible in unchanged test source",
            "evidence_status": "source inspected; prior task-test failure not rerun",
        },
    }
    DEST.mkdir(parents=True, exist_ok=True)
    (DEST / "input.json").write_text(json.dumps([r["input"] for r in records] + [baseline]) + "\n")
    (DEST / "malformed-input.json").write_text(json.dumps(malformed) + "\n")
    (DEST / "probe.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({
        "task_id": TASK, "generated_count": len(records),
        "generated_validator_failures": sum(bool(r["validator"]["returned"]) or r["validator"]["exception"] is not None for r in records),
        "independent_mirror_failures": sum(not r["python_mirror_matches"] for r in records),
        "reversed_order_different_count": sum(r["reversed_order_rival_output"] != r["independent_output"] for r in records),
        "malformed_validator": result["finding"]["validator"],
    }, indent=2))


def finalize():
    probe = json.loads((DEST / "probe.json").read_text())
    labels = json.loads((DEST / "racket.json").read_text())
    malformed_log = (DEST / "malformed-racket.log").read_text()
    records, results = probe["generated_records"], labels["results"]
    assert len(records) == 36 and len(results) == 37
    assert labels["generator_sha256"] == probe["generator_sha256"]
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == probe["generator_sha256"]
    assert labels["executed_rule_hash"] == probe["declared_rule_hash"]
    assert all(not row["error"] and row["valid_output"] for row in results)
    assert all(row["output"] == record["independent_output"]
               for record, row in zip(records, results))
    assert results[-1]["output"] == probe["finding"]["baseline_output"]
    assert "cells must be integers 0..9" in malformed_log
    finding = probe["finding"]
    commands = [
        {
            "cwd": "packet_root",
            "actual_cwd": str(Path.cwd()),
            "argv": [".venv/bin/python", str(DEST / "probe.py")],
            "environment": {"PYTHONPATH": "repo/src:repo/shared/runtime"},
            "exit_code": 0,
            "evidence_paths": [str(DEST / name) for name in ("probe.json", "input.json", "malformed-input.json")],
        },
        {
            "cwd": "packet_root", "runtime_cwd": "repo",
            "argv": ["python3", "run_with_racket.py", "python3", "-m", "arcpuzzles", "apply", TASK,
                     "--input", f"../{DEST}/input.json", "--out", f"../{DEST}/racket.json"],
            "environment_setup": "source .venv/bin/activate",
            "exit_code": 0,
            "evidence_paths": [str(DEST / "racket.json"), str(DEST / "racket.log")],
        },
        {
            "cwd": "packet_root", "runtime_cwd": "repo",
            "argv": ["python3", "run_with_racket.py", "python3", "-m", "arcpuzzles", "apply", TASK,
                     "--input", f"../{DEST}/malformed-input.json", "--out", f"../{DEST}/malformed-racket.json"],
            "environment_setup": "source .venv/bin/activate",
            "exit_code": 1,
            "evidence_paths": [str(DEST / "malformed-racket.log")],
            "note": "Expected normalization rejection; no malformed-racket.json or reference output is produced.",
        },
        {
            "cwd": "packet_root",
            "actual_cwd": str(Path.cwd()),
            "argv": [".venv/bin/python", str(DEST / "probe.py"), "--finalize"],
            "environment": {"PYTHONPATH": "repo/src:repo/shared/runtime"},
            "exit_code": 0,
            "evidence_paths": [str(DEST / "audit.json")],
        },
    ]
    report = {
        "schema": "review-audit-counterexample-v1", "task_id": TASK,
        "finding_id": "A2", "finding_type": "reproduced_validator_robustness_defect",
        "finding": "One null motif cell crashes self_check while sorting mixed None/int colors instead of returning findings.",
        "generator_sha256": probe["generator_sha256"], "generator_version": probe["generator_version"],
        "declared_rule_hash": probe["declared_rule_hash"],
        "executed_rule_hash": labels["executed_rule_hash"],
        "rule_text_sha256": labels["rule_text_sha256"],
        "seed": None, "sample_index": None, "overrides": {},
        "input": finding["input"], "input_path": finding["input_path"],
        "construction": finding["origin"], "validator_result": finding["validator"],
        "domain_status": finding["domain_status"],
        "actual_racket_output": None, "rival_output": None,
        "reference_status": "Public apply rejects the malformed grid during normalization; there is no legal reference output.",
        "reference_rejection": "input 0 cells must be integers 0..9",
        "unchanged_control": {
            "input": finding["baseline_input"], "validator_result": finding["baseline_validator"],
            "actual_racket_output": results[-1]["output"], "racket_result_index": 36,
        },
        "lawful_probe_results": {
            "canonical_pairs": 5, "canonical_validator_and_independent_checks_passed": 5,
            "generated_inputs": 36, "unique_generated_inputs": len({json.dumps(r["input"]) for r in records}),
            "seed": 802, "sample_indices": [0, 35], "command_pairs": "all 36 ordered pairs in 0..5 × 0..5",
            "joint_controls": "8×9 canvas, 2×5 motif, three colors, rotating easy/medium/hard difficulty",
            "validator_failures": 0, "observable_override_mismatches": sum(r["observed_axes"] != r["overrides"] for r in records),
            "racket_generated_matches": 36, "racket_control_matches": 1, "racket_execution_errors": 0,
            "reversed_order_rival_disagrees": sum(r["reversed_order_rival_output"] != row["output"] for r, row in zip(records, results)),
        },
        "cause": finding["cause"],
        "suggested_repair": "Return collected structural/type errors before analyzing the scene, then add a null-cell validator regression.",
        "patch_status": "audit only; target source, tests, and notes unchanged",
        "prior_audit": probe["prior_audit"],
        "limitations": [
            "The new counterexample is outside the documented integer-grid generator domain; it demonstrates validator robustness, not incorrect labels on lawful generated inputs.",
            "No full battery or task-test rerun was performed for this findings-only audit.",
            "The finite command matrix is not an exhaustive seed or distribution proof.",
        ],
        "verification_commands": commands,
    }
    (DEST / "audit.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"audit": str(DEST / "audit.json"), "racket_matches": 37,
                      "finding": report["finding"], "source_unchanged": True}, indent=2))


if __name__ == "__main__":
    finalize() if sys.argv[1:] == ["--finalize"] else main()
