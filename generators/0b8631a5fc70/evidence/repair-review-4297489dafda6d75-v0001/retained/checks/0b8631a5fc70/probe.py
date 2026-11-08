#!/usr/bin/env python3
"""Bounded current-source reproduction of the first/last-marker teaching gap.

Run from the packet outer directory:
  WORK/.venv/bin/python review.py run python3 ../checks/0b8631a5fc70/probe.py
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1] / "repo"
TASK = "0b8631a5fc70"
EXPECTED_SOURCE = "ad2a881eb69521352ff4960eec3d61716e1c265618d6c0961e1b74ccd036dad7"
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "shared/runtime")]
from arcpuzzles.catalog import Catalog
from arcpuzzles.parametric_worker import _real_evaluator
from reviewer_support import load_selected_generator, public_challenge_bytes


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def save(name, value):
    (HERE / name).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def main():
    source = ROOT / "generators" / TASK / "generator.py"
    before = hashlib.sha256(source.read_bytes()).hexdigest()
    assert before == EXPECTED_SOURCE, ("source changed; triage before rerunning", before)
    module, selected, loaded_hash = load_selected_generator(TASK, root=ROOT)
    assert selected == source and loaded_hash == before
    catalog = Catalog(ROOT)
    row = catalog.describe(TASK)
    assert row["generator_sha256"] == before
    canonical = {v["program_solution"] for v in catalog._variants()[TASK]}
    assert len(canonical) == 1
    program = canonical.pop()
    assert row["rule_hash"] == "c328d1c4e7f4"
    rival = program.replace("(first (find-color g 8))", "(last (find-color g 8))").replace(
        "(first (find-color g 9))", "(last (find-color g 9))")
    assert rival != program
    # Native assembly is exercised, including pair rejection and lesson checks.
    episode, = catalog.generate(TASK, count=1, seed=0, sample_index=8,
        n_train=3, n_test=1, allow_unapproved=True, timeout=60)
    assert episode["sample_indices"] == [8, 9, 10, 11]
    apply, identity, bridge = _real_evaluator(ROOT / "shared/runtime")
    checks, rivals = [], []
    try:
        for index, pair in zip(episode["sample_indices"], episode["train"] + episode["test"]):
            grid = pair["input"]
            errors = module.self_check(grid)
            assert not errors, errors
            actual = apply(program, grid)
            alternative = apply(rival, grid)
            assert actual == pair["output"], "native label differs from protected replay"
            rivals.append(alternative)
            checks.append({"sample_index": index, "domain_errors": errors,
                "marker_counts": {str(color): sum(row.count(color) for row in grid) for color in (8, 9)},
                "rival_matches_racket_label": alternative == actual,
                "input_sha256": digest(grid), "racket_label_sha256": digest(actual),
                "rival_sha256": digest(alternative)})
    finally:
        bridge.close()
    assert all(c["rival_matches_racket_label"] for c in checks[:3])
    assert not checks[3]["rival_matches_racket_label"]
    assert hashlib.sha256(source.read_bytes()).hexdigest() == before
    (HERE / "public_lesson.json").write_bytes(public_challenge_bytes(episode))
    save("private_labels.json", {"query_output": episode["test"][0]["output"],
        "rival_query_output": rivals[3], "canonical_program": program, "rival_program": rival})
    report = {"schema": "bounded-peer-learnability-v1", "task_id": TASK,
        "outcome": "reproduced_existing_teaching_ambiguity", "source_sha256": before,
        "canonical_rule_hash": row["rule_hash"], "seed": 0,
        "sample_indices": episode["sample_indices"], "racket": identity,
        "protected_replay_evaluations": 8, "native_rejections": episode["rejections"],
        "native_lesson_check": episode.get("lesson_check"), "checks": checks,
        "rival": "Use last row-major 8 and last row-major 9; translate payload and erase all markers.",
        "rival_fits_all_demos": True, "rival_changes_query": True,
        "scope": "One native seed-0 lesson; one explicit rival. No prevalence estimate or full battery.",
        "recommendation": "Ensure a distinguishing extra-markers demonstration whenever the query needs first-marker selection, or add an executable lesson rival check."}
    save("witness.json", report)
    print(json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
