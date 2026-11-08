#!/usr/bin/env python3
"""Reproduce the findings-only palette-control audit of 58f520283ae2.

Run from packet_root. Imports the unmodified target through shared/runtime and
uses only the supported packet CLI to obtain reference Racket output.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

sys.dont_write_bytecode = True
PACKET = Path(__file__).resolve().parents[4]
REPO = PACKET / "repo"
TASK_ID = "58f520283ae2"
TARGET = REPO / "generators" / TASK_ID / "generator.py"
OUT = PACKET / "checks" / "audit" / TASK_ID
SEED = 20261003
SAMPLE_INDEX = 2
DIFFICULTY = "medium"


def sha_bytes(data):
    return hashlib.sha256(data).hexdigest()


def grid_sha(grid):
    return sha_bytes(json.dumps(grid, separators=(",", ":")).encode())


def write_json(path, data):
    path.write_text(json.dumps(data, indent=2) + "\n")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    generator_sha = sha_bytes(TARGET.read_bytes())
    script_sha = sha_bytes(Path(__file__).read_bytes())
    canonical_path = REPO / "shared/data/canonical/puzzles.jsonl"
    with canonical_path.open() as handle:
        canonical = next(json.loads(line) for line in handle
                         if json.loads(line)["task_id"] == TASK_ID)
    program = canonical["program_solution"]
    canonical_rule_sha = sha_bytes(program.encode())
    canonical_rule_hash = sha_bytes(" ".join(program.split()).encode())[:12]

    sys.path.insert(0, str(REPO / "shared/runtime"))
    spec = importlib.util.spec_from_file_location("audit_target_58f520283ae2", TARGET)
    target = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(target)

    overrides = [{}, {"palette_size": 2}, {"palette_size": 3},
                 {"n_distinct_colors": 2}, {"n_distinct_colors": 3},
                 {"palette_size": 2, "n_distinct_colors": 2}]
    cases = []
    grids = []
    for override in overrides:
        grid = target.generate(SEED, SAMPLE_INDEX, difficulty=DIFFICULTY, **override)
        colors = sorted({value for r, row in enumerate(grid)
                         for c, value in enumerate(row)
                         if (r, c) != (0, 0) and value != 0})
        cases.append({"seed": SEED, "sample_index": SAMPLE_INDEX,
                      "difficulty": DIFFICULTY, "overrides": override,
                      "input_sha256": grid_sha(grid), "motif_colors": colors,
                      "motif_color_count": len(colors),
                      "validator_errors": target.self_check(grid, difficulty=DIFFICULTY)})
        grids.append(grid)
    grid = grids[-1]
    assert all(candidate == grid for candidate in grids)
    assert all(case["validator_errors"] == [] for case in cases)
    assert cases[-1]["motif_colors"] == [4, 5, 9]
    positions = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row)
                 if (r, c) != (0, 0) and value != 0]
    top, left = min(r for r, c in positions), min(c for r, c in positions)
    bottom, right = max(r for r, c in positions), max(c for r, c in positions)
    crop = [row[left:right + 1] for row in grid[top:bottom + 1]]
    assert grid[0][0] == 6 and (bottom - top + 1, right - left + 1) == (4, 2)
    independent_output = crop[::-1]
    write_json(OUT / "input.json", {"input": grid})

    argv = ["python3", "run_with_racket.py", "python3", "-m", "arcpuzzles", "apply",
            TASK_ID, "--input", "../checks/audit/58f520283ae2/input.json",
            "--out", "../checks/audit/58f520283ae2/racket.json"]
    # The CLI refuses to overwrite evidence. Reproduction is intended for a
    # fresh extraction, or a fresh audit output directory.
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    run = subprocess.run(argv, cwd=PACKET, env=env, capture_output=True, text=True)
    (OUT / "racket_command.log").write_text(run.stdout + run.stderr)
    command = {"cwd": "packet_root", "argv": argv, "exit_code": run.returncode,
               "evidence_paths": ["checks/audit/58f520283ae2/racket.json",
                                  "checks/audit/58f520283ae2/racket_command.log"]}
    if run.returncode != 0:
        write_json(OUT / "command_failure.json", command)
        print(run.stderr, file=sys.stderr)
        return run.returncode
    racket = json.loads((OUT / "racket.json").read_text())
    result = racket["results"][0]
    assert result["error"] is None
    assert result["input"] == grid
    assert racket["generator_sha256"] == generator_sha
    assert racket["executed_rule_hash"] == canonical_rule_hash
    assert result["output"] == independent_output
    assert sha_bytes(TARGET.read_bytes()) == generator_sha

    report = {
        "schema": "task-local-audit-v1", "task_id": TASK_ID,
        "finding_id": "A-58f520283ae2-1", "status": "reproduced_defect",
        "title": "Exact palette-count overrides are ignored",
        "phase": "unchanged audit-target snapshot",
        "generator_path": "repo/generators/58f520283ae2/generator.py",
        "generator_version": target.VERSION, "generator_sha256": generator_sha,
        "canonical_rule_source_sha256": canonical_rule_sha,
        "executed_rule_hash": racket["executed_rule_hash"],
        "executed_rule_text_sha256": racket["rule_text_sha256"],
        "audit_script_sha256": script_sha,
        "runtime_import_root": "repo/shared/runtime",
        "runtime_base_sha256": sha_bytes((REPO / "shared/runtime/puzzle_generators/base.py").read_bytes()),
        "runtime_grid_helper_sha256": sha_bytes((REPO / "shared/runtime/puzzle_generators/helpers/grid.py").read_bytes()),
        "declared_axes": {key: target.AXES[key] for key in ("palette_size", "n_distinct_colors")},
        "sampling": {"seed_values": [SEED], "sample_indices": [SAMPLE_INDEX],
                     "difficulty": DIFFICULTY, "generation_calls": len(cases),
                     "unique_inputs": len({case["input_sha256"] for case in cases}),
                     "all_six_calls_identical": True, "cases": cases},
        "counterexample": {
            "seed": SEED, "sample_index": SAMPLE_INDEX, "difficulty": DIFFICULTY,
            "overrides": overrides[-1], "input": grid, "input_sha256": grid_sha(grid),
            "target_validator_errors": [], "passes_target_validator": True,
            "documented_generator_domain": True,
            "documented_domain_reason": "An ordinary generated 11x10 zero-background grid, command 6 at (0,0), separate motif with a 4x2 non-square bbox, three nonzero motif colors, and every bbox edge touched. It is in the general documented domain but violates the requested exact two-color controls.",
            "expected_motif_color_count": 2, "actual_motif_color_count": 3,
            "actual_motif_colors": [4, 5, 9], "motif_bbox": [top, left, bottom, right],
            "actual_racket_output": result["output"],
            "rival_output": independent_output,
            "rival_description": "Independent literal command-6 implementation: remove command, crop nonzero motif, reverse row order. This is an output-concordance check; no alternative shortcut claim is made.",
            "racket_output_matches_independent_output": True,
            "racket_output_color_count": len({v for row in result["output"] for v in row if v != 0}),
        },
        "cause": "generate passes no palette controls into _rand_motif; _rand_motif privately draws a palette length in 2..3 and colors using only the layout RNG. Neither advertised palette-size control is read.",
        "impact": "Callers cannot pin the documented exact color-count controls; requesting two colors silently returns a three-color input and reference output.",
        "target_or_rule_modified": False,
        "limitations": "One fixed seed/index with six override variants, one unique input, and one supported Racket application. No full battery, lesson-frequency estimate, canonical-shortcut fit claim, or broad semantic correctness claim.",
        "verification_commands": [command],
    }
    write_json(OUT / "report.json", report)
    section = f"""## 58f520283ae2

