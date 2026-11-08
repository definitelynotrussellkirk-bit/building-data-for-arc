#!/usr/bin/env python3
"""Verify saved public-Racket evidence; use the same command cwd as probe.py."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

from reviewer_support import find_root

TASK_ID = "5666b68dd4b9"
OUT = Path(__file__).resolve().parent


def main():
    root = find_root(Path.cwd())
    source = root / "generators" / TASK_ID / "generator.py"
    spec = importlib.util.spec_from_file_location("audited_generator", source)
    generator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(generator)
    manifest = json.loads((OUT / "manifest.json").read_text())
    applied = json.loads((OUT / "racket.json").read_text())
    cases, results = manifest["cases"], applied["results"]
    assert hashlib.sha256(source.read_bytes()).hexdigest() == manifest["generator_sha256"] == applied["generator_sha256"]
    assert manifest["rule_hash"] == applied["executed_rule_hash"] == applied["catalog_rule_hash"]
    assert applied["rule_hash_matches_catalog"]
    assert len(cases) == len(results) == 37
    for index, (case, result) in enumerate(zip(cases, results)):
        assert index == case["apply_index"] == result["index"]
        assert case["input"] == result["input"]
        assert result["error"] is None and result["valid_output"]
        assert result["output"] == generator.rule_mirror(case["input"]) == case["mirror_output"]
        assert generator.self_check(case["input"]) == []
        assert generator.strict_canonical_like(case["input"]) == []
        if case["kind"] == "canonical":
            assert case["output"] == result["output"]
        case["actual_racket_output"] = result["output"]
        case["rival_matches_racket"] = case["rival_output"] == result["output"]

    assert all(case["rival_matches_racket"] for case in cases[:-1])
    assert not cases[-1]["rival_matches_racket"]
    canonical = [case for case in cases if case["kind"] == "canonical"]
    declared_shortcuts = {
        name: {"agreements": sum(fn(case["input"]) == case["actual_racket_output"] for case in canonical), "denominator": 4}
        for name, fn in generator.CANONICAL_SHORTCUTS.items()
    }
    assert all(row["agreements"] == 4 for row in declared_shortcuts.values())
    blocks = []
    for seed in range(8):
        block = [case for case in cases if case["kind"] == "generated" and case["seed"] == seed]
        assert len(block) == 4
        refutations = {
            name: [case["sample_index"] for case in block if fn(case["input"]) != case["actual_racket_output"]]
            for name, fn in generator.LESSON_COMPETITORS.items()
        }
        assert all(refutations.values())
        blocks.append({"seed": seed, "sample_indices": [0, 1, 2, 3],
                       "declared_competitor_refuting_indices": refutations,
                       "new_rival_agreements": 4, "demonstration_denominator": 4})

    witness = cases[-1]
    differences = [
        {"row": r, "col": c, "racket": color, "rival": witness["rival_output"][r][c]}
        for r, row in enumerate(witness["actual_racket_output"])
        for c, color in enumerate(row) if color != witness["rival_output"][r][c]
    ]
    shared = {"task_id": TASK_ID, "generator_sha256": manifest["generator_sha256"],
              "canonical_program_sha256": manifest["rule_sha256"],
              "executed_rule_hash": applied["executed_rule_hash"],
              "executed_rule_text_sha256": applied["rule_text_sha256"]}
    counterexample = {
        **shared, **witness, "different_output_cells": differences,
        "public_apply_result_index": 36, "public_apply_evidence_path": f"checks/audit/{TASK_ID}/racket.json",
        "command": {**manifest["public_command"], "exit_code": 0},
        "classification": "Suspected shortcut with reproduced separating input; generator distribution blind spot, not a Racket-label mismatch.",
    }
    summary = {
        **shared, "audit_state": "complete", "source_state": "unchanged audit target",
        "classification": counterexample["classification"],
        "rival": manifest["rival"], "sample_range": manifest["generated_sample_range"],
        "counts": {**manifest["counts"], "generated_rival_racket_agreement": 32,
                   "canonical_rival_racket_agreement": 4, "canonical_racket_label_agreement": 4,
                   "racket_valid_outputs": 37, "self_check_accepted": 37,
                   "strict_canonical_like_accepted": 37, "mirror_racket_parity": 37,
                   "counterexample_rival_disagreements": 1, "counterexample_changed_cells": len(differences),
                   "nonoverlapping_four_demo_blocks": 8},
        "declared_canonical_shortcuts": declared_shortcuts,
        "demo_blocks": blocks,
        "limits": [
            "Thirty-two unique generated inputs: seeds 0..7, sample indices 0..3, hard difficulty, no overrides. The sample contains four of the six source templates.",
            "Eight nonoverlapping four-demonstration blocks were scored; no generated query rotations or exhaustive stream starts were measured.",
            "The counterexample is validator-accepted and structurally canonical-like but is not emitted by this source: its seven-cell asymmetric distractor differs from the hard-coded eight-cell ring.",
            "Static reading supports the same shortcut across the emitted shape/distractor construction, but the measured Racket denominator is only 37 inputs.",
            "No generator, rule, canonical record, assignment, or root report was modified. No solve directories or private query labels were accessed."
        ],
        "recommended_followup": "Emit larger asymmetric wrong-colour distractors as well as the ring, and add largest_half_turn_asymmetric_component as a canonical-fitting rival with a selector-dependent witness.",
    }
    (OUT / "counterexample.json").write_text(json.dumps(counterexample, indent=2) + "\n")
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps({"task_id": TASK_ID, "counts": summary["counts"], "classification": summary["classification"]}, indent=2))


if __name__ == "__main__":
    main()
