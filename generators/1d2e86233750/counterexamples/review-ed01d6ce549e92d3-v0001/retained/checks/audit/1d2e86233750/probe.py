"""Small findings-only audit; run through review.py run from the packet root."""
from __future__ import annotations

import copy
import hashlib
import json
import sys
from pathlib import Path

from reviewer_support import load_selected_generator

TASK = "1d2e86233750"
EXPECTED_SOURCE = "e2903eeeb93fb7aad0e4e630c3ce498a06b9697adcda3bef799b5b1003549873"
OUT = Path(__file__).resolve().parent
ROOT = Path.cwd()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def write(name, data):
    raw = (json.dumps(data, indent=2) + "\n").encode()
    (OUT / name).write_bytes(raw)
    return sha(raw)


def panels(grid):
    # The selected generator fixes one-row/column padding and one-column gaps.
    n = len(grid) - 4
    return [
        [row[2 + i * (n + 3):2 + i * (n + 3) + n] for row in grid[2:2 + n]]
        for i in range(3)
    ]


def transforms(grid):
    return {
        1: [list(row) for row in zip(*grid[::-1])],
        2: [row[::-1] for row in grid[::-1]],
        3: [row[::-1] for row in grid],
        4: [row[:] for row in grid[::-1]],
    }


def prepare():
    module, source, digest = load_selected_generator(TASK, root=ROOT)
    assert digest == EXPECTED_SOURCE, digest
    selected = next(
        row for line in (ROOT / "shared/data/canonical/puzzles.jsonl").open()
        if (row := json.loads(line)).get("task_id") == TASK
    )
    rule_text = selected["program_solution"]

    lesson_inputs, lesson_rows = [], []
    for index in range(12, 16):
        grid = module.generate(1, index, difficulty="medium")
        a, b, c = panels(grid)
        matches = [code for code, output in transforms(a).items() if output == b]
        assert module.self_check(grid) == []
        lesson_inputs.append(grid)
        lesson_rows.append({
            "seed": 1, "sample_index": index, "difficulty": "medium", "overrides": {},
            "validator_errors": module.self_check(grid), "inferred_transform_codes": matches,
            "always_clockwise_c_output": transforms(c)[1],
        })
    teaching_hash = write("teaching_inputs.json", lesson_inputs)

    for seed in range(20):
        original = module.generate(seed, 0, difficulty="medium")
        n = len(original) - 4
        c_left = 1 + 2 * (n + 3)
        source_cell, destination_cell = (1, c_left + 1), (2, c_left + 1)
        if original[destination_cell[0]][destination_cell[1]] != 0:
            continue
        malformed = copy.deepcopy(original)
        malformed[source_cell[0]][source_cell[1]] = 0
        malformed[destination_cell[0]][destination_cell[1]] = 9
        assert original[source_cell[0]][source_cell[1]] == 9
        assert module.self_check(original) == []
        assert module.self_check(malformed) == [], module.self_check(malformed)
        break
    else:
        raise AssertionError("No eligible deterministic mutation in the bounded probe")
    original_hash = write("original_input.json", original)
    malformed_hash = write("malformed_input.json", malformed)
    record = {
        "task_id": TASK, "generator_sha256": digest,
        "generator_path": str(source.relative_to(ROOT)),
        "canonical_rule_program_sha256": sha(rule_text.encode()),
        "canonical_rule_program": rule_text,
        "teaching": {
            "input_path": "checks/audit/1d2e86233750/teaching_inputs.json",
            "input_file_sha256": teaching_hash,
            "policy": "three consecutive demonstrations; fourth pair held out as query",
            "domain": "unmodified ordinary generator outputs with no overrides",
            "pairs": lesson_rows,
        },
        "malformed_frame": {
            "base_seed": seed, "sample_index": 0, "difficulty": "medium", "overrides": {},
            "moved_color_9_from": source_cell, "moved_color_9_to": destination_cell,
            "original_input_path": "checks/audit/1d2e86233750/original_input.json",
            "original_input_file_sha256": original_hash,
            "input_path": "checks/audit/1d2e86233750/malformed_input.json",
            "input_file_sha256": malformed_hash,
            "validator_errors_before": module.self_check(original),
            "validator_errors_after": module.self_check(malformed),
            "domain": "validator-only counterexample; mutated C frame is outside documented hollow-frame domain",
            "expected_reference_behavior": "reject C as a frame; fewer than three frames remain",
        },
    }
    write("precheck.json", record)
    print(json.dumps({
        "source_sha256": digest,
        "rule_sha256": record["canonical_rule_program_sha256"],
        "lesson_codes": [row["inferred_transform_codes"] for row in lesson_rows],
        "mutation_seed": seed,
        "malformed_validator_errors": module.self_check(malformed),
    }, indent=2))


