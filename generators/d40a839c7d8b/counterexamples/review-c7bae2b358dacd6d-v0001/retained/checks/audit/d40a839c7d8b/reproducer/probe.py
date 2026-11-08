#!/usr/bin/env python3
"""Extract and independently score the retained height-parity lesson witness."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from reviewer_support import load_selected_generator

TASK_ID = "d40a839c7d8b"
EXPECTED_SOURCE_SHA256 = "c280887166f87ab76d450d737548b3a27a75f315ebb672a55de211d310d0660c"
TARGET_SEED = 256453378305694
TARGET_SAMPLE_INDEX = 33
TARGET_BAND = "medium"


def digest(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def height_parity(grid: list[list[int]]) -> list[list[int]]:
    h = len(grid)
    trigger = (h + 1) % 2
    return [
        [3 if value == 5 and c % 2 == trigger else value for c, value in enumerate(row)]
        for row in grid
    ]


def cell_differences(a: list[list[int]], b: list[list[int]]) -> list[dict[str, int]]:
    return [
        {"row": r, "col": c, "actual": a[r][c], "rival": b[r][c]}
        for r in range(len(a))
        for c in range(len(a[0]))
        if a[r][c] != b[r][c]
    ]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--semantic-report", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    module, source_path, source_sha256 = load_selected_generator(TASK_ID, root=args.repo.resolve())
    if source_sha256 != EXPECTED_SOURCE_SHA256:
        raise SystemExit(f"source hash mismatch: {source_sha256}")

    audit = json.loads(args.semantic_report.read_text())["audits"][0]
    examples = audit["lessons"]["rotations"]["examples"]
    row = next(
        item for item in examples
        if item.get("seed") == TARGET_SEED
        and item.get("sample_index") == TARGET_SAMPLE_INDEX
        and item.get("band") == TARGET_BAND
        and item.get("query_index") == 3
    )
    instance = row["instance"]
    demos = instance["train"]
    query = instance["test"][0]

    demo_rows = []
    for index, pair in enumerate(demos):
        rival = height_parity(pair["input"])
        h, w = len(pair["input"]), len(pair["input"][0])
        demo_rows.append({
            "index": index,
            "height": h,
            "width": w,
            "width_trigger": (w + 1) % 2,
            "height_trigger": (h + 1) % 2,
            "height_parity_matches_label": rival == pair["output"],
            "input_sha256": digest(pair["input"]),
            "output_sha256": digest(pair["output"]),
        })

    query_rival = height_parity(query["input"])
    differences = cell_differences(query["output"], query_rival)
    query_h, query_w = len(query["input"]), len(query["input"][0])
    report = {
        "schema": "arcpuzzles-audit-height-parity-witness-v1",
        "task_id": TASK_ID,
        "generator_path": str(source_path),
        "generator_sha256": source_sha256,
        "semantic_report": str(args.semantic_report),
        "replay": {
            "band": TARGET_BAND,
            "seed": TARGET_SEED,
            "sample_index": TARGET_SAMPLE_INDEX,
            "n_demos": len(demos),
            "query_policy": "fourth generated pair is the production query",
        },
        "hook_reasons": module.lesson_identifiable(demos, query),
        "demos": demo_rows,
        "all_demos_fit_height_parity": all(
            row["height_parity_matches_label"] for row in demo_rows
        ),
        "query": {
            "height": query_h,
            "width": query_w,
            "width_trigger": (query_w + 1) % 2,
            "height_trigger": (query_h + 1) % 2,
            "self_check": module.self_check(query["input"]),
            "rule_mirror_matches_retained_racket_label": module.rule_mirror(query["input"]) == query["output"],
            "height_parity_matches_label": query_rival == query["output"],
            "differing_cell_count": len(differences),
            "differences": differences,
            "input_sha256": digest(query["input"]),
            "actual_output_sha256": digest(query["output"]),
            "rival_output_sha256": digest(query_rival),
        },
        "finding": (
            "All three demonstrations have matching height- and width-derived trigger parity, "
            "so the height-parity rival fits every label. The 3x12 query separates the rules; "
            "the demos therefore do not determine the retained Racket answer."
        ),
        "command": [
            "python3", "../checks/audit/d40a839c7d8b/reproducer/probe.py",
            "--repo", ".",
            "--semantic-report", "../checks/audit/d40a839c7d8b/checks/d40a839c7d8b_audit_semantic_gate.json",
            "--out", "../checks/audit/d40a839c7d8b/reproducer",
        ],
        "cwd": "repo",
    }

    (args.out / "lesson-instance.json").write_text(json.dumps(instance, indent=2) + "\n")
    (args.out / "input.json").write_text(json.dumps(query["input"], indent=2) + "\n")
    (args.out / "retained-racket-output.json").write_text(json.dumps(query["output"], indent=2) + "\n")
    (args.out / "height-parity-rival-output.json").write_text(json.dumps(query_rival, indent=2) + "\n")
    (args.out / "report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")

    reproduced = (
        report["all_demos_fit_height_parity"]
        and not report["query"]["height_parity_matches_label"]
        and report["query"]["self_check"] == []
        and report["query"]["rule_mirror_matches_retained_racket_label"]
        and report["hook_reasons"] == ["demos do not falsify shortcut 'derive parity from height'"]
    )
    print(json.dumps({
        "task_id": TASK_ID,
        "generator_sha256": source_sha256,
        "reproduced": reproduced,
        "differing_cell_count": len(differences),
        "report": str(args.out / "report.json"),
    }, sort_keys=True))
    return 0 if reproduced else 1


if __name__ == "__main__":
    raise SystemExit(main())
