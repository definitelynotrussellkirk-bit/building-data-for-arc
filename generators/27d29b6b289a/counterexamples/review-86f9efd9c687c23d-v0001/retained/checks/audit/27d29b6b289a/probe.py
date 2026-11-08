#!/usr/bin/env python3
"""Audit CANONICAL_SHORTCUTS declarations for 27d29b6b289a."""
from __future__ import annotations

import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve()
for parent in HERE.parents:
    for support in (parent / "repo" / "shared" / "runtime", parent / "shared" / "runtime"):
        if (support / "reviewer_support.py").is_file():
            sys.path.insert(0, str(support))
            break
    else:
        continue
    break

from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK_ID = "27d29b6b289a"


def identity(pair):
    return {
        "variant": pair["variant"],
        "split": pair["split"],
        "pair_index": pair["pair_index"],
    }


def main():
    root = find_root(__file__)
    generator, source, source_sha = load_selected_generator(TASK_ID, root=root)
    pairs = canonical_pairs(TASK_ID, root=root, labeled_only=True)
    declarations = dict(generator.CANONICAL_SHORTCUTS)
    results = {}
    for name, rival in declarations.items():
        rows = []
        for pair in pairs:
            try:
                predicted = rival(pair["input"])
                rows.append({
                    "pair": identity(pair),
                    "fits": predicted == pair["output"],
                    "error": None,
                })
            except Exception as exc:
                rows.append({
                    "pair": identity(pair),
                    "fits": False,
                    "error": f"{type(exc).__name__}: {exc}",
                })
        results[name] = {
            "checked": len(rows),
            "fits": sum(row["fits"] for row in rows),
            "mismatches": sum(not row["fits"] and row["error"] is None for row in rows),
            "errors": sum(row["error"] is not None for row in rows),
            "rows": rows,
        }

    witness = next(
        pair for pair in pairs
        if pair["variant"] == 0 and pair["split"] == "train" and pair["pair_index"] == 0
    )
    witness_outputs = {
        name: rival(witness["input"]) for name, rival in declarations.items()
    }
    report = {
        "schema": "audit-27d29b6b289a-canonical-shortcuts-v1",
        "task_id": TASK_ID,
        "generator_source": str(source.relative_to(root)),
        "generator_sha256": source_sha,
        "declared_rule_hash": generator.RULE_HASH,
        "labeled_canonical_pairs": len(pairs),
        "shortcut_results": results,
        "witness_pair": identity(witness),
        "generator_domain_errors_on_witness": generator.self_check(witness["input"]),
        "input": witness["input"],
        "canonical_output": witness["output"],
        "rival_outputs": witness_outputs,
        "witness_matches": {
            name: output == witness["output"] for name, output in witness_outputs.items()
        },
        "lesson_competitor_names": sorted(generator.LESSON_COMPETITORS),
        "conclusion": (
            "Every CANONICAL_SHORTCUTS entry violates that declaration's contract: "
            "repair_without_color_cycle fits 0/8 canonicals, cycle_visible_only fits "
            "0/8, and numeric_sorted_cycle fits 4/8. These functions are useful "
            "LESSON_COMPETITORS, but are not canonical-fitting shortcuts."
        ),
    }
    out = HERE.parent / "probe.json"
    inp = HERE.parent / "input.json"
    out.write_text(json.dumps(report, indent=2) + "\n")
    inp.write_text(json.dumps({"input": witness["input"]}, indent=2) + "\n")
    print(json.dumps({
        "out": str(out),
        "input": str(inp),
        "generator_sha256": source_sha,
        "declared_rule_hash": generator.RULE_HASH,
        "counts": {
            name: {k: row[k] for k in ("checked", "fits", "mismatches", "errors")}
            for name, row in results.items()
        },
    }, indent=2))


if __name__ == "__main__":
    main()
