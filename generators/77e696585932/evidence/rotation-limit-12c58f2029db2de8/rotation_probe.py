"""Bounded, read-only audit of the selected three-profile lesson schedule.

All labels are obtained from Catalog.apply(reference="canonical"), which executes
the selected Racket authority. The Python tie rival is independently implemented.
Only the requested evidence JSON is written; selected task files remain unchanged.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
TASK = "77e696585932"
ROOT = Path(__file__).resolve().parents[3] / "repo"
SOURCE = ROOT / "generators" / TASK / "generator.py"
CANONICAL = ROOT / "shared/data/base/solutions/training/1a07d186__77e696585932.json"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tie_to_column(grid):
    """Nearest matching line, with column winning a row/column distance tie."""
    height, width = len(grid), len(grid[0])
    rows = [(r, grid[r][0]) for r in range(height)
            if grid[r][0] and all(value == grid[r][0] for value in grid[r])]
    columns = [(c, grid[0][c]) for c in range(width)
               if grid[0][c] and all(grid[r][c] == grid[0][c] for r in range(height))]
    row_indices = {r for r, _ in rows}
    column_indices = {c for c, _ in columns}
    out = [[grid[r][c] if r in row_indices or c in column_indices else 0
            for c in range(width)] for r in range(height)]
    for r in range(height):
        for c in range(width):
            color = grid[r][c]
            if not color or r in row_indices or c in column_indices:
                continue
            matched_rows = [(abs(rr-r), rr) for rr, value in rows if value == color]
            matched_columns = [(abs(cc-c), cc) for cc, value in columns if value == color]
            if not matched_rows and not matched_columns:
                continue
            dr, rr = min(matched_rows, default=(9999, -1))
            dc, cc = min(matched_columns, default=(9999, -1))
            if dr < dc:
                destination = (rr - 1 if r < rr else rr + 1, c)
            else:
                destination = (r, cc - 1 if c < cc else cc + 1)
            out[destination[0]][destination[1]] = color
    return out


def differences(expected, actual):
    return [{"row": r, "column": c, "racket": value, "rival": actual[r][c]}
            for r, row in enumerate(expected) for c, value in enumerate(row)
            if value != actual[r][c]]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    before = {"generator_sha256": digest(SOURCE), "canonical_record_sha256": digest(CANONICAL)}
    spec = importlib.util.spec_from_file_location("audited_generator_77e696585932", SOURCE)
    generator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(generator)
    seed, band = 0, "medium"
    start = next(i for i in range(3) if generator.schedule_profile(seed, i, band) == "rows")
    calls = [{"seed": seed, "sample_index": start + i, "difficulty": band, "overrides": {}}
             for i in range(4)]
    grids = [generator.generate(call["seed"], call["sample_index"],
                                difficulty=band) for call in calls]
    profiles = [generator.observe_overrides(grid)["scene_profile"] for grid in grids]
    assert profiles == ["rows", "columns", "cross", "rows"], profiles

    record = json.loads(CANONICAL.read_text())
    canonical_pairs = [{"split": "train", "index": i, **pair}
                       for i, pair in enumerate(record["visible_context"]["train"])]
    for i, (pair, output) in enumerate(zip(record["visible_context"]["test_inputs"],
                                         record["verification"]["expected_test_outputs"], strict=True)):
        canonical_pairs.append({"split": "test", "index": i,
                                "input": pair["input"], "output": output})
    sys.path.insert(0, str(ROOT / "src"))
    from arcpuzzles.catalog import Catalog
    application = Catalog(ROOT).apply(TASK, grids + [p["input"] for p in canonical_pairs],
                                      reference="canonical", timeout=90,
                                      check_generator_domain=True)
    assert application["rule_hash_matches_catalog"], application
    assert application["executed_rule_hash"] == generator.RULE_HASH
    assert all(result["output"] is not None for result in application["results"])
    results = application.pop("results")
    pairs = []
    for call, profile, grid, result in zip(calls, profiles, grids, results[:4], strict=True):
        predicted = tie_to_column(grid)
        assert predicted == generator.LESSON_COMPETITORS["tie_to_column"](grid)
        pairs.append({"generate_call": call, "profile": profile, "input": grid,
                      "output": result["output"], "reference_result": result,
                      "self_check": generator.self_check(grid, difficulty=band),
                      "strict_canonical_like": generator.strict_canonical_like(grid),
                      "tie_to_column_prediction": predicted,
                      "tie_to_column_differences": differences(result["output"], predicted)})
    canonical_validation = []
    for pair, result in zip(canonical_pairs, results[4:], strict=True):
        expected = result["output"]
        assert expected == pair["output"], (pair["split"], pair["index"])
        prediction = tie_to_column(pair["input"])
        canonical_validation.append({**pair, "racket_output": expected,
                                     "reference_result": result,
                                     "tie_to_column_prediction": prediction,
                                     "rival_fits": prediction == expected})

    rotations = []
    for query_index in range(4):
        demo_indices = [i for i in range(4) if i != query_index]
        demos = [{"input": pairs[i]["input"], "output": pairs[i]["output"]} for i in demo_indices]
        query = {"input": pairs[query_index]["input"], "output": pairs[query_index]["output"]}
        scores = {}
        for name, rival in generator.LESSON_COMPETITORS.items():
            demo_fit = [rival(demo["input"]) == demo["output"] for demo in demos]
            query_fit = rival(query["input"]) == query["output"]
            scores[name] = {"demo_fit": demo_fit, "query_fit": query_fit,
                            "status": "ambiguous" if all(demo_fit) and not query_fit else
                            "survived_all" if all(demo_fit) and query_fit else "refuted"}
        rotations.append({"query_index": query_index, "demo_indices": demo_indices,
                          "query_profile": profiles[query_index],
                          "demo_profiles": [profiles[i] for i in demo_indices],
                          "lesson_identifiable_reasons": generator.lesson_identifiable(demos, query),
                          "competitors": scores})
    assert not rotations[3]["lesson_identifiable_reasons"], rotations[3]
    assert rotations[2]["competitors"]["tie_to_column"]["status"] == "ambiguous"
    assert rotations[2]["lesson_identifiable_reasons"], "The hook should warn about missing cross"
    assert all(p["rival_fits"] for p in canonical_validation)
    assert all(not p["self_check"] and not p["strict_canonical_like"] for p in pairs)
    after = {"generator_sha256": digest(SOURCE), "canonical_record_sha256": digest(CANONICAL)}
    assert after == before
    evidence = {"schema": "arc-generator-bounded-rotation-audit-v1", "task_id": TASK,
                "source": {"generator_file": str(SOURCE.relative_to(ROOT)),
                           "canonical_record": str(CANONICAL.relative_to(ROOT)),
                           "version": generator.VERSION, "rule_hash": generator.RULE_HASH,
                           **before, "after": after, "source_changed": after != before},
                "scope": {"generated_draws": 4, "canonical_labeled_pairs": len(canonical_pairs),
                          "racket_applications": len(results), "query_rotations": 4,
                          "seed": seed, "start_index": start, "difficulty": band,
                          "default_production_query_index": 3},
                "reference_application": application,
                "pairs": pairs, "canonical_validation": canonical_validation, "rotations": rotations,
                "finding": {"kind": "rotation_ambiguity_correctly_rejected_by_hook",
                            "production_original_orientation_ambiguous": False,
                            "ambiguous_query_index": 2, "rival": "tie_to_column",
                            "qualification": "Ordered three-demo production contains all profiles. Holding out the sole cross removes every tie cue; the generator's hook correctly rejects that lesson."}}
    args.out.write_text(json.dumps(evidence, indent=2) + "\n")
    print(json.dumps({"task_id": TASK, "generator_sha256": before["generator_sha256"],
                      "executed_rule_hash": application["executed_rule_hash"],
                      "scope": evidence["scope"], "profiles": profiles,
                      "canonical_rival_fit": [p["rival_fits"] for p in canonical_validation],
                      "original_hook": rotations[3]["lesson_identifiable_reasons"],
                      "ambiguous_rotation": rotations[2],
                      "cross_query_changed_cells": pairs[2]["tie_to_column_differences"],
                      "source_changed": False, "out": str(args.out)}, indent=2))


if __name__ == "__main__":
    main()
