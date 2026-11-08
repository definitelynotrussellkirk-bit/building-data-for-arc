#!/usr/bin/env python3
"""Verify retained supported-Racket evidence without executing an oracle."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def sha(value):
    if not isinstance(value, bytes):
        value = json.dumps(value, separators=(",", ":"), sort_keys=True).encode()
    return hashlib.sha256(value).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--evidence", type=Path, required=True)
    args = parser.parse_args()
    evidence = args.evidence
    screening = json.loads((evidence / "screening.json").read_text())
    applied = json.loads((evidence / "racket.json").read_text())
    episode_lines = (evidence / "episode.jsonl").read_text().splitlines()
    assert len(episode_lines) == 1
    episode = json.loads(episode_lines[0])
    task = screening["task_id"]
    assert applied["task_id"] == episode["task_id"] == task
    actual_source_sha = sha((args.repo / "generators" / task / "generator.py").read_bytes())
    assert actual_source_sha == screening["generator_sha256"] == applied["generator_sha256"]
    assert episode["provenance"]["generator_sha256"] == actual_source_sha
    assert applied["executed_rule_hash"] == episode["executed_rule_hash"] == screening["rule_hash_12"]
    assert applied["rule_hash_matches_catalog"] is True
    assert applied["reference"] == "canonical"
    canonical_source_sha = sha(episode["program"].encode())
    assert {record["exact_sha256"] for record in screening["canonical_source_records"]} == {canonical_source_sha}
    # apply.rule_text_sha256 identifies the wrapped executable callable, not
    # the original canonical program. Retain those distinct identities below.
    assert sha(" ".join(episode["program"].split()).encode())[:12] == applied["executed_rule_hash"]
    assert len(applied["results"]) == len(screening["racket_apply_records"]) == 16
    windows = {}
    canonical_fit = 0
    for record, result in zip(screening["racket_apply_records"], applied["results"], strict=True):
        assert result["index"] == record["apply_index"]
        assert result["error"] is None and result["valid_output"] is True
        assert result["generator_domain"] == {"status": "valid", "errors": []}
        assert sha(result["input"]) == record["input_sha256"] == result["input_sha256"]
        assert result["output"] == record["expected_reference_output"]
        match = result["output"] == record["rival_output"]
        if record["role"] == "canonical":
            assert match
            canonical_fit += 1
        else:
            window = windows.setdefault(record["difficulty"], [])
            window.append({"sample_index": record["sample_index"], "rival_matches_racket": match,
                           "input": result["input"], "racket_output": result["output"],
                           "rival_output": record["rival_output"]})
    assert canonical_fit == 4
    for band, window in windows.items():
        assert [row["sample_index"] for row in window] == [0, 1, 2, 3]
        assert [row["rival_matches_racket"] for row in window] == [True, True, True, False]
    medium = windows["medium"]
    assert episode["seed"] == 67 and episode["sample_indices"] == [0, 1, 2, 3]
    assert episode["rejections"] == [] and len(episode["train"]) == 3 and len(episode["test"]) == 1
    assert episode["lesson_check"]["status"] == "not_declared"
    assert episode["provenance"]["demonstration_policy"]["requested_n_train"] is None
    assert episode["provenance"]["demonstration_policy"]["resolved_n_train"] == 3
    for pair, actual in zip(episode["train"] + episode["test"], medium, strict=True):
        assert pair == {"input": actual["input"], "output": actual["racket_output"]}
    queries = {band: {"racket_output": window[3]["racket_output"],
                      "rival_output": window[3]["rival_output"],
                      "mismatching_cells": [[r, c] for r in range(3) for c in range(3)
                                            if window[3]["racket_output"][r][c] != window[3]["rival_output"][r][c]]}
               for band, window in windows.items()}
    assert all(row["mismatching_cells"] == [[0, 0], [2, 2]] for row in queries.values())
    receipt = {
        "schema_version": 1, "status": "PASS", "finding_reproduced": True,
        "finding_id": "A-b2f8fcc010d5-1", "task_id": task,
        "generator_version": screening["generator_version"],
        "generator_sha256": actual_source_sha, "rule_hash_12": applied["executed_rule_hash"],
        "canonical_program_source_sha256": canonical_source_sha,
        "executed_callable_sha256": applied["rule_text_sha256"],
        "canonical_racket_pairs_matching_rival": {"pass": 4, "total": 4},
        "racket_labelled_witnesses": {"bands": list(windows), "seed": 67,
                                     "train_indices": [0, 1, 2], "query_index": 3,
                                     "demonstrations_matching_rival": {"pass": 9, "total": 9},
                                     "queries_disagreeing_with_rival": {"count": 3, "total": 3}},
        "racket_inputs_domain_valid": {"pass": 16, "total": 16},
        "supported_generation_replay": {"episodes": 1, "difficulty": "medium", "seed": 67,
                                        "sample_indices": [0, 1, 2, 3], "rejections": 0,
                                        "default_demo_count": 3, "lesson_check_status": "not_declared",
                                        "production_ambiguous_against_named_rival": True},
        "query_witnesses": queries,
        "evidence_sha256": {filename: sha((evidence / filename).read_bytes())
                            for filename in ("screening.json", "input.json", "racket.json", "episode.jsonl")},
        "scope": "One supported production episode and three Racket-labelled four-pair witness windows; finite named-rival evidence.",
    }
    (evidence / "verified.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": "PASS", "finding_id": receipt["finding_id"],
                      "canonical_fit": "4/4", "witness_demo_fit": "9/9",
                      "witness_query_disagreements": "3/3", "production_episode_reproduced": True}, indent=2))


if __name__ == "__main__":
    main()
