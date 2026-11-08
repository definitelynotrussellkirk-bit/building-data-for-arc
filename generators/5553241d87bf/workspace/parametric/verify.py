#!/usr/bin/env python3
"""Protected-Racket self-audit for the marker-count rotation family."""
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
    raw = json.dumps(grid, separators=(",", ":"), sort_keys=False).encode()
    return hashlib.sha256(raw).hexdigest()


def _execute(programs: dict[str, str], grids: list[list[list[int]]]):
    with RacketBridge() as bridge:
        rules = {}
        for index, (name, source) in enumerate(programs.items()):
            symbol = f"__marker_count_rotation_rule_{index}"
            bridge.eval_text(f"(define {symbol} {wrap_rule(source)})")
            rules[name] = symbol
        inputs = []
        for index, grid in enumerate(grids):
            symbol = f"__marker_count_rotation_input_{index}"
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
        raise AssertionError("input sampling depends on hidden stamp_transform")

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
            if not demo_disagreements or len(query_disagreements) != 4:
                raise AssertionError(f"retained lesson does not reject {name}")
            rivals[name] = {
                "demo_disagreement_indices": demo_disagreements,
                "query_disagreement_indices": query_disagreements,
            }
        reveal_ids = []
        for index in range(4):
            payload = prototype.visible_turn(episode, index)
            identifier = hashlib.sha256(payload).hexdigest()
            if identifier in public_payloads and public_payloads[identifier] != payload:
                raise AssertionError("public identifier collision")
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
    malformed = lambda: prototype.generate(
        seed, {prototype.PARAMETER_NAME: "mirror"}, 3, 4
    )
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

    one = prototype.generate(seed, {prototype.PARAMETER_NAME: "identity"}, 3, 1)
    four = prototype.generate(seed, {prototype.PARAMETER_NAME: "identity"}, 3, 4)
    if prototype.visible_turn(one, 0) != prototype.visible_turn(four, 0):
        raise AssertionError("first public turn changes with query count")
    adversarial["query_prefix"] = {"identical": True}

    public_dir = out_dir / "public"
    public_dir.mkdir(parents=True)
    for identifier, payload in sorted(public_payloads.items()):
        if any(
            secret in payload
            for secret in (b"settings", b"program", b"stamp_transform", b"output\":")
        ):
            # Demonstration outputs are intentionally public; only a test output
            # could leak. Parse below rather than treating every output key as private.
            visible = json.loads(payload)
            if any("output" in pair for pair in visible["test"]):
                raise AssertionError("public turn leaks a query answer")
            if any(secret in payload for secret in (b"settings", b"program", b"stamp_transform")):
                raise AssertionError("public turn leaks private metadata")
        (public_dir / f"{identifier}.json").write_bytes(payload)

    stress_grid = inputs[-1]
    stress = prototype.features(stress_grid)
    nonzero = {
        (row, col)
        for row, values in enumerate(stress_grid)
        for col, value in enumerate(values)
        if value != 0
    }

    witness_grid = inputs[demo_count]
    witness_facts = prototype.features(witness_grid)
    target = next(record for record in witness_facts["targets"] if record["dot_count"] == 2)
    correct = matrix["marker_count_rotation"][demo_count]
    wrong = matrix["always_quarter_turn"][demo_count]
    if correct == wrong:
        raise AssertionError("wrong-intermediate witness did not change final output")
    r0, r1, c0, c1 = target["bounds"]
    witness = {
        "schema": f"{prototype.TASK_ID}-sequential-dependency-witness-v1",
        "status": "passed",
        "setting": {prototype.PARAMETER_NAME: "marker_count_rotation"},
        "step_a": "count zero markers inside each target cell",
        "intermediate": {
            "target_index": target["index"],
            "actual_dot_count": 2,
            "actual_quarter_turns": 2,
            "counterfactual_dot_count": 1,
            "counterfactual_quarter_turns": 1,
        },
        "step_b": "select that clockwise rotation of the complete template and stamp it",
        "why_b_depends_on_a": (
            "The target stamp is selected only after the target-local marker count is known; "
            "forcing the intermediate from two to one selects a different rotation."
        ),
        "programs": {
            "correct": {
                "name": "marker_count_rotation",
                "sha256": hashlib.sha256(programs["marker_count_rotation"].encode()).hexdigest(),
            },
            "wrong_intermediate": {
                "name": "always_quarter_turn",
                "sha256": hashlib.sha256(programs["always_quarter_turn"].encode()).hexdigest(),
            },
        },
        "input": witness_grid,
        "correct_output": correct,
        "wrong_intermediate_output": wrong,
        "target_correct_stamp": [row[c0 : c1 + 1] for row in correct[r0 : r1 + 1]],
        "target_wrong_stamp": [row[c0 : c1 + 1] for row in wrong[r0 : r1 + 1]],
        "changed_cells": sum(
            left != right
            for left_row, right_row in zip(correct, wrong)
            for left, right in zip(left_row, right_row)
        ),
        "racket": {"backend": "RacketBridge", "protected": True},
        "training_admitted": False,
    }
    _write_json(out_dir / "sequential-witness.json", witness)

    private = {
        "schema": f"{prototype.TASK_ID}-marker-count-rotation-parametric-racket-v1",
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
            "logical_shape": stress["logical_shape"],
            "cell_shape": stress["cell_shape"],
            "targets": stress["target_count"],
            "dot_count_histogram": {
                str(value): stress["target_dot_counts"].count(value)
                for value in sorted(set(stress["target_dot_counts"]))
            },
            "touches_all_boundaries": all(
                (
                    any(row == 0 for row, _ in nonzero),
                    any(row == 29 for row, _ in nonzero),
                    any(col == 0 for _, col in nonzero),
                    any(col == 29 for _, col in nonzero),
                )
            ),
        },
        "sequential_witness": "sequential-witness.json",
        "source_sha256": {
            path.name: _sha(path)
            for path in (
                HERE / "prototype.py",
                HERE / "adapter.py",
                HERE / "promotion.json",
                HERE / "canonical.rkt",
                HERE / "marker_count_rotation.rkt",
                HERE / "verify.py",
            )
        },
        "limitations": [
            "Evidence covers two settings and five declared finite shortcuts at one retained seed.",
            "The marker-count grammar is bounded to square 3x3 through 5x5 logical cells.",
            "The exact 30x30 profile uses one two-row and one two-column internal separator band.",
            "No variant is owner-accepted or training-admitted by this receipt.",
        ],
    }
    _write_json(out_dir / "private-report.json", private)
    manifest = {
        "schema": f"{prototype.TASK_ID}-marker-count-rotation-evidence-v1",
        "status": "passed",
        "public_files": len(public_payloads),
        "private_report": "private-report.json",
        "sequential_witness": "sequential-witness.json",
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
