"""Five-input, source-bound audit; authority labels come from public Racket commands.

This is an adversarial authoring probe, not a blind solve. It imports only the
assigned generator and its declared public helper packages, never a runner.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2] / "repo"
TASK = "311ebe067559"
EXPECTED_SHA = "2b6674e389e68102a1aa93c28a4c52929051e2b7bf36906595682a11d65891a1"


def write(name, value):
    (HERE / name).write_text(json.dumps(value, indent=2) + "\n")


def digest(value):
    return hashlib.sha256(json.dumps(value, separators=(",", ":")).encode()).hexdigest()


def load_generator():
    source = REPO / "generators" / TASK / "generator.py"
    assert hashlib.sha256(source.read_bytes()).hexdigest() == EXPECTED_SHA
    sys.path.insert(0, str(REPO / "shared" / "runtime"))
    spec = importlib.util.spec_from_file_location("audited_generator", source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def ray_output(grid, *, numeric_priority):
    """Retain emitter/blocker semantics; rival alone replaces legend by numeric order."""
    legend = [value for value in grid[0] if value]
    field = grid[1:]
    height, width = len(field), len(field[0])
    rank = {color: legend.index(color) for color in legend}
    emitters = []
    for row, cols, dr, dc in ((0, range(width), 1, 0), (height - 1, range(width), -1, 0)):
        emitters.extend((row, col, field[row][col], dr, dc)
                        for col in cols if field[row][col] not in (0, 5))
    for col, dr, dc in ((0, 0, 1), (width - 1, 0, -1)):
        emitters.extend((row, col, field[row][col], dr, dc)
                        for row in range(1, height - 1)
                        if field[row][col] not in (0, 5))
    out = [[5 if field[row][col] == 5 else 0 for col in range(width)]
           for row in range(height)]
    for row, col, color, _, _ in emitters:
        out[row][col] = color
    hits = {}
    for row, col, color, dr, dc in emitters:
        row, col = row + dr, col + dc
        while 0 <= row < height and 0 <= col < width and field[row][col] != 5:
            hits.setdefault((row, col), []).append(color)
            row, col = row + dr, col + dc
    for (row, col), colors in hits.items():
        if out[row][col] == 0:
            out[row][col] = max(colors, key=(lambda color: color) if numeric_priority
                                else (lambda color: rank.get(color, -1)))
    return out


def differing_cells(authority, rival):
    return [{"row": r, "column": c, "racket": color, "rival": rival[r][c]}
            for r, row in enumerate(authority) for c, color in enumerate(row)
            if color != rival[r][c]]


def ordinary_domain(grid):
    """Check the inspected medium generator's structural range, independently of self_check."""
    h, w = len(grid), len(grid[0])
    legend = [v for v in grid[0] if v]
    allowed = {1, 2, 3, 4, 6, 7, 8, 9}
    body = grid[1:]
    border = {(0, c) for c in range(w)} | {(h - 2, c) for c in range(w)}
    border |= {(r, c) for r in range(1, h - 2) for c in (0, w - 1)}
    emitters = [(r, c) for r, c in border if body[r][c] not in (0, 5)]
    blockers = [(r, c) for r, row in enumerate(body) for c, value in enumerate(row) if value == 5]
    predicates = {
        "medium_dimensions": 7 <= h <= 10 and 7 <= w <= 11,
        "unique_legend_3_to_5": 3 <= len(legend) <= 5 and len(legend) == len(set(legend)),
        "allowed_legend_colors": set(legend) <= allowed,
        "legend_left_packed": grid[0] == legend + [0] * (w - len(legend)),
        "three_to_six_emitters": 3 <= len(emitters) <= 6,
        "emitter_colors_in_legend": all(body[r][c] in legend for r, c in emitters),
        "one_to_three_interior_blockers": 1 <= len(blockers) <= 3 and all((r, c) not in border for r, c in blockers),
        "interior_has_only_zero_or_five": all(value in (0, 5) for r, row in enumerate(body)
                                                for c, value in enumerate(row) if (r, c) not in border),
    }
    return {"ordinary_medium_domain": all(predicates.values()), "checks": predicates}


