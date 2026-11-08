#!/usr/bin/env python3
"""Source-bound audit probe for invalid canonical-shortcut declarations."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK_ID = "4f640d81f260"
EXPECTED_SOURCE_SHA256 = "bbe764cf557cb9879a33a81199da57ea8b67c895375bb8987ff47652452213b9"


def first_difference(left, right):
    for row, (lrow, rrow) in enumerate(zip(left, right)):
        for col, (lv, rv) in enumerate(zip(lrow, rrow)):
            if lv != rv:
                return {"row": row, "col": col, "expected": lv, "rival": rv}
    if len(left) != len(right) or any(len(a) != len(b) for a, b in zip(left, right)):
        return {"shape_mismatch": True}
    return None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    root = find_root(__file__)
    gen, source, source_sha256 = load_selected_generator(TASK_ID, root=root)
    if source_sha256 != EXPECTED_SOURCE_SHA256:
        raise RuntimeError(f"source drift: expected {EXPECTED_SOURCE_SHA256}, got {source_sha256}")
    pairs = canonical_pairs(TASK_ID, root=root)

    shortcuts = getattr(gen, "CANONICAL_SHORTCUTS", {})
    results = {}
    for name, shortcut in shortcuts.items():
        mismatches = []
        for index, pair in enumerate(pairs):
            predicted = shortcut(pair["input"])
            if predicted != pair["output"]:
                mismatches.append({
                    "pair_index": index,
                    "first_difference": first_difference(pair["output"], predicted),
                    "input": pair["input"] if len(mismatches) == 0 else None,
                    "expected_output": pair["output"] if len(mismatches) == 0 else None,
                    "rival_output": predicted if len(mismatches) == 0 else None,
                })
        results[name] = {
            "checked": len(pairs),
            "mismatches": len(mismatches),
            "fits_all_canonical_pairs": not mismatches,
            "first_mismatch": mismatches[0] if mismatches else None,
        }

    report = {
        "schema": "arcpuzzles-audit-probe-4f640d81f260-v1",
        "task_id": TASK_ID,
        "generator_path": str(source.relative_to(root)),
        "generator_source_sha256": source_sha256,
        "declared_rule_hash": getattr(gen, "RULE_HASH", None),
        "canonical_pair_count": len(pairs),
        "declared_canonical_shortcuts": sorted(shortcuts),
        "results": results,
        "all_declarations_invalid": bool(results) and all(
            not item["fits_all_canonical_pairs"] for item in results.values()
        ),
        "scope_note": (
            "CANONICAL_SHORTCUTS is reserved for rivals that reproduce every labeled canonical pair. "
            "These transforms are legitimate semantic rivals but belong in LESSON_COMPETITORS only."
        ),
        "portable_task_test_failure": {
            "evidence": "checks/audit/4f640d81f260-task-tests/result.json",
            "summary": (
                "Portable task tests exit 2 because they import scripts.canonical_profile_gate and use a fixed "
                "Path(__file__).parents[1] canonical path; reviewer_support APIs are required."
            ),
        },
        "command": [
            "python3", "review.py", "run", "python3",
            "../checks/audit/4f640d81f260/probe.py", "--out",
            "../checks/audit/4f640d81f260/probe.json",
        ],
        "working_directory": "packet_root",
        "payload_working_directory": "repo",
    }
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "source_sha256": source_sha256,
        "canonical_pair_count": len(pairs),
        "mismatch_counts": {name: item["mismatches"] for name, item in results.items()},
        "all_declarations_invalid": report["all_declarations_invalid"],
    }, indent=2, sort_keys=True))
    return 0 if report["all_declarations_invalid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
