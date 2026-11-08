"""Source-bound audit of an ordered lesson's query-rotation limitation.

Authoring evidence only.  The rival is an intentional diagnostic hypothesis,
not an attempted visible-only solve and not a proposed reference rule.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK_ID = "28b87bd4c441"
HERE = Path(__file__).resolve().parent


def dump(name, value):
    (HERE / name).write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def ignore_pure_left_translation(grid):
    """Copy normally except a purely leftward request yields an empty grid."""
    h, w = len(grid), len(grid[0])
    blob = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 5]
    marker = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 2]
    if not blob or len(marker) != 1:
        raise ValueError("expected a component and one marker")
    top = min(r for r, c in blob)
    left = min(c for r, c in blob)
    mr, mc = marker[0]
    dr, dc = mr - top, mc - left
    output = [[0] * w for _ in range(h)]
    if dr == 0 and dc < 0:
        return output
    for r, c in blob:
        rr, cc = r + dr, c + dc
        if not (0 <= rr < h and 0 <= cc < w):
            raise ValueError("unexpected out-of-bounds input")
        output[rr][cc] = 5
    return output


def prepare():
    root = find_root(__file__)
    generator, source, digest = load_selected_generator(TASK_ID, root=root)
    semantic_path = HERE / "combined/checks/28b87bd4c441_audit_semantic_gate.json"
    semantic_bytes = semantic_path.read_bytes()
    audit = json.loads(semantic_bytes)["audits"][0]
    example = next(
        row for row in audit["lessons"]["rotations"]["examples"]
        if any("row_left_hollow_l3" in warning for warning in row["warnings"])
    )
    instance = example["instance"]
    pairs = instance["train"] + instance["test"]
    query_index = example["query_index"]
    train_indices = example["train_indices"]
    canonical = canonical_pairs(TASK_ID, root=root, labeled_only=True)
    assert len(canonical) == 4
    assert len(pairs) == 9 and len(train_indices) == 8
    assert all(generator.self_check(pair["input"]) == [] for pair in pairs)
    assert all(ignore_pure_left_translation(pair["input"]) == pair["output"] for pair in canonical)
    assert all(ignore_pure_left_translation(pairs[i]["input"]) == pairs[i]["output"] for i in train_indices)
    assert ignore_pure_left_translation(pairs[query_index]["input"]) != pairs[query_index]["output"]
    replay_index = example["sample_index"] + query_index
    replay_input = generator.generate(example["seed"], replay_index, difficulty=example["band"])
    assert replay_input == pairs[query_index]["input"]
    dump("inputs.json", [pair["input"] for pair in canonical] + [pair["input"] for pair in pairs])
    dump("counterexample_input.json", pairs[query_index]["input"])
    dump("rotation_lesson.json", {
        "task_id": TASK_ID,
        "original_instance": instance,
        "rotation_query_index": query_index,
        "rotation_train_indices": train_indices,
        "train": [pairs[i] for i in train_indices],
        "test": [pairs[query_index]],
        "labels_origin": "public isolated semantic gate; independently rechecked by public apply",
    })
    report = {
        "finding_id": "A1",
        "classification": "reproduced query-rotation limitation; no ordered-production label defect",
        "task_id": TASK_ID,
        "generator_source": str(source.relative_to(root)),
        "generator_sha256": digest,
        "probe_source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "semantic_report": "checks/audit/28b87bd4c441/combined/checks/28b87bd4c441_audit_semantic_gate.json",
        "semantic_report_sha256": hashlib.sha256(semantic_bytes).hexdigest(),
        "rival": "ignore_pure_left_translation",
        "rival_intent": "intentional diagnostic hypothesis",
        "canonical_labeled_pairs": len(canonical),
        "canonical_train_pairs": sum(p["split"] == "train" for p in canonical),
        "rotation_demo_count": len(train_indices),
        "rotation_query_pair_index": query_index,
        "rotation_train_indices": train_indices,
        "seed": example["seed"],
        "difficulty": example["band"],
        "requested_lesson_start": example["sample_index"],
        "reproducing_query_sample_index": replay_index,
        "replayed_query_input_equal": True,
        "query_self_check": generator.self_check(pairs[query_index]["input"]),
        "query_observed_profile": generator.observe_overrides(pairs[query_index]["input"]),
        "query_in_generator_domain": True,
        "query_input": pairs[query_index]["input"],
        "query_output_from_semantic_gate": pairs[query_index]["output"],
        "query_rival_output": ignore_pure_left_translation(pairs[query_index]["input"]),
        "original_production_hook": generator.lesson_identifiable(instance["train"], instance["test"][0]),
        "rotation_hook": generator.lesson_identifiable([pairs[i] for i in train_indices], pairs[query_index]),
        "public_apply_receipt": "checks/audit/28b87bd4c441/racket.json",
        "public_apply_verified": False,
    }
    dump("counterexample.json", report)
    print(json.dumps({key: report[key] for key in ["generator_sha256", "canonical_labeled_pairs", "rotation_demo_count", "rotation_query_pair_index", "seed", "difficulty", "reproducing_query_sample_index", "query_self_check", "original_production_hook", "rotation_hook"]}))


if __name__ == "__main__":
    prepare()
