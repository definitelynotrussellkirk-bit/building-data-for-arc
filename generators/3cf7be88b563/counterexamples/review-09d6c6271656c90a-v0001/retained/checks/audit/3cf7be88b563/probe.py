"""Read-only, source-bound audit probes; run through packet review.py run."""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path

from reviewer_support import canonical_pairs, canonical_path, find_root, load_selected_generator

TASK = "3cf7be88b563"
HERE = Path(__file__).resolve().parent
ROOT = find_root(__file__)
MODULE, SOURCE, SOURCE_SHA = load_selected_generator(TASK, root=ROOT)
CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))
DIAGONAL = ((-1, -1), (-1, 1), (1, -1), (1, 1))


def digest(value):
    return hashlib.sha256(json.dumps(value, separators=(",", ":")).encode()).hexdigest()


def rule_identity():
    rows = [json.loads(line) for line in canonical_path(ROOT).read_text().splitlines()
            if line.strip() and json.loads(line).get("task_id") == TASK]
    assert len(rows) == 1
    program = rows[0]["program_solution"]
    return {"rule_sha256": hashlib.sha256(program.encode()).hexdigest(),
            "normalized_rule_sha256": hashlib.sha256(" ".join(program.split()).encode()).hexdigest()}


def has_neighbor(grid, r, c, value, offsets):
    return any(0 <= r + dr < len(grid) and 0 <= c + dc < len(grid[0])
               and grid[r + dr][c + dc] == value for dr, dc in offsets)


def blue_only(grid):
    """Lesson rival: preserve nonzero cells; expand only blue to seven."""
    result = deepcopy(grid)
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value == 0 and has_neighbor(grid, r, c, 1, CARDINAL):
                result[r][c] = 7
    return result


def red_priority(grid):
    """Canonical-fitting rival: red-X wins if both halos hit a zero cell."""
    result = deepcopy(grid)
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value:
                continue
            if has_neighbor(grid, r, c, 2, DIAGONAL):
                result[r][c] = 4
            elif has_neighbor(grid, r, c, 1, CARDINAL):
                result[r][c] = 7
    return result


def overlapping_halos(grid):
    return [[r, c] for r, row in enumerate(grid) for c, value in enumerate(row)
            if value == 0 and has_neighbor(grid, r, c, 1, CARDINAL)
            and has_neighbor(grid, r, c, 2, DIAGONAL)]


def generated(seed, index, band, overrides=None):
    overrides = dict(overrides or {})
    grid = MODULE.generate(seed, index, difficulty=band, **overrides)
    return {"seed": seed, "sample_index": index, "difficulty": band,
            "overrides": overrides, "input": grid,
            "input_sha256": digest(grid),
            "self_check": MODULE.self_check(deepcopy(grid), difficulty=band),
            "marker_counts": {str(color): sum(row.count(color) for row in grid)
                              for color in (1, 2)},
            "overlapping_halo_cells": overlapping_halos(grid)}


