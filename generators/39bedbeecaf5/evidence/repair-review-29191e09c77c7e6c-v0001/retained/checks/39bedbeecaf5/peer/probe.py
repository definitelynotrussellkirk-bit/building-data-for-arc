#!/usr/bin/env python3
"""Bounded, source-pinned peer audit of triangle-reflection teaching coverage.

From the packet root:
  WORK/.venv/bin/python review.py run python3 ../checks/39bedbeecaf5/peer/probe.py

One rival, 16 ordinary sampled inputs, four canonical pairs, and one single-cell
separating contrast. No generator source is changed or approved by this probe.
"""
import hashlib
import json
from pathlib import Path

from arcpuzzles.parametric_worker import _grid, _real_evaluator
from reviewer_support import canonical_pairs, canonical_path, find_root, load_selected_generator

TASK_ID = "39bedbeecaf5"
EXPECTED_GENERATOR_SHA256 = "6cb2081b3996469e47f535e52b28c81817c6a1eabbf6e074a5cbacdebc033268"
RIVAL = """(rule! (lambda (g)
  (let ((n (rows g)))
    (grid-from-fn n n
      (lambda (r c) (if (= r c) 5 (at g c r)))))))"""


def main():
    root = find_root(__file__)
    generator, source, digest = load_selected_generator(TASK_ID, root=root)
    if digest != EXPECTED_GENERATOR_SHA256:
        raise ValueError("Generator source changed; audit must be reassessed")
    rows = [json.loads(line) for line in canonical_path(root).read_text().splitlines()]
    authority = [row for row in rows if row.get("task_id") == TASK_ID]
    assert len(authority) == 1
    program = authority[0]["program_solution"]
    pairs = canonical_pairs(TASK_ID, root=root, labeled_only=True)
    apply, identity, bridge = _real_evaluator(root / "shared/runtime")
    evaluations = 0
    canonical, samples = [], []
    try:
        for pair in pairs:
            actual = _grid(apply(program, pair["input"]))
            alternate = _grid(apply(RIVAL, pair["input"]))
            evaluations += 2
            assert actual == pair["output"] == alternate
            errors = generator.self_check(pair["input"])
            assert errors == ["input contains color 5; diagonal 5 belongs to the output only"]
            canonical.append({**pair, "validator_errors": errors,
                              "racket_matches_stored_label": True, "rival_matches": True})
        for band in (None, "easy", "medium", "hard"):
            for index in range(4):
                grid = generator.generate(0, index, difficulty=band)
                errors = generator.self_check(grid)
                assert not errors
                assert all(grid[i][i] == 0 for i in range(len(grid)))
                actual = _grid(apply(program, grid))
                alternate = _grid(apply(RIVAL, grid))
                evaluations += 2
                assert actual == alternate
                samples.append({"seed": 0, "sample_index": index, "difficulty": band,
                                "input_sha256": hashlib.sha256(json.dumps(grid).encode()).hexdigest(),
                                "size": len(grid), "validator_errors": errors,
                                "diagonal_is_zero": True, "rival_matches": True})
        base = [[0, 0, 0], [3, 0, 0], [0, 0, 0]]
        witness = [[0, 1, 0], [3, 0, 0], [0, 0, 0]]
        baseline_actual = _grid(apply(program, base))
        baseline_rival = _grid(apply(RIVAL, base))
        actual = _grid(apply(program, witness))
        alternate = _grid(apply(RIVAL, witness))
        evaluations += 4
        assert not generator.self_check(base)
        assert baseline_actual == baseline_rival
        assert actual == [[5, 3, 0], [0, 5, 0], [0, 0, 5]]
        assert alternate == [[5, 3, 0], [1, 5, 0], [0, 0, 5]]
        assert actual != alternate
        witness_errors = generator.self_check(witness)
        assert witness_errors == ["found 1 nonzero cells above diagonal in input"]
    finally:
        bridge.close()
    report = {
        "schema": "triangle-reflection-peer-review-v1", "task_id": TASK_ID,
        "status": "finding", "generator_sha256": digest,
        "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "canonical_program_sha256": hashlib.sha256(program.encode()).hexdigest(),
        "canonical_program": program,
        "rival_name": "transpose_entire_grid_then_force_diagonal_five",
        "rival_program": RIVAL, "rival_program_sha256": hashlib.sha256(RIVAL.encode()).hexdigest(),
        "racket": identity, "protected_evaluations": evaluations,
        "canonical_pairs_checked": len(canonical), "ordinary_draws_checked": len(samples),
        "canonical_pairs": canonical, "ordinary_draws": samples,
        "canonical_coverage_finding": {
            "description": "All three canonical demonstrations and the canonical query contain diagonal5 and are rejected by the current validator, while ordinary sampling leaves the diagonal0.",
            "scope": "Input-domain/canonical-fidelity mismatch, not a demonstrated reference-label error."
        },
        "teaching_coverage_finding": {
            "description": "The full-transpose-plus-diagonal5 rival fits all canonical pairs and all16sampled draws. It is output-equivalent throughout the current admitted lower-only/no5 input grammar. A one-cell upper distractor separates it, but that witness is rejected by the validator.",
            "scope": "Outside-domain teaching coverage gap, not a sampled-query ambiguity or accepted-input label error.",
            "accepted_baseline": {"input": base, "canonical_output": baseline_actual, "rival_output": baseline_rival},
            "single_cell_contrast": {"input": witness, "canonical_output": actual,
                                     "rival_output": alternate, "validator_errors": witness_errors}
        },
        "proposed_next_repairs": [
            "Restore canonical input coverage by permitting color5 on the diagonal and sampling the canonical diagonal marker; keep arbitrary off-diagonal5 decisions explicit.",
            "Only if stronger masking-rule teaching is desired, intentionally extend the input grammar with upper-triangle distractors and teach their deletion; do not present the current rejected witness as a generator failure."
        ],
        "limits": "One declared rival,16ordinary draws and4canonical pairs. No production changes, full battery, owner integration, approval or training admission."
    }
    output = Path(__file__).resolve().with_name("report.json")
    output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({key: report[key] for key in ("status", "generator_sha256", "canonical_pairs_checked", "ordinary_draws_checked", "protected_evaluations")}))


if __name__ == "__main__":
    main()
