"""Findings-only audit: a connected-object shortcut in fa3550d200a0.

Run through the packet's run_with_racket.py wrapper. Reference labels are
obtained separately through the public `arcpuzzles apply` command.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2] / "repo"
TASK = "fa3550d200a0"
GENERATOR = ROOT / "generators" / TASK / "generator.py"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def json_hash(value):
    return sha(json.dumps(value, separators=(",", ":")).encode())


def load_generator():
    spec = importlib.util.spec_from_file_location("audit_fa3550d200a0", GENERATOR)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def window_rival(grid):
    """Copy each matched marker's local 3x3; never trace connected objects."""
    counts = Counter(value for row in grid for value in row if value)
    canvas = max(counts, key=counts.get)
    positions = [(r, c) for r, row in enumerate(grid)
                 for c, value in enumerate(row) if value == canvas]
    top, bottom = min(r for r, _ in positions), max(r for r, _ in positions)
    left, right = min(c for _, c in positions), max(c for _, c in positions)
    output = [row[left:right + 1] for row in grid[top:bottom + 1]]
    anchors = {grid[r][c]: (r - top, c - left)
               for r in range(top, bottom + 1)
               for c in range(left, right + 1)
               if grid[r][c] not in (0, 2, canvas)}
    for r, row in enumerate(grid):
        for c, marker in enumerate(row):
            if top <= r <= bottom and left <= c <= right:
                continue
            if marker not in anchors:
                continue
            ar, ac = anchors[marker]
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    rr, cc = r + dr, c + dc
                    nr, nc = ar + dr, ac + dc
                    if (0 <= rr < len(grid) and 0 <= cc < len(row)
                            and grid[rr][cc] != 0
                            and 0 <= nr < len(output)
                            and 0 <= nc < len(output[0])):
                        output[nr][nc] = grid[rr][cc]
    return output


def witness():
    grid = [[0] * 24 for _ in range(20)]
    for r in range(4, 10):
        for c in range(1, 7):
            grid[r][c] = 1
    grid[6][3] = 3
    grid[8][5] = 4
    # Three-cell horizontal piece, marker at an endpoint: distance two is needed.
    grid[2][12], grid[2][13], grid[2][14] = 3, 2, 2
    # An ordinary matched piece maintains the documented two-piece minimum.
    grid[7][12], grid[8][12], grid[9][12] = 2, 4, 2
    return grid


def prepare():
    gen = load_generator()
    cases = []

    def add(case_id, grid, **meta):
        errors = gen.self_check(grid)
        cases.append({
            "case_id": case_id, "input": grid,
            "input_sha256_compact_json": json_hash(grid),
            "validator_errors": errors, "validator_pass": errors == [],
            "observed_overrides": gen.observe_overrides(grid) if not errors else None,
            "rival_output": window_rival(grid), **meta,
        })

    add("radius_two_witness", witness(), kind="handmade", seed=None,
        sample_index=None, overrides=None,
        domain_status={
            "validator_accepted": True,
            "declared_invariants_satisfied": True,
            "all_observed_axes_within_declared_ranges": True,
            "actual_generator_support": False,
            "reason": "The 3-cell marker-endpoint piece reaches offset (0,2); every transformed _BASE_SHAPES cell has Chebyshev radius <=1. The witness uses no clipping, markerless object, duplicate marker, multi-special piece, or unmatched canvas marker.",
            "claim_limit": "This is a canonical-compatible curriculum shortcut/domain-extension question, not a mismatch on an emitted generated input.",
        })

    canonical_programs = []
    for line_number, line in enumerate((ROOT / "shared/data/canonical/puzzles.jsonl").open(), 1):
        row = json.loads(line)
        if row.get("task_id") != TASK:
            continue
        canonical_programs.append({"line": line_number,
                                   "exact_program_text_sha256": sha(row["program_solution"].encode())})
        for split in ("train", "test"):
            for pair_index, pair in enumerate(row.get(split, [])):
                add(f"canonical_{line_number}_{split}_{pair_index}", pair["input"],
                    kind="canonical", canonical_line=line_number, split=split,
                    pair_index=pair_index, official_output=pair["output"],
                    seed=None, sample_index=None, overrides=None)

    for seed, difficulty in enumerate((None, "easy", "medium", "hard")):
        for index in range(8):
            add(f"generated_{seed}_{index}", gen.generate(seed, index, difficulty=difficulty),
                kind="generated", seed=seed, sample_index=index, difficulty=difficulty,
                overrides={})

    for index in range(16):
        overrides = {
            "grid_h": 30 if index & 1 else 20,
            "grid_w": 30 if index & 2 else 24,
            "rect_h": 12 if index & 4 else 6,
            "rect_w": 12 if index & 8 else 6,
            "piece_count": 5 if index & 1 else 2,
            "decoy_count": 1 if index & 2 else 0,
            "canvas_side": "right" if index & 4 else "left",
            "palette_kind": gen.PALETTE_KINDS[index % 4],
        }
        grid = gen.generate(90210, index, difficulty="hard", **overrides)
        add(f"override_{index}", grid, kind="override", seed=90210,
            sample_index=index, difficulty="hard", overrides=overrides)
        assert cases[-1]["observed_overrides"] == overrides

    proof = []
    for shape_index, shape in enumerate(gen._BASE_SHAPES):
        for turn in range(4):
            for reflect in (False, True):
                cells = gen._transform_shape(shape, turn, reflect)
                radius = max(max(abs(r), abs(c)) for r, c in cells)
                proof.append({"shape_index": shape_index, "turn": turn,
                              "reflect": reflect, "radius": radius})
                assert radius == 1

    metadata = {
        "task_id": TASK,
        "generator_version": gen.VERSION,
        "generator_sha256": sha(GENERATOR.read_bytes()),
        "declared_rule_hash": gen.RULE_HASH,
        "canonical_programs": canonical_programs,
        "probe_sha256": sha(Path(__file__).read_bytes()),
        "rival": "copy_matching_marker_centered_3x3",
        "rival_description": "Find the modal nonzero canvas rectangle, then copy nonzero cells in a 3x3 window centered on each outside marker with a matching inside color. Do not trace connected components.",
        "declared_canonical_shortcuts": list(getattr(gen, "CANONICAL_SHORTCUTS", {})),
        "declared_lesson_competitors": list(getattr(gen, "LESSON_COMPETITORS", {})),
        "finite_shape_transform_proof": proof,
        "case_count": len(cases),
        "unique_input_count": len({case["input_sha256_compact_json"] for case in cases}),
        "cases": cases,
    }
    (HERE / "input.json").write_text(json.dumps([case["input"] for case in cases]) + "\n")
    (HERE / "prepared.json").write_text(json.dumps(metadata, indent=2) + "\n")
    print(json.dumps({"case_count": len(cases), "unique_input_count": metadata["unique_input_count"],
                      "validator_pass": sum(case["validator_pass"] for case in cases),
                      "generator_sha256": metadata["generator_sha256"]}))


