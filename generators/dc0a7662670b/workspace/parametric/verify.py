#!/usr/bin/env python3
"""Protected-Racket and finite-rival authoring audit for dc0a7662670b.

This is intentionally bounded.  Native qualification is still the promotion
authority; the report here supplies source-bound authoring evidence, public-turn
examples, and the required wrong-intermediate causal witness.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
from typing import Any

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import public_challenge_bytes

HERE = Path(__file__).resolve().parent
TASK_ID = "dc0a7662670b"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


PROTOTYPE = _load("_dc0a7662670b_verify_prototype", HERE / "prototype.py")
ADAPTER = _load("_dc0a7662670b_verify_adapter", HERE / "adapter.py")


def _sha_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha_text(value: str) -> str:
    return _sha_bytes(value.encode("utf-8"))


def _grid_bytes(grid: list[list[int]]) -> bytes:
    return json.dumps(grid, separators=(",", ":")).encode("utf-8")


def _grid_hash(grid: list[list[int]]) -> str:
    return _sha_bytes(_grid_bytes(grid))


def _literal(grid: list[list[int]]) -> str:
    return "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"


def _source_hashes() -> dict[str, str]:
    names = (
        "adapter.py",
        "prototype.py",
        "promotion.json",
        "canonical.rkt",
        "winner_width_relay.rkt",
        "winner_height_counterfactual.rkt",
        "verify.py",
    )
    return {name: _sha_bytes((HERE / name).read_bytes()) for name in names}


def _write_public_examples(destination: Path, episodes: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    public_dir = destination / "public"
    public_dir.mkdir(parents=True, exist_ok=False)
    rows = []
    seen: set[str] = set()
    for mode, episode in episodes.items():
        for query_index in range(len(episode["test"])):
            challenge = PROTOTYPE.public_turn(episode, query_index)
            payload = public_challenge_bytes(challenge)
            identifier = _sha_bytes(payload)
            if identifier in seen:
                raise AssertionError(f"duplicate visible public payload: {identifier}")
            seen.add(identifier)
            path = public_dir / f"{identifier}.json"
            path.write_bytes(payload)
            rows.append(
                {
                    "public_id": identifier,
                    "filename": path.name,
                    "mode_private": mode,
                    "query_index_private": query_index,
                    "sha256": _sha_bytes(path.read_bytes()),
                }
            )
    return sorted(rows, key=lambda row: row["public_id"])


def run(*, output: Path, seeds: list[int], rival_seeds: int) -> dict[str, Any]:
    if output.exists() or output.is_symlink():
        raise FileExistsError(output)
    output.mkdir(parents=True)
    modes = PROTOTYPE.MODES
    programs = {
        mode: ADAPTER.program({"mode": mode})
        for mode in modes
    }
    counterfactual_program = PROTOTYPE.counterfactual_program()

    canonical_path = HERE / "canonical.rkt"
    if canonical_path.read_text(encoding="utf-8") != programs["canonical"]:
        raise AssertionError("canonical file and adapter program differ")

    evaluations = 0
    parity_rows = []
    selector_values: set[int] = set()
    runtime: dict[str, Any]
    wrapped = {name: wrap_rule(source) for name, source in {
        **programs,
        "winner_height_counterfactual": counterfactual_program,
    }.items()}

    with RacketBridge(timeout=30, max_calls_before_restart=256) as bridge:
        runtime = dict(bridge.runtime_identity)
        if runtime.get("backend") != "racket" or runtime.get("protected") is not True:
            raise AssertionError("verification requires protected Racket")

        for seed in seeds:
            episodes = {
                mode: ADAPTER.generate(seed, {"mode": mode}, 3, 4)
                for mode in modes
            }
            left_inputs = [
                pair["input"]
                for split in ("train", "test")
                for pair in episodes[modes[0]][split]
            ]
            right_inputs = [
                pair["input"]
                for split in ("train", "test")
                for pair in episodes[modes[1]][split]
            ]
            if left_inputs != right_inputs:
                raise AssertionError("input sampling depends on setting")

            for pair_index, grid in enumerate(left_inputs):
                facts = PROTOTYPE.analyze(grid)
                selector_values.add(facts["winner_width"])
                expected = {
                    "canonical": PROTOTYPE.transform(grid, {"mode": "canonical"}),
                    "winner_width_relay": PROTOTYPE.transform(
                        grid, {"mode": "winner_width_relay"}
                    ),
                    "winner_height_counterfactual": PROTOTYPE.transform_height_counterfactual(grid),
                }
                outputs = {}
                for name, source in wrapped.items():
                    outputs[name] = bridge.eval_text(f"({source} {_literal(grid)})")
                    evaluations += 1
                    if outputs[name] != expected[name]:
                        raise AssertionError(
                            f"Racket/Python mismatch seed={seed} pair={pair_index} program={name}"
                        )
                parity_rows.append(
                    {
                        "seed": seed,
                        "pair_index": pair_index,
                        "input_shape": [len(grid), len(grid[0])],
                        "input_sha256": _grid_hash(grid),
                        "winner_width": facts["winner_width"],
                        "winner_height": facts["winner_height"],
                        "program_outputs": {
                            name: _grid_hash(value) for name, value in outputs.items()
                        },
                    }
                )

        witness = PROTOTYPE.causal_witness(seed=71)
        witness_grid = witness["input"]
        relay_output = bridge.eval_text(
            f"({wrapped['winner_width_relay']} {_literal(witness_grid)})"
        )
        evaluations += 1
        height_output = bridge.eval_text(
            f"({wrapped['winner_height_counterfactual']} {_literal(witness_grid)})"
        )
        evaluations += 1
        if relay_output != witness["program_output"]:
            raise AssertionError("causal witness relay output failed protected-Racket replay")
        if height_output != witness["counterfactual_output"]:
            raise AssertionError("causal witness counterfactual failed protected-Racket replay")
        if relay_output == height_output:
            raise AssertionError("wrong-intermediate witness does not change final output")

    finite_rows = []
    finite_failures = []
    for seed in range(rival_seeds):
        report = PROTOTYPE.finite_rival_audit(10_000 + seed, demos=2, queries=4)
        finite_rows.extend(report["rows"])
        finite_failures.extend(report["failures"])
    if finite_failures:
        raise AssertionError("; ".join(finite_failures[:5]))

    count_rows = []
    for demos, queries in ((2, 1), (2, 4), (6, 1), (6, 4)):
        left = ADAPTER.generate(31337, {"mode": "canonical"}, demos, queries)
        right = ADAPTER.generate(31337, {"mode": "winner_width_relay"}, demos, queries)
        left_inputs = [pair["input"] for split in ("train", "test") for pair in left[split]]
        right_inputs = [pair["input"] for split in ("train", "test") for pair in right[split]]
        if left_inputs != right_inputs:
            raise AssertionError("count-boundary input sampling depends on setting")
        count_rows.append({"demos": demos, "queries": queries, "inputs": len(left_inputs)})

    example_episodes = {
        mode: ADAPTER.generate(101, {"mode": mode}, 3, 4)
        for mode in modes
    }
    single = ADAPTER.generate(101, {"mode": "winner_width_relay"}, 3, 1)
    if PROTOTYPE.public_turn(single, 0) != PROTOTYPE.public_turn(
        example_episodes["winner_width_relay"], 0
    ):
        raise AssertionError("first public turn depends on total query count")
    public_rows = _write_public_examples(output, example_episodes)

    witness.update(
        {
            "program_output": relay_output,
            "counterfactual_output": height_output,
            "program_sha256": _sha_text(programs["winner_width_relay"]),
            "counterfactual_program_sha256": _sha_text(counterfactual_program),
            "input_sha256": _grid_hash(witness_grid),
            "program_output_sha256": _grid_hash(relay_output),
            "counterfactual_output_sha256": _grid_hash(height_output),
            "replay_status": "reviewer_replayed",
            "racket": {
                key: runtime[key]
                for key in (
                    "schema",
                    "backend",
                    "protected",
                    "binary_sha256",
                    "prelude_sha256",
                    "bridge_sha256",
                    "boot_script_sha256",
                    "candidate_symbol_policy_sha256",
                )
                if key in runtime
            },
        }
    )
    (output / "causal-witness.json").write_text(
        json.dumps(witness, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    report = {
        "schema": "dc0a7662670b-parametric-authoring-v1",
        "status": "passed",
        "scope": "bounded task-local authoring evidence; not owner acceptance",
        "task_id": TASK_ID,
        "parameter": {
            "name": "mode",
            "values": list(modes),
            "default": "canonical",
            "input_sampling_independent_of_setting": True,
        },
        "sequential_dependency": {
            "step_a": witness["step_a"],
            "intermediate": witness["intermediate_name"],
            "step_b": witness["step_b"],
            "why_b_depends_on_a": witness["why_b_depends_on_a"],
            "witness": "causal-witness.json",
        },
        "counts": {
            "racket_seeds": len(seeds),
            "racket_inputs": len(parity_rows),
            "racket_program_evaluations": evaluations,
            "finite_rival_seeds": rival_seeds,
            "finite_rival_rows": len(finite_rows),
            "public_files": len(public_rows),
        },
        "selector_values_seen": sorted(selector_values),
        "count_boundaries": count_rows,
        "maximum_query": {
            "shape": [30, 30],
            "nonzero_cells": sum(cell != 0 for row in witness_grid for cell in row),
            "components": len(PROTOTYPE.analyze(witness_grid)["ranked"]),
            "touches_all_four_boundaries": all(
                (
                    any(witness_grid[0][col] != 0 for col in range(30)),
                    any(witness_grid[29][col] != 0 for col in range(30)),
                    any(row[0] != 0 for row in witness_grid),
                    any(row[29] != 0 for row in witness_grid),
                )
            ),
        },
        "finite_rival_failures": finite_failures,
        "public_inventory": public_rows,
        "program_sha256": {name: _sha_text(source) for name, source in programs.items()},
        "counterfactual_program_sha256": _sha_text(counterfactual_program),
        "source_sha256": _source_hashes(),
        "racket": witness["racket"],
        "parity_rows": parity_rows,
        "limitations": [
            "The named-rival audit is finite and does not prove unique induction against arbitrary programs.",
            "Protected-Racket parity covers the listed seeds plus one retained causal witness.",
            "The family remains proposed until exact integrated owner qualification and acceptance.",
        ],
    }
    (output / "authoring.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output / "public-index-private.json").write_text(
        json.dumps(public_rows, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seed", type=int, action="append", dest="seeds")
    parser.add_argument("--rival-seeds", type=int, default=64)
    args = parser.parse_args()
    seeds = args.seeds or [0, 17]
    report = run(output=args.out, seeds=seeds, rival_seeds=args.rival_seeds)
    print(
        json.dumps(
            {
                "status": report["status"],
                "racket_inputs": report["counts"]["racket_inputs"],
                "racket_program_evaluations": report["counts"]["racket_program_evaluations"],
                "finite_rival_rows": report["counts"]["finite_rival_rows"],
                "public_files": report["counts"]["public_files"],
                "selector_values_seen": report["selector_values_seen"],
                "maximum_query": report["maximum_query"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
