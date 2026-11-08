#!/usr/bin/env python3
"""Reproduce a source-color-count/transform-family shortcut."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

WORK = Path(__file__).resolve().parents[3]
REPO = WORK / "repo"
sys.path[:0] = [str(REPO / "src"), str(REPO / "shared/runtime")]
from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK = "4c26a1072222"
OUT_DIR = Path(__file__).resolve().parent
gen, source_path, source_sha256 = load_selected_generator(TASK, root=find_root(__file__))


def color_count_cued_rival(grid):
    """Use a relation only when source color count predicts its transform family.

    The production sampler always couples three source colors to transpose or
    anti-transpose and two source colors to every other transform.  On a
    decoupled lawful band this rival leaves C in its original orientation.
    """
    info, errors = gen._analyze(grid)
    if errors:
        raise ValueError("; ".join(errors))
    output = [[0, 0] for _ in range(info["height"])]
    for band in info["bands"]:
        cue_says_transpose = band["source_color_count"] == 3
        selected_is_transpose = band["transform"] in (6, 7)
        if cue_says_transpose == selected_is_transpose:
            gen._render_band(output, band, band["transform"], band["mapping"])
        else:
            gen._render_band(output, band, 0, {})
    return output


def coupling_signature(grid):
    info, errors = gen._analyze(grid)
    if errors:
        return {"errors": errors}
    return {
        "bands": [
            {
                "source_color_count": band["source_color_count"],
                "transform_index": band["transform"],
                "transform_name": gen.TRANSFORM_NAMES[band["transform"]],
                "cue_matches_family": (band["source_color_count"] == 3)
                == (band["transform"] in (6, 7)),
            }
            for band in info["bands"]
        ]
    }


def main() -> int:
    grid = json.loads((OUT_DIR / "input.json").read_text())
    racket = json.loads((OUT_DIR / "racket.json").read_text())
    actual = racket["results"][0]["output"]
    rival = color_count_cued_rival(grid)
    (OUT_DIR / "rival.json").write_text(json.dumps({"output": rival}, indent=2) + "\n")

    canonical = canonical_pairs(TASK, root=REPO, labeled_only=True)
    canonical_rows = []
    for pair in canonical:
        prediction = color_count_cued_rival(pair["input"])
        canonical_rows.append({
            "variant": pair["variant"],
            "split": pair["split"],
            "pair_index": pair["pair_index"],
            "fits": prediction == pair["output"],
            "signature": coupling_signature(pair["input"]),
        })

    generated_rows = []
    for difficulty in (None, "easy", "medium", "hard"):
        for index in range(150):
            sample = gen.generate(
                910_000 + index,
                index * 17 + 5,
                difficulty=difficulty,
            )
            signature = coupling_signature(sample)
            generated_rows.append({
                "difficulty": difficulty,
                "index": index,
                "self_check": gen.self_check(sample),
                "all_bands_follow_cue": all(
                    band["cue_matches_family"] for band in signature["bands"]
                ),
                "rival_matches_rule_mirror": color_count_cued_rival(sample)
                == gen.rule_mirror(sample),
            })

    signature = coupling_signature(grid)
    report = {
        "schema": "arcpuzzles-audit-counterexample-v1",
        "task_id": TASK,
        "finding": "source color count predicts transpose-family membership",
        "generator_path": str(source_path.relative_to(WORK)),
        "generator_sha256": source_sha256,
        "rule_hash": racket["executed_rule_hash"],
        "input_path": str((OUT_DIR / "input.json").relative_to(WORK)),
        "racket_output_path": str((OUT_DIR / "racket.json").relative_to(WORK)),
        "rival_output_path": str((OUT_DIR / "rival.json").relative_to(WORK)),
        "racket_command": racket["command"],
        "racket_cwd": "repo",
        "counterexample": {
            "input": grid,
            "generator_self_check": gen.self_check(grid),
            "strict_canonical_like": gen.strict_canonical_like(grid),
            "observed_overrides": gen.observe_overrides(grid),
            "coupling_signature": signature,
            "actual_racket_output": actual,
            "rival_output": rival,
            "outputs_disagree": actual != rival,
            "validator_accepts": not gen.self_check(grid),
        },
        "shortcut_fit": {
            "canonical_labeled_pairs": len(canonical_rows),
            "canonical_rows": canonical_rows,
            "fits_all_canonical_labeled_pairs": all(row["fits"] for row in canonical_rows),
            "generated_samples_checked": len(generated_rows),
            "generated_self_check_failures": sum(bool(row["self_check"]) for row in generated_rows),
            "generated_cue_violations": sum(not row["all_bands_follow_cue"] for row in generated_rows),
            "generated_rival_mismatches": sum(not row["rival_matches_rule_mirror"] for row in generated_rows),
        },
        "interpretation": (
            "A learner can treat source-color count as a perfect gate for transpose-family membership: "
            "three colors means transpose/anti-transpose, two colors means any other D4 branch. "
            "That gate fits every canonical labeled pair and all 600 sampled production inputs, "
            "but fails a validator-accepted three-color rotate_cw band."
        ),
        "limits": (
            "The rival still uses the selected relation inside the sampler-supported coupling; "
            "the finding isolates an unintended secondary cue rather than claiming the whole task is trivial."
        ),
    }
    (OUT_DIR / "probe.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "generator_sha256": source_sha256,
        "validator_accepts": report["counterexample"]["validator_accepts"],
        "outputs_disagree": report["counterexample"]["outputs_disagree"],
        "canonical_labeled_pairs": report["shortcut_fit"]["canonical_labeled_pairs"],
        "fits_all_canonical": report["shortcut_fit"]["fits_all_canonical_labeled_pairs"],
        "generated_samples_checked": report["shortcut_fit"]["generated_samples_checked"],
        "generated_cue_violations": report["shortcut_fit"]["generated_cue_violations"],
        "generated_rival_mismatches": report["shortcut_fit"]["generated_rival_mismatches"],
        "out": str((OUT_DIR / "probe.json").relative_to(WORK)),
    }, sort_keys=True))
    return int(
        not report["counterexample"]["validator_accepts"]
        or not report["counterexample"]["outputs_disagree"]
        or not report["shortcut_fit"]["fits_all_canonical_labeled_pairs"]
        or report["shortcut_fit"]["generated_self_check_failures"] != 0
        or report["shortcut_fit"]["generated_cue_violations"] != 0
        or report["shortcut_fit"]["generated_rival_mismatches"] != 0
    )


if __name__ == "__main__":
    raise SystemExit(main())
