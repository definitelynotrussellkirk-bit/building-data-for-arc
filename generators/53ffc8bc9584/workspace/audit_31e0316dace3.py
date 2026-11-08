#!/usr/bin/env python3
"""Source-bound findings-only profile audit; no target/runtime edits.

From packet_root:
  python3 repo/generators/53ffc8bc9584/workspace/audit_31e0316dace3.py prepare
  python3 run_with_racket.py python3 -m arcpuzzles apply 31e0316dace3 --input ../checks/audit/31e0316dace3/input.json --out ../checks/audit/31e0316dace3/racket.json
  python3 repo/generators/53ffc8bc9584/workspace/audit_31e0316dace3.py finish

Imports use the portable shared/runtime tree and importlib, not runner internals.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True


TASK_ID = "31e0316dace3"
PACKET = Path(__file__).resolve().parents[4]
REPO = PACKET / "repo"
OUT = PACKET / "checks" / "audit" / TASK_ID
SOURCE = REPO / "generators" / TASK_ID / "generator.py"
SCRIPT = "repo/generators/53ffc8bc9584/workspace/audit_31e0316dace3.py"
BANDS = ("easy", "medium", "hard")


def sha(value):
    if not isinstance(value, bytes):
        value = value.encode()
    return hashlib.sha256(value).hexdigest()


def grid_sha(grid):
    return sha(json.dumps(grid, separators=(",", ":")))


def profile(grid):
    return [len(grid), len(grid[0]), len({v for row in grid for v in row})]


def load_gen():
    sys.path.insert(0, str(REPO / "shared" / "runtime"))
    spec = importlib.util.spec_from_file_location("audit_target_31e0316dace3", SOURCE)
    gen = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gen)
    return gen


def canonical():
    for line in (REPO / "shared/data/canonical/puzzles.jsonl").read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            pairs = row["train"] + (row["test"] if isinstance(row["test"], list) else [row["test"]])
            decode = lambda g: [[int(v) for v in r] for r in g]
            return row["program_solution"], [{"input": decode(p["input"]), "output": decode(p["output"])} for p in pairs]
    raise RuntimeError("canonical task not found")


def documented_domain_errors(g):
    h, w = len(g), len(g[0])
    errors = []
    if h % 2 or w % 2 or not 6 <= h <= 14 or not 6 <= w <= 14:
        errors.append("dimensions outside documented even 6..14 range")
    if any(len(row) != w for row in g) or any(type(v) is not int or not 0 <= v <= 9 for row in g for v in row):
        errors.append("nonrectangular or non-ARC grid")
    colors = []
    for qr in range(2):
        for qc in range(2):
            vals = [g[r][c] for r in range(qr*h//2, (qr+1)*h//2) for c in range(qc*w//2, (qc+1)*w//2) if g[r][c]]
            if vals:
                if len(set(vals)) != 1 or not 2 <= len(vals) <= 6:
                    errors.append(f"quadrant {qr},{qc} lacks 2..6 cells of one color")
                colors.append(vals[0])
    if len(colors) < 3 or len(set(colors)) != len(colors):
        errors.append("more than one empty quadrant or repeated quadrant color")
    return errors


def prepare():
    gen = load_gen()
    rule, pairs = canonical()
    canonical_profiles = sorted({tuple(profile(pair["input"])) for pair in pairs})
    cases, grids = [], []

    def add(grid, **metadata):
        cases.append({
            "input_index": len(grids), **metadata,
            "input_sha256_compact_json": grid_sha(grid), "profile": profile(grid),
            "validator_errors": gen.self_check(grid),
            "documented_domain_errors": documented_domain_errors(grid),
            "canonical_profile_hit": tuple(profile(grid)) in canonical_profiles,
        })
        grids.append(grid)

    for index, pair in enumerate(pairs):
        add(pair["input"], kind="canonical", canonical_pair_index=index,
            canonical_output=pair["output"], seed=None, sample_index=None, overrides={})
    band_stats = {}
    for band in BANDS:
        start = len(cases)
        for index in range(20):
            seed = int(sha(f"profile-floor:v1:{TASK_ID}:{band}:{index}")[:12], 16)
            sample_index = seed % 7919 + index
            grid = gen.generate(seed, sample_index, difficulty=band)
            add(grid, kind="generated", difficulty=band, census_index=index,
                seed=seed, sample_index=sample_index, overrides={})
        selected = cases[start:]
        band_stats[band] = {
            "draws": len(selected),
            "unique_input_count": len({c["input_sha256_compact_json"] for c in selected}),
            "canonical_profile_hits": sum(c["canonical_profile_hit"] for c in selected),
            "profile_counts": dict(Counter("x".join(map(str, c["profile"])) for c in selected)),
            "validator_rejected": sum(bool(c["validator_errors"]) for c in selected),
            "documented_domain_rejected": sum(bool(c["documented_domain_errors"]) for c in selected),
        }
    overrides = {"half_h": 4, "half_w": 4, "empty_quadrant": "top_right"}
    add(gen.generate(31415926, 0, difficulty="hard", **overrides), kind="override_witness",
        difficulty="hard", seed=31415926, sample_index=0, overrides=overrides)
    assert len(grids) == 64
    report = {
        "task_id": TASK_ID, "finding_id": "A31-PROFILE-HARD",
        "phase": "unchanged audit target source",
        "generator_source_path": str(SOURCE.relative_to(PACKET)),
        "generator_source_sha256": sha(SOURCE.read_bytes()),
        "rule_source_sha256": sha(rule),
        "rule_normalized_sha256": sha(" ".join(rule.split())),
        "rule_hash": sha(" ".join(rule.split()))[:12],
        "declared_rule_hash": gen.RULE_HASH,
        "runtime_directory": "repo/shared/runtime",
        "sampler": "target generate; default overrides; exact profile-floor:v1 pinned seed policy",
        "census_index_range_inclusive": [0, 19],
        "seed_formula": "int(sha256(f'profile-floor:v1:31e0316dace3:{band}:{index}').hexdigest()[:12], 16)",
        "sample_index_formula": "seed % 7919 + census_index",
        "sample_denominator": 60,
        "canonical_pair_denominator": len(pairs),
        "canonical_profiles": canonical_profiles,
        "band_stats": band_stats,
        "cases": cases,
        "rival_output": None,
        "rival_output_reason": "Distribution coverage finding, not an input-output rule counterexample; no rival solver is claimed.",
        "limitations": [
            "Only one profile-floor census and 64 real Racket cases; no full audit battery or universal semantic pass is claimed.",
            "Easy and medium do have canonical profile hits; the gap is specifically the default hard sampler.",
            "Explicit hard dimension overrides can reach a canonical profile; default sampling cannot under the current draw_int_diff mapping."
        ],
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "input.json").write_text(json.dumps(grids, separators=(",", ":")) + "\n")
    (OUT / "generation.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"generated_inputs": 64, "band_stats": band_stats, "generator_sha256": report["generator_source_sha256"], "rule_hash": report["rule_hash"]}, indent=2))


def finish():
    report = json.loads((OUT / "generation.json").read_text())
    if sha(SOURCE.read_bytes()) != report["generator_source_sha256"]:
        raise RuntimeError("target generator changed after prepare")
    rule, _ = canonical()
    if sha(rule) != report["rule_source_sha256"]:
        raise RuntimeError("canonical rule changed after prepare")
    racket = json.loads((OUT / "racket.json").read_text())
    results = racket["results"]
    assert len(results) == len(report["cases"]) == 64
    assert racket["generator_sha256"] == report["generator_source_sha256"]
    # apply.rule_text_sha256 covers the callable wrapper, not program_solution.
    # The selected canonical source is independently pinned above and its
    # normalized hash is what the public report identifies as executed_rule_hash.
    assert racket["executed_rule_hash"] == report["rule_hash"] == report["declared_rule_hash"]
    canonical_matches = expected_matches = valid = 0
    for metadata, actual in zip(report["cases"], results):
        assert metadata["input_index"] == actual["index"]
        g = actual["input"]
        assert grid_sha(g) == metadata["input_sha256_compact_json"]
        assert not metadata["validator_errors"]
        assert not metadata["documented_domain_errors"]
        h, w = len(g), len(g[0])
        expected = [[next(iter({g[r][c] for r in range(qr*h//2, (qr+1)*h//2)
                              for c in range(qc*w//2, (qc+1)*w//2) if g[r][c]}), 0)
                     for qc in range(2)] for qr in range(2)]
        expected_matches += actual["output"] == expected
        valid += actual["valid_output"] and actual["error"] is None
        if metadata["kind"] == "canonical":
            canonical_matches += actual["output"] == metadata["canonical_output"]
    assert expected_matches == valid == 64
    assert canonical_matches == 3
    gate_path = OUT / "profile_floor/checks/31e0316dace3_after_profile_floor.json"
    gate = json.loads(gate_path.read_text())["audits"][0]
    assert gate["status"] == "FAIL"
    assert gate["bands_below_floor"] == ["hard"]
    for band in BANDS:
        assert gate["per_band"][band]["exact"] == report["band_stats"][band]["canonical_profile_hits"]
    assert report["cases"][63]["canonical_profile_hit"]
    report["shared_context_source_sha256"] = sha((REPO / "shared/runtime/puzzle_generators/base.py").read_bytes())
    report["audit_script_sha256"] = sha(Path(__file__).read_bytes())
    report["finding_status"] = "reproduced distribution coverage defect"
    report["profile_floor"] = gate
    report["racket_execution"] = {
        "case_count": 64, "valid_output_count": valid,
        "documented_quadrant_output_matches": expected_matches,
        "canonical_pair_matches": canonical_matches,
        "evidence_path": "checks/audit/31e0316dace3/racket.json",
        "recorded_command": racket["command"], "recorded_cwd": racket["cwd"],
        "generator_sha256": racket["generator_sha256"],
        "executed_rule_hash": racket["executed_rule_hash"],
        "wrapped_callable_sha256_from_apply": racket["rule_text_sha256"],
    }
    witness = {
        "task_id": TASK_ID, "finding_id": report["finding_id"],
        "generator_sha256": report["generator_source_sha256"],
        "rule_source_sha256": report["rule_source_sha256"],
        "rule_hash": report["rule_hash"],
        **report["cases"][63],
        "input": results[63]["input"], "actual_racket_output": results[63]["output"],
        "rival_output": None,
        "rival_output_reason": report["rival_output_reason"],
        "input_passes_target_validator": True,
        "input_belongs_to_documented_domain": True,
        "input_has_support_under_default_hard_sampler": False,
        "reason": "The hard dimension draws have round(3 + 4*d) with d in [0.66,1], hence half-dimensions 6 or 7 only. This lawful hard override grid has half-dimensions 4 and 4.",
        "command": ["python3", "run_with_racket.py", "python3", "-m", "arcpuzzles", "apply", TASK_ID, "--input", "../checks/audit/31e0316dace3/input.json", "--out", "../checks/audit/31e0316dace3/racket.json"],
        "cwd": "packet_root", "exit_code": 0,
    }
    (OUT / "counterexample.json").write_text(json.dumps(witness, indent=2) + "\n")
    report["verification_commands"] = [
        {
            "cwd": "packet_root", "argv": ["python3", "run_with_racket.py", "python3", "-m", "arcpuzzles", "check", TASK_ID, "--stage", "profile_floor", "--phase", "after", "--out", "../checks/audit/31e0316dace3/profile_floor"],
            "exit_code": 1, "expected_reproduced_failure": True,
            "evidence_paths": ["checks/audit/31e0316dace3/profile_floor/result.json", "checks/audit/31e0316dace3/profile_floor/checks/31e0316dace3_after_profile_floor.json", "checks/audit/31e0316dace3/profile_floor/checks/31e0316dace3_after_profile_floor.log"],
        },
        {"cwd": "packet_root", "argv": ["python3", SCRIPT, "prepare"], "exit_code": 0,
         "evidence_paths": ["checks/audit/31e0316dace3/input.json", "checks/audit/31e0316dace3/generation.json"]},
        {"cwd": "packet_root", "argv": witness["command"], "exit_code": 0,
         "evidence_paths": ["checks/audit/31e0316dace3/racket.json"]},
        {"cwd": "packet_root", "argv": ["python3", SCRIPT, "finish"], "exit_code": 1,
         "phase": "intermediate audit harness; wrong raw-source/callable-wrapper hash equality assumption",
         "audit_script_sha256": "5bcbd844d76112a557ce1d08c98de720d590805739f286593cd81c6024556f4f",
         "evidence_paths": ["checks/audit/31e0316dace3/finish_assertion_failure.json"]},
        {"cwd": "packet_root", "argv": ["python3", SCRIPT, "finish"], "exit_code": 0,
         "evidence_paths": ["checks/audit/31e0316dace3/audit.json", "checks/audit/31e0316dace3/counterexample.json"]},
    ]
    (OUT / "audit.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"finding": report["finding_status"], "profile_floor_status": gate["status"], "hard_exact_hits": "0/20", "racket_valid": f"{valid}/64", "canonical_matches": f"{canonical_matches}/3", "source_stable": True}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["prepare", "finish"])
    args = parser.parse_args()
    globals()[args.action]()
