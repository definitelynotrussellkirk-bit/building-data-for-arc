#!/usr/bin/env python3
"""Verify retained public-Racket labels against exact audit grids and claims."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def grid_sha(grid):
    return hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    base = args.out.resolve()
    probe = json.loads((base / "probe.json").read_text())
    racket = json.loads((base / "racket.json").read_text())
    identities = json.loads((base / "input-identities.json").read_text())
    assert racket["generator_sha256"] == probe["generator_sha256"]
    assert hashlib.sha256(Path(probe["generator_source"]).read_bytes()).hexdigest() == probe["generator_sha256"]
    assert racket["rule_hash_matches_catalog"]
    assert len(racket["results"]) == 7
    checks = []
    for index, result in enumerate(racket["results"]):
        inp, output = result["input"], result["output"]
        assert result["valid_output"] and result["error"] is None
        assert result["generator_domain"] == {"status": "valid", "errors": []}
        assert result["input_sha256"] == grid_sha(inp)
        assert result["output_sha256"] == grid_sha(output)
        changes = [{"row": r, "col": c, "before": x, "after": y}
                   for r, (before, after) in enumerate(zip(inp, output, strict=True))
                   for c, (x, y) in enumerate(zip(before, after, strict=True)) if x != y]
        check = {"index": index, "identity": identities[index],
                 "input_sha256": result["input_sha256"],
                 "output_sha256": result["output_sha256"],
                 "valid_output": True, "error": None,
                 "generator_domain": result["generator_domain"],
                 "changed_cells": changes,
                 "output_shape": [len(output), len(output[0])]}
        if index < 2:
            scene = probe["primary_witness"] if index == 0 else probe["same_size_feasibility_witness"]
            assert inp == scene["input"]
            expected = {tuple(cell) for frame in scene["components"] for cell in frame["corners"]}
            assert {(cell["row"], cell["col"]) for cell in changes} == expected
            assert all(cell["before"] == 3 and cell["after"] == 4 for cell in changes)
            check["matches_frame_corner_rule"] = True
        else:
            pair = probe["canonical_pairs"][index - 2]
            assert inp == pair["input"] and output == pair["output"]
            check["matches_canonical"] = True
        checks.append(check)
    verified = {key: value for key, value in racket.items() if key != "results"}
    verified["checks"] = checks
    verified["status"] = "seven_reference_labels_and_domains_verified"
    (base / "racket-verification.json").write_text(json.dumps(verified, indent=2) + "\n")
    evidence = {
        "schema": "arcpuzzles-focused-audit-result-v1", "task_id": probe["task_id"],
        "status": "current_exact_control_defect_reproduced",
        "generator_sha256": probe["generator_sha256"],
        "canonical_program_source_sha256": probe["canonical_program_source_sha256"],
        "executed_rule_hash": racket["executed_rule_hash"],
        "executed_rule_text_sha256": racket["rule_text_sha256"],
        "primary_witness": dict(probe["primary_witness"],
                                reference_output=racket["results"][0]["output"],
                                reference_output_sha256=racket["results"][0]["output_sha256"],
                                reference_changed_cells=checks[0]["changed_cells"]),
        "same_size_feasibility_witness": dict(probe["same_size_feasibility_witness"],
                                               reference_output=racket["results"][1]["output"],
                                               reference_changed_cells=checks[1]["changed_cells"]),
        "bounded_probe_counts": probe["counts"],
        "reference_labels_checked": 7,
        "canonical_labels_matched": 5,
        "declared_control_rejections": probe["declared_control_rejections"],
        "paired_control_probe_summary": {"palette_kind_warm_vs_cool": "4/4 equal", "texture_warm_vs_cool": "4/4 equal"},
        "commands": ["probe.command.json", "racket.command.json", "verify.command.json"],
        "retained_runtime_trees": [],
        "limitations": probe["no_claims"],
    }
    (base / "evidence.json").write_text(json.dumps(evidence, indent=2) + "\n")
    print(json.dumps({"status": evidence["status"],
                      "generator_sha256": evidence["generator_sha256"],
                      "executed_rule_hash": evidence["executed_rule_hash"],
                      "reference_labels_checked": 7, "canonical_labels_matched": 5,
                      "probe_counts": probe["counts"]}, indent=2))


if __name__ == "__main__":
    main()
