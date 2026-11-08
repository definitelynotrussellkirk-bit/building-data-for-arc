"""Small source-bound before/after check using the real canonical Racket rule.

Run through WORK/run_with_racket.py from the packet; no runtime tree is copied.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys


CHECKS = Path(__file__).resolve().parent
REPO = CHECKS.parents[1] / "repo"
TASK = REPO / "generators/c4f6a0585dbf"
AUDIT = (TASK / "counterexamples/review-0697b52e64b4b855-v0001/retained/checks"
         / "audit/c4f6a0585dbf/semantic")
sys.path.insert(0, str(REPO / "shared/runtime"))
from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule


def digest(data):
    return hashlib.sha256(data).hexdigest()


def grid_hash(grid):
    return digest(json.dumps(grid, separators=(",", ":")).encode())


def main():
    phase = sys.argv[1]
    if phase not in ("before", "after"):
        raise ValueError("phase must be before or after")
    spec = importlib.util.spec_from_file_location("canonical_check", TASK / "generator.py")
    generator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(generator)
    rule_file = REPO / "shared/data/canonical/puzzles.jsonl"
    rows = [json.loads(line) for line in rule_file.open()
            if json.loads(line).get("task_id") == generator.TASK_ID]
    rules = {row["program_solution"] for row in rows}
    assert len(rules) == 1, "canonical rule must be unambiguous"
    rule = rules.pop()
    rule_hash = digest(" ".join(rule.split()).encode())[:12]
    assert rule_hash == "d401b3cd92ff"
    cases = [dict(seed=seed, sample_index=index, difficulty=difficulty)
             for seed in (0, 13) for index in (0, 5)
             for difficulty in (None, "easy", "medium", "hard")]
    cases += [dict(seed=13, sample_index=5, difficulty="medium", grid_h=18,
                   grid_w=30, n_fours=17),
              dict(seed=0, sample_index=0, difficulty="hard", grid_h=30,
                   grid_w=18, n_fours=47)]
    generated = []
    for args in cases:
        grid = generator.generate(**args)
        assert generator.self_check(grid) == [], (args, generator.self_check(grid))
        assert {v for row in grid for v in row} == {0, 1, 4}
        generated.append({"arguments": args, "input_sha256": grid_hash(grid),
                          "shape": [len(grid), len(grid[0])]})
    warm = json.loads((AUDIT / "input.json").read_text())
    control = generator.generate(13, 5, difficulty="medium")
    assert control == json.loads((AUDIT / "control_input.json").read_text())
    warm_errors = generator.self_check(warm)
    if phase == "before":
        assert generator.generate(13, 5, difficulty="medium", palette_kind="warm") == warm
        assert warm_errors == []
    else:
        before = json.loads((CHECKS / "before.json").read_text())
        assert before["seeded_samples"] == generated, "canonical sampling changed"
        assert warm_errors, "warm witness must be rejected"
        try:
            generator.generate(13, 5, difficulty="medium", palette_kind="warm")
        except ValueError as exc:
            rejected_message = str(exc)
        else:
            raise AssertionError("palette_kind warm was accepted")
    calls = []
    with RacketBridge(timeout=30.0) as bridge:
        bridge.eval_text(f"(define canonical_rule {wrap_rule(rule)})")
        def apply(name, grid, expected, changes=None):
            bridge.define_grid("canonical_input", grid)
            output = bridge.eval_text("(canonical_rule canonical_input)")
            assert output == expected, name
            count = sum(a != b for inrow, outrow in zip(grid, output)
                        for a, b in zip(inrow, outrow))
            if changes is not None:
                assert count == changes, (name, count)
            calls.append({"name": name, "input_sha256": grid_hash(grid),
                          "output_sha256": grid_hash(output), "changed_cells": count,
                          "matches_expected": True})
        apply("retained_warm_witness", warm,
              json.loads((AUDIT / "racket.json").read_text())["results"][0]["output"], 0)
        apply("canonical_seed_13_index_5", control,
              json.loads((AUDIT / "control_racket.json").read_text())["results"][0]["output"], 10)
        if phase == "after":
            for texture in ("no_targets", "full_grid"):
                grid = generator.generate(13, 5, texture=texture)
                assert generator.self_check(grid) == []
                apply(texture, grid, grid, 0)
            seen = set()
            for row in rows:
                for pair in row.get("train", []) + row.get("test", []):
                    identity = grid_hash(pair["input"])
                    if identity not in seen:
                        seen.add(identity)
                        apply(f"canonical_pair_{len(seen)}", pair["input"], pair["output"])
        binary = bridge.racket_binary
    receipt = {
        "schema": "canonical-palette-focused-check-v1", "phase": phase,
        "command": [sys.executable, *sys.argv], "cwd": str(Path.cwd()),
        "exit_code": 0, "generator_sha256": digest((TASK / "generator.py").read_bytes()),
        "test_sha256": digest((TASK / "tests/test_canonical_palette.py").read_bytes()),
        "check_script_sha256": digest(Path(__file__).read_bytes()),
        "racket_binary": binary, "racket_wrapper_sha256": digest(Path(binary).read_bytes()),
        "environment": {key: os.environ.get(key) for key in
                        ("RACKET_PATH", "PYTHONPATH", "PYTHONDONTWRITEBYTECODE")},
        "rule_file": str(rule_file.relative_to(REPO)),
        "rule_file_sha256": digest(rule_file.read_bytes()),
        "rule_text_sha256": digest(rule.encode()), "executed_rule_hash": rule_hash,
        "seeded_samples": generated, "seeded_samples_match_before": phase == "after",
        "warm_self_check": warm_errors, "racket_results": calls,
        "unrun": ["full repository suite", "inherited generator battery", "broad stochastic semantic sweep"],
        "approval_or_audit_resolution_changed": False,
    }
    if phase == "after":
        receipt["palette_kind_rejection"] = rejected_message
    (CHECKS / f"{phase}.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({"phase": phase, "source_sha256": receipt["generator_sha256"],
                      "seeded_samples": len(generated), "racket_cases": len(calls),
                      "warm_changed_cells": calls[0]["changed_cells"],
                      "control_changed_cells": calls[1]["changed_cells"],
                      "warm_self_check": warm_errors}))


if __name__ == "__main__":
    main()
