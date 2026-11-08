"""Findings-only audit of a cyan-bbox-derived repeat-count shortcut.

Run both modes through the packet's review.py run entrypoint. Racket labels
are materialized separately by the supported arcpuzzles apply CLI.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK_ID = "87aae821984d"
SEED = 87002026
HERE = Path(__file__).resolve().parent
ROOT = find_root(__file__)
GEN, SOURCE, SOURCE_SHA = load_selected_generator(TASK_ID, root=ROOT)


def dump(name, value):
    (HERE / name).write_text(json.dumps(value, indent=2) + "\n")


def read(name):
    return json.loads((HERE / name).read_text())


def bbox_count_rival(grid):
    """Ignore yellow; derive repeat count only from the cyan tight bbox."""
    cyan = {(r, c) for r, row in enumerate(grid)
            for c, color in enumerate(row) if color == 8}
    r0, r1 = min(r for r, _ in cyan), max(r for r, _ in cyan)
    c0, c1 = min(c for _, c in cyan), max(c for _, c in cyan)
    height, width = r1 - r0 + 1, c1 - c0 + 1
    repeats = 1 + (3 - height) + 2 * (3 - width)
    tile = [[8 if (r1 - 2 + r, c1 - 2 + c) in cyan else 0
             for c in range(3)] for r in range(3)]
    return [row * repeats for row in tile]


def prepare():
    cases = []
    for band in (None, "easy", "medium", "hard"):
        for index in range(7):
            grid = GEN.generate(SEED, index, difficulty=band)
            cases.append({
                "case_id": f"ordinary-{band}-{index}",
                "origin": "generated_default",
                "seed": SEED, "sample_index": index,
                "difficulty": band, "overrides": {}, "input": grid,
            })
    for index, count in enumerate((2, 3, 4, 1)):
        overrides = {"n_4_cells": count}
        grid = GEN.generate(SEED, index, difficulty="medium", **overrides)
        cases.append({
            "case_id": f"generated-counterexample-{index}",
            "origin": "generated_override",
            "seed": SEED, "sample_index": index,
            "difficulty": "medium", "overrides": overrides, "input": grid,
        })
    for item in canonical_pairs(TASK_ID, root=ROOT):
        cases.append({
            "case_id": f"canonical-{item['variant']}-{item['split']}-{item['pair_index']}",
            "origin": "canonical_authoring_pair",
            "variant": item["variant"], "split": item["split"],
            "pair_index": item["pair_index"], "input": item["input"],
            "canonical_output": item["output"],
        })
    for case in cases:
        case["self_check"] = GEN.self_check(case["input"])
        case["observed_axes"] = GEN.observe_overrides(case["input"])
        case["rival_output"] = bbox_count_rival(case["input"])
        assert case["self_check"] == [], case
    dump("input.json", [row["input"] for row in cases])
    dump("cases.json", {"task_id": TASK_ID, "generator_sha256": SOURCE_SHA,
                        "generator_path": str(SOURCE.relative_to(ROOT)),
                        "declared_rule_hash": GEN.RULE_HASH, "cases": cases})
    print(json.dumps({"prepared": len(cases), "generator_sha256": SOURCE_SHA,
                      "racket_labels": "pending"}))


def verify():
    prepared = read("cases.json")
    receipt = read("racket.json")
    assert prepared["generator_sha256"] == SOURCE_SHA
    assert receipt["generator_sha256"] == SOURCE_SHA
    assert receipt["rule_hash_matches_catalog"] is True
    cases = prepared["cases"]
    results = receipt["results"]
    assert len(results) == len(cases)
    for case, result in zip(cases, results):
        assert result["error"] is None, result
        case["racket_output"] = result["output"]
        case["rival_matches_racket"] = case["rival_output"] == result["output"]
        assert GEN.rule_mirror(case["input"]) == result["output"]
        if "canonical_output" in case:
            assert case["canonical_output"] == result["output"]
    ordinary = [case for case in cases if case["origin"] == "generated_default"]
    witnesses = [case for case in cases if case["origin"] == "generated_override"]
    canonical = [case for case in cases if case["origin"] == "canonical_authoring_pair"]
    assert all(case["rival_matches_racket"] for case in ordinary)
    assert all(not case["rival_matches_racket"] for case in witnesses)
    canonical_shortcuts = {}
    for name, rival in GEN.CANONICAL_SHORTCUTS.items():
        matches = [rival(case["input"]) == case["racket_output"] for case in canonical]
        canonical_shortcuts[name] = {"matches": sum(matches), "denominator": len(matches)}
        assert all(matches), name
    lessons = []
    for band in (None, "easy", "medium", "hard"):
        band_cases = [case for case in ordinary if case["difficulty"] == band]
        for start in range(GEN.LESSON_SCHEDULE_PERIOD):
            window = band_cases[start:start + GEN.EXAMPLES_NEEDED + 1]
            pairs = [{"input": case["input"], "output": case["racket_output"]}
                     for case in window]
            rotations = []
            for query_index in range(len(pairs)):
                demos = [pair for i, pair in enumerate(pairs) if i != query_index]
                reasons = GEN.lesson_identifiable(demos, pairs[query_index])
                declared_refutations = {
                    name: [i for i, demo in enumerate(demos)
                           if rival(demo["input"]) != demo["output"]]
                    for name, rival in GEN.LESSON_COMPETITORS.items()
                }
                survived = all(bbox_count_rival(demo["input"]) == demo["output"]
                               for demo in demos)
                query_matched = bbox_count_rival(pairs[query_index]["input"]) == pairs[query_index]["output"]
                assert reasons == []
                assert all(declared_refutations.values())
                assert survived and query_matched
                rotations.append({"query_index": query_index,
                                  "lesson_identifiable_reasons": reasons,
                                  "declared_rival_refuting_demo_indices": declared_refutations,
                                  "bbox_count_rival_fits_all_demos": survived,
                                  "bbox_count_rival_matches_query": query_matched})
            lessons.append({"difficulty": band, "start_index": start,
                            "case_ids": [case["case_id"] for case in window],
                            "production_query_index": len(pairs) - 1,
                            "rotations": rotations})
    identity_keys = ["generator_sha256", "executed_rule_hash", "catalog_rule_hash", "rule_text_sha256",
                     "rule_hash_matches_catalog", "command", "cwd"]
    identity = {key: receipt.get(key) for key in identity_keys}
    witness = witnesses[0]
    counterexample = {
        "task_id": TASK_ID, "finding_id": "A87-1", "finding_kind": "reproduced_distribution_shortcut",
        "identity": identity, "rival": "bbox_count_rival",
        "rival_description": "Ignore yellow; repeat bottom/right-aligned cyan tile 1 + (3 - bbox_height) + 2 * (3 - bbox_width) times.",
        "documented_domain": True,
        "domain_basis": "Current generator itself emits the exact input with accepted n_4_cells=2 override; self_check returns []; observed count is exact.",
        "generated_or_authored": "generated using documented override, not an authored grid",
        **witness,
        "source_probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "racket_receipt": "checks/audit/87aae821984d/racket.json",
        "all_cases": "checks/audit/87aae821984d/cases-labelled.json",
    }
    dump("counterexample.json", counterexample)
    dump("cases-labelled.json", {"task_id": TASK_ID, "identity": identity, "cases": cases})
    summary = {
        "task_id": TASK_ID, "finding_id": "A87-1", "identity": identity,
        "seed": SEED, "default_sample_index_range_inclusive": [0, 6],
        "difficulty_values": [None, "easy", "medium", "hard"],
        "racket_cases": {"passed": len(cases), "denominator": len(cases)},
        "self_check": {"accepted": len(cases), "denominator": len(cases)},
        "ordinary_unique_inputs": len({json.dumps(case["input"]) for case in ordinary}),
        "ordinary_rival_matches": {"matches": sum(case["rival_matches_racket"] for case in ordinary), "denominator": len(ordinary)},
        "generated_override_rival_matches": {"matches": sum(case["rival_matches_racket"] for case in witnesses), "denominator": len(witnesses)},
        "canonical_new_rival_matches": {"matches": sum(case["rival_matches_racket"] for case in canonical), "denominator": len(canonical)},
        "declared_canonical_shortcuts": canonical_shortcuts,
        "lesson_policy": {"demonstrations": GEN.EXAMPLES_NEEDED, "production_query": "fourth consecutive generated sample", "starts": list(range(GEN.LESSON_SCHEDULE_PERIOD)), "overlapping_windows": True},
        "production_lessons": {"declared_contract_passes": len(lessons), "new_rival_survives": len(lessons), "denominator": len(lessons)},
        "query_rotations": {"declared_contract_passes": sum(len(row["rotations"]) for row in lessons), "new_rival_survives": sum(len(row["rotations"]) for row in lessons), "denominator": sum(len(row["rotations"]) for row in lessons)},
        "lessons": lessons,
        "scope_limit": "One fixed seed and all four start residues in each listed difficulty. Static source ties default repeat count to bbox for every default draw. The new rival is a generated-distribution shortcut, not claimed to fit all canonical pairs; counterexamples use supported overrides.",
    }
    dump("summary.json", summary)
    print(json.dumps({key: value for key, value in summary.items() if key != "lessons"}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("prepare", "verify"))
    args = parser.parse_args()
    (prepare if args.mode == "prepare" else verify)()
