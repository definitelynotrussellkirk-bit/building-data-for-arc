#!/usr/bin/env python3
"""Bounded, findings-only audit; run through the packet's review.py run wrapper.

Uses public generator hooks, GenCtx provenance and portable canonical helpers.
It never imports private runner functions and never modifies the generator.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys

from arcpuzzles import Catalog
from reviewer_support import canonical_pairs, canonical_path, find_root
from puzzle_generators.base import set_ctx_observer

TASK = "dded62bb9e3a"
EXPECTED_SOURCE = "e66451a5e7b900225b1fb61ed5a64775331a87b36b4349bec3f3b0b4c6e37493"
OUT = Path(__file__).resolve().parent


def sha(value):
    return hashlib.sha256(json.dumps(value, separators=(",", ":")).encode()).hexdigest()


def write(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def read(name):
    return json.loads((OUT / name).read_text(encoding="utf-8"))


def source():
    # A task-local copy finds itself. In this packet checks/ is outside repo/;
    # the wrapper binds Catalog to this packet's explicit ARCPUZZLES_HOME.
    try:
        root = find_root(__file__)
    except FileNotFoundError:
        root = find_root(Catalog().root)
    path = root / "generators" / TASK / "generator.py"
    if not path.is_file():
        path = root / "puzzle_generators" / "per_puzzle" / (TASK + ".py")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    assert digest == EXPECTED_SOURCE, ("Audit source changed", digest)
    spec = importlib.util.spec_from_file_location("audited_" + TASK, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return root, path, digest, module


def components(cells):
    cells = set(cells)
    n = 0
    while cells:
        n += 1
        stack = [cells.pop()]
        while stack:
            r, c = stack.pop()
            for p in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if p in cells:
                    cells.remove(p)
                    stack.append(p)
    return n


def inspect_grid(grid):
    h, w = len(grid), len(grid[0])
    frame = {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 5}
    blob = {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v not in (0, 5)}
    fr1, fr2 = min(r for r, c in frame), max(r for r, c in frame)
    fc1, fc2 = min(c for r, c in frame), max(c for r, c in frame)
    br1, br2 = min(r for r, c in blob), max(r for r, c in blob)
    bc1, bc2 = min(c for r, c in blob), max(c for r, c in blob)
    expected_frame = {(r, c) for r in range(fr1, fr2 + 1) for c in range(fc1, fc2 + 1)
                      if r in (fr1, fr2) or c in (fc1, fc2)}
    requirements = {
        "integer_colors_0_to_9": all(type(v) is int and 0 <= v <= 9 for row in grid for v in row),
        "rectangular": all(len(row) == w for row in grid),
        "exact_hollow_5_frame_at_least_4_by_4": frame == expected_frame and fr2-fr1 >= 3 and fc2-fc1 >= 3,
        "one_blob_color": len({grid[r][c] for r, c in blob}) == 1,
        "one_four_connected_blob": components(blob) == 1,
        "whole_blob_outside_frame_bbox": all(not(fr1 <= r <= fr2 and fc1 <= c <= fc2) for r, c in blob),
        "blob_bbox_fits_frame_interior": br2-br1+1 <= fr2-fr1-1 and bc2-bc1+1 <= fc2-fc1-1,
    }
    return {
        "input_shape": [h, w], "blob_cell_count": len(blob),
        "frame_bbox": [fr1, fc1, fr2, fc2], "blob_bbox": [br1, bc1, br2, bc2],
        "frame_flush_bottom_right": fr2 == h-1 and fc2 == w-1,
        "documented_domain_requirements": requirements,
        "belongs_to_documented_rule_domain": all(requirements.values()),
    }


def relocate(grid, *, fixed_bottom_right=False):
    info = inspect_grid(grid)
    h, w = info["input_shape"]
    fr1, fc1, fr2, fc2 = info["frame_bbox"]
    br1, bc1, _, _ = info["blob_bbox"]
    if fixed_bottom_right:
        fr1, fc1 = h - (fr2-fr1+1), w - (fc2-fc1+1)
    output = [[0] * w for _ in range(h)]
    for r, row in enumerate(grid):
        for c, v in enumerate(row):
            if v not in (0, 5):
                output[fr1 + 1 + r - br1][fc1 + 1 + c - bc1] = v
    return output


def prepare():
    root, path, digest, gen = source()
    inputs, input_by_hash, cases, controls = [], {}, [], []

    def retain(grid, case):
        key = sha(grid)
        if key not in input_by_hash:
            input_by_hash[key] = len(inputs)
            inputs.append(grid)
        case = {**case, "authority_index": input_by_hash[key], "input_sha256": key,
                "self_check": gen.self_check(grid), **inspect_grid(grid)}
        cases.append(case)
        return case

    pairs = canonical_pairs(TASK, root=root, labeled_only=True)
    for pair in pairs:
        retain(pair["input"], {"kind": "canonical", "variant": pair["variant"],
               "split": pair["split"], "pair_index": pair["pair_index"],
               "canonical_output": pair["output"], "seed": None, "sample_index": None, "overrides": None})

    for difficulty in (None, "easy", "medium", "hard"):
        for seed in (0, 17):
            for sample_index in (0, 1):
                group = []
                for overrides in ({}, {"blob_size": 1}, {"blob_size": 5}):
                    contexts = []
                    set_ctx_observer(contexts.append)
                    try:
                        grid = gen.generate(seed, sample_index, difficulty=difficulty, **overrides)
                    finally:
                        set_ctx_observer(None)
                    assert len(contexts) == 1
                    ctx = contexts[0]
                    case = retain(grid, {"kind": "direct_public_hooks", "seed": seed,
                         "sample_index": sample_index, "difficulty": difficulty, "overrides": overrides,
                         "recorded_draws": ctx.recorded_draws(), "overrides_used": ctx.overrides_used()})
                    group.append(case)
                controls.append({"seed": seed, "sample_index": sample_index, "difficulty": difficulty,
                    "same_grid_for_default_and_sizes_1_and_5": len({p["input_sha256"] for p in group}) == 1,
                    "observed_blob_cells": [p["blob_cell_count"] for p in group],
                    "blob_size_override_used": ["blob_size" in p["overrides_used"] for p in group],
                    "authority_indices": [p["authority_index"] for p in group]})

    public_rows = [json.loads(line) for line in (OUT / "public-generate.jsonl").read_text().splitlines() if line]
    for row in public_rows:
        assert row["provenance"]["generator_sha256"] == digest
        for split in ("train", "test"):
            for pi, pair in enumerate(row[split]):
                sample = next(p["sample_index"] for p in row["sampling"]["accepted_pairs"]
                              if p["split"] == split and p["pair_index"] == pi)
                retain(pair["input"], {"kind": "public_generate", "split": split, "pair_index": pi,
                    "seed": row["seed"], "sample_index": sample, "difficulty": row["provenance"]["difficulty"],
                    "overrides": row["provenance"]["overrides"], "public_output": pair["output"]})

    assert len(inputs) <= 64
    declared = {name: [getattr(item, "__name__", str(item)) for item in getattr(gen, name, ())]
                for name in ("CANONICAL_SHORTCUTS", "LESSON_COMPETITORS")}
    rivals = [{"authority_index": i, "input_sha256": sha(grid),
        "observed_frame_translation_mirror": relocate(grid),
        "fixed_bottom_right_rival": relocate(grid, fixed_bottom_right=True)} for i, grid in enumerate(inputs)]
    write("input.json", inputs)
    write("rival.json", {"description": "Copy blob to equal-size bottom-right frame interior, ignoring observed frame position.",
         "declared_rivals": declared, "is_claimed_canonical_shortcut": False, "results": rivals})
    report = {"schema": "review-dded62bb9e3a-bounded-audit-v1", "task_id": TASK,
        "phase": "final_unchanged_audit_source", "generator_version": gen.VERSION,
        "generator_sha256": digest, "runtime_cwd": str(Path.cwd()), "resolved_root": str(root),
        "generator_path": str(path.relative_to(root)), "canonical_path": str(canonical_path(root).relative_to(root)),
        "AXES_blob_size": gen.AXES["blob_size"], "declared_rivals": declared,
        "canonical_pair_count": len(pairs), "direct_generation_calls": 48,
        "control_group_count": len(controls), "public_generation_pair_count": sum(len(r[s]) for r in public_rows for s in ("train", "test")),
        "unique_input_count": len(inputs), "control_groups": controls, "cases": cases}
    write("probe.json", report)
    print(json.dumps({k: report[k] for k in ("task_id", "generator_sha256", "canonical_pair_count", "direct_generation_calls", "control_group_count", "public_generation_pair_count", "unique_input_count")}))


def verify():
    root, path, digest, gen = source()
    report, authority, rivals = read("probe.json"), read("racket.json"), read("rival.json")
    assert report["generator_sha256"] == authority["generator_sha256"] == digest
    assert authority["rule_hash_matches_catalog"]
    rows = authority["results"]
    assert len(rows) == report["unique_input_count"] == len(rivals["results"])
    comparisons = []
    for actual, rival in zip(rows, rivals["results"], strict=True):
        assert actual["index"] == rival["authority_index"]
        assert actual["input_sha256"] == rival["input_sha256"]
        assert actual["valid_output"] and actual["error"] is None
        comparisons.append({"authority_index": actual["index"], "mirror_matches_racket": actual["output"] == rival["observed_frame_translation_mirror"],
            "fixed_bottom_right_matches_racket": actual["output"] == rival["fixed_bottom_right_rival"]})
    canonical = [c for c in report["cases"] if c["kind"] == "canonical"]
    generated = [c for c in report["cases"] if c["kind"] == "direct_public_hooks"]
    public = [c for c in report["cases"] if c["kind"] == "public_generate"]
    canonical_pass = sum(rows[c["authority_index"]]["output"] == c["canonical_output"] for c in canonical)
    public_pass = sum(rows[c["authority_index"]]["output"] == c["public_output"] for c in public)
    generated_unique = sorted({c["authority_index"] for c in generated + public})
    stats = {
        "self_check_passes": sum(not c["self_check"] for c in report["cases"]),
        "self_check_total_case_records": len(report["cases"]),
        "unique_self_check_inputs": len(rows),
        "independent_documented_domain_passes": sum(c["belongs_to_documented_rule_domain"] for c in report["cases"]),
        "canonical_labels_match_racket": [canonical_pass, len(canonical)],
        "public_generation_labels_match_racket": [public_pass, len(public)],
        "description_mirror_matches_racket": [sum(c["mirror_matches_racket"] for c in comparisons), len(rows)],
        "ignored_blob_size_controls": [sum(c["same_grid_for_default_and_sizes_1_and_5"] and not any(c["blob_size_override_used"]) for c in report["control_groups"]), report["control_group_count"]],
        "public_requested_size_5_mismatches": [sum(c["overrides"] == {"blob_size": 5} and c["blob_cell_count"] != 5 for c in public), len(public)],
        "public_requested_size_5_actual_sizes": [c["blob_cell_count"] for c in public],
        "fixed_corner_rival_canonical_matches": [sum(comparisons[c["authority_index"]]["fixed_bottom_right_matches_racket"] for c in canonical), len(canonical)],
        "fixed_corner_rival_generated_unique_matches": [sum(comparisons[i]["fixed_bottom_right_matches_racket"] for i in generated_unique), len(generated_unique)],
    }
    assert canonical_pass == len(canonical) and public_pass == len(public)
    assert all(c["mirror_matches_racket"] for c in comparisons)
    assert stats["ignored_blob_size_controls"] == [16, 16]
    assert stats["public_requested_size_5_mismatches"] == [4, 4]
    assert all(not c["self_check"] and c["belongs_to_documented_rule_domain"] for c in report["cases"])
    witness = next(c for c in public if c["sample_index"] == 0)
    idx = witness["authority_index"]
    finding = {"schema": "arcpuzzles-review-audit-counterexample-v1", "task_id": TASK,
        "finding_id": "A1", "classification": "reproduced exact-control defect",
        "generator_sha256": digest, "generator_version": gen.VERSION,
        "rule_hash": authority["executed_rule_hash"], "rule_text_sha256": authority["rule_text_sha256"],
        "seed": witness["seed"], "sample_index": witness["sample_index"], "difficulty": witness["difficulty"], "overrides": witness["overrides"],
        "input": rows[idx]["input"], "input_sha256": rows[idx]["input_sha256"],
        "actual_racket_output": rows[idx]["output"], "actual_racket_output_sha256": rows[idx]["output_sha256"],
        "rival_output": rivals["results"][idx]["fixed_bottom_right_rival"],
        "rival_relation_to_primary_finding": "This rival agrees on the generated witness; exact-control defect is requested size 5 versus observed size, not a label error.",
        "validator_findings": witness["self_check"], "documented_domain": inspect_grid(rows[idx]["input"]),
        "observed_blob_cell_count": witness["blob_cell_count"], "requested_blob_size": 5,
        "evidence": {"authority_index": idx, "apply": "checks/audit/dded62bb9e3a/racket.json",
            "public_generate": "checks/audit/dded62bb9e3a/public-generate.jsonl", "all_trials": "checks/audit/dded62bb9e3a/probe.json"},
        "authority_command": ["python3", "review.py", "run", "python3", "-m", "arcpuzzles", "apply", TASK, "--input", "../checks/audit/dded62bb9e3a/input.json", "--out", "../checks/audit/dded62bb9e3a/racket.json"],
        "command_cwd": "packet_root", "effective_runtime_cwd": str(Path.cwd()),
    }
    write("finding.json", finding)
    result = {"task_id": TASK, "phase": "final_unchanged_audit_source", "generator_sha256": digest,
        "rule_hash": authority["executed_rule_hash"], "rule_text_sha256": authority["rule_text_sha256"],
        "runtime_cwd": str(Path.cwd()), "seed_set": [0, 17], "sample_indices": [0, 1],
        "difficulty_set": [None, "easy", "medium", "hard"], "override_set": [{}, {"blob_size": 1}, {"blob_size": 5}],
        "public_seed": 17, "public_sample_indices": [0, 1, 2, 3], "public_overrides": {"blob_size": 5},
        "stats": stats, "comparisons": comparisons,
        "lesson_evaluation": {"demonstrations": 3, "query_count": 1, "assembly": "public generate: accepted sample indices 0,1,2 demonstrate; index 3 queries",
            "production_verdict": "unknown", "rotation_verdict": "unknown", "reason": "No executable lesson contract or declared rival suite; no lesson identifiability claim is made."},
        "verdict": "reproduced_exact_control_defect_and_existing_position_shortcut",
        "limitations": "Bounded audit, no full battery; positional rival is not canonical-compatible and is not claimed to fit every canonical pair."}
    write("verification.json", result)
    print(json.dumps({"task_id": TASK, "generator_sha256": digest, "stats": stats, "verdict": result["verdict"]}))


if __name__ == "__main__":
    if sys.argv[1:] == ["prepare"]:
        prepare()
    elif sys.argv[1:] == ["verify"]:
        verify()
    else:
        raise SystemExit("Usage: probe.py prepare|verify")
