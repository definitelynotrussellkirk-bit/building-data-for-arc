#!/usr/bin/env python3
"""Audit the unchanged native export, including its automatic four-demo policy."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

from arcpuzzles.parametric_worker import _real_evaluator
from reviewer_support import load_selected_generator
from border_probe import RIVAL, TASK


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        raise FileExistsError(args.out)
    folder = Path(__file__).resolve().parent
    source_file = folder / "native-default.jsonl"
    episodes = [json.loads(line) for line in source_file.read_text().splitlines()]
    assert len(episodes) == 1
    episode = episodes[0]
    baseline, _, baseline_sha = load_selected_generator(TASK, root=Path.cwd())
    proposal = folder / "proposal/generators" / TASK / "generator.py"
    spec = importlib.util.spec_from_file_location("native_lesson_proposal", proposal)
    candidate = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(candidate)
    assert episode["provenance"]["generator_sha256"] == baseline_sha
    assert episode["provenance"]["demonstration_policy"]["automatic"] is True
    assert episode["task_id"] == TASK and episode["seed"] == 17
    assert len(episode["train"]) == len(episode["test"]) == 4
    apply, runtime, bridge = _real_evaluator(Path.cwd() / "shared/runtime")
    predictions = []
    try:
        for pair in episode["train"] + episode["test"]:
            official = apply(episode["program"], pair["input"])
            assert official == pair["output"]
            predictions.append(apply(RIVAL, pair["input"]))
    finally:
        bridge.close()
    fits = all(prediction == pair["output"] for prediction, pair in zip(predictions[:4], episode["train"]))
    queries = []
    for index, (prediction, pair) in enumerate(zip(predictions[4:], episode["test"])):
        queries.append({"query_index": index, "sample_index": episode["sample_indices"][index + 4],
                        "rival_matches": prediction == pair["output"], "rival_output": prediction,
                        "before_gate": baseline.lesson_identifiable(episode["train"], pair),
                        "after_gate": candidate.lesson_identifiable(episode["train"], pair),
                        "differing_cells": [[r, c] for r, row in enumerate(prediction)
                                            for c, value in enumerate(row) if value != pair["output"][r][c]]})
    assert fits and any(not row["rival_matches"] for row in queries)
    assert all(not row["before_gate"] for row in queries)
    assert all(any("small_zero_regions" in reason for reason in row["after_gate"])
               for row in queries if not row["rival_matches"])
    result = {
        "schema": "native-export-border-rival-audit-v1", "task_id": TASK,
        "native_export_sha256": hashlib.sha256(source_file.read_bytes()).hexdigest(),
        "baseline_sha256": baseline_sha, "proposal_sha256": hashlib.sha256(proposal.read_bytes()).hexdigest(),
        "audit_script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "demo_count": 4, "query_count": 4, "racket_evaluations": 16,
        "runtime_identity": runtime, "rival_program": RIVAL,
        "native_lesson_status": episode["lesson_check"]["status"],
        "automatic_demonstration_policy": episode["provenance"]["demonstration_policy"],
        "rival_fits_all_demos": fits, "queries": queries,
        "ambiguous_query_indices": [row["query_index"] for row in queries if not row["rival_matches"]],
        "status": "native_default_lesson_ambiguity_reproduced_and_candidate_gate_detects_it",
        "safety_scope": "The raw native export retains the catalog's preexisting approved/reviewed_safe labels as exact evidence. This particular lesson is underidentified and must be treated as adversarial/alternative-answer research evidence, not clean single-answer training data. No approval metadata was changed.",
    }
    with args.out.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2, sort_keys=True)
        stream.write("\n")
    print(json.dumps({key: result[key] for key in ("status", "racket_evaluations", "demo_count", "rival_fits_all_demos", "ambiguous_query_indices")}, indent=2))


if __name__ == "__main__":
    main()
