"""Findings-only, source-bound audit of b43d103c28d9.

Run from WORK through run_with_racket.py using the WORK .venv interpreter.
This script writes only beside itself.  It never changes generator sources,
reference rules, approval metadata, inherited evidence, or solve lanes.
"""
from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path

from arcpuzzles import Catalog
from reviewer_support import canonical_pairs, find_root, load_selected_generator


TASK_ID = "b43d103c28d9"
EXPECTED_SOURCE_SHA256 = "9130060c0791667161cb26c103102a26c228f31061e193144d3fd097e3735bfc"
EXPECTED_RULE_HASH = "a2f07dce6b36"
ROOT = find_root(__file__)
HERE = Path(__file__).resolve().parent


def stable_pack(grid):
    """Independent audit probe; reference labels are obtained from Racket."""
    out = [[0] * len(grid[0]) for _ in grid]
    for c in range(len(grid[0])):
        for r, value in enumerate(row[c] for row in grid if row[c] != 0):
            out[r][c] = value
    return out


def group_middle_color(grid):
    """Pack leading A, all following non-A, then returning A in each column.

    This preserves A*B*A* and A*B* but incorrectly changes A-B-A-B into
    A-B-B-A. It uses each column's own first color, so the query does not rely
    on the inherited audit's rejected mixed-first-color input.
    """
    out = [[0] * len(grid[0]) for _ in grid]
    for c in range(len(grid[0])):
        values = [row[c] for row in grid if row[c] != 0]
        if not values:
            continue
        first = values[0]
        leading = 0
        while leading < len(values) and values[leading] == first:
            leading += 1
        remaining = values[leading:]
        reordered = (values[:leading] + [v for v in remaining if v != first]
                     + [v for v in remaining if v == first])
        for r, value in enumerate(reordered):
            out[r][c] = value
    return out


def nonzero_runs(grid, column):
    runs = []
    for row in grid:
        if row[column] != 0 and (not runs or row[column] != runs[-1]):
            runs.append(row[column])
    return runs


def handmade_query():
    grid = [[0] * 8 for _ in range(8)]
    for c in (2, 3, 4):
        grid[1][c] = 1
        grid[3][c] = 2
        grid[5][c] = 1
    grid[7][3] = 2
    return grid


