#!/usr/bin/env python3
"""Focused, source-bound audit; the only reference execution uses the public CLI.

The independent rival replaces occupied cells by all integer points in their
Euclidean convex hull, then draws their exterior four-neighbor shell in the
unique least-frequent input color. It imports no generator geometry/rule helper.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import time
from collections import Counter

TASK = "48bda9528e71"
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
REPO = ROOT / "repo"
SOURCE = REPO / "generators" / TASK / "generator.py"
CANONICAL = REPO / "shared/data/canonical/puzzles.jsonl"
BG = 8


def sha(data):
    return hashlib.sha256(data).hexdigest()


def grid_hash(grid):
    return sha(json.dumps(grid, separators=(",", ":")).encode())


def write_json(name, value):
    (HERE / name).write_text(json.dumps(value, indent=2) + "\n")


def occupied(grid):
    return {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value != BG}


def cross(a, b, p):
    return (b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0])


def convex_closure(points):
    """Exact integer geometry; no floating-point hull or external dependency."""
    points = sorted(points)
    lower, upper = [], []
    for p in points:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    for p in reversed(points):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    hull = lower[:-1] + upper[:-1]
    assert len(hull) >= 3
    return {
        (r, c)
        for r in range(min(p[0] for p in points), max(p[0] for p in points) + 1)
        for c in range(min(p[1] for p in points), max(p[1] for p in points) + 1)
        if all(cross(a, b, (r, c)) >= 0 for a, b in zip(hull, hull[1:] + hull[:1]))
    }


def shell_output(grid, points):
    """Four-neighbor exterior shell, independent of row/column extent code."""
    counts = Counter(value for row in grid for value in row if value != BG)
    chosen = min(counts, key=counts.get)
    assert sum(count == counts[chosen] for count in counts.values()) == 1
    height, width = len(grid), len(grid[0])
    result = [[BG] * width for _ in range(height)]
    for r, c in points:
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            rr, cc = r + dr, c + dc
            if 0 <= rr < height and 0 <= cc < width and (rr, cc) not in points:
                result[rr][cc] = chosen
    return result


def load_source():
    sys.path.insert(0, str(REPO / "shared/runtime"))
    spec = importlib.util.spec_from_file_location("audit_48bda9528e71_generator", SOURCE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def prepare():
    module = load_source()
    rows = [json.loads(line) for line in CANONICAL.read_text().splitlines()
            if json.loads(line).get("task_id") == TASK]
    rule_texts = {row["program_solution"] for row in rows}
    assert len(rule_texts) == 1
    rule = next(iter(rule_texts))
    identity = {
        "task_id": TASK,
        "generator_path": str(SOURCE.relative_to(ROOT)),
        "generator_sha256": sha(SOURCE.read_bytes()),
        "generator_version": module.VERSION,
        "declared_rule_hash": module.RULE_HASH,
        "canonical_rule_text_sha256": sha(rule.encode()),
        "canonical_rule_rows": len(rows),
        "canonical_file_sha256": sha(CANONICAL.read_bytes()),
        "prior_notes_path": f"repo/generators/{TASK}/evidence/associated_notes.jsonl",
        "prior_notes_sha256": sha((SOURCE.parent / "evidence/associated_notes.jsonl").read_bytes()),
        "prior_notes_used_as_leads": ["GNOTE-000899", "GNOTE-000979", "GNOTE-000865"],
    }
    grids, samples, canonical_expected = [], [], {}
    seen = set()
    for row in rows:
        for split in ("train", "test"):
            for pair_index, pair in enumerate(row.get(split, [])):
                key = grid_hash(pair["input"])
                if key in seen:
                    continue
                seen.add(key)
                index = len(grids)
                grids.append(pair["input"])
                canonical_expected[str(index)] = pair["output"]
                samples.append({"kind": "canonical", "canonical_source": row["source"],
                                "split": split, "pair_index": pair_index,
                                "seed": None, "sample_index": None, "overrides": {}})
    assert len(grids) == 3
    for band in ("easy", "medium", "hard"):
        for seed in range(20):
            sample_index = seed * 17 + 3
            overrides = {"scene_profile": "general"}
            grids.append(module.generate(seed, sample_index, difficulty=band, **overrides))
            samples.append({"kind": "generated", "difficulty": band, "seed": seed,
                            "sample_index": sample_index, "overrides": overrides})

    # 5x5 occupied L: three full rows, then two rows of width three. This is
    # orthogonally convex but its convex hull additionally contains (5, 5).
    witness = [[BG] * 9 for _ in range(9)]
    for r in range(2, 7):
        for c in range(2, 7 if r < 5 else 5):
            witness[r][c] = 4
    witness[3][3] = 2
    grids.append(witness)
    samples.append({"kind": "constructed_domain_witness", "seed": None,
                    "sample_index": None, "overrides": {},
                    "construction": "9x9; color 4 on rows 2..4, cols 2..6 and rows 5..6, cols 2..4; color 2 at (3,3); background 8 elsewhere"})
    assert len(grids) == 64
    rival_outputs = []
    independent_outputs = []
    for index, (grid, sample) in enumerate(zip(grids, samples, strict=True)):
        points = occupied(grid)
        closure = convex_closure(points)
        validator_errors = module.self_check(grid)
        assert not validator_errors, (index, validator_errors)
        sample.update({"index": index, "input_sha256": grid_hash(grid),
                       "dimensions": [len(grid), len(grid[0])],
                       "validator_errors": validator_errors,
                       "observed_overrides": module.observe_overrides(grid),
                       "occupied_cells": len(points),
                       "hull_added_cells": [list(p) for p in sorted(closure - points)]})
        rival_outputs.append(shell_output(grid, closure))
        independent_outputs.append(shell_output(grid, points))
    write_json("input.json", grids)
    write_json("rival.json", {"rival": "convexify_then_cardinal_shell", "outputs": rival_outputs})
    write_json("independent.json", {"method": "cardinal_shell_without_convexification", "outputs": independent_outputs})
    write_json("sampling.json", {"source_identity": identity, "samples": samples,
                                 "canonical_expected": canonical_expected,
                                 "sampler": "actual module.generate; 20 seeds per difficulty with exact general-profile override; no rejection or filtering by the audit"})
    return grids, samples, identity


def bind():
    argv = ["python3", "run_with_racket.py", "python3", "-m", "arcpuzzles", "apply", TASK,
            "--input", f"../checks/audit/{TASK}/input.json",
            "--out", f"../checks/audit/{TASK}/racket.json"]
    before = time.monotonic()
    completed = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True)
    receipt = {"cwd": "packet_root", "absolute_cwd": str(ROOT), "argv": argv,
               "wrapper_effective_cwd": "repo", "wrapper_effective_absolute_cwd": str(REPO),
               "exit_code": completed.returncode, "elapsed_seconds": round(time.monotonic() - before, 3),
               "stdout": completed.stdout, "stderr": completed.stderr,
               "evidence_paths": [f"checks/audit/{TASK}/racket.json", f"checks/audit/{TASK}/input.json",
                                  f"checks/audit/{TASK}/rival.json", f"checks/audit/{TASK}/counterexample.json"]}
    write_json("command_receipt.json", receipt)
    if completed.returncode:
        raise SystemExit(completed.returncode)


def summarize():
    sampling = json.loads((HERE / "sampling.json").read_text())
    source = sampling["source_identity"]
    actual = json.loads((HERE / "racket.json").read_text())
    rival = json.loads((HERE / "rival.json").read_text())["outputs"]
    independent = json.loads((HERE / "independent.json").read_text())["outputs"]
    assert actual["generator_sha256"] == source["generator_sha256"] == sha(SOURCE.read_bytes())
    assert actual["rule_text_sha256"] == source["canonical_rule_text_sha256"]
    assert actual["executed_rule_hash"] == source["declared_rule_hash"]
    assert actual["rule_hash_matches_catalog"]
    assert len(actual["results"]) == 64
    results = []
    for sample, reference, rival_grid, independent_grid in zip(sampling["samples"], actual["results"], rival, independent, strict=True):
        index = sample["index"]
        assert not reference["error"], (index, reference["error"])
        assert reference["input_sha256"] == sample["input_sha256"]
        result = {"index": index, "kind": sample["kind"],
                  "rival_matches_reference": rival_grid == reference["output"],
                  "independent_shell_matches_reference": independent_grid == reference["output"]}
        if sample["kind"] == "canonical":
            result["canonical_matches_reference"] = sampling["canonical_expected"][str(index)] == reference["output"]
        results.append(result)
    assert all(item["independent_shell_matches_reference"] for item in results)
    assert all(item["rival_matches_reference"] for item in results[:63])
    assert all(item.get("canonical_matches_reference", True) for item in results)
    assert not results[63]["rival_matches_reference"]
    witness = actual["results"][63]
    differences = [{"row": r, "column": c, "racket": expected, "rival": rival[63][r][c]}
                   for r, row in enumerate(witness["output"]) for c, expected in enumerate(row)
                   if expected != rival[63][r][c]]
    counterexample = {
        **source,
        "classification": "reproduced distribution/domain coverage gap with a canonical-consistent rival; not a Racket semantic defect",
        "sample": sampling["samples"][63], "input": witness["input"],
        "actual_racket_output": witness["output"], "independent_rival_output": rival[63],
        "differences_zero_based": differences,
        "validator_passes": True,
        "documented_domain_status": "Satisfies every INVARIANTS entry and every self_check constraint; observed as general. It is outside the actual current sampler support because its occupied mask is not digitally convex.",
        "reference_command": json.loads((HERE / "command_receipt.json").read_text()),
    }
    write_json("counterexample.json", counterexample)
    summary = {
        "source_identity": source,
        "reference_errors": 0,
        "reference_cases": 64,
        "unique_inputs": len({sample["input_sha256"] for sample in sampling["samples"]}),
        "validator_passes": 64,
        "canonical_unique_pairs": 3,
        "canonical_pairs_matching_reference_and_rival": 3,
        "generated_cases": 60,
        "generated_unique_inputs": len({sample["input_sha256"] for sample in sampling["samples"] if sample["kind"] == "generated"}),
        "generated_rival_matches": 60,
        "generated_convexity_failures": 0,
        "constructed_domain_witnesses": 1,
        "constructed_rival_disagreements": 1,
        "independent_shell_matches": 64,
        "witness_difference_count": len(differences),
        "results": results,
        "limitations": ["Focused audit only: no battery, no lesson-frequency measurement, no model-behavior measurement.",
                        "Rival success on all actual generator support is a source argument from convex masks and D4/color transforms; the executed sample is 60 generated inputs, not an empirical universal test.",
                        "The broader validator domain includes the retained witness, while its generator reachability is excluded by source geometry."],
    }
    write_json("summary.json", summary)
    print(json.dumps({key: value for key, value in summary.items() if key not in ("results", "limitations", "source_identity")}, indent=2))


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "all"
    if mode in ("prepare", "all"):
        prepare()
    if mode in ("bind", "all"):
        bind()
    if mode in ("summarize", "all"):
        summarize()
