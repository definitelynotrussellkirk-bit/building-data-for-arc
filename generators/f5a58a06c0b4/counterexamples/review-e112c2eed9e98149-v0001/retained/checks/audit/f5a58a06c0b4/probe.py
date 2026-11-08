"""Bounded findings-only audit. Writes only beside this script."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
WORK = HERE.parents[2]
REPO = WORK / "repo"
TID = "f5a58a06c0b4"
EXPECTED_GENERATOR = "dc80bb6f9cdbf71e38456d1d7afa83a2da14da8a18a05bcf0c2d05c85e43cf90"
EXPECTED_RULE_TEXT = "0437f967046f855f44b0a1eb1cc22c75551097cf6d8b110d4e7e249bfdd2ab24"


def save(name, value):
    (HERE / name).write_text(json.dumps(value, indent=2) + "\n")


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def load_generator():
    path = REPO / "generators" / TID / "generator.py"
    assert digest(path.read_bytes()) == EXPECTED_GENERATOR
    spec = importlib.util.spec_from_file_location("audit_f5a58a06c0b4_generator", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def rival(gen, grid):
    """Keep selection, but choose a fixed endpoint from orientation alone."""
    a = gen._analyze(grid)
    endpoint = 0 if a["selected"]["kind"] in ("horizontal", "diag_down") else 1
    return gen._move_marker(grid, a["selected"]["endpoints"][endpoint])


def analysis_summary(gen, grid):
    a = gen._analyze(grid)
    return {
        "self_check": gen.self_check(grid),
        "dimensions": [len(grid), len(grid[0])],
        "marker": a["marker"],
        "selected_kind": a["selected"]["kind"],
        "selected_cells": a["selected"]["cells"],
        "selection_key": a["selected"]["selection_key"],
        "best_tie_count": a["best_tie_count"],
        "endpoint_distances": a["selected"]["endpoint_distances"],
        "destination": a["destination"],
        "destination_index": a["destination_index"],
        "rival_output": rival(gen, grid),
    }


def prepare():
    gen = load_generator()
    canonical_path = REPO / "shared/data/canonical/puzzles.jsonl"
    selected = []
    selected_raw = []
    for line_number, raw in enumerate(canonical_path.read_bytes().splitlines(keepends=True), 1):
        row = json.loads(raw)
        if row.get("task_id") == TID:
            selected.append({"line_number": line_number, "record": row,
                             "exact_line_sha256": digest(raw)})
            selected_raw.append(raw)
    assert len(selected) == 2
    assert all(digest(x["record"]["program_solution"].encode()) == EXPECTED_RULE_TEXT for x in selected)
    (HERE / "canonical_records.jsonl").write_bytes(b"".join(selected_raw))
    (HERE / "audited_rule.rkt").write_text(selected[0]["record"]["program_solution"])
    source_paths = [
        "generators/f5a58a06c0b4/generator.py",
        "generators/f5a58a06c0b4/notes.md",
        "generators/f5a58a06c0b4/evidence/associated_notes.jsonl",
        "generators/f5a58a06c0b4/tests/test_generator_f5a58a06c0b4.py",
    ]
    hashes = {path: digest((REPO / path).read_bytes()) for path in source_paths}
    review_index = REPO / "generators/f5a58a06c0b4/evidence/review_index.json"
    notes = [json.loads(line) for line in (REPO / source_paths[2]).read_text().splitlines()]
    save("source_identity.json", {
        "task_id": TID, "generator_sha256": EXPECTED_GENERATOR,
        "declared_rule_hash": gen.RULE_HASH,
        "rule_text_sha256": EXPECTED_RULE_TEXT,
        "source_files": hashes,
        "audit_assignment_sha256": digest((WORK / "AUDIT_ASSIGNMENT.json").read_bytes()),
        "canonical_path": str(canonical_path),
        "canonical_rows": [{"line_number": x["line_number"],
                            "source": x["record"]["source"],
                            "content_hash": x["record"]["content_hash"],
                            "exact_line_sha256": x["exact_line_sha256"]} for x in selected],
        "current_review_index_exists": review_index.exists(),
        "current_associated_notes": notes,
    })

    minimal = [[7] * 6 for _ in range(6)]
    minimal[0][:3] = [0, 0, 0]
    minimal[2][2] = 5
    assert gen.self_check(minimal) == []
    cases = [{"name": "minimal_valid_query", "seed": None, "sample_index": None,
              "difficulty": None, "overrides": {},
              "construction": "6x6 7-field; zero at (0,0),(0,1),(0,2); gray at (2,2)",
              "input": minimal}]
    overrides = {"grid_h": 6, "grid_w": 6, "run_kind": "horizontal"}
    cases.append({"name": "generated_counterexample", "seed": 85011, "sample_index": 1,
                  "difficulty": "medium", "overrides": overrides,
                  "input": gen.generate(85011, 1, difficulty="medium", **overrides)})
    for difficulty in ("easy", "medium", "hard"):
        for index in range(4):
            cases.append({"name": f"ordinary_{difficulty}_{index}", "seed": 85011,
                          "sample_index": index, "difficulty": difficulty, "overrides": {},
                          "input": gen.generate(85011, index, difficulty=difficulty)})
    for selected_row in selected:
        row = selected_row["record"]
        for split in ("train", "test"):
            for index, pair in enumerate(row[split]):
                cases.append({"name": f"canonical_{row['source']}_{split}_{index}",
                              "seed": None, "sample_index": None, "overrides": {},
                              "input": pair["input"], "canonical_output": pair["output"]})
    for case in cases:
        case.update(analysis_summary(gen, case["input"]))
        assert case["self_check"] == [], case["name"]
    assert len(cases) == 22
    save("cases.json", cases)
    save("input.json", {"inputs": [case["input"] for case in cases]})
    save("minimal_input.json", minimal)
    save("generated_counterexample_input.json", cases[1]["input"])
    print(json.dumps({"prepared_cases": len(cases),
                      "ordinary_generated": 12, "canonical_pairs": 8,
                      "minimal_valid_query": cases[0],
                      "generated_counterexample": cases[1]}, indent=2))


def verify():
    gen = load_generator()
    cases = json.loads((HERE / "cases.json").read_text())
    applied = json.loads((HERE / "racket.json").read_text())
    assert applied["generator_sha256"] == EXPECTED_GENERATOR
    raw_rule = (HERE / "audited_rule.rkt").read_text()
    assert digest(raw_rule.encode()) == EXPECTED_RULE_TEXT
    assert digest(" ".join(raw_rule.split()).encode())[:12] == applied["executed_rule_hash"]
    assert applied["rule_text_sha256"] == "c9d8e249d3861302eb974d159daab69c04ecc27c822c4dddf7185651efabff6b"
    assert applied["executed_rule_hash"] == gen.RULE_HASH
    assert applied["rule_hash_matches_catalog"] is True
    assert len(applied["results"]) == len(cases)
    summaries = []
    pairs = {}
    for case, result in zip(cases, applied["results"], strict=True):
        assert not result["error"], result
        assert result["input"] == case["input"]
        assert gen.self_check(case["input"]) == []
        assert result["output"] == gen.rule_mirror(case["input"]), case["name"]
        if "canonical_output" in case:
            assert result["output"] == case["canonical_output"], case["name"]
        pairs[case["name"]] = {"input": result["input"], "output": result["output"]}
        summary = {"name": case["name"], "self_check": gen.self_check(case["input"]),
                   "selected_kind": case["selected_kind"],
                   "destination_index": case["destination_index"],
                   "rival_matches_racket": rival(gen, result["input"]) == result["output"],
                   "mirror_matches_racket": True}
        summaries.append(summary)
    assert all(x["rival_matches_racket"] for x in summaries if x["name"].startswith("ordinary_"))
    assert not summaries[0]["rival_matches_racket"]
    assert not summaries[1]["rival_matches_racket"]
    lessons = []
    for difficulty in ("easy", "medium", "hard"):
        demos = [pairs[f"ordinary_{difficulty}_{index}"] for index in range(4)]
        for query_name in ("minimal_valid_query", "generated_counterexample"):
            query = pairs[query_name]
            errors = gen.lesson_identifiable(demos, query)
            assert errors == [], (difficulty, query_name, errors)
            lessons.append({"difficulty": difficulty, "seed": 85011,
                            "demo_indexes": [0, 1, 2, 3], "demo_overrides": {},
                            "query": query_name, "lesson_identifiable": errors,
                            "rival_fits_all_demos": all(rival(gen, p["input"]) == p["output"] for p in demos),
                            "rival_disagrees_with_racket_query": rival(gen, query["input"]) != query["output"]})
    result = {"classification": "suspected shortcut", "finding_reproduced": True,
              "description": "Ordinary orientation schedule fixes the destination endpoint independently of marker nearness; the accepted lesson does not eliminate that rival.",
              "source_identity": {key: applied[key] for key in (
                  "generator_sha256", "executed_rule_hash", "rule_text_sha256", "rule_hash_matches_catalog")},
              "all_22_inputs_pass_self_check": True,
              "all_22_racket_outputs_match_generator_mirror": True,
              "all_8_recorded_canonical_outputs_match_racket": True,
              "ordinary_rival_matches": 12, "ordinary_checked": 12,
              "lesson_false_negatives": lessons, "case_results": summaries,
              "minimal": {**cases[0], "actual_racket_output": applied["results"][0]["output"]},
              "generated_counterexample": {**cases[1], "actual_racket_output": applied["results"][1]["output"]},
              "scope": "Bounded task-only audit: 12 ordinary inputs, one generated override witness, one 6x6 minimal-domain witness, and eight recorded canonical pairs. No full-library tests or source edits."}
    result["raw_canonical_rule_sha256"] = EXPECTED_RULE_TEXT
    result["initial_probe_failures"] = [
        "First verifier compared raw (rule! ...) source bytes with the API's wrapped callable-text hash; these are different identities. Corrected the audit-only verifier to bind the retained raw source by its full SHA-256 and independently recompute its normalized declared hash, while retaining the actual callable-text digest separately.",
        "The next verifier tried invoking internal wrap_rule in the direct source layout, which lacks the staged scripts parser package. Removed that unnecessary internal-runtime invocation; actual output and callable-text identity come from the successful public apply execution. Both failed verification attempts are retained. The Racket batch was not rerun or changed.",
    ]
    save("finding.json", result)
    save("lesson_medium.json", {"train": [pairs[f"ordinary_medium_{i}"] for i in range(4)],
                                "test": [pairs["minimal_valid_query"], pairs["generated_counterexample"]]})
    save("minimal_racket_output.json", applied["results"][0]["output"])
    save("minimal_rival_output.json", rival(gen, cases[0]["input"]))
    save("generated_counterexample_racket_output.json", applied["results"][1]["output"])
    print(json.dumps({key: result[key] for key in (
        "classification", "finding_reproduced", "source_identity",
        "all_22_inputs_pass_self_check", "all_22_racket_outputs_match_generator_mirror",
        "all_8_recorded_canonical_outputs_match_racket", "ordinary_rival_matches",
        "ordinary_checked", "lesson_false_negatives")}, indent=2))


if __name__ == "__main__":
    {"prepare": prepare, "verify": verify}[sys.argv[1]]()
