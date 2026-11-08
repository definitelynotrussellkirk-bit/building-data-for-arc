#!/usr/bin/env python3
"""Replay the retained stable-vs-sorted gravity witness on protected Racket."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

from reviewer_support import load_selected_generator
from arcpuzzles.parametric_worker import _grid, _local_imports, _real_evaluator

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2] / "repo"
TASK = "3bf9215de862"
EXPECTED_SOURCE_SHA256 = "7c326b90aa46cea37e712bf444a4999cb31944b50e024f95857e70f94e9e2ece"
WITNESS_PATH = (
    ROOT
    / "generators/3bf9215de862/counterexamples/"
      "review-8c047b6aa472e331-v0001/retained/checks/audit/"
      "3bf9215de862/counterexample.json"
)

SORTED_RIVAL = r'''(rule!
  (let* ((cmd (at g 0 0))
         (work (set-cell g 0 0 0)))
    (define (pack-end values)
      (let* ((payload (sort (filter (lambda (v) (!= v 0)) values) <))
             (padding (- (length values) (length payload))))
        (append (make-list padding 0) payload)))
    (define (pack-start values)
      (let* ((payload (sort (filter (lambda (v) (!= v 0)) values) <))
             (padding (- (length values) (length payload))))
        (append payload (make-list padding 0))))
    (cond [(= cmd 1) (transpose (map pack-end (transpose work)))]
          [(= cmd 2) (transpose (map pack-start (transpose work)))]
          [(= cmd 3) (map pack-start work)]
          [else (map pack-end work)])))'''


def canonical_program() -> str:
    with (ROOT / "shared/data/canonical/puzzles.jsonl").open(encoding="utf-8") as handle:
        rows = [json.loads(line) for line in handle if f'"task_id": "{TASK}"' in line]
    matches = [row for row in rows if row.get("task_id") == TASK]
    if len(matches) != 1:
        raise ValueError(f"Expected one canonical row for {TASK}, found {len(matches)}")
    return matches[0]["program_solution"]


def sorted_gravity(grid: list[list[int]]) -> list[list[int]]:
    """Independent Python definition of the plausible sorted-order shortcut."""
    output = copy.deepcopy(grid)
    cmd = output[0][0]
    output[0][0] = 0
    h, w = len(output), len(output[0])
    if cmd in (1, 2):
        for c in range(w):
            payload = sorted(output[r][c] for r in range(h) if output[r][c] != 0)
            values = ([0] * (h - len(payload)) + payload) if cmd == 1 else (payload + [0] * (h - len(payload)))
            for r, value in enumerate(values):
                output[r][c] = value
    else:
        for r in range(h):
            payload = sorted(value for value in output[r] if value != 0)
            output[r] = (payload + [0] * (w - len(payload))) if cmd == 3 else ([0] * (w - len(payload)) + payload)
    return output


def main() -> None:
    generator, source_path, source_sha256 = load_selected_generator(TASK, root=ROOT)
    if source_sha256 != EXPECTED_SOURCE_SHA256:
        raise ValueError(f"Peer source changed: {source_sha256}")
    witness = json.loads(WITNESS_PATH.read_text(encoding="utf-8"))
    program = canonical_program()
    normalized_rule_hash = hashlib.sha256(" ".join(program.split()).encode()).hexdigest()[:12]
    if normalized_rule_hash != witness["rule_hash"]:
        raise ValueError("Canonical rule hash differs from retained witness")
    if witness["generator_sha256"] != source_sha256:
        raise ValueError("Retained witness is not bound to current generator source")

    runtime = ROOT / "shared/runtime"
    comparisons: list[dict] = []
    with _local_imports(runtime, source_path.parent):
        from puzzle_generators.rule_wrap import wrap_rule

        wrapped_program_sha256 = hashlib.sha256(wrap_rule(program).encode()).hexdigest()
        if wrapped_program_sha256 != witness["rule_text_sha256"]:
            raise ValueError("Wrapped canonical program differs from retained witness")
        apply, identity, bridge = _real_evaluator(runtime)
        try:
            for pair in witness["pairs"]:
                grid = pair["input"]
                errors = generator.self_check(copy.deepcopy(grid))
                if errors:
                    raise AssertionError(f"Retained input left generator domain: {errors}")
                truth = _grid(apply(program, grid))
                alternate = _grid(apply(SORTED_RIVAL, grid))
                python_alternate = sorted_gravity(grid)
                if truth != pair["racket_output"]:
                    raise AssertionError("Fresh canonical Racket output differs from retained label")
                if alternate != pair["rival_output"] or alternate != python_alternate:
                    raise AssertionError("Fresh executable rival differs from retained/Python rival")
                comparisons.append(
                    {
                        "role": pair["role"],
                        "sample_index": pair["sample_index"],
                        "command": pair["command"],
                        "canonical_equals_sorted_rival": truth == alternate,
                        "differing_cells": sum(
                            left != right
                            for left_row, right_row in zip(truth, alternate)
                            for left, right in zip(left_row, right_row)
                        ),
                    }
                )
        finally:
            bridge.close()

    demo_flags = [row["canonical_equals_sorted_rival"] for row in comparisons if row["role"] == "demo"]
    query_rows = [row for row in comparisons if row["role"] == "query"]
    if demo_flags != [True, True, True]:
        raise AssertionError(f"Rival no longer fits all demonstrations: {demo_flags}")
    if len(query_rows) != 1 or query_rows[0]["canonical_equals_sorted_rival"]:
        raise AssertionError("Rival no longer changes the retained query")

    report = {
        "schema": "source-bound-peer-replay-v1",
        "task_id": TASK,
        "status": "counterexample_protected_racket_confirmed",
        "finding": "Three demonstrations admit color-sorted gravity although the canonical rule preserves stable payload order.",
        "source_path": str(source_path.relative_to(ROOT)),
        "source_sha256": source_sha256,
        "canonical_program_sha256": hashlib.sha256(program.encode()).hexdigest(),
        "canonical_wrapped_program_sha256": wrapped_program_sha256,
        "canonical_rule_hash": normalized_rule_hash,
        "rival_program_sha256": hashlib.sha256(SORTED_RIVAL.encode()).hexdigest(),
        "retained_witness": str(WITNESS_PATH.relative_to(ROOT)),
        "lesson": witness["lesson"],
        "comparisons": comparisons,
        "demonstrations_all_agree": all(demo_flags),
        "query_disagrees": not query_rows[0]["canonical_equals_sorted_rival"],
        "query_differing_cells": query_rows[0]["differing_cells"],
        "all_inputs_pass_current_self_check": True,
        "all_stored_labels_replayed": True,
        "protected_racket_evaluations": 2 * len(comparisons),
        "racket_runtime": identity,
        "limits": [
            "One retained generated lesson, not a prevalence estimate.",
            "The peer generator remains unchanged and unapproved; this is repair evidence only.",
        ],
        "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }
    (HERE / "replay.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