def discover():
    identity = {"task_id": TASK, "generator_sha256": SOURCE_SHA, **rule_identity()}
    pairs = canonical_pairs(TASK, root=ROOT, labeled_only=True)
    counts = {}
    first_lesson = None
    first_missing = None
    for band in ("easy", "medium", "hard"):
        stats = Counter()
        inputs = set()
        for seed in range(512):
            examples = [generated(seed, index, band) for index in range(4)]
            for row in examples:
                stats["inputs"] += 1
                stats["missing_red"] += row["marker_counts"]["2"] == 0
                stats["validator_rejections"] += bool(row["self_check"])
                stats["overlap_inputs"] += bool(row["overlapping_halo_cells"])
                inputs.add(row["input_sha256"])
                if first_missing is None and row["marker_counts"]["2"] == 0:
                    first_missing = row
            if (all(row["marker_counts"]["2"] == 0 for row in examples[:3])
                    and examples[3]["marker_counts"]["2"] > 0
                    and len({row["input_sha256"] for row in examples}) == 4):
                stats["candidate_ambiguous_3plus1_lessons"] += 1
                if first_lesson is None:
                    first_lesson = examples
        counts[band] = {**dict(stats), "unique_inputs": len(inputs),
                        "seeds": [0, 511], "sample_indices": [0, 1, 2, 3],
                        "raw_lessons": 512}
    assert first_missing is not None
    assert first_lesson is not None, "No all-blue lesson found within bound"
    overlap = None
    for seed in range(128):
        row = generated(seed, 0, "easy", {"min_separation": 2})
        if row["overlapping_halo_cells"]:
            overlap = row
            break
    assert overlap is not None
    report = {**identity,
              "observed_domain": "generated default draws; optional legal min_separation=2 override",
              "raw_generation_counts_not_racket_census": counts,
              "declared_semantic_names": {
                  name: sorted(getattr(MODULE, name, {}))
                  for name in ("SEMANTIC_WITNESSES", "SEMANTIC_RIVALS", "LESSON_COMPETITORS", "CANONICAL_SHORTCUTS")},
              "canonical_pairs": len(pairs),
              "canonical_red_priority_matches": sum(red_priority(p["input"]) == p["output"] for p in pairs),
              "canonical_blue_only_matches": sum(blue_only(p["input"]) == p["output"] for p in pairs),
              "first_missing_red": first_missing,
              "lesson_candidate": first_lesson,
              "overlap_override_witness": overlap,
              "racket_input_order": ["canonical_0", "canonical_1", "canonical_2", "canonical_3",
                                      "lesson_demo_0", "lesson_demo_1", "lesson_demo_2", "lesson_query", "overlap_override"]}
    inputs = [p["input"] for p in pairs] + [row["input"] for row in first_lesson] + [overlap["input"]]
    assert len(inputs) <= 64
    (HERE / "discovery.json").write_text(json.dumps(report, indent=2) + "\n")
    (HERE / "input.json").write_text(json.dumps(inputs, separators=(",", ":")) + "\n")
    print(json.dumps({**identity, "counts": counts,
                      "lesson_seed": first_lesson[0]["seed"], "lesson_band": first_lesson[0]["difficulty"],
                      "overlap_seed": overlap["seed"], "racket_inputs": len(inputs)}, indent=2))


def differences(expected, actual):
    assert len(expected) == len(actual)
    assert all(len(left) == len(right) for left, right in zip(expected, actual))
    return [{"row": r, "column": c, "racket": value, "rival": actual[r][c]}
            for r, row in enumerate(expected) for c, value in enumerate(row)
            if value != actual[r][c]]


