"""Read-only, public-reference audit of task f395ecd79f92.

This is an intentional rival probe, not a solver attempt. Source files are
never edited, and actual reference outputs are obtained separately through
the supported arcpuzzles apply command.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
AUDIT_DIR = Path(__file__).resolve().parent
PACKET_ROOT = AUDIT_DIR.parents[2]
REPO = PACKET_ROOT / "repo"
TASK_ID = "f395ecd79f92"
sys.path.insert(0, str(REPO / "shared" / "runtime"))
GENERATOR_PATH = REPO / "generators" / TASK_ID / "generator.py"
spec = importlib.util.spec_from_file_location("audited_f395ecd79f92", GENERATOR_PATH)
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def digest(value):
    return hashlib.sha256(json.dumps(value, separators=(",", ":"), sort_keys=True).encode()).hexdigest()


def write(name, value):
    (AUDIT_DIR / name).write_text(json.dumps(value, indent=2) + "\n")


def components(grid):
    """Independent same-color, four-connected, row-major components."""
    unseen = {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v != 0}
    out = []
    while unseen:
        first = min(unseen)
        color = grid[first[0]][first[1]]
        unseen.remove(first)
        cells = {first}
        stack = [first]
        while stack:
            r, c = stack.pop()
            for p in ((r-1, c), (r+1, c), (r, c-1), (r, c+1)):
                if p in unseen and grid[p[0]][p[1]] == color:
                    unseen.remove(p)
                    cells.add(p)
                    stack.append(p)
        r0 = min(r for r, c in cells)
        r1 = max(r for r, c in cells)
        c0 = min(c for r, c in cells)
        c1 = max(c for r, c in cells)
        out.append({"color": color, "cells": sorted(cells), "first": first,
                    "area": len(cells), "bbox": [r0, c0, r1, c1],
                    "bbox_area": (r1-r0+1)*(c1-c0+1)})
    return out


def rival(grid):
    """Wrong rule: keep median bounding-box area, ties by reading order."""
    comps = components(grid)
    selected = sorted(comps, key=lambda item: (item["bbox_area"], item["first"]))[len(comps)//2]
    out = [[0] * len(grid[0]) for _ in grid]
    for r, c in selected["cells"]:
        out[r][c] = selected["color"]
    return out


def load_canonical():
    with (REPO / "shared" / "data" / "canonical" / "puzzles.jsonl").open() as stream:
        for line in stream:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise AssertionError("assigned canonical row missing")


def prepare():
    canonical = load_canonical()
    pairs = canonical["train"] + canonical["test"]
    generator_sha = hashlib.sha256(GENERATOR_PATH.read_bytes()).hexdigest()
    assignment = json.loads((PACKET_ROOT / "AUDIT_ASSIGNMENT.json").read_text())
    assigned_sha = next(item["generator_sha256"] for item in assignment["targets"]
                        if item["task_id"] == TASK_ID)
    assert generator_sha == assigned_sha
    grids = [module.generate(0, i, difficulty="medium") for i in range(8)]
    samples = []
    for i, grid in enumerate(grids):
        comps = components(grid)
        diagnostics = module.self_check(grid, difficulty="medium")
        assert diagnostics == []
        assert len(comps) in (3, 5, 7)
        assert len({obj["area"] for obj in comps}) == len(comps)
        assert len({obj["color"] for obj in comps}) == len(comps)
        samples.append({
            "input_index": i, "seed": 0, "sample_index": i,
            "difficulty": "medium", "overrides": {}, "slot": i % 4,
            "input_sha256": digest(grid), "rival_output_sha256": digest(rival(grid)),
            "self_check": diagnostics, "documented_domain_member": True,
            "domain_basis": "Unmodified default generate call; one of 3/5/7 distinct-color, distinct-area isolated 4-connected components, in declared dimensions, with a majority zero background; target self_check passes.",
            "dimensions": [len(grid), len(grid[0])], "components_in_reading_order": comps,
        })
    write("input.json", grids)
    write("rival.json", [rival(grid) for grid in grids])
    write("probe_meta.json", {
        "schema": "task-local-read-only-audit-v1", "finding_id": "F4",
        "task_id": TASK_ID, "source_state": "assigned frozen source; unchanged",
        "generator_sha256": generator_sha, "assignment_generator_sha256": assigned_sha,
        "rule_hash_declared": module.RULE_HASH,
        "rule_sha256": hashlib.sha256(canonical["program_solution"].encode()).hexdigest(),
        "canonical_row_sha256": digest(canonical),
        "rival": "median bounding-box area; reading-order tie-break",
        "rival_intent": "intentional audit teaching negative",
        "canonical_pairs_checked": len(pairs),
        "canonical_pairs_matched": sum(rival(pair["input"]) == pair["output"] for pair in pairs),
        "declared_CANONICAL_SHORTCUTS": list(getattr(module, "CANONICAL_SHORTCUTS", {})),
        "declared_LESSON_COMPETITORS": list(getattr(module, "LESSON_COMPETITORS", {})),
        "sample_count": len(samples), "unique_input_count": len({digest(g) for g in grids}),
        "sample_policy": "seed 0, medium, indices 0..7, no overrides; four overlapping cyclic windows, each with 3 consecutive demonstrations and the next 2 consecutive queries",
        "samples": samples,
    })
    print(json.dumps({"prepared_inputs": len(grids), "generator_sha256": generator_sha,
                      "canonical_rival_fits": f"{sum(rival(p['input']) == p['output'] for p in pairs)}/{len(pairs)}"}))


def finalize():
    meta = json.loads((AUDIT_DIR / "probe_meta.json").read_text())
    reference = json.loads((AUDIT_DIR / "racket.json").read_text())
    grids = json.loads((AUDIT_DIR / "input.json").read_text())
    rival_outputs = json.loads((AUDIT_DIR / "rival.json").read_text())
    assert reference["task_id"] == TASK_ID
    assert reference["generator_sha256"] == meta["generator_sha256"]
    assert reference["executed_rule_hash"] == meta["rule_hash_declared"]
    canonical_rule = load_canonical()["program_solution"]
    assert hashlib.sha256(canonical_rule.encode()).hexdigest() == meta["rule_sha256"]
    # The public apply report hashes its executed rule text, which is distinct
    # from the multiline text retained in the canonical row. Compare the
    # whitespace-normalized rule identity, and retain both full text hashes.
    assert hashlib.sha256(" ".join(canonical_rule.split()).encode()).hexdigest()[:12] == reference["executed_rule_hash"]
    assert hashlib.sha256(GENERATOR_PATH.read_bytes()).hexdigest() == meta["generator_sha256"]
    results = reference["results"]
    assert len(results) == len(grids) == 8
    pairs = []
    for i, result in enumerate(results):
        assert result["index"] == i and result["input"] == grids[i]
        assert result["error"] is None and result["valid_output"]
        assert result["input_sha256"] == digest(grids[i])
        assert result["output_sha256"] == digest(result["output"])
        assert module.expected_output(grids[i]) == result["output"]
        pairs.append({"input": grids[i], "output": result["output"]})

    windows = []
    for start in range(4):
        demo_indices = list(range(start, start+3))
        query_indices = list(range(start+3, start+5))
        fits_demos = all(rival_outputs[i] == pairs[i]["output"] for i in demo_indices)
        differing_queries = [i for i in query_indices if rival_outputs[i] != pairs[i]["output"]]
        windows.append({
            "start_sample_index": start, "demo_indices": demo_indices,
            "query_indices": query_indices, "bbox_rival_fits_all_demos": fits_demos,
            "bbox_rival_differing_query_indices": differing_queries,
            "surviving_rival_counterexample": bool(fits_demos and differing_queries),
            "target_lesson_identifiable": {
                str(i): module.lesson_identifiable([pairs[j] for j in demo_indices], pairs[i])
                for i in query_indices
            },
        })
    failures = [window for window in windows if window["surviving_rival_counterexample"]]
    assert len(failures) == 1 and failures[0]["start_sample_index"] == 2
    assert failures[0]["bbox_rival_differing_query_indices"] == [5]
    witness_index = 5
    actual_object = components(pairs[witness_index]["output"])[0]
    rival_object = components(rival_outputs[witness_index])[0]
    summary = {
        "finding_id": "F4", "task_id": TASK_ID,
        "classification": "reproduced teaching-schedule shortcut gap; reference outputs are correct",
        "generator_sha256": meta["generator_sha256"],
        "executed_rule_hash": reference["executed_rule_hash"],
        "rule_text_sha256": reference["rule_text_sha256"],
        "canonical_row_rule_text_sha256": meta["rule_sha256"],
        "canonical_bbox_rival_matches": {"numerator": meta["canonical_pairs_matched"], "denominator": meta["canonical_pairs_checked"]},
        "generated_reference_runs": {"valid": 8, "total": 8},
        "target_self_check_passes": {"numerator": 8, "denominator": 8},
        "python_expected_output_matches_actual_racket": {"numerator": 8, "denominator": 8},
        "generated_bbox_rival_matches": {"numerator": sum(rival_outputs[i] == pairs[i]["output"] for i in range(8)), "denominator": 8},
        "sampling": meta["sample_policy"], "unique_inputs": 8,
        "lesson_windows": windows,
        "failing_lesson_windows": {"numerator": len(failures), "denominator": len(windows), "overlapping": True},
        "decisive_query": {"seed": 0, "sample_index": 5, "difficulty": "medium", "overrides": {},
                           "actual_selected_color": actual_object["color"], "actual_selected_cell_area": actual_object["area"],
                           "rival_selected_color": rival_object["color"], "rival_selected_cell_area": rival_object["area"]},
        "important_qualification": "The target's lesson_identifiable hook correctly returns a missing-bbox-witness reason for the failing window. A consumer enforcing that hook would reject the lesson; this audit establishes a scheduling/coverage defect, not a silent reference-label error or proven admission bypass.",
        "source_files_modified": False,
    }
    write("summary.json", summary)
    write("counterexample.json", {
        "finding_id": "F4", "task_id": TASK_ID,
        "generator_sha256": meta["generator_sha256"],
        "executed_rule_hash": reference["executed_rule_hash"],
        "rule_text_sha256": reference["rule_text_sha256"],
        "canonical_row_rule_text_sha256": meta["rule_sha256"],
        "seed": 0, "sample_index": 5, "difficulty": "medium", "overrides": {},
        "self_check": meta["samples"][5]["self_check"],
        "documented_generator_domain_member": True,
        "domain_basis": meta["samples"][5]["domain_basis"],
        "input": grids[5], "actual_racket_output": pairs[5]["output"],
        "rival_output": rival_outputs[5], "rival_rule": meta["rival"],
        "input_sha256": results[5]["input_sha256"],
        "actual_racket_output_sha256": results[5]["output_sha256"],
        "rival_output_sha256": digest(rival_outputs[5]),
        "demonstrations_that_rival_matches": [
            {"seed": 0, "sample_index": i, "difficulty": "medium", "overrides": {},
             "input": grids[i], "actual_racket_output": pairs[i]["output"],
             "rival_output": rival_outputs[i], "self_check": meta["samples"][i]["self_check"]}
            for i in (2, 3, 4)
        ],
        "command_cwd": "packet_root",
        "actual_apply_cwd": "repo (set by run_with_racket.py)",
        "command_argv": ["python3", "run_with_racket.py", "python3", "-m", "arcpuzzles", "apply", TASK_ID,
                         "--input", "../checks/audit/f395ecd79f92/input.json", "--out", "../checks/audit/f395ecd79f92/racket.json"],
    })
    print(json.dumps({"failing_windows": f"{len(failures)}/{len(windows)}", "decisive_query": summary["decisive_query"],
                      "target_hook_reasons": failures[0]["target_lesson_identifiable"]}))


if __name__ == "__main__":
    if sys.argv[1:] == ["prepare"]:
        prepare()
    elif sys.argv[1:] == ["finalize"]:
        finalize()
    else:
        raise SystemExit("usage: probe.py prepare|finalize")
