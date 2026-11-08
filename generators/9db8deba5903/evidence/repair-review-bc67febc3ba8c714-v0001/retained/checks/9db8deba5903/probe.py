"""Bounded peer audit: fixed D4-transform quadrant rivals, Racket labels.

From the packet root:
  WORK/.venv/bin/python review.py run python3 ../checks/9db8deba5903/probe.py
This is owner-checked-only evidence, not approval or exhaustive learnability.
"""
from __future__ import annotations

import hashlib
import itertools
import json
import math
import os
from pathlib import Path

from reviewer_support import find_root, load_selected_generator, normalize_grid
from arc_repl.isolated_verifier import Limits, verify_candidate


TASK = "9db8deba5903"
PIN = "59b8d0b23d4ffbcf741af0db076dd2ac9777d1c03c426eaab71ef38184f908f5"
RULE = "847ceb038813"
SEED = 20261024
OUT = Path(__file__).resolve().parent
NAMES = ("identity", "cw90", "halfturn", "ccw90", "flip_lr",
         "cw90_after_flip_lr", "halfturn_after_flip_lr", "ccw90_after_flip_lr")


def transforms(grid):
    """Independent rival implementation; no generator mirror is used."""
    result = []
    for initial in (grid, [row[::-1] for row in grid]):
        current = [row[:] for row in initial]
        for _ in range(4):
            result.append(current)
            current = [list(row) for row in zip(*current[::-1])]
    return result


def quadrants(output):
    n = len(output) // 2
    return [[row[:n] for row in output[:n]],
            [row[n:] for row in output[:n]],
            [row[:n] for row in output[n:]],
            [row[n:] for row in output[n:]]]


def inspect(demos, query, expected):
    # A candidate chooses one of eight transforms for each of four quadrants.
    # Factoring the exact-fit predicate is equivalent to enumerating all 8**4.
    survivors = [[t for t in range(8) if all(
        transforms(pair["input"])[t] == quadrants(pair["output"])[q]
        for pair in demos)] for q in range(4)]
    count = math.prod(map(len, survivors))
    query_transforms, query_quads = transforms(query), quadrants(expected)
    exact = math.prod(sum(query_transforms[t] == query_quads[q] for t in choices)
                      for q, choices in enumerate(survivors))
    wrong = count - exact
    witness = None
    if wrong:
        for choice in itertools.product(*survivors):
            if any(query_transforms[t] != query_quads[q] for q, t in enumerate(choice)):
                witness = [NAMES[t] for t in choice]
                break
    return {"hypotheses_tested": 8**4, "surviving_assignments": count,
            "query_disagreeing_survivors": wrong,
            "surviving_transforms_by_quadrant": [[NAMES[t] for t in x] for x in survivors],
            "first_wrong_assignment": witness}


def main():
    root = find_root(__file__)
    gen, source, digest = load_selected_generator(TASK, root=root)
    # Fail closed before any generated sample is requested.
    assert digest == PIN, ("selected source changed", digest, PIN)
    assert gen.RULE_HASH == RULE
    with (root / "shared/data/canonical/puzzles.jsonl").open() as handle:
        canonical = next(json.loads(line) for line in handle
                         if line.strip() and json.loads(line).get("task_id") == TASK)
    rule = canonical["program_solution"]
    assert hashlib.sha256(" ".join(rule.split()).encode()).hexdigest()[:12] == RULE
    first = canonical["train"][0]
    anchor = {key: normalize_grid(first[key]) for key in ("input", "output")}
    samples = []
    for band in ("easy", "medium", "hard"):
        for index in range(8):
            grid = gen.generate(SEED, index, difficulty=band)
            assert gen.self_check(grid) == [], (band, index)
            samples.append({"difficulty": band, "sample_index": index,
                            "profile": gen.schedule_profile(SEED, index, band),
                            "input": grid})
    request = {"train": [anchor], "test": [{"input": s["input"]} for s in samples]}
    wrapped = rule if rule.lstrip().startswith("(rule!") else f"(rule! {rule})"
    receipt = verify_candidate(request, wrapped, racket_path=os.environ["RACKET_PATH"],
                               limits=Limits(wall_seconds=45, max_pairs=25))
    (OUT / "racket-receipt.json").write_text(json.dumps(receipt, separators=(",", ":")) + "\n")
    assert receipt["status"] == "pass", receipt
    for sample, output in zip(samples, receipt["test_outputs"], strict=True):
        sample["output"] = output
    lessons = []
    for b, band in enumerate(("easy", "medium", "hard")):
        for start in range(4):
            demo_ids = [b * 8 + start + i for i in range(4)]
            query_id = b * 8 + start + 4
            demos = [samples[i] for i in demo_ids]
            query = samples[query_id]
            gate = gen.lesson_identifiable(demos, {"input": query["input"]})
            assert gate == [], (band, start, gate)
            result = inspect(demos, query["input"], query["output"])
            assert result["surviving_assignments"] >= 1
            lessons.append({"difficulty": band, "start_index": start,
                            "demo_sample_ids": demo_ids, "query_sample_id": query_id,
                            "lesson_identifiable_errors": gate, **result})
    # Deliberately ambiguous half-turn-only demos: the wrong direction should
    # survive, then fail on a full-orbit query; the generator gate must reject.
    control_demos = [samples[0]] * 4
    control_query = samples[1]
    control = inspect(control_demos, control_query["input"], control_query["output"])
    control["lesson_identifiable_errors"] = gen.lesson_identifiable(
        control_demos, {"input": control_query["input"]})
    assert control["query_disagreeing_survivors"] > 0
    assert control["lesson_identifiable_errors"]
    findings = [row for row in lessons if row["query_disagreeing_survivors"]]
    result = {"schema": "arcpuzzles-bounded-peer-learnability-v1", "task_id": TASK,
              "status": "finding" if findings else "no_finding_in_bounded_scope",
              "proposal_status": "owner-checked-only", "source_sha256": digest,
              "source_path": source.relative_to(root).as_posix(), "rule_hash": RULE,
              "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "seed": SEED, "racket_labeled_generated_grids": len(samples),
              "hypothesis_family": "All fixed independent D4 transforms of the input in four output quadrants",
              "hypotheses_per_lesson": 4096, "scheduled_lessons": lessons,
              "positive_detection_control": {"demo_sample_ids": [0, 0, 0, 0],
                                             "query_sample_id": 1, **control},
              "samples": samples,
              "limits": ["One seed; 8 consecutive draws per difficulty; 12 overlapping four-demo lessons.",
                         "Only fixed D4 quadrant assignments; no color/size/profile-conditioned rules or arbitrary programs.",
                         "Control repeats one half-turn input and is intentionally rejected by the lesson gate.",
                         "No full battery, model run, parametric qualification, approval change, or audit disposition."]}
    (OUT / "evidence.json").write_text(json.dumps(result, separators=(",", ":")) + "\n")
    print(json.dumps({key: result[key] for key in ("task_id", "status", "source_sha256",
                      "rule_hash", "racket_labeled_generated_grids", "hypotheses_per_lesson")}))
    print(json.dumps({"lessons": len(lessons), "findings": len(findings),
                      "surviving_assignments_per_lesson": [x["surviving_assignments"] for x in lessons],
                      "control_wrong_survivors": control["query_disagreeing_survivors"]}))


if __name__ == "__main__":
    main()