def summarize():
    module, _, digest = load_selected_generator(TASK, root=ROOT)
    assert digest == EXPECTED_SOURCE
    before = json.loads((OUT / "precheck.json").read_text())
    lesson = json.loads((OUT / "teaching_racket_venv.json").read_text())
    original = json.loads((OUT / "original_racket_venv.json").read_text())
    malformed = json.loads((OUT / "malformed_racket_venv.json").read_text())
    for receipt in (lesson, original, malformed):
        assert receipt["generator_sha256"] == digest
        assert receipt["executed_rule_hash"] == "d59b40f14330"
        assert receipt["rule_hash_matches_catalog"] is True
    matches = []
    pairs = []
    for probe, result in zip(before["teaching"]["pairs"], lesson["results"], strict=True):
        assert result["valid_output"] and result["error"] is None
        assert module.self_check(result["input"]) == []
        agrees = probe["always_clockwise_c_output"] == result["output"]
        matches.append(agrees)
        pairs.append({**probe, **result, "rival_matches_reference": agrees})
    assert matches == [True, True, True, False], matches
    control, failure = original["results"][0], malformed["results"][0]
    assert control["valid_output"] and control["error"] is None
    assert failure["output"] is None and not failure["valid_output"]
    assert "take: contract violation" in failure["error"]
    assert module.self_check(failure["input"]) == []
    assert module.self_check(control["input"]) == []
    report = {
        "task_id": TASK, "generator_sha256": digest,
        "runtime_python": sys.executable,
        "reproducer_sha256": sha(Path(__file__).read_bytes()),
        "executed_rule_hash": lesson["executed_rule_hash"],
        "executed_rule_text_sha256": lesson["rule_text_sha256"],
        "findings": [
            {
                "id": "A-1d2-1", "classification": "reproduced_defect",
                "scope": "validator_only_outside_documented_domain",
                "summary": "self_check accepts a nonrectangular color-9 frame that the Racket authority rejects",
                **before["malformed_frame"],
                "unmodified_control": control,
                "malformed_case": failure,
                "public_apply_exit_code": 1,
                "limit": "One two-cell mutation; no claim that ordinary generation emits this malformed frame.",
                "suggested_fix": "Require each color-9 component to equal its bounding-box perimeter, not merely have the same cell count.",
            },
            {
                "id": "A-1d2-2", "classification": "reproduced_teaching_defect",
                "scope": "ordinary_generated_four_pair_episode",
                "summary": "Always rotate C clockwise fits all three demonstrations but changes the held-out query",
                "seed": 1, "sample_indices": [12, 13, 14, 15], "difficulty": "medium",
                "demonstration_count": 3, "query_index": 3,
                "rival_matches_reference": matches, "pairs": pairs,
                "prior_status": "Current review index retains this exact teaching defect as needs_triage; independently reproduced on the unchanged source.",
                "limit": "Existence of one reachable ordered lesson, not an estimate of frequency or an exhaustive query-rotation census.",
                "suggested_fix": "Schedule transform variation, declare constant-transform rivals, and test each lesson and supported holdout policy.",
            },
        ],
        "source_unchanged": True,
        "racket_receipts": [
            "checks/audit/1d2e86233750/teaching_racket_venv.json",
            "checks/audit/1d2e86233750/original_racket_venv.json",
            "checks/audit/1d2e86233750/malformed_racket_venv.json",
        ],
    }
    write("counterexample.json", report)
    base = "checks/audit/1d2e86233750/"
    commands = [{
        "cwd": "packet_root", "payload_cwd": "repo", "phase": "audit",
        "argv": ["python3", "review.py", "run", "../.venv/bin/python", "../" + base + "probe.py"],
        "exit_code": 0,
        "evidence_paths": [base + name for name in (
            "probe.py", "precheck.json", "teaching_inputs.json", "original_input.json", "malformed_input.json")],
    }]
    for input_name, output_name, exit_code in (
        ("teaching_inputs.json", "teaching_racket_venv.json", 0),
        ("original_input.json", "original_racket_venv.json", 0),
        ("malformed_input.json", "malformed_racket_venv.json", 1),
    ):
        commands.append({
            "cwd": "packet_root", "payload_cwd": "repo", "phase": "audit",
            "argv": ["python3", "review.py", "run", "../.venv/bin/python", "-m", "arcpuzzles", "apply", TASK,
                     "--input", "../" + base + input_name, "--out", "../" + base + output_name],
            "exit_code": exit_code,
            "evidence_paths": [base + input_name, base + output_name],
        })
    commands.append({
        "cwd": "packet_root", "payload_cwd": "repo", "phase": "audit",
        "argv": ["python3", "review.py", "run", "../.venv/bin/python", "../" + base + "probe.py", "summarize"],
        "exit_code": 0, "evidence_paths": [base + "counterexample.json", base + "commands.json"],
    })
    write("commands.json", commands)
    print(json.dumps({
        "source_sha256": digest,
        "findings": [finding["id"] for finding in report["findings"]],
        "rival_matches_reference": matches,
        "malformed_case": "self_check accepts; public Racket apply exits 1",
    }, indent=2))


if __name__ == "__main__":
    if sys.argv[1:] == ["summarize"]:
        summarize()
    elif not sys.argv[1:]:
        prepare()
    else:
        raise SystemExit("Usage: probe.py [summarize]")
