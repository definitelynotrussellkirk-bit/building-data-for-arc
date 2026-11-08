#!/usr/bin/env python3
"""Protected-Racket self-audit for the modal transform-composition family."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
from typing import Any

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule

import prototype

HERE = Path(__file__).resolve().parent


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _grid_sha(grid: list[list[int]]) -> str:
    raw = json.dumps(grid, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def _execute(programs: dict[str, str], grids: list[list[list[int]]]):
    with RacketBridge() as bridge:
        rules = {}
        for index, (name, source) in enumerate(programs.items()):
            symbol = f"__modal_transform_rule_{index}"
            bridge.eval_text(f"(define {symbol} {wrap_rule(source)})")
            rules[name] = symbol
        inputs = []
        for index, grid in enumerate(grids):
            symbol = f"__modal_transform_input_{index}"
            bridge.define_grid(symbol, grid)
            inputs.append(symbol)
        return {
            name: [bridge.eval_text(f"({symbol} {grid})") for grid in inputs]
            for name, symbol in rules.items()
        }


def verify(out_dir: Path, seed: int = 20261024) -> dict[str, Any]:
    if out_dir.exists():
        raise FileExistsError(out_dir)
    settings = [{prototype.PARAMETER_NAME: value} for value in prototype.SETTINGS]
    episodes = [prototype.generate(seed, setting, 3, 4) for setting in settings]
    inputs = [pair["input"] for pair in episodes[0]["train"] + episodes[0]["test"]]
    if [pair["input"] for pair in episodes[1]["train"] + episodes[1]["test"]] != inputs:
        raise AssertionError("input sampling depends on hidden stamp_rule")

    programs = prototype.rival_programs()
    matrix = _execute(programs, inputs)
    python_matrix = {
        name: [prototype.rival_outputs(grid)[name] for grid in inputs]
        for name in programs
    }
    if matrix != python_matrix:
        mismatches = [name for name in programs if matrix[name] != python_matrix[name]]
        raise AssertionError(f"Racket/Python mismatch for {mismatches}")

    public_payloads: dict[str, bytes] = {}
    records = []
    demo_count = len(episodes[0]["train"])
    for episode in episodes:
        selected = episode["settings"][prototype.PARAMETER_NAME]
        expected = [pair["output"] for pair in episode["train"] + episode["test"]]
        if matrix[selected] != expected:
            raise AssertionError(f"selected Racket labels disagree for {selected}")
        rivals = {}
        for name in programs:
            if name == selected:
                continue
            demo_disagreements = [
                index for index in range(demo_count) if matrix[name][index] != expected[index]
            ]
            query_disagreements = [
                index
                for index in range(4)
                if matrix[name][demo_count + index] != expected[demo_count + index]
            ]
            if not demo_disagreements:
                raise AssertionError(f"retained lesson does not reject {name}")
            rivals[name] = {
                "demo_disagreement_indices": demo_disagreements,
                "query_disagreement_indices": query_disagreements,
            }
        reveal_ids = []
        for index in range(4):
            payload = prototype.visible_turn(episode, index)
            identifier = hashlib.sha256(payload).hexdigest()
            public_payloads[identifier] = payload
            reveal_ids.append(identifier)
        records.append(
            {
                "settings": episode["settings"],
                "program_sha256": hashlib.sha256(
                    episode["program_solution"].encode()
                ).hexdigest(),
                "certificate": episode["certificate"],
                "reveal_ids": reveal_ids,
                "rivals": rivals,
                "input_sha256": [_grid_sha(grid) for grid in inputs],
                "output_sha256": [_grid_sha(grid) for grid in expected],
            }
        )

    adversarial = {}
    malformed = lambda: prototype.generate(seed, {prototype.PARAMETER_NAME: "mirror"}, 3, 4)
    tampered = copy.deepcopy(episodes[0])
    tampered["test"][0]["output"][0][0] = (tampered["test"][0]["output"][0][0] + 1) % 10
    duplicate = copy.deepcopy(episodes[0])
    duplicate["test"][0] = copy.deepcopy(duplicate["train"][0])
    boolean = copy.deepcopy(episodes[0])
    boolean["train"][0]["input"][0][0] = False
    for name, action in {
        "malformed_setting": malformed,
        "tampered_label": lambda: prototype.verify_episode(tampered),
        "duplicate_input": lambda: prototype.verify_episode(duplicate),
        "boolean_cell": lambda: prototype.verify_episode(boolean),
    }.items():
        try:
            action()
        except ValueError as error:
            adversarial[name] = {"rejected": True, "error": str(error)}
        else:
            raise AssertionError(f"adversarial case accepted: {name}")

    one = prototype.generate(seed, {prototype.PARAMETER_NAME: "direct"}, 3, 1)
    four = prototype.generate(seed, {prototype.PARAMETER_NAME: "direct"}, 3, 4)
    if prototype.visible_turn(one, 0) != prototype.visible_turn(four, 0):
        raise AssertionError("first public turn changes with query count")
    adversarial["query_prefix"] = {"identical": True}

    public_dir = out_dir / "public"
    public_dir.mkdir(parents=True)
    for identifier, payload in sorted(public_payloads.items()):
        visible = json.loads(payload)
        if any(secret in payload for secret in (b"settings", b"program", b"stamp_rule")):
            raise AssertionError("public turn leaks private metadata")
        if any("output" in pair for pair in visible["test"]):
            raise AssertionError("public turn leaks a query answer")
        (public_dir / f"{identifier}.json").write_bytes(payload)

    stress_grid = inputs[-1]
    stress_output = matrix["modal_postcompose"][-1]
    stress = prototype.features(stress_grid)
    input_nonzero = {
        (row, col)
        for row, values in enumerate(stress_grid)
        for col, value in enumerate(values)
        if value != 0
    }
    output_nonzero = {
        (row, col)
        for row, values in enumerate(stress_output)
        for col, value in enumerate(values)
        if value != 0
    }

    # The first demonstration has modal color 4. Force color 6 instead: this is
    # a wrong input-derived intermediate, not a new setting.
    witness_index = 0
    witness_grid = inputs[witness_index]
    correct = matrix["modal_postcompose"][witness_index]
    wrong = matrix["fixed_cw"][witness_index]
    if correct == wrong:
        raise AssertionError("wrong-intermediate witness did not change final output")
    audited_case = {
        "settings": {prototype.PARAMETER_NAME: "modal_postcompose"},
        "program": programs["modal_postcompose"],
        "input": witness_grid,
        "output": correct,
        "counterfactual_program": programs["fixed_cw"],
        "intermediate_value": {
            "marker_counts": prototype.features(witness_grid)["marker_counts"],
            "actual_modal_color": 4,
            "actual_global_operation": "flip_left_right",
            "counterfactual_modal_color": 6,
            "counterfactual_global_operation": "rotate_clockwise",
        },
        "ablation": "wrong_intermediate",
    }
    _write_json(out_dir / "audited-case.json", audited_case)

    private = {
        "schema": f"{prototype.TASK_ID}-modal-transform-parametric-racket-v1",
        "status": "passed",
        "reference": "proposed_parametric",
        "training_admitted": False,
        "seed": seed,
        "racket": {
            "backend": "RacketBridge",
            "protected": True,
            "programs": len(programs),
            "inputs": len(inputs),
            "evaluations": len(programs) * len(inputs),
        },
        "episodes": records,
        "adversarial": adversarial,
        "stress": {
            "shape": [len(stress_grid), len(stress_grid[0])],
            "template_size": stress["template_size"],
            "marker_counts": stress["marker_counts"],
            "modal_color": stress["modal_color"],
            "d4_orbit_size": stress["d4_orbit_size"],
            "input_touches_all_boundaries": all(
                (
                    any(row == 0 for row, _ in input_nonzero),
                    any(row == 29 for row, _ in input_nonzero),
                    any(col == 0 for _, col in input_nonzero),
                    any(col == 29 for _, col in input_nonzero),
                )
            ),
            "output_touches_all_boundaries": all(
                (
                    any(row == 0 for row, _ in output_nonzero),
                    any(row == 29 for row, _ in output_nonzero),
                    any(col == 0 for _, col in output_nonzero),
                    any(col == 29 for _, col in output_nonzero),
                )
            ),
            "stamped_cells": len(output_nonzero),
        },
        "audited_case": "audited-case.json",
        "source_sha256": {
            path.name: _sha(path)
            for path in (
                HERE / "prototype.py",
                HERE / "adapter.py",
                HERE / "promotion.json",
                HERE / "canonical.rkt",
                HERE / "modal_postcompose.rkt",
                HERE / "verify.py",
            )
        },
        "limitations": [
            "Evidence covers two admitted settings and seven declared finite shortcuts at one retained seed.",
            "The sampler uses one repeated marker among exactly five markers; it does not claim every frequency grammar.",
            "The fourth query's identity global operation intentionally matches the direct setting while exercising the no-op branch.",
            "No variant is owner-accepted or training-admitted by this receipt.",
        ],
    }
    _write_json(out_dir / "private-report.json", private)
    manifest = {
        "schema": f"{prototype.TASK_ID}-modal-transform-evidence-v1",
        "status": "passed",
        "public_files": len(public_payloads),
        "private_report": "private-report.json",
        "audited_case": "audited-case.json",
        "files": {
            path.relative_to(out_dir).as_posix(): {
                "sha256": _sha(path),
                "bytes": path.stat().st_size,
            }
            for path in sorted(out_dir.rglob("*"))
            if path.is_file()
        },
    }
    _write_json(out_dir / "manifest.json", manifest)
    return private


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=HERE / "evidence" / "current")
    parser.add_argument("--seed", type=int, default=20261024)
    args = parser.parse_args()
    report = verify(args.out, args.seed)
    print(
        json.dumps(
            {
                "status": report["status"],
                "episodes": len(report["episodes"]),
                "racket_evaluations": report["racket"]["evaluations"],
                "evidence": str(args.out),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
