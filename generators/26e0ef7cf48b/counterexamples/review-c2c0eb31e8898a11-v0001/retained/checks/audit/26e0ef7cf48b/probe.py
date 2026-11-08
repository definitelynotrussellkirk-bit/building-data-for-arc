#!/usr/bin/env python3
"""Focused source-mask rival probe; all reported authority labels come from public apply."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

TASK = "26e0ef7cf48b"
HERE = Path(__file__).resolve().parent
WORK = HERE.parents[2]
REPO = WORK / "repo"
SOURCE = REPO / "generators" / TASK / "generator.py"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def module():
    sys.path.insert(0, str(REPO / "shared/runtime"))
    spec = importlib.util.spec_from_file_location("audited_stamp_generator", SOURCE)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def canonical():
    path = REPO / "shared/data/canonical/puzzles.jsonl"
    for line in path.open():
        row = json.loads(line)
        if row.get("task_id") == TASK:
            test = row["test"]
            return row, list(row["train"]) + ([test] if isinstance(test, dict) else list(test))
    raise RuntimeError("canonical task absent")


def stamp(grid, *, source_is_obstacle):
    """Standalone spatial rule. The rival also excludes original red source cells."""
    red = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 2]
    r0 = min(r for r, _ in red)
    c0 = min(c for _, c in red)
    offsets = [(r - r0, c - c0) for r, c in red]
    h, w = len(grid), len(grid[0])
    out = [[0] * w for _ in range(h)]
    obstacles = {2, 9} if source_is_obstacle else {9}
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value in (3, 4):
                for dr, dc in offsets:
                    rr, cc = r + dr, c + dc
                    if 0 <= rr < h and 0 <= cc < w and grid[rr][cc] not in obstacles:
                        out[rr][cc] = 8
    return out


def write_json(name, value):
    (HERE / name).write_text(json.dumps(value, indent=2) + "\n")


def select():
    gen = module()
    row, pairs = canonical()
    canonical_fit = [stamp(p["input"], source_is_obstacle=True) == p["output"] for p in pairs]
    if not all(canonical_fit):
        raise AssertionError(f"rival does not fit canonical pairs: {canonical_fit}")
    explored = []
    selected = None
    for seed in range(32):
        grids = [gen.generate(seed, index, difficulty="easy") for index in range(4)]
        self_checks = [gen.self_check(g, difficulty="easy", meta={"overrides": {}}) for g in grids]
        assert not any(self_checks), self_checks
        fits = [stamp(g, source_is_obstacle=True) == stamp(g, source_is_obstacle=False) for g in grids]
        explored.append({"seed": seed, "difficulty": "easy", "sample_indices": [0, 1, 2, 3],
                         "python_reference_rival_fits": fits})
        if fits == [True, True, True, False]:
            selected = (seed, grids, self_checks)
            break
    assert selected is not None, "No bounded witness found in seeds 0..31"
    seed, grids, self_checks = selected
    records = []
    for index, pair in enumerate(pairs):
        records.append({"kind": "canonical", "canonical_pair_index": index,
                        "role": "demonstration" if index < len(row["train"]) else "query-verification",
                        "input": pair["input"], "canonical_expected_output": pair["output"],
                        "self_check": gen.self_check(pair["input"]), "documented_domain": True})
    for index, grid in enumerate(grids):
        records.append({"kind": "generated", "seed": seed, "sample_index": index,
                        "difficulty": "easy", "overrides": {},
                        "role": "demonstration" if index < 3 else "query",
                        "input": grid, "self_check": self_checks[index],
                        "documented_domain": True, "semantic_signature": gen.semantic_signature(grid),
                        "observed_exact_axes": gen.observe_overrides(grid)})
    rule = row["program_solution"]
    selection = {
        "task_id": TASK, "generator_version": gen.VERSION, "generator_sha256": digest(SOURCE),
        "rule_text_sha256": hashlib.sha256(rule.encode()).hexdigest(),
        "normalized_rule_sha256": hashlib.sha256(" ".join(rule.split()).encode()).hexdigest(),
        "declared_rule_hash": gen.RULE_HASH,
        "review_index_present": (SOURCE.parent / "evidence/review_index.json").exists(),
        "source_paths": [str(SOURCE.relative_to(WORK))],
        "rival": "Stamp the normalized red template at every 3/4 marker in cyan, clipping to the canvas; treat both original red (2) source cells and maroon (9) wall cells as forbidden stamp destinations.",
        "rival_intent": "intentional teaching negative / adversarial ambiguity probe",
        "exploration_label_authority": "Standalone Python calculation only; not a Racket result",
        "exploration": explored,
        "canonical_shortcuts_declaration": getattr(gen, "CANONICAL_SHORTCUTS", None),
        "lesson_competitors_declaration": getattr(gen, "LESSON_COMPETITORS", None),
        "canonical_fit_python": canonical_fit,
        "records": records,
    }
    write_json("selection.json", selection)
    write_json("input.json", [r["input"] for r in records])
    print(json.dumps({"selected_seed": seed, "difficulty": "easy", "sample_indices": [0, 1, 2, 3],
                      "python_only_explored_lessons": len(explored), "inputs_for_public_apply": len(records)}))


def verify():
    selection = json.loads((HERE / "selection.json").read_text())
    applied = json.loads((HERE / "racket.json").read_text())
    assert selection["generator_sha256"] == digest(SOURCE) == applied["generator_sha256"]
    # Public apply's rule_text_sha256 hashes rule_callable_text, not rule_source.
    current_canonical, _ = canonical()
    assert selection["rule_text_sha256"] == hashlib.sha256(current_canonical["program_solution"].encode()).hexdigest()
    assert selection["normalized_rule_sha256"][:12] == applied["executed_rule_hash"]
    assert applied["rule_hash_matches_catalog"]
    records = []
    for meta, result in zip(selection["records"], applied["results"], strict=True):
        assert meta["input"] == result["input"]
        assert result["output"] is not None, result
        assert result["valid_output"] is True and result["error"] is None, result
        assert result["generator_domain"] == {"status": "valid", "errors": []}, result
        rival = stamp(meta["input"], source_is_obstacle=True)
        actual = result["output"]
        assert stamp(meta["input"], source_is_obstacle=False) == actual
        diffs = [{"row": r, "col": c, "input_color": meta["input"][r][c],
                  "racket": actual[r][c], "rival": rival[r][c]}
                 for r in range(len(actual)) for c in range(len(actual[0])) if actual[r][c] != rival[r][c]]
        if "canonical_expected_output" in meta:
            assert actual == meta["canonical_expected_output"]
        records.append({**meta, "actual_racket_output": actual, "rival_output": rival,
                        "rival_matches_racket": not diffs, "differences": diffs,
                        "public_apply_domain_check": result.get("generator_domain")})
    assert [r["rival_matches_racket"] for r in records] == [True] * 6 + [False]
    report = {k: v for k, v in selection.items() if k != "records"}
    report["canonical_rule_source_sha256"] = report.pop("rule_text_sha256")
    report["public_apply_callable_sha256"] = applied["rule_text_sha256"]
    report.update({"status": "reproduced_lesson_ambiguity", "phase": "final_unchanged_audit_source",
                   "finding_id": "A26-1", "authority": "public arcpuzzles apply; canonical reference",
                   "executed_rule_hash": applied["executed_rule_hash"],
                   "canonical_fit_count": 3, "canonical_pair_count": 3,
                   "generated_demonstration_fit_count": 3, "generated_demonstration_count": 3,
                   "generated_query_disagreements": 1, "generated_query_count": 1,
                   "generated_unique_inputs": 4,
                   "production_lesson_policy": "seed fixed; sample_index 0,1,2 are demonstrations; 3 is query",
                   "production_identifiability_verdict": "fails_against_declared_source_mask_rival",
                   "query_rotation_verdict": "unknown_not_tested",
                   "limitations": ["Focused witness search, not a full battery or incidence estimate.",
                                   "No claimed mismatch between the selected Racket rule and valid generated-domain semantics.",
                                   "Rival is intentionally authored, not an observed failed blind solve.",
                                   "No generator, rule, catalog, or task-local existing file was modified."],
                   "records": records})
    write_json("evidence.json", report)
    print(json.dumps({"status": report["status"], "source_sha256": report["generator_sha256"],
                      "canonical_fit": "3/3", "generated_demonstration_fit": "3/3", "query_diff": records[-1]["differences"]}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("select", "verify"))
    args = parser.parse_args()
    {"select": select, "verify": verify}[args.mode]()
