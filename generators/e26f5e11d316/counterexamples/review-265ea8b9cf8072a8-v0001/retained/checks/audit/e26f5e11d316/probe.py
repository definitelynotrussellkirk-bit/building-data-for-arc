"""Findings-only audit probe. Run from the packet's repo via the public wrapper."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys


TASK_ID = "e26f5e11d316"


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def grid_digest(grid):
    return digest(json.dumps(grid, separators=(",", ":")).encode())


def save(path, value):
    path.write_text(json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n")


def load_source(repo):
    source = repo / f"generators/{TASK_ID}/generator.py"
    spec = importlib.util.spec_from_file_location("audited_e26f5e11d316", source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, digest(source.read_bytes())


def canonical_record(repo):
    path = repo / "shared/data/canonical/puzzles.jsonl"
    for line in path.open():
        if TASK_ID in line:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row, digest(line.encode())
    raise ValueError("Assigned canonical record is missing")


def walls(grid, color):
    height, width = len(grid), len(grid[0])
    rows = [r for r in range(height) if all(value == color for value in grid[r])]
    cols = [c for c in range(width) if all(grid[r][c] == color for r in range(height))]
    return rows, cols


def documented_wall5_mirror(grid):
    """Literal generator prose: preserve 5-walls; fill rooms from their own seeds."""
    result = [row[:] for row in grid]
    rows, cols = walls(grid, 5)
    for r0, r1 in zip(rows, rows[1:]):
        for c0, c1 in zip(cols, cols[1:]):
            cells = [(r, c) for r in range(r0 + 1, r1) for c in range(c0 + 1, c1)]
            seeds = [(r, c, grid[r][c]) for r, c in cells if grid[r][c] not in (0, 5)]
            for r, c in cells:
                if grid[r][c] == 0 and seeds:
                    result[r][c] = min((abs(r - sr) + abs(c - sc), color)
                                       for sr, sc, color in seeds)[1]
    return result


def authored_witness():
    grid = [[5 if r in (0, 4, 8) or c in (0, 4, 8) else 0 for c in range(9)]
            for r in range(9)]
    for (r, c), color in zip(((2, 2), (2, 6), (6, 2), (6, 6)), (1, 2, 3, 4)):
        grid[r][c] = color
    return grid


def prepare(repo, out):
    generator, source_sha = load_source(repo)
    canonical, row_sha = canonical_record(repo)
    authored = authored_witness()
    generated = generator.generate(seed=0, sample_index=0)
    inputs = [authored, generated]
    mirrors = [documented_wall5_mirror(grid) for grid in inputs]
    cases = [
        {"name": "authored_minimum_easy_rooms", "origin": "authored", "call": None,
         "domain_status": "within documented construction domain",
         "domain_basis": "9x9; four 3x3 chambers separated and enclosed by complete 5-walls; one isolated center seed per chamber, in colors 1,2,3,4. Chamber dimensions 3x3 are within the easy range and accepted ch_h/ch_w overrides. This is an authored witness, not a claimed RNG draw."},
        {"name": "ordinary_generated_seed0_index0", "origin": "generated",
         "call": {"seed": 0, "sample_index": 0, "difficulty": None, "overrides": {}},
         "domain_status": "ordinary generator output", "domain_basis": "Unmodified generate(seed=0, sample_index=0) with no overrides."},
    ]
    for index, (case, grid, mirror) in enumerate(zip(cases, inputs, mirrors)):
        case.update(index=index, input_shape=[len(grid), len(grid[0])],
                    input_sha256=grid_digest(grid), mirror_sha256=grid_digest(mirror),
                    self_check=generator.self_check(grid), full_wall5_rows=walls(grid, 5)[0],
                    full_wall5_cols=walls(grid, 5)[1])
    canonical_checks = []
    for split in ("train", "test"):
        for index, pair in enumerate(canonical.get(split, [])):
            grid = pair["input"]
            canonical_checks.append({"pair": f"{split}[{index}]", "shape": [len(grid), len(grid[0])],
                                     "input_sha256": grid_digest(grid), "self_check": generator.self_check(grid),
                                     "full_wall5_rows": walls(grid, 5)[0], "full_wall5_cols": walls(grid, 5)[1],
                                     "full_wall8_rows": walls(grid, 8)[0], "full_wall8_cols": walls(grid, 8)[1]})
    review_index = json.loads((repo / f"generators/{TASK_ID}/evidence/review_index.json").read_text())
    metadata = {"schema": "e26-findings-prepare-v1", "task_id": TASK_ID,
                "generator_sha256": source_sha, "generator_version": generator.VERSION,
                "canonical_row_sha256": row_sha,
                "canonical_program_sha256": digest(canonical["program_solution"].encode()),
                "canonical_path": "repo/shared/data/canonical/puzzles.jsonl",
                "runtime_cwd": str(repo), "argv": sys.orig_argv,
                "cases": cases, "canonical_checks": canonical_checks,
                "prior_open_audits": [{key: item.get(key) for key in
                                       ("return_id", "source_sha256", "resolution", "verification_status", "assets_manifest", "assets_manifest_sha256")}
                                      for item in review_index.get("audits", [])]}
    out.mkdir(parents=True, exist_ok=True)
    save(out / "input.json", inputs)
    save(out / "rival-output.json", mirrors)
    save(out / "preparation.json", metadata)
    assert all(not case["self_check"] for case in cases), "Witness must pass the target validator"
    print(json.dumps({"prepared": len(cases), "generator_sha256": source_sha,
                      "canonical_inputs": len(canonical_checks),
                      "canonical_rejected": sum(bool(row["self_check"]) for row in canonical_checks)}))


def compare(repo, out):
    metadata = json.loads((out / "preparation.json").read_text())
    inputs = json.loads((out / "input.json").read_text())
    mirrors = json.loads((out / "rival-output.json").read_text())
    actual = json.loads((out / "racket.json").read_text())
    current_sha = digest((repo / f"generators/{TASK_ID}/generator.py").read_bytes())
    assert current_sha == metadata["generator_sha256"] == actual["generator_sha256"]
    assert actual["task_id"] == TASK_ID and len(actual["results"]) == len(inputs)
    cases = []
    for case, original, mirror, row in zip(metadata["cases"], inputs, mirrors, actual["results"]):
        assert row["error"] is None and row["valid_output"] and row["input"] == original
        output = row["output"]
        assert len(output) == len(original) and all(len(a) == len(b) for a, b in zip(output, original))
        differences = [{"row": r, "column": c, "actual": output[r][c], "documented_mirror": mirror[r][c]}
                       for r in range(len(original)) for c in range(len(original[0])) if output[r][c] != mirror[r][c]]
        cases.append({**case, "input": original, "actual_racket_output": output,
                      "rival_documented_rule_output": mirror, "actual_output_sha256": row["output_sha256"],
                      "differing_cells": len(differences), "differences": differences,
                      "actual_changed_cells": sum(a != b for ar, br in zip(original, output) for a, b in zip(ar, br)),
                      "mirror_changed_cells": sum(a != b for ar, br in zip(original, mirror) for a, b in zip(ar, br))})
    result = {"schema": "arcpuzzles-audit-counterexample-v1", "finding_id": "AUD-E26-01",
              "task_id": TASK_ID, "audit_verdict": "reproduced_existing_authority_domain_defect",
              "generator_sha256": current_sha, "rule_text_sha256": actual["rule_text_sha256"],
              "executed_rule_hash": actual["executed_rule_hash"],
              "canonical_row_sha256": metadata["canonical_row_sha256"],
              "canonical_program_sha256": metadata["canonical_program_sha256"],
              "racket_command": actual["command"], "racket_cwd": actual["cwd"],
              "runtime_cwd": str(repo), "argv": sys.orig_argv,
              "canonical_inputs": len(metadata["canonical_checks"]),
              "canonical_rejected": sum(bool(row["self_check"]) for row in metadata["canonical_checks"]),
              "canonical_checks": metadata["canonical_checks"], "cases": cases,
              "explanation": "The generator and its prose reserve 5 for walls, but the selected canonical Racket program treats 8 as walls and any nonzero non-8 cell, including a generated 5-wall cell, as a seed. The actual output therefore differs from filling each 5-bounded chamber from its declared seeds.",
              "prior_open_audits": metadata["prior_open_audits"],
              "semantic_pass": False,
              "probe_exit_policy": "Exit zero means this audit reproducer's assertions passed, not that the audited generator passed."}
    save(out / "audit-counterexample.json", result)
    assert [case["differing_cells"] for case in cases] == [16, 41]
    assert result["canonical_inputs"] == result["canonical_rejected"] == 5
    print(json.dumps({"audit_verdict": result["audit_verdict"], "differing_cells": [case["differing_cells"] for case in cases],
                      "canonical_rejected": result["canonical_rejected"], "canonical_inputs": result["canonical_inputs"],
                      "generator_sha256": current_sha, "rule_text_sha256": result["rule_text_sha256"]}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("prepare", "compare"))
    args = parser.parse_args()
    repo = Path.cwd().resolve()
    if not (repo / f"generators/{TASK_ID}/generator.py").is_file():
        raise SystemExit("Run from the packet repository, e.g. through python3 review.py run ...")
    out = repo.parent / "checks/audit" / TASK_ID
    (prepare if args.stage == "prepare" else compare)(repo, out)
