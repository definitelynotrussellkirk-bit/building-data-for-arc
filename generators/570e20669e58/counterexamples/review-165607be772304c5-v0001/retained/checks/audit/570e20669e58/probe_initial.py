"""Focused findings-only audit; run through the packet's public Racket wrapper.

The prepare step inspects only this task's source/canonical data. The analyze
step consumes actual public-CLI Racket output; no Python result is a label.
"""
from __future__ import annotations

from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

from arcpuzzles import Catalog

TASK = "570e20669e58"
HERE = Path(__file__).resolve().parent
ROOT = Path.cwd().resolve()
assert (ROOT / "catalog/puzzles.jsonl").is_file(), "Payload must run from repo"
SOURCE = ROOT / "generators" / TASK / "generator.py"


def write(name, value):
    (HERE / name).write_text(json.dumps(value, indent=2) + "\n")


def load():
    spec = importlib.util.spec_from_file_location("audit_target", SOURCE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def endpoints(grid):
    result = {}
    for r, row in enumerate(grid):
        for c, v in enumerate(row):
            if v:
                result.setdefault(v, []).append((r, c))
    return result


def rival(grid, mode):
    counts = [[0] * len(grid[0]) for _ in grid]
    for pts in endpoints(grid).values():
        if len(pts) != 2:
            continue
        (r1, c1), (r2, c2) = pts
        horizontal_first = {(r1, c) for c in range(min(c1, c2), max(c1, c2) + 1)}
        horizontal_first |= {(r, c2) for r in range(r1, r2 + 1)}
        paths = [horizontal_first]
        if mode == "both_elbows_as_documented":
            vertical_first = {(r, c1) for r in range(r1, r2 + 1)}
            vertical_first |= {(r2, c) for c in range(min(c1, c2), max(c1, c2) + 1)}
            paths.append(vertical_first)
        for path in paths:
            for r, c in path:
                counts[r][c] += 1
    cap = 3 if mode == "cap_at_two" else 4
    return [[0 if v == 0 else min(v + 1, cap) for v in row] for row in counts]


def adjacent_pairs(grid):
    pts = [(r, c, v) for r, row in enumerate(grid) for c, v in enumerate(row) if v]
    return [[list(a), list(b)] for i, a in enumerate(pts) for b in pts[i + 1:]
            if max(abs(a[0] - b[0]), abs(a[1] - b[1])) <= 1]


def prepare():
    module = load()
    row = Catalog(root=ROOT).get(TASK)
    assert len(row["variants"]) == 1
    canonical = row["variants"][0]
    cases = []
    for split in ("train", "test"):
        for i, pair in enumerate(canonical[split]):
            cases.append({"case_id": f"canonical_{split}_{i}", "kind": "canonical",
                          "split": split, "index": i, "input": pair["input"],
                          "canonical_output": pair["output"],
                          "documented_domain": False,
                          "domain_reason": "Endpoints of distinct colors are Chebyshev-adjacent; SUMMARY/INVARIANTS exclude this."})
    for difficulty in ("easy", "medium", "hard"):
        for sample_index in range(8):
            grid = module.generate(17, sample_index, difficulty=difficulty)
            cases.append({"case_id": f"generated_{difficulty}_{sample_index}",
                          "kind": "generated", "seed": 17, "sample_index": sample_index,
                          "difficulty": difficulty, "overrides": {}, "input": grid,
                          "documented_domain": True, "domain_reason": "Produced by unchanged generator with default controls."})
    grid = [[0] * 10 for _ in range(8)]
    for color, pts in {1: [(0, 4), (6, 4)], 5: [(2, 0), (4, 8)], 7: [(2, 2), (7, 6)]}.items():
        for r, c in pts:
            grid[r][c] = color
    cases.append({"case_id": "handmade_three_path_crossing", "kind": "handmade",
                  "seed": None, "sample_index": None, "overrides": None, "input": grid,
                  "documented_domain": True,
                  "domain_reason": "8x10, background 0, three colors in 1..9 each appearing twice, endpoints pairwise Chebyshev distance >=2."})
    for case in cases:
        case["self_check_errors"] = module.self_check(case["input"], difficulty=case.get("difficulty"))
        case["adjacent_endpoint_pairs"] = adjacent_pairs(case["input"])
    override_checks = []
    for name in ("n_distinct_colors", "palette_size"):
        for i in range(8):
            values = []
            for requested in (3, 4):
                g = module.generate(17, i, difficulty="medium", **{name: requested})
                values.append({"requested": requested, "observed_colors": len(endpoints(g)),
                               "input_sha256": hashlib.sha256(json.dumps(g, separators=(",", ":")).encode()).hexdigest(),
                               "matches_retained_case": f"generated_medium_{i}",
                               "self_check_errors": module.self_check(g)})
                assert g == next(c["input"] for c in cases if c["case_id"] == f"generated_medium_{i}")
            override_checks.append({"seed": 17, "sample_index": i, "difficulty": "medium", "axis": name,
                                    "outputs_identical_for_3_and_4": values[0]["input_sha256"] == values[1]["input_sha256"],
                                    "requests": values})
    report = {"task_id": TASK, "phase": "unchanged_audit_target",
              "generator_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
              "catalog_rule_hash": row["rule_hash"],
              "canonical_program_text_sha256": hashlib.sha256(canonical["program_solution"].encode()).hexdigest(),
              "canonical_source": "repo/shared/data/canonical/puzzles.jsonl",
              "canonical_selector": {"task_id": TASK, "variant": 0, "source": canonical["source"]},
              "canonical_written_solution": canonical["written_solution"],
              "review_index_exists": (SOURCE.parent / "evidence/review_index.json").exists(),
              "associated_note_count": len(row["associated_notes"]),
              "declared_CANONICAL_SHORTCUTS": getattr(module, "CANONICAL_SHORTCUTS", None),
              "declared_LESSON_COMPETITORS": getattr(module, "LESSON_COMPETITORS", None),
              "cases": cases, "override_checks": override_checks}
    write("prepared.json", report)
    write("input.json", [c["input"] for c in cases])
    print(json.dumps({"prepared_cases": len(cases), "canonical_accepted": sum(not c["self_check_errors"] for c in cases if c["kind"] == "canonical"),
                      "override_request_count": sum(len(c["requests"]) for c in override_checks)}))


def analyze():
    prepared = json.loads((HERE / "prepared.json").read_text())
    actual = json.loads((HERE / "racket.json").read_text())
    assert prepared["generator_sha256"] == actual["generator_sha256"]
    assert prepared["catalog_rule_hash"] == actual["executed_rule_hash"]
    assert prepared["canonical_program_text_sha256"] == actual["rule_text_sha256"]
    rivals = ("cap_at_two", "both_elbows_as_documented")
    comparisons = []
    for case, result in zip(prepared["cases"], actual["results"], strict=True):
        assert case["input"] == result["input"]
        assert result["output"] is not None, result
        entry = {"case_id": case["case_id"], "kind": case["kind"],
                 "self_check_errors": case["self_check_errors"],
                 "documented_domain": case["documented_domain"],
                 "racket_output": result["output"], "rivals": {}}
        if case["kind"] == "canonical":
            entry["racket_matches_canonical"] = result["output"] == case["canonical_output"]
        for name in rivals:
            output = rival(case["input"], name)
            diffs = [[r, c, v, output[r][c]] for r, rr in enumerate(result["output"]) for c, v in enumerate(rr) if v != output[r][c]]
            entry["rivals"][name] = {"output": output, "matches_racket": not diffs,
                                       "mismatch_count": len(diffs), "first_difference_r_c_racket_rival": diffs[0] if diffs else None}
        comparisons.append(entry)
    summary = {}
    for kind in ("canonical", "generated", "handmade"):
        rows = [c for c in comparisons if c["kind"] == kind]
        summary[kind] = {"count": len(rows), "validator_accepted": sum(not c["self_check_errors"] for c in rows),
                         "rival_matches": {name: sum(c["rivals"][name]["matches_racket"] for c in rows) for name in rivals}}
    summary["canonical"]["racket_matches_canonical"] = sum(c.get("racket_matches_canonical", False) for c in comparisons)
    summary["unique_inputs"] = len({json.dumps(c["input"]) for c in prepared["cases"]})
    summary["override_requests"] = sum(len(x["requests"]) for x in prepared["override_checks"])
    summary["override_request_mismatches"] = sum(r["requested"] != r["observed_colors"] for x in prepared["override_checks"] for r in x["requests"])
    write("findings.json", {"task_id": TASK, "generator_sha256": actual["generator_sha256"],
                            "executed_rule_hash": actual["executed_rule_hash"],
                            "rule_text_sha256": actual["rule_text_sha256"],
                            "summary": summary, "comparisons": comparisons})
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    {"prepare": prepare, "analyze": analyze}[sys.argv[1]]()