def main():
    generator, source, source_sha256 = load_selected_generator(TASK_ID, root=ROOT)
    if source_sha256 != EXPECTED_SOURCE_SHA256:
        raise RuntimeError("Audited source has changed; draw a new source-bound audit")
    pairs = canonical_pairs(TASK_ID, root=ROOT)
    assert len(pairs) == 4
    canonical_checks = []
    for pair in pairs:
        canonical_checks.append({
            "variant": pair["variant"], "split": pair["split"],
            "pair_index": pair["pair_index"],
            "self_check": generator.self_check(pair["input"]),
            "stable_probe_matches_label": stable_pack(pair["input"]) == pair["output"],
            "rival_matches_label": group_middle_color(pair["input"]) == pair["output"],
        })
    assert all(not row["self_check"] and row["stable_probe_matches_label"]
               and row["rival_matches_label"] for row in canonical_checks)

    cohort = {}
    reference_inputs = []
    reference_bindings = []
    for band in ("easy", "medium", "hard"):
        scenes = Counter()
        highest_runs = 0
        mismatches = []
        for index in range(200):
            seed = 2026101900 + index
            grid = generator.generate(seed, index, difficulty=band)
            assert generator.self_check(grid) == []
            scenes[generator.observe_overrides(grid)["scene_type"]] += 1
            highest_runs = max(highest_runs, max(
                len(nonzero_runs(grid, c)) for c in range(len(grid[0]))
            ))
            if group_middle_color(grid) != stable_pack(grid):
                mismatches.append({"seed": seed, "sample_index": index})
            if index < 8:  # Two full schedules in every difficulty: 24 Racket probes.
                reference_inputs.append(grid)
                reference_bindings.append({
                    "kind": "cohort_sample", "difficulty": band,
                    "seed": seed, "sample_index": index, "overrides": {},
                })
        cohort[band] = {
            "count": 200, "seed_formula": "2026101900 + sample_index",
            "sample_indexes": [0, 199], "overrides": {},
            "scene_counts": dict(scenes), "max_nonzero_color_runs": highest_runs,
            "rival_matches_independent_probe": 200 - len(mismatches),
            "rival_mismatches": mismatches,
        }
    assert all(row["rival_matches_independent_probe"] == 200 for row in cohort.values())

    demos = []
    for index in range(4):
        grid = generator.generate(20261019, index, difficulty="hard")
        demos.append({"seed": 20261019, "sample_index": index,
                      "difficulty": "hard", "overrides": {}, "input": grid})
        reference_inputs.append(grid)
        reference_bindings.append({"kind": "demonstration", "demo_index": index,
                                   "seed": 20261019, "sample_index": index,
                                   "difficulty": "hard", "overrides": {}})
    for pair in pairs:
        reference_inputs.append(pair["input"])
        reference_bindings.append({"kind": "canonical", "variant": pair["variant"],
                                   "split": pair["split"], "pair_index": pair["pair_index"]})
    query = handmade_query()
    reference_inputs.append(query)
    reference_bindings.append({"kind": "query", "seed": None, "sample_index": None,
                               "overrides": None, "origin": "hand-constructed"})

    overrides_checked = []
    for requested in (10.9, 14.9, "10", 10.0, 8, 14, 7, 15, True, False):
        row = {"seed": 17, "sample_index": 0, "difficulty": None,
               "overrides": {"grid_size": requested},
               "requested_type": type(requested).__name__}
        try:
            grid = generator.generate(17, 0, grid_size=requested)
            row.update(status="returned", observed=generator.observe_overrides(grid),
                       self_check=generator.self_check(grid))
            if type(requested) is float and requested == 14.9:
                row["input"] = grid
                reference_inputs.append(grid)
                reference_bindings.append({"kind": "coerced_override", "seed": 17,
                                           "sample_index": 0, "difficulty": None,
                                           "overrides": {"grid_size": requested}})
        except (TypeError, ValueError) as error:
            row.update(status="rejected", error_type=type(error).__name__, error=str(error))
        overrides_checked.append(row)

    # These are the authoritative labels, obtained in one bounded public call.
    applied = Catalog(ROOT).apply(TASK_ID, reference_inputs,
                                  reference="canonical", allow_unapproved=True,
                                  check_generator_domain=True, timeout=120)
    assert applied["generator_sha256"] == EXPECTED_SOURCE_SHA256
    assert applied["executed_rule_hash"] == EXPECTED_RULE_HASH
    assert applied["rule_hash_matches_catalog"]
    query_record = None
    for binding, row in zip(reference_bindings, applied["results"], strict=True):
        row["audit_binding"] = binding
        row["independent_probe_matches_reference"] = stable_pack(row["input"]) == row["output"]
        row["rival_prediction"] = group_middle_color(row["input"])
        row["rival_matches_reference"] = row["rival_prediction"] == row["output"]
        assert row["independent_probe_matches_reference"]
        if binding["kind"] == "demonstration":
            demos[binding["demo_index"]]["output"] = row["output"]
            demos[binding["demo_index"]]["rival_matches_reference"] = row["rival_matches_reference"]
        elif binding["kind"] == "query":
            query_record = row
        else:
            assert row["rival_matches_reference"]
    assert query_record is not None and not query_record["rival_matches_reference"]
    query_reasons = generator.self_check(query)
    lesson_reasons = generator.lesson_identifiable(demos, query_record)
    assert query_reasons == [] and lesson_reasons == []
    assert all(pair["rival_matches_reference"] for pair in demos)
    assert hashlib.sha256(source.read_bytes()).hexdigest() == EXPECTED_SOURCE_SHA256

    result = {
        "schema": "arcpuzzles-focused-audit-v1", "task_id": TASK_ID,
        "source_path": str(source.relative_to(ROOT)),
        "generator_sha256": source_sha256, "generator_version": generator.VERSION,
        "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "executed_rule_hash": applied["executed_rule_hash"],
        "catalog_rule_hash": applied["catalog_rule_hash"],
        "rule_hash_matches_catalog": applied["rule_hash_matches_catalog"],
        "rule_text_sha256": applied["rule_text_sha256"],
        "canonical_checks": canonical_checks, "cohort": cohort,
        "reference_checks": {"total": len(reference_inputs), "cohort_samples": 24,
                             "demos": 4, "canonical_pairs": 4, "query": 1,
                             "coerced_override": 1,
                             "all_independent_probe_outputs_match_reference": True},
        "finding": {
            "classification": "validator-accepted distribution ambiguity",
            "rival": "group_middle_color: leading A run, all non-A, remaining A",
            "construction": "8x8; columns 2,3,4 contain rows 1:A,3:B,5:A; column3 adds row7:B",
            "query": query_record, "query_self_check": query_reasons,
            "demonstrations": demos, "lesson_identifiable": lesson_reasons,
            "generator_label_error_claimed": False,
            "explanation": "The rival fits all canonical pairs and current sampled AB/ABA examples, but fails on the validator-accepted ABAB query. The existing lesson validator accepts this ambiguous four-demo lesson.",
        },
        "override_checks": overrides_checked,
        "limits": [
            "600 sampled grids compared against an independent Python stable-pack probe; 24 cohort samples, four demos, four canonical pairs, the query, and one coerced-override input were executed through Racket.",
            "The new query was hand-constructed, not emitted by the current generator. It is accepted by self_check and lesson_identifiable.",
            "This finding concerns distribution coverage and a finite-rival lesson gate; it does not allege incorrect reference labels for generated inputs or universal lesson identifiability.",
            "The scalar coercion comes from legacy draw_int; strict integer draws are opt-in in shared runtime documentation.",
        ],
    }
    (HERE / "racket.json").write_text(json.dumps(applied, separators=(",", ":")) + "\n")
    (HERE / "finding.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({
        "task_id": TASK_ID, "generator_sha256": source_sha256,
        "executed_rule_hash": applied["executed_rule_hash"],
        "rival_fits_canonical": len(canonical_checks),
        "rival_fits_cohort": sum(row["rival_matches_independent_probe"] for row in cohort.values()),
        "reference_inputs_checked": len(reference_inputs),
        "self_check_accepts_query": query_reasons == [],
        "lesson_identifiable_accepts_ambiguous_lesson": lesson_reasons == [],
        "query_rival_disagrees_with_reference": not query_record["rival_matches_reference"],
        "output": str(HERE / "finding.json"),
    }, indent=2))


if __name__ == "__main__":
    main()
