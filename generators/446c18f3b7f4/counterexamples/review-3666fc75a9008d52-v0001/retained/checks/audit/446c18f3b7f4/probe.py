#!/usr/bin/env python3
"""Read-only current-source audit of exact frame-count/control behavior.

Run through the packet wrapper using the WORK/.venv interpreter. The generator
and canonical pairs are loaded from the explicit selected repository; Racket
labels are obtained separately through the public arcpuzzles apply command.
"""
from __future__ import annotations

import argparse
from collections import deque
import hashlib
import json
from pathlib import Path
import sys


TASK = "446c18f3b7f4"


def sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def grid_sha(grid) -> str:
    return sha(json.dumps(grid, separators=(",", ":")).encode())


def frames(grid):
    """Independent four-neighbor component and full-border check."""
    todo = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 3}
    found = []
    while todo:
        first = min(todo)
        todo.remove(first)
        work = deque([first])
        cells = {first}
        while work:
            r, c = work.popleft()
            for p in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if p in todo:
                    todo.remove(p)
                    cells.add(p)
                    work.append(p)
        r0, r1 = min(r for r, c in cells), max(r for r, c in cells)
        c0, c1 = min(c for r, c in cells), max(c for r, c in cells)
        border = {(r, c) for r in range(r0, r1 + 1) for c in range(c0, c1 + 1)
                  if r in (r0, r1) or c in (c0, c1)}
        found.append({"bbox_inclusive": [r0, c0, r1, c1],
                      "shape": [r1 - r0 + 1, c1 - c0 + 1],
                      "green_cells": len(cells), "exact_hollow_border": cells == border,
                      "corners": [[r0, c0], [r0, c1], [r1, c0], [r1, c1]]})
    return sorted(found, key=lambda record: record["bbox_inclusive"])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    repo, out = args.repo.resolve(), args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    sys.path.insert(0, str(repo / "shared/runtime"))
    from reviewer_support import canonical_pairs, load_selected_generator
    gen, source, digest = load_selected_generator(TASK, root=repo)
    pairs = canonical_pairs(TASK, root=repo)
    selected = []
    with (repo / "shared/data/canonical/puzzles.jsonl").open() as handle:
        for line in handle:
            if line.strip():
                row = json.loads(line)
                if row.get("task_id") == TASK:
                    selected.append(row)
    assert len(selected) == 1

    controls = {"grid_h": 11, "grid_w": 11, "n_frames": 3}
    draws = []
    for seed in range(4):
        grid = gen.generate(seed, 0, difficulty="medium", **controls)
        boxes = frames(grid)
        draws.append({"seed": seed, "sample_index": 0, "difficulty": "medium",
                      "overrides": controls, "input": grid,
                      "input_sha256": grid_sha(grid), "actual_frame_count": len(boxes),
                      "requested_frame_count": 3, "components": boxes,
                      "self_check": gen.self_check(grid),
                      "emission_status": "actual generate return with exact recorded controls"})
    witness = draws[0]
    assert witness["actual_frame_count"] != 3
    assert witness["self_check"] == []
    assert gen.generate(0, 0, difficulty="medium", **controls) == witness["input"]

    # A constructive, same-size valid arrangement demonstrates that requesting
    # three frames is feasible, even under the generator's two-empty-cell gap.
    feasible = [[0] * 11 for _ in range(11)]
    for r0, c0 in ((0, 0), (0, 5), (5, 0)):
        for r in range(r0, r0 + 3):
            for c in range(c0, c0 + 3):
                if r in (r0, r0 + 2) or c in (c0, c0 + 2):
                    feasible[r][c] = 3
    feasible_record = {"input": feasible, "input_sha256": grid_sha(feasible),
                       "components": frames(feasible), "self_check": gen.self_check(feasible),
                       "emission_status": "hand-constructed feasibility witness; not claimed generated"}
    assert len(feasible_record["components"]) == 3
    assert feasible_record["self_check"] == []

    rejections = []
    for difficulty, overrides in [
        ("medium", {"n_frames": 6}),
        ("medium", {"grid_h": 5}),
        ("easy", {"n_frames": 2}),
    ]:
        try:
            value = gen.generate(0, 0, difficulty=difficulty, **overrides)
        except Exception as error:
            rejections.append({"seed": 0, "sample_index": 0,
                               "difficulty": difficulty, "overrides": overrides,
                               "outcome": "raised", "exception_type": type(error).__name__,
                               "error": str(error)})
        else:
            rejections.append({"seed": 0, "sample_index": 0,
                               "difficulty": difficulty, "overrides": overrides,
                               "outcome": "returned", "input_sha256": grid_sha(value)})

    paired = []
    for axis, a, b in (("palette_kind", "warm", "cool"),
                       ("texture", "warm", "cool")):
        for seed in range(4):
            first = gen.generate(seed, 0, difficulty="medium", **controls, **{axis: a})
            second = gen.generate(seed, 0, difficulty="medium", **controls, **{axis: b})
            paired.append({"axis": axis, "first_value": a, "second_value": b,
                           "seed": seed, "sample_index": 0, "difficulty": "medium",
                           "fixed_overrides": controls, "equal": first == second,
                           "first_input_sha256": grid_sha(first),
                           "second_input_sha256": grid_sha(second),
                           "first_self_check": gen.self_check(first),
                           "second_self_check": gen.self_check(second)})

    canonical = [dict(pair, input_sha256=grid_sha(pair["input"]),
                      output_sha256=grid_sha(pair["output"]),
                      self_check=gen.self_check(pair["input"])) for pair in pairs]
    current_index = json.loads((repo / f"generators/{TASK}/evidence/review_index.json").read_text())
    record = {"schema": "arcpuzzles-focused-audit-evidence-v1", "task_id": TASK,
              "generator_source": str(source), "generator_sha256": digest,
              "source_sha256_at_end": sha(source.read_bytes()),
              "probe_sha256": sha(Path(__file__).read_bytes()),
              "canonical_program_solution": selected[0]["program_solution"],
              "canonical_program_source_sha256": sha(selected[0]["program_solution"].encode()),
              "current_review_index_sha256": sha((repo / f"generators/{TASK}/evidence/review_index.json").read_bytes()),
              "prior_findings_status": [{"return_id": row["return_id"], "resolution": row["resolution"], "source_sha256": row["source_sha256"]} for row in current_index.get("audits", [])],
              "declared_axes": gen.AXES,
              "canonical_pairs": canonical,
              "exact_count_probe": draws,
              "primary_witness": witness,
              "same_size_feasibility_witness": feasible_record,
              "declared_control_rejections": rejections,
              "paired_helpful_control_probes": paired,
              "counts": {"requested_count_probes": len(draws),
                         "count_mismatches": sum(r["actual_frame_count"] != 3 for r in draws),
                         "canonical_pairs": len(canonical),
                         "canonical_domain_passes": sum(r["self_check"] == [] for r in canonical),
                         "paired_control_probes": len(paired),
                         "paired_control_equalities": sum(r["equal"] for r in paired)},
              "no_claims": ["No full battery or lesson census was run.",
                            "No wrong reference output or semantic rival is asserted.",
                            "Prior unresolved findings were leads; the exact current source was independently run.",
                            "No private solve labels or solver programs were read."]}
    assert record["source_sha256_at_end"] == digest
    (out / "probe.json").write_text(json.dumps(record, indent=2) + "\n")
    inputs = [witness["input"], feasible, *[pair["input"] for pair in pairs]]
    identities = ["primary_generated_frame_count_witness", "handmade_three_frame_feasibility",
                  *[f"canonical:{p['variant']}:{p['split']}:{p['pair_index']}" for p in pairs]]
    (out / "input.json").write_text(json.dumps({"inputs": inputs}, indent=2) + "\n")
    (out / "input-identities.json").write_text(json.dumps(identities, indent=2) + "\n")
    print(json.dumps({"generator_sha256": digest, "canonical_program_source_sha256": record["canonical_program_source_sha256"],
                      "counts": record["counts"], "primary_witness": witness,
                      "declared_control_rejections": rejections}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
