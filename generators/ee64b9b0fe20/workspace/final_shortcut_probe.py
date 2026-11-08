#!/usr/bin/env python3
"""Retain a final-source counterexample for every declared canonical shortcut.

Run from the repository through the packet wrapper. The first pass writes an
input and local diagnostic outputs. Run ``arcpuzzles apply`` on that input, then
pass its JSON receipt with ``--racket-receipt`` to bind the final report to the
canonical Racket authority.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK_ID = "ee64b9b0fe20"
BANDS = ("easy", "medium", "hard")


def digest_json(value) -> str:
    return hashlib.sha256(json.dumps(value, separators=(",", ":")).encode()).hexdigest()


def dump(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    parser.add_argument("--racket-receipt")
    args = parser.parse_args()

    root = find_root(__file__)
    gen, source, source_sha = load_selected_generator(TASK_ID, root=root)
    shortcuts = dict(getattr(gen, "CANONICAL_SHORTCUTS", {}))
    if not shortcuts:
        raise RuntimeError("generator declares no CANONICAL_SHORTCUTS")

    pairs = canonical_pairs(TASK_ID, root=root, labeled_only=True)
    canonical = {}
    for name, rival in shortcuts.items():
        rows = []
        for pair in pairs:
            rival_output = rival(pair["input"])
            rows.append({
                "variant": pair["variant"],
                "split": pair["split"],
                "pair_index": pair["pair_index"],
                "rival_matches_label": rival_output == pair["output"],
            })
        canonical[name] = {
            "fits_all_labeled_pairs": all(row["rival_matches_label"] for row in rows),
            "pairs": rows,
        }

    witness = None
    for band in BANDS:
        for seed in range(100):
            for sample_index in range(6):
                grid = gen.generate(seed, sample_index, difficulty=band)
                intended = gen.rule_mirror(grid)
                for name, rival in shortcuts.items():
                    rival_output = rival(grid)
                    if rival_output != intended:
                        witness = {
                            "shortcut": name,
                            "seed": seed,
                            "sample_index": sample_index,
                            "difficulty": band,
                            "overrides": {},
                            "input": grid,
                            "intended_local": intended,
                            "rival_output": rival_output,
                            "self_check_errors": gen.self_check(grid),
                        }
                        break
                if witness:
                    break
            if witness:
                break
        if witness:
            break
    if witness is None:
        raise RuntimeError("no generated counterexample found in bounded search")

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    dump(out / "input.json", witness["input"])
    dump(out / "intended_local.json", witness["intended_local"])
    dump(out / "rival_output.json", witness["rival_output"])

    receipt_summary = None
    if args.racket_receipt:
        receipt_path = Path(args.racket_receipt)
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        result = receipt["results"][0]
        racket_output = result["output"]
        receipt_summary = {
            "path": str(receipt_path),
            "executed_rule_hash": receipt.get("executed_rule_hash"),
            "generator_sha256": receipt.get("generator_sha256"),
            "rule_hash_matches_catalog": receipt.get("rule_hash_matches_catalog"),
            "valid_output": result.get("valid_output"),
            "input_sha256": result.get("input_sha256"),
            "output_sha256": result.get("output_sha256"),
            "local_intended_matches_racket": racket_output == witness["intended_local"],
            "rival_differs_from_racket": racket_output != witness["rival_output"],
        }

    report = {
        "schema": "ee64b9b0fe20-final-shortcut-probe-v1",
        "task_id": TASK_ID,
        "generator_source": str(source.relative_to(root)),
        "generator_sha256": source_sha,
        "declared_rule_hash": getattr(gen, "RULE_HASH", None),
        "canonical_shortcuts": canonical,
        "bounded_search": {
            "bands": list(BANDS),
            "seed_range": "0..99",
            "sample_index_range": "0..5",
            "first_witness": {
                key: value for key, value in witness.items()
                if key not in {"input", "intended_local", "rival_output"}
            },
        },
        "files": {
            "input": "input.json",
            "intended_local": "intended_local.json",
            "rival_output": "rival_output.json",
        },
        "hashes": {
            "input": digest_json(witness["input"]),
            "intended_local": digest_json(witness["intended_local"]),
            "rival_output": digest_json(witness["rival_output"]),
        },
        "racket_receipt": receipt_summary,
    }
    dump(out / "probe.json", report)
    print(json.dumps({
        "report": str(out / "probe.json"),
        "generator_sha256": source_sha,
        "shortcut": witness["shortcut"],
        "recipe": {key: witness[key] for key in ("seed", "sample_index", "difficulty", "overrides")},
        "racket_bound": receipt_summary is not None,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
