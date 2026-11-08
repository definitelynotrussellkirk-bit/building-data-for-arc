#!/usr/bin/env python3
"""Bounded findings-only audit; reference labels use the public apply CLI.

Run from packet_root: python3 checks/audit/29a832606002/probe.py
Use --prepare-only to recreate inputs without running Racket. The public
reference command refuses to overwrite an existing racket.json; preserve it.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

sys.dont_write_bytecode = True
TASK = "29a832606002"
HERE = Path(__file__).resolve().parent
PACKET = HERE.parents[2]
REPO = PACKET / "repo"
SOURCE = REPO / "generators" / TASK / "generator.py"
sys.path.insert(0, str(REPO / "shared/runtime"))
from puzzle_generators.base import set_ctx_observer
from reviewer_support import canonical_pairs


def digest(value):
    return hashlib.sha256(value).hexdigest()


def grid_hash(grid):
    return digest(json.dumps(grid, separators=(",", ":")).encode())


def save(name, obj):
    (HERE / name).write_text(json.dumps(obj, indent=2) + "\n")


def rotate_cw(grid):
    return [list(row) for row in zip(*grid[::-1])]


def rotation_gallery(grid):
    cw = rotate_cw(grid)
    half = rotate_cw(cw)
    ccw = rotate_cw(half)
    return [a + b for a, b in zip(grid, cw)] + [a + b for a, b in zip(ccw, half)]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prepare-only", action="store_true")
    args = parser.parse_args()
    spec = importlib.util.spec_from_file_location("audit_target_29a832606002", SOURCE)
    generator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(generator)
    ledger = REPO / "shared/data/canonical/puzzles.jsonl"
    with ledger.open() as handle:
        selected = [json.loads(line) for line in handle if json.loads(line).get("task_id") == TASK]
    assert len(selected) == 1
    identities = {
        "task_id": TASK,
        "generator_version": generator.VERSION,
        "generator_path": "repo/generators/29a832606002/generator.py",
        "generator_sha256": digest(SOURCE.read_bytes()),
        "canonical_ledger_sha256": digest(ledger.read_bytes()),
        "canonical_rule_text_sha256": digest(selected[0]["program_solution"].encode()),
        "phase": "audit_of_unchanged_source",
    }
    inputs, cases = [], []

    def add_case(name, grid, *, replay=None, expected=None, domain, meta=None):
        index = len(inputs)
        inputs.append(grid)
        cases.append({
            "name": name, "input_index": index, "input_sha256": grid_hash(grid),
            "replay": replay,
            "validator_errors": generator.self_check(grid, meta=meta),
            "documented_domain": domain,
            "expected_output_sha256": grid_hash(expected if expected is not None else rotation_gallery(grid)),
            "expected_basis": "canonical recorded pair" if expected is not None else "independent Python TL=input, TR=CW, BL=CCW, BR=180 rotation gallery",
            "rival_output": None,
            "rival_status": "not a shortcut claim; no rival result asserted",
        })
        return index

    canonical = canonical_pairs(TASK, root=REPO)
    for pair in canonical:
        assert rotation_gallery(pair["input"]) == pair["output"]
        add_case(f"canonical/{pair['split']}/{pair['pair_index']}", pair["input"],
                 expected=pair["output"], domain="canonical square input", replay={
                     "variant": pair["variant"], "split": pair["split"], "pair_index": pair["pair_index"]})

    for band in ("easy", "medium", "hard"):
        for seed in (0, 1, 17):
            for sample_index in (0, 1):
                grid = generator.generate(seed, sample_index, difficulty=band)
                add_case(f"default/{band}/{seed}/{sample_index}", grid,
                         replay={"seed": seed, "sample_index": sample_index, "difficulty": band, "overrides": {}},
                         domain="default-generated normal instance")

    background_trials = []
    for bgc in range(10):
        overrides = {"grid_n": 3, "palette_size": 3, "texture": "plus",
                     "bg_density": 0.95, "noise_overlay": 0.0, "bgc": bgc}
        seen = []
        set_ctx_observer(seen.append)
        try:
            grid = generator.generate(17, 0, difficulty="easy", **overrides)
        finally:
            set_ctx_observer(None)
        background_trials.append({
            "seed": 17, "sample_index": 0, "difficulty": "easy", "overrides": overrides,
            "input": grid, "input_sha256": grid_hash(grid),
            "validator_errors": generator.self_check(grid),
            "recorded_palette": seen[0].recorded_draws().get("palette"),
            "recorded_bgc": seen[0].recorded_draws().get("bgc"),
            "bgc_consumed": "bgc" in seen[0].overrides_used(),
        })
    background_index = add_case("bgc/witness", background_trials[0]["input"],
        replay={key: background_trials[0][key] for key in ("seed", "sample_index", "difficulty", "overrides")},
        domain="normal output from documented in-range overrides; same grid for bgc 0..9")
    for trial in background_trials:
        trial["racket_input_index"] = background_index

    boundary_specs = [
        (None, {"grid_n": 1}),
        (None, {"palette_size": 1}),
        (None, {"palette_size": 8}),
        ("easy", {"palette_size": 8}),
        ("hard", {"palette_size": 8}),
        ("easy", {"grid_n": 15}),
        ("hard", {"grid_n": 3}),
    ]
    boundary_trials = []
    for band, overrides in boundary_specs:
        row = {"seed": 0, "sample_index": 0, "difficulty": band, "overrides": overrides,
               "declared_axis_ranges": {key: generator.AXES[key] for key in overrides}}
        try:
            grid = generator.generate(0, 0, difficulty=band, **overrides)
            row.update({"input": grid, "exception": None, "validator_errors": generator.self_check(grid)})
        except Exception as error:
            row.update({"input": None, "exception": {"type": type(error).__name__, "message": str(error)},
                        "validator_errors": None, "racket_output": None,
                        "status": "generation rejected before an input exists"})
        boundary_trials.append(row)

    sym_overrides = {"grid_n": 3, "palette_size": 3, "texture": "frame",
                     "bg_density": 0.0, "noise_overlay": 0.0, "asymmetry_force": False}
    sym_grid = generator.generate(0, 0, difficulty="easy", **sym_overrides)
    symmetry_index = add_case("asymmetry_force/false", sym_grid,
        replay={"seed": 0, "sample_index": 0, "difficulty": "easy", "overrides": sym_overrides},
        meta=sym_overrides,
        domain="documented overrides; valid square with two colors, but conflicts with self_check's unconditional symmetry exclusion")

    one_index = add_case("handmade/n1", [[7]],
        domain="square rule domain and AXES grid_n range; outside normal >=2-color invariant; not generator-emitted")

    declarations = {name: list(getattr(generator, name, ())) for name in ("CANONICAL_SHORTCUTS", "LESSON_COMPETITORS")}
    public_command = ["python3", "run_with_racket.py", "python3", "-m", "arcpuzzles", "apply", TASK,
                      "--input", f"../checks/audit/{TASK}/input.json", "--out", f"../checks/audit/{TASK}/racket.json"]
    report = {
        "schema": "bounded-generator-audit-v1", **identities,
        "probe_sha256": digest(Path(__file__).read_bytes()),
        "declared_rivals": declarations,
        "canonical_pairs": len(canonical),
        "default_sample_schedule": {"seeds": [0, 1, 17], "sample_indices": [0, 1], "bands": ["easy", "medium", "hard"], "count": 18},
        "cases": cases,
        "background_trials": background_trials,
        "boundary_trials": boundary_trials,
        "symmetry_case_index": symmetry_index,
        "handmade_one_cell_index": one_index,
        "reference_command": {"cwd": "packet_root", "effective_cwd": "repo", "argv": public_command, "exit_code": None,
                              "evidence_paths": [f"checks/audit/{TASK}/input.json", f"checks/audit/{TASK}/racket.json", f"checks/audit/{TASK}/racket-command.log"]},
        "limits": ["No full battery or production lesson census.", "No exhaustive size, texture, or seed coverage.",
                   "No claim of canonical-consistent shortcut or wrong reference label.",
                   "CANONICAL_SHORTCUTS and LESSON_COMPETITORS absent; no rival list was copied into this probe."]}
    (HERE / "input.json").write_text(json.dumps(inputs, separators=(",", ":")) + "\n")
    save("report.json", report)
    if args.prepare_only:
        print(json.dumps({"prepared_inputs": len(inputs), **identities}))
        return 0
    result = subprocess.run(public_command, cwd=PACKET, env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
                            text=True, capture_output=True, timeout=180)
    (HERE / "racket-command.log").write_text(result.stdout + result.stderr)
    report["reference_command"]["exit_code"] = result.returncode
    if result.returncode:
        save("report.json", report)
        print(result.stderr, file=sys.stderr)
        return result.returncode
    applied = json.loads((HERE / "racket.json").read_text())
    report["reference_identity"] = {key: applied[key] for key in
        ("executed_rule_hash", "catalog_rule_hash", "rule_text_sha256", "rule_hash_matches_catalog", "generator_sha256")}
    assert applied["generator_sha256"] == identities["generator_sha256"]
    for case, actual in zip(cases, applied["results"], strict=True):
        case["actual_output_sha256"] = grid_hash(actual["output"])
        case["actual_output_matches_expected"] = case["actual_output_sha256"] == case["expected_output_sha256"]
        case["actual_racket_output_path"] = f"checks/audit/{TASK}/racket.json#/results/{case['input_index']}/output"
    default_cases = [case for case in cases if case["name"].startswith("default/")]
    report["counts"] = {
        "racket_inputs": len(cases), "racket_unique_inputs": len({case["input_sha256"] for case in cases}),
        "racket_expected_matches": sum(case["actual_output_matches_expected"] for case in cases),
        "default_inputs": len(default_cases), "default_unique_inputs": len({case["input_sha256"] for case in default_cases}),
        "default_validator_passes": sum(not case["validator_errors"] for case in default_cases),
        "bgc_trials": len(background_trials), "bgc_unique_inputs": len({case["input_sha256"] for case in background_trials}),
        "bgc_consumed": sum(trial["bgc_consumed"] for trial in background_trials),
        "boundary_trials": len(boundary_trials), "boundary_exceptions": sum(trial["exception"] is not None for trial in boundary_trials),
    }
    save("report.json", report)
    print(json.dumps({"counts": report["counts"], "reference_identity": report["reference_identity"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
