"""Bounded authoring audit; invokes only public loader/catalog APIs.

Run prepare through review.py run, obtain labels with arcpuzzles apply, then
run analyze. This is an audit rival, never an attempted blind solution.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

from reviewer_support import canonical_pairs, find_root, load_selected_generator
from arcpuzzles import Catalog

TASK = "b81390858ebd"
SEED = 20261023
HERE = Path(__file__).resolve().parent


def digest(value):
    return hashlib.sha256(json.dumps(value, separators=(",", ":")).encode()).hexdigest()


def write(name, value):
    (HERE / name).write_text(json.dumps(value, indent=2) + "\n")


def components(grid):
    height, width = len(grid), len(grid[0])
    seen = set()
    result = []
    for r in range(height):
        for c in range(width):
            if grid[r][c] == 0 or (r, c) in seen:
                continue
            cells, pending = [], [(r, c)]
            seen.add((r, c))
            while pending:
                rr, cc = pending.pop()
                cells.append((rr, cc))
                for nr, nc in ((rr-1, cc), (rr+1, cc), (rr, cc-1), (rr, cc+1)):
                    if (0 <= nr < height and 0 <= nc < width
                            and (nr, nc) not in seen and grid[nr][nc] == grid[r][c]):
                        seen.add((nr, nc))
                        pending.append((nr, nc))
            result.append({"color": grid[r][c], "cells": sorted(cells)})
    ownership = {cell: i for i, obj in enumerate(result) for cell in obj["cells"]}
    for i, obj in enumerate(result):
        neighbors = set()
        for r, c in obj["cells"]:
            for other in ((r-1, c), (r+1, c), (r, c-1), (r, c+1)):
                j = ownership.get(other)
                if j is not None and j != i:
                    neighbors.add(j)
        obj["degree"] = len(neighbors)
        obj["size"] = len(obj["cells"])
        obj["top_left"] = obj["cells"][0]
    return result


def crop(obj):
    cells = set(obj["cells"])
    lo_r, hi_r = min(r for r, _ in cells), max(r for r, _ in cells)
    lo_c, hi_c = min(c for _, c in cells), max(c for _, c in cells)
    return [[8 if (r, c) in cells else 0 for c in range(lo_c, hi_c+1)]
            for r in range(lo_r, hi_r+1)]


def rivals(grid):
    objs = components(grid)
    degree_choice = min(objs, key=lambda o: (-o["degree"], -o["size"], o["top_left"]))
    size_choice = min(objs, key=lambda o: (-o["size"], o["top_left"]))
    return {
        "degree_rule_mirror": crop(degree_choice),
        "largest_component_then_top_left": crop(size_choice),
        "component_summary": [{k: v for k, v in o.items() if k != "cells"} for o in objs],
        "degree_target_unique_largest": (
            len([o for o in objs if o["size"] == max(x["size"] for x in objs)]) == 1
            and degree_choice is size_choice),
    }


def prepare():
    root = find_root(__file__)
    gen, source, sha = load_selected_generator(TASK, root=root)
    info = Catalog(root).get(TASK)
    program = info["variants"][0]["program_solution"]
    cases = []
    for difficulty in (None, "easy", "medium", "hard"):
        for sample_index in range(15):
            grid = gen.generate(SEED, sample_index, difficulty=difficulty)
            cases.append({
                "case_id": f"generated-{difficulty or 'default'}-{sample_index:02d}",
                "kind": "generated", "seed": SEED, "sample_index": sample_index,
                "difficulty": difficulty, "overrides": {}, "input": grid,
                "input_sha256": digest(grid),
                "self_check_errors": gen.self_check(grid, difficulty=difficulty),
                "documented_generator_domain": True, **rivals(grid),
            })
    for pair in canonical_pairs(TASK, root=root, labeled_only=True):
        grid = pair["input"]
        cases.append({
            "case_id": f"canonical-{pair['variant']}-{pair['split']}-{pair['pair_index']}",
            "kind": "canonical", "input": grid,
            "canonical_output": pair["output"], "input_sha256": digest(grid),
            "variant": pair["variant"], "split": pair["split"],
            "pair_index": pair["pair_index"],
            "self_check_errors": gen.self_check(grid), **rivals(grid),
        })
    witness = [[0] * 11 for _ in range(9)]
    for r, c in ((1, 7), (1, 8), (2, 7), (2, 8)):
        witness[r][c] = 7
    for r, c, color in ((4, 4, 3), (4, 6, 4), (5, 4, 2), (5, 5, 2),
                        (5, 6, 2), (6, 5, 6), (7, 1, 9)):
        witness[r][c] = color
    cases.append({
        "case_id": "handmade-larger-isolated-distractor", "kind": "counterexample",
        "seed": None, "sample_index": None, "overrides": None,
        "construction": "Handmade 3-cell degree-3 hub, 3 singleton leaves, 4-cell isolated distractor, 1 isolated singleton.",
        "input": witness, "input_sha256": digest(witness),
        "self_check_errors": gen.self_check(witness),
        "documented_generator_domain": False,
        "canonical_rule_domain": True,
        "domain_reason": "Unique positive highest-degree component; arbitrary same-color 4-connected component sizes are valid for the written/Racket rule. Generator SUMMARY and self_check instead require all non-hub objects to be singletons.",
        **rivals(witness),
    })
    assert len(cases) <= 64
    report = {
        "task_id": TASK, "scope": "final unchanged audit source",
        "source_path": source.relative_to(root).as_posix(), "generator_sha256": sha,
        "rule_hash": info["rule_hash"],
        "rule_program_sha256": hashlib.sha256(program.encode()).hexdigest(),
        "rule_program": program, "written_solution": info["variants"][0]["written_solution"],
        "generator_version": gen.VERSION, "examples_needed": gen.EXAMPLES_NEEDED,
        "declared_canonical_shortcuts": getattr(gen, "CANONICAL_SHORTCUTS", None),
        "declared_lesson_competitors": getattr(gen, "LESSON_COMPETITORS", None),
        "prior_audit": {"return_id": "review-aae0bbad2bb6c284:v0001", "resolution": "needs_triage", "same_source": sha == "8ac5187e5abb962d5eb46dd402f5e4aae6a2348db7323eb30bcd4faea0708c6c"},
        "cases": cases,
    }
    write("prepared.json", report)
    write("inputs.json", [case["input"] for case in cases])
    print(json.dumps({"prepared": len(cases), "generator_sha256": sha,
                      "generated": 60, "canonical": len(cases)-61,
                      "counterexample_validator": cases[-1]["self_check_errors"]}))


def analyze():
    prepared = json.loads((HERE / "prepared.json").read_text())
    actual = json.loads((HERE / "racket.json").read_text())
    print(json.dumps({"racket_result_keys": list(actual)}))
    rows = actual["results"]
    assert len(rows) == len(prepared["cases"])
    assert actual["generator_sha256"] == prepared["generator_sha256"]
    assert actual["executed_rule_hash"] == prepared["rule_hash"]
    # Catalog hashes normalized source; apply.rule_text_sha256 hashes the
    # executable callable wrapper (worker.py:175-176), a different identity.
    normalized = " ".join(prepared["rule_program"].split())
    assert actual["executed_rule_hash"] == hashlib.sha256(normalized.encode()).hexdigest()[:12]
    prepared["executed_callable_sha256"] = actual["rule_text_sha256"]
    for index, (case, row) in enumerate(zip(prepared["cases"], rows)):
        assert row["index"] == index
        assert row["input"] == case["input"]
        assert row["error"] is None and row["valid_output"]
        output = row["output"]
        case["racket_output"] = output
        case["mirror_matches_racket"] = output == case["degree_rule_mirror"]
        case["rival_matches_racket"] = output == case["largest_component_then_top_left"]
    generated = [c for c in prepared["cases"] if c["kind"] == "generated"]
    canonical = [c for c in prepared["cases"] if c["kind"] == "canonical"]
    counterexamples = [c for c in prepared["cases"] if c["kind"] == "counterexample"]
    summary = {
        "generated_count": len(generated),
        "generated_unique_input_count": len({c["input_sha256"] for c in generated}),
        "generated_validator_passed": sum(not c["self_check_errors"] for c in generated),
        "generated_rival_matches_racket": sum(c["rival_matches_racket"] for c in generated),
        "generated_unique_largest_target": sum(c["degree_target_unique_largest"] for c in generated),
        "canonical_labeled_count": len(canonical),
        "canonical_rival_matches_label": sum(c["largest_component_then_top_left"] == c["canonical_output"] for c in canonical),
        "canonical_label_matches_racket": sum(c["racket_output"] == c["canonical_output"] for c in canonical),
        "counterexample_count": len(counterexamples),
        "counterexample_rival_disagrees": sum(not c["rival_matches_racket"] for c in counterexamples),
        "mirror_matches_racket": sum(c["mirror_matches_racket"] for c in prepared["cases"]),
        "racket_count": len(rows),
        "lesson_production_verdict": "unknown_not_run",
        "lesson_query_rotation_verdict": "unknown_not_run",
        "lesson_count_tested": 0,
        "lesson_structural_inference": "Any lesson composed only of accepted generator draws cannot refute the largest-component rival, regardless of demonstration ordering or query position.",
        "scope_limit": "15 indices 0..14 at seed 20261023 per default/easy/medium/hard; no full battery, stage, or lesson census. Whole-support shortcut argument follows sampler and validator structure, not extrapolated counts.",
    }
    prepared["summary"] = summary
    prepared["racket_evidence"] = "checks/audit/b81390858ebd/racket.json"
    write("report.json", prepared)
    print(json.dumps(summary, indent=2))
    assert summary["generated_validator_passed"] == 60
    assert summary["generated_rival_matches_racket"] == 60
    assert summary["canonical_rival_matches_label"] == len(canonical)
    assert summary["canonical_label_matches_racket"] == len(canonical)
    assert summary["counterexample_rival_disagrees"] == 1
    assert summary["mirror_matches_racket"] == len(rows)


if __name__ == "__main__":
    {"prepare": prepare, "analyze": analyze}[sys.argv[1]]()