def prepare():
    generator = load_generator()
    canonical = json.loads((HERE / "canonical.json").read_text())
    lesson = json.loads((HERE / "production.jsonl").read_text())
    rule = canonical["variants"][0]["program_solution"]
    assert canonical["generator_sha256"] == EXPECTED_SHA
    assert lesson["provenance"]["generator_sha256"] == EXPECTED_SHA
    assert lesson["program"] == rule
    assert lesson["executed_rule_hash"] == generator.RULE_HASH == canonical["rule_hash"]
    (HERE / "canonical-rule.rkt").write_text(rule)
    cases = []
    for split in ("train", "test"):
        for index, pair in enumerate(lesson[split]):
            sample_index = lesson["sample_indices"][len(cases)]
            generated = generator.generate(2, sample_index, difficulty="medium")
            assert generated == pair["input"]
            mirror = ray_output(pair["input"], numeric_priority=False)
            assert mirror == pair["output"], (split, index, "mirror mismatch")
            rival = ray_output(pair["input"], numeric_priority=True)
            errors = generator.self_check(pair["input"], difficulty="medium")
            domain = ordinary_domain(pair["input"])
            assert not errors and domain["ordinary_medium_domain"]
            cases.append({"split": split, "pair_index": index, "sample_index": sample_index,
                          "seed": 2, "difficulty": "medium", "overrides": {},
                          "input": pair["input"], "input_sha256_compact_json": digest(pair["input"]),
                          "racket_output_from_production": pair["output"], "rival_output": rival,
                          "validator_errors": errors, "domain": domain,
                          "rival_matches": pair["output"] == rival,
                          "differing_cells_zero_based": differing_cells(pair["output"], rival)})
    assert [case["rival_matches"] for case in cases] == [True, True, True, False]
    query = cases[-1]
    write("input.json", query["input"])
    write("rival_output.json", query["rival_output"])
    write("lesson-analysis.json", {"seed": 2, "difficulty": "medium", "sample_indices": [0, 1, 2, 3],
                                   "overrides": {}, "cases": cases})
    overrides = {"grid_h": 14, "grid_w": 16, "palette_size": 2, "n_distinct_colors": 2}
    baseline = generator.generate(17, 9, difficulty="medium")
    control = generator.generate(17, 9, difficulty="medium", **overrides)
    assert baseline == control
    errors = generator.self_check(control, difficulty="medium")
    domain = ordinary_domain(control)
    assert not errors and domain["ordinary_medium_domain"]
    assert (len(control), len(control[0])) == (8, 8)
    write("control-input.json", control)
    write("control-probe.json", {"seed": 17, "sample_index": 9, "difficulty": "medium",
          "overrides": overrides, "baseline_overrides": {}, "input": control,
          "baseline_input": baseline, "identical_to_no_override": True,
          "input_sha256_compact_json": digest(control),
          "observed_grid_h": len(control), "observed_grid_w": len(control[0]),
          "observed_legend_colors": len([v for v in control[0] if v]),
          "requested_controls_satisfied": False,
          "validator_errors": errors, "domain": domain,
          "python_rule_mirror_output": ray_output(control, numeric_priority=False),
          "rival_output": ray_output(control, numeric_priority=True)})
    canonical_results = []
    for variant_index, variant in enumerate(canonical["variants"]):
        for split in ("train", "test"):
            for pair_index, pair in enumerate(variant.get(split, [])):
                if "output" not in pair:
                    continue
                mirror = ray_output(pair["input"], numeric_priority=False)
                assert mirror == pair["output"]
                canonical_results.append({"variant_index": variant_index, "split": split,
                                          "pair_index": pair_index, "mirror_matches": True,
                                          "rival_matches": ray_output(pair["input"], numeric_priority=True) == pair["output"]})
    write("source-and-scope.json", {
        "task_id": TASK, "generator_path": "repo/generators/311ebe067559/generator.py",
        "generator_sha256": EXPECTED_SHA, "generator_version": generator.VERSION,
        "rule_hash": generator.RULE_HASH,
        "canonical_program_utf8_sha256": hashlib.sha256(rule.encode()).hexdigest(),
        "canonical_evidence_path": "checks/audit/311ebe067559/canonical.json",
        "canonical_labeled_pairs_examined": canonical_results,
        "ordinary_generated_unique_inputs": 5,
        "direct_generator_calls": 6,
        "public_production_accepted_pairs": 4,
        "scope": "One preselected production lesson, four ordinary medium samples; one paired exact-control probe at seed 17/index 9. No seed sweep or battery.",
        "finding_origin": "Fresh reproduction of both existing needs_triage findings in current review_index.json; no novelty claim.",
        "domain_status": "All five retained inputs satisfy ordinary medium generator structure and return no self_check errors; the override request itself is unsatisfied.",
        "target_modified": False,
    })
    print(json.dumps({"lesson_rival_matches": [case["rival_matches"] for case in cases],
                      "query_differences": query["differing_cells_zero_based"],
                      "control_shape": [len(control), len(control[0])],
                      "canonical_rival_matches": [case["rival_matches"] for case in canonical_results]}))


