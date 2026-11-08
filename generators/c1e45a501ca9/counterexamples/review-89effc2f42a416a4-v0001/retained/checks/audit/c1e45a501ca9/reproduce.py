#!/usr/bin/env python3
"""Bounded findings-only audit; reads selected source without modifying it.

Run from the outer packet directory with the packet environment activated:
    python3 review.py run python3 ../checks/audit/c1e45a501ca9/reproduce.py
Then obtain labels with the supported arcpuzzles apply command and run this
script with --finalize to bind that actual authority receipt into the witness.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK = "c1e45a501ca9"
OUT = Path(__file__).resolve().parent
ROOT = find_root(__file__)


def sha(value):
    return hashlib.sha256(json.dumps(value, separators=(",", ":")).encode()).hexdigest()


def write(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def probe():
    module, source, digest = load_selected_generator(TASK, root=ROOT)
    from puzzle_generators.base import set_ctx_observer

    seed, sample_index, difficulty = 0, 0, "easy"
    probes = [
        ("baseline", {}),
        ("n_cells_min", {"n_cells": 1}),
        ("n_cells_max", {"n_cells": 6}),
        ("palette_size_min", {"palette_size": 1}),
        ("unknown_key", {"typo_axis": 123}),
    ]
    rows = []
    baseline = None
    for name, overrides in probes:
        contexts = []
        set_ctx_observer(contexts.append)
        try:
            grid = module.generate(seed, sample_index, difficulty=difficulty, **overrides)
        finally:
            set_ctx_observer(None)
        if baseline is None:
            baseline = grid
        cells = [[r, c, v] for r, row in enumerate(grid) for c, v in enumerate(row) if v not in (0, 8)]
        rows.append({
            "probe": name,
            "overrides": overrides,
            "accepted": True,
            "same_as_baseline": grid == baseline,
            "n_cells": len(cells),
            "n_distinct_source_colors": len({v for r, c, v in cells}),
            "source_cells": cells,
            "shape": [len(grid), len(grid[0])],
            "self_check": module.self_check(grid, difficulty=difficulty),
            "recorded_draws": contexts[0].recorded_draws(),
            "overrides_used": contexts[0].overrides_used(),
            "input_compact_json_sha256": sha(grid),
            "input": grid,
        })

    canonical = canonical_pairs(TASK, root=ROOT, labeled_only=True)
    canonical_checks = [{
        "variant": pair["variant"], "split": pair["split"], "pair_index": pair["pair_index"],
        "shape": [len(pair["input"]), len(pair["input"][0])],
        "self_check": module.self_check(pair["input"]),
        "input_compact_json_sha256": sha(pair["input"]),
    } for pair in canonical]

    record = {
        "schema": "arcpuzzles-audit-counterexample-v1",
        "task_id": TASK,
        "generator_sha256": digest,
        "generator_version": module.VERSION,
        "selected_source_path_relative_to_repo": source.relative_to(ROOT).as_posix(),
        "seed": seed, "sample_index": sample_index, "difficulty": difficulty,
        "overrides": {"n_cells": 1},
        "declared_axes": {k: module.AXES[k] for k in ("n_cells", "palette_size", "n_distinct_colors")},
        "generator_calls": len(rows),
        "unique_generated_inputs": len({row["input_compact_json_sha256"] for row in rows}),
        "probes": rows,
        "input": rows[1]["input"],
        "self_check": rows[1]["self_check"],
        "domain_membership": "Actual ordinary generator output; accepted by self_check; the same grid is also produced without overrides.",
        "finding": "Declared exact n_cells=1 and n_cells=6 both produce two colored source cells; palette_size=1 still produces two source colors; typo_axis=123 is silently accepted. Every controlled call returns the baseline grid and records no consumed overrides.",
        "inherited_leads": [
            {"return_id": "review-9a3cfcbadd2ba12e:v0001", "resolution": "unresolved", "source_sha256": digest},
            {"return_id": "review-31118be85ee0aad5:v0001", "resolution": "needs_triage", "source_sha256": digest},
        ],
        "canonical_validator_scope": {
            "source": "canonical_pairs(task_id, root=find_root(__file__), labeled_only=True)",
            "pairs": canonical_checks,
            "accepted": sum(not row["self_check"] for row in canonical_checks),
            "total": len(canonical_checks),
            "interpretation": "Documented-domain question only: the generator and validator restrict seeds to left/upper side with every target in bounds; canonical examples also have below-guide seeds and clipped reflections. This is not claimed to be a new label defect.",
        },
        "rival_output": None,
        "rival_note": "The counterexample is to an exact input-control/provenance contract, not to a competing output rule; no unique alternative output grid follows from requesting n_cells=1.",
        "command": {"cwd": "packet_root", "payload_cwd": "repo", "argv": ["python3", "review.py", "run", "python3", "../checks/audit/c1e45a501ca9/reproduce.py"]},
        "supported_apply": {"cwd": "packet_root", "payload_cwd": "repo", "argv": ["python3", "review.py", "run", "python3", "-m", "arcpuzzles", "apply", TASK, "--input", "../checks/audit/c1e45a501ca9/input.json", "--out", "../checks/audit/c1e45a501ca9/racket.json"]},
        "limits": "Five calls at one seed/index/band, one unique generated grid, and five canonical validator calls. No random census, task-test stage, semantic gate, lesson assembly, or query-rotation assessment was run. Universal generator validity and lesson identifiability remain unknown.",
    }
    write("input.json", record["input"])
    write("counterexample.json", record)
    assert digest == "0088b656430fb47933974db0db91df01fdd78fc4e03a60a7e8d406a78306c791"
    assert len(rows) == 5 and all(row["accepted"] and row["same_as_baseline"] and not row["self_check"] for row in rows)
    assert all(row["n_cells"] == 2 and row["n_distinct_source_colors"] == 2 and row["overrides_used"] == {} for row in rows)
    print(json.dumps({"reproduced": True, "generator_sha256": digest, "calls": len(rows), "unique_inputs": record["unique_generated_inputs"], "observed_n_cells": 2, "canonical_validator_acceptance": [record["canonical_validator_scope"]["accepted"], len(canonical_checks)]}, indent=2))


def finalize():
    record = json.loads((OUT / "counterexample.json").read_text())
    authority = json.loads((OUT / "racket.json").read_text())
    result = authority["results"][0]
    _, source, digest = load_selected_generator(TASK, root=ROOT)
    assert authority["generator_sha256"] == record["generator_sha256"] == digest
    assert authority["rule_hash_matches_catalog"] is True
    assert len(authority["results"]) == 1
    assert result["input"] == record["input"]
    assert result["valid_output"] is True and result["error"] is None
    record.update({
        "executed_rule_hash": authority["executed_rule_hash"],
        "rule_text_sha256": authority["rule_text_sha256"],
        "rule_hash_matches_catalog": authority["rule_hash_matches_catalog"],
        "actual_racket_output": result["output"],
        "racket_valid_output": result["valid_output"],
        "input_sha256": result["input_sha256"],
        "output_sha256": result["output_sha256"],
        "source_hash_unchanged_after_apply": True,
    })
    # The apply receipt remains unmodified. Record its whole-file hash here so
    # nested evidence can be inspected against the selected command's own schema.
    record["racket_receipt_sha256"] = hashlib.sha256((OUT / "racket.json").read_bytes()).hexdigest()
    write("counterexample.json", record)
    print(json.dumps({"racket_receipt_sha256": record["racket_receipt_sha256"], "generator_sha256": digest, "executed_rule_hash": authority["executed_rule_hash"], "rule_text_sha256": authority["rule_text_sha256"], "valid_outputs": 1, "total_inputs": 1, "source_unchanged": True}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--finalize", action="store_true")
    args = parser.parse_args()
    finalize() if args.finalize else probe()
