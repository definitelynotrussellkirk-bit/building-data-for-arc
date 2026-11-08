"""Finite three-slot closure at one seed, using actual Racket labels."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

from arcpuzzles import Catalog
from reviewer_support import find_root, load_selected_generator

ROOT = find_root(__file__)
OUT = Path(__file__).resolve().parent
TASK = "42a152269589"
SOURCE_SHA256 = "1595b2fdf3cb839e695ebd8cd8bb783d000806c2efb08fefb2ebf94d550c92e8"
SEED = 91999884919982
BANDS = ("easy", "medium", "hard")


def write_json(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def main():
    gen, source_path, source_hash = load_selected_generator(TASK, root=ROOT)
    assert source_hash == SOURCE_SHA256
    assert len(gen.SCHEDULE_PROFILES) == 3
    bindings = {
        f"{namespace}:{name}": fn
        for namespace in ("CANONICAL_SHORTCUTS", "SEMANTIC_RIVALS", "LESSON_COMPETITORS")
        for name, fn in getattr(gen, namespace).items()
    }
    inputs = [{"band": band, "sample_index": index,
               "input": gen.generate(SEED, index, difficulty=band),
               "profile": gen.schedule_profile(SEED, index, band)}
              for band in BANDS for index in range(6)]
    authority = Catalog(ROOT).apply(TASK, [row["input"] for row in inputs],
                                    reference="canonical", timeout=90)
    write_json("apply-receipt.json", authority)
    assert authority["generator_sha256"] == source_hash
    assert authority["rule_hash_matches_catalog"] is True
    assert len(authority["results"]) == 18
    assert all(row["error"] is None for row in authority["results"])
    for row, result in zip(inputs, authority["results"]):
        row["output"] = result["output"]
        row["input_sha256"] = hashlib.sha256(json.dumps(row["input"], separators=(",", ":")).encode()).hexdigest()
        row["self_check"] = gen.self_check(row["input"])
        row["mirror_matches_racket"] = gen.rule_mirror(row["input"]) == row["output"]
        assert not row["self_check"] and row["mirror_matches_racket"]
        row["rival_outputs"] = {name: fn(row["input"]) for name, fn in bindings.items()}
    indexed = {(row["band"], row["sample_index"]): row for row in inputs}

    def evaluate(band, start, query_offset):
        rows = [indexed[(band, index)] for index in range(start, start + 4)]
        query = rows[query_offset]
        demos = [row for i, row in enumerate(rows) if i != query_offset]
        rivals = {
            name: {
                "fits_demos": all(row["rival_outputs"][name] == row["output"] for row in demos),
                "changes_query": query["rival_outputs"][name] != query["output"],
            }
            for name in bindings
        }
        ambiguous_rivals = [name for name, result in rivals.items()
                            if result["fits_demos"] and result["changes_query"]]
        return {
            "band": band, "start": start,
            "train_sample_indices": [row["sample_index"] for row in demos],
            "query_sample_index": query["sample_index"],
            "query_offset": query_offset,
            "ambiguous": bool(ambiguous_rivals), "ambiguous_rivals": ambiguous_rivals,
            "rivals": rivals, "lesson_hook_reasons": gen.lesson_identifiable(demos, query),
        }

    ordered = [evaluate(band, start, 3) for band in BANDS for start in range(3)]
    rotated = [evaluate(band, start, query_offset)
               for band in BANDS for start in range(3) for query_offset in range(4)]
    assert hashlib.sha256(source_path.read_bytes()).hexdigest() == source_hash
    summary = {
        "materialized_unique_pair_positions": len(inputs),
        "unique_inputs": len({row["input_sha256"] for row in inputs}),
        "racket_applications": len(authority["results"]), "racket_errors": 0,
        "self_check_failures": sum(bool(row["self_check"]) for row in inputs),
        "mirror_matches_racket": sum(row["mirror_matches_racket"] for row in inputs),
        "ordered_lessons": len(ordered),
        "ordered_ambiguities": sum(row["ambiguous"] for row in ordered),
        "ordered_hook_warnings": sum(bool(row["lesson_hook_reasons"]) for row in ordered),
        "rotated_holdouts": len(rotated),
        "rotated_ambiguities": sum(row["ambiguous"] for row in rotated),
        "rotated_hook_warnings": sum(bool(row["lesson_hook_reasons"]) for row in rotated),
        "declaration_bindings": len(bindings),
        "unique_rival_callables": len({id(fn) for fn in bindings.values()}),
    }
    report = {
        "schema": "42a152269589-fixed-seed-cyclic-starts-v1",
        "status": "completed", "production_status": "ambiguous" if summary["ordered_ambiguities"] else "no_ambiguity_found",
        "rotation_status": "ambiguous" if summary["rotated_ambiguities"] else "no_ambiguity_found",
        "rotation_policy": "diagnostic", "task_id": TASK,
        "generator_sha256": source_hash, "executed_rule_hash": authority["executed_rule_hash"],
        "rule_callable_sha256": authority["rule_text_sha256"],
        "command": [sys.executable, *sys.argv], "cwd": str(Path.cwd()),
        "seed": SEED, "bands": BANDS, "start_residues": [0, 1, 2],
        "profiles": list(gen.SCHEDULE_PROFILES),
        "source_declares_LESSON_SCHEDULE_PERIOD": hasattr(gen, "LESSON_SCHEDULE_PERIOD"),
        "summary": summary, "inputs": inputs, "ordered_lessons": ordered, "rotated_holdouts": rotated,
        "scope": "All three starting residues at one fixed seed in each band; 18 generated pairs reused for nine ordered lessons and 36 holdouts. No proof over all seeds or undeclared rivals, no arbitrary-rotation support or approval claimed.",
    }
    write_json("report.json", report)
    print(json.dumps({"generator_sha256": source_hash, "summary": summary}, indent=2))
    assert summary["ordered_ambiguities"] == 0 and summary["ordered_hook_warnings"] == 0


if __name__ == "__main__":
    main()
