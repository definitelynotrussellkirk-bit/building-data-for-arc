#!/usr/bin/env python3
"""Bounded protected-Racket audit for the cascading-completion family."""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

from reviewer_support import public_challenge_bytes, public_challenge_id

HERE = Path(__file__).resolve().parent
TASK_ID = "b4d9320e0d9d"
SETTINGS = ("one_pass", "two_pass")


def _load(name: str, filename: str):
    path = HERE / filename
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _literal(grid: list[list[int]]) -> str:
    return "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"


def _digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    ).hexdigest()


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seeds", type=int, default=16)
    args = parser.parse_args(argv)
    if args.seeds < 1:
        parser.error("--seeds must be positive")
    if args.out.exists() or args.out.is_symlink():
        parser.error("--out must be a new directory")

    prototype = _load("_b4_parametric_audit_prototype", "prototype.py")
    adapter = _load("_b4_parametric_audit_adapter", "adapter.py")
    failures: list[dict[str, Any]] = []
    jobs = 0
    public_turns = 0

    for seed in range(args.seeds):
        for demos in range(2, 7):
            episodes = {
                mode: adapter.generate(seed, {"completion_rounds": mode}, demos=demos, queries=4)
                for mode in SETTINGS
            }
            baseline_inputs = [
                pair["input"]
                for split in ("train", "test")
                for pair in episodes["one_pass"][split]
            ]
            for mode, episode in episodes.items():
                jobs += 1
                inputs = [
                    pair["input"]
                    for split in ("train", "test")
                    for pair in episode[split]
                ]
                if inputs != baseline_inputs:
                    failures.append({"seed": seed, "demos": demos, "mode": mode, "finding": "setting-dependent inputs"})
                certificate = prototype.teaching_certificate(episode, mode)
                if certificate["declared_setting_survivors"] != [mode]:
                    failures.append({"seed": seed, "demos": demos, "mode": mode, "finding": "setting not uniquely identified", "certificate": certificate})
                if certificate["surviving_named_rivals"]:
                    failures.append({"seed": seed, "demos": demos, "mode": mode, "finding": "named rival survives demos", "certificate": certificate})
                for index in range(4):
                    public = adapter.public_turn(episode, index)
                    public_turns += 1
                    if public != {"train": episode["train"], "test": [{"input": episode["test"][index]["input"]}]}:
                        failures.append({"seed": seed, "demos": demos, "mode": mode, "finding": "bad public turn", "query_index": index})
                one = adapter.generate(seed, {"completion_rounds": mode}, demos=demos, queries=1)
                if one["train"] != episode["train"] or one["test"] != episode["test"][:1]:
                    failures.append({"seed": seed, "demos": demos, "mode": mode, "finding": "query prefix instability"})

    args.out.mkdir(parents=True)
    (args.out / "public").mkdir()
    (args.out / "private").mkdir()

    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule

    racket_evaluations = 0
    examples: list[dict[str, Any]] = []
    with RacketBridge(timeout=30, max_calls_before_restart=128) as bridge:
        if bridge.runtime_identity.get("protected") is not True:
            raise RuntimeError("protected Racket runtime required")
        for mode in SETTINGS:
            episode = adapter.generate(1701, {"completion_rounds": mode}, demos=3, queries=4)
            wrapped = wrap_rule(episode["program_solution"])
            for split in ("train", "test"):
                for pair in episode[split]:
                    actual = bridge.eval_text(f"({wrapped} {_literal(pair['input'])})")
                    racket_evaluations += 1
                    if actual != pair["output"]:
                        failures.append({"mode": mode, "finding": "Racket label mismatch", "split": split})
            public_raw = public_challenge_bytes(episode)
            public_id = public_challenge_id(episode)
            (args.out / "public" / f"{public_id}.json").write_bytes(public_raw)
            private = {
                "task_id": TASK_ID,
                "seed": 1701,
                "settings": {"completion_rounds": mode},
                "program": episode["program_solution"],
                "program_sha256": hashlib.sha256(episode["program_solution"].encode()).hexdigest(),
                "episode": episode,
                "teaching_certificate": prototype.teaching_certificate(episode, mode),
            }
            (args.out / "private" / f"{mode}.json").write_text(json.dumps(private, sort_keys=True, indent=2) + "\n")
            altered = copy.deepcopy(episode)
            altered["program_solution"] = "private mutation"
            for pair in altered["test"]:
                pair["output"] = [[9]]
            if public_challenge_id(altered) != public_id:
                failures.append({"mode": mode, "finding": "public identifier includes private fields"})
            examples.append({
                "mode": mode,
                "public_id": public_id,
                "public_path": f"public/{public_id}.json",
                "private_path": f"private/{mode}.json",
                "input_shapes": [[len(pair["input"]), len(pair["input"][0])] for pair in episode["train"] + episode["test"]],
                "stress": prototype.analyse_grid(episode["test"][3]["input"]),
            })

        witness_episode = adapter.generate(1701, {"completion_rounds": "two_pass"}, demos=3, queries=4)
        witness_grid = witness_episode["test"][0]["input"]
        trace = prototype.dependency_trace(witness_grid)
        one_output = bridge.eval_text(
            f"({wrap_rule(adapter.program({'completion_rounds': 'one_pass'}))} {_literal(witness_grid)})"
        )
        two_output = bridge.eval_text(
            f"({wrap_rule(adapter.program({'completion_rounds': 'two_pass'}))} {_literal(witness_grid)})"
        )
        racket_evaluations += 2
        if one_output == two_output or one_output != trace["skip_step_b_output"] or two_output != trace["step_b_output"]:
            failures.append({"finding": "causal dependency witness failed"})
        witness = {
            "schema": "arcpuzzles-parametric-sequential-dependency-v1",
            "task_id": TASK_ID,
            "setting": {"completion_rounds": "two_pass"},
            "seed": 1701,
            "split": "query",
            "index": 0,
            "step_a": trace["step_a"],
            "intermediate": "the full first-pass grid",
            "step_b": trace["step_b"],
            "why_b_depends_on_a": "The second eligibility scan reads cells created by step A; scanning the original input again cannot create the witnessed second-stage cells.",
            "witness_path": "generators/b4d9320e0d9d/workspace/parametric/evidence/current/sequential_dependency.json",
            "input_sha256": _digest(witness_grid),
            "intermediate_sha256": _digest(trace["intermediate"]),
            "skip_step_b_output_sha256": _digest(one_output),
            "step_b_output_sha256": _digest(two_output),
            "changed_cells_in_step_b": trace["changed_cells_in_step_b"],
            "protected_racket": True,
            "program_sha256": {
                mode: hashlib.sha256(adapter.program({"completion_rounds": mode}).encode()).hexdigest()
                for mode in SETTINGS
            },
            "input": witness_grid,
            "intermediate_grid": trace["intermediate"],
            "skip_step_b_output": one_output,
            "step_b_output": two_output,
        }
        (args.out / "sequential_dependency.json").write_text(json.dumps(witness, sort_keys=True, indent=2) + "\n")
        racket_identity = bridge.runtime_identity

    report = {
        "schema": "b4d9320e0d9d-parametric-authoring-evidence-v1",
        "task_id": TASK_ID,
        "status": "passed" if not failures else "failed",
        "parameter": {"name": "completion_rounds", "values": list(SETTINGS), "default": "one_pass", "chosen_once_per_episode": True},
        "bounded_self_audit": {
            "seeds": args.seeds,
            "demo_counts": [2, 3, 4, 5, 6],
            "settings": len(SETTINGS),
            "episodes": jobs,
            "public_turns": public_turns,
            "failures": failures,
            "scope": "Finite deterministic seeds and named rivals only; no universal uniqueness claim.",
        },
        "count_independence": {"demos_supported": [2, 6], "queries_supported": [1, 4], "prefix_stable": not any(f.get("finding") == "query prefix instability" for f in failures)},
        "examples": examples,
        "racket": racket_identity,
        "racket_label_count": racket_evaluations,
        "public_projection": "reviewer_support.public_challenge_bytes/public_challenge_id plus one-query public_turn",
        "sequential_dependency_path": "sequential_dependency.json",
        "training_admitted": False,
    }
    (args.out / "report.json").write_text(json.dumps(report, sort_keys=True, indent=2) + "\n")
    print(json.dumps({"status": report["status"], "episodes": jobs, "public_turns": public_turns, "racket_evaluations": racket_evaluations, "failures": len(failures)}, sort_keys=True))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
