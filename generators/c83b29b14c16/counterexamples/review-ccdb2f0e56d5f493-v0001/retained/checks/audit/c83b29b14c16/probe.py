#!/usr/bin/env python3
"""Bounded findings-only c83b audit; run via review.py run (no private runner).

prepare writes <=64 inputs for public arcpuzzles apply. verify consumes its
actual Racket receipt. All writes remain beside this script.
"""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import itertools
import json
from pathlib import Path
import sys

ID = "c83b29b14c16"
OUT = Path(__file__).resolve().parent


def dump(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def cells_by_color(grid):
    groups = {}
    for r, row in enumerate(grid):
        for c, color in enumerate(row):
            if color:
                groups.setdefault(color, []).append((r, c))
    return groups


def oblique_bbox_rival(grid):
    """Wrong: reject only exact 45-degree diagonal pairs, otherwise fill bbox."""
    out = [row[:] for row in grid]
    for color, cells in cells_by_color(grid).items():
        if len(cells) != 2:
            continue
        (r0, c0), (r1, c1) = cells
        if abs(r1 - r0) == abs(c1 - c0):
            continue
        for r in range(min(r0, r1), max(r0, r1) + 1):
            for c in range(min(c0, c1), max(c0, c1) + 1):
                out[r][c] = color
    return out


def even_distance_rival(grid):
    """Already recorded restriction: connect only even endpoint distances."""
    out = [row[:] for row in grid]
    for color, cells in cells_by_color(grid).items():
        if len(cells) != 2:
            continue
        (r0, c0), (r1, c1) = cells
        if r0 != r1 and c0 != c1:
            continue
        if (abs(r1-r0) + abs(c1-c0)) % 2:
            continue
        for r in range(min(r0, r1), max(r0, r1) + 1):
            for c in range(min(c0, c1), max(c0, c1) + 1):
                out[r][c] = color
    return out


def prepare(g, source, sha, root, canonical_pairs):
    canon = canonical_pairs(ID, root=root, labeled_only=True)
    declared = {"CANONICAL_SHORTCUTS": g.CANONICAL_SHORTCUTS,
                "LESSON_COMPETITORS": g.LESSON_COMPETITORS}
    canonical_results = {
        group: {name: {"matches": sum(fn(p["input"]) == p["output"] for p in canon),
                       "total": len(canon)} for name, fn in rivals.items()}
        for group, rivals in declared.items()
    }
    canonical_results["additional_audit_rivals"] = {
        name: {"matches": sum(fn(p["input"]) == p["output"] for p in canon), "total": len(canon)}
        for name, fn in [("oblique_bbox_rival", oblique_bbox_rival), ("even_distance_rival", even_distance_rival)]
    }
    samples = []
    distances, diagonals, errs = Counter(), Counter(), []
    cache = {}
    for band in ("easy", "medium", "hard"):
        for seed in range(761980, 761990):
            for si in range(8):
                grid = g.generate(seed, si, difficulty=band)
                truth = g.rule_mirror(grid)
                e = g.self_check(grid)
                if e:
                    errs.append({"seed": seed, "sample_index": si, "difficulty": band, "errors": e})
                row = {"seed": seed, "sample_index": si, "difficulty": band,
                       "overrides": {}, "input": grid, "output": truth}
                samples.append(row)
                cache[(band, seed, si)] = row
                for cells in cells_by_color(grid).values():
                    if len(cells) == 2:
                        (r0, c0), (r1, c1) = cells
                        dr, dc = abs(r0-r1), abs(c0-c1)
                        if not dr or not dc:
                            distances[str(dr+dc)] += 1
                        else:
                            diagonals[f"{dr},{dc}"] += 1
    exact_failures = []
    override_count = 0
    for band in ("easy", "medium", "hard"):
        for vals in itertools.product((7, 10), (7, 10), (2, 3), (0, 1), (0, 1), (0, 1), (0, 1)):
            ov = dict(zip(g.AXES, vals))
            grid = g.generate(762001, 0, difficulty=band, **ov)
            observed = g.observe_overrides(grid)
            override_count += 1
            if observed != ov or g.self_check(grid, meta={"overrides": ov}):
                exact_failures.append({"difficulty": band, "overrides": ov, "observed": observed})
    lessons = {"production_total": 0, "production_failures": [],
               "rotation_total": 0, "rotation_failures": []}
    for band in ("easy", "medium", "hard"):
        for seed in range(761980, 761990):
            for start in range(4):
                pairs = [cache[(band, seed, si)] for si in range(start, start+5)]
                lesson_errors = g.lesson_identifiable(pairs[:4], pairs[4])
                lessons["production_total"] += 1
                if lesson_errors:
                    lessons["production_failures"].append({"difficulty": band, "seed": seed, "start": start, "errors": lesson_errors})
                for query in range(5):
                    lessons["rotation_total"] += 1
                    e = g.lesson_identifiable([p for i, p in enumerate(pairs) if i != query], pairs[query])
                    if e:
                        lessons["rotation_failures"].append({"difficulty": band, "seed": seed, "start": start, "query_position": query, "errors": e})
    apply_rows = []
    for p in canon:
        apply_rows.append({"kind": "canonical", **p, "self_check_errors": g.self_check(p["input"])})
    for band in ("easy", "medium", "hard"):
        for si in range(16):
            grid = g.generate(761980, si, difficulty=band)
            apply_rows.append({"kind": "generated", "seed": 761980, "sample_index": si,
                               "difficulty": band, "overrides": {}, "input": grid,
                               "self_check_errors": g.self_check(grid)})
    max_ov = {"grid_h": 7, "grid_w": 7, "n_pairs": 3, "n_singletons": 1,
              "n_diagonal_pairs": 1, "n_triples": 1, "n_short_pairs": 1}
    for band in ("easy", "medium", "hard"):
        grid = g.generate(762001, 0, difficulty=band, **max_ov)
        apply_rows.append({"kind": "generated_override", "seed": 762001, "sample_index": 0,
                           "difficulty": band, "overrides": max_ov, "input": grid,
                           "self_check_errors": g.self_check(grid, meta={"overrides": max_ov})})
    for endpoint in ((4, 3), (6, 3)):
        grid = [[0] * 7 for _ in range(7)]
        for color, cells in {1: [(0, 0), (0, 2)], 2: [(0, 6), (4, 6)], 3: [(3, 1), endpoint]}.items():
            for r, c in cells:
                grid[r][c] = color
        apply_rows.append({"kind": "authored_oblique_witness", "construction": "minimum 7x7 canvas and minimum 6 markers satisfying 2 active pairs plus diagonal control",
                           "seed": None, "sample_index": None, "difficulty": None, "overrides": None,
                           "input": grid, "self_check_errors": g.self_check(grid),
                           "observed_axes": g.observe_overrides(grid)})
    dump("input.json", [p["input"] for p in apply_rows])
    dump("case_manifest.json", apply_rows)
    summary = {"task_id": ID, "generator_source": str(source.relative_to(root)),
               "generator_sha256": sha, "version": g.VERSION, "declared_rule_hash": g.RULE_HASH,
               "canonical_results": canonical_results,
               "python_mirror_census": {"seed_start": 761980, "seed_end_inclusive": 761989,
                 "sample_index_start": 0, "sample_index_end_inclusive": 7,
                 "difficulties": ["easy", "medium", "hard"], "overrides": {},
                 "inputs": len(samples), "unique_inputs": len({json.dumps(p["input"]) for p in samples}),
                 "validator_errors": errs, "active_distance_histogram": distances,
                 "diagonal_abs_delta_histogram": diagonals,
                 "new_rival_agreements": sum(oblique_bbox_rival(p["input"]) == p["output"] for p in samples),
                 "known_parity_rival_agreements": sum(even_distance_rival(p["input"]) == p["output"] for p in samples)},
               "override_probe": {"seed": 762001, "sample_index": 0,
                 "axis_values_in_iteration_order": {k: list(v) for k, v in zip(g.AXES, ((7,10),(7,10),(2,3),(0,1),(0,1),(0,1),(0,1)))},
                 "difficulties": ["easy", "medium", "hard"], "total": override_count,
                 "failures": exact_failures}, "python_mirror_lesson_diagnostic": lessons,
               "lesson_policy": {"demonstrations": 4, "query_position": 4, "sample_starts": [0,1,2,3],
                 "rotated_query_positions": [0,1,2,3,4], "pair_appearances_production": 600,
                 "unique_sample_draws_in_all_windows": len(samples), "label_scope": "Python mirror only; supported apply separately labels 58 selected cases"},
               "apply_inputs": len(apply_rows)}
    dump("prepare_report.json", summary)
    print(json.dumps({"prepared": len(apply_rows), "census": len(samples), "override_draws": override_count,
                      "production_failures": len(lessons["production_failures"]),
                      "rotation_failures": len(lessons["rotation_failures"])}))


def verify(g, source, sha, root, canonical_pairs):
    receipt = json.loads((OUT / "racket.json").read_text())
    cases = json.loads((OUT / "case_manifest.json").read_text())
    prepared = json.loads((OUT / "prepare_report.json").read_text())
    assert receipt["generator_sha256"] == sha == prepared["generator_sha256"]
    assert receipt["executed_rule_hash"] == g.RULE_HASH
    results = receipt["results"]
    assert len(results) == len(cases) == 58
    counts, failures = {}, []
    for case, result in zip(cases, results):
        assert result["input"] == case["input"]
        assert result["valid_output"] and not result["error"]
        kind = case["kind"]
        cnt = counts.setdefault(kind, {"total": 0, "validator_accepted": 0,
                    "python_mirror_matches": 0, "oblique_bbox_rival_matches": 0,
                    "even_distance_rival_matches": 0})
        cnt["total"] += 1
        cnt["validator_accepted"] += not g.self_check(case["input"])
        cnt["python_mirror_matches"] += g.rule_mirror(case["input"]) == result["output"]
        cnt["oblique_bbox_rival_matches"] += oblique_bbox_rival(case["input"]) == result["output"]
        cnt["even_distance_rival_matches"] += even_distance_rival(case["input"]) == result["output"]
        if "output" in case:
            assert case["output"] == result["output"]
    binding = {k: receipt[k] for k in ("task_id", "generator_sha256", "executed_rule_hash",
                "catalog_rule_hash", "rule_text_sha256", "rule_hash_matches_catalog")}
    command = {"cwd": "..", "argv": ["python3", "review.py", "run", "python3", "-m", "arcpuzzles", "apply", ID,
                   "--input", "../checks/audit/" + ID + "/input.json", "--out", "../checks/audit/" + ID + "/racket.json"],
               "environment": {"PYTHONDONTWRITEBYTECODE": "1", "TMPDIR": "/dev/shm/arcpuzzles-review-ccdb-tmp"},
               "payload_cwd": "repo", "exit_code": 0,
               "evidence_paths": ["checks/audit/" + ID + "/input.json", "checks/audit/" + ID + "/racket.json"]}
    demo_rows = [{**cases[i], "output": results[i]["output"]} for i in range(5, 9)]
    for wi, i in enumerate((56, 57)):
        case, result = cases[i], results[i]
        rival = oblique_bbox_rival(case["input"])
        assert rival != result["output"] and case["self_check_errors"] == []
        assert all(oblique_bbox_rival(p["input"]) == p["output"] for p in demo_rows)
        named_errors = g.lesson_identifiable(demo_rows, {"input": case["input"]})
        assert named_errors == []
        witness = {**binding, "finding": "45-degree-only rejection shortcut survives sampler and all canonicals",
                   "case_index_in_apply": i, "case": case, "actual_racket_output": result["output"],
                   "input_sha256": result["input_sha256"], "output_sha256": result["output_sha256"],
                   "rival": "oblique_bbox_rival", "rival_output": rival,
                   "rival_disagreement_cells": [[r, c] for r, row in enumerate(rival) for c, v in enumerate(row)
                                                if v != result["output"][r][c]],
                   "domain": "accepted by self_check and documented grammar; outside current sampler support because diagonal |dr| != |dc|",
                   "minimality": "7x7 is validator minimum; two active pairs plus diagonal control require at least six markers; not a general optimization proof",
                   "label_command": command,
                   "four_demo_lesson": {"demos": demo_rows, "query_input": case["input"],
                     "query_output": result["output"], "named_lesson_identifiable_errors": named_errors,
                     "audit_rival_fits_all_demos": True, "audit_rival_changes_query": True}}
        dump(f"oblique_witness_{wi + 1}.json", witness)
    production, rotations = [], []
    for band in ("easy", "medium", "hard"):
        for start in range(4):
            indices = [i for i, c in enumerate(cases) if c["kind"] == "generated" and c["difficulty"] == band
                       and start <= c["sample_index"] <= start+4]
            pairs = [{**cases[i], "output": results[i]["output"]} for i in indices]
            production.append(g.lesson_identifiable(pairs[:4], pairs[4]))
            for qi in range(5):
                demos = [p for i, p in enumerate(pairs) if i != qi]
                errors = g.lesson_identifiable(demos, pairs[qi])
                rotations.append(errors)
                if errors and not (OUT / "rotation_witness.json").exists():
                    dump("rotation_witness.json", {**binding, "classification": "ordered-curriculum limitation; query rotation diagnostic",
                         "seed": 761980, "sample_start": start, "difficulty": band, "query_position": qi,
                         "demonstrations": demos, "query": pairs[qi], "lesson_identifiable_errors": errors,
                         "label_command": command})
    report = {**binding, "racket_counts": counts, "racket_total": len(results),
              "racket_unique_inputs": len({json.dumps(r["input"]) for r in results}),
              "racket_lesson_diagnostic": {"seed": 761980, "difficulties": ["easy", "medium", "hard"],
                "sample_starts": [0, 1, 2, 3], "demonstrations": 4,
                "production": {"total": len(production), "passed": sum(not x for x in production)},
                "rotations": {"total": len(rotations), "passed": sum(not x for x in rotations)}},
              "evidence_scope": "One exact generator source. Public Racket labels 58 cases. Larger 240-draw/384-override checks and 120 lesson windows use Python mirror; counts are kept separate.",
              "raw_source_unchanged": hashlib.sha256(source.read_bytes()).hexdigest() == sha}
    dump("audit_report.json", report)
    commands = []
    for phase, evidence in [("prepare", ["probe.py", "prepare_report.json", "case_manifest.json", "input.json"]),
                            ("verify", ["probe.py", "audit_report.json", "oblique_witness_1.json", "oblique_witness_2.json", "rotation_witness.json"])]:
        row = {"cwd": "..", "argv": ["python3", "review.py", "run", "python3", "../checks/audit/" + ID + "/probe.py", phase],
               "environment": command["environment"], "payload_cwd": "repo", "exit_code": 0,
               "evidence_paths": ["checks/audit/" + ID + "/" + p for p in evidence]}
        commands.append(row)
    commands.insert(1, command)
    dump("commands.json", {"verification_commands": commands})
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("phase", choices=("prepare", "verify"))
    ap.add_argument("--root", type=Path, default=Path.cwd())
    args = ap.parse_args()
    for helper in (args.root / "shared/runtime", args.root):
        if (helper / "reviewer_support.py").is_file():
            sys.path.insert(0, str(helper.resolve()))
            break
    from reviewer_support import canonical_pairs, find_root, load_selected_generator
    root = find_root(args.root)
    g, source, sha = load_selected_generator(ID, root=root)
    {"prepare": prepare, "verify": verify}[args.phase](g, source, sha, root, canonical_pairs)