**A-58f520283ae2-1 — Reproduced defect: advertised exact palette counts are ignored.** The unmodified `generator.py` (version `{target.VERSION}`, SHA-256 `{generator_sha}`) advertises `palette_size` and `n_distinct_colors` with valid values 2 and 3. At seed `{SEED}`, sample index `{SAMPLE_INDEX}`, difficulty `{DIFFICULTY}`, requesting both controls as 2 produces a motif with **three colors: 4, 5, and 9**. Requests for either control individually produce the same violation. The default draw, the two values of each individual control, and the joint two-color request all produce identical grids: six generation calls, one unique input. This is a fixed-witness check, not a frequency estimate.

`self_check` returns `[]` for all six variants. The 11×10 input belongs to the documented general generator domain: command 6 at (0,0), zero background, a separate motif with a non-square 4×2 bounding box, three colors, and every bounding-box edge touched. It violates the requested exact two-color controls. The cause is direct: `generate` does not pass either control to `_rand_motif`, whose palette size comes from its own `rng.randint(2, 3)` draw.

The supported `arcpuzzles apply` command succeeds (exit 0) and returns `[[5,0],[5,4],[9,0],[0,9]]`, preserving all three motif colors. It agrees with an independently computed crop followed by a vertical flip for command 6. That comparison checks the recorded reference output; this finding does not assert a rule error or a successful shortcut. The executed normalized rule hash is `{racket['executed_rule_hash']}`; the full canonical rule source SHA-256 is `{canonical_rule_sha}`; the executed callable-text SHA-256 is `{racket['rule_text_sha256']}`.

Evidence: `checks/audit/58f520283ae2/input.json`, `checks/audit/58f520283ae2/racket.json`, and `checks/audit/58f520283ae2/report.json`. The report includes every override, seed/index, validator result, input hash, actual Racket output, independent output, exact command, and working directory. Reproducer: `repo/generators/53ffc8bc9584/workspace/audit_58f520283ae2.py` (uses the unchanged target through `repo/shared/runtime`). Run from `packet_root`: `python3 repo/generators/53ffc8bc9584/workspace/audit_58f520283ae2.py` with a fresh audit output directory, because the supported apply command refuses to overwrite `racket.json`.

No target or rule files were changed. Scope: one witness, six control variants, one unique input, and one reference application. No full battery, lesson distribution study, or universal semantic claim was attempted. Fixing the control plumbing and guaranteeing the chosen number of colors appears in the motif would address this defect; no fix is included in this findings-only audit.
"""
    (OUT / "AUDIT_SECTION.md").write_text(section)
    print(json.dumps({"finding_id": report["finding_id"], "status": report["status"],
                      "generator_sha256": generator_sha, "rule_hash": canonical_rule_hash,
                      "unique_inputs": 1, "generation_calls": len(cases),
                      "racket_exit_code": run.returncode, "report": str(OUT / "report.json")}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
