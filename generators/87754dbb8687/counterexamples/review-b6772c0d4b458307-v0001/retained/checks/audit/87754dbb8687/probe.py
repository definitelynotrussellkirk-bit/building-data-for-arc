"""Bounded findings-only audit of the selected equality-matrix generator.

Uses public reviewer_support loading and Catalog.apply for reference labels.
All outputs are retained beside this script; target sources remain untouched.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

from arcpuzzles import Catalog
from reviewer_support import canonical_pairs, find_root, load_selected_generator


TASK = "87754dbb8687"
SOURCE_SHA = "59979b211b1389ba34214d0c7748b58457518df7f22912745cb251468cd79aa0"
RULE_HASH = "0ac662ce40c7"


def sha(value):
    blob = value if isinstance(value, bytes) else json.dumps(value, separators=(",", ":")).encode()
    return hashlib.sha256(blob).hexdigest()


def write(name, value):
    with (Path(__file__).resolve().parent / name).open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write("\n")


def equality(grid, *, suppress_blue=False):
    top = grid[0][1:]
    left = [row[0] for row in grid[1:]]
    return [[color if color == col and color != 0 and not (suppress_blue and color == 1) else 0
             for col in top] for color in left]


def measurements(grid):
    top, left = set(grid[0][1:]), {row[0] for row in grid[1:]}
    return {"h": len(grid), "w": len(grid[0]),
            "shared_header_color_count": len((top & left) - {0}),
            "distinct_nonzero_color_count": len((top | left) - {0}),
            "header_colors": sorted((top | left) - {0})}


def main():
    root = find_root(__file__)
    module, path, digest = load_selected_generator(TASK, root=root)
    assert digest == SOURCE_SHA, ("Audited source changed", digest)
    catalog = Catalog(root)
    metadata = catalog.describe(TASK)
    assert metadata["rule_hash"] == RULE_HASH
    source_binding = {"task_id": TASK, "generator_path": str(path.relative_to(root)),
                      "generator_sha256": digest, "catalog_rule_hash": RULE_HASH,
                      "probe_sha256": sha(Path(__file__).read_bytes())}
    generated, observations = [], []
    for band in ("easy", "medium", "hard"):
        for seed in range(8):
            for index in (0, 1):
                grid = module.generate(seed, index, difficulty=band)
                generated.append(grid)
                observations.append({"generate_call": {"seed": seed, "sample_index": index,
                    "difficulty": band, "overrides": {}}, "input_sha256": sha(grid),
                    "self_check": module.self_check(grid, difficulty=band), **measurements(grid)})
    pairs = canonical_pairs(TASK, root=root)
    blue = [[0, 1, 2, 3, 4], [1, 0, 0, 0, 0], [2, 0, 0, 0, 0],
            [3, 0, 0, 0, 0], [4, 0, 0, 0, 0]]
    inputs = generated + [pair["input"] for pair in pairs] + [blue]
    write("inputs.json", inputs)
    applied = catalog.apply(TASK, inputs, reference="canonical", timeout=180,
                            check_generator_domain=True)
    applied["audit_command"] = ["WORK/.venv-review/bin/python", "review.py", "run",
                               "../.venv-review/bin/python", "../checks/audit/87754dbb8687/probe.py"]
    applied["audit_command_cwd"] = "packet_root"
    applied["payload_cwd"] = str(Path.cwd())
    write("racket.json", applied)
    assert applied["generator_sha256"] == SOURCE_SHA
    assert applied["executed_rule_hash"] == RULE_HASH
    results = applied["results"]
    assert len(results) == len(inputs)
    for observation, grid, result in zip(observations, generated, results):
        observation["racket_error"] = result.get("error")
        observation["literal_equality_matches_racket"] = equality(grid) == result["output"]
        observation["nonblue_rival_matches_racket"] = equality(grid, suppress_blue=True) == result["output"]
    canonical_results = []
    for index, pair in enumerate(pairs):
        actual = results[len(generated) + index]
        canonical_results.append({"variant": pair["variant"], "split": pair["split"],
             "pair_index": pair["pair_index"], "self_check": module.self_check(pair["input"]),
             "racket_matches_saved_label": actual["output"] == pair["output"],
             "nonblue_rival_matches_label": equality(pair["input"], suppress_blue=True) == pair["output"],
             "input_sha256": sha(pair["input"])})
    override_tests = []
    override_choices = {"n_shared": (1, 3), "palette_size": (2, 8),
                        "n_distinct_colors": (2, 8), "palette_kind": ("warm", "cool"),
                        "texture": ("warm", "cool")}
    witness = None
    for name, choices in override_choices.items():
        for seed in range(8):
            baseline = module.generate(seed, 0, difficulty="medium")
            draws = []
            for value in choices:
                grid = module.generate(seed, 0, difficulty="medium", **{name: value})
                row = {"override": {name: value}, "input_sha256": sha(grid),
                       "equals_unoverridden_draw": grid == baseline,
                       "self_check": module.self_check(grid), **measurements(grid)}
                draws.append(row)
                if name == "palette_size" and value == 2 and row["distinct_nonzero_color_count"] > 2 and witness is None:
                    canonical_index = next(i for i, obs in enumerate(observations)
                        if obs["generate_call"] == {"seed": seed, "sample_index": 0, "difficulty": "medium", "overrides": {}})
                    witness = {**source_binding, "finding_id": "A877-1", "kind": "reproduced_override_contract_defect",
                        "generate_call": {"seed": seed, "sample_index": 0, "difficulty": "medium", "overrides": {name: value}},
                        "input": grid, "self_check": module.self_check(grid), **measurements(grid),
                        "actual_racket_output": results[canonical_index]["output"],
                        "racket_evidence": "checks/audit/87754dbb8687/racket.json",
                        "racket_result_index": canonical_index,
                        "reference_input_equals_override_input": inputs[canonical_index] == grid,
                        "expected_palette_size": 2,
                        "explanation": "The declared palette_size override is ignored and produces more than two non-background header colors."}
            override_tests.append({"axis": name, "seed": seed, "sample_index": 0,
                                   "difficulty": "medium", "choices": draws,
                                   "both_equal_unoverridden_draw": all(row["equals_unoverridden_draw"] for row in draws)})
    bound_tests = []
    for overrides in ({"grid_h": 4}, {"grid_w": 10}):
        try:
            grid = module.generate(0, 0, difficulty=None, **overrides)
            bound_tests.append({"generate_call": {"seed": 0, "sample_index": 0, "difficulty": None,
                 "overrides": overrides}, "accepted": True, "measurements": measurements(grid)})
        except (TypeError, ValueError) as exc:
            bound_tests.append({"generate_call": {"seed": 0, "sample_index": 0, "difficulty": None,
                 "overrides": overrides}, "accepted": False, "error_type": type(exc).__name__, "error": str(exc)})
    blue_output = results[-1]["output"]
    write("blue-counterexample.json", {**source_binding, "finding_id": "A877-2",
        "kind": "reproduced_support_gap_and_suspected_shortcut",
        "construction": "handmade color-role counterfactual, not claimed to be a generated draw",
        "input": blue, "self_check": module.self_check(blue), "measurements": measurements(blue),
        "actual_racket_output": blue_output, "rival_output": equality(blue, suppress_blue=True),
        "rival_definition": "Apply equality matrix but suppress matches whose header color is 1.",
        "disagrees_with_racket": blue_output != equality(blue, suppress_blue=True),
        "racket_evidence": "checks/audit/87754dbb8687/racket.json", "racket_result_index": len(inputs) - 1,
        "domain": "Passes target self_check; 5x5 fits actual default size range. Color 1 is a legal nonzero ARC color, but generate() fixes its palette to 2..9, so this counterfactual is outside implemented generated support."})
    assert witness is not None
    write("override-counterexample.json", witness)
    write("census.json", {**source_binding, "status": "completed", "generated": observations,
        "canonical": canonical_results, "override_tests": override_tests, "bounds_tests": bound_tests,
        "declared_axes": module.AXES, "has_declared_lesson_contract": hasattr(module, "LESSON_COMPETITORS"),
        "summary": {"generated_count": len(generated), "seed_range_inclusive": [0, 7], "sample_indices": [0, 1],
            "bands": ["easy", "medium", "hard"], "canonical_pair_count": len(pairs),
            "public_racket_inputs": len(inputs), "generated_self_check_failures": sum(bool(row["self_check"]) for row in observations),
            "generated_literal_equality_mismatches": sum(not row["literal_equality_matches_racket"] for row in observations),
            "generated_nonblue_rival_matches": sum(row["nonblue_rival_matches_racket"] for row in observations),
            "generated_contains_blue": sum(1 in row["header_colors"] for row in observations),
            "canonical_reference_label_matches": sum(row["racket_matches_saved_label"] for row in canonical_results),
            "canonical_nonblue_rival_matches": sum(row["nonblue_rival_matches_label"] for row in canonical_results),
            "override_pair_tests": len(override_tests),
            "override_pairs_identical_to_unoverridden": sum(row["both_equal_unoverridden_draw"] for row in override_tests),
            "rejected_declared_boundary_values": sum(not row["accepted"] for row in bound_tests)}})
    print(json.dumps({"status": "completed", "generated": len(generated), "reference_inputs": len(inputs),
                      "override_pair_tests": len(override_tests), "source_sha256": digest}))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        write("probe-failure.json", {"exception": type(exc).__name__, "message": str(exc), "argv": sys.argv})
        raise
