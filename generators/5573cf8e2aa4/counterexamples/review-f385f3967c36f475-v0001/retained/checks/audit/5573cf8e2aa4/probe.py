#!/usr/bin/env python3
"""Findings-only column-span rival probe; obtain labels with public apply CLI."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

TASK_ID = "5573cf8e2aa4"
OUT = Path(__file__).resolve().parent


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(name, data):
    (OUT / name).write_text(json.dumps(data, separators=(",", ":")) + "\n")


def load_generator(repo):
    sys.path.insert(0, str(repo / "shared/runtime"))
    from reviewer_support import canonical_pairs, canonical_path, find_root

    root = find_root(repo)
    source = root / "generators" / TASK_ID / "generator.py"
    spec = importlib.util.spec_from_file_location("audited_generator", source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    pairs = canonical_pairs(TASK_ID, root=root, labeled_only=True)
    canonical_rows = [
        json.loads(line)
        for line in canonical_path(root).read_text().splitlines()
        if json.loads(line).get("task_id") == TASK_ID
    ]
    assert len(canonical_rows) == 1
    rule = canonical_rows[0]["program_solution"]
    return module, pairs, {
        "generator_path": f"repo/generators/{TASK_ID}/generator.py",
        "generator_sha256": sha256(source),
        "rule_sha256_utf8": hashlib.sha256(rule.encode()).hexdigest(),
        "declared_rule_hash": module.RULE_HASH,
    }


def column_span_rival(grid):
    """Paint each column from its first to last occupied panel coordinate."""
    h, w = len(grid), (len(grid[0]) - 1) // 2
    out = [[0] * w for _ in range(h)]
    for c in range(w):
        occupied_rows = [
            r for r in range(h) if grid[r][c] != 0 or grid[r][w + 1 + c] != 0
        ]
        if occupied_rows:
            for r in range(min(occupied_rows), max(occupied_rows) + 1):
                out[r][c] = 8
    return out


def ring_input():
    """Two monochrome connected arcs whose sparse union is an eight-cell ring."""
    ring = [(1, 1), (1, 2), (1, 3), (2, 3), (3, 3), (3, 2), (3, 1), (2, 1)]
    grid = [[0] * 11 for _ in range(5)]
    for row in grid:
        row[5] = 9
    for r, c in ring[:5]:
        grid[r][c] = 3
    for r, c in ring[3:]:
        grid[r][6 + c] = 3
    return grid


def make_cases(gen, canonical):
    cases = []
    for pair in canonical:
        cases.append({
            "kind": "canonical", "variant": pair["variant"],
            "split": pair["split"], "pair_index": pair["pair_index"],
            "input": pair["input"], "canonical_output": pair["output"],
            "seed": None, "sample_index": None, "difficulty": None,
            "overrides": {}, "documented_generator_domain": True,
            "construction_reachable": "canonical authoring input, not asserted generated",
        })
    for seed in (0, 1, 23):
        for difficulty in ("easy", "medium", "hard"):
            for sample_index in range(4):
                cases.append({
                    "kind": "default_generated", "seed": seed,
                    "sample_index": sample_index, "difficulty": difficulty,
                    "overrides": {}, "documented_generator_domain": True,
                    "construction_reachable": True,
                    "input": gen.generate(seed, sample_index, difficulty=difficulty),
                })
    for palette_size in (1, 2):
        for profile in gen.RELATION_PROFILES:
            overrides = {
                "grid_h": 5, "half_w": 5, "palette_size": palette_size,
                "relation_profile": profile,
            }
            cases.append({
                "kind": "override_generated", "seed": 23,
                "sample_index": 5, "difficulty": "medium", "overrides": overrides,
                "documented_generator_domain": True, "construction_reachable": True,
                "input": gen.generate(23, 5, difficulty="medium", **overrides),
            })
    cases.append({
        "kind": "hand_constructed_counterexample", "seed": None,
        "sample_index": None, "difficulty": None,
        "overrides": {"grid_h": 5, "half_w": 5, "palette_size": 1, "relation_profile": "sparse"},
        "input": ring_input(),
        "documented_generator_domain": "satisfies declared AXES and INVARIANTS; both panels are connected paths",
        "construction_reachable": False,
        "domain_caveat": "Union is not a contiguous interval of _snake_cells. Notes explicitly acknowledge restricted path-like support geometry; this is a coverage/teaching shortcut, not a generated-label mismatch.",
    })
    for index, case in enumerate(cases):
        case["input_index"] = index
        case["self_check_errors"] = gen.self_check(case["input"], meta={"overrides": case["overrides"]})
        case["observed_overrides"] = gen.observe_overrides(case["input"])
        case["relation_counts"] = gen.relation_counts(case["input"])
    return cases


def prepare(repo):
    gen, canonical, identity = load_generator(repo)
    cases = make_cases(gen, canonical)
    write_json("input.json", [case["input"] for case in cases])
    write_json("prepared.json", {"task_id": TASK_ID, **identity, "cases": cases})
    print(json.dumps({"input_count": len(cases), **identity}))


def verify(repo):
    gen, canonical, identity = load_generator(repo)
    prepared = json.loads((OUT / "prepared.json").read_text())
    racket = json.loads((OUT / "racket.json").read_text())
    assert identity["generator_sha256"] == prepared["generator_sha256"] == racket["generator_sha256"]
    assert identity["rule_sha256_utf8"] == prepared["rule_sha256_utf8"]
    assert identity["declared_rule_hash"] == racket["executed_rule_hash"]
    cases = prepared["cases"]
    results = racket["results"]
    assert len(cases) == len(results) == 46
    comparisons = []
    for case, result in zip(cases, results):
        assert case["input_index"] == result["index"]
        assert case["input"] == result["input"]
        assert result["error"] is None and result["valid_output"]
        assert not case["self_check_errors"]
        intended = result["output"]
        assert gen.rule_mirror(case["input"]) == intended
        if case["kind"] == "canonical":
            assert case["canonical_output"] == intended
        rival = column_span_rival(case["input"])
        comparisons.append({
            "input_index": case["input_index"], "kind": case["kind"],
            "column_span_rival_matches": rival == intended,
            "mismatch_cells": [
                {"row": r, "column": c, "racket": expected, "rival": rival[r][c]}
                for r, row in enumerate(intended) for c, expected in enumerate(row)
                if rival[r][c] != expected
            ],
        })
    canonical_results = [results[case["input_index"]] for case in cases if case["kind"] == "canonical"]
    declarations = {}
    for name in ("CANONICAL_SHORTCUTS", "LESSON_COMPETITORS"):
        declarations[name] = {
            rival_name: {
                "matches_by_canonical_input_index": [
                    fn(result["input"]) == result["output"] for result in canonical_results
                ],
                "fits_all_canonical_pairs": all(
                    fn(result["input"]) == result["output"] for result in canonical_results
                ),
            }
            for rival_name, fn in getattr(gen, name).items()
        }
    generated = [case for case in cases if case["kind"] in ("default_generated", "override_generated")]
    windows = []
    for seed in (0, 1, 23):
        for difficulty in ("easy", "medium", "hard"):
            group = [case for case in cases if case["kind"] == "default_generated"
                     and case["seed"] == seed and case["difficulty"] == difficulty]
            pairs = [results[case["input_index"]] for case in group]
            rotations = []
            for query_index in range(4):
                demos = [pair for i, pair in enumerate(pairs) if i != query_index]
                query = pairs[query_index]
                rotations.append({
                    "query_sample_index": query_index,
                    "declared_competitor_reasons": gen.lesson_identifiable(demos, query),
                    "column_span_fits_all_demos": all(
                        column_span_rival(pair["input"]) == pair["output"] for pair in demos
                    ),
                    "column_span_fits_query": column_span_rival(query["input"]) == query["output"],
                })
            windows.append({"seed": seed, "difficulty": difficulty,
                            "sample_indices": [0, 1, 2, 3], "production_query_index": 3,
                            "demonstration_count": 3, "rotations": rotations})
    ring = cases[-1]
    evidence = {
        "task_id": TASK_ID, **identity,
        "executed_rule_text_sha256": racket["rule_text_sha256"],
        "racket_output_evidence": "checks/audit/5573cf8e2aa4/racket.json",
        "racket_input_index": ring["input_index"], **ring,
        "actual_racket_output": results[-1]["output"],
        "rival_name": "fill_each_occupied_column_span", "rival_output": column_span_rival(ring["input"]),
        "mismatch_cells": comparisons[-1]["mismatch_cells"],
        "command": ["python3", "run_with_racket.py", "python3", "-m", "arcpuzzles", "apply", TASK_ID,
                    "--input", "../checks/audit/5573cf8e2aa4/input.json", "--out", "../checks/audit/5573cf8e2aa4/racket.json"],
        "command_cwd": "packet_root", "effective_cwd": racket["cwd"], "exit_code": 0,
    }
    write_json("counterexample.json", evidence)
    summary = {
        "racket_cases": len(cases), "valid_racket_outputs": len(results),
        "self_check_accepted": sum(not case["self_check_errors"] for case in cases),
        "canonical_pairs": len(canonical_results),
        "canonical_column_span_matches": sum(row["column_span_rival_matches"] for row in comparisons if row["kind"] == "canonical"),
        "default_draws": 36, "override_draws": 6,
        "generated_unique_inputs": len({json.dumps(case["input"]) for case in generated}),
        "generated_column_span_matches": sum(row["column_span_rival_matches"] for row in comparisons if row["kind"] in ("default_generated", "override_generated")),
        "ring_mismatch_cells": len(comparisons[-1]["mismatch_cells"]),
        "production_windows": len(windows), "query_rotations": sum(len(window["rotations"]) for window in windows),
        "column_span_survives_production_windows": sum(window["rotations"][3]["column_span_fits_all_demos"] for window in windows),
        "column_span_survives_rotations": sum(rotation["column_span_fits_all_demos"] for window in windows for rotation in window["rotations"]),
    }
    assert summary["canonical_column_span_matches"] == 3
    assert summary["generated_column_span_matches"] == 42
    assert summary["ring_mismatch_cells"] == 1
    report = {"task_id": TASK_ID, **identity, "executed_rule_text_sha256": racket["rule_text_sha256"],
              "summary": summary, "comparisons": comparisons, "canonical_declarations": declarations,
              "lessons": windows, "findings_only": True, "source_changed": False}
    write_json("report.json", report)
    print(json.dumps(summary))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("prepare", "verify"))
    parser.add_argument("--repo", type=Path, default=Path("repo"))
    args = parser.parse_args()
    {"prepare": prepare, "verify": verify}[args.mode](args.repo.resolve())


if __name__ == "__main__":
    main()