def verify():
    discovery = json.loads((HERE / "discovery.json").read_text())
    applied = json.loads((HERE / "racket.json").read_text())
    lesson = json.loads((HERE / "lesson.jsonl").read_text())
    inputs = json.loads((HERE / "input.json").read_text())
    pairs = canonical_pairs(TASK, root=ROOT, labeled_only=True)
    assert SOURCE_SHA == discovery["generator_sha256"] == applied["generator_sha256"]
    assert SOURCE_SHA == lesson["provenance"]["generator_sha256"]
    assert rule_identity()["rule_sha256"] == discovery["rule_sha256"]
    assert applied["rule_hash_matches_catalog"] is True
    assert applied["executed_rule_hash"] == discovery["normalized_rule_sha256"][:12]
    records = applied["results"]
    assert len(records) == len(inputs) == 9
    assert all(row["valid_output"] and row["error"] is None for row in records)
    assert [row["input"] for row in records] == inputs
    assert [row["output"] for row in records[:4]] == [row["output"] for row in pairs]
    assert all(red_priority(row["input"]) == row["output"] for row in records[:4])
    generated_rows = discovery["lesson_candidate"] + [discovery["overlap_override_witness"]]
    for row, record in zip(generated_rows, records[4:]):
        fresh = generated(row["seed"], row["sample_index"], row["difficulty"], row["overrides"])
        assert fresh == row
        assert fresh["input"] == record["input"]
        assert fresh["self_check"] == []
    assert lesson["sample_indices"] == [0, 1, 2, 3]
    assert lesson["rejections"] == []
    actual_pairs = lesson["train"] + lesson["test"]
    assert len(lesson["train"]) == 3 and len(lesson["test"]) == 1
    assert actual_pairs == [{"input": row["input"], "output": row["output"]}
                            for row in records[4:8]]
    demo_matches = [blue_only(row["input"]) == row["output"] for row in lesson["train"]]
    assert demo_matches == [True, True, True]
    query = lesson["test"][0]
    query_rival = blue_only(query["input"])
    query_differences = differences(query["output"], query_rival)
    assert query_differences
    overlap = records[8]
    overlap_rival = red_priority(overlap["input"])
    overlap_differences = differences(overlap["output"], overlap_rival)
    assert overlap_differences
    identity = {"task_id": TASK, "generator_sha256": SOURCE_SHA,
                **rule_identity(), "executed_rule_callable_sha256": applied["rule_text_sha256"],
                "executed_rule_hash": applied["executed_rule_hash"]}
    report = {**identity, "verification": "PASS: findings reproduced; this is not a generator pass",
              "canonical_racket_matches": {"matched": 4, "total": 4},
              "public_apply": {"valid_outputs": 9, "total": 9, "errors": 0},
              "default_lesson": {
                  "seed": 191, "difficulty": "medium", "overrides": {},
                  "demonstration_count": 3, "query_policy": "fourth accepted pair; no rotations claimed",
                  "accepted_sample_indices": [0, 1, 2, 3], "rejections": [],
                  "generated_again_matches_saved": True, "self_check": [[], [], [], []],
                  "domain_classification": "Ordinary no-override generated support; missing red markers contradict documented 1-2 red invariant. Not merely validator-only.",
                  "lesson_rival": "blue_only", "demo_matches": demo_matches,
                  "query_differences": query_differences,
                  "rival_is_canonical_shortcut": False,
                  "canonical_matches": discovery["canonical_blue_only_matches"],
                  "canonical_total": discovery["canonical_pairs"],
                  "input": query["input"], "racket_output": query["output"], "rival_output": query_rival},
              "priority_shortcut": {
                  "rival": "red_priority", "canonical_matches": 4, "canonical_total": 4,
                  "default_overlap_inputs": 0, "raw_default_inputs": 6144,
                  "seed": 2, "sample_index": 0, "difficulty": "easy", "overrides": {"min_separation": 2},
                  "self_check": [], "domain_classification": "Generated from advertised AXES min_separation=2; minimum Manhattan distance 3 also satisfies SUMMARY's >=3 wording, though INVARIANTS separately excludes within distance 3. Not default support and not merely validator-only.",
                  "input": overlap["input"], "racket_output": overlap["output"], "rival_output": overlap_rival,
                  "differences": overlap_differences,
                  "limit": "A default-distribution coverage gap; not a demonstrated default query ambiguity for this priority rival."},
              "racket_evidence": "checks/audit/3cf7be88b563/racket.json",
              "lesson_evidence": "checks/audit/3cf7be88b563/lesson.jsonl",
              "command_receipts": "checks/audit/3cf7be88b563/commands.json"}
    (HERE / "verification.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({**identity, "racket_outputs_valid": "9/9", "canonical_match": "4/4",
                      "blue_only_demo_matches": demo_matches, "query_difference_cells": len(query_differences),
                      "red_priority_difference_cells": overlap_differences,
                      "verification": report["verification"]}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["discover", "verify"])
    args = parser.parse_args()
    if args.mode == "discover":
        discover()
    else:
        verify()
