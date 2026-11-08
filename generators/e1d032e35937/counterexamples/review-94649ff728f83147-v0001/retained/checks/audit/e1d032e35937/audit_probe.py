#!/usr/bin/env python3
"""Findings-only replay for e1d032e35937; execute through review.py run.

prepare writes the exact Racket input batch and local observations.
compare consumes only the public arcpuzzles apply receipt, never a Python oracle.
An exit status of zero means the audit observations were reproduced.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from reviewer_support import canonical_pairs, canonical_path, find_root, load_selected_generator

TASK_ID = "e1d032e35937"
BASE = Path(__file__).resolve().parent


def digest(value):
    return hashlib.sha256(json.dumps(value, separators=(",", ":")).encode()).hexdigest()


def write(name, value):
    path = BASE / name
    if path.exists():
        raise FileExistsError(f"Refusing to replace retained evidence: {path}")
    path.write_text(json.dumps(value, indent=2) + "\n")


def fixed_canvas_reflection(grid):
    """Intentional rival: fill zeros from the opposite canvas column, ignoring the bar."""
    return [[value or reflected for value, reflected in zip(row, reversed(row))]
            for row in grid]


def prepare():
    root = find_root(__file__)
    module, source, source_hash = load_selected_generator(TASK_ID, root=root)
    from puzzle_generators.base import set_ctx_observer
    canonical = [json.loads(line) for line in canonical_path(root).open()
                 if json.loads(line).get("task_id") == TASK_ID]
    assert len(canonical) == 1
    pairs = canonical_pairs(TASK_ID, root=root, labeled_only=True)

    def generate(seed, sample_index, difficulty, overrides):
        contexts = []
        set_ctx_observer(contexts.append)
        try:
            grid = module.generate(seed, sample_index, difficulty=difficulty, **overrides)
            result = {"input": grid, "input_sha256": digest(grid),
                      "self_check_errors": module.self_check(grid, difficulty=difficulty),
                      "height": len(grid), "width": len(grid[0]),
                      "source_colors": sorted({v for row in grid for v in row if v not in (0, 8)}),
                      "error": None}
        except Exception as exc:
            result = {"input": None, "input_sha256": None,
                      "self_check_errors": None, "error": f"{type(exc).__name__}: {exc}"}
        finally:
            set_ctx_observer(None)
        result.update(seed=seed, sample_index=sample_index,
                      difficulty=difficulty, overrides=overrides,
                      overrides_used=[ctx.overrides_used() for ctx in contexts])
        return result

    # Same h/w/count ranges as ordinary easy draws, with a different bar position.
    witness = [[0] * 9 for _ in range(8)]
    for row in witness:
        row[3] = 8
    for r, c, v in [(1, 1, 2), (3, 2, 3), (5, 0, 4)]:
        witness[r][c] = v
    cases = [{"case_id": "hand_off_center", "kind": "hand_constructed",
              "seed": None, "sample_index": None, "difficulty": None, "overrides": {},
              "input": witness, "input_sha256": digest(witness),
              "self_check_errors": module.self_check(witness),
              "documented_domain": "Satisfies INVARIANTS and AXES shape/count ranges; not in helpful generator support.",
              "bar_column": 3, "canvas_center_column": 4}]
    for pair in pairs:
        cases.append({"case_id": f"canonical_v{pair['variant']}_{pair['split']}_{pair['pair_index']}",
                      "kind": "canonical", "seed": None, "sample_index": None,
                      "difficulty": None, "overrides": {}, **pair,
                      "input_sha256": digest(pair["input"]),
                      "self_check_errors": module.self_check(pair["input"])})
    for difficulty in ("easy", "medium", "hard"):
        for seed in (0, 1, 17):
            for sample_index in (0, 1):
                result = generate(seed, sample_index, difficulty, {})
                assert result["error"] is None, result
                cases.append({"case_id": f"generated_{difficulty}_s{seed}_i{sample_index}",
                              "kind": "generated", **result})
    for index, case in enumerate(cases):
        case["racket_result_index"] = index
        case["rival_output"] = fixed_canvas_reflection(case["input"])
    assert all(case["self_check_errors"] == [] for case in cases)

    baseline = generate(17, 0, "medium", {})
    controls = []
    for key, values in (("palette_kind", module.PALETTE_KINDS),
                        ("texture", module.HELPFUL_TEXTURES),
                        ("palette_size", range(1, 7)),
                        ("n_distinct_colors", range(1, 7))):
        for value in values:
            result = generate(17, 0, "medium", {key: value})
            result["equals_no_override"] = result["input"] == baseline["input"]
            controls.append(result)
    boundary_cases = []
    for difficulty in (None, "easy", "medium", "hard"):
        for overrides in ({"source_count": 1}, {"source_count": 12}, {"grid_h": 5}):
            boundary_cases.append(generate(0, 0, difficulty, overrides))
    width_cases = [generate(0, 0, "medium", {"grid_w": 10}),
                   generate(0, 0, "hard", {"grid_w": 14})]
    declarations = {key: getattr(module, key, None)
                    for key in ("CANONICAL_SHORTCUTS", "LESSON_COMPETITORS", "LESSON_CONTRACT")}
    report = {"schema": "e1d032e35937-focused-audit-v1", "task_id": TASK_ID,
              "generator_version": module.VERSION, "generator_sha256": source_hash,
              "generator_source": str(source.relative_to(root)),
              "actual_cwd": str(Path.cwd()), "root": str(root),
              "canonical_program_sha256": hashlib.sha256(canonical[0]["program_solution"].encode()).hexdigest(),
              "canonical_record_sha256": digest(canonical[0]), "canonical_record": canonical[0],
              "prior_lead": "review-bf9d7c5f13da3e98:v0001; leads independently reproduced, not reused as measurement",
              "declared_competitors": declarations,
              "cases": cases, "control_baseline": baseline, "controls": controls,
              "boundary_cases": boundary_cases, "width_cases": width_cases}
    write("input.json", {"inputs": [case["input"] for case in cases]})
    write("probe.json", report)
    print(json.dumps({"generator_sha256": source_hash, "racket_input_count": len(cases),
                      "generated_count": sum(case["kind"] == "generated" for case in cases),
                      "control_comparisons": len(controls), "retained_contract_exceptions": sum(bool(c["error"]) for c in boundary_cases),
                      "width_probes": len(width_cases)}))


def compare():
    probe = json.loads((BASE / "probe.json").read_text())
    racket = json.loads((BASE / "racket.json").read_text())
    assert racket["task_id"] == TASK_ID
    assert racket["generator_sha256"] == probe["generator_sha256"]
    assert racket["rule_hash_matches_catalog"] is True
    results = []
    for case, actual in zip(probe["cases"], racket["results"], strict=True):
        assert actual["index"] == case["racket_result_index"]
        assert actual["input"] == case["input"]
        assert actual["error"] is None, actual
        actual_grid, rival = actual["output"], case["rival_output"]
        assert len(actual_grid) == len(rival)
        differences = [{"row": r, "col": c, "racket": a, "rival": b}
                       for r, (actual_row, rival_row) in enumerate(zip(actual_grid, rival, strict=True))
                       for c, (a, b) in enumerate(zip(actual_row, rival_row, strict=True)) if a != b]
        results.append({**case, "racket_output": actual_grid,
                        "rival_matches_racket": not differences,
                        "differences": differences,
                        "canonical_label_matches_racket": actual_grid == case["output"] if case["kind"] == "canonical" else None})
    witness = results[0]
    generated = [row for row in results if row["kind"] == "generated"]
    canonical = [row for row in results if row["kind"] == "canonical"]
    summary = {"authority_inputs": len(results), "authority_errors": 0,
               "validator_accepted_inputs": sum(row["self_check_errors"] == [] for row in results),
               "generated_inputs": len(generated),
               "unique_generated_inputs": len({row["input_sha256"] for row in generated}),
               "generated_rival_matches": sum(row["rival_matches_racket"] for row in generated),
               "canonical_pairs": len(canonical),
               "canonical_rival_matches": sum(row["rival_matches_racket"] for row in canonical),
               "canonical_racket_label_matches": sum(row["canonical_label_matches_racket"] for row in canonical),
               "hand_witness_differences": len(witness["differences"]),
               "palette_controls": len(probe["controls"]),
               "unchanged_controls": sum(row["equals_no_override"] for row in probe["controls"]),
               "unconsumed_controls": sum(all(not item for item in row["overrides_used"]) for row in probe["controls"]),
               "baseline_distinct_source_colors": len(probe["control_baseline"]["source_colors"]),
               "boundary_probes": len(probe["boundary_cases"]),
               "boundary_exceptions": sum(bool(row["error"]) for row in probe["boundary_cases"]),
               "width_probes": len(probe["width_cases"]),
               "width_mismatches": sum(row.get("width") != row["overrides"]["grid_w"] for row in probe["width_cases"])}
    bindings = {key: racket[key] for key in ("task_id", "generator_sha256", "executed_rule_hash",
                "catalog_rule_hash", "rule_text_sha256", "command", "cwd")}
    write("comparison.json", {"summary": summary, "source_bindings": bindings,
                              "canonical_program_sha256": probe["canonical_program_sha256"],
                              "cases": results})
    write("counterexample.json", {"source_bindings": bindings,
                                   "canonical_program_sha256": probe["canonical_program_sha256"], **witness})
    print(json.dumps(summary, sort_keys=True))
    assert summary["generated_rival_matches"] == summary["generated_inputs"] == 18
    assert summary["canonical_racket_label_matches"] == summary["canonical_rival_matches"] == summary["canonical_pairs"] == 3
    assert summary["hand_witness_differences"] > 0
    assert summary["unchanged_controls"] == summary["unconsumed_controls"] == summary["palette_controls"] == 20
    assert summary["baseline_distinct_source_colors"] > 1
    assert summary["boundary_exceptions"] == summary["boundary_probes"] == 12
    assert summary["width_mismatches"] == summary["width_probes"] == 2


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("prepare", "compare"))
    parser.add_argument("--out-dir", type=Path, default=BASE)
    args = parser.parse_args()
    BASE = args.out_dir.resolve()
    BASE.mkdir(parents=True, exist_ok=True)
    globals()[args.mode]()
