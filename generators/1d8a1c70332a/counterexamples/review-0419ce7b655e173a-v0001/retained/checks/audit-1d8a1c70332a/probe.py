"""Bounded findings-only audit: ignored controls and unchecked histogram bounds."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

TASK = "1d8a1c70332a"
SOURCE_HASH = "3a71edc11890b5bb86f469b4d6d5f4378a7816d14a91dc38ce1363bdf3c88fef"
HERE = Path(__file__).resolve().parent
WORK = HERE.parent.parent
ROOT = WORK / "repo"
REQUESTED = {"grid_h": 22, "grid_w": 24, "anchor_size": 10, "anchor_color": 2}


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def save(name, value):
    (HERE / name).write_text(json.dumps(value, indent=2) + "\n")


def observe(grid):
    anchor = [value for row in grid for value in row if value not in (0, 1)]
    return {"grid_h": len(grid), "grid_w": len(grid[0]),
            "anchor_size": len(anchor), "anchor_color": next(iter(set(anchor)))}


def simple_profile_output(grid):
    cells = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row)
             if value not in (0, 1)]
    marker = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 1]
    assert len(marker) == 1
    top = min(r for r, _ in cells)
    bottom = max(r for r, _ in cells)
    profile = [sum(r == rr for r, _ in cells) for rr in range(top, bottom + 1)]
    mr, mc = marker[0]
    footprint = [[mr + dr, mc + dc] for dr, count in enumerate(profile) for dc in range(count)]
    outside = [[r, c] for r, c in footprint if not (0 <= r < len(grid) and 0 <= c < len(grid[0]))]
    if outside:
        return {"profile": profile, "marker": marker[0], "outside_cells": outside, "output": None}
    output = [[0] * len(grid[0]) for _ in grid]
    for r, c in footprint:
        output[r][c] = 8
    return {"profile": profile, "marker": marker[0], "outside_cells": [], "output": output}


def main():
    source = ROOT / "generators" / TASK / "generator.py"
    raw = source.read_bytes()
    assert digest(raw) == SOURCE_HASH
    sys.path.insert(0, str(ROOT / "shared/runtime"))
    from reviewer_support import canonical_pairs
    spec = importlib.util.spec_from_file_location("audited_anchor_histogram", source)
    gen = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gen)
    rows = []
    with (ROOT / "shared/data/canonical/puzzles.jsonl").open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK:
                rows.append(row)
    assert len(rows) == 1
    rule = rows[0]["program_solution"]
    (HERE / "generator_snapshot.py").write_bytes(raw)
    (HERE / "canonical_rule.rkt").write_text(rule + "\n")
    baseline = gen.generate(0, 0, difficulty="medium")
    overridden = gen.generate(0, 0, difficulty="medium", **REQUESTED)
    actual = observe(overridden)
    overflow = [[0] * 12 for _ in range(12)]
    for r, c in ((1, 1), (1, 2), (2, 1), (2, 2)):
        overflow[r][c] = 3
    overflow[11][11] = 1
    canonical = canonical_pairs(TASK, root=ROOT)
    cases = [
        {"name": "valid_requested_controls_ignored", "input": overridden,
         "self_check": gen.self_check(overridden, difficulty="medium", meta={"overrides": REQUESTED}),
         "independent": simple_profile_output(overridden)},
        {"name": "histogram_out_of_bounds_accepted", "input": overflow,
         "self_check": gen.self_check(overflow), "independent": simple_profile_output(overflow)},
    ]
    for pair in canonical:
        cases.append({"name": f"canonical_v{pair['variant']}_{pair['split']}_{pair['pair_index']}",
                      "input": pair["input"], "expected_output": pair["output"],
                      "self_check": gen.self_check(pair["input"])})
    save("cases.json", cases)
    save("input.json", {"inputs": [case["input"] for case in cases]})
    argv = ["python3", "run_with_racket.py", "python3", "-m", "arcpuzzles", "apply", TASK,
            "--input", "../checks/audit-1d8a1c70332a/input.json",
            "--out", "../checks/audit-1d8a1c70332a/racket.json"]
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    reuse = "--reuse-reference" in sys.argv[1:]
    if reuse:
        commands = json.loads((HERE / "commands.json").read_text())
        commands["reference_recheck"] = {
            "argv": ["python3", "checks/audit-1d8a1c70332a/probe.py", "--reuse-reference"],
            "cwd": str(WORK), "environment": {"PYTHONDONTWRITEBYTECODE": "1"},
            "basis": "Rechecks retained authoritative outputs; does not execute Racket again."}
    else:
        if (HERE / "racket.json").exists():
            raise FileExistsError("Reference receipt exists; use --reuse-reference to verify it without rerunning Racket")
        completed = subprocess.run(argv, cwd=WORK, env=env, capture_output=True, text=True)
        (HERE / "racket-command.stdout.txt").write_text(completed.stdout)
        (HERE / "racket-command.stderr.txt").write_text(completed.stderr)
        commands = {"audit": {"argv": ["python3", "checks/audit-1d8a1c70332a/probe.py"],
                              "cwd": str(WORK), "environment": {"PYTHONDONTWRITEBYTECODE": "1"}},
                    "reference": {"argv": argv, "cwd": str(WORK),
                                  "payload_cwd": str(ROOT), "exit_code": completed.returncode,
                                  "environment": {"PYTHONDONTWRITEBYTECODE": "1"}}}
        assert completed.returncode == 0, completed.stderr
    receipt = json.loads((HERE / "racket.json").read_text())
    assert receipt["generator_sha256"] == SOURCE_HASH
    assert receipt["executed_rule_hash"] == "e9dfc88c50af"
    assert receipt["rule_hash_matches_catalog"]
    for case, result in zip(cases, receipt["results"], strict=True):
        assert result["input"] == case["input"], case["name"]
        case["racket_valid_output"] = result["valid_output"]
        case["racket_error"] = result.get("error")
        case["racket_nonzero_cells"] = [[r, c, value] for r, row in enumerate(result["output"] or [])
                                        for c, value in enumerate(row) if value]
        if "expected_output" in case:
            assert result["output"] == case["expected_output"], case["name"]
        elif case["independent"]["output"] is not None:
            assert result["output"] == case["independent"]["output"], case["name"]
    assert source.read_bytes() == raw
    report = {"schema": "bounded-generator-audit-v1", "task_id": TASK,
              "generator_sha256_before": SOURCE_HASH, "generator_sha256_after": digest(source.read_bytes()),
              "canonical_program_sha256": digest(rule.encode()),
              "executed_rule_hash": receipt["executed_rule_hash"],
              "executed_rule_text_sha256": receipt["rule_text_sha256"],
              "generation_calls": 2, "racket_inputs_checked": len(cases),
              "requested": REQUESTED, "observed": actual,
              "mismatches": {k: {"requested": v, "observed": actual[k]} for k, v in REQUESTED.items() if actual[k] != v},
              "baseline_equals_overridden": baseline == overridden,
              "prior_audit": "Reconfirms the same-source retained AUDIT-1D8A-OVERRIDES-IGNORED finding; not claimed as novel.",
              "cases": [{k: v for k, v in case.items() if k not in ("input", "expected_output")} for case in cases],
              "target_unchanged": True}
    save("findings.json", report)
    assert report["mismatches"] and cases[1]["self_check"] == []
    assert cases[1]["independent"]["outside_cells"] == [[11, 12], [12, 11], [12, 12]]
    assert cases[1]["racket_nonzero_cells"] == [[11, 11, 8]]
    commands["audit"]["exit_code"] = 0
    if reuse:
        commands["reference_recheck"]["exit_code"] = 0
    save("commands.json", commands)
    print(json.dumps({"mismatches": report["mismatches"], "racket_inputs_checked": len(cases),
                      "overflow": cases[1]["racket_error"], "overflow_valid": cases[1]["racket_valid_output"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