def finalize():
    prepared = json.loads((HERE / "prepared.json").read_text())
    receipt = json.loads((HERE / "racket.json").read_text())
    print(json.dumps({"receipt_keys": list(receipt), "first_result_keys": list(receipt["results"][0])}))
    assert prepared["generator_sha256"] == sha(GENERATOR.read_bytes())
    assert receipt["generator_sha256"] == prepared["generator_sha256"]
    assert receipt["rule_hash_matches_catalog"] is True
    assert len(receipt["results"]) == len(prepared["cases"])
    results = []
    for case, actual in zip(prepared["cases"], receipt["results"]):
        assert actual["error"] is None
        output = actual["output"]
        difference = [{"row": r, "col": c, "racket": value,
                       "rival": case["rival_output"][r][c]}
                      for r, row in enumerate(output) for c, value in enumerate(row)
                      if value != case["rival_output"][r][c]]
        results.append({"case_id": case["case_id"], "kind": case["kind"],
                        "validator_pass": case["validator_pass"],
                        "rival_matches_racket": not difference,
                        "racket_matches_official": output == case["official_output"] if "official_output" in case else None,
                        "different_cells": difference})
    witness_case = prepared["cases"][0]
    witness_receipt = receipt["results"][0]
    counterexample = {key: value for key, value in prepared.items()
                      if key not in ("cases", "finite_shape_transform_proof")}
    counterexample.update(witness_case)
    counterexample["actual_racket_output"] = witness_receipt["output"]
    counterexample["racket_identity"] = {key: value for key, value in receipt.items()
                                           if key not in ("results",)}
    counterexample["racket_result"] = witness_receipt
    counterexample["different_cells"] = results[0]["different_cells"]
    counterexample["authority_command"] = {
        "cwd": "packet_root",
        "effective_payload_cwd": "repo",
        "argv": ["python3", "run_with_racket.py", "python3", "-m", "arcpuzzles", "apply", TASK,
                 "--input", "../checks/audit/fa3550d200a0/input.json",
                 "--out", "../checks/audit/fa3550d200a0/racket.json"],
    }
    groups = {}
    for kind in ("handmade", "canonical", "generated", "override"):
        selected = [r for r in results if r["kind"] == kind]
        cases = [c for c in prepared["cases"] if c["kind"] == kind]
        groups[kind] = {
            "count": len(selected),
            "unique_input_count": len({case["input_sha256_compact_json"] for case in cases}),
            "validator_pass": sum(r["validator_pass"] for r in selected),
            "rival_matches_racket": sum(r["rival_matches_racket"] for r in selected),
            "racket_matches_official": sum(r["racket_matches_official"] is True for r in selected),
        }
    report = {"task_id": TASK, "generator_sha256": prepared["generator_sha256"],
              "catalog_rule_hash": receipt["catalog_rule_hash"],
              "executed_rule_hash": receipt["executed_rule_hash"],
              "rule_hash_matches_catalog": receipt["rule_hash_matches_catalog"],
              "count_basis": "Final assigned target bytes, unchanged. Eight canonical appearances represent four unique inputs. Generation uses seeds 0..3 × sample indices 0..7 and seed 90210 × override indices 0..15 as recorded in prepared.json.",
              "groups": groups, "results": results,
              "shape_transform_bound": {"checked": len(prepared["finite_shape_transform_proof"]),
                                          "radius_one": sum(row["radius"] == 1 for row in prepared["finite_shape_transform_proof"])},
              "lesson_claim": "Since the rival agrees pointwise on the complete generated shape support, no generated lesson, cyclic window, or query rotation can reject it. This is a source argument, not a measured lesson count.",
              "limitations": ["No full battery run; this is a focused findings-only audit.",
                              "No emitted-input labeling defect is claimed.",
                              "The witness is outside actual sampling support but passes self_check and declared semantic invariants; extending support beyond radius one requires a maintainer domain decision."]}
    (HERE / "counterexample.json").write_text(json.dumps(counterexample, indent=2) + "\n")
    (HERE / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"groups": groups, "witness_differences": results[0]["different_cells"]}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=("prepare", "finalize"))
    args = parser.parse_args()
    (prepare if args.phase == "prepare" else finalize)()
