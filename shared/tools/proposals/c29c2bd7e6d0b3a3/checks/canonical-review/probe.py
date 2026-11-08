#!/usr/bin/env python3
"""Source-bound selected-task canonical and histogram shortcut review.

Writes only beneath --out. Reference and rival labels use the selected tree's
real Racket bridge. No blind/private solve data is opened.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys


TASK = "7a37505e7bd0"
NONZERO_RULE = """(rule! (lambda (g)
  (let ((n (length (filter (lambda (c) (not (= c 0))) (grid-colors g)))))
    (if (<= n 1) g (upscale g n)))))"""
COMPLEMENT_MODAL_RULE = """(rule! (lambda (g)
  (let* ((flat (apply append g))
         (cs (grid-colors g))
         (m (apply max (map (lambda (c)
                             (length (filter (lambda (v) (= v c)) flat)))
                           cs)))
         (n (if (= (length cs) 1) 1 (- 7 m))))
    (if (<= n 1) g (upscale g n)))))"""


def sha_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def grid_hash(grid) -> str:
    return sha_bytes(json.dumps(grid, separators=(",", ":")).encode())


def shape(grid):
    return [len(grid), len(grid[0])]


def record_grid(grid):
    counts = Counter(v for row in grid for v in row)
    return {"input": grid, "input_sha256": grid_hash(grid),
            "color_count": len(counts), "colors": sorted(counts),
            "frequency_profile": sorted(counts.values()),
            "modal_frequency": max(counts.values())}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--runtime", type=Path, required=True,
                        help="Selected portable runtime from prepare_runtime")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    root = args.repo.resolve()
    runtime = args.runtime.resolve()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    sys.path.insert(0, str(runtime))
    from reviewer_support import canonical_pairs, canonical_path, load_selected_generator
    from puzzle_generators.rule_wrap import wrap_rule
    from arc_repl.racket_bridge import RacketBridge

    generator, source_path, source_sha = load_selected_generator(TASK, root=runtime)
    ledger_path = canonical_path(runtime)
    selected = []
    with ledger_path.open() as handle:
        for line in handle:
            if line.strip():
                row = json.loads(line)
                if row.get("task_id") == TASK:
                    selected.append(row)
    assert len(selected) == 1, "Probe expects one selected canonical variant"
    rule = selected[0]["program_solution"]
    rules = {"reference": rule, "nonzero": NONZERO_RULE,
             "seven_minus_modal": COMPLEMENT_MODAL_RULE}
    wrapped = {name: wrap_rule(src) for name, src in rules.items()}
    pairs = canonical_pairs(TASK, root=runtime)
    assert len(pairs) == 8
    reference_evaluations = 0
    rival_evaluations = Counter()
    canonical_checks = []
    generated_checks = []
    histogram_summary = Counter()
    zero_summary = Counter()
    question_witness = None
    modal_canonical_witness = None

    with RacketBridge() as bridge:
        runtime_identity = bridge.runtime_identity

        def evaluate(name, grid):
            nonlocal reference_evaluations
            literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
            expression = f"({wrapped[name]} {literal})"
            result = bridge.eval_text(expression)
            if name == "reference":
                reference_evaluations += 1
            else:
                rival_evaluations[name] += 1
            return result

        for pair in pairs:
            grid = pair["input"]
            true = evaluate("reference", grid)
            assert true == pair["output"]
            assert generator.self_check(grid) == []
            assert generator.rule_mirror(grid) == true
            nonzero = evaluate("nonzero", grid)
            modal = evaluate("seven_minus_modal", grid)
            detail = dict(record_grid(grid), variant=pair["variant"],
                          split=pair["split"], pair_index=pair["pair_index"],
                          self_check=[], reference_matches_canonical=True,
                          output_shape=shape(true), output_sha256=grid_hash(true),
                          nonzero_matches=nonzero == true,
                          seven_minus_modal_matches=modal == true)
            canonical_checks.append(detail)
            if modal != true and modal_canonical_witness is None:
                modal_canonical_witness = dict(detail, true_output=true,
                    rival_output=modal, rival_output_shape=shape(modal),
                    rival_output_sha256=grid_hash(modal))

        for band in ("easy", "medium", "hard"):
            for seed in range(12):
                for index in range(5):
                    grid = generator.generate(seed, index, difficulty=band)
                    true = evaluate("reference", grid)
                    nonzero = evaluate("nonzero", grid)
                    modal = evaluate("seven_minus_modal", grid)
                    assert generator.self_check(grid) == []
                    assert generator.rule_mirror(grid) == true
                    counts = Counter(v for row in grid for v in row)
                    n = len(counts)
                    histogram_summary[(n, tuple(sorted(counts.values())))] += 1
                    zero_summary[(n, 0 in counts)] += 1
                    record = dict(record_grid(grid), seed=seed,
                                  sample_index=index, difficulty=band,
                                  self_check=[], output_shape=shape(true),
                                  output_sha256=grid_hash(true),
                                  nonzero_matches=nonzero == true,
                                  seven_minus_modal_matches=modal == true)
                    generated_checks.append(record)
                    if band == "medium" and seed == 0 and index == 1:
                        question_witness = dict(record,
                            generate_argv={"seed": seed, "sample_index": index,
                                           "difficulty": band},
                            true_output=true, rival_output=nonzero,
                            rival_output_shape=shape(nonzero),
                            rival_output_sha256=grid_hash(nonzero),
                            emitted=True, overrides={},
                            regenerated_input_equal=(grid == generator.generate(seed, index, difficulty=band)))

    # Source-level fixed-histogram algebra explains the sampled result, without
    # claiming exhaustive seeds or unique identification against all rivals.
    template_proof = []
    for n, labels in sorted(generator._TEMPLATES.items()):
        counts = Counter(labels)
        predicted = 1 if len(counts) == 1 else 7 - max(counts.values())
        template_proof.append({"scale": n,
                               "profile": sorted(counts.values()),
                               "seven_minus_modal_factor": predicted,
                               "factor_matches": predicted == n})

    source_end_sha = sha_bytes(source_path.read_bytes())
    report = {
        "schema": "arcpuzzles-selected-canonical-review-v1",
        "task_id": TASK, "generator_source": str(source_path),
        "library_generator_source": str(root / f"generators/{TASK}/generator.py"),
        "generator_sha256": source_sha,
        "source_sha256_at_end": source_end_sha,
        "source_changed_during_run": source_end_sha != source_sha,
        "rule": rule, "rule_sha256": sha_bytes(rule.encode()),
        "selected_canonical_row_sha256": sha_bytes(json.dumps(selected[0], sort_keys=True, separators=(",", ":")).encode()),
        "grid_hash_encoding": "sha256(UTF-8 compact JSON integer grid; separators comma/colon)",
        "rival_rules": rules,
        "racket_runtime_identity": runtime_identity,
        "reference_evaluations": reference_evaluations,
        "rival_evaluations": dict(rival_evaluations),
        "canonical_pair_count": len(canonical_checks),
        "canonical_nonzero_fit_count": sum(r["nonzero_matches"] for r in canonical_checks),
        "canonical_seven_minus_modal_fit_count": sum(r["seven_minus_modal_matches"] for r in canonical_checks),
        "generated_pair_count": len(generated_checks),
        "generated_nonzero_disagreement_count": sum(not r["nonzero_matches"] for r in generated_checks),
        "generated_seven_minus_modal_disagreement_count": sum(not r["seven_minus_modal_matches"] for r in generated_checks),
        "zero_by_scale": [dict(color_count=n, includes_zero=z, samples=count)
                          for (n, z), count in sorted(zero_summary.items())],
        "histograms_by_scale": [dict(color_count=n, frequency_profile=list(profile), samples=count)
                                for (n, profile), count in sorted(histogram_summary.items())],
        "template_algebra": template_proof,
        "question_witness": question_witness,
        "canonical_counterexample_to_histogram_shortcut": modal_canonical_witness,
        "canonical_checks": canonical_checks,
        "generated_checks": generated_checks,
        "limitations": ["This is a selected-source review, not a random audit.",
                        "The histogram rival does not fit all canonical demonstrations; it is a mismatch between generated teaching evidence and canonical evidence.",
                        "The zero/scale correlation is recorded as a residual distribution constraint, not proof of a labeling defect.",
                        "Finite generated sampling does not prove unique rule induction."]
    }
    assert question_witness and question_witness["emitted"]
    assert not question_witness["nonzero_matches"]
    assert modal_canonical_witness
    assert all(r["nonzero_matches"] for r in canonical_checks)
    (out / "evidence.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({key: report[key] for key in (
        "generator_sha256", "source_changed_during_run", "rule_sha256",
        "canonical_pair_count", "canonical_nonzero_fit_count",
        "canonical_seven_minus_modal_fit_count", "generated_pair_count",
        "generated_nonzero_disagreement_count",
        "generated_seven_minus_modal_disagreement_count", "zero_by_scale",
        "histograms_by_scale", "template_algebra")}, indent=2))
    print(json.dumps({"question_witness": question_witness,
                      "canonical_counterexample_to_histogram_shortcut": modal_canonical_witness}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