def verify():
    generator = load_generator()
    lesson = json.loads((HERE / "lesson-analysis.json").read_text())
    query_authority = json.loads((HERE / "racket.json").read_text())
    control_authority = json.loads((HERE / "control-racket.json").read_text())
    control = json.loads((HERE / "control-probe.json").read_text())
    source = json.loads((HERE / "source-and-scope.json").read_text())
    for receipt in (query_authority, control_authority):
        assert receipt["schema"] == "arcpuzzles-apply-v1"
        assert receipt["task_id"] == TASK
        assert receipt["generator_sha256"] == EXPECTED_SHA
        assert receipt["executed_rule_hash"] == generator.RULE_HASH
        assert receipt["rule_hash_matches_catalog"]
        assert len(receipt["results"]) == 1
        assert receipt["results"][0]["valid_output"]
        assert receipt["results"][0]["error"] is None
    query = lesson["cases"][-1]
    query_result = query_authority["results"][0]
    control_result = control_authority["results"][0]
    assert query_result["input"] == query["input"]
    assert query_result["output"] == query["racket_output_from_production"]
    assert control_result["input"] == control["input"]
    assert control_result["output"] == control["python_rule_mirror_output"]
    differences = differing_cells(query_result["output"], query["rival_output"])
    assert differences == [{"row": 3, "column": 7, "racket": 7, "rival": 9}]
    for case in lesson["cases"]:
        assert not generator.self_check(case["input"], difficulty="medium")
    assert not generator.self_check(control["input"], difficulty="medium")
    source["executed_rule_text_sha256"] = query_authority["rule_text_sha256"]
    assert source["executed_rule_text_sha256"] == control_authority["rule_text_sha256"]
    write("source-and-scope.json", source)
    write("verified-counterexample.json", {
        "task_id": TASK,
        "status": "reproduced_unresolved_findings",
        "source": source,
        "finding_a1": {
            "description": "Numeric color priority fits all three production demos and fails on the query.",
            "seed": 2, "sample_indices": [0, 1, 2, 3], "difficulty": "medium", "overrides": {},
            "rival_matches_demos": [True, True, True], "rival_matches_query": False,
            "query_input": query["input"], "query_input_sha256": query_result["input_sha256"],
            "racket_output": query_result["output"], "rival_output": query["rival_output"],
            "differing_cells_zero_based": differences,
            "validator_errors": query["validator_errors"], "domain": query["domain"],
            "independent_public_apply_matches_production": True,
            "production_lesson_hook": "not_declared",
            "evidence": ["production.jsonl", "lesson-analysis.json", "input.json", "rival_output.json", "racket.json"],
        },
        "finding_a2": {
            "description": "Advertised exact dimensions and palette controls are ignored.",
            "seed": 17, "sample_index": 9, "difficulty": "medium", "overrides": control["overrides"],
            "input": control["input"], "input_sha256": control_result["input_sha256"],
            "same_as_no_override": True, "observed_shape": [8, 8], "observed_legend_colors": 5,
            "racket_output": control_result["output"], "rival_output": control["rival_output"],
            "validator_errors": control["validator_errors"], "domain": control["domain"],
            "evidence": ["control-probe.json", "control-input.json", "control-racket.json"],
        },
        "verification": {
            "query_public_apply": "success", "control_public_apply": "success",
            "rule_hash_matches_catalog": True, "all_five_validator_inputs_accepted": True,
            "catalog_approved": False, "train_safety": "unverified",
            "python_probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "scope": source["scope"],
        },
    })
    print(json.dumps({"verified": True, "task_id": TASK,
                      "query_public_apply_matches_production": True,
                      "query_differences": differences,
                      "control_public_apply_valid": True,
                      "all_five_validator_inputs_accepted": True,
                      "generator_sha256": EXPECTED_SHA,
                      "executed_rule_hash": generator.RULE_HASH}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["prepare", "verify"])
    args = parser.parse_args()
    {"prepare": prepare, "verify": verify}[args.action]()
