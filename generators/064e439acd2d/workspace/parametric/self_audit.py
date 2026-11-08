#!/usr/bin/env python3
"""Protected-Racket bounded audit for the 064e projection-edge family."""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
MODULE_PATH = HERE / "prototype.py"
SPEC = importlib.util.spec_from_file_location("_edge_mode_self_audit_prototype", MODULE_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("cannot load adjacent prototype")
p = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(p)


def digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def inputs(episode: dict[str, Any]) -> list[list[list[int]]]:
    return [pair["input"] for pair in episode["train"] + episode["test"]]


def audit(seeds: list[int]) -> dict[str, Any]:
    if not seeds or any(type(seed) is not int for seed in seeds):
        raise ValueError("seeds must be a nonempty exact-integer list")
    jobs = []
    racket_evaluations = 0
    public_turn_ids: set[str] = set()
    stress_records = []

    with p.RacketRunner() as execute:
        for seed in seeds:
            max_episodes = {
                setting["edge_mode"]: p.generate(seed, setting, demos=6, queries=4)
                for setting in p.SETTINGS
            }
            near_inputs = inputs(max_episodes["near"])
            far_inputs = inputs(max_episodes["far"])
            if near_inputs != far_inputs:
                raise AssertionError(f"seed {seed}: inputs reveal the setting")

            for setting in p.SETTINGS:
                maximum = max_episodes[setting["edge_mode"]]
                minimum = p.generate(seed, setting, demos=2, queries=4)
                one_query = p.generate(seed, setting, demos=6, queries=1)
                if minimum["train"] != maximum["train"][:2]:
                    raise AssertionError(f"seed {seed} {setting}: demo prefix instability")
                if one_query["train"] != maximum["train"] or one_query["test"] != maximum["test"][:1]:
                    raise AssertionError(f"seed {seed} {setting}: query prefix instability")

                for demos, episode in ((2, minimum), (6, maximum)):
                    certificate = p.certify(episode, execute)
                    # certify executes both declared programs on demonstrations,
                    # then the selected program on all retained pairs.
                    racket_evaluations += 2 * demos + demos + 4
                    if certificate["survivors"] != [setting]:
                        raise AssertionError(f"seed {seed} {setting}: wrong survivors")
                    if not certificate["all_declared_rivals_refuted"]:
                        raise AssertionError(f"seed {seed} {setting}: finite rival survived")

                    query_disagreements = []
                    alternate = {"edge_mode": "far" if setting["edge_mode"] == "near" else "near"}
                    for pair in episode["test"]:
                        rival = execute(p.program(alternate), pair["input"])
                        racket_evaluations += 1
                        query_disagreements.append(rival != pair["output"])
                    if not all(query_disagreements):
                        raise AssertionError(f"seed {seed} {setting}: a query does not require the setting")

                    first_turn = p.public_turn_bytes(episode, 0)
                    changed = copy.deepcopy(episode)
                    changed["settings"] = {"private": "changed"}
                    changed["program_solution"] = "changed"
                    changed["test"][0]["output"] = [[9]]
                    changed["test"][3]["input"] = [[9]]
                    if p.public_turn_bytes(changed, 0) != first_turn:
                        raise AssertionError("first public turn depends on private/future data")
                    turn_id = hashlib.sha256(first_turn).hexdigest()
                    if turn_id in public_turn_ids:
                        raise AssertionError("duplicate visible first turn")
                    public_turn_ids.add(turn_id)

                    jobs.append(
                        {
                            "seed": seed,
                            "settings": setting,
                            "demos": demos,
                            "queries": 4,
                            "input_sha256": [digest(grid) for grid in inputs(episode)],
                            "program_sha256": hashlib.sha256(p.program(setting).encode()).hexdigest(),
                            "survivors": certificate["survivors"],
                            "rival_first_refutation": certificate["rival_first_refutation"],
                            "all_queries_require_setting": True,
                            "public_first_turn_sha256": turn_id,
                        }
                    )

                stress = maximum["test"][3]
                changed_cells = sum(
                    before != after
                    for in_row, out_row in zip(stress["input"], stress["output"])
                    for before, after in zip(in_row, out_row)
                )
                nonzero = sum(cell != 0 for row in stress["input"] for cell in row)
                if (len(stress["input"]), len(stress["input"][0])) != (30, 30):
                    raise AssertionError("fourth query is not 30x30")
                if changed_cells < 16 or nonzero < 250:
                    raise AssertionError("30x30 stress is not substantive")
                stress_records.append(
                    {
                        "seed": seed,
                        "settings": setting,
                        "shape": [30, 30],
                        "nonzero_input_cells": nonzero,
                        "changed_cells": changed_cells,
                        "input_sha256": digest(stress["input"]),
                        "output_sha256": digest(stress["output"]),
                    }
                )

        runtime = execute.identity

    return {
        "schema": "arcpuzzles-projection-edge-self-audit-v1",
        "task_id": p.TASK_ID,
        "status": "passed",
        "scope": {
            "settings": p.SETTINGS,
            "seeds": seeds,
            "demo_counts": [2, 6],
            "queries": 4,
            "finite_rivals": list(p._RIVAL_NAMES),
            "limits": "Finite source-bound audit; not universal uniqueness or owner acceptance.",
        },
        "runtime": runtime,
        "jobs": jobs,
        "jobs_passed": len(jobs),
        "racket_evaluations": racket_evaluations,
        "matched_inputs_across_settings": True,
        "prefix_stable_counts": True,
        "all_declared_rivals_refuted_by_two_demos": True,
        "public_first_turn_private_and_future_invariant": True,
        "distinct_public_first_turns": len(public_turn_ids),
        "stress_30x30": stress_records,
        "source": {
            "prototype": str(MODULE_PATH.relative_to(p.REPO)),
            "prototype_sha256": hashlib.sha256(MODULE_PATH.read_bytes()).hexdigest(),
            "adapter_sha256": hashlib.sha256((HERE / "adapter.py").read_bytes()).hexdigest(),
            "promotion_sha256": hashlib.sha256((HERE / "promotion.json").read_bytes()).hexdigest(),
            "canonical_sha256": hashlib.sha256((HERE / "canonical.rkt").read_bytes()).hexdigest(),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, action="append", dest="seeds")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    report = audit(args.seeds or [0, 17])
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "status": report["status"],
                "jobs_passed": report["jobs_passed"],
                "racket_evaluations": report["racket_evaluations"],
                "stress_30x30": report["stress_30x30"],
                "out": str(args.out),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
