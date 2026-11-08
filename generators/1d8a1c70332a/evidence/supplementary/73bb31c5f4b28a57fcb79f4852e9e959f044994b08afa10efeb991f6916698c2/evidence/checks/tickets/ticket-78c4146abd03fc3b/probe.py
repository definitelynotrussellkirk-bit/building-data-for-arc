"""Two-draw audit of the selected generator's documented override controls."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

from arcpuzzles import Catalog

TASK = "1d8a1c70332a"
EXPECTED_SOURCE = "3a71edc11890b5bb86f469b4d6d5f4378a7816d14a91dc38ce1363bdf3c88fef"
REQUESTED = {"grid_h": 22, "grid_w": 24, "anchor_size": 10, "anchor_color": 2}


def digest(grid):
    return hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()


def observe(grid):
    cells = [(r, c, v) for r, row in enumerate(grid) for c, v in enumerate(row) if v not in (0, 1)]
    return {"grid_h": len(grid), "grid_w": len(grid[0]), "anchor_size": len(cells),
            "anchor_color": next(iter({v for r, c, v in cells}))}


def independent_output(grid):
    points = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v not in (0, 1)]
    markers = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 1]
    assert len(markers) == 1
    r0, c0 = markers[0]
    top, bottom = min(r for r, c in points), max(r for r, c in points)
    profile = [sum(r == row for r, c in points) for row in range(top, bottom + 1)]
    out = [[0] * len(grid[0]) for _ in grid]
    for dr, count in enumerate(profile):
        for dc in range(count):
            out[r0 + dr][c0 + dc] = 8
    return out, profile


def main():
    root = Path.cwd()  # WORK/run_with_racket.py explicitly selects repo as cwd.
    out = Path(__file__).resolve().parent
    source = root / "generators" / TASK / "generator.py"
    raw = source.read_bytes()
    source_sha = hashlib.sha256(raw).hexdigest()
    assert source_sha == EXPECTED_SOURCE
    (out / "generator_snapshot.py").write_bytes(raw)
    spec = importlib.util.spec_from_file_location("audited_generator", source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    baseline = module.generate(0, 0, difficulty="medium")
    actual = module.generate(0, 0, difficulty="medium", **REQUESTED)
    observed = observe(actual)
    reference = Catalog(root).apply(TASK, [actual], timeout=120)
    (out / "racket.json").write_text(json.dumps(reference, indent=2) + "\n")
    authority_output = reference["results"][0]["output"]
    expected, profile = independent_output(actual)
    assert authority_output == expected
    assert reference["generator_sha256"] == source_sha
    assert source.read_bytes() == raw
    mismatches = {axis: {"requested": value, "observed": observed[axis]}
                  for axis, value in REQUESTED.items() if observed[axis] != value}
    report = {
        "schema": "task-local-generator-audit-v1", "task_id": TASK,
        "finding_id": "AUDIT-1D8A-OVERRIDES-IGNORED", "status": "confirmed",
        "generator_sha256": source_sha, "rule_hash": reference["executed_rule_hash"],
        "rule_text_sha256": reference["rule_text_sha256"],
        "command": "python3 WORK/run_with_racket.py python3 ../checks/audit/1d8a1c70332a/probe.py",
        "command_cwd": "packet root", "seed": 0, "sample_index": 0,
        "difficulty": "medium", "overrides": REQUESTED,
        "documented_valid_values": {axis: module.AXES[axis]["valid"] for axis in REQUESTED},
        "observed": observed, "mismatches": mismatches,
        "baseline_equals_overridden_input": baseline == actual,
        "generation_calls": 2, "distinct_generated_inputs": len({digest(baseline), digest(actual)}),
        "racket_inputs_checked": 1, "independent_output_matches_racket": True,
        "self_check": module.self_check(actual, difficulty="medium", meta={"overrides": REQUESTED}),
        "input_sha256": digest(actual), "input": actual,
        "output_sha256": digest(authority_output), "output": authority_output,
        "anchor_row_profile": profile,
        "nonzero_input_cells": [[r, c, v] for r, row in enumerate(actual) for c, v in enumerate(row) if v],
        "nonzero_output_cells": [[r, c, v] for r, row in enumerate(authority_output) for c, v in enumerate(row) if v],
        "scope": "One paired control counterfactual, four documented valid controls, one unique grid. No general safety or distribution verdict.",
        "exit_code": 1 if mismatches else 0,
    }
    (out / "finding.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({key: report[key] for key in ("status", "generator_sha256", "rule_hash", "mismatches",
          "baseline_equals_overridden_input", "self_check", "anchor_row_profile", "nonzero_input_cells", "nonzero_output_cells")}, indent=2))
    return report["exit_code"]


if __name__ == "__main__":
    raise SystemExit(main())
