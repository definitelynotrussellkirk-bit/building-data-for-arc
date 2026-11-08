#!/usr/bin/env python3
"""Focused, findings-only audit. Run prepare, public Racket apply, then verify.

Writes only beside this file. Exit 0 means the recorded finding reproduced;
it does not certify the generator or alter its approval.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

TASK = "e91a8e375e64"
EXPECTED_SOURCE = "bffb5d7558b3c846d5d41959a99b9f2f62d87c35822a8fd3980fa5ffdcc6328a"
HERE = Path(__file__).resolve().parent
WORK = HERE.parents[2]
REPO = WORK / "repo"
sys.dont_write_bytecode = True
sys.path.insert(0, str(REPO / "shared/runtime"))


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def grid_hash(grid):
    return digest(json.dumps(grid, separators=(",", ":")).encode())


def save(name, value):
    (HERE / name).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def load_target():
    source = REPO / "generators" / TASK / "generator.py"
    assert digest(source.read_bytes()) == EXPECTED_SOURCE, "Audited source changed"
    spec = importlib.util.spec_from_file_location("audited_e91", source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def panels(grid):
    n = len(grid)
    return [[row[i * (n + 1):i * (n + 1) + n] for row in grid] for i in range(5)]


def interpretation(grid):
    """Independent coordinate formulation; no generator transform helpers."""
    a, b, c, d, q = panels(grid)
    n = len(a)
    maps = {
        "id": lambda r, c: (r, c),
        "rot90": lambda r, c: (c, n - 1 - r),
        "rot180": lambda r, c: (n - 1 - r, n - 1 - c),
        "rot270": lambda r, c: (n - 1 - c, r),
        "flip-h": lambda r, c: (r, n - 1 - c),
        "flip-v": lambda r, c: (n - 1 - r, c),
        "transpose": lambda r, c: (c, r),
        "anti-transpose": lambda r, c: (n - 1 - c, n - 1 - r),
    }

    def transform(matrix, fn):
        out = [[0] * n for _ in range(n)]
        for r in range(n):
            for c in range(n):
                rr, cc = fn(r, c)
                out[rr][cc] = matrix[r][c]
        return out

    matches = [name for name, fn in maps.items() if transform(a, fn) == b]
    assert len(matches) == 1
    mapping = {x: y for cr, dr in zip(c, d) for x, y in zip(cr, dr) if x and y}
    recolor = lambda m: [[mapping.get(v, v) for v in row] for row in m]
    return {
        "inferred_transform": matches[0],
        "inferred_color_map": mapping,
        "independent_expected_output": recolor(transform(q, maps[matches[0]])),
        "rival": {
            "name": "recolor_query_without_geometric_transform",
            "output": recolor(q),
            "purpose": "Diagnostic only; the override-contract finding does not assert a lesson shortcut.",
        },
    }


def prepare():
    target = load_target()
    canonical_path = REPO / "shared/data/canonical/puzzles.jsonl"
    rows = [line for line in canonical_path.read_bytes().splitlines()
            if json.loads(line).get("task_id") == TASK]
    assert len(rows) == 1
    canonical = json.loads(rows[0])
    rule = canonical["program_solution"]
    texture_groups = []
    for seed in range(3):
        cases = []
        for texture in (None, "varied", "wide_map", "big_panel"):
            overrides = {} if texture is None else {"texture": texture}
            grid = target.generate(seed, 0, difficulty="easy", **overrides)
            issues = target.self_check(grid, difficulty="easy")
            assert issues == []
            cases.append({"seed": seed, "sample_index": 0, "difficulty": "easy",
                          "overrides": overrides, "input_sha256": grid_hash(grid),
                          "panel_size": len(grid),
                          "mapping_size": len({v for row in panels(grid)[2] for v in row if v}),
                          "validator_errors": issues})
        assert len({case["input_sha256"] for case in cases}) == 1
        texture_groups.append({"seed": seed, "all_four_inputs_equal": True, "cases": cases})

    rejected = []
    for difficulty, overrides in ((None, {"panel_size": 3}), (None, {"n_map": 4}),
                                  ("hard", {"panel_size": 3}), ("easy", {"n_map": 4})):
        try:
            target.generate(0, 0, difficulty=difficulty, **overrides)
        except ValueError as exc:
            rejected.append({"seed": 0, "sample_index": 0, "difficulty": difficulty,
                             "overrides": overrides, "exception_type": type(exc).__name__,
                             "exception": str(exc), "input": None,
                             "declared_axis_values_valid": True,
                             "validator_acceptance": "not reached: generation raised"})
        else:
            raise AssertionError(f"Expected reported override rejection: {difficulty}, {overrides}")

    witness = target.generate(0, 0, difficulty="easy", texture="big_panel")
    assert len(witness) == 3
    assert witness == target.generate(0, 0, difficulty="easy", panel_size=3)
    save("input.json", witness)
    source_home = REPO / "generators" / TASK
    evidence = {
        "schema": "arcpuzzles-focused-audit-e91-v1",
        "task_id": TASK,
        "status": "findings_reproduced_pending_racket_application",
        "source_stage": "unchanged assigned audit source",
        "generator_sha256": EXPECTED_SOURCE,
        "generator_version": target.VERSION,
        "canonical_rule_text_sha256": digest(rule.encode()),
        "canonical_rule_normalized_sha256": digest(" ".join(rule.split()).encode()),
        "canonical_row_sha256_no_newline": digest(rows[0]),
        "notes_sha256": digest((source_home / "notes.md").read_bytes()),
        "review_index_present": (source_home / "evidence/review_index.json").exists(),
        "declared_axes": target.AXES,
        "findings": [
            {"id": "A-E91-1", "kind": "ignored_override",
             "claim": "All three advertised helpful textures take the same ordinary generation path; texture does not affect RNG or content.",
             "source_locations": ["generators/e91a8e375e64/generator.py:49-56", "generators/e91a8e375e64/generator.py:157-193"],
             "scope": {"seeds": [0, 1, 2], "sample_index": 0, "difficulty": "easy",
                       "calls": 12, "within_seed_groups": 3, "identical_groups": 3},
             "groups": texture_groups},
            {"id": "A-E91-2", "kind": "advertised_valid_override_rejected",
             "claim": "Explicit advertised panel_size/n_map values are rejected by difficulty-narrowed draw_int calls evaluated as dict.get defaults.",
             "source_locations": ["generators/e91a8e375e64/generator.py:49-56", "generators/e91a8e375e64/generator.py:162-169"],
             "cases": rejected},
        ],
        "witness": {
            "seed": 0, "sample_index": 0, "difficulty": "easy",
            "overrides": {"texture": "big_panel"}, "input": witness,
            "input_sha256": grid_hash(witness),
            "validator_errors": target.self_check(witness, difficulty="easy"),
            "validator_accepts": True, "documented_generator_domain": True,
            "domain_basis": "Declared easy generation; five 3x3 square panels, 3x19 total, separator color 5, unique nonidentity A->B, consistent demonstrated nonidentity color map covering Q.",
            **interpretation(witness),
        },
        "limits": ["Focused override-contract audit only; no exhaustive seed, default-lesson, or full-battery claim.",
                   "No wrong Racket label or shortcut is asserted by these override findings.",
                   "No target source, rule, notes, metadata, assignment, or approval record was edited."],
    }
    save("finding.json", evidence)
    print(json.dumps({"prepared": str(HERE / "finding.json"), "texture_groups_reproduced": 3,
                      "calls_in_texture_probe": 12, "valid_override_rejections": len(rejected)}))


def verify():
    load_target()
    evidence = json.loads((HERE / "finding.json").read_text())
    record = json.loads((HERE / "racket.json").read_text())
    assert record["generator_sha256"] == EXPECTED_SOURCE
    # apply.rule_text_sha256 binds the executable callable wrapper, while the
    # canonical field above binds the original rule! source. These are distinct.
    assert record["executed_rule_hash"] == evidence["canonical_rule_normalized_sha256"][:12]
    assert record["rule_hash_matches_catalog"] is True
    assert len(record["results"]) == 1
    actual = record["results"][0]
    witness = evidence["witness"]
    assert actual["input"] == witness["input"]
    assert actual["output"] == witness["independent_expected_output"]
    witness["real_racket_output"] = actual["output"]
    witness["rival"]["equals_real_racket_output"] = witness["rival"]["output"] == actual["output"]
    evidence["executed_rule_hash"] = record["executed_rule_hash"]
    evidence["racket_callable_text_sha256"] = record["rule_text_sha256"]
    evidence["racket_record_sha256"] = digest((HERE / "racket.json").read_bytes())
    evidence["reproducer_sha256"] = digest(Path(__file__).read_bytes())
    evidence["status"] = "findings_reproduced_and_racket_witness_verified"
    save("finding.json", evidence)
    print(json.dumps({"status": evidence["status"], "generator_sha256": EXPECTED_SOURCE,
                      "rule_text_sha256": record["rule_text_sha256"],
                      "validator_accepts": True, "independent_oracle_matches_racket": True,
                      "rival_matches_racket": witness["rival"]["equals_real_racket_output"]}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=("prepare", "verify"))
    args = parser.parse_args()
    {"prepare": prepare, "verify": verify}[args.phase]()
