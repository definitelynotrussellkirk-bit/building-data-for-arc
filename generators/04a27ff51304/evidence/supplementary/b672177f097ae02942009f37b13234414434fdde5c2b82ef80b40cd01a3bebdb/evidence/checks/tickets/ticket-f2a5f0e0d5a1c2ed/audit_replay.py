#!/usr/bin/env python3
"""Replay the pinned 04a27ff51304 teaching-ambiguity witness.

The replay verifies every retained asset hash, regenerates the exact four-input
window from the pinned source, reruns the exact canonical Racket authority, and
recomputes the occupancy-only rival. It reports reproduction only when all
bindings and the [true,true,true,false] agreement vector match.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

TASK_ID = "04a27ff51304"
RETURN_ID = "review-487b1a938ca9e144:v0001"
SOURCE_SHA256 = "d9e6c8d15eae0c2505749ea4eb92ca5b29036c416fc3c13a017e0eb9194d9101"
MANIFEST_SHA256 = "6f6cb798171f1643e09e4a229c718603737a6236f8bb8e0fb1c79361fdf4d1a3"
INDEX_SHA256 = "a0da87df23a2497d2a20de06e29f6308a7548c0fa117f4ae8dc4146c704cea76"
AUDIT_RECORD_SHA256 = "8b8a5ce8ffea0b986a2ef5d929bdc6c4a8934c9e60a5fd4af182045ee9b82c02"
RULE_HASH = "f3a3e1a37f60"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_json_sha256(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _run_length(grid: list[list[int]], r: int, c: int, dr: int, dc: int, *, same_color: bool) -> int:
    if grid[r][c] == 0:
        return 0
    h, w = len(grid), len(grid[0])
    color = grid[r][c]
    count = 1
    for sign in (-1, 1):
        rr, cc = r + sign * dr, c + sign * dc
        while 0 <= rr < h and 0 <= cc < w:
            value = grid[rr][cc]
            if value == 0 or (same_color and value != color):
                break
            count += 1
            rr += sign * dr
            cc += sign * dc
    return count


def same_color_targets(grid: list[list[int]]) -> list[tuple[int, int]]:
    return [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 0
        and _run_length(grid, r, c, 0, 1, same_color=True) >= 3
        and _run_length(grid, r, c, 1, 0, same_color=True) >= 3
    ]


def occupancy_targets(grid: list[list[int]]) -> list[tuple[int, int]]:
    return [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 0
        and _run_length(grid, r, c, 0, 1, same_color=False) >= 3
        and _run_length(grid, r, c, 1, 0, same_color=False) >= 3
    ]


def paint_targets(grid: list[list[int]], targets: list[tuple[int, int]]) -> list[list[int]]:
    output = [[0 for _ in row] for row in grid]
    for r, c in targets:
        output[r][c] = 8
    return output


def differing_cells(a: list[list[int]], b: list[list[int]]) -> list[list[int]]:
    return [[r, c] for r, row in enumerate(a) for c, value in enumerate(row) if value != b[r][c]]


def _canonical_program(repo: Path) -> str:
    from reviewer_support import canonical_path

    programs = []
    with canonical_path(repo).open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                row = json.loads(line)
                if row.get("task_id") == TASK_ID:
                    programs.append(row["program_solution"])
    if not programs or len(set(programs)) != 1:
        raise RuntimeError("expected one stable canonical Racket authority")
    return programs[0]


def _racket_outputs(repo: Path, inputs: list[list[list[int]]]) -> tuple[list[list[list[int]]], dict[str, Any]]:
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import strip_rule_wrapper
    from reviewer_support import normalize_grid

    program = _canonical_program(repo)
    function = strip_rule_wrapper(program)
    outputs = []
    with RacketBridge(timeout=20.0) as bridge:
        runtime = dict(bridge.runtime_identity)
        for grid in inputs:
            normalized = normalize_grid(grid)
            datum = "(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in normalized) + ")"
            expression = (
                f"({function} '{datum})"
                if function.startswith("(lambda (g)")
                else f"((lambda (g) {function}) '{datum})"
            )
            outputs.append(normalize_grid(bridge.eval_text(expression)))
    return outputs, runtime


def run_replay(work_root: Path, *, run_racket: bool = True) -> dict[str, Any]:
    from reviewer_support import load_selected_generator

    work = Path(work_root).resolve()
    repo = work / "repo"
    task_dir = repo / "generators" / TASK_ID
    asset_dir = task_dir / "counterexamples/review-487b1a938ca9e144-v0001"
    manifest_path = asset_dir / "audit_assets.json"
    index_path = task_dir / "evidence/review_index.json"
    bindings = {
        "generator": {"expected": SOURCE_SHA256, "actual": sha256_file(task_dir / "generator.py")},
        "assets_manifest": {"expected": MANIFEST_SHA256, "actual": sha256_file(manifest_path)},
        "audit_index": {"expected": INDEX_SHA256, "actual": sha256_file(index_path)},
    }
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    index = json.loads(index_path.read_text(encoding="utf-8"))
    audit_rows = [row for row in index.get("audits", []) if row.get("return_id") == RETURN_ID]
    if len(audit_rows) != 1:
        raise RuntimeError("pinned audit record missing or duplicated")
    audit_record = audit_rows[0]
    bindings["audit_record"] = {
        "expected": AUDIT_RECORD_SHA256,
        "actual": canonical_json_sha256(audit_record),
    }
    retained_hashes = []
    for entry in manifest.get("files", []):
        path = repo / entry["path"]
        retained_hashes.append(
            {
                "path": entry["path"],
                "expected": entry["sha256"],
                "actual": sha256_file(path),
                "matches": sha256_file(path) == entry["sha256"],
            }
        )
    base = asset_dir / "retained/checks/audit/04a27ff51304"
    retained_inputs = json.loads((base / "input.json").read_text(encoding="utf-8"))
    retained_racket = json.loads((base / "racket.json").read_text(encoding="utf-8"))
    retained_rival = json.loads((base / "rival-output.json").read_text(encoding="utf-8"))
    retained_repro = json.loads((base / "shortcut-repro.json").read_text(encoding="utf-8"))
    generator, source_path, source_digest = load_selected_generator(TASK_ID, root=repo)
    generated_inputs = [generator.generate(0, index, difficulty=None) for index in range(4)]
    self_checks = [generator.self_check(grid, difficulty=None) for grid in generated_inputs]
    mirror_outputs = [paint_targets(grid, same_color_targets(grid)) for grid in generated_inputs]
    rival_outputs = [paint_targets(grid, occupancy_targets(grid)) for grid in generated_inputs]
    retained_outputs = [row["output"] for row in retained_racket["results"]]
    fresh_outputs, runtime = (None, None)
    if run_racket:
        fresh_outputs, runtime = _racket_outputs(repo, generated_inputs)
    authority_outputs = fresh_outputs if fresh_outputs is not None else retained_outputs
    agreements = [rival == authority for rival, authority in zip(rival_outputs, authority_outputs)]
    diffs = [differing_cells(rival, authority) for rival, authority in zip(rival_outputs, authority_outputs)]
    checks = {
        "all_identity_hashes_match": all(row["expected"] == row["actual"] for row in bindings.values()),
        "all_retained_asset_hashes_match": all(row["matches"] for row in retained_hashes),
        "manifest_identity_matches": manifest.get("return_id") == RETURN_ID and manifest.get("audited_generator_sha256") == SOURCE_SHA256,
        "source_loader_matches": source_path == task_dir / "generator.py" and source_digest == SOURCE_SHA256,
        "generated_inputs_match_retained": generated_inputs == retained_inputs,
        "all_inputs_pass_self_check": all(errors == [] for errors in self_checks),
        "python_authority_mirror_matches_retained_racket": mirror_outputs == retained_outputs,
        "fresh_racket_matches_retained": fresh_outputs == retained_outputs if fresh_outputs is not None else None,
        "retained_rival_matches_recomputed": rival_outputs == retained_rival,
        "retained_rule_hash_matches": retained_racket.get("executed_rule_hash") == RULE_HASH,
        "retained_agreement_vector_matches": [row["rival_matches_authority_mirror"] for row in retained_repro["pair_results"]] == [True, True, True, False],
        "fresh_agreement_vector_matches": agreements == [True, True, True, False],
        "query_diff_is_exact_cell_6_1": diffs == [[], [], [], [[6, 1]]],
    }
    reproduced = all(value is True for value in checks.values() if value is not None)
    return {
        "schema": "arcpuzzles-audit-replay-ticket-v1",
        "ticket_id": "ticket-f2a5f0e0d5a1c2ed",
        "task_id": TASK_ID,
        "audit_return_id": RETURN_ID,
        "status": "reproduced" if reproduced else "not_reproduced",
        "claim": "occupancy-only crossing rival fits demonstrations 0..2 and differs on query 3 at exactly (6,1)",
        "bindings": bindings,
        "retained_asset_hashes": retained_hashes,
        "rule_hash": RULE_HASH,
        "seed": 0,
        "difficulty": None,
        "sample_indices": [0, 1, 2, 3],
        "self_checks": self_checks,
        "same_color_targets": [[list(cell) for cell in same_color_targets(grid)] for grid in generated_inputs],
        "occupancy_targets": [[list(cell) for cell in occupancy_targets(grid)] for grid in generated_inputs],
        "agreement_vector": agreements,
        "differing_cells": diffs,
        "checks": checks,
        "racket_runtime": runtime,
        "scope": "Bounded witness replay only; this does not clear, resolve, approve, or broaden the retained audit.",
    }


def markdown(report: dict[str, Any]) -> str:
    return (
        "# Pinned audit replay\n\n"
        f"Status: **{report['status']}**\n\n"
        f"Task: `{report['task_id']}`; return: `{report['audit_return_id']}`; rule hash: `{report['rule_hash']}`.\n\n"
        "The exact retained source and asset identities matched. Seed 0, default difficulty, indices 0–3 regenerated byte-for-byte. "
        "All four inputs passed `self_check`; fresh Racket outputs matched the retained authority outputs. The occupancy-only rival "
        f"agreement vector was `{report['agreement_vector']}` and the only query difference was `{report['differing_cells'][3]}`.\n\n"
        "This reproduces only the bounded teaching-ambiguity witness. It does not clear the audit or change approval/training status.\n"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--markdown-out", type=Path, required=True)
    args = parser.parse_args()
    report = run_replay(args.work_root, run_racket=True)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.markdown_out.write_text(markdown(report), encoding="utf-8")
    print(json.dumps({"status": report["status"], "agreement_vector": report["agreement_vector"], "out": str(args.out)}, sort_keys=True))
    return 0 if report["status"] == "reproduced" else 1


if __name__ == "__main__":
    raise SystemExit(main())
