"""Replay bounded canonical-contract evidence from this packet's source tree."""
from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from pathlib import Path

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import strip_rule_wrapper
from reviewer_support import canonical_path, find_root, load_selected_generator


def sha(value):
    return hashlib.sha256(json.dumps(value, separators=(",", ":")).encode()).hexdigest()


def main():
    out = Path(__file__).resolve().parent
    root = find_root(__file__)
    generator, source, source_sha256 = load_selected_generator("dc2c4869445c", root=root)
    before = json.loads((out / "before-generation.json").read_text())
    canonical = {
        row["program_solution"]
        for line in canonical_path(root).read_text().splitlines()
        if (row := json.loads(line)).get("task_id") == generator.TASK_ID
    }
    assert len(canonical) == 1
    program = canonical.pop()
    callable_text = strip_rule_wrapper(program)
    report = {
        "schema": "dc2c4869445c-canonical-contract-evidence-v1",
        "command": "WORK/.venv-review/bin/python review.py run ../.venv-review/bin/python ../checks/canonical-contract/probe.py",
        "task_id": generator.TASK_ID,
        "source": str(source.relative_to(root)),
        "generator_before_sha256": before["generator_sha256"],
        "generator_sha256": source_sha256,
        "test_sha256": hashlib.sha256((root / "generators/dc2c4869445c/tests/test_contract_dc2c4869445c.py").read_bytes()).hexdigest(),
        "version": generator.VERSION,
        "rule_hash_declared": generator.RULE_HASH,
        "canonical_program": program,
        "canonical_program_sha256": hashlib.sha256(program.encode()).hexdigest(),
        "callable_sha256": hashlib.sha256(callable_text.encode()).hexdigest(),
        "before_calls": len(before["cases"]),
        "preserved_successful_inputs": 0,
        "changed_successful_inputs": [],
        "repaired_calls": [],
        "lawful_textures": [],
        "witness_census": {},
        "witness_examples": {},
        "scope": (
            "Finite generation replay and executed canonical-Racket witnesses. "
            "No lesson contract, universal identifiability, clipping extension, "
            "whole-repository pass, or parametric-prototype approval is claimed."
        ),
    }
    racket_calls = 0
    with RacketBridge() as bridge:
        bridge.eval_text(f"(define contract-rule {callable_text})")
        report["runtime_identity"] = bridge.runtime_identity

        def apply(grid):
            nonlocal racket_calls
            bridge.define_grid("contract-input", grid)
            result = bridge.eval_text("(contract-rule contract-input)")
            racket_calls += 1
            assert result == generator.rule_mirror(grid)
            return result

        for case in before["cases"]:
            grid = generator.generate(
                case["seed"], case["sample_index"],
                difficulty=case["difficulty"], **case["overrides"],
            )
            assert generator.self_check(grid) == []
            if "error" in case:
                expected = apply(grid)
                report["repaired_calls"].append({
                    **case, "input": grid, "output": expected,
                    "observed": generator.observe_overrides(grid),
                    "input_sha256": sha(grid), "output_sha256": sha(expected),
                })
            elif sha(grid) == case["input_sha256"]:
                report["preserved_successful_inputs"] += 1
            else:
                report["changed_successful_inputs"].append(case)
        assert not report["changed_successful_inputs"]

        for texture in generator.LAWFUL_DEGENERATE_TEXTURES:
            for band in ("easy", "medium", "hard"):
                for seed in range(3):
                    grid = generator.generate(seed, 2, difficulty=band, texture=texture)
                    assert generator.self_check(grid) == []
                    expected = apply(grid)
                    assert expected != grid
                    report["lawful_textures"].append({
                        "texture": texture, "difficulty": band, "seed": seed,
                        "sample_index": 2, "input": grid, "output": expected,
                        "observed": generator.observe_overrides(grid),
                        "input_sha256": sha(grid), "output_sha256": sha(expected),
                    })

        for band in ("easy", "medium", "hard"):
            counts = {name: {"fired": 0, "racket_refuted": 0}
                      for name in generator.SEMANTIC_WITNESSES}
            for seed in range(30):
                grid = generator.generate(seed, seed * 17 + 3, difficulty=band)
                assert generator.self_check(grid) == []
                original = deepcopy(grid)
                expected = apply(grid)
                for name, predicate in generator.SEMANTIC_WITNESSES.items():
                    if not predicate(grid):
                        continue
                    counts[name]["fired"] += 1
                    rivals = {rival: generator.SEMANTIC_RIVALS[rival](grid)
                              for rival in generator.WITNESS_RIVALS[name]}
                    assert any(result != expected for result in rivals.values())
                    counts[name]["racket_refuted"] += 1
                    if name not in report["witness_examples"]:
                        report["witness_examples"][name] = {
                            "difficulty": band, "seed": seed,
                            "sample_index": seed * 17 + 3,
                            "input": grid, "output": expected,
                            "rival_outputs": rivals,
                        }
                assert grid == original
            report["witness_census"][band] = {"draws": 30, "counts": counts}

    assert set(report["witness_examples"]) == set(generator.SEMANTIC_WITNESSES)
    report["racket_calls"] = racket_calls
    report["status"] = "PASS_FINITE_EVIDENCE"
    (out / "evidence.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({key: report[key] for key in (
        "status", "generator_sha256", "before_calls", "preserved_successful_inputs",
        "changed_successful_inputs", "racket_calls", "witness_census",
    )}, indent=2))
    print("repaired calls:", len(report["repaired_calls"]))
    print("lawful texture examples:", len(report["lawful_textures"]))


if __name__ == "__main__":
    main()
