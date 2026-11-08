"""Recheck the canonical-compatible rotation-only rival on selected source bytes."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

from arcpuzzles import Catalog
from reviewer_support import canonical_pairs, find_root, load_selected_generator

OUT = Path(__file__).resolve().parent
ROOT = find_root(__file__)
EXPECTED_SOURCE = "1595b2fdf3cb839e695ebd8cd8bb783d000806c2efb08fefb2ebf94d550c92e8"


def write_json(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def main():
    gen, source_path, source_hash = load_selected_generator("42a152269589", root=ROOT)
    assert source_hash == EXPECTED_SOURCE, "This receipt must bind the final reviewed source"
    canonical = canonical_pairs(gen.TASK_ID, root=ROOT, labeled_only=True)
    seed = 91999884919982
    inputs = [gen.generate(seed, i, difficulty="easy") for i in range(4)]
    receipt = Catalog(ROOT).apply(
        gen.TASK_ID, [p["input"] for p in canonical] + inputs,
        reference="canonical", timeout=90,
    )
    write_json("apply-receipt.json", receipt)
    assert receipt["generator_sha256"] == source_hash
    assert receipt["rule_hash_matches_catalog"] is True
    assert all(row["error"] is None for row in receipt["results"])
    n = len(canonical)
    assert n == 8
    assert all(p["output"] == row["output"]
               for p, row in zip(canonical, receipt["results"][:n]))
    lesson = [{"input": grid, "output": row["output"]}
              for grid, row in zip(inputs, receipt["results"][n:])]
    rival = gen.LESSON_COMPETITORS["rotation_only"]
    witness = {
        "input": inputs[2],
        "expected_output": lesson[2]["output"],
        "rival_output": rival(inputs[2]),
        "self_check": gen.self_check(inputs[2]),
        "reflection_required_by_python_mirror": gen.SEMANTIC_WITNESSES["reflection_required"](inputs[2]),
    }
    canonical_fit = {
        name: {"checked": n, "matches": sum(fn(p["input"]) == p["output"] for p in canonical),
               "mismatch_indices": [i for i, p in enumerate(canonical) if fn(p["input"]) != p["output"]]}
        for name, fn in gen.LESSON_COMPETITORS.items()
    }
    assert canonical_fit["rotation_only"]["matches"] == n
    assert not witness["self_check"]
    assert witness["expected_output"] != witness["rival_output"]
    assert witness["reflection_required_by_python_mirror"]
    rotated_fits = all(rival(lesson[i]["input"]) == lesson[i]["output"] for i in (0, 1, 3))
    assert rotated_fits
    assert hashlib.sha256(source_path.read_bytes()).hexdigest() == source_hash
    report = {
        "schema": "42a152269589-final-question-witness-v1", "status": "passed",
        "task_id": gen.TASK_ID, "generator_sha256": source_hash,
        "executed_rule_hash": receipt["executed_rule_hash"],
        "rule_callable_sha256": receipt["rule_text_sha256"],
        "command": [sys.executable, *sys.argv], "cwd": str(Path.cwd()),
        "canonical_variants": len({p["variant"] for p in canonical}),
        "canonical_labeled_pairs": n, "canonical_labels_confirmed_by_racket": n,
        "canonical_rival_fit": canonical_fit,
        "racket_applications": len(receipt["results"]), "racket_errors": 0,
        "recipe": {"seed": seed, "difficulty": "easy", "sample_indices": [0, 1, 2, 3],
                   "witness_sample_index": 2,
                   "profiles": [gen.schedule_profile(seed, i, "easy") for i in range(4)]},
        "witness": witness, "lesson": lesson,
        "ordered_lesson_reasons": gen.lesson_identifiable(lesson[:3], lesson[3]),
        "rotated_train_indices": [0, 1, 3], "rotated_query_index": 2,
        "rotation_only_fits_rotated_demos": rotated_fits,
        "rotated_lesson_reasons": gen.lesson_identifiable([lesson[i] for i in (0, 1, 3)], lesson[2]),
        "scope": "One exact generated four-pair lesson; eight canonical labels; finite evidence only.",
    }
    write_json("input.json", witness["input"])
    write_json("report.json", report)
    print(json.dumps({k: report[k] for k in ["status", "generator_sha256", "canonical_rival_fit",
                                            "racket_applications", "racket_errors",
                                            "ordered_lesson_reasons", "rotated_lesson_reasons"]}, indent=2))


if __name__ == "__main__":
    main()
