"""Source-bound findings-only audit; labels come from the public Racket apply API."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
TASK = "56c98fd9e674"


def sha_bytes(data):
    return hashlib.sha256(data).hexdigest()


def grid_hash(grid):
    return sha_bytes(json.dumps(grid, separators=(",", ":")).encode())


def markers(grid):
    return [(r, c, value) for r, row in enumerate(grid)
            for c, value in enumerate(row) if value != 0]


def main():
    sys.path.insert(0, str(ROOT / "repo/shared/runtime"))
    from puzzle_generators.base import set_ctx_observer
    source = ROOT / f"repo/generators/{TASK}/generator.py"
    source_hash = sha_bytes(source.read_bytes())
    spec = importlib.util.spec_from_file_location("assigned_audit_generator", source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    canonical = next(json.loads(line) for line in
                     (ROOT / "repo/shared/data/canonical/puzzles.jsonl").read_text().splitlines()
                     if json.loads(line)["task_id"] == TASK)
    rule = canonical["program_solution"]
    contexts = []
    set_ctx_observer(contexts.append)
    cases = []
    requests = [
        ("silent_marker_loss", 3, 0, "easy", {"grid_h": 5, "grid_w": 5, "n_cells": 2}),
        ("ignored_color_axis", 17, 0, "hard", {"n_cells": 5, "n_distinct_colors": 1}),
        ("rejected_corner_witness", 0, 0, "medium", {"texture": "cells_at_corner"}),
    ]
    for name, seed, index, band, overrides in requests:
        grid = module.generate(seed, index, difficulty=band, **overrides)
        ctx = contexts[-1]
        cases.append({"name": name, "request": {"seed": seed, "sample_index": index,
                      "difficulty": band, "overrides": overrides}, "input": grid,
                      "input_sha256": grid_hash(grid), "markers": markers(grid),
                      "observed_n_cells": len(markers(grid)),
                      "observed_nonzero_colors": sorted({v for _, _, v in markers(grid)}),
                      "self_check": module.self_check(grid),
                      "recorded_draws": ctx.recorded_draws(),
                      "overrides_used": ctx.overrides_used()})
    set_ctx_observer(None)
    canonical_checks = []
    test_pairs = canonical["test"]
    if isinstance(test_pairs, dict):
        test_pairs = [test_pairs]
    for split, pairs in (("train", canonical["train"]), ("test", test_pairs)):
        for index, pair in enumerate(pairs):
            canonical_checks.append({"split": split, "pair_index": index,
                                     "input_sha256": grid_hash(pair["input"]),
                                     "markers": markers(pair["input"]),
                                     "self_check": module.self_check(pair["input"])})
    input_path = OUT / "input.json"
    input_path.write_text(json.dumps({"inputs": [case["input"] for case in cases]}, indent=2) + "\n")
    command = [".venv-review/bin/python", "run_with_racket.py", "../.venv-review/bin/python",
               "-m", "arcpuzzles", "apply", TASK, "--input",
               f"../checks/audit/{TASK}/input.json", "--out", f"../checks/audit/{TASK}/racket.json"]
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    execution = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, text=True, timeout=180)
    (OUT / "apply.stdout.log").write_text(execution.stdout)
    (OUT / "apply.stderr.log").write_text(execution.stderr)
    result_path = OUT / "racket.json"
    result = json.loads(result_path.read_text()) if result_path.exists() else None
    verification_errors = []
    if execution.returncode != 0 or result is None:
        verification_errors.append("public apply failed")
    else:
        for case, labeled in zip(cases, result["results"]):
            case["public_racket_output"] = labeled["output"]
            case["public_input_sha256"] = labeled["input_sha256"]
            case["public_output_sha256"] = labeled["output_sha256"]
            case["public_valid_output"] = labeled["valid_output"]
            if labeled["input"] != case["input"] or not labeled["valid_output"] or labeled["error"]:
                verification_errors.append("invalid or mismatched public label: " + case["name"])
    if cases[0]["observed_n_cells"] != 1 or cases[0]["self_check"]:
        verification_errors.append("silent marker loss not reproduced")
    if not canonical_checks[1]["self_check"]:
        verification_errors.append("canonical boundary rejection not reproduced")
    if source_hash != sha_bytes(source.read_bytes()):
        verification_errors.append("generator source changed during probe")
    report = {"schema": "findings-only-assigned-audit-v1", "task_id": TASK,
              "generator_sha256": source_hash,
              "generator_sha256_after_probe": sha_bytes(source.read_bytes()),
              "canonical_rule_raw_sha256": sha_bytes(rule.encode()),
              "canonical_rule_normalized_sha256": sha_bytes(" ".join(rule.split()).encode()),
              "canonical_rule_hash": sha_bytes(" ".join(rule.split()).encode())[:12],
              "prior_lead": "review-57bc0a63a72e9edc:v0001; current review_index audit is accepted/needs_triage and bound to the same source bytes",
              "probe_command": [".venv-review/bin/python", "-B", f"checks/audit/{TASK}/probe.py"],
              "command_argv": command, "cwd": str(ROOT), "payload_cwd": str(ROOT / "repo"),
              "apply_exit_code": execution.returncode,
              "probe_exit_code": int(bool(verification_errors)),
              "verification_errors": verification_errors,
              "probe_sha256": sha_bytes(Path(__file__).read_bytes()),
              "input_file_sha256": sha_bytes(input_path.read_bytes()),
              "racket_result_file_sha256": sha_bytes(result_path.read_bytes()) if result else None,
              "generated_cases": cases, "canonical_validation": canonical_checks,
              "public_apply_result": result,
              "scope": "Three decisive generated cases and three public canonical input validations; no full battery or private solve access."}
    (OUT / "receipt.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"apply_exit_code": execution.returncode, "generator_sha256": source_hash,
                      "receipt": str(OUT / "receipt.json"),
                      "case_counts": [case["observed_n_cells"] for case in cases],
                      "canonical_validation": canonical_checks}))
    return int(bool(verification_errors))


if __name__ == "__main__":
    raise SystemExit(main())
